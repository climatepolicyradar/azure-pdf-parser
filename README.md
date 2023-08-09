# Azure PDF Parser 

[//]: # (TODO: Update the reamde)
[//]: # (TODO: Update py2pdf package - DeprecationWarning: PyPDF2 is deprecated. Please move to the pypdf library instead.)
[//]: # (TODO: Tag the dal to a specific version and specify this in poetry.)
[//]: # (TODO: Add detect_and_set_languages to the parser output object in dal.)
[//]: # (TODO: Update the types of text block in dal)
[//]: # (TODO: Split out anything that contains data access lib types into a separate packkage in this repo such that we have azure pdf parser and cpr pdf parser)

## Context 

This repo provides two python packages. A python wrapper class for azure text extraction api and a package for using this response for our purposes at cpr. 


## Design Decisions 

1. Separate Distinct packages: 
    * The `azure_api_wrapper` provides a generic wrapper for calling the azure api. This means that the package knows nothing of our CPR data model and could be used in isolation if a user desired to simply extract text from pdf documents using python.
    * The `cpr_pdf_parser` provides more useful functionality for us at CPR by converting the response to our data model, providing the option to save to s3 or locally etc. 
      * The arguments to this parser contain a client connection to s3 and the azure api as well as the config for the parser. This means that we can front load any connection issues in the program as well as any configuration value errors.
      * Experimental types are implemented as an option to extract tables. 
    * Decision to pull down the documents and use the from bytes endpoint. 
      * This allows us to get the md5sum 
      * Identify whether the document is a large document and thus, which endpoint we should use (default or large document).

        
