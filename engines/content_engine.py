from product_agent.config import settings
from product_agent.models import EngineResult, ProductInput


class ContentEngine:
    CATEGORIES = [
        "problem_solving",
        "transformation",
        "comparison",
        "tutorial",
        "reaction",
        "challenge",
        "mistakes",
        "before_after",
    ]

    def analyze(self, product: ProductInput) -> EngineResult:
        try:
            tagged_ideas = self._generate_tagged_ideas(product.product_name)

            unique_ideas, duplicate_count = self._deduplicate(tagged_ideas)
            unique_count = len(unique_ideas)

            category_breakdown = self._count_by_category(unique_ideas)
            diversity_score = self._calculate_diversity(category_breakdown)
            score = self._score(unique_count)

            return EngineResult(
                score=round(score, 2),
                max_score=5.0,
                confidence=round(min(0.9, 0.4 + unique_count / 80.0), 2),
                details={
                    "unique_ideas": unique_count,
                    "duplicate_ideas": duplicate_count,
                    "diversity_score": round(diversity_score, 2),
                    "categories_covered": sum(1 for v in category_breakdown.values() if v > 0),
                    "total_categories": len(self.CATEGORIES),
                    "category_breakdown": category_breakdown,
                    "sample_ideas": [text for text, _ in list(unique_ideas)[:10]],
                    "sources_confirmed": 1,
                    "sources_checked": 1,
                },
            )
        except Exception as e:
            return EngineResult(
                score=2.5, max_score=5.0, confidence=0.4,
                details={"error": str(e)}, error=str(e),
            )

    def _generate_tagged_ideas(self, product_name: str) -> list:
        p = product_name.strip()
        pl = p.lower()
        tagged = []
        for cat in self.CATEGORIES:
            templates = self._templates_for_category(cat, p, pl)
            active_count = self._active_template_count(cat, pl, len(templates))
            for i in range(active_count):
                if i < len(templates):
                    tagged.append((templates[i], cat))
        return tagged

    def _active_template_count(self, category: str, pl: str, total: int) -> int:
        fit_map = {
            "problem_solving": lambda: total if any(
                w in pl for w in ["remov", "clean", "fix", "solv", "stop",
                                  "prevent", "protect", "repair", "elimin"]
            ) else max(4, total - 4),
            "transformation": lambda: total if any(
                w in pl for w in ["remov", "clean", "beauty", "hair", "skin",
                                  "makeup", "before", "after", "change"]
            ) else max(3, total - 5),
            "comparison": lambda: total,
            "tutorial": lambda: total,
            "reaction": lambda: total,
            "challenge": lambda: total,
            "mistakes": lambda: total,
            "before_after": lambda: total if any(
                w in pl for w in ["remov", "clean", "beauty", "hair", "skin",
                                  "makeup", "results", "change", "before"]
            ) else max(3, total - 5),
        }
        fn = fit_map.get(category, lambda: total)
        return fn()

    def _templates_for_category(self, category: str, p: str, pl: str) -> list:
        t = {
            "problem_solving": [
                f"Tired of dealing with {pl} Try this instead",
                f"Stop struggling with {pl} forever",
                f"The {pl} problem solved in 30 seconds",
                f"How {pl} fixes your biggest annoyance",
                f"Never deal with {pl} again use this hack",
                f"This {p} solves what nothing else could",
                f"The real reason your {pl} isnt working and how to fix it",
                f"One simple trick to fix {pl} permanently",
                f"Why everyone with {pl} needs this solution",
                f"Stop wasting time on {pl} do this instead",
            ],
            "transformation": [
                f"What {p} did to my {self._attr(pl)} was shocking",
                f"Watch {p} transform this completely",
                f"I used {p} for 7 days and here is what changed",
                f"The {p} glow up nobody asked for",
                f"From disaster to perfect with {p}",
                f"You wont believe what {p} can do",
                f"This {p} changed everything in 24 hours",
                f"The satisfying transformation with {p}",
                f"How {p} upgraded my whole routine",
                f"See the magic of {p} in action",
            ],
            "comparison": [
                f"{p} vs the expensive brand",
                f"{p} vs homemade alternatives",
                f"{p} vs leading competitor tested",
                f"Why {p} beats every other option",
                f"{p} tested against 5 alternatives",
                f"Cheap vs premium {self._cat(pl)} battle",
                f"The honest comparison nobody asked for",
                f"{p} vs knockoff which is better",
                f"Side by side {p} vs the rest",
                f"Is {p} really better than the original",
            ],
            "tutorial": [
                f"How to use {p} step by step",
                f"{p} beginners guide in 60 seconds",
                f"5 ways to use {p} you havent tried",
                f"The only {p} tutorial you will ever need",
                f"How to master {p} in 3 easy steps",
                f"10 hidden features of {p} you didnt know",
                f"Quick start guide for {p}",
                f"How to get the most out of {p}",
                f"Pro tips for using {p} like a expert",
                f"The complete guide to {p} for beginners",
            ],
            "reaction": [
                f"I tried {p} so you dont have to",
                f"My honest reaction to {p}",
                f"First time using {p} here is what happened",
                f"I bought {p} and I have thoughts",
                f"Unboxing and reacting to {p}",
                f"Everyone is talking about {p} so I tried it",
                f"The truth about {p} nobody talks about",
                f"Initial reaction testing {p} for the first time",
                f"I finally tried {p} was it worth it",
                f"My family reacts to {p} for the first time",
            ],
            "challenge": [
                f"30 day challenge with {p} results",
                f"Can {p} survive this extreme test",
                f"I only used {p} for a week challenge",
                f"The {p} challenge will it pass",
                f"Trying to break {p} in 60 seconds",
                f"24 hour challenge using only {p}",
                f"How many uses until {p} gives up",
                f"I put {p} through the ultimate test",
                f"The hardest challenge for {p} yet",
                f"Can {p} handle a week of daily use",
            ],
            "mistakes": [
                f"5 mistakes people make with {p}",
                f"Dont buy {p} until you watch this",
                f"The biggest {p} mistake ruining results",
                f"Stop using {p} wrong right now",
                f"3 things nobody tells you about {p}",
                f"I wasted money on {p} so you dont have to",
                f"Common {p} errors and how to avoid them",
                f"The number one mistake with {p}",
                f"Dont make these {p} mistakes",
                f"What I learned the hard way about {p}",
            ],
            "before_after": [
                f"Before and after using {p}",
                f"This before after with {p} is insane",
                f"What {p} did in 30 days before and after",
                f"See the difference {p} makes before after",
                f"The most satisfying before after with {p}",
                f"Real results before after using {p}",
                f"30 day transformation with {p}",
                f"The shocking before after of {p}",
                f"Proof {p} works before and after",
                f"Customer before after results with {p}",
            ],
        }
        return t.get(category, [])

    def _attr(self, pl: str) -> str:
        attrs = {"dog": "dogs fur", "cat": "cats fur", "pet": "pets coat",
                 "hair": "hair", "car": "cars interior", "skin": "skin",
                 "floor": "floors", "carpet": "carpet", "fabric": "fabric"}
        for k, v in attrs.items():
            if k in pl:
                return v
        return "things"

    def _cat(self, pl: str) -> str:
        cats = {"pet": "pet", "home": "home", "beauty": "beauty",
                "kitchen": "kitchen", "car": "auto", "fitness": "fitness",
                "dog": "pet", "cat": "pet", "hair": "beauty"}
        for k, v in cats.items():
            if k in pl:
                return v
        return "product"

    def _deduplicate(self, tagged: list) -> tuple:
        seen = set()
        unique = []
        dupes = 0
        for text, cat in tagged:
            key = text.lower().strip()
            if key not in seen:
                seen.add(key)
                unique.append((text, cat))
            else:
                dupes += 1
        return unique, dupes

    def _count_by_category(self, unique_ideas: list) -> dict:
        counts = {}
        for _, cat in unique_ideas:
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _calculate_diversity(self, breakdown: dict) -> float:
        populated = sum(1 for cat in self.CATEGORIES if breakdown.get(cat, 0) > 0)
        return round(populated / len(self.CATEGORIES), 2)

    def _score(self, unique_count: int) -> float:
        if unique_count >= 50:
            return 5.0
        if unique_count >= 40:
            return 4.0
        if unique_count >= 30:
            return 3.0
        if unique_count >= 20:
            return 2.0
        return 1.0
