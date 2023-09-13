import logging
import os
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv, find_dotenv
import click
from tqdm.auto import tqdm
from azure.core.exceptions import HttpResponseError
from cpr_data_access.parser_models import PDFData, ParserOutput, BackendDocument

from src.azure_pdf_parser import AzureApiWrapper
from src.azure_pdf_parser.convert import (
    extract_azure_api_response_paragraphs,
    extract_azure_api_response_page_metadata,
)

LOGGER = logging.getLogger(__name__)

AZURE_PROCESSOR_KEY = os.environ.get("AZURE_PROCESSOR_KEY")
AZURE_PROCESSOR_ENDPOINT = os.environ.get("AZURE_PROCESSOR_ENDPOINT")

empty_backend_document = BackendDocument(
    name="",
    description="",
    import_id="",
    family_import_id="",
    slug="",
    publication_ts=datetime(1900, 1, 1),
    source_url=None,
    download_url=None,
    type="",
    source="",
    category="",
    geography="",
    languages=[],
    metadata={},
)


@click.command()
@click.option(
    "--pdf-dir",
    help="Path to directory containing pdfs to process.",
    required=True,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--output-dir",
    help="""Path to directory to write output JSONs to. 
    Filenames and document IDs are be the filenames of the PDFs without extensions.
    Directory will be created if it doesn't exist.""",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
)
def cli(pdf_dir: Path, output_dir: Path):
    """
    Run Azure PDF parser on a directory of PDFs.

    Outputs 'blank' parser output jsons to `--output-dir`, with just
    document ID, document name, text block and page metadata information populated.
    """
    load_dotenv(find_dotenv())

    if not output_dir.exists():
        LOGGER.warning(f"Output directory {output_dir} does not exist. Creating.")
        output_dir.mkdir(parents=True)

    if not AZURE_PROCESSOR_KEY or not AZURE_PROCESSOR_ENDPOINT:
        raise ValueError(
            """Missing Azure API credentials. Set AZURE_PROCESSOR_KEY and 
            AZURE_PROCESSOR_ENDPOINT environment variables."""
        )

    azure_client = AzureApiWrapper(AZURE_PROCESSOR_KEY, AZURE_PROCESSOR_ENDPOINT)

    for pdf_path in tqdm(list(pdf_dir.glob("*.pdf"))):
        pdf_bytes = pdf_path.read_bytes()

        try:
            azure_response = azure_client.analyze_document_from_bytes(pdf_bytes)
        except HttpResponseError:
            LOGGER.error(
                f"""Error processing {pdf_path.name} as short document. 
                Trying again in individual pages."""
            )
            try:
                _, azure_response = azure_client.analyze_large_document_from_bytes(
                    pdf_bytes
                )
            except Exception:
                LOGGER.error(
                    f"Error processing {pdf_path.name} as individual pages. Skipping."
                )
                continue

        text_blocks = extract_azure_api_response_paragraphs(azure_response)
        page_metadata = extract_azure_api_response_page_metadata(azure_response)

        parser_output = (
            ParserOutput(
                document_id=pdf_path.stem,
                document_name=pdf_path.stem,
                document_cdn_object="",
                document_content_type="application/pdf",
                document_description="",
                document_metadata=empty_backend_document,
                document_md5_sum="",
                document_slug="",
                document_source_url="http://example.com",  # type: ignore
                pdf_data=PDFData(
                    text_blocks=text_blocks, page_metadata=page_metadata, md5sum=""
                ),
            )
            .detect_and_set_languages()
            .set_document_languages_from_text_blocks()
        )

        (output_dir / f"{pdf_path.stem}.json").write_text(parser_output.json())


if __name__ == "__main__":
    cli()
