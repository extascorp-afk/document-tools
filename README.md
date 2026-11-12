# Document tools and public-data scrapers for AI pipelines

Hosted, pay-per-use tools that turn documents and public web data into clean, LLM-ready output. Nothing to install: call them from the Apify console, the API, Python, JavaScript, Make, Zapier or n8n.

Try the converters free in your browser at **[hackthehydra.com](https://hackthehydra.com)**. Full list of robots: [hackthehydra.com/apify-robots](https://hackthehydra.com/apify-robots/).

## Document converters

| Tool | What it does | Run it |
| --- | --- | --- |
| [`pdf-to-markdown`](pdf-to-markdown) | PDF → Markdown with headings, tables, OCR for scanned pages | [apify.com/extas_corp/pdf-to-markdown](https://apify.com/extas_corp/pdf-to-markdown) |
| [`image-ocr`](image-ocr) | Bulk image → text (Tesseract), confidence + word boxes | [apify.com/extas_corp/image-ocr](https://apify.com/extas_corp/image-ocr) |
| [`document-to-markdown`](document-to-markdown) | DOCX, PPTX, XLSX, HTML, EPUB → Markdown | [apify.com/extas_corp/document-to-markdown](https://apify.com/extas_corp/document-to-markdown) |
| [`website-to-markdown`](website-to-markdown) | Crawl a site (sitemap, depth, globs, robots.txt) → clean Markdown per page for RAG | [apify.com/extas_corp/website-to-markdown](https://apify.com/extas_corp/website-to-markdown) |

## Data scrapers (public data, no login, no proxy)

| Tool | What it does | Run it |
| --- | --- | --- |
| [`google-play-reviews-scraper`](google-play-reviews-scraper) | Google Play reviews by app ID/URL, country, language, stars, date, developer replies | [apify.com/extas_corp/google-play-reviews-scraper](https://apify.com/extas_corp/google-play-reviews-scraper) |
| [`appstore-reviews-scraper`](appstore-reviews-scraper) | Apple App Store reviews by app ID and country | [apify.com/extas_corp/appstore-reviews-scraper](https://apify.com/extas_corp/appstore-reviews-scraper) |
| [`hackernews-scraper`](hackernews-scraper) | Hacker News stories, comments and "Who is hiring" threads | [apify.com/extas_corp/hackernews-scraper](https://apify.com/extas_corp/hackernews-scraper) |
| [`bluesky-scraper`](bluesky-scraper) | Bluesky posts and profiles via the public API | [apify.com/extas_corp/bluesky-scraper](https://apify.com/extas_corp/bluesky-scraper) |
| [`wayback-machine-scraper`](wayback-machine-scraper) | Wayback Machine snapshots / archived URL list for a domain | [apify.com/extas_corp/wayback-machine-scraper](https://apify.com/extas_corp/wayback-machine-scraper) |
| [`redirect-checker`](redirect-checker) | Follow every redirect hop of a list of URLs and report the chain and final status | [apify.com/extas_corp/redirect-checker](https://apify.com/extas_corp/redirect-checker) |

Each folder holds the documentation of one tool: inputs, output fields, examples and FAQ.

## Call a tool from the command line

```bash
curl -X POST "https://api.apify.com/v2/acts/extas_corp~pdf-to-markdown/run-sync-get-dataset-items?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"pdfUrls":[{"url":"https://arxiv.org/pdf/1706.03762"}]}'
```

## Call a tool from Python

```python
from apify_client import ApifyClient  # pip install apify-client

client = ApifyClient("YOUR_APIFY_TOKEN")
run = client.actor("extas_corp/pdf-to-markdown").call(
    run_input={"pdfUrls": [{"url": "https://arxiv.org/pdf/1706.03762"}]}
)
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["markdown"][:500])
```

A free Apify account includes monthly credits, enough to try every tool.

## Questions and requests

Open an issue here to report a problem or ask for a new input option or a new tool.

This repository contains documentation and usage examples only.
