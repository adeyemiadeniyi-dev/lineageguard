import asyncio
import json
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse

# =========================
# Internal Imports
# =========================
from handlers.webhook_handler import normalize_event
from services.openmetadata import (
    get_fqn_from_table_search,
    get_table_id_from_fqn,
    get_lineage
)
from utils.lineage_parser import extract_downstream_tables
from services.risk_engine import (
    calculate_risk_score,
    classify_risk,
    estimate_financial_risk
)
from services.ai_agent import generate_ai_insight

# =========================
# App Init & State
# =========================
app = FastAPI()

# 🔥 Global Event Queue for Real-Time UI updates
ui_queue = asyncio.Queue()

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Static Dashboard
# =========================
# Ensure the "dashboard" directory exists before mounting
if not os.path.exists("dashboard"):
    os.makedirs("dashboard")

app.mount("/dashboard", StaticFiles(directory="dashboard"), name="dashboard")

@app.get("/")
def serve_dashboard():
    return FileResponse(os.path.join("dashboard", "index.html"))

# =========================
# Real-Time Event Stream (SSE)
# =========================
@app.get("/api/events")
async def event_stream(request: Request):
    """
    The dashboard connects to this endpoint to receive live risk updates.
    """
    async def event_generator():
        while True:
            # If the connection is closed, stop sending events
            if await request.is_disconnected():
                break
                
            # Wait for a new event from the webhook listener
            event_data = await ui_queue.get()
            yield f"data: {json.dumps(event_data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# =========================
# Health Check
# =========================
@app.get("/health")
def health():
    return {"status": "ok"}

# =========================
# Webhook Endpoint
# =========================
@app.post("/webhook")
async def webhook_listener(request: Request):
    try:
        payload = await request.json()
        print("\n📩 Incoming webhook:", payload)

        # Normalize Event
        event = normalize_event(payload)

        if not event.get("is_schema_change"):
            return {"status": "ignored"}

        table_name = event.get("table_name")
        if not table_name:
            return {"status": "invalid_table_name"}

        print(f"🚨 Schema change detected: {table_name}")

        # Fetch Metadata
        fqn = get_fqn_from_table_search(table_name)
        if not fqn:
            print("❌ No table found in search")
            return {"status": "no_metadata", "table": table_name}

        print(f"🔎 FQN: {fqn}")
        table_id = get_table_id_from_fqn(fqn)

        if not table_id:
            return {"status": "table_not_found", "fqn": fqn}

        print(f"🆔 UUID: {table_id}")
        lineage = get_lineage(table_id)

        if not lineage:
            return {"status": "no_lineage", "fqn": fqn}

        print("✅ Lineage fetched")
        downstream = extract_downstream_tables(lineage)
        print(f"📊 Downstream: {downstream}")

        # REAL RISK ENGINE
        risk_score = calculate_risk_score(downstream)
        risk = classify_risk(risk_score)
        financial_risk = estimate_financial_risk(risk_score)

        print(f"📊 Risk Score: {risk_score} | ⚠️ Risk: {risk} | 💰 Finance: {financial_risk}")

        # AI INSIGHT (NVIDIA NIM)
        ai_insight = generate_ai_insight(
            table_name=table_name,
            downstream_tables=downstream,
            risk=risk,
            financial_risk=financial_risk
        )

        # Build Final Package
        final_report = {
            "status": "processed",
            "table": table_name,
            "fqn": fqn,
            "risk_score": risk_score,
            "risk": risk,
            "financial_risk": financial_risk,
            "downstream_tables": downstream,
            "ai_insight": ai_insight
        }

        # 🔥 Push to the UI Queue so the Dashboard updates instantly
        await ui_queue.put(final_report)

        return final_report

    except Exception as e:
        print("❌ WEBHOOK ERROR:", str(e))
        return {
            "status": "error",
            "message": str(e)
        }