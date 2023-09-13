# Azure PDF Parser 

## Context 

This repo provides a python wrapper class for calling text extraction on local or url accessible pdf documents. 

Utility code is then provided to enable the conversion of this api response object to a Parser Output object.


## Setup 

Prior to using this wrapper class you will need to have an [Azure FormRecognizer processor](https://azure.microsoft.com/en-gb/products/form-recognizer) instantiated in the microsoft azure cloud. 

You will then need to identify your endpoint and key variables for access. 

## Usage

### Via CLI

The CLI takes as input a directory of pdfs and outputs a directory of 'blank' parser output JSON files, with only the document_id, document_name, text blocks and page metadata fields populated.

1. Install extra `cli` dependency group: `poetry install --with cli`
2. Populate environment variables (see `.env.example`)
3. Run the CLI: `poetry run python -m src.cli --pdf-dir <path to pdf directory> --output-dir <path to output directory>`



### Programatically

Install dependencies and enter the python shell: 

        poetry install
        python3 

Import the wrapper class and conversion function: 

        from azure_pdf_parser import AzureApiWrapper
        from azure_pdf_parser import azure_api_response_to_parser_output

Instantiate client connection and call text extraction on a pdf accessible via an endpoint. Then convert to a parser output object:

        azure_client = AzureApiWrapper(AZURE_KEY, AZURE_ENDPOINT)

        api_response = azure_client.analyze_document_from_url(
            doc_url="https://example.com/file.pdf"
        )
        
        parser_output = azure_api_response_to_parser_output(
            parser_input=parser_input,
            md5_sum=md5_sum,
            api_response=api_response,
            experimental_extract_tables=True,
        )


One has four options for calling the text extraction api:

1. `analyze_document_from_url` - Pass a url to a pdf document.
2. `analyze_document_from_bytes` - Pass a byte string of a pdf document.
3. `analyze_large_document_from_url` - Pass a url to a pdf document that's greater than ~1500 pages.
4. `analyze_large_document_from_bytes` - Pass a bytes string of a pdf document that's greater than ~1500 pages. 

The reason we have two different methods for large documents is so the Azure API can provide functionality for a user to provide either the bytes of a document or the url of the document. For the `analyze_large_document_from_url` method the azure wrapper will then handle the download of the document from source as well as the splitting of the document and calling of the api. 

The package also provides functionality to extract tables from the pdf document. This is an experimental feature and is not recommended for use in production. This can be configured by setting the `experimental_extract_tables` flag to `True` when calling the `azure_api_response_to_parser_output` function. This defaults to `False`.