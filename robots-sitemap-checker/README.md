# Robots.txt & Sitemap Checker: Bulk Validation of robots.txt and XML Sitemaps

Paste a list of sites and get, for each one, a **list of problems** in its `robots.txt` and in the sitemaps it declares. It reads `/robots.txt`, follows the `Sitemap:` lines (and sitemap index files, up to 10 files per site), and checks what a crawler would trip over. It reads only public files that the server gives to any crawler.

- **robots.txt**: HTTP status (a 5xx can make Google stop crawling; a 404 means "everything allowed"), `Disallow: /` for `User-agent: *` (the whole site blocked), rules placed before any `User-agent`, unknown directives, paths that do not start with `/`, relative `Sitemap:` URLs. The list of user-agents and the declared sitemaps are returned too.
- **Sitemaps**: declared in robots.txt, or `/sitemap.xml` when none is declared. Handles `urlset` and `sitemapindex`, gzip files, and checks: invalid XML, wrong root element, more than 50,000 URLs in one file, `<lastmod>` values that are not W3C dates, duplicate `<loc>`, URLs on another host than the site (search engines ignore them), entries with no `<loc>`.
- **Dead links**: requests the first 0 to 3 URLs of each sitemap file (your choice) and reports any status 400 or above.
- Errors are reported per site, they never stop the run.
- **Safe by design**: hosts that resolve to private, local or link-local addresses are refused (also after a redirect). XML with a DOCTYPE/ENTITY declaration is refused (entity-expansion attacks). Files are read with a size cap (robots.txt 500 KB, sitemaps 5 MB).
- **Free during launch**: no per-site fee at the moment, you only pay Apify platform usage (covered by the Free plan's monthly credit for normal use).

## Input example

```json
{
  "urls": ["github.com", "example.com", "https://www.python.org"],
  "sampleUrls": 3
}
```

A bare domain is checked over HTTPS. Duplicates are checked once.

## Example output

`github.com` (real run):
```json
{
  "url": "https://github.com",
  "robotsStatus": 200,
  "robots": {"agents": ["*", "bingbot", "gptbot", "claudebot", "..."], "sitemaps": ["https://github.com/sitemap_marketing.xml"], "blocksAll": false},
  "sitemaps": [
    {"url": "https://github.com/sitemap_marketing.xml", "status": 200, "kind": "urlset", "entries": 376, "problems": ["1 duplicate <loc> values"]}
  ],
  "problems": ["https://github.com/sitemap_marketing.xml: 1 duplicate <loc> values"],
  "error": null
}
```
(agents shortened here.)

`example.com` (real run) returns `robotsStatus: 404` and the problems `robots.txt returns 404: crawlers treat the site as fully crawlable`, `no Sitemap line in robots.txt (tried /sitemap.xml)` and `https://example.com/sitemap.xml: returns 404`.

## Pricing

**Free during launch**: no per-site fee, only Apify platform usage. A price per checked site may be introduced later, with advance notice.

## Limits

- It **validates the files, it does not apply your rules**: it does not tell you whether a given URL is allowed or blocked for a given crawler. Wildcard and precedence rules are not evaluated.
- Only the site root `/robots.txt` is read. Subdomains are separate sites: pass them as separate inputs.
- Sitemaps are read up to **5 MB** (after decompression). A larger file is reported as "not validated", not as valid. Sitemap index files are followed for up to 10 files per site in total, so a huge index is only partly checked.
- The dead-link check requests at most 3 URLs per sitemap file: it is a smoke test, not a full link audit. Image, video and news sitemap extensions are not validated.
- Sites that block automated clients (Cloudflare challenge, 403) are reported with their HTTP status.
- It sends normal GET requests with a clear User-Agent. Only check sites you are allowed to look at.
