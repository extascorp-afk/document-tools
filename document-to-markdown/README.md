# DOCX, PPTX, XLSX to Markdown Converter for LLM & RAG

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

## Input example

```json
{
  "documentUrls": [
    { "url": "https://example.com/report.docx" },
    { "url": "https://example.com/deck.pptx" }
  ]
}
```

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

**Free during launch:** this Actor currently has no per-result fee. You only pay Apify platform usage, which the Free plan's monthly credit covers for normal use. The prices below are the regular prices and are not charged at the moment.

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

## Free browser version

Converting just one file? Use the free in-browser converter at [hackthehydra.com](https://hackthehydra.com): no upload, no account.

## More ways to use it

- **REST API without an Apify account:** the same converters are available on RapidAPI as the [Document to Markdown API](https://rapidapi.com/ExtasCorporation/api/document-to-markdown) (PDF, DOCX, PPTX, XLSX, images; free plan included).
- **Free in your browser:** [hackthehydra.com](https://hackthehydra.com) has no-upload converters for PDF, Word, Excel, PowerPoint and images.

## Use cases

- **LLM and RAG**: Word reports, slide decks and spreadsheets as Markdown ready for chunking.
- **Research**: normalise a folder of mixed Office files into one text corpus.
- **Content migration and SEO**: move DOCX content into a Markdown-based CMS or docs site.

## Integrations

Python (Apify client):

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/document-to-markdown").call(run_input={"documentUrls": [{"url": "https://filesamples.com/samples/document/docx/sample3.docx"}]})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["markdown"][:500])
```

**LangChain / RAG** (turn each result into a `Document`):

```python
from apify_client import ApifyClient
from langchain_core.documents import Document

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/document-to-markdown").call(run_input={"documentUrls": [{"url": "https://filesamples.com/samples/document/docx/sample3.docx"}]})
docs = [Document(page_content=i["markdown"], metadata={"source": i.get("url")})
        for i in client.dataset(run["defaultDatasetId"]).iterate_items() if i.get("markdown")]
```

**Make, Zapier, n8n**: add the Apify app, choose *Run Actor* (or *Run Actor and get dataset items*), set the Actor to `extas_corp/document-to-markdown` and map the JSON input. The same Actor can be started on a schedule from Apify itself, with a webhook to your own endpoint when the run finishes.

## FAQ

**Which formats?** DOCX, PPTX and XLSX. For PDFs use PDF to Markdown, for images use Image OCR.

**Do I need to pay to try it?** New Apify accounts include free monthly platform credit (about $5 on the free plan at the time of writing), so you can run the example input above and many more items before paying anything. You only pay the per-event price listed under Pricing; runs that return nothing or fail are not charged for the failed items.
