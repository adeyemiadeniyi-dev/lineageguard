import requests

url = "http://localhost:8000/webhook"

payload = {
    "eventType": "entityUpdated",
    "entityType": "table",
    "entity": {
        "name": "raw_transactions"
    },
    "changeDescription": {
        "fieldsUpdated": [
            {"name": "columns"}
        ]
    }
}

response = requests.post(url, json=payload)

print("Status Code:", response.status_code)
print("Raw Response:", response.text)

try:
    print("JSON:", response.json())
except:
    print("⚠️ Not JSON")