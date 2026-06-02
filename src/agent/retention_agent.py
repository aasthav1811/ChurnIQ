from src.utils.llm import call_llm
from src.agent.intervention_logic import select_interventions
from src.explain.shap_explainer import explain_customer
import pandas as pd

PROMPT = """You are a customer retention specialist. Draft a short, warm, personalized
retention email (max 120 words) for the customer below.

Customer profile:
- Tenure: {tenure} months
- Monthly charges: ${monthly}
- Segment: {segment}
- Churn risk: {risk} ({proba:.0%})

Top reasons they may churn (from model analysis):
{shap_reasons}

Suggested interventions to weave in (pick the most relevant):
{interventions}

Constraints:
- Lead with empathy
- Reference their specific risk drivers naturally
- End with a clear, easy CTA
- No corporate jargon

Email:"""

def run_retention_agent(customer_row: pd.Series):
    df_one = pd.DataFrame([customer_row])
    shap_top = explain_customer(df_one, top_k=4)
    shap_text = "\n".join(
        f"- {s['feature']} (impact={s['shap_value']:+.3f})" for s in shap_top
    )
    interventions = select_interventions(
        customer_row["risk_band"],
        customer_row.get("segment", "Other"),
        customer_row["MonthlyCharges"],
    )
    prompt = PROMPT.format(
        tenure=customer_row["tenure"],
        monthly=customer_row["MonthlyCharges"],
        segment=customer_row.get("segment", "Other"),
        risk=customer_row["risk_band"],
        proba=customer_row["churn_probability"],
        shap_reasons=shap_text,
        interventions="\n".join(f"- {i}" for i in interventions),
    )
    email = call_llm(prompt, temperature=0.4)
    return {
        "email": email,
        "interventions": interventions,
        "shap_drivers": shap_top,
    }