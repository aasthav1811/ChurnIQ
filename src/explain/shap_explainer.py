import shap
import joblib
import numpy as np
import pandas as pd
from src.config import MODEL_PATH, PREPROCESSOR_PATH
from src.pipeline.feature_engineering import engineer_features

_explainer = None


def get_explainer():
    global _explainer
    if _explainer is None:
        model = joblib.load(MODEL_PATH)
        _explainer = shap.TreeExplainer(model)
    return _explainer


def explain_customer(df_one: pd.DataFrame, top_k: int = 5) -> list[dict]:
    pre = joblib.load(PREPROCESSOR_PATH)
    df_eng = engineer_features(df_one)
    drop_cols = [c for c in ["customerID", "Churn"] if c in df_eng.columns]
    X = df_eng.drop(columns=drop_cols)
    X_t = pre.transform(X)

    # Handle sparse matrix
    try:
        X_t = X_t.toarray()
    except AttributeError:
        pass

    feature_names = pre.get_feature_names_out()
    explainer = get_explainer()
    shap_values = explainer.shap_values(X_t)

    # Handle both 1D and 2D shap output shapes
    if isinstance(shap_values, list):
        vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
    elif shap_values.ndim > 1:
        vals = shap_values[0]
    else:
        vals = shap_values

    contrib = pd.DataFrame(
        {
            "feature": feature_names,
            "shap_value": vals,
            "abs_shap": np.abs(vals),
        }
    ).sort_values("abs_shap", ascending=False).head(top_k)

    return contrib.to_dict(orient="records")
