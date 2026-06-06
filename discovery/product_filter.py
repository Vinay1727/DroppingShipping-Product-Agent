import re
import logging

logger = logging.getLogger(__name__)

PRODUCT_KEYWORDS = {
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
    "conditioner", "soap", "wash", "scrub", "toner",
    "moisturizer", "sunscreen", "balm", "gloss",
    "foundation", "concealer", "powder", "blush", "eyeshadow",
    "liner", "mascara",
    "pan", "pot", "skillet", "cookware", "bakeware",
    "sneaker", "backpack",
    "power bank", "candle", "diffuser",
    "saw", "drill", "screwdriver", "hammer", "wrench",
    "pliers", "level", "tape", "glue", "sander", "router",
    "clamp", "vise", "anvil", "sharpener", "whetstone",
    "strop", "hone", "fork", "spoon", "spatula",
    "tongs", "ladle", "whisk", "zester",
    "mandolin", "corer", "pitter", "cracker",
    "grinder", "mill", "strainer", "colander",
    "sieve", "funnel", "measuring cup", "scale",
    "blender", "toaster", "mixer", "oven", "cooker",
    "steamer", "kettle", "coffee maker", "juicer",
    "dehydrator", "roaster", "griddle", "waffle",
    "brush", "comb", "clipper", "trimmer", "shaver",
    "curler", "straightener", "dryer", "styler",
    "clip", "bobby pin", "hair tie", "headband",
    "yoga mat", "dumbbell", "kettlebell", "barbell",
    "resistance band", "jump rope", "foam roller",
    "glove", "wrap", "pad", "bench", "rack",
    "scale", "pedometer", "tracker", "smartwatch",
    "charger", "cable", "adapter", "hub", "dock",
    "mouse pad", "wrist rest", "laptop stand",
    "phone case", "screen protector", "tempered glass",
    "pop socket", "ring light", "tripod", "gimbal",
    "water bottle", "lunch box", "food container",
    "ice pack", "lunch bag", "straw", "cup",
    "cat toy", "dog toy", "pet bed", "cat tree",
    "leash", "collar", "harness", "pet carrier",
    "litter box", "scratching post", "pet bowl",
    "plant pot", "planter", "vase", "candle holder",
    "picture frame", "mirror", "clock", "rug",
    "curtain", "blind", "throw pillow", "blanket",
    "desk lamp", "floor lamp", "string light",
    "notebook", "pen", "marker", "planner", "sticker",
    "earplug", "sleep mask", "white noise machine",
}

COMPANY_NAMES = {
    "apple", "google", "microsoft", "amazon", "meta", "netflix",
    "tesla", "nvidia", "samsung", "sony", "lg", "panasonic",
    "philips", "dyson", "ninja", "instant pot", "kitchenaid",
    "cuisinart", "breville", "de'longhi", "nespresso", "keurig",
    "bose", "jbl", "sennheiser", "beats", "anker", "belkin",
    "nike", "adidas", "puma", "reebok", "under armour", "lululemon",
    "levi's", "gap", "h&m", "zara", "uniqlo", "ralph lauren",
    "tommy hilfiger", "calvin klein", "coach", "michael kors",
    "gucci", "prada", "louis vuitton", "chanel", "dior", "hermes",
    "fenty", "rare beauty", "kylie", "kylie cosmetics",
    "sephora", "ulta", "nyx", "maybelline", "l'oreal", "covergirl",
    "revlon", "estee lauder", "clinique", "neutrogena", "cetaphil",
    "cerave", "la roche-posay", "the ordinary", "glossier",
    "trader joe's", "whole foods", "walmart", "target", "costco",
    "home depot", "lowes", "ikea", "bed bath & beyond",
    "tj maxx", "marshalls", "ross", "burlington",
    "dollar tree", "dollar general", "family dollar",
    "petco", "petsmart", "pet smart", "pet valu", "pet supplies plus",
    "chewy", "amazon basics", "great value", "equate",
    "starbucks", "dunkin", "mcdonald's", "wendy's", "burger king",
    "kfc", "taco bell", "pizza hut", "domino's", "subway",
    "coca-cola", "pepsi", "nestle", "unilever", "procter & gamble",
    "colgate", "oral-b", "gillette", "schick", "bic",
    "scotch", "3m", "duracell", "energizer", "rayovac",
    "huggies", "pampers", "johnson & johnson",
    "pfizer", "moderna", "sonos", "ring", "nest", "ecobee",
    "roomba", "irobot", "shark", "black+decker", "dewalt",
    "milwaukee", "makita", "bosch", "ryobi", "craftsman",
    "stanley", "snap-on", "matco", "mac tools",
    "harbor freight", "nordstrom", "macy's", "kohl's",
    "j crew", "banana republic", "american eagle", "abercrombie",
    "hollister", "old navy", "forever 21", "shein", "zaful",
    "bon prix", "wish", "aliexpress", "temu", "etsy",
    "shopify", "bigcommerce", "woocommerce",
    "disney", "warner bros", "paramount", "nbc", "cbs", "abc",
    "fox", "cnn", "bbc", "ny times", "washington post",
    "patagonia", "north face", "columbia", "merrell", "keen",
    "timberland", "ugg", "crocs", "vans", "converse",
    "new balance", "asics", "brooks", "hoka", "on running",
    "herman miller", "steelcase", "honeywell",
    "clorox", "lysol", "tide", "gain", "downy", "bounce",
    "at home",
    "bank of america", "7-eleven", "krispy kreme",
}

CELEBRITY_FIRST_NAMES = {
    "taylor swift", "beyonce", "kanye", "kardashian", "kim kardashian",
    "kylie jenner", "kendall jenner", "khloe kardashian", "kourtney kardashian",
    "hailey bieber", "justin bieber", "selena gomez", "ariana grande",
    "billie eilish", "olivia rodrigo", "drake", "the weeknd", "bad bunny",
    "harry styles", "dua lipa", "ed sheeran", "adele", "lady gaga",
    "madonna", "rihanna", "jennifer lopez", "shakira",
    "lebr james", "messi", "ronaldo", "tom brady", "patrick mahomes",
    "serena williams", "mike tyson", "conor mcgregor",
    "elon musk", "jeff bezos", "mark zuckerberg", "bill gates",
    "warren buffett", "tim cook", "sam altman",
    "mrbeast", "pewdiepie", "logan paul", "ksi",
    "oprah", "ellen", "dr. phil", "joe rogan",
    "tom cruise", "leonardo dicaprio", "brad pitt", "angelina jolie",
    "johnny depp", "amber heard", "will smith", "jada pinkett",
    "robert downey", "scarlett johansson", "chris hemsworth",
    "chris evans", "keanu reeves", "dwayne johnson", "the rock",
}

SETTLEMENT_KEYWORDS = {
    "settlement", "lawsuit", "data breach", "class action", "recall",
    "payout", "compensation", "refund", "fine", "penalty",
    "investigation", "allegation", "verdict", "ruling", "court",
    "litigation", "arbitration", "mediation",
}

NEWS_KEYWORDS = {
    "news", "update", "report", "announcement", "statement",
    "confirms", "denies", "claims", "alleges", "accuses",
    "scandal", "controversy", "backlash", "outrage",
    "crisis", "shortage", "supply chain", "inflation",
    "recession", "economy", "market", "stock", "share",
    "merger", "acquisition", "ipo", "earnings", "revenue",
    "layoff", "hiring", "hike", "bonus",
    "election", "campaign", "politician", "senator", "congress",
    "president", "governor", "mayor", "bill", "law", "regulation",
    "covid", "pandemic", "virus", "vaccine", "outbreak",
}

GENERIC_BUSINESS = {
    "strategy", "growth", "opportunity", "insights",
    "analysis", "overview",
    "how to", "what is", "why is", "ways to",
    "business", "startup", "entrepreneur", "side hustle",
    "passive income", "work from home", "remote",
    "marketing", "seo", "social media", "content",
    "digital", "online", "ecommerce", "dropshipping",
    "subscription", "platform", "software",
    "course", "coaching", "consulting", "membership",
    "b2b", "b2c", "saas", "wholesale", "retail",
    "franchise", "licensing", "patent", "trademark",
    "crm", "erp", "api", "cloud", "blockchain", "nft",
    "cryptocurrency", "bitcoin", "ethereum", "mining",
    "ai", "artificial intelligence", "machine learning",
    "chatbot", "chatgpt", "gpt", "llm", "automation",
}

LOCATIONS = {
    "usa", "united states", "america", "canada", "uk",
    "london", "new york", "los angeles", "chicago", "san francisco",
    "miami", "dallas", "houston", "seattle", "boston",
    "europe", "asia", "china", "japan", "india", "germany",
    "france", "italy", "spain", "australia", "brazil",
    "california", "texas", "florida", "nevada", "arizona",
    "paris", "tokyo", "sydney", "dubai", "singapore",
    "vegas", "las vegas", "orlando", "disney world",
}

SPORTS_TEAMS = {
    "nfl", "nba", "mlb", "nhl", "mls", "ncaa", "super bowl",
    "world cup", "olympics", "championship", "playoff",
    "lakers", "warriors", "celtics", "knicks", "bulls",
    "cowboys", "patriots", "chiefs", "49ers", "packers",
    "yankees", "red sox", "dodgers", "cubs", "astros",
}

POLITICAL = {
    "democrat", "republican", "biden", "trump", "obama",
    "congress", "senate", "house of representatives",
    "supreme court", "white house", "government",
    "abortion", "gun control", "immigration", "tax",
    "climate change", "global warming", "education",
    "healthcare", "medicare", "social security",
    "defense", "military", "veteran", "police",
}

CATEGORY_MAP = [
    (r"\b(pet|dog|cat|fish|bird|horse|animal|puppy|kitten)\b", "pet"),
    (r"\b(beauty|makeup|cosmetic|skincare|haircare|hair|fragrance|lip|eye|lash|nail|face|body lotion|shampoo|conditioner)\b", "beauty"),
    (r"\b(kitchen|cookware|bakeware|cooking|baking|knife|pan|pot|utensil|cook|chef|food)\b", "kitchen"),
    (r"\b(fitness|exercise|workout|gym|yoga|pilates|dumbbell|kettlebell|barbell|weight|cardio|running|jogging|sport)\b", "fitness"),
    (r"\b(electronics|electronic|gadget|device|tech|smart|bluetooth|wireless|charger|cable|adapter|speaker|headphone|earphone|monitor|keyboard|mouse)\b", "electronics"),
    (r"\b(home|house|garden|yard|lawn|furniture|decor|furnishing|lighting|bedding|bath|kitchen|storage|organization)\b", "home"),
    (r"\b(phone|tablet|laptop|computer|tv|television|console|gaming|camera|lens|drone)\b", "electronics"),
    (r"\b(baby|infant|toddler|kids|children|toy|game|stroller|car seat|crib|diaper)\b", "baby"),
    (r"\b(office|desk|chair|stationery|pen|paper|notebook|planner|organizer)\b", "office"),
    (r"\b(outdoor|camping|hiking|fishing|hunting|garden|patio|deck|bbq|grill)\b", "outdoor"),
    (r"\b(car|auto|automotive|vehicle|truck|van|garage|tool)\b", "automotive"),
    (r"\b(food|snack|drink|beverage|coffee|tea|protein|supplement|vitamin)\b", "food"),
    (r"\b(fashion|clothing|apparel|shirt|pant|dress|shoe|boot|sneaker|jacket|coat|sock|hat|cap|accessory|jewelry|watch|bag|wallet)\b", "fashion"),
    (r"\b(clean|cleaning|laundry|mop|broom|vacuum|basket|soap|detergent|disinfect)\b", "cleaning"),
    (r"\b(health|wellness|medical|first aid|bandage|mask|sanitizer|thermometer|pill|tablet|supplement|vitamin|mineral|protein)\b", "health"),
]

ACCEPT_CATEGORIES = {
    "pet", "beauty", "kitchen", "fitness", "electronics",
    "home", "baby", "office", "outdoor", "automotive",
    "food", "fashion", "cleaning", "health",
}

def _has_product_keyword(text: str) -> bool:
    words = set(text.split())
    for kw in PRODUCT_KEYWORDS:
        kw_words = kw.split()
        if len(kw_words) == 1:
            if re.search(r'\b' + re.escape(kw_words[0]) + r'\b', text):
                return True
        else:
            if kw in text:
                return True
    return False


def _detect_category(text: str) -> str:
    for pattern, category in CATEGORY_MAP:
        if re.search(pattern, text):
            return category
    return "general"


def _matches_any(text: str, keywords: set) -> bool:
    for kw in keywords:
        if kw in text:
            return True
    return False


def qualify_candidate(candidate_text: str) -> dict:
    text = candidate_text.strip().lower()
    text_clean = re.sub(r"[^\w\s'-]", " ", text)
    text_clean = re.sub(r"\s+", " ", text_clean).strip()

    if _matches_any(text_clean, SETTLEMENT_KEYWORDS):
        return {"candidate": candidate_text, "is_product": False, "reason": "news_topic"}

    strong_product = _has_product_keyword(text_clean)

    if strong_product:
        category = _detect_category(text_clean)
        return {"candidate": candidate_text, "is_product": True, "category": category}
    if _matches_any(text_clean, COMPANY_NAMES):
        if _matches_any(text_clean, NEWS_KEYWORDS):
            return {"candidate": candidate_text, "is_product": False, "reason": "news_topic"}
        return {"candidate": candidate_text, "is_product": False, "reason": "company"}
    if _matches_any(text_clean, CELEBRITY_FIRST_NAMES):
        return {"candidate": candidate_text, "is_product": False, "reason": "celebrity"}
    if _matches_any(text_clean, SPORTS_TEAMS):
        return {"candidate": candidate_text, "is_product": False, "reason": "sports_topic"}
    if _matches_any(text_clean, POLITICAL):
        return {"candidate": candidate_text, "is_product": False, "reason": "political_topic"}
    if _matches_any(text_clean, LOCATIONS):
        return {"candidate": candidate_text, "is_product": False, "reason": "location"}

    category = _detect_category(text_clean)
    if category in ACCEPT_CATEGORIES:
        return {"candidate": candidate_text, "is_product": True, "category": category}

    if _matches_any(text_clean, GENERIC_BUSINESS):
        return {"candidate": candidate_text, "is_product": False, "reason": "generic_concept"}
    if _matches_any(text_clean, NEWS_KEYWORDS):
        return {"candidate": candidate_text, "is_product": False, "reason": "news_topic"}

    return {"candidate": candidate_text, "is_product": False, "reason": "unrecognized"}


def filter_candidates(candidates: list) -> tuple:
    qualified = []
    rejected = []

    for c in candidates:
        result = qualify_candidate(c["product"])
        if result["is_product"]:
            c["category"] = result["category"]
            qualified.append(c)
        else:
            c["reject_reason"] = result["reason"]
            rejected.append(c)

    qualified_pct = len(qualified) / max(len(candidates), 1) * 100
    logger.info(f"Qualified: {len(qualified)}/{len(candidates)} ({qualified_pct:.0f}%)")
    if rejected:
        logger.info(f"Rejected ({len(rejected)}):")
        for r in rejected[:10]:
            logger.info(f"  ✗ {r['product']:40s} → {r['reject_reason']}")
        if len(rejected) > 10:
            logger.info(f"  ... and {len(rejected) - 10} more")

    return qualified, rejected
