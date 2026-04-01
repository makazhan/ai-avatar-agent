from mcp.server.fastmcp import FastMCP
import os
import sys
import asyncio
from pathlib import Path

# Allow import of shared cache_utils when run as subprocess
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from mcp_servers.cache_utils import get_cached, set_cache

mcp = FastMCP("twogis")
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
CACHE_DIR = Path(".cache/twogis")


MOCK_DATA = [
    {
        "name": "Del Papa",
        "address": "пр. Достык, 85",
        "rating": 4.5,
        "cuisine": "итальянская",
        "price_range": "$$",
        "working_hours": "10:00-23:00",
        "phone": "+7 727 111-22-33",
    },
    {
        "name": "Бочка",
        "address": "ул. Кабанбай батыра, 42",
        "rating": 4.3,
        "cuisine": "европейская",
        "price_range": "$$",
        "working_hours": "11:00-00:00",
        "phone": "+7 727 222-33-44",
    },
    {
        "name": "Kishlak",
        "address": "ул. Тулебаева, 78",
        "rating": 4.6,
        "cuisine": "узбекская",
        "price_range": "$",
        "working_hours": "09:00-22:00",
        "phone": "+7 727 333-44-55",
    },
    {
        "name": "Grill House",
        "address": "ул. Жандосова, 15",
        "rating": 4.4,
        "cuisine": "грузинская",
        "price_range": "$$",
        "working_hours": "12:00-23:00",
        "phone": "+7 727 444-55-66",
    },
    {
        "name": "Sushi Master",
        "address": "пр. Аль-Фараби, 120",
        "rating": 4.2,
        "cuisine": "японская",
        "price_range": "$$$",
        "working_hours": "11:00-23:00",
        "phone": "+7 727 555-66-77",
    },
]


@mcp.tool()
async def search_restaurants(query: str, location: str = "Алматы") -> list[dict]:
    """Search restaurants in Almaty via 2GIS.
    Returns list with: name, address, rating, cuisine, price_range, working_hours, phone."""
    cache_key = f"{query}:{location}"
    cached = get_cached(CACHE_DIR, cache_key)
    if cached is not None:
        return cached

    if USE_MOCKS:
        # Filter mock data loosely by query keywords
        query_lower = query.lower()
        results = [
            r
            for r in MOCK_DATA
            if query_lower in r["cuisine"].lower()
            or query_lower in r["name"].lower()
        ]
        if not results:
            results = MOCK_DATA[:3]
        set_cache(CACHE_DIR, cache_key, results)
        return results

    from playwright.async_api import async_playwright
    import re

    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
        )
        page = await ctx.new_page()
        await page.add_init_script(
            'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
        )

        search_url = f"https://2gis.kz/almaty/search/{query}"
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        raw = await page.evaluate(
            """() => {
            const results = [];
            const cards = document.querySelectorAll('._1kf6gff');
            for (const card of [...cards].slice(0, 10)) {
                const nameEl = card.querySelector('a._1rehek');
                if (!nameEl) continue;
                const ratingEl = card.querySelector('[class*="_y10azs"]');
                const children = [...card.children];
                const texts = children.map(c => c.textContent.trim()).filter(Boolean);
                results.push({
                    name: nameEl.textContent.trim(),
                    rating: ratingEl ? ratingEl.textContent.trim() : '',
                    texts: texts.slice(0, 5)
                });
            }
            return results;
        }"""
        )

        for item in raw:
            name = item["name"]
            texts = item["texts"]
            # texts[1] = type, texts[2] = "4.9601 оценка", texts[3] = address, texts[4] = cuisine tags
            rating_text = item["rating"]
            try:
                rating = float(rating_text)
            except (ValueError, TypeError):
                rating = 0.0

            address = texts[3].lstrip("\u200b").strip() if len(texts) > 3 else ""
            cuisine_line = texts[4] if len(texts) > 4 else ""
            # Extract price from "Чек XXXX тнг."
            price_match = re.search(r"Чек\s+(\d+)", cuisine_line)
            price_range = f"{price_match.group(1)} тнг." if price_match else ""

            results.append(
                {
                    "name": name,
                    "address": address,
                    "rating": rating,
                    "cuisine": cuisine_line.split("·")[0].strip() if cuisine_line else query,
                    "price_range": price_range,
                    "working_hours": "",
                    "phone": "",
                }
            )

        await browser.close()

    set_cache(CACHE_DIR, cache_key, results)
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
