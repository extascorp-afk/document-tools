# SPF, DKIM & DMARC Checker: Bulk Email Authentication Audit

Paste a list of domains and get, for each one, **how well its email is protected against spoofing and how likely its mail is to be rejected**: SPF, DMARC, DKIM, MTA-STS, TLS-RPT, BIMI and MX, a score out of 100, a grade (A to F) and a plain-English list of issues.

Everything comes from public DNS (plus the public MTA-STS policy file). No login, no browser, no proxy, no e-mail is sent.

- **SPF**: the record, its final `all` qualifier, and the **total number of DNS lookups** after following every `include:` and `redirect=` (receivers reject SPF above 10, a common silent failure). Several SPF records, loops and broken includes are reported.
- **DMARC**: policy (`none` / `quarantine` / `reject`), subdomain policy, `pct`, alignment, and the **domains** that receive aggregate reports (the local part of report addresses is masked: `mailto:*@domain`)
- **DKIM**: which selectors publish a key, from 19 common ones (Google Workspace, Microsoft 365, Mailchimp/Mandrill, Amazon SES, Zoho, Proton...) or your own list. Revoked keys (empty `p=`) do not count.
- **MTA-STS** record and policy mode (`enforce` / `testing` / `none`), **TLS-RPT**, **BIMI** record and logo URL
- **MX** hosts with priorities (a null MX is shown as an empty host)
- One `ok` column for filtering and alerts: exactly one SPF record ending in `-all` or `~all` within 10 lookups, and a DMARC policy of `quarantine` or `reject`
- A domain that does not exist or does not answer gets `error` and never stops the run
- **Free during launch**: no per-domain fee at the moment, you only pay Apify platform usage (covered by the Free plan's monthly credit for normal use).

## Input example

```json
{
  "domains": ["apify.com", "https://www.wikipedia.org/", "someone@example.com"],
  "dkimSelectors": []
}
```

URLs and e-mail addresses are accepted: only the domain is used. Leave `dkimSelectors` empty to try the common ones.

## Example output

A well configured domain (real run, MX list shortened):
```json
{
  "domain": "apify.com",
  "ok": true,
  "score": 100,
  "grade": "A",
  "issues": ["SPF uses 10 of the 10 allowed DNS lookups: one more include will break it"],
  "error": null,
  "mx": [{"priority": 1, "host": "aspmx.l.google.com"}, {"priority": 5, "host": "alt1.aspmx.l.google.com"}],
  "spf": {
    "record": "v=spf1 a mx include:_spf.google.com include:mailgun.org include:amazonses.com include:19497222.spf05.hubspotemail.net -all",
    "records": 1,
    "all": "-all",
    "lookups": 10,
    "errors": []
  },
  "dmarc": {
    "record": "v=DMARC1; p=reject; sp=reject; pct=100; rua=mailto:*@apify.com; ri=604800",
    "records": 1,
    "policy": "reject",
    "subdomainPolicy": "reject",
    "pct": 100,
    "reportDomains": ["apify.com"],
    "alignmentSpf": "r",
    "alignmentDkim": "r"
  },
  "dkim": {"checked": ["google", "selector1", "..."], "found": ["google"]},
  "mtaSts": {"record": "v=STSv1; id=29919a352ef9476a", "policyMode": "enforce"},
  "tlsRpt": "v=TLSRPTv1; rua=mailto:*@apify.com",
  "bimi": {
    "record": "v=BIMI1;l=https://apify.com/ext/apify-bimi-logo.svg;a=https://apify.com/ext/apify-bimi-certificate.pem;avp=personal",
    "logo": "https://apify.com/ext/apify-bimi-logo.svg"
  }
}
```

A domain that receives mail but publishes no SPF and no DMARC (real run, shortened):
```json
{
  "domain": "badssl.com",
  "ok": false,
  "score": 30,
  "grade": "F",
  "issues": [
    "no SPF record",
    "no DMARC record",
    "no DKIM key on the selectors tried (the domain may use another selector)",
    "no MTA-STS (optional): inbound mail TLS is not enforced"
  ],
  "error": null,
  "mx": [{"priority": 5, "host": "gmr-smtp-in.l.google.com"}]
}
```

A domain that does not exist: `{"domain": "...", "ok": false, "error": "domain does not exist (NXDOMAIN)"}`.

## Score

Starts at 100. Missing or duplicated SPF: -30. SPF ending in `+all` or with no `all`: -20, `?all`: -10. More than 10 SPF lookups: -20. Missing, duplicated or invalid DMARC: -30. DMARC `p=none`: -15. `pct` below 100: -5. No `rua`: -5. No DKIM key on the selectors tried: -10 (not applied to domains that declare they send no mail with `v=spf1 -all`). MTA-STS is reported but never lowers the score. Grade: A 90+, B 75+, C 60+, D 40+, F below.

## Use cases

- **Deliverability checks** before a campaign: catch an SPF over 10 lookups or a missing DMARC before Gmail and Yahoo reject the mail
- **Agencies, MSPs and IT providers**: audit every client domain in one run, export to CSV or Excel
- **Monitoring**: schedule it weekly and alert when `ok` turns false (someone added one include too many)
- **Security reviews and vendor checks**: which suppliers can be spoofed (no DMARC enforcement)
- **Sales qualification for email and security services**: find the domains that need help, from public DNS only

## Integrations

Python:
```python
from apify_client import ApifyClient
client = ApifyClient("<YOUR_API_TOKEN>")
run = client.actor("extas_corp/email-auth-checker").call(run_input={"domains": ["example.com"]})
for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(item["domain"], item.get("grade"), item.get("issues"), item["error"])
```
Results can be exported as CSV, Excel or JSON from the dataset, or pushed to Google Sheets, Make, Zapier or n8n.

## Limits

- **DKIM selectors cannot be listed from DNS.** If a domain signs with a selector that is not in the list, it is reported as "no DKIM key on the selectors tried". Add the selector (found in the `DKIM-Signature: s=` header of one of its e-mails) to `dkimSelectors`.
- SPF macros (`%{i}`) are counted as one lookup but not followed. When SPF uses `redirect=`, `all` shows `redirect` and the target's own qualifier is not graded.
- It reads DNS records; it does not send mail, test SMTP servers, check blocklists or verify that DKIM signatures actually validate.
- DMARC is read on the exact name you give. For a subdomain without its own record, receivers fall back to the parent domain's DMARC: check the parent too.
- DNS answers are those seen from Apify's resolver at run time; a record changed minutes ago may not be visible yet.

## FAQ

**Does it need a proxy or a browser?** No. A few DNS questions per domain, plus one HTTPS request to the MTA-STS policy file when the domain has an MTA-STS record.

**Why "no DKIM key" when the domain does use DKIM?** See the first limit: the selector name is not public. Add it to `dkimSelectors`.

**Does it collect personal data?** No. It reads public DNS records of domains. The local part of DMARC and TLS-RPT report addresses is masked, only their domain is shown.

**Do I need to pay to try it?** The Apify Free plan includes monthly platform credit, enough to check thousands of domains.
