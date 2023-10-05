import hashlib
import io
from io import BytesIO
from typing import Sequence, Any, Optional
import logging

from pypdf import PdfReader, PdfWriter
from azure.ai.formrecognizer import AnalyzeResult

from .base import PDFPagesBatchExtracted, PDFPagesBatch

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
    if batch.extracted_content.paragraphs:
        for paragraph in batch.extracted_content.paragraphs:
            if paragraph and paragraph.bounding_regions:
                paragraph.bounding_regions[0].page_number = (
                    paragraph.bounding_regions[0].page_number + batch.page_range[0] - 1
                )

    if batch.extracted_content.tables:
        for table in batch.extracted_content.tables:
            for cell in table.cells:
                if cell and cell.bounding_regions:
                    for bounding_region in cell.bounding_regions:
                        bounding_region.page_number = (
                            bounding_region.page_number + batch.page_range[0] - 1
                        )

            if table.bounding_regions:
                for bounding_region in table.bounding_regions:
                    bounding_region.page_number = (
                        bounding_region.page_number + batch.page_range[0] - 1
                    )
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
    for batch in batches:
        if batch.extracted_content.paragraphs:
            all_paragraphs.extend(batch.extracted_content.paragraphs)
        if batch.extracted_content.tables:
            all_tables.extend(batch.extracted_content.tables)

    # Copy the first result to a variable and add the content for all the pages.
    merged_analyse_result: AnalyzeResult = batches.pop(0).extracted_content
    merged_analyse_result.paragraphs = all_paragraphs
    merged_analyse_result.tables = all_tables

    return merged_analyse_result


def split_into_batches(
    document_bytes: BytesIO, batch_size: Optional[int] = DEFAULT_BATCH_SIZE
) -> list[PDFPagesBatch]:
    if not batch_size:
        batch_size = DEFAULT_BATCH_SIZE

    if batch_size < 1:
        raise ValueError("Batch size must be greater than 0.")

    """Split the API response into a batch of pages."""
    logger.info(
        "Splitting pdf into batches.", extra={"props": {"batch size": batch_size}}
    )
    pdf = PdfReader(document_bytes)

    batches: list[list] = [
        pdf.pages[page_index : page_index + batch_size]
        for batch, page_index in enumerate(range(0, len(pdf.pages), batch_size))
    ]

    batches_with_bytes = []
    for index, batch in enumerate(batches):
        # Create a new PDF writer object
        pdf_writer = PdfWriter()

        # TODO check the page number is correct
        [pdf_writer.add_page(page) for page in batch]

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
                page_range=(batch[0].page_number + 1, batch[-1].page_number + 1),
                batch_number=index,
                batch_size_max=batch_size,
            )
        )

    return batches_with_bytes


def calculate_md5_sum(doc_bytes: bytes) -> str:
    """Calculate the md5 sum of the document bytes."""
    return hashlib.md5(doc_bytes).hexdigest()
