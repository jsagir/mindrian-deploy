# Google Document AI Implementation Plan

## Overview

Use Google Document AI to process educational materials (PDFs, slides, worksheets) with advanced OCR capabilities including Math OCR for LaTeX extraction.

## Why Document AI?

| Current Approach | Document AI Advantage |
|------------------|----------------------|
| Basic PDF text extraction | 200+ language support, handwriting detection |
| No math support | **Math OCR → LaTeX** extraction |
| Flat text output | Structured layout (blocks, paragraphs, tables) |
| No form processing | Checkbox detection, form field extraction |

## Pricing Summary

| Feature | Cost | Volume Discount |
|---------|------|-----------------|
| Enterprise Document OCR | $1.50/1K pages | $0.60/1K after 5M pages |
| Math OCR add-on | ~$6/1K pages | Premium feature |
| Layout Parser | $10/1K pages | Structured extraction |
| Form Parser | $30/1K pages | Key-value pairs |

**Free tier**: $300 credits for new GCP accounts

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCUMENT PROCESSING PIPELINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   User Upload                                                    │
│       │                                                          │
│       ▼                                                          │
│   ┌─────────────┐                                               │
│   │  Chainlit   │  File upload handler                          │
│   │  on_upload  │                                               │
│   └──────┬──────┘                                               │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              DOCUMENT AI PROCESSOR                       │  │
│   │                                                          │  │
│   │  1. Enterprise Document OCR (text + layout)             │  │
│   │  2. Math OCR (equations → LaTeX)                        │  │
│   │  3. Checkbox extraction (assessments)                   │  │
│   │  4. Table extraction (data)                             │  │
│   │                                                          │  │
│   └──────┬──────────────────────────────────────────────────┘  │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              POST-PROCESSING                             │  │
│   │                                                          │  │
│   │  • Convert LaTeX to display format                      │  │
│   │  • Structure tables as markdown                         │  │
│   │  • Extract checkbox states                              │  │
│   │  • Preserve layout hierarchy                            │  │
│   │                                                          │  │
│   └──────┬──────────────────────────────────────────────────┘  │
│          │                                                       │
│          ▼                                                       │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │  Gemini     │    │   Neo4j     │    │  Supabase   │        │
│   │  Embedding  │    │  (entities) │    │  (storage)  │        │
│   └─────────────┘    └─────────────┘    └─────────────┘        │
│          │                  │                  │                 │
│          └──────────────────┴──────────────────┘                │
│                             │                                    │
│                             ▼                                    │
│                      File Search RAG                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: Basic Integration (Week 1)

**Goal**: Replace current PDF extraction with Document AI OCR

```python
# tools/document_ai.py

from google.cloud import documentai_v1 as documentai
import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = "us"  # or "eu"
PROCESSOR_ID = os.getenv("DOCAI_PROCESSOR_ID")

async def process_document(
    file_content: bytes,
    mime_type: str = "application/pdf",
    enable_math_ocr: bool = False
) -> dict:
    """
    Process document with Google Document AI.

    Returns:
        {
            "text": str,           # Full extracted text
            "pages": list,         # Per-page content
            "tables": list,        # Extracted tables
            "equations": list,     # LaTeX equations (if math_ocr enabled)
            "checkboxes": list,    # Checkbox states
            "confidence": float    # OCR confidence score
        }
    """
    client = documentai.DocumentProcessorServiceClient()

    # Configure processing options
    process_options = documentai.ProcessOptions(
        ocr_config=documentai.OcrConfig(
            enable_native_pdf_parsing=True,
            premium_features=documentai.OcrConfig.PremiumFeatures(
                enable_math_ocr=enable_math_ocr,
            )
        )
    )

    request = documentai.ProcessRequest(
        name=f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}",
        raw_document=documentai.RawDocument(
            content=file_content,
            mime_type=mime_type
        ),
        process_options=process_options
    )

    result = client.process_document(request=request)
    document = result.document

    return {
        "text": document.text,
        "pages": extract_pages(document),
        "tables": extract_tables(document),
        "equations": extract_equations(document) if enable_math_ocr else [],
        "checkboxes": extract_checkboxes(document),
        "confidence": calculate_confidence(document)
    }
```

**Tasks**:
- [ ] Create GCP project and enable Document AI API
- [ ] Create Enterprise Document OCR processor
- [ ] Implement `tools/document_ai.py`
- [ ] Update `utils/file_processor.py` to use Document AI
- [ ] Add environment variables to Render

### Phase 2: Math OCR Integration (Week 2)

**Goal**: Extract equations from course materials as LaTeX

```python
def extract_equations(document) -> list:
    """Extract math equations as LaTeX."""
    equations = []

    for page in document.pages:
        for math_formula in page.math_formulas:
            equations.append({
                "latex": math_formula.detected_latex,
                "confidence": math_formula.confidence,
                "page": page.page_number,
                "bounding_box": get_bounding_box(math_formula.layout)
            })

    return equations


def format_equation_for_display(latex: str) -> str:
    """Format LaTeX for markdown display."""
    # Inline: $equation$
    # Block: $$equation$$
    if "\n" in latex or len(latex) > 50:
        return f"$$\n{latex}\n$$"
    return f"${latex}$"
```

**Tasks**:
- [ ] Enable Math OCR premium feature
- [ ] Implement equation extraction
- [ ] Add LaTeX rendering support in Chainlit (KaTeX/MathJax)
- [ ] Test with PWS course materials containing equations

### Phase 3: Structured Extraction (Week 3)

**Goal**: Extract tables, forms, and checkboxes from worksheets

```python
def extract_tables(document) -> list:
    """Extract tables as structured data."""
    tables = []

    for page in document.pages:
        for table in page.tables:
            rows = []
            for row in table.body_rows:
                cells = [get_cell_text(cell) for cell in row.cells]
                rows.append(cells)

            headers = []
            for row in table.header_rows:
                headers = [get_cell_text(cell) for cell in row.cells]

            tables.append({
                "headers": headers,
                "rows": rows,
                "page": page.page_number
            })

    return tables


def extract_checkboxes(document) -> list:
    """Extract checkbox states from forms."""
    checkboxes = []

    for page in document.pages:
        for visual_element in page.visual_elements:
            if visual_element.type_ == "checkbox":
                checkboxes.append({
                    "checked": visual_element.detected_checkbox.state == "CHECKED",
                    "confidence": visual_element.confidence,
                    "context": get_surrounding_text(visual_element, document)
                })

    return checkboxes
```

**Tasks**:
- [ ] Implement table extraction with markdown conversion
- [ ] Implement checkbox extraction
- [ ] Update RAG pipeline to handle structured content
- [ ] Create assessment parser for PWS worksheets

### Phase 4: Batch Processing (Week 4)

**Goal**: Process entire course material libraries efficiently

```python
async def batch_process_documents(
    gcs_input_uri: str,
    gcs_output_uri: str,
    enable_math_ocr: bool = True
) -> str:
    """
    Batch process multiple documents from Cloud Storage.

    Args:
        gcs_input_uri: gs://bucket/input/folder/
        gcs_output_uri: gs://bucket/output/folder/

    Returns:
        Operation name for tracking
    """
    client = documentai.DocumentProcessorServiceClient()

    gcs_documents = documentai.GcsDocuments(
        documents=[
            documentai.GcsDocument(
                gcs_uri=gcs_input_uri,
                mime_type="application/pdf"
            )
        ]
    )

    input_config = documentai.BatchDocumentsInputConfig(
        gcs_documents=gcs_documents
    )

    output_config = documentai.DocumentOutputConfig(
        gcs_output_config=documentai.DocumentOutputConfig.GcsOutputConfig(
            gcs_uri=gcs_output_uri
        )
    )

    request = documentai.BatchProcessRequest(
        name=f"projects/{PROJECT_ID}/locations/{LOCATION}/processors/{PROCESSOR_ID}",
        input_documents=input_config,
        document_output_config=output_config
    )

    operation = client.batch_process_documents(request=request)
    return operation.operation.name
```

**Tasks**:
- [ ] Set up Cloud Storage buckets for batch processing
- [ ] Implement batch processing pipeline
- [ ] Create progress tracking UI
- [ ] Process entire PWS course library

## Cost Estimation

### Current PWS Materials

| Material Type | Est. Pages | OCR Cost | Math OCR | Total |
|--------------|-----------|----------|----------|-------|
| Lecture slides | ~500 | $0.75 | $3.00 | $3.75 |
| Worksheets | ~200 | $0.30 | $1.20 | $1.50 |
| Case studies | ~300 | $0.45 | - | $0.45 |
| **Total** | **~1,000** | **$1.50** | **$4.20** | **$5.70** |

**One-time processing cost**: ~$6 for entire course library

### Ongoing Usage

| Scenario | Pages/Month | Est. Cost |
|----------|-------------|-----------|
| Light (few uploads) | 100 | $0.15 |
| Medium (active class) | 1,000 | $1.50 |
| Heavy (multiple cohorts) | 10,000 | $15.00 |

## Environment Variables

```bash
# Add to Render
GCP_PROJECT_ID=mindrian-prod
GCP_LOCATION=us
DOCAI_PROCESSOR_ID=abc123...
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## Alternative: Use Existing Gemini

Before implementing Document AI, consider that **Gemini 2.5** can:
- Read PDFs natively (via File API)
- Extract text and understand layout
- Process images and diagrams
- Understand math (though not output LaTeX)

**Document AI is better when you need**:
- **LaTeX output** for equations
- **Checkbox detection** for assessments
- **High-volume batch processing**
- **Structured table extraction**
- **Handwriting recognition**

## Decision: Phased Approach

1. **Start with Gemini** for general document understanding (free with API)
2. **Add Document AI** when specific features are needed:
   - Math OCR for equation-heavy materials
   - Batch processing for large libraries
   - Form parsing for assessments

## Resources

- [Document AI Python Codelab](https://codelabs.developers.google.com/codelabs/docai-ocr-python)
- [Enterprise Document OCR Docs](https://docs.cloud.google.com/document-ai/docs/enterprise-document-ocr)
- [Document AI Pricing](https://cloud.google.com/document-ai/pricing)
- [Math OCR Feature](https://docs.cloud.google.com/document-ai/docs/enterprise-document-ocr#math_ocr)

---

## Implementation Status: DONE ✅

The smart Document AI fallback is now implemented:

### Files Created/Modified

- `tools/document_ai.py` - Document AI wrapper with smart detection
- `utils/file_processor.py` - Enhanced with `smart_process_file()` function

### How It Works

```python
# Standard processing (uses PyPDF2, docx, etc.)
content, metadata = process_uploaded_file(file_path, file_name)

# Smart processing (auto-detects when Document AI is needed)
content, metadata = await smart_process_file(file_path, file_name)

# Force Document AI
content, metadata = await smart_process_file(file_path, file_name, force_document_ai=True)
```

### Auto-Detection Triggers

Document AI is automatically used when:
1. File is an image (JPG, PNG, etc.) → needs OCR
2. PDF extraction returns < 100 chars → likely scanned
3. Math content detected → LaTeX extraction
4. Explicitly forced by user

### Setup (When Ready to Enable)

1. **Create GCP Project** and enable Document AI API
2. **Create Processor**:
   - Go to Document AI Console
   - Create "Enterprise Document OCR" processor
   - Copy the Processor ID
3. **Add Environment Variables** to Render:
   ```
   GCP_PROJECT_ID=your-project-id
   GCP_LOCATION=us
   DOCAI_PROCESSOR_ID=your-processor-id
   ```
4. **Add Service Account**:
   - Create service account with Document AI User role
   - Download JSON key
   - Set `GOOGLE_APPLICATION_CREDENTIALS` or embed in deployment

### Without Document AI Configured

The system gracefully falls back to standard processing. No errors, just prints warnings:
```
⚠️ Document AI needed for scan.pdf (PDF extraction failed) but not configured
```

## Next Steps

1. [x] Implement smart fallback processor
2. [ ] Set up GCP project when specific need arises
3. [ ] Test with actual scanned worksheets
4. [ ] Test with math-heavy course materials
