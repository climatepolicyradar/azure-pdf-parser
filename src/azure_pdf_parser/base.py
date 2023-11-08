from azure.ai.formrecognizer import AnalyzeResult
from pydantic import BaseModel, ConfigDict

DIMENSION_CONVERSION_FACTOR = 72


class PDFPagesBatchExtracted(BaseModel):
    """A batch of pdf pages with content spanning a range of pages."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    page_range: tuple[int, int]
    extracted_content: AnalyzeResult
    batch_number: int
    batch_size_max: int


class PDFPagesBatch(BaseModel):
    """A batch of pdf pages with content spanning a range of pages."""

    page_range: tuple[int, int]
    batch_content: bytes
    batch_number: int
    batch_size_max: int
