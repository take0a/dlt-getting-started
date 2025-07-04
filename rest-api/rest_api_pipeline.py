import dlt
from dlt.sources.rest_api import rest_api_source


pokemon_source = rest_api_source(
    {
        "client": {
            "base_url": "https://pokeapi.co/api/v2/",
        },
        "resource_defaults": {
            "endpoint": {
                "params": {
                    "limit": 1000,
                },
            },
        },
        "resources": [
            "pokemon",
            "berry",
            "location",
        ],
    }
)

pipeline = dlt.pipeline(
    pipeline_name="rest_api_pokemon",
    destination="duckdb",
    dataset_name="rest_api_data",
)

load_info = pipeline.run(pokemon_source)
print(load_info)
