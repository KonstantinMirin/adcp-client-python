"""Grade D2's enumeration row: an ``enum`` node becomes a ``StrEnum``/``IntEnum``.

**Why this file exists at all, and what the harness does and does not reach.**
``tests/test_emit.py`` grades every emitted pair through its checks, and on an
enumeration they are blind: the accepts draw and the liveness check both run through
``strict_validate``, whose SCHEMA half refuses a non-member whatever the annotation
says, so they grade the document and not the model.  Measured as a test below
(:func:`test_the_accepts_and_liveness_checks_are_blind_to_this_row`): the enum
widening -- an enum node lowered to the scalar its ``type`` names -- leaves both
halves green.

So nothing but this file grades the row, and that reaches everything about an
enumeration: the accepted set, the member NAMES, the per-member descriptions, and the
base.  A lower-cased member is caught by nothing except an import failure, and that is
why the upper-casing is asserted here over the whole emitted population.

Every assertion is over something DERIVED -- the population off the bundle, the
members off the document, the names off the function that runs -- so a pass cannot
be a record of what the tree happens to hold.
"""

from __future__ import annotations

import ast
import enum as pyenum
import functools
import importlib
import json
from pathlib import Path
from typing import Any

import populations
import pytest
from compiled import compiled
from conftest import refusal_from
from pydantic import TypeAdapter, ValidationError

from adcp.types._base import SchemaRef, schema_at
from codegen import bundle, compiler, emit, ir, keywords, render, store
from codegen import refusal as refusal_module
from codegen.keywords import Position
from codegen.lower import enum as lower_enum
from codegen.lower import names
from codegen.schema import nodes as schema_nodes
from codegen.schema import parse as schema_parse
from tests.nodeset import claimed, partitions
from tests.test_emit import BUNDLE, PACKAGES, TREE, graded, population


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


@functools.cache
def emitted_enum_classes() -> list[tuple[str, str, type[pyenum.Enum]]]:
    """``(document, module source, class)`` for every enum class in the tree.

    **A reading of the module's NAMESPACE, which is §3a's own correction of 2026-11-02:**

        "**AND A GUARD THAT READS CLASS STATEMENTS GOES BLIND TO AN ASSIGNMENT, so it
        reads the NAMESPACE.**  A collision guard exists to answer what a consumer meets
        when importing the module, and a consumer meets the module's namespace, not its
        syntax.  Reading the emitted module's own bindings is both stricter and not a
        structural assertion -- it stops caring how a name came to be bound, which is the
        property that let the functional form slip past it."

    It read the AST and selected by the BASE the compiler rendered, and §3a's other
    correction is what made that population wrong rather than merely narrow: a value
    list the bundle states under two names judged distinct is written once and the types
    over it are ``StrEnum('<Name>', _VALUES)``, which subclasses nothing in the text.
    Measured over this bundle: 33 classes in 34 modules are built that way, and an AST
    census by base graded none of them -- a scope omitting exactly the code the new row
    added.

    ``__module__`` is what tells a DECLARATION from an import, so a class one module
    declares and another imports is graded once, under the document that produced it.

    The SOURCE rides along because two checks here are about the TEXT and not about the
    namespace -- a member docstring is a class-body statement and a module-level
    ``__doc__`` assignment, and neither is a runtime attribute of an ``Enum`` member.
    WHICH FILE each document's module is in is a derivation and not a scan, and the
    derivation is ``emit.module_file``: a document whose path is also a directory's is a
    package ROOT written to ``<path>/__init__.py``, so ``module_path`` (the NAME's path)
    names no file for ``brand.json``.
    """
    out: list[tuple[str, str, type[pyenum.Enum]]] = []
    for document in sorted({g.ref.document for g in graded()}):
        src = (TREE / f"{emit.module_file(document, PACKAGES)}.py").read_text()
        name = emit.module_name(document)
        module = importlib.import_module(name)
        for value in vars(module).values():
            if (
                isinstance(value, type)
                and issubclass(value, pyenum.Enum)
                and value.__module__ == name
            ):
                out.append((document, src, value))
    return out


def _members(cls: type[pyenum.Enum]) -> list[tuple[str, Any]]:
    """``(name, value)`` for each member, read off the class the module BOUND.

    ``__members__`` and not ``__iter__``, so an ALIAS is reached under its own key: two
    values that spell one member name render a ``Literal`` and no class at all (§5's
    ``enum`` row), so a class here has one member per value by construction -- and a
    reading that silently dropped an alias would be the one that could not say so.
    """
    return [(name, member.value) for name, member in cls.__members__.items()]


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

    out = compiled(BUNDLE, population())
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
        return isinstance(doc.get("type"), str) and doc["type"] in compiler.SCALAR

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
def test_an_enum_node_is_an_enumeration_in_the_modules_namespace_and_not_a_scalar() -> None:
    """D2: an ``enum`` node is an enumeration, not the scalar its ``type`` names.

    **It was two halves and is one, which is §3a's correction of 2026-11-02 and not a
    weakening**: the first half read the AST for a ``ClassDef`` over
    ``StrEnum``/``IntEnum`` and asserted the symbol was *not also* a module-level
    assignment, "which is what a lowering that fell back to the scalar row would emit".
    §3a's functional form IS a module-level assignment, so that reading reported the
    thing it was built to permit -- and a guard "exists to answer what a consumer meets
    when importing the module, and a consumer meets the module's namespace, not its
    syntax".

    So the one half is the namespace, and it is STRICTER than the pair it replaces: it
    answers "the name is bound to an enumeration whose members are the document's own
    ``enum`` array, in order, exactly", which a lowering that fell back to the scalar row
    fails at the binding rather than at the syntax.
    """
    classes = emitted_enum_classes()
    # **NO COUNT OF THE CLASSES IS ASSERTED, and the comment that stood here is why.**
    # It recorded eight re-pointings of this one number -- 447, 482, 484, 506, 502, 504,
    # and a 503 that came and went inside a single row -- each one correct, each one a
    # population growing or D3's dedup collapsing a node, and not one of them a defect
    # this check exists to catch.  Two rows in flight compute two different right
    # answers for it.  What IS asserted is the set: the classes the tree carries are
    # non-empty, and the root half of them is exactly the root enums.
    claimed("enum classes the tree carries", {(d, c.__name__) for d, _, c in classes})
    # The ROOT half is exactly the root enums, by name: every root enum the tree
    # carries a class for IS a root enum, and none is missing.  A set identity rather
    # than a count of 214, so a root enum that stops getting a class is named here.
    roots = [d for d in root_enums() if d in {c[0] for c in classes}]
    assert claimed("root enums with a class", roots) == set(root_enums()), sorted(
        set(root_enums()) - set(roots)
    )

    for document in roots:
        doc = bundle.read(BUNDLE, document)
        module = importlib.import_module(emit.module_name(document))
        (symbol,) = module.__all__
        cls = getattr(module, symbol)
        # The BASE off the class and not off a base list in the text, which is the same
        # move: ``StrEnum`` and ``IntEnum`` are what D2's two kinds resolve to, and a
        # class built from a value list has them as bases without naming them in a
        # statement.
        assert isinstance(cls, type) and issubclass(cls, pyenum.Enum), document
        assert issubclass(cls, pyenum.StrEnum | pyenum.IntEnum), document
        # The one symbol this document exports is DECLARED here and not imported, which
        # is §1's one-import-path rule read at the root: a root that re-exported another
        # module's class would leave its own document with no name of its own.
        assert cls.__module__ == emit.module_name(document), document
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
            assert name == name.upper(), (document, cls.__name__, name)
            assert name == lower_enum.member_name(value), (
                document,
                cls.__name__,
                name,
                value,
            )
            names.add((cls.__name__, name))
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

    # So the check is over `member_name`, and it is injective at every node the walk
    # reaches THAT GETS AN ENUM CLASS -- which is the claim, with its denominator.
    #
    # **The else branch inverted on 2026-10-29 and the claim it holds is now the
    # ROUTE.**  It read: a colliding node's document refuses before this is read, so
    # the injectivity is vacuous nowhere.  §5's ``enum`` row withdrew that refusal --
    # the node renders a ``Literal``, which mints no member name at all -- so what the
    # branch asserts is that the colliding node minted NO enum class, which is what
    # keeps the injectivity above a statement about every class and not about most of
    # them.  Read off the module the COMPILER produced, because a document that
    # emits for the first time has no file in the committed tree yet.
    nodes: set[tuple[str, str]] = set()
    for document in sorted({g.ref.document for g in graded()}):
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document)):
            values = node.get("enum")
            if not isinstance(values, list) or not values:
                continue
            spelled = [lower_enum.member_name(v) for v in values]
            if len(set(spelled)) == len(spelled):
                nodes.add((document, pointer))
            else:  # routed to a ``Literal``, so no class was minted from it
                # **Off the module's NAMESPACE** (§3a, 2026-11-02: a guard "reads the
                # NAMESPACE" because that is what a consumer meets), which is also the
                # only reading that can still see the class a value list is CONSTRUCTED
                # into -- ``X = StrEnum('X', _VALUES)`` has no base list to select on.
                minted = {
                    frozenset(name for name, _ in _members(cls))
                    for _, _, cls in emitted_enum_classes()
                    if cls.__module__ == emit.module_name(document)
                }
                assert frozenset(spelled) not in minted, (document, pointer)
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
    descriptions: nothing in the harness grades an annotation, which changes no
    accepted set.

    The compiler's own enum printer has the slot, so this asserts that every
    entry of every node the walk REACHES is in the emitted text -- counted, so it
    cannot pass by looking at nothing.
    """
    nodes: set[tuple[str, str]] = set()
    entries: set[tuple[str, str, str]] = set()
    multiline: set[tuple[str, str, str]] = set()
    by_document: dict[str, list[type[pyenum.Enum]]] = {}
    for document, _, cls in emitted_enum_classes():
        by_document.setdefault(document, []).append(cls)
    for document in sorted({g.ref.document for g in graded()}):
        tree = ast.parse((TREE / f"{emit.module_file(document, PACKAGES)}.py").read_text())
        # **The TEXT and not the namespace, and that is a fact about ``enum`` rather than
        # a leftover reading.**  A member docstring is a bare string EXPRESSION in a class
        # body, which Python evaluates and discards -- ``X.A.__doc__`` is the ``Enum``
        # default and never the text -- so the module's bindings cannot answer this and
        # the source is what carries it (:func:`_docstrings`).  §3a's namespace rule is
        # about what a consumer MEETS, and a consumer meets a member docstring in an
        # editor and in ``help()``, both of which read the source.
        #
        # The CLASSES come from the namespace census, which is what keeps an enumeration
        # over a shared value list in scope: its members' values are read out of a
        # constant, so nothing in the text names a base this could have selected on.
        rendered = {
            frozenset(name for name, _ in _members(cls)): _docstrings(tree, cls.__name__)
            for cls in by_document.get(document, ())
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
                # Verbatim where the description is one line, and by its WORDS where
                # it is not: the compiler indents a multi-line docstring into the class
                # body, so the literal differs by exactly that indentation and nothing
                # else (:func:`_by_words`).
                if "\n" in text:
                    multiline.add((document, pointer, member))
                    assert _by_words(got.get(member)) == _by_words(text), (
                        document,
                        pointer,
                        member,
                    )
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
    # `enumDescriptions` is not even a keyword a faithful model renders.  P2 in
    # ``docs/plan/step3-prediction.md`` predicted that before it was probed.
    assert "enumDescriptions" not in keywords.rendered_at(Position.ROOT)


def _by_words(x: Any) -> Any:
    """A description read by its words and not by its line breaks.

    The compiler indents a multi-line docstring into the class body, so the emitted
    literal and the document's own text differ by exactly that indentation.  A
    non-string travels through unchanged, so a member the emitted class does not
    carry at all is still a mismatch rather than a crash.
    """
    return " ".join(x.split()) if isinstance(x, str) else x


def _docstrings(tree: ast.Module, symbol: str) -> dict[str, str]:
    """``member -> docstring`` for the enum class ``symbol``, off the module's source.

    The parsed CONSTANT and not the source text, so what is compared is the string
    the module defines rather than the compiler's escaping of it -- a description
    carrying a quote or a backslash is escaped in the source and would never match
    the document verbatim there.

    **ONE FORM, and that is what §3a's value list costing a consumer's checker settled**:
    an enumeration over a shared value list is a class statement like any other and only
    its members' VALUES move into the constant, so the docstring slot is the class body's
    in both cases and there is one reading of it.  It was two for the length of one
    commit, while the shared case was the functional ``StrEnum('<Name>', …)`` call and the
    member docstring had to be a module-level ``<Symbol>.<MEMBER>.__doc__`` statement.

    ``symbol`` and not the whole module, because a class is found by the NAME the
    namespace census read off the class object -- so the two readings cannot disagree
    about which class a docstring belongs to.
    """
    out: dict[str, str] = {}
    for node in tree.body:
        if not (isinstance(node, ast.ClassDef) and node.name == symbol):
            continue
        for assign, after in zip(node.body, node.body[1:], strict=False):
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
            name = names.field_name(key, render.RESERVED)
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
        d for d in root_enums() if d in compiled(BUNDLE, population()).emitted
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


def test_the_accepts_and_liveness_checks_are_blind_to_this_row() -> None:
    """The finding this file rests on, measured rather than carried forward.

    The enum widening -- an enum node lowered to the scalar its ``type`` names --
    leaves both halves of ``check_pair`` green, for the reason they are blind to
    everything the annotation does not decide: ``strict_validate``'s schema half
    refuses a non-member whatever the annotation says, so the draw accepts what the
    document accepts, the dump validates, and the liveness check gets its refusal from
    the document.  So nothing here grades the enumeration, and everything this file
    asserts about one it asserts over the emitted population itself.

    Graded on the document of a real root enum, through the production shape of an
    entry point: the document decides, then the annotation builds.
    """
    document = next(d for d in root_enums() if d in compiled(BUNDLE, population()).emitted)
    doc = schema_at(SchemaRef(document, "#"))

    from codegen.harness import Pair, check_accepts, check_pair

    adapter = TypeAdapter(str)

    def wide_accept(payload: Any) -> Any:
        from adcp.types._base import _refuse

        _refuse(doc, payload, "Wide")
        return adapter.validate_python(payload)

    assert check_accepts(doc, wide_accept).outcome == "pass"
    wide = check_pair(Pair(name="wide", schema=doc, model=str, accept=wide_accept))
    assert wide.accepts.outcome == "pass"
    assert wide.liveness.outcome == "pass", (wide.liveness.how, wide.liveness.detail)
    assert wide.graded_instances > 0, wide.graded_instances


# --------------------------------------------------------------------------- #
# the three refusals, the base this bundle does not reach, and the collision
# that is a rendering and not a refusal
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    ("values", "because"),
    [
        (["a", 1], "mixed type"),
        ([], "enumerates nothing"),
        (["a", "a"], "appears twice"),
        ([True, False], "bool is an int subclass"),
    ],
    ids=["mixed-types", "empty", "duplicated-value", "boolean"],
)
def test_a_node_this_row_cannot_represent_refuses_by_name(values: list, because: str) -> None:
    """The three representability refusals, plus the excluded base.

    **None of them is reachable from this bundle**, and that is stated rather than
    hidden: there are 0 mixed, 0 empty, 0 duplicated and 0 boolean enum nodes over
    all 1,069.  So they are graded on nodes written here, which is the right level
    -- they are properties of the lowering, not of the bundle.

    **The fourth case left this list on 2026-10-29 and became the test below it.**
    ``["clickTag", "clickTAG"]`` was a parameter here, asserting the hand-written
    verdict §5's ``enum`` row withdrew; the collision now selects a RENDERING, so
    there is nothing for this test to catch and a refusal would be the defect.
    """
    caught = refusal_from(lower_enum.decide(_probe({"enum": values}, "/properties/x"), "Probe"))
    assert caught.keyword == "enum"
    assert caught.pointer == "/properties/x"
    assert because in caught.detail, caught.detail


def test_a_constraint_beside_an_enum_refuses_an_excluded_member_so_the_members_are_the_set() -> None:
    """The premise §3a's value-list key rests on, stated where the refusal that makes it
    true lives.

    §3a keys a catalogue entry on the VALUE LIST, and ``compiler.Module.restatements``
    was asked only of a node carrying no constraint beside its ``enum`` -- "a value list
    beside a ``pattern`` admits a subset of the members and is not the entry's
    vocabulary".  That premise is :func:`lower_enum.excluded` restated and it is false
    past it: the row REFUSES a node whose own constraints exclude any member, so every
    node that lowers at all admits exactly its members and two positions over one value
    list admit the same instances.

    Both directions, because only the pair says it:

    * a constraint that excludes a member is a VERDICT, named on the keyword that
      excludes it -- so the subset case never reaches the key;
    * a constraint every member satisfies lowers to the members unchanged -- so the
      relaxation gives up nothing.

    **Graded on nodes written here, which is the right level** for
    :func:`test_a_node_this_row_cannot_represent_refuses_by_name`'s own reason: the RAW
    bundle states 0 constraint keywords beside an ``enum``, and the one node that reaches
    the case gets its ``pattern`` from §2's intersection rule during the walk.  The
    MEASURED half of it is below -- that node's two classes became one.
    """
    excluded = lower_enum.lower(
        _probe({"enum": ["DE", "CH", "at"], "pattern": "^[A-Z]{2}$"}, "/properties/country"),
        compiler.Module(document="probe.json"),
    )
    caught = refusal_from(excluded)
    assert caught.keyword == "pattern", caught
    assert caught.pointer == "/properties/country"
    assert "'at'" in caught.detail, caught.detail

    inside = lower_enum.decide(
        _probe({"enum": ["DE", "CH", "AT"], "pattern": "^[A-Z]{2}$"}, "/properties/country"),
        "Probe",
    )
    assert not isinstance(inside, refusal_module.Refusal), inside
    assert [m.value for m in inside.members] == ["DE", "CH", "AT"]

    # And the measurement: the one node of this bundle that reaches the case.  §2's
    # intersection rule puts ``core/postal-country-system.json``'s root ``^[A-Z]{2}$``
    # beside its branch's three members, and ``core/postal-area.json`` re-lowers that very
    # node -- which drew a second class over one value list until the guard was relaxed.
    out = compiled(BUNDLE, population())
    home = "core/postal-country-system.json"
    composing = "core/postal-area.json"
    assert out.declared[home]["/anyOf/3/properties/country"] == "Country"
    assert "Country" not in set(out.declared[composing].values()), out.declared[composing]
    assert "from .postal_country_system import" in out.files[
        f"{emit.module_file(composing, PACKAGES)}.py"
    ]


def test_two_members_spelling_one_name_give_a_literal_of_both_and_no_enum_class() -> None:
    """§5's ``enum`` row, decided 2026-10-29, at the one node of the bundle that reaches it.

    "Two members whose spellings yield one Python name → a ``Literal`` of the members
    and NOT an enum class.  The collision exists only because an enum mints a Python
    IDENTIFIER per member; a ``Literal`` needs none, so both values are carried exactly
    as the document spells them and nothing is dropped."

    Four claims, each read off something derived:

    * the collision is still in the bundle, and it is asked of ``member_name`` -- the
      function that names the members -- rather than of a second spelling here;
    * the node lowers to a ``Literal`` carrying BOTH values in the document's own
      order and spelling, so nothing is dropped and no member is aliased away;
    * the document EMITS, where it refused with 20 chained behind it before;
    * and the emitted module states both spellings, which is the only place a dropped
      member could hide.

    The pointer is NOT pinned as a constant: it is derived from the document by the
    same predicate the compiler routes on, so a second colliding node joins the set
    and reddens here rather than passing unseen.
    """
    document = "formats/canonical/html5.json"
    raw = bundle.read(BUNDLE, document)
    node = raw["properties"]["clicktag_macro"]
    assert node["enum"] == ["clickTag", "clickTAG"]
    assert len({lower_enum.member_name(v) for v in node["enum"]}) == 1

    walked = claimed(
        "enum nodes of this document",
        [p for p, n in bundle.nodes(raw) if isinstance(n.get("enum"), list) and n["enum"]],
    )
    colliding = [
        p
        for p, n in bundle.nodes(raw)
        if isinstance(n.get("enum"), list)
        and n["enum"]
        and len({lower_enum.member_name(v) for v in n["enum"]}) != len(n["enum"])
    ]
    assert colliding == ["/properties/clicktag_macro"], colliding
    assert set(colliding) <= set(walked), colliding

    # The ROUTE and the RENDERING, off the lowering itself rather than off the tree:
    # the predicate answers yes and the node decides to a ``Literal`` of both values.
    probe = _probe(node, "/properties/clicktag_macro")
    assert lower_enum.two_members_spell_one_name(probe) is True
    decided = lower_enum.literal(probe)
    assert not isinstance(decided, refusal_module.Refusal), decided
    assert decided.type.literals == ("clickTag", "clickTAG"), decided.type

    # And the document emits, which is the 21 refusals the withdrawn clause cost.
    #
    # Read off the COMPILE and not off the committed tree: a newly emitting document
    # has no module there until the tree is repopulated, and the claim is about what
    # the compiler produces.
    out = compiled(BUNDLE, population())
    assert document not in out.refusals, out.refusals[document]
    assert document in out.emitted
    source = out.files[f"{emit.module_file(document, PACKAGES)}.py"]
    assert "'clickTag'" in source and "'clickTAG'" in source, source


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
    reached = integer_enum_nodes(sorted(compiled(BUNDLE, population()).emitted))
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
        # **The module's NAMESPACE and not its class statements**, which is §3a's own
        # correction of 2026-11-02: "a collision guard exists to answer what a consumer
        # meets when importing the module, and a consumer meets the module's namespace,
        # not its syntax."  The same reading is what this half needs, and §3a's catalogue
        # is what made the difference visible: ``{16, 24, 32}`` is one vocabulary stated
        # at ``core/assets/audio-asset.json``'s ``bit_depth`` and at
        # ``core/assets/video-asset.json``'s ``audio_bit_depth``, so the second module
        # IMPORTS ``AudioBitDepth`` instead of declaring a second class over the same
        # three values.  Selecting over class statements asserted which of those two
        # §3a decides, which is not what this test is about; the base and the members at
        # the node are, and both are read off the object a consumer reaches.
        at_this_node = [
            held
            for held in vars(module).values()
            if isinstance(held, type)
            if issubclass(held, pyenum.IntEnum)
            if [m.value for m in held] == node["enum"]
        ]
        assert len(at_this_node) == 1, (document, pointer, [c.__name__ for c in at_this_node])
        cls = at_this_node[0]
        assert issubclass(cls, pyenum.IntEnum), (document, pointer)
        assert [m.value for m in cls] == node["enum"], (document, pointer)

    decided = lower_enum.decide(_probe({"type": "integer", "enum": [16, 24, 32]}), "BitDepth")
    assert decided.kind == "integer"
    assert [m.name for m in decided.members] == ["V_16", "V_24", "V_32"]
    text = render.enum(decided).text
    assert text.startswith("class BitDepth(IntEnum):"), text
    scope: dict[str, Any] = {"IntEnum": pyenum.IntEnum}
    exec(compile(text, "<probe>", "exec"), scope)  # the compiler's own output
    assert [m.value for m in scope["BitDepth"]] == [16, 24, 32]
    assert TypeAdapter(scope["BitDepth"]).json_schema()["type"] == "integer"


def test_the_base_comes_from_the_members_which_is_what_admits_a_typeless_node() -> None:
    """164 of the bundle's 1,069 enum nodes declare no ``type`` at all.

    Reading the base off the members is what lowers them -- and it is a faithful
    reading rather than a fallback, because ``type`` and the members agree at all
    1,069 nodes, measured here.
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
    out = compiled(BUNDLE, population())
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
        # ``emit.emit`` and NOT ``compiled``: swapping the TABLE is a runtime
        # perturbation, and ``tests/compiled.py``'s key is a digest of ``codegen/``'s
        # SOURCE -- which a reassignment does not move.  The cache would price the row
        # against the UNMODIFIED table, so the four documents below would be measured
        # against themselves.  Enforced by
        # ``tests/test_no_cached_compile_under_a_perturbation.py``.
        #
        # ``store.perturbed()`` is that sentence one layer down: ``emit.emit`` holds §1's
        # census on disk under the same kind of source digest (``codegen/store.py``), and a
        # reassignment of the TABLE does not move that digest either -- so a miss here
        # would write a census derived without the row under the key every honest run asks
        # for, and a hit would price the row against the census the row is still in.
        with store.perturbed():
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

    **THE ROOT IS EXPORTED, AND THE ORDER IS NOT A CLAIM ANY MORE.**  This asserted
    ``listed[:1] == [root]`` -- the document's own class at the HEAD of ``__all__`` --
    and ``tests/test_emit.py``'s ``_symbol`` read index 0 on the strength of it.  The
    position stopped being the emitter's to decide at 6cb95c568: ``render.module``
    writes ``sorted(exports, key=_export_key)``, which is ``RUF022``'s order and was
    adopted to clear 31 findings in the generated tree, so ``emit.exported``'s
    root-first list is sorted away.  Measured here: the root is at index 0 in 1,023 of
    1,054 modules and somewhere else in 31 -- ``BaseGroupAsset`` before ``Format``,
    ``Agents`` before ``BrandDiscovery``, ``AgeRestriction`` first of
    ``core/targeting.json``'s 24.

    So the claim is restated as the one the emitter can keep while a linter decides the
    order, and it is the claim ``_symbol`` now depends on: the root is EXPORTED, and the
    two independent derivations of which symbol it is agree.  ``compiler.class_name``
    over the document's own ``title`` is the function ``lower_document`` makes the symbol
    with; ``__adcp_schema__`` is §8's record of the node a class came from, and the root
    is the class at pointer ``#``.  Neither restates what the tree happens to hold, and a
    renamed root that the walk did not follow fails both halves.
    """
    # **THE TWO READINGS ARE BOTH NEEDED HERE and they are not interchangeable**, which
    # is why each has its own name below.  ``module`` is the NAME's path and it is what a
    # relative import's TAIL resolves to, so it is the key ``exported`` is held under and
    # the key ``target`` is looked up by.  ``file`` is the FILE that holds it, which is
    # what gets opened AND what the LEADING DOTS count hops up from -- the same asymmetry
    # ``emit.relative_module`` is written to: ``brand.json`` is a package root, so its
    # name is ``brand`` and its file is ``brand/__init__``, one level deeper.
    exported: dict[str, set[str]] = {}
    #: The two halves of the root claim, each named so neither can grade an empty set:
    #: every document's root is exported, and the subset of roots that are CLASSES --
    #: the ones with somewhere to carry a ref, D2 making a scalar root an alias instead --
    #: is where the provenance derivation can be asked at all.
    by_title: set[tuple[str, str]] = set()
    by_provenance: set[tuple[str, str]] = set()
    for document in sorted({g.ref.document for g in graded()}):
        module = emit.module_path(document)
        tree = ast.parse((TREE / f"{emit.module_file(document, PACKAGES)}.py").read_text())
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
        assert root in listed, (module, listed, root)
        by_title.add((document, root))
        held = importlib.import_module(emit.module_name(document))
        carrying = [
            name
            for name in listed
            if getattr(getattr(held, name), "__adcp_schema__", None) == SchemaRef(document, "#")
        ]
        # A class carries the ref or the module does (§5's root binding), and a module
        # whose root is another document's node re-exports that class, which correctly
        # carries the OTHER document's ref.  Where a class answers, it is the root the
        # title derived; where none does, the module exports one name and there is
        # nothing for two derivations to disagree about.
        if carrying:
            assert carrying == [root], (module, carrying, root)
            by_provenance.add((document, root))
        else:
            assert listed == [root], (module, listed, root)
        exported[module] = set(listed)
    claimed("documents whose root symbol the title derives", by_title)
    claimed("documents whose root CLASS carries the document's own ref", by_provenance)
    checked: set[tuple[str, str, str]] = set()
    for document in sorted({g.ref.document for g in graded()}):
        module = emit.module_path(document)
        file = emit.module_file(document, PACKAGES)
        tree = ast.parse((TREE / f"{file}.py").read_text())
        for n in ast.walk(tree):
            if not isinstance(n, ast.ImportFrom) or not n.level:
                continue
            up = Path(file).parent
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
    # ``SlotsItem`` crossed into 7 modules with no ``$ref`` naming
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
