import streamlit as st
import requests

import os
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Real Estate Agent", page_icon="🏠", layout="wide")

st.markdown("""
<style>
    /* page background */
    .stApp { background-color: #f0f2f6; }

    /* tighten the main container */
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; max-width: 1050px; }

    /* hero banner */
    .hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
        border-radius: 14px;
        padding: 1.4rem 2rem;
        margin-bottom: 1.2rem;
        color: white;
    }
    .hero h1 { font-size: 1.7rem; font-weight: 700; margin: 0 0 0.2rem 0; color: white; }
    .hero p  { font-size: 0.88rem; opacity: 0.7; margin: 0; }

    /* section cards */
    .card {
        background: white;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.7rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    }
    .card-title {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #999;
        margin-bottom: 0.5rem;
    }

    /* missing feature input rows — label left, small white input right */
    .feat-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 2px 0;
        border-bottom: 1px solid #f0f0f0;
        gap: 8px;
    }
    .feat-row:last-child { border-bottom: none; }
    .feat-label { font-size: 0.83rem; color: #333; flex: 1; }

    /* query textarea — large, comfortable to type in */
    div[data-testid="stForm"] textarea {
        background-color: white !important;
        border: 1.5px solid #ced4da !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="stForm"] textarea:focus {
        border-color: #0077b6 !important;
        box-shadow: 0 0 0 2px rgba(0, 119, 182, 0.15) !important;
        outline: none !important;
    }

    /* missing feature input boxes — small, number-sized */
    div[data-testid="stTextInput"] input {
        background-color: white !important;
        border: 1.5px solid #ced4da !important;
        border-radius: 6px !important;
        padding: 3px 8px !important;
        font-size: 0.82rem !important;
        height: 30px !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: #0077b6 !important;
        box-shadow: 0 0 0 2px rgba(0, 119, 182, 0.15) !important;
        outline: none !important;
    }
    /* remove the default label above each text input (we render our own) */
    div[data-testid="stTextInput"] label { display: none !important; }
    /* tighten the vertical gap streamlit adds around each input widget */
    div[data-testid="stTextInput"] { margin-bottom: 0 !important; padding-bottom: 0 !important; }
    /* collapse the default gap Streamlit adds between rows inside columns */
    div[data-testid="column"] > div > div { gap: 0 !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0 !important; padding: 0 !important; }
    /* remove form border/background that Streamlit adds */
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; }

    /* feature chips */
    .chip-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 0.3rem; }
    .chip {
        display: inline-flex; align-items: center; gap: 4px;
        padding: 3px 9px; border-radius: 20px;
        font-size: 0.78rem; font-weight: 500;
    }
    .chip-found   { background: #e8f5e9; color: #2e7d32; }
    .chip-missing { background: #fff8e1; color: #f57f17; }

    /* price result */
    .price-box {
        background: linear-gradient(135deg, #0f3460, #1a1a2e);
        border-radius: 12px;
        padding: 1.4rem 2rem;
        text-align: center;
        color: white;
        margin-bottom: 0.8rem;
    }
    .price-label { font-size: 0.78rem; opacity: 0.65; letter-spacing: 0.08em; text-transform: uppercase; }
    .price-value { font-size: 2.6rem; font-weight: 800; margin: 0.2rem 0; }

    /* step badge */
    .step-badge {
        display: inline-block;
        background: #0f3460;
        color: white;
        border-radius: 50%;
        width: 22px; height: 22px;
        line-height: 22px;
        text-align: center;
        font-size: 0.72rem;
        font-weight: 700;
        margin-right: 6px;
    }
    .step-title { font-size: 0.95rem; font-weight: 600; color: #1a1a2e; }

    /* ── Extract Features button — teal gradient ── */
    div.stButton > button:not([kind="primary"]) {
        background: linear-gradient(135deg, #0077b6, #00b4d8) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.55rem 1.2rem !important;
        letter-spacing: 0.03em !important;
        box-shadow: 0 3px 10px rgba(0, 119, 182, 0.35) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button:not([kind="primary"]):hover {
        background: linear-gradient(135deg, #005f8e, #0096b4) !important;
        box-shadow: 0 5px 16px rgba(0, 119, 182, 0.5) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Predict Price button — amber/gold gradient ── */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #e67e22, #f39c12) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 0.55rem 1.2rem !important;
        letter-spacing: 0.03em !important;
        box-shadow: 0 3px 10px rgba(230, 126, 34, 0.4) !important;
        transition: all 0.2s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #cf6d17, #d68910) !important;
        box-shadow: 0 5px 16px rgba(230, 126, 34, 0.55) !important;
        transform: translateY(-1px) !important;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
    <h1>🏠 AI Real Estate Agent</h1>
    <p>Describe any property in plain English — we'll extract the details, estimate the price, and explain the result.</p>
</div>
""", unsafe_allow_html=True)

# constants
FEATURE_LABELS = {
    "overall_qual":  "Overall Quality (1–10)",
    "gr_liv_area":   "Living Area (sqft)",
    "year_built":    "Year Built",
    "total_bsmt_sf": "Total Basement Area (sqft)",
    "first_flr_sf":  "First Floor Area (sqft)",
    "second_flr_sf": "Second Floor Area (sqft)",
    "bsmtfin_sf_1":  "Finished Basement Area (sqft)",
    "lot_area":      "Lot Size (sqft)",
    "full_bath":     "Full Bathrooms",
    "garage_cars":   "Garage Capacity (cars)",
    "bsmt_qual":     "Basement Quality (Ex/Gd/TA/Fa/Po/None)",
    "kitchen_qual":  "Kitchen Quality (Ex/Gd/TA/Fa/Po)",
}


def label(feat: str) -> str:
    return FEATURE_LABELS.get(feat, feat)


def try_cast(val: str):
    # try to convert the user's text input to a number
    
    val = val.strip()

    try:
        return int(val)
    except ValueError:
        pass  # not an integer, try float next

    try:
        return float(val)
    except ValueError:
        pass  # not a float either, return as-is

    return val


# session state
if "extraction" not in st.session_state:
    st.session_state.extraction = None
if "prediction" not in st.session_state:
    st.session_state.prediction = None

# main two-column layout
left_col, right_col = st.columns(2, gap="large")

# LEFT: Step 1: describe the property
with left_col:
    st.markdown('<span class="step-badge">1</span><span class="step-title">Describe the property</span>', unsafe_allow_html=True)

    with st.form("extract_form"):
        query = st.text_area(
            "Property description",
            placeholder="e.g. A 3-bedroom 2-bath house with a 2-car garage, good quality finishes, built in the 1990s, about 1800 sqft",
            height=160,
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("🔍  Extract Features", use_container_width=True)

    if submitted:
        if not query.strip():
            st.warning("Please describe a property first.")
        else:
            # clear any previous results when a new extraction starts
            st.session_state.extraction = None
            st.session_state.prediction = None
            with st.spinner("Reading your description..."):
                try:
                    resp = requests.post(f"{API_URL}/extract", json={"query": query}, timeout=30)
                    if resp.status_code != 200:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"Extraction failed ({resp.status_code}): {detail}")
                    else:
                        st.session_state.extraction = resp.json()
                        st.session_state.extraction["query"] = query
                except requests.exceptions.ConnectionError:
                    st.error("Can't reach the API. Make sure the server is running:\n\n`uvicorn app:app --reload`")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

# Step 2: review and fill in features
with right_col:
    if st.session_state.extraction:
        extraction = st.session_state.extraction
        features  = extraction["features"]
        confident = extraction["confident_features"]
        missing   = extraction["missing_features"]

        st.markdown('<span class="step-badge">2</span><span class="step-title">Review & fill in features</span>', unsafe_allow_html=True)

        # show what the LLM found
        st.markdown('<div class="card"><div class="card-title">✅ Extracted from your description</div>', unsafe_allow_html=True)
        if confident:
            chips = ""
            for f in confident:
                chips += f'<span class="chip chip-found">✓ {label(f)}: <b>{features.get(f)}</b></span>'
            st.markdown(f'<div class="chip-row">{chips}</div>', unsafe_allow_html=True)
        else:
            st.markdown("<p style='color:#999;font-size:0.85rem'>Nothing extracted — try adding more detail.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        # show inputs for anything the LLM didn't find
        user_filled = {}
        if missing:
            st.markdown(
                '<div class="card">'
                '<div class="card-title">❓ Fill in what you know (optional)</div>'
                '<p style="font-size:0.78rem;color:#888;margin:0 0 0.6rem 0">'
                'Leave any box blank — the model will use dataset averages.</p>',
                unsafe_allow_html=True
            )
            for feat in missing:
                # each row: feature name on the left, small input box on the right
                label_col, input_col = st.columns([3, 1])
                with label_col:
                    st.markdown(f'<div class="feat-label">{label(feat)}</div>', unsafe_allow_html=True)
                with input_col:
                    typed = st.text_input(label(feat), value="", key=f"fill_{feat}", label_visibility="collapsed")
                    if typed.strip():
                        user_filled[feat] = try_cast(typed)
        # predict button
        if st.button("💰  Predict Price", type="primary", use_container_width=True):
            merged = {k: v for k, v in features.items() if v is not None}
            merged.update(user_filled)
            with st.spinner("Calculating price estimate..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/predict",
                        json={"query": extraction["query"], "features": merged},
                        timeout=60,
                    )
                    if resp.status_code != 200:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"Prediction failed ({resp.status_code}): {detail}")
                    else:
                        # store the result so it stays visible after the page reruns
                        st.session_state.prediction = resp.json()
                except requests.exceptions.ConnectionError:
                    st.error("Can't reach the API. Make sure the server is running.")
                except Exception as e:
                    st.error(f"Something went wrong: {e}")


if st.session_state.prediction:
    data = st.session_state.prediction
    st.markdown("---")

    # Price display
    st.markdown(f"""
    <div class="price-box">
        <div class="price-label">Estimated Sale Price</div>
        <div class="price-value">${data['predicted_price']:,.0f}</div>
        <div style="opacity:0.6;font-size:0.78rem">Ames, Iowa · Gradient Boosting model</div>
    </div>
    """, unsafe_allow_html=True)

    # LLM interpretation
    st.markdown('<div class="card"><div class="card-title">📊 What\'s driving this estimate</div>', unsafe_allow_html=True)
    st.markdown(f"<p style='line-height:1.7'>{data['interpretation']}</p>", unsafe_allow_html=True)
    if data["missing_features"]:
        st.markdown(
            f"<p style='color:#f57f17;font-size:0.85rem'>⚠️ {len(data['missing_features'])} feature(s) were filled by model defaults — "
            "providing more details would improve accuracy.</p>",
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### How it works")
    st.markdown("""
1. **Describe** the property
2. **LLM** extracts 12 key features
3. **You fill** anything missing
4. **ML model** predicts the price
5. **LLM** explains the result
    """)
    st.markdown("---")
    st.markdown("**Model:** Gradient Boosting")
    st.markdown("**Dataset:** Ames Housing · 2,930 sales")
    st.markdown("**Test RMSE:** $23,945 · **R²:** 0.916")
    st.markdown("**LLM:** Groq · Llama 3.3 70B")
    st.markdown("---")
    try:
        h = requests.get(f"{API_URL}/health", timeout=3)
        if h.status_code == 200:
            st.success("API: Connected ✓")
        else:
            st.error("API: Error")
    except Exception:
        st.warning("API: Not connected")