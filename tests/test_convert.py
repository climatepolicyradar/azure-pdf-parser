import unittest

from azure.ai.formrecognizer import (
    Point,
    DocumentParagraph,
    DocumentTable,
    AnalyzeResult,
)
from cpr_data_access.parser_models import PDFTextBlock, ParserInput

from azure_pdf_parser.base import ExperimentalPDFTableBlock
from azure_pdf_parser.convert import (
    polygon_to_co_ordinates,
    azure_paragraph_to_text_block,
    azure_table_to_table_block,
    azure_api_response_to_parser_output,
)


def test_valid_polygon_to_co_ordinates() -> None:
    """Test that we can convert a sequence of points into a list of coordinates."""
    valid_points = [
        Point(x=0.0, y=1.0),
        Point(x=1.0, y=1.0),
        Point(x=1.0, y=0.0),
        Point(x=0.0, y=0.0),
    ]

    coords = polygon_to_co_ordinates(valid_points)
    assert isinstance(coords, list)
    for coord in coords:
        assert isinstance(coord, tuple)
        for coord_val in coord:
            assert isinstance(coord_val, float)


def test_invalid_polygon_to_co_ordinates() -> None:
    """Test that we throw an exception should the polygon not be of the correct form."""

    invalid_points = [
        Point(
            x=0.0,
            y=1.0,
        ),
        Point(x=1.0, y=1.0),
    ]

    coords = None
    error = None
    try:
        coords = polygon_to_co_ordinates(invalid_points)
    except ValueError as e:
        error = e

    assert error.__class__ is ValueError
    assert coords is None


def test_azure_paragraph_to_text_block(document_paragraph: DocumentParagraph) -> None:
    """Test that we can convert an Azure document paragraph to a text block."""
    print(document_paragraph.role)
    text_block = azure_paragraph_to_text_block(
        paragraph_id=1, paragraph=document_paragraph
    )

    # Pydantic will validate the types so not alot more validation needed
    assert isinstance(text_block, PDFTextBlock)
    assert text_block.type == "Document Header"


def test_azure_table_to_table_block(document_table: DocumentTable) -> None:
    """Test that we can assign data from a document table to a pdf table block."""
    index = 123
    table_block = azure_table_to_table_block(document_table, index=index)

    assert isinstance(table_block, ExperimentalPDFTableBlock)
    assert table_block.table_id == str(index)
    assert table_block.row_count is document_table.row_count
    assert table_block.column_count is document_table.column_count
    assert len(table_block.cells) is len(document_table.cells)


def test_azure_api_response_to_parser_output(
    parser_input: ParserInput,
    parser_input_empty_optional_fields: ParserInput,
    one_page_analyse_result: AnalyzeResult,
) -> None:
    """Test that we can convert an azure api response to a parser output object."""
    md5_sum = "1234567890"

    # Convert without experimental tables
    parser_output = azure_api_response_to_parser_output(
        parser_input=parser_input,
        md5_sum=md5_sum,
        api_response=one_page_analyse_result,
    )
    assert parser_output.document_md5_sum == md5_sum

    # Convert with experimental tables
    parser_output = azure_api_response_to_parser_output(
        parser_input=parser_input,
        md5_sum=md5_sum,
        api_response=one_page_analyse_result,
        experimental_extract_tables=True,
    )
    assert parser_output.document_md5_sum == md5_sum

    # Convert with a parser input object containing empty optional fields
    with unittest.TestCase().assertRaises(ValueError) as context:
        azure_api_response_to_parser_output(
            parser_input=parser_input_empty_optional_fields,
            md5_sum=md5_sum,
            api_response=one_page_analyse_result,
        )
    assert str(context.exception) == "Document content type must be PDF."

    # Convert with a parser input object containing empty optional fields and
    # experimental tables
    with unittest.TestCase().assertRaises(ValueError) as context:
        azure_api_response_to_parser_output(
            parser_input=parser_input_empty_optional_fields,
            md5_sum=md5_sum,
            api_response=one_page_analyse_result,
            experimental_extract_tables=True,
        )
    assert str(context.exception) == "Document content type must be PDF."
