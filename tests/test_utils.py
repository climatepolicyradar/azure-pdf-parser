import io
import unittest
from unittest import mock

from azure.ai.formrecognizer import AnalyzeResult

from azure_pdf_parser import PDFPagesBatchExtracted
from azure_pdf_parser.base import PDFPagesBatch
from azure_pdf_parser.utils import (
    calculate_md5_sum,
    propagate_page_number,
    merge_responses,
    split_into_batches,
    call_api_with_error_handling,
)
from tests.helpers import is_valid_md5, is_valid_pdf


@mock.patch("azure_pdf_parser.utils.logger")
def test_call_api_with_error_handling_good_response(mock_logger) -> None:
    """Test that the API function is called correctly."""
    mock_api_function = mock.Mock(return_value="response")
    result = call_api_with_error_handling(3, mock_api_function, "arg1", kwarg="value")

    assert result == "response"
    mock_api_function.assert_called_once_with("arg1", kwarg="value")
    mock_logger.info.assert_called_once_with(
        "Calling API function with retries...",
        extra={"props": {"retries": 3}},
    )


@mock.patch("azure_pdf_parser.utils.logger")
def test_call_api_with_error_handling_bad_response(mock_logger) -> None:
    """Test that the API function is called correctly."""
    retries = 3
    mock_api_function = mock.Mock(side_effect=Exception("API error"))

    with unittest.TestCase().assertRaises(Exception) as context:
        call_api_with_error_handling(retries, mock_api_function, "arg1", kwarg="value")

    assert str(context.exception) == "API error"
    mock_api_function.assert_called_with("arg1", kwarg="value")
    mock_logger.info.assert_called_once_with(
        "Calling API function with retries...",
        extra={"props": {"retries": retries}},
    )
    assert mock_logger.error.call_count == retries


def test_propagate_page_number(pdf_page) -> None:
    """Test that the correct page number is propagated."""
    initial_page_number = (
        pdf_page.extracted_content.paragraphs[0].bounding_regions[0].page_number
    )
    initial_extracted_content = pdf_page.extracted_content

    pdf_page_processed = propagate_page_number(pdf_page)

    assert pdf_page_processed.extracted_content.paragraphs != initial_extracted_content

    for paragraph in pdf_page_processed.extracted_content.paragraphs:
        assert paragraph.bounding_regions[0].page_number != initial_page_number
        assert (
            paragraph.bounding_regions[0].page_number
            == pdf_page_processed.page_range[0]
        )

    for table in pdf_page_processed.extracted_content.tables:
        for cell in table.cells:
            for bounding_region in cell.bounding_regions:
                assert bounding_region.page_number != initial_page_number
                assert bounding_region.page_number == pdf_page_processed.page_range[0]

        for bounding_region in table.bounding_regions:
            assert bounding_region.page_number != initial_page_number
            assert bounding_region.page_number == pdf_page_processed.page_range[0]


def test_merge_responses(one_page_analyse_result: AnalyzeResult) -> None:
    """Test that the responses are merged correctly."""
    api_responses = [
        PDFPagesBatchExtracted(
            page_range=(1, 1),
            extracted_content=one_page_analyse_result,
            batch_number=1,
            batch_size_max=1,
        ),
        PDFPagesBatchExtracted(
            page_range=(2, 2),
            extracted_content=one_page_analyse_result,
            batch_number=2,
            batch_size_max=1,
        ),
        PDFPagesBatchExtracted(
            page_range=(3, 3),
            extracted_content=one_page_analyse_result,
            batch_number=3,
            batch_size_max=1,
        ),
    ]

    assert one_page_analyse_result.paragraphs is not None
    assert one_page_analyse_result.tables is not None
    paragraph_number_initial = len(one_page_analyse_result.paragraphs) * len(
        api_responses
    )
    table_number_initial = len(one_page_analyse_result.tables) * len(api_responses)

    merged_api_response = merge_responses(api_responses)

    # Check that the result is an AnalyzeResult object
    assert isinstance(merged_api_response, AnalyzeResult)
    assert merged_api_response.api_version == one_page_analyse_result.api_version
    assert merged_api_response.model_id == one_page_analyse_result.model_id
    assert merged_api_response.languages == one_page_analyse_result.languages
    assert merged_api_response.styles == one_page_analyse_result.styles
    assert merged_api_response.documents == one_page_analyse_result.documents

    # Check that the number of paragraphs and tables is correct
    assert merged_api_response.paragraphs is not None
    assert merged_api_response.tables is not None
    assert len(merged_api_response.paragraphs) == paragraph_number_initial
    assert len(merged_api_response.tables) == table_number_initial


def test_split_into_batches(
    one_page_pdf_bytes: bytes,
    two_page_pdf_bytes: bytes,
    sixty_eight_page_pdf_bytes: bytes,
) -> None:
    """Test that the PDF is split into batches correctly."""
    batches: list[PDFPagesBatch] = split_into_batches(
        io.BytesIO(one_page_pdf_bytes), batch_size=1
    )
    assert len(batches) == 1
    assert batches[0].page_range == (1, 1)
    assert batches[0].batch_size_max == 1
    assert batches[0].batch_number == 0
    for batch in batches:
        assert is_valid_pdf(batch.batch_content)

    batches = split_into_batches(io.BytesIO(two_page_pdf_bytes), batch_size=1)
    assert len(batches) == 2
    assert batches[0].page_range == (1, 1)
    assert batches[1].page_range == (2, 2)
    for batch in batches:
        assert is_valid_pdf(batch.batch_content)

    batches = split_into_batches(io.BytesIO(two_page_pdf_bytes), batch_size=2)
    assert len(batches) == 1
    assert batches[0].page_range == (1, 2)
    for batch in batches:
        assert is_valid_pdf(batch.batch_content)

    batches = split_into_batches(io.BytesIO(sixty_eight_page_pdf_bytes), batch_size=1)
    assert len(batches) == 68
    assert batches[0].page_range == (1, 1)
    assert batches[67].page_range == (68, 68)
    for batch in batches:
        assert is_valid_pdf(batch.batch_content)

    batches = split_into_batches(io.BytesIO(sixty_eight_page_pdf_bytes), batch_size=12)
    assert len(batches) == 6  # 68 / 12 = 5.6666 -> 6
    assert batches[0].page_range == (1, 12)
    assert batches[1].page_range == (13, 24)
    assert batches[2].page_range == (25, 36)
    assert batches[3].page_range == (37, 48)
    assert batches[4].page_range == (49, 60)
    assert batches[5].page_range == (61, 68)
    for batch in batches:
        assert is_valid_pdf(batch.batch_content)


def test_calculate_md5_sum(one_page_pdf_bytes: bytes) -> None:
    """Test that the md5 sum is calculated correctly."""

    md5_sum = calculate_md5_sum(one_page_pdf_bytes)
    assert isinstance(md5_sum, str)
    assert is_valid_md5(md5_sum)

    md5_sum = calculate_md5_sum(b"Random bytes!")
    assert isinstance(md5_sum, str)
    assert is_valid_md5(md5_sum)
