import logging
from pathlib import Path
from typing import Iterable, Optional

import click

from azure_pdf_parser.run import run_parser

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


@click.command()
@click.option(
    "--id-and-source-url",
    help="Document ID and source url tuple to process.",
    required=False,
    multiple=True,
    type=click.Tuple([str, str]),
)
@click.option(
    "--pdf-dir",
    help="Path to dir containing pdfs to process with document id's as filenames.",
    required=False,
    type=click.Path(exists=True, file_okay=False, path_type=Path),
)
@click.option(
    "--output-dir",
    help="""Path to directory to write output JSONs to. Filenames and document IDs are 
    be the filenames of the PDFs without extensions. Directory will be created if it 
    doesn't exist.""",
    required=True,
    type=click.Path(file_okay=False, path_type=Path),
)
@click.option(
    "--save-raw-azure-response",
    help="""Whether to save the raw Azure API response to disk. Saved to same directory 
    as output JSONs with suffix '_raw'.""",
    is_flag=True,
)
@click.option(
    "--experimental-extract-tables",
    help="Whether to extract tables from the PDFs. (WARNING: EXPERIMENTAL)",
    is_flag=True,
    default=False,
)
def cli(
    id_and_source_url: Optional[Iterable[tuple[str, str]]],
    pdf_dir: Optional[Path],
    output_dir: Path,
    save_raw_azure_response: bool,
    experimental_extract_tables: bool,
) -> None:
    return run_parser(
        output_dir=output_dir,
        ids_and_source_urls=id_and_source_url,
        pdf_dir=pdf_dir,
        save_raw_azure_response=save_raw_azure_response,
        experimental_extract_tables=experimental_extract_tables,
    )


if __name__ == "__main__":
    cli()
