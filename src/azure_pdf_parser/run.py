import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Union, Callable, Optional, Iterable
import json

from azure.ai.formrecognizer import AnalyzeResult
from azure.core.exceptions import HttpResponseError
from cpr_data_access.parser_models import BackendDocument, ParserInput
from dotenv import load_dotenv, find_dotenv
from tqdm.auto import tqdm

from azure_pdf_parser import AzureApiWrapper
from azure_pdf_parser.convert import azure_api_response_to_parser_output

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

load_dotenv(find_dotenv())

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
    api_response: AnalyzeResult,
    output_dir: Path,
    source_url: Optional[str] = None,
    extract_tables: bool = False,
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
        source_url=source_url,
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
        document_source_url=source_url,
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
        experimental_extract_tables=extract_tables,
    )

    (output_dir / f"{import_id}.json").write_text(parser_output.model_dump_json())

    LOGGER.info(f"Successfully processed and saved {import_id}.")


def run_parser(
    output_dir: Path,
    ids_and_source_urls: Optional[Iterable[tuple[str, str]]] = None,
    pdf_dir: Optional[Path] = None,
    save_raw_azure_response: bool = False,
    experimental_extract_tables: bool = False,
) -> None:
    """
    Run Azure PDF parser on a directory of PDFs, or sequence of IDs and source URLs.

    Outputs 'blank' parser output jsons to `--output-dir`, with just document ID,
    document name, text block and page metadata information populated.

    :param output_dir: directory to write output JSONs to
    :param ids_and_source_urls: optional iterable of [(document ID, source URL), ...].
    :param pdf_dir: optional directory of PDFs to parse. Filenames will be used as IDs.
    :param save_raw_azure_response: optionally save raw Azure API response to disk.
    :param experimental_extract_tables: optionally extract structured representations of
        tables.
    :raises ValueError: if neither source_url or pdf_dir are provided, or if Azure
    API keys are missing from environment variables.
    """

    if not output_dir.exists():
        LOGGER.warning(f"Output directory {output_dir} does not exist. Creating.")
        output_dir.mkdir(parents=True)

    if not AZURE_PROCESSOR_KEY or not AZURE_PROCESSOR_ENDPOINT:
        raise ValueError(
            """Missing Azure API credentials. Set AZURE_PROCESSOR_KEY and 
            AZURE_PROCESSOR_ENDPOINT environment variables."""
        )

    if not ids_and_source_urls and not pdf_dir:
        raise ValueError("""Must provide either source urls or pdf directory.""")

    azure_client = AzureApiWrapper(AZURE_PROCESSOR_KEY, AZURE_PROCESSOR_ENDPOINT)

    if ids_and_source_urls:
        for import_id, url in ids_and_source_urls:
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
                    extract_tables=experimental_extract_tables,
                )
    if pdf_dir:
        for pdf_path in tqdm(list(pdf_dir.glob("*.pdf"))):
            pdf_bytes = pdf_path.read_bytes()

            analyse_result = process_document(
                document_parameter=pdf_bytes,
                process_callable=azure_client.analyze_document_from_bytes,
                process_callable_retry=azure_client.analyze_large_document_from_bytes,
            )

            if analyse_result and save_raw_azure_response:
                (output_dir / f"{pdf_path.stem}_raw.json").write_text(
                    json.dumps(analyse_result.to_dict())
                )

            if analyse_result:
                # Source url cannot be None and must have a minimum length.
                convert_and_save_api_response(
                    import_id=pdf_path.stem,
                    api_response=analyse_result,
                    output_dir=output_dir,
                    extract_tables=experimental_extract_tables,
                )
