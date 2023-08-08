from azure.ai.formrecognizer import AnalyzeResult

from azure_pdf_parser.utils import (
    calculate_md5_sum,
    is_valid_md5,
    propagate_page_number,
    merge_responses,
)
from azure_pdf_parser.base import PDFPage


def test_call_api_with_error_handling() -> None:
    pass


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
            paragraph.bounding_regions[0].page_number == pdf_page_processed.page_number
        )

    for table in pdf_page_processed.extracted_content.tables:
        for cell in table.cells:
            for bounding_region in cell.bounding_regions:
                assert bounding_region.page_number != initial_page_number
                assert bounding_region.page_number == pdf_page_processed.page_number

        for bounding_region in table.bounding_regions:
            assert bounding_region.page_number != initial_page_number
            assert bounding_region.page_number == pdf_page_processed.page_number


def test_merge_responses(one_page_analyse_result: AnalyzeResult) -> None:
    """Test that the responses are merged correctly."""
    api_responses = [
        PDFPage(page_number=1, extracted_content=one_page_analyse_result),
        PDFPage(page_number=2, extracted_content=one_page_analyse_result),
        PDFPage(page_number=3, extracted_content=one_page_analyse_result),
    ]

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
    assert len(merged_api_response.paragraphs) == paragraph_number_initial
    assert len(merged_api_response.tables) == table_number_initial


def test_split_into_pages():
    pass


def test_is_valid_md5() -> None:
    """Test that the function returns True for valid MD5 sums."""
    assert not is_valid_md5("Invalid MD5 sum")
    assert is_valid_md5("d41d8cd98f00b204e9800998ecf8427e")


def test_calculate_md5_sum(one_page_pdf_bytes: bytes) -> None:
    """Test that the md5 sum is calculated correctly."""

    md5_sum = calculate_md5_sum(one_page_pdf_bytes)
    assert isinstance(md5_sum, str)
    assert is_valid_md5(md5_sum)

    md5_sum = calculate_md5_sum(b"Random bytes!")
    assert isinstance(md5_sum, str)
    assert is_valid_md5(md5_sum)
