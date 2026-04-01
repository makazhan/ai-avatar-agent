from mcp.server.fastmcp import FastMCP
import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from mcp_servers.cache_utils import get_cached, set_cache

mcp = FastMCP("chocolife")
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
CACHE_DIR = Path(".cache/chocolife")


MOCK_DATA = [
    {
        "title": "Ужин на двоих в Del Papa",
        "restaurant_name": "Del Papa",
        "original_price": 15000,
        "discount_price": 9000,
        "discount_percent": 40,
        "description": "Два основных блюда + десерт + напитки",
        "url": "https://chocolife.me/almaty/deal/12345",
    },
    {
        "title": "Бизнес-ланч в Бочке",
        "restaurant_name": "Бочка",
        "original_price": 5000,
        "discount_price": 3500,
        "discount_percent": 30,
        "description": "Салат + суп + горячее + напиток",
        "url": "https://chocolife.me/almaty/deal/67890",
    },
    {
        "title": "Романтический ужин в Olive Garden",
        "restaurant_name": "Olive Garden",
        "original_price": 20000,
        "discount_price": 12000,
        "discount_percent": 40,
        "description": "Два стейка + вино + десерт",
        "url": "https://chocolife.me/almaty/deal/11111",
    },
    {
        "title": "Суши-сет на компанию в Sushi Master",
        "restaurant_name": "Sushi Master",
        "original_price": 12000,
        "discount_price": 7200,
        "discount_percent": 40,
        "description": "48 роллов + мисо-суп + напитки",
        "url": "https://chocolife.me/almaty/deal/22222",
    },
]


@mcp.tool()
async def search_deals(
    category: str = "рестораны", city: str = "Алматы"
) -> list[dict]:
    """Search restaurant deals on Chocolife.
    Returns list with: title, restaurant_name, original_price, discount_price, discount_percent, description, url."""
    cache_key = f"{category}:{city}"
    cached = get_cached(CACHE_DIR, cache_key)
    if cached is not None:
        return cached

    if USE_MOCKS:
        set_cache(CACHE_DIR, cache_key, MOCK_DATA)
        return MOCK_DATA

    from playwright.async_api import async_playwright
    import re

    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="ru-RU")
        page = await ctx.new_page()
        await page.goto(
            "https://chocolife.me/restorany-kafe-i-bary/",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(5)

        raw = await page.evaluate(
            """() => {
            const results = [];
            const cards = document.querySelectorAll('div.deal');
            for (const card of [...cards].slice(0, 10)) {
                const titleEl = card.querySelector('h3.deal__title');
                const percentEl = card.querySelector('.deal__percent');
                const priceEl = card.querySelector('.deal__price');
                const reviewEl = card.querySelector('.deal__review');
                const linkEl = card.querySelector('a[href]');
                const infoDiv = card.querySelector('.deal__info');
                let bizName = '';
                if (infoDiv) {
                    const spans = infoDiv.querySelectorAll('span');
                    for (const s of spans) {
                        const t = s.textContent?.trim();
                        if (t && !t.startsWith('·') && t.length > 2 && t.length < 60 && !s.className) {
                            bizName = t;
                            break;
                        }
                    }
                }
                results.push({
                    title: titleEl ? titleEl.textContent.trim() : '',
                    discount: percentEl ? percentEl.textContent.trim() : '',
                    price: priceEl ? priceEl.textContent.trim() : '',
                    rating: reviewEl ? reviewEl.textContent.trim() : '',
                    name: bizName,
                    url: linkEl ? linkEl.href : ''
                });
            }
            return results;
        }"""
        )

        def parse_price(text: str) -> int:
            digits = "".join(c for c in text if c.isdigit())
            return int(digits) if digits else 0

        for item in raw:
            discount_text = item["discount"]  # e.g. "до -40%" or "-30%"
            discount_match = re.search(r"(\d+)", discount_text)
            discount_percent = int(discount_match.group(1)) if discount_match else 0

            discount_price = parse_price(item["price"])
            original_price = (
                int(discount_price * 100 / (100 - discount_percent))
                if discount_percent and discount_price
                else 0
            )

            results.append(
                {
                    "title": item["title"],
                    "restaurant_name": item["name"] or item["title"],
                    "original_price": original_price,
                    "discount_price": discount_price,
                    "discount_percent": discount_percent,
                    "description": item["title"],
                    "url": item["url"],
                }
            )

        await browser.close()

    set_cache(CACHE_DIR, cache_key, results)
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
