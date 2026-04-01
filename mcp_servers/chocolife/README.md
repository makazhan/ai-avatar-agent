# Chocolife MCP Server

MCP server for searching restaurant deals and discounts on Chocolife.

## Tool: `search_deals`

Searches for restaurant deals and promotions.

**Parameters:**
- `category` (str, default: "рестораны") — Deal category
- `city` (str, default: "Алматы") — City name

**Returns:** List of dicts with fields:
- `title` — Deal title
- `restaurant_name` — Restaurant name
- `original_price` — Original price (KZT)
- `discount_price` — Discounted price (KZT)
- `discount_percent` — Discount percentage
- `description` — Deal description
- `url` — Link to the deal page

## Running

```bash
# Standalone (stdio transport):
uv run python mcp_servers/chocolife/server.py

# With mocks:
USE_MOCKS=true uv run python mcp_servers/chocolife/server.py
```

## Caching

Results are cached to `.cache/chocolife/` as JSON files with a 24-hour TTL. Repeated queries within the TTL window are served from cache without scraping.

## Scraping

When `USE_MOCKS=false`, uses Playwright with headless Chromium to scrape Chocolife deal listings. Includes a 2-second delay between page loads to avoid rate limiting.
