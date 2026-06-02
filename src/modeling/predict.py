import joblib
import numpy as np
import pandas as pd
from src.pipeline.feature_engineering import engineer_features
from src.config import MODEL_PATH, PREPROCESSOR_PATH, RISK_THRESHOLDS

_model = None
_pre = None


def get_artifacts():
    global _model, _pre
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        _pre = joblib.load(PREPROCESSOR_PATH)
    return _model, _pre


def risk_band(p: float) -> str:
    if p < RISK_THRESHOLDS["low"]:
        return "low"
    if p < RISK_THRESHOLDS["medium"]:
        return "medium"
    return "high"


def predict(df: pd.DataFrame) -> pd.DataFrame:
    model, pre = get_artifacts()
    df_eng = engineer_features(df)
    drop_cols = [c for c in ["customerID", "Churn"] if c in df_eng.columns]
    X = df_eng.drop(columns=drop_cols)
    X_t = pre.transform(X)

    # Handle sparse matrix
    try:
        X_t = X_t.toarray()
    except AttributeError:
        pass

    proba = model.predict_proba(X_t)[:, 1]
    out = df.copy()
    out["churn_probability"] = proba
    out["risk_band"] = [risk_band(p) for p in proba]
    return out
