import pandas as pd


def segment_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    conditions = [
        (df["risk_band"] == "high") & (df["MonthlyCharges"] > 70),
        (df["risk_band"] == "high"),
        (df["risk_band"] == "medium") & (df["tenure"] < 12),
        (df["risk_band"] == "medium"),
        (df["risk_band"] == "low"),
    ]
    segments = [
        "VIP at risk",
        "High risk",
        "New & uncertain",
        "Watch list",
        "Healthy",
    ]
    df["segment"] = "Other"
    for cond, seg in zip(conditions, segments):
        df.loc[cond, "segment"] = seg
    return df
