# Google Play Reviews Scraper

Download **Google Play Store reviews** for any Android app: by app name, package ID or Play Store URL, for any country and language. It reads the public review data behind play.google.com. No login, no cookies, no browser, no proxies.

- **Any app**: paste a Play Store URL, a package name (`com.duolingo`) or just the app name
- **Any country and language**: one run can cover many storefronts (`us`, `gb`, `de`, `in`, `br`, ...)
- **Filters**: newest / most relevant / by rating, star range (e.g. 1-2 stars to find complaints), `since` date
- **Developer replies** included, plus the app's name, developer, average rating, rating count and install bracket on every row
- Great for app review monitoring, sentiment analysis, competitor research, churn analysis and training data
- **$0.40 per 1,000 reviews.** Failed lookups are never charged.

## Input examples

```json
{ "apps": ["com.duolingo"], "countries": ["us"], "maxReviews": 100 }
```
```json
{ "apps": ["Spotify", "https://play.google.com/store/apps/details?id=com.whatsapp"], "countries": ["us", "gb", "de"], "language": "en", "maxRating": 2, "since": "2026-01-01", "maxReviews": 500 }
```

## Output

`type` (`review` or `error`), `appId`, `appName`, `developer`, `appRating`, `appRatingCount`, `installs`, `country`, `language`, `reviewId`, `rating` (1-5), `text`, `version`, `author` (public display name), `date` (ISO 8601 UTC), `thumbsUp`, `developerReply`, `developerReplyDate`, `appUrl`, `source`.

## Use with the API

```bash
curl -X POST "https://api.apify.com/v2/acts/extas_corp~google-play-reviews-scraper/run-sync-get-dataset-items?token=$APIFY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"apps":["com.duolingo"],"maxReviews":20}'
```

## Notes

- Google decides how deep the review list goes; very popular apps allow thousands of reviews per country and language, small apps have fewer.
- Items with `type: error` are free.
- iPhone apps too? Use the sibling [App Store Reviews Scraper](https://apify.com/extas_corp/appstore-reviews-scraper).

## Pricing

**Free during launch:** this Actor currently has no per-result fee. You only pay Apify platform usage, which the Free plan's monthly credit covers for normal use. The prices below are the regular prices and are not charged at the moment.

| Event | Price |
| --- | --- |
| Review | $0.0004 |

Reviews contain public display names; please respect applicable privacy law when using them.

## Example output

```json
{
  "type": "review",
  "appId": "com.spotify.tv.android",
  "appName": "Spotify: Music & Podcasts",
  "appRating": 3.9,
  "country": "us",
  "language": "en",
  "rating": 2,
  "text": "That's a nice app, but ...",
  "version": "1.95.13",
  "author": "ahmed hamid",
  "date": "2026-11-02T17:14:41Z",
  "thumbsUp": 0,
  "developerReply": null
}
```

## Use cases

- **Product research**: read what users complain about (use `maxRating: 2`) in your app or a competitor's.
- **LLM analysis**: send reviews to a model for topic and sentiment clustering.
- **Monitoring**: schedule a daily run with `since` to catch new reviews and developer replies.

## Integrations

Python (Apify client):

```python
from apify_client import ApifyClient

client = ApifyClient("<APIFY_TOKEN>")
run = client.actor("extas_corp/google-play-reviews-scraper").call(run_input={"apps": ["com.duolingo"], "countries": ["us"], "maxReviews": 50})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["rating"], item["text"])
```

**Make, Zapier, n8n**: add the Apify app, choose *Run Actor* (or *Run Actor and get dataset items*), set the Actor to `extas_corp/google-play-reviews-scraper` and map the JSON input. The same Actor can be started on a schedule from Apify itself, with a webhook to your own endpoint when the run finishes.

## FAQ

**How are app names resolved?** A name like `Spotify` resolves to the top Google Play search result (`com.spotify.music`). The log shows which app was picked. For a guaranteed match, pass the package name (e.g. `com.spotify.music`) or the Play URL.

**How many reviews can I get?** Google decides the depth. Big apps allow thousands per country and language.

**Do I need to pay to try it?** New Apify accounts include free monthly platform credit (about $5 on the free plan at the time of writing), so you can run the example input above and many more items before paying anything. You only pay the per-event price listed under Pricing; runs that return nothing or fail are not charged for the failed items.
