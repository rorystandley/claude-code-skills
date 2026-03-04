#!/usr/bin/env python3
"""
Google Search Console query tool.

Usage:
    python3 gsc-query.py --report queries   [--days N] [--limit N]
    python3 gsc-query.py --report pages     [--days N] [--limit N]
    python3 gsc-query.py --report countries [--days N]
    python3 gsc-query.py --report devices   [--days N]
    python3 gsc-query.py --report sitemaps
    python3 gsc-query.py --report url       --url <URL>
    python3 gsc-query.py --report queries   --start-date YYYY-MM-DD --end-date YYYY-MM-DD
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent / "auth"
SA_FILE = SCRIPT_DIR / "gsc-service-account.json"
CONFIG_FILE = SCRIPT_DIR / "config.json"

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def get_creds():
    from google.oauth2 import service_account

    if not SA_FILE.exists():
        print(f"No service account file found at {SA_FILE}")
        print("Place your GSC service account JSON at that path.")
        sys.exit(1)
    return service_account.Credentials.from_service_account_file(
        str(SA_FILE), scopes=SCOPES
    )


def get_config():
    if not CONFIG_FILE.exists():
        print(f"No config.json found at {CONFIG_FILE}")
        print("Create it with: {\"site_url\": \"https://your-site.com/\", \"ga4_property_id\": \"123456789\"}")
        sys.exit(1)
    return json.loads(CONFIG_FILE.read_text())


def build_service(creds):
    from googleapiclient.discovery import build
    return build("webmasters", "v3", credentials=creds)


def date_range(days, start_date=None, end_date=None):
    if start_date and end_date:
        return start_date, end_date
    today = date.today()
    end = today - timedelta(days=3)  # GSC has ~3 day lag
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def fmt_num(n):
    return f"{int(n):,}"


def fmt_pct(n):
    return f"{n * 100:.1f}%"


def fmt_pos(n):
    return f"{n:.1f}"


def print_table(headers, rows, max_col_width=50):
    if not rows:
        print("  No data returned.")
        return
    col_widths = [len(h) for h in headers]
    str_rows = []
    for row in rows:
        str_row = [str(cell) for cell in row]
        str_rows.append(str_row)
        for i, cell in enumerate(str_row):
            col_widths[i] = min(max_col_width, max(col_widths[i], len(cell)))

    sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
    header_row = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    print(sep)
    print(header_row)
    print(sep)
    for row in str_rows:
        print("| " + " | ".join(cell.ljust(col_widths[i]) for i, cell in enumerate(row)) + " |")
    print(sep)


# ── Report: Search Analytics (queries / pages / countries / devices) ──────────

def search_analytics(service, site_url, dimension, start_date, end_date, limit):
    body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": [dimension],
        "rowLimit": limit,
        "startRow": 0,
    }
    try:
        res = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    except Exception as e:
        print(f"API error: {e}")
        sys.exit(1)

    rows = res.get("rows", [])
    return rows


def report_queries(service, site_url, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n📊 Top {args.limit} Search Queries — {start} to {end}")
    print(f"   Site: {site_url}\n")

    rows = search_analytics(service, site_url, "query", start, end, args.limit)
    if not rows:
        print("No data. (Search Console has a 2-3 day lag; try a wider date range.)")
        return

    total_clicks = sum(r["clicks"] for r in rows)
    total_impressions = sum(r["impressions"] for r in rows)

    table_rows = []
    for r in rows:
        table_rows.append([
            r["keys"][0][:50],
            fmt_num(r["clicks"]),
            fmt_num(r["impressions"]),
            fmt_pct(r["ctr"]),
            fmt_pos(r["position"]),
        ])

    print_table(["Query", "Clicks", "Impressions", "CTR", "Avg Position"], table_rows)
    avg_ctr = total_clicks / total_impressions if total_impressions else 0
    print(f"\n  Totals: {fmt_num(total_clicks)} clicks | {fmt_num(total_impressions)} impressions | {fmt_pct(avg_ctr)} avg CTR")


def report_pages(service, site_url, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n📄 Top {args.limit} Pages by Clicks — {start} to {end}")
    print(f"   Site: {site_url}\n")

    rows = search_analytics(service, site_url, "page", start, end, args.limit)
    if not rows:
        print("No data.")
        return

    table_rows = []
    for r in rows:
        url = r["keys"][0].replace(site_url, "/")[:50]
        table_rows.append([
            url,
            fmt_num(r["clicks"]),
            fmt_num(r["impressions"]),
            fmt_pct(r["ctr"]),
            fmt_pos(r["position"]),
        ])

    print_table(["Page", "Clicks", "Impressions", "CTR", "Avg Position"], table_rows)


def report_countries(service, site_url, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n🌍 Performance by Country — {start} to {end}")
    print(f"   Site: {site_url}\n")

    rows = search_analytics(service, site_url, "country", start, end, 50)
    if not rows:
        print("No data.")
        return

    table_rows = [
        [r["keys"][0].upper(), fmt_num(r["clicks"]), fmt_num(r["impressions"]), fmt_pct(r["ctr"]), fmt_pos(r["position"])]
        for r in rows
    ]
    print_table(["Country", "Clicks", "Impressions", "CTR", "Avg Position"], table_rows)


def report_devices(service, site_url, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n📱 Performance by Device — {start} to {end}")
    print(f"   Site: {site_url}\n")

    rows = search_analytics(service, site_url, "device", start, end, 10)
    if not rows:
        print("No data.")
        return

    table_rows = [
        [r["keys"][0].capitalize(), fmt_num(r["clicks"]), fmt_num(r["impressions"]), fmt_pct(r["ctr"]), fmt_pos(r["position"])]
        for r in rows
    ]
    print_table(["Device", "Clicks", "Impressions", "CTR", "Avg Position"], table_rows)


# ── Report: Sitemaps ───────────────────────────────────────────────────────────

def report_sitemaps(service, site_url):
    print(f"\n🗺  Sitemaps — {site_url}\n")
    try:
        res = service.sitemaps().list(siteUrl=site_url).execute()
    except Exception as e:
        print(f"API error: {e}")
        sys.exit(1)

    sitemaps = res.get("sitemap", [])
    if not sitemaps:
        print("No sitemaps found.")
        return

    table_rows = []
    for s in sitemaps:
        errors = s.get("errors", "0")
        warnings = s.get("warnings", "0")
        submitted = s.get("contents", [{}])[0].get("submitted", "?") if s.get("contents") else "?"
        indexed = s.get("contents", [{}])[0].get("indexed", "?") if s.get("contents") else "?"
        table_rows.append([
            s["path"][:60],
            s.get("lastSubmitted", "")[:10],
            s.get("isPending", False) and "Pending" or "Done",
            str(submitted),
            str(indexed),
            str(errors),
            str(warnings),
        ])

    print_table(["Sitemap URL", "Last Submitted", "Status", "Submitted", "Indexed", "Errors", "Warnings"], table_rows)


# ── Report: URL Inspection ─────────────────────────────────────────────────────

def report_url(service, site_url, url):
    print(f"\n🔍 URL Inspection\n   URL: {url}\n   Site: {site_url}\n")
    try:
        res = service.urlInspection().index().inspect(
            body={"inspectionUrl": url, "siteUrl": site_url}
        ).execute()
    except Exception as e:
        print(f"API error: {e}")
        sys.exit(1)

    result = res.get("inspectionResult", {})
    index_status = result.get("indexStatusResult", {})

    verdict = index_status.get("verdict", "UNKNOWN")
    coverage = index_status.get("coverageState", "Unknown")
    crawled = index_status.get("lastCrawlTime", "Never")
    robots = index_status.get("robotsTxtState", "Unknown")
    canonical = index_status.get("googleCanonical", url)
    referring = index_status.get("referringUrls", [])

    verdict_icon = {"PASS": "✅", "FAIL": "❌", "NEUTRAL": "⚠️"}.get(verdict, "❓")

    print(f"  Verdict:       {verdict_icon} {verdict}")
    print(f"  Coverage:      {coverage}")
    print(f"  Last crawled:  {crawled[:19] if crawled else 'Never'}")
    print(f"  Robots.txt:    {robots}")
    print(f"  Canonical:     {canonical}")
    if referring:
        print(f"  Referring URLs: {', '.join(referring[:3])}")

    mobile = result.get("mobileUsabilityResult", {})
    if mobile:
        mv = mobile.get("verdict", "UNKNOWN")
        mv_icon = {"PASS": "✅", "FAIL": "❌"}.get(mv, "⚠️")
        print(f"  Mobile:        {mv_icon} {mv}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Google Search Console query tool")
    parser.add_argument("--report", required=True,
                        choices=["queries", "pages", "countries", "devices", "sitemaps", "url"],
                        help="Report type")
    parser.add_argument("--days", type=int, default=28, help="Number of days (default: 28)")
    parser.add_argument("--limit", type=int, default=20, help="Max rows to return (default: 20)")
    parser.add_argument("--start-date", help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", help="End date YYYY-MM-DD")
    parser.add_argument("--url", help="URL to inspect (for --report url)")
    args = parser.parse_args()

    creds = get_creds()
    config = get_config()
    site_url = config["site_url"]
    service = build_service(creds)

    if args.report == "queries":
        report_queries(service, site_url, args)
    elif args.report == "pages":
        report_pages(service, site_url, args)
    elif args.report == "countries":
        report_countries(service, site_url, args)
    elif args.report == "devices":
        report_devices(service, site_url, args)
    elif args.report == "sitemaps":
        report_sitemaps(service, site_url)
    elif args.report == "url":
        if not args.url:
            print("--url required for url inspection report")
            sys.exit(1)
        report_url(service, site_url, args.url)

    print()


if __name__ == "__main__":
    main()
