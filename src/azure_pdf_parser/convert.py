from typing import Sequence, Union

from azure.ai.formrecognizer import (
    AnalyzeResult,
    DocumentParagraph,
    Point,
    DocumentTable,
)
from cpr_data_access.parser_models import (
    ParserOutput,
    PDFTextBlock,
    PDFData,
    PDFPageMetadata,
    ParserInput,
)
from azure_pdf_parser.base import (
    ExperimentalTableCell,
    ExperimentalBoundingRegion,
    ExperimentalPDFTableBlock,
    ExperimentalPDFData,
    ExperimentalParserOutput,
)


def polygon_to_coords(polygon: Sequence[Point]) -> list[tuple[float, float]]:
    """Converts a polygon (four x,y co-ordinates) to a list of co-ordinates.

    The origin of the co-ordinate system is the top left corner of the page.

    The points array is ordered as follows:
    - top left, top  right, bottom right, bottom left
    """

    if len(polygon) != 4:
        raise ValueError("Polygon must have exactly four points.")

    return [(vertex.x, vertex.y) for vertex in polygon]


def azure_paragraph_to_text_block(
    paragraph_id: int, paragraph: DocumentParagraph
) -> PDFTextBlock:
    """Convert a DocumentParagraph to a PDFTextBlock."""
    return PDFTextBlock(
        coords=polygon_to_coords(paragraph.bounding_regions[0].polygon),
        # FIXME: The paragraph could be split across multiple pages, page_number only
        #  allows int
        page_number=paragraph.bounding_regions[0].page_number,
        text=[paragraph.content],
        text_block_id=str(paragraph_id),
        language=None,
        type=paragraph.role or "Ambiguous",
        type_confidence=1.0,
    )


def azure_table_to_table_block(
    table: DocumentTable, index: int
) -> ExperimentalPDFTableBlock:
    """Convert the tables in an api response to an array of table blocks."""
    return ExperimentalPDFTableBlock(
        table_id=index,
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
                        page_number=cell.bounding_regions[0].page_number,
                        polygon=cell.bounding_regions[0].polygon,
                    )
                ],
            )
            for cell in table.cells
        ],
    )


def azure_api_response_to_parser_output(
    parser_input: ParserInput,
    md5sum: str,
    api_response: AnalyzeResult,
    experimental_extract_tables: bool = False,
) -> Union[ParserOutput, ExperimentalParserOutput]:
    """Convert the API response AnalyzeResult object to a ParserOutput or an
    ExperimentalParserOutput.

    The experimental parser output configuration will also extract tables from the api
    response.
    """

    if experimental_extract_tables:
        return (
            ExperimentalParserOutput(
                document_id=parser_input.document_id,
                document_metadata=parser_input.document_metadata,
                document_name=parser_input.document_name,
                document_description=parser_input.document_description,
                document_source_url=parser_input.document_source_url,
                document_cdn_object=parser_input.document_cdn_object,
                document_content_type=parser_input.document_cdn_object,
                document_md5_sum=md5sum,
                document_slug=parser_input.document_slug,
                languages=None,
                translated=False,
                html_data=None,
                pdf_data=ExperimentalPDFData(
                    # FIXME: Check that the units of the dimensions are correct (units are
                    #  in inches)
                    page_metadata=[
                        PDFPageMetadata(
                            page_number=page.page_number,
                            dimensions=(page.width, page.height),
                        )
                        for page in api_response.pages
                    ],
                    md5sum=md5sum,
                    text_blocks=[
                        azure_paragraph_to_text_block(
                            paragraph_id=index, paragraph=paragraph
                        )
                        for index, paragraph in enumerate(api_response.paragraphs)
                    ],
                    table_blocks=[
                        azure_table_to_table_block(table=table, index=index)
                        for index, table in enumerate(api_response.tables)
                    ],
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
            document_content_type=parser_input.document_cdn_object,
            document_md5_sum=md5sum,
            document_slug=parser_input.document_slug,
            languages=None,
            translated=False,
            html_data=None,
            pdf_data=PDFData(
                # FIXME: Check that the units of the dimensions are correct (units are
                #  in inches)
                page_metadata=[
                    PDFPageMetadata(
                        page_number=page.page_number,
                        dimensions=(page.width, page.height),
                    )
                    for page in api_response.pages
                ],
                md5sum=md5sum,
                text_blocks=[
                    azure_paragraph_to_text_block(
                        paragraph_id=index, paragraph=paragraph
                    )
                    for index, paragraph in enumerate(api_response.paragraphs)
                ],
            ),
        )
        .detect_and_set_languages()
        .set_document_languages_from_text_blocks()
    )
