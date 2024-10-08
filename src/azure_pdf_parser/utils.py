import hashlib
import io
import logging
from io import BytesIO
from typing import Any, Optional, Sequence

from azure.ai.formrecognizer import AnalyzeResult
from pypdf import PdfReader, PdfWriter

from .base import PDFPagesBatch, PDFPagesBatchExtracted

logger = logging.getLogger(__name__)


DEFAULT_BATCH_SIZE = 50


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


def propagate_page_number(batch: PDFPagesBatchExtracted) -> PDFPagesBatchExtracted:
    """
    Correct the page numbers in the batch.

    This is done by propagating the page number of the start index of the batch to the
    paragraphs and tables.

    Page number in the batch is incremented as follows:

    [1,2,3,4] and a page range of 101-104 -> [101,102,103,104]
    Thus, incremented page number = page number + batch.page_range[0] - 1

    E.g.
    - page number 1 in the batch is page number 101 in the document (1 + 101 - 1).
    - page number 2 in the batch is page number 102 in the document (2 + 101 - 1).
    """
    page_offset = batch.page_range[0] - 1

    if batch.extracted_content.paragraphs:
        for paragraph in batch.extracted_content.paragraphs:
            if paragraph and paragraph.bounding_regions:
                paragraph.bounding_regions[0].page_number = (
                    paragraph.bounding_regions[0].page_number + page_offset
                )

    if batch.extracted_content.tables:
        for table in batch.extracted_content.tables:
            for cell in table.cells:
                if cell and cell.bounding_regions:
                    for bounding_region in cell.bounding_regions:
                        bounding_region.page_number = (
                            bounding_region.page_number + page_offset
                        )

            if table.bounding_regions:
                for bounding_region in table.bounding_regions:
                    bounding_region.page_number = (
                        bounding_region.page_number + page_offset
                    )

    for page in batch.extracted_content.pages:
        if page and page.page_number:
            page.page_number = page.page_number + page_offset
    return batch


def merge_responses(batches: Sequence[PDFPagesBatchExtracted]) -> AnalyzeResult:
    """
    Merge page batch responses from multiple API calls into one.

    Currently, merging is done by concatenating the paragraphs and tables from each
    page.

    This is as styles, documents, languages is found to be empty and we are only
    concerned with the tables and paragraphs for CPR purposes. If this changes,
    we will be storing the raw api responses and thus will be able to recover state.

    Note that the content field is not required to be appended to in the merge analyse
    result as this content duplicates the data in the paragraphs.
    """
    batches = [propagate_page_number(batch) for batch in batches]

    all_paragraphs = []
    all_tables = []
    all_pages = []
    for batch in batches:
        if batch.extracted_content.paragraphs:
            all_paragraphs.extend(batch.extracted_content.paragraphs)
        if batch.extracted_content.tables:
            all_tables.extend(batch.extracted_content.tables)
        all_pages.extend(batch.extracted_content.pages)

    merged_analyse_result = AnalyzeResult()
    merged_analyse_result.api_version = batches[0].extracted_content.api_version
    merged_analyse_result.model_id = batches[0].extracted_content.model_id
    merged_analyse_result.paragraphs = all_paragraphs
    merged_analyse_result.tables = all_tables
    merged_analyse_result.pages = all_pages

    return merged_analyse_result


def split_into_batches(
    document_bytes: BytesIO, batch_size: Optional[int] = None
) -> list[PDFPagesBatch]:
    if batch_size is None:
        batch_size = DEFAULT_BATCH_SIZE

    if batch_size < 1:
        raise ValueError("Batch size must be greater than 0.")

    """Split the API response into a batch of pages."""
    logger.info(
        "Splitting pdf into batches.", extra={"props": {"batch size": batch_size}}
    )
    pdf = PdfReader(document_bytes)

    page_batches: list[list] = [
        pdf.pages[page_index : page_index + batch_size]
        for page_index in range(0, len(pdf.pages), batch_size)
    ]

    batches_with_bytes = []
    for batch_index, pages in enumerate(page_batches):
        # Create a new PDF writer object
        pdf_writer = PdfWriter()

        # TODO check the page number is correct
        [pdf_writer.add_page(page) for page in pages]

        # Create a BytesIO buffer to write the PDF content
        output_buffer = io.BytesIO()
        pdf_writer.write(output_buffer)

        # Get the bytes content
        pdf_batch_bytes = output_buffer.getvalue()

        # TODO check the page number is correct
        # Adding one to the page range as we want to go from 1 -> n
        batches_with_bytes.append(
            PDFPagesBatch(
                batch_content=pdf_batch_bytes,
                page_range=(pages[0].page_number + 1, pages[-1].page_number + 1),
                batch_number=batch_index,
                batch_size_max=batch_size,
            )
        )

    return batches_with_bytes


def calculate_md5_sum(doc_bytes: bytes) -> str:
    """Calculate the md5 sum of the document bytes."""
    return hashlib.md5(doc_bytes).hexdigest()
