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

**Free during launch:** this Actor currently has no per-result fee. You only pay Apify platform usage, which the Free plan's monthly credit covers for normal use. The prices below are the regular prices and are not charged at the moment.

| Event | Price |
| --- | --- |
| Snapshot | $0.0005 |

Data comes from the Internet Archive's public API. Please keep request volumes reasonable.

## Example output

```json
{
  "type": "snapshot",
  "url": "https://crawlee.dev/",
  "date": "2022-08-04T21:57:09Z",
  "statusCode": 200,
  "mimeType": "text/html",
  "archiveUrl": "https://web.archive.org/web/20220804215709/https://crawlee.dev/",
  "rawUrl": "https://web.archive.org/web/20220804215709id_/https://crawlee.dev/"
}
```

## Use cases

- **SEO and migrations**: list every archived URL of a domain to rebuild redirects or recover content.
- **Research and legal evidence**: find how a page looked on a given date (`closestTo`).
- **Link recovery**: find dead pages that still have inbound links.

## Integrations

Python (Apify client):

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/wayback-machine-scraper").call(run_input={"mode": "snapshots", "urls": ["example.com"], "maxItems": 20})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["date"], item["archiveUrl"])
```

**Make, Zapier, n8n**: add the Apify app, choose *Run Actor* (or *Run Actor and get dataset items*), set the Actor to `extas_corp/wayback-machine-scraper` and map the JSON input. The same Actor can be started on a schedule from Apify itself, with a webhook to your own endpoint when the run finishes.

## FAQ

**Does it download page content?** It returns snapshot records with ready-to-open `archiveUrl` and raw `rawUrl`. Fetch the raw content from there or feed it to Website to Markdown.

**Do I need to pay to try it?** New Apify accounts include free monthly platform credit (about $5 on the free plan at the time of writing), so you can run the example input above and many more items before paying anything. You only pay the per-event price listed under Pricing; runs that return nothing or fail are not charged for the failed items.
