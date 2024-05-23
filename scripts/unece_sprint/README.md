# Docs for UNECE Sprint

<https://linear.app/climate-policy-radar/issue/RND-1278/documents-in-for-unece-sprint>

A group of experts from UNECE have volunteered their time/effort to help us with RAG evaluation labelling. They've sent us a list of documents which they would like to use in the sprint. These documents aren't yet in the CPR database, so we need to fetch and parse them. The `parse_docs.py` script uses the `azure_pdf_parser` cli runner to do this.

The pdfs and parser output objects are written to a local `data/` directory, which is not committed to version control. Instead, the data is persisted in an s3 bucket for later use.

The `check_parsed_docs.py` script runs a simple check to make sure that the docs in s3 can be loaded using the CPR SDK.
