from azure_pdf_parser.utils import calculate_md5_sum, is_valid_md5


def test_propagate_with_correct_page():
    pass


def test_merge_responses():
    pass


def test_split_into_pages():
    pass


def test_is_valid_md5() -> None:
    """Test that the function returns True for valid MD5 sums."""
    assert not is_valid_md5("Invalid MD5 sum")

    assert is_valid_md5("d41d8cd98f00b204e9800998ecf8427e")


def test_calculate_md5_sum(one_page_pdf_bytes: bytes) -> None:
    """Test that the md5 sum is calculated correctly."""

    md5_sum = calculate_md5_sum(one_page_pdf_bytes)
    assert isinstance(md5_sum, str)
    assert is_valid_md5(md5_sum)

    md5_sum = calculate_md5_sum(b"Random bytes!")
    assert isinstance(md5_sum, str)
    assert is_valid_md5(md5_sum)
