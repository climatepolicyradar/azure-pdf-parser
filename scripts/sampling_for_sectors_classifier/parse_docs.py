"""
Parse a selection of local PDFs, and store the results in S3

This script uses  the `azure_pdf_parser` CLI runner to parse a set of local pdf 
documents, and uploads the source folder and results to an AWS S3 bucket for later 
retrieval.

The script assumes that the PDFs are stored in a directory structure like this:
    
data/
└── pdfs/
    ├── source1/
    │   ├── abcdef.pdf
    │   └── ...
    ├── source2/
    │   ├── ghijkl.pdf
    │   └── ...
    └── ...

Make sure you've set up your AWS credentials for the labs profile by running
`aws sso login --profile labs` before running this script.

You'll also need a set of environment variables for the Azure API credentials:
AZURE_PROCESSOR_KEY
AZURE_PROCESSOR_ENDPOINT
"""

from pathlib import Path

import boto3
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import track

from azure_pdf_parser.run import run_parser

load_dotenv()

console = Console()

data_dir = Path("./data")
pdf_dir = data_dir / "pdfs"
if not pdf_dir.exists():
    raise FileNotFoundError(
        "The PDFs directory does not exist. "
        "Please create a directory called 'pdfs' in the 'data' directory."
    )
if not any(
    file.suffix == ".pdf" for sub_dir in pdf_dir.iterdir() for file in sub_dir.iterdir()
):
    raise FileNotFoundError(
        "The PDFs directory is empty. "
        "The 'pdfs' directory should contain subdirectories with PDFs to parse."
    )

# for pdf_source_directory in pdf_dir.iterdir():
pdf_source_directory = pdf_dir / "test"
console.print(f"📄 Parsing PDFs in {pdf_source_directory.name}")
output_dir = data_dir / "output" / pdf_source_directory.name
output_dir.mkdir(exist_ok=True, parents=True)
run_parser(pdf_dir=pdf_source_directory, output_dir=output_dir)

console.print("📄 All PDFs parsed successfully", style="green")

session = boto3.Session(profile_name="labs")
s3_client = session.client("s3", region_name="eu-west-1")
bucket_name = "cpr-sectors-classifier-sampling"
existing_buckets = [
    bucket["Name"] for bucket in s3_client.list_buckets().get("Buckets")
]
if bucket_name in existing_buckets:
    s3_client.delete_bucket(Bucket=bucket_name)
    console.print(f"🪣 Deleted existing AWS S3 bucket: {bucket_name}", style="green")
bucket = s3_client.create_bucket(
    Bucket=bucket_name, CreateBucketConfiguration={"LocationConstraint": "eu-west-1"}
)
console.print(f"🪣 Created new AWS S3 bucket: {bucket_name}", style="green")

file_paths = list(data_dir.rglob("*"))
for file_path in track(
    file_paths,
    description="☁️ Uploading data to AWS S3...",
    total=len(file_paths),
    transient=True,
):
    if file_path.is_file():
        with file_path.open("rb") as file:
            s3_client.upload_fileobj(
                file, bucket_name, str(file_path.relative_to(data_dir))
            )

console.print("☁️ All data uploaded successfully to AWS S3", style="green")
console.print(f"🔗 S3 bucket URL: https://{bucket_name}.s3.amazonaws.com/")
