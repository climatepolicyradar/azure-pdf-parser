import pytest
from azure.ai.formrecognizer import AnalyzeResult, DocumentParagraph, DocumentTable
from cpr_data_access.parser_models import ParserInput

from cpr_pdf_parser.tests.helpers import read_local_json_file


@pytest.fixture()
def one_page_analyse_result() -> AnalyzeResult:
    """Mock response for the analyse document from url endpoint."""
    data = read_local_json_file("./src/cpr_pdf_parser/tests/data/sample-one-page.json")
    return AnalyzeResult.from_dict(data[0])


@pytest.fixture
def document_paragraph() -> DocumentParagraph:
    """Construct a document paragraph object."""
    data = read_local_json_file(
        "./src/cpr_pdf_parser/tests/data/document-paragraph.json"
    )
    return DocumentParagraph.from_dict(data)


@pytest.fixture
def document_table() -> DocumentTable:
    """Construct a document table object."""
    data = read_local_json_file("./src/cpr_pdf_parser/tests/data/document-table.json")
    return DocumentTable.from_dict(data)


@pytest.fixture
def parser_input() -> ParserInput:
    """A parser input object"""
    return ParserInput(
        document_id="123",
        document_metadata={"metadata_key": "metadata_value"},
        document_name="name",
        document_description="description",
        document_source_url="https://example.com",
        document_cdn_object="cdn_object",
        document_content_type="application/pdf",
        document_md5_sum="md5_sum_123_name",
        document_slug="slug_123_name",
    )


@pytest.fixture
def parser_input_empty_optional_fields() -> ParserInput:
    """A parser input object with empty optional fields"""
    return ParserInput(
        document_id="123",
        document_metadata={"metadata_key": "metadata_value"},
        document_name="name",
        document_description="description",
        document_slug="slug_123_name",
    )
