import requests
from config import OMD_URL, OMD_TOKEN

HEADERS = {
    "Authorization": f"Bearer {OMD_TOKEN}",
    "Content-Type": "application/json"
}


def search_table_by_name(table_name: str):
    url = f"{OMD_URL}/search/query"

    params = {
        "q": f"name:{table_name}",
        "index": "table_search_index"
    }

    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print(f"❌ Search failed: {response.status_code}")
        print(response.text)
        return None

    data = response.json()
    hits = data.get("hits", {}).get("hits", [])

    if not hits:
        print("❌ No table found in search")
        return None

    table = hits[0]["_source"]

    print(f"✅ Found table: {table.get('fullyQualifiedName')}")

    return table


def get_fqn_from_table_search(table_name: str) -> str | None:
    table = search_table_by_name(table_name)

    if not table:
        return None

    return table.get("fullyQualifiedName")


def get_table_id_from_fqn(fqn: str) -> str | None:
    url = f"{OMD_URL}/tables/name/{fqn}"

    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"❌ Failed to fetch table: {response.status_code}")
        print(response.text)
        return None

    table = response.json()
    table_id = table.get("id")

    print(f"✅ Resolved UUID: {table_id}")

    return table_id


def get_lineage(table_id: str):
    url = f"{OMD_URL}/lineage/table/{table_id}"

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json()

    print(f"❌ Failed to fetch lineage: {response.status_code}")
    print(response.text)
    return None