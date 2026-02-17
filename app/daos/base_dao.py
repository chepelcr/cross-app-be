from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
    before_sleep_log,
)

from app.configuration.app_config import AppConfig
from app.exceptions.api_not_available_exception import ApiNotAvailableException

logger = logging.getLogger(__name__)


class BaseDAO:
    """Base Data Access Object for external API communication.

    Uses httpx with automatic retry logic for transient failures.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.timeout = timeout

        if base_url:
            self.base_url = base_url
        else:
            self.base_url = AppConfig.get_key("api.services.url", "")

        self.client = httpx.Client(
            timeout=httpx.Timeout(timeout),
            follow_redirects=True,
        )

        logger.debug(f"BaseDAO initialized with base_url={self.base_url}, timeout={timeout}s")

    def __del__(self):
        if hasattr(self, "client") and self.client:
            self.client.close()

    def close(self) -> None:
        if self.client:
            self.client.close()
            logger.debug("HTTP client closed")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type((httpx.ConnectError, httpx.TimeoutException)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> Any:
        full_url = url if url.startswith("http") else f"{self.base_url}{url}"

        try:
            logger.debug(f"Making {method} request to {full_url}")
            response = self.client.request(method, full_url, **kwargs)
            response.raise_for_status()

            if response.content:
                return response.json()
            return None

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error(f"Connection/timeout error for {full_url}: {e}")
            raise

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} for {full_url}: {e.response.text}")
            raise

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        return self._request("GET", url, params=params, **kwargs)

    def _post(self, url: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        return self._request("POST", url, json=json, **kwargs)

    def _put(self, url: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        return self._request("PUT", url, json=json, **kwargs)

    def _patch(self, url: str, json: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Any:
        return self._request("PATCH", url, json=json, **kwargs)

    def _delete(self, url: str, **kwargs: Any) -> Any:
        return self._request("DELETE", url, **kwargs)
