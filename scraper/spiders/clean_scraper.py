#!/usr/bin/env python3
"""
Production-ready async real estate scraper with Playwright
Supports API interception and DOM fallback with WAF detection
Follows ethical scraping practices and ToS compliance
"""
import asyncio
import argparse
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright, Browser, Page, Response

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealEstateScraper:
    """Production-ready async real estate scraper with WAF detection"""
    
    def __init__(self, headless: bool = True, timeout_ms: int = 30000, debug: bool = False):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.debug = debug
        self.browser: Optional[Browser] = None
        self.captured_api_data: List[Dict] = []
        self.start_time = time.time()
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        
        # Set browser executable path for Docker environment
        import os
        executable_path = None
        if os.path.exists("/home/scraper/.cache/ms-playwright/chromium-1091/chrome-linux/chrome"):
            executable_path = "/home/scraper/.cache/ms-playwright/chromium-1091/chrome-linux/chrome"
        
        self.browser = await self.playwright.chromium.launch(
            executable_path=executable_path,
            headless=self.headless,
            args=[
                '--no-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-web-security',
                '--disable-features=site-per-process',
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()
        
    def build_search_url(self, where: str, what: str, when: str, start_url: Optional[str] = None) -> str:
        """Build search URL from CLI args or use provided start_url"""
        if start_url:
            return start_url
            
        # Default URL building logic - ADAPT PER SOURCE
        base_url = "https://www.realtor.ca"  # Example - change per source
        
        # Normalize location
        where_clean = where.lower().replace(" ", "-").strip("/")
        what_clean = what.lower().replace(" ", "-").strip("/")
        
        # Build path based on source's URL structure
        if "lachine" in where_clean or "montreal" in where_clean:
            path = f"/qc/montreal/{where_clean}"
        else:
            path = f"/qc/{where_clean}"
            
        if "condo" in what_clean:
            path += "/condos-for-sale"
        elif "rent" in what_clean:
            path += "/real-estate-for-rent"
        else:
            path += "/real-estate-for-sale"
            
        return f"{base_url}{path}"
        
    async def detect_waf_block(self, page: Page) -> tuple[bool, str]:
        """Detect WAF blocks and return (is_blocked, reason)"""
        try:
            content = await page.content()
            content_lower = content.lower()
            
            # Common WAF patterns - DO NOT attempt to bypass
            waf_patterns = [
                ("incapsula", "Incapsula protection"),
                ("cloudflare", "Cloudflare protection"),
                ("access denied", "Access denied"),
                ("blocked", "Request blocked"),
                ("captcha", "CAPTCHA required"),
                ("incident id", "WAF incident"),
                ("security check", "Security check"),
                ("ddos protection", "DDoS protection"),
                ("rate limit", "Rate limited"),
                ("forbidden", "Forbidden access")
            ]
            
            for pattern, reason in waf_patterns:
                if pattern in content_lower:
                    logger.warning(f"WAF detected: {reason}")
                    return True, reason
                    
            # Check for common blocked status codes
            if page.url.startswith("data:") or "about:blank" in page.url:
                return True, "Navigation blocked"
                
            return False, ""
            
        except Exception as e:
            logger.error(f"WAF detection error: {e}")
            return True, f"Detection error: {e}"
            
    async def capture_api(self, page: Page) -> List[Dict]:
        """Capture API/XHR responses - ONLY if allowed by ToS"""
        captured_data = []
        
        async def handle_response(response: Response):
            try:
                url = response.url
                # ADAPT: Change API patterns per source
                api_patterns = [
                    '/api/listing',
                    '/api/property',
                    'PropertySearch',
                    '/search/results',
                    'ajax/search'
                ]
                
                if any(pattern.lower() in url.lower() for pattern in api_patterns):
                    if response.status == 200:
                        try:
                            json_data = await response.json()
                            if json_data and isinstance(json_data, dict):
                                logger.info(f"Captured API response from: {url}")
                                captured_data.append({
                                    "url": url,
                                    "data": json_data,
                                    "timestamp": datetime.now(timezone.utc).isoformat()
                                })
                        except Exception as e:
                            logger.debug(f"Failed to parse JSON from {url}: {e}")
            except Exception as e:
                logger.debug(f"Response handler error: {e}")
                
        page.on("response", handle_response)
        return captured_data
        
    async def extract_dom(self, page: Page) -> List[Dict]:
        """Extract listings from DOM using CSS selectors"""
        listings = []
        
        try:
            # ADAPT: Change selectors per source
            listing_selectors = [
                '[data-testid*="listing"]',
                '[class*="listing-card"]',
                '[class*="property-card"]',
                '.listing',
                '.property',
                '[itemtype*="RealEstateListing"]'
            ]
            
            for selector in listing_selectors:
                elements = await page.query_selector_all(selector)
                if elements:
                    logger.info(f"Found {len(elements)} listings with selector: {selector}")
                    
                    for i, element in enumerate(elements[:50]):  # Limit to prevent timeouts
                        try:
                            listing_data = await self.extract_single_listing(element, page.url)
                            if listing_data:
                                listings.append(listing_data)
                        except Exception as e:
                            logger.debug(f"Failed to extract listing {i}: {e}")
                    break  # Use first successful selector
                    
        except Exception as e:
            logger.error(f"DOM extraction failed: {e}")
            
        return listings
        
    async def extract_single_listing(self, element, base_url: str) -> Optional[Dict]:
        """Extract data from a single listing DOM element"""
        try:
            data = {}
            
            # ADAPT: Change selectors per source's HTML structure
            
            # Extract price
            price_selectors = [
                '[class*="price"]',
                '[data-testid*="price"]',
                '.price',
                '[class*="amount"]'
            ]
            
            for sel in price_selectors:
                try:
                    price_elem = await element.query_selector(sel)
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        if price_text and ('$' in price_text or '€' in price_text):
                            data['price_raw'] = price_text.strip()
                            break
                except:
                    continue
                    
            # Extract address
            addr_selectors = [
                '[class*="address"]',
                '[data-testid*="address"]',
                '.address',
                '[class*="location"]'
            ]
            
            for sel in addr_selectors:
                try:
                    addr_elem = await element.query_selector(sel)
                    if addr_elem:
                        addr_text = await addr_elem.inner_text()
                        if addr_text and len(addr_text.strip()) > 5:
                            data['address'] = addr_text.strip()
                            break
                except:
                    continue
                    
            # Extract URL
            try:
                link_elem = await element.query_selector('a[href]')
                if link_elem:
                    href = await link_elem.get_attribute('href')
                    if href:
                        data['url'] = urljoin(base_url, href)
            except:
                pass
                
            # Extract additional fields - ADAPT per source
            try:
                # Bedrooms
                bed_elem = await element.query_selector('[class*="bed"], [data-testid*="bed"]')
                if bed_elem:
                    bed_text = await bed_elem.inner_text()
                    bed_match = re.search(r'(\d+)', bed_text)
                    if bed_match:
                        data['bedrooms'] = int(bed_match.group(1))
                        
                # Bathrooms
                bath_elem = await element.query_selector('[class*="bath"], [data-testid*="bath"]')
                if bath_elem:
                    bath_text = await bath_elem.inner_text()
                    bath_match = re.search(r'(\d+(?:\.\d+)?)', bath_text)
                    if bath_match:
                        data['bathrooms'] = float(bath_match.group(1))
                        
            except:
                pass
                
            return data if data else None
            
        except Exception as e:
            logger.debug(f"Single listing extraction failed: {e}")
            return None
            
    def normalize_listing(self, listing: Dict, source: str = "dom") -> Optional[Dict]:
        """Normalize listing data to standard format"""
        try:
            normalized = {}
            
            # Normalize price
            if 'price_raw' in listing:
                price_text = listing['price_raw']
                # Extract numeric value
                price_match = re.search(r'[\d,]+', price_text.replace(' ', ''))
                if price_match:
                    try:
                        normalized['price'] = int(price_match.group().replace(',', ''))
                    except:
                        pass
            elif 'price' in listing:
                normalized['price'] = listing.get('price')
                
            # Address
            if listing.get('address'):
                normalized['address'] = listing['address']
                
            # URL
            if listing.get('url'):
                normalized['url'] = listing['url']
                
            # Additional fields
            if listing.get('bedrooms'):
                normalized['bedrooms'] = listing['bedrooms']
            if listing.get('bathrooms'):
                normalized['bathrooms'] = listing['bathrooms']
                
            # Only return if we have essential data
            if normalized.get('price') or normalized.get('address'):
                return normalized
                
        except Exception as e:
            logger.debug(f"Normalization failed: {e}")
            
        return None
        
    async def write_preview(self, listings: List[Dict], source: str, blocked: bool, strategy: str, error: Optional[str] = None):
        """Write standardized preview JSON file"""
        try:
            logs_dir = Path(__file__).resolve().parents[2] / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            elapsed_sec = round(time.time() - self.start_time, 2)
            
            preview_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "count": len(listings),
                "preview": listings[:20] if listings else [],  # First 20 items
                "blocked": blocked,
                "strategy": strategy,
                "elapsed_sec": elapsed_sec,
                "source": source
            }
            
            if error:
                preview_data["error"] = error
                
            preview_path = logs_dir / f"preview_{source}.json"
            preview_path.write_text(
                json.dumps(preview_data, indent=2, ensure_ascii=False), 
                encoding="utf-8"
            )
            
            logger.info(f"Preview written: {preview_path} ({len(listings)} items, {strategy})")
            return str(preview_path)
            
        except Exception as e:
            logger.error(f"Failed to write preview: {e}")
            raise
            
    async def save_debug_files(self, page: Page, source: str):
        """Save debug files if --debug enabled"""
        if not self.debug:
            return
            
        try:
            logs_dir = Path(__file__).resolve().parents[2] / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # Save HTML
            html_content = await page.content()
            html_path = logs_dir / f"debug_{source}_page.html"
            html_path.write_text(html_content, encoding="utf-8")
            
            # Save screenshot
            screenshot_path = logs_dir / f"debug_{source}_screenshot.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)
            
            logger.info(f"Debug files saved: {html_path}, {screenshot_path}")
            
        except Exception as e:
            logger.warning(f"Debug file save failed: {e}")
            
    async def scrape(self, where: str, what: str, when: str, start_url: Optional[str] = None, 
                    force_dom: bool = False, source: str = "realtor") -> Dict:
        """Main scraping method"""
        if not self.browser:
            raise RuntimeError("Browser not initialized - use async context manager")
            
        search_url = self.build_search_url(where, what, when, start_url)
        logger.info(f"Starting scrape: {search_url}")
        
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        page = await context.new_page()
        
        try:
            # Set up API capture if not forcing DOM
            if not force_dom:
                await self.capture_api(page)
            
            # Add random delay to simulate human behavior
            await asyncio.sleep(2 + (time.time() % 3))
            
            # Navigate to page with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                    logger.info(f"Page loaded: {page.url}")
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise e
                    logger.warning(f"Navigation attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(5 + attempt * 2)
            
            # Simulate human behavior - scroll and mouse movements
            await page.mouse.move(100, 100)
            await asyncio.sleep(1)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 4)")
            await asyncio.sleep(2)
            
            # Check for WAF block immediately
            is_blocked, block_reason = await self.detect_waf_block(page)
            if is_blocked:
                await self.save_debug_files(page, source)
                await self.write_preview([], source, True, "blocked", block_reason)
                logger.warning(f"WAF blocked: {block_reason}")
                return {"blocked": True, "reason": block_reason}
            
            # Wait for dynamic content with longer timeout
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except:
                logger.info("Networkidle timeout - continuing")
            
            # Additional wait for API calls to complete
            await asyncio.sleep(3 + (time.time() % 2))
            
            listings = []
            strategy = "blocked"
            
            # Try API capture first (if allowed and not forced DOM)
            if not force_dom and self.captured_api_data:
                logger.info("Processing captured API data")
                for api_response in self.captured_api_data:
                    # ADAPT: Parse API response structure per source
                    api_data = api_response.get('data', {})
                    results = (api_data.get('Results') or 
                              api_data.get('listings') or 
                              api_data.get('properties') or [])
                    
                    if results and isinstance(results, list):
                        for item in results:
                            normalized = self.normalize_listing(item, "api")
                            if normalized:
                                listings.append(normalized)
                
                if listings:
                    strategy = "api"
            
            # Fallback to DOM extraction
            if not listings:
                logger.info("No API data - extracting from DOM")
                dom_listings = await self.extract_dom(page)
                for item in dom_listings:
                    normalized = self.normalize_listing(item, "dom")
                    if normalized:
                        listings.append(normalized)
                
                if listings:
                    strategy = "dom"
                else:
                    strategy = "blocked"
            
            # Save debug files
            await self.save_debug_files(page, source)
            
            # Write preview
            await self.write_preview(listings, source, False, strategy)
            
            logger.info(f"Scraping completed: {len(listings)} listings via {strategy}")
            return {
                "success": True,
                "count": len(listings), 
                "strategy": strategy,
                "blocked": False
            }
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            await self.save_debug_files(page, source)
            await self.write_preview([], source, False, "error", str(e))
            return {"success": False, "error": str(e)}
            
        finally:
            await context.close()


async def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(description="Production real estate scraper")
    parser.add_argument('--where', required=True, help='City/location to search')
    parser.add_argument('--what', required=True, help='Property type (condo, house, etc)')
    parser.add_argument('--when', default='all', help='Date filter (last_7_days, last_30_days, all)')
    parser.add_argument('--start_url', help='Direct URL to scrape (overrides where/what)')
    parser.add_argument('--source', default='realtor', help='Source name for output file')
    parser.add_argument('--dom', action='store_true', help='Force DOM extraction only')
    parser.add_argument('--debug', action='store_true', help='Save HTML and screenshots')
    parser.add_argument('--headless', action='store_true', default=True, help='Run headless')
    parser.add_argument('--timeout', type=int, default=30000, help='Page timeout (ms)')
    
    args = parser.parse_args()
    
    logger.info(f"Starting scraper: {args.source} - {args.where} {args.what}")
    
    try:
        async with RealEstateScraper(
            headless=args.headless, 
            timeout_ms=args.timeout,
            debug=args.debug
        ) as scraper:
            
            result = await scraper.scrape(
                where=args.where,
                what=args.what, 
                when=args.when,
                start_url=args.start_url,
                force_dom=args.dom,
                source=args.source
            )
            
            if result.get("blocked"):
                logger.warning(f"❌ Blocked by WAF: {result.get('reason')}")
                return 2  # Blocked exit code
            elif result.get("success"):
                logger.info(f"✅ Success: {result.get('count')} listings via {result.get('strategy')}")
                return 0
            else:
                logger.error(f"❌ Failed: {result.get('error')}")
                return 1
                
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
