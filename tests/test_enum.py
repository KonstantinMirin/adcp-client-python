"""Grade D2's enumeration row: an ``enum`` node becomes a ``StrEnum``/``IntEnum``.

**Why this file exists at all, and what the harness does and does not reach.**
``tests/test_emit.py`` grades every emitted pair through the three checks, and for
an enumeration two of the three are nearly blind: the accepts and invalid-payload checks
run through ``strict_validate``, whose SCHEMA half refuses a non-member whatever
the annotation says, so they grade the document and not the model.  Measured as a
test below (:func:`test_the_schema_comparison_is_what_grades_this_row`), and the
result corrects a finding carried forward from an earlier attempt at this step:
the SCHEMA COMPARISON does grade it now, because ``enum`` is in
``harness.FACTS`` -- a node lowered to the scalar its ``type`` names states no
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
from codegen import bundle, compiler, emit
from codegen.harness import (
    _implied_by_an_enum,
    _narrows_nothing,
    _text,
    compare_schema,
    FACTS,
)
from codegen.lower import enum as lower_enum
from codegen.refusal import Refusal
from tests.test_emit import BUNDLE, graded, population, TREE


def root_enums() -> list[str]:
    """Every document whose ROOT carries an ``enum``, off the bundle."""
    return [d for d in bundle.portable(BUNDLE) if bundle.is_enum_root(bundle.read(BUNDLE, d))]


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
    roots = root_enums()
    assert len(roots) == 214, len(roots)
    assert set(roots) <= set(population()), "a root enum outside the step's population"

    out = emit.emit(BUNDLE, population())
    emitted = [d for d in roots if d in out.emitted]
    refused = {d: out.refusals[d] for d in roots if d in out.refusals}
    assert len(emitted) == 214, len(emitted)
    assert refused == {}, refused
    assert set(emitted) | set(refused) == set(roots)

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
            for _, uri in bundle.references(bundle.read(BUNDLE, d))
            if bundle.document_for(uri, known) == "enums/task-type.json"
        }
    )
    assert len(referrers) == 7, referrers
    in_population = [d for d in referrers if d in population()]
    # 7, not the 6 this read before step 4's population landed: ``composes_at_the_root``
    # names one more of the referrers, and the cascade claim is the same either way.
    assert len(in_population) == 7, in_population
    emitted_referrers = sorted(d for d in in_population if d in out.emitted)
    refused_referrers = sorted(d for d in in_population if d in out.refusals)
    # 6 and 1 at 0130e5fc9; 4 and 3 at 16052ffb0, before step 4's row landed.
    # A partition and not two counts: a referrer in NEITHER half would be a
    # document the emitter neither built nor refused, and the equality below is
    # what reports that rather than letting the two numbers absorb it.
    assert len(emitted_referrers) == 6, emitted_referrers
    assert len(refused_referrers) == 1, refused_referrers
    assert sorted(emitted_referrers + refused_referrers) == sorted(in_population)
    # The claim is that none of them was blocked BY this document, which is read off
    # the refusal's own detail, and that is the only reading that still works: the
    # one referrer still refusing refuses on a ``$ref`` at ``/properties/result``,
    # and its detail is a CHAINED one -- "its target core/async-response-data.json
    # is refused: ..." -- so what blocks it is named two documents away.  A keyword
    # test would have read it as this document's cascade; the detail does not.
    assert [d for d in refused_referrers if "task-type" in out.refusals[d]["detail"]] == []


def test_the_dispatch_table_is_unordered_because_no_document_is_claimed_twice() -> None:
    """§5's rule, and the one word that makes it true.

    A document two rows claim is a build failure rather than a precedence, and
    that is only a workable rule if the rows are actually disjoint.  Asserted in
    both directions over all 1,054 documents: 0 claimed twice as the rows stand,
    and 214 -- every root enum -- the moment the scalar row stops excluding an
    enumeration.  So the exclusion is load-bearing and is measured as such.
    """
    documents = [bundle.read(BUNDLE, d) for d in bundle.portable(BUNDLE)]
    # Every row's selector comes from ``codegen.bundle`` (D13), which is what a
    # count of rows cannot say and what keeps this from going stale as rows land.
    assert [s for s, _ in emit.ROWS if getattr(bundle, s.__name__, None) is not s] == []
    claimed = [sum(1 for selects, _ in emit.ROWS if selects(doc)) for doc in documents]
    assert [n for n in claimed if n > 1] == []
    assert sum(1 for n in claimed if n == 1) == 1047, sum(1 for n in claimed if n == 1)
    assert sum(1 for n in claimed if n == 0) == 7  # the roots no row describes at all

    def scalar_without_the_exclusion(doc: dict) -> bool:
        return isinstance(doc.get("type"), str) and doc["type"] in emit.SCALAR

    overlap = [
        doc for doc in documents if scalar_without_the_exclusion(doc) and bundle.is_enum_root(doc)
    ]
    assert len(overlap) == 214, len(overlap)

    # A row cannot claim a document its step does not count.
    assert [d for d in documents if bundle.is_enum_root(d) and not bundle.carries_an_enum(d)] == []


def test_two_rows_claiming_one_root_is_a_build_failure_and_not_a_refusal() -> None:
    """The rule itself, on a document built to break it.

    No bundle document reaches it (the test above is why), so it is graded on a
    row added for the purpose.  A ``Refusal`` would be the wrong outcome: it would
    land in the refusal report as a document the BUNDLE is responsible for, when
    it is the emitter disagreeing with itself about which row owns a node kind.
    """
    doc = {"title": "Both", "type": "string", "enum": ["a", "b"]}
    rows = (*emit.ROWS, (lambda d: "enum" in d, emit._enum_root))  # noqa: SLF001
    original = emit.ROWS
    try:
        emit.ROWS = rows
        with pytest.raises(emit.AmbiguousRoot) as caught:
            emit.lower_document("both.json", doc)
    finally:
        emit.ROWS = original
    assert "is_enum_root" in str(caught.value)
    # and with the real table the same document emits
    assert emit.lower_document("both.json", doc)[1] == "Both"


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
    # 447 -> 482 on fe0e185f9: every count in this file is over the documents
    # ``population()`` names, so each moved as the emitted population grew.
    # 482 -> 484 at ``salesagent-j3k2l.40``, which emits 5 more of those documents.
    # Re-measured in one pass with the other three counts of this file; the ROOT half
    # (214) did not move, so the 2 are both INLINE and the baseline says so -- this
    # file is 1 failed / 22 passed at ``c9bfb5133`` and these four were the 4 green
    # ones that moved.
    assert len(classes) == 484, len(classes)  # 214 roots, the rest inline
    roots = [d for d in root_enums() if d in {c[0] for c in classes}]
    assert len(roots) == 214, len(roots)

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
    names = 0
    keywords_seen: set[str] = set()
    for document, _, cls in classes:
        for name, value in _members(cls):
            assert name == name.upper(), (document, cls.name, name)
            assert name == lower_enum.member_name(value), (document, cls.name, name, value)
            names += 1
            if isinstance(value, str) and value in ("pass", "global"):
                keywords_seen.add(value)
    # 2692 -> 2892 on fe0e185f9, population growth; 2892 -> 2917 at
    # ``salesagent-j3k2l.40``, the same 5 documents.
    assert names == 2917, names
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
        compiler.Member(name="zZ_not_a_name_any_rule_would_pick", value="a"),
        compiler.Member(name="SECOND", value="b"),
    )
    text = compiler.render_enum(
        compiler.Enumeration(name="Probe", kind="string", members=members)
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
    nodes = 0
    for document in sorted({g.ref.document for g in graded()}):
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document)):
            values = node.get("enum")
            if not isinstance(values, list) or not values:
                continue
            spelled = [lower_enum.member_name(v) for v in values]
            if len(set(spelled)) == len(spelled):
                nodes += 1
            else:  # the one colliding node's document refuses before this is read
                assert document not in emit.emit(BUNDLE, population()).emitted, (document, pointer)
    # 501 enum NODES the walk reaches, against the 447 enum CLASSES
    # ``test_an_enum_node_is_a_class_over_an_enum_base...`` counts.  The two were
    # equal at 277 and again at 333 and that was a coincidence of the populations,
    # not a rule -- a node under a position that reuses an already-declared class
    # is reached without adding one.  Neither number is derived from the other.
    # 501 -> 541 on fe0e185f9, population growth; 541 -> 545 at
    # ``salesagent-j3k2l.40``.  Still not derived from the CLASS count above, which
    # moved by 2 against this 4 -- the two were equal at 277 and again at 333 by
    # coincidence of the populations, and this is the third pair that is not.
    assert nodes == 545, nodes


def test_enum_descriptions_are_carried_into_the_member_docstrings() -> None:
    """137 nodes carry ``enumDescriptions`` and a previous attempt dropped all of
    them, for the same reason a hand-rolled renderer dropped 142 property
    descriptions: nothing compares an annotation that changes no accepted set.

    The compiler's own enum printer has the slot, so this asserts that every
    entry of every node the walk REACHES is in the emitted text -- counted, so it
    cannot pass by looking at nothing.
    """
    nodes = entries = multiline = 0
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
            nodes += 1
            for member, text in sorted(want.items()):
                if not isinstance(text, str) or not text:
                    continue
                entries += 1
                # Verbatim where the description is one line, and compared by its
                # WORDS where it is not: the compiler indents a multi-line
                # docstring into the class body, so the literal differs by exactly
                # that indentation.  ``harness._text`` is the normalizer the schema
                # comparison already uses for a description, rather than a second
                # one that could be looser.
                if "\n" in text:
                    multiline += 1
                    assert _text(got.get(member)) == _text(text), (document, pointer, member)
                else:
                    assert got.get(member) == text, (document, pointer, member)
    assert (nodes, entries, multiline) == (137, 1151, 10), (nodes, entries, multiline)

    # The whole block is an annotation, so NO check in the harness grades it:
    # `enumDescriptions` is not a fact the comparison compares.  P2 in
    # ``docs/plan/step3-prediction.md`` predicted that before it was probed.
    assert "enumDescriptions" not in FACTS


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

    sites = 0
    inherited = 0
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
            inherited += owner is not g.model
            assert bound[0].__name__ in names_spelled(owner.__module__), (
                g.ref.document,
                key,
                owner.__module__,
            )
            sites += 1
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
    assert (sites, len(documents), inherited) == (128, 78, 0), (
        sites,
        len(documents),
        inherited,
    )


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
    assert "class_body_lines" not in (compiler.StrEnum.TEMPLATE_FILE_PATH or "")

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
    annotation says.  The SCHEMA COMPARISON is not, because ``enum`` is in
    ``FACTS``: the widened model states no ``enum`` where the document states
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

    assert "enum" in FACTS
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


def test_a_model_only_fact_an_enum_implies_is_excused_and_a_narrowing_is_not() -> None:
    """The one instrument edit this step forced, and each clause of it falsified.

    ``hypothesis_jsonschema``'s ``canonicalish`` -- which ``harness.resolve``
    runs, and which the documents the package carries are written through --
    reduces an enum node to its ``enum`` ALONE.  So a faithful enumeration states
    three facts its own resolved document no longer does, and
    ``_narrows_nothing`` excuses exactly those three at exactly that node.

    The canonicalization is measured here rather than cited, and then each clause
    is shown to still report a real narrowing -- which is what keeps the row from
    being a hole of the shape the symmetric comparison was built to close.
    """
    from hypothesis_jsonschema._canonicalise import canonicalish

    stated = {"type": "string", "enum": ["a", "b"], "description": "d", "default": "a"}
    assert canonicalish(stated) == {"enum": ["a", "b"]}
    # ... and the same node WITHOUT the enum keeps all four, so this is the
    # enum collapse and not a general drop.
    kept = {"type": "string", "minLength": 1, "description": "d", "default": "x"}
    assert canonicalish(kept) == kept

    doc = {"enum": ["a", "b"]}

    class Faithful(pyenum.StrEnum):
        """d"""

        A = "a"
        B = "b"

    excused = compare_schema(doc, Faithful)
    assert excused.outcome == "pass", (excused.added, excused.missing)
    assert excused.model_facts == 2, excused.model_facts  # type and description

    # Each clause, falsified on the RULE.  End to end is the wrong level for
    # these: every model that states a wrong type or an invented default without
    # also stating the enum is already caught as ``model_drops_a_fact``, so a
    # report read off one says nothing about whether this row excused anything.
    assert _implied_by_an_enum("type", "string", ["a", "b"]) is True
    assert _implied_by_an_enum("type", "integer", ["a", "b"]) is False
    assert _implied_by_an_enum("type", "string", ["a", 1]) is False  # no one implied type
    # bool before int, because bool IS an int: a model claiming ``integer`` over a
    # boolean enum is a narrowing and stays reported.
    assert _implied_by_an_enum("type", "integer", [True, False]) is False
    assert _implied_by_an_enum("type", "boolean", [True, False]) is True
    assert _implied_by_an_enum("default", "a", ["a", "b"]) is True
    assert _implied_by_an_enum("default", "z", ["a", "b"]) is False  # not in the set
    assert _implied_by_an_enum("default", 1, ["a"]) is False  # nor of the members' type
    assert _implied_by_an_enum("default", None, ["a"]) is True  # Python's spelling of absence
    assert _implied_by_an_enum("description", "anything", ["a"]) is True
    # Anything the three rows do not name is reported, so the row excuses three
    # keywords and not "whatever sits beside an enum".
    assert _implied_by_an_enum("minLength", 5, ["a"]) is False
    assert _narrows_nothing("minLength", 5, doc) is False
    assert _implied_by_an_enum("type", "string", []) is False  # not an enum to imply from

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
    with pytest.raises(Refusal) as caught:
        lower_enum.decide({"enum": values}, "Probe", "/properties/x")
    assert caught.value.keyword == "enum"
    assert caught.value.pointer == "/properties/x"
    assert because in caught.value.detail, caught.value.detail


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
    colliding = [
        p
        for p, n in bundle.nodes(bundle.read(BUNDLE, document))
        if isinstance(n.get("enum"), list)
        and n["enum"]
        and len({lower_enum.member_name(v) for v in n["enum"]}) != len(n["enum"])
    ]
    assert colliding == ["/properties/clicktag_macro"], colliding
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
    assert len(in_bundle) == 3, in_bundle
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

    decided = lower_enum.decide({"type": "integer", "enum": [16, 24, 32]}, "BitDepth", "")
    assert decided.kind == "integer"
    assert [m.name for m in decided.members] == ["V_16", "V_24", "V_32"]
    text = compiler.render_enum(decided).text
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
    assert counted == {"typed": 905, "typeless": 164, "disagreeing": 0}, counted
    assert lower_enum.decide({"enum": ["a"]}, "P", "").kind == "string"
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
    assert len(needs) == 23, needs
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
    the reason above is a fact about the KEYWORD and not about an enum root, so
    ``compiler.BUNDLE_ANNOTATIONS`` takes it once for every position and
    ``lower.enum.HANDLED`` no longer names it. Asserted in BOTH directions here,
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
    assert "enumMetadata" in compiler.BUNDLE_ANNOTATIONS
    assert "enumMetadata" not in lower_enum.HANDLED
    out = emit.emit(BUNDLE, population())
    enum_rooted = [d for d in carriers if bundle.is_enum_root(bundle.read(BUNDLE, d))]
    assert len(enum_rooted) == 3, enum_rooted
    assert all(d in out.emitted for d in enum_rooted)

    # The price. ``compiler.ANNOTATIONS`` is the set ``check_keywords`` reads; the
    # one module that still binds it at import (``lower.rules``) asks a
    # different question of it -- what a node DECLARES -- and patching that as well
    # was measured to give the same three documents, so this patches the one.  The
    # second such binder was ``lower.product``, which is ``compiler``'s own
    # ``lower_composition`` now and reads the name it patches.
    without = frozenset(compiler.ANNOTATIONS - {"enumMetadata"})
    original = compiler.ANNOTATIONS
    try:
        compiler.ANNOTATIONS = without
        refusing = emit.emit(BUNDLE, population())
    finally:
        compiler.ANNOTATIONS = original
    assert sorted(set(refusing.refusals) - set(out.refusals)) == enum_rooted
    assert len(refusing.emitted) == len(out.emitted) - 3, len(refusing.emitted)
    for document in enum_rooted:
        assert refusing.refusals[document]["keyword"] == "enumMetadata"
        assert refusing.refusals[document]["pointer"] == "/"


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
    checked = 0
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
                checked += 1
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
    # 977 is the alias POPULATION over the ``graded()`` documents of the committed
    # 682-module tree -- the ``population()`` run, not the 691-of-1054 metric run --
    # re-measured on this tree at every step rather than carried: 910 at 0130e5fc9,
    # 957 at ac9175209, 964 at d9989750c, 977 at ``salesagent-j3k2l.40``, because the
    # population grows under the rows. 0 are unexported. The assertion is NOT weakened to ``defined in the target module``:
    # that would grade importability, which the whole-tree import in
    # ``tests/test_emit.py`` already grades, and would retire the only check on what a
    # module DECLARES -- the check that has now caught two separate defects.
    assert checked == 977, checked
