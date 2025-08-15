"""
LLM-based extraction using Ollama for the ETL pipeline.
Provides intelligent data extraction from HTML content.
"""

import json
import logging
import requests
from typing import Optional, Dict, Any
from datetime import datetime

from .schema import Listing, validate_listing


logger = logging.getLogger(__name__)


class OllamaExtractor:
    """
    LLM-based extractor using Ollama for intelligent data extraction.
    """
    
    def __init__(
        self, 
        base_url: str = "http://localhost:11434",
        model: str = "llama2",
        timeout: int = 30
    ):
        """
        Initialize the Ollama extractor.
        
        Args:
            base_url: Ollama API base URL
            model: LLM model to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.session = requests.Session()
    
    def extract(
        self, 
        url: str, 
        title: Optional[str] = None, 
        html: Optional[str] = None
    ) -> Optional[Listing]:
        """
        Extract structured data from HTML using LLM.
        
        Args:
            url: Source URL
            title: Page title (optional)
            html: HTML content to extract from
            
        Returns:
            Validated Listing object or None if extraction fails
        """
        if not html:
            logger.warning(f"No HTML content provided for URL: {url}")
            return None
        
        try:
            # Prepare extraction prompt
            prompt = self._build_extraction_prompt(url, title, html)
            
            # Call Ollama API
            response = self._call_ollama(prompt)
            if not response:
                return None
            
            # Parse JSON response
            extracted_data = self._parse_response(response)
            if not extracted_data:
                return None
            
            # Add metadata
            extracted_data.update({
                'url': url,
                'source': 'ollama_extraction',
                'scraped_at': datetime.now(),
            })
            
            if title:
                extracted_data['title'] = title
            
            # Validate and return
            return validate_listing(extracted_data)
        
        except Exception as e:
            logger.error(f"LLM extraction failed for {url}: {e}")
            return None
    
    def _build_extraction_prompt(
        self, 
        url: str, 
        title: Optional[str], 
        html: str
    ) -> str:
        """
        Build extraction prompt for the LLM.
        
        Args:
            url: Source URL
            title: Page title
            html: HTML content
            
        Returns:
            Formatted prompt string
        """
        # Truncate HTML to avoid token limits
        html_snippet = html[:8000] if len(html) > 8000 else html
        
        prompt = f"""
Extract real estate listing information from the following HTML content and return it as valid JSON.

URL: {url}
Title: {title or 'N/A'}

HTML Content:
{html_snippet}

Extract the following information and return as JSON:
{{
    "title": "string - property title",
    "description": "string - property description", 
    "property_type": "string - apartment, house, etc.",
    "price": "number - price value only",
    "currency": "string - EUR, USD, etc.",
    "area": "number - area value only",
    "area_unit": "string - sqm, sqft, etc.",
    "address": "string - full address",
    "city": "string - city name",
    "postal_code": "string - postal code",
    "rooms": "number - total rooms",
    "bedrooms": "number - bedrooms",
    "bathrooms": "number - bathrooms",
    "floor": "number - floor number",
    "balcony": "boolean - has balcony",
    "parking": "boolean - has parking",
    "garden": "boolean - has garden",
    "elevator": "boolean - has elevator"
}}

Rules:
- Return only valid JSON, no other text
- Use null for missing values
- Extract numbers without currency symbols or units
- Be conservative - if unsure, use null
- Focus on key information: price, area, location, rooms

JSON:
"""
        return prompt
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """
        Call Ollama API with the extraction prompt.
        
        Args:
            prompt: Formatted prompt
            
        Returns:
            LLM response text or None if call fails
        """
        try:
            url = f"{self.base_url}/api/generate"
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Low temperature for consistent extraction
                    "top_p": 0.9,
                    "num_predict": 1000,  # Limit response length
                }
            }
            
            response = self.session.post(
                url, 
                json=payload, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response')
        
        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            return None
    
    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM response to extract JSON data.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed data dictionary or None if parsing fails
        """
        try:
            # Try to find JSON in response
            response = response.strip()
            
            # Look for JSON block
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            
            # Try parsing entire response as JSON
            return json.loads(response)
        
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error parsing LLM response: {e}")
            return None
    
    def is_available(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if service is responding
        """
        try:
            url = f"{self.base_url}/api/tags"
            response = self.session.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


# Alias for backward compatibility
Ollama = OllamaExtractor
