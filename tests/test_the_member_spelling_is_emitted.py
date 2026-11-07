"""Reading 10's SECOND member spelling, graded as an EMITTED class-body line.

``docs/plan/final-state.md`` reading 10, at ATTRIBUTE granularity, and
``adcp-client-python-4yk8``'s ruling of 2026-11-06:

    YES -- the emitted enum carries the value-verbatim spelling as an alias member, in the
    CLASS BODY. ... an enum alias is a NAME and never a second member (``__members__``
    unchanged) ... EMITTED in the class body, never installed at runtime, because reading 8
    says the wheel is the artifact ... REFUSED where the spelling cannot be one: invalid
    identifier, two values re-casing onto one attribute, collision with a canonical member
    -- reported with counts, never silently skipped.

**WHAT THIS GRADES AND WHY NOTHING ELSE CAN.**  Our generated members are ``UPPER_SNAKE``
and ``datamodel-code-generator``'s are the value verbatim, so ``Recovery('transient')``
works on both packages and ``Recovery.transient`` worked on theirs alone -- and **3,282 of
upstream 9.6.1's behavioural tests failed on that ONE member**, more than any class name
that lane found.  ``core/error.json`` states the value list
``transient|correctable|terminal`` and says NOTHING about the attribute a caller types, so
this is not a wire difference and not a reading 1 exposure: both spellings reach the same
member and both enums admit exactly the same set.  Neither the accepts draw nor the
liveness check can see any of it -- ``tests/test_enum.py``'s own preamble says why, the
schema half of ``strict_validate`` refuses a non-member whatever the annotation says -- and
``tests/test_the_alias_layer_is_names.py`` cannot either, because that table ranges over
NAMES (classes) and a member is an attribute OF one.

**THE TREE READ HERE IS THE ONE A FRESH RUN EMITS**, through
``tests/test_enum.py``'s ``emitted_enum_classes`` and therefore through ``tests/fresh.py``.
That is not a convenience: the ruling requires this gate to redden when the EMITTER is
perturbed, and two source-side perturbations earlier in this project read GREEN and were
discarded as worthless gates.  A reading of ``src/`` would be one of those -- it passes on
whatever was last written there.  Every figure below is consequently a function of the
bundle and of ``codegen/``, and the one derivation of the spellings
(``codegen.lower.enum.member_aliases``) is READ rather than restated, for the reason
``member_name`` is read rather than restated next door: a second spelling function written
in a test is a copy that can disagree with the one that runs, and a refusal count derived
from a copy describes a tree nobody emitted.

**A FOURTH REFUSAL CLASS, WHICH THE MEASUREMENT ADDED TO THE RULING'S THREE** and which
:func:`test_every_refusal_class_is_counted_and_named_in_the_bundle` reports beside them:
the value verbatim is a name the ENUMERATION ITSELF already resolves
(``adcp.types._base.MEMBER_NAMES_TAKEN``).  ``"name"`` and ``"value"`` are live enum values
of this bundle, so the first tree emitted under this row carried
``name = MemberAlias('NAME')`` and ``Kind.NAME.name`` returned the MEMBER -- the
``enum.Enum.name`` descriptor shadowed by a class-body line.  A fifth would be a fifth
entry here; none is hidden.
"""

from __future__ import annotations

import ast
import enum as pyenum
import functools
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from compiled import compiled
from pydantic import TypeAdapter
from test_emit import BUNDLE, population
from test_enum import _members, emitted_enum_classes

from adcp.types._base import MEMBER_NAMES_TAKEN, MemberAlias
from codegen import bundle, ir, render
from codegen.lower import enum as lower_enum
from tests.nodeset import claimed, partitions

#: The one member the bead is written about, as the document that states it and the
#: attribute a caller of upstream's package types.  Not a fixture of the tree: the VALUE
#: LIST is read out of the bundle below and the spelling is derived from it, so this names
#: a document and a property and nothing about the output.
DOCUMENT = "core/error.json"
POINTER = "/properties/recovery"


@functools.cache
def _aliased() -> list[tuple[str, type[pyenum.Enum], dict[str, str], dict[str, str]]]:
    """``(document, class, {alias: canonical}, {canonical: refusal})`` per emitted enum.

    The two dicts come from ``codegen.lower.enum.member_aliases`` -- THE derivation -- over
    the member set read off the class the fresh tree BOUND.  So the pairing graded here is
    "what the compiler decides" against "what the artifact carries", and neither side is a
    list anybody wrote.

    ``_name_`` and ``_value_`` rather than ``.name`` and ``.value``, because the sunder
    names are the ones a member cannot lose: the public two are
    ``DynamicClassAttribute``s a class-body line can shadow, which is the defect
    :data:`MEMBER_NAMES_TAKEN` exists to refuse and which this reading must survive in
    order to report.
    """
    out = []
    for document, _, cls in emitted_enum_classes():
        members = [ir.Member(name=m._name_, value=m._value_) for m in cls]
        aliases, refused = lower_enum.member_aliases(members)
        out.append((document, cls, aliases, refused))
    return out


def _trimmed(lines: list[str]) -> list[str]:
    """``lines`` with its trailing blank ones dropped."""
    out = list(lines)
    while out and not out[-1].strip():
        out.pop()
    return out


def _descriptors(cls: type[pyenum.Enum]) -> dict[str, str]:
    """``{bound name: canonical member name}`` for every alias in the class's own dict."""
    return {
        name: value.canonical
        for name, value in vars(cls).items()
        if isinstance(value, MemberAlias)
    }


# --------------------------------------------------------------------------- #
# the named member: the one 3,282 of upstream's tests failed on
# --------------------------------------------------------------------------- #
def test_the_value_verbatim_spelling_of_the_named_member_resolves_to_the_same_member() -> None:
    """``Recovery.transient is Recovery.TRANSIENT``, with the value list read off the bundle.

    Four claims, and the first is ``is`` and not ``==``.  Equality would be satisfied by a
    second member carrying the same value -- which is precisely the mechanism this row
    refuses -- and a ``StrEnum`` would satisfy it by a bare string as well:
    ``Recovery.TRANSIENT == 'transient'`` is already true and says nothing.

    * the spelling resolves, and resolves to the SAME OBJECT as the canonical member;
    * ``__members__`` carries THREE names and the lower-case spelling is not one of them,
      so the alias is a name and never a second member;
    * the value set is exactly the document's own ``enum``, read out of
      ``schemas/cache/3.2`` rather than written here;
    * and ``Recovery('transient')`` -- the call that worked on both packages before this
      row and is the reason this is not a wire difference -- still returns that member.
    """
    node = bundle.read(BUNDLE, DOCUMENT)["properties"]["recovery"]
    stated = node["enum"]
    assert stated == ["transient", "correctable", "terminal"], stated

    recovery = next(
        cls
        for document, _, cls in emitted_enum_classes()
        if document == DOCUMENT and cls.__name__ == "Recovery"
    )

    # IDENTITY, per value, over the document's own list.
    for value in stated:
        canonical = lower_enum.member_name(value)
        assert getattr(recovery, value) is getattr(recovery, canonical), value
        assert recovery(value) is getattr(recovery, canonical), value

    # A NAME AND NEVER A SECOND MEMBER: three, not six.
    assert len(recovery.__members__) == len(stated) == 3, recovery.__members__
    assert set(recovery.__members__) == {lower_enum.member_name(v) for v in stated}
    assert [v for v in stated if v in recovery.__members__] == []

    # AND NO VALUE SET WIDENED: the map the runtime dispatches on is the document's list.
    assert list(recovery._value2member_map_) == stated, recovery._value2member_map_

    # The three spellings are DESCRIPTORS in the class's own dict, which is what makes the
    # two statements above compatible at all.
    assert _descriptors(recovery) == {
        "transient": "TRANSIENT",
        "correctable": "CORRECTABLE",
        "terminal": "TERMINAL",
    }


# --------------------------------------------------------------------------- #
# the whole population
# --------------------------------------------------------------------------- #
def test_an_alias_is_a_name_over_every_emitted_enum_and_no_member_set_moves() -> None:
    """Reading 10's clause over all of it, with the denominator claimed.

    Four assertions per class, and each one is the negation of a way this row could have
    gone wrong:

    * **``__members__`` is exactly the canonical spellings.**  ``member_name`` is applied
      to the class's own values and the result must be the member set, which no alias can
      be a member of -- ``transient`` is ``member_name`` of nothing.  This is the clause
      that reddens on the obvious wrong implementation (a plain ``transient = 'transient'``
      beside ``TRANSIENT``, which is python's own enum aliasing and puts the second name IN
      ``__members__``).
    * **one member per value**, so no alias became a member that ``__iter__`` skips.
    * **``_value2member_map_`` is exactly the class's values**, so nothing widened: an
      alias carrying a value of its own would be a fourth entry here.
    * **every descriptor the artifact carries is one the compiler decided**, and resolves
      by ``is`` to its canonical member.  Asserted as set equality in BOTH directions, so a
      spelling the artifact carries and the compiler did not decide is as much a failure as
      the reverse.
    """
    graded = _aliased()
    assert graded, "no enum class was graded"

    spellings: set[tuple[str, str]] = set()
    for document, cls, aliases, _ in graded:
        values = [value for _, value in _members(cls)]
        assert set(cls.__members__) == {lower_enum.member_name(v) for v in values}, (
            document,
            cls.__name__,
        )
        assert len(cls.__members__) == len(values) == len(list(cls)), (document, cls.__name__)
        assert set(cls._value2member_map_) == set(values), (document, cls.__name__)

        assert _descriptors(cls) == aliases, (document, cls.__name__)
        for alias, canonical in aliases.items():
            assert getattr(cls, alias) is cls[canonical], (document, cls.__name__, alias)
            assert alias not in cls.__members__, (document, cls.__name__, alias)
            spellings.add((cls.__module__, alias))

    # The second spellings the tree carries, as the non-empty set of (module, name) pairs.
    # A population figure and not a floor: it moves with the bundle, and what is asserted
    # is the per-class pairing above.
    claimed("value-verbatim member spellings emitted", spellings)


def test_the_alias_free_twin_of_every_class_admits_the_same_set_so_nothing_is_approximated() -> None:
    """The aliases change no accepted set, shown by BUILDING both classes from one decl.

    ``docs/plan/final-state.md`` reading 10: "an enum alias is a NAME and never a second
    member ... no value set widened, and no ``approximated`` fact arising".  The second
    half is a claim about §2's ladder and cannot be read off a count that happens not to
    have moved, so it is asserted as an EQUIVALENCE: one :class:`ir.EnumDecl`, rendered
    twice -- once as the emitter renders it and once with every ``alias`` stripped -- both
    executed, and the two classes compared on the three things an accepted set is made of.

    * ``__members__`` -- the names a consumer can reach;
    * ``_value2member_map_`` -- the values the runtime admits;
    * and the JSON Schema **pydantic** renders for the annotation, which is what §8's
      comparison grades and what a widening would have to show up in.

    **And the aliases are rendered by the RENDERER, which this exercises directly**, so a
    perturbation of ``codegen/render.py`` reaches this test without the tree being
    rewritten: the only textual difference between the two renderings must be the alias
    lines themselves, asserted by stripping them and comparing the remainder.

    The other half of the sentence is the compile's own record: no approximation is
    declared at an enum node at all, so there is no fact for an alias to have arisen
    beside.
    """
    graded = _aliased()
    assert graded, "no enum class was graded"

    checked = 0
    for document, cls, aliases, _ in graded:
        canonical = {canon: alias for alias, canon in aliases.items()}
        kind = lower_enum.BASES[type(next(iter(cls))._value_).__name__]
        decl = ir.EnumDecl(
            name=cls.__name__,
            kind=kind,
            members=tuple(
                ir.Member(name=m._name_, value=m._value_, alias=canonical.get(m._name_))
                for m in cls
            ),
        )
        bare = replace(
            decl, members=tuple(replace(m, alias=None) for m in decl.members)
        )
        with_aliases, without = render.enum(decl), render.enum(bare)

        # The TEXT: the alias lines, and a TRAILING BLANK the template's own rule adds --
        # declared by :func:`test_a_described_last_member_gains_the_blank_line_the_template_already_gives_every_other`
        # and by no other difference.
        kept = [
            line
            for line in with_aliases.text.splitlines()
            if f" = {render.MEMBER_ALIAS[1]}(" not in line
        ]
        assert len(with_aliases.text.splitlines()) - len(kept) == len(aliases)
        assert _trimmed(kept) == _trimmed(without.text.splitlines()), (document, cls.__name__)
        assert all(not line.strip() for line in kept[len(_trimmed(kept)) :])
        assert (render.MEMBER_ALIAS in with_aliases.imports) is bool(aliases)

        # The SETS: built, not read.
        built = {}
        for label, rendered in (("aliased", with_aliases), ("bare", without)):
            scope: dict[str, Any] = {
                "StrEnum": pyenum.StrEnum,
                "IntEnum": pyenum.IntEnum,
                render.MEMBER_ALIAS[1]: MemberAlias,
            }
            exec(compile(rendered.text, f"<{label}>", "exec"), scope)  # noqa: S102
            built[label] = scope[cls.__name__]
        one, two = built["aliased"], built["bare"]
        assert set(one.__members__) == set(two.__members__), (document, cls.__name__)
        assert len(one.__members__) == len(two.__members__), (document, cls.__name__)
        assert set(one._value2member_map_) == set(two._value2member_map_)
        assert TypeAdapter(one).json_schema() == TypeAdapter(two).json_schema(), (
            document,
            cls.__name__,
        )
        checked += 1
    assert checked == len(graded)

    # And the other half: §2's ladder is not spent at an enum node, so no fact of one can
    # have been approximated by an alias beside it.
    out = compiled(BUNDLE, population())
    enum_pointers = {
        (document, pointer)
        for document in sorted(out.emitted)
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document))
        if isinstance(node.get("enum"), list) and node["enum"]
    }
    assert enum_pointers, "no enum node was reached"
    declared = {
        (document, record.pointer)
        for document, records in out.approximations.items()
        for record in records
    }
    assert not declared & enum_pointers, sorted(declared & enum_pointers)


def test_a_described_last_member_gains_the_blank_line_the_template_already_gives_every_other() -> None:
    """**THE ONE BYTE OF THE ARTIFACT THIS ROW MOVES THAT IS NOT AN ALIAS LINE, DECLARED.**

    ``docs/plan/architecture.md`` §14's preamble: a *bytes* mark forbids an UNDECLARED
    change.  Regenerating the tree under this row writes **4,224 lines and deletes 450**,
    and all of it is accounted for: **3,514** alias lines, **450** rewritten
    ``from adcp.types._base import …`` lines, and **260** BLANK ones.  The blank ones are
    this test's subject.

    ``Enum.jinja2``'s member docstring carries ``{%- if
    field.use_inline_field_description and not loop.last %}``, so every described member
    but the LAST is followed by a blank line and the last one is not.  An alias rendered
    beside its member means a described last member is no longer last, so it gains the
    blank line all of its siblings already had -- in **260 of the 751 emitted
    enumerations**, two lines each, which is the whole of the 260.

    **Not worked around, because every way of removing it is worse than declaring it.**
    Rendering the alias BEFORE its member would keep the byte and put a second spelling
    above the member it spells; appending the aliases in a trailing block moves the blank
    line and does not remove it; and suppressing the docstring slot would drop 1,151
    ``enumDescriptions`` entries to save whitespace.  So it is asserted here, as the exact
    text, over a probe that carries a description -- which the population check next door
    cannot do, because a member docstring is a class-body statement and not a runtime
    attribute of an ``Enum`` member.
    """
    members = (
        ir.Member(name="OPERATOR", value="operator", alias="operator", description="one"),
        ir.Member(name="BRAND", value="brand", alias="brand", description="two"),
    )
    decl = ir.EnumDecl(name="AccountScope", kind="string", members=members)
    bare = replace(decl, members=tuple(replace(m, alias=None) for m in members))

    assert render.enum(bare).text.splitlines() == [
        "class AccountScope(StrEnum):",
        "    OPERATOR = 'operator'",
        '    """one"""',
        "",
        "",
        "    BRAND = 'brand'",
        '    """two"""',
    ]
    assert render.enum(decl).text.splitlines() == [
        "class AccountScope(StrEnum):",
        "    OPERATOR = 'operator'",
        '    """one"""',
        "",
        "",
        "    operator = MemberAlias('OPERATOR')",
        "    BRAND = 'brand'",
        '    """two"""',
        "",
        "",
        "    brand = MemberAlias('BRAND')",
    ]

    # An UNDESCRIBED last member gains nothing, which is why the figure is 260 and not 751.
    plain = replace(
        decl, members=tuple(replace(m, description=None) for m in members)
    )
    assert render.enum(plain).text.splitlines() == [
        "class AccountScope(StrEnum):",
        "    OPERATOR = 'operator'",
        "    operator = MemberAlias('OPERATOR')",
        "    BRAND = 'brand'",
        "    brand = MemberAlias('BRAND')",
    ]


# --------------------------------------------------------------------------- #
# the refusals, counted
# --------------------------------------------------------------------------- #
def test_every_refusal_class_is_counted_and_named_in_the_bundle() -> None:
    """Reading 10: "reported with their counts, not silently skipped".

    **The counts PARTITION the member set**, which is what makes them a report rather than
    a tally: every member spelling of every emitted enum is either emitted as an alias or
    refused under exactly one of :data:`codegen.lower.enum.ALIAS_REFUSALS`, and the two
    halves sum to ``__members__``.  A fifth reason added to the compiler without a fifth
    entry here would break the partition rather than hide in it.

    **Each class is named at a real case of the bundle**, asserted non-empty, with the one
    exception the reading's own wording reaches:

    * ``NOT_AN_IDENTIFIER`` -- ``'dark-bg'``, and the four KEYWORD values (``'pass'``
      three times and ``'global'`` once) that make ``keyword.iskeyword`` a live branch
      beside a naming that does not upper-case.  Emitting those four would have produced
      four modules that do not PARSE.
    * ``IS_THE_CANONICAL_NAME`` -- ``'GET'``, where the value already IS the ``UPPER_SNAKE``
      spelling, so no alias is needed or possible and no migration entry is owed:
      ``Method.GET`` is the attribute on both packages.
    * ``TAKEN_BY_THE_BASE`` -- ``'name'``, the fourth class, which reading 10 does not name
      and the measurement added.
    * ``RE_CASES`` is **EMPTY inside every emitted class, and that is a theorem rather than
      a figure that could move** -- see :data:`codegen.lower.enum.ALIAS_REFUSALS`.  So the
      bundle's one re-casing collision is named where it actually lives: at the NODE, where
      ``formats/canonical/html5.json#/properties/clicktag_macro`` states ``clickTag`` and
      ``clickTAG``, §5's row renders a ``Literal`` and no enum class, and BOTH spellings
      are ones upstream has as members and this tree has as neither.  The clause is
      asserted here, over the bundle, so the day a second such node appears the count moves
      in a test that says what it costs.
    """
    graded = _aliased()
    assert graded, "no enum class was graded"

    #: Each member spelling as the triple that identifies it -- the module the class is
    #: DECLARED in, the class, and the canonical member -- so the partition is over the
    #: spellings themselves and not over four numbers that happen to add up.
    #: ``nodeset.partitions``'s own docstring is why: "two sets whose sizes sum correctly
    #: can still both miss a member and double-count another".
    whole: set[tuple[str, str, str]] = set()
    emitted: set[tuple[str, str, str]] = set()
    refusals: dict[str, set[tuple[str, str, str]]] = {
        why: set() for why in lower_enum.ALIAS_REFUSALS
    }
    named: dict[str, set[Any]] = {why: set() for why in lower_enum.ALIAS_REFUSALS}
    for _, cls, aliases, refused in graded:
        whole |= {(cls.__module__, cls.__name__, name) for name in cls.__members__}
        emitted |= {(cls.__module__, cls.__name__, canon) for canon in aliases.values()}
        for canon, why in refused.items():
            refusals[why].add((cls.__module__, cls.__name__, canon))
            named[why].add(cls[canon]._value_)

    # THE PARTITION: every member spelling is emitted or refused, under exactly one reason.
    partitions(whole, emitted=emitted, **{f"refused: {w}": r for w, r in refusals.items()})
    counts = {why: len(rows) for why, rows in refusals.items()}
    assert len(emitted) + sum(counts.values()) == len(whole), (len(emitted), counts, len(whole))

    # Each class, named at a case of the bundle.  ``RE_CASES`` is the theorem; the other
    # three are asserted non-empty and spelled.
    assert "dark-bg" in named[lower_enum.NOT_AN_IDENTIFIER]
    assert {"pass", "global"} <= named[lower_enum.NOT_AN_IDENTIFIER]
    assert "GET" in named[lower_enum.IS_THE_CANONICAL_NAME]
    assert {"name", "value"} <= named[lower_enum.TAKEN_BY_THE_BASE]
    assert "name" in MEMBER_NAMES_TAKEN and "value" in MEMBER_NAMES_TAKEN
    assert counts[lower_enum.RE_CASES] == 0, sorted(refusals[lower_enum.RE_CASES])

    # A KEYWORD is what ``str.isidentifier`` admits and a class body does not, which is the
    # whole reason the first test is not ``isidentifier`` alone.  Proved by compiling it.
    for word in ("pass", "global"):
        with pytest.raises(SyntaxError):
            compile(f"class X:\n    {word} = 1\n", "<probe>", "exec")

    # ``RE_CASES`` at the NODE, over the bundle, with what it costs.
    colliding = [
        (document, pointer, tuple(node["enum"]))
        for document in sorted(bundle.portable(BUNDLE))
        for pointer, node in bundle.nodes(bundle.read(BUNDLE, document))
        if isinstance(node.get("enum"), list)
        and node["enum"]
        and len({lower_enum.member_name(v) for v in node["enum"]}) != len(node["enum"])
    ]
    assert colliding == [
        ("formats/canonical/html5.json", "/properties/clicktag_macro", ("clickTag", "clickTAG"))
    ], colliding
    # And the node mints no member name at all, so neither spelling is in the tree.
    assert not any(
        "clickTag" in _descriptors(cls) or "clickTAG" in _descriptors(cls)
        for _, cls, _, _ in graded
    )


def test_the_migration_guide_owes_an_entry_for_each_spelling_upstream_has_and_this_tree_does_not() -> None:
    """Reading 10's pair rule: "a member upstream spells and we cannot is a migration-guide
    entry".

    **Two of the four classes owe one and two do not**, which is the whole content of the
    check and is why the entries are not one paragraph:

    * ``NOT_AN_IDENTIFIER`` and ``TAKEN_BY_THE_BASE`` owe one -- the value is not an
      attribute of ours, so a caller who wrote ``Background.dark_bg`` against upstream has
      to write ``Background.DARK_BG`` or ``Background('dark-bg')`` here;
    * ``RE_CASES`` owes one at the NODE -- there is no class, so BOTH spellings are gone and
      the value is reached as a ``str``;
    * ``IS_THE_CANONICAL_NAME`` owes NOTHING, because the spelling upstream has is the one
      this tree has: the value already IS the ``UPPER_SNAKE`` name.

    The document is read and the refusal WORDS are required to appear in it, so a reason
    added to the compiler and not to the guide reddens here.  The words are the compiler's
    own constants rather than prose quoted twice.
    """
    guide = Path(__file__).resolve().parents[1] / "docs" / "migration-from-upstream.md"
    assert guide.exists(), guide
    text = guide.read_text()

    for why in (
        lower_enum.NOT_AN_IDENTIFIER,
        lower_enum.RE_CASES,
        lower_enum.TAKEN_BY_THE_BASE,
    ):
        assert why in text, why
    # The one that owes nothing is SAID to owe nothing, by name, so a reader does not have
    # to infer it from an absence.
    assert lower_enum.IS_THE_CANONICAL_NAME in text

    # The three named cases, each spelled in the guide as a caller meets it.
    for spelling in ("dark-bg", "clickTag", "Recovery.transient"):
        assert spelling in text, spelling


# --------------------------------------------------------------------------- #
# where the alias lives: the class body of the artifact
# --------------------------------------------------------------------------- #
def test_the_spelling_is_a_class_body_statement_of_the_artifact_and_not_a_runtime_walk() -> None:
    """Reading 8: the wheel is the ARTIFACT, so the alias is in the emitted text.

    ``adcp-client-python-4yk8``: "EMITTED in the class body, never installed at runtime ...
    your INTERNALERROR on ``tests/fresh.py::_bound`` is the evidence, not an
    inconvenience", and "a runtime walk and an emitted member are two mechanisms for one
    fact".  An alias that exists because an import had a side effect is a property of
    having RUN: a consumer's type checker cannot see it, and binding it eagerly bound
    ``adcp.types._schemas`` while ``adcp.types``'s own body was still running.

    So three claims, all over the fresh run's own TEXT:

    * every spelling is an ``ast.Assign`` INSIDE the ``ClassDef`` of its enumeration --
      not a module-level ``Cls.alias = Cls.CANONICAL`` line, which is the same ``setattr``
      by another spelling and is invisible to a checker;
    * the count of those statements equals the count of descriptors the namespace carries,
      so no spelling reaches the class by any other route;
    * and no module of the tree performs the walk: no ``pkgutil``, no ``walk_packages``,
      no ``setattr``, and no import of a drop-in module.
    """
    graded = _aliased()
    assert graded, "no enum class was graded"

    #: **Asserted non-empty FIRST, because this check's loop skips a class with no
    #: spelling** -- and an emitter that writes none would otherwise satisfy every
    #: assertion below by reaching none of them.  Measured: the perturbation that renders
    #: the alias as a plain ``transient = 'transient'`` reddens four tests of this file and
    #: left this one green until this line existed.
    in_class_body: set[tuple[str, str, str]] = set()
    for _, cls, aliases, _ in graded:
        in_class_body |= {(cls.__module__, cls.__name__, a) for a in aliases}
    claimed("spellings the emitter decided for the class body", in_class_body)

    #: **Keyed on the DECIDED set and not on what the text happens to hold**, so an
    #: emitter writing nothing fails the arithmetic rather than skipping the loop: the
    #: per-class comparison is against the compiler's own decision, and the namespace is
    #: compared to the same decision beside it.
    decided = {(cls.__module__, cls.__name__): a for _, cls, a, _ in graded}
    in_body: set[tuple[str, str, str]] = set()
    for document, source, cls in emitted_enum_classes():
        wanted = decided[(cls.__module__, cls.__name__)]
        tree = ast.parse(source)
        found = {
            target.id: statement.value.args[0].value
            for klass in ast.walk(tree)
            if isinstance(klass, ast.ClassDef) and klass.name == cls.__name__
            for statement in klass.body
            if isinstance(statement, ast.Assign)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == render.MEMBER_ALIAS[1]
            for target in statement.targets
            if isinstance(target, ast.Name)
        }
        assert found == wanted, (document, cls.__name__, found, wanted)
        assert found == _descriptors(cls), (document, cls.__name__)
        in_body |= {(cls.__module__, cls.__name__, name) for name in found}

    assert in_body == in_class_body, len(in_class_body - in_body)

    #: No module of the tree installs a spelling at import time, by any spelling of it.
    for document, source, _ in emitted_enum_classes():
        for word in ("pkgutil", "walk_packages", "setattr", "_dropin"):
            assert word not in source, (document, word)
