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
from adcp.server import ADCPHandler, serve, adcp_error
from adcp.server.responses import capabilities_response, signals_response, activate_signal_response

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

serve(MySignalsAgent(), name="my-signals-agent")
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

If `signal_spec` doesn't match anything specific, return all signals (discovery query).

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

    # Exact ID lookup
    if signal_ids := params.get("signal_ids"):
        id_set = {sid.get("id") or sid for sid in signal_ids}
        results = [s for s in results if s["signal_id"]["id"] in id_set]

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
        "agent_url": "http://localhost:3001/mcp", # for owned
        "id": "seg-001",
    },
    "value_type": "binary",                      # recommended: "binary" | "categorical" | "numeric"
}
```

**`activate_signal`**
```python
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
                "deployed_at": "2026-01-01T00:00:00Z",
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
                "deployed_at": "2026-01-01T00:00:00Z",
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

## Validation

```bash
python agent.py &
npx @adcp/client storyboard run http://localhost:3001/mcp signal_owned --json       # for owned data
npx @adcp/client storyboard run http://localhost:3001/mcp signal_marketplace --json  # for marketplace
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
