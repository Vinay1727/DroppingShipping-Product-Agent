from typing import Optional

import requests

from product_agent.config import settings
from product_agent.models import ProviderResult
from .base_provider import BaseProvider


class RedditProvider(BaseProvider):
    priority = 1
    display_name = "Reddit"
    USER_AGENT = "ProductAgent/1.0 (by /u/product_agent)"

    def _do_fetch(self, product_name: str) -> ProviderResult:
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            result = self._fetch_via_praw(product_name)
            if result.success:
                return result

        return self._fetch_via_json_api(product_name)

    def _fetch_via_praw(self, product_name: str) -> ProviderResult:
        try:
            import praw

            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )

            post_count = 0
            comment_count = 0
            subreddits = set()

            for submission in reddit.subreddit("all").search(
                product_name, sort="new", time_filter="month", limit=50
            ):
                post_count += 1
                subreddits.add(submission.subreddit.display_name)
                comment_count += submission.num_comments

            is_trending = post_count > 10

            return ProviderResult(
                source="RedditProvider",
                success=True,
                data={
                    "post_count_30d": post_count,
                    "comment_count_30d": comment_count,
                    "avg_sentiment": 0.5,
                    "subreddits": list(subreddits),
                    "is_trending": is_trending,
                },
            )

        except Exception as e:
            return ProviderResult(
                source="RedditProvider",
                success=False,
                error=f"PRAW error: {e}",
            )

    def _fetch_via_json_api(self, product_name: str) -> ProviderResult:
        try:
            headers = {"User-Agent": self.USER_AGENT}
            params = {
                "q": product_name,
                "sort": "new",
                "t": "month",
                "limit": 100,
                "restrict_sr": "off",
            }

            resp = requests.get(
                "https://www.reddit.com/r/all/search.json",
                params=params,
                headers=headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()

            children = data.get("data", {}).get("children", [])
            posts = [c["data"] for c in children if c.get("kind") == "t3"]

            post_count = len(posts)
            subreddits = list({p.get("subreddit", "") for p in posts if p.get("subreddit")})
            comment_count = sum(p.get("num_comments", 0) for p in posts)
            is_trending = post_count > 10

            return ProviderResult(
                source="RedditProvider",
                success=True,
                data={
                    "post_count_30d": post_count,
                    "comment_count_30d": comment_count,
                    "avg_sentiment": 0.5,
                    "subreddits": subreddits,
                    "is_trending": is_trending,
                },
            )

        except Exception as e:
            return ProviderResult(
                source="RedditProvider",
                success=False,
                error=f"Reddit JSON API error: {e}",
            )
