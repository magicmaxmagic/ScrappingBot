from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Iterable

import orjson

# Cloudflare D1 loader using wrangler CLI. Assumes a binding name and database configured.
# We'll generate SQL with INSERT OR REPLACE to upsert by primary key id.


def generate_upsert_sql(records: Iterable[dict]) -> str:
    stmts = [
        "BEGIN TRANSACTION;",
    ]
    for r in records:
        cols = [
            "id",
            "kind",
            "price",
            "currency",
            "url",
            "title",
            "address",
            "area_sqm",
            "rooms",
            "latitude",
            "longitude",
            "neighborhood",
            "site_domain",
            "raw_html_path",
            "extracted_at",
        ]
        vals = [r.get(c) for c in cols]
        # Escape values for SQL (very simple)
        esc = []
        for v in vals:
            if v is None:
                esc.append("NULL")
            elif isinstance(v, (int, float)):
                esc.append(str(v))
            else:
                s = str(v).replace("'", "''")
                esc.append(f"'{s}'")
        stmts.append(
            f"INSERT OR REPLACE INTO listings ({', '.join(cols)}) VALUES ({', '.join(esc)});"
        )
    stmts.append("COMMIT;")
    return "\n".join(stmts)


def upload_to_d1(sql: str, wrangler_d1_db: str, wrangler_profile: str | None = None) -> int:
    # Use wrangler d1 execute --file -
    env = os.environ.copy()
    args = ["wrangler", "d1", "execute", wrangler_d1_db, "--command", sql]
    if wrangler_profile:
        args += ["--profile", wrangler_profile]
    proc = subprocess.run(args, capture_output=True, text=True)
    return proc.returncode
