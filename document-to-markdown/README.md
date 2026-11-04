# Word, PowerPoint, Excel to Markdown

Convert **Office documents and web formats to clean Markdown** in bulk, ready for LLMs, RAG, vector databases and AI agents.

| Format | What you get |
| --- | --- |
| **DOCX** (Word) | Headings, paragraphs, lists, tables, links |
| **PPTX** (PowerPoint) | One section per slide, titles, text, tables, speaker notes |
| **XLSX / XLS** (Excel) | One Markdown table per sheet |
| **HTML** | Main content as Markdown |
| **EPUB** | Book metadata + chapters |
| **CSV, JSON, XML, IPYNB, MSG (Outlook), ZIP** | Readable Markdown (ZIP: every file inside) |

Powered by Microsoft's open-source [MarkItDown](https://github.com/microsoft/markitdown) library, running inside your run: your files are never sent to a third-party API.

**Fair pricing**: you pay only for files that convert. Broken links and unsupported files are free.

## How to use

1. Paste direct file links into **Document URLs** (or upload a text file with one URL per line).
2. Click **Start**.
3. Export as JSON, CSV or Excel, or fetch through the API.

## Output example

```json
{
  "url": "https://example.com/report.docx",
  "status": "ok",
  "fileType": "docx",
  "title": null,
  "charCount": 3292,
  "markdown": "# Sample Document\n\nThis document was created using accessibility techniques for headings, lists..."
}
```

## Pricing

| Event | Price |
| --- | --- |
| Document converted | $0.002 per file |

1,000 documents cost $2.

## PDFs and images

- **PDFs** (including scanned ones, with tables): use [PDF to Markdown Converter (Tables + OCR)](https://apify.com/extas_corp/pdf-to-markdown).
- **Images** (screenshots, scans, photos): use [Bulk Image OCR](https://apify.com/extas_corp/image-ocr).

## Limits

- Max 50 MB per file, 3 minutes per file.
- Old binary formats (.doc, .ppt) aren't supported. Save them as .docx / .pptx.
- Some websites block automated downloads (HTTP 403). Those items fail and aren't charged.
