from typing import Optional

from ..config import settings
from ..models import ProviderResult
from .base_provider import BaseProvider


class RedditProvider(BaseProvider):
    def _do_fetch(self, product_name: str) -> ProviderResult:
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            return self._fetch_via_praw(product_name)

        return self._fetch_via_pushshift(product_name)

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

            avg_sentiment = 0.5
            is_trending = post_count > 10

            return ProviderResult(
                source="RedditProvider",
                success=True,
                data={
                    "post_count_30d": post_count,
                    "comment_count_30d": comment_count,
                    "avg_sentiment": avg_sentiment,
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

    def _fetch_via_pushshift(self, product_name: str) -> ProviderResult:
        try:
            import requests

            params = {
                "q": product_name,
                "size": 100,
                "sort": "created_utc",
                "order": "desc",
                "subreddit": "all",
                "after": "30d",
            }
            resp = requests.get(
                "https://api.pushshift.io/reddit/search/submission",
                params=params,
                timeout=15,
            )
            data = resp.json()
            posts = data.get("data", [])

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
                error=f"Pushshift error: {e}",
            )
