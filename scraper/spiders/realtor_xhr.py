#!/usr/bin/env python3
"""
Async real estate scraper with Playwright
Supports API interception and DOM fallback with WAF detection
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

class RealtorXHRScraper:
    def __init__(self, headless: bool = True, timeout_ms: int = 30000):
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.browser: Optional[Browser] = None
        self.captured_data: List[Dict] = []

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        await self.playwright.stop()

    def build_search_url(self, where: str = "montreal/lachine", what: str = "condos-for-sale", when: str = "") -> str:
        """Build realtor.ca search URL from CLI args"""
        base_url = "https://www.realtor.ca"
        
        # Normalize location
        where_clean = where.lower().replace(" ", "-").strip("/")
        if not where_clean.startswith("qc/"):
            where_clean = f"qc/{where_clean}"
        
        # Build path
        path_parts = [where_clean, what]
        if when:
            path_parts.append(when)
        
        url = f"{base_url}/{'/'.join(path_parts)}"
        logger.info(f"Built search URL: {url}")
        return url

    async def intercept_api_calls(self, page: Page):
        """Set up response interception for PropertySearch API calls"""
        
        async def handle_response(response: Response):
            try:
                url = response.url
                if ('PropertySearch' in url or 'api/Listing' in url) and response.status == 200:
                    logger.info(f"Intercepted API call: {url}")
                    
                    try:
                        json_data = await response.json()
                        if isinstance(json_data, dict):
                            # Look for listings array in various possible paths
                            listings = (
                                json_data.get('Results', []) or
                                json_data.get('listings', []) or 
                                json_data.get('data', {}).get('listings', []) or
                                json_data.get('properties', []) or
                                []
                            )
                            
                            if listings and isinstance(listings, list):
                                logger.info(f"Found {len(listings)} listings in API response")
                                self.captured_data.extend(listings)
                            else:
                                logger.info(f"API response structure: {list(json_data.keys())}")
                                # Save full response for debugging
                                self.captured_data.append({
                                    "_debug_full_response": json_data,
                                    "_api_url": url
                                })
                    except Exception as e:
                        logger.warning(f"Failed to parse JSON from {url}: {e}")
                        
            except Exception as e:
                logger.warning(f"Response handler error: {e}")

        page.on("response", handle_response)
        
    async def save_html_fallback(self, page: Page):
        """Save HTML fallback for debugging"""
        try:
            html_content = await page.content()
            logs_dir = Path(__file__).resolve().parents[2] / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            html_path = logs_dir / "realtor_index.html"
            html_path.write_text(html_content, encoding="utf-8")
            logger.info(f"Saved HTML fallback: {html_path}")
        except Exception as e:
            logger.warning(f"Failed to save HTML fallback: {e}")
            
    async def extract_dom_fallback_basic(self, page: Page):
        """Fallback DOM extraction if API interception fails (basic version)"""
        try:
            # Look for common listing container patterns
            selectors = [
                '[data-testid*="listing"]',
                '[class*="listing"]',
                '[class*="property"]',
                '.property-card',
                '.listing-card'
            ]
            
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for element in elements[:20]:  # Limit to avoid timeouts
                            try:
                                listing = await self.extract_listing_data_basic(element)
                                if listing and (listing.get('price') or listing.get('address')):
                                    self.captured_data.append(listing)
                            except Exception as e:
                                logger.debug(f"Failed to extract listing data: {e}")
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"DOM fallback extraction failed: {e}")
            
    async def extract_listing_data_basic(self, element) -> Optional[Dict]:
        """Extract listing data from a DOM element (basic fallback)"""
        try:
            data = {}
            
            # Try to extract price
            price_selectors = ['[class*="price"]', '[data-testid*="price"]', '.price']
            for sel in price_selectors:
                try:
                    price_elem = await element.query_selector(sel)
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        if price_text and '$' in price_text:
                            data['price'] = price_text.strip()
                            break
                except:
                    continue
                    
            # Try to extract address
            addr_selectors = ['[class*="address"]', '[data-testid*="address"]', '.address']
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
            
            # Try to extract link/URL
            try:
                link_elem = await element.query_selector('a[href]')
                if link_elem:
                    href = await link_elem.get_attribute('href')
                    if href:
                        data['url'] = href
            except:
                pass
                
            return data if data else None
            
        except Exception as e:
            logger.debug(f"Element extraction failed: {e}")
            return None

    async def scrape_listings(self, where: str = "", what: str = "", when: str = "") -> List[Dict]:
        """Main scraping method"""
        if not self.browser:
            raise RuntimeError("Browser not initialized")
            
        search_url = self.build_search_url(where, what, when)
        logger.info(f"Navigating to: {search_url}")
        
        context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
                "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Upgrade-Insecure-Requests": "1"
            }
        )
        
        page = await context.new_page()
        
        # Set up response interception for multiple API patterns
        await self.intercept_api_calls(page)
        
        try:
            # Navigate with longer timeout and handle potential protection
            await page.goto(search_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
            
            # Wait for potential Incapsula or other protection to clear
            await asyncio.sleep(5)
            
            # Check if we hit protection and try to wait it out
            page_content = await page.content()
            if "incapsula" in page_content.lower() or "incident" in page_content.lower():
                logger.warning("Detected anti-bot protection, waiting longer...")
                await asyncio.sleep(10)
                
                # Try to reload or navigate again
                try:
                    await page.reload(wait_until="domcontentloaded", timeout=self.timeout_ms)
                    await asyncio.sleep(3)
                except:
                    logger.info("Reload failed, continuing with current page state")
            
            # Wait for page to fully load
            await page.wait_for_load_state("networkidle", timeout=20000)
            logger.info(f"Page loaded: {page.url}")
            
            # Try to find and interact with search/listing elements
            try:
                # Wait for potential React/Vue app to initialize
                await asyncio.sleep(5)
                
                # Try different approaches to trigger API calls
                approaches = [
                    # Scroll to trigger lazy loading
                    lambda: page.evaluate("window.scrollTo(0, document.body.scrollHeight)"),
                    # Try to click search or filter buttons
                    lambda: self.try_click_element(page, '[data-testid*="search"]'),
                    lambda: self.try_click_element(page, 'button[class*="search"]'),
                    lambda: self.try_click_element(page, 'button[class*="filter"]'),
                    # Try to trigger map view which often loads listings
                    lambda: self.try_click_element(page, '[data-testid*="map"]'),
                    lambda: self.try_click_element(page, 'button[class*="map"]'),
                ]
                
                for approach in approaches:
                    try:
                        await approach()
                        await asyncio.sleep(2)
                    except Exception as e:
                        logger.debug(f"Approach failed: {e}")
                        
                # Final scroll and wait
                for i in range(3):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.warning(f"Error during page interaction: {e}")
            
            # Save current HTML for debugging
            await self.save_html_fallback(page)
            
            # If no API data captured, try to extract from DOM as fallback
            if not self.captured_data:
                logger.info("No API data captured, attempting DOM extraction...")
                await self.extract_dom_fallback(page)
                
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            try:
                await self.save_html_fallback(page)
            except:
                pass
        finally:
            await context.close()
            
        logger.info(f"Captured {len(self.captured_data)} API responses/listings")
        return self.captured_data
        
    async def try_click_element(self, page: Page, selector: str):
        """Try to click an element if it exists and is visible"""
        try:
            element = await page.query_selector(selector)
            if element and await element.is_visible():
                await element.click()
                logger.debug(f"Clicked element: {selector}")
                return True
        except:
            pass
        return False
        
    async def extract_dom_fallback(self, page: Page):
        """Fallback DOM extraction if API interception fails"""
        try:
            # Look for common listing container patterns
            selectors = [
                '[data-testid*="listing"]',
                '[class*="listing"]',
                '[data-cy*="listing"]',
                '.property-card',
                '.listing-card',
                '[itemtype*="RealEstateListing"]'
            ]
            
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        logger.info(f"Found {len(elements)} elements with selector: {selector}")
                        
                        for element in elements[:20]:  # Limit to avoid timeouts
                            try:
                                # Extract basic listing data
                                listing = await self.extract_listing_data(element)
                                if listing is not None and (listing.get('price') or listing.get('address')):
                                    self.captured_data.append(listing)
                            except Exception as e:
                                logger.debug(f"Failed to extract listing data: {e}")
                        break
                except:
                    continue
                    
        except Exception as e:
            logger.warning(f"DOM fallback extraction failed: {e}")
            
    async def extract_listing_data(self, element) -> Optional[Dict]:
        """Extract listing data from a DOM element"""
        try:
            data = {}
            
            # Try to extract price
            price_selectors = ['[class*="price"]', '[data-testid*="price"]', '.price']
            for sel in price_selectors:
                try:
                    price_elem = await element.query_selector(sel)
                    if price_elem:
                        price_text = await price_elem.inner_text()
                        if price_text and '$' in price_text:
                            data['price'] = price_text.strip()
                            break
                except:
                    continue
                    
            # Try to extract address
            addr_selectors = ['[class*="address"]', '[data-testid*="address"]', '.address']
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
            
            # Try to extract link/URL
            try:
                link_elem = await element.query_selector('a[href]')
                if link_elem:
                    href = await link_elem.get_attribute('href')
                    if href:
                        data['url'] = href
            except:
                pass
                
            return data if data else None
            
        except Exception as e:
            logger.debug(f"Element extraction failed: {e}")
            return None

    async def save_preview(self, data: List[Dict], output_file: str = "logs/preview_realtor.json"):
        """Save captured data as preview JSON"""
        output_path = Path(__file__).parent.parent.parent / output_file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Limit preview to first 50 items for performance
        preview_data = data[:50] if len(data) > 50 else data
        
        with output_path.open('w', encoding='utf-8') as f:
            json.dump({
                "timestamp": asyncio.get_event_loop().time(),
                "total_captured": len(data),
                "preview_count": len(preview_data),
                "data": preview_data
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved preview to: {output_path}")
        return str(output_path)


async def main():
    parser = argparse.ArgumentParser(description="Realtor.ca XHR-based scraper")
    parser.add_argument('--where', default='montreal/lachine', help='Location (e.g., montreal/lachine)')
    parser.add_argument('--what', default='condos-for-sale', help='Property type (e.g., condos-for-sale)')
    parser.add_argument('--when', default='', help='Time filter (optional)')
    parser.add_argument('--headless', action='store_true', default=True, help='Run in headless mode')
    parser.add_argument('--output', default='logs/preview_realtor.json', help='Output JSON file')
    parser.add_argument('--timeout', type=int, default=30000, help='Page timeout in milliseconds')
    
    args = parser.parse_args()
    
    async with RealtorXHRScraper(headless=args.headless, timeout_ms=args.timeout) as scraper:
        listings = await scraper.scrape_listings(args.where, args.what, args.when)
        
        if listings:
            preview_file = await scraper.save_preview(listings, args.output)
            print(f"✅ Scraped {len(listings)} items, preview saved to: {preview_file}")
            return 0
        else:
            print("❌ No listings captured")
            return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
