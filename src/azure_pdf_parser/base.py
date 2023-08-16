from azure.ai.formrecognizer import AnalyzeResult
from pydantic import BaseModel

DIMENSION_CONVERSION_FACTOR = 72


class PDFPage(BaseModel):
    """Pdf document page object with content and page number."""

    class Config:
        """Config for the pydantic model to use AnalyzeResult."""

        arbitrary_types_allowed = True

    page_number: int
    extracted_content: AnalyzeResult
