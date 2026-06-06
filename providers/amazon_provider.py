from typing import Optional

from product_agent.config import settings
from product_agent.models import ProviderResult
from .base_provider import BaseProvider


class AmazonProvider(BaseProvider):
    priority = 2
    display_name = "Amazon"

    def _do_fetch(self, product_name: str) -> ProviderResult:
        serp_key = settings.SERPAPI_API_KEY
        amazon_key = settings.AMAZON_API_KEY

        if serp_key:
            return self._fetch_via_serpapi(product_name, serp_key)
        if amazon_key:
            return self._fetch_via_paapi(product_name, amazon_key)

        return ProviderResult(
            source="AmazonProvider",
            success=False,
            data={"available": False, "reason": "amazon provider unavailable"},
            error="Amazon provider unavailable: no SerpAPI or PAAPI keys configured",
        )

    def _fetch_via_serpapi(self, product_name: str, api_key: str) -> ProviderResult:
        try:
            params = {
                "api_key": api_key,
                "engine": "amazon",
                "amazon_domain": "amazon.com",
                "q": product_name,
            }
            resp = self._safe_request(
                "https://serpapi.com/search",
                params=params,
            )
            data = resp.json()

            organic = data.get("organic_results", [])
            product_count = len(organic)

            prices = []
            ratings = []
            review_counts = []

            for result in organic:
                price_str = result.get("price", "").replace("$", "").replace(",", "")
                try:
                    prices.append(float(price_str))
                except (ValueError, TypeError):
                    pass

                rating = result.get("rating")
                if rating is not None:
                    try:
                        ratings.append(float(rating))
                    except (ValueError, TypeError):
                        pass

                reviews = result.get("reviews")
                if reviews is not None:
                    try:
                        review_counts.append(int(reviews))
                    except (ValueError, TypeError):
                        pass

            avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0
            avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
            total_reviews = sum(review_counts)
            price_min = min(prices) if prices else 0.0
            price_max = max(prices) if prices else 0.0

            return ProviderResult(
                source="AmazonProvider",
                success=True,
                data={
                    "available": True,
                    "product_count": product_count,
                    "avg_price": avg_price,
                    "price_min": price_min,
                    "price_max": price_max,
                    "avg_rating": avg_rating,
                    "total_reviews": total_reviews,
                    "top_category": "",
                },
            )

        except Exception as e:
            return ProviderResult(
                source="AmazonProvider",
                success=False,
                error=f"SerpAPI error: {e}",
            )

    def _fetch_via_paapi(self, product_name: str, api_key: str) -> ProviderResult:
        try:
            import requests

            resp = requests.post(
                "https://webservices.amazon.com/paapi5/searchitems",
                json={
                    "Keywords": product_name,
                    "Resources": [
                        "ItemInfo.Title",
                        "Offers.Listings.Price",
                        "ItemInfo.Features",
                    ],
                    "PartnerTag": settings.AMAZON_ASSOCIATE_TAG,
                    "PartnerType": "Associates",
                    "Marketplace": "www.amazon.com",
                },
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": api_key,
                },
                timeout=15,
            )
            data = resp.json()

            items = data.get("ItemsResult", {}).get("Items", [])
            prices = []
            for item in items:
                listing = item.get("Offers", {}).get("Listings", [])
                for l in listing:
                    price = l.get("Price", {}).get("Amount")
                    if price:
                        prices.append(float(price))

            avg_price = round(sum(prices) / len(prices), 2) if prices else 0.0
            price_min = min(prices) if prices else 0.0
            price_max = max(prices) if prices else 0.0

            return ProviderResult(
                source="AmazonProvider",
                success=True,
                data={
                    "available": True,
                    "product_count": len(items),
                    "avg_price": avg_price,
                    "price_min": price_min,
                    "price_max": price_max,
                    "avg_rating": 0.0,
                    "total_reviews": 0,
                    "top_category": "",
                },
            )

        except Exception as e:
            return ProviderResult(
                source="AmazonProvider",
                success=False,
                error=f"PAAPI error: {e}",
            )
