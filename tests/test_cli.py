from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from click.testing import CliRunner
from cpr_sdk.parser_models import ParserOutput

from src.azure_pdf_parser import AzureApiWrapper


def test_cli(
    mock_azure_client: AzureApiWrapper,
    one_page_pdf_bytes: bytes,
    two_page_pdf_bytes: bytes,
    monkeypatch,
):
    runner = CliRunner()

    monkeypatch.setenv("AZURE_PROCESSOR_KEY", "hello")
    monkeypatch.setenv("AZURE_PROCESSOR_ENDPOINT", "https://example.com/")

    # Note: import needed here so that the monkeypatch works, otherwise the
    # environment variables are retrieved before the monkeypatch is applied.

    with TemporaryDirectory() as temp_dir:
        pdf_dir = Path(temp_dir)
        (pdf_dir / "test1.pdf").write_bytes(one_page_pdf_bytes)
        (pdf_dir / "test2.pdf").write_bytes(two_page_pdf_bytes)

        output_dir = Path(temp_dir) / "output"

        # patch the azure client with mock
        with patch("azure_pdf_parser.AzureApiWrapper", return_value=mock_azure_client):
            from src.cli import cli

            result = runner.invoke(
                cli, ["--pdf-dir", str(pdf_dir), "--output-dir", str(output_dir)]
            )

        assert result.exit_code == 0
        assert (output_dir / "test1.json").exists()
        assert (output_dir / "test2.json").exists()
        assert len(list(output_dir.glob("*.json"))) == 2


def test_cli_with_source_urls(
    mock_azure_client: AzureApiWrapper,
    one_page_pdf_bytes: bytes,
    two_page_pdf_bytes: bytes,
    monkeypatch,
):
    runner = CliRunner()

    monkeypatch.setenv("AZURE_PROCESSOR_KEY", "hello")
    monkeypatch.setenv("AZURE_PROCESSOR_ENDPOINT", "https://example.com/")

    # Note: import needed here so that the monkeypatch works, otherwise the
    # environment variables are retrieved before the monkeypatch is applied.

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        source_urls = ["https://example.com/", "https://example.com/"]
        import_ids = ["CCLW.executive.1.1", "CCLW.executive.1.2"]

        # patch the azure client with mock
        with patch("azure_pdf_parser.AzureApiWrapper", return_value=mock_azure_client):
            from src.cli import cli

            result = runner.invoke(
                cli,
                [
                    "--output-dir",
                    str(output_dir),
                    "--id-and-source-url",
                    import_ids[0],
                    source_urls[0],
                    "--id-and-source-url",
                    import_ids[1],
                    source_urls[1],
                ],
            )

        assert result.exit_code == 0
        assert (output_dir / "CCLW.executive.1.1.json").exists()
        assert (output_dir / "CCLW.executive.1.2.json").exists()
        output_dir_files = output_dir.glob("*.json")
        assert len(list(output_dir_files)) == 2
        for file in output_dir_files:
            parser_output = ParserOutput.model_validate_json(file.read_text())
            assert parser_output.document_id == file.stem


def test_cli_importable(mock_azure_client, monkeypatch):
    monkeypatch.setenv("AZURE_PROCESSOR_KEY", "hello")
    monkeypatch.setenv("AZURE_PROCESSOR_ENDPOINT", "https://example.com/")

    with TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "output"
        source_urls = ["https://example.com/", "https://example.com/"]
        import_ids = ["CCLW.executive.1.1", "CCLW.executive.1.2"]

        # patch the azure client with mock
        with patch("azure_pdf_parser.AzureApiWrapper", return_value=mock_azure_client):
            from src.cli import run_parser

            run_parser(
                output_dir=output_dir,
                ids_and_source_urls=zip(import_ids, source_urls),
            )

        assert (output_dir / "CCLW.executive.1.1.json").exists()
        assert (output_dir / "CCLW.executive.1.2.json").exists()
        output_dir_files = output_dir.glob("*.json")
        assert len(list(output_dir_files)) == 2
        for file in output_dir_files:
            parser_output = ParserOutput.model_validate_json(file.read_text())
            assert parser_output.document_id == file.stem
