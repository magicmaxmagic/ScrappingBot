import hashlib
import os
import json
import re
from urllib.parse import urljoin, urlparse

import orjson
import scrapy
from scrapy import Request
from scrapy.http import Response

# Simple HTML text helpers
WHITESPACE_RE = re.compile(r"\s+")


def clean_text(x: str) -> str:
    return WHITESPACE_RE.sub(" ", (x or "").strip())


class SiteGenericSpider(scrapy.Spider):
    name = "site_generic"

    custom_settings = {
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
    }

    def start_requests(self):
        # Load sources from config file; allow override via SOURCES_FILE env
        import yaml
        from pathlib import Path

        override = os.environ.get("SOURCES_FILE")
        cfg_path = Path(override) if override else (Path(__file__).resolve().parents[2] / "config" / "sources.yml")
        try:
            with cfg_path.open("r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(orjson.dumps({"event": "config_error", "error": str(e)}).decode())
            cfg = {"sources": []}
        for site in cfg.get("sources", []) or []:
            for url in (site.get("start_urls", []) or []) + (site.get("sitemaps", []) or []):
                yield Request(
                    url,
                    callback=self.parse_listing_index,
                    meta={
                        "playwright": site.get("use_js", False),
                        "site": site,
                    },
                )

    def parse_listing_index(self, response: Response):
        site = response.meta.get("site", {})
        link_patterns = site.get("listing_patterns") or []
        hrefs = response.css("a::attr(href)")
        href_list = hrefs.getall() if hrefs is not None else []
        for href in href_list:
            abs_url = urljoin(response.url, href)
            if any(re.search(pat, abs_url) for pat in link_patterns):
                yield Request(
                    abs_url,
                    callback=self.parse_listing,
                    meta={
                        "playwright": site.get("use_js", False),
                        "site": site,
                    },
                )

    def parse_listing(self, response: Response):
        site = response.meta.get("site", {})
        url = response.url
        body_text = clean_text(response.text)

        # Heuristic extraction (very simple) — extractor/ will refine downstream
        price_match = re.search(r"([€$]|EUR|USD)\s?([0-9][0-9\s.,]*)", body_text)
        price = None
        currency = None
        if price_match:
            cur_raw = price_match.group(1)
            currency = "EUR" if cur_raw in ["€", "EUR"] else ("USD" if cur_raw in ["$", "USD"] else None)
            price = re.sub(r"[^0-9.]", "", price_match.group(2)).strip()
            price = float(price) if price else None

        kind = "rent" if re.search(r"\blocation\b|\brent\b", body_text, re.I) else "sale"

        item = {
            "kind": kind,
            "price": price,
            "currency": currency,
            "url": url,
            "title": response.css("title::text").get(),
            "site_domain": urlparse(url).netloc,
            "raw_html_path": self.save_html(response),
        }

        # Log JSON line
        self.logger.info(orjson.dumps({"event": "parsed", "url": url}).decode())

        yield item

    def save_html(self, response: Response) -> str:
        # Save raw HTML for auditing; GitHub Actions will upload as artifact
        from pathlib import Path

        domain = urlparse(response.url).netloc.replace(":", "_")
        out_dir = Path(__file__).resolve().parents[2] / "data" / "html" / domain
        out_dir.mkdir(parents=True, exist_ok=True)
        sha = hashlib.sha1(response.url.encode()).hexdigest()[:12]
        path = out_dir / f"{sha}.html"
        path.write_bytes(response.body)
        return str(path)
