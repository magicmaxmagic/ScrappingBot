from __future__ import annotations

import hashlib
from typing import Iterable, List, Tuple

# Simple SimHash implementation for near-duplicate text

def _tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"\w+", (text or "").lower()) if t]


import re


def simhash(text: str, bits: int = 64) -> int:
    v = [0] * bits
    for tok in _tokenize(text):
        h = int(hashlib.sha1(tok.encode()).hexdigest(), 16)
        for i in range(bits):
            v[i] += 1 if (h >> i) & 1 else -1
    fp = 0
    for i in range(bits):
        if v[i] >= 0:
            fp |= 1 << i
    return fp


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def canonical_id(url: str, price: float | None, area_sqm: float | None) -> str:
    base = f"{url}|{price or ''}|{area_sqm or ''}"
    return hashlib.sha1(base.encode()).hexdigest()


def dedupe_records(records: Iterable[dict], simhash_threshold: int = 3) -> List[dict]:
    seen_ids: set[str] = set()
    seen_text_fp: List[Tuple[int, str]] = []  # (fp, id)
    out: List[dict] = []

    for r in records:
        cid = canonical_id(r.get("url", ""), r.get("price"), r.get("area_sqm"))
        if cid in seen_ids:
            continue
        text = " ".join(
            str(r.get(k, "")) for k in ["title", "address", "site_domain"]
        )
        fp = simhash(text)
        is_dup = any(hamming(fp, prev_fp) <= simhash_threshold for prev_fp, _ in seen_text_fp)
        if is_dup:
            continue
        seen_ids.add(cid)
        seen_text_fp.append((fp, cid))
        r["id"] = cid
        out.append(r)

    return out
