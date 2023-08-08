from azure_api_wrapper import AzureApiWrapper
from cpr_pdf_parser.base import ParsingConfig


class CprPdfParser:
    """A class for configuring and handling the behaviour of pdf parsing at CPR."""

    def __init__(self, azure_client: AzureApiWrapper, parsing_config: ParsingConfig):
        """Initialize the class."""
        self.azure_client = azure_client
        self.parsing_config = parsing_config

    def parse_url(self, document_url: str):
        """Parse a document from a url."""
        # TODO call azure api

        # TODO use the parsing config to determine what to do with the response
        pass

    def parse_file(self, document_path: str):
        """Parse a document from a file path."""
        # TODO read in bytes

        # TODO call azure api

        # TODO use the parsing config to determine what to do with the response
        pass
