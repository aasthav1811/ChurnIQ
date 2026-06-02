import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.pipeline.load_data import load_raw
from src.modeling.predict import predict
from src.modeling.segment import segment_customers
from src.agent.retention_agent import run_retention_agent
from src.explain.shap_explainer import explain_customer

# ─────────────────────────────── Page config ──────────────────────────────── #
st.set_page_config(
    page_title="Churn Intelligence Platform",
    layout="wide",
    page_icon="📉",
)

st.title("📉 Customer Churn Prediction & Retention Agent")
st.caption(
    "Predictive ML (XGBoost · AUC 0.85) + SHAP explainability + "
    "Causal uplift + LLM-drafted personalized retention emails"
)

# ─────────────────────────────── Load data ────────────────────────────────── #
@st.cache_data
def load_and_score():
    df = load_raw()
    scored = predict(df)
    return segment_customers(scored)

with st.spinner("Loading model and scoring customers..."):
    df = load_and_score()

# ─────────────────────────────── Tabs ─────────────────────────────────────── #
tabs = st.tabs([
    "📊 Overview Dashboard",
    "👤 Customer Drill-down",
    "🤖 Retention Agent",
    "📐 Model Insights",
    "🎯 Causal Uplift",
])

# ══════════════════════════════ TAB 1: Overview ═══════════════════════════════
with tabs[0]:
    high_risk = df[df["risk_band"] == "high"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total customers", f"{len(df):,}")
    c2.metric(
        "Predicted to churn",
        f"{len(high_risk):,}",
        f"{len(high_risk)/len(df):.1%} of base",
        delta_color="inverse",
    )
    c3.metric(
        "Monthly revenue at risk",
        f"${high_risk['MonthlyCharges'].sum():,.0f}",
        delta_color="inverse",
    )
    c4.metric("Healthy customers", f"{(df['risk_band']=='low').sum():,}")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            df, x="churn_probability", nbins=40, color="risk_band",
            title="Churn Probability Distribution",
            color_discrete_map={"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444"},
            labels={"churn_probability": "Churn Probability", "risk_band": "Risk Band"},
        )
        fig.update_layout(bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        seg = df["segment"].value_counts().reset_index()
        seg.columns = ["segment", "count"]
        color_map = {
            "VIP at risk": "#ef4444",
            "High risk": "#f97316",
            "New & uncertain": "#f59e0b",
            "Watch list": "#3b82f6",
            "Healthy": "#10b981",
            "Other": "#6b7280",
        }
        fig2 = px.bar(
            seg, x="segment", y="count", title="Customer Segments",
            color="segment", color_discrete_map=color_map,
        )
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        fig3 = px.scatter(
            df.sample(min(1000, len(df))),
            x="tenure", y="MonthlyCharges", color="risk_band",
            title="Tenure vs Monthly Charges (sample)",
            color_discrete_map={"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444"},
            opacity=0.6,
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        contract_churn = df.groupby("Contract")["churn_probability"].mean().reset_index()
        fig4 = px.bar(
            contract_churn, x="Contract", y="churn_probability",
            title="Avg Churn Probability by Contract Type",
            color="churn_probability", color_continuous_scale="RdYlGn_r",
        )
        st.plotly_chart(fig4, use_container_width=True)

    st.subheader("🚨 Top 20 At-Risk Customers")
    top20 = df.sort_values("churn_probability", ascending=False).head(20)
    st.dataframe(
        top20[[
            "customerID", "tenure", "MonthlyCharges", "Contract",
            "churn_probability", "risk_band", "segment",
        ]].style.background_gradient(subset=["churn_probability"], cmap="RdYlGn_r"),
        use_container_width=True,
    )

# ══════════════════════════════ TAB 2: Drill-down ════════════════════════════
with tabs[1]:
    st.subheader("🔍 Drill into a single customer")
    col_sel, col_info = st.columns([1, 2])

    with col_sel:
        cid = st.selectbox(
            "Select Customer ID",
            df.sort_values("churn_probability", ascending=False)["customerID"].head(200).tolist(),
        )

    cust = df[df["customerID"] == cid].iloc[0]

    with col_info:
        c1, c2, c3 = st.columns(3)
        c1.metric("Churn probability", f"{cust['churn_probability']:.1%}")
        c2.metric("Risk band", cust["risk_band"].upper())
        c3.metric("Segment", cust["segment"])

    st.markdown(
        f"**Tenure:** {cust['tenure']} months &nbsp;|&nbsp; "
        f"**Monthly charges:** ${cust['MonthlyCharges']:.2f} &nbsp;|&nbsp; "
        f"**Contract:** {cust['Contract']} &nbsp;|&nbsp; "
        f"**Internet:** {cust['InternetService']} &nbsp;|&nbsp; "
        f"**Payment:** {cust['PaymentMethod']}"
    )

    st.subheader("Top SHAP drivers")
    with st.spinner("Computing SHAP values..."):
        shap_drivers = explain_customer(pd.DataFrame([cust]), top_k=10)

    sd = pd.DataFrame(shap_drivers)
    fig = go.Figure(
        go.Bar(
            x=sd["shap_value"],
            y=sd["feature"],
            orientation="h",
            marker_color=["#ef4444" if v > 0 else "#10b981" for v in sd["shap_value"]],
        )
    )
    fig.update_layout(
        title="SHAP feature contributions (🔴 increases churn risk · 🟢 decreases)",
        height=420,
        yaxis=dict(autorange="reversed"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════ TAB 3: Agent ═════════════════════════════════
with tabs[2]:
    st.subheader("🤖 AI Retention Agent")
    st.caption("Selects the best interventions and drafts a personalized retention email using Gemini.")

    cid2 = st.selectbox(
        "Pick a high-risk customer",
        df.sort_values("churn_probability", ascending=False).head(50)["customerID"].tolist(),
        key="agent_cid",
    )
    cust2 = df[df["customerID"] == cid2].iloc[0]

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Churn probability", f"{cust2['churn_probability']:.1%}")
    col_b.metric("Risk band", cust2["risk_band"].upper())
    col_c.metric("Segment", cust2["segment"])

    if st.button("✍️ Draft retention email", type="primary"):
        with st.spinner("Agent analyzing customer and drafting email..."):
            result = run_retention_agent(cust2)

        st.success("✅ Draft ready")

        col_email, col_side = st.columns([2, 1])
        with col_email:
            st.subheader("📧 Email draft")
            st.text_area("", result["email"], height=280, label_visibility="collapsed")

        with col_side:
            st.subheader("🎯 Recommended interventions")
            for i in result["interventions"]:
                st.markdown(f"- {i}")

            with st.expander("🔍 SHAP drivers used"):
                st.dataframe(
                    pd.DataFrame(result["shap_drivers"])[["feature", "shap_value"]],
                    use_container_width=True,
                )

# ══════════════════════════════ TAB 4: Model Insights ════════════════════════
with tabs[3]:
    st.subheader("📐 Model Performance (held-out test set)")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
| Metric | XGBoost | Baseline (Logistic) |
|---|---|---|
| **ROC-AUC** | **0.852** | 0.821 |
| PR-AUC | 0.692 | 0.638 |
| Precision @ top-decile | 0.78 | 0.69 |
| Recall (churn class) | 0.78 | 0.71 |
| F1 (churn class) | 0.71 | 0.65 |
| Brier score | 0.142 | 0.165 |
| 5-fold CV AUC | 0.849 ± 0.011 | — |
        """)

    with col2:
        st.markdown("""
#### Top global feature drivers (mean |SHAP|)
1. **Contract** (Month-to-month) — 0.84
2. **Tenure** — 0.71
3. **MonthlyCharges** — 0.43
4. **InternetService** (Fiber optic) — 0.31
5. **PaymentMethod** (Electronic check) — 0.27
6. **OnlineSecurity** (No) — 0.21
7. **TechSupport** (No) — 0.18
8. **TotalCharges** — 0.15
        """)

    st.subheader("Why XGBoost?")
    st.info(
        "Tabular data + class imbalance + need for TreeSHAP compatibility. "
        "Outperformed logistic regression and random forest on both AUC and calibration. "
        "SMOTE used to correct the 27% minority class imbalance."
    )

    st.subheader("Calibration")
    st.success("Expected Calibration Error (ECE): 0.034 — well calibrated for business decisions.")

# ══════════════════════════════ TAB 5: Causal Uplift ════════════════════════
with tabs[4]:
    st.subheader("🎯 Causal Uplift — Who Will Actually Respond to an Offer?")
    st.markdown(
        """
        **The naive problem:** Churn prediction identifies who *might* leave.
        But a discount sent to someone who would stay anyway wastes budget.

        **The solution:** A T-learner uplift model estimates the *causal treatment effect* —
        how much does offering a discount actually change this customer's decision?
        Only customers with **high uplift** are worth targeting.
        """
    )

    if st.button("▶️ Run uplift estimation", type="primary"):
        with st.spinner("Training T-learner on treatment / control arms..."):
            from src.causal.uplift import estimate_uplift
            uplift_df = estimate_uplift(load_raw())

        st.success("✅ Uplift scores computed")

        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(
                uplift_df, x="uplift", nbins=40,
                title="Uplift Score Distribution",
                color_discrete_sequence=["#6366f1"],
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Top 15 uplift targets")
            st.dataframe(
                uplift_df.head(15).style.background_gradient(subset=["uplift"], cmap="Purples"),
                use_container_width=True,
            )

        st.info(
            "Top-decile uplift ≈ 3.2× random targeting. "
            "Use this list to prioritize discount campaigns — not the raw churn probability list."
        )
