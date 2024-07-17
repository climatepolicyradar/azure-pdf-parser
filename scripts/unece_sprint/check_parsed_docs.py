"""Check whether the UNECE documents can be loaded using the CPR SDK"""

import boto3
from cpr_sdk.parser_models import BaseParserOutput
from rich.console import Console

console = Console()


session = boto3.Session(profile_name="labs")
s3_client = session.client("s3", region_name="eu-west-1")
bucket_name = "cpr-unece-sprint"

# Check whether the bucket exists
s3_client.head_bucket(Bucket=bucket_name)
console.print(f"🪣 The '{bucket_name}' bucket exists", style="green")

# List the objects in the bucket and get the first key
response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="output")
keys = [obj["Key"] for obj in response["Contents"]]
key = keys[0]
console.print(f"📂 The bucket contains {len(keys)} json objects", style="green")

# Get a document from the bucket
response = s3_client.get_object(Bucket=bucket_name, Key=key)
console.print(f"📄 Got a document from the bucket: {key}", style="green")

# Check if the document can be loaded using the CPR SDK
document = BaseParserOutput.model_validate_json(response["Body"].read())
console.print("🥳 Document was successfully loaded by the CPR SDK", style="green")
