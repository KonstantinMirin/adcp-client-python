"""One schema node is one type, read off the EMITTED TREE by the five-part key.

``docs/plan/final-state.md`` reading 4: *"A type stated at more than one position is
written once and referenced, never restated"*, confirmed by *"a regression guard per
layer, keyed on that layer's own identity"* -- and the object layer's identity is what
this file spells.  Reading 6 states the counting rule the guard needs in one clause:
**"counting OBJECTS, not names"**.

**WHAT A DECLARATION IS, AND WHY THE PREDICATE IS THE WHOLE INSTRUMENT.**  A declaration
is a class whose ``__module__`` is the module it is read from -- an alias or a re-export
is not one.  ``__module__`` alone does not say that: an alias bound IN the declaring
module (``PreviewRenderHtmlDimensions = PreviewRenderUrlDimensions``) carries the
declaring module's name, because it carries the declaring class's.  A predicate that walks
``vars(module).values()`` and keeps everything whose ``__module__`` matches therefore
counts one class once per NAME bound to it, and reading 6's clause is the reason that is
wrong rather than conservative.

Measured on this tree: 2,370 such bindings over 2,352 class objects.  The 18-binding
difference was reported as *"17 types, 35 declarations, one schema node emitting several
classes"*; every one of the 17 groups is ONE class object under two or three names.
:func:`declarations_in` counts objects, :func:`bindings_in` counts names, and the first
test below is the equality that says where the 18 come from -- not as a literal, but as
the run's own record of its content dedup.

**THE FIVE-PART KEY, which is what makes this a guard on the object layer rather than on
a field set.**  A type is what it admits and what it does with what it admits, so two
declarations are one type when they agree on all five of: the pydantic JSON schema, the
``_adcp_rules`` tuple, ``_branch_models``, ``_BRANCH_DISCRIMINATOR``, and
``model_config``'s extra policy.  A key over FIELD NAMES is the instrument behind every
earlier figure on this epic (790, 718, 650, 547): the field set cannot see the branch
models, so 305 union roots sharing an inherited envelope's fields were counted as
duplicates of each other -- ``GetAccountFinancialsResponse`` and ``AcquireRightsResponse``
state the same 13 fields and dispatch to 2 and 4 different branches.  They are different
types.  Reading 4 says the same thing from the design side: *"A guard keyed on a name, an
export path or a constraint set cannot see a repeated object type."*

**AND PART 1 CARRIES THE CLASS'S OWN NAME UNLESS IT IS TAKEN OUT, which makes the same
sentence true of the key the five parts are usually spelled with.**  pydantic writes
``title`` into ``model_json_schema()`` from ``__name__`` for a model that states none of
its own, and :func:`test_the_schema_half_of_the_key_would_otherwise_carry_the_name` is the
equality that says it does so for every one of the tree's declarations.  A key holding
that title is a NAME key wearing a schema: it can never group two declarations of one type
under two names, which is most of what a per-position naming rule produces.  Measured over
this tree, the title costs the key 7 of its 15 groups and 20 of its 40 declarations.
:func:`schema_half` takes ``title`` out at every depth.

**``description`` STAYS IN, and that is the other half of the same boundary.**  A title is
the name WE minted; a description is what the DOCUMENT states, and reading 4 is explicit
that two positions stating the same shape are not automatically the same concept.  Taking
it out as well collapses 82 groups over 234 declarations, 28 of them inside one document --
``core/flight-item.json``'s ``origin`` and ``destination``, ``core/format.json``'s
``format_card`` and ``format_card_detailed``,
``media-buy/get-media-buy-delivery-request.json``'s ``keyword_targets`` and
``negative_keywords``.  Those are different subjects with one shape, and a key that joins
them reports a correct split as a duplicate -- which is the failure mode this file's
self-test exists to catch.

**AND THE KEY GRADES ITSELF, because a key that over-groups turns a correct split into a
reported duplicate.**  :func:`test_the_key_agrees_on_a_value_wherever_it_groups` offers
one derived payload set to every member of every group the key forms and requires the same
verdict from ``model_validate`` and from ``strict_validate`` -- the second being the half
the key does not carry, since it reads the member's own DOCUMENT.  A group whose members
disagree refutes the key and is a finding about the instrument.  Its red direction
constructs such a pair.

**WHAT THIS FILE ASSERTS AND WHAT IT ONLY REPORTS.**  Two declarations of ONE document
that are one type are this row: a document is one subject, its node is one node, and the
walk reaching it at several positions is settled by the compiler's content dedup with no
name to choose.  Two declarations in DIFFERENT documents that are one type are not: that
is one structure restated across documents, it needs a NAME, and naming it is the judgment
table's row.  So the assertion is per document and the cross-document groups are named in
the report rather than asserted over -- which is section 8's clause, "a check that
enumerates a subset reports on that subset only, and says so".

**AND ONE CROSS-DOCUMENT SHAPE IS ASSERTED AFTER ALL, because the BUNDLE decides it and
not a judgment.**  Reading 4's own test for which of the two a position is -- *"whether the
bundle REFERENCES one node from the others or RESTATES it is the question that tells our
defect from the schema's own duplication"* -- has an answer that needs no name where the
reference is written down: a node whose whole content is ``{"allOf": [{"$ref": X}]}`` IS
the bundle referencing X, so a class declared at it is a second declaration of X's type
and the collapse is licensed by the document rather than by the two classes sharing a field
set.  :func:`test_a_node_whose_whole_content_is_a_reference_declares_no_class_of_its_own`
is that, as an equality between a derivation over the BUNDLE and a derivation over the
TREE.  It is the one cross-document assertion here and it asserts nothing about a group:
the four groups the report names are decided by their DOCUMENTS and three of them disagree,
which is :func:`test_the_key_agrees_on_a_value_wherever_it_groups`'s blind spot and not
this file's gate.

**THE TREE IS THE EMITTED ONE.**  ``tests/fresh.py`` binds the generated half of
``adcp.types`` to a fresh run's output before collection, so importing
``adcp.types._schemas`` here reads the tree this run wrote and never ``src/``.
"""

from __future__ import annotations

import collections
import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

import pytest
from compiled import compiled
from nodeset import claimed, partitions
from pydantic import BaseModel, ValidationError, field_validator

from adcp.types._base import AdCPBaseModel, SchemaRef
from codegen import bundle, keywords

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"


# --------------------------------------------------------------------------- #
# What a declaration is, in two predicates that differ on exactly one thing
# --------------------------------------------------------------------------- #
def bindings_in(module: Any) -> list[tuple[str, type[BaseModel]]]:
    """Every NAME in ``module`` bound to a class whose ``__module__`` is ``module``.

    **Kept because it is the red direction's instrument and not because anything grades
    it.**  This is the predicate that read 2,370 declarations where the tree declares
    2,352, and :func:`test_a_declaration_is_a_class_object_and_never_a_name` is what says
    so by construction.  A reader reaching for a declaration set wants
    :func:`declarations_in`.
    """
    return [
        (name, value)
        for name, value in vars(module).items()
        if isinstance(value, type) and issubclass(value, BaseModel) and value.__module__ == module.__name__
    ]


def declarations_in(module: Any) -> list[type[BaseModel]]:
    """Every class ``module`` DECLARES, counted once per class OBJECT.

    Reading 6's clause, applied: *"counting OBJECTS, not names"*.  ``dict`` on ``id``
    rather than a ``set`` of classes, because a pydantic model's ``__hash__`` is not
    identity-keyed for every shape the tree emits and the order a module declares in is
    the order a failure should be reported in.
    """
    taken: dict[int, type[BaseModel]] = {}
    for _, value in bindings_in(module):
        taken.setdefault(id(value), value)
    return list(taken.values())


def modules_of(package: Any) -> list[str]:
    """Every module of ``package``, package roots INCLUDED.

    ``ispkg`` is not a screen: ``emit.write``'s layout rule puts a document whose own path
    is also a directory of the bundle at ``<path>/__init__.py``, so ``brand.json``'s module
    is ``adcp.types._schemas.brand`` and ``pkgutil`` reports it as a package.  31 of the
    tree's 1,088 modules are package roots and 68 declarations live in their own bodies --
    ``brand/__init__.py`` holds all 68.  ``tests/_imports_a_tree.py`` carries the same
    reading from the import side: screening them out is how one gate came to range over
    1,057 modules of 1,088 with the rest discharged by nothing.
    """
    return sorted(i.name for i in pkgutil.walk_packages(package.__path__, package.__name__ + "."))


def the_tree() -> dict[str, list[type[BaseModel]]]:
    """Module name -> the declarations it holds, over the tree this run emitted."""
    import adcp.types._schemas as pkg

    return {name: declarations_in(importlib.import_module(name)) for name in modules_of(pkg)}


# --------------------------------------------------------------------------- #
# The five-part key
# --------------------------------------------------------------------------- #
def schema_half(cls: type[BaseModel]) -> Any:
    """Part 1 of the key: the pydantic JSON schema with every ``title`` taken out.

    A ``title`` admits nothing.  pydantic derives the top-level one from ``__name__`` and
    the per-field ones from the field names, which the ``properties`` keys already carry,
    so removing them loses no fact about what the class accepts and removes the one thing
    in part 1 that is a NAME.  Recursive, because a nested ``$defs`` entry carries its
    own.
    """

    def without(node: Any) -> Any:
        if isinstance(node, dict):
            return {word: without(sub) for word, sub in node.items() if word != "title"}
        if isinstance(node, list):
            return [without(sub) for sub in node]
        return node

    return without(cls.model_json_schema(mode="validation"))


def key_of(cls: type[BaseModel]) -> tuple[Any, ...]:
    """A type is what it ADMITS and what it DOES with what it admits.

    1. the pydantic JSON schema -- fields, annotations, requiredness, defaults, nesting;
    2. ``_adcp_rules`` -- the runtime rules the JSON schema does not carry;
    3. ``_branch_models`` -- what it dispatches TO;
    4. ``_BRANCH_DISCRIMINATOR`` -- what it dispatches ON;
    5. ``model_config``'s extra policy -- what it admits that it does not declare.

    The branch models are spelled by ``__module__`` and ``__qualname__`` and not by
    identity, so two roots dispatching to two equal-but-distinct branch sets are one type
    only if those branches are themselves the same declarations.
    """
    return (
        json.dumps(schema_half(cls), sort_keys=True),
        repr(getattr(cls, "_adcp_rules", ())),
        tuple(f"{b.__module__}.{b.__qualname__}" for b in getattr(cls, "_branch_models", ())),
        getattr(cls, "_BRANCH_DISCRIMINATOR", None),
        str(cls.model_config.get("extra")),
    )


def ref_of(cls: type[BaseModel]) -> tuple[str, str] | None:
    """The ``(document, pointer)`` the class names, read off ``__adcp_schema__``.

    **Never by name and never by ``__all__[0]``**: ``__all__`` is sorted, so index 0 is
    the document's root for 1,023 of the tree's 1,054 modules and something else for 31.
    """
    ref = getattr(cls, "__adcp_schema__", None)
    return (ref.document, ref.pointer) if isinstance(ref, SchemaRef) else None


def grouped(declarations: list[type[BaseModel]]) -> dict[tuple[Any, ...], list[type[BaseModel]]]:
    """The declarations handed in, grouped by the five-part key."""
    out: dict[tuple[Any, ...], list[type[BaseModel]]] = collections.defaultdict(list)
    for cls in declarations:
        out[key_of(cls)].append(cls)
    return dict(out)


def document_of(cls: type[BaseModel]) -> str | None:
    ref = ref_of(cls)
    return ref[0] if ref is not None else None


def restated_within_one_document(
    declarations: list[type[BaseModel]],
) -> dict[tuple[str | None, tuple[Any, ...]], list[type[BaseModel]]]:
    """Groups of two or more declarations of ONE document that are one type.

    This row's defect, in the form a reader can act on: the document, the key, and every
    pointer that declared a class for it.  Empty is the invariant.
    """
    out: dict[tuple[str | None, tuple[Any, ...]], list[type[BaseModel]]] = collections.defaultdict(list)
    for cls in declarations:
        out[(document_of(cls), key_of(cls))].append(cls)
    return {where: members for where, members in out.items() if len(members) > 1}


# --------------------------------------------------------------------------- #
# A payload set derived from a group's own schema, for the key's self-test
# --------------------------------------------------------------------------- #
#: A value of each JSON type, for a payload derived from a declared field's type.  Not a
#: fixture: nothing here is a fact about a document, it is one inhabitant per type word so
#: that a derived payload can carry a value at all.
_OF_TYPE: dict[str, Any] = {
    "string": "x",
    "integer": 1,
    "number": 1.5,
    "boolean": True,
    "array": [],
    "object": {},
    "null": None,
}


def _a_value(schema: Any, defs: dict[str, Any], depth: int = 0) -> Any:
    """One value the field's declared type admits the shape of, derived from the schema."""
    if not isinstance(schema, dict) or depth > 4:
        return "x"
    if "const" in schema:
        return schema["const"]
    if isinstance(schema.get("enum"), list) and schema["enum"]:
        return schema["enum"][0]
    if isinstance(schema.get("$ref"), str):
        name = schema["$ref"].rsplit("/", 1)[-1]
        return _a_value(defs.get(name, {}), defs, depth + 1)
    for word in ("anyOf", "oneOf", "allOf"):
        if isinstance(schema.get(word), list) and schema[word]:
            return _a_value(schema[word][0], defs, depth + 1)
    kind = schema.get("type")
    if isinstance(kind, list):
        kind = kind[0] if kind else None
    if kind == "object":
        props = schema.get("properties") or {}
        return {
            name: _a_value(props[name], defs, depth + 1) for name in (schema.get("required") or []) if name in props
        }
    if isinstance(kind, str) and kind in _OF_TYPE:
        return _OF_TYPE[kind]
    return "x"


def payloads_for(schema: dict[str, Any]) -> list[Any]:
    """Payloads derived from a group's own pydantic schema, one per way it can be probed.

    **Derived and never written down** (section 8's fixture rule): every member of a group
    shares part 1 of the key, so the schema these come from is the group's own and the set
    is the same for every member of it -- which is what makes a disagreement between two
    members a fact about the members.

    The set probes the halves the key does NOT carry: a validator attached to a field, a
    rule evaluated after construction, and the DOCUMENT ``strict_validate`` reads.  So it
    holds the empty object, the required-only object, the all-properties object, each
    property alone, each property at the wrong type, and the all-properties object with an
    undeclared key -- plus the three scalars a root model may be offered.
    """
    defs = schema.get("$defs") or {}
    props = schema.get("properties") or {}
    required = [name for name in (schema.get("required") or []) if name in props]
    full = {name: _a_value(sub, defs) for name, sub in props.items()}
    out: list[Any] = [{}, dict(full), {name: full[name] for name in required}]
    for name in sorted(props):
        out.append({name: full[name]})
        out.append({**full, name: "a value of the wrong type" if full[name] != "x" else 0})
    out.append({**full, "a key no document declares": 1})
    out.extend(["x", 0, None, []])
    return out


def _verdict(cls: type[BaseModel], payload: Any, *, strict: bool) -> Any:
    """What ``cls`` DOES with ``payload``: the value it builds, or why it refused."""
    try:
        built = cls.strict_validate(payload) if strict else cls.model_validate(payload)
    except ValidationError as why:
        return ("refused", sorted({(e["type"], e["loc"]) for e in why.errors()}))
    except Exception as why:  # noqa: BLE001 -- the reason is the verdict
        return ("raised", type(why).__name__)
    try:
        return ("admitted", json.dumps(built.model_dump(mode="json"), sort_keys=True, default=repr))
    except Exception as why:  # noqa: BLE001 -- the reason is the verdict
        return ("admitted, undumpable", type(why).__name__)


def disagreements(members: list[type[BaseModel]], *, strict: bool) -> list[Any]:
    """Every payload on which the members of one group do not agree on a value.

    ``strict`` picks which entry point is asked, and the two are kept apart because they
    answer different questions about the key.  ``model_validate`` is what the CLASS does,
    which is what the five parts describe; ``strict_validate`` validates against the
    member's own DOCUMENT first, which no part of the key carries.
    """
    found: list[Any] = []
    for payload in payloads_for(schema_half(members[0])):
        verdicts = {f"{c.__module__}.{c.__name__}": _verdict(c, payload, strict=strict) for c in members}
        if len(set(map(repr, verdicts.values()))) > 1:
            found.append({"payload": payload, "verdicts": verdicts})
    return found


# --------------------------------------------------------------------------- #
# The red directions, each a tree built on purpose
# --------------------------------------------------------------------------- #
def _a_module(name: str, **bound: Any) -> Any:
    """A module object holding exactly what it is handed, for the predicates to read.

    A real module and not a stub: :func:`bindings_in` and :func:`declarations_in` read
    ``vars(module)`` and ``module.__name__`` and nothing else, so what they are proved
    against here is what they do to the tree.
    """
    import types

    module = types.ModuleType(name)
    for attribute, value in bound.items():
        setattr(module, attribute, value)
    return module


def _refuses_every_size(_cls: Any, _value: Any) -> Any:
    """A field validator the schema does not state, for the key's red direction."""
    raise ValueError("no size is admitted")


def _a_class(name: str, module: str, ref: SchemaRef, **namespace: Any) -> type[AdCPBaseModel]:
    """One emitted-shaped class: an ``AdCPBaseModel`` carrying its own ``__adcp_schema__``."""
    return type(
        name,
        (AdCPBaseModel,),
        {
            "__module__": module,
            "__annotations__": {"size": int},
            "__adcp_schema__": ref,
            "size": 1,
            **namespace,
        },
    )


# --------------------------------------------------------------------------- #
# 1. The predicate, proved in both directions, and the 18 accounted for
# --------------------------------------------------------------------------- #
def test_a_declaration_is_a_class_object_and_never_a_name() -> None:
    """One class under two names is ONE declaration; two classes are two.

    **Proved by construction and not by argument**, which is the only thing that tells a
    corrected predicate from a narrowed one.  :func:`bindings_in` is kept beside
    :func:`declarations_in` so the two readings of the same module are compared here: the
    first counts names and the second counts objects, and the module they are given holds
    one class under two names and one other class.

    Then the SAME difference, over the tree, as an equality between two derivations rather
    than as a literal: the names a module binds beyond the classes it declares are exactly
    the adoptions the run RECORDED for that document under a name of their own.
    ``Emitted.adopted`` is the walk's record of section 4's content dedup -- pointer -> the
    symbol the node at it adopted because an earlier node of identical content declared it
    -- and ``Emitted.declared`` holds the name the adopting position derived for itself.
    Where the two differ the renderer writes ``X = TheClass``, which is one class and a
    second name.

    **That equality is this row's cause, stated where it can go red.**  The first
    hypothesis -- that a node is lowered once per enclosing PATH, minting a class each time
    -- is refuted by it: a node reached twice is lowered once, and what is minted per
    position is the NAME (``codegen.lower.names.adopt``: "one class, as many names as the
    node has positions").  If a later row makes the walk mint a second CLASS at an adopting
    position, the tree's binding count rises while the run's adoption record does not, and
    this is the equality that breaks.
    """
    first = _a_class("First", "a.module", SchemaRef(document="a.json", pointer="#"))
    second = _a_class("Second", "a.module", SchemaRef(document="a.json", pointer="#/x"))
    built = _a_module("a.module", First=first, Aliased=first, Second=second, Elsewhere=BaseModel)

    assert [name for name, _ in bindings_in(built)] == ["First", "Aliased", "Second"]
    assert declarations_in(built) == [first, second]

    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    import adcp.types._schemas as pkg

    #: module -> the document it was written for, which is the run's own record inverted.
    document_at = {written: document for document, written in out.emitted.items()}
    named_twice: set[tuple[str, str]] = set()
    renamed_adoptions: set[tuple[str, str]] = set()
    for name in modules_of(pkg):
        imported = importlib.import_module(name)
        objects = {id(cls) for cls in declarations_in(imported)}
        seen: set[int] = set()
        for binding, cls in bindings_in(imported):
            if id(cls) in seen or binding != cls.__name__:
                named_twice.add((name, binding))
            seen.add(id(cls))
        document = document_at.get(name)
        if document is None:
            continue
        for pointer, adopted in out.adopted[document].items():
            derived = out.declared[document][pointer]
            if derived == adopted:
                continue  # ``assign`` dropped a degenerate ``X = X``; no second name
            bound = getattr(imported, derived, None)
            if isinstance(bound, type) and id(bound) in objects:
                renamed_adoptions.add((name, derived))

    claimed("names bound beyond the class they name", named_twice)
    assert named_twice == renamed_adoptions, {
        "a second name with no adoption behind it": sorted(named_twice - renamed_adoptions),
        "an adoption whose second name the tree does not carry": sorted(renamed_adoptions - named_twice),
    }


def test_the_schema_half_of_the_key_would_otherwise_carry_the_name() -> None:
    """``model_json_schema()``'s ``title`` IS the class's name, for every declaration.

    Stated as an equality between two derivations -- the titles the tree's schemas carry
    against the names its declarations have -- because the reason ``title`` is out of the
    key is this fact and not a preference.  If pydantic ever stopped echoing ``__name__``
    there, or if a row started writing a document's own ``title`` onto a class, this is
    where that shows up, and the key would then be taking out something a document states.

    And the consequence, so the exclusion is not free either: the key WITH the title forms
    strictly fewer groups than the key without it.  A guard spelled on the first key is
    blind in exactly that difference.
    """
    declarations = [cls for members in the_tree().values() for cls in members]
    claimed("declarations whose schema carries a title", declarations)
    titles = {f"{cls.__module__}.{cls.__name__}": cls.model_json_schema()["title"] for cls in declarations}
    assert titles == {f"{cls.__module__}.{cls.__name__}": cls.__name__ for cls in declarations}, {
        name: title for name, title in titles.items() if title != name.rsplit(".", 1)[-1]
    }

    with_the_name = collections.Counter(
        (json.dumps(cls.model_json_schema(mode="validation"), sort_keys=True), *key_of(cls)[1:]) for cls in declarations
    )
    without_it = collections.Counter(key_of(cls) for cls in declarations)
    blind_to = sum(count for count in with_the_name.values() if count > 1)
    sees = sum(count for count in without_it.values() if count > 1)
    assert sees > blind_to, (sees, blind_to)


# --------------------------------------------------------------------------- #
# 2. The gate
# --------------------------------------------------------------------------- #
def test_no_two_declarations_of_one_document_are_one_type() -> None:
    """One document's node is one node, so it is one type and gets one class.

    The declarations of the tree this run emitted, grouped by the five-part key WITHIN a
    document.  A group of two is the defect: one subject, two classes, and no name to
    choose between them -- the walk reached one node by more than one path and lowered it
    twice.

    **The cross-document groups are reported and not asserted over**, and that is section
    8's clause rather than an exemption: two documents RESTATING one structure is a
    different row with a different repair, because the type needs a NAME and nothing in
    one document decides it.  The partition below is what makes the split total -- every
    group the key forms is in exactly one part -- so a group cannot fall out of both.
    """
    tree = the_tree()
    declarations = [cls for members in tree.values() for cls in members]
    claimed("declarations of the emitted tree", declarations)
    assert all(ref_of(cls) is not None for cls in declarations), [
        f"{cls.__module__}.{cls.__name__}" for cls in declarations if ref_of(cls) is None
    ]

    repeated = {key: members for key, members in grouped(declarations).items() if len(members) > 1}
    claimed("keys the tree declares more than once", repeated)
    partitions(
        repeated,
        **{
            "one document, several positions": [
                key for key, members in repeated.items() if len({document_of(c) for c in members}) == 1
            ],
            "several documents, needs a name": [
                key for key, members in repeated.items() if len({document_of(c) for c in members}) > 1
            ],
        },
    )

    restated = restated_within_one_document(declarations)
    assert restated == {}, {
        document: [{"class": f"{cls.__module__}.{cls.__name__}", "names": ref_of(cls)} for cls in members]
        for (document, _), members in restated.items()
    }


def test_one_document_declaring_two_classes_for_one_type_reddens_the_gate() -> None:
    """The gate's own reading, over a module built to hold the defect.

    ``test_no_two_declarations_of_one_document_are_one_type`` is the green direction and
    proves nothing by itself -- ``assert {} == {}`` passes it.  This is the red one, and it
    calls the SAME function rather than restating the predicate: a restated predicate
    proves that a copy of the gate reddens, which is not the claim.

    Two classes, one document, equal content at two pointers -- which is what a walk that
    lowers a node once per enclosing path produces.  And the second direction beside it:
    the same two classes made to state DIFFERENT content are two types, so the gate does
    not report a correct split.
    """
    document = "one/document.json"
    twice = [
        _a_class("AtZero", "one.module", SchemaRef(document=document, pointer="#/oneOf/0/properties/d")),
        _a_class("AtOne", "one.module", SchemaRef(document=document, pointer="#/oneOf/1/properties/d")),
    ]
    assert len(restated_within_one_document(twice)) == 1, restated_within_one_document(twice)

    split = [
        twice[0],
        _a_class(
            "AtOne",
            "one.module",
            SchemaRef(document=document, pointer="#/oneOf/1/properties/d"),
            __annotations__={"size": str},
            size="x",
        ),
    ]
    assert restated_within_one_document(split) == {}, restated_within_one_document(split)


# --------------------------------------------------------------------------- #
# 2a. A position whose whole content is a reference, read off the BUNDLE
# --------------------------------------------------------------------------- #
def asserts_nothing_anywhere() -> frozenset[str]:
    """Every keyword the TABLE answers ``NOTHING`` for at every position it has a cell at.

    **DERIVED from ``codegen/keywords.py`` and not listed**, which is ``codegen/catalogue``'s
    ``_carried`` for the same reason §9 gives: *"a keyword handled in code but named in none
    of §5, §6 or §7 is an invented rule"*, and a list beside the table is how the two come
    to disagree -- it would have said ``default`` is an annotation while the table says its
    cell is FIELD at PROP.

    Narrower than that function on purpose: ``_carried`` admits ANNOTATION too, because an
    annotation does not change what a node ADMITS, and the question here is not what a node
    admits but whether it STATES anything of its own.  §6's description-authority rule makes
    a ``description`` a statement this document makes at this pointer, which a type that IS
    another document's class cannot carry -- so ``description`` is out and
    ``x-adcp-schema-uri``, whose every cell is NOTHING, is in.
    """
    return frozenset(
        word
        for word, row in keywords.TABLE.items()
        if all(cell.effect is keywords.Effect.NOTHING for cell in (row.default, *row.at.values()))
    )


def whole_content_is_a_reference(document: str) -> set[str]:
    """The non-root pointers of ``document`` whose whole content is one ``$ref``.

    Read off the document as the bundle ships it and never off the record: §3's record
    INLINES every cross-document reference, so a reading over it cannot tell a position
    that references from one that restates -- which is the distinction reading 4 turns on.

    A ROOT is excluded, and that is ``lower.references._root``'s decision rather than a
    caution: D5 fixes a root's symbol, so a document whose root is a bare reference must
    declare a class of its own -- *"binding this module's symbol to another module's class
    would be a second way to reach one class, against §1"* -- and the answer there is a
    subclass.  A non-root position declares no symbol, so there is nothing for a second
    reach to be.
    """
    inert = asserts_nothing_anywhere()
    found: set[str] = set()

    def walk(node: Any, pointer: str) -> None:
        if isinstance(node, dict):
            conjuncts = node.get("allOf")
            if (
                pointer != "#"
                and isinstance(conjuncts, list)
                and len(conjuncts) == 1
                and isinstance(conjuncts[0], dict)
                and set(conjuncts[0]) == {"$ref"}
                and set(node) - {"allOf"} <= inert
            ):
                found.add(pointer)
            for word, sub in node.items():
                walk(sub, f"{pointer}/{word}")
        elif isinstance(node, list):
            for index, sub in enumerate(node):
                walk(sub, f"{pointer}/{index}")

    walk(bundle.read(BUNDLE, document), "#")
    return found


def test_a_node_whose_whole_content_is_a_reference_declares_no_class_of_its_own() -> None:
    """Reading 4 at the one position where the BUNDLE answers it: write once, reference.

    *"A type stated at more than one position is written once and referenced, never
    restated"*, and reading 4's own clause for deciding which this is -- *"whether the
    bundle REFERENCES one node from the others or RESTATES it is the question that tells our
    defect from the schema's own duplication"*.  A node stating ``{"allOf": [{"$ref": X}]}``
    and nothing that asserts anything is the bundle REFERENCING, so the type is X's, X's
    module declares it, and a class here would be a second declaration of it under a second
    name -- which is ours and needs no title, because the bundle has already named the type
    in X's own document.

    **AN EQUALITY BETWEEN TWO DERIVATIONS and not a count**: the positions the BUNDLE states
    that way, against the subset of them the TREE declares no class at.  Both sides move
    with the inputs -- the first with the bundle, the second with the compiler -- so there is
    no figure here to re-point when either moves, and the failure names the pointers rather
    than a difference of two totals.

    Its RED direction is the tree that was committed before this landed: three
    ``push_notification_config`` properties in ``media-buy/decline-proposals-request.json``,
    ``refine-proposals-request.json`` and ``request-proposals-request.json``, each an
    ``allOf`` of one ``$ref`` to ``core/push-notification-config.json`` plus an
    ``x-adcp-schema-uri``, and each declaring an empty subclass of that document's class.
    The same four declarations are what
    ``test_the_key_agrees_on_a_value_wherever_it_groups`` reported as one group of four with
    no disagreement on any payload -- a group's members agreeing is the five-part key's
    hypothesis, and the document stating the reference is the verdict.

    **The four remaining ``context`` positions are in the claimed set and were never
    classes**: ``core/context.json``'s root is not a class, so §5's ``$ref`` row at CONJ
    already answered them with the target's own symbol.  They are in the set this check
    ranges over, which is what makes the equality a statement about every position the
    bundle states this way rather than about the three that moved.
    """
    positions = claimed(
        "positions whose whole content is a reference",
        {
            (document, pointer)
            for document in bundle.portable(BUNDLE)
            for pointer in whole_content_is_a_reference(document)
        },
    )
    declared = {ref_of(cls) for members in the_tree().values() for cls in members}
    assert positions - declared == positions, {
        "the bundle references here and the tree declares a class anyway": sorted(
            positions & declared
        )
    }


# --------------------------------------------------------------------------- #
# 3. The key, graded by the thing it is a key over
# --------------------------------------------------------------------------- #
def test_the_key_agrees_on_a_value_wherever_it_groups() -> None:
    """Every group the key forms agrees on a value through the class, and the one place it
    does not agree is the DOCUMENT -- which is a fact about the key, stated where it can
    go red.

    **This is the direction four earlier figures on this epic did not have.**  A key that
    over-groups turns a correct split into a reported duplicate, and a field-set key did
    exactly that: 305 union roots sharing an inherited envelope's fields were counted as
    duplicates of each other.  So every group the five-part key forms is offered one
    payload set derived from the group's own schema and required to return the same verdict
    on every member.

    **Two entry points, and the split between them is the result.**  Through
    ``model_validate`` -- what the CLASS does, which is what the five parts describe --
    every group agrees, so the key is sound over the thing it is a key over.  Through
    ``strict_validate`` five of them do not, because that entry point validates against
    the member's own DOCUMENT and no part of the key carries one: ``NotificationConfig``
    and ``account/sync-accounts-request.json``'s ``NotificationConfigsItem`` build the same
    object from the same payload and their two documents disagree about ``format`` and
    ``minItems``.

    So the assertion is the BOUNDARY rather than silence on either side: a disagreement is
    reached through ``strict_validate`` only, and only in a group whose members name
    different documents.  Both halves can go red and each names a different defect.  A
    disagreement through ``model_validate`` says the key misses something the class itself
    does, which would refute it outright; a disagreement inside ONE document says it
    misses something a document does, which would refute the gate below, since that gate
    reads a same-document group as a duplicate.

    ``title`` is the worked case of why this direction is required: with it in part 1 the
    key formed 8 groups, every one of which agrees, and the 7 it could not see include
    three of the five that disagree.  A key graded only where it already agrees grades
    nothing.
    """
    declarations = [cls for members in the_tree().values() for cls in members]
    repeated = {key: members for key, members in grouped(declarations).items() if len(members) > 1}
    claimed("groups the key forms, which it is graded over", repeated)

    refuted: dict[tuple[Any, ...], list[Any]] = {}
    for key, members in repeated.items():
        claimed(
            f"payloads offered to {members[0].__name__}",
            map(json.dumps, payloads_for(schema_half(members[0]))),
        )
        through_the_class = disagreements(members, strict=False)
        assert through_the_class == [], {
            "the key grouped these and the CLASS disagrees, which refutes it": [
                f"{c.__module__}.{c.__name__}" for c in members
            ],
            "on": through_the_class[:3],
        }
        through_the_document = disagreements(members, strict=True)
        if through_the_document:
            refuted[key] = through_the_document
            assert len({document_of(c) for c in members}) > 1, {
                "one document, and the key's members still disagree": [
                    f"{c.__module__}.{c.__name__} {ref_of(c)}" for c in members
                ],
                "on": through_the_document[:3],
            }

    claimed("groups the DOCUMENT refutes, which is the key's one blind spot", refuted)


def test_two_classes_the_key_groups_that_disagree_on_a_value_refute_it() -> None:
    """The self-test's red direction, built rather than argued.

    Two classes the five-part key cannot tell apart -- same JSON schema, same rule tuple,
    same branches, same discriminator, same extra policy -- one of which carries a field
    validator the schema does not state.  The key says one type; a value says two, and
    :func:`disagreements` is what reports it.  Without this direction the self-test above
    is satisfied by a payload set that probes nothing.
    """
    ref = SchemaRef(document="one/document.json", pointer="#")
    plain = _a_class("Plain", "one.module", ref)
    fussy = _a_class(
        "Fussy",
        "one.module",
        ref,
        refuse=field_validator("size")(classmethod(_refuses_every_size)),
    )
    assert key_of(plain) == key_of(fussy)
    found = disagreements([plain, fussy], strict=False)
    assert found, "the payload set probes nothing a validator can refuse"


if __name__ == "__main__":  # pragma: no cover -- the report, for a reader
    raise SystemExit(pytest.main([__file__, "-q"]))
