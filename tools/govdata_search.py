"""
US Government Data Search for Mindrian
========================================

Unified interface to 3 federal data APIs:
  - BLS (Bureau of Labor Statistics) — employment, wages, CPI, productivity
  - Census ACS (American Community Survey) — demographics, economics, housing
  - FRED (Federal Reserve Economic Data) — 800K+ economic time series

BLS: No key required (public API).
Census: Requires DATA_GOV_API_KEY (free at api.data.gov/signup).
FRED: Requires FRED_API_KEY (free at fred.stlouisfed.org).
"""

import logging
import os
import json
from typing import Dict, List, Optional

import requests

logger = logging.getLogger("govdata_search")

# ---------------------------------------------------------------------------
# BLS — Bureau of Labor Statistics (no key needed for v1)
# ---------------------------------------------------------------------------

# Common series IDs for PWS-relevant data
BLS_POPULAR_SERIES = {
    "unemployment": "LNS14000000",       # Unemployment rate
    "cpi": "CUUR0000SA0",                # CPI All Urban Consumers
    "nonfarm_payroll": "CES0000000001",   # Total Nonfarm Employment
    "avg_hourly_earnings": "CES0500000003",  # Avg Hourly Earnings
    "productivity": "PRS85006092",        # Nonfarm Business Labor Productivity
    "job_openings": "JTS000000000000000JOL",  # JOLTS Job Openings
}


def search_bls(query: str, start_year: str = "2020", end_year: str = "2025") -> Dict:
    """
    Search BLS for labor/economic data.

    Uses v2 API if BLS_API_KEY is set, otherwise v1 (no key, limited).
    The query is matched against popular series descriptions.
    """
    api_key = os.getenv("BLS_API_KEY")
    base = "https://api.bls.gov/publicAPI/v2/timeseries/data/" if api_key else "https://api.bls.gov/publicAPI/v1/timeseries/data/"

    # Match query to known series
    ql = query.lower()
    matched_series = []
    for label, series_id in BLS_POPULAR_SERIES.items():
        if any(w in ql for w in label.replace("_", " ").split()):
            matched_series.append((label, series_id))

    if not matched_series:
        # Default to unemployment + CPI for general economic queries
        matched_series = [("unemployment", BLS_POPULAR_SERIES["unemployment"]),
                          ("cpi", BLS_POPULAR_SERIES["cpi"])]

    series_ids = [s[1] for s in matched_series[:3]]

    try:
        payload = {
            "seriesid": series_ids,
            "startyear": start_year,
            "endyear": end_year,
        }
        if api_key:
            payload["registrationkey"] = api_key

        resp = requests.post(base, json=payload, timeout=15)
        data = resp.json()

        if data.get("status") != "REQUEST_SUCCEEDED":
            return {"source": "BLS", "query": query, "series": [], "error": data.get("message", ["Unknown error"])}

        series_results = []
        for i, series in enumerate(data.get("Results", {}).get("series", [])):
            label = matched_series[i][0] if i < len(matched_series) else "unknown"
            points = series.get("data", [])[:12]  # Last 12 periods
            series_results.append({
                "label": label,
                "series_id": series.get("seriesID"),
                "latest": points[0] if points else None,
                "points": points,
            })

        return {"source": "BLS", "query": query, "series": series_results, "error": None}

    except Exception as e:
        logger.error("BLS error: %s", e)
        return {"source": "BLS", "query": query, "series": [], "error": str(e)}


# ---------------------------------------------------------------------------
# FRED — Federal Reserve Economic Data
# ---------------------------------------------------------------------------

FRED_POPULAR_SERIES = {
    "gdp": "GDP",
    "inflation": "CPIAUCSL",
    "interest_rate": "FEDFUNDS",
    "housing": "MSPUS",
    "sp500": "SP500",
    "consumer_sentiment": "UMCSENT",
    "venture_capital": "BOGZ1FL893064105Q",
}


def search_fred(query: str, limit: int = 5) -> Dict:
    """Search FRED for economic time series by keyword."""
    api_key = os.getenv("FRED_API_KEY")
    if not api_key:
        return {"source": "FRED", "query": query, "series": [], "error": "FRED_API_KEY not set"}

    try:
        # Search for series
        resp = requests.get(
            "https://api.stlouisfed.org/fred/series/search",
            params={"search_text": query, "api_key": api_key, "file_type": "json", "limit": limit,
                    "order_by": "popularity", "sort_order": "desc"},
            timeout=15,
        )
        data = resp.json()
        series_list = data.get("seriess", [])

        results = []
        for s in series_list[:limit]:
            # Get latest observation
            obs_resp = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={"series_id": s["id"], "api_key": api_key, "file_type": "json",
                        "sort_order": "desc", "limit": 6},
                timeout=10,
            )
            obs = obs_resp.json().get("observations", [])

            results.append({
                "id": s["id"],
                "title": s.get("title", ""),
                "frequency": s.get("frequency", ""),
                "units": s.get("units", ""),
                "latest_value": obs[0]["value"] if obs else None,
                "latest_date": obs[0]["date"] if obs else None,
                "recent_values": [(o["date"], o["value"]) for o in obs[:6]],
            })

        return {"source": "FRED", "query": query, "series": results, "error": None}

    except Exception as e:
        logger.error("FRED error: %s", e)
        return {"source": "FRED", "query": query, "series": [], "error": str(e)}


# ---------------------------------------------------------------------------
# Census ACS — American Community Survey
# ---------------------------------------------------------------------------

def search_census(query: str, year: str = "2022") -> Dict:
    """
    Search Census ACS data. Uses Gemini to pick variable codes, or falls back
    to common variables.
    """
    api_key = os.getenv("DATA_GOV_API_KEY") or os.getenv("CENSUS_API_KEY")

    # Common ACS variables for PWS-relevant topics
    COMMON_VARS = {
        "population": ("B01003_001E", "Total Population"),
        "income": ("B19013_001E", "Median Household Income"),
        "poverty": ("B17001_002E", "Population Below Poverty"),
        "education": ("B15003_022E", "Bachelor's Degree or Higher"),
        "employment": ("B23025_004E", "Employed Population 16+"),
        "housing": ("B25077_001E", "Median Home Value"),
        "business": ("B24011_001E", "Median Earnings"),
    }

    # Match query to variables
    ql = query.lower()
    selected = []
    for label, (var_code, desc) in COMMON_VARS.items():
        if any(w in ql for w in label.split("_")):
            selected.append((var_code, desc))

    if not selected:
        selected = [
            (COMMON_VARS["population"][0], COMMON_VARS["population"][1]),
            (COMMON_VARS["income"][0], COMMON_VARS["income"][1]),
        ]

    var_codes = ",".join([v[0] for v in selected[:4]])

    try:
        url = f"https://api.census.gov/data/{year}/acs/acs1"
        params = {"get": f"NAME,{var_codes}", "for": "state:*"}
        if api_key:
            params["key"] = api_key

        resp = requests.get(url, params=params, timeout=15)
        rows = resp.json()

        if not rows or len(rows) < 2:
            return {"source": "Census ACS", "query": query, "data": [], "error": "No data returned"}

        headers = rows[0]
        # Return top 10 states by first variable
        data_rows = rows[1:11]

        return {
            "source": "Census ACS",
            "query": query,
            "year": year,
            "variables": [v[1] for v in selected[:4]],
            "headers": headers,
            "data": data_rows,
            "error": None,
        }

    except Exception as e:
        logger.error("Census error: %s", e)
        return {"source": "Census ACS", "query": query, "data": [], "error": str(e)}


# ---------------------------------------------------------------------------
# Unified search + formatter
# ---------------------------------------------------------------------------

def search_govdata(query: str, sources: Optional[List[str]] = None) -> Dict:
    """
    Search across government data sources.

    Args:
        query: Search terms.
        sources: List of sources to query. Default: auto-detect from query.
                 Options: 'bls', 'fred', 'census'
    """
    ql = query.lower()

    if sources is None:
        sources = []
        if any(w in ql for w in ["employment", "labor", "wage", "job", "cpi", "inflation",
                                  "productivity", "payroll", "workforce", "hiring"]):
            sources.append("bls")
        if any(w in ql for w in ["gdp", "economic", "interest rate", "housing market",
                                  "consumer", "venture", "recession", "growth", "fed"]):
            sources.append("fred")
        if any(w in ql for w in ["population", "demographic", "income", "poverty",
                                  "education", "census", "housing", "community"]):
            sources.append("census")
        if not sources:
            sources = ["fred", "bls"]  # Default combo

    results = {}
    for src in sources[:2]:  # Max 2 sources per query
        if src == "bls":
            results["bls"] = search_bls(query)
        elif src == "fred":
            results["fred"] = search_fred(query)
        elif src == "census":
            results["census"] = search_census(query)

    return {"query": query, "sources": sources, "results": results}


def format_govdata_markdown(results: Dict) -> str:
    """Format government data results as readable markdown."""
    parts = [f"**US Government Data: {results.get('query', '')}**\n"]

    for source_key, data in results.get("results", {}).items():
        if data.get("error"):
            parts.append(f"**{data['source']}:** Error — {data['error']}\n")
            continue

        if source_key == "bls":
            parts.append(f"### Bureau of Labor Statistics")
            for s in data.get("series", []):
                label = s["label"].replace("_", " ").title()
                latest = s.get("latest")
                if latest:
                    parts.append(f"- **{label}**: {latest.get('value', 'N/A')} ({latest.get('year', '')}-{latest.get('period', '').replace('M', '')})")
                # Show trend from last 4 data points
                pts = s.get("points", [])[:4]
                if len(pts) >= 2:
                    vals = [float(p["value"]) for p in pts if p["value"] != "-"]
                    if vals:
                        direction = "📈 Rising" if vals[0] > vals[-1] else "📉 Declining" if vals[0] < vals[-1] else "➡️ Stable"
                        parts.append(f"  {direction} (last {len(vals)} periods)")
            parts.append("")

        elif source_key == "fred":
            parts.append(f"### Federal Reserve Economic Data")
            for s in data.get("series", []):
                parts.append(f"- **{s['title']}** ({s['units']})")
                if s.get("latest_value"):
                    parts.append(f"  Latest: {s['latest_value']} ({s['latest_date']})")
                recent = s.get("recent_values", [])
                if len(recent) >= 2:
                    try:
                        vals = [float(v[1]) for v in recent if v[1] != "."]
                        if vals:
                            direction = "📈 Rising" if vals[0] > vals[-1] else "📉 Declining" if vals[0] < vals[-1] else "➡️ Stable"
                            parts.append(f"  {direction} trend")
                    except ValueError:
                        pass
            parts.append("")

        elif source_key == "census":
            parts.append(f"### Census ACS ({data.get('year', '')})")
            variables = data.get("variables", [])
            parts.append(f"Variables: {', '.join(variables)}")
            headers = data.get("headers", [])
            rows = data.get("data", [])
            if rows and headers:
                parts.append("")
                for row in rows[:8]:
                    state_name = row[0]
                    values = row[1:-1]  # Exclude state FIPS
                    formatted_vals = []
                    for i, v in enumerate(values):
                        try:
                            num = int(v)
                            formatted_vals.append(f"{num:,}")
                        except (ValueError, TypeError):
                            formatted_vals.append(str(v))
                    parts.append(f"- **{state_name}**: {', '.join(formatted_vals)}")
            parts.append("")

    if len(parts) <= 1:
        parts.append("No government data found for this query.")

    return "\n".join(parts)
