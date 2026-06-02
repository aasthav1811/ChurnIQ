import pandas as pd
from src.config import RAW_DATA_PATH


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(RAW_DATA_PATH)
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"]).reset_index(drop=True)
    df["Churn"] = (df["Churn"] == "Yes").astype(int)
    return df


if __name__ == "__main__":
    df = load_raw()
    print(f"Shape: {df.shape}")
    print(f"Churn rate: {df['Churn'].mean():.2%}")
    print(df.head())
