# Bulk Image OCR: Image to Text

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
