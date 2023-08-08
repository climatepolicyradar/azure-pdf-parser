from typing import Union

from azure_api_wrapper import AzureApiWrapper
from cpr_pdf_parser.base import ParsingConfig, LocalSaveConfig, S3SaveConfig


class CprPdfParser:
    """A class for configuring and handling the behaviour of pdf parsing at CPR."""

    def __init__(self, azure_client: AzureApiWrapper, parsing_config: ParsingConfig):
        """Initialize the class."""
        self.azure_client = azure_client
        self.parsing_config = parsing_config

    def parse_url(
        self,
        document_url: str,
        big_document: bool = False,
        save_name: Union[str, None] = None,
    ):
        """
        Parse a document from a url.

        Args:
            document_url: The url of the document to parse.
            big_document: Whether the document is large (>1500 pages).
            save_name: The name to save the document as.
        """
        # TODO call azure api
        if big_document:
            api_response = self.azure_client.analyze_large_document_from_url(
                document_url
            )
        else:
            api_response = self.azure_client.analyze_document_from_url(document_url)

        self.save(data=api_response.to_dict(), save_name=save_name)

        if self.parsing_config.parser_output_config.generate:
            pass

    def parse_file(self, document_path: str, big_document: bool = False):
        """Parse a document from a file path."""
        # TODO read in bytes

        # TODO call azure api

        # TODO use the parsing config to determine what to do with the response
        pass

    def save(self, data: dict, save_name: Union[str, None]) -> None:
        """Save the output of the parser."""
        save_config = self.parsing_config.api_response_config.save_config
        if save_config:
            if isinstance(save_config, LocalSaveConfig):
                # TODO save to local
                pass
            elif isinstance(save_config, S3SaveConfig):
                # TODO save to s3
                pass
            else:
                raise ValueError(
                    f"Invalid save config type {type(save_config)} for api response."
                )
