# Apple App Store Reviews Scraper

Download **App Store reviews** for any iPhone, iPad or Mac app from **Apple's official customer-reviews feed** (the public RSS/JSON feed behind apps.apple.com) plus the iTunes lookup/search APIs. No login, no cookies, no browser, no proxies.

- **Any app**: paste an App Store URL, a numeric app ID, or just the app name
- **Any country**: one run can cover many storefronts (`us`, `gb`, `de`, `fr`, `jp`, ...)
- **Filters**: newest or most helpful first, star range (e.g. 1-2 stars to find complaints), `since` date
- Each review carries the app's name, developer, current average rating and rating count
- Up to 500 reviews per app and country (the limit of Apple's feed)
- **$0.20 per 1,000 reviews.** Failed lookups are never charged.

## Input examples

```json
{ "apps": ["389801252"], "countries": ["us"], "maxReviews": 100 }
```
```json
{ "apps": ["Duolingo", "https://apps.apple.com/gb/app/spotify-music-and-podcasts/id324684580"], "countries": ["us", "gb", "de"], "maxRating": 2, "since": "2026-01-01", "maxReviews": 500 }
```

## Output

`type` (`review` or `error`), `appId`, `appName`, `developer`, `appRating`, `appRatingCount`, `country`, `reviewId`, `rating` (1-5), `title`, `text`, `version`, `author` (public display name), `date` (ISO 8601 UTC), `helpfulVotes`, `totalVotes`, `appUrl`, `source`.

## Notes

- Apple only exposes the most recent 500 reviews per app and storefront; run several countries for more coverage.
- Review volume per country differs a lot; small storefronts may return few reviews.
- Items with `type: error` are free.

## Pricing

**Free during launch:** this Actor currently has no per-result fee. You only pay Apify platform usage, which the Free plan's monthly credit covers for normal use. The prices below are the regular prices and are not charged at the moment.

| Event | Price |
| --- | --- |
| Review | $0.0002 |

Data comes from Apple's public feeds. Reviews contain public display names; please respect applicable privacy law when using them.

## Example output

```json
{
  "type": "review",
  "appId": "570060128",
  "appName": "Duolingo",
  "country": "de",
  "rating": 2,
  "title": "I don't need chests and tiles",
  "text": "Please add option to skip chests opening ...",
  "version": "7.147.0",
  "author": "fijveu",
  "date": "2026-11-03T06:44:13Z",
  "helpfulVotes": 0
}
```

## Use cases

- **Product research**: find recurring complaints with `maxRating: 2`.
- **LLM analysis**: feed reviews to a model for sentiment and feature requests.
- **Competitor tracking**: schedule runs per country and compare ratings over time.

## Integrations

Python (Apify client):

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/appstore-reviews-scraper").call(run_input={"apps": ["389801252"], "countries": ["us"], "maxReviews": 50})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["rating"], item["text"])
```

**Make, Zapier, n8n**: add the Apify app, choose *Run Actor* (or *Run Actor and get dataset items*), set the Actor to `extas_corp/appstore-reviews-scraper` and map the JSON input. The same Actor can be started on a schedule from Apify itself, with a webhook to your own endpoint when the run finishes.

## FAQ

**Where do the reviews come from?** The public Apple customer-review feed per storefront; no login needed.

**Android too?** Yes, see Google Play Reviews Scraper.

**Do I need to pay to try it?** New Apify accounts include free monthly platform credit (about $5 on the free plan at the time of writing), so you can run the example input above and many more items before paying anything. You only pay the per-event price listed under Pricing; runs that return nothing or fail are not charged for the failed items.
