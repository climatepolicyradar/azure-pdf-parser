from typing import Any, Sequence, Optional, List

from azure.ai.formrecognizer import BoundingRegion, Point
from cpr_data_access.parser_models import PDFData, ParserOutput
from pydantic import BaseModel


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
    bounding_regions: List[BoundingRegion]


class ExperimentalPDFTableBlock(BaseModel):
    """Table block parsed form a PDF document.
    Stores the text and positional information for a single table block extracted from a document.
    """

    table_id: str
    row_count: int
    column_count: int
    cells: List[ExperimentalTableCell]


class ExperimentalPDFData(PDFData):
    """Experimental addition to the PDFData object that also optionally contains table
    blocks."""

    table_blocks: Optional[Sequence[ExperimentalPDFTableBlock]] = None


class ExperimentalParserOutput(ParserOutput):
    """Experimental parser output with pdf data containing tables."""

    pdf_data = Optional[ExperimentalPDFData] = None
