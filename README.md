# Azure PDF Parser 

[//]: # (TODO: Update the reamde)
[//]: # (TODO: Update py2pdf package - DeprecationWarning: PyPDF2 is deprecated. Please move to the pypdf library instead.)
[//]: # (TODO: Tag the dal to a specific version and specify this in poetry.)
[//]: # (TODO: Add detect_and_set_languages to the parser output object in dal.)
[//]: # (TODO: Update the types of text block in dal)
[//]: # (TODO: Split out anything that contains data access lib types into a separate packkage in this repo such that we have azure pdf parser and cpr pdf parser)

## Context 

This repo provides a python wrapper class for calling text extraction on local or url accessible pdf documents. 

Utility code is then provided to enable the conversion of this api response object to a Parser Output object.


## Setup 

Prior to using this wrapper class you will need to have an [Azure FormRecognizer processor](https://azure.microsoft.com/en-gb/products/form-recognizer) instantiated in the microsoft azure cloud. 

You will then need to identify your endpoint and key variables for access. 

## Usage

Install dependencies: 

        poetry install 

Enter the python shell: 

        python3 

Import the wrapper class and conversion function: 

        from azure_wrapper_temp.azure_wrapper import AzureApiWrapper
        
        from azure_wrapper.convert import azure_api_response_to_parser_output

Instantiate client connection and call text extraction on a pdf accessible via an endpoint. Then convert to a parser output object:

        azure_client = AzureApiWrapper(AZURE_KEY, AZURE_ENDPOINT)

        api_response = azure_client.analyze_document_from_url(
                            doc_url="https://example.com/file.pdf"
                        )
        
        parser_output = azure_api_response_to_parser_output(
                            api_response
                        )


        
