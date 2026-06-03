import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from src.pipeline.load_data import load_raw
from src.modeling.predict import predict
from src.modeling.segment import segment_customers
from src.explain.shap_explainer import explain_customer
from src.agent.retention_agent import run_retention_agent

# ── Cache scored data at startup so every request is instant ──
_cache: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading and scoring all customers...")
    df = segment_customers(predict(load_raw()))
    _cache["df"] = df
    print(f"Ready — {len(df):,} customers scored.")
    yield

app = FastAPI(title="ChurnIQ API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helpers ──────────────────────────────────────────────────
def get_df() -> pd.DataFrame:
    if "df" not in _cache:
        raise HTTPException(status_code=503, detail="Data not loaded yet")
    return _cache["df"]


# ── Routes ───────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "customers_loaded": len(_cache.get("df", []))}


@app.get("/dashboard")
def dashboard():
    """KPI summary + segment breakdown + top 20 at-risk customers."""
    df = get_df()
    high = df[df["risk_band"] == "high"]
    med  = df[df["risk_band"] == "medium"]
    low  = df[df["risk_band"] == "low"]

    segment_counts = df["segment"].value_counts().to_dict()
    contract_risk  = (
        df.groupby("Contract")["churn_probability"]
        .mean()
        .round(4)
        .to_dict()
    )

    # Histogram buckets (20 bins 0→1)
    import numpy as np
    counts, edges = np.histogram(df["churn_probability"], bins=20, range=(0, 1))
    histogram = [
        {"bucket": round(float(edges[i]), 2), "count": int(counts[i]),
         "risk": "low" if edges[i] < 0.3 else "medium" if edges[i] < 0.6 else "high"}
        for i in range(len(counts))
    ]

    top20 = (
        df.sort_values("churn_probability", ascending=False)
        .head(20)[["customerID","tenure","MonthlyCharges","Contract",
                   "InternetService","churn_probability","risk_band","segment"]]
        .round({"churn_probability": 4})
        .to_dict(orient="records")
    )

    # Scatter sample (800 points)
    scatter = (
        df.sample(min(800, len(df)), random_state=42)
        [["tenure","MonthlyCharges","risk_band"]]
        .to_dict(orient="records")
    )

    return {
        "kpis": {
            "total_customers":   int(len(df)),
            "high_risk_count":   int(len(high)),
            "high_risk_pct":     round(len(high)/len(df), 4),
            "medium_risk_count": int(len(med)),
            "low_risk_count":    int(len(low)),
            "revenue_at_risk":   round(float(high["MonthlyCharges"].sum()), 2),
        },
        "segment_counts":  segment_counts,
        "contract_risk":   contract_risk,
        "histogram":       histogram,
        "scatter_sample":  scatter,
        "top20":           top20,
    }


@app.get("/customers")
def list_customers(limit: int = 50, risk: str = "high"):
    """Return top N customers filtered by risk band."""
    df = get_df()
    filtered = (
        df[df["risk_band"] == risk]
        .sort_values("churn_probability", ascending=False)
        .head(limit)[["customerID","tenure","MonthlyCharges",
                      "churn_probability","risk_band","segment"]]
        .round({"churn_probability": 4})
    )
    return filtered.to_dict(orient="records")


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str):
    """Single customer profile + SHAP drivers."""
    df = get_df()
    rows = df[df["customerID"] == customer_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail="Customer not found")
    cust = rows.iloc[0]
    shap_drivers = explain_customer(pd.DataFrame([cust]), top_k=10)
    return {
        "profile": {
            "customerID":    cust["customerID"],
            "tenure":        int(cust["tenure"]),
            "MonthlyCharges":float(cust["MonthlyCharges"]),
            "TotalCharges":  float(cust["TotalCharges"]),
            "Contract":      cust["Contract"],
            "InternetService":cust["InternetService"],
            "PaymentMethod": cust["PaymentMethod"],
            "churn_probability": round(float(cust["churn_probability"]), 4),
            "risk_band":     cust["risk_band"],
            "segment":       cust["segment"],
        },
        "shap_drivers": shap_drivers,
    }


@app.post("/customers/{customer_id}/agent")
def run_agent(customer_id: str):
    """Generate personalized retention email for a customer."""
    df = get_df()
    rows = df[df["customerID"] == customer_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail="Customer not found")
    cust = rows.iloc[0]
    result = run_retention_agent(cust)
    return {
        "customerID":    customer_id,
        "email":         result["email"],
        "interventions": result["interventions"],
        "shap_drivers":  result["shap_drivers"],
    }
