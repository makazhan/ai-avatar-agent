# ABR Group MCP Server

MCP server for getting menu, booking, and location info about ABR Group restaurants — Kazakhstan's largest restaurant company (Del Papa, Бочонок, Дареджани, Cafeteria, Broadway Burger, AUYL, SPIROS, etc.).

## Tool: `get_abr_restaurants`

Gets detailed restaurant information from ABR Group's website.

**When to use:** User asks about menus, prices, or booking at a specific ABR restaurant. For general restaurant discovery use `search_restaurants` (2GIS), for deals use `search_deals` (Chocolife).

**Parameters:**
- `name` (str, default: "") — Restaurant name filter. If empty, returns all ABR restaurants.

**Returns:** List of dicts with fields:
- `name` — Restaurant concept name
- `cuisine` — Description / cuisine type
- `city` — Cities where the restaurant operates
- `addresses` — List of location addresses
- `phones` — List of phone numbers
- `working_hours` — Operating hours
- `menu_url` — Link to menu PDF
- `booking_url` — Link to restaurant page on abr.kz

## Running

```bash
# Standalone (stdio transport):
uv run python mcp_servers/abr_group/server.py

# With mocks:
USE_MOCKS=true uv run python mcp_servers/abr_group/server.py
```

## Caching

Results are cached to `.cache/abr_group/` as JSON files with a 24-hour TTL. Repeated queries within the TTL window are served from cache without hitting abr.kz.

## Scraping

When `USE_MOCKS=false`, uses Playwright with headless Chromium to:
1. Scrape the listing page (`/restaurants/`) for all restaurant names and detail URLs
2. Visit each detail page to extract addresses, phones, hours, menu PDF, and description
3. Cache the combined result

Includes 1-second delays between page loads to be respectful to the server.
