import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("AIzaSyCpjiTwwicLvYleB8OXmIpp3B5Mk3iTDvA")
LLM_MODEL = "gemini-1.5-flash"

RAW_DATA_PATH = "data/raw/telco_churn.csv"
PROCESSED_DATA_PATH = "data/processed/churn_processed.csv"
MODEL_PATH = "models/xgb_churn.pkl"
PREPROCESSOR_PATH = "models/preprocessor.pkl"

TARGET_COL = "Churn"
RANDOM_STATE = 42

RISK_THRESHOLDS = {"low": 0.3, "medium": 0.6, "high": 1.0}

INTERVENTIONS = {
    "high_risk": [
        "20% discount for 6 months",
        "Free premium upgrade",
        "Personal CSM call",
    ],
    "medium_risk": [
        "10% loyalty discount",
        "Onboarding refresh email",
        "Feature highlight email",
    ],
    "low_risk": [
        "Newsletter",
        "Community invite",
    ],
}
