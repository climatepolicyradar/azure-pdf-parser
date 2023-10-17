import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Union, Callable

import click
from azure.ai.formrecognizer import AnalyzeResult
from azure.core.exceptions import HttpResponseError
from cpr_data_access.parser_models import BackendDocument, ParserInput
from dotenv import load_dotenv, find_dotenv
from tqdm.auto import tqdm

from src.azure_pdf_parser import AzureApiWrapper
from src.azure_pdf_parser.convert import azure_api_response_to_parser_output

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

AZURE_PROCESSOR_KEY = os.environ.get("AZURE_PROCESSOR_KEY")
AZURE_PROCESSOR_ENDPOINT = os.environ.get("AZURE_PROCESSOR_ENDPOINT")


def process_document(
    document_parameter: Union[str, bytes, None],
    process_callable: Callable,
    process_callable_retry: Callable,
) -> Union[AnalyzeResult, None]:
    """Attempt to retrieve an analyze result for a document."""
    try:
        return process_callable(document_parameter)
    except HttpResponseError:
        try:
            return process_callable_retry(document_parameter)[1]
        except Exception:
            return None


def convert_and_save_api_response(
    import_id: str,
    source_url: Union[str, None],
    api_response: AnalyzeResult,
    output_dir: Path,
) -> None:
    """Convert Azure API response to parser output and save to disk."""

    backend_document = BackendDocument(
        name="",
        description="",
        import_id=import_id,
        family_import_id="",
        family_slug="",
        slug="",
        publication_ts=datetime(1900, 1, 1),
        source_url=source_url or "",
        download_url=None,
        type="",
        source="",
        category="",
        geography="",
        languages=[],
        metadata={},
    )

    parser_input = ParserInput(
        document_id=import_id,
        document_name="",
        document_description="",
        document_source_url=source_url or "",
        document_cdn_object="",
        document_content_type="application/pdf",
        document_md5_sum="",
        document_slug="",
        document_metadata=backend_document,
    )

    parser_output = azure_api_response_to_parser_output(
        parser_input=parser_input,
        md5_sum="",
        api_response=api_response,
        experimental_extract_tables=True,
    )

    (output_dir / f"{import_id}.json").write_text(parser_output.json())

    LOGGER.info(f"Successfully processed and saved {import_id}.")


@click.command()
@click.option(
    "--source-url",
    help="Source url with the associated document id to process.",
    required=False,
    multiple=True,
    type=click.Tuple([str, str]),
)
@click.option(
    "--pdf-dir",
    help="Path to dir containing pdfs to process with document id's as filenames.",
    required=False,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--output-dir",
    help="""Path to directory to write output JSONs to. Filenames and document IDs are 
    be the filenames of the PDFs without extensions. Directory will be created if it 
    doesn't exist.""",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
)
def cli(source_url: tuple[str, str], pdf_dir: Path, output_dir: Path):
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

    if not source_url and not pdf_dir:
        raise ValueError("""Must provide either source urls or pdf directory.""")

    azure_client = AzureApiWrapper(AZURE_PROCESSOR_KEY, AZURE_PROCESSOR_ENDPOINT)

    if source_url:
        for import_id, url in source_url:
            analyse_result = process_document(
                document_parameter=url,
                process_callable=azure_client.analyze_document_from_url,
                process_callable_retry=azure_client.analyze_large_document_from_url,
            )

            if analyse_result:
                convert_and_save_api_response(
                    import_id=import_id,
                    source_url=url,
                    api_response=analyse_result,
                    output_dir=output_dir,
                )
    if pdf_dir:
        for pdf_path in tqdm(list(pdf_dir.glob("*.pdf"))):
            pdf_bytes = pdf_path.read_bytes()

            analyse_result = process_document(
                document_parameter=pdf_bytes,
                process_callable=azure_client.analyze_document_from_bytes,
                process_callable_retry=azure_client.analyze_large_document_from_bytes,
            )

            if analyse_result:
                # Source url cannot be None and must have a minimum length.
                convert_and_save_api_response(
                    import_id=pdf_path.stem,
                    source_url="https://example.com/",
                    api_response=analyse_result,
                    output_dir=output_dir,
                )


if __name__ == "__main__":
    cli()
