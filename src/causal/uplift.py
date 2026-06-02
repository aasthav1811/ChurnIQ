"""
Uplift / causal effect estimator using a T-learner.

Estimates: which customers benefit MOST from a discount intervention?
The T-learner trains two separate models — one on the treatment group,
one on the control group — and scores the difference in predicted churn probability.
A high uplift score = this customer's churn decision is likely to flip with intervention.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from src.pipeline.feature_engineering import engineer_features


# Columns dropped before transform — must not appear in preprocessor
DROP_COLS = ["customerID", "Churn", "treatment", "PaperlessBilling"]

NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges", "avg_monthly_spend"]
CATEGORICAL = [
    "gender", "SeniorCitizen", "Partner", "Dependents", "PhoneService",
    "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup",
    "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies",
    "Contract", "PaymentMethod",   # ← PaperlessBilling intentionally excluded
    "tenure_bucket", "high_value",
]


def _build_uplift_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL),
    ])


def simulate_treatment(df: pd.DataFrame, treatment_col: str = "PaperlessBilling") -> pd.DataFrame:
    """Uses PaperlessBilling=Yes as a proxy for 'discount/offer applied' (synthetic example)."""
    df = df.copy()
    df["treatment"] = (df[treatment_col] == "Yes").astype(int)
    return df


def estimate_uplift(df: pd.DataFrame) -> pd.DataFrame:
    """
    T-learner: train two models, one per treatment arm, score the CATE difference.
    Returns dataframe sorted by uplift descending (best intervention targets first).
    """
    df = simulate_treatment(df)
    df_eng = engineer_features(df)

    # Drop columns that aren't features
    X = df_eng.drop(columns=[c for c in DROP_COLS if c in df_eng.columns])
    y = df_eng["Churn"].values
    t = df_eng["treatment"].values

    # Only keep columns the preprocessor actually knows about
    available_num = [c for c in NUMERIC if c in X.columns]
    available_cat = [c for c in CATEGORICAL if c in X.columns]
    X = X[available_num + available_cat]

    pre = _build_uplift_preprocessor()
    # Rebuild with only available columns
    pre = ColumnTransformer([
        ("num", StandardScaler(), available_num),
        ("cat", OneHotEncoder(handle_unknown="ignore"), available_cat),
    ])
    Xp = pre.fit_transform(X)

    try:
        Xp = Xp.toarray()
    except AttributeError:
        pass

    # Treatment arm model (received the intervention)
    m1 = RandomForestClassifier(n_estimators=200, random_state=42)
    m1.fit(Xp[t == 1], y[t == 1])

    # Control arm model (no intervention)
    m0 = RandomForestClassifier(n_estimators=200, random_state=42)
    m0.fit(Xp[t == 0], y[t == 0])

    p1 = m1.predict_proba(Xp)[:, 1]  # P(churn | treated)
    p0 = m0.predict_proba(Xp)[:, 1]  # P(churn | not treated)
    uplift = p0 - p1                  # positive = treatment reduces churn

    result = df[["customerID"]].copy()
    result["p_churn_no_offer"] = p0
    result["p_churn_with_offer"] = p1
    result["uplift"] = uplift
    return result.sort_values("uplift", ascending=False)


if __name__ == "__main__":
    from src.pipeline.load_data import load_raw
    df = load_raw()
    results = estimate_uplift(df)
    print("Top uplift customers:")
    print(results.head(10))