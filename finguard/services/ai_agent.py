# services/ai_agent.py

from openai import OpenAI
from config import NVIDIA_API_KEY
from services.prompts import build_risk_prompt

import json
import re


client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=NVIDIA_API_KEY
)


def _safe_parse_json(content: str) -> dict:
    if not content or not isinstance(content, str):
        return {
            "business_impact": "Empty AI response",
            "financial_risk": "unknown",
            "reasoning": "No content returned",
            "confidence": 0.0,
            "recommended_action": "retry or fallback"
        }

    clean = re.sub(r'[\x00-\x1F\x7F]', '', content)

    match = re.search(r'\{.*\}', clean, re.DOTALL)

    if match:
        try:
            return json.loads(match.group(0))
        except Exception as e:
            print("⚠️ JSON parse failed:", str(e))

    return {
        "business_impact": clean[:200],
        "financial_risk": "unknown",
        "reasoning": "Recovered from malformed AI output",
        "confidence": 0.3,
        "recommended_action": "manual review recommended"
    }


def generate_ai_insight(table_name: str, downstream_tables: list[str], risk: str, financial_risk: str) -> dict:
    prompt = build_risk_prompt(table_name, downstream_tables, risk, financial_risk)

    try:
        completion = client.chat.completions.create(
            model="meta/llama-3.1-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=200,
            response_format={"type": "json_object"}
        )

        content = completion.choices[0].message.content

        print("🧠 RAW AI OUTPUT:", content)

        return _safe_parse_json(content)

    except Exception as e:
        print("❌ AI ERROR:", str(e))

        return {
            "business_impact": "AI service unavailable",
            "financial_risk": financial_risk,
            "reasoning": str(e),
            "confidence": 0.0,
            "recommended_action": "fallback to rule-based system"
        }