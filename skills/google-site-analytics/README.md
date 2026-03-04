# google-site-analytics

A Claude Code skill that lets you query **Google Search Console** and **Google Analytics 4** directly from your terminal using natural language.

Ask Claude things like:
- *"What are my top search queries this month?"*
- *"Show me traffic sources for the last 90 days"*
- *"How many active users are on the site right now?"*
- *"Which pages have the most impressions but lowest CTR?"*

## How it works

This is a [Claude Code skill](https://docs.anthropic.com/en/docs/claude-code/skills) — a set of scripts and instructions that Claude Code reads to know how to fetch and present your site data. Authentication uses **Google Cloud service accounts** (no browser OAuth flow required).

## Installation

### 1. Copy into your project

```bash
cp -r google-site-analytics .claude/skills/google-site-analytics
```

### 2. Install Python dependencies

```bash
pip3 install -r .claude/skills/google-site-analytics/requirements.txt
```

### 3. Create service accounts

In [Google Cloud Console](https://console.cloud.google.com/):

1. Enable the **Google Search Console API** and **Google Analytics Data API**
2. Create two service accounts (IAM & Admin → Service Accounts):
   - One for Search Console (e.g. `gsc-reader`)
   - One for GA4 (e.g. `ga4-reader`)
3. Download a JSON key for each and save them as:
   - `.claude/skills/google-site-analytics/auth/gsc-service-account.json`
   - `.claude/skills/google-site-analytics/auth/ga4-service-account.json`

### 4. Grant property access

**Search Console:** Settings → Users and permissions → Add user → enter the GSC service account email → Full or Restricted permission.

**GA4:** Admin → Property Access Management → Add user → enter the GA4 service account email → Viewer role.

### 5. Configure your site

```bash
cp .claude/skills/google-site-analytics/auth/config.example.json \
   .claude/skills/google-site-analytics/auth/config.json
```

Edit `config.json`:

```json
{
  "site_url": "sc-domain:your-site.com",
  "ga4_property_id": "123456789"
}
```

> **Finding your values:**
> - `site_url`: Check Search Console — domain properties use `sc-domain:example.com`, URL prefix properties use `https://example.com/`
> - `ga4_property_id`: The numeric ID from GA4 Admin → Property Settings. Find it in your GA4 URL: `analytics.google.com/analytics/web/#/p**123456789**/...`. This is NOT the `G-XXXXXXXX` Measurement ID.

### 6. Add to `.gitignore`

Your credentials are already listed in `.gitignore` within the skill folder, but make sure your project's root `.gitignore` also excludes them:

```
.claude/skills/google-site-analytics/auth/*.json
```

## Usage

Once installed, just ask Claude Code naturally:

```
show me my top search queries this week
```

```
what's my GA4 traffic overview for the last 90 days?
```

```
check the indexing status of https://my-site.com/blog/post-1
```

```
show traffic by country and device for last month
```

You can also run the scripts directly:

```bash
# Search Console
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report queries --days 28
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report pages --days 28
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report countries --days 28
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report devices --days 28
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report sitemaps
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report url --url "https://your-site.com/page"

# Google Analytics 4
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report overview --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report pages --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report sources --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report events --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report countries --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report devices --days 28
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report realtime
```

## Project structure

```
google-site-analytics/
├── SKILL.md                      # Claude Code skill definition
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── .gitignore                    # Excludes credential files
├── auth/
│   └── config.example.json       # Config template (copy to config.json)
└── scripts/
    ├── gsc-query.py              # Google Search Console queries
    └── ga4-query.py              # Google Analytics 4 queries
```

## Requirements

- Python 3.8+
- [Claude Code](https://claude.ai/code)
- A Google Cloud project with Search Console API and Analytics Data API enabled

## License

MIT
