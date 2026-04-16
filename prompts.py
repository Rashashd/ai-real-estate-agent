"""
Prompt templates for the two-stage LLM chain.

Stage 1 has two versions (V1 and V2) so we can compare extraction accuracy.
Stage 2 interprets the prediction for the user.

V1 is detailed with examples and explicit mapping guidance.
V2 is shorter, more structured, relies on the model knowing real estate terms.
We test both on the same queries in prompt_eval.py and pick the winner.
"""

# stage 1: Feature extraction prompts

EXTRACTION_PROMPT_V1 = """You are a real estate data extraction assistant. A user describes a property they want priced. Extract only the features the pricing model needs.

FEATURES TO EXTRACT (set null if not mentioned):

Numeric:
- overall_qual (int 1-10): overall quality. Map: "poor"=2, "average"=5, "good"=7, "great"=8, "excellent"=9, "luxury"=10
- gr_liv_area (int): above-ground living area in sqft
- year_built (int): year built
- total_bsmt_sf (float): total basement sqft. 0 if explicitly no basement, null if unknown
- first_flr_sf (float): first floor sqft
- second_flr_sf (float): second floor sqft. 0 for single-story, null if unknown
- bsmtfin_sf_1 (float): finished basement sqft
- lot_area (int): lot size in sqft
- full_bath (int): full bathrooms above ground
- garage_cars (int): garage capacity in cars. "no garage"=0, "small/1-car"=1, "2-car"=2, "big/3-car"=3

Ordinal (use exact codes only):
- bsmt_qual: basement quality — Ex, Gd, TA, Fa, Po, or None (if no basement)
- kitchen_qual: kitchen quality — Ex, Gd, TA, Fa, Po

RULES:
1. Only extract what the user actually said or clearly implied. Never invent data.
2. For 2-story houses, if only total sqft is given, split roughly 60/40 (first/second floor).
3. List every extracted feature in confident_features. Everything else goes in missing_features.

Respond with ONLY this JSON (no markdown, no explanation):
{{
  "features": {{
    "overall_qual": null,
    "gr_liv_area": null,
    "year_built": null,
    "total_bsmt_sf": null,
    "first_flr_sf": null,
    "second_flr_sf": null,
    "bsmtfin_sf_1": null,
    "lot_area": null,
    "full_bath": null,
    "garage_cars": null,
    "bsmt_qual": null,
    "kitchen_qual": null
  }},
  "confident_features": [],
  "missing_features": []
}}

User's description: {query}"""


EXTRACTION_PROMPT_V2 = """Extract property features for a house price model. Return JSON only.

Only these 12 features matter (null if not mentioned):
- overall_qual (int 1-10): quality. "average"→5, "good"→7, "excellent"→9
- gr_liv_area (int): living area sqft
- year_built (int): construction year
- total_bsmt_sf (float): basement sqft, 0 if no basement
- first_flr_sf (float): 1st floor sqft
- second_flr_sf (float): 2nd floor sqft, 0 if single-story
- bsmtfin_sf_1 (float): finished basement sqft
- lot_area (int): lot sqft
- full_bath (int): full bathrooms
- garage_cars (int): garage capacity. 0=none, 1=small, 2=standard, 3=large
- bsmt_qual (str): Ex/Gd/TA/Fa/Po/None
- kitchen_qual (str): Ex/Gd/TA/Fa/Po

Only extract what's stated or clearly implied. Do not guess.
Include confident_features (what you found) and missing_features (what's not there).

JSON: {{"features": {{...}}, "confident_features": [...], "missing_features": [...]}}

Description: {query}"""


# stage 2: Prediction interpretation prompts

INTERPRETATION_PROMPT = """You are a real estate analyst explaining a price prediction to a homebuyer.

Here's what we know:
- Extracted property features: {features}
- Features we're confident about: {confident}
- Features that were missing (filled by model defaults): {missing}
- Predicted price: {predicted_price}

For context, here are stats from our training data (Ames, Iowa):
- Median sale price: {median_price}
- 25th percentile: {q25}
- 75th percentile: {q75}
- Mean sale price: {mean_price}

Write a clear 3-4 sentence interpretation that:
1. States the predicted price
2. Compares it to the market (is it above/below median? which quartile?)
3. Explains what's likely driving the price up or down based on the features provided
4. Notes if many features were missing, which adds uncertainty to the estimate

Keep it conversational and helpful. No bullet points. No hedging like "I think" — be direct."""