"""Which branch of the webhook `result` union a payload actually carries.

``core/mcp-webhook-payload.json#/properties/result`` points at
``core/async-response-data.json``, a **42-branch untagged ``anyOf``** with no
``discriminator`` keyword.  Re-derived here the way
``adcontextprotocol/adcp#8964`` derives it -- by VALIDATING the empty object
against each branch over the bundle, not by a structural proxy -- **the empty
object satisfies 15 of the 42 branches**.  So a ``preview_creative`` result
validates against ``media-buy/get-products-async-response-working.json``, a
plain jsonschema validator agrees, and the branch a bare union hands back is
whichever vacuous one comes first.

**THE DOCUMENT ITSELF INSTRUCTS THE CALLER TO DO WHAT THIS MODULE DOES.**
``core/async-response-data.json``'s own ``description``:

    Because this shared webhook union is not tagged with the originating task
    type, callers MUST also validate a terminal result against that task or
    event's specific schema.

This module is that MUST, performed once for the developer instead of
re-implemented in every receiver.  It is not a workaround for the union's
vacuity -- the union is faithfully emitted and the document cannot
discriminate -- it is the second validation the document requires, against the
schema the originating task names.

**THE ENVELOPE KNOWS WHICH BRANCH ITS ``result`` IS.**
``core/mcp-webhook-payload.json`` requires ``['idempotency_key',
'operation_id', 'task_id', 'task_type', 'status', 'timestamp']``, and two of
those sit right beside ``result``: ``task_type`` (``enums/task-type.json``,
"Type of AdCP operation") and ``status`` (``enums/task-status.json``, "Current
task status").  The ``result`` description says the payload is "Task-specific
payload matching the status".  Together the pair names the schema; the
schema-level dependency is simply never stated as ``if``/``then``.

**AND IT IS A PLAIN FUNCTION, for three recorded reasons.**  It is not a
change to the compiler or the lowering, because inventing a discriminator the
document does not state is the one thing the compiler must never do
(``docs/plan/architecture.md`` §5: *the compiler transcribes a document; it
never decides whether the document is satisfiable*).  It is not a patch to the
generated ``McpWebhookPayload``, because a hand edit to an emitted file is a
change with a deletion already scheduled.  And it is not an import-time model
patch: this repository deleted that layer on purpose
(``verdicts/the-dead-patch-layer.md``, ``FINDINGS-126.md`` row R5).

**THE MAPPING IS DERIVED FROM THE BUNDLE AND NOT TYPED OUT.**  See
:func:`resolution_table` for the derivation and
``FINDINGS-webhook.md`` for the measurement it produces.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from types import MappingProxyType
from typing import Any

from adcp.exceptions import ADCPWebhookError

# **The DOMAIN paths and not the flat ``adcp.types`` facade**, which is the same
# import ``adcp.webhook_receiver`` makes of ``McpWebhookPayload``.  The facade is
# lazy (PEP 562) and binds these names as module-level variables, so a checker
# reads ``Variable "adcp.types.McpWebhookPayload" is not valid as a type`` for
# every annotation written against it; a domain path is where the class is
# DEFINED, and `CLAUDE.md` makes it a supported import for exactly this.
from adcp.types.base import AdCPBaseModel
from adcp.types.domains.core.async_response_data import AdCPAsyncResponseData
from adcp.types.domains.core.mcp_webhook_payload import McpWebhookPayload
from adcp.types.domains.enums.task_status import TaskStatus
from adcp.types.domains.enums.task_type import TaskType
from adcp.validation.schema_loader import get_named_schema_document

#: The document the union's branches are positions in.  A branch class carries
#: ``SchemaRef(document=UNION_DOCUMENT, pointer="#/anyOf/<i>")`` for its position
#: and inherits the referenced document's own root class, which is where the
#: branch's schema identity is read from.
UNION_DOCUMENT = "core/async-response-data.json"

#: The envelope whose ``task_type``/``status`` pair names the branch.
ENVELOPE_DOCUMENT = "core/mcp-webhook-payload.json"

#: **The one DECLARATION in this derivation, and it is three status values
#: rather than 42 branches.**  ``core/tasks-get-response.json``'s own ``result``
#: description states the terminal set and the resolution procedure in the same
#: sentence: *"Present when include_result was true and a completed, failed, or
#: rejected task produced a terminal artifact; canceled tasks may omit it.
#: Consumers and sellers MUST resolve and validate the exact schema through
#: manifest.task_result_resolution: use terminal_schema_overrides[task_type]
#: when present, otherwise tools[task_type].response_schema."*
#:
#: That is the polling envelope talking about ITS ``result``, and it is the only
#: place the bundle writes the procedure down.  The webhook envelope's ``result``
#: carries the untagged union instead of repeating it, which is the whole of
#: ``adcontextprotocol/adcp#8964``.
TERMINAL_STATUSES = ("completed", "failed", "rejected")

#: The ``$ref`` prefix every bundle document uses for a sibling.  Split on
#: ``/schemas/`` rather than matched against a pinned version, so a bundle bump
#: does not have to be spelled here.
_REF_MARK = "/schemas/"

#: How deep an ``allOf``/``$ref`` chain is followed from the document the
#: manifest names to the nearest branch of the union.  Measured on 3.2: the
#: longest chain is ONE hop (``media-buy/buy-products-response.json`` ->
#: ``media-buy/media-buy-commitment-response.json``), so this is slack and not a
#: budget.
_MAX_CHAIN = 4


class WebhookResultUnresolvedError(ADCPWebhookError):
    """The envelope's ``(task_type, status)`` pair names no branch of the union.

    Raised rather than guessing: a guess here is the vacuous-branch behaviour
    this module exists to replace.  :attr:`document` carries the schema the pair
    DOES name where one exists but is not a branch of the webhook union -- that
    is a schema the caller can still validate against itself, and naming it is
    more use than a bare refusal.
    """

    def __init__(
        self,
        message: str,
        *,
        task_type: str,
        status: str,
        document: str | None = None,
    ) -> None:
        super().__init__(message)
        self.task_type = task_type
        self.status = status
        self.document = document


@dataclass(frozen=True)
class Resolution:
    """What one ``(task_type, status)`` pair resolves to.

    ``documents`` is every schema the pair NAMES, in derivation order, and
    ``branches`` is the union branches those schemas reach.  The length of
    ``branches`` is the whole of the pair's state, which is why it is one field
    and not three:

    * **one** -- resolved, and :attr:`model` is the class to validate against;
    * **none** -- the pair names a schema the webhook union does not contain,
      measured on 3.2 for 66 of the 153 named pairs, covering 22 of the 38 task
      types;
    * **more than one** -- ambiguous, and :attr:`model` is ``None``.

    **An ambiguous pair is reported and not silently resolved.**  There is no
    precedence to invent between two documents the derivation reaches equally:
    picking one would be the vacuous-branch guess again, one layer up.
    Measured on 3.2, no pair is ambiguous -- which is a measurement, not a
    reason to stop accumulating candidates.
    """

    task_type: str
    status: str
    documents: tuple[str, ...]
    branches: tuple[str, ...]
    model: type[AdCPBaseModel] | None
    #: ``"manifest"`` for a pair resolved through ``task_result_resolution``,
    #: ``"envelope"`` for one the envelope's own ``if``/``then`` names.
    source: str

    @property
    def document(self) -> str:
        """The schema the pair names, for the single-document case."""
        return self.documents[0]

    @property
    def ambiguous(self) -> bool:
        """Whether the pair names more than one branch of the union."""
        return len(self.branches) > 1


def _relative(reference: str) -> str | None:
    """``"https://…/schemas/3.2.7/core/x.json"`` -> ``"core/x.json"``."""
    if _REF_MARK not in reference:
        return None
    tail = reference.split(_REF_MARK, 1)[1]
    return tail.split("/", 1)[1] if "/" in tail else None


def _value(member: Any) -> str:
    """The wire string of an enum member, or the string itself."""
    return str(getattr(member, "value", member))


def _mapping(node: Any) -> dict[str, Any]:
    """``node`` where it is an object, and an empty one where it is not.

    A schema keyword's value is whatever the document put there, so every read
    below goes through this: ``(x or {}).get(...)`` is the same expression one
    truthy non-dict away from an ``AttributeError``.
    """
    return node if isinstance(node, dict) else {}


@lru_cache(maxsize=1)
def branch_documents() -> Mapping[str, type[AdCPBaseModel]]:
    """Every branch of the union, as ``document -> the class it is emitted as``.

    **Read off ``__adcp_schema__`` and off nothing else.**  Each of the union's
    branch classes carries its own position (``#/anyOf/<i>``) and inherits the
    referenced document's root class, which carries
    ``SchemaRef(document, "#")``.  Walking the mro for that root is what turns a
    branch POSITION into a branch DOCUMENT, and the root class -- not the
    position subclass -- is what the resolver validates against, because the
    document's own ``oneOf`` is what finally picks the shape.  Measured: 42
    documents, each with exactly one root class, from 46 branch classes (two
    positions are themselves three-branch ``oneOf``s).
    """
    out: dict[str, type[AdCPBaseModel]] = {}
    for branch in AdCPAsyncResponseData._branch_models:
        for ancestor in branch.__mro__:
            ref = ancestor.__dict__.get("__adcp_schema__")
            if ref is None or ref.pointer != "#" or ref.document == UNION_DOCUMENT:
                continue
            out.setdefault(ref.document, ancestor)
            break
    return MappingProxyType(out)


def _nearest_branch(document: str, version: str | None, depth: int = 0) -> str | None:
    """The branch document reachable from ``document`` through ``allOf``/``$ref``.

    The manifest names a task's own response schema, which is sometimes a
    wrapper: ``media-buy/buy-products-response.json`` is a title and a
    description over ``allOf: [media-buy/media-buy-commitment-response.json]``,
    and the union holds the inner one.  Following the chain is reading a
    reference, not deciding anything -- the same reading
    ``adcp.validation.schema_loader`` already does to compile a validator.
    """
    if document in branch_documents():
        return document
    if depth >= _MAX_CHAIN:
        return None
    node = get_named_schema_document(document, version=version)
    if node is None:
        return None
    references = [
        clause.get("$ref") for clause in (node.get("allOf") or []) if isinstance(clause, dict)
    ]
    references.append(node.get("$ref"))
    for reference in references:
        if not isinstance(reference, str):
            continue
        relative = _relative(reference)
        if relative is None:
            continue
        found = _nearest_branch(relative, version, depth + 1)
        if found is not None:
            return found
    return None


def _envelope_overrides(version: str | None) -> dict[tuple[str, str], str]:
    """The ``(task_type, status) -> document`` pairs the ENVELOPE states itself.

    ``core/mcp-webhook-payload.json`` carries an ``allOf`` of ``if``/``then``
    clauses, and this is the ONLY place in the bundle where the dependency the
    union lacks is written down.  Measured on 3.2 there is exactly ONE clause --
    ``task_type: get_products`` with ``result.status: rejected`` ->
    ``media-buy/get-products-rejected.json`` -- and it is what reaches the 42nd
    branch, which ``task_result_resolution`` alone never names.

    It is also the fix shape ``adcontextprotocol/adcp#8964`` asks for, already
    applied once by upstream's own hand, which is why this is read rather than
    re-stated: one clause today, more after the issue lands, and no edit here.

    **The clause tests ``result.status`` and not the envelope's ``status``**, and
    they are different fields.  Keyed on the inner one as written, because the
    envelope's ``result`` description -- "Task-specific payload matching the
    status" -- is the document saying the two agree.
    """
    envelope = get_named_schema_document(ENVELOPE_DOCUMENT, version=version)
    if envelope is None:
        return {}
    out: dict[tuple[str, str], str] = {}
    for clause in envelope.get("allOf") or []:
        if not isinstance(clause, dict):
            continue
        condition, consequent = clause.get("if"), clause.get("then")
        if not isinstance(condition, dict) or not isinstance(consequent, dict):
            continue
        asserted = _mapping(condition.get("properties"))
        produced = _mapping(consequent.get("properties"))
        task_type = _mapping(asserted.get("task_type")).get("const")
        status = _mapping(_mapping(asserted.get("result")).get("properties")).get("status")
        reference = _mapping(produced.get("result")).get("$ref")
        if not isinstance(task_type, str) or not isinstance(reference, str):
            continue
        value = _mapping(status).get("const")
        relative = _relative(reference)
        if isinstance(value, str) and relative is not None:
            out[(task_type, value)] = relative
    return out


@lru_cache(maxsize=4)
def resolution_table(version: str | None = None) -> Mapping[tuple[str, str], Resolution]:
    """``(task_type, status) -> Resolution``, derived from the bundle.

    **THE DERIVATION, in two readings and no hand-written branch list.**

    1. ``manifest.json``'s ``task_result_resolution`` -- the procedure
       ``core/tasks-get-response.json`` says consumers MUST use.  For each
       member of ``enums/task-type.json``: a terminal status
       (:data:`TERMINAL_STATUSES`) names
       ``terminal_schema_overrides[task_type]`` where present and
       ``tools[task_type].response_schema`` otherwise; every entry of
       ``tools[task_type].async_response_schemas`` names the status its own
       filename ends in, matched against ``enums/task-status.json`` so the
       suffix is a status value and not a guess at one.
    2. The envelope's own ``if``/``then`` clauses
       (:func:`_envelope_overrides`), which REPLACE a manifest answer where they
       speak -- a clause naming one pair is the more specific statement.

    Each named document is then followed through ``allOf``/``$ref`` to the
    nearest branch of the union (:func:`_nearest_branch`) and the branch's root
    class looked up in :func:`branch_documents`.

    **Measured on the 3.2 bundle**: the two readings reach **42 of 42** branch
    documents.  They name a document for **153 of the 342**
    ``task_type x status`` pairs; **87** of those resolve to a branch of the
    union, **66** name a schema the union does not contain, and **0** name more
    than one branch.  An unnamed pair -- ``canceled``, ``auth-required``,
    ``unknown``, and every status of a task whose manifest entry omits it -- is
    absent from this table, and :func:`resolve_result` raises for it.
    """
    manifest = get_named_schema_document("manifest.json", version=version)
    if manifest is None:
        return MappingProxyType({})
    resolution = _mapping(manifest.get("task_result_resolution"))
    overrides = _mapping(resolution.get("terminal_schema_overrides"))
    tools = _mapping(manifest.get("tools"))
    statuses = tuple(_value(member) for member in TaskStatus)

    # Every document a pair names, ACCUMULATED rather than overwritten: a pair
    # named twice is a measurement to report, and an assignment would hide it.
    named: dict[tuple[str, str], list[str]] = {}
    for member in TaskType:
        task_type = _value(member)
        tool = _mapping(tools.get(task_type))
        terminal = overrides.get(task_type) or tool.get("response_schema")
        if isinstance(terminal, str):
            for status in TERMINAL_STATUSES:
                named.setdefault((task_type, status), []).append(terminal)
        for entry in tool.get("async_response_schemas") or ():
            if not isinstance(entry, str):
                continue
            stem = entry.rsplit("/", 1)[-1].removesuffix(".json")
            for status in statuses:
                if stem.endswith(f"-async-response-{status}"):
                    named.setdefault((task_type, status), []).append(entry)
                    break
    # **The envelope REPLACES rather than adds**, which is the one precedence
    # in this derivation and the only one the bundle states: an ``if``/``then``
    # naming ONE pair is a more specific statement than a template over every
    # task_type, and reading it as a second candidate would manufacture an
    # ambiguity the document settles.
    overridden = _envelope_overrides(version)
    for pair, document in overridden.items():
        named[pair] = [document]

    branches = branch_documents()
    out: dict[tuple[str, str], Resolution] = {}
    for pair, documents in named.items():
        task_type, status = pair
        reached = []
        for document in documents:
            nearest = _nearest_branch(document, version)
            if nearest is not None and nearest not in reached:
                reached.append(nearest)
        out[pair] = Resolution(
            task_type=task_type,
            status=status,
            documents=tuple(documents),
            branches=tuple(reached),
            model=branches.get(reached[0]) if len(reached) == 1 else None,
            source="envelope" if pair in overridden else "manifest",
        )
    return MappingProxyType(out)


def _ordered(found: Any) -> tuple[Resolution, ...]:
    return tuple(sorted(found, key=lambda one: (one.task_type, one.status)))


def unresolved_pairs(version: str | None = None) -> tuple[Resolution, ...]:
    """Pairs that NAME a schema the webhook union does not contain.

    The measurement ``adcontextprotocol/adcp#8964``'s fix would shrink: the
    manifest knows exactly which schema a ``sync_accounts`` webhook carries, and
    ``core/async-response-data.json`` has no branch for it -- so the vacuous
    branches accept the payload and nothing notices.  Ordered, so a reader and a
    test see the same list.
    """
    table = resolution_table(version)
    return _ordered(one for one in table.values() if not one.branches)


def ambiguous_pairs(version: str | None = None) -> tuple[Resolution, ...]:
    """Pairs that name MORE THAN ONE branch of the union.

    Empty on the 3.2 bundle, and read rather than assumed empty: the derivation
    accumulates candidates instead of overwriting them precisely so this is a
    measurement a reader can take.  :func:`resolve_result` raises for every
    entry here rather than choosing.
    """
    return _ordered(one for one in resolution_table(version).values() if one.ambiguous)


def result_model(
    task_type: str | TaskType,
    status: str | TaskStatus,
    *,
    version: str | None = None,
) -> type[AdCPBaseModel] | None:
    """The branch class ``(task_type, status)`` names, or ``None``.

    ``None`` for a pair this table does not cover and for a pair whose named
    schema is not a branch of the union; :func:`resolve_result` is what tells
    the two apart in its message.
    """
    found = resolution_table(version).get((_value(task_type), _value(status)))
    return None if found is None else found.model


def resolve_result(
    payload: McpWebhookPayload | Mapping[str, Any],
    *,
    version: str | None = None,
) -> AdCPBaseModel | None:
    """The ``result`` of ``payload``, as the branch its envelope names.

    This is the second validation ``core/async-response-data.json`` requires of
    every caller:

        Because this shared webhook union is not tagged with the originating
        task type, callers MUST also validate a terminal result against that
        task or event's specific schema.

    ``payload`` is an already-validated :class:`McpWebhookPayload` or the raw
    mapping a receiver holds; either way ``task_type`` and ``status`` are
    required members of the envelope, so the pair is always present to read.

    Returns ``None`` when the envelope carries no ``result`` -- it is an
    optional member, and ``core/tasks-get-response.json`` says in as many words
    that "canceled tasks may omit it".

    **The BRANCH inside the branch is pydantic's to pick, not this function's.**
    What is returned is validated against the task's own root class, and where
    that document states a ``oneOf`` the payload selects the shape: a
    ``preview_creative`` result comes back as
    ``PreviewCreativeVariantResponse``, a ``build_creative`` one as
    ``BuildCreativeSuccess`` or ``BuildCreativeMultiSuccess``, and ``isinstance``
    holds against the root either way.

    Raises:
        WebhookResultUnresolvedError: the pair names no branch, names a schema
            the union does not contain, or names more than one branch.  Never a
            guess -- picking one of the 15 branches that admit any object is
            exactly the behaviour this replaces, and picking between two named
            branches would be the same move one layer up.
        pydantic.ValidationError: the pair named a branch and ``result`` does
            not satisfy it.  Propagated unchanged: that is a payload
            disagreeing with its own envelope, and it is a finding rather than
            something to recover from.
    """
    if isinstance(payload, McpWebhookPayload):
        task_type = _value(payload.task_type)
        status = _value(payload.status)
        result: Any = payload.result
        if isinstance(result, AdCPBaseModel):
            # The union already parsed it into whichever vacuous branch came
            # first; ``extra='allow'`` kept every member, so the dump is the
            # wire object again.  ``exclude_none`` because the schema admits no
            # ``null`` for an absent property.
            result = result.model_dump(mode="json", exclude_none=True)
    else:
        missing = [name for name in ("task_type", "status") if payload.get(name) is None]
        if missing:
            raise WebhookResultUnresolvedError(
                f"{ENVELOPE_DOCUMENT} requires {missing} and this payload states none of "
                "them, so there is no pair to resolve on",
                task_type=_value(payload.get("task_type")),
                status=_value(payload.get("status")),
            )
        task_type = _value(payload.get("task_type"))
        status = _value(payload.get("status"))
        result = payload.get("result")

    if result is None:
        return None

    found = resolution_table(version).get((task_type, status))
    if found is None:
        raise WebhookResultUnresolvedError(
            f"no branch of {UNION_DOCUMENT} is named by task_type={task_type!r} with "
            f"status={status!r}: manifest.task_result_resolution names a terminal schema "
            f"for {TERMINAL_STATUSES} and an async schema per entry of "
            "async_response_schemas, and this pair is in neither",
            task_type=task_type,
            status=status,
        )
    if found.ambiguous:
        raise WebhookResultUnresolvedError(
            f"task_type={task_type!r} with status={status!r} names more than one branch of "
            f"{UNION_DOCUMENT} -- {list(found.branches)}, through {list(found.documents)}. "
            "Reported rather than resolved: there is no precedence between them to read "
            "off the bundle, and picking one is the guess this function exists to refuse",
            task_type=task_type,
            status=status,
        )
    if found.model is None:
        raise WebhookResultUnresolvedError(
            f"task_type={task_type!r} with status={status!r} names {found.document!r}, "
            f"which is NOT a branch of {UNION_DOCUMENT} -- validate against that schema "
            "directly (adcontextprotocol/adcp#8964)",
            task_type=task_type,
            status=status,
            document=found.document,
        )
    return found.model.model_validate(result)


__all__ = [
    "ENVELOPE_DOCUMENT",
    "TERMINAL_STATUSES",
    "UNION_DOCUMENT",
    "Resolution",
    "WebhookResultUnresolvedError",
    "ambiguous_pairs",
    "branch_documents",
    "resolution_table",
    "resolve_result",
    "result_model",
    "unresolved_pairs",
]
