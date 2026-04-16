# AI Real Estate Agent

Describe a house in plain English and get a price estimate for Ames, Iowa.

## How it works

```
Your description → LLM extracts features → ML model predicts price → LLM explains result
```

1. **LLM (Stage 1)** — reads your description and pulls out structured features (bedrooms, sqft, quality, etc.)
2. **ML Model** — a GradientBoosting pipeline trained on 2,930 Ames housing sales predicts the price
3. **LLM (Stage 2)** — explains the prediction and puts it in context of the local market

**Model accuracy:** RMSE $23,945 · R² 0.916

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Get a free Groq API key**

Sign up at [console.groq.com/keys](https://console.groq.com/keys) and copy your key.

**3. Create your `.env` file**
```bash
cp .env.example .env
# open .env and paste your GROQ_API_KEY
```

**4. Place the trained model**

Put `final_best_model.joblib` in the `model/` folder.

**5. Start the API**
```bash
uvicorn app:app --reload
```

**6. Start the UI** (in a second terminal)
```bash
streamlit run ui.py
```

Open `http://localhost:8501` in your browser.

## Docker

```bash
docker build -t real-estate-agent .
docker run -p 8000:8000 -e GROQ_API_KEY=your_key_here real-estate-agent
```

Then run the UI locally pointing at `http://localhost:8000` (already the default).

## Prompt versions

Two extraction prompts are available (V1 = detailed with examples, V2 = concise). To run a scored comparison across 5 test queries:

```bash
python prompt_eval.py
```

Results are saved to `prompt_eval_log.json` and the best prompt with be used in `app.py`

## Project structure

```
app.py            — FastAPI server and prompt chain
schemas.py        — Pydantic models for features and LLM output
prompts.py        — Prompt templates (2 extraction + 1 interpretation)
llm_client.py     — Groq API wrapper
prompt_eval.py    — Script to compare prompt versions
ui.py             — Streamlit frontend
Dockerfile        — Container for the API
model/
  final_best_model.joblib   — trained pipeline (not in git)
```
