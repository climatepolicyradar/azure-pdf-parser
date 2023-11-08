from typing import Tuple, Sequence
from unittest.mock import MagicMock, Mock

import pytest
from azure.ai.formrecognizer import (
    AnalyzeResult,
    DocumentParagraph,
    DocumentTable,
    DocumentSpan,
    DocumentTableCell,
)
from cpr_data_access.parser_models import ParserInput

from azure_pdf_parser import AzureApiWrapper, PDFPagesBatchExtracted
from tests.helpers import read_local_json_file, read_pdf_to_bytes


@pytest.fixture()
def backend_document_json() -> dict:
    """A sample backend document json."""
    return {
        "publication_ts": "2013-01-01T00:00:00",
        "name": "Dummy Name",
        "description": "description",
        "source_url": "http://existing.com",
        "download_url": None,
        "url": None,
        "md5_sum": None,
        "type": "EU Decision",
        "source": "CCLW",
        "import_id": "TESTCCLW.executive.4.4",
        "family_import_id": "TESTCCLW.family.4.0",
        "family_slug": "slug_TESTCCLW.family.4.0",
        "category": "Law",
        "geography": "EUR",
        "languages": ["English"],
        "metadata": {
            "hazards": [],
            "frameworks": [],
            "instruments": ["Capacity building|Governance"],
            "keywords": ["Adaptation"],
            "sectors": ["Economy-wide"],
            "topics": ["Adaptation"],
        },
        "slug": "dummy_slug",
    }


@pytest.fixture()
def one_page_pdf_bytes() -> bytes:
    """Content for the sample one page pdf"""
    return read_pdf_to_bytes("./tests/data/sample-one-page.pdf")


@pytest.fixture()
def two_page_pdf_bytes() -> bytes:
    """Content for the sample two page pdf"""
    return read_pdf_to_bytes("./tests/data/sample-two-page.pdf")


@pytest.fixture()
def sixty_eight_page_pdf_bytes() -> bytes:
    """Content for the sample sixty-eight page pdf"""
    return read_pdf_to_bytes("./tests/data/sample-sixty-eight-page.pdf")


@pytest.fixture()
def one_page_analyse_result() -> AnalyzeResult:
    """Mock response for the analyse document from url endpoint."""
    data = read_local_json_file("./tests/data/sample-one-page.json")
    return AnalyzeResult.from_dict(data[0])


@pytest.fixture()
def sixteen_page_analyse_result() -> AnalyzeResult:
    """Mock response for the analyse document from url endpoint."""
    data = read_local_json_file("./tests/data/sample-sixteen-page.json")
    return AnalyzeResult.from_dict(data[0])


@pytest.fixture()
def mock_azure_client(one_page_analyse_result) -> AzureApiWrapper:
    """
    A mock client to the azure form recognizer api.

    Client contains mocked responses from the api endpoints.
    """
    azure_client = AzureApiWrapper("user", "pass")
    azure_client.analyze_document_from_url = MagicMock(
        return_value=one_page_analyse_result
    )
    azure_client.analyze_document_from_bytes = MagicMock(
        return_value=one_page_analyse_result
    )
    return azure_client


@pytest.fixture()
def mock_azure_client_sixteen_page(sixteen_page_analyse_result) -> AzureApiWrapper:
    """
    A mock client to the azure form recognizer api.

    Client contains mocked responses from the api endpoints.
    """
    azure_client = AzureApiWrapper("user", "pass")
    azure_client.analyze_document_from_url = MagicMock(
        return_value=sixteen_page_analyse_result
    )
    azure_client.analyze_document_from_bytes = MagicMock(
        return_value=sixteen_page_analyse_result
    )
    return azure_client


@pytest.fixture
def mock_document_download_response_one_page(one_page_pdf_bytes) -> Mock:
    """Create a mock response to a download request for a pdf document with one page."""
    # Create a mock Response object
    mock_response = Mock()
    mock_response.content = one_page_pdf_bytes

    # Set the status code and other attributes as needed for your test
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/pdf"}

    return mock_response


@pytest.fixture
def mock_document_download_response_sixty_eight_page(
    sixty_eight_page_pdf_bytes,
) -> Mock:
    """Create a mock response to a download request for a pdf document with one page."""
    # Create a mock Response object
    mock_response = Mock()
    mock_response.content = sixty_eight_page_pdf_bytes

    # Set the status code and other attributes as needed for your test
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/pdf"}

    return mock_response


@pytest.fixture
def mock_document_download_response_two_page(two_page_pdf_bytes) -> Mock:
    """Create a mock response to a download request for a pdf document with two page."""
    # Create a mock Response object
    mock_response = Mock()
    mock_response.content = two_page_pdf_bytes

    # Set the status code and other attributes as needed for your test
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/pdf"}

    return mock_response


@pytest.fixture
def document_paragraph() -> DocumentParagraph:
    """Construct a document paragraph object."""
    data = read_local_json_file("./tests/data/document-paragraph.json")
    return DocumentParagraph.from_dict(data)  # type: ignore


@pytest.fixture
def document_table() -> DocumentTable:
    """Construct a document table object."""
    data = read_local_json_file("./tests/data/document-table.json")
    return DocumentTable.from_dict(data)  # type: ignore


@pytest.fixture
def parser_input(backend_document_json: dict) -> ParserInput:
    """A parser input object"""
    return ParserInput(
        document_id="123",
        document_metadata=backend_document_json, # type: ignore 
        document_name="name",
        document_description="description",
        document_source_url="https://example.com", # type: ignore
        document_cdn_object="cdn_object",
        document_content_type="application/pdf",
        document_md5_sum="md5_sum_123_name",
        document_slug="slug_123_name",
    )


@pytest.fixture
def parser_input_no_content_type(backend_document_json: dict) -> ParserInput:
    """A parser input object with no content-type"""
    return ParserInput(
        document_id="123",
        document_metadata=backend_document_json, # type: ignore
        document_name="name",
        document_description="description",
        document_source_url="https://example.com", # type: ignore
        document_cdn_object="cdn_object",
        document_content_type=None,
        document_md5_sum="md5_sum_123_name",
        document_slug="slug_123_name",
    )


@pytest.fixture
def parser_input_empty_optional_fields(backend_document_json) -> ParserInput:
    """A parser input object with empty optional fields"""
    return ParserInput(
        document_id="123",
        document_metadata=backend_document_json,
        document_name="name",
        document_description="description",
        document_slug="slug_123_name",
    )


@pytest.fixture
def pdf_page(one_page_analyse_result) -> PDFPagesBatchExtracted:
    """
    A pdf batch object with extracted content.

    Note: The batch_number starts from a 0 -> n range where as the page range starts
    from 1 -> n.
    """
    return PDFPagesBatchExtracted(
        page_range=(123, 123),
        extracted_content=one_page_analyse_result,
        batch_number=122,
        batch_size_max=1,
    )


@pytest.fixture
def analyze_result_known_table_content(
    one_page_analyse_result,
) -> Tuple[
    AnalyzeResult,
    Sequence[DocumentParagraph],
    Sequence[DocumentTableCell],
    Sequence[DocumentSpan],
]:
    """
    Create an analyze result with the known table content.

    We create known table cells with particular span content as well as paragraphs in
    the analyze result with the same spans. This means that when tagging the
    paragraphs we have an object where we know which paragraphs should be tagged with
    the relevant table block type.
    """
    # Create the spans
    spans = [DocumentSpan(offset=i, length=i) for i in range(1, 10)]

    # Create the cells
    cells = [
        DocumentTableCell(
            bounding_regions=[],
            column_index=0,
            column_span=0,
            content="",
            kind="",
            row_index=0,
            row_span=0,
            spans=[span],
        )
        for span in spans
    ]

    # Create the paragraphs with the table spans
    paragraphs_with_table_spans = [
        DocumentParagraph(
            bounding_regions=[],
            content="",
            role=None,
            spans=[span],
        )
        for span in spans
    ]

    # Keep only the first table
    one_page_analyse_result.tables = one_page_analyse_result.tables[:1]

    # Replace the table content with the new cells
    one_page_analyse_result.tables[0].cells = cells

    # Extend the paragraphs with the paragraphs that reference the table content
    one_page_analyse_result.paragraphs = (
        paragraphs_with_table_spans + one_page_analyse_result.paragraphs
    )

    return one_page_analyse_result, paragraphs_with_table_spans, cells, spans


@pytest.fixture
def analyze_result_table_cell_no_spans(one_page_analyse_result) -> AnalyzeResult:
    """Create an analyze result with a table cell containing no spans."""

    # Create the cells
    cells = [
        DocumentTableCell(
            bounding_regions=[],
            column_index=0,
            column_span=0,
            content="",
            kind="",
            row_index=0,
            row_span=0,
            spans=[],
        ),
        DocumentTableCell(
            bounding_regions=[],
            column_index=0,
            column_span=0,
            content="",
            kind="",
            row_index=0,
            row_span=0,
            spans=None,
        ),
    ]

    # Keep only the first table
    one_page_analyse_result.tables = one_page_analyse_result.tables[:1]

    # Replace the table content with the new cells
    one_page_analyse_result.tables[0].cells = cells

    return one_page_analyse_result
