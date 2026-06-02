from src.config import INTERVENTIONS


def select_interventions(risk_band: str, segment: str, monthly_charges: float) -> list[str]:
    """
    Rule-based intervention selector.
    Combines base risk-band interventions with segment-specific overrides.
    """
    base = INTERVENTIONS.get(f"{risk_band}_risk", INTERVENTIONS["low_risk"])

    if segment == "VIP at risk":
        base = ["30% discount + premium upgrade", "Account exec call within 24h"] + base

    if segment == "New & uncertain":
        base = ["Onboarding office hours invite", "Tutorial email series"] + base

    if monthly_charges > 90 and risk_band == "high":
        base = ["Dedicated account review call"] + base

    return base
