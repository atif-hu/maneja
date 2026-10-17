# Smoke-test helper: verify API health (no auth)
# Usage: python scripts/smoke_health.py

from __future__ import annotations

import os
import sys
import urllib.request

API = os.environ.get("NEXT_PUBLIC_API_URL") or os.environ.get("API_BASE_URL") or "http://localhost:8000"


def main() -> int:
    url = f"{API.rstrip('/')}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode()
            print(resp.status, body)
            return 0 if resp.status == 200 else 1
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
