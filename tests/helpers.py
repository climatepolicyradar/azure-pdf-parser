import io
import json
import re
from typing import Union


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


def read_local_json_file(file_path: str) -> Union[list[dict], dict]:
    """Read a local json file and return the data."""
    with open(file_path) as json_file:
        data = json.load(json_file)
    return data


def read_pdf_to_bytes(file_path: str) -> bytes:
    """Read a pdf to bytes from a local path."""
    with open(file_path, "rb") as file:
        pdf_bytes = file.read()
    return pdf_bytes
