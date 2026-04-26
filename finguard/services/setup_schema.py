import os
from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.generated.schema.entity.data.table import Table, Column, DataType
from metadata.generated.schema.api.data.createTable import CreateTableRequest
from metadata.generated.schema.api.lineage.addLineage import AddLineageRequest
from metadata.generated.schema.type.entityLineage import EntitiesEdge
from metadata.generated.schema.type.entityReference import EntityReference
from dotenv import load_dotenv

load_dotenv()

# Config
server_config = {
    "hostPort": "http://localhost:8585/api",
    "authConfig": {"jwtToken": os.getenv("OMD_TOKEN")}
}
metadata = OpenMetadata(config=server_config)

def create_table(name, description, columns):
    request = CreateTableRequest(
        name=name,
        description=description,
        columns=columns,
        databaseSchema="default.default.default" # Ensure this matches your service.schema
    )
    return metadata.create_or_update(request)

# --- TABLE DEFINITIONS ---

# 1. Raw Transactions (Source)
raw_cols = [
    Column(name="id", dataType=DataType.UUID),
    Column(name="user_id", dataType=DataType.INT),
    Column(name="amount", dataType=DataType.DECIMAL),
    Column(name="currency", dataType=DataType.STRING),
    Column(name="timestamp", dataType=DataType.TIMESTAMP),
]
t1 = create_table("raw_transactions", "Incoming payment source of truth", raw_cols)

# 2. Processed Transactions
proc_cols = [
    Column(name="id", dataType=DataType.UUID),
    Column(name="user_id", dataType=DataType.INT),
    Column(name="amount_usd", dataType=DataType.DECIMAL),
    Column(name="status", dataType=DataType.STRING),
]
t2 = create_table("processed_transactions", "Validated and normalized payments", proc_cols)

# 3. Fraud Scores
fraud_cols = [
    Column(name="transaction_id", dataType=DataType.UUID),
    Column(name="risk_score", dataType=DataType.INT),
    Column(name="flagged", dataType=DataType.BOOLEAN),
]
t3 = create_table("fraud_scores", "Real-time payment integrity signals", fraud_cols)

# 4. Reconciliation Reports
recon_cols = [
    Column(name="report_id", dataType=DataType.UUID),
    Column(name="total_volume", dataType=DataType.DECIMAL),
    Column(name="failed_transactions", dataType=DataType.INT),
    Column(name="timestamp", dataType=DataType.TIMESTAMP),
]
t4 = create_table("reconciliation_reports", "Statutory business ledger layer", recon_cols)

# --- LINEAGE (The Blast Radius) ---
# Raw -> Processed -> Fraud & Reconciliation
def link(from_node, to_node):
    edge = AddLineageRequest(
        edge=EntitiesEdge(
            fromEntity=EntityReference(id=from_node.id, type="table"),
            toEntity=EntityReference(id=to_node.id, type="table")
        )
    )
    metadata.add_lineage(edge)

link(t1, t2)
link(t2, t3)
link(t2, t4)

print(f" Schema Ready!")
print(f" TARGET TABLE ID (for Webhook Test): {t1.id}")