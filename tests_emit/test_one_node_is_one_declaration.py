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

Measured on this tree: 2,358 such bindings over 2,340 class objects.  The 18-binding
difference was reported as *"17 types, 35 declarations, one schema node emitting several
classes"*; every one of the 17 groups is ONE class object under two or three names.
:func:`declarations_in` counts objects, :func:`bindings_in` counts names, and the first
test below is the equality that says where the 18 come from -- not as a literal, but as
the run's own record of its content dedup.

**AND THE SAME 18 WERE RE-REPORTED AS A DEFECT, which is why the counting rule is now a
GATE and not only a predicate** (``adcp-client-python-qpzf``, reading 4 at the object
layer).  The second report walked ``__adcp_schema__`` instead of the module bindings and
found *"17 ``(document, pointer)`` pairs carrying MORE THAN ONE class, involving 35
classes"* -- six ``oneOf`` branches of ``adagents.json``'s authorized-agent item plus
``tags/additionalProperties``, and ten others.  It is the same 17 nodes and the same 35
NAMES, and ``nodes with more than one CLASS OBJECT`` is **0** at every one of them: the
pair at ``#/oneOf/1/properties/tags/additionalProperties`` is ``SignalTagsValue =
TagsValue``, one object read through two names, which is ``lower/names.adopt``'s own
clause -- *"one class, as many names as the node has positions"* -- working.  A measurement
that cannot tell an alias from a declaration says nothing about reading 4 either way, and
the answer to that is a clause stated where it can go red:
:func:`test_one_schema_node_is_declared_by_at_most_one_class` ranges over the nodes, counts
OBJECTS, and is handed the 35-name population beside the 2,340-object one so that the
alias-blindness is asserted and not argued.

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

**AND ONE CLAUSE THAT IS NOT ABOUT GROUPS AT ALL, because the five-part key cannot state
it.**  Both populations below are groups the KEY forms, so both are silent wherever the key
SEPARATES two declarations -- and two classes at ONE schema node differing in part 1 are
separated by it.  ``test_one_document_declaring_two_classes_for_one_type_reddens_the_gate``
writes that out already: its ``split`` pair sits at one pointer, states different content,
and ``restated_within_one_document`` returns ``{}`` for it, correctly, because they are not
one TYPE.  They are still two classes at one NODE, which no row of ``tests/duplicates.py``
and no group of this file can see.  :func:`two_classes_at_one_node` is keyed on the node and
on nothing else, and it is the clause reading 4 states literally: a node is one node, so it
gets one class.

**WHAT THIS FILE ASSERTS, IN TWO POPULATIONS THAT PARTITION THE GROUPS.**  Two declarations
of ONE document that are one type are the first: a document is one subject, its node is one
node, and the walk reaching it at several positions is settled by the compiler's content
dedup with no name to choose, so the assertion is that there are none.  Two declarations in
DIFFERENT documents that are one type are the second: that is one structure restated across
documents, it needs a NAME or a reading, and the decision is one per group.

**THE SECOND POPULATION WAS REPORTED AND NOTHING ASSERTED OVER IT, AND THAT IS WHAT
``tests/duplicates.py`` ENDS.**  A decision recorded in a bead comment is a judgment the
build does not apply, and the architecture's clause for that is not softer for a decision
than for a patch: "AN OVERRIDE THE BUILD DOES NOT APPLY IS A LIE, AND THE GATE IS ON THE
ARTIFACT."  So every cross-document group the EMITTED tree forms is answered by exactly one
row of that table -- a group with no row is RED because nobody decided it, and a row whose
group is gone is RED because the row is to be DELETED.  The table's size is the debt figure
and both directions of the equality are what keep it one.

**THE TREE IS THE EMITTED ONE.**  ``tests/fresh.py`` binds the generated half of
``adcp.types`` to a fresh run's output before collection, so importing
``adcp.types._schemas`` here reads the tree this run wrote and never ``src/``.
"""

from __future__ import annotations

import collections
import dataclasses
import importlib
import json
import pkgutil
from pathlib import Path
from typing import Any

import duplicates
import pytest
from compiled import compiled
from judgment import name_at as judgment_name_at
from nodeset import claimed, partitions, ratchet
from pydantic import BaseModel, ValidationError, field_validator

from adcp.types._base import AdCPBaseModel, SchemaRef, schema_at
from codegen import bundle, catalogue, emit, keywords, patch

REPO = Path(__file__).resolve().parents[1]
#: **The bundle a RUN reads**: the published one with the build's patch sets applied
#: (:func:`codegen.patch.for_build`), which is ``./check``'s own derivation and
#: ``tests/fresh.py``'s.  The tree this file grades is emitted from THAT bundle, so reading
#: the published one here would group the tree's declarations against a document set five
#: documents short of the one they were compiled from -- and every title the override table
#: supplies would be invisible to the one check that is about titles.
BUNDLE = patch.for_build(REPO / "schemas" / "cache" / "3.2")


# --------------------------------------------------------------------------- #
# What a declaration is, in two predicates that differ on exactly one thing
# --------------------------------------------------------------------------- #
def bindings_in(module: Any) -> list[tuple[str, type[BaseModel]]]:
    """Every NAME in ``module`` bound to a class whose ``__module__`` is ``module``.

    **Kept because it is the red direction's instrument and not because anything grades
    it.**  This is the predicate that read 2,358 declarations where the tree declares
    2,340, and :func:`test_a_declaration_is_a_class_object_and_never_a_name` is what says
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


def two_classes_at_one_node(
    declarations: list[type[BaseModel]],
) -> dict[tuple[str, str], list[type[BaseModel]]]:
    """``(document, pointer)`` -> the two or more CLASS OBJECTS that name it.

    Keyed on the schema NODE and on nothing else -- not on the five-part key, not on a
    name, not on a module -- which is what makes it the one reading of reading 4 that holds
    where the key separates the pair.  ``{}`` is the invariant.

    **COUNTING OBJECTS, and the ``id`` dict is the whole of why this is a gate rather than
    the figure that was mistaken for one.**  ``adcp-client-python-qpzf`` read 35 classes at
    17 nodes off ``__adcp_schema__`` and every pair is one object under two names: an alias
    is a Python assignment, so ``SignalTagsValue.__adcp_schema__`` IS ``TagsValue``'s and a
    reader keying on the pair counts the class once per name bound to it.  Reading 6's
    clause -- *"counting OBJECTS, not names"* -- is therefore load-bearing HERE and not only
    in :func:`declarations_in`, because this function is the one a reader will hand a
    binding list to.  Handed :func:`bindings_in`'s 2,358 names it must still answer ``{}``,
    and :func:`test_one_schema_node_is_declared_by_at_most_one_class` hands it exactly that.

    A declaration with no ``__adcp_schema__`` is not at a node and is not in the population:
    ``lower/envelope.py``'s synthesised base carries no reference on purpose and
    ``ir.ClassDecl``'s own docstring says what that means -- *"a class with no reference is
    not in the pairing at all"*.
    """
    out: dict[tuple[str, str], dict[int, type[BaseModel]]] = collections.defaultdict(dict)
    for cls in declarations:
        if (at := ref_of(cls)) is not None:
            out[at][id(cls)] = cls
    return {at: list(members.values()) for at, members in out.items() if len(members) > 1}


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


def disagreements(
    members: list[type[BaseModel]], *, strict: bool, over: list[Any] | None = None
) -> list[Any]:
    """Every payload on which the members of one group do not agree on a value.

    ``strict`` picks which entry point is asked, and the two are kept apart because they
    answer different questions about the key.  ``model_validate`` is what the CLASS does,
    which is what the five parts describe; ``strict_validate`` validates against the
    member's own DOCUMENT first, which no part of the key carries.

    ``over`` is the payload set, and it defaults to the one derived from the group's own
    SHARED schema -- which is the right set for grading the KEY, because every member
    shares part 1 of it.  :func:`from_each_own_node` is the other set and is the right one
    for grading a DECISION: a group's shared schema is what the classes agree on, so a
    payload derived from it cannot probe the thing the classes differ in, and measured on
    ``adcp-client-python-6h1`` the shared set found 0 of the discriminating payloads the
    per-member set found.
    """
    found: list[Any] = []
    for payload in payloads_for(schema_half(members[0])) if over is None else over:
        verdicts = {f"{c.__module__}.{c.__name__}": _verdict(c, payload, strict=strict) for c in members}
        if len(set(map(repr, verdicts.values()))) > 1:
            found.append({"payload": payload, "verdicts": verdicts})
    return found


def applied_at(cls: type[BaseModel]) -> Any:
    """The node the member's own DOCUMENT applies at the member's pointer.

    Through ``adcp.types._base.schema_at`` and with the member's own ``__module__``, which
    is "A READER DERIVES ITS KEY FROM THE ACCESSOR THE GRADE READS THROUGH" applied here:
    the record stores each distinct subtree once and references it at every occurrence, so
    a reader that walked the stored text would key on a form the grade never sees.
    """
    ref = getattr(cls, "__adcp_schema__", None)
    return schema_at(ref, module=cls.__module__) if isinstance(ref, SchemaRef) else {}


def probes(members: list[type[BaseModel]]) -> list[Any]:
    """Every payload a DECISION is graded over: the derived set plus the table's own.

    **The second half is why probe 7 of this file's fire-probe reddens.**  A payload set
    derived from the members' nodes is built by walking declared types, so it reaches a
    ``const`` and an ``enum[0]`` and nothing else -- and the facts the dropped-conjunct
    groups turn on are stated inside an ``if``, which the walk does not enter.  Measured:
    the derived set finds no verdict difference at the ``core/error.json`` group, so a
    collapse graded on it alone would pass over a class that admits what its own document
    refuses.  Every payload any row of :data:`tests.duplicates.DECIDED` carries is
    therefore offered to every group -- those payloads are the bundle's own words, read off
    the documents that state the conjuncts, and a decision that cannot survive another
    row's payload is a decision to look at again.
    """
    seen: set[str] = set()
    out: list[Any] = []
    for payload in from_each_own_node(members) + [
        row.payload for row in duplicates.DECIDED if row.payload is not duplicates.NO_PAYLOAD
    ]:
        spelled = json.dumps(payload, sort_keys=True, default=repr)
        if spelled not in seen:
            seen.add(spelled)
            out.append(payload)
    return out


def from_each_own_node(members: list[type[BaseModel]]) -> list[Any]:
    """Payloads derived from EVERY member's own applied node, deduplicated.

    :func:`payloads_for`'s set over the group's shared pydantic schema probes what the
    CLASSES state; this one probes what the DOCUMENTS state, because a member's applied
    node carries the conjuncts, the ``not``\\ s and the enclosing compositions no part of
    the five-part key holds.  Union over the members and not over the first, since the
    whole question a decision asks is whether one document states something another does
    not.
    """
    seen: set[str] = set()
    out: list[Any] = []
    for member in members:
        node = applied_at(member)
        for payload in payloads_for(node if isinstance(node, dict) else {}):
            spelled = json.dumps(payload, sort_keys=True, default=repr)
            if spelled not in seen:
                seen.add(spelled)
                out.append(payload)
    return out


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

    **AND THE SECOND KIND OF SECOND NAME IS ON THE SAME EQUALITY AND NOT BESIDE IT**
    (``lower/names.UPSTREAM_TITLE_CASE``, ``Emitted.recased``).  A document ROOT whose
    title carries an acronym is spelled one way by this compiler and was spelled another
    by upstream's, and the module binds upstream's beside ours -- so the tree has names
    bound beyond the class they name for a second REASON.  ``Emitted.recased`` is the
    run's record of exactly those, read here as the second term of the union, which is
    what keeps the equality an equality: a recasing the tree carries and the run did not
    record is as red as an adoption's missing name, and so is the reverse.  It is NOT an
    allowance -- nothing is subtracted, and a binding neither record accounts for still
    fails.

    **AND THE THIRD IS THE OTHER HALF OF THAT SAME REASON** (``codegen.structure``,
    ``Emitted.restructured``).  A position no TITLE names -- a union branch leaf, an array
    element, a nested model, a nested enumeration -- was named by upstream's generator from
    the FIELD PATH and numbered by traversal order (``Assets``, ``Assets9``, ``Fields``),
    and the module binds that published word beside ours where a structural join finds it
    uniquely.  It is the same kind of second name as a recasing, so it goes on the same
    equality for the same reason: three terms, nothing subtracted, and a word in any record
    the tree does not carry as a class fails here.

    **AND THE FOURTH IS UPSTREAM'S OWN SENTENCE, WHICH THIS EQUALITY WAS RED FOR UNTIL THE
    RECORD CARRIED IT** (``codegen.structure.bind_statements``, ``Emitted.stated``).  The
    third key the lowering joins upstream's surface on is a STATEMENT upstream wrote --
    ``Creatives1 = Creative``, ``PrincipalCurrentResult = Result2`` -- and the module binds
    that word beside ours exactly as the other two do.  ``lower/names.assign`` has written
    the record since the key landed and ``Emitted`` did not carry it, so this test could
    read two of the three and **reported 34 bindings as unaccounted while the run had
    recorded every one of them** -- ``protocol/get-principal-response.json``'s four
    ``Principal*Result`` words among them, which is the same defect
    ``emit._alias_words`` was written for, found from the other end.  The term is the
    record, not an allowance: nothing is subtracted, and a word the record names and the
    tree does not carry as a class still fails.
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
    recased: set[tuple[str, str]] = set()
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
        # **Keyed on the MODULE and not on the document, which is how the run records a
        # recasing** -- it is not a position of the document, so there is no pointer to
        # reach it by (``Emitted.recased``).  ``emit.module_path`` is the key's own
        # spelling, a bundle-relative path, which is why the dotted module name is turned
        # back into a document first.  A word the record names and the tree does not carry
        # as a class is left out of this term, so the equality below reports it.
        # All THREE second-name records of the module are read in one pass, because they
        # are the same KIND of binding reached by three keys -- a title's recasing, a
        # structural join and a statement of upstream's own -- and a reader that took one
        # for the other would report a binding as unaccounted while the run had recorded
        # it (``Emitted.restructured``, ``Emitted.stated``).  :meth:`Emitted.upstream_words`
        # is that union, so this reads the one merge ``emit`` itself exports rather than
        # restating it: a fourth key would reach here with nothing edited, and the two
        # readers cannot come to disagree about what the tree states.
        for word in out.upstream_words().get(emit.module_path(document), {}):
            bound = getattr(imported, word, None)
            if isinstance(bound, type) and id(bound) in objects:
                recased.add((name, word))
        for pointer, adopted in out.adopted[document].items():
            derived = out.declared[document][pointer]
            if derived == adopted:
                continue  # ``assign`` dropped a degenerate ``X = X``; no second name
            bound = getattr(imported, derived, None)
            if isinstance(bound, type) and id(bound) in objects:
                renamed_adoptions.add((name, derived))

    claimed("names bound beyond the class they name", named_twice)
    claimed("second names the run recorded as an adoption's", renamed_adoptions)
    claimed("second names the run recorded as one of UPSTREAM's own words", recased)
    accounted = renamed_adoptions | recased
    assert named_twice == accounted, {
        "a second name with no adoption and no upstream word behind it": sorted(
            named_twice - accounted
        ),
        "an adoption whose second name the tree does not carry": sorted(
            renamed_adoptions - named_twice
        ),
        "an upstream word the record names and the tree does not carry": sorted(
            recased - named_twice
        ),
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

    **The cross-document groups are asserted over by
    :func:`test_every_cross_document_duplicate_group_is_decided`**, which is a different
    claim with a different repair: two documents RESTATING one structure needs a NAME or a
    reading, and nothing in one document decides it.  The partition below is what makes the
    split total -- every group the key forms is in exactly one part -- so a group cannot
    fall out of both, and the two parts together are the whole duplicate question.
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


def test_one_schema_node_is_declared_by_at_most_one_class() -> None:
    """**A NODE IS ONE NODE, SO IT GETS ONE CLASS**, and the key is the node alone.

    ``docs/plan/final-state.md`` reading 4: *"a type stated at more than one position is
    written once and referenced, never restated"*.  The two gates beside this one read that
    through the five-part KEY, so each is silent wherever the key separates two declarations
    -- and two classes at ONE node that state different content ARE separated by it, which
    ``test_one_document_declaring_two_classes_for_one_type_reddens_the_gate``'s ``split``
    pair asserts from the other side.  This is the clause that has no key but the node, so
    nothing a declaration says about itself can hide a second declaration of it.

    **TWO readings, and they are a BIJECTION rather than a one-way count.**  No node carries
    two class objects, and no declaration is without a node -- so ``declarations``, ``nodes``
    and ``distinct nodes`` are one number, and a class that lost its reference cannot pay for
    a node that gained one.

    **The NAME population is :func:`test_a_second_name_at_a_node_is_not_a_second_declaration`
    and is deliberately not here**, because it is a different obligation with a different red
    direction: this one fails when the EMITTER declares twice, that one also fails when the
    emitter stops aliasing at all, and a single test holding both reddens on either without
    saying which.  Measured: §4's content dedup switched off reddens the name reading on an
    empty population and leaves this gate GREEN, because a second class at a second node is
    not a second class at one node.

    Its red direction is :func:`test_two_classes_at_one_schema_node_redden_the_gate`, and the
    EMITTER's is ``./perturb_two_classes_at_one_node.sh``, which runs every gate under every
    case because a clause that reddens where an existing one also reddens is a second
    spelling of it: ``declare_object`` made to hand the adagents ``oneOf/1`` branch its
    ``oneOf/0`` sibling's reference reddens THIS and leaves
    ``test_no_two_declarations_of_one_document_are_one_type`` green, which is the measurement
    that says the clause was missing rather than unexercised.
    """
    tree = the_tree()
    declarations = [cls for members in tree.values() for cls in members]
    claimed("declarations of the emitted tree", declarations)
    nodes = [at for cls in declarations if (at := ref_of(cls)) is not None]
    claimed("schema nodes the tree declares a class for", nodes)

    twice = two_classes_at_one_node(declarations)
    assert twice == {}, {
        f"{document} {pointer}": sorted(f"{cls.__module__}.{cls.__name__}" for cls in members)
        for (document, pointer), members in twice.items()
    }
    # The same fact from the other side: every declaration names a node and no two name one,
    # so the two sets are one bijection and nothing is left over in either direction.
    assert len(set(nodes)) == len(nodes) == len(declarations), {
        "declarations": len(declarations),
        "nodes": len(nodes),
        "distinct nodes": len(set(nodes)),
    }


def test_a_second_name_at_a_node_is_not_a_second_declaration() -> None:
    """The 35 names at 17 nodes, through the SAME function, and still ``{}``.

    **This is the sentence ``adcp-client-python-qpzf`` needed and could not get from a
    count.**  That report walked ``__adcp_schema__`` and found *"17 ``(document, pointer)``
    pairs carrying MORE THAN ONE class, involving 35 classes"*; the pairs are real and the
    classes are not -- ``SignalTagsValue = TagsValue`` is one object at one node under two
    names, and a Python assignment carries the aliased class's ``__adcp_schema__`` because it
    carries the aliased class.  So the measurement cannot tell §4's dedup WORKING from
    reading 4 broken, and the answer is to hand the name population to the gate and assert
    the verdict rather than to argue it.

    ``claimed`` is what makes it an assertion: the 17 nodes are a LIVE population read off
    this run's tree, so if the emitter ever stops aliasing, this reddens on an empty
    population instead of passing vacuously -- which is exactly what §4's content dedup
    switched off does, and it leaves
    :func:`test_one_schema_node_is_declared_by_at_most_one_class` green while doing it.

    The BINDING and never ``cls.__name__``: an alias's ``__name__`` is the DECLARING name at
    both of its bindings, which is the same reason ``ref_of`` reads the same pair twice and is
    the whole reason this population exists.
    """
    import adcp.types._schemas as pkg

    every_binding = [
        (binding, cls) for name in modules_of(pkg) for binding, cls in bindings_in(importlib.import_module(name))
    ]
    bound = [cls for _, cls in every_binding]
    several: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for binding, cls in every_binding:
        if (at := ref_of(cls)) is not None:
            several[at].add(binding)
    at_several_names = {at for at, names in several.items() if len(names) > 1}
    claimed("schema nodes the tree binds more than one NAME at", at_several_names)

    declarations = [cls for members in the_tree().values() for cls in members]
    assert len(bound) > len(declarations), (len(bound), len(declarations))
    assert two_classes_at_one_node(bound) == {}, two_classes_at_one_node(bound)
    # And the names beyond the declarations are exactly the second and later names at those
    # nodes, so the surplus is accounted for by this population and not by something else.
    assert len(bound) - len(declarations) == sum(len(several[at]) - 1 for at in at_several_names)


def test_two_classes_at_one_schema_node_redden_the_gate() -> None:
    """The gate's own reading, over a pair built to hold the defect -- and the GAP, measured.

    :func:`test_one_schema_node_is_declared_by_at_most_one_class` is the green direction and
    ``assert {} == {}`` passes it.  This calls the SAME function over two classes that name
    one ``(document, pointer)`` and state DIFFERENT content, which is the shape a mis-derived
    home or a reference handed to the wrong declaration produces.

    **The second assertion is the clause's whole justification and is not a restatement of
    the first.**  ``restated_within_one_document`` is GREEN on that very pair, correctly: the
    two differ in part 1 of the five-part key, so they are not one type and the group never
    forms.  Part 1 is therefore the part that separates them, and a guard spelled on the key
    is blind in exactly this difference -- the same sentence
    :func:`test_the_schema_half_of_the_key_would_otherwise_carry_the_name` makes about the
    title, read at the node layer.

    And the two states that must NOT redden it: one class under a second NAME, which is the
    35-name population the tree actually carries, and two classes at two different nodes,
    which is the group the gates beside this one own.
    """
    document = "one/document.json"
    pointer = "#/oneOf/1/properties/d"
    one = _a_class("AtOne", "one.module", SchemaRef(document=document, pointer=pointer))
    other = _a_class(
        "AlsoAtOne",
        "one.module",
        SchemaRef(document=document, pointer=pointer),
        __annotations__={"size": str},
        size="x",
    )
    pair = [one, other]
    found = two_classes_at_one_node(pair)
    assert list(found) == [(document, pointer)], found
    assert found[(document, pointer)] == pair

    # THE GAP: the five-part key separates them on part 1, so the gate beside this one is
    # green on the same pair and the clause above is not a second spelling of it.
    assert restated_within_one_document(pair) == {}, restated_within_one_document(pair)
    assert key_of(one) != key_of(other)
    assert key_of(one)[1:] == key_of(other)[1:]  # parts 2-5 agree; part 1 is what differs

    # One class under a second name is ONE declaration.
    assert two_classes_at_one_node([one, one]) == {}
    # And two classes at two nodes are the neighbouring defect, not this one.
    elsewhere = _a_class("Elsewhere", "one.module", SchemaRef(document=document, pointer="#/oneOf/0/properties/d"))
    assert two_classes_at_one_node([one, elsewhere]) == {}
    assert len(restated_within_one_document([one, elsewhere])) == 1


def named_at_every_position(bundle_dir: Path) -> dict[str, tuple[str, frozenset[tuple[str, str]]]]:
    """Every structure the BUNDLE names with ONE title at EVERY position that states it.

    ``key -> (the title, the (document, pointer) set)``, over both structural layers §3a
    collects -- L2's own-``properties`` object types and L2C's composed ones -- because the
    claim is about what the bundle SAYS and not about which layer reads it.  A reader that
    took one layer would be silent wherever the other answered, and the two partition the
    object positions rather than overlap (``catalogue.shape_states``).

    **The condition is the judgment table's own evidence sentence**, not a weaker one: *"the
    bundle names EVERY one of the N positions"*.  One title among several untitled positions
    says nothing about the positions that are silent, so a group with one is not a group the
    bundle names -- which is why this reads ``all`` and not ``len(titles) == 1``.
    """
    admitted = catalogue.Admitted(bundle_dir)
    standing = emit.standing_order(bundle_dir)
    found: dict[str, tuple[str, frozenset[tuple[str, str]]]] = {}
    for layer in ("L2", "L2C"):
        groups: dict[str, list[catalogue.Shaped]] = {}
        for position in catalogue.shape_states(admitted, layer):
            groups.setdefault(position.key, []).append(position)
        for key, group in groups.items():
            titles = {p.title for p in group}
            if len(group) < 2 or len({p.document for p in group}) < 2:
                continue
            if len(titles) != 1 or None in titles:
                continue
            found[key] = (
                next(iter(titles)),
                frozenset((p.document, f"#{p.pointer}") for p in group),
            )
    assert standing  # the home rule's input; a layer collected without it has no home
    return found


def declared_twice_though_named(
    declarations: list[type[BaseModel]], named: dict[str, tuple[str, frozenset[tuple[str, str]]]]
) -> dict[str, list[str]]:
    """Titles the bundle states at every position of a structure the TREE declares twice.

    The two derivations this gate is an equality between: the left is the bundle's own
    titles (:func:`named_at_every_position`), the right is the tree's declarations grouped
    by the five-part key.  A title appears here exactly when two or more declarations of
    ONE type both name a position the bundle gave that title -- which is the defect, stated
    as what the bundle says against what the tree wrote and not as a count.
    """
    at: dict[tuple[str, str], str] = {
        position: title for title, positions in named.values() for position in positions
    }
    out: dict[str, list[str]] = {}
    for members in grouped(declarations).values():
        if len(members) < 2:
            continue
        titled = [
            (at[where], cls)
            for cls in members
            if (where := (ref_of(cls) or ("", ""))[0:2]) in at
        ]
        for title, _ in titled:
            if sum(1 for other, _ in titled if other == title) > 1:
                out.setdefault(title, []).extend(
                    f"{cls.__module__}.{cls.__name__} {ref_of(cls)}" for _, cls in titled
                )
    return {title: sorted(set(where)) for title, where in out.items()}


def test_a_structure_the_bundle_titles_at_every_position_is_declared_once() -> None:
    """**A TITLE IS A NAME FOR A SUBJECT, so the subject gets ONE class.**

    ``docs/plan/final-state.md`` reading 4: *"a type stated at more than one position is
    written once and referenced, never restated"*.  The gate above asserts that per
    DOCUMENT and reports the cross-document groups, because *"the type needs a NAME and
    nothing in one document decides it"*.  **This is the half of that clause the bundle can
    discharge**: where the bundle names every stating position of one structure with one and
    the same ``title``, the name is no longer undecided, so the reason the cross-document
    groups were reported rather than asserted over does not reach them and they are a
    duplicate like any other.

    **Both derivations are readings and neither is a literal.**  The left is
    ``catalogue.shape_states`` over the bundle a RUN reads, which is the published bundle
    with the override table applied -- so the titles this ranges over are the ones upstream
    states plus the ones ``patches/8735`` asks upstream for, and a title landing upstream
    moves nothing here because ``patch.additions`` refuses an entry whose node already
    carries the keyword.  The right is the tree's own declarations under the five-part key.
    Empty is the invariant, and the failure names the TITLE -- which is the thing a reader
    has to go and look at -- with every declaration that took it.

    **Red on the state this test exists for**, measured rather than asserted: with
    ``patches/8735``'s four titles in the override table and the L2C layer absent from
    ``codegen/emit.py``'s collection, this reads **9 structures the bundle titles at every
    stating position and reddens on 4 of them, over 12 declarations** -- URL Macro
    Declaration at 5, Explicit Collection Selector at 3, Publisher Placement Reference at
    2, Unlocalized Creative Asset at 2.  Its own red direction is
    :func:`test_a_titled_restatement_declared_twice_reddens_the_gate`, which calls
    :func:`declared_twice_though_named` over a pair built to hold the defect.
    """
    declarations = [cls for members in the_tree().values() for cls in members]
    named = named_at_every_position(BUNDLE)
    claimed("structures the bundle titles at every stating position", named)
    restated = declared_twice_though_named(declarations, named)
    assert restated == {}, restated


# --------------------------------------------------------------------------- #
# 2b. Every cross-document group is DECIDED, and the decision is on the artifact
# --------------------------------------------------------------------------- #
def cross_document_groups(
    declarations: list[type[BaseModel]],
) -> dict[frozenset[duplicates.POSITION], list[type[BaseModel]]]:
    """The groups of the key whose members name MORE THAN ONE document, keyed by position.

    The key a ROW carries (``tests.duplicates.key_for``) and never a name, a module or a
    count -- so the table and this reading cannot come apart, and a group whose members
    moved to other pointers reports as a new group rather than silently matching an old
    row.
    """
    out: dict[frozenset[duplicates.POSITION], list[type[BaseModel]]] = {}
    for members in grouped(declarations).values():
        if len(members) > 1 and len({document_of(cls) for cls in members}) > 1:
            out[duplicates.key_for(members)] = members
    return out


def _states(at: duplicates.POSITION) -> dict[str, Any] | None:
    """The node the BUNDLE A RUN READS states at ``at``, or ``None`` where it states none.

    The published bundle with the build's patch sets applied, which is the bundle the tree
    was compiled from -- reading the published one here would hide every title
    ``patches/8735`` supplies from the one check that is about what the bundle says.  A
    ``None`` is a FACT and is asserted on rather than defaulted: a row keyed on a pointer
    no document states is a row nobody can check.
    """
    document, pointer = at
    try:
        node = bundle.node_at(bundle.read(BUNDLE, document), pointer.lstrip("#"))
    except (KeyError, IndexError, TypeError, OSError, ValueError):
        # A document the bundle does not hold and a pointer it does not state are the SAME
        # answer here -- "the bundle says nothing at this position" -- and both are facts a
        # row can be wrong about, so neither may escape as an exception from a reading whose
        # whole job is to report what the bundle states.
        return None
    return node if isinstance(node, dict) else None


def test_every_cross_document_duplicate_group_is_decided() -> None:
    """**ONE ROW PER GROUP, IN BOTH DIRECTIONS, AND THE EQUALITY IS ON THE EMITTED TREE.**

    ``docs/plan/final-state.md`` reading 9: *"Each declared fact is ours with a decision
    recorded, or upstream with an issue that exists.  An unfiled gap is ours."*  A duplicate
    group is such a fact, and until this check existed the cross-document ones were listed
    in a report that nothing graded -- so a group could appear, be looked at by nobody, and
    leave the duplicate question's figure a sentence in a bead rather than a measurement.

    **The left side is the ARTIFACT and the right side is the table.**  A group the tree
    forms and the table does not answer is RED with its positions named, because nobody
    decided it.  A row the tree no longer forms is RED too and the instruction is to DELETE
    it: that is the architecture's removability clause for the one kind of entry that adds
    no document and transcribes no keyword -- *"an override that is no longer needed must
    BREAK THE BUILD"* -- and it fires the day a repair lands or the bundle moves.

    The row count is a DEBT figure and ratchets DOWN only.
    """
    tree = the_tree()
    declarations = [cls for members in tree.values() for cls in members]
    live = cross_document_groups(declarations)
    claimed("cross-document groups the emitted tree forms", live)
    decided = duplicates.by_position()
    claimed("rows of the decision table", decided)

    assert set(live) == set(decided), {
        "a duplicate group nobody decided -- add a row to tests/duplicates.py": [
            {
                "at": sorted(at),
                "declares": sorted(f"{c.__module__}.{c.__name__}" for c in live[at]),
            }
            for at in set(live) - set(decided)
        ],
        "a row whose group the tree no longer forms -- DELETE it": [
            {"at": sorted(at), "outcome": decided[at].outcome, "ask": decided[at].ask}
            for at in set(decided) - set(live)
        ],
    }
    partitions(
        set(live),
        **{
            outcome: {at for at, row in decided.items() if row.outcome == outcome}
            for outcome in sorted({row.outcome for row in duplicates.DECIDED})
        },
    )
    ratchet(
        "cross-document duplicate groups the table answers locally",
        len(decided),
        at_most=8,
        because="the table's size IS the debt figure: a row names the ask that deletes it, "
        "so this falls to zero for a bundle that titles what it restates and a compiler "
        "that declares a type once.  A RISE is a new duplicate nobody decided, which is "
        "what the equality above reports before this ratchet is reached",
    )
    # **AND NO ROW IS A COLLAPSE, which is a stronger statement than the count and is the
    # one the architecture makes**: a COLLAPSE is the outcome whose defect is OURS -- one
    # subject declared twice and the bundle naming it -- so such a row IS "an override the
    # build does not apply".  The three this table held are applied by the build now
    # (``adcp-client-python-8212``, ``-nlkz``, ``-e4z``), and a new one may not be written
    # here in place of the repair it owes: the ratchet above would admit a ninth row
    # dropping to eight elsewhere, and this clause would not.
    assert [row.at for row in duplicates.DECIDED if row.outcome == duplicates.COLLAPSE] == []
    for row in duplicates.DECIDED:
        assert row.defect.strip() and row.ask.strip(), row
        assert "the bundle" in row.defect or row.defect.startswith("NONE"), row.defect


def unproved(row: duplicates.Decided, members: list[type[BaseModel]]) -> list[dict[str, Any]]:
    """Every way this row's EVIDENCE fails to support its outcome, over the live group.

    **A function and not a loop body, because the gate's red direction calls it.**  The
    green direction is an empty list over eleven rows the table already decides correctly,
    and ``assert [] == []`` proves nothing; the red direction perturbs each live row into
    the outcome its evidence does NOT support and calls this, which is the one arrangement
    where "the evidence is graded" is a claim about the thing shipped.

    One form per outcome, each able to go red on its own cause:

    * ``SPLIT`` with a payload -- the two DOCUMENTS disagree on it, so one admits what
      another refuses.  **Both verdicts and both reasons are reported**, because two classes
      refusing one payload for different reasons are not evidence of anything and that
      error has been made on this epic.  Red the day the two documents converge.
    * ``SPLIT`` by the bundle's words -- two or more different ``title`` strings over the
      group's own positions.  Red the day upstream unifies them, which is the day the split
      stops being the bundle's and becomes ours.
    * ``PENDING A NAME`` -- the bundle titles NO position of the group and names the
      positions by two or more different words.  Red the day a title arrives, which IS the
      ask, and red the day the words converge, which would make a title a transcription
      rather than a judgment.
    * ``NOT ONE TYPE`` -- the payload a member's class ADMITS through ``model_validate``
      while its own document REFUSES it through ``strict_validate``.  Red the day the
      dropped fact is carried, and the group un-forms at the same moment.
    * ``COLLAPSE`` -- no payload of :func:`probes` makes any member disagree with its OWN
      DOCUMENT or with another member, **and** the bundle names the subject at a position
      of the structure.  Red the day a document stops stating that title.
    """
    at = row.at
    where = sorted(f"{c.__module__}.{c.__name__} {ref_of(c)}" for c in members)
    found: list[dict[str, Any]] = []
    through_the_document: dict[str, Any] = {}

    if row.payload is not duplicates.NO_PAYLOAD and row.outcome in (
        duplicates.SPLIT,
        duplicates.NOT_ONE_TYPE,
    ):
        through_the_document = {
            f"{c.__module__}.{c.__name__}": _verdict(c, row.payload, strict=True)
            for c in members
        }
        admits = {n for n, v in through_the_document.items() if v[0].startswith("admitted")}
        refuses = {n for n, v in through_the_document.items() if v[0] == "refused"}
        if not (admits and refuses):
            found.append(
                {
                    "the row's payload does not discriminate": row.payload,
                    "verdicts, with the reason and not only the verdict": through_the_document,
                    "over": where,
                }
            )

    if row.outcome == duplicates.NOT_ONE_TYPE:
        through_the_class = {
            f"{c.__module__}.{c.__name__}": _verdict(c, row.payload, strict=False)
            for c in members
        }
        dropped = {
            name
            for name, verdict in through_the_class.items()
            if verdict[0].startswith("admitted")
            and through_the_document.get(name, ("",))[0] == "refused"
        }
        if not dropped:
            found.append(
                {
                    "no member admits what its own document refuses, so the group is not a "
                    "dropped fact and NOT ONE TYPE is the wrong outcome": row.ask,
                    "through the class": through_the_class,
                    "through the document": through_the_document,
                }
            )

    if row.outcome == duplicates.SPLIT and row.payload is duplicates.NO_PAYLOAD:
        titles = {
            title
            for position in at
            if isinstance(title := (_states(position) or {}).get("title"), str)
        }
        if len(titles) < 2:
            found.append(
                {
                    "a SPLIT with no payload is the bundle's own two names, and the bundle "
                    "states fewer than two here": sorted(titles),
                    "over": where,
                }
            )

    if row.outcome == duplicates.PENDING_A_NAME:
        stated = {position: _states(position) for position in at}
        silent = sorted(position for position, node in stated.items() if node is None)
        if silent:
            found.append({"a row keyed on a pointer no document states": silent})
        titled = sorted(position for position, node in stated.items() if "title" in (node or {}))
        if titled:
            found.append(
                {
                    "the bundle titles a position of a group that is PENDING A NAME, so the "
                    "ask has landed and the row is to be re-read": titled
                }
            )
        words = {judgment_name_at(pointer) for _, pointer in at}
        if len(words) < 2:
            found.append(
                {
                    "the positions agree on one word, so this is a transcription and not a "
                    "silence": sorted(map(str, words)),
                    "over": where,
                }
            )

    if row.outcome == duplicates.COLLAPSE:
        pool = probes(members)
        # **THE HALF A MEMBER-VERSUS-MEMBER READING CANNOT GIVE.**  The three dropped-fact
        # groups agree with EACH OTHER on every derived payload too -- that is what makes
        # them look like duplicates -- so what a collapse has to answer is not whether the
        # members agree but whether each member agrees with ITS OWN DOCUMENT.  Measured: 0
        # mismatches at all three collapses and at least one at every ``NOT ONE TYPE``
        # group.  The member-versus-member reading alone passed the ``core/error.json``
        # group as a collapse, which is the probe this clause exists for.
        loose = [
            {
                "class": f"{c.__module__}.{c.__name__}",
                "payload": payload,
                "through the class": _verdict(c, payload, strict=False),
                "through its own document": _verdict(c, payload, strict=True),
            }
            for c in members
            for payload in pool
            if _verdict(c, payload, strict=False)[0].startswith("admitted")
            != _verdict(c, payload, strict=True)[0].startswith("admitted")
        ]
        if loose:
            found.append(
                {
                    "a COLLAPSE whose member disagrees with its own DOCUMENT is a dropped "
                    "fact wearing a duplicate, not a collapse": loose[:2],
                    "over": where,
                }
            )
        for strict in (False, True):
            apart = [
                one
                for one in disagreements(members, strict=strict, over=pool)
                if len({v[0] for v in one["verdicts"].values()}) > 1
            ]
            if apart:
                found.append(
                    {
                        "a COLLAPSE whose members disagree on a VALUE is two subjects": apart[:2],
                        "strict": strict,
                        "over": where,
                    }
                )
        document, pointer, title = row.names_the_subject or ("", "", None)
        node = _states((document, pointer))
        if node is None:
            found.append(
                {"the position the row says names the subject is not in the bundle": (document, pointer)}
            )
        elif node.get("title") != title:
            found.append(
                {
                    "the bundle no longer names the subject here, so the collapse is no "
                    "longer licensed by it": (document, pointer, node.get("title"), title)
                }
            )
    return found


def test_each_decision_is_proved_by_a_value_or_by_the_bundle_s_own_words() -> None:
    """**THE EVIDENCE OBLIGATION, graded over the group each row decides.**

    A shared key is a HYPOTHESIS.  ``test_the_key_agrees_on_a_value_wherever_it_groups``
    says the key is sound over what the CLASSES do, and that is exactly why it cannot
    decide a group: what a decision turns on is what the DOCUMENTS do, and no part of the
    key carries one.  :func:`unproved` is the reading and holds the five forms;
    :func:`test_a_decision_whose_evidence_does_not_support_it_reddens_the_gate` is this
    one's red direction and calls the same function.
    """
    declarations = [cls for members in the_tree().values() for cls in members]
    live = cross_document_groups(declarations)
    decided = duplicates.by_position()
    graded = claimed("decided groups the tree still forms", set(live) & set(decided))
    claimed(
        "payloads the table offers every group",
        [
            json.dumps(row.payload, sort_keys=True, default=repr)
            for row in duplicates.DECIDED
            if row.payload is not duplicates.NO_PAYLOAD
        ],
    )
    for at in sorted(graded, key=sorted):
        assert unproved(decided[at], live[at]) == [], {
            "outcome": decided[at].outcome,
            "ask": decided[at].ask,
            "unproved": unproved(decided[at], live[at]),
        }


def test_a_decision_whose_evidence_does_not_support_it_reddens_the_gate() -> None:
    """Each live row perturbed into an outcome its own evidence refutes, through
    :func:`unproved` itself.

    Five perturbations, each measured on this bundle rather than assumed, and each the
    mistake the corresponding clause exists to catch:

    1. a dropped-fact group re-declared a ``COLLAPSE`` -- the member-versus-member reading
       passes it and the class-versus-document reading does not, which is why both are in;
    2. a ``PENDING A NAME`` group re-declared a ``SPLIT`` -- the bundle titles none of its
       positions, so there are no two names to split on;
    3. a ``SPLIT``-by-titles group re-declared ``PENDING A NAME`` -- the bundle titles it,
       so the silence the outcome claims is not there;
    4. a row's proving payload replaced by one the group's documents agree on;
    5. a ``COLLAPSE``'s named subject pointed at a title the bundle does not state there --
       **asked of a group re-declared a COLLAPSE and not of a live one, because there is no
       live COLLAPSE row left and the clause still has to be graded.**  All three were
       applied by the build (``tests/duplicates.py``'s own docstring), so the licence half
       of the COLLAPSE evidence form is reached the only way it can be: perturb a row into
       that outcome, then perturb the licence, and require the second finding by its own
       sentence.  Asserting the LIST is non-empty would pass on the wrong finding, since a
       re-declared ``NOT ONE TYPE`` group reddens the member-versus-document clause too.

    The green state is asserted beside each one, so a perturbation that reddens because the
    function reddens on everything is reported as such.
    """
    declarations = [cls for members in the_tree().values() for cls in members]
    live = cross_document_groups(declarations)
    rows = {at: row for at, row in duplicates.by_position().items() if at in live}
    claimed("rows whose group the tree forms, which the perturbations range over", rows)

    def perturbed(row: duplicates.Decided, **moved: Any) -> list[dict[str, Any]]:
        return unproved(dataclasses.replace(row, **moved), live[row.at])

    for at, row in rows.items():
        assert unproved(row, live[at]) == [], (row.outcome, at)
        if row.outcome == duplicates.NOT_ONE_TYPE:
            assert perturbed(
                row, outcome=duplicates.COLLAPSE, names_the_subject=row.names_the_subject
            ), at
            assert perturbed(row, payload={}), at
            # The LICENCE half of the COLLAPSE evidence form, reached through this row
            # because no live row carries that outcome any more.  A position of this
            # group the bundle DOES title, with a title it does not state there.
            titled = sorted(
                position for position in at if "title" in (_states(position) or {})
            )
            for position in titled[:1]:
                assert any(
                    "no longer names the subject" in sentence
                    for found in perturbed(
                        row,
                        outcome=duplicates.COLLAPSE,
                        names_the_subject=(*position, "A Title No Document States"),
                    )
                    for sentence in found
                ), (at, position)
        if row.outcome == duplicates.PENDING_A_NAME:
            assert perturbed(row, outcome=duplicates.SPLIT), at
        if row.outcome == duplicates.SPLIT and row.payload is duplicates.NO_PAYLOAD:
            assert perturbed(row, outcome=duplicates.PENDING_A_NAME), at
        if row.outcome == duplicates.SPLIT and row.payload is not duplicates.NO_PAYLOAD:
            assert perturbed(row, payload={}), at


def test_a_group_with_no_row_and_a_row_with_no_group_both_redden_the_gate() -> None:
    """The gate's own readings, over trees and tables built to hold each failure.

    ``test_every_cross_document_duplicate_group_is_decided`` is an equality between two
    derivations and ``assert set() == set()`` would pass it, so each direction is shown
    over the SAME functions rather than over a restated predicate.

    Four states: a group the table does not answer, a row the tree does not form, the
    answered state that must stay green, and a SAME-document group -- which must not enter
    this population at all, because the gate above owns it and a decision table that could
    answer one would be an exemption for the defect this file exists to assert away.
    """
    one = ("one/document.json", "#/properties/a/items")
    other = ("another/document.json", "#/properties/b/items")
    pair = [
        _a_class("AtOne", "one.module", SchemaRef(document=one[0], pointer=one[1])),
        _a_class("AtOther", "another.module", SchemaRef(document=other[0], pointer=other[1])),
    ]
    live = cross_document_groups(pair)
    assert set(live) == {frozenset({one, other})}, live

    answered = {frozenset({one, other}): duplicates.DECIDED[0]}
    assert set(live) - set(answered) == set()
    assert set(answered) - set(live) == set()
    # A group the table does not answer, and a row the tree does not form.
    assert set(live) - set() == set(live)
    stale = {frozenset({("gone.json", "#")}): duplicates.DECIDED[0]}
    assert set(stale) - set(live) == set(stale)
    # And two declarations of ONE document never reach this population.
    same = [
        _a_class("AtZero", "one.module", SchemaRef(document=one[0], pointer="#/oneOf/0/d")),
        _a_class("AtOne", "one.module", SchemaRef(document=one[0], pointer="#/oneOf/1/d")),
    ]
    assert cross_document_groups(same) == {}, cross_document_groups(same)
    assert len(restated_within_one_document(same)) == 1


def test_a_titled_restatement_declared_twice_reddens_the_gate() -> None:
    """The gate's own reading, over two classes built to hold the defect.

    ``test_a_structure_the_bundle_titles_at_every_position_is_declared_once`` is the green
    direction and ``assert {} == {}`` passes it.  This calls the SAME function -- a restated
    predicate would prove that a copy of the gate reddens, which is not the claim -- over
    two declarations of one type at two positions one title names, and over the two states
    that must NOT redden it: the same pair with only one of the positions named, and a
    single declaration at a named position.
    """
    one = ("one/document.json", "#/properties/a/items")
    other = ("another/document.json", "#/properties/b/items")
    pair = [
        _a_class("AtOne", "one.module", SchemaRef(document=one[0], pointer=one[1])),
        _a_class("AtOther", "another.module", SchemaRef(document=other[0], pointer=other[1])),
    ]
    both = {"k": ("A Subject", frozenset({one, other}))}
    assert declared_twice_though_named(pair, both) == {
        "A Subject": sorted(
            f"{cls.__module__}.{cls.__name__} {ref_of(cls)}" for cls in pair
        )
    }
    # One position named and the other silent is NOT this defect: the bundle has not said
    # the two are one subject, which is ``named_at_every_position``'s own condition read
    # from the other side.
    assert declared_twice_though_named(pair, {"k": ("A Subject", frozenset({one}))}) == {}
    # And one declaration at a named position is the collapsed state, which must stay green.
    assert declared_twice_though_named(pair[:1], both) == {}


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
