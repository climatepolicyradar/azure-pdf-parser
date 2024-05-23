import logging
from typing import Sequence, Set, Tuple, Union

from azure.ai.formrecognizer import (
    AnalyzeResult,
    DocumentParagraph,
    DocumentTable,
    Point,
)
from cpr_data_access.parser_models import (
    CONTENT_TYPE_PDF,
    BlockType,
    ParserInput,
    ParserOutput,
    PDFData,
    PDFPageMetadata,
    PDFTextBlock,
)

from .base import DIMENSION_CONVERSION_FACTOR
from .experimental_base import (
    ExperimentalBoundingRegion,
    ExperimentalParserOutput,
    ExperimentalPDFData,
    ExperimentalPDFTableBlock,
    ExperimentalTableCell,
)

logger = logging.getLogger(__name__)


def polygon_to_co_ordinates(polygon: Sequence[Point]) -> list[tuple[float, float]]:
    """
    Converts a polygon (four x,y co-ordinates) to a list of co-ordinates.

    The origin of the co-ordinate system is the top left corner of the page. The
    points array is ordered as follows: - top left, top  right, bottom right,
    bottom left.
    """

    if len(polygon) != 4:
        raise ValueError("Polygon must have exactly four points.")

    return [(vertex.x, vertex.y) for vertex in polygon]


def azure_paragraph_to_text_block(
    paragraph_id: int, paragraph: DocumentParagraph
) -> PDFTextBlock:
    """
    Convert a DocumentParagraph to a PDFTextBlock.

    Paragraph bounding region is an optional field in the azure object model. And
    thus, we must handle this scenario. For our purposes it is a requirement to have
    the coordinates of a text block, and thus we do not return a text block in this
    instance.

    If paragraph role is not present we default to text.
    We auto-assign a type-confidence of one as azure does not provide confidence scores.
    """
    if paragraph.bounding_regions is None:
        raise ValueError("Paragraph must have bounding regions to create text block.")

    return PDFTextBlock(
        coords=[
            (
                DIMENSION_CONVERSION_FACTOR * coord[0],
                DIMENSION_CONVERSION_FACTOR * coord[1],
            )
            for coord in polygon_to_co_ordinates(paragraph.bounding_regions[0].polygon)
        ],
        page_number=paragraph.bounding_regions[0].page_number - 1,
        text=[paragraph.content],
        text_block_id=str(paragraph_id),
        language=None,
        type=paragraph.role or "Text",
        type_confidence=1.0,
    )


def extract_azure_api_response_paragraphs(
    api_response: AnalyzeResult,
) -> Sequence[PDFTextBlock]:
    """
    Extract paragraphs from an azure api response.

    The paragraphs must contain bounding regions.
    """
    text_blocks = []
    if api_response.paragraphs is not None:
        for index, paragraph in enumerate(api_response.paragraphs):
            if paragraph is not None and paragraph.bounding_regions is not None:
                text_blocks.append(
                    azure_paragraph_to_text_block(
                        paragraph_id=index, paragraph=paragraph
                    )
                )
    return text_blocks


def azure_table_to_table_block(
    table: DocumentTable, index: int
) -> ExperimentalPDFTableBlock:
    """Convert the tables in an api response to an array of table blocks."""
    return ExperimentalPDFTableBlock(
        table_id=str(index),
        row_count=table.row_count,
        column_count=table.column_count,
        cells=[
            ExperimentalTableCell(
                cell_type=cell.kind,
                row_index=cell.row_index,
                column_index=cell.column_index,
                row_span=cell.row_span,
                column_span=cell.column_span,
                content=cell.content,
                bounding_regions=[
                    ExperimentalBoundingRegion(
                        page_number=cell.bounding_regions[0].page_number - 1,
                        polygon=[
                            Point(
                                x=DIMENSION_CONVERSION_FACTOR * point.x,
                                y=DIMENSION_CONVERSION_FACTOR * point.y,
                            )
                            for point in cell.bounding_regions[0].polygon
                        ],
                    )
                ],
            )
            for cell in table.cells
            if (
                cell.bounding_regions is not None
                and cell.kind is not None
                and cell.row_span is not None
                and cell.column_span is not None
            )
        ],
    )


def extract_azure_api_response_tables(
    api_response: AnalyzeResult,
) -> Union[Sequence[ExperimentalPDFTableBlock], None]:
    """
    Extract tables from an azure api response.

    The table cells must contain bounding regions.
    """
    table_blocks = []
    if api_response.tables is not None:
        for index, table in enumerate(api_response.tables):
            if table is not None and all(cell is not None for cell in table.cells):
                table_blocks.append(
                    azure_table_to_table_block(table=table, index=index)
                )

    return table_blocks if table_blocks is not [] else None


def extract_azure_api_response_page_metadata(
    api_response: AnalyzeResult,
) -> Sequence[PDFPageMetadata]:
    """
    Extract page metadata from an azure api response.

    Page Number: Azure page numbers start from an index of 1, at cpr our data starts
    from 0 and thus we minus one from the page number.

    Dimensions: Azure units are in inches but our corpus is in 72ppi pixels, and thus we
    multiply by a conversion factor.
    """
    pdf_page_metadata = []
    for page in api_response.pages:
        if (
            page.width is not None
            and page.height is not None
            and page.page_number is not None
        ):
            pdf_page_metadata.append(
                PDFPageMetadata(
                    page_number=page.page_number - 1,
                    dimensions=(
                        page.width * DIMENSION_CONVERSION_FACTOR,
                        page.height * DIMENSION_CONVERSION_FACTOR,
                    ),
                )
            )

        else:
            logger.warning(
                f"Page metadata for page {page.page_number} is missing dimensions.",
                extra={
                    "props": {
                        "page_number": page.page_number,
                        "width": page.width,
                        "height": page.height,
                    }
                },
            )

    return pdf_page_metadata


def get_all_table_cell_spans(api_response: AnalyzeResult) -> Set[Tuple[int, int]]:
    """
    Retrieve the spans from all the table cells in the api response.

    This is represented as a tuple of (length, offset).
    """
    table_cell_spans = set()

    if api_response.tables is not None:
        for table in api_response.tables:
            for cell in table.cells:
                if isinstance(cell.spans, list) and len(cell.spans) > 0:
                    table_cell_spans.add((cell.spans[0].length, cell.spans[0].offset))

    return table_cell_spans


def tag_table_paragraphs(api_response: AnalyzeResult) -> AnalyzeResult:
    """
    Tag the paragraphs that contain data from a Table with the type table-text.

    This is done using the span of the content.
    """
    if api_response.paragraphs is None:
        return api_response

    table_cell_spans = get_all_table_cell_spans(api_response)

    for paragraph in api_response.paragraphs:
        paragraph_span = (paragraph.spans[0].length, paragraph.spans[0].offset)
        if paragraph_span in table_cell_spans:
            paragraph.role = BlockType.TABLE_CELL.value

    return api_response


def azure_api_response_to_parser_output(
    parser_input: ParserInput,
    md5_sum: str,
    api_response: AnalyzeResult,
    experimental_extract_tables: bool = False,
) -> Union[ParserOutput, ExperimentalParserOutput]:
    """
    Convert the API response AnalyzeResult object to a ParserOutput.

    Also, optionally convert to an ExperimentalParserOutput. The experimental parser
    output configuration will also extract tables from the api response.

    parser_input: ParserInput
        The input object to the parser.
    md5_sum: str
        The md5 sum of the document.
    api_response: AnalyzeResult
        The API response from the Azure Form Recognizer API.
    experimental_extract_tables: bool
        Whether to extract tables from the API response.
    """

    if parser_input.document_content_type != CONTENT_TYPE_PDF:
        raise ValueError("Document content type must be PDF.")

    api_response = tag_table_paragraphs(api_response)
    text_blocks = extract_azure_api_response_paragraphs(api_response)
    page_metadata = extract_azure_api_response_page_metadata(api_response)

    if experimental_extract_tables:
        table_blocks = extract_azure_api_response_tables(api_response=api_response)

        return (
            ExperimentalParserOutput(
                document_id=parser_input.document_id,
                document_metadata=parser_input.document_metadata,
                document_name=parser_input.document_name,
                document_description=parser_input.document_description,
                document_source_url=parser_input.document_source_url,
                document_cdn_object=parser_input.document_cdn_object,
                document_content_type=parser_input.document_content_type,
                document_md5_sum=md5_sum,
                document_slug=parser_input.document_slug,
                languages=None,
                translated=False,
                html_data=None,
                pdf_data=ExperimentalPDFData(
                    page_metadata=page_metadata,
                    md5sum=md5_sum,
                    text_blocks=text_blocks if not None else [],
                    table_blocks=table_blocks,
                ),
            )
            .detect_and_set_languages()
            .set_document_languages_from_text_blocks()
        )

    return (
        ParserOutput(
            document_id=parser_input.document_id,
            document_metadata=parser_input.document_metadata,
            document_name=parser_input.document_name,
            document_description=parser_input.document_description,
            document_source_url=parser_input.document_source_url,
            document_cdn_object=parser_input.document_cdn_object,
            document_content_type=parser_input.document_content_type,
            document_md5_sum=md5_sum,
            document_slug=parser_input.document_slug,
            languages=None,
            translated=False,
            html_data=None,
            pdf_data=PDFData(
                page_metadata=page_metadata,
                md5sum=md5_sum,
                text_blocks=text_blocks if not None else [],
            ),
        )
        .detect_and_set_languages()
        .set_document_languages_from_text_blocks()
    )
