"""The payloads that contradict the envelope, corrected as DATA and applied by the build.

**`core/protocol-envelope.json` states `required: ['status']`, and every task response
composes it through an `allOf`.**  A payload that omits `status` therefore contradicts its
own document.  Upstream's suite is full of such payloads and upstream's suite is green,
because their generator wrote

    status: Literal['completed'] = 'completed'

on the response classes -- a default the document states nowhere.  The default is what makes
an incomplete payload validate, so removing the default is what makes the payload visible.
Our emitter states the field as the document does: required, from the nine-value
`enums/task-status.json`.  **The correction is to the PAYLOAD, never to the class and never
to an assertion.**

**WHAT MAY BE CORRECTED, AND IT IS A LINE.**  A row may exist only where the document
*refuses* the payload, and the value it adds must be one the document *admits*:

* the document's own pin where there is one -- `media-buy/sync-reporting-receipts-response.json`
  pins `status` to ``'completed'`` and that row's value is not a choice;
* otherwise the value the payload's own neighbourhood states.  Every row below is a response
  returned synchronously, in full, with no task handed off and no `task_id` minted -- several
  are already wrapped by the suite's own ``TaskResult(status=TaskStatus.COMPLETED, ...)``,
  which is the test saying what its scenario means.  ``'completed'`` is that reading.

No row changes an assertion, an expected value or a comparison.  Where a test's
*expectation* disagrees with its document, that is a finding and the test is left failing;
those are named in ``verdicts/payload-corrections.md``, not repaired here.

**WHY DATA AND NOT AN EDIT.**  The substituted tree is disposable (architecture §8a): it is
regenerated from this repository and never edited, and ``regenerate.py --audit`` reports a
hand-edited file as ``UPSTREAM EDITED`` -- a fork beginning.  So the corrections live here,
each one readable as a row carrying the document and pointer that justifies it, and the
build applies them.  The tree stays regenerable and every correction stays auditable.

**A ROW THAT DOES NOT APPLY IS AN ERROR, NOT A SKIP.**  ``apply`` asserts each row's site
count exactly.  When upstream rewrites one of these files the row stops matching and the
build fails loudly, which is the only way a stale correction gets noticed.  There is no
allowlist and no tolerance: a row is right or the build stops.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

ENVELOPE = "core/protocol-envelope.json"

# The readings that fix a value.  Every row cites one of them.
#: **NOT A JUSTIFICATION -- A DISQUALIFICATION.**  A row that would cite this has no
#: business existing: a pinned node leaves the instance nothing to say, so the omission is
#: the emitter's to close.  Kept named so the test is written down rather than remembered.
_PINNED = (
    "DISQUALIFIED: the node pins this property to one value, so supplying it in the "
    "payload writes the document into its own instance -- the emitter closes this, not a "
    "payload row (verdicts/a-pinned-default-is-the-documents-own.md)"
)
_SYNC = (
    "returned synchronously and in full -- no task_id minted, no handoff -- so the task "
    "the envelope asks about is finished; 'completed' is in enums/task-status.json"
)
_SYNC_WRAPPED = (
    "returned synchronously and in full, and the suite's own wrapper states the status: "
    "TaskResult(status=TaskStatus.COMPLETED, data=...)"
)


@dataclass(frozen=True)
class Construction:
    """Every construction of ``spelling`` in ``path`` that omits ``keyword``.

    The row names a CLASS AND A FILE, not a line: the applier finds the constructions by
    AST and skips any that already state the keyword at their own top level, so the row
    survives upstream moving the code around inside the file.  ``sites`` is the count
    measured when the row was written and is asserted on every build.
    """

    path: str
    spelling: str  # the name as THAT file spells it -- upstream's alias, not ours
    via: str  # "" for Cls(...), "model_validate" for Cls.model_validate({...})
    model: str  # the emitted class whose document refuses the payload
    document: str
    pointer: str
    value: str
    sites: int
    why: str
    keyword: str = "status"


@dataclass(frozen=True)
class Literal:
    """One payload built as a bare dict literal, anchored on its exact opening text.

    Used where the payload is not a model construction at all -- a helper that returns a
    dict, or a wire string the test serialises -- so there is no class name to key on.
    """

    path: str
    anchor: str  # exact source text, through the opening brace
    model: str
    document: str
    pointer: str
    value: str
    sites: int
    why: str
    keyword: str = "status"


# --------------------------------------------------------------------------------------
# The rows.  Grouped by the file they correct; every one carries its document and pointer.
# --------------------------------------------------------------------------------------

CONSTRUCTIONS: tuple[Construction, ...] = (
    # -- second round: revealed by correcting the payload that was refused first ---------
    Construction(
        "tests/test_server_framework.py", "ListPropertyListsResponse", "",
        "ListPropertyListsResponse", "property/list-property-lists-response.json", "#",
        "completed", 1, _SYNC,
    ),
    Construction(
        "tests/test_simple_api.py", "LegacyPreviewCreativeResponse1", "",
        "PreviewCreativeSingleResponse", "creative/preview-creative-response.json",
        "#/oneOf/0", "completed", 1, _SYNC,
    ),
    # **THE ONE ROW THAT CAME BACK OUT, AND IT IS A RULE AND NOT AN EXCEPTION.**
    # ``tests/conformance/reporting/_buyer_submission_support.py`` built a
    # ``SyncReportingReceiptsResponse`` without ``status``, 28 tests reached it, and this
    # file corrected it -- citing the document's `const: 'completed'` as the strongest
    # justification a row could have.  That reading is backwards.  Where the node pins the
    # property to ONE value the payload is not choosing anything, so supplying it writes
    # the document back into its own instances: the omission is the EMITTER's to close, on
    # the Python route, with the JSON route still refusing it.  A payload correction is for
    # a node that admits SEVERAL values, where the instance is the only thing that can say
    # which.  Measured over the bundle: 82 of the 559 `Field required` failures sit at a
    # pinned node and none of them is a payload defect -- `verdicts/
    # a-pinned-default-is-the-documents-own.md`, bead `adcp-client-python-rgra`.
    #
    # The pair that makes it unambiguous is in one bundle:
    # `SyncReportingReceiptsResponse.status` is pinned to 'completed', and
    # `GetProductsResponse.status` is the full `TaskStatus`.  So the question is asked of
    # the NODE and never of the property's name, and `_PINNED` is kept below only as the
    # test every new row has to fail.
    # -- get_products, the response the suite builds most often -------------------------
    Construction(
        "tests/test_decisioning_async_discovery.py", "GetProductsResponse", "",
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 11, _SYNC,
    ),
    Construction(
        "tests/test_decisioning_async_discovery.py", "GetSignalsResponse", "",
        "GetSignalsResponse", "signals/get-signals-response.json", "#",
        "completed", 6, _SYNC,
    ),
    Construction(
        "tests/test_decisioning_brand_authz_dispatch.py", "GetProductsResponse", "",
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 6, _SYNC,
    ),
    Construction(
        "tests/test_decisioning_buyer_agent_dispatch.py", "GetProductsResponse", "",
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 5, _SYNC,
    ),
    Construction(
        "tests/test_decisioning_handler.py", "GetProductsResponse", "",
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 4, _SYNC,
    ),
    Construction(
        "tests/test_decisioning_handler.py", "LegacyListCreativeFormatsResponse", "",
        "ListCreativeFormatsResponse", "media-buy/list-creative-formats-response.json", "#",
        "completed", 1, _SYNC,
    ),
    Construction(
        "tests/test_decisioning_handler.py", "SyncCreativesSuccessResponse", "",
        "SyncCreativesSuccess", "creative/sync-creatives-response.json", "#/oneOf/0",
        "completed", 1, _SYNC,
    ),
    Construction(
        "tests/test_decisioning_refine.py", "GetProductsResponse", "",
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 3, _SYNC,
    ),
    Construction(
        "tests/test_get_products_projection.py", "GetProductsResponse", "",
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 6, _SYNC,
    ),
    Construction(
        "tests/test_typed_handler_params.py", "GetProductsResponse", "",
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 1, _SYNC,
    ),
    # -- capabilities, wrapped by the suite's own COMPLETED TaskResult ------------------
    Construction(
        "tests/test_account_lifecycle.py", "GetAdcpCapabilitiesResponse", "model_validate",
        "GetAdCPCapabilitiesResponse", "protocol/get-adcp-capabilities-response.json", "#",
        "completed", 1, _SYNC_WRAPPED,
    ),
    Construction(
        "tests/test_account_lifecycle.py", "GetProductsResponse", "",
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 2, _SYNC_WRAPPED,
    ),
    Construction(
        "tests/test_negotiated_signing_profiles.py", "GetAdcpCapabilitiesResponse",
        "model_validate",
        "GetAdCPCapabilitiesResponse", "protocol/get-adcp-capabilities-response.json", "#",
        "completed", 1, _SYNC,
    ),
    # -- media buys ---------------------------------------------------------------------
    Construction(
        "tests/test_create_media_buy_response_types.py", "CreateMediaBuySuccessResponse", "",
        "CreateMediaBuySuccess", "media-buy/create-media-buy-response.json", "#/oneOf/0",
        "completed", 2, _SYNC,
    ),
    Construction(
        "tests/test_create_media_buy_response_types.py", "CreateMediaBuySuccessResponse",
        "model_validate",
        "CreateMediaBuySuccess", "media-buy/create-media-buy-response.json", "#/oneOf/0",
        "completed", 4, _SYNC,
    ),
    Construction(
        "tests/test_server_dx.py", "CreateMediaBuySuccessResponse", "",
        "CreateMediaBuySuccess", "media-buy/create-media-buy-response.json", "#/oneOf/0",
        "completed", 2, _SYNC,
    ),
    Construction(
        "tests/test_server_dx.py", "UpdateMediaBuySuccessResponse", "",
        "UpdateMediaBuySuccess", "media-buy/update-media-buy-response.json", "#/oneOf/0",
        "completed", 2, _SYNC,
    ),
    Construction(
        "tests/conformance/reporting/test_reliable_reporting_core_recovery.py",
        "GetMediaBuyDeliveryResponse", "model_validate",
        "GetMediaBuyDeliveryResponse", "media-buy/get-media-buy-delivery-response.json", "#",
        "completed", 1, _SYNC,
    ),
    # -- creatives ----------------------------------------------------------------------
    Construction(
        "tests/test_manifest_response_readback.py", "LegacyBuildCreativeResponse3",
        "model_validate",
        "BuildCreativeVariantSuccess", "media-buy/build-creative-response.json", "#/oneOf/2",
        "submitted", 1, "the #/oneOf/2 arm; the response has no completed creative to "
                        "return, which is the arm 'submitted' names",
    ),
    Construction(
        "tests/test_manifest_response_readback.py", "LegacyBuildCreativeResponse4",
        "model_validate",
        "BuildCreativeSuccess", "media-buy/build-creative-response.json", "#/oneOf/0",
        "completed", 1, _SYNC,
    ),
    Construction(
        "tests/test_preview_html.py", "LegacyPreviewCreativeBatchResponse", "",
        "PreviewCreativeBatchResponse", "creative/preview-creative-response.json", "#/oneOf/1",
        "completed", 1, _SYNC,
    ),
    Construction(
        "tests/test_preview_html.py", "LegacyListCreativeFormatsResponse", "",
        "ListCreativeFormatsResponse", "media-buy/list-creative-formats-response.json", "#",
        "completed", 1, _SYNC,
    ),
    # -- principals, plans, properties --------------------------------------------------
    Construction(
        "tests/test_principal.py", "GetPrincipalResponse", "model_validate",
        "GetPrincipalResponse", "protocol/get-principal-response.json", "#",
        "completed", 2, _SYNC,
    ),
    Construction(
        "tests/test_principal.py", "SyncPrincipalResponse", "model_validate",
        "SyncPrincipalResponse", "protocol/sync-principal-response.json", "#",
        "completed", 2, _SYNC,
    ),
    Construction(
        "tests/test_server_framework.py", "SyncPlansResponse", "",
        "SyncPlansResponse", "governance/sync-plans-response.json", "#",
        "completed", 1, _SYNC,
    ),
    Construction(
        "tests/test_server_framework.py", "GetPropertyListResponse", "",
        "GetPropertyListResponse", "property/get-property-list-response.json", "#",
        "completed", 1, _SYNC,
    ),
)


LITERALS: tuple[Literal, ...] = (
    # ``response_case`` returns (model, payload) pairs; the payload is a bare dict, so there
    # is no class name at the construction to key on.  One helper, five payloads.
    Literal(
        "tests/test_manifest_response_readback.py",
        'return LegacyPreviewCreativeResponse3, {\n            "response_type": "variant",',
        "PreviewCreativeVariantResponse", "creative/preview-creative-response.json",
        "#/oneOf/2", "completed", 1, _SYNC,
    ),
    Literal(
        "tests/test_manifest_response_readback.py",
        'return LegacyBuildCreativeResponse1, {"creative_manifest": manifest}',
        "BuildCreativeSuccess", "media-buy/build-creative-response.json", "#/oneOf/0",
        "completed", 1, _SYNC,
    ),
    Literal(
        "tests/test_manifest_response_readback.py",
        'return LegacyBuildCreativeResponse3, {"creative_manifests": [manifest]}',
        "BuildCreativeVariantSuccess", "media-buy/build-creative-response.json", "#/oneOf/2",
        "completed", 1, _SYNC,
    ),
    Literal(
        "tests/test_manifest_response_readback.py",
        'return model, {\n            "request_id": "request-1",',
        "ContextMatchResponseRouterPublisher", "trusted-match/context-match-response.json",
        "#", "completed", 1, _SYNC,
    ),
    Literal(
        "tests/test_manifest_response_readback.py",
        'return LegacyBuildCreativeResponse4, {\n        "creatives": [',
        "BuildCreativeSuccess", "media-buy/build-creative-response.json", "#/oneOf/0",
        "completed", 1, _SYNC,
    ),
    # ``_success_response`` builds the update_rights wire dict the A2A mock returns.
    Literal(
        "tests/test_update_rights_roundtrip.py",
        'response: dict[str, Any] = {\n        "rights_id": rights_id,',
        "UpdateRightsResponse", "brand/update-rights-response.json", "#",
        "completed", 1, _SYNC,
    ),
    # A wire STRING the test serialises and feeds through the client's own parser.
    Literal(
        "tests/test_response_size_limit.py",
        'json.dumps({"products": [], "padding": "x" * 200_000})',
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 2, _SYNC,
    ),
    # Payloads the test builds as a bare dict and only NAMES at the construction.
    Literal(
        "tests/test_decisioning_property_list.py",
        'payload = {"products": [p_pass, p_fail], "seller_extra": {"retained": True}}',
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 1, _SYNC,
    ),
    Literal(
        "tests/test_decisioning_property_list.py",
        'payload = {"products": [], "property_list_applied": applied, "seller_extra": "keep"}',
        "GetProductsResponse", "media-buy/get-products-response.json", "#",
        "completed", 1, _SYNC,
    ),
    Literal(
        "tests/test_catalog_types.py",
        'data = {\n        "errors": [',
        "SyncCatalogsError", "media-buy/sync-catalogs-response.json", "#/oneOf/1",
        "failed", 1,
        "the #/oneOf/1 ERROR arm -- the payload is an `errors` list and nothing else, so "
        "'failed' is the enums/task-status.json value that states a task which ran and did "
        "not succeed; 'completed' would contradict the arm the payload chose",
    ),
    Literal(
        "tests/test_manifest_response_readback.py",
        'payload = {\n        "query_summary": {"total_matching": 1, "returned": 1},',
        "ListCreativesResponse", "creative/list-creatives-response.json", "#",
        "completed", 1, _SYNC,
    ),
    # **UPSTREAM'S OWN EXAMPLE SELLER EMITS THREE RESPONSES ITS ENVELOPE REFUSES.**  These
    # are not test payloads: `examples/hello_seller.py` is the file upstream ships as the
    # worked example an adopter copies, and three of its handlers return a task response
    # with no `status`.  Any conforming peer would reject all three on the wire.  The three
    # tests that validate those returns are the suite catching it, which is what they are
    # for -- so the correction belongs in the example, not in the tests that grade it.
    Literal(
        "examples/hello_seller.py",
        'return {"media_buys": []}',
        "GetMediaBuysResponse", "media-buy/get-media-buys-response.json", "#",
        "completed", 1, _SYNC,
    ),
    Literal(
        "examples/hello_seller.py",
        'return {"formats": []}',
        "ListCreativeFormatsResponse", "media-buy/list-creative-formats-response.json", "#",
        "completed", 1, _SYNC,
    ),
    Literal(
        "examples/hello_seller.py",
        'return {\n            "query_summary": {"total_matching": 0, "returned": 0},',
        "ListCreativesResponse", "creative/list-creatives-response.json", "#",
        "completed", 1, _SYNC,
    ),
    # **SECOND ROUND.**  These were MASKED: their file's first payload was refused before
    # the reader ever reached them, so the junit named only the earlier site.  Correcting
    # the first one is what made these visible -- the same cause, one layer down, derived
    # from the run that followed the first round rather than guessed at ahead of it.
    Literal(
        "tests/test_account_lifecycle.py",
        'validate_union(SyncAccountsResponse, {"accounts": rows})',
        "SyncAccountsResponse", "account/sync-accounts-response.json", "#",
        "completed", 1, _SYNC,
    ),
    Literal(
        "tests/test_account_lifecycle.py",
        'validate_union(ListAccountsResponse, {"accounts": []})',
        "ListAccountsResponse", "account/list-accounts-response.json", "#",
        "completed", 1, _SYNC,
    ),
    # ``validate_union`` takes the payload as an argument, so the dict is the anchor.
    Literal(
        "tests/test_server_framework.py",
        'validate_union(GetCreativeFeaturesResponse, {',
        "GetCreativeFeaturesResponse", "creative/get-creative-features-response.json", "#",
        "completed", 1, _SYNC,
    ),
)


def _offsets(src: str) -> list[int]:
    """Absolute offset of the start of each 1-indexed line."""
    out, n = [0, 0], 0
    for line in src.splitlines(keepends=True):
        n += len(line)
        out.append(n)
    return out


def _states_keyword(call: ast.Call, keyword: str) -> bool:
    """Does this construction already state ``keyword`` at its OWN top level?

    A nested occurrence does not count: ``{"results": [{"status": "failed"}]}`` states a
    per-item result, not the envelope's task status.
    """
    if any(k.arg == keyword for k in call.keywords):
        return True
    first = call.args[0] if call.args else None
    return isinstance(first, ast.Dict) and any(
        isinstance(k, ast.Constant) and k.value == keyword for k in first.keys
    )


def _construction_edits(src: str, row: Construction) -> list[tuple[int, str]]:
    """(offset, text) insertions for every matching construction that omits the keyword."""
    lines = _offsets(src)
    edits: list[tuple[int, str]] = []
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if row.via:
            if not (
                isinstance(func, ast.Attribute)
                and func.attr == row.via
                and getattr(func.value, "id", None) == row.spelling
            ):
                continue
        elif getattr(func, "id", None) != row.spelling:
            continue
        if not node.args and not node.keywords:
            continue  # Cls() with no payload states nothing to correct
        if _states_keyword(node, row.keyword):
            continue
        if row.via:
            first = node.args[0] if node.args else None
            if not isinstance(first, ast.Dict):
                continue  # the payload is a variable -- a Literal row's job, not this one
            at = lines[first.lineno] + first.col_offset + 1  # just inside the `{`
            edits.append((at, f'"{row.keyword}": {row.value!r}, '))
        else:
            start = lines[func.end_lineno or func.lineno] + (func.end_col_offset or 0)
            at = src.index("(", start) + 1
            edits.append((at, f"{row.keyword}={row.value!r}, "))
    return edits


def _literal_edits(src: str, row: Literal) -> list[tuple[int, str]]:
    """(offset, text) insertions just inside the payload's OWN opening brace.

    **IT IS THE FIRST BRACE IN THE ANCHOR AND NOT THE LAST.**  Reading the last one put
    three corrections inside a NESTED object -- ``"query_summary": {"status": ...}`` and
    ``"seller_extra": {"status": ...}`` -- which states the envelope's task status on a
    sub-object that does not have one, leaving the payload still refused and adding a key
    the document never asked for.  An anchor opens at the payload it names, so the first
    brace is the payload's.  A row whose anchor would need the second must be written to
    start later instead.
    """
    edits: list[tuple[int, str]] = []
    opens = row.anchor.index("{")
    at = src.find(row.anchor)
    while at != -1:
        edits.append((at + opens + 1, f'"{row.keyword}": "{row.value}", '))
        at = src.find(row.anchor, at + 1)
    return edits


def apply(tree: Path) -> dict[str, object]:
    """Apply every row to the laid tree, asserting each one's site count exactly.

    Returns the report the build prints.  Raises ``SystemExit`` on the first row whose
    measured site count disagrees with the row -- a stale correction stops the build rather
    than quietly correcting less than it claims.
    """
    rows: list[tuple[str, str, str, str, str, str, int]] = []
    by_path: dict[str, list[tuple[int, str]]] = {}
    for row in (*CONSTRUCTIONS, *LITERALS):
        path = tree / row.path
        if not path.is_file():
            raise SystemExit(f"payload_fixes: {row.path} is not in the laid tree")
        src = path.read_text()
        edits = (
            _literal_edits(src, row)
            if isinstance(row, Literal)
            else _construction_edits(src, row)
        )
        if len(edits) != row.sites:
            raise SystemExit(
                f"payload_fixes: {row.path} :: {row.model} -- the row claims {row.sites} "
                f"site(s) omitting {row.keyword!r}, the tree has {len(edits)}.  Upstream "
                f"moved or already corrected this payload; re-measure the row, do not "
                f"loosen it."
            )
        by_path.setdefault(row.path, []).extend(edits)
        rows.append(
            (row.path, row.model, row.document + row.pointer, row.keyword, row.value,
             row.why, row.sites)
        )
    for rel, edits in by_path.items():
        path = tree / rel
        src = path.read_text()
        for at, text in sorted(edits, reverse=True):  # back to front: offsets stay valid
            src = src[:at] + text + src[at:]
        ast.parse(src)  # the correction must leave the file parseable
        path.write_text(src)
    table = tree / "payload-corrections.tsv"
    table.write_text(
        "path\tmodel\tdocument\tkeyword\tvalue\treason\tsites\n"
        + "".join("\t".join((*r[:6], str(r[6]))) + "\n" for r in sorted(rows))
    )
    return {
        "rows": len(rows),
        "files": len(by_path),
        "sites corrected": sum(r[6] for r in rows),
        "keyword": sorted({r[3] for r in rows}),
        "values": sorted({r[4] for r in rows}),
        "table": str(table),
    }
