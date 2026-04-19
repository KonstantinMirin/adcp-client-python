---
name: build-generative-seller-agent
description: Use when building an AdCP generative seller — an AI ad network, generative DSP, or platform that sells inventory AND generates creatives from briefs.
---

# Build a Generative Seller Agent (Python)

## Overview

A generative seller does everything a standard seller does (products, media buys, delivery) plus generates creatives from briefs. The buyer sends a creative brief instead of uploading pre-built assets.

A generative seller that sells programmatic inventory MUST also accept standard IAB formats (display images, VAST tags). The generative capability is additive.

## When to Use

- User wants to build a generative DSP or AI ad network
- User's platform both sells inventory and creates/generates creatives
- User mentions "creative from brief", "AI-generated ads", or "generative"

**Not this skill:**
- Standard seller (no creative generation) → `skills/build-seller-agent/`
- Standalone creative agent → `skills/build-creative-agent/`
- Signals/audience data → `skills/build-signals-agent/`

## Before Writing Code

Same decisions as the seller skill, plus: what generative formats? What brief inputs (name, objective, tone, messaging)? How to handle invalid brand domains?

## Architecture

Start from `examples/seller_agent.py` (the 9/9 passing seller reference), then modify `list_creative_formats` and `sync_creatives` to handle generative formats.

```python
from adcp.server import ADCPHandler, serve
from adcp.server.responses import (
    capabilities_response, products_response, media_buy_response,
    delivery_response, creative_formats_response, sync_creatives_response,
    build_creative_response, preview_creative_response,
)
from adcp.server.test_controller import TestControllerStore

AGENT_URL = "http://localhost:3001/mcp"

class MyGenerativeSeller(ADCPHandler):
    # All seller tools (see seller skill) with modified creative handling
    ...

serve(MyGenerativeSeller(), name="my-gen-seller", port=3001, test_controller=MyStore())
```

## Seller Tools (Required)

Implement all tools from the seller skill. Copy the pattern from `examples/seller_agent.py`:

- `get_adcp_capabilities` → `capabilities_response(["media_buy"])`
- `sync_accounts` → `sync_accounts_response(results)`
- `sync_governance` → `sync_governance_response(results)`
- `get_products` → `products_response(PRODUCTS)`
- `create_media_buy` → `media_buy_response(mb_id, packages)`
- `get_media_buys` → `media_buys_response(buys)`
- `get_media_buy_delivery` → `delivery_response(deliveries, reporting_period=...)`

See `skills/build-seller-agent/SKILL.md` for the exact response shapes of each.

## Generative-Specific Changes

**`list_creative_formats`** — return BOTH generative and standard formats:
```python
from adcp.server.responses import creative_formats_response

async def list_creative_formats(self, params, context=None):
    return creative_formats_response([
        # Generative format — accepts brief input
        {
            "format_id": {"agent_url": AGENT_URL, "id": "display_300x250_generative"},
            "name": "Generated Display 300x250",
            "description": "AI-generated display ad from creative brief",
            "renders": [{"width": 300, "height": 250}],
            "assets": [{
                "item_type": "individual",
                "asset_id": "brief",
                "asset_type": "brief",
                "required": True,
                "description": "Creative brief with messaging and brand guidelines",
            }],
        },
        # Standard format — accepts pre-built assets
        {
            "format_id": {"agent_url": AGENT_URL, "id": "display_300x250"},
            "name": "Display 300x250",
            "renders": [{"width": 300, "height": 250}],
            "assets": [{
                "item_type": "individual",
                "asset_id": "image",
                "asset_type": "image",
                "required": True,
                "accepted_media_types": ["image/jpeg", "image/png"],
            }],
        },
    ])
```

**`sync_creatives`** — handle both brief-based and standard creatives:
```python
from adcp.server.responses import sync_creatives_response

async def sync_creatives(self, params, context=None):
    results = []
    for c in params.get("creatives", []):
        creative_id = c.get("creative_id", f"c-{uuid.uuid4().hex[:8]}")
        format_id = c.get("format_id", {}).get("id", "")

        if "generative" in format_id:
            # Brief-based: async generation, return pending_review
            creatives[creative_id] = {**c, "status": "pending_review"}
            results.append({"creative_id": creative_id, "action": "created", "status": "pending_review"})
        else:
            # Standard upload: immediate approve
            creatives[creative_id] = {**c, "status": "approved"}
            results.append({"creative_id": creative_id, "action": "created", "status": "approved"})

    return sync_creatives_response(results)
```

## Compliance Testing

Same as the seller skill. Copy the `TestControllerStore` from `examples/seller_agent.py`:

```python
serve(MyGenerativeSeller(), name="my-gen-seller", port=3001, test_controller=MyStore())
```

## SDK Quick Reference

All seller response builders apply. The generative delta is in `list_creative_formats` (both generative + standard formats) and `sync_creatives` (check format_id to decide processing path).

| Function | Usage |
|----------|-------|
| `creative_formats_response(formats)` | `list_creative_formats` response |
| `sync_creatives_response(creatives)` | `sync_creatives` response |

## Generative Tools (Required)

`ADCPHandler` advertises `build_creative` and `preview_creative` by default and returns `not_supported` unless you override them. A generative seller MUST implement both, or the storyboard fails at the generation step.

**`build_creative`** — render a creative manifest from a brief. `idempotency_key` is a REQUIRED request field (pattern `^[A-Za-z0-9_.:-]{16,255}$`, see `src/adcp/types/generated_poc/media_buy/build_creative_request.py:157-165`). Use `adcp.server.idempotency.IdempotencyStore` to dedupe retries:

```python
from adcp.server.responses import build_creative_response
from adcp.server.idempotency import IdempotencyStore, MemoryBackend

idempotency = IdempotencyStore(backend=MemoryBackend(), ttl_seconds=86400)

async def build_creative(self, params, context=None):
    key = params["idempotency_key"]  # required by schema
    if cached := await idempotency.get(key):
        return cached
    manifest = {
        "promoted_offering": params.get("promoted_offering"),
        "format_id": params["format_id"],
        "assets": [{"asset_id": "image", "url": "https://cdn.example/generated.jpg"}],
    }
    response = build_creative_response(manifest)
    await idempotency.put(key, response)
    return response
```

**`preview_creative`** — return pre-render previews for a built manifest. Responses wrap a list of `{preview_id, input, renders}`:

```python
from adcp.server.responses import preview_creative_response

async def preview_creative(self, params, context=None):
    return preview_creative_response([{
        "preview_id": f"prev-{uuid.uuid4().hex[:8]}",
        "input": params,
        "renders": [{"width": 300, "height": 250, "url": "https://cdn.example/preview.png"}],
    }])
```

## Validation

```bash
python agent.py &
npx -y -p @adcp/client adcp storyboard run http://localhost:3001/mcp media_buy_generative_seller --json
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Only generative formats, no standard IAB | Must accept pre-built assets too |
| Same handler for brief and standard | Check format_id to decide processing path |
| Skip seller tools | All seller tools are required — start from `examples/seller_agent.py` |
| Wrong `delivery_response` signature | Takes `delivery_response(deliveries_list, reporting_period=...)`, not individual metrics |

## Reference

- `skills/build-seller-agent/SKILL.md` — base seller skill (start there, modify creative handling)
- `skills/build-seller-agent/SKILL.md` — complete seller tool shapes
