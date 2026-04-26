def classify_risk(table_name, downstream_tables):
    critical_tables = [
        "fraud_scores",
        "reconciliation_reports",
        "payment_settlements"
    ]

    # 🔥 Critical system impact
    if any(t in downstream_tables for t in critical_tables):
        return "HIGH"

    # 🔥 Large blast radius
    if len(downstream_tables) >= 3:
        return "HIGH"

    if len(downstream_tables) == 2:
        return "MEDIUM"

    return "LOW"


def generate_business_impact(table_name: str, downstream_tables: list[str], risk: str) -> str:
    if "fraud_scores" in downstream_tables:
        if risk == "HIGH":
            return "🚨 HIGH RISK: Fraud detection pipeline impacted. Potential undetected fraud."
        return "⚠️ Fraud detection may degrade."

    if "reconciliation_reports" in downstream_tables:
        if risk == "HIGH":
            return "🚨 HIGH RISK: Financial reconciliation impacted. Possible reporting inconsistencies."
        return "⚠️ Financial reporting inconsistencies may occur."

    if risk == "HIGH":
        return f"🚨 HIGH RISK: Changes in '{table_name}' impact multiple systems."

    if risk == "MEDIUM":
        return f"⚠️ MEDIUM RISK: '{table_name}' may affect downstream pipelines."

    return f"ℹ️ LOW RISK: Limited impact from '{table_name}'."


def recommend_action(risk: str) -> str:
    if risk == "HIGH":
        return "🚨 Immediate action: Validate pipelines and notify stakeholders."

    if risk == "MEDIUM":
        return "⚠️ Review downstream transformations and validate outputs."

    return "ℹ️ Monitor system behavior."


def estimate_financial_risk(downstream_tables):
    if "fraud_scores" in downstream_tables:
        return "$100K+"

    if "reconciliation_reports" in downstream_tables:
        return "$50K - $100K"

    if len(downstream_tables) >= 3:
        return "$10K - $50K"

    return "$1K - $10K"