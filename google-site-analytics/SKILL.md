---
name: google-site-analytics
description: "Fetch and analyze data from Google Search Console and Google Analytics 4 for a site. Use when the user asks about: site search performance, keyword rankings, click-through rates, impressions, page indexing, crawl errors, sitemaps, traffic metrics, page views, sessions, user behavior, conversion events, realtime visitors, or any Google site monitoring. Keywords: search console, analytics, GA4, GSC, rankings, traffic, impressions, clicks, CTR, sessions, users, events."
disable-model-invocation: false
---

# Google Site Analytics Skill

Fetch and present data from **Google Search Console** (search performance, indexing) and **Google Analytics 4** (traffic, behavior, conversions) using service account credentials and their REST APIs.

---

## Prerequisites Check

Before fetching any data, verify credentials are in place. Run:

```bash
ls .claude/skills/google-site-analytics/auth/
```

Look for:
- `gsc-service-account.json` — Google Cloud service account key for Search Console
- `ga4-service-account.json` — Google Cloud service account key for GA4
- `config.json` — Site URL and GA4 property ID

If any are missing, follow **Step 1: Setup** below. Otherwise skip to the relevant query step.

---

## Step 1: First-Time Setup

### 1a. Create service accounts in Google Cloud

Tell the user:

> **You need a Google Cloud project with the APIs enabled and two service accounts:**
>
> 1. Go to https://console.cloud.google.com/
> 2. Create or select a project
> 3. Enable these APIs:
>    - **Google Search Console API** (`searchconsole.googleapis.com`)
>    - **Google Analytics Data API** (`analyticsdata.googleapis.com`)
> 4. Go to **IAM & Admin → Service Accounts → Create Service Account**
> 5. Create one for GSC (e.g. `google-search-console`) and one for GA4 (e.g. `ga4-analytics`)
> 6. For each: click the account → **Keys → Add Key → JSON** → download
> 7. Save as:
>    - `.claude/skills/google-site-analytics/auth/gsc-service-account.json`
>    - `.claude/skills/google-site-analytics/auth/ga4-service-account.json`

### 1b. Grant property access

**Search Console:**
- Go to https://search.google.com/search-console
- Settings → Users and permissions → Add user
- Enter the GSC service account email (e.g. `google-search-console@your-project.iam.gserviceaccount.com`)
- Permission: Full or Restricted

**Google Analytics 4:**
- Go to GA4 → Admin → Property Access Management → `+` Add users
- Enter the GA4 service account email (e.g. `ga4-analytics@your-project.iam.gserviceaccount.com`)
- Role: Viewer

### 1c. Create config.json

Ask the user for:
- **Site URL** — as it appears in Search Console. Domain properties use `sc-domain:example.com`; URL prefix properties use `https://example.com/`
- **GA4 Property ID** — the numeric ID from GA4 Admin → Property Settings (e.g. `486975613`). This is NOT the Measurement ID (`G-XXXXXXXX`) and NOT the Account ID.

Copy the example and fill it in:

```bash
cp .claude/skills/google-site-analytics/auth/config.example.json \
   .claude/skills/google-site-analytics/auth/config.json
```

Edit `config.json`:
```json
{
  "site_url": "sc-domain:your-site.com",
  "ga4_property_id": "YOUR_NUMERIC_PROPERTY_ID"
}
```

> **Tip:** Find the GA4 Property ID in the URL when viewing your property:
> `analytics.google.com/analytics/web/#/p**486975613**/...`

### 1d. Install dependencies

```bash
pip3 install -r .claude/skills/google-site-analytics/requirements.txt
```

---

## Step 2: Google Search Console — Search Performance

### Get top queries (last 28 days)

```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py \
  --report queries \
  --days 28 \
  --limit 20
```

**Output columns:** Query | Clicks | Impressions | CTR | Position

### Get top pages by clicks

```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py \
  --report pages \
  --days 28 \
  --limit 20
```

### Get performance for a specific date range

```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py \
  --report queries \
  --start-date 2024-01-01 \
  --end-date 2024-01-31
```

### Get performance by country

```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py \
  --report countries \
  --days 28
```

### Get performance by device

```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py \
  --report devices \
  --days 28
```

### Check indexing / URL inspection

```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py \
  --report url \
  --url "https://your-site.com/specific-page"
```

### List sitemaps

```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py \
  --report sitemaps
```

---

## Step 3: Google Analytics 4 — Traffic & Behavior

### Get sessions and users overview (last 28 days)

```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py \
  --report overview \
  --days 28
```

**Output:** Sessions | Users | New Users | Bounce Rate | Avg Session Duration

### Get top pages by views

```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py \
  --report pages \
  --days 28 \
  --limit 20
```

### Get traffic by source/medium

```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py \
  --report sources \
  --days 28
```

### Get top events

```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py \
  --report events \
  --days 28
```

### Get realtime active users

```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py \
  --report realtime
```

### Get traffic by country

```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py \
  --report countries \
  --days 28
```

### Get traffic by device category

```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py \
  --report devices \
  --days 28
```

### Custom date range

```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py \
  --report overview \
  --start-date 2024-01-01 \
  --end-date 2024-01-31
```

---

## Step 4: Present Results

After running any query, format the data clearly for the user:

1. **Show a summary table** with the key metrics
2. **Highlight notable trends** — biggest gainers/losers, anomalies
3. **Compare to previous period** if the user asks (run the same command with an earlier date range)
4. **Provide actionable insights** based on the data

### Example output format for top queries:

```
📊 Top Search Queries — Last 28 Days

| Query                    | Clicks | Impressions |  CTR  | Position |
|--------------------------|--------|-------------|-------|----------|
| your brand name          |  1,234 |      8,901  | 13.9% |    1.2   |
| best product category    |    456 |     12,300  |  3.7% |    8.4   |
| how to do something      |    234 |      6,700  |  3.5% |    6.1   |

Total: 1,924 clicks | 27,901 impressions | 6.9% avg CTR | 5.2 avg position
```

---

## Troubleshooting

### 403 Forbidden

- Confirm the service account email has been added to the property (Search Console or GA4) — GCP project ownership alone is not sufficient
- For Search Console: the property may be a domain property (`sc-domain:example.com`) rather than URL prefix (`https://example.com/`). Check by listing sites:
  ```python
  from google.oauth2 import service_account
  from googleapiclient.discovery import build
  creds = service_account.Credentials.from_service_account_file(
      "auth/gsc-service-account.json",
      scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
  )
  service = build("webmasters", "v3", credentials=creds)
  print(service.sites().list().execute())
  ```
- For GA4: confirm `ga4_property_id` is the numeric Property ID, not the Account ID or Measurement ID (`G-XXXXXXXX`)

### No data returned

- Search Console has a ~2-3 day data lag
- GA4 has a ~24-48 hour data lag
- Try a wider date range with `--days 90`

---

## Common Workflows

### Morning site health check
```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report queries --days 7
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report overview --days 7
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report realtime
```

### SEO performance review
```bash
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report queries --days 90 --limit 50
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report pages --days 90 --limit 50
```

### Traffic source analysis
```bash
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report sources --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report countries --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report devices --days 28
```
