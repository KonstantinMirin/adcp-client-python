"""Make upstream's test constructions satisfy the documents they claim to construct.

Upstream's code generator dropped declared and ``allOf``-composed ``required``, so their
fixtures construct instances the PROTOCOL rejects and our schema-derived types correctly
refuse.  Established against the RAW documents under ``schemas/cache/3.2`` with
``jsonschema``'s ``Draft202012Validator`` over a registry of the same tree -- never
against our own IR, which would be circular.  This generalises
``add_required_status_to_fixtures.py`` from the one field ``status`` to EVERY
document-required field missing from a construction.

It does NOT replace that script, and the reason is measured rather than assumed.  The
population and the skips here are a strict superset of its.  The VALUE derivation is not:
for an arm that pins ``status`` the document gives a ``const`` and this script reads it
(``update-media-buy-response.json``'s submitted arm -> ``"submitted"``), but an ordinary
response composes the envelope through ``allOf`` and refines ``status`` only negatively --
``get-products-response.json`` says ``{"not": {"const": "rejected"}}`` and nothing more,
so the rules below correctly DECLINE where the status script read ``"completed"`` off the
envelope's prose and the loaded annotation.  Enum order is no help either:
``task-status.json`` begins at ``submitted``.  Both scripts therefore stay.

**THE POPULATION IS KEYED ON THE RESOLVED CLASS, NEVER ON THE CALLEE'S WORD.**  Every
``ast.Call`` under ``tests/`` is resolved through its own file's lexical bindings,
innermost enclosing scope outward -- these tests import inside the test function, and a
``ClassDef`` in the file SHADOWS an import of the same name.  A name only correlates with
a class; the binding IS the class.  Matching the bare callee word instead inflates the
count by a factor of three: ``Account`` alone has 195 name matches in this tree, 13 of
which bind ``adcp.decisioning.types.Account`` -- a plain ``@dataclass``, not a pydantic
model, which constructs happily today and raises ``TypeError`` on ``account_id``.

Two remedies fall out of the measurement, and WHICH ONE applies is derived, not listed:

* **REBIND** -- the file names the wrong class.  Before adding anything, the script looks
  for a class with the SAME ``__name__`` whose required set the call's keywords ALREADY
  satisfy.  When exactly one exists and it satisfies strictly more of the file's sites
  than the current binding does, the fixture is not incomplete: the import is wrong.  The
  IMPORT is rewritten and not one call site is touched.

  This is the whole of the ``Format`` population.  Two classes are named ``Format``:
  ``core/format.json``'s registered format, which requires ``format_id`` + ``name``, and
  the declaration, which requires ``format_kind`` + ``params``.  Upstream's public
  ``Format`` was the declaration; ours reserves the flat name for the registered format,
  which is correct -- so ``Format(format_kind="image", params={...})`` names the wrong
  class rather than omitting fields.  Adding ``format_id`` would have been wrong twice
  over: it would make the construction validate while meaning the wrong thing, and
  ``format_id`` does not even take a string (it wants a structured object).  The rebind
  target is reached by its domain path, which the import architecture sanctions exactly
  when "the flat ``adcp.types`` namespace cannot bind the name you need, because several
  schemas declare it."

* **ADD** -- no same-named alternative fits, so the fields really are missing.  Each one
  gets a value READ OFF ITS SUBSCHEMA, per field, never a default.  ``const`` leaves no
  choice; an ``enum`` reached through a ``$ref`` is resolved in the cache; ``minimum``
  gives the smallest admitted integer; and where the document says a field was "Renamed
  from ``X``" and the call still passes ``X``, that value is carried across -- which is
  how ``CheckGovernanceResponse(status="approved")`` yields ``verdict="approved"`` rather
  than the enum's first member.  Where the surrounding test already constructs the same
  class WITH the field, that literal wins over the document, so a derived
  ``confirmed_at`` matches the timestamp its neighbours use.  Every produced value is
  validated against its own subschema before it is written; one that does not validate is
  refused and printed rather than introduced as a new failure.

**A SITE WHOSE FIELD IS THE TEST'S SUBJECT IS NOT TOUCHED**, and every one is printed.
The ``status`` script declined any site whose enclosing scope read ``status`` back off the
name it bound, because supplying it turns ``assert buys.status == "completed"`` into a
tautology.  Generalising that to every field exposes two more shapes of the same mistake,
and they matter more than the site count:

* ``# type: ignore[call-arg]`` on the statement.  That is mypy's OWN name for a missing
  required named argument: upstream annotated the omission as deliberate.  It marks
  ``IdempotencySupported(supported=True)`` under "supported arm rejects missing
  replay_ttl_seconds" and ``VersionUnsupportedDetails(adcp_version="3.2")``.
* ANY construction under ``pytest.raises``.  The test's subject there is the error, and
  a missing required field is one of its causes, so supplying the field can turn a
  passing test red.  Sometimes the source says so -- ``test_typed_success_requires_-
  revision`` names the field, and ``assert "agent_url" in str(exc_info.value)`` asserts
  on it.  **But the source is not sufficient, and this was MEASURED, not assumed.**  An
  earlier pass skipped only the sites that named the field and edited the rest; that
  broke ``test_typed_success_rejects_async_task_status`` on both media-buy arms, because
  ``CreateMediaBuySuccessResponse(status="working", ...)`` raises ONLY while ``revision``
  and ``confirmed_at`` are absent -- with them supplied the async status is accepted and
  nothing is raised.  Those two tests pass today for a reason they do not name, which is
  worth reporting and is a defect in the success arm's ``status`` pin, not in the
  fixture.  So every ``pytest.raises`` site is declined, and the ones whose source gives
  the field away are merely the ones where that is visible without running.

The skips gate ADD only -- a REBIND supplies nothing, which is what lets
``test_params_is_required`` grade ``params`` rather than ``format_id``.

Run ``--check`` to print the plan and touch nothing.
"""

from __future__ import annotations

import argparse
import ast
import collections
import json
import pathlib
import re
import sys
import typing

import pydantic

ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
CACHE = ROOT / "schemas" / "cache" / "3.2"

#: Scopes that can carry a binding. ``Module`` is the outermost.
SCOPES = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)

#: ``line-length`` in ``pyproject.toml``, which governs ruff and black alike.
LIMIT = 100

#: mypy's own name for "missing a required named argument". Upstream writes it where the
#: omission is the point, so it is a deliberate-omission marker and not noise.
DELIBERATE = "type: ignore[call-arg]"

#: A document ``$ref`` is absolute and version-pinned; the cache is one directory.
REF = re.compile(r"^https://adcontextprotocol\.org/schemas/[^/]+/(?P<rel>.+)$")

#: "Renamed from `status` in 3.1 to free the top-level `status` key [...]" -- the document
#: telling us which key the caller is still writing.
RENAMED = re.compile(r"[Rr]enamed from [`'\"]?(?P<old>[a-z_][a-z0-9_]*)[`'\"]?")

#: "On a successful response, one of: active, pending_handoff, or complete." -- the
#: document naming the members a success arm may carry, in its own order of preference.
SUCCESS = re.compile(r"one of:\s*(?P<members>[a-z_,\s]+?)(?:\.|$)")

#: 'Synchronous tasks [...] normally emit `status: "completed"`' -- the document naming
#: one member as the ordinary value. Enum ORDER does not say that: ``task-status.json``
#: begins at ``submitted``, so the first member would be exactly the wrong answer for the
#: envelope's own normal case.
NORMALLY = re.compile(r"normally[^.]*?[`\"](?P<member>[a-z][a-z0-9_-]*)[`\"]")


# --------------------------------------------------------------------------- bindings


class Binding(typing.NamedTuple):
    """What one name denotes in one scope, and the statement that bound it."""

    kind: str  # "import" | "local"
    module: str | None
    attribute: str | None
    node: ast.stmt


def scope_bindings(scope: ast.AST) -> dict[str, Binding]:
    """Every name bound DIRECTLY in one scope, nested scopes excluded.

    Nested scopes are skipped so the caller can walk outward and let an inner
    ``from adcp.decisioning import Account`` shadow an outer ``from adcp.types import
    Account``; both spellings occur in the same file, which is why this cannot be a flat
    per-file map. A ``ClassDef`` or ``FunctionDef`` is recorded too: a class the file
    DEFINES shadows an import of its name, and resolving past it would attribute a test's
    own subclass to the schema class it happens to be named after.
    """
    out: dict[str, Binding] = {}

    def walk(statements: list[ast.stmt]) -> None:
        for statement in statements:
            if isinstance(statement, ast.ImportFrom):
                if statement.level or statement.module is None:
                    continue  # relative import: not resolvable by module name alone
                for alias in statement.names:
                    name = alias.asname or alias.name
                    out[name] = Binding("import", statement.module, alias.name, statement)
            elif isinstance(statement, ast.Import):
                for alias in statement.names:
                    if alias.asname:
                        out[alias.asname] = Binding("import", alias.name, None, statement)
                    else:
                        head = alias.name.split(".")[0]
                        out[head] = Binding("import", head, None, statement)
            elif isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                out[statement.name] = Binding("local", None, None, statement)
            else:
                for _, value in ast.iter_fields(statement):
                    if isinstance(value, list):
                        walk([v for v in value if isinstance(v, ast.stmt)])
                    elif isinstance(value, ast.stmt):
                        walk([value])

    walk(getattr(scope, "body", []))
    return out


def _import(module_name: str) -> object | None:
    import importlib

    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


class Resolver:
    """Resolves a callee to the object it denotes, through one file's own bindings."""

    def __init__(self, tree: ast.Module) -> None:
        self.parent: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                self.parent[child] = node
        self.cache: dict[ast.AST, dict[str, Binding]] = {}

    def binding(self, node: ast.AST, name: str) -> Binding | None:
        scope: ast.AST | None = node
        while scope is not None:
            if isinstance(scope, SCOPES):
                if scope not in self.cache:
                    self.cache[scope] = scope_bindings(scope)
                found = self.cache[scope].get(name)
                if found is not None:
                    return found
            scope = self.parent.get(scope)
        return None

    def callee(self, call: ast.Call) -> tuple[object, Binding, str] | None:
        """``(object, binding, attribute)`` for ``call.func``, or ``None``.

        ``attribute`` is the name the object is known by at its binding, which is what a
        rewritten import has to spell.
        """
        func = call.func
        if isinstance(func, ast.Name):
            found = self.binding(call, func.id)
            if found is None or found.kind != "import":
                return None
            if found.attribute is None:  # `import adcp` used bare: not a class
                return None
            module = _import(found.module or "")
            obj = getattr(module, found.attribute, None) if module else None
            return (obj, found, found.attribute) if obj is not None else None
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            base = self.binding(call, func.value.id)
            if base is None or base.kind != "import":
                return None
            name = base.module if base.attribute is None else f"{base.module}.{base.attribute}"
            module = _import(name or "")
            obj = getattr(module, func.attr, None) if module else None
            return (obj, base, func.attr) if obj is not None else None
        return None

    def scope_of(self, node: ast.AST) -> ast.AST | None:
        scope: ast.AST | None = self.parent.get(node)
        while scope is not None and not isinstance(scope, SCOPES):
            scope = self.parent.get(scope)
        return scope

    def statement_of(self, node: ast.AST) -> ast.stmt | None:
        current: ast.AST | None = node
        while current is not None and not isinstance(current, ast.stmt):
            current = self.parent.get(current)
        return typing.cast("ast.stmt | None", current)

    def inside_raises(self, node: ast.AST) -> ast.With | None:
        """The ``with pytest.raises(...)`` this node sits under, if any."""
        current: ast.AST | None = node
        while current is not None:
            if isinstance(current, (ast.With, ast.AsyncWith)):
                for item in current.items:
                    text = ast.unparse(item.context_expr)
                    if "raises" in text:
                        return typing.cast("ast.With", current)
            current = self.parent.get(current)
        return None


# ------------------------------------------------------------------------ the document


_DOCUMENTS: dict[str, dict[str, object]] = {}


def document(relative: str) -> dict[str, object] | None:
    if relative not in _DOCUMENTS:
        path = CACHE / relative
        try:
            _DOCUMENTS[relative] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    return _DOCUMENTS[relative]


def schema_ref(model: type[pydantic.BaseModel]) -> str | None:
    """The document a model was generated from, found along its MRO.

    ``canonical_creative``'s hand-written arms carry no marker of their own; the generated
    wire model they subclass does, which is the document they must satisfy.
    """
    for base in model.__mro__:
        marker = base.__dict__.get("__adcp_schema__")
        if marker is not None and getattr(marker, "document", None):
            return str(marker.document)
    return None


def subschemas(node: object, field: str) -> list[dict[str, object]]:
    """Every subschema that declares ``field`` as one of its own ``required`` properties.

    A document is a tree of ``$defs`` / ``oneOf`` / ``allOf`` arms, so the field's
    definition is wherever it is both declared and required -- not necessarily at ``#``.
    """
    found: list[dict[str, object]] = []
    if isinstance(node, dict):
        properties = node.get("properties")
        required = node.get("required")
        if (
            isinstance(properties, dict)
            and field in properties
            and isinstance(required, list)
            and field in required
        ):
            found.append(node)
        for value in node.values():
            found.extend(subschemas(value, field))
    elif isinstance(node, list):
        for value in node:
            found.extend(subschemas(value, field))
    return found


def field_schema(
    model: type[pydantic.BaseModel], field: str
) -> tuple[dict[str, object], str] | None:
    """``(subschema for one field, document)``, chosen by fit to the model's own fields.

    A document can require the same field in several arms (``check-governance-response``
    requires ``verdict`` in six).  The arm meant is the one whose ``properties`` overlap
    the model's field set most: the ``if`` guards that pin ``verdict`` to one ``const``
    declare that property alone, while the arm the class was generated from declares all
    of them.
    """
    relative = schema_ref(model)
    if relative is None:
        return None
    root = document(relative)
    if root is None:
        return None
    names = set(model.model_fields)
    best: tuple[int, dict[str, object]] | None = None
    for candidate in subschemas(root, field):
        properties = typing.cast("dict[str, object]", candidate.get("properties", {}))
        score = len(names & set(properties))
        if best is None or score > best[0]:
            best = (score, typing.cast("dict[str, object]", properties[field]))
    return (best[1], relative) if best else None


def resolved(schema: dict[str, object]) -> dict[str, object]:
    """One ``$ref`` hop into the cache, so an enum behind a reference is readable."""
    reference = schema.get("$ref")
    if not isinstance(reference, str):
        return schema
    match = REF.match(reference)
    if match is None:
        return schema
    target = document(match.group("rel"))
    if target is None:
        return schema
    merged = {**target, **{k: v for k, v in schema.items() if k != "$ref"}}
    return merged


# --------------------------------------------------------------------- derived values


def literal(value: object) -> str:
    """Source text for a derived value. ``repr`` with double quotes, as black writes."""
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, bool):
        return "True" if value else "False"
    return json.dumps(value)


def correlated(tree: ast.Module, resolver: Resolver, model: type, field: str) -> str | None:
    """The source text this file already uses for ``field`` on the same class.

    "Where the surrounding test supplies a correlated value, match it": a derived
    ``confirmed_at`` should be the timestamp its neighbours write, not a fresh instant.
    """
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        found = resolver.callee(node)
        if found is None or found[0] is not model:
            continue
        for keyword in node.keywords:
            if keyword.arg == field and isinstance(keyword.value, ast.Constant):
                return literal(keyword.value.value)
    return None


def identifier_suffix(tree: ast.Module) -> str:
    """The file's own convention for an opaque id, read off its ``*_id`` literals.

    ``check_id="chk_123"``, ``outcome_id="out_123"``, ``plan_id="plan_123"`` -- a required
    identifier with no ``pattern`` and no example in the document takes the suffix its
    neighbours use rather than one this script invents.
    """
    counts: collections.Counter[str] = collections.Counter()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.keyword)
            and node.arg
            and node.arg.endswith("_id")
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and "_" in node.value.value
        ):
            counts[node.value.value.rsplit("_", 1)[1]] += 1
    return counts.most_common(1)[0][0] if counts else "1"


def derive(
    schema: dict[str, object],
    call: ast.Call,
    tree: ast.Module,
    resolver: Resolver,
    model: type,
    field: str,
) -> tuple[str, str] | None:
    """``(source text, the rule that produced it)`` for one missing field."""
    schema = resolved(schema)
    description = str(schema.get("description", ""))
    types = schema.get("type")
    types = types if isinstance(types, list) else [types]

    if "const" in schema:
        return literal(schema["const"]), f"`const` in the document: {schema['const']!r}"

    members = schema.get("enum")
    if isinstance(members, list) and members:
        rename = RENAMED.search(description)
        if rename:
            old = rename.group("old")
            for keyword in call.keywords:
                if (
                    keyword.arg == old
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value in members
                ):
                    return literal(keyword.value.value), (
                        f"the document says this field was renamed from `{old}`, which"
                        f" this call still passes as {keyword.value.value!r}"
                    )
        normal = NORMALLY.search(description)
        if normal and normal.group("member") in members:
            return literal(normal.group("member")), (
                f"the member the document calls the normal one: {normal.group(0)!r}"
            )
        if schema.get("default") in members:
            return literal(schema["default"]), "the document's own `default`"
        examples = schema.get("examples")
        if isinstance(examples, list) and examples and examples[0] in members:
            return literal(examples[0]), "the document's first `examples` entry"
        success = SUCCESS.search(description)
        if success:
            for word in re.split(r"[,\s]+(?:or\s+)?", success.group("members")):
                if word in members:
                    return literal(word), (
                        "the first member the document names for a successful"
                        f" response: {success.group('members').strip()!r}"
                    )
        return literal(members[0]), f"first member of the document's enum {members!r}"

    examples = schema.get("examples")
    if isinstance(examples, list) and examples:
        return literal(examples[0]), "the document's first `examples` entry"

    reuse = correlated(tree, resolver, model, field)

    if "integer" in types or "number" in types:
        if reuse:
            return reuse, "the value this file already writes for the field"
        if "minimum" in schema:
            return literal(schema["minimum"]), f"the document's `minimum` ({schema['minimum']})"
        if "exclusiveMinimum" in schema:
            bound = typing.cast("int", schema["exclusiveMinimum"])
            return literal(bound + 1), f"one past the document's `exclusiveMinimum` ({bound})"
        return None

    if "boolean" in types:
        if reuse:
            return reuse, "the value this file already writes for the field"
        # "Whether the offering is currently available", "Whether session was successfully
        # terminated": the document frames these as the success predicate of the very arm
        # that requires them, and these fixtures are that arm.
        return "True", "the affirmative of the success arm this response is"

    if "string" in types:
        if reuse:
            return reuse, "the value this file already writes for the field"
        if schema.get("format") == "date-time":
            return None  # no instant is derivable; a correlated one or nothing
        if "pattern" in schema:
            return None  # a value this script invented could violate it
        stem = field[:-3] if field.endswith("_id") else field
        return f'"{stem}_{identifier_suffix(tree)}"', (
            "an opaque identifier with no `pattern` and no example, spelled with the"
            " suffix this file's other identifiers use"
        )

    return None


def validates(schema: dict[str, object], value: object) -> bool:
    """Does the derived value satisfy its own subschema, read from the raw document?

    A ``pattern`` or ``format: date-time`` this script violated would be a new failure it
    introduced, so nothing is written that the document has not accepted first.
    """
    try:
        import jsonschema
        import referencing
        import referencing.jsonschema
    except ImportError:
        print("jsonschema is not importable -- values go out unverified", file=sys.stderr)
        return True

    draft = referencing.jsonschema.DRAFT202012

    def retrieve(uri: str) -> referencing.Resource:
        match = REF.match(uri)
        if match is None:
            raise referencing.exceptions.NoSuchResource(ref=uri)
        loaded = document(match.group("rel"))
        if loaded is None:
            raise referencing.exceptions.NoSuchResource(ref=uri)
        return referencing.Resource.from_contents(loaded, default_specification=draft)

    registry = referencing.Registry(retrieve=retrieve)  # type: ignore[call-arg]
    validator = jsonschema.Draft202012Validator(
        schema, registry=registry, format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER
    )
    return not list(validator.iter_errors(value))


# ---------------------------------------------------------------------- the population


class Gap(typing.NamedTuple):
    path: pathlib.Path
    call: ast.Call
    model: type[pydantic.BaseModel]
    binding: Binding
    attribute: str
    missing: tuple[str, ...]


def gaps(path: pathlib.Path, tree: ast.Module, resolver: Resolver) -> list[Gap]:
    """Every resolved keyword construction in one file that the document would refuse."""
    out: list[Gap] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        found = resolver.callee(node)
        if found is None:
            continue
        model, binding, attribute = found
        if not (isinstance(model, type) and issubclass(model, pydantic.BaseModel)):
            continue
        if any(isinstance(argument, ast.Starred) for argument in node.args):
            continue
        if any(keyword.arg is None for keyword in node.keywords):
            continue
        given = {keyword.arg for keyword in node.keywords}
        for name, field in model.model_fields.items():
            if field.alias and field.alias in given:
                given.add(name)
        missing = tuple(
            sorted(name for name, field in model.model_fields.items() if field.is_required())
        )
        missing = tuple(name for name in missing if name not in given)
        if missing:
            out.append(Gap(path, node, model, binding, attribute, missing))
    return out


def satisfied(call: ast.Call, model: type[pydantic.BaseModel]) -> bool:
    """Would ``model``'s required set already be covered by this call's keywords?"""
    given = {keyword.arg for keyword in call.keywords}
    return all(name in given for name, field in model.model_fields.items() if field.is_required())


def same_named(model: type[pydantic.BaseModel]) -> list[type[pydantic.BaseModel]]:
    """Every OTHER loaded class sharing this one's ``__name__``.

    Nothing is listed: the alternatives are read out of the loaded modules, so a schema
    bump that merges, splits or renames a class moves through here with nothing edited.
    """
    out: list[type[pydantic.BaseModel]] = []
    for name, module in list(sys.modules.items()):
        if module is None or not (name == "adcp" or name.startswith("adcp.")):
            continue
        for value in list(vars(module).values()):
            if (
                isinstance(value, type)
                and issubclass(value, pydantic.BaseModel)
                and value.__name__ == model.__name__
                and value is not model
                and value not in out
            ):
                out.append(value)
    return out


# ------------------------------------------------------------------------- the remedies


class Rebind(typing.NamedTuple):
    binding: Binding
    attribute: str
    was: type[pydantic.BaseModel]
    now: type[pydantic.BaseModel]
    covered: int
    total: int
    base: str | None  # the module alias in `adcp.Format(...)`, when attribute-bound
    held: tuple[str, ...] = ()  # references left alone because they ARE the subject


class Add(typing.NamedTuple):
    line: int
    end_line: int
    paren_column: int
    end_column: int
    arguments: tuple[tuple[int, int], ...]
    single_line: bool
    callee: str
    model: str
    document: str
    fields: tuple[tuple[str, str, str], ...]  # (field, source text, rule)


def rebind_for(path: pathlib.Path, tree: ast.Module, resolver: Resolver, found: list[Gap]):
    """One REBIND per binding whose sites a same-named class fits better than it does."""
    plans: dict[tuple[int, str], Rebind] = {}
    by_binding: dict[tuple[int, str], list[Gap]] = collections.defaultdict(list)
    for gap in found:
        by_binding[(id(gap.binding.node), gap.attribute)].append(gap)

    # Every site bound to the same statement and name, gap or not: a rebind moves them
    # all, so the comparison has to see the ones that are already complete.
    everything: dict[tuple[int, str], list[tuple[ast.Call, type]]] = collections.defaultdict(list)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        resolution = resolver.callee(node)
        if resolution is None:
            continue
        model, binding, attribute = resolution
        if isinstance(model, type) and issubclass(model, pydantic.BaseModel):
            everything[(id(binding.node), attribute)].append((node, model))

    for key, group in by_binding.items():
        model = group[0].model
        sites = everything[key]
        here = sum(1 for call, current in sites if satisfied(call, current))
        fits = [
            alternative
            for alternative in same_named(model)
            if sum(1 for call, _ in sites if satisfied(call, alternative)) > here
        ]
        if len(fits) != 1:
            continue
        alternative = fits[0]
        covered = sum(1 for call, _ in sites if satisfied(call, alternative))
        binding = group[0].binding
        base = None
        if binding.attribute is None or binding.attribute != group[0].attribute:
            # `import adcp` + `adcp.Format(...)`: the name lives on the module, so the
            # rewrite has to introduce a binding and retarget the attribute.
            base = next(
                (
                    node.func.value.id
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.attr == group[0].attribute
                    and resolver.binding(node, node.func.value.id) is binding
                ),
                None,
            )
            if base is None:
                continue
        plan = Rebind(binding, group[0].attribute, model, alternative, covered, len(sites), base)
        if base is not None:
            plan = plan._replace(held=tuple(attribute_spots(tree, resolver, plan)[1]))
        plans[key] = plan
    return plans


def inspects_binding(resolver: Resolver, node: ast.AST) -> bool:
    """Is this reference an assertion ABOUT the name rather than a use OF the class?

    ``assert adcp.Format is not adcp.ProductFormatDeclaration`` and ``assert "format_kind"
    in adcp.Format.model_fields`` are upstream asserting what the ROOT SURFACE binds.
    Retargeting those would make them pass by changing their subject, and would erase the
    evidence that our flat ``Format`` differs from upstream's -- which is a defect in
    ``src/adcp/types``, not in the fixture.  Same principle as the ADD skips: where the
    thing under test is the thing being changed, leave it and say so.
    """
    inside = False
    current: ast.AST | None = node
    while current is not None:
        if isinstance(current, ast.Assert):
            inside = True
            break
        current = resolver.parent.get(current)
    if not inside:
        return False
    parent = resolver.parent.get(node)
    if isinstance(parent, ast.Attribute) and (
        parent.attr == "model_fields" or parent.attr.startswith("__")
    ):
        return True
    return isinstance(parent, ast.Compare) and any(
        isinstance(op, (ast.Is, ast.IsNot)) for op in parent.ops
    )


def attribute_spots(
    tree: ast.Module, resolver: Resolver, plan: Rebind
) -> tuple[list[tuple[int, int, int]], list[str]]:
    """``(references to retarget, references held back)`` for an attribute-bound rebind."""
    spots: list[tuple[int, int, int]] = []
    held: list[str] = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Attribute)
            and node.attr == plan.attribute
            and isinstance(node.value, ast.Name)
            and node.value.id == plan.base
            and resolver.binding(node, node.value.id) is plan.binding
        ):
            continue
        if inspects_binding(resolver, node):
            held.append(f"L{node.lineno} {ast.unparse(node)}")
            continue
        spots.append((node.lineno, node.col_offset, node.end_col_offset or 0))
    return spots, held


def add_for(gap: Gap, tree: ast.Module, resolver: Resolver) -> tuple[Add | None, list[str]]:
    """One ADD for a gap, plus the reasons any of its fields were declined."""
    notes: list[str] = []
    call = gap.call
    scope = resolver.scope_of(call)
    statement = resolver.statement_of(call)
    raises = resolver.inside_raises(call)
    where = f"{gap.path.relative_to(ROOT)}:{call.lineno}"
    spelling = ast.unparse(call.func)

    deliberate = False
    if statement is not None:
        source = read_lines(gap.path)
        window = source[statement.lineno - 1 : (statement.end_lineno or statement.lineno)]
        deliberate = any(DELIBERATE in line for line in window)

    words: set[str] = set()
    name = ""
    if isinstance(scope, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name = scope.name
    if raises is not None and scope is not None:
        words = {
            token
            for node in ast.walk(scope)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
            for token in re.split(r"[^a-z0-9_]+", node.value.lower())
        }

    bound = None
    parent = resolver.parent.get(call)
    if isinstance(parent, ast.Assign) and len(parent.targets) == 1:
        if isinstance(parent.targets[0], ast.Name):
            bound = parent.targets[0].id
    elif isinstance(parent, ast.AnnAssign) and isinstance(parent.target, ast.Name):
        bound = parent.target.id

    wanted: list[tuple[str, str, str]] = []
    for field in gap.missing:
        if deliberate:
            notes.append(f"{where} {spelling}.{field}: `{DELIBERATE}` -- upstream marked the")
            notes.append("        omission deliberate; mypy's own name for this is the marker")
            continue
        if bound is not None and scope is not None and _reads_back(scope, bound, field):
            notes.append(f"{where} {spelling}.{field}: the scope reads `{bound}.{field}` back, so")
            notes.append("        supplying it would make the test's own assertion vacuous")
            continue
        if raises is not None:
            # ``_``-delimited, so ``test_..._requires_revision_and_confirmed_at`` names
            # BOTH its fields; splitting on ``_`` would find only the single-word one.
            named = re.search(rf"(?:^|_){re.escape(field)}(?:_|$)", name) is not None
            why = (
                f"named in `{name}` or its strings"
                if named or field in words
                else "load-bearing for the expected error, which only running shows"
            )
            notes.append(f"{where} {spelling}.{field}: a `pytest.raises` whose error this")
            notes.append(f"        field is -- {why}")
            continue
        schema = field_schema(gap.model, field)
        if schema is None:
            notes.append(f"{where} {spelling}.{field}: no subschema found in the document")
            continue
        value = derive(schema[0], call, tree, resolver, gap.model, field)
        if value is None:
            notes.append(
                f"{where} {spelling}.{field}: no value derivable from {schema[1]}"
                f" ({json.dumps(resolved(schema[0]))[:80]})"
            )
            continue
        if not validates(resolved(schema[0]), json.loads(value[0].replace("True", "true"))):
            notes.append(f"{where} {spelling}.{field}: derived {value[0]} fails its own subschema")
            continue
        wanted.append((field, value[0], value[1]))

    if not wanted:
        return None, notes
    relative = schema_ref(gap.model) or "?"
    return (
        Add(
            line=call.lineno,
            end_line=call.end_lineno or call.lineno,
            paren_column=call.func.end_col_offset or 0,
            end_column=call.end_col_offset or 0,
            arguments=tuple(
                sorted(
                    (argument.col_offset, argument.end_col_offset or 0)
                    for argument in (*call.args, *call.keywords)
                )
            ),
            single_line=call.lineno == (call.end_lineno or call.lineno),
            callee=spelling,
            model=f"{gap.model.__module__}.{gap.model.__qualname__}",
            document=relative,
            fields=tuple(wanted),
        ),
        notes,
    )


def _reads_back(scope: ast.AST, name: str, field: str) -> bool:
    for node in ast.walk(scope):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == field
            and isinstance(node.value, ast.Name)
            and node.value.id == name
        ):
            return True
    return False


# ----------------------------------------------------------------------------- rewriting


def read_lines(path: pathlib.Path) -> list[str]:
    """One file's lines, split the way the TOKENIZER splits them: on ``\\n`` only.

    ``str.splitlines()`` also breaks on U+2028 LINE SEPARATOR, U+2029, ``\\x0b`` and
    ``\\x0c`` -- and ``test_canonical_formats_v2_to_v1`` holds a literal U+2028 inside a
    string, because scrubbing it is what that test is about.  Splitting there and
    rejoining on ``\\n`` silently cut the line in half and left the file unparseable.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return lines


def indent_of(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def apply_add(lines: list[str], add: Add) -> list[str]:
    """Insert the derived keywords into one call, with the derivation above it."""
    head = add.line - 1
    pad = indent_of(lines[head])
    names = ", ".join(f"`{field}`" for field, _, _ in add.fields)
    verb = "is" if len(add.fields) == 1 else "are"
    it = "it" if len(add.fields) == 1 else "them"
    comment = _wrap(
        [
            f"{names} {verb} required by {add.document}. Upstream's generator dropped"
            f" declared and allOf-composed `required`, so their fixtures omit {it}.",
            *(f"{field}={value} -- {rule}." for field, value, rule in add.fields),
        ],
        pad,
    )

    keywords = [f"{field}={value}" for field, value, _ in add.fields]
    if add.single_line:
        column = add.paren_column
        text = lines[head]
        assert text[column] == "(", text  # `func(` -- the paren follows the callee
        rest = text[column + 1 :]
        tail = "" if rest.startswith(")") else ", "
        inline = f"{text[: column + 1]}{', '.join(keywords)}{tail}{rest}"
        if len(inline) <= LIMIT:
            lines[head] = inline
        else:
            inner = pad + "    "
            arguments = [f"{inner}{keyword}," for keyword in keywords]
            arguments += [f"{inner}{text[start:end]}," for start, end in add.arguments]
            lines[head : head + 1] = [
                text[: column + 1],
                *arguments,
                f"{pad}{text[add.end_column - 1 :]}",
            ]
    else:
        inner = indent_of(lines[head + 1]) if len(lines) > head + 1 else pad + "    "
        for offset, keyword in enumerate(keywords):
            lines.insert(head + 1 + offset, f"{inner}{keyword},")
    lines[head:head] = comment
    return lines


def _wrap(paragraphs: list[str], pad: str) -> list[str]:
    """One ``# `` comment per paragraph, wrapped to the repository's line length."""
    out: list[str] = []
    for paragraph in paragraphs:
        current = f"{pad}#"
        for word in paragraph.split():
            if len(current) + len(word) + 1 > LIMIT:
                out.append(current)
                current = f"{pad}#   {word}"
            else:
                current = f"{current} {word}"
        out.append(current)
    return out


def apply_rebind(
    lines: list[str], plan: Rebind, tree: ast.Module, resolver: Resolver
) -> tuple[str, str]:
    """Point one binding at the class the file's keywords fit; return the import to place.

    The name is withdrawn from where it is bound now, and the caller re-parses before
    placing the replacement -- the insertion point has to be computed against the lines
    as they will actually be, not as they were before the withdrawal.
    """
    statement = plan.binding.node
    module = plan.now.__module__

    if plan.base is None:
        assert isinstance(statement, ast.ImportFrom)
        pad = " " * statement.col_offset
        staying = [a for a in statement.names if (a.asname or a.name) != plan.attribute]
        start = statement.lineno - 1
        end = statement.end_lineno or statement.lineno
        if staying:
            words = [
                a.name if not a.asname else f"{a.name} as {a.asname}"
                for a in sorted(staying, key=lambda a: a.name)
            ]
            flat = f"{pad}from {statement.module} import {', '.join(words)}"
            if len(flat) <= LIMIT:
                lines[start:end] = [flat]
            else:
                lines[start:end] = [
                    f"{pad}from {statement.module} import (",
                    *(f"{pad}    {word}," for word in words),
                    f"{pad})",
                ]
        else:
            lines[start:end] = []
        return module, plan.attribute

    # `adcp.Format(...)`: retarget every `adcp.Format` in the file except the ones that
    # assert what the root surface binds, then bind the bare name.
    spots, held = attribute_spots(tree, resolver, plan)
    for line, start, end in sorted(spots, reverse=True):
        text = lines[line - 1]
        lines[line - 1] = text[:start] + plan.attribute + text[end:]
    if not held and _spent(tree, resolver, plan):
        # The module was imported for this one name. Leaving `import adcp` behind is an
        # F401 the rewrite would be introducing, and ruff has `"F"` selected.
        del lines[statement.lineno - 1 : (statement.end_lineno or statement.lineno)]
    return module, plan.attribute


def _spent(tree: ast.Module, resolver: Resolver, plan: Rebind) -> bool:
    """Was the module imported for nothing but the name the rebind just retargeted?"""
    statement = plan.binding.node
    if not (isinstance(statement, ast.Import) and len(statement.names) == 1):
        return False
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Name) and node.id == plan.base):
            continue
        if not isinstance(node.ctx, ast.Load):
            continue
        parent = resolver.parent.get(node)
        if isinstance(parent, ast.Attribute) and parent.attr == plan.attribute:
            continue  # this reference is the one being retargeted
        return False
    return True


def place_import(lines: list[str], tree: ast.Module, module: str, name: str) -> None:
    """Bind ``name`` from ``module`` at the sorted position among the file's own imports.

    ``[tool.ruff.lint] select`` carries ``"I"``, so an import appended after the block it
    belongs in would be a finding. Ruff's own ``--fix`` is not used for this: these files
    are ALREADY ``I001`` under the pinned ruff, so running it would reorder lines this
    change has no business touching while nothing it reports is new. Merging into an
    existing import of the same module, or sorting in beside its package's neighbours,
    leaves the block exactly as un-sorted as it was and no more.
    """
    siblings = [
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom)) and node.col_offset == 0
    ]
    package = module.split(".")[0]

    for node in siblings:
        if isinstance(node, ast.ImportFrom) and node.module == module and not node.level:
            words = sorted({*(a.asname or a.name for a in node.names), name})
            flat = f"from {module} import {', '.join(words)}"
            start, end = node.lineno - 1, node.end_lineno or node.lineno
            if len(flat) <= LIMIT:
                lines[start:end] = [flat]
            else:
                lines[start:end] = [
                    f"from {module} import (",
                    *(f"    {word}," for word in words),
                    ")",
                ]
            return

    def key(node: ast.Import | ast.ImportFrom) -> str:
        if isinstance(node, ast.ImportFrom):
            return node.module or ""
        return node.names[0].name

    family = [node for node in siblings if key(node).split(".")[0] == package]
    after = [node for node in family if key(node) < module]
    if after:
        at = max(node.end_lineno or node.lineno for node in after)
    elif family:
        at = min(node.lineno for node in family) - 1
    else:
        at = max((node.end_lineno or node.lineno for node in siblings), default=0)
    lines.insert(at, f"from {module} import {name}")


def reformat(paths: list[pathlib.Path]) -> None:
    """Hand the edited files to the repository's own black, at its own settings.

    Inserting a first argument into a call changes what black wants of the LAST one (a
    magic trailing comma it did not need while the argument was alone), and an exploded
    nested call is a shape black re-indents from the outside in. Replicating that here
    would be a second formatter to keep in step with ``[tool.black]``.
    """
    try:
        import black
    except ImportError:
        print("black is not importable -- run `black` over the edited files", file=sys.stderr)
        return
    mode = black.Mode(line_length=LIMIT, target_versions={black.TargetVersion.PY310})
    for path in paths:
        source = path.read_text(encoding="utf-8")
        try:
            formatted = black.format_file_contents(source, fast=False, mode=mode)
        except black.NothingChanged:
            continue
        path.write_text(formatted, encoding="utf-8")


# ---------------------------------------------------------------------------- the run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="print the plan, write nothing")
    arguments = parser.parse_args()

    # Realize the lazy public facade and the hand-written canonical surface, so
    # ``same_named`` can see every class a test could have meant.
    import adcp
    import adcp.types
    import adcp.types.canonical_creative  # noqa: F401
    import adcp.types.legacy  # noqa: F401

    _ = adcp.types.Format

    total = complete = 0
    adds: dict[pathlib.Path, list[Add]] = {}
    rebinds: dict[pathlib.Path, list[Rebind]] = {}
    declined: list[str] = []
    counts: collections.Counter[tuple[str, str]] = collections.Counter()

    for path in sorted(TESTS.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        resolver = Resolver(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            resolution = resolver.callee(node)
            if resolution is None:
                continue
            model = resolution[0]
            if not (isinstance(model, type) and issubclass(model, pydantic.BaseModel)):
                continue
            if any(isinstance(a, ast.Starred) for a in node.args):
                continue
            if any(keyword.arg is None for keyword in node.keywords):
                continue
            total += 1
            complete += 1 if satisfied(node, model) else 0

        found = gaps(path, tree, resolver)
        if not found:
            continue
        plans = rebind_for(path, tree, resolver, found)
        if plans:
            rebinds[path] = list(plans.values())
        for gap in found:
            if (id(gap.binding.node), gap.attribute) in plans:
                continue  # the binding moves; the call is already right
            for field in gap.missing:
                counts[(gap.model.__name__, field)] += 1
            add, notes = add_for(gap, tree, resolver)
            declined.extend(notes)
            if add is not None:
                adds.setdefault(path, []).append(add)

    print(f"{total} resolved keyword constructions; {complete} complete, {total - complete} not")
    if counts:
        print("\nranked missing (class, field), after the rebinds are taken out:")
        for (name, field), count in counts.most_common():
            print(f"    {count:4d}  {name}.{field}")

    if rebinds:
        sites = sum(plan.total for plans in rebinds.values() for plan in plans)
        print(f"\nREBIND -- {len(rebinds)} files name a class whose required set they do not")
        print(f"satisfy while a same-named class fits; {sites} call sites move, none edited:")
        for path, plans in sorted(rebinds.items()):
            for plan in plans:
                print(f"  {path.relative_to(ROOT)}  L{plan.binding.node.lineno} {plan.attribute}")
                print(f"      was {plan.was.__module__}.{plan.was.__qualname__}")
                print(f"      now {plan.now.__module__}.{plan.now.__qualname__}")
                print(f"      satisfies {plan.covered}/{plan.total} of this file's sites")
                for reference in plan.held:
                    print(f"      HELD {reference} -- asserts what the root surface binds")

    if declined:
        print("\nDECLINED -- the field is the test's subject at these sites, so supplying")
        print("it would erase what the test grades:")
        for note in declined:
            print(f"    {note}")

    if adds:
        sites = sum(len(found_adds) for found_adds in adds.values())
        print(f"\nADD -- {sites} constructions across {len(adds)} files really are missing")
        print("fields; each value below is read off the document, per field:")
        for path, found_adds in sorted(adds.items()):
            print(f"\n  {path.relative_to(ROOT)}")
            for add in sorted(found_adds):
                for field, value, rule in add.fields:
                    print(f"    L{add.line:<5} {add.callee:<30} {field}={value}")
                    print(f"             <- {rule}")

    if arguments.check:
        return 0

    touched: list[pathlib.Path] = []
    for path in sorted(set(adds) | set(rebinds)):
        lines = read_lines(path)
        for add in sorted(adds.get(path, []), reverse=True):
            lines = apply_add(lines, add)
        if path in rebinds:
            tree = ast.parse("\n".join(lines) + "\n")
            resolver = Resolver(tree)
            fresh = rebind_for(path, tree, resolver, gaps(path, tree, resolver))
            pending = [
                apply_rebind(lines, plan, tree, resolver)
                for plan in sorted(fresh.values(), key=lambda p: -p.binding.node.lineno)
            ]
            for module, name in pending:
                place_import(lines, ast.parse("\n".join(lines) + "\n"), module, name)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        touched.append(path)
    reformat(touched)
    print(f"\nrewrote {len(touched)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
