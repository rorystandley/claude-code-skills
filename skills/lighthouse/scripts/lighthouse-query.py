#!/usr/bin/env python3
"""
PageSpeed Insights / Lighthouse query tool.

Usage:
    python3 lighthouse-query.py --report score        --url <URL> [--strategy mobile|desktop|both]
    python3 lighthouse-query.py --report vitals       --url <URL> [--strategy mobile|desktop]
    python3 lighthouse-query.py --report opportunities --url <URL> [--strategy mobile|desktop]
    python3 lighthouse-query.py --report site         [--strategy mobile|desktop]
"""

import argparse
import json
import sys
from pathlib import Path

import requests

AUTH_DIR = Path(__file__).parent.parent / "auth"
CONFIG_FILE = AUTH_DIR / "config.json"
PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

CAT_LABEL = {"FAST": "GOOD", "AVERAGE": "NEEDS IMPROVEMENT", "SLOW": "POOR"}

OPPORTUNITY_IDS = [
    "render-blocking-resources",
    "unused-javascript",
    "unused-css-rules",
    "uses-optimized-images",
    "uses-webp-images",
    "uses-responsive-images",
    "efficient-animated-content",
    "uses-text-compression",
    "uses-long-cache-ttl",
    "total-byte-weight",
    "dom-size",
    "server-response-time",
    "redirects",
    "mainthread-work-breakdown",
    "third-party-summary",
]


def get_config():
    if not CONFIG_FILE.exists():
        print(f"No config.json found at {CONFIG_FILE}")
        print("Copy auth/config.example.json to auth/config.json and fill in your API key.")
        sys.exit(1)
    return json.loads(CONFIG_FILE.read_text())


def score_label(score):
    if score is None:
        return "N/A"
    if score >= 0.9:
        return "GOOD"
    if score >= 0.5:
        return "NEEDS IMPROVEMENT"
    return "POOR"


def score_pct(score):
    if score is None:
        return "N/A"
    return str(int(score * 100))


def fmt_ms(ms):
    if ms is None:
        return "N/A"
    if ms >= 1000:
        return f"{ms / 1000:.1f} s"
    return f"{int(ms)} ms"


def cwv_label(metric, value):
    thresholds = {
        "LCP": (2500, 4000),
        "INP": (200, 500),
        "CLS": (0.1, 0.25),
        "FCP": (1800, 3000),
        "TTFB": (800, 1800),
        "TBT": (200, 600),
    }
    if metric not in thresholds or value is None:
        return ""
    good, poor = thresholds[metric]
    if value <= good:
        return "GOOD"
    if value <= poor:
        return "NEEDS IMPROVEMENT"
    return "POOR"


def print_table(headers, rows, max_col_width=60):
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


def run_psi(url, strategy, api_key):
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    }
    if api_key:
        params["key"] = api_key
    try:
        resp = requests.get(PSI_URL, params=params, timeout=60)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        body = e.response.text[:300]
        print(f"API error ({e.response.status_code}): {body}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        sys.exit(1)


def extract_scores(data):
    cats = data.get("lighthouseResult", {}).get("categories", {})
    return {k: cats.get(k, {}).get("score") for k in ["performance", "accessibility", "best-practices", "seo"]}


def extract_lab_vitals(data):
    audits = data.get("lighthouseResult", {}).get("audits", {})
    def a(key):
        return audits.get(key, {})
    return {
        "LCP":          a("largest-contentful-paint").get("numericValue"),
        "LCP_display":  a("largest-contentful-paint").get("displayValue"),
        "TBT":          a("total-blocking-time").get("numericValue"),
        "TBT_display":  a("total-blocking-time").get("displayValue"),
        "CLS":          a("cumulative-layout-shift").get("numericValue"),
        "CLS_display":  a("cumulative-layout-shift").get("displayValue"),
        "FCP":          a("first-contentful-paint").get("numericValue"),
        "FCP_display":  a("first-contentful-paint").get("displayValue"),
        "SI":           a("speed-index").get("numericValue"),
        "SI_display":   a("speed-index").get("displayValue"),
        "TTFB":         a("server-response-time").get("numericValue"),
        "TTFB_display": a("server-response-time").get("displayValue"),
    }


def extract_field_vitals(data):
    exp = data.get("loadingExperience", {})
    metrics = exp.get("metrics", {})
    if not metrics:
        return None

    def m(key):
        return metrics.get(key, {})

    # CLS percentile from CrUX is returned ×100 (e.g. 10 = 0.10)
    cls_raw = m("CUMULATIVE_LAYOUT_SHIFT_SCORE").get("percentile")
    cls_val = cls_raw / 100 if cls_raw is not None else None

    return {
        "LCP_ms":   m("LARGEST_CONTENTFUL_PAINT_MS").get("percentile"),
        "LCP_cat":  CAT_LABEL.get(m("LARGEST_CONTENTFUL_PAINT_MS").get("category"), ""),
        "INP_ms":   m("INTERACTION_TO_NEXT_PAINT").get("percentile"),
        "INP_cat":  CAT_LABEL.get(m("INTERACTION_TO_NEXT_PAINT").get("category"), ""),
        "CLS":      cls_val,
        "CLS_cat":  CAT_LABEL.get(m("CUMULATIVE_LAYOUT_SHIFT_SCORE").get("category"), ""),
        "FCP_ms":   m("FIRST_CONTENTFUL_PAINT_MS").get("percentile"),
        "FCP_cat":  CAT_LABEL.get(m("FIRST_CONTENTFUL_PAINT_MS").get("category"), ""),
        "TTFB_ms":  m("EXPERIMENTAL_TIME_TO_FIRST_BYTE").get("percentile"),
        "TTFB_cat": CAT_LABEL.get(m("EXPERIMENTAL_TIME_TO_FIRST_BYTE").get("category"), ""),
        "overall":  exp.get("overall_category"),
    }


def extract_opportunities(data):
    audits = data.get("lighthouseResult", {}).get("audits", {})
    opps = []
    for audit_id in OPPORTUNITY_IDS:
        audit = audits.get(audit_id, {})
        score = audit.get("score")
        if score is not None and score < 0.9:
            savings_ms = None
            if audit.get("details", {}).get("type") == "opportunity":
                savings_ms = audit["details"].get("overallSavingsMs")
            opps.append({
                "title":      audit.get("title", audit_id),
                "score":      score,
                "display":    audit.get("displayValue", ""),
                "savings_ms": savings_ms,
            })
    opps.sort(key=lambda x: x["score"] if x["score"] is not None else 1)
    return opps


# ── Reports ───────────────────────────────────────────────────────────────────

def report_score(config, url, strategies):
    print(f"\n  Lighthouse Scores — {url}\n")
    rows = []
    for strategy in strategies:
        print(f"  Auditing {strategy}...", end=" ", flush=True)
        data = run_psi(url, strategy, config.get("api_key", ""))
        s = extract_scores(data)
        print("done")
        rows.append([
            strategy.capitalize(),
            f"{score_pct(s['performance'])} ({score_label(s['performance'])})",
            f"{score_pct(s['accessibility'])} ({score_label(s['accessibility'])})",
            f"{score_pct(s['best-practices'])} ({score_label(s['best-practices'])})",
            f"{score_pct(s['seo'])} ({score_label(s['seo'])})",
        ])
    print()
    print_table(["Strategy", "Performance", "Accessibility", "Best Practices", "SEO"], rows)


def report_vitals(config, url, strategy):
    print(f"\n  Core Web Vitals — {url} ({strategy})\n")
    print("  Fetching...", end=" ", flush=True)
    data = run_psi(url, strategy, config.get("api_key", ""))
    print("done\n")

    lab = extract_lab_vitals(data)
    field = extract_field_vitals(data)

    print("  Lab Data (Lighthouse simulation):")
    cls_display = lab["CLS_display"] or (f"{lab['CLS']:.3f}" if lab["CLS"] is not None else "N/A")
    lab_rows = [
        ["LCP — Largest Contentful Paint", lab["LCP_display"] or fmt_ms(lab["LCP"]), cwv_label("LCP", lab["LCP"])],
        ["TBT — Total Blocking Time",      lab["TBT_display"] or fmt_ms(lab["TBT"]), cwv_label("TBT", lab["TBT"])],
        ["CLS — Cumulative Layout Shift",  cls_display,                               cwv_label("CLS", lab["CLS"])],
        ["FCP — First Contentful Paint",   lab["FCP_display"] or fmt_ms(lab["FCP"]), cwv_label("FCP", lab["FCP"])],
        ["Speed Index",                    lab["SI_display"]  or fmt_ms(lab["SI"]),  ""],
        ["TTFB — Server Response Time",    lab["TTFB_display"] or fmt_ms(lab["TTFB"]), cwv_label("TTFB", lab["TTFB"])],
    ]
    print_table(["Metric", "Value", "Rating"], lab_rows)

    print("\n  Field Data (Real Users — 75th percentile):")
    if not field:
        print("  No field data available. Not enough real-user traffic for this URL.")
        return

    if field.get("overall"):
        overall = CAT_LABEL.get(field["overall"], field["overall"])
        print(f"  Overall experience: {overall}\n")

    field_rows = []
    if field["LCP_ms"] is not None:
        field_rows.append(["LCP", fmt_ms(field["LCP_ms"]), field["LCP_cat"]])
    if field["INP_ms"] is not None:
        field_rows.append(["INP — Interaction to Next Paint", fmt_ms(field["INP_ms"]), field["INP_cat"]])
    if field["CLS"] is not None:
        field_rows.append(["CLS", f"{field['CLS']:.3f}", field["CLS_cat"]])
    if field["FCP_ms"] is not None:
        field_rows.append(["FCP", fmt_ms(field["FCP_ms"]), field["FCP_cat"]])
    if field["TTFB_ms"] is not None:
        field_rows.append(["TTFB", fmt_ms(field["TTFB_ms"]), field["TTFB_cat"]])

    if field_rows:
        print_table(["Metric", "p75", "Rating"], field_rows)
    else:
        print("  No individual metric data available.")


def report_opportunities(config, url, strategy):
    print(f"\n  Improvement Opportunities — {url} ({strategy})\n")
    print("  Fetching...", end=" ", flush=True)
    data = run_psi(url, strategy, config.get("api_key", ""))
    print("done\n")

    scores = extract_scores(data)
    perf = scores["performance"]
    print(f"  Performance score: {score_pct(perf)} — {score_label(perf)}\n")

    opps = extract_opportunities(data)
    if not opps:
        print("  No significant opportunities found. Page is well optimised.")
        return

    rows = []
    for opp in opps:
        saving = ""
        if opp["savings_ms"] is not None and opp["savings_ms"] > 0:
            saving = f"~{fmt_ms(opp['savings_ms'])}"
        elif opp["display"]:
            saving = opp["display"]
        rows.append([opp["title"][:55], score_pct(opp["score"]), saving])

    print_table(["Opportunity", "Score", "Potential Saving"], rows)


def report_site(config, strategy):
    urls = config.get("urls", [])
    if not urls:
        print("No URLs configured. Add a 'urls' list to auth/config.json.")
        sys.exit(1)

    print(f"\n  Site Performance Overview ({strategy})\n")
    rows = []
    for url in urls:
        short = url.replace("https://", "").replace("http://", "").rstrip("/")[:45]
        print(f"  Auditing {short}...", end=" ", flush=True)
        data = run_psi(url, strategy, config.get("api_key", ""))
        s = extract_scores(data)
        lab = extract_lab_vitals(data)
        print("done")
        cls_display = lab["CLS_display"] or (f"{lab['CLS']:.3f}" if lab["CLS"] is not None else "N/A")
        rows.append([
            short,
            score_pct(s["performance"]),
            score_pct(s["seo"]),
            score_pct(s["accessibility"]),
            lab["LCP_display"] or fmt_ms(lab["LCP"]),
            lab["TBT_display"] or fmt_ms(lab["TBT"]),
            cls_display,
        ])

    print()
    print_table(["URL", "Perf", "SEO", "A11y", "LCP", "TBT", "CLS"], rows)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PageSpeed Insights / Lighthouse query tool")
    parser.add_argument("--report", required=True,
                        choices=["score", "vitals", "opportunities", "site"])
    parser.add_argument("--url", help="URL to audit (required for score/vitals/opportunities)")
    parser.add_argument("--strategy", default="mobile",
                        choices=["mobile", "desktop", "both"],
                        help="Device strategy (default: mobile)")
    args = parser.parse_args()

    config = get_config()

    if args.report in ("score", "vitals", "opportunities") and not args.url:
        print("--url is required for this report type")
        sys.exit(1)

    if args.report == "score":
        strategies = ["mobile", "desktop"] if args.strategy == "both" else [args.strategy]
        report_score(config, args.url, strategies)
    elif args.report == "vitals":
        strategy = "mobile" if args.strategy == "both" else args.strategy
        report_vitals(config, args.url, strategy)
    elif args.report == "opportunities":
        strategy = "mobile" if args.strategy == "both" else args.strategy
        report_opportunities(config, args.url, strategy)
    elif args.report == "site":
        strategy = "mobile" if args.strategy == "both" else args.strategy
        report_site(config, strategy)

    print()


if __name__ == "__main__":
    main()
