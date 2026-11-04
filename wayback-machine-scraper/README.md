# Wayback Machine Scraper: Archived Snapshots & URLs

Query the **Internet Archive's official CDX Server API** and get clean, flat snapshot records for any URL or domain. No login, no cookies, no browser, no proxies.

- **Snapshots over time**: every capture of a page, thinned out by hour / day / month / year or by content change
- **Closest snapshot** to a date (e.g. what did this site look like on 2020-06-15?)
- **All archived URLs** of a domain, host or path prefix (great for site migrations, SEO audits, link recovery)
- Filter by date range, HTTP status and MIME type
- Ready-to-open `archiveUrl` and raw `rawUrl` (original content without the Wayback toolbar)
- Paginated with resume keys, so you can pull tens of thousands of rows
- **$0.50 per 1,000 snapshots.** Failed lookups are never charged.

## Input examples

```json
{ "mode": "snapshots", "urls": ["example.com/pricing"], "collapse": "month", "from": "2020", "maxItems": 200 }
```
```json
{ "mode": "closest", "urls": ["apify.com", "openai.com"], "closestTo": "2020-06-15" }
```
```json
{ "mode": "urls", "urls": ["crawlee.dev"], "matchType": "domain", "mimeType": "text/html", "maxItems": 5000 }
```

## Output

`type` (`snapshot` or `error`), `url`, `timestamp` (YYYYMMDDhhmmss), `date` (ISO 8601 UTC), `statusCode`, `mimeType`, `digest` (content hash: same digest = unchanged page), `length`, `archiveUrl`, `rawUrl`, `source`.

## Notes

- This Actor returns snapshot metadata and links; it does not download the archived pages.
- Domain-wide queries on very large sites can be slow on the Archive's side; the Actor retries automatically, and a lower *Max results* helps.
- Items with `type: error` are free.

## Pricing

| Event | Price |
| --- | --- |
| Snapshot | $0.0005 |

Data comes from the Internet Archive's public API. Please keep request volumes reasonable.
