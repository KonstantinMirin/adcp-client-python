---
name: build-creative-agent
description: Use when building an AdCP creative agent — an ad server, creative management platform, or any system that accepts, stores, transforms, and serves ad creatives.
---

# Build a Creative Agent (Python)

## Overview

A creative agent manages the creative lifecycle: accepts assets from buyers, stores them in a library, builds serving tags, and renders previews. Unlike a generative seller (which also sells inventory), a creative agent is a standalone creative platform.

## When to Use

- User wants to build an ad server, creative management platform, or creative rendering service
- User mentions `build_creative`, `preview_creative`, `sync_creatives`, or `list_creatives`
- User references creative formats, VAST tags, serving tags, or creative libraries

**Not this skill:**
- Selling inventory + generating creatives → `skills/build-generative-seller-agent/`
- Selling inventory (no creative management) → `skills/build-seller-agent/`
- Serving audience segments → `skills/build-signals-agent/`

## Before Writing Code

Determine these things. Ask the user — don't guess.

### 1. What kind of creative platform?

- **Ad server** (Innovid, Flashtalking) — stateful library, builds serving tags (VAST, display tags)
- **Creative management platform** (Celtra) — format transformation, template rendering
- **Publisher creative service** — accepts buyer assets, validates against publisher specs

### 2. What formats?

Get specific formats. Each format needs: dimensions, accepted asset types, mime types.
- **Display**: `display_300x250`, `display_728x90`
- **Video**: `video_30s`, `vast_30s`
- **Native**: `native_content` (image + headline + description)

### 3. What operations?

- **Sync** — accept and store creatives (always needed)
- **List** — query the library with filtering (needed for storyboard)
- **Preview** — render a visual preview (needed for storyboard)
- **Build** — produce serving tags from stored creatives (needed for storyboard)

## Architecture

One file. Subclass `ADCPHandler`, override the tools you support, call `serve()`. Use an in-memory dict to store synced creatives.

```python
from adcp.server import ADCPHandler, serve
from adcp.server.helpers import adcp_error
from adcp.server.responses import (
    capabilities_response, creative_formats_response, sync_creatives_response,
    list_creatives_response, preview_creative_response, build_creative_response,
)

creatives: dict[str, dict] = {}  # in-memory creative library

class MyCreativeAgent(ADCPHandler):
    async def get_adcp_capabilities(self, params, context=None):
        return capabilities_response(["creative"])
    # ... implement tools

serve(MyCreativeAgent(), name="my-creative-agent")
```

## Tools and Required Response Shapes

Every tool uses a response builder from `adcp.server.responses`.

**`get_adcp_capabilities`**
```python
from adcp.server.responses import capabilities_response

async def get_adcp_capabilities(self, params, context=None):
    return capabilities_response(["creative"])
```

**`list_creative_formats`**
```python
from adcp.server.responses import creative_formats_response

AGENT_URL = "http://localhost:3001/mcp"

async def list_creative_formats(self, params, context=None):
    return creative_formats_response([
        {
            "format_id": {"agent_url": AGENT_URL, "id": "display_300x250"},
            "name": "Display 300x250",
            "description": "Standard IAB medium rectangle",
            "renders": [{"width": 300, "height": 250}],
            "assets": [{
                "item_type": "individual",
                "asset_id": "image",
                "asset_type": "image",
                "required": True,
                "accepted_media_types": ["image/png", "image/jpeg"],
            }],
        },
        {
            "format_id": {"agent_url": AGENT_URL, "id": "video_30s"},
            "name": "Video 30s Pre-Roll",
            "renders": [{"width": 1920, "height": 1080}],
            "assets": [{
                "item_type": "individual",
                "asset_id": "video",
                "asset_type": "video",
                "required": True,
                "accepted_media_types": ["video/mp4"],
            }],
        },
    ])
```

**`sync_creatives`** — store creatives in the library. Status must be a valid `CreativeStatus`: `processing`, `pending_review`, `approved`, `rejected`, `archived`.
```python
from adcp.server.responses import sync_creatives_response

async def sync_creatives(self, params, context=None):
    results = []
    for c in params.get("creatives", []):
        creative_id = c.get("creative_id", f"c-{uuid.uuid4().hex[:8]}")
        creatives[creative_id] = {**c, "creative_id": creative_id, "status": "approved"}
        results.append({
            "creative_id": creative_id,
            "action": "created",
            "status": "approved",
        })
    return sync_creatives_response(results)
```

**`list_creatives`** — query the library. Must include `pagination` and `query_summary` fields. Status must be a valid `CreativeStatus`.
```python
from datetime import datetime, timezone
from adcp.server.responses import list_creatives_response

async def list_creatives(self, params, context=None):
    results = list(creatives.values())

    # Filter by format_ids if provided
    filters = params.get("filters") or {}
    if format_ids := filters.get("format_ids"):
        format_id_set = {f.get("id", "") if isinstance(f, dict) else str(f) for f in format_ids}
        results = [c for c in results if c.get("format_id", {}).get("id") in format_id_set]

    now = datetime.now(timezone.utc).isoformat()
    serialized = [
        {
            "creative_id": c["creative_id"],
            "name": c.get("name", ""),
            "format_id": c.get("format_id"),
            "status": c.get("status", "approved"),
            "created_date": now,
            "updated_date": now,
        }
        for c in results
    ]
    return list_creatives_response(serialized)
```

**`preview_creative`** — render a preview of a stored creative
```python
from adcp.server.responses import preview_creative_response

async def preview_creative(self, params, context=None):
    creative_id = params.get("creative_id")
    creative = creatives.get(creative_id) if creative_id else None
    format_id = params.get("format_id") or (creative or {}).get("format_id", {})

    return preview_creative_response([{
        "preview_id": f"prev-{uuid.uuid4().hex[:8]}",
        "input": {
            "format_id": format_id,
            "name": (creative or {}).get("name", "Preview"),
            "assets": (creative or {}).get("assets", {}),
        },
        "renders": [{
            "render_id": f"render-{uuid.uuid4().hex[:8]}",
            "output_format": "url",
            "preview_url": f"https://example.com/preview/{creative_id or 'unknown'}.png",
            "role": "primary",
            "dimensions": {"width": 300, "height": 250},
        }],
    }])
```

**`build_creative`** — produce serving tags. The storyboard sends `target_format_id` (not `output_format`). Look up the creative by ID, by format match, or fall back to the first available.
```python
from adcp.server.responses import build_creative_response

async def build_creative(self, params, context=None):
    creative_id = params.get("creative_id")
    creative = creatives.get(creative_id) if creative_id else None

    # Resolve target format
    # target_format_id is canonical per spec; other names are legacy aliases accepted for compatibility.
    target_format = params.get("target_format_id") or params.get("output_format") or params.get("format_id")

    # Find creative by format if not found by ID
    if not creative and target_format:
        target_id = target_format.get("id", "") if isinstance(target_format, dict) else str(target_format)
        for c in creatives.values():
            if c.get("format_id", {}).get("id") == target_id:
                creative = c
                break

    if not creative:
        return adcp_error("CREATIVE_NOT_FOUND", f"No creative found for format {target_format_id}", field="target_format_id")

    format_id = target_format or (creative or {}).get("format_id", {})

    # Build assets dict from stored creative
    stored_assets = (creative or {}).get("assets", [])
    built_assets = {}
    if isinstance(stored_assets, list):
        for asset in stored_assets:
            built_assets[asset.get("asset_id", "unknown")] = asset
    elif isinstance(stored_assets, dict):
        built_assets = stored_assets

    return build_creative_response({
        "format_id": format_id,
        "name": (creative or {}).get("name", "Built Creative"),
        "assets": built_assets,
    })
```

## SDK Quick Reference

| Function | Usage |
|----------|-------|
| `serve(handler, transport="a2a"\|"streamable-http", port=3001)` | Start MCP or A2A server. Context passthrough is automatic. |
| `capabilities_response(protocols)` | `get_adcp_capabilities` response |
| `creative_formats_response(formats)` | `list_creative_formats` response |
| `sync_creatives_response(creatives)` | `sync_creatives` response |
| `list_creatives_response(creatives)` | `list_creatives` response (adds pagination, query_summary) |
| `preview_creative_response(previews)` | `preview_creative` response (adds response_type, expires_at) |
| `build_creative_response(manifest)` | `build_creative` response |

Import handlers from `adcp.server`. Import response builders from `adcp.server.responses`.

## Validation

```bash
python agent.py &
npx -y -p @adcp/client adcp storyboard run http://localhost:3001/mcp creative_lifecycle --json
```

**Keep iterating until all steps pass.**

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip `get_adcp_capabilities` | Must be implemented |
| Return raw dicts without builders | Use response builders for every tool |
| Wrong creative status | Must be `approved`, not `accepted`. Valid: `processing`, `pending_review`, `approved`, `rejected`, `archived` |
| `list_creatives` ignores format filter | Check `filters.format_ids` and filter results |
| `list_creatives` missing pagination/query_summary | Use `list_creatives_response()` which adds them automatically |
| `build_creative` can't find creative | Check `target_format_id` param (not `output_format`), fall back to first available |
| No in-memory store for synced creatives | `list_creatives`, `preview_creative`, `build_creative` need previously synced creatives |

## Reference

This skill contains everything needed to build a 6/6 passing creative agent. The code blocks above are taken from a validated implementation.
