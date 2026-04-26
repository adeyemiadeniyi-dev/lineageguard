import os
from dotenv import load_dotenv

from metadata.ingestion.ometa.ometa_api import OpenMetadata
from metadata.generated.schema.entity.services.connections.metadata.openMetadataConnection import OpenMetadataConnection
from metadata.generated.schema.security.client.openMetadataJWTClientConfig import OpenMetadataJWTClientConfig
from metadata.generated.schema.api.data.createTable import CreateTableRequest
from metadata.generated.schema.api.data.createDatabase import CreateDatabaseRequest
from metadata.generated.schema.api.data.createDatabaseSchema import CreateDatabaseSchemaRequest
from metadata.generated.schema.api.services.createDatabaseService import CreateDatabaseServiceRequest
from metadata.generated.schema.api.lineage.addLineage import AddLineageRequest
from metadata.generated.schema.entity.data.table import Column, DataType
from metadata.generated.schema.entity.services.databaseService import DatabaseServiceType, DatabaseConnection
from metadata.generated.schema.entity.services.connections.database.customDatabaseConnection import CustomDatabaseConnection, CustomDatabaseType
from metadata.generated.schema.type.entityLineage import EntitiesEdge
from metadata.generated.schema.type.entityReference import EntityReference

load_dotenv()

token = os.getenv("OMD_TOKEN")

server_config = OpenMetadataConnection(
    hostPort="http://localhost:8585/api",
    securityConfig=OpenMetadataJWTClientConfig(jwtToken=token),
)

metadata = OpenMetadata(config=server_config)

# --- 1. Create Database Service ---
svc = metadata.create_or_update(CreateDatabaseServiceRequest(
    name="finguard",
    serviceType=DatabaseServiceType.CustomDatabase,
    connection=DatabaseConnection(config=CustomDatabaseConnection(type=CustomDatabaseType.CustomDatabase, sourcePythonClass="finguard")),
))

# --- 2. Create Database ---
db = metadata.create_or_update(CreateDatabaseRequest(
    name="finance",
    service=svc.fullyQualifiedName,
))

# --- 3. Create Schema ---
schema = metadata.create_or_update(CreateDatabaseSchemaRequest(
    name="ledger",
    database=db.fullyQualifiedName,
))

FQN = schema.fullyQualifiedName  # finguard.finance.ledger

def create_table(name, description, columns):
    return metadata.create_or_update(CreateTableRequest(
        name=name,
        description=description,
        columns=columns,
        databaseSchema=FQN,
    ))

def link(from_node, to_node):
    metadata.add_lineage(AddLineageRequest(
        edge=EntitiesEdge(
            fromEntity=EntityReference(id=from_node.id, type="table"),
            toEntity=EntityReference(id=to_node.id, type="table"),
        )
    ))

try:
    print("🏗️  Building Financial Ledger Infrastructure...")

    t1 = create_table("raw_transactions", "Source: Payment Gateway Inbound", [
        Column(name="id", dataType=DataType.UUID),
        Column(name="amount", dataType=DataType.DECIMAL),
        Column(name="currency", dataType=DataType.STRING),
    ])

    t2 = create_table("processed_transactions", "Normalized Financial Records", [
        Column(name="id", dataType=DataType.UUID),
        Column(name="amount_usd", dataType=DataType.DECIMAL),
        Column(name="status", dataType=DataType.STRING),
    ])

    t3 = create_table("fraud_scores", "Real-time Payment Integrity Monitor", [
        Column(name="transaction_id", dataType=DataType.UUID),
        Column(name="risk_score", dataType=DataType.INT),
    ])

    t4 = create_table("reconciliation_reports", "Statutory Audit Ledger", [
        Column(name="report_id", dataType=DataType.UUID),
        Column(name="total_volume", dataType=DataType.DECIMAL),
    ])

    print("🔗  Weaving Data Lineage...")
    link(t1, t2)
    link(t2, t3)
    link(t2, t4)

    print(f"\n✅ DATABASE READY")
    print(f"🚀 TARGET UUID (raw_transactions): {t1.id}")

except Exception as e:
    print(f"❌ Error during population: {e}")
