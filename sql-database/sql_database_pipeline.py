# flake8: noqa
import dlt
from dlt.sources.sql_database import sql_database


source = sql_database().with_resources("family", "genome")

pipeline = dlt.pipeline(
    pipeline_name="sql_to_duckdb_pipeline",
    destination="duckdb",
    dataset_name="sql_to_duckdb_pipeline_data",
)

load_info = pipeline.run(source)
print(load_info)
