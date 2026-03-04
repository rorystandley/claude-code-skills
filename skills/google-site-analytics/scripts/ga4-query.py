#!/usr/bin/env python3
"""
Google Analytics 4 (Data API) query tool.

Usage:
    python3 ga4-query.py --report overview   [--days N]
    python3 ga4-query.py --report pages      [--days N] [--limit N]
    python3 ga4-query.py --report sources    [--days N]
    python3 ga4-query.py --report events     [--days N] [--limit N]
    python3 ga4-query.py --report countries  [--days N]
    python3 ga4-query.py --report devices    [--days N]
    python3 ga4-query.py --report realtime
    python3 ga4-query.py --report overview   --start-date YYYY-MM-DD --end-date YYYY-MM-DD
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent / "auth"
SA_FILE = SCRIPT_DIR / "ga4-service-account.json"
CONFIG_FILE = SCRIPT_DIR / "config.json"

SCOPES = ["https://www.googleapis.com/auth/analytics.readonly"]


def get_creds():
    from google.oauth2 import service_account

    if not SA_FILE.exists():
        print(f"No service account file found at {SA_FILE}")
        print("Place your GA4 service account JSON at that path.")
        sys.exit(1)
    return service_account.Credentials.from_service_account_file(
        str(SA_FILE), scopes=SCOPES
    )


def get_config():
    if not CONFIG_FILE.exists():
        print(f"No config.json found at {CONFIG_FILE}")
        print('Create it with: {"site_url": "https://your-site.com/", "ga4_property_id": "123456789"}')
        sys.exit(1)
    return json.loads(CONFIG_FILE.read_text())


def build_client(creds):
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    return BetaAnalyticsDataClient(credentials=creds)


def ensure_ga4_package():
    try:
        import google.analytics.data_v1beta  # noqa: F401
    except ImportError:
        import os
        print("Installing google-analytics-data...")
        os.system(f"{sys.executable} -m pip install google-analytics-data --quiet")


def date_range(days, start_date=None, end_date=None):
    if start_date and end_date:
        return start_date, end_date
    today = date.today()
    end = today - timedelta(days=1)  # GA4 has ~24h lag
    start = end - timedelta(days=days - 1)
    return start.isoformat(), end.isoformat()


def fmt_num(n):
    try:
        return f"{int(float(n)):,}"
    except (ValueError, TypeError):
        return str(n)


def fmt_pct(n):
    try:
        return f"{float(n) * 100:.1f}%"
    except (ValueError, TypeError):
        return str(n)


def fmt_dur(seconds):
    try:
        s = float(seconds)
        if s < 60:
            return f"{s:.0f}s"
        m, sec = divmod(int(s), 60)
        return f"{m}m {sec:02d}s"
    except (ValueError, TypeError):
        return str(seconds)


def print_table(headers, rows, max_col_width=55):
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


def run_report(client, property_id, dimensions, metrics, start_date, end_date, limit=20):
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric, OrderBy
    )

    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
        limit=limit,
        order_bys=[OrderBy(metric=OrderBy.MetricOrderBy(metric_name=metrics[0]), desc=True)],
    )
    try:
        return client.run_report(request)
    except Exception as e:
        print(f"GA4 API error: {e}")
        sys.exit(1)


def run_realtime_report(client, property_id):
    from google.analytics.data_v1beta.types import (
        RunRealtimeReportRequest, Dimension, Metric
    )

    request = RunRealtimeReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="unifiedScreenName")],
        metrics=[Metric(name="activeUsers")],
        limit=20,
    )
    try:
        return client.run_realtime_report(request)
    except Exception as e:
        print(f"GA4 Realtime API error: {e}")
        sys.exit(1)


def extract_rows(response):
    rows = []
    for row in response.rows:
        dim_values = [d.value for d in row.dimension_values]
        metric_values = [m.value for m in row.metric_values]
        rows.append(dim_values + metric_values)
    return rows


# ── Reports ────────────────────────────────────────────────────────────────────

def report_overview(client, property_id, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n📈 Site Overview — {start} to {end}")
    print(f"   GA4 Property: {property_id}\n")

    response = run_report(
        client, property_id,
        dimensions=["date"],
        metrics=["sessions", "totalUsers", "newUsers", "bounceRate", "averageSessionDuration", "screenPageViews"],
        start_date=start,
        end_date=end,
        limit=400,
    )

    if not response.rows:
        print("No data. (GA4 has a ~24-48h lag; try a wider date range.)")
        return

    totals = {
        "sessions": 0, "users": 0, "new_users": 0,
        "bounce_rate_sum": 0.0, "duration_sum": 0.0, "pageviews": 0, "row_count": 0
    }
    for row in response.rows:
        vals = [m.value for m in row.metric_values]
        totals["sessions"] += int(float(vals[0]))
        totals["users"] += int(float(vals[1]))
        totals["new_users"] += int(float(vals[2]))
        totals["bounce_rate_sum"] += float(vals[3])
        totals["duration_sum"] += float(vals[4])
        totals["pageviews"] += int(float(vals[5]))
        totals["row_count"] += 1

    n = totals["row_count"] or 1
    avg_bounce = totals["bounce_rate_sum"] / n
    avg_duration = totals["duration_sum"] / n

    days_shown = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    print(f"  Sessions:          {fmt_num(totals['sessions'])}")
    print(f"  Users:             {fmt_num(totals['users'])}")
    print(f"  New Users:         {fmt_num(totals['new_users'])}")
    print(f"  Page Views:        {fmt_num(totals['pageviews'])}")
    print(f"  Avg Bounce Rate:   {fmt_pct(avg_bounce)}")
    print(f"  Avg Session Dur:   {fmt_dur(avg_duration)}")
    print(f"  Days in range:     {days_shown}")
    print(f"  Sessions/day avg:  {fmt_num(totals['sessions'] / days_shown)}")


def report_pages(client, property_id, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n📄 Top {args.limit} Pages by Views — {start} to {end}\n")

    response = run_report(
        client, property_id,
        dimensions=["pagePath"],
        metrics=["screenPageViews", "sessions", "totalUsers", "averageSessionDuration"],
        start_date=start,
        end_date=end,
        limit=args.limit,
    )

    rows = extract_rows(response)
    if not rows:
        print("No data.")
        return

    table_rows = [
        [r[0][:55], fmt_num(r[1]), fmt_num(r[2]), fmt_num(r[3]), fmt_dur(r[4])]
        for r in rows
    ]
    print_table(["Page Path", "Views", "Sessions", "Users", "Avg Duration"], table_rows)


def report_sources(client, property_id, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n🔗 Traffic by Source/Medium — {start} to {end}\n")

    response = run_report(
        client, property_id,
        dimensions=["sessionSource", "sessionMedium"],
        metrics=["sessions", "totalUsers", "newUsers", "bounceRate"],
        start_date=start,
        end_date=end,
        limit=25,
    )

    rows = extract_rows(response)
    if not rows:
        print("No data.")
        return

    table_rows = [
        [r[0][:30], r[1][:15], fmt_num(r[2]), fmt_num(r[3]), fmt_num(r[4]), fmt_pct(r[5])]
        for r in rows
    ]
    print_table(["Source", "Medium", "Sessions", "Users", "New Users", "Bounce Rate"], table_rows)


def report_events(client, property_id, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n⚡ Top {args.limit} Events — {start} to {end}\n")

    response = run_report(
        client, property_id,
        dimensions=["eventName"],
        metrics=["eventCount", "totalUsers", "eventCountPerUser"],
        start_date=start,
        end_date=end,
        limit=args.limit,
    )

    rows = extract_rows(response)
    if not rows:
        print("No data.")
        return

    table_rows = [
        [r[0][:40], fmt_num(r[1]), fmt_num(r[2]), f"{float(r[3]):.1f}"]
        for r in rows
    ]
    print_table(["Event Name", "Count", "Users", "Per User"], table_rows)


def report_countries(client, property_id, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n🌍 Traffic by Country — {start} to {end}\n")

    response = run_report(
        client, property_id,
        dimensions=["country"],
        metrics=["sessions", "totalUsers", "screenPageViews"],
        start_date=start,
        end_date=end,
        limit=30,
    )

    rows = extract_rows(response)
    if not rows:
        print("No data.")
        return

    table_rows = [
        [r[0][:30], fmt_num(r[1]), fmt_num(r[2]), fmt_num(r[3])]
        for r in rows
    ]
    print_table(["Country", "Sessions", "Users", "Page Views"], table_rows)


def report_devices(client, property_id, args):
    start, end = date_range(args.days, args.start_date, args.end_date)
    print(f"\n📱 Traffic by Device Category — {start} to {end}\n")

    response = run_report(
        client, property_id,
        dimensions=["deviceCategory"],
        metrics=["sessions", "totalUsers", "bounceRate", "averageSessionDuration"],
        start_date=start,
        end_date=end,
        limit=10,
    )

    rows = extract_rows(response)
    if not rows:
        print("No data.")
        return

    table_rows = [
        [r[0].capitalize(), fmt_num(r[1]), fmt_num(r[2]), fmt_pct(r[3]), fmt_dur(r[4])]
        for r in rows
    ]
    print_table(["Device", "Sessions", "Users", "Bounce Rate", "Avg Duration"], table_rows)


def report_realtime(client, property_id):
    print(f"\n⚡ Realtime Active Users — GA4 Property {property_id}\n")

    response = run_realtime_report(client, property_id)

    if not response.rows:
        print("  0 active users right now.")
        return

    total = sum(int(r.metric_values[0].value) for r in response.rows)
    print(f"  Active users right now: {fmt_num(total)}\n")

    table_rows = [
        [r.dimension_values[0].value[:55], fmt_num(r.metric_values[0].value)]
        for r in response.rows
    ]
    print_table(["Active Page/Screen", "Users"], table_rows)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Google Analytics 4 query tool")
    parser.add_argument("--report", required=True,
                        choices=["overview", "pages", "sources", "events", "countries", "devices", "realtime"],
                        help="Report type")
    parser.add_argument("--days", type=int, default=28, help="Number of days (default: 28)")
    parser.add_argument("--limit", type=int, default=20, help="Max rows (default: 20)")
    parser.add_argument("--start-date", help="Start date YYYY-MM-DD")
    parser.add_argument("--end-date", help="End date YYYY-MM-DD")
    args = parser.parse_args()

    ensure_ga4_package()

    creds = get_creds()
    config = get_config()
    property_id = config.get("ga4_property_id")
    if not property_id:
        print("ga4_property_id not set in config.json")
        sys.exit(1)

    client = build_client(creds)

    if args.report == "overview":
        report_overview(client, property_id, args)
    elif args.report == "pages":
        report_pages(client, property_id, args)
    elif args.report == "sources":
        report_sources(client, property_id, args)
    elif args.report == "events":
        report_events(client, property_id, args)
    elif args.report == "countries":
        report_countries(client, property_id, args)
    elif args.report == "devices":
        report_devices(client, property_id, args)
    elif args.report == "realtime":
        report_realtime(client, property_id)

    print()


if __name__ == "__main__":
    main()
