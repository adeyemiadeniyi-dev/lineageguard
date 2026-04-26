CRITICAL_TABLES = {
    "payment_settlements": 5,
    "fraud_scores": 5,
    "reconciliation_reports": 5,
    "ledger_entries": 5
}

IMPORTANT_TABLES = {
    "processed_transactions": 3,
    "user_accounts": 3
}

LOW_TABLES = {
    "logs": 1,
    "analytics": 1
}


def get_table_weight(table_name: str) -> int:
    if table_name in CRITICAL_TABLES:
        return CRITICAL_TABLES[table_name]
    if table_name in IMPORTANT_TABLES:
        return IMPORTANT_TABLES[table_name]
    return 1


def calculate_risk_score(downstream_tables: list[str]) -> int:
    if not downstream_tables:
        return 1

    weights = [get_table_weight(t) for t in downstream_tables]

    # Key idea: highest impact dominates
    max_weight = max(weights)

    # Add blast radius effect
    breadth_bonus = min(len(downstream_tables), 5)

    return max_weight + breadth_bonus


def classify_risk(score: int) -> str:
    if score >= 8:
        return "HIGH"
    elif score >= 5:
        return "MEDIUM"
    return "LOW"


def estimate_financial_risk(score: int) -> str:
    if score >= 8:
        return "$100K+"
    elif score >= 5:
        return "$10K - $100K"
    return "$1K - $10K"