# Where `input_value=None` comes from, and where it does not

Measured off the drop-in run artifact at `/srv/ws/dropin-full/junit/chunk-*.json` (pytest's
own json report, key `call.longrepr`), by walking **every frame of every traceback** rather
than the tail line. **280 failures carry `input_value=None`**; 149 of them carry
`type=string_type`.

This survey stands on its own: the call-site sweep it was gathered for is reverted, because
the fix turned out to be one method and not 190 sites (the route split in
`_AbsenceIsOmission`). What the survey answers is the question that fix does *not* — where
a `None` is written in code we ship, and where it arrives in data.

## The split, by the deepest frame in the traceback

| the deepest frame is | failures |
| --- | --- |
| a caller in `src/adcp/` outside `types/` | **137** |
| a **test's own fixture** | **143** |
| no `.py` frame at all | **0** |

**The 143 are a payload question and not ours.** My earlier report said "128 failures carry
no frame in `src/adcp/` outside `types/`, so the artifact does not name their caller" — that
was an artefact of reading only the tail `src/adcp/…` match. Walking the whole traceback
names every one of them, and 143 bottom out in a test constructing a payload itself. They
are named here so nobody has to re-derive it:

| test file | failures |
| --- | --- |
| `tests/conformance/signing/test_install_signing_event_hook.py` | 14 |
| `tests/test_webhooks_deliver.py` | 11 |
| `tests/test_implementation_config.py` | 7 |
| `tests/conformance/signing/test_autosign.py` | 5 |
| `tests/conformance/signing/test_autosign.py` and 3 more | 10 |

(the remainder spread over `tests/test_decisioning_pagination.py`,
`tests/test_decisioning_negotiation.py`, `tests/test_account_projection.py`, and the models
those payloads are validated against are `MCPWebhookPayload` ×56, `GetReportingStatusResponse`
×28, `RequestSigning` ×21, `ReportingObligation` ×18,
`GetAdCPCapabilitiesResponseMediaBuy` ×13, `GetMediaBuyDeliveryRequest` ×11,
`WholesaleFeedWebhook` ×8, `GetProductsResponse` ×7)

**Every one of the 143 is fixed by the route split and not by any edit to a test**, because
each is a Python dict or a Python keyword argument carrying `None` — which is exactly the
route upstream's own contract reads as absence.

## The 137 with a caller in `src/adcp/`

| site | failures |
| --- | --- |
| `src/adcp/webhooks.py:272` | 35 |
| `src/adcp/feed_mirror.py:449` | 32 |
| `src/adcp/canonical_formats/advisory.py:141` | 31 |
| `src/adcp/server/principal.py:462` | 10 |
| `src/adcp/decisioning/handler.py:2628` | 5 |
| `src/adcp/webhook_sender.py:1619`, `:755`, `:1538` | 3 each |
| `src/adcp/webhooks.py:394` | 2 |
| `src/adcp/reporting/service.py:347` | 2 |
| `src/adcp/decisioning/refine.py:236` | 2 |
| `webhook_sender.py:1450`, `principal.py:374`, `principal.py:460`, `mcp_tools.py:3485`, `refine.py:196`, `refine.py:238`, `mcp_tools.py:3996`, `client.py:7060`, `handler.py:1977` | 1 each |

Two of those are intermediate frames and not constructions: `webhook_sender.py:755` calls
the helper in `webhooks.py`, and `webhooks.py:394` is a logging `extra=` dict.

## THE 13 THE BRIEF ASKED ABOUT: four of five are NOT this defect

These were handed over as "the same fix with the same helper". They are not, and the
distinction is the point — in four of the five the `None` is **in the data**, not written at
the call site:

| site | what it validates | verdict |
| --- | --- | --- |
| `decisioning/handler.py:2628` | `GetProductsResponse.model_validate(project_incomplete_response(...))` | **the defect, in another file** |
| `decisioning/handler.py:1804`, `:1977` | `AdcpError(...)` — not a generated model | not this defect |
| `decisioning/proposal_manager.py:248` | `MediaBuy.model_validate({"proposal_refinement": raw_refinement})` — adopter-supplied config | not ours |
| `reporting/service.py:347`, `:349` | `ReportingDeliveryOffering.model_validate(_wire(item))` — adopter mapping | not ours |
| `client.py:6680`, `:7060` | `McpWebhookPayload.model_validate(payload)` — an **inbound webhook body** | must keep refusing |

**`client.py` is the one to be careful about.** That payload arrived over the wire. A JSON
`null` there is a value the document refuses, so refusing it is CORRECT, and stripping nulls
from an inbound body would widen the SDK at exactly the boundary `strict_validate` exists to
hold. The route split does not touch it either: an inbound body parsed from JSON takes the
JSON route, where the null arm stays struck.

**And `handler.py:2628` points at a one-line defect in a file this lane may not edit.**
`src/adcp/decisioning/time_budget.py:273` builds

```python
{"scope": "products", "description": description, "estimated_wait": None}
```

and the function's own docstring says *"`estimated_wait` is omitted (`None`) when the plain
adopter path is used"* — it says **omitted** and spells it `None`. That dict is returned to
every caller, so the honest repair is in the helper and not a wrapper at the handler. It is
reported rather than edited because `time_budget.py` is outside this lane's write scope. The
route split makes those 5 failures pass regardless, because the dict goes in through
`model_validate`; the line is still worth fixing so the helper's text and its behaviour agree.
