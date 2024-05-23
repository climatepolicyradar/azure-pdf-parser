import io
import logging
import sys
import time
from io import BytesIO
from typing import Optional, Sequence, Tuple, Union

import requests
from azure.ai.formrecognizer import AnalyzeResult, DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.core.polling import LROPoller

from .base import PDFPagesBatchExtracted
from .utils import call_api_with_error_handling, merge_responses, split_into_batches

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
        self,
        doc_url: str,
        timeout: Optional[Union[int, None]] = None,
        batch_size: Optional[int] = None,
    ) -> Tuple[Sequence[PDFPagesBatchExtracted], AnalyzeResult]:
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

        batches = split_into_batches(
            document_bytes=BytesIO(resp.content), batch_size=batch_size
        )

        page_api_responses = [
            PDFPagesBatchExtracted(
                page_range=batch.page_range,
                extracted_content=call_api_with_error_handling(
                    func=self.analyze_document_from_bytes,
                    retries=3,
                    doc_bytes=batch.batch_content,
                    timeout=timeout,
                ),
                batch_number=batch.batch_number,
                batch_size_max=batch.batch_size_max,
            )
            for batch in batches
        ]

        return page_api_responses, merge_responses(page_api_responses)

    def analyze_large_document_from_bytes(
        self,
        doc_bytes: bytes,
        timeout: Optional[Union[int, None]] = None,
        batch_size: Optional[int] = None,
    ) -> Tuple[Sequence[PDFPagesBatchExtracted], AnalyzeResult]:
        """Analyze a large pdf document (>1500 pages) in the bytes form."""
        logger.info(
            "Analyzing large document from bytes by splitting into individual pages...",
            extra={"props": {"bytes_size": sys.getsizeof(doc_bytes)}},
        )
        batches = split_into_batches(
            document_bytes=io.BytesIO(doc_bytes), batch_size=batch_size
        )
        page_api_responses = [
            PDFPagesBatchExtracted(
                page_range=batch.page_range,
                extracted_content=call_api_with_error_handling(
                    func=self.analyze_document_from_bytes,
                    retries=3,
                    doc_bytes=batch.batch_content,
                    timeout=timeout,
                ),
                batch_number=batch.batch_number,
                batch_size_max=batch.batch_size_max,
            )
            for batch in batches
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
