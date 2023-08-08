from azure_pdf_parser.tests.helpers import is_valid_md5, is_valid_pdf


def test_is_valid_md5() -> None:
    """Test that the function returns True for valid MD5 sums."""
    assert not is_valid_md5("Invalid MD5 sum")
    assert is_valid_md5("d41d8cd98f00b204e9800998ecf8427e")


def test_is_valid_pdf(one_page_pdf_bytes: bytes) -> None:
    """Test that the function returns True for valid PDF files."""
    assert not is_valid_pdf(b"Invalid PDF file")
    assert is_valid_pdf(one_page_pdf_bytes)
