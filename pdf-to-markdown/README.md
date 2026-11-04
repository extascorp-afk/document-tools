# PDF to Markdown Converter (Tables + OCR)

Convert PDF files to **clean, LLM-ready Markdown**: headings, paragraphs, Markdown tables, and OCR for scanned pages. Built for **RAG pipelines, AI agents, document search and data extraction**.

- **Headings detected** from font sizes (`#`, `##`, `###`), paragraphs re-joined, hyphenated words fixed
- **Tables** converted to real Markdown tables (layout boxes are ignored)
- **Scanned PDFs**: pages without a text layer are OCR'd with Tesseract (English, French, German, Spanish, Italian, Portuguese, Dutch)
- **Bulk**: give hundreds of URLs, they're processed in parallel
- **Fair pricing**: you pay only for PDFs that convert successfully. Failed downloads cost nothing.

## How to use

1. Paste one or more direct PDF links into **PDF URLs** (or upload a text file with one URL per line).
2. Keep the defaults, or turn off OCR / tables, limit pages, pick the OCR language.
3. Click **Start**. Each PDF becomes one dataset item. Export as JSON, CSV, Excel, or fetch through the API.

## Input example

```json
{
  "pdfUrls": [{ "url": "https://arxiv.org/pdf/1706.03762" }],
  "extractTables": true,
  "ocrScannedPages": true,
  "ocrLanguage": "eng",
  "maxPages": 0
}
```

## Output example

```json
{
  "url": "https://arxiv.org/pdf/1706.03762",
  "status": "ok",
  "title": "Attention Is All You Need",
  "pageCount": 15,
  "ocrPages": 0,
  "tableCount": 0,
  "charCount": 40211,
  "markdown": "# Attention Is All You Need\n\nAshish Vaswani ...\n\n### Abstract\n\nThe dominant sequence transduction models ..."
}
```

Failed PDFs come back with `"status": "error"` and an `error` message (not charged).

## Pricing

Pay per event:

| Event | Price |
| --- | --- |
| PDF converted (text layer) | $0.003 per PDF |
| OCR page (scanned page) | $0.01 per page |

1,000 text PDFs cost $3. Set a maximum cost per run in the run options and the Actor stops cleanly when it is reached.

## Use with AI agents and APIs

Call it from the Apify API, Python/JS clients, Make, Zapier, n8n, LangChain, LlamaIndex, or through the Apify MCP server, so your agent can read any PDF by URL.

```bash
curl -X POST "https://api.apify.com/v2/acts/<ACTOR_ID>/run-sync-get-dataset-items?token=<TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"pdfUrls":[{"url":"https://arxiv.org/pdf/1706.03762"}]}'
```

## Limits

- Max 100 MB per PDF, 5 minutes per PDF.
- Password-protected PDFs aren't supported.
- Complex multi-level tables (e.g. tax tables with merged cells) may come out simplified. Tables drawn without lines are kept as text.
- Two-column layouts are read line by line across the page.

## FAQ

**Is my data stored?** Only in your own Apify run storage, which follows your retention settings.

**Can I convert local files?** Upload them to any public URL (or Apify key-value store) and pass the link.

Found a PDF that converts badly? Open an issue on the Actor's Issues tab with the link and it will be fixed.

## Related Actors

- [Bulk Image OCR](https://apify.com/extas_corp/image-ocr): text from screenshots, scans and photos
- [Word, PowerPoint & Excel to Markdown](https://apify.com/extas_corp/document-to-markdown): DOCX, PPTX, XLSX, HTML, EPUB to Markdown

## Free browser version

Converting just one file? Use the free in-browser converter at [hackthehydra.com](https://hackthehydra.com): no upload, no account.
