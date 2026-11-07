# Document tools and public-data scrapers for AI pipelines

Try them free in your browser at **[hackthehydra.com](https://hackthehydra.com)**.

Small open-source converters that turn documents into clean, LLM-ready Markdown. Each one is also available as a hosted, pay-per-use API on Apify, so you can use it without installing anything:

| Tool | What it does | Hosted version |
| --- | --- | --- |
| [`pdf-to-markdown`](pdf-to-markdown) | PDF → Markdown with headings, tables, OCR for scanned pages | [apify.com/extas_corp/pdf-to-markdown](https://apify.com/extas_corp/pdf-to-markdown) |
| [`image-ocr`](image-ocr) | Bulk image → text (Tesseract), confidence + word boxes | [apify.com/extas_corp/image-ocr](https://apify.com/extas_corp/image-ocr) |
| [`document-to-markdown`](document-to-markdown) | DOCX, PPTX, XLSX, HTML, EPUB → Markdown (MarkItDown) | [apify.com/extas_corp/document-to-markdown](https://apify.com/extas_corp/document-to-markdown) |
| [`website-to-markdown`](website-to-markdown) | Crawl a site (sitemap, depth, globs, robots.txt) → clean Markdown per page for RAG | [apify.com/extas_corp/website-to-markdown](https://apify.com/extas_corp/website-to-markdown) |

## Data scrapers (public data, no login, no proxy)

| Tool | What it does | Hosted version |
| --- | --- | --- |
| [`google-play-reviews-scraper`](google-play-reviews-scraper) | Google Play reviews by app ID/URL, country, language, stars, date, developer replies | [apify.com/extas_corp/google-play-reviews-scraper](https://apify.com/extas_corp/google-play-reviews-scraper) |
| [`appstore-reviews-scraper`](appstore-reviews-scraper) | Apple App Store reviews by app ID and country | [apify.com/extas_corp/appstore-reviews-scraper](https://apify.com/extas_corp/appstore-reviews-scraper) |
| [`hackernews-scraper`](hackernews-scraper) | Hacker News stories, comments and "Who is hiring" threads | [apify.com/extas_corp/hackernews-scraper](https://apify.com/extas_corp/hackernews-scraper) |
| [`bluesky-scraper`](bluesky-scraper) | Bluesky posts and profiles via the public API | [apify.com/extas_corp/bluesky-scraper](https://apify.com/extas_corp/bluesky-scraper) |
| [`wayback-machine-scraper`](wayback-machine-scraper) | Wayback Machine snapshots / archived URL list for a domain | [apify.com/extas_corp/wayback-machine-scraper](https://apify.com/extas_corp/wayback-machine-scraper) |

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
