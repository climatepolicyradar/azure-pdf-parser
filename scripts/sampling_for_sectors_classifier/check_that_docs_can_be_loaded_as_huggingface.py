"""
Check whether the parsed docs can be loaded as a huggingface dataset using the CPR SDK

- Downloads the data from AWS S3
- loads the documents as a huggingface dataset using the CPR SDK
"""

import json

import boto3
from cpr_data_access.models import BaseDocument, Dataset
from cpr_data_access.parser_models import BaseParserOutput
from numpy.random import choice
from rich.console import Console
from rich.progress import track

console = Console()


session = boto3.Session(profile_name="labs")
s3_client = session.client("s3", region_name="eu-west-1")
bucket_name = "cpr-sectors-classifier-sampling"

# Check whether the bucket exists
s3_client.head_bucket(Bucket=bucket_name)
console.print(f"🪣 The '{bucket_name}' bucket exists", style="green")

# List the objects in the bucket and get the first key
response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="output")
keys = [obj["Key"] for obj in response["Contents"]]
console.print(f"🔑 Found {len(keys)} keys in the bucket", style="green")

# randomly sample 20 keys
keys = choice(keys, 20, replace=False)

# get the documents from the bucket
documents = []
for key in track(keys, description="📄 Loading documents from S3...", transient=True):
    response = s3_client.get_object(Bucket=bucket_name, Key=key)
    parser_output_data = json.loads(response["Body"].read().decode("utf-8"))
    parser_output = BaseParserOutput(**parser_output_data)
    document = BaseDocument.from_parser_output(parser_output)
    documents.append(document)

console.print(
    f"📄 Loaded a sample of {len(documents)} documents from S3", style="green"
)

# Structure the documents as a dataset, and convert it to a huggingface dataset format
with console.status("Structuring the documents as a dataset..."):
    dataset = Dataset(documents=documents)
    hf_dataset = dataset.to_huggingface()

# print the columns of the dataset

console.print(
    f"✅ Successfully loaded {len(hf_dataset)} passages "
    f"from {len(documents)} documents as a huggingface dataset",
    style="green",
)
console.print("Columns:", style="bold blue")
console.print(hf_dataset.column_names)
