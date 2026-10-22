"""Grade D2's enumeration row: an ``enum`` node becomes a ``StrEnum``/``IntEnum``.

**Why this file exists at all, and what the harness does and does not reach.**
``tests/test_emit.py`` grades every emitted pair through the three checks, and for
an enumeration two of the three are nearly blind: the accepts and refuses checks
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

    213 of 214, with the refusal named -- and the one refusal is on a keyword the
    document carries BESIDE its enum, not on the enum.
    """
    roots = root_enums()
    assert len(roots) == 214, len(roots)
    assert set(roots) <= set(population()), "a root enum outside the step's population"

    out = emit.emit(BUNDLE, population())
    emitted = [d for d in roots if d in out.emitted]
    refused = {d: out.refusals[d] for d in roots if d in out.refusals}
    assert len(emitted) == 213, len(emitted)
    assert sorted(refused) == ["enums/task-type.json"], sorted(refused)
    assert refused["enums/task-type.json"]["keyword"] == "notes"
    assert refused["enums/task-type.json"]["pointer"] == "/"
    assert set(emitted) | set(refused) == set(roots)

    # Its cascade cost, MEASURED rather than asserted to be small: every document
    # that references it and is in the population refuses on a keyword of its
    # own, so emitting it would unblock nothing.
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
    # The claim is that NONE of them is blocked BY this document, which is read off
    # the refusal's own detail.  The keyword alone no longer says it: with step 4's
    # row claiming these roots the walk reaches their conjuncts, and 6 of the 7 now
    # refuse on a DIFFERENT ``$ref`` -- a fragment of another document, or a target
    # that composes.  A keyword test would have read those as this document's
    # cascade; the detail names the target and does not.
    assert [d for d in in_population if "task-type" in out.refusals[d]["detail"]] == []


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
    assert len(classes) == 274, len(classes)  # 213 roots, the rest inline
    roots = [d for d in root_enums() if d in {c[0] for c in classes}]
    assert len(roots) == 213, len(roots)

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
    assert names == 1964, names
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
    assert nodes == 274, nodes


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
    assert (nodes, entries, multiline) == (132, 1097, 10), (nodes, entries, multiline)

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
    sites = 0
    documents: set[str] = set()
    for g in graded():
        if g.ref.pointer != "#" or not hasattr(g.model, "model_fields"):
            continue
        raw = bundle.read(BUNDLE, g.ref.document)
        tree = ast.parse((TREE / f"{emit.module_path(g.ref.document)}.py").read_text())
        for key, sub in sorted((raw.get("properties") or {}).items()):
            if not isinstance(sub, dict) or "$ref" not in sub:
                continue
            target = bundle.document_for(sub["$ref"], known)
            if target not in roots:
                continue
            field = g.model.model_fields[compiler.field_name(key)]
            bound = [
                a for a in getattr(field.annotation, "__args__", (field.annotation,))
                if isinstance(a, type) and issubclass(a, pyenum.Enum)
            ]
            assert len(bound) == 1, (g.ref.document, key, field.annotation)
            named = {
                n.id for n in ast.walk(tree) if isinstance(n, ast.Name)
            }
            assert bound[0].__name__ in named, (g.ref.document, key)
            sites += 1
            documents.add(g.ref.document)
    assert (sites, len(documents)) == (33, 22), (sites, len(documents))


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
    wide = check_pair(Pair(name="wide", schema=doc, model=str, accept=wide_accept), max_steps=None)
    assert wide.accepts.outcome == "pass"
    assert [r.outcome for r in wide.refuses] == ["pass"]
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
    # ``$ref`` and not ``allOf``: step 4's row now claims this root, so the walk
    # reaches the conjuncts and refuses on the first one that names a FRAGMENT of
    # another document -- a node needing a name of its own, which is a later row.
    # The claim this test makes is that the colliding enum node is never reached,
    # and it holds on either keyword.
    assert out.refusals[document]["keyword"] == "$ref"
    assert out.refusals[document]["pointer"] == "/allOf/0"


def test_an_integer_enum_becomes_an_int_enum_though_no_emitted_document_has_one() -> None:
    """The second base, with its reach stated.

    3 enum nodes in the bundle have integer members, and all 3 sit in documents
    that refuse on ``const`` before the enum is read -- so **0 emitted documents
    carry an IntEnum** and the base would otherwise be graded by nothing.  Read
    off the lowering and the compiler on a node written here.
    """
    reached = [
        (d, p)
        for d in sorted(emit.emit(BUNDLE, population()).emitted)
        for p, n in bundle.nodes(bundle.read(BUNDLE, d))
        if isinstance(n.get("enum"), list)
        and any(isinstance(v, int) and not isinstance(v, bool) for v in n["enum"])
    ]
    assert reached == [], reached
    in_bundle = [
        (d, p)
        for d in bundle.portable(BUNDLE)
        for p, n in bundle.nodes(bundle.read(BUNDLE, d))
        if isinstance(n.get("enum"), list)
        and any(isinstance(v, int) and not isinstance(v, bool) for v in n["enum"])
    ]
    assert len(in_bundle) == 3, in_bundle

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


def test_enum_metadata_is_an_annotation_of_this_row_and_the_cost_is_named() -> None:
    """The one keyword decision this lane took, with its measured price.

    ``enumMetadata`` states nothing about an instance -- ``enum`` has closed the
    value set -- and an enumeration has no slot for a per-value block, so the row
    carries it as an annotation and the three documents holding one emit.
    Refusing it instead is one row out of ``HANDLED`` and costs exactly those 3
    with no cascade, which is asserted here so the alternative is priced rather
    than argued.
    """
    carriers = sorted(
        d
        for d in bundle.portable(BUNDLE)
        for _, n in bundle.nodes(bundle.read(BUNDLE, d))
        if "enum" in n and "enumMetadata" in n
    )
    assert carriers == [
        "enums/error-code.json",
        "enums/media-buy-valid-action.json",
        "enums/request-signing-error-code.json",
    ], carriers
    assert "enumMetadata" in lower_enum.HANDLED
    out = emit.emit(BUNDLE, population())
    assert all(d in out.emitted for d in carriers)

    without = frozenset(lower_enum.HANDLED - {"enumMetadata"})
    original = lower_enum.HANDLED
    try:
        lower_enum.HANDLED = without
        refusing = emit.emit(BUNDLE, population())
    finally:
        lower_enum.HANDLED = original
    assert sorted(set(refusing.refusals) - set(out.refusals)) == carriers
    assert len(refusing.emitted) == len(out.emitted) - 3, len(refusing.emitted)


def test_identical_enum_nodes_under_one_document_are_unreached_by_this_step() -> None:
    """D3's content dedup, as a ceiling with its denominator.

    D3 says two nodes with identical content are one node.  This row emits two
    classes for them, and that is a gap -- 36 such repeats over 21 documents.
    Every one of them sits under ``oneOf``/``allOf``/``definitions``/``items``,
    positions this step does not descend into, so the REACHED count is 0 and the
    fix belongs to the step whose population reaches one.
    """
    emitted = set(emit.emit(BUNDLE, population()).emitted)
    repeats = reached = 0
    for document in bundle.portable(BUNDLE):
        seen: dict[str, list[str]] = {}
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document)):
            if "enum" not in node:
                continue
            seen.setdefault(json.dumps(node, sort_keys=True), []).append(pointer)
        for pointers in seen.values():
            if len(pointers) < 2:
                continue
            repeats += len(pointers) - 1
            parts = [[p for p in ptr.split("/") if p] for ptr in pointers]
            if document in emitted and all(
                all(hop[i] == "properties" for i in range(0, len(hop), 2)) for hop in parts
            ):
                reached += 1
    assert repeats == 36, repeats
    assert reached == 0, reached


def test_the_emitted_tree_still_declares_every_module_it_imports() -> None:
    """The walk's closure, over the enum imports this step added.

    An enumeration reaches a referencing module as an IMPORT, so a root enum that
    refused while a referrer emitted would be an ImportError at the gate.  The
    whole tree is imported by ``tests/test_emit.py``; this reads the other
    direction off the AST, so a module importing a symbol from a sibling that does
    not export it fails here by name.
    """
    exported: dict[str, set[str]] = {}
    for document in sorted({g.ref.document for g in graded()}):
        module = emit.module_path(document)
        tree = ast.parse((TREE / f"{module}.py").read_text())
        exported[module] = {
            e.value
            for n in tree.body
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "__all__" for t in n.targets)
            if isinstance(n.value, (ast.List, ast.Tuple))
            for e in n.value.elts
            if isinstance(e, ast.Constant)
        }
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
    assert checked == 200, checked
