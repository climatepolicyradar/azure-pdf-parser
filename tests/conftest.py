from unittest.mock import MagicMock, Mock

import pytest
from azure.ai.formrecognizer import AnalyzeResult, DocumentParagraph, DocumentTable
from cpr_data_access.parser_models import ParserInput

from azure_pdf_parser import AzureApiWrapper, PDFPage
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
def one_page_analyse_result() -> AnalyzeResult:
    """Mock response for the analyse document from url endpoint."""
    data = read_local_json_file("./tests/data/sample-one-page.json")
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
        document_metadata=backend_document_json,
        document_name="name",
        document_description="description",
        document_source_url="https://example.com",
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
        document_metadata=backend_document_json,
        document_name="name",
        document_description="description",
        document_source_url="https://example.com",
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
def pdf_page(one_page_analyse_result) -> PDFPage:
    """A pdf page object"""
    return PDFPage(page_number=123, extracted_content=one_page_analyse_result)
