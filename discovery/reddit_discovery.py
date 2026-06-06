import logging
import re
from typing import List

logger = logging.getLogger(__name__)

DISCOVERY_SUBREDDITS = [
    "AmazonFind", "deals", "shutupandtakemymoney", "gadgets",
    "BuyItForLife", "EDC", "CampingGear", "Coffee",
    "SkincareAddiction", "HaircareScience",
    "HomeImprovement", "gardening", "Cooking", "Tools",
    "DIY", "headphones", "MechanicalKeyboards", "photography",
    "frugalmalefashion", "malefashionadvice", "Watches",
    "Sneakers", "Ultralight", "GoodValue",
    "homeautomation", "slowcooking",
    "techsupport",
]

DISCOVERY_QUERIES = [
    "best", "recommend", "deal", "worth", "amazing",
    "love", "favorite", "must have", "game changer",
    "hidden gem", "underrated", "life changing",
]

PRODUCT_KEYWORDS = [
    "remover", "cleaner", "vacuum", "mop", "broom", "brush",
    "tool", "kit", "set", "bag", "case", "cover", "holder",
    "stand", "mount", "light", "lamp", "lantern", "flashlight",
    "speaker", "headphone", "earphone", "earbud", "charger",
    "cable", "adapter", "sensor", "camera", "lens", "filter",
    "pad", "mat", "towel", "blanket", "pillow", "cushion",
    "organizer", "rack", "shelf", "container", "bottle", "cup",
    "mug", "glass", "flask", "thermos", "cooler", "grill",
    "heater", "fan", "purifier", "humidifier", "knife",
    "board", "peeler", "grater", "slicer", "chopper", "press",
    "maker", "machine", "device", "gadget", "appliance",
    "monitor", "screen", "tablet", "keyboard", "mouse",
    "watch", "band", "strap", "wallet", "card", "keychain",
    "multitool", "shirt", "hoodie", "jacket", "pant", "short",
    "shoe", "boot", "sandal", "slipper", "sock", "hat", "cap",
    "belt", "bracelet", "necklace", "ring", "earring",
    "glove", "scarf", "mask", "goggle", "helmet",
    "cream", "lotion", "serum", "oil", "spray", "shampoo",
    "conditioner", "soap", "wash", "mask", "scrub", "toner",
    "moisturizer", "sunscreen", "balm", "gloss",
    "foundation", "concealer", "powder", "blush", "eyeshadow",
    "liner", "mascara",
    "pan", "pot", "skillet", "cookware", "bakeware",
    "sneaker", "headphone", "notebook", "backpack",
    "charger", "power bank", "candle", "diffuser",
    "saw", "drill", "screwdriver", "hammer", "wrench",
    "pliers", "level", "tape", "glue", "sander", "router",
    "clamp", "vise", "anvil", "sharpener", "whetstone",
    "strop", "hone", "knife", "fork", "spoon", "spatula",
    "tongs", "ladle", "whisk", "peeler", "zester", "grater",
    "mandolin", "slicer", "corer", "pitter", "cracker",
    "press", "grinder", "mill", "strainer", "colander",
    "sieve", "funnel", "measuring cup", "scale",
]

SKIP_PATTERNS = [
    r"^(looking for|recommend me|what.*(should|is|are)|how.*(to|do|can)|where.*(to|can)|does anyone|has anyone|anyone.*(use|try|have|know)|can.*(recommend|suggest))",
    r"^(buyer beware|review of|my experience|first time|is this|should i|do you|are there|who else)",
    r"(daily|weekly|monthly).*(thread|question|discussion|chat)",
    r"(psa:|tip:|guide:|tutorial:|question:|help:)",
    r"versus|vs\.?$",
]


def discover_from_reddit(max_candidates=100) -> List[dict]:
    products = {}
    seen_products = set()

    try:
        from product_agent.config import settings
        client_id = settings.REDDIT_CLIENT_ID
        client_secret = settings.REDDIT_CLIENT_SECRET
    except Exception:
        client_id = None
        client_secret = None

    if not client_id or not client_secret:
        logger.warning("No Reddit API credentials configured for discovery")
        return []

    try:
        import praw
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="ProductAgentDiscovery/1.0 (by /u/product_agent)",
        )
    except Exception as e:
        logger.warning(f"Failed to initialize PRAW: {e}")
        return []

    subreddits = DISCOVERY_SUBREDDITS[:15]
    queries = DISCOVERY_QUERIES[:5]

    for sub_name in subreddits:
        try:
            subreddit = reddit.subreddit(sub_name)
            for query in queries:
                try:
                    for submission in subreddit.search(
                        query, sort="top", time_filter="month", limit=10
                    ):
                        title = submission.title
                        product = _extract_product(title, sub_name)
                        if not product:
                            continue
                        if product in seen_products:
                            products[product]["mentions"] += 1
                            continue
                        seen_products.add(product)
                        products[product] = {
                            "product": product,
                            "source": "reddit",
                            "mentions": 1,
                            "subreddit": sub_name,
                        }
                except Exception:
                    continue
        except Exception:
            continue

    result = sorted(products.values(), key=lambda x: x["mentions"], reverse=True)
    return result[:max_candidates]


def _extract_product(title: str, subreddit: str) -> str | None:
    clean = title.lower().strip()
    clean = re.sub(r"[^\w\s'-]", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    for pattern in SKIP_PATTERNS:
        if re.search(pattern, clean):
            return None

    noise = {
        "buyer", "beware", "swear", "dump", "after", "review", "reviewed",
        "question", "anyone", "someone", "everyone", "update",
        "recommendation", "advice", "opinion", "thoughts",
        "looking", "recommend", "suggest", "need", "want",
        "worth", "best", "deal", "amazing", "love", "favorite",
        "must", "hidden", "gem", "underrated", "life", "changing",
        "finally", "just", "bought", "got", "new", "first",
        "last", "next", "another", "other", "various",
        "actually", "really", "still", "always", "never",
        "much", "many", "some", "any", "every", "all",
        "please", "help", "thanks", "thank", "here", "there",
        "year", "years", "month", "week", "day", "time",
        "thing", "items", "stuff", "things",
    }

    words = clean.split()
    filtered = [w for w in words if w not in noise and len(w) > 2]

    product_idx = -1
    for i, w in enumerate(filtered):
        if w in PRODUCT_KEYWORDS or any(
            kw.startswith(w) for kw in PRODUCT_KEYWORDS
        ):
            product_idx = i
            break

    if product_idx >= 0:
        start = max(0, product_idx - 3)
        end = min(len(filtered), product_idx + 2)
        phrase = " ".join(filtered[start:end])
        if len(phrase) >= 5:
            return phrase.title()

    return None
