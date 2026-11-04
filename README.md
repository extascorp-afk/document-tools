# Document tools for AI pipelines

Small open-source converters that turn documents into clean, LLM-ready Markdown. Each one is also available as a hosted, pay-per-use API on Apify, so you can use it without installing anything:

| Tool | What it does | Hosted version |
| --- | --- | --- |
| [`pdf-to-markdown`](pdf-to-markdown) | PDF → Markdown with headings, tables, OCR for scanned pages | [apify.com/extas_corp/pdf-to-markdown](https://apify.com/extas_corp/pdf-to-markdown) |
| [`image-ocr`](image-ocr) | Bulk image → text (Tesseract), confidence + word boxes | [apify.com/extas_corp/image-ocr](https://apify.com/extas_corp/image-ocr) |
| [`document-to-markdown`](document-to-markdown) | DOCX, PPTX, XLSX, HTML, EPUB → Markdown (MarkItDown) | [apify.com/extas_corp/document-to-markdown](https://apify.com/extas_corp/document-to-markdown) |

## Use the converter in your own code

```python
from my_actor.convert import pdf_to_markdown  # run from pdf-to-markdown/

with open("paper.pdf", "rb") as f:
    print(pdf_to_markdown(f.read()).markdown)
```

## Run as an API

```bash
curl -X POST "https://api.apify.com/v2/acts/extas_corp~pdf-to-markdown/run-sync-get-dataset-items?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pdfUrls":[{"url":"https://arxiv.org/pdf/1706.03762"}]}'
```

Issues and PRs welcome.

## License

MIT
