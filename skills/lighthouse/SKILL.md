---
name: lighthouse
description: "Run Lighthouse / PageSpeed Insights audits against any URL to get performance scores, Core Web Vitals, and improvement opportunities. Use when the user asks about: page speed, performance score, Core Web Vitals, LCP, INP, CLS, FCP, TTFB, TBT, Lighthouse, PageSpeed, how fast is a page, site performance, web vitals, slow page, render-blocking resources, unused JavaScript, image optimisation, mobile performance, desktop performance, accessibility score, SEO score. Keywords: lighthouse, pagespeed, cwv, web vitals, lcp, cls, inp, ttfb, fcp, tbt, performance, speed, slow."
argument-hint: "[score|vitals|opportunities|site] [--url <URL>] [--strategy mobile|desktop|both]"
allowed-tools: Bash
disable-model-invocation: false
---

# Lighthouse / PageSpeed Insights Skill

Run Google PageSpeed Insights against any URL to get Lighthouse performance scores, Core Web Vitals (lab + real-user field data), and a ranked list of improvement opportunities.

Uses the free [PageSpeed Insights API](https://developers.google.com/speed/docs/insights/v5/get-started) — no local Chrome required.

---

## Prerequisites Check

Before running any audit, verify credentials are in place:

```bash
ls .claude/skills/lighthouse/auth/
```

Look for `config.json`. If missing, follow **Step 1: Setup** below.

---

## Step 1: First-Time Setup

### 1a. Create config.json

```bash
cp .claude/skills/lighthouse/auth/config.example.json \
   .claude/skills/lighthouse/auth/config.json
```

Edit `config.json` with your site's URLs:
```json
{
  "api_key": "",
  "urls": [
    "https://your-site.com/",
    "https://your-site.com/important-page"
  ]
}
```

`urls` is used by `--report site` to audit multiple pages at once. `api_key` is optional — the API works unauthenticated. Only add a key if you hit 429 rate-limit errors (free GCP API key, no service account needed).

### 1b. Install dependencies

```bash
pip3 install -r .claude/skills/lighthouse/requirements.txt
```

---

## Step 2: Run Audits

### Get all Lighthouse scores (performance, SEO, accessibility, best practices)

```bash
python3 .claude/skills/lighthouse/scripts/lighthouse-query.py \
  --report score \
  --url "https://your-site.com/" \
  --strategy both
```

Outputs a table with mobile and desktop scores for all four Lighthouse categories.

### Get Core Web Vitals detail

```bash
python3 .claude/skills/lighthouse/scripts/lighthouse-query.py \
  --report vitals \
  --url "https://your-site.com/" \
  --strategy mobile
```

Shows **lab data** (Lighthouse simulation) and **field data** (real users at p75) for LCP, INP, CLS, FCP, TTFB. Field data is only available when there is enough real-user traffic for the URL (from the Chrome UX Report).

### Get improvement opportunities

```bash
python3 .claude/skills/lighthouse/scripts/lighthouse-query.py \
  --report opportunities \
  --url "https://your-site.com/" \
  --strategy mobile
```

Lists every audit that scored below 90, sorted by score (worst first), with estimated time savings where available.

### Batch audit all configured URLs

```bash
python3 .claude/skills/lighthouse/scripts/lighthouse-query.py \
  --report site \
  --strategy mobile
```

Runs performance scores across every URL in `config.json` and outputs a comparison table. Useful for a morning health check alongside GSC and GA4.

---

## Step 3: Interpret and Act

After running an audit, help the user understand and prioritise:

1. **Score colour bands:** 90–100 = Good, 50–89 = Needs Improvement, 0–49 = Poor
2. **Core Web Vitals thresholds:**
   | Metric | Good     | Needs Improvement | Poor     |
   |--------|----------|-------------------|----------|
   | LCP    | < 2.5 s  | 2.5 – 4.0 s       | > 4.0 s  |
   | INP    | < 200 ms | 200 – 500 ms      | > 500 ms |
   | CLS    | < 0.10   | 0.10 – 0.25       | > 0.25   |
   | FCP    | < 1.8 s  | 1.8 – 3.0 s       | > 3.0 s  |
   | TTFB   | < 800 ms | 800 ms – 1.8 s    | > 1.8 s  |
3. **Lab vs field data:** Lab data is reproducible but synthetic. Field data (CrUX) is real users — it's what Google actually uses for ranking. If lab is green but field is red, check for slow third-party scripts or real-device CPU constraints.
4. **Quickest wins:** Unused JS/CSS and unoptimised images typically offer the largest savings with the least implementation effort.

---

## Common Workflows

### Morning performance check (alongside analytics)
```bash
python3 .claude/skills/lighthouse/scripts/lighthouse-query.py --report site --strategy mobile
python3 .claude/skills/google-site-analytics/scripts/gsc-query.py --report queries --days 7
python3 .claude/skills/google-site-analytics/scripts/ga4-query.py --report overview --days 7
```

### Investigate a specific slow page
```bash
python3 .claude/skills/lighthouse/scripts/lighthouse-query.py --report vitals --url "https://your-site.com/slow-page" --strategy mobile
python3 .claude/skills/lighthouse/scripts/lighthouse-query.py --report opportunities --url "https://your-site.com/slow-page" --strategy mobile
```

### Mobile vs desktop comparison
```bash
python3 .claude/skills/lighthouse/scripts/lighthouse-query.py --report score --url "https://your-site.com/" --strategy both
```

---

## Troubleshooting

### 400 Bad Request
- The URL must include `https://` or `http://` and be publicly accessible (not localhost)
- Check the URL is valid: `curl -I "https://your-site.com/"`

### 429 Too Many Requests
- You've hit the unauthenticated rate limit; make sure `api_key` is set in `config.json`
- Free quota is 25,000 requests/day — each `--report site` call uses one request per URL

### Field data missing
- Normal for low-traffic pages or new URLs — the Chrome UX Report only includes URLs with sufficient real-user data
- Lab data (Lighthouse simulation) is always available

### Score varies between runs
- Lighthouse scores have natural variance (~5 points) due to network conditions and CPU throttling in the simulation
- Run 3 times and average, or use field data for a more stable signal
