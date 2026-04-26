import os
from dotenv import load_dotenv

# Main API
from metadata.ingestion.ometa.ometa_api import OpenMetadata

# Security & Connection
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import (
    OpenMetadataConnection,
)
from metadata.generated.schema.security.client.openMetadataJWTClientConfig import (
    OpenMetadataJWTClientConfig,
)

# Data & Lineage schemas
from metadata.generated.schema.api.data.createTable import CreateTableRequest
from metadata.generated.schema.api.lineage.addLineage import AddLineageRequest
from metadata.generated.schema.entity.data.table import Column, DataType
from metadata.generated.schema.type.entityLineage import EntitiesEdge
from metadata.generated.schema.type.entityReference import EntityReference

load_dotenv()

# --- 1. CONFIGURATION ---
token = os.getenv("OMD_TOKEN")

# We use OpenMetadataJWTClientConfig which is the standard for JWT tokens
server_config = OpenMetadataConnection(
    hostPort="http://localhost:8585/api",
    authConfig=OpenMetadataJWTClientConfig(jwtToken=token),
)

metadata = OpenMetadata(config=server_config)

# --- 2. HELPERS ---
def create_table(name, description, columns):
    # Using 'sample_data' service which is default in Docker
    request = CreateTableRequest(
        name=name,
        description=description,
        columns=columns,
        databaseSchema="sample_data.ecommerce.shopify" 
    )
    return metadata.create_or_update(request)

def link(from_node, to_node):
    edge = AddLineageRequest(
        edge=EntitiesEdge(
            fromEntity=EntityReference(id=from_node.id, type="table"),
            toEntity=EntityReference(id=to_node.id, type="table")
        )
    )
    metadata.add_lineage(edge)

# --- 3. RUN POPULATION ---
try:
    print("🏗️  Building Financial Ledger Infrastructure...")

    # 1. RAW LAYER
    t1 = create_table("raw_transactions", "Source: Payment Gateway Inbound", [
        Column(name="id", dataType=DataType.UUID),
        Column(name="amount", dataType=DataType.DECIMAL),
        Column(name="currency", dataType=DataType.STRING)
    ])

    # 2. PROCESSING LAYER
    t2 = create_table("processed_transactions", "Normalized Financial Records", [
        Column(name="id", dataType=DataType.UUID),
        Column(name="amount_usd", dataType=DataType.DECIMAL),
        Column(name="status", dataType=DataType.STRING)
    ])

    # 3. OBSERVABILITY LAYER (Health)
    t3 = create_table("fraud_scores", "Real-time Payment Integrity Monitor", [
        Column(name="transaction_id", dataType=DataType.UUID),
        Column(name="risk_score", dataType=DataType.INT)
    ])

    # 4. COMPLIANCE LAYER (Governance)
    t4 = create_table("reconciliation_reports", "Statutory Audit Ledger", [
        Column(name="report_id", dataType=DataType.UUID),
        Column(name="total_volume", dataType=DataType.DECIMAL)
    ])

    print("🔗  Weaving Data Lineage...")
    link(t1, t2)
    link(t2, t3)
    link(t2, t4)

    print(f"\n✅ DATABASE READY")
    print(f"🚀 TARGET UUID (raw_transactions): {t1.id}")

except Exception as e:
    print(f"❌ Error during population: {e}")