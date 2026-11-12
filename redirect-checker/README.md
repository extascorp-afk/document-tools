# Redirect Checker: Bulk Redirect Chains & Migration Map Validator

Paste a list of URLs and get **every hop of every redirect chain**: status codes (301, 302, 303, 307, 308), the `Location` of each hop, the final URL and its status. Or paste your **site migration redirect map** (`old URL -> expected new URL`) and see at a glance which redirects are missing, broken or point to the wrong page.

No login, no browser, no proxies: plain HTTP requests, headers only (page bodies are never downloaded), so it is fast and cheap.

- Full chain per URL, e.g. `301 > 302 > 200`, with the URL and `Location` of each hop
- SEO warnings: chains longer than 1 hop, temporary redirects (302/303/307) where a 301/308 is expected, HTTPS to HTTP downgrades, redirect loops, too many redirects
- **Migration validation**: `matchesExpected` is true only when the chain ends on your expected URL with a 200
- DNS, TLS and timeout errors are reported per URL, they never stop the run
- One `ok` column to filter on: final status < 400, no loop, and expected target matched (if given)
- Parallel checks (up to 50 at once), custom User-Agent to test bot-specific redirects
- **Free during launch**: no per-URL fee at the moment, you only pay Apify platform usage (covered by the Free plan's monthly credit for normal use).

## Input examples

Simple list:
```json
{ "urls": ["http://example.com", "example.com/old-page", "https://bit.ly/3xyz"] }
```

Migration redirect map (paste two columns from a spreadsheet, or use `->`). The expected target can be a full URL or a path:
```json
{ "urls": [
    "https://old-shop.com/product/42 -> https://new-shop.com/p/blue-shoes",
    "https://old-shop.com/about -> /company",
    "https://old-shop.com/contact\thttps://new-shop.com/contact"
] }
```

## Example output

```json
{
  "url": "http://apify.com",
  "finalUrl": "https://apify.com/",
  "finalStatusCode": 200,
  "redirectCount": 1,
  "chain": [
    { "url": "http://apify.com", "statusCode": 301, "location": "https://apify.com/" },
    { "url": "https://apify.com/", "statusCode": 200, "location": null }
  ],
  "statusChain": "301 > 200",
  "timeMs": 281,
  "warnings": [],
  "error": null,
  "expectedUrl": "https://apify.com/",
  "matchesExpected": true,
  "ok": true
}
```

URL comparison for `matchesExpected` ignores case of scheme and host, default ports, a trailing slash and the `#fragment`; the query string must match.

## Use cases

- **Site migrations and redesigns**: validate hundreds of old -> new redirects before and after launch
- **SEO audits**: find redirect chains, 302s that should be 301s, loops and redirects to 404 pages
- **Link checking**: expand short links (bit.ly, t.co, ...) and affiliate links to their real destination
- **Monitoring**: schedule the Actor daily and alert (Make, Zapier, n8n, webhooks) when `ok` becomes false

## Integrations

Python:
```python
from apify_client import ApifyClient
client = ApifyClient("<YOUR_API_TOKEN>")
run = client.actor("extas_corp/redirect-checker").call(run_input={"urls": ["http://example.com"]})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["url"], item["statusChain"], item["finalUrl"])
```
Results can be exported as CSV, Excel or JSON from the dataset, or pushed to Google Sheets, Make, Zapier or n8n.

## FAQ

**Does it render JavaScript or follow meta refresh redirects?** No. It checks HTTP redirects (the `Location` header), which is what search engines treat as real redirects. JavaScript and `<meta refresh>` redirects are not followed.

**Is it a GET or a HEAD request?** GET, because many servers answer HEAD differently. Only the headers are read; the body is not downloaded.

**Can it check sites behind a login or a bot wall?** No. It sends normal anonymous requests. Sites that block bots may answer 403 or 429; this is reported as is.

**Do I need to pay to try it?** The Apify Free plan includes monthly platform credit, enough to check thousands of URLs.
