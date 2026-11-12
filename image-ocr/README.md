# Image to Text OCR: Bulk Screenshot & Scan Reader

Extract text from **thousands of images** in one run: screenshots, scanned documents, photos of pages, receipts, signs, memes, UI captures. Powered by Tesseract OCR, running inside your Apify run, so your images are never sent to a third-party OCR API.

- **Full text** per image, line by line
- **Confidence score** per image (and per word) so you can filter bad reads
- **Word bounding boxes** (optional): text + pixel position for every word
- **7 languages**: English, French, German, Spanish, Italian, Portuguese, Dutch, and mixes like `eng+fra`
- **Layout modes** for documents vs. sparse text (screenshots, signs)
- **Auto-rotation** of phone photos (EXIF)
- **Fair pricing**: you pay only for images that were read. Broken links cost nothing.

## How to use

1. Paste image links into **Image URLs** (or upload a text file with one URL per line).
2. Choose the language. Pick **Sparse text** for screenshots and signs.
3. Click **Start**, then export the results as JSON, CSV or Excel, or fetch them through the API.

## Input example

```json
{
  "imageUrls": [{ "url": "https://example.com/scan.png" }],
  "language": "eng",
  "includeWordBoxes": false
}
```

## Output example

```json
{
  "url": "https://example.com/scan.png",
  "status": "ok",
  "text": "INVOICE #4521\nDate: 2026-03-02\nTotal: 149.00 EUR",
  "meanConfidence": 91.4,
  "wordCount": 7,
  "imageWidth": 1240,
  "imageHeight": 1754
}
```

With **Include word bounding boxes** on, each item also has `words: [{ "text", "confidence", "left", "top", "width", "height", "block", "line" }]`.

## Pricing

| Event | Price |
| --- | --- |
| Image read | $0.0015 per image |

1,000 images cost $1.50. Set a maximum cost per run and the Actor stops cleanly when it is reached.

## Need PDFs?

For PDF files (text PDFs and scanned PDFs, with tables), use the companion Actor [PDF to Markdown Converter (Tables + OCR)](https://apify.com/extas_corp/pdf-to-markdown).

## Limits

- Max 30 MB per image, 2 minutes per image.
- Handwriting is read poorly (Tesseract is built for printed text).
- Very low-resolution images (under ~20 px text height) give low confidence. Check `meanConfidence`.

## Free browser version

Converting just one file? Use the free in-browser converter at [hackthehydra.com](https://hackthehydra.com): no upload, no account.

## More ways to use it

- **REST API without an Apify account:** the same converters are available on RapidAPI as the [Document to Markdown API](https://rapidapi.com/ExtasCorporation/api/document-to-markdown) (PDF, DOCX, PPTX, XLSX, images; free plan included).
- **Free in your browser:** [hackthehydra.com](https://hackthehydra.com) has no-upload converters for PDF, Word, Excel, PowerPoint and images.

## Use cases

- **Research and archives**: digitise scans, screenshots and photographed documents in bulk.
- **LLM pipelines**: feed text from images into RAG or classification steps.
- **Ops**: read receipts, labels and slides at scale instead of retyping them.

## Integrations

Python (Apify client):

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/image-ocr").call(run_input={"imageUrls": [{"url": "https://raw.githubusercontent.com/tesseract-ocr/tessdoc/main/images/eurotext.png"}]})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item.get("text"))
```

**Make, Zapier, n8n**: add the Apify app, choose *Run Actor* (or *Run Actor and get dataset items*), set the Actor to `extas_corp/image-ocr` and map the JSON input. The same Actor can be started on a schedule from Apify itself, with a webhook to your own endpoint when the run finishes.

## FAQ

**Which languages?** Any Tesseract language code, set with the `language` input (default `eng`).

**How accurate is it?** Good on clean, high-resolution images; low-resolution or handwritten input gives weaker results.

**Do I need to pay to try it?** New Apify accounts include free monthly platform credit (about $5 on the free plan at the time of writing), so you can run the example input above and many more items before paying anything. You only pay the per-event price listed under Pricing; runs that return nothing or fail are not charged for the failed items.
