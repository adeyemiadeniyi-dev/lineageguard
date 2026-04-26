def normalize_event(payload: dict):
    event_type = payload.get("eventType")
    entity_type = payload.get("entityType")

    if event_type != "entityUpdated" or entity_type != "table":
        return {"is_schema_change": False}

    change = payload.get("changeDescription", {})
    fields = change.get("fieldsUpdated", [])

    is_schema_change = any(f.get("name") == "columns" for f in fields)

    if not is_schema_change:
        return {"is_schema_change": False}

    entity = payload.get("entity", {})

    return {
        "is_schema_change": True,
        "table_name": entity.get("name")
    }