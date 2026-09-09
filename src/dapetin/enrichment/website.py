from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

from dapetin.domain.models import Business

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d .()\-]{7,}\d)")
SOCIAL_HOSTS = ("instagram.com", "facebook.com", "linkedin.com", "tiktok.com")


@dataclass(slots=True)
class EnrichmentResult:
    success: bool
    url: str | None = None
    title: str | None = None
    emails: list[str] | None = None
    phones: list[str] | None = None
    social_urls: list[str] | None = None
    whatsapp: bool = False
    error: str | None = None


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.links: list[str] = []
        self.text_parts: list[str] = []
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        href = attributes.get("href")
        if href:
            self.links.append(href)
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title_parts.append(data)
        self.text_parts.append(data)


class WebsiteEnricher:
    """Fetch one public webpage and extract lightweight contact signals."""

    def __init__(self, timeout: float = 8.0, max_bytes: int = 1_000_000) -> None:
        self.timeout = timeout
        self.max_bytes = max_bytes

    def enrich(self, business: Business) -> EnrichmentResult:
        if not business.website:
            return EnrichmentResult(success=False, error="business has no website")

        url = _normalize_url(business.website)
        request = Request(url, headers={"User-Agent": "DAPETIN/0.1 (+public-site-enrichment)"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                final_url = response.geturl()
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    return EnrichmentResult(success=False, url=final_url, error="not an HTML page")
                html = response.read(self.max_bytes).decode("utf-8", errors="ignore")
        except Exception as exc:  # network failures should not stop the pipeline
            return EnrichmentResult(success=False, url=url, error=str(exc))

        parser = _PageParser()
        parser.feed(html)
        text = " ".join(parser.text_parts)
        emails = sorted(set(EMAIL_RE.findall(html + " " + text)))
        phones = sorted({_normalize_phone(value) for value in PHONE_RE.findall(text) if _normalize_phone(value)})
        absolute_links = [urljoin(final_url, link) for link in parser.links]
        social_urls = sorted({link for link in absolute_links if _is_social(link)})
        whatsapp = any("wa.me/" in link.lower() or "whatsapp.com" in link.lower() for link in absolute_links)

        return EnrichmentResult(
            success=True,
            url=final_url,
            title=" ".join(parser.title_parts).strip() or None,
            emails=emails,
            phones=phones,
            social_urls=social_urls,
            whatsapp=whatsapp,
        )


def apply_enrichment(business: Business, result: EnrichmentResult) -> Business:
    """Merge enrichment signals into the existing business record."""
    if result.url:
        business.website = result.url
    if result.emails and not business.email:
        business.email = result.emails[0]
    if result.phones and not business.phone:
        business.phone = result.phones[0]
    if result.title:
        business.metadata["website_title"] = result.title
    if result.social_urls:
        business.metadata["social_urls"] = "|".join(result.social_urls)
    if result.whatsapp:
        business.metadata["whatsapp"] = "true"
    if result.error:
        business.metadata["enrichment_error"] = result.error
    business.metadata["enrichment_status"] = "success" if result.success else "failed"
    return business


def _normalize_url(value: str) -> str:
    value = value.strip()
    return value if urlparse(value).scheme else f"https://{value}"


def _normalize_phone(value: str) -> str:
    value = re.sub(r"[^+\d]", "", value)
    return value if len(re.sub(r"\D", "", value)) >= 9 else ""


def _is_social(url: str) -> bool:
    host = (urlparse(url).hostname or "").lower()
    return any(host == domain or host.endswith("." + domain) for domain in SOCIAL_HOSTS)
