import json
from typing import Any


def read_local_json_file(file_path: str) -> Any:
    """Read a local json file and return the data."""
    with open(file_path) as json_file:
        data = json.load(json_file)
    return data
