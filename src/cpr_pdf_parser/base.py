from typing import Union, Optional

from pydantic import BaseModel, root_validator
from enum import Enum


class ParserOutputTypes(str, Enum):
    """Enum for the different types of parser output."""

    Default = "Default"
    Experimental = "Experimental"


class S3SaveConfig(BaseModel):
    """A class for configuring the saving of files to S3."""

    output_bucket: str
    output_prefix: str
    aws_access_key_id: str
    aws_secret_access_key: str


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

    parser_output_config: ParserOutputConfig
    api_response_config: ApiResponseConfig
