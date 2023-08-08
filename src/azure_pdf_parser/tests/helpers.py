import re
import io


def is_valid_md5(input_string):
    """
    Check if the input string is a valid md5 hash.

    MD5 hashes are 32-character hexadecimal strings
    """
    md5_pattern = re.compile(r"^[a-fA-F0-9]{32}$")
    return bool(md5_pattern.match(input_string))


def is_valid_pdf(document_bytes: bytes) -> bool:
    """Check whether the bytes of a file correspond to a PDF file."""
    # Convert bytes to BytesIO
    document_io = io.BytesIO(document_bytes)
    return document_io.read(8).startswith(b"%PDF-1.")
