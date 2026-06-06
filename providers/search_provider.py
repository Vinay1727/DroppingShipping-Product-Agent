from typing import Optional

from product_agent.models import ProviderResult
from .base_provider import BaseProvider


class SearchProvider(BaseProvider):
    priority = 1
    display_name = "Google Search"

    def _do_fetch(self, product_name: str) -> ProviderResult:
        result = self._fetch_via_duckduckgo(product_name)
        if result.success:
            return result

        return self._fetch_via_google(product_name)

    def _fetch_via_duckduckgo(self, product_name: str) -> ProviderResult:
        try:
            from ddgs import DDGS

            with DDGS() as ddgs:
                results = list(ddgs.text(product_name, max_results=20))

            urls = []
            for r in results:
                url = r.get("href", "") or r.get("link", "")
                if url:
                    urls.append(url)

            return ProviderResult(
                source="SearchProvider",
                success=True,
                data={
                    "result_count": len(results),
                    "top_urls": urls[:10],
                    "related_queries": [],
                    "has_amazon_listings": any("amazon" in u for u in urls),
                },
            )

        except Exception as e:
            return ProviderResult(
                source="SearchProvider",
                success=False,
                error=f"DuckDuckGo error: {e}",
            )

    def _fetch_via_google(self, product_name: str) -> ProviderResult:
        try:
            from googlesearch import search

            urls = list(search(product_name, num_results=15))
            result_count = len(urls)

            return ProviderResult(
                source="SearchProvider",
                success=True,
                data={
                    "result_count": result_count,
                    "top_urls": urls[:10],
                    "related_queries": [],
                    "has_amazon_listings": any("amazon" in u for u in urls),
                },
            )

        except Exception as e:
            return ProviderResult(
                source="SearchProvider",
                success=False,
                error=f"Google search error: {e}",
            )
