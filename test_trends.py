#!/usr/bin/env python3
"""Standalone test for Google Trends data fetching."""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import sys
from pytrends.request import TrendReq
from pytrends.exceptions import ResponseError


def fetch_trends(product_name: str):
    print(f"\nFetching Google Trends data for: {product_name}")
    print("-" * 50)

    try:
        pytrends = TrendReq(hl="en-US", tz=360, retries=3, backoff_factor=0.5)
    except TypeError:
        pytrends = TrendReq(hl="en-US", tz=360)

    pytrends.build_payload(
        [product_name], cat=0, timeframe="today 5-y", geo="", gprop=""
    )

    df = pytrends.interest_over_time()
    if df.empty:
        print("ERROR: No trend data returned from Google Trends")
        sys.exit(1)

    if "isPartial" in df.columns:
        df = df.drop(columns=["isPartial"])

    series = df[product_name]
    total_points = len(series)

    print(f"Total data points: {total_points}")
    print()

    seven = float(series.tail(min(7, total_points)).mean())
    thirty = float(series.tail(min(30, total_points)).mean())
    ninety = float(series.tail(min(90, total_points)).mean())
    one_eighty = float(series.tail(min(180, total_points)).mean())

    print(f"  7d avg:       {seven:.2f}")
    print(f"  30d avg:      {thirty:.2f}")
    print(f"  90d avg:      {ninety:.2f}")
    print(f"  180d avg:     {one_eighty:.2f}")

    if total_points >= 60:
        recent = float(series.tail(30).mean())
        older = float(series.tail(60).head(30).mean())
        momentum = (recent - older) / (older + 1)
    else:
        momentum = 0.0

    if momentum > 0.1:
        direction = "rising"
    elif momentum < -0.1:
        direction = "declining"
    else:
        direction = "stable"

    print(f"  Direction:    {direction} (momentum={momentum:.4f})")

    denom = max(ninety, thirty)
    stability = min(ninety, thirty) / denom if denom > 0 else 0.0
    print(f"  Stability:    {stability:.4f}")

    if total_points >= 60:
        recent = float(series.tail(30).mean())
        older = float(series.tail(60).head(30).mean())
        momentum = (recent - older) / (older + 1)
    else:
        momentum = 0.0
    print(f"  Momentum:     {momentum:.4f}")

    print()
    print("✓ Real Google Trends data retrieved successfully!")
    print()

    return {
        "seven_day_avg": round(seven, 2),
        "thirty_day_avg": round(thirty, 2),
        "ninety_day_avg": round(ninety, 2),
        "one_eighty_day_avg": round(one_eighty, 2),
        "direction": direction,
        "stability": round(stability, 4),
        "momentum": round(momentum, 4),
    }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "Dog Hair Remover"

    result = fetch_trends(query)
    print("Returned data:")
    for k, v in result.items():
        print(f"  {k}: {v}")
