"""Grade D2's enumeration row: an ``enum`` node becomes a ``StrEnum``/``IntEnum``.

**Why this file exists at all, and what the harness does and does not reach.**
``tests/test_emit.py`` grades every emitted pair through the three checks, and for
an enumeration two of the three are nearly blind: the accepts and invalid-payload checks
run through ``strict_validate``, whose SCHEMA half refuses a non-member whatever
the annotation says, so they grade the document and not the model.  Measured as a
test below (:func:`test_the_schema_comparison_is_what_grades_this_row`), and the
result corrects a finding carried forward from an earlier attempt at this step:
the SCHEMA COMPARISON does grade it now, because ``enum`` is in
the compared set -- a node lowered to the scalar its ``type`` names states no
``enum`` where the document states one, and that reddens.

What the harness still cannot see is everything about the enumeration that is not
an accepted set: the member NAMES, the per-member descriptions, and the base.  A
lower-cased member is caught by nothing except an import failure, and that is why
the upper-casing is asserted here over the whole emitted population.

Every assertion is over something DERIVED -- the population off the bundle, the
members off the document, the names off the function that runs -- so a pass cannot
be a record of what the tree happens to hold.
"""

from __future__ import annotations

import ast
import enum as pyenum
import importlib
import json
from pathlib import Path
from typing import Annotated, Any

import pytest
from pydantic import Field, TypeAdapter, ValidationError

from adcp.types._base import SchemaRef, schema_at
from codegen import bundle, compiler, emit, ir, keywords, render
from codegen.keywords import Position
from codegen.harness import (
    _entails_type,
    _narrows_nothing,
    _text,
    compare_schema,
    compared_facts,
)
from codegen.lower import enum as lower_enum
from codegen.schema import nodes as schema_nodes
from codegen.schema import parse as schema_parse
from codegen import refusal as refusal_module
import populations
from conftest import refusal_from
from tests.test_emit import BUNDLE, graded, population, TREE
from tests.nodeset import claimed, partitions

def _probe(raw: dict, pointer: str = "", position: Position = Position.PROP) -> schema_nodes.Base:
    """One hand-written declaration as the NODE the parser decides it is.

    §14 step 5 makes a handler take its node, so a test that grades the lowering of a
    shape the bundle does not carry builds the node the way the walk builds it -- through
    ``codegen.schema.parse.parse``, at a pointer and a position of its own.  Going round
    the parser would grade a node no document can produce, which is the fixture-derived-
    from-the-thing-it-grades defect this file's own rules name.
    """
    return schema_parse.parse(
        raw,
        pointer=pointer,
        position=position,
        source=schema_parse.Source(document="probe.json"),
    )



def root_enums() -> list[str]:
    """Every document whose ROOT carries an ``enum``, off the bundle."""
    return [d for d in bundle.portable(BUNDLE) if populations.is_enum_root(bundle.read(BUNDLE, d))]


def emitted_enum_classes() -> list[tuple[str, str, ast.ClassDef]]:
    """``(document, module source, class)`` for every enum class in the tree.

    Read off the AST of what was committed, and selected by the BASE the compiler
    rendered rather than by a name convention, so a class that stopped being an
    enumeration drops out of the population instead of being graded as one.
    """
    out: list[tuple[str, str, ast.ClassDef]] = []
    for document in sorted({g.ref.document for g in graded()}):
        src = (TREE / f"{emit.module_path(document)}.py").read_text()
        for node in ast.walk(ast.parse(src)):
            if isinstance(node, ast.ClassDef) and {
                b.id for b in node.bases if isinstance(b, ast.Name)
            } & {"StrEnum", "IntEnum"}:
                out.append((document, src, node))
    return out


def _members(cls: ast.ClassDef) -> list[tuple[str, Any]]:
    """``(name, value)`` for each member, read off the emitted class body."""
    return [
        (t.id, s.value.value)
        for s in cls.body
        if isinstance(s, ast.Assign) and isinstance(s.value, ast.Constant)
        for t in s.targets
        if isinstance(t, ast.Name)
    ]


# --------------------------------------------------------------------------- #
# the population, and the one refusal
# --------------------------------------------------------------------------- #
def test_every_root_enum_is_emitted_or_refused_by_name_pointer_and_keyword() -> None:
    """The step's exit condition, over its own denominator.

    **214 of 214, and the refusal branch is now empty.** It held one document,
    ``enums/task-type.json``, refused for the ``notes`` beside its ``enum`` --
    and ``salesagent-j3k2l.23`` admitted that annotation, because ``notes`` is
    not a JSON Schema keyword and constrains no instance.

    The branch is kept rather than deleted: it is what makes the 214 a partition
    and not a count, so a root enum this row stops emitting lands here by name
    instead of lowering the figure above with nothing to read.
    """
    roots = claimed("root enums", root_enums(), inside=population())

    out = emit.emit(BUNDLE, population())
    emitted = [d for d in roots if d in out.emitted]
    refused = {d: out.refusals[d] for d in roots if d in out.refusals}
    # EVERY root enum emits and the refusal branch is EMPTY -- asserted as the
    # partition and the empty part, which is what "214 of 214" was two readings of.
    # The number itself is the selector's population and no row of this step may move
    # it, but a row that ADDS a root enum to the bundle moves it correctly, so what is
    # asserted is that the two halves exhaust the roots and that the refused half is
    # empty.
    assert refused == {}, refused
    partitions(roots, emitted=emitted, refused=set(refused))
    claimed("root enums emitted", emitted, inside=roots)

    # And the document that was refused is emitted BY THIS ROW, which the count
    # above does not say on its own: its class is a ``StrEnum`` in the module the
    # emitter names for it.
    assert "enums/task-type.json" in out.emitted
    assert "class TaskType(StrEnum)" in out.files["enums/task_type.py"]

    # Its cascade cost, MEASURED, and the measurement is why admitting ``notes``
    # emitted ONE document and not eight: no referrer of it was ever waiting on
    # this document.  The PARTITION under that claim keeps moving -- all 7
    # refused when this was written, 4 emitted at 16052ffb0 and 6 emit at
    # 0130e5fc9 -- so it is asserted as a partition rather than as "all of them
    # refuse", which was a fact about the tree of the day and never the claim.
    known = set(bundle.portable(BUNDLE))
    referrers = sorted(
        {
            d
            for d in known
            for _, uri, _ in bundle.references(bundle.read(BUNDLE, d))
            if bundle.document_for(uri, known) == "enums/task-type.json"
        }
    )
    claimed("documents referring to enums/task-type.json", referrers, inside=known)
    in_population = claimed(
        "those referrers inside the step's population", 
        [d for d in referrers if d in population()],
        inside=referrers,
    )
    emitted_referrers = sorted(d for d in in_population if d in out.emitted)
    refused_referrers = sorted(d for d in in_population if d in out.refusals)
    # A PARTITION and not two counts: a referrer in NEITHER half would be a document
    # the emitter neither built nor refused, which is what this reports rather than
    # letting two numbers absorb it.  The split itself keeps moving as other rows land
    # -- all 7 refused when this was written, then 4/3, then 6/1 -- and every move was
    # another row doing its work, which is why neither half is counted here.
    partitions(in_population, emitted=emitted_referrers, refused=refused_referrers)
    claimed("referrers emitted", emitted_referrers, inside=in_population)
    # The claim is that none of them was blocked BY this document, which is read off
    # the refusal's own detail, and that is the only reading that still works: the
    # one referrer still refusing refuses on a ``$ref`` at ``/properties/result``,
    # and its detail is a CHAINED one -- "its target core/async-response-data.json
    # is refused: ..." -- so what blocks it is named two documents away.  A keyword
    # test would have read it as this document's cascade; the detail does not.
    assert [d for d in refused_referrers if "task-type" in out.refusals[d]["detail"]] == []


#: The seven population predicates, in the order their steps landed.  Read off
#: ``tests/populations.py`` rather than off ``emit.ROWS``, which §14 step 5 deleted: the
#: walk dispatches on a node's KIND at every position now, so there is no table of
#: selectors and no second reading of a root's kind for a test to count.
ROOT_POPULATIONS = (
    populations.is_object_root,
    populations.is_scalar_root,
    populations.is_enum_root,
    populations.composes_at_the_root,
    populations.union_root,
    populations.is_container_root,
)


def test_the_root_populations_are_disjoint_because_a_root_is_exactly_one_kind() -> None:
    """A root is exactly one kind, and the one word that makes the measurement true.

    **This asserted ``emit.ROWS``, and §14 step 5 deleted the table.**  §5: "Root and
    non-root are one path.  There is no second table of root selectors."  So what was a
    rule about a DISPATCH -- a document two rows claim is a build failure -- is now a
    property of the MEASUREMENTS in ``tests/populations.py``: each one counts the
    documents of one step, and a root belonging to two of them would mean two steps
    counted one document and the epic's arithmetic double-counted it.  The walk cannot
    be ambiguous any more, because a ``match`` over a node's kind reaches one arm.

    Asserted in both directions over all 1,054 documents: 0 counted twice as the
    predicates stand, and 214 -- every root enum -- the moment the scalar one stops
    excluding an enumeration.  So the exclusion is load-bearing and is measured as such.
    """
    documents = [bundle.read(BUNDLE, d) for d in bundle.portable(BUNDLE)]
    claims = [sum(1 for counts in ROOT_POPULATIONS if counts(doc)) for doc in documents]
    assert [n for n in claims if n > 1] == []
    # The two parts partition the bundle, and the one-population part is NON-EMPTY --
    # which is what keeps the disjointness above from being satisfied by predicates that
    # count nothing.  Which documents no predicate describes at all is the other part,
    # and how many there are is a function of the predicates rather than a fact about
    # this step.
    partitions(
        range(len(claims)),
        counted_by_one_population=[i for i, n in enumerate(claims) if n == 1],
        counted_by_no_population=[i for i, n in enumerate(claims) if n == 0],
    )
    assert [i for i, n in enumerate(claims) if n == 1], "no document is counted at all"

    def scalar_without_the_exclusion(doc: dict) -> bool:
        return isinstance(doc.get("type"), str) and doc["type"] in emit.SCALAR

    overlap = [
        d
        for d in bundle.portable(BUNDLE)
        if scalar_without_the_exclusion(bundle.read(BUNDLE, d))
        and populations.is_enum_root(bundle.read(BUNDLE, d))
    ]
    # Every root enum would be claimed twice the moment the scalar row stops excluding
    # an enumeration, so the exclusion is load-bearing.  Asserted as the SET IDENTITY
    # against the root enums rather than as a count of them, because that is the claim:
    # not "214 documents" but "exactly the root enums, each by name".
    assert claimed("documents the scalar row would also claim", overlap) == set(root_enums())

    # A row cannot claim a document its step does not count.
    assert [
        d for d in documents if populations.is_enum_root(d) and not bundle.carries_an_enum(d)
    ] == []


def test_a_root_stating_two_kinds_reaches_one_arm_and_the_enum_wins_by_position() -> None:
    """**``AmbiguousRoot`` is gone, and what replaces it is that there is no table.**

    This asserted the build failure a document two ``emit.ROWS`` selectors claimed
    produced, on a table built to collide, because no bundle document could reach one.
    §14 step 5 deletes the table: §5 says "root and non-root are one path", so a root
    goes to ``emit._decide`` like every other node and a dispatch on a node's KIND
    reaches exactly one arm.  A build failure with no way to occur is not a check that
    was dropped -- it is a shape the structure no longer has.

    What is still a real question is which ARM a root stating two kinds reaches, and
    that is the ORDER of the arms rather than a precedence between rows.
    ``{"type": "string", "enum": [...]}`` is the shape: the ``enum`` arm is read before
    ``type`` is read at all, because the base comes from the MEMBERS
    (``lower.enum.BASES``) and an ``enum`` closes the value set whatever ``type`` the
    document spells beside it.  So the document emits an enumeration, which is what the
    deleted ``is_enum_root`` row did -- and ``populations.is_scalar_root``'s exclusion
    of an enumeration is the measurement above that says the two agree.
    """
    doc = {"title": "Both", "type": "string", "enum": ["a", "b"]}
    mod, symbol = emit.lower_document("both.json", doc)
    assert symbol == "Both"
    # The ENUMERATION, not the scalar alias the ``type`` word would have produced: one
    # declaration, and it is the root binding around an ``EnumDecl``.
    held = [d for d in mod.declarations if isinstance(d, ir.RootBinding)]
    assert [type(d.declaration).__name__ for d in held] == ["EnumDecl"], mod.declarations
    assert [m.value for m in held[0].declaration.members] == ["a", "b"]


# --------------------------------------------------------------------------- #
# the emitted class
# --------------------------------------------------------------------------- #
def test_an_enum_node_is_a_class_over_an_enum_base_and_is_not_also_assigned() -> None:
    """D2: an ``enum`` node is an enumeration, not the scalar its ``type`` names.

    The AST half -- the symbol is a ClassDef over ``StrEnum``/``IntEnum`` and is
    not ALSO a module-level assignment, which is what a lowering that fell back to
    the scalar row would emit -- and then the imported half: the members' values
    are the document's ``enum`` array, in order, exactly.
    """
    classes = emitted_enum_classes()
    # **NO COUNT OF THE CLASSES IS ASSERTED, and the comment that stood here is why.**
    # It recorded eight re-pointings of this one number -- 447, 482, 484, 506, 502, 504,
    # and a 503 that came and went inside a single row -- each one correct, each one a
    # population growing or D3's dedup collapsing a node, and not one of them a defect
    # this check exists to catch.  Two rows in flight compute two different right
    # answers for it.  What IS asserted is the set: the classes the tree carries are
    # non-empty, and the root half of them is exactly the root enums.
    claimed("enum classes the tree carries", {(d, c.name) for d, _, c in classes})
    # The ROOT half is exactly the root enums, by name: every root enum the tree
    # carries a class for IS a root enum, and none is missing.  A set identity rather
    # than a count of 214, so a root enum that stops getting a class is named here.
    roots = [d for d in root_enums() if d in {c[0] for c in classes}]
    assert claimed("root enums with a class", roots) == set(root_enums()), sorted(
        set(root_enums()) - set(roots)
    )

    for document in roots:
        doc = bundle.read(BUNDLE, document)
        module = importlib.import_module(f"{emit.PACKAGE}.{emit.module_path(document).replace('/', '.')}")
        (symbol,) = module.__all__
        tree = ast.parse((TREE / f"{emit.module_path(document)}.py").read_text())
        declared = [n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == symbol]
        assert len(declared) == 1, document
        assert {b.id for b in declared[0].bases if isinstance(b, ast.Name)} <= {
            "StrEnum",
            "IntEnum",
        }, document
        assigned = {
            t.id
            for n in tree.body
            if isinstance(n, ast.Assign)
            for t in n.targets
            if isinstance(t, ast.Name)
        }
        assert symbol not in assigned, document

        cls = getattr(module, symbol)
        assert issubclass(cls, pyenum.Enum), document
        assert [m.value for m in cls] == doc["enum"], document


def test_a_member_name_is_upper_cased_and_that_is_why_the_module_parses() -> None:
    """The correctness requirement, over the whole emitted population.

    ``pass`` and ``global`` are live enum VALUES in this bundle, so a lower-cased
    member emits ``pass = "pass"`` -- a module that does not parse.  Asserted
    three ways, and the third is the one that makes it a requirement rather than
    a convention:

    * every member name of every emitted enum class is upper-case;
    * the two keyword values are present, so the population is not vacuous;
    * the lower-cased spelling of each of them is NOT a valid class body, proved
      by compiling it.
    """
    classes = emitted_enum_classes()
    assert classes, "no enum class was graded"
    names: set[tuple[str, str]] = set()
    keywords_seen: set[str] = set()
    for document, _, cls in classes:
        for name, value in _members(cls):
            assert name == name.upper(), (document, cls.name, name)
            assert name == lower_enum.member_name(value), (document, cls.name, name, value)
            names.add((cls.name, name))
            if isinstance(value, str) and value in ("pass", "global"):
                keywords_seen.add(value)
    # The member names, as the non-empty set of (class, member) pairs the loop graded.
    # Every member is asserted upper-case and round-tripped through ``member_name``
    # above, so what this denominator has to say is that members were reached -- the
    # count moved at six rows (2692, 2892, 2917, 2993, 2979, 2985, and a 2977 inside
    # one of them), every move a population change rather than a defect.
    claimed("enum members graded", names)
    assert keywords_seen == {"pass", "global"}, keywords_seen

    for word in sorted(keywords_seen):
        with pytest.raises(SyntaxError):
            compile(f"class X:\n    {word} = {word!r}\n", "<probe>", "exec")
        compile(f"class X:\n    {word.upper()} = {word!r}\n", "<probe>", "exec")

    # And the whole of the keyword question: upper-casing settles it, so a
    # `keyword.iskeyword` branch beside the rule would be unreachable.
    import keyword as kw

    assert not any(k.upper() == k for k in kw.kwlist)
    # ... as would a guard against `Enum`'s own reserved names.
    assert all(n.islower() or n.startswith("_") for n in ("name", "value", "mro", "_name_"))


def test_the_injectivity_check_binds_to_the_function_that_actually_runs() -> None:
    """The compiler names NOTHING here, asserted rather than assumed.

    If the compiler named members, an injectivity check over our own function
    would be vacuous while the compiler silently aliased two values onto one
    member.  It does not: ``Enum.jinja2`` renders ``{{ field.name }}``, so the
    name we hand it is the name in the output.  Proved by handing it a name no
    naming function would produce and finding that exact text in the rendering.
    """
    members = (
        ir.Member(name="zZ_not_a_name_any_rule_would_pick", value="a"),
        ir.Member(name="SECOND", value="b"),
    )
    text = render.enum(
        ir.EnumDecl(name="Probe", kind="string", members=members)
    ).text
    assigned = [
        t.id
        for cls in ast.parse(text).body
        if isinstance(cls, ast.ClassDef)
        for s in cls.body
        if isinstance(s, ast.Assign)
        for t in s.targets
        if isinstance(t, ast.Name)
    ]
    assert assigned == [m.name for m in members], (assigned, text)

    # So the check is over `member_name`, and it is injective over the bundle at
    # every node the walk reaches -- which is the claim, with its denominator.
    nodes: set[tuple[str, str]] = set()
    for document in sorted({g.ref.document for g in graded()}):
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document)):
            values = node.get("enum")
            if not isinstance(values, list) or not values:
                continue
            spelled = [lower_enum.member_name(v) for v in values]
            if len(set(spelled)) == len(spelled):
                nodes.add((document, pointer))
            else:  # the one colliding node's document refuses before this is read
                assert document not in emit.emit(BUNDLE, population()).emitted, (document, pointer)
    # The enum NODES the walk reaches, as a non-empty set.  It is deliberately NOT
    # derived from the enum CLASS count above -- a node under a position that reuses an
    # already-declared class is reached without adding one, and the two figures were
    # equal at 277 and again at 333 by coincidence of the populations.  Neither is
    # asserted now: both moved at every row that grew the population (501, 541, 545,
    # 568, 574), and the obligation is the per-node injectivity asserted in the loop.
    claimed("enum nodes whose member names are injective", nodes)


def test_enum_descriptions_are_carried_into_the_member_docstrings() -> None:
    """137 nodes carry ``enumDescriptions`` and a previous attempt dropped all of
    them, for the same reason a hand-rolled renderer dropped 142 property
    descriptions: nothing compares an annotation that changes no accepted set.

    The compiler's own enum printer has the slot, so this asserts that every
    entry of every node the walk REACHES is in the emitted text -- counted, so it
    cannot pass by looking at nothing.
    """
    nodes: set[tuple[str, str]] = set()
    entries: set[tuple[str, str, str]] = set()
    multiline: set[tuple[str, str, str]] = set()
    for document in sorted({g.ref.document for g in graded()}):
        tree = ast.parse((TREE / f"{emit.module_path(document)}.py").read_text())
        rendered = {
            frozenset(n for n, _ in _members(cls)): _docstrings(cls)
            for cls in ast.walk(tree)
            if isinstance(cls, ast.ClassDef)
            if {b.id for b in cls.bases if isinstance(b, ast.Name)} & {"StrEnum", "IntEnum"}
        }
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document)):
            described = node.get("enumDescriptions")
            if "enum" not in node or not isinstance(described, dict):
                continue
            want = {lower_enum.member_name(v): described.get(str(v)) for v in node["enum"]}
            got = rendered.get(frozenset(want))
            if got is None:
                continue  # a node under a composition the walk does not descend into
            nodes.add((document, pointer))
            for member, text in sorted(want.items()):
                if not isinstance(text, str) or not text:
                    continue
                entries.add((document, pointer, member))
                # Verbatim where the description is one line, and compared by its
                # WORDS where it is not: the compiler indents a multi-line
                # docstring into the class body, so the literal differs by exactly
                # that indentation.  ``harness._text`` is the normalizer the schema
                # comparison already uses for a description, rather than a second
                # one that could be looser.
                if "\n" in text:
                    multiline.add((document, pointer, member))
                    assert _text(got.get(member)) == _text(text), (document, pointer, member)
                else:
                    assert got.get(member) == text, (document, pointer, member)
    # Three non-empty sets rather than three counts: the per-member assertion in the
    # loop is the obligation, and each of these says one ARM of it was reached -- a node
    # at all, an entry with text, and the multi-line arm whose normalizer is the half a
    # one-line-only population would leave ungraded.
    claimed("nodes carrying enumDescriptions", nodes)
    claimed("described members compared", entries)
    claimed("multi-line descriptions compared", multiline)

    # The whole block is an annotation, so NO check in the harness grades it:
    # `enumDescriptions` is not a fact the comparison compares.  P2 in
    # ``docs/plan/step3-prediction.md`` predicted that before it was probed.
    assert "enumDescriptions" not in compared_facts(Position.ROOT)


def _docstrings(cls: ast.ClassDef) -> dict[str, str]:
    """``member -> docstring`` for one emitted enum class, off the AST.

    The parsed CONSTANT and not the source text, so what is compared is the string
    the module defines rather than the compiler's escaping of it -- a description
    carrying a quote or a backslash is escaped in the source and would never match
    the document verbatim there.
    """
    out: dict[str, str] = {}
    for assign, after in zip(cls.body, cls.body[1:], strict=False):
        if not (isinstance(assign, ast.Assign) and isinstance(assign.targets[0], ast.Name)):
            continue
        if isinstance(after, ast.Expr) and isinstance(after.value, ast.Constant):
            if isinstance(after.value.value, str):
                out[assign.targets[0].id] = after.value.value
    return out


def test_a_reference_to_a_root_enum_binds_the_class_and_not_a_copy() -> None:
    """The defect inventory's enum widening, closed by construction.

    A referencing property's annotation NAMES the imported enumeration -- so
    there is no enum case at the reference site, and nothing re-spells the member
    list.  Both halves: the AST names the symbol, and the imported annotation IS
    that class.
    """
    known = set(bundle.portable(BUNDLE))
    roots = set(root_enums())

    def exported_class(document: str) -> Any:
        """The one symbol a root enum's own module exports."""
        module = importlib.import_module(
            f"{emit.PACKAGE}.{emit.module_path(document).replace('/', '.')}"
        )
        (symbol,) = module.__all__
        return getattr(module, symbol)

    def names_spelled(module_name: str) -> set[str]:
        """Every ``Name`` the AST of one emitted module spells."""
        relative = module_name[len(emit.PACKAGE) + 1 :].replace(".", "/")
        tree = ast.parse((TREE / f"{relative}.py").read_text())
        return {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}

    sites: set[tuple[str, str]] = set()
    inherited: set[tuple[str, str]] = set()
    documents: set[str] = set()
    for g in graded():
        if g.ref.pointer != "#" or not hasattr(g.model, "model_fields"):
            continue
        raw = bundle.read(BUNDLE, g.ref.document)
        for key, sub in sorted((raw.get("properties") or {}).items()):
            if not isinstance(sub, dict) or "$ref" not in sub:
                continue
            target = bundle.document_for(sub["$ref"], known)
            if target not in roots:
                continue
            name = compiler.field_name(key)
            field = g.model.model_fields[name]
            bound = [
                a for a in getattr(field.annotation, "__args__", (field.annotation,))
                if isinstance(a, type) and issubclass(a, pyenum.Enum)
            ]
            assert len(bound) == 1, (g.ref.document, key, field.annotation)
            # "and not a copy", asserted by IDENTITY rather than by a name: the
            # annotation is the very class object the TARGET document's module
            # exports, so a re-spelled enumeration with the same members and the
            # same name fails here.  This is the half that closes the widening.
            assert bound[0] is exported_class(target), (g.ref.document, key, bound[0])
            # ... and the AST half, read off the module that DECLARES the field.
            # Not always this document's own module: step 4's row composes a root
            # over its ``$ref`` bases, so an inherited field is spelled in the
            # BASE's module -- ``core/tasks-get-response.json`` takes ``status``
            # from ``ProtocolEnvelope``.  Reading the document's own module instead
            # reported 2 sites as failures at 0130e5fc9 when both were faithful.
            owner = next(
                k for k in g.model.__mro__ if name in getattr(k, "__annotations__", {})
            )
            if owner is not g.model:
                inherited.add((g.ref.document, key))
            assert bound[0].__name__ in names_spelled(owner.__module__), (
                g.ref.document,
                key,
                owner.__module__,
            )
            sites.add((g.ref.document, key))
            documents.add(g.ref.document)
    # ``inherited`` is pinned so the branch above is not graded by an empty set:
    # if the composition row stopped inheriting, the AST half would silently go
    # back to reading only each document's own module.
    # (124, 76, 2) -> (128, 78, 0) on fe0e185f9. `sites` and `documents` moved for
    # population growth. `inherited` FELL TO ZERO, and that is a design change rather
    # than drift: salesagent-j3k2l.36 made a composing subclass RE-USE its base's
    # decided field, so the two sites that were inherited through ProtocolEnvelope --
    # core/tasks-get-response.json and protocol/get-task-status-response.json, both on
    # `status` -- now declare the field in their own module.
    #
    # SO THE `inherited` ARM NOW GRADES A POPULATION OF 0, and it is pinned at 0
    # rather than dropped: the shape it covers -- a root enum bound through a base's
    # field -- is still reachable if a later row inherits again, and a pin at 0 says
    # loudly that nothing exercises it today. This is the same treatment
    # salesagent-j3k2l.28 gave the fifth fold's `enum` arm when its population went to
    # zero: label the dormancy, do not delete a legitimate shape or let a dead arm read
    # as live.
    # The two live denominators are non-empty sets and the dormant arm is EMPTY, which
    # is the half that matters: a new site binding a COPY rather than the class shows up
    # in the per-site assertion above, while the site and document counts moved at every
    # row that referenced one more root enum -- (124, 76, 2), (128, 78, 0), (131, 81, 0),
    # (134, 83, 0) -- and each move was another row's work.
    assert inherited == set(), sorted(inherited)
    claimed("reference sites binding a root enum class", sites)
    claimed("documents holding such a site", documents)


# --------------------------------------------------------------------------- #
# the two halves of strict_validate, on an enumeration
# --------------------------------------------------------------------------- #
def test_a_root_enum_binds_its_schema_and_strict_validate_at_module_scope() -> None:
    """Where the reference lives, and why it is not in the class body.

    ``Enum.jinja2`` has no ``class_body_lines`` slot, so the compiler cannot put
    an ``__adcp_schema__`` line inside an enumeration at all, and D9 forbids
    writing one in afterwards.  So a root enumeration binds the same two halves
    D2's root-scalar row binds, at module scope, through the same ``_refuse``.

    Asserted on behaviour and not on spelling: the document decides acceptance
    (a non-member is refused with the DOCUMENT's keyword, ``enum``), and the
    constructor half returns the member.
    """
    document = next(
        d for d in root_enums() if d in emit.emit(BUNDLE, population()).emitted
    )
    module = importlib.import_module(
        f"{emit.PACKAGE}.{emit.module_path(document).replace('/', '.')}"
    )
    (symbol,) = module.__all__
    cls = getattr(module, symbol)
    assert module.__adcp_schema__ == SchemaRef(document, "#")
    assert not hasattr(cls, "strict_validate")
    assert "class_body_lines" not in (render.StrEnum.TEMPLATE_FILE_PATH or "")

    member = schema_at(module.__adcp_schema__)["enum"][0]
    assert module.strict_validate(member) is cls(member)
    with pytest.raises(ValidationError) as caught:
        module.strict_validate("__not_a_member__")
    assert [e["type"] for e in caught.value.errors()] == ["enum"]


def test_the_schema_comparison_is_what_grades_this_row() -> None:
    """P3 as a test, and it CORRECTS a finding carried forward from an earlier
    attempt at this step.

    That attempt measured the enum widening -- an enum node lowered to the scalar
    its ``type`` names -- as leaving ``check_pair`` green in both directions, and
    concluded that nothing in the harness can grade the row.  Two of the three
    checks are still blind, for the reason they are blind to everything:
    ``strict_validate``'s schema half refuses a non-member whatever the
    annotation says.  The SCHEMA COMPARISON is not, because ``enum`` is in the
    compared set: the widened model states no ``enum`` where the document states
    one.

    Graded on the document of a real root enum, with the faithful model beside the
    widened one so the two reports are read against each other rather than in
    isolation.
    """
    document = next(d for d in root_enums() if d in emit.emit(BUNDLE, population()).emitted)
    doc = schema_at(SchemaRef(document, "#"))
    module = importlib.import_module(
        f"{emit.PACKAGE}.{emit.module_path(document).replace('/', '.')}"
    )
    (symbol,) = module.__all__

    assert "enum" in compared_facts(Position.ROOT)
    faithful = compare_schema(doc, getattr(module, symbol))
    widened = compare_schema(doc, str)  # the scalar the document's `type` names

    assert faithful.outcome == "pass", (faithful.missing, faithful.differs, faithful.added)
    assert widened.outcome == "model_drops_a_fact", widened
    assert ["/enum", "/description"] == [m.split(":")[0] for m in widened.missing], widened.missing
    # ... and the other two checks really are blind to it: the widened annotation
    # accepts and refuses exactly what the document does, because the schema half
    # answers first.
    from codegen.harness import check_accepts, check_pair, Pair

    adapter = TypeAdapter(str)

    def wide_accept(payload: Any) -> Any:
        from adcp.types._base import _refuse  # noqa: PLC0415,SLF001

        _refuse(doc, payload, "Wide")
        return adapter.validate_python(payload)

    assert check_accepts(doc, wide_accept).outcome == "pass"
    wide = check_pair(Pair(name="wide", schema=doc, model=str, accept=wide_accept))
    assert wide.accepts.outcome == "pass"
    assert wide.liveness.outcome == "pass", (wide.liveness.how, wide.liveness.detail)
    assert wide.graded_instances > 0, wide.graded_instances
    assert wide.outcome.startswith("comparison:"), wide.outcome


def test_the_type_an_enums_members_force_is_excused_and_a_narrowing_is_not() -> None:
    """The one instrument clause that SURVIVES row .3, and each case of it falsified.

    This used to be ``_narrows_nothing``'s enum row, which excused a model-only
    ``type``, ``description`` and ``default`` at an enum node.  Its reason was the
    delegated resolver: ``hypothesis_jsonschema``'s ``canonicalish`` reduces an enum
    node to its ``enum`` ALONE, so a faithful enumeration stated three facts its own
    resolved document no longer did.  ``bundle.record`` copies the node, so the
    ``description`` and the ``default`` are now COMPARED against the document's own and
    the row's two annotation clauses are deleted (architecture §9).

    **The ``type`` clause has a second source the record does not touch, so it stays
    and it MOVED to the function that asks its question.**  164 nodes of the raw 3.2
    bundle, in 79 documents, state an ``enum`` and no ``type`` -- the document's own
    text, not a view of it -- and a pydantic ``StrEnum`` renders
    ``{"enum": [...], "type": "string"}``.  So the answer is "the type the node's own
    content forces", which is ``_entails_type``'s question, beside the ``const``
    derivation it already carried.

    The canonicalization is still measured here rather than cited, because it is what
    the deletion rests on: the resolver really did drop the three, and the record
    really does not.
    """
    from hypothesis_jsonschema._canonicalise import canonicalish

    stated = {"type": "string", "enum": ["a", "b"], "description": "d", "default": "a"}
    assert canonicalish(stated) == {"enum": ["a", "b"]}
    # ... and the same node WITHOUT the enum keeps all four, so this is the
    # enum collapse and not a general drop.
    kept = {"type": "string", "minLength": 1, "description": "d", "default": "x"}
    assert canonicalish(kept) == kept
    # The record performs no such reduction: the node is copied through a reference
    # with every key it states, which is the whole of why the two clauses are gone.
    assert bundle.record(BUNDLE, "core/catalog-selection.json")["properties"]["type"].keys() >= {
        "description",
        "enum",
        "type",
    }

    doc = {"enum": ["a", "b"]}

    class Faithful(pyenum.StrEnum):
        """d"""

        A = "a"
        B = "b"

    # The model states the TYPE its members force, which is excused, and a
    # ``description`` the document no longer fails to state -- so it is now reported.
    excused = compare_schema(doc, Faithful)
    assert excused.model_facts == 2, excused.model_facts  # type and description
    assert [a.split(":")[0] for a in excused.added] == ["/description"], excused.added

    # Each case, falsified on the RULE.  End to end is the wrong level for these: every
    # model that states a wrong type without also stating the enum is already caught as
    # ``model_drops_a_fact``, so a report read off one says nothing about whether this
    # clause excused anything.
    assert _entails_type({"enum": ["a", "b"]}, "string") is True
    assert _entails_type({"enum": ["a", "b"]}, "integer") is False
    assert _entails_type({"enum": ["a", 1]}, "string") is False  # no one implied type
    # bool is not int here, because ``_JSON_TYPE`` is keyed on the EXACT type: a model
    # claiming ``integer`` over a boolean enum is a narrowing and stays reported.
    assert _entails_type({"enum": [True, False]}, "integer") is False
    assert _entails_type({"enum": [True, False]}, "boolean") is True
    assert _entails_type({"enum": []}, "string") is False  # not an enum to imply from
    # Anything else beside an enum is reported, so the clause excuses ONE keyword and
    # not "whatever sits beside an enum".
    assert _narrows_nothing("minLength", 5, doc) is False
    assert _narrows_nothing("description", "anything", doc) is False
    assert _narrows_nothing("default", "a", doc) is False
    # ``default: None`` stays excused, and by the OTHER clause: it is D4's spelling of
    # an absent key and has nothing to do with the enum.
    assert _narrows_nothing("default", None, doc) is True
    assert _narrows_nothing("default", None, doc, required=True) is False

    # And end to end, a constraint at an enum node is still in ``added``.
    narrower = compare_schema(doc, Annotated[str, Field(min_length=5)])
    assert "/minLength" in [a.split(": ")[0] for a in narrower.added], narrower.added


# --------------------------------------------------------------------------- #
# the four refusals, and the base this bundle does not reach
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("values", "because"),
    [
        (["clickTag", "clickTAG"], "both spell the member"),
        (["a", 1], "mixed type"),
        ([], "enumerates nothing"),
        (["a", "a"], "appears twice"),
        ([True, False], "bool is an int subclass"),
    ],
    ids=["one-member-name", "mixed-types", "empty", "duplicated-value", "boolean"],
)
def test_a_node_this_row_cannot_represent_refuses_by_name(values: list, because: str) -> None:
    """The four representability refusals, plus the excluded base.

    **None of them is reachable from this bundle**, and that is stated rather than
    hidden: the one colliding node lives in
    ``formats/canonical/html5.json``, whose root composes and therefore refuses on
    ``allOf`` before any enum is read (measured cascade cost: 0), and there are 0
    mixed, 0 empty, 0 duplicated and 0 boolean enum nodes over all 1,069.  So they
    are graded on nodes written here, which is the right level -- they are
    properties of the lowering, not of the bundle.
    """
    caught = refusal_from(lower_enum.decide(_probe({"enum": values}, "/properties/x"), "Probe"))
    assert caught.keyword == "enum"
    assert caught.pointer == "/properties/x"
    assert because in caught.detail, caught.detail


def test_the_colliding_node_is_in_the_bundle_and_its_document_refuses_earlier() -> None:
    """Both halves of "unreachable", so the claim is measured and not assumed."""
    document = "formats/canonical/html5.json"
    node = bundle.read(BUNDLE, document)["properties"]["clicktag_macro"]
    assert node["enum"] == ["clickTag", "clickTAG"]
    assert len({lower_enum.member_name(v) for v in node["enum"]}) == 1
    out = emit.emit(BUNDLE, population())
    # THE KEYWORD IS NO LONGER PINNED HERE, which is this file's own precedent --
    # 9cd0aeaa9, "stop pinning the keyword a negative fixture refuses on".  This
    # refusal has read ``allOf`` at ``/allOf/0``, then ``$ref`` at ``/allOf/0``,
    # then ``oneOf`` at ``/allOf/1``, moving each time a later row claimed more of
    # this root; and the comment beside it said every time that the claim "holds
    # on either keyword".  A pin on a keyword the test does not assert is just
    # somewhere for a re-measurement to keep landing.
    #
    # So the claim is asserted directly, over a population derived from the
    # document rather than named: the collision is still there, the document does
    # not emit, so no class was built from the colliding node -- and the refusal
    # fires OUTSIDE that node, so the walk never read it.
    walked = claimed(
        "enum nodes of this document",
        [
            p
            for p, n in bundle.nodes(bundle.read(BUNDLE, document))
            if isinstance(n.get("enum"), list) and n["enum"]
        ],
    )
    colliding = [
        p
        for p, n in bundle.nodes(bundle.read(BUNDLE, document))
        if isinstance(n.get("enum"), list)
        and n["enum"]
        and len({lower_enum.member_name(v) for v in n["enum"]}) != len(n["enum"])
    ]
    assert colliding == ["/properties/clicktag_macro"], colliding
    assert set(colliding) <= set(walked), colliding
    assert document not in out.emitted
    assert not any(
        out.refusals[document]["pointer"].startswith(p) for p in colliding
    ), out.refusals[document]


def test_an_integer_enum_becomes_an_int_enum_at_the_three_nodes_that_carry_one() -> None:
    """The second base, with its reach stated -- and the reach is no longer 0.

    **This test's premise inverted between measurements and the assertions moved
    with it, rather than the numbers being re-pointed.**  It read: 3 enum nodes in
    the bundle have integer members, all 3 sit in documents that refuse on
    ``const`` before the enum is read, so 0 emitted documents carry an IntEnum and
    the base is graded by nothing but a node written here.  At 16052ffb0 both
    asset documents emit, so all 3 of the bundle's integer enum nodes are REACHED
    and the committed tree carries the base.  Keeping ``reached == []`` would have
    been asserting the old tree; re-pointing it to a count alone would have thrown
    away the grader the inversion handed us.

    So both halves run: the tree's own IntEnum classes at the 3 nodes, selected by
    their MEMBER VALUES rather than by a class name (the naming rule is graded by
    :func:`test_a_member_name_that_cannot_begin_an_identifier_takes_the_prefix`,
    and selecting by it here would make this test pass or fail on that rule), and
    then the lowering and the compiler on a node written here -- which still grades
    the ``IntEnum`` header and the integer ``json_schema`` that no bundle node
    isolates.
    """

    def integer_enum_nodes(documents: list[str]) -> list[tuple[str, str]]:
        return [
            (d, p)
            for d in sorted(documents)
            for p, n in bundle.nodes(bundle.read(BUNDLE, d))
            if isinstance(n.get("enum"), list)
            and any(isinstance(v, int) and not isinstance(v, bool) for v in n["enum"])
        ]

    in_bundle = integer_enum_nodes(list(bundle.portable(BUNDLE)))
    claimed("integer enum nodes in the bundle", in_bundle)
    reached = integer_enum_nodes(sorted(emit.emit(BUNDLE, population()).emitted))
    # Every one of them, which is what makes the tree half below non-vacuous.
    assert reached == in_bundle, (reached, in_bundle)
    assert sorted({d for d, _ in reached}) == [
        "core/assets/audio-asset.json",
        "core/assets/video-asset.json",
    ], reached

    for document, pointer in reached:
        node = next(n for p, n in bundle.nodes(bundle.read(BUNDLE, document)) if p == pointer)
        module = importlib.import_module(
            f"{emit.PACKAGE}.{emit.module_path(document).replace('/', '.')}"
        )
        tree = ast.parse((TREE / f"{emit.module_path(document)}.py").read_text())
        at_this_node = [
            cls
            for cls in ast.walk(tree)
            if isinstance(cls, ast.ClassDef)
            if {b.id for b in cls.bases if isinstance(b, ast.Name)} == {"IntEnum"}
            if [v for _, v in _members(cls)] == node["enum"]
        ]
        assert len(at_this_node) == 1, (document, pointer, [c.name for c in at_this_node])
        cls = getattr(module, at_this_node[0].name)
        assert issubclass(cls, pyenum.IntEnum), (document, pointer)
        assert [m.value for m in cls] == node["enum"], (document, pointer)

    decided = lower_enum.decide(_probe({"type": "integer", "enum": [16, 24, 32]}), "BitDepth")
    assert decided.kind == "integer"
    assert [m.name for m in decided.members] == ["V_16", "V_24", "V_32"]
    text = render.enum(decided).text
    assert text.startswith("class BitDepth(IntEnum):"), text
    scope: dict[str, Any] = {"IntEnum": pyenum.IntEnum}
    exec(compile(text, "<probe>", "exec"), scope)  # noqa: S102 -- the compiler's own output
    assert [m.value for m in scope["BitDepth"]] == [16, 24, 32]
    assert TypeAdapter(scope["BitDepth"]).json_schema()["type"] == "integer"


def test_the_base_comes_from_the_members_which_is_what_admits_a_typeless_node() -> None:
    """164 of the bundle's 1,069 enum nodes declare no ``type`` at all.

    Reading the base off the members is what lowers them -- and it is a faithful
    reading rather than a fallback, because ``type`` and the members agree at all
    1,069 nodes, measured here, and the schema comparison grades ``type`` either
    way.
    """
    counted = {"typed": 0, "typeless": 0, "disagreeing": 0}
    for document in bundle.portable(BUNDLE):
        for _, node in bundle.nodes(bundle.read(BUNDLE, document)):
            values = node.get("enum")
            if not isinstance(values, list) or not values:
                continue
            kinds = {type(v).__name__ for v in values}
            implied = lower_enum.BASES.get(next(iter(kinds))) if len(kinds) == 1 else None
            declared = node.get("type")
            if declared is None:
                counted["typeless"] += 1
            else:
                counted["typed"] += 1
                if implied is not None and implied != declared:
                    counted["disagreeing"] += 1
    # The two live parts non-empty and the third EMPTY, which is the claim: an enum's
    # implied base never disagrees with a declared type.  The two live counts were a
    # reading of one bundle version and said nothing the non-emptiness does not.
    assert counted["disagreeing"] == 0, counted
    assert counted["typed"] and counted["typeless"], counted
    assert lower_enum.decide(_probe({"enum": ["a"]}), "P").kind == "string"
    assert "boolean" not in lower_enum.BASES.values()


def test_a_member_name_that_cannot_begin_an_identifier_takes_the_prefix() -> None:
    """The prefix, over the values that need it, derived from the bundle.

    17 string values and 6 integer values cannot begin an identifier.  Asserted
    on the function and then on what it produces being a usable member name,
    rather than on a list of expected spellings.
    """
    needs = sorted(
        {
            json.dumps(v)
            for d in bundle.portable(BUNDLE)
            for _, n in bundle.nodes(bundle.read(BUNDLE, d))
            if isinstance(n.get("enum"), list)
            for v in n["enum"]
            if lower_enum.member_name(v).startswith(lower_enum.PREFIX)
        }
    )
    # Non-empty: every member of the set is asserted to be a valid upper-case
    # identifier below, so the denominator's job is to say the prefix has values to be
    # derived over.
    claimed("bundle enum values needing the prefix", needs)
    for raw in needs:
        value = json.loads(raw)
        name = lower_enum.member_name(value)
        assert name.isidentifier(), (value, name)
        assert name == name.upper(), (value, name)
    assert lower_enum.member_name("1.0") == "V_1_0"
    assert lower_enum.member_name(16) == "V_16"
    assert lower_enum.member_name("broad") == "BROAD"
    assert lower_enum.member_name("media-buy/create") == "MEDIA_BUY_CREATE"


def test_enum_metadata_is_an_annotation_of_the_bundle_and_the_cost_is_named() -> None:
    """The keyword decision, where it is now taken, with its measured price.

    ``enumMetadata`` states nothing about an instance -- ``enum`` has closed the
    value set -- and an enumeration has no slot for a per-value block, so it is
    ignored and the documents holding one emit.

    **The decision is no longer this row's**, and that is ``salesagent-j3k2l.23``:
    the reason above is a fact about the KEYWORD and not about an enum root, so §6's
    own row in ``codegen.keywords`` takes it once for every position and
    ``lower.enum.CLAIMS`` no longer names it. Asserted in BOTH directions here,
    because one name admitted in two places is two places for one decision to
    drift -- and the drift was observable: the 4th document carrying one
    (``core/media-buy-available-action-id.json``) is a union root, which this
    row's set never reached.

    Refusing it instead is one name out of the admitted set and costs exactly the
    3 enum roots with no cascade, which is measured here so the alternative is
    priced rather than argued.
    """
    carriers = sorted(
        d
        for d in bundle.portable(BUNDLE)
        for _, n in bundle.nodes(bundle.read(BUNDLE, d))
        if "enumMetadata" in n
    )
    assert carriers == [
        # Not an enum root, and so the document this row's own set could not reach.
        "core/media-buy-available-action-id.json",
        "enums/error-code.json",
        "enums/media-buy-valid-action.json",
        "enums/request-signing-error-code.json",
    ], carriers
    assert keywords.cell("enumMetadata", Position.ROOT).effect is keywords.Effect.NOTHING
    assert keywords.grid_of("enumMetadata") == keywords.ADMITTED
    assert "enumMetadata" not in lower_enum.CLAIMS
    out = emit.emit(BUNDLE, population())
    # **THE PRICED SET, NOT ITS SIZE.**  The comment below prices unannotating the
    # keyword, and a count of three went stale as an ARGUMENT while staying green as an
    # assertion: ``core/media-buy-available-action-id.json`` carries ``enumMetadata``,
    # is not an enum root and did not emit, and once it emitted the price grew without
    # this number moving.  So the set is named, and ``direct`` below adds that document
    # to it explicitly.
    enum_rooted = [d for d in carriers if populations.is_enum_root(bundle.read(BUNDLE, d))]
    assert claimed("enum-rooted carriers of enumMetadata", enum_rooted) == {
        "enums/error-code.json",
        "enums/media-buy-valid-action.json",
        "enums/request-signing-error-code.json",
    }, sorted(enum_rooted)
    assert all(d in out.emitted for d in enum_rooted)

    # The price, priced by REMOVING THE ROW rather than by patching a set: the
    # alternative is "§6 does not admit this keyword", and with no row the screen
    # refuses the document by name at every position -- which is exactly what §7's
    # last rule says happens to a keyword none of the three sections names.  One table
    # and one reading of it, so there is no second set left to patch.
    without = {k: v for k, v in keywords.TABLE.items() if k != "enumMetadata"}
    original = keywords.TABLE
    try:
        keywords.TABLE = without
        refusing = emit.emit(BUNDLE, population())
    finally:
        keywords.TABLE = original
    # **THE PRICE IS FOUR DOCUMENTS NOW, NOT THREE, AND THAT IS
    # ``salesagent-j3k2l.21``.**  The docstring above priced it at "exactly the 3 enum
    # roots with no cascade", and the carriers list says why that was true:
    # ``core/media-buy-available-action-id.json`` carries ``enumMetadata`` and is NOT an
    # enum root, so this row's own set could not reach it -- and it did not emit, so
    # unannotating the keyword cost nothing there. It emits now (a union root of scalars
    # is an alias), so refusing ``enumMetadata`` would refuse it too. The price is read
    # off the measurement rather than held at the figure the comment argued.
    # **THE PRICE IS SEVEN DOCUMENTS, NOT THREE, AND IT CASCADES.** The docstring
    # above priced it at "exactly the 3 enum roots with no cascade", and that was true
    # for a reason it does not state: the fourth carrier,
    # ``core/media-buy-available-action-id.json``, is NOT an enum root -- so this row's
    # own set could not reach it -- and it did not EMIT, so unannotating the keyword
    # cost nothing there. ``salesagent-j3k2l.21`` makes it emit (a union root of scalars
    # is an alias), so the keyword has a cost at that document, and three more documents
    # ``$ref`` it and go with it. "With no cascade" is the half that stopped being true.
    #
    # **Asserted as the SET and not as its size**, which is the general lesson rather
    # than a style choice: ``assert len(enum_rooted) == 3`` passed throughout, because
    # there really are still three enum roots. What went stale was the sentence using
    # that 3 to argue the alternative is cheap -- a comment that prices an alternative
    # is a measurement and goes stale like one, while the assertion beside it stays
    # green. A set reddens when a member arrives; a count of three does not.
    #
    # Split by HOW each one refuses, because the two halves are different facts: four
    # carry the keyword at their own root, and three carry a ``$ref`` to one that does.
    direct = sorted([*enum_rooted, "core/media-buy-available-action-id.json"])
    cascaded = [
        "core/media-buy-available-action.json",
        "core/product-allowed-action.json",
        "error-details/action-not-allowed.json",
    ]
    priced = sorted([*direct, *cascaded])
    assert sorted(set(refusing.refusals) - set(out.refusals)) == priced, priced
    # The price is the PRICED SET and the arithmetic is derived from it: every document
    # in it stops emitting, and nothing else does.
    assert sorted(set(out.emitted) - set(refusing.emitted)) == priced, priced
    assert len(refusing.emitted) == len(out.emitted) - len(priced), len(refusing.emitted)
    for document in direct:
        assert refusing.refusals[document]["keyword"] == "enumMetadata", document
        assert refusing.refusals[document]["pointer"] == "/", document
    for document in cascaded:
        row = refusing.refusals[document]
        assert row["keyword"] == "$ref", (document, row)
        assert row["kind"] == refusal_module.Kind.CHAINED, (document, row)


# ``test_identical_enum_nodes_under_one_document_are_unreached_by_this_step`` stood
# here, and salesagent-j3k2l.38 CLOSED it rather than re-pointing it.  It was D3's
# content dedup as a ceiling: 36 enum repeats over 21 documents, 0 of them REACHED, and
# "the fix belongs to the step whose population reaches one".  That step arrived, the
# reached count became 1, and the issue says explicitly that re-pointing 0 to 1 would
# convert a defect into a baseline.
#
# It is gone because the check that replaced it SUBSUMES it in both directions.  The
# ceiling was enum-only and its reach test was a pointer-spelling proxy -- all hops are
# ``properties`` pairs -- and the defect was never enum-only: the walk declared two
# classes for one node at 7 content groups over 6 documents, and 5 of the 7 are OBJECT
# classes.  The proxy also undercounted its own population: of the 2 enum groups,
# ``formats/canonical/image_carousel.json``'s two pointers reach the node through an
# ``items`` hop, which the proxy rejected while the walk descends it.
# ``tests/test_emit.py::test_identical_content_is_one_class_and_different_content_is_
# never_one`` grades every node of every document the whole bundle emits, through the
# very function the collapse is keyed on, and asserts its three denominators -- so a run
# that collapses nothing fails there rather than passing over an empty loop.
#
# The ceiling's own census is not lost, it is explained: 36 bundle-side enum repeats and
# 8 walk-side collapses are two different populations, and the difference is documents
# the emitter refuses and positions no row descends.  The new check counts what the walk
# DECLARED, which is the only population a dedup can be graded over.


def test_the_emitted_tree_still_declares_every_module_it_imports() -> None:
    """The walk's closure, over the enum imports this step added.

    An enumeration reaches a referencing module as an IMPORT, so a root enum that
    refused while a referrer emitted would be an ImportError at the gate.  The
    whole tree is imported by ``tests/test_emit.py``; this reads the other
    direction off the AST, so a module importing a symbol from a sibling that does
    not export it fails here by name.

    The ORDER is graded too, because ``__all__`` holds more than one name since
    salesagent-j3k2l.31 and ``tests/test_emit.py`` reads the root off the head of it.
    The expected head is derived -- ``emit.class_name`` over the document's own title,
    which is the function ``lower_document`` makes the symbol with -- so this cannot
    pass by restating what the tree happens to hold.
    """
    exported: dict[str, set[str]] = {}
    for document in sorted({g.ref.document for g in graded()}):
        module = emit.module_path(document)
        tree = ast.parse((TREE / f"{module}.py").read_text())
        listed = [
            e.value
            for n in tree.body
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)
            if isinstance(n.value, (ast.List, ast.Tuple))
            for e in n.value.elts
            if isinstance(e, ast.Constant)
        ]
        root = compiler.class_name(bundle.read(BUNDLE, document)["title"])
        assert listed[:1] == [root], (module, listed[:1], root)
        exported[module] = set(listed)
    checked: set[tuple[str, str, str]] = set()
    for document in sorted({g.ref.document for g in graded()}):
        module = emit.module_path(document)
        tree = ast.parse((TREE / f"{module}.py").read_text())
        for n in ast.walk(tree):
            if not isinstance(n, ast.ImportFrom) or not n.level:
                continue
            up = Path(module).parent
            for _ in range(n.level - 1):
                up = up.parent
            target = str(up / (n.module or "").replace(".", "/"))
            assert target in exported, (module, n.module, n.level)
            for alias in n.names:
                assert alias.name in exported[target], (module, target, alias.name)
                checked.add((str(module), target, alias.name))
    # LEFT RED ON PURPOSE at 0130e5fc9, and the assertion above is what found it: the
    # tree held imports of a symbol the target module DECLARED and did not list in its
    # ``__all__`` -- e.g. ``core/reporting_delivery_offering`` importing
    # ``ReportingCanonicalizationContractReportingPrimaryKey`` from
    # ``core/reporting_canonicalization_contract``, whose ``__all__`` was
    # ``["ReportingCanonicalizationContract"]`` alone.  Nothing ImportErrors -- Python
    # does not consult ``__all__`` on import -- so what it found was the EMITTER
    # disagreeing with itself: the binder resolves a fragment reference to
    # ``mod.declared[into]`` while the writer exported the root alone.
    #
    # CLOSED at salesagent-j3k2l.31, on the first of the two readings the issue names:
    # the symbols are exported, because the other reading is a second name for one
    # document node (P2).  The 16 named 8 distinct symbols, 4 of them ``StrEnum``
    # CLASSES accounting for 9 of the imports, and one of those is imported by 6
    # modules -- so copying would be 7 classes for one node, not the 15 "module-level
    # type aliases" the issue describes.  ``emit.exported`` is the fix and carries the
    # reasoning; ``docs/plan/rebuild-plan.md`` section 6 records the decision.
    #
    # AND IT TOOK TWO CLAUSES, which is this assertion's second catch rather than a
    # correction to the first.  salesagent-j3k2l.36 landed a subclass that RE-USES a
    # composed base's decided field, so ``formats/canonical/_base``'s
    # ``CanonicalFormatBaseSlotsItem`` crossed into 7 modules with no ``$ref`` naming
    # it -- the bundle-named clause cannot reach that, and this assertion found it
    # again the same way.  A symbol crosses in exactly those two ways, so
    # ``emit.exported`` is now the union of both and still not every declared symbol.
    #
    # THE DENOMINATOR IS THE SET OF RESOLVED IMPORTS, non-empty, and not a count of
    # them: the count was the alias population over the committed tree and it moved at
    # every row -- 910, 957, 964, 977, 1013, 1039 -- each move a population growing
    # under the rows and none of them a defect.  The assertion is NOT weakened to
    # ``defined in the target module``: that would grade importability, which the
    # whole-tree import in ``tests/test_emit.py`` already grades, and would retire the
    # only check on what a module DECLARES -- the check that has now caught two
    # separate defects.
    claimed("relative imports resolved against the target's __all__", checked)
