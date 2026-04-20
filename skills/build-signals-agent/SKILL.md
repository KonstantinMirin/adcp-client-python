---
name: build-signals-agent
description: Use when building an AdCP signals agent, creating an audience data server, or standing up a data provider agent that serves targeting segments to buyers.
---

# Build a Signals Agent (Python)

## Overview

A signals agent serves audience segments to buyers for campaign targeting. Two tools: `get_signals` (discovery) and `activate_signal` (push to DSPs or sales agents). The business model — marketplace vs owned data — shapes every implementation decision. Determine that first.

## When to Use

- User wants to build an agent that serves audience/targeting data
- User mentions signals, segments, audiences, data provider, or CDP in the context of AdCP
- User references `get_signals`, `activate_signal`, or the signals protocol

**Not this skill:**
- Selling ad inventory → `skills/build-seller-agent/`
- Rendering creatives → `skills/build-creative-agent/`
- Building a client that *calls* a signals agent → see client docs

## Before Writing Code

Determine these four things. Ask the user — don't guess.

### 1. Marketplace or Owned?

**Marketplace** — aggregates third-party data providers. Each signal traces to a `data_provider_domain`. `signal_id.source: "catalog"`.

**Owned** — first-party data (retailer CDP, publisher contextual, CRM). `signal_id.source: "agent"`.

**Custom** — agent-native segments built on demand from models, composites, or buyer inputs. `signal_id.source: "agent"`, `signal_type: "custom"`.

### 2. What Segments?

Get specifics: names, definitions, what each represents. Push for 3-5 segments with variety. Each needs:
- Clear behavioral/demographic definition
- Realistic `coverage_percentage` (typically 5-30%)
- Value type: `binary` (in/out), `categorical` (tier levels), or `numeric` (score range)

### 3. Pricing

At least one pricing option per signal:
- `cpm` — `{"pricing_option_id": "po_cpm", "model": "cpm", "cpm": 2.50, "currency": "USD"}`
- `flat_fee` — `{"pricing_option_id": "po_flat", "model": "flat_fee", "amount": 5000, "period": "monthly", "currency": "USD"}`

### 4. Activation Destinations

- **Platform** (DSP): `type: "platform"`, returns `activation_key: {"type": "segment_id", "segment_id": "..."}`
- **Agent** (sales agent): `type: "agent"`, returns `activation_key: {"type": "key_value", "key": "...", "value": "..."}`

## Architecture

One file. Subclass `ADCPHandler`, override the tools you support, call `serve()`.

```python
import os
from adcp.server import ADCPHandler, serve, adcp_error
from adcp.server.responses import capabilities_response, signals_response, activate_signal_response

ADCP_PORT = int(os.environ.get("ADCP_PORT", 3001))
AGENT_URL = f"http://localhost:{ADCP_PORT}/mcp"

class MySignalsAgent(ADCPHandler):
    async def get_adcp_capabilities(self, params, context=None):
        return capabilities_response(["signals"])

    async def get_signals(self, params, context=None):
        return signals_response(MY_SIGNALS)

    async def activate_signal(self, params, context=None):
        # adcp_error() auto-classifies recovery (correctable/transient/terminal)
        segment_id = params.get("signal_agent_segment_id")
        if segment_id not in SIGNALS:
            return adcp_error("SIGNAL_NOT_FOUND", f"Signal {segment_id} not found")
        return activate_signal_response(deployments)

serve(MySignalsAgent(), name="my-signals-agent", port=3001)
```

## Tools and Required Response Shapes

Every tool uses a response builder from `adcp.server.responses`.

**`get_adcp_capabilities`**
```python
from adcp.server.responses import capabilities_response

async def get_adcp_capabilities(self, params, context=None):
    return capabilities_response(["signals"])
```

**`get_signals`** — supports two discovery modes:

1. `signal_spec` — natural language. Match against segment names and descriptions.
2. `signal_ids` — exact lookup by ID.

`get_signals` requires anyOf(`signal_spec`, `signal_ids`) per schema — an empty request is invalid.

If `signal_spec` doesn't match anything specific, return all signals (discovery query).

**Ordering matters when mixing signal types.** When an agent returns both marketplace and owned signals, return marketplace signals first. Storyboard runners and many buyers chain `signals[0]` into follow-up calls (activation, verification) — if `signals[0]` is an owned signal, it lacks `data_provider_domain` and the downstream call fails.

```python
from adcp.server.responses import signals_response

async def get_signals(self, params, context=None):
    results = list(SIGNALS.values())

    # Natural language search — return all if no match (discovery)
    if signal_spec := params.get("signal_spec"):
        words = [w.lower() for w in signal_spec.split() if len(w) > 3]
        matched = [s for s in results if any(
            w in s["name"].lower() or w in s.get("description", "").lower()
            for w in words
        )]
        if matched:
            results = matched

    # Exact ID lookup — key on (source, scope, id) where scope is agent_url
    # for source=agent and data_provider_domain for source=catalog.
    def _signal_key(sid: dict) -> tuple:
        source = sid["source"]
        scope = sid["agent_url"] if source == "agent" else sid.get("data_provider_domain", "")
        return (source, scope, sid["id"])

    if signal_ids := params.get("signal_ids"):
        id_set = {_signal_key(sid) for sid in signal_ids}
        results = [s for s in results if _signal_key(s["signal_id"]) in id_set]

    # CPM filter
    filters = params.get("filters") or {}
    if max_cpm := filters.get("max_cpm"):
        results = [s for s in results if any(
            po.get("model") == "cpm" and po.get("cpm", 999) <= max_cpm
            for po in s.get("pricing_options", [])
        )]

    return signals_response(results)
```

Each signal must include:
```python
{
    "signal_agent_segment_id": "seg-001",       # required — key for activate_signal
    "name": "Frequent Travelers",                # required
    "description": "Users who travel 4+ times/year",  # required
    "signal_type": "owned",                      # required: "marketplace" | "owned" | "custom"
    "data_provider": "My Data Company",          # required
    "coverage_percentage": 18.5,                 # required: 0-100
    "deployments": [],                           # required — empty until activated
    "pricing_options": [{                        # required — at least one
        "pricing_option_id": "po_cpm",
        "model": "cpm",
        "cpm": 2.50,
        "currency": "USD",
    }],
    "signal_id": {                               # required — shape depends on type
        "source": "agent",                       # "agent" for owned, "catalog" for marketplace
        "agent_url": AGENT_URL,                  # for owned
        "id": "seg-001",
    },
    "value_type": "binary",                      # recommended: "binary" | "categorical" | "numeric"
}
```

**`activate_signal`**
```python
import uuid
from datetime import datetime, timezone

from adcp.server import adcp_error
from adcp.server.responses import activate_signal_response

async def activate_signal(self, params, context=None):
    segment_id = params.get("signal_agent_segment_id")
    signal = SIGNALS.get(segment_id)
    if not signal:
        return adcp_error("SIGNAL_NOT_FOUND", f"Signal {segment_id} not found")

    deployments = []
    for dest in params.get("destinations", []):
        if dest.get("type") == "platform":
            deployments.append({
                "type": "platform",
                "platform": dest.get("platform"),
                "account": dest.get("account"),
                "is_live": True,
                "activation_key": {
                    "type": "segment_id",
                    "segment_id": f"plat-{uuid.uuid4().hex[:8]}",
                },
                "deployed_at": datetime.now(timezone.utc).isoformat(),
            })
        elif dest.get("type") == "agent":
            deployments.append({
                "type": "agent",
                "agent_url": dest.get("agent_url"),
                "is_live": True,
                "activation_key": {
                    "type": "key_value",
                    "key": "segment",
                    "value": segment_id,
                },
                "deployed_at": datetime.now(timezone.utc).isoformat(),
            })

    return activate_signal_response(deployments)
```

## SDK Quick Reference

**Response builders** (from `adcp.server.responses`):

| Function | Usage |
|----------|-------|
| `capabilities_response(protocols)` | `get_adcp_capabilities` response |
| `signals_response(signals)` | `get_signals` response |
| `activate_signal_response(deployments)` | `activate_signal` response |

**DX helpers** (from `adcp.server`):

| Function | Usage |
|----------|-------|
| `adcp_error(code, message, field=, suggestion=)` | Structured error with auto-recovery |
| `serve(handler, transport="a2a"\|"streamable-http", port=3001)` | Start MCP or A2A server. Context passthrough is automatic — no need to call `inject_context` in handlers. |

Import helpers from `adcp.server`. Import response builders from `adcp.server.responses`.

## Idempotency for activate_signal

`idempotency_key` is REQUIRED on `activate_signal` per schema (`schemas/cache/signals/activate-signal-request.json`). Use `adcp.server.idempotency.IdempotencyStore` to dedupe replays: same key + same payload returns the cached deployments; different payload returns an `IDEMPOTENCY_CONFLICT` error. Declare the capability so buyers know replays are safe.

```python
from adcp.server.idempotency import IdempotencyStore, MemoryBackend

store = IdempotencyStore(backend=MemoryBackend(), ttl_seconds=86400)  # 24h per spec minimum

async def get_adcp_capabilities(self, params, context=None):
    return capabilities_response(["signals"], idempotency=store.capability())

@store.wrap
async def activate_signal(self, params, context=None):
    # idempotency_key is required; @store.wrap dedups replays per (caller, key).
    # Same key + same payload → cached deployments; different payload → IDEMPOTENCY_CONFLICT.
    return activate_signal_response(deployments=[...])
```

## Governance Tracks (Optional)

Marketplace signals agents with compliance review flows MUST also implement `sync_accounts` and `sync_governance`. The `signal_marketplace/governance_denied` sub-track exercises both — without them, the storyboard fails before it reaches activation. Skip for pure owned-data agents.

```python
from adcp.server.responses import sync_accounts_response, sync_governance_response

async def sync_accounts(self, params, context=None):
    # Echo brand + operator back; assign an account_id, store, return "active".
    # See examples/seller_agent.py for the full shape.
    return sync_accounts_response([...])

async def sync_governance(self, params, context=None):
    # Echo account + governance_agents (url + categories) back as "synced".
    # See examples/seller_agent.py for the full shape.
    return sync_governance_response([...])
```

Required to PASS `signal_marketplace/governance_denied`.

## Validation

```bash
python agent.py &
npx -y -p @adcp/client adcp storyboard run http://localhost:3001/mcp signal_owned --json       # for owned data
npx -y -p @adcp/client adcp storyboard run http://localhost:3001/mcp signal_marketplace --json  # for marketplace
```

**Keep iterating until all steps pass.**

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip `get_adcp_capabilities` | Must be implemented — buyers call it first |
| Return raw dicts without builders | Use `signals_response()` and `activate_signal_response()` |
| `signal_spec` search returns empty for broad queries | Return all signals when no specific match (discovery) |
| Missing `signal_agent_segment_id` | Buyers can't activate without it |
| Wrong `signal_id` shape | Owned: `source: "agent"` + `agent_url`. Marketplace: `source: "catalog"` + `data_provider_domain` |
| Empty `pricing_options` | Must have at least one per signal |
| `is_live: True` in `get_signals` deployments | Signals aren't live until activated — use empty `deployments: []` |
| Activation doesn't match destination type | Platform request → platform deployment. Agent request → agent deployment |

## Reference

This skill contains everything needed to build a 4/4 passing signals agent. The code blocks above are taken from a validated implementation.
