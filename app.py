import os
import json
import joblib
from pathlib import Path
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from schemas import PropertyFeatures, LLMExtractionResult, PredictionResponse
from prompts import EXTRACTION_PROMPT_V1, INTERPRETATION_PROMPT
from llm_client import call_llm

load_dotenv(Path(__file__).parent / ".env", override=True)

app = FastAPI(title="AI Real Estate Agent", version="1.0")

# let the streamlit frontend talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# load model at startup
MODEL_PATH = os.getenv("MODEL_PATH", "model/final_best_model.joblib")
pipeline = joblib.load(MODEL_PATH)
print(f"[startup] loaded pipeline from {MODEL_PATH}")

# training set summary stats for interpretation context coming straight from the notebook
TRAINING_STATS = {
    "median_price": 160000,
    "mean_price": 180796,
    "std_price": 79887,
    "min_price": 12789,
    "max_price": 625000,
    "q25_price": 129500,
    "q75_price": 213500,
}

# all 81 columns the preprocessor expects because the pipeline was trained on the full Ames dataframe (minus SalePrice), so we need to pass in a row with all these columns
ALL_COLUMNS = [
    "Order", "PID", "MS SubClass", "MS Zoning", "Lot Frontage", "Lot Area",
    "Street", "Alley", "Lot Shape", "Land Contour", "Utilities", "Lot Config",
    "Land Slope", "Neighborhood", "Condition 1", "Condition 2", "Bldg Type",
    "House Style", "Overall Qual", "Overall Cond", "Year Built", "Year Remod/Add",
    "Roof Style", "Roof Matl", "Exterior 1st", "Exterior 2nd", "Mas Vnr Type",
    "Mas Vnr Area", "Exter Qual", "Exter Cond", "Foundation", "Bsmt Qual",
    "Bsmt Cond", "Bsmt Exposure", "BsmtFin Type 1", "BsmtFin SF 1",
    "BsmtFin Type 2", "BsmtFin SF 2", "Bsmt Unf SF", "Total Bsmt SF",
    "Heating", "Heating QC", "Central Air", "Electrical", "1st Flr SF",
    "2nd Flr SF", "Low Qual Fin SF", "Gr Liv Area", "Bsmt Full Bath",
    "Bsmt Half Bath", "Full Bath", "Half Bath", "Bedroom AbvGr",
    "Kitchen AbvGr", "Kitchen Qual", "TotRms AbvGrd", "Functional",
    "Fireplaces", "Fireplace Qu", "Garage Type", "Garage Yr Blt",
    "Garage Finish", "Garage Cars", "Garage Area", "Garage Qual",
    "Garage Cond", "Paved Drive", "Wood Deck SF", "Open Porch SF",
    "Enclosed Porch", "3Ssn Porch", "Screen Porch", "Pool Area", "Pool QC",
    "Fence", "Misc Feature", "Misc Val", "Mo Sold", "Yr Sold",
    "Sale Type", "Sale Condition",
]

# mapping the 12 selected feature names and the actual dataset column names
FEATURE_TO_COLUMN = {
    "overall_qual": "Overall Qual",
    "gr_liv_area": "Gr Liv Area",
    "year_built": "Year Built",
    "total_bsmt_sf": "Total Bsmt SF",
    "first_flr_sf": "1st Flr SF",
    "second_flr_sf": "2nd Flr SF",
    "bsmtfin_sf_1": "BsmtFin SF 1",
    "lot_area": "Lot Area",
    "full_bath": "Full Bath",
    "garage_cars": "Garage Cars",
    "bsmt_qual": "Bsmt Qual",
    "kitchen_qual": "Kitchen Qual",
}


def build_dataframe(features: dict) -> pd.DataFrame:

    # start with a row where every column is NaN and the pipeline's imputers will fill in defaults for anything not provided

    row = {}
    for col in ALL_COLUMNS:
        row[col] = np.nan

    row["Order"] = 1
    row["PID"] = 1000000000

    # fill in the features the user actually provided.
    for schema_key, col_name in FEATURE_TO_COLUMN.items():
        val = features.get(schema_key)
        if val is not None:
            row[col_name] = val

    return pd.DataFrame([row])


def parse_llm_json(text: str) -> dict:

    cleaned = text.strip()

    # strip out any line that starts with ``` before parsing
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        clean_lines = []
        for line in lines:
            if not line.strip().startswith("```"):
                clean_lines.append(line)
        cleaned = "\n".join(clean_lines)

    return json.loads(cleaned)


# request models
class ExtractRequest(BaseModel):
    query: str


class PredictRequest(BaseModel):
    query: str
    features: dict = {}  # pre-filled by the user after reviewing Stage 1 output


# Stage 1 endpoint
@app.post("/extract")
async def extract(request: ExtractRequest):
    
    # parse the natural language query into structured features and the UI uses this to let the user fill gaps before prediction runs
    
    prompt = EXTRACTION_PROMPT_V1.format(query=request.query)

    try:
        raw = call_llm(prompt)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM extraction failed: {e}")

    try:
        parsed = parse_llm_json(raw)
        extraction = LLMExtractionResult(**parsed)
   
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"LLM output did not match expected schema: {e}. Raw output: {raw[:500]}"
        )

    return {
        "features": extraction.features.model_dump(),
        "confident_features": extraction.confident_features,
        "missing_features": extraction.missing_features,
    }


# main prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictRequest):
    
    # Stages 2 & 3: ML prediction + LLM interpretation.
    # doesn't re-run Stage 1, the features dict is used directly.
    
    # validate and coerce feature values through the schema
    try:
        validated = PropertyFeatures(**request.features)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid feature values: {e}")

    features_dict = validated.model_dump()

    confident = []
    missing = []
    for key, value in features_dict.items():
        if value is not None:
            confident.append(key)
        else:
            missing.append(key)

    # ML prediction
    df = build_dataframe(features_dict)
    try:
        price = float(pipeline.predict(df)[0])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model prediction error: {e}")

    # LLM interpretation: build a dict of only the features that were provided, then format the prompt with the prediction and market stats

    provided_features = {}
    for key, value in features_dict.items():
        if value is not None:
            provided_features[key] = value

    interp_prompt = INTERPRETATION_PROMPT.format(
        features=json.dumps(provided_features, indent=2),
        confident=json.dumps(confident),
        missing=json.dumps(missing),
        predicted_price=f"${price:,.0f}",
        median_price=f"${TRAINING_STATS['median_price']:,}",
        q25=f"${TRAINING_STATS['q25_price']:,}",
        q75=f"${TRAINING_STATS['q75_price']:,}",
        mean_price=f"${TRAINING_STATS['mean_price']:,}",
    )

    try:
        interpretation = call_llm(interp_prompt)
    except Exception:
        interpretation = (
            f"Predicted price: ${price:,.0f}. "
            f"The median in our dataset is ${TRAINING_STATS['median_price']:,}."
        )

    return PredictionResponse(
        query=request.query,
        extracted_features=features_dict,
        confident_features=confident,
        missing_features=missing,
        predicted_price=round(price, 2),
        interpretation=interpretation,
    )


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": pipeline is not None}