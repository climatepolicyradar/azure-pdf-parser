import io
from io import BytesIO
from typing import Sequence, Any
import logging

from PyPDF2 import PdfReader, PdfWriter
from azure.ai.formrecognizer import AnalyzeResult

from azure_wrapper_temp.base import PDFPage

logger = logging.getLogger(__name__)


def call_api_with_error_handling(retries: int, func, *args, **kwargs) -> Any:
    """Call an API function with retries and error handling."""
    logger.info(
        "Calling API function with retries...", extra={"props": {"retries": retries}}
    )
    for i in range(retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                "Error occurred while calling API function...",
                extra={"props": {"error": str(e)}},
            )
            if i == retries - 1:
                raise e


def propagate_page_number(page: PDFPage) -> PDFPage:
    """Propagate the page number to the paragraphs and tables."""
    for paragraph in page.extracted_content.paragraphs:
        paragraph.bounding_regions[0].page_number = page.page_number

    for table in page.extracted_content.tables:
        for cell in table.cells:
            for bounding_region in cell.bounding_regions:
                bounding_region.page_number = page.page_number

        for bounding_region in table.bounding_regions:
            bounding_region.page_number = page.page_number
    return page


def merge_responses(pages: Sequence[PDFPage]) -> AnalyzeResult:
    """Merge individual page responses from multiple API calls into one.

    Currently, merging is done by concatenating the paragraphs and tables from each page.
    """

    pages = [propagate_page_number(page) for page in pages]

    page_merged = pages[0].extracted_content

    [
        page_merged.paragraphs.append(page.extracted_content.paragraphs)
        for page in pages[1:]
    ]

    [page_merged.tables.append(page.extracted_content.tables) for page in pages[1:]]

    return page_merged


def split_into_pages(document_bytes: BytesIO) -> dict[int, bytes]:
    """Split the API response into individual pages."""
    pdf = PdfReader(document_bytes)

    pages_dict = {}
    total_pages = len(pdf.pages)
    for page_num in range(total_pages):
        writer = PdfWriter()
        writer.add_page(pdf.pages[page_num])
        pdf_bytes = io.BytesIO()
        writer.write(pdf_bytes)
        pdf_bytes.seek(0)
        pages_dict[page_num + 1] = pdf_bytes.read()

    return pages_dict
