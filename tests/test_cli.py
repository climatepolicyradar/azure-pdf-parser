from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from click.testing import CliRunner

from src.azure_pdf_parser import AzureApiWrapper
from src.cli import cli


def test_cli(
    mock_azure_client: AzureApiWrapper,
    one_page_pdf_bytes: bytes,
    two_page_pdf_bytes: bytes,
    monkeypatch,
):
    runner = CliRunner()

    monkeypatch.setenv("AZURE_PROCESSOR_KEY", "hello")
    monkeypatch.setenv(
        "AZURE_PROCESSOR_ENDPOINT",
        "https://pipeline-1-text-extraction.cognitiveservices.azure.com/",
    )

    with TemporaryDirectory() as temp_dir:
        pdf_dir = Path(temp_dir)
        (pdf_dir / "test1.pdf").write_bytes(one_page_pdf_bytes)
        (pdf_dir / "test2.pdf").write_bytes(two_page_pdf_bytes)

        output_dir = Path(temp_dir) / "output"

        # patch the azure client with mock
        with patch("src.cli.AzureApiWrapper", return_value=mock_azure_client):
            result = runner.invoke(
                cli, ["--pdf-dir", str(pdf_dir), "--output-dir", str(output_dir)]
            )

        assert result.exit_code == 0
        assert (output_dir / "test1.json").exists()
        assert (output_dir / "test2.json").exists()
        assert len(list(output_dir.glob("*.json"))) == 2
