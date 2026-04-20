---
name: build-retail-media-agent
description: Use when building an AdCP retail media network agent — a platform that sells on-site placements, supports product catalogs, tracks conversions, and reports performance.
---

# Build a Retail Media Agent (Python)

## Overview

A retail media agent sells advertising on a retailer's properties (sponsored products, homepage banners, search results). It extends the standard seller with catalog sync, event tracking, and performance feedback.

## When to Use

- User wants to build a retail media network, commerce media platform, or sponsored products agent
- User mentions catalogs, product feeds, conversion tracking, or performance feedback

**Not this skill:**
- Standard seller without catalogs → `skills/build-seller-agent/`
- Generative seller → `skills/build-generative-seller-agent/`
- Signals/audience data → `skills/build-signals-agent/`

## Before Writing Code

Same decisions as the seller skill, plus: what catalogs does the platform accept? What conversion events? Does the buyer send performance metrics back?

## Architecture

Start from `examples/seller_agent.py` (the 9/9 passing seller reference), then add retail-specific tools. Same pattern: subclass `ADCPHandler`, use response builders, call `serve()`.

```python
from adcp.server import ADCPHandler, serve
from adcp.server.responses import (
    capabilities_response, products_response, media_buy_response,
    delivery_response, sync_accounts_response, sync_governance_response,
    creative_formats_response, sync_creatives_response, media_buys_response,
    sync_catalogs_response, log_event_response,
)
from adcp.server.test_controller import TestControllerStore

class MyRetailAgent(ADCPHandler):
    # All seller tools (see seller skill) PLUS retail-specific tools below
    ...

serve(MyRetailAgent(), name="my-retail-agent", test_controller=MyStore())
```

## Seller Tools (Required)

Implement all tools from the seller skill. Copy the pattern from `examples/seller_agent.py`:

- `get_adcp_capabilities` → `capabilities_response(["media_buy"])`
- `sync_accounts` → `sync_accounts_response(results)`
- `sync_governance` → `sync_governance_response(results)`
- `get_products` → `products_response(PRODUCTS)`
- `create_media_buy` → `media_buy_response(mb_id, packages)`
- `get_media_buys` → `media_buys_response(buys)`
- `list_creative_formats` → `creative_formats_response(formats)`
- `sync_creatives` → `sync_creatives_response(results)`
- `get_media_buy_delivery` → `delivery_response(deliveries, reporting_period=...)`

See `skills/build-seller-agent/SKILL.md` for the exact response shapes of each.

If your retail platform supports guaranteed deals with negotiation, also implement the proposal workflow from the seller skill. Refined proposals must include `proposal_id`, `name`, and `allocations[]` with `product_id` + `allocation_percentage` (summing to 100) — see "Proposal Workflow (Guaranteed Deals)" in `skills/build-seller-agent/SKILL.md`.

## Retail-Specific Tools

**`sync_catalogs`** — accept product catalog feeds
```python
from adcp.server.responses import sync_catalogs_response

async def sync_catalogs(self, params, context=None):
    results = []
    for cat in params.get("catalogs", []):
        catalog_id = cat.get("catalog_id", f"cat-{uuid.uuid4().hex[:8]}")
        items = cat.get("items", [])
        catalogs[catalog_id] = cat
        results.append({
            "catalog_id": catalog_id,
            "action": "created",
            "item_count": len(items),
            "items_approved": len(items),
        })
    return sync_catalogs_response(results)
```

**`log_event`** — accept conversion events
```python
from adcp.server.responses import log_event_response

async def log_event(self, params, context=None):
    events = params.get("events", [])
    return log_event_response(events_received=len(events), events_processed=len(events))
```

**`provide_performance_feedback`** — accept buyer metrics
```python
async def provide_performance_feedback(self, params, context=None):
    # Return shape varies by success/error — consult `ProvidePerformanceFeedbackResponse` in `adcp.types`.
    return {"success": True, "sandbox": True}
```

**`sync_event_sources`** — register event tracking
```python
async def sync_event_sources(self, params, context=None):
    results = []
    for src in params.get("event_sources", []):
        results.append({
            "event_source_id": src.get("event_source_id", f"es-{uuid.uuid4().hex[:8]}"),
            "action": "created",
        })
    return {"event_sources": results, "sandbox": True}
```

## Compliance Testing

Same as the seller skill. Copy the `TestControllerStore` from `examples/seller_agent.py` and pass to `serve()`:

```python
serve(MyRetailAgent(), name="my-retail-agent", test_controller=MyStore())
```

## SDK Quick Reference

All seller response builders apply, plus:

| Function | Usage |
|----------|-------|
| `sync_catalogs_response(catalogs)` | `sync_catalogs` response |
| `log_event_response(received, processed)` | `log_event` response |

## Validation

```bash
python agent.py &
npx -y -p @adcp/client adcp storyboard run http://localhost:3001/mcp media_buy_seller --json
npx -y -p @adcp/client adcp storyboard run http://localhost:3001/mcp media_buy_catalog_creative --json
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip seller tools | All seller tools are required — start from `examples/seller_agent.py` |
| `sync_catalogs` missing `item_count` | Required field |
| `log_event` missing `events_received`/`events_processed` | Use `log_event_response()` |
| Wrong `delivery_response` signature | Takes `delivery_response(deliveries_list, reporting_period=...)`, not individual metrics |

## Reference

- `skills/build-seller-agent/SKILL.md` — base seller skill (start there, add retail tools)
- `skills/build-seller-agent/SKILL.md` — complete seller tool shapes
