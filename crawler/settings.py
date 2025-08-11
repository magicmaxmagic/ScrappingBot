import os

BOT_NAME = "ai_scraper"
SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

# Respect robots.txt
ROBOTSTXT_OBEY = True

# Concurrency & throttling
CONCURRENT_REQUESTS = int(os.getenv("CONCURRENT_REQUESTS", 8))
DOWNLOAD_DELAY = float(os.getenv("DOWNLOAD_DELAY", 0.5))
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Identify politely
DEFAULT_REQUEST_HEADERS = {
    "User-Agent": os.getenv(
        "USER_AGENT",
        "ai-scraper/0.1 (+https://example.com; contact: ops@example.com)"
    )
}

# Logging: JSON-friendly minimal format
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# FEEDS example (disabled by default)
# FEEDS = {"data/listings.json": {"format": "json", "encoding": "utf8", "overwrite": True}}

# Playwright integration
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": True,
}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = int(os.getenv("PLAYWRIGHT_TIMEOUT_MS", "30000"))

# No explicit downloader middlewares needed for scrapy-playwright>=0.0.33
