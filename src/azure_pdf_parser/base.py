from typing import Any, Sequence, Optional, List

from azure.ai.formrecognizer import Point
from cpr_data_access.parser_models import (
    PDFData,
    ParserOutput,
    CONTENT_TYPE_HTML,
    CONTENT_TYPE_PDF,
    HTMLData,
    TextBlock,
)
from pydantic import BaseModel, root_validator, AnyHttpUrl


class PDFPage(BaseModel):
    """Pdf document page object with content and page number."""

    page_number: int
    extracted_content: Any


class ExperimentalBoundingRegion(BaseModel):
    """Region of a cell in a table."""

    page_number: int
    polygon: List[Point]


class ExperimentalTableCell(BaseModel):
    """Cell of a table."""

    # TODO create cell type enum
    # TODO potentially enforce bounding regions to be one region per page
    cell_type: str
    row_index: int
    column_index: int
    row_span: int
    column_span: int
    content: str
    bounding_regions: List[ExperimentalBoundingRegion]


class ExperimentalPDFTableBlock(BaseModel):
    """
    Table block parsed form a PDF document.

    Stores the text and positional information for a single table block extracted from
    a document.
    """

    table_id: str
    row_count: int
    column_count: int
    cells: List[ExperimentalTableCell]


class ExperimentalPDFData(PDFData):
    """PDFData object that also optionally contains table blocks."""

    table_blocks: Optional[Sequence[ExperimentalPDFTableBlock]] = None


class ExperimentalParserOutput(ParserOutput):
    """Experimental parser output with pdf data containing tables."""

    document_id: str
    document_metadata: dict
    document_name: str
    document_description: str
    document_source_url: Optional[AnyHttpUrl]
    document_cdn_object: Optional[str]
    document_content_type: Optional[str]
    document_md5_sum: Optional[str]
    document_slug: str

    languages: Optional[Sequence[str]] = None
    translated: bool = False
    html_data: Optional[HTMLData] = None
    pdf_data: Optional[ExperimentalPDFData] = None

    @root_validator
    def check_html_pdf_metadata(cls, values):
        """
        Validation for the data that is set.

        Check that html_data is set if content_type is HTML, or pdf_data is set if
        content_type is PDF.
        """
        if (
            values["document_content_type"] == CONTENT_TYPE_HTML
            and values["html_data"] is None
        ):
            raise ValueError("html_metadata must be set for HTML documents")

        if (
            values["document_content_type"] == CONTENT_TYPE_PDF
            and values["pdf_data"] is None
        ):
            raise ValueError("pdf_data must be set for PDF documents")

        if values["document_content_type"] is None and (
            values["html_data"] is not None or values["pdf_data"] is not None
        ):
            raise ValueError(
                "html_metadata and pdf_metadata must be null for documents with no "
                "content type. "
            )

        return values

    @property
    def text_blocks(self) -> Sequence[TextBlock]:
        """
        Return the text blocks in the document.

        These could differ in format depending on the content type.

        :return: Sequence[TextBlock]
        """
        if self.document_content_type == CONTENT_TYPE_HTML:
            html_data: HTMLData = self.html_data
            return html_data.text_blocks
        elif self.document_content_type == CONTENT_TYPE_PDF:
            pdf_data: PDFData = self.pdf_data
            return pdf_data.text_blocks
        return []

    def to_string(self) -> str:  # type: ignore
        """Return the text blocks in the parser output as a string"""

        return " ".join(
            [text_block.to_string().strip() for text_block in self.text_blocks]
        )
