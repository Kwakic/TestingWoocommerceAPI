import json

from EcommerceAPI.plugins.entities import discover_entity_names

matrix = {
    "entity": discover_entity_names(),
}

print(json.dumps(matrix))
