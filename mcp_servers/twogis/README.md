# 2GIS MCP Server

MCP server for searching restaurants in Almaty via 2GIS.

## Tool: `search_restaurants`

Searches restaurants by query string and location.

**Parameters:**
- `query` (str, required) — Search query (e.g. "итальянский ресторан", "суши")
- `location` (str, default: "Алматы") — City name

**Returns:** List of dicts with fields:
- `name` — Restaurant name
- `address` — Street address
- `rating` — Numeric rating (0-5)
- `cuisine` — Cuisine type
- `price_range` — Price tier ($, $$, $$$)
- `working_hours` — Operating hours
- `phone` — Contact phone

## Running

```bash
# Standalone (stdio transport):
uv run python mcp_servers/twogis/server.py

# With mocks:
USE_MOCKS=true uv run python mcp_servers/twogis/server.py
```

## Caching

Results are cached to `.cache/twogis/` as JSON files with a 24-hour TTL. Repeated queries within the TTL window are served from cache without hitting 2GIS.

## Scraping

When `USE_MOCKS=false`, uses Playwright with headless Chromium to scrape 2GIS search results. Includes a 2-second delay between page loads to avoid rate limiting.
