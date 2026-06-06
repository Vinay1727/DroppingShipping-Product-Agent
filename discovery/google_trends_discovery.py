import time
import logging

logger = logging.getLogger(__name__)

SEED_CATEGORIES = [
    "pet supplies", "home goods", "beauty products", "kitchen gadgets",
    "fitness equipment", "electronics accessories", "fashion accessories",
    "garden tools", "travel accessories", "phone accessories",
    "baby products", "sports equipment", "tools", "office supplies",
    "car accessories", "outdoor gear", "camping gear", "cooking tools",
    "cleaning products", "storage solutions", "organization",
    "party supplies", "craft supplies", "art supplies", "pet toys",
    "home decor", "lighting", "bedding", "bathroom accessories",
    "kitchen tools", "cookware", "bakeware", "food storage",
    "water bottles", "lunch boxes", "backpacks", "bags", "wallets",
    "jewelry", "watches", "sunglasses", "hats", "scarves",
    "yoga mats", "dumbbells", "resistance bands", "jump rope",
    "skincare", "haircare", "makeup", "nail care", "fragrance",
]

SEED_CATEGORIES_SHORT = [
    "pet supplies", "home goods", "beauty products", "kitchen gadgets",
    "fitness equipment", "electronics",
]


def discover_from_trends(max_candidates=100):
    products = []
    seen = set()

    try:
        from pytrends.request import TrendReq
        pytrends = TrendReq(hl="en-US", tz=360, retries=2, backoff_factor=0.5)
    except Exception as e:
        logger.error(f"Failed to initialize pytrends: {e}")
        return products

    categories = SEED_CATEGORIES_SHORT

    for seed in categories:
        time.sleep(3)
        try:
            pytrends.build_payload(
                [seed], cat=0, timeframe="today 3-m", geo="US", gprop=""
            )
            related = pytrends.related_queries()
            if not related or seed not in related:
                continue

            rising = related[seed].get("rising")
            if rising is not None and not rising.empty:
                for _, row in rising.iterrows():
                    query = row.get("query", "").strip().lower()
                    if not query or len(query) < 5:
                        continue
                    if query in seen:
                        continue
                    if seed in query:
                        continue

                    seen.add(query)
                    products.append({
                        "product": query,
                        "source": "google_trends",
                        "growth": int(row.get("value", 0)),
                        "seed_category": seed,
                    })

            top = related[seed].get("top")
            if top is not None and not top.empty and len(products) < max_candidates:
                for _, row in top.iterrows():
                    query = row.get("query", "").strip().lower()
                    if not query or len(query) < 5:
                        continue
                    if query in seen:
                        continue
                    if seed in query:
                        continue

                    seen.add(query)
                    products.append({
                        "product": query,
                        "source": "google_trends",
                        "growth": int(row.get("value", 0)),
                        "seed_category": seed,
                    })

        except Exception as e:
            logger.warning(f"Error processing seed '{seed}': {e}")
            time.sleep(3)
            continue

    products.sort(key=lambda x: x["growth"], reverse=True)
    return products[:max_candidates]
