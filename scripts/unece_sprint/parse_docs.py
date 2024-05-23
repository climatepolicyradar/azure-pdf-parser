"""
Download and parse a selection of PDFs for the UNECE sprint, and store the results in S3

This script downloads a selection of PDFs from a variety of sources, parses them using
the `azure_pdf_parser` CLI runner, and uploads the results to an AWS S3 bucket.

Make sure you've set up your AWS credentials for the labs profile by running
`aws sso login --profile labs` before running this script.
"""

from pathlib import Path

import boto3
import httpx
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, track

from azure_pdf_parser.run import run_parser

load_dotenv()

console = Console()


# Set up the data directory and URLs to download
def recursive_delete(path: Path):
    if path.exists():
        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                recursive_delete(child)
        path.rmdir()


data_dir = Path("./data")

with console.status("📂 Setting up data directory"):
    recursive_delete(data_dir)
    pdf_dir = data_dir / "pdfs"
    pdf_dir.mkdir(exist_ok=True, parents=True)

console.print("📂 Data directory is ready", style="green")

pdf_source_urls = {
    "OSCE": [
        "https://www.osce.org/files/f/documents/f/f/561811.pdf",
        "https://www.osce.org/files/f/documents/8/8/513787_0.pdf",
        "https://www.osce.org/files/f/documents/a/d/242651.pdf",
    ],
    "WMO": [
        "https://library.wmo.int/viewer/68891/download?file=1351_State_of_the_Climate_in_LAC_2023_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/68890/download?file=1350_State-of-the-Climate-in-Asia-2023.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/68887/download?file=ESOTC_2023_Summary_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/68835/download?file=1347_Global-statement-2023_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/66273/download?file=1312_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/68235/download?file=United+in+Science+2023_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/68473/download?file=1333_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/68576/download?file=WMO-IRENA_2023_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/68532/download?file=GHG-19_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/68585/download?file=1338_Decadal_State_Climate-HG_en.pdf&type=pdf&navigator=1",
        "https://library.wmo.int/viewer/58116/download?file=1301_WMO_Climate_services_Energy_en.pdf&type=pdf&navigator=1",
    ],
    "IAEA": [
        "https://www.iaea.org/sites/default/files/iaea-ccnp2022-body-web.pdf",
        "https://www.iaea.org/sites/default/files/22/10/nuclear-science-and-technology-for-climate-change-mitigation-adaptation-and-monitoring.pdf",
        "https://www.iaea.org/sites/default/files/21/10/nuclear-energy-for-a-net-zero-world.pdf",
        "https://www.iaea.org/sites/default/files/21/06/transitions-to-low-carbon-electricity-systems-changing-course-in-a-post-pandemic-world.pdf",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/PUB1911_web.pdf",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/PAT-003_web.pdf",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/PAT-004_web.pdf",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/PAT-002_web.pdf",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/PUB2041_web.pdf",
        "https://www-pub.iaea.org/MTCD/Publications/PDF/p15664-PAT_006_G20_web.pdf",
    ],
    "IEA": [
        "https://iea.blob.core.windows.net/assets/86ede39e-4436-42d7-ba2a-edf61467e070/WorldEnergyOutlook2023.pdf",
        "https://iea.blob.core.windows.net/assets/cb39c1bf-d2b3-446d-8c35-aae6b1f3a4a0/BatteriesandSecureEnergyTransitions.pdf",
        "https://iea.blob.core.windows.net/assets/f63eebbc-a3df-4542-b2fb-364dd66a2199/AVisionforCleanCookingAccessforAll.pdf",
        "https://iea.blob.core.windows.net/assets/9a698da4-4002-4e53-8ef3-631d8971bf84/NetZeroRoadmap_AGlobalPathwaytoKeepthe1.5CGoalinReach-2023Update.pdf",
        "https://iea.blob.core.windows.net/assets/96d66a8b-d502-476b-ba94-54ffda84cf72/Renewables_2023.pdf",
        "https://iea.blob.core.windows.net/assets/dfd9134f-12eb-4045-9789-9d6ab8d9fbf4/EnergyEfficiency2023.pdf",
        "https://iea.blob.core.windows.net/assets/33e2badc-b839-4c18-84ce-f6387b3c008f/CO2Emissionsin2023.pdf",
        "https://iea.blob.core.windows.net/assets/ee01701d-1d5c-4ba8-9df6-abeeac9de99a/GlobalCriticalMineralsOutlook2024.pdf",
        "https://www.iea.org/commentaries/climate-resilience-is-key-to-energy-transitions-in-the-middle-east-and-north-africa",
        "https://iea.blob.core.windows.net/assets/ea2ff609-8180-4312-8de9-494bcf21696d/ElectricityGridsandSecureEnergyTransitions.pdf",
        "https://iea.blob.core.windows.net/assets/1055131a-8dc4-488b-9e9e-7eb4f72bf7ad/LatinAmericaEnergyOutlook.pdf",
        "https://iea.blob.core.windows.net/assets/f065ae5e-94ed-4fcb-8f17-8ceffde8bdd2/TheOilandGasIndustryinNetZeroTransitions.pdf",
        "https://unfccc.int/sites/default/files/resource/cma2023_16a01E.pdf",
        "https://iea.blob.core.windows.net/assets/dfd9134f-12eb-4045-9789-9d6ab8d9fbf4/EnergyEfficiency2023.pdf",
        "https://iea.blob.core.windows.net/assets/4616ca1a-33a1-46be-80a9-e52ed40997a7/AcceleratingJustTransitionsfortheCoalSector-WEOSpecialReport.pdf",
        "https://iea.blob.core.windows.net/assets/227da10f-c527-406d-b94f-dbaa38ae9abb/ReducingtheCostofCapital.pdf",
        "https://iea.blob.core.windows.net/assets/8834d3af-af60-4df0-9643-72e2684f7221/WorldEnergyInvestment2023.pdf",
        "https://iea.blob.core.windows.net/assets/86ede39e-4436-42d7-ba2a-edf61467e070/WorldEnergyOutlook2023.pdf",
        "https://iea.blob.core.windows.net/assets/ba1eab3e-8e4c-490c-9983-80601fa9d736/World_Energy_Employment_2023.pdf",
        "https://iea.blob.core.windows.net/assets/ecdfc3bb-d212-4a4c-9ff7-6ce5b1e19cef/GlobalHydrogenReview2023.pdf",
        "https://iea.blob.core.windows.net/assets/016228e1-42bd-4ca7-bad9-a227c4a40b04/NuclearPowerandSecureEnergyTransitions.pdf",
        "https://iea.blob.core.windows.net/assets/a9e3544b-0b12-4e15-b407-65f5c8ce1b5f/GlobalEVOutlook2024.pdf",
    ],
}

html_source_urls = {
    "IEA": [
        "https://www.iea.org/commentaries/climate-resilience-is-key-to-energy-transitions-in-the-middle-east-and-north-africa",
        "https://www.iea.org/reports/climate-resilience-for-energy-transition-in-egypt",
        "https://www.iea.org/reports/climate-resilience-for-energy-transition-in-morocco",
        "https://www.iea.org/reports/climate-resilience-for-energy-transition-in-oman",
        "https://www.iea.org/reports/climate-resilience-policy-indicator",
        "https://www.iea.org/reports/belgium-climate-resilience-policy-indicator",
        "https://www.iea.org/reports/tracking-clean-energy-progress-2023",
        "https://www.iea.org/data-and-statistics/data-tools/renewable-energy-progress-tracker",
        "https://www.iea.org/reports/energy-efficiency-the-decade-for-action/energy-efficiency-policy-toolkit-2023-from-sonderborg-to-versailles",
        "https://www.iea.org/data-and-statistics/data-tools/global-observatory-on-people-centred-clean-energy-transitions",
        "https://www.iea.org/reports/global-methane-tracker-2024",
    ]
}

n_html_urls = sum(len(v) for v in html_source_urls.values())
console.print(f"📚 Number of HTML URLs: {n_html_urls}")

n_pdf_urls = sum(len(v) for v in pdf_source_urls.values())
console.print(f"📚 Number of PDF URLs: {n_pdf_urls}")

console.print(
    "⚠️ Ignoring HTML URLs for now, as they can't be easily parsed", style="yellow"
)

progress = Progress(transient=True)
task = progress.add_task("📄 Downloading pdfs...", total=n_pdf_urls)
progress.start()

# Disable SSL verification to avoid certificate issues
client = httpx.Client(verify=False)  # trunk-ignore(bandit/B501)
for source, urls in pdf_source_urls.items():
    source_dir = pdf_dir / source
    source_dir.mkdir(exist_ok=True)
    for url in urls:
        response = client.get(url)
        response.raise_for_status()
        # the source documents are not uniquely named, so we use the hash of the URL
        file_name = str(hash(url)) + ".pdf"
        file_path = source_dir / file_name
        with file_path.open("wb") as file:
            file.write(response.content)
        progress.advance(task)
progress.stop()

console.print("📄 All PDFs downloaded successfully", style="green")


for pdf_source_directory in pdf_dir.iterdir():
    console.print(f"📄 Parsing PDFs in {pdf_source_directory.name}")
    output_dir = data_dir / "output" / pdf_source_directory.name
    output_dir.mkdir(exist_ok=True, parents=True)
    run_parser(pdf_dir=pdf_source_directory, output_dir=output_dir)

console.print("📄 All PDFs parsed successfully", style="green")

session = boto3.Session(profile_name="labs")
s3_client = session.client("s3", region_name="eu-west-1")
bucket_name = "cpr-unece-sprint"
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
