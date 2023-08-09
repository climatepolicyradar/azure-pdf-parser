from typing import Union, Optional

from azure.ai.formrecognizer import AnalyzeResult
from cpr_data_access.parser_models import ParserOutput
from pydantic import BaseModel, root_validator
from enum import Enum

from cpr_pdf_parser.experimental_base import ExperimentalParserOutput


class ParserOutputTypes(str, Enum):
    """
    Enum for the different types of parser output.

    Default: Default parser output with no tables.
    Experimental: Experimental parser output with tables.
    """

    Default = "Default"
    Experimental = "Experimental"


class S3SaveConfig(BaseModel):
    """A class for configuring the saving of files to S3."""

    output_bucket: str
    output_prefix: str


class LocalSaveConfig(BaseModel):
    """A class for configuring the saving of files locally."""

    output_dir: str


class ParserOutputConfig(BaseModel):
    """A class for configuring the parser output logic of the parser."""

    generate: bool = True
    type: ParserOutputTypes = ParserOutputTypes.Default
    save_config: Optional[Union[S3SaveConfig, LocalSaveConfig]] = None

    @root_validator()
    def check_generating_output_if_saving(self) -> "ParserOutputConfig":
        """Check that if saving output then we are generating it."""
        if self.save_config is not None and not self.generate:
            raise ValueError("Must be generating output if saving it!")
        return self


class ApiResponseConfig(BaseModel):
    """A class for configuring the api response logic of the parser."""

    save_config: Optional[Union[S3SaveConfig, LocalSaveConfig]] = None


class ParsingConfig(BaseModel):
    """A class for configuring the behaviour of pdf parsing at CPR."""

    parser_output: ParserOutputConfig
    api_response: ApiResponseConfig


class ParsedDocumentResponse(BaseModel):
    """A response from the CPR PDF Parser from a document parsing operation."""

    parser_output: Optional[Union[ParserOutput, ExperimentalParserOutput]] = None
    api_response: Optional[AnalyzeResult] = None
