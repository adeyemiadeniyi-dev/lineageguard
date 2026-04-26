# LineageGuard

> OpenMetadata Hackathon Project — Combining lineage + event detection to map technical schema changes to business impact, enabling real-time decision making.

## 🌐 Live Demo

| Service | URL |
|---|---|
| Dashboard | https://lineageguard.tripleadev.com |
| Health Check | https://lineageguard.tripleadev.com/health |
| Webhook Endpoint | https://lineageguard.tripleadev.com/webhook |
| Live Event Stream (SSE) | https://lineageguard.tripleadev.com/api/events |

---

## 🏗️ Architecture

```
OpenMetadata (schema change event)
        │
        ▼
POST /webhook  ──▶  Normalize event
                        │
                        ▼
              OpenMetadata API
              (search → FQN → UUID → lineage)
                        │
                        ▼
              Risk Engine
              (score → classify → financial estimate)
                        │
                        ▼
              NVIDIA NIM (Llama 3.1 70B)
              (AI business impact insight)
                        │
                        ▼
              SSE Queue ──▶ /api/events ──▶ Live Dashboard
```

**Stack:**
- **finguard** — FastAPI app (Python 3.12)
- **OpenMetadata 1.12.5** — metadata + lineage platform
- **PostgreSQL** — OpenMetadata backend database
- **Elasticsearch** — OpenMetadata search index
- **Nginx** — reverse proxy with HTTPS (Let's Encrypt)
- **NVIDIA NIM** — Llama 3.1 70B for AI risk insights

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Live dashboard (HTML/JS) |
| `GET` | `/health` | Health check |
| `GET` | `/api/events` | SSE stream for real-time risk updates |
| `POST` | `/webhook` | Receives OpenMetadata change events |

### Webhook Payload Example

```json
{
  "eventType": "entityUpdated",
  "entityType": "table",
  "entity": { "name": "raw_transactions" },
  "changeDescription": {
    "fieldsUpdated": [{ "name": "columns" }]
  }
}
```

### Webhook Response Example

```json
{
  "status": "processed",
  "table": "raw_transactions",
  "fqn": "finguard.finance.ledger.raw_transactions",
  "risk_score": 4,
  "risk": "LOW",
  "financial_risk": "$1K - $10K",
  "downstream_tables": ["processed_transactions"],
  "ai_insight": {
    "business_impact": "Non-critical system impact...",
    "financial_risk": "$1K - $10K",
    "reasoning": "...",
    "confidence": 0.8,
    "recommended_action": "Medium priority review..."
  }
}
```

---

## 🚀 Running Locally

### Prerequisites
- Docker & Docker Compose
- Python 3.12
- Git

### 1. Clone the repo

```bash
git clone https://github.com/adeyemiadeniyi-dev/lineageguard.git
cd lineageguard
```

### 2. Start OpenMetadata stack

```bash
cd openmetadata-docker
docker compose -f docker-compose-postgres.yml pull
docker compose -f docker-compose-postgres.yml up -d
```

Wait ~2 minutes for all services to be healthy:

```bash
docker ps --format "table {{.Names}}\t{{.Status}}"
```

### 3. Get an OpenMetadata token

```bash
TOKEN=$(curl -s -X POST "http://localhost:8585/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@open-metadata.org\",\"password\":\"$(echo -n 'admin' | base64)\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('accessToken',''))")
```

### 4. Configure environment

```bash
cat > finguard/.env << EOF
OMD_URL=http://localhost:8585/api/v1
OMD_USERNAME=admin@open-metadata.org
OMD_PASSWORD=admin
OMD_TOKEN=$TOKEN
NVIDIA_API_KEY=your-nvidia-nim-api-key
EOF
```

### 5. Install Python dependencies and seed data

```bash
cd finguard
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install cachetools
.venv/bin/python services/populate_fin_data.py
```

### 6. Run the app

```bash
.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Visit http://localhost:8000

---

## ☁️ Production Deployment (AWS EC2)

### Server Details
- **Instance:** m7i-flex.large (2 vCPU, 8GB RAM)
- **OS:** Ubuntu 24.04 LTS
- **Region:** eu-north-1

### Initial Server Setup

```bash
# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update && sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin nginx certbot python3-certbot-nginx git python3.12-venv
sudo usermod -aG docker ubuntu && newgrp docker
```

### Deploy

```bash
git clone https://github.com/adeyemiadeniyi-dev/lineageguard.git
cd lineageguard

# Create .env
cat > finguard/.env << 'EOF'
OMD_URL=http://openmetadata-server:8585/api/v1
OMD_USERNAME=admin@open-metadata.org
OMD_PASSWORD=admin
OMD_TOKEN=placeholder
NVIDIA_API_KEY=your-nvidia-nim-api-key
EOF

# Start stack
docker compose -f openmetadata-docker/docker-compose-postgres.yml pull
docker compose -f openmetadata-docker/docker-compose-postgres.yml up -d

# Fix PostgreSQL permissions (first time only)
docker exec openmetadata_postgresql psql -U postgres -c "CREATE USER openmetadata_user WITH PASSWORD 'openmetadata_password';"
docker exec openmetadata_postgresql psql -U postgres -c "CREATE DATABASE openmetadata_db OWNER openmetadata_user;"
docker exec openmetadata_postgresql psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE openmetadata_db TO openmetadata_user;"
docker exec openmetadata_postgresql psql -U postgres -c "GRANT ALL ON SCHEMA public TO openmetadata_user;"
docker compose -f openmetadata-docker/docker-compose-postgres.yml up execute-migrate-all
docker compose -f openmetadata-docker/docker-compose-postgres.yml up -d
```

### Nginx + HTTPS Setup

```bash
sudo nano /etc/nginx/sites-available/lineageguard
# (paste the nginx config below)

sudo ln -s /etc/nginx/sites-available/lineageguard /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d lineageguard.tripleadev.com
```

**Nginx config:**

```nginx
server {
    listen 80;
    server_name lineageguard.tripleadev.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/events {
        proxy_pass http://localhost:8000/api/events;
        proxy_set_header Host $host;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
        chunked_transfer_encoding on;
    }

    location /openmetadata/ {
        proxy_pass http://localhost:8585/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Seed Financial Tables & Lineage

```bash
cd ~/lineageguard/finguard
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install cachetools

# Refresh token first (see below), then:
.venv/bin/python services/populate_fin_data.py
```

---

## 🔑 Token Refresh (Required Every Hour)

The OpenMetadata admin session token expires every hour. Run this command to refresh it and restart finguard:

```bash
TOKEN=$(curl -s -X POST "http://localhost:8585/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@open-metadata.org\",\"password\":\"$(echo -n 'admin' | base64)\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('accessToken',''))") \
&& sed -i "s|OMD_TOKEN=.*|OMD_TOKEN=$TOKEN|" ~/lineageguard/finguard/.env \
&& docker compose -f ~/lineageguard/openmetadata-docker/docker-compose-postgres.yml up -d --force-recreate finguard
```

> **Note for testers:** Run this command before testing the webhook if the server has been running for more than an hour.

---

## 🧪 Testing the Webhook

```bash
echo '{"eventType":"entityUpdated","entityType":"table","entity":{"name":"raw_transactions"},"changeDescription":{"fieldsUpdated":[{"name":"columns"}]}}' > /tmp/payload.json

curl -s -X POST https://lineageguard.tripleadev.com/webhook \
  -H "Content-Type: application/json" \
  -d @/tmp/payload.json
```

**Financial tables available for testing:**
- `raw_transactions` — source table (triggers full lineage blast radius)
- `processed_transactions` — downstream of raw_transactions
- `fraud_scores` — downstream of processed_transactions (HIGH risk)
- `reconciliation_reports` — downstream of processed_transactions (HIGH risk)

---

## 📁 Project Structure

```
lineageguard/
├── finguard/
│   ├── main.py                  # FastAPI app + endpoints
│   ├── config.py                # Env config
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── handlers/
│   │   └── webhook_handler.py   # Normalizes OM webhook events
│   ├── services/
│   │   ├── openmetadata.py      # OM API calls (search, lineage)
│   │   ├── risk_engine.py       # Risk scoring + classification
│   │   ├── ai_agent.py          # NVIDIA NIM integration
│   │   ├── prompts.py           # LLM prompt builder
│   │   └── populate_fin_data.py # Seeds OM with financial tables
│   ├── utils/
│   │   └── lineage_parser.py    # Extracts downstream tables
│   ├── simulator/
│   │   └── event_simulator.py   # Test webhook payload sender
│   └── dashboard/
│       ├── index.html           # Live risk dashboard
│       └── script.js
└── openmetadata-docker/
    └── docker-compose-postgres.yml  # Full OM stack
```

---

## 🔐 Environment Variables

| Variable | Description |
|---|---|
| `OMD_URL` | OpenMetadata API URL |
| `OMD_TOKEN` | Admin JWT token (expires every hour) |
| `NVIDIA_API_KEY` | NVIDIA NIM API key for Llama 3.1 70B |
