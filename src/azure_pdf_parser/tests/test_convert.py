import unittest

from azure.ai.formrecognizer import (
    Point,
    DocumentParagraph,
    DocumentTable,
    AnalyzeResult,
)
from cpr_data_access.parser_models import PDFTextBlock, ParserInput, ParserOutput

from azure_pdf_parser.experimental_base import (
    ExperimentalPDFTableBlock,
    ExperimentalParserOutput,
    ExperimentalTableCell,
)
from azure_pdf_parser.convert import (
    polygon_to_co_ordinates,
    azure_paragraph_to_text_block,
    azure_table_to_table_block,
    azure_api_response_to_parser_output,
)


def test_valid_polygon_to_co_ordinates() -> None:
    """Test that we can convert a sequence of points into a list of coordinates."""
    valid_points_raw = [
        (0.0, 1.0),
        (1.0, 1.0),
        (1.0, 0.0),
        (0.0, 0.0),
    ]

    valid_points = [Point(x=x, y=y) for x, y in valid_points_raw]

    coords = polygon_to_co_ordinates(valid_points)
    assert isinstance(coords, list)
    for coord in coords:
        assert isinstance(coord, tuple)
        for coord_val in coord:
            assert isinstance(coord_val, float)

    assert coords == valid_points_raw


def test_invalid_polygon_to_co_ordinates() -> None:
    """Test that we throw an exception should the polygon not be of the correct form."""

    invalid_points = [
        Point(
            x=0.0,
            y=1.0,
        ),
        Point(x=1.0, y=1.0),
    ]

    with unittest.TestCase().assertRaises(ValueError) as context:
        polygon_to_co_ordinates(invalid_points)
    assert str(context.exception) == "Polygon must have exactly four points."


def test_azure_paragraph_to_text_block(document_paragraph: DocumentParagraph) -> None:
    """Test that we can convert an Azure document paragraph to a text block."""
    text_block = azure_paragraph_to_text_block(
        paragraph_id=1, paragraph=document_paragraph
    )

    assert isinstance(text_block, PDFTextBlock)
    assert text_block.type == document_paragraph.role
    assert text_block.type_confidence == 1
    assert text_block.text_block_id == "1"
    assert text_block.page_number == document_paragraph.bounding_regions[0].page_number
    assert text_block.coords == polygon_to_co_ordinates(
        document_paragraph.bounding_regions[0].polygon
    )
    assert text_block.text == [document_paragraph.content]
    assert text_block.language is None


def test_azure_table_to_table_block(document_table: DocumentTable) -> None:
    """Test that we can assign data from a document table to a pdf table block."""
    index = 123
    table_block = azure_table_to_table_block(document_table, index=index)

    assert isinstance(table_block, ExperimentalPDFTableBlock)
    assert table_block.table_id == str(index)
    assert table_block.row_count is document_table.row_count
    assert table_block.column_count is document_table.column_count
    assert len(table_block.cells) is len(document_table.cells)
    for cell in table_block.cells:
        assert isinstance(cell, ExperimentalTableCell)
    # TODO think more about cell content tests, potentially split out into separate
    #   function and tests


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
    assert isinstance(parser_output, ParserOutput)
    assert parser_output.document_md5_sum == md5_sum

    # Convert with experimental tables
    parser_output = azure_api_response_to_parser_output(
        parser_input=parser_input,
        md5_sum=md5_sum,
        api_response=one_page_analyse_result,
        experimental_extract_tables=True,
    )
    assert isinstance(parser_output, ExperimentalParserOutput)
    assert parser_output.pdf_data.table_blocks is not None
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
