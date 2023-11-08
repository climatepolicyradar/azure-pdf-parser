import logging
from collections import Counter
from typing import Sequence, Optional, Union, List

from azure.ai.formrecognizer import Point
from cpr_data_access.parser_models import (
    PDFData,
    CONTENT_TYPE_HTML,
    CONTENT_TYPE_PDF,
    HTMLData,
    TextBlock,
)
from cpr_data_access.pipeline_general_models import BackendDocument
from langdetect import DetectorFactory, detect
from pydantic import BaseModel, AnyHttpUrl, model_validator

logger = logging.getLogger(__name__)

#  TODO add tests for the experimental types if we decide to keep them
#    Won't build until we do this


class ExperimentalBoundingRegion(BaseModel):
    """Region of a cell in a table."""

    page_number: int
    polygon: Sequence[Point]


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


class ExperimentalParserOutput(BaseModel):
    """Experimental parser output with pdf data containing tables."""

    document_id: str
    document_metadata: BackendDocument
    document_name: str
    document_description: str
    document_source_url: Optional[AnyHttpUrl] = None
    document_cdn_object: Optional[str] = None
    document_content_type: Optional[str] = None
    document_md5_sum: Optional[str] = None
    document_slug: str

    languages: Optional[Sequence[str]] = None
    translated: bool = False
    html_data: Optional[HTMLData] = None
    pdf_data: Optional[ExperimentalPDFData] = None

    @model_validator(mode="after")
    def check_html_pdf_metadata(self):
        """
        Validate the relationship between content-type and the data that is set.

        Check that html_data is set if content_type is HTML, or pdf_data is set if
        content_type is PDF.

        Check that if the content-type is not HTML or PDF, then html_data and pdf_data
        are both null.
        """
        if self.document_content_type == CONTENT_TYPE_HTML and self.html_data is None:
            raise ValueError("html_data must be set for HTML documents")

        if self.document_content_type == CONTENT_TYPE_PDF and self.pdf_data is None:
            raise ValueError("pdf_data must be set for PDF documents")

        if self.document_content_type not in {
            CONTENT_TYPE_HTML,
            CONTENT_TYPE_PDF,
        } and (self.html_data is not None or self.pdf_data is not None):
            raise ValueError(
                "html_data and pdf_data must be null for documents with no content type"
            )

        return self

    @property
    def text_blocks(self) -> Sequence[TextBlock]:
        """
        Return the text blocks in the document.

        These could differ in format depending on the content type.

        :return: Sequence[TextBlock]
        """
        if self.document_content_type == CONTENT_TYPE_HTML:
            html_data: Union[HTMLData, None] = self.html_data
            if html_data: 
                return html_data.text_blocks
        elif self.document_content_type == CONTENT_TYPE_PDF:
            pdf_data: Union[PDFData, None] = self.pdf_data
            if pdf_data:
                return pdf_data.text_blocks
        return []

    def to_string(self) -> str:  # type: ignore
        """Return the text blocks in the parser output as a string"""

        return " ".join(
            [text_block.to_string().strip() for text_block in self.text_blocks]
        )

    def detect_and_set_languages(self) -> "ExperimentalParserOutput":
        """
        Detect language of the text and set the language attribute.

        Return an instance of ParserOutput with the language attribute set. Assumes
        that a document only has one language.
        """

        # FIXME: We can remove this now as this api doesn't support language detection
        if self.document_content_type != CONTENT_TYPE_HTML:
            logger.warning(
                "Language detection should not be required for non-HTML documents, "
                "but it has been run on one. This will overwrite any document "
                "languages detected via other means, e.g. OCR. "
            )

        # language detection is not deterministic, so we need to set a seed
        DetectorFactory.seed = 0

        if len(self.text_blocks) > 0:
            detected_language = detect(self.to_string())
            self.languages = [detected_language]
            for text_block in self.text_blocks:
                text_block.language = detected_language

        return self

    def set_document_languages_from_text_blocks(
        self, min_language_proportion: float = 0.4
    ):
        """
        Store the document languages attribute as part of the object.

        This is done by getting all languages with proportion above
        `min_language_proportion`.

        :attribute min_language_proportion: Minimum proportion of text blocks in a
        language for it to be considered a language of the document.
        """

        all_text_block_languages = [
            text_block.language for text_block in self.text_blocks
        ]

        if all([lang is None for lang in all_text_block_languages]):
            self.languages = None

        else:
            lang_counter = Counter(
                [lang for lang in all_text_block_languages if lang is not None]
            )
            self.languages = [
                lang
                for lang, count in lang_counter.items()
                if count / len(all_text_block_languages) > min_language_proportion
            ]

        return self
