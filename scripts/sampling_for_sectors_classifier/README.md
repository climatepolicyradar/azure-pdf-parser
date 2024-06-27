# Sampling for sectors classifier

We're currently trying to build a classifier for [economic sectors](https://climatepolicyradar.wikibase.cloud/wiki/Item:Q709).To build classifiers for the more nuanced subconcepts, we need to collect a set of hand-labelled passages of text which pertain to each concept. To build that hand-labelled dataset, we need data for labelling, and for that, we need to parse a whole load of new documents.

This script parses a set of docs from MCFs and corporate disclosures so that they can be sampled by a separate script in the knowledge-graph repo.

The script uses the `azure_pdf_parser` cli runner to do this. The pdfs and parser output objects are written to a local `data/` directory, which is not committed to version control. Instead, the data is persisted in an s3 bucket for later use.
