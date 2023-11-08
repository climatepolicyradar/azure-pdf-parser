from typing import Sequence
from unittest.mock import patch, Mock
from azure.ai.formrecognizer import AnalyzeResult

from azure_pdf_parser import (
    AzureApiWrapper,
    PDFPagesBatchExtracted,
    azure_api_response_to_parser_output,
)
from cpr_data_access.parser_models import ParserInput, ParserOutput
from azure_pdf_parser.utils import call_api_with_error_handling


# TODO test non english document


def test_call_api_with_error_handling_good_response(
    mock_azure_client: AzureApiWrapper,
    one_page_pdf_bytes: bytes,
    one_page_analyse_result: AnalyzeResult,
) -> None:
    """Test the retry logic and exception handling of the function."""
    response = call_api_with_error_handling(
        retries=3,
        func=mock_azure_client.analyze_document_from_url,
        doc_bytes=one_page_pdf_bytes,
        timeout=None,
    )

    assert response == one_page_analyse_result
    assert mock_azure_client.analyze_document_from_url.call_count == 1


def test_call_api_with_error_handling_bad_response(
    mock_azure_client: AzureApiWrapper,
    one_page_pdf_bytes: bytes,
) -> None:
    """Test the retry logic and exception handling of the function."""
    retries = 3
    exception_to_raise = Exception("Simulated API error")
    mock_azure_client.analyze_document_from_url.side_effect = exception_to_raise

    exception_raised = None
    try:
        call_api_with_error_handling(
            retries=retries,
            func=mock_azure_client.analyze_document_from_url,
            doc_bytes=one_page_pdf_bytes,
            timeout=None,
        )
    except Exception as e:
        exception_raised = e

    assert exception_raised == exception_to_raise
    assert mock_azure_client.analyze_document_from_url.call_count is retries


def test_analyze_document_from_url(
    mock_azure_client: AzureApiWrapper, one_page_analyse_result: AnalyzeResult
) -> None:
    """Test that the document from url method returns the correct response."""
    response = mock_azure_client.analyze_document_from_url(
        "https://example.com/test.pdf"
    )

    assert mock_azure_client.analyze_document_from_url.call_count == 1
    assert response == one_page_analyse_result


def test_analyze_document_from_bytes(
    mock_azure_client: AzureApiWrapper, one_page_analyse_result: AnalyzeResult
) -> None:
    """Test that the document from bytes method returns the correct response."""
    response = mock_azure_client.analyze_document_from_bytes(
        bytes("Random Content".encode("UTF-8"))
    )

    assert response == one_page_analyse_result


def test_document_split_one_page(
    mock_azure_client: AzureApiWrapper,
    one_page_analyse_result: AnalyzeResult,
    mock_document_download_response_one_page: Mock,
) -> None:
    """Test the processing of a document via url with the multi page function."""
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_document_download_response_one_page

        response = mock_azure_client.analyze_large_document_from_url(
            "https://example.com/test.pdf"
        )

        batch_api_responses = response[0]
        merged_batch_api_responses = response[1]

        assert isinstance(batch_api_responses, list)
        assert len(batch_api_responses) == 1
        assert isinstance(batch_api_responses[0], PDFPagesBatchExtracted)
        assert batch_api_responses[0].page_range == (1, 1)
        assert batch_api_responses[0].batch_number == 0
        assert batch_api_responses[0].batch_size_max == 50  # Default batch size
        assert batch_api_responses[0].extracted_content == one_page_analyse_result
        assert isinstance(merged_batch_api_responses, AnalyzeResult)


def test_document_split_two_page(
    mock_azure_client: AzureApiWrapper,
    one_page_analyse_result: AnalyzeResult,
    mock_document_download_response_two_page: Mock,
) -> None:
    """
    Test the processing of a document via url with the split page functionality.

    We mock the response from the document download request as well as the response
    from the azure api to extract content from the page.
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_document_download_response_two_page

        response = mock_azure_client.analyze_large_document_from_url(
            "https://example.com/test.pdf",
            batch_size=1,
        )

        page_api_responses: Sequence[PDFPagesBatchExtracted] = response[0]
        merged_page_api_responses: AnalyzeResult = response[1]

        assert isinstance(page_api_responses, list)
        assert len(page_api_responses) == 2
        for page_api_response in page_api_responses:
            assert isinstance(page_api_response, PDFPagesBatchExtracted)
            # Check we received the mock one-page response
            assert page_api_response.extracted_content == one_page_analyse_result

        assert isinstance(merged_page_api_responses, AnalyzeResult)


def test_document_split_sixty_eight_page(
    mock_azure_client_sixteen_page: AzureApiWrapper,
    sixteen_page_analyse_result: AnalyzeResult,
    mock_document_download_response_sixty_eight_page: Mock,
    parser_input: ParserInput,
) -> None:
    """
    Test the processing of a document via url with the split page functionality.

    We mock the response from the document download request as well as the response
    from the azure api to extract content from the page.

    For this configuration a document of 66 pages will be downloaded. This will be
    chunked into batches of a size 16 pages. We will then mock the response from the
    azure api to contain data for an 16 page document.

    Thus, we are testing the azure api batching method at the package level with a
    batch size of greater than one.
    """
    with patch("requests.get") as mock_get:
        mock_get.return_value = mock_document_download_response_sixty_eight_page

        response = mock_azure_client_sixteen_page.analyze_large_document_from_url(
            "https://example.com/test.pdf",
            batch_size=16,
        )

        page_api_responses: Sequence[PDFPagesBatchExtracted] = response[0]
        merged_page_api_responses: AnalyzeResult = response[1]

        assert isinstance(page_api_responses, list)
        assert len(page_api_responses) == 5  # 68 / 16 = 4.25 -> 5
        for page_api_response in page_api_responses:
            assert isinstance(page_api_response, PDFPagesBatchExtracted)
            # Check we received the mock one-page response
            assert page_api_response.extracted_content == sixteen_page_analyse_result

        assert isinstance(merged_page_api_responses, AnalyzeResult)

        parser_output = azure_api_response_to_parser_output(
            parser_input=parser_input,
            md5_sum="123456",
            api_response=merged_page_api_responses,
        )
        
        assert isinstance(parser_output, ParserOutput)
        parser_output.vertically_flip_text_block_coords()
