---
name: build-seller-agent
description: Use when building an AdCP seller agent — a publisher, SSP, or retail media network that sells advertising inventory to buyer agents.
---

# Build a Seller Agent (Python)

## Overview

A seller agent receives briefs from buyers, returns products with pricing, accepts media buys, manages creatives, and reports delivery. The business model — what you sell, how you price it, and whether humans approve deals — shapes every implementation decision. Determine that first.

## When to Use

- User wants to build an agent that sells ad inventory
- User mentions publisher, SSP, retail media, or media network in the context of AdCP
- User references `get_products`, `create_media_buy`, or the media buy protocol

**Not this skill:**
- Buying ad inventory → buyer/DSP agent
- Serving audience segments → `skills/build-signals-agent/`
- Rendering creatives from briefs → creative agent

## Before Writing Code

Determine these five things. Ask the user — don't guess.

### 1. What Kind of Seller?

- **Premium publisher** — guaranteed inventory, fixed pricing, IO approval
- **SSP / Exchange** — non-guaranteed, auction-based, instant activation
- **Retail media network** — both guaranteed and non-guaranteed, catalog-driven

### 2. Guaranteed or Non-Guaranteed?

- **Guaranteed** — `delivery_type: "guaranteed"`, may require async approval
- **Non-guaranteed** — `delivery_type: "non_guaranteed"`, buyer sets `bid_price`, instant activation

### 3. Products and Pricing

Each product needs: name, description, publisher_properties, format_ids, delivery_type, pricing_options.

Pricing models:
- `cpm` — `CpmPricingOption(pricing_option_id="...", pricing_model="cpm", floor_price=12.00, currency="USD")`
- `flat_rate` — `FlatRatePricingOption(pricing_option_id="...", pricing_model="flat_rate", fixed_price=250.00, currency="USD")`

### 4. Approval Workflow

- **Instant** — `create_media_buy` returns confirmed status
- **Async** — returns submitted, buyer polls `get_media_buys`

### 5. Creative Management

- **Standard** — `list_creative_formats` + `sync_creatives`
- **None** — omit creative tools

## Architecture

One file. Subclass `ADCPHandler`, override the tools you support, call `serve()`.

```python
from adcp.server import ADCPHandler, serve
from adcp.server.responses import capabilities_response, products_response
from adcp.server.test_controller import TestControllerStore

class MySeller(ADCPHandler):
    async def get_adcp_capabilities(self, params, context=None):
        return capabilities_response(["media_buy", "compliance_testing"])

    async def get_products(self, params, context=None):
        return products_response(MY_PRODUCTS)

    # ... more tools ...

serve(MySeller(), name="my-seller", test_controller=MyStore())
```

## Tools and Required Response Shapes

Every tool below uses a response builder from `adcp.server.responses`. Use the builders — never return raw dicts.

**`get_adcp_capabilities`**
```python
from adcp.server.responses import capabilities_response

async def get_adcp_capabilities(self, params, context=None):
    return capabilities_response(["media_buy", "compliance_testing"])
```

**`sync_accounts`**
```python
from adcp.server.responses import sync_accounts_response

async def sync_accounts(self, params, context=None):
    results = []
    for acct in params.get("accounts", []):
        account_id = f"acct-{uuid.uuid4().hex[:8]}"
        # Store in memory so test controller can find it
        accounts[account_id] = {"status": "active", "brand": acct.get("brand"), "operator": acct.get("operator")}
        results.append({
            "account_id": account_id,
            "brand": acct.get("brand"),        # echo back
            "operator": acct.get("operator"),   # echo back
            "action": "created",
            "status": "active",
            "account_scope": "operator_brand",
        })
    return sync_accounts_response(results)
```

**`sync_governance`**
```python
from adcp.server.responses import sync_governance_response

async def sync_governance(self, params, context=None):
    results = []
    for entry in params.get("accounts", []):
        acct_ref = entry.get("account", {})
        agents = entry.get("governance_agents", [])
        results.append({
            "account": acct_ref,
            "status": "synced",
            "governance_agents": [
                {"url": a.get("url"), "categories": a.get("categories", [])}
                for a in agents
            ],
        })
    return sync_governance_response(results)
```

**`get_products`**
```python
from adcp.server.responses import products_response
from adcp.types import Product, CpmPricingOption, FormatId, PublisherPropertiesAll, DeliveryType, DeliveryMeasurement

async def get_products(self, params, context=None):
    return products_response(PRODUCTS)
```

**`create_media_buy`**
```python
from adcp.server.responses import media_buy_response

async def create_media_buy(self, params, context=None):
    packages = []
    for pkg in params.get("packages", []):
        packages.append({
            "package_id": f"pkg-{uuid.uuid4().hex[:8]}",
            "product_id": pkg.get("product_id"),
            "pricing_option_id": pkg.get("pricing_option_id"),
            "budget": pkg.get("budget"),
        })
    mb_id = f"mb-{uuid.uuid4().hex[:8]}"
    # Store so get_media_buys and test controller can find it
    media_buys[mb_id] = {"status": "active", "currency": "USD", "packages": packages}
    return media_buy_response(mb_id, packages)
```

**`get_media_buys`**
```python
from adcp.server.responses import media_buys_response

async def get_media_buys(self, params, context=None):
    requested_ids = params.get("media_buy_ids")
    results = []
    for mb_id, mb in media_buys.items():
        if requested_ids and mb_id not in requested_ids:
            continue
        results.append({
            "media_buy_id": mb_id,
            "status": mb["status"],
            "currency": mb.get("currency", "USD"),
            "packages": mb.get("packages", []),
        })
    return media_buys_response(results)
```

**`list_creative_formats`**
```python
from adcp.server.responses import creative_formats_response

async def list_creative_formats(self, params, context=None):
    return creative_formats_response([
        {
            "format_id": {"agent_url": AGENT_URL, "id": "display_300x250"},
            "name": "Display 300x250",
            "renders": [{"width": 300, "height": 250}],
            "assets": [{
                "item_type": "individual",
                "asset_id": "image",
                "asset_type": "image",
                "required": True,
                "accepted_media_types": ["image/png", "image/jpeg"],
            }],
        },
    ])
```

**`sync_creatives`**
```python
from adcp.server.responses import sync_creatives_response

async def sync_creatives(self, params, context=None):
    results = []
    for c in params.get("creatives", []):
        creative_id = c.get("creative_id", f"c-{uuid.uuid4().hex[:8]}")
        # Store so test controller can find it
        creatives[creative_id] = {**c, "status": "approved"}
        results.append({
            "creative_id": creative_id,
            "action": "created",
            "status": "approved",
        })
    return sync_creatives_response(results)
```

**`get_media_buy_delivery`**
```python
from adcp.server.responses import delivery_response

async def get_media_buy_delivery(self, params, context=None):
    requested_ids = params.get("media_buy_ids", [])
    deliveries = []
    for mb_id in requested_ids:
        if mb_id in media_buys:
            deliveries.append({
                "media_buy_id": mb_id,
                "status": "active",
                "totals": {"impressions": 45000, "clicks": 680, "spend": 540.00},
                "by_package": [],
            })
    return delivery_response(
        deliveries,
        reporting_period={"start": "2026-04-01T00:00:00Z", "end": "2026-04-09T23:59:59Z"},
    )
```

## Compliance Testing

Add a `TestControllerStore` so storyboard tests can force state transitions. Override the methods for scenarios your agent supports.

```python
from adcp.server.test_controller import TestControllerStore, TestControllerError

class MyStore(TestControllerStore):
    async def force_account_status(self, account_id, status):
        acct = accounts.get(account_id)
        if not acct:
            raise TestControllerError("NOT_FOUND", f"Account {account_id} not found")
        prev = acct["status"]
        acct["status"] = status
        return {"previous_state": prev, "current_state": status}

    async def force_media_buy_status(self, media_buy_id, status, rejection_reason=None):
        mb = media_buys.get(media_buy_id)
        if not mb:
            raise TestControllerError("NOT_FOUND", f"Media buy {media_buy_id} not found")
        prev = mb["status"]
        if prev in ("completed", "rejected", "canceled"):
            raise TestControllerError("INVALID_TRANSITION", f"Cannot transition from {prev}", current_state=prev)
        mb["status"] = status
        return {"previous_state": prev, "current_state": status}

    async def force_creative_status(self, creative_id, status, rejection_reason=None):
        c = creatives.get(creative_id)
        if not c:
            raise TestControllerError("NOT_FOUND", f"Creative {creative_id} not found")
        prev = c.get("status", "unknown")
        if prev == "archived":
            raise TestControllerError("INVALID_TRANSITION", "Cannot transition from archived", current_state=prev)
        c["status"] = status
        return {"previous_state": prev, "current_state": status}

    async def simulate_delivery(self, media_buy_id, impressions=None, clicks=None, conversions=None, reported_spend=None):
        if media_buy_id not in media_buys:
            raise TestControllerError("NOT_FOUND", f"Media buy {media_buy_id} not found")
        simulated = {"media_buy_id": media_buy_id}
        if impressions is not None: simulated["impressions"] = impressions
        if clicks is not None: simulated["clicks"] = clicks
        return {"simulated": simulated, "cumulative": simulated}

    async def simulate_budget_spend(self, spend_percentage, account_id=None, media_buy_id=None):
        return {"simulated": {"spend_percentage": spend_percentage}}
```

Pass the store to `serve()`:
```python
serve(MySeller(), name="my-seller", test_controller=MyStore())
```

Declare `compliance_testing` in supported_protocols:
```python
return capabilities_response(["media_buy", "compliance_testing"])
```

## SDK Quick Reference

| Function | Usage |
|----------|-------|
| `serve(handler, test_controller=store)` | Start server on `:3001/mcp` with test controller |
| `create_mcp_server(handler)` | Create server without starting (for customization) |
| `capabilities_response(protocols)` | `get_adcp_capabilities` response |
| `products_response(products)` | `get_products` response |
| `media_buy_response(id, packages)` | `create_media_buy` success response |
| `media_buys_response(media_buys)` | `get_media_buys` response |
| `delivery_response(deliveries, reporting_period=...)` | `get_media_buy_delivery` response |
| `sync_accounts_response(accounts)` | `sync_accounts` response |
| `sync_governance_response(accounts)` | `sync_governance` response |
| `creative_formats_response(formats)` | `list_creative_formats` response |
| `sync_creatives_response(creatives)` | `sync_creatives` response |
| `error_response(code, message)` | Structured error |

Import handlers from `adcp.server`. Import response builders from `adcp.server.responses`. Import types from `adcp.types`.

## Validation

**After writing the agent, validate it. Fix failures. Repeat.**

```bash
python agent.py &
npx @adcp/client storyboard run http://localhost:3001/mcp media_buy_seller --json
```

**Keep iterating until all steps pass.**

## Storyboards

| Storyboard | Use case |
|-----------|----------|
| `media_buy_seller` | Full lifecycle — every seller should pass this (9 steps) |
| `deterministic_testing` | Test controller state machine validation |
| `media_buy_non_guaranteed` | Auction flow with bid adjustment |
| `media_buy_guaranteed_approval` | IO approval workflow |

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skip `get_adcp_capabilities` | Must be implemented — buyers call it first |
| Return raw dicts without builders | Use response builders from `adcp.server.responses` |
| Missing `brand`/`operator` in sync_accounts | Echo them back from the request |
| Not storing entities in memory | Test controller needs to find accounts, media buys, creatives |
| Wrong `delivery_response` signature | Takes `delivery_response(deliveries_list, reporting_period=...)`, not individual metrics |

## Reference

This skill contains everything needed to build a 9/9 passing seller agent. The code blocks above are taken from a validated implementation.
