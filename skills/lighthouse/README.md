# lighthouse

Run [Google PageSpeed Insights](https://pagespeed.web.dev/) from Claude Code to get Lighthouse performance scores, Core Web Vitals, and improvement opportunities for any URL.

No local Chrome or Node.js required — uses the free PageSpeed Insights REST API.

## What it gives you

- **Performance, SEO, Accessibility, Best Practices** scores (0–100) for mobile and/or desktop
- **Core Web Vitals** — LCP, INP, CLS, FCP, TTFB — with both Lighthouse lab data and real-user field data from the Chrome UX Report
- **Ranked improvement opportunities** with estimated time savings (unused JS, render-blocking resources, image optimisation, etc.)
- **Batch site audit** — scores for all your key URLs in one table

## Setup

### 1. Get a Google API key

The PageSpeed Insights API is free (25,000 requests/day with a key).

1. Open [Google Cloud Console](https://console.cloud.google.com/)
2. Select or create a project (you can reuse the one you made for google-site-analytics)
3. Go to **APIs & Services → Library**, search for **PageSpeed Insights API**, and enable it
4. Go to **APIs & Services → Credentials → Create Credentials → API key**
5. Copy the key

### 2. Create your config file

```bash
cp auth/config.example.json auth/config.json
```

Edit `auth/config.json`:

```json
{
  "api_key": "YOUR_GOOGLE_API_KEY",
  "urls": [
    "https://your-site.com/",
    "https://your-site.com/blog",
    "https://your-site.com/pricing"
  ]
}
```

`urls` is the list of pages audited by `--report site`. Add your homepage and key landing pages.

### 3. Install dependencies

```bash
pip3 install -r requirements.txt
```

## Usage

```bash
# All Lighthouse scores for a URL (mobile + desktop)
python3 scripts/lighthouse-query.py --report score --url "https://your-site.com/" --strategy both

# Core Web Vitals (lab + real-user data)
python3 scripts/lighthouse-query.py --report vitals --url "https://your-site.com/"

# What to fix and estimated savings
python3 scripts/lighthouse-query.py --report opportunities --url "https://your-site.com/"

# Batch audit of all configured URLs
python3 scripts/lighthouse-query.py --report site
```

When installed as a Claude Code plugin, just ask naturally:
- *"How fast is my homepage?"*
- *"Check Core Web Vitals for the pricing page"*
- *"What's dragging down my Lighthouse score?"*
- *"Run a performance check across the site"*

## Auth files

`auth/config.json` is gitignored — never commit it.
