def extract_downstream_tables(lineage):
    if not lineage:
        return []

    nodes = lineage.get("nodes", [])

    tables = []

    for node in nodes:
        name = node.get("name")
        if name:
            tables.append(name)

    return list(set(tables))