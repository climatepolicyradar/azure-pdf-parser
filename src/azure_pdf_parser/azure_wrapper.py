import io
import sys
from io import BytesIO
import time
from typing import Tuple, Sequence, Union, Optional
import logging
import requests

from azure.ai.formrecognizer import AnalyzeResult, DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.polling import LROPoller

from azure_pdf_parser.utils import split_into_pages, merge_responses
from azure_pdf_parser.experimental_base import PDFPage
from azure_pdf_parser.utils import call_api_with_error_handling

logger = logging.getLogger(__name__)


class AzureApiWrapper:
    """Wrapper for Azure Form Extraction API."""

    def __init__(self, key: str, endpoint: str):
        logger.info(
            "Initializing Azure API wrapper with endpoint...",
            extra={"props": {"endpoint": endpoint}},
        )
        self.document_analysis_client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key),
        )

    def analyze_document_from_url(
        self, doc_url: str, timeout: Optional[Union[int, None]] = None
    ) -> AnalyzeResult:
        """Analyze a pdf document accessible by an endpoint."""
        logger.info("Analyzing document from url...", extra={"props": {"url": doc_url}})
        poller = self.document_analysis_client.begin_analyze_document_from_url(
            "prebuilt-document",
            doc_url,
        )

        self.poller_loop(poller)

        return poller.result(timeout=timeout)

    def analyze_document_from_bytes(
        self, doc_bytes: bytes, timeout: Optional[Union[int, None]] = None
    ) -> AnalyzeResult:
        """Analyze a pdf document in the form of bytes."""
        logger.info(
            "Analyzing document from bytes...",
            extra={"props": {"bytes_size": sys.getsizeof(doc_bytes)}},
        )
        poller = self.document_analysis_client.begin_analyze_document(
            "prebuilt-document",
            doc_bytes,
        )

        self.poller_loop(poller)

        return poller.result(timeout=timeout)

    def analyze_large_document_from_url(
        self, doc_url: str, timeout: Optional[Union[int, None]] = None
    ) -> Tuple[Sequence[PDFPage], AnalyzeResult]:
        """Analyze a large pdf document (>1500 pages) accessible by an endpoint."""
        logger.info(
            "Analyzing large document from url by splitting into individual pages...",
            extra={"props": {"url": doc_url}},
        )
        resp: requests.Response = call_api_with_error_handling(
            func=requests.get, retries=3, url=doc_url
        )
        if resp.status_code != 200:
            resp.raise_for_status()

        pages_dict = split_into_pages(document_bytes=BytesIO(resp.content))

        page_api_responses = [
            PDFPage(
                page_number=page_num,
                extracted_content=call_api_with_error_handling(
                    func=self.analyze_document_from_bytes,
                    retries=3,
                    doc_bytes=page_bytes,
                    timeout=timeout,
                ),
            )
            for page_num, page_bytes in pages_dict.items()
        ]

        return page_api_responses, merge_responses(page_api_responses)

    def analyze_large_document_from_bytes(
        self, doc_bytes: bytes, timeout: Optional[Union[int, None]] = None
    ) -> Tuple[Sequence[PDFPage], AnalyzeResult]:
        """Analyze a large pdf document (>1500 pages) in the bytes form."""
        logger.info(
            "Analyzing large document from bytes by splitting into individual pages...",
            extra={"props": {"bytes_size": sys.getsizeof(doc_bytes)}},
        )
        pages = split_into_pages(document_bytes=io.BytesIO(doc_bytes))
        page_api_responses = [
            PDFPage(
                page_number=page_num,
                extracted_content=call_api_with_error_handling(
                    func=self.analyze_document_from_bytes,
                    retries=3,
                    doc_bytes=page_bytes,
                    timeout=timeout,
                ),
            )
            for page_num, page_bytes in pages.items()
        ]

        return page_api_responses, merge_responses(page_api_responses)

    @staticmethod
    def poller_loop(poller: LROPoller[AnalyzeResult]) -> None:
        """Poll the status of the poller until it is done."""
        counter = 0
        logger.info(f"Poller status {poller.status()}...")
        while not poller.done():
            time.sleep(0.2)
            counter += 1
            if counter % 50 == 0:
                logger.info(f"Poller status {poller.status()}...")
        logger.info(f"Poller status {poller.status()}...")
