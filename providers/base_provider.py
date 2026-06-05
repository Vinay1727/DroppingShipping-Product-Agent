import time
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

import requests
from cachetools import TTLCache

from ..config import settings
from ..models import ProviderResult


logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    CACHE_TTL = settings.PROVIDER_CACHE_TTL
    _caches: dict = {}

    @classmethod
    def _get_cache(cls) -> TTLCache:
        name = cls.__name__
        if name not in cls._caches:
            cls._caches[name] = TTLCache(maxsize=100, ttl=cls.CACHE_TTL)
        return cls._caches[name]

    @abstractmethod
    def _do_fetch(self, product_name: str) -> ProviderResult:
        pass

    def fetch(self, product_name: str) -> ProviderResult:
        cache = self._get_cache()
        cache_key = product_name.lower().strip()

        if cache_key in cache:
            logger.debug(f"Cache hit for {self.__class__.__name__}: {product_name}")
            return cache[cache_key]

        result = self._rate_limited_fetch(product_name)
        cache[cache_key] = result
        return result

    def _rate_limited_fetch(self, product_name: str) -> ProviderResult:
        delay = settings.PROVIDER_RATE_LIMIT_DELAY
        max_retries = settings.PROVIDER_MAX_RETRIES

        for attempt in range(max_retries + 1):
            if attempt > 0:
                wait = delay * (2 ** attempt)
                logger.info(f"Retry {attempt}/{max_retries} for {product_name} after {wait:.1f}s")
                time.sleep(wait)
            else:
                time.sleep(delay)

            try:
                result = self._do_fetch(product_name)
                result.fetched_at = datetime.now().isoformat()
                return result
            except requests.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1} for {product_name}")
                if attempt == max_retries:
                    return ProviderResult(
                        source=self.__class__.__name__,
                        success=False,
                        error=f"Request timed out after {max_retries + 1} attempts",
                    )
            except Exception as e:
                logger.error(f"{self.__class__.__name__} error for '{product_name}': {e}")
                return ProviderResult(
                    source=self.__class__.__name__,
                    success=False,
                    error=str(e),
                )

        return ProviderResult(
            source=self.__class__.__name__,
            success=False,
            error="Max retries exceeded",
        )

    def _safe_request(
        self,
        url: str,
        params: Optional[dict] = None,
        headers: Optional[dict] = None,
        timeout: int = 15,
    ) -> requests.Response:
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp
