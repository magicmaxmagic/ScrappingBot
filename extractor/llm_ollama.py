from __future__ import annotations

import json
import os
from typing import Optional

import requests
from pydantic import ValidationError

from .schema import Listing, get_extraction_json_schema


LLM_PROMPT_TEMPLATE = (
    "You are an information extractor for real estate listings.\n"
    "Return a STRICT JSON object that conforms to the provided JSON Schema.\n"
    "Do not include any extra keys or commentary.\n"
    "If uncertain, set fields to null.\n\n"
    "Schema: {schema}\n\n"
    "Extract from this HTML snippet and metadata:\n"
    "URL: {url}\n"
    "Title: {title}\n"
    "HTML: ```{html}```\n\n"
    "Output only JSON."
)


class OllamaExtractor:
    """
    Minimal extractor using a local Ollama server to avoid building llama-cpp-python.
    Requires `ollama serve` and a pulled model (e.g., `ollama pull llama3.2:3b-instruct`).
    """

    def __init__(
        self,
        model: str = "llama3.2:latest",
        endpoint: str = "http://localhost:11434/api/generate",
        options: Optional[dict] = None,
        timeout: int = 60,
    ):
        # Allow override via environment for easy tuning
        self.model = os.getenv("AI_SCRAPER_OLLAMA_MODEL", model)
        self.endpoint = os.getenv("AI_SCRAPER_OLLAMA_ENDPOINT", endpoint)
        # Low-RAM friendly defaults; can be overridden via options param
        self.options = {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_ctx": 1024,
            "num_predict": 128,
        }
        if options:
            self.options.update(options)
        # Merge environment overrides for options
        def _env_int(name: str) -> Optional[int]:
            v = os.getenv(name)
            if v is None:
                return None
            try:
                return int(v)
            except ValueError:
                return None

        def _env_float(name: str) -> Optional[float]:
            v = os.getenv(name)
            if v is None:
                return None
            try:
                return float(v)
            except ValueError:
                return None

        num_ctx = _env_int("AI_SCRAPER_OLLAMA_NUM_CTX")
        if num_ctx:
            self.options["num_ctx"] = num_ctx
        num_predict = _env_int("AI_SCRAPER_OLLAMA_NUM_PREDICT")
        if num_predict:
            self.options["num_predict"] = num_predict
        temperature = _env_float("AI_SCRAPER_OLLAMA_TEMPERATURE")
        if temperature is not None:
            self.options["temperature"] = temperature
        top_p = _env_float("AI_SCRAPER_OLLAMA_TOP_P")
        if top_p is not None:
            self.options["top_p"] = top_p

        self.timeout = int(os.getenv("AI_SCRAPER_OLLAMA_TIMEOUT", str(timeout)))

    def extract(self, url: str, title: Optional[str], html: str) -> Optional[Listing]:
        schema = get_extraction_json_schema()
        prompt = LLM_PROMPT_TEMPLATE.format(schema=json.dumps(schema), url=url, title=title or "", html=html[:5000])
        try:
            resp = requests.post(
                self.endpoint,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False,
                    "options": self.options,
                    "keep_alive": "5m",
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data.get("response") or data.get("choices", [{}])[0].get("text")
            if not text:
                return None
            obj = json.loads(text)
            return Listing.model_validate(obj)
        except (requests.RequestException, json.JSONDecodeError, ValidationError, Exception):
            return None
