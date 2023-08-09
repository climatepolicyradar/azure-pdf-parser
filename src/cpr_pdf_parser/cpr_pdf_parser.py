from typing import Union, Tuple

from azure.ai.formrecognizer import AnalyzeResult
from boto3.resources.base import ServiceResource
from cpr_data_access.parser_models import ParserInput, ParserOutput

from azure_api_wrapper import AzureApiWrapper
from cpr_pdf_parser.base import ParsingConfig, LocalSaveConfig, S3SaveConfig
from cpr_pdf_parser.convert import azure_api_response_to_parser_output


class CprPdfParser:
    """A class for configuring and handling the behaviour of pdf parsing at CPR."""

    def __init__(
        self,
        azure_client: AzureApiWrapper,
        config: ParsingConfig,
        s3_client: ServiceResource = None,
    ):
        """Initialize the class."""
        self.azure_client = azure_client
        self.config = config
        self.s3_client = s3_client
        self.validate_config()

    def validate_config(self):
        """Validate that we have an s3 client if we are saving to s3."""
        if (
            self.config.parser_output.save_config.__repr_name__() == "S3SaveConfig"
            or self.config.api_response.save_config.__repr_name__() == "S3SaveConfig"
            and self.s3_client is None
        ):
            raise ValueError("Must provide s3 client if saving to s3.")

    def parse_url(
        self,
        document_url: str,
        big_document: bool = False,
        save_name: Union[str, None] = None,
        parser_input: Union[ParserInput, None] = None,
    ) -> Union[AnalyzeResult, Tuple[AnalyzeResult, ParserOutput]]:
        """
        Parse a document from a url.

        Args:
            document_url: The url of the document to parse.
            big_document: Whether the document is large (>1500 pages).
            save_name: The name to save the document as.
            parser_input: The input to the parser. This should only be provided if
                wishing to convert the api response to a parser output object.
        """
        if self.config.parser_output.generate and parser_input is None:
            raise ValueError(
                "Must set parser input object if converting to parser output."
            )

        if big_document:
            api_response = self.azure_client.analyze_large_document_from_url(
                document_url
            )
        else:
            api_response = self.azure_client.analyze_document_from_url(document_url)

        self.save(data=api_response, save_name=save_name)

        if self.config.parser_output.generate:
            extract_tables = (
                True
                if self.config.parser_output.type.value is "Experimental"
                else False
            )
            parser_output = azure_api_response_to_parser_output(
                parser_input=parser_input,
                # FIXME: I think we can make this optional in the pydantic model
                md5_sum="12345",
                api_response=api_response,
                experimental_extract_tables=extract_tables,
            )

            self.save(data=parser_output, save_name=save_name)

            return api_response, parser_output
        # TODO need to add a return type here
        return api_response

    def parse_file(self, document_path: str, big_document: bool = False):
        """Parse a document from a file path."""
        pass

    def save(
        self, data: Union[ParserOutput, AnalyzeResult], save_name: Union[str, None]
    ) -> None:
        """Save the output of the parser."""
        # TODO generate save name if not provided
        save_config = self.config.api_response.save_config
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
