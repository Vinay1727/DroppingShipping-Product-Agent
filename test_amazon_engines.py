#!/usr/bin/env python3
"""
Test script: search product on Amazon, return raw data,
then run Demand / Competition / Review engines with real data.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from product_agent.config import settings
from product_agent.models import ProductInput, ProviderResult
from product_agent.providers.amazon_provider import AmazonProvider
from product_agent.engines.demand_engine import DemandEngine
from product_agent.engines.competition_engine import CompetitionEngine
from product_agent.engines.review_engine import ReviewEngine


def main():
    if len(sys.argv) > 1:
        product_name = " ".join(sys.argv[1:])
    else:
        product_name = "Dog Hair Remover"

    print(f"\n{'='*60}")
    print(f"  Searching Amazon for: {product_name}")
    print(f"{'='*60}\n")

    # -- Step 1: Fetch Amazon data --
    AmazonProvider._caches = {}
    provider = AmazonProvider()
    result = provider.fetch(product_name)

    if result.success:
        d = result.data
        print(f"  Product count:   {d['product_count']}")
        print(f"  Avg rating:      {d['avg_rating']}")
        print(f"  Total reviews:   {d['total_reviews']}")
        print(f"  Price range:     ${d['price_min']:.2f} - ${d['price_max']:.2f}")
        print(f"  Avg price:       ${d['avg_price']:.2f}")
    else:
        print(f"  Amazon data: UNAVAILABLE")
        print(f"  Reason: {result.error}")

    print()

    # -- Step 2: Build provider_data dict --
    product = ProductInput(
        product_name=product_name,
        supplier_price=10,
        selling_price=30,
    )
    provider_data = {"amazon": result}

    # -- Step 3: Run Demand Engine --
    demand = DemandEngine()
    demand_result = demand.analyze(product, provider_data=provider_data)
    print(f"  Demand Engine: {demand_result.score:.1f}/{demand_result.max_score:.0f}")
    for k, v in demand_result.details.items():
        if k in ("amazon", "google_trends", "reddit", "heuristic", "confirmed_sources", "total_sources"):
            print(f"    {k}: {v}")

    print()

    # -- Step 4: Run Competition Engine --
    competition = CompetitionEngine()
    comp_result = competition.analyze(product, provider_data=provider_data)
    print(f"  Competition Engine: {comp_result.score:.1f}/{comp_result.max_score:.0f}")
    print(f"    Level: {comp_result.details.get('competition_level')}")
    print(f"    Data source: {comp_result.details.get('data_source')}")
    if result.success:
        print(f"    Product count: {comp_result.details.get('estimated_competitor_count')}")

    print()

    # -- Step 5: Run Review Engine --
    review = ReviewEngine()
    rev_result = review.analyze(product, provider_data=provider_data)
    print(f"  Review Engine: {rev_result.score:.1f}/{rev_result.max_score:.0f}")
    print(f"    Quality: {rev_result.details.get('review_quality')}")
    print(f"    Data source: {rev_result.details.get('data_source')}")
    if result.success:
        print(f"    Avg rating: {rev_result.details.get('avg_rating')}")
        print(f"    Total reviews: {rev_result.details.get('total_reviews')}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
