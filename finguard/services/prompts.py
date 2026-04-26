# services/prompts.py

def build_risk_prompt(table_name: str, downstream_tables: list[str], risk: str, financial_risk: str) -> str:
    return f"""
You are an expert financial data risk expert. Your job is to analyze schema changes in a fintech environment.
If a change affects downstream tables like 'processed_transactions', 'fraud_scores' or 'reconciliation_reports', 
you MUST emphasize the high risk of regulatory non-compliance (SOX/GDPR) and potential financial loss. Do not be passive.

## CONTEXT
A schema change has occurred.

- Table: {table_name}
- Downstream systems: {downstream_tables}
- Risk level: {risk}
- Precomputed financial exposure: {financial_risk}

## DOMAIN CONTEXT
- System processes financial transactions
- Critical tables:
  - fraud_scores → fraud detection
  - reconciliation_reports → financial reporting

## CONSTRAINTS (STRICT)
- Use ONLY the provided downstream systems
- DO NOT mention fraud_scores or reconciliation_reports unless they appear in downstream_tables
- DO NOT invent new systems or impacts
- Use the provided financial_risk EXACTLY (do not modify it)  

## TASK
Provide a structured business decision.

## RULES
- Use the provided financial exposure EXACTLY (do not change it)
- Be specific and concise
- Use executive-level language
- Justify the risk classification
- No generic statements
- Use ONLY the provided downstream tables
- DO NOT mention systems not present in downstream list
- If fraud_scores or reconciliation_reports are NOT in downstream, do NOT reference them

## OUTPUT REQUIREMENTS
- business_impact:
  - Must clearly state whether critical systems are impacted or NOT
  - Avoid vague terms like "minimal" without explanation
  - Use decision-grade language (e.g., "non-critical system impact")

- reasoning:
  - Must justify the risk level using ONLY downstream systems
  - Be concise and factual

- recommended_action:
  - Must include priority level (e.g., Immediate, High, Medium, Low)
  - Must be actionable

- confidence:
  - Value between 0.0 and 1.0
  - Reflect certainty based on available context

## OUTPUT (STRICT JSON)

{{
  "business_impact": "...",
  "financial_risk": "{financial_risk}",
  "reasoning": "...",
  "confidence": 0.0,
  "recommended_action": "..."
}}
"""