import dlt
from dlt.sources.filesystem import filesystem, read_csv

files = filesystem(bucket_url="gs://filesystem-tutorial", file_glob="encounters*.csv")
reader = (files | read_csv()).with_name("encounters")
pipeline = dlt.pipeline(
    pipeline_name="hospital_data_pipeline",
    dataset_name="hospital_data",
    destination="duckdb",
)

info = pipeline.run(reader)
print(info)
