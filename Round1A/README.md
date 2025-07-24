# Adobe India Hackathon - Round 1A Submission

## PDF Outline Extractor

This solution extracts structured outlines (title and headings) from PDF documents and outputs them in JSON format.

### Approach

1. *PDF Processing*: Uses PyMuPDF (fitz) for efficient PDF text extraction
2. *Heading Detection*: Implements font-size based heading level detection
3. *Title Extraction*: Uses the first H1 heading or filename as fallback
4. *Output Generation*: Creates valid JSON in the specified format

### Dependencies

- Python 3.8+
- PyMuPDF (fitz)

### Build and Run

1. Build the Docker image:
   ```bash
   docker build --platform linux/amd64 -t pdf-outline-extractor .