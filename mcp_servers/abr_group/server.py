from mcp.server.fastmcp import FastMCP
import logging
import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from mcp_servers.cache_utils import get_cached, set_cache

log = logging.getLogger(__name__)

mcp = FastMCP("abr_group")
USE_MOCKS = os.getenv("USE_MOCKS", "true").lower() == "true"
CACHE_DIR = Path(".cache/abr_group")


def _make_entry(
    name: str,
    cuisine: str = "",
    city: str = "Алматы",
    addresses: list[str] | None = None,
    menu_highlights: list[str] | None = None,
    average_check: str = "",
    working_hours: str = "",
    phones: list[str] | None = None,
    menu_url: str = "",
    booking_url: str = "",
) -> dict:
    """Build a restaurant entry with consistent shape for both mock and real data."""
    return {
        "name": name,
        "cuisine": cuisine,
        "city": city,
        "addresses": addresses or [],
        "menu_highlights": menu_highlights or [],
        "average_check": average_check,
        "working_hours": working_hours,
        "phones": phones or [],
        "menu_url": menu_url,
        "booking_url": booking_url,
    }


MOCK_DATA = [
    _make_entry(
        "Del Papa",
        cuisine="итальянская",
        addresses=["пр. Достык, 85", "ул. Панфилова, 100"],
        menu_highlights=["Паста карбонара", "Пицца маргарита", "Тирамису"],
        average_check="8000-12000 тнг.",
        booking_url="https://abr.kz/restaurant/del-papa",
    ),
    _make_entry(
        "Бочонок",
        cuisine="европейская, пивной ресторан",
        addresses=["ул. Кабанбай батыра, 42", "пр. Достык, 340"],
        menu_highlights=["Свиная рулька", "Колбаски на гриле", "Чешское пиво"],
        average_check="6000-10000 тнг.",
        booking_url="https://abr.kz/restaurant/bochonok",
    ),
    _make_entry(
        "Дареджани",
        cuisine="грузинская",
        addresses=["ул. Курмангазы, 61"],
        menu_highlights=["Хинкали", "Хачапури по-аджарски", "Шашлык"],
        average_check="7000-11000 тнг.",
        booking_url="https://abr.kz/restaurant/daredzhani",
    ),
    _make_entry(
        "Cafeteria",
        cuisine="европейская, кафе",
        addresses=["пр. Достык, 210"],
        menu_highlights=["Завтраки весь день", "Сэндвичи", "Десерты"],
        average_check="4000-7000 тнг.",
        booking_url="https://abr.kz/restaurant/cafeteria",
    ),
    _make_entry(
        "Broadway Burger",
        cuisine="бургерная, американская",
        addresses=["пр. Аль-Фараби, 77/8"],
        menu_highlights=["Классик бургер", "Чизбургер", "Картофель фри"],
        average_check="3500-6000 тнг.",
        booking_url="https://abr.kz/restaurant/broadway-burger",
    ),
]


def _filter_by_name(data: list[dict], name: str) -> list[dict]:
    if not name:
        return data
    name_lower = name.lower()
    return [r for r in data if name_lower in r["name"].lower()] or data


@mcp.tool()
async def get_abr_restaurants(name: str = "") -> list[dict]:
    """Get menu, average check, and booking info for ABR Group restaurants
    (Del Papa, Бочонок, Дареджани, Cafeteria, Broadway Burger, etc.).
    Use this when user asks about menus, prices, or booking at a specific ABR restaurant.
    Use search_restaurants for general discovery/location, search_deals for discounts.
    If name is provided, filters to that restaurant. If empty, returns all.
    Returns: name, cuisine, city, addresses, menu_highlights, average_check, booking_url."""
    cache_key = f"abr:{name}"
    cached = get_cached(CACHE_DIR, cache_key)
    if cached is not None:
        return cached

    if USE_MOCKS:
        results = _filter_by_name(MOCK_DATA, name)
        set_cache(CACHE_DIR, cache_key, results)
        return results

    from playwright.async_api import async_playwright

    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(locale="ru-RU")
        page = await ctx.new_page()

        await page.goto(
            "https://abr.kz/restaurants/",
            wait_until="networkidle",
            timeout=30000,
        )
        await asyncio.sleep(2)

        listing = await page.evaluate(
            """() => {
            const items = [];
            const cards = document.querySelectorAll('a.item-list-wrap');
            for (const card of cards) {
                const titleEl = card.querySelector('.item-title');
                if (!titleEl) continue;
                items.push({
                    name: titleEl.textContent.trim(),
                    url: card.href
                });
            }
            return items;
        }"""
        )

        # Filter listing before visiting detail pages to avoid unnecessary scraping
        if name:
            name_lower = name.lower()
            filtered = [i for i in listing if name_lower in i["name"].lower()]
            if filtered:
                listing = filtered

        for item in listing:
            await asyncio.sleep(1)
            try:
                await page.goto(
                    item["url"],
                    wait_until="networkidle",
                    timeout=20000,
                )
                await asyncio.sleep(1)

                detail = await page.evaluate(
                    """() => {
                    const desc = document.querySelector('.item-desc');
                    const menuBtn = document.querySelector('a.btn.btn-hollow');
                    const addrEls = document.querySelectorAll('.restaurants-city-list .item-title');
                    const addresses = [...addrEls].map(el => el.textContent.trim());
                    const hoursEls = document.querySelectorAll('.item-col-desc');
                    const hours = [];
                    for (const h of hoursEls) {
                        const text = h.textContent.trim();
                        if (text.includes(':')) hours.push(text);
                    }
                    const phoneEls = document.querySelectorAll('a.item-col-link');
                    const phones = [];
                    for (const ph of phoneEls) {
                        const text = ph.textContent.trim();
                        if (text.startsWith('+')) phones.push(text);
                    }
                    const cityEls = document.querySelectorAll('.nav-tabs a');
                    const cities = [...cityEls].map(c => c.textContent.trim()).filter(Boolean);
                    return {
                        description: desc ? desc.textContent.trim() : '',
                        menuUrl: menuBtn ? menuBtn.href : '',
                        addresses, hours: hours[0] || '', phones, cities
                    };
                }"""
                )

                results.append(
                    _make_entry(
                        name=item["name"],
                        cuisine=detail.get("description", ""),
                        city=", ".join(detail.get("cities", [])) or "Алматы",
                        addresses=detail.get("addresses", []),
                        working_hours=detail.get("hours", ""),
                        phones=detail.get("phones", []),
                        menu_url=detail.get("menuUrl", ""),
                        booking_url=item["url"],
                    )
                )
            except Exception:
                log.warning("Failed to scrape %s (%s)", item["name"], item["url"], exc_info=True)
                results.append(
                    _make_entry(name=item["name"], booking_url=item["url"])
                )

        await browser.close()

    set_cache(CACHE_DIR, cache_key, results)
    return results


if __name__ == "__main__":
    mcp.run(transport="stdio")
