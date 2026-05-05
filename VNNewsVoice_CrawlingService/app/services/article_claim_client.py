import logging
from dataclasses import dataclass
from typing import Any

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ArticleClaimDecision:
    should_publish: bool
    reason: str
    canonical_url: str


class ArticleClaimClient:
    """Client for pre-ML duplicate claim checks against ArticleService."""

    def __init__(
        self,
        *,
        base_url: str,
        claim_endpoint: str,
        timeout_seconds: float,
        enabled: bool,
        fail_open: bool,
    ) -> None:
        self._enabled = enabled
        self._fail_open = fail_open
        self._timeout_seconds = max(timeout_seconds, 0.1)
        self._claim_url = f"{base_url.rstrip('/')}/{claim_endpoint.lstrip('/')}"

    @classmethod
    def from_settings(cls) -> "ArticleClaimClient":
        return cls(
            base_url=settings.article_service_base_url,
            claim_endpoint=settings.article_claim_endpoint,
            timeout_seconds=settings.article_claim_timeout_seconds,
            enabled=settings.article_claim_enabled,
            fail_open=settings.article_claim_fail_open,
        )

    async def claim(
        self,
        *,
        source_id: str,
        source_name: str,
        title: str,
        url: str,
    ) -> ArticleClaimDecision:
        if not self._enabled:
            return ArticleClaimDecision(
                should_publish=True,
                reason="claim_check_disabled",
                canonical_url=url,
            )

        payload = {
            "sourceId": source_id,
            "sourceName": source_name,
            "title": title,
            "url": url,
        }

        timeout = aiohttp.ClientTimeout(total=self._timeout_seconds)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(self._claim_url, json=payload) as response:
                    text_body = await response.text()

                    if response.status < 200 or response.status >= 300:
                        logger.warning(
                            "Article claim failed: status=%s url=%s body=%r",
                            response.status,
                            self._claim_url,
                            text_body[:300],
                        )
                        if self._fail_open:
                            return ArticleClaimDecision(
                                True, "claim_http_error_fail_open", url
                            )
                        return ArticleClaimDecision(
                            False, "claim_http_error_fail_closed", url
                        )

                    data: Any
                    try:
                        data = await response.json(content_type=None)
                    except Exception:
                        logger.warning(
                            "Article claim returned non-JSON payload: url=%s body=%r",
                            self._claim_url,
                            text_body[:300],
                        )
                        if self._fail_open:
                            return ArticleClaimDecision(
                                True, "claim_non_json_fail_open", url
                            )
                        return ArticleClaimDecision(
                            False, "claim_non_json_fail_closed", url
                        )

                    result = data.get("result") if isinstance(data, dict) else None
                    decision = result if isinstance(result, dict) else data
                    if not isinstance(decision, dict):
                        if self._fail_open:
                            return ArticleClaimDecision(
                                True, "claim_invalid_payload_fail_open", url
                            )
                        return ArticleClaimDecision(
                            False, "claim_invalid_payload_fail_closed", url
                        )

                    should_process_raw = decision.get("shouldProcess", True)
                    should_publish = bool(should_process_raw)
                    reason = str(decision.get("reason") or "unknown")
                    canonical_url = (
                        str(decision.get("canonicalUrl") or url).strip() or url
                    )
                    return ArticleClaimDecision(should_publish, reason, canonical_url)
        except Exception:
            logger.exception("Article claim request failed: url=%s", self._claim_url)
            if self._fail_open:
                return ArticleClaimDecision(True, "claim_request_error_fail_open", url)
            return ArticleClaimDecision(False, "claim_request_error_fail_closed", url)
