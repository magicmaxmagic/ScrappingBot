from __future__ import annotations

import json
from typing import Any, Dict
import os

import orjson
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


class LLMExtractor:
    def __init__(self, model_path: str | None = None):
        # Lazy import to avoid heavy dep during tests without LLM
        self._model_path = model_path
        self._llm = None

    def _ensure_llm(self):
        if self._llm is None:
            # Default tiny model path can be overridden via env
            path = self._model_path or os.getenv("AI_SCRAPER_LLAMA_MODEL", "./models/llama-tiny.gguf")
            # Lazy import llama-cpp only when needed
            try:
                from llama_cpp import Llama  # type: ignore
            except Exception:
                raise RuntimeError("llama-cpp-python non installé. Utilisez Ollama ou installez requirements-llm.txt.")
            n_ctx = int(os.getenv("AI_SCRAPER_LLAMA_CTX", "2048"))
            n_threads = int(os.getenv("AI_SCRAPER_LLAMA_THREADS", "4"))
            self._llm = Llama(model_path=path, n_ctx=n_ctx, n_threads=n_threads)

    def extract(self, url: str, title: str | None, html: str) -> Listing | None:
        schema = get_extraction_json_schema()
        prompt = LLM_PROMPT_TEMPLATE.format(schema=json.dumps(schema), url=url, title=title or "", html=html[:5000])

        try:
            self._ensure_llm()
            if self._llm is None:
                return None
            out = self._llm(
                prompt,
                max_tokens=int(os.getenv("AI_SCRAPER_LLAMA_MAX_TOKENS", "256")),
                temperature=float(os.getenv("AI_SCRAPER_LLAMA_TEMPERATURE", "0.1")),
                top_p=float(os.getenv("AI_SCRAPER_LLAMA_TOP_P", "0.9")),
                stop=["\n\n"],
            )
            text = (
                out.get("response")
                or (out.get("choices") or [{}])[0].get("text")
                or ""
            )
        except Exception:
            return None

        # Try parse strict JSON
        try:
            data = orjson.loads(text)
        except Exception:
            return None

        # Validate against Pydantic model
        try:
            return Listing.model_validate(data)
        except ValidationError:
            return None
