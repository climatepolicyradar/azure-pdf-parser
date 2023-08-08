from unittest.mock import MagicMock, Mock

import pytest
from azure.ai.formrecognizer import AnalyzeResult

from azure_api_wrapper.azure_wrapper import AzureApiWrapper
from azure_api_wrapper.base import PDFPage
from azure_api_wrapper.tests.helpers import read_local_json_file, read_pdf_to_bytes


@pytest.fixture()
def one_page_pdf_bytes() -> bytes:
    """Content for the sample one page pdf"""
    return read_pdf_to_bytes("./src/azure_api_wrapper/tests/data/sample-one-page.pdf")


@pytest.fixture()
def two_page_pdf_bytes() -> bytes:
    """Content for the sample two page pdf"""
    return read_pdf_to_bytes("./src/azure_api_wrapper/tests/data/sample-two-page.pdf")


@pytest.fixture()
def one_page_analyse_result() -> AnalyzeResult:
    """Mock response for the analyse document from url endpoint."""
    data = read_local_json_file(
        "./src/azure_api_wrapper/tests/data/sample-one-page.json"
    )
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
def mock_document_download_response_one_page(
    one_page_pdf_bytes: bytes,
) -> Mock:
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
def pdf_page(one_page_analyse_result) -> PDFPage:
    """A pdf page object"""
    return PDFPage(page_number=123, extracted_content=one_page_analyse_result)
