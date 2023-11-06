import unittest

from azure.ai.formrecognizer import (
    Point,
    DocumentParagraph,
    DocumentTable,
    AnalyzeResult,
)
from cpr_data_access.parser_models import (
    PDFTextBlock,
    ParserInput,
    ParserOutput,
    BlockType,
)

from azure_pdf_parser.base import DIMENSION_CONVERSION_FACTOR
from azure_pdf_parser.convert import (
    polygon_to_co_ordinates,
    azure_paragraph_to_text_block,
    azure_table_to_table_block,
    azure_api_response_to_parser_output,
    get_all_table_cell_spans,
    tag_table_paragraphs,
)
from azure_pdf_parser.experimental_base import (
    ExperimentalPDFTableBlock,
    ExperimentalParserOutput,
    ExperimentalTableCell,
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
    assert document_paragraph.bounding_regions is not None
    assert (
        text_block.page_number == document_paragraph.bounding_regions[0].page_number - 1
    )
    assert text_block.coords == [
        (DIMENSION_CONVERSION_FACTOR * coord[0], DIMENSION_CONVERSION_FACTOR * coord[1])
        for coord in polygon_to_co_ordinates(
            document_paragraph.bounding_regions[0].polygon
        )
    ]
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
    parser_input_no_content_type: ParserInput,
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

    # Convert with no document content-type
    with unittest.TestCase().assertRaises(ValueError) as context:
        azure_api_response_to_parser_output(
            parser_input=parser_input_no_content_type,
            md5_sum=md5_sum,
            api_response=one_page_analyse_result,
        )
    assert str(context.exception) == "Document content type must be PDF."

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

    # Test that we can call the vertically_flip_text_block_coords method on the
    # ParserOutput, this will assert that the page numbers are correct as well.
    parser_output = azure_api_response_to_parser_output(
        parser_input=parser_input,
        md5_sum=md5_sum,
        api_response=one_page_analyse_result,
    )
    assert isinstance(parser_output, ParserOutput)
    parser_output.vertically_flip_text_block_coords().get_text_blocks()


def test_get_table_cell_spans(analyze_result_known_table_content) -> None:
    """Test that we can get the cell spans from a table block."""
    # Get the input data
    (
        analyse_result,
        paragraphs_with_table_spans,
        cells,
        spans,
    ) = analyze_result_known_table_content

    # Get the table spans
    table_spans = get_all_table_cell_spans(analyse_result)

    # Check the output
    assert len(table_spans) > 0
    assert len(table_spans) == len(spans)
    assert table_spans == set([(span.offset, span.length) for span in spans])


def test_tag_table_paragraphs(analyze_result_known_table_content) -> None:
    """Test that we can successfully tag the paragraphs that are of the type table."""
    # Get the input data
    (
        analyse_result,
        paragraphs_with_table_spans,
        cells,
        spans,
    ) = analyze_result_known_table_content

    # Tag the table paragraphs
    analyse_result_tagged = tag_table_paragraphs(analyse_result)

    # Check the output
    table_paragraphs = [
        paragraph
        for paragraph in analyse_result_tagged.paragraphs
        if paragraph.role == BlockType.TABLE_CELL.value
    ]

    assert len(table_paragraphs) > 0
    assert len(table_paragraphs) == len(paragraphs_with_table_spans)
    assert table_paragraphs == paragraphs_with_table_spans

    table_paragraph_spans = [paragraph.spans[0] for paragraph in table_paragraphs]
    assert len(table_paragraph_spans) > 0
    assert len(table_paragraph_spans) == len(spans)
    assert table_paragraph_spans == spans


def test_table_paragraph_assumptions(
    one_page_analyse_result: AnalyzeResult,
    sixteen_page_analyse_result: AnalyzeResult,
) -> None:
    """
    Test the assumptions for tagging paragraphs as table blocks.

    Assumptions:
    - All the spans in an azure response are unique.
    - All table text objects have a related paragraph.
    - All the content and bounding regions are the same for related table and paragraph.
    """
    for result in [one_page_analyse_result, sixteen_page_analyse_result]:
        # Create a list of all the table cells
        table_cells = [cell for table in result.tables for cell in table.cells]

        # Create a list of all the table cell spans as a tuple of (offset, length)
        table_cell_spans = [
            (cell.spans[0].offset, cell.spans[0].length) for cell in table_cells
        ]

        # Create a list of all the paragraph spans as a tuple of (offset, length)
        paragraph_spans = [
            (paragraph.spans[0].offset, paragraph.spans[0].length)
            for paragraph in result.paragraphs
        ]

        # Create a mapping of the table cell and the related paragraph
        table_cell_paragraph_mapping = []
        for cell in table_cells:
            for paragraph in result.paragraphs:
                if (
                    paragraph.spans[0].offset == cell.spans[0].offset
                    and paragraph.spans[0].length == cell.spans[0].length
                ):
                    table_cell_paragraph_mapping.append((cell, paragraph))

        # Check that all the paragraph spans are unique
        assert len(paragraph_spans) == len(set(paragraph_spans))

        # Check that all the table cell spans are unique
        assert len(table_cell_spans) == len(set(table_cell_spans))

        # Check each table cell span is in the paragraph spans
        for span in table_cell_spans:
            assert span in paragraph_spans

        # Check that the content is the same
        assert len(table_cell_paragraph_mapping) == len(table_cells)
        for cell, paragraph in table_cell_paragraph_mapping:
            assert cell.content == paragraph.content
            assert len(cell.bounding_regions) == 1
            assert len(paragraph.bounding_regions) == 1
            assert cell.bounding_regions[0].page_number == (
                paragraph.bounding_regions[0].page_number
            )
            assert cell.bounding_regions[0].polygon == (
                paragraph.bounding_regions[0].polygon
            )
