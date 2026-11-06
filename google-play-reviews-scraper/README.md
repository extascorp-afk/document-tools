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

| Event | Price |
| --- | --- |
| Review | $0.0004 |

Reviews contain public display names; please respect applicable privacy law when using them.
