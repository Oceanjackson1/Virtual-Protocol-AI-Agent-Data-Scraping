"""
Phase 1: API endpoint discovery via Playwright network interception.
Opens the ACP scan page and agent detail page, captures all API calls.
"""

import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright, Response

API_PATTERNS = re.compile(
    r"(api|graphql|agents|leaderboard|agdp|metrics|scan|acp|claw)", re.IGNORECASE
)
SKIP_EXTENSIONS = re.compile(r"\.(js|css|png|jpg|jpeg|gif|svg|ico|woff2?|ttf|eot|map)(\?|$)")


async def capture_api_calls(url: str, label: str, timeout_ms: int = 30000):
    """Visit a URL and capture all API-like network responses."""
    captured = []

    async def on_response(response: Response):
        req_url = response.url
        if SKIP_EXTENSIONS.search(req_url):
            return
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type and "graphql" not in req_url:
            return
        try:
            body = await response.json()
        except Exception:
            body = "(failed to parse)"
        captured.append({
            "url": req_url,
            "method": response.request.method,
            "status": response.status,
            "content_type": content_type,
            "body_preview": json.dumps(body, ensure_ascii=False)[:2000] if isinstance(body, (dict, list)) else str(body)[:500],
        })

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.on("response", on_response)

        print(f"\n[{label}] Loading {url} ...")
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout_ms)
            await page.wait_for_timeout(5000)
        except Exception as e:
            print(f"  Warning: page load issue - {e}")

        await browser.close()

    return captured


async def discover():
    """Discover API endpoints from scan and agent-detail pages."""
    print("=" * 70)
    print("Virtuals ACP - API Endpoint Discovery")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 70)

    scan_apis = await capture_api_calls(
        "https://app.virtuals.io/acp/scan", "SCAN PAGE", timeout_ms=45000
    )
    detail_apis = await capture_api_calls(
        "https://app.virtuals.io/acp/agent-details/84", "AGENT DETAIL", timeout_ms=45000
    )

    all_results = {"scan_page": scan_apis, "agent_detail_page": detail_apis}

    print("\n" + "=" * 70)
    print(f"SCAN PAGE: captured {len(scan_apis)} API calls")
    print("=" * 70)
    for i, api in enumerate(scan_apis, 1):
        print(f"\n--- [{i}] {api['method']} {api['status']} ---")
        print(f"URL: {api['url']}")
        print(f"Type: {api['content_type']}")
        print(f"Body: {api['body_preview'][:500]}")

    print("\n" + "=" * 70)
    print(f"AGENT DETAIL PAGE: captured {len(detail_apis)} API calls")
    print("=" * 70)
    for i, api in enumerate(detail_apis, 1):
        print(f"\n--- [{i}] {api['method']} {api['status']} ---")
        print(f"URL: {api['url']}")
        print(f"Type: {api['content_type']}")
        print(f"Body: {api['body_preview'][:500]}")

    out_path = "output/api_discovery.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\nFull results saved to {out_path}")

    return all_results


if __name__ == "__main__":
    asyncio.run(discover())
