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
# the SANITISER: the word that cost 159 files
# --------------------------------------------------------------------------- #
def test_every_value_that_is_not_already_an_identifier_resolves_under_its_sanitised_spelling() -> (
    None
):
    """**THE ROW'S WHOLE CLAIM, over every value the verbatim rule could not reach.**

    ``docs/plan/final-state.md`` reading 10: "'the derived spelling' is NOT 'the value
    verbatim', which is the word that cost 159 files.  Where the value is not already an
    identifier -- a kebab value like ``media-buy`` -- upstream does not refuse it, it
    SANITISES it to ``media_buy`` and ships that."

    So the population is exactly the values the predecessor rule REFUSED -- every string
    enum value of the tree that ``str.isidentifier`` rejects -- and over that population
    the claim is an identity:

    * the sanitiser derives a spelling for EVERY one of them (``None`` is a non-string's
      signature and nothing a string reaches), so the class of values with no derivable
      identifier holds no string at all;
    * that spelling RESOLVES on the class and ``is`` the canonical member -- whether it
      got there as a descriptor or because the sanitiser landed on the canonical name
      itself, which is the only two outcomes the refusal classes leave;
    * and it resolves by ``is`` and never by ``==``: a ``StrEnum`` satisfies ``==``
      against a bare string, and a SECOND MEMBER carrying the same value satisfies it too
      -- which is the mechanism this row refuses.

    The one exception is NAMED and is the fourth refusal class: a spelling the enumeration
    itself already resolves (``name``, ``value``, ``count``) resolves to the LANGUAGE's
    attribute, and asserting it is not the member is what keeps that class honest rather
    than letting it pass as a success.
    """
    graded = _aliased()
    assert graded, "no enum class was graded"

    #: The values the predecessor rule refused, as the triple that identifies each one --
    #: asserted non-empty FIRST, because every claim below is inside this loop.
    not_already_identifiers: set[tuple[str, str, str]] = set()
    for _, cls, _, _ in graded:
        not_already_identifiers |= {
            (cls.__module__, cls.__name__, name)
            for name, member in cls.__members__.items()
            if isinstance(member._value_, str) and not member._value_.isidentifier()
        }
    claimed("values that are not already python identifiers", not_already_identifiers)

    #: A SET and not a counter, for :func:`emitted_enum_classes`'s own reason: D3's content
    #: dedup binds one class under two or three names in its defining module, so
    #: ``vars(module)`` yields the same class object more than once and a count would
    #: exceed the population it is compared against.  Measured: 234 visits, 231 spellings.
    checked: set[tuple[str, str, str]] = set()
    for document, cls, _, refused in graded:
        for name, member in cls.__members__.items():
            value = member._value_
            if not isinstance(value, str) or value.isidentifier():
                continue
            spelling = lower_enum.their_spelling(value)
            assert spelling is not None, (document, cls.__name__, value)
            assert spelling.isidentifier(), (document, cls.__name__, value, spelling)
            if refused.get(name) == lower_enum.TAKEN_BY_THE_BASE:
                # The fourth class: the spelling reaches the LANGUAGE's attribute, and the
                # whole reason it is refused is that it would shadow it.
                assert spelling in MEMBER_NAMES_TAKEN, (document, cls.__name__, spelling)
                assert getattr(cls, spelling) is not member, (document, cls.__name__, spelling)
            else:
                assert refused.get(name) in (None, lower_enum.IS_THE_CANONICAL_NAME), (
                    document,
                    cls.__name__,
                    value,
                    refused.get(name),
                )
                assert getattr(cls, spelling) is member, (document, cls.__name__, value)
                assert cls(value) is member, (document, cls.__name__, value)
            checked.add((cls.__module__, cls.__name__, name))
    assert checked == not_already_identifiers, len(checked ^ not_already_identifiers)

    # AND ``None`` IS THE NON-STRING'S SIGNATURE AND NOTHING ELSE, which is the half of
    # :func:`codegen.lower.enum.their_spelling`'s clause 4 that a loop over the bundle
    # cannot show: asserted over the derivation directly.
    assert lower_enum.their_spelling(42) is None
    assert lower_enum.their_spelling(True) is None
    for value in ("", "---", "1.0", "_x", "pass", "media-buy", "text/plain", "4:2:0"):
        derived = lower_enum.their_spelling(value)
        assert derived is not None and derived.isidentifier(), (value, derived)


def test_the_member_set_is_unmoved_three_ways_with_the_sanitised_spellings_emitted() -> None:
    """``__members__`` does not move, and the three readings are read SUMMED.

    ``adcp-client-python-4yk8``'s invariant, re-stated for the sanitiser: ``sum
    len(__members__)`` over every emitted enumeration read the same figure before and
    after the aliases landed, and it must read the same figure after the spelling they are
    emitted UNDER changes.  Adding 236 sanitised spellings adds 236 names and no members.

    **Three readings and not one, because each one is a different way the claim could be
    false**, and the sum is taken over the whole population so a class that gained a
    member cannot be cancelled by one that lost one:

    * ``__members__`` -- the mapping a consumer reads and ``tests/test_enum.py``'s census
      reads.  A plain ``dark_bg = 'dark-bg'`` beside ``DARK_BG`` is python's own enum
      aliasing and puts the second name HERE;
    * ``list(E)`` -- ``__iter__``, which SKIPS an alias, so a spelling that became a member
      python treats as an alias shows up as a difference between this and the first;
    * ``_value2member_map_`` -- the map the runtime dispatches a value through.  A
      spelling carrying a value of its own would widen the accepted set, and this is the
      reading that would show it.

    All three equal the number of VALUES the documents state, which is the figure none of
    the three can be compared against each other to establish.
    """
    graded = _aliased()
    assert graded, "no enum class was graded"

    members = sum(len(cls.__members__) for _, cls, _, _ in graded)
    listed = sum(len(list(cls)) for _, cls, _, _ in graded)
    values = sum(len(cls._value2member_map_) for _, cls, _, _ in graded)
    stated = sum(len({v for _, v in _members(cls)}) for _, cls, _, _ in graded)
    assert members == listed == values == stated, (members, listed, values, stated)

    # And the spellings are a NON-EMPTY addition that moved none of it, which is what
    # makes the equality above a statement about this row rather than about an empty set.
    spellings = sum(len(aliases) for _, _, aliases, _ in graded)
    sanitised = sum(
        1
        for _, cls, aliases, _ in graded
        for alias, canon in aliases.items()
        if alias != cls[canon]._value_
    )
    assert spellings > 0 and sanitised > 0, (spellings, sanitised)
    #: NOT also over ``_value2member_map_``, and the asymmetry is the point: that map is
    #: keyed by VALUE, and a VERBATIM spelling IS its member's value -- ``'transient'`` is
    #: a key there by construction and says nothing about a name.  The claim is over
    #: ``__members__``, which is keyed by NAME and is where a plain assignment would land.
    assert not any(
        alias in cls.__members__ for _, cls, aliases, _ in graded for alias in aliases
    )


def test_the_kebab_case_is_covered_by_the_bundle_values_that_held_159_files_at_zero() -> None:
    """**THE KEBAB CASE, named at the documents that state it and at the four clauses.**

    ``adcp-client-python-tuuc``: "this exact gap held 159 of upstream's behavioural files
    at ZERO.  ``alias_enum_members`` asked ``value.isidentifier()``, the bundle is
    kebab-case, so ``AdcpProtocol.media_buy`` never resolved -- and ``webhooks.py:92``
    reads that member AT MODULE SCOPE, so every one of those files aborted at pytest
    startup."

    So the values are read OUT OF THE BUNDLE, by document and pointer, and the attribute
    asserted is the one a consumer of upstream's package types:

    * ``enums/adcp-protocol.json`` states ``media-buy`` -> ``AdCPProtocol.media_buy``;
    * ``brand.json#/definitions/logo/properties/background`` states ``dark-bg`` ->
      ``Background.dark_bg``;
    * ``brand.json#/definitions/logo_placement/properties/preferred_position`` states
      ``top-left`` -> ``PreferredPosition.top_left``;
    * ``brand.json#/definitions/logo/properties/variant`` states ``full-lockup`` ->
      ``LogoVariant.full_lockup``.

    Each is the spelling upstream's own 9.6.1 wheel carries (``media_buy = 'media-buy'`` in
    ``adcp/types/domains/enums/adcp_protocol.py``, ``dark_bg = 'dark-bg'`` and
    ``full_lockup = 'full-lockup'`` in ``adcp/types/domains/brand_discovery.py``), so the
    assertion is against THEIR artifact and not against our own derivation read twice.

    **And then over every kebab value of the whole tree**, so the four named cases are
    examples of a property and not the property itself.
    """
    #: ``(document, pointer, value, class, attribute)`` -- the value is read off the
    #: bundle and the attribute is upstream's, quoted from their wheel.
    cases = [
        ("enums/adcp-protocol.json", None, "media-buy", "AdCPProtocol", "media_buy"),
        (
            "brand.json",
            "/definitions/logo/properties/background",
            "dark-bg",
            "Background",
            "dark_bg",
        ),
        (
            "brand.json",
            "/definitions/logo_placement/properties/preferred_position",
            "top-left",
            "PreferredPosition",
            "top_left",
        ),
        (
            "brand.json",
            "/definitions/logo/properties/variant",
            "full-lockup",
            "LogoVariant",
            "full_lockup",
        ),
    ]
    classes = {cls.__name__: cls for _, _, cls in emitted_enum_classes()}
    for document, pointer, value, name, attribute in cases:
        nodes = dict(bundle.nodes(bundle.read(BUNDLE, document)))
        node = nodes[pointer] if pointer is not None else bundle.read(BUNDLE, document)
        assert value in node["enum"], (document, pointer, value, node.get("enum"))
        assert lower_enum.their_spelling(value) == attribute, (value, attribute)
        cls = classes[name]
        assert getattr(cls, attribute) is cls[lower_enum.member_name(value)], (name, attribute)
        assert attribute not in cls.__members__, (name, attribute)

    # EVERY kebab value of the tree, which is the property the four cases illustrate.
    kebab: set[tuple[str, str, str]] = set()
    for document, cls, _, refused in _aliased():
        for name, member in cls.__members__.items():
            if not isinstance(member._value_, str) or "-" not in member._value_:
                continue
            kebab.add((cls.__module__, cls.__name__, name))
            spelling = lower_enum.their_spelling(member._value_)
            assert spelling is not None and "-" not in spelling
            assert getattr(cls, spelling) is member, (document, cls.__name__, member._value_)
            # No kebab value is refused for want of an identifier any more, which is the
            # ruling this row corrected: a transformation was named as a refusal.
            assert refused.get(name) != lower_enum.NO_SPELLING_DERIVES, (
                document,
                cls.__name__,
                member._value_,
            )
    claimed("kebab member values of the emitted tree", kebab)


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

    * ``NO_SPELLING_DERIVES`` -- the INTEGER values, and after this row's re-partition
      nothing else.  Its predecessor class was ``not a python identifier``, asked of the
      value VERBATIM, and most of what it held was kebab that upstream's sanitiser
      handles: ``'dark-bg'`` and the four KEYWORD values (``'pass'`` three times and
      ``'global'`` once) are now EMITTED, under ``dark_bg`` and ``pass_``/``global_``,
      which is what upstream's wheel carries.  Asserted here from both sides -- the
      values this class holds are non-strings, and the five named values are not in it.
    * ``IS_THE_CANONICAL_NAME`` -- ``'GET'``, where the value already IS the ``UPPER_SNAKE``
      spelling, so no alias is needed or possible and no migration entry is owed:
      ``Method.GET`` is the attribute on both packages.  And ``'HMAC-SHA256'``, which this
      row MOVED here: it is kebab, so the verbatim rule refused it, and its sanitised
      spelling ``HMAC_SHA256`` is exactly the canonical member -- so upstream's attribute
      and ours are the same word and nothing is owed for it either.
    * ``TAKEN_BY_THE_BASE`` -- ``'name'``, the fourth class, which reading 10 does not name
      and the measurement added.
    * ``RE_CASES`` is **EMPTY over this bundle, and this row took away the argument that
      made it a theorem** -- see :data:`codegen.lower.enum.ALIAS_REFUSALS`.  While the
      alias was the value verbatim, a collision forced the two members to spell one
      CANONICAL name, which §5's row has already sent to a ``Literal``; the sanitiser and
      :func:`codegen.lower.enum.member_name` no longer agree on the character test, so the
      emptiness is now MEASURED.  The bundle's one same-canonical-name collision is still
      named where it lives: at the NODE, where
      ``formats/canonical/html5.json#/properties/clicktag_macro`` states ``clickTag`` and
      ``clickTAG``, §5's row renders a ``Literal`` and no enum class, and BOTH spellings
      are ones upstream has as members and this tree has as neither.  The clause is
      asserted here, over the bundle, so the day a second such node appears the count moves
      in a test that says what it costs.

    **AND THE EMITTED HALF IS SPLIT IN TWO**, which is the other half of the
    re-partition: a spelling that is the value VERBATIM owed nothing before this row, and
    a spelling that is the SANITISER's output is the one that did not exist.  Both are in
    the partition, so the 236 cannot grow or shrink without this test saying so.
    """
    graded = _aliased()
    assert graded, "no enum class was graded"

    #: Each member spelling as the triple that identifies it -- the module the class is
    #: DECLARED in, the class, and the canonical member -- so the partition is over the
    #: spellings themselves and not over four numbers that happen to add up.
    #: ``nodeset.partitions``'s own docstring is why: "two sets whose sizes sum correctly
    #: can still both miss a member and double-count another".
    whole: set[tuple[str, str, str]] = set()
    verbatim: set[tuple[str, str, str]] = set()
    sanitised: set[tuple[str, str, str]] = set()
    refusals: dict[str, set[tuple[str, str, str]]] = {
        why: set() for why in lower_enum.ALIAS_REFUSALS
    }
    named: dict[str, set[Any]] = {why: set() for why in lower_enum.ALIAS_REFUSALS}
    spelled_by_the_sanitiser: set[Any] = set()
    for _, cls, aliases, refused in graded:
        whole |= {(cls.__module__, cls.__name__, name) for name in cls.__members__}
        for alias, canon in aliases.items():
            row = (cls.__module__, cls.__name__, canon)
            if alias == cls[canon]._value_:
                verbatim.add(row)
            else:
                sanitised.add(row)
                spelled_by_the_sanitiser.add(cls[canon]._value_)
        for canon, why in refused.items():
            refusals[why].add((cls.__module__, cls.__name__, canon))
            named[why].add(cls[canon]._value_)

    # THE PARTITION: every member spelling is emitted -- verbatim or sanitised -- or
    # refused under exactly one reason.  SIX parts, which is this row's re-partition: the
    # emitted half splits because the sanitised spelling is the one that did not exist,
    # and a class changing size without this statement changing breaks the gate.
    partitions(
        whole,
        emitted_verbatim=verbatim,
        emitted_under_the_sanitised_spelling=sanitised,
        **{f"refused: {w}": r for w, r in refusals.items()},
    )
    counts = {why: len(rows) for why, rows in refusals.items()}
    assert len(verbatim) + len(sanitised) + sum(counts.values()) == len(whole), (
        len(verbatim),
        len(sanitised),
        counts,
        len(whole),
    )

    # Each class, named at a case of the bundle.  ``RE_CASES`` is measured empty; the other
    # three are asserted non-empty and spelled.
    assert all(not isinstance(v, str) for v in named[lower_enum.NO_SPELLING_DERIVES]), sorted(
        map(repr, named[lower_enum.NO_SPELLING_DERIVES])
    )
    assert named[lower_enum.NO_SPELLING_DERIVES], "the integer members are the class"
    # AND THE VALUES THE PREDECESSOR CLASS HELD ARE EMITTED NOW, not refused anywhere:
    # the whole content of this row read off the refusal side.
    rescued = {"dark-bg", "top-left", "full-lockup", "media-buy", "pass", "global"}
    assert rescued <= spelled_by_the_sanitiser, sorted(rescued - spelled_by_the_sanitiser)
    for why in lower_enum.ALIAS_REFUSALS:
        assert not rescued & named[why], (why, sorted(rescued & named[why]))

    assert "GET" in named[lower_enum.IS_THE_CANONICAL_NAME]
    # Kebab, and its sanitised spelling IS the canonical member -- so it moved HERE out of
    # the predecessor class rather than into the emitted half.
    assert "HMAC-SHA256" in named[lower_enum.IS_THE_CANONICAL_NAME]
    assert lower_enum.their_spelling("HMAC-SHA256") == lower_enum.member_name("HMAC-SHA256")
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

    * ``NO_SPELLING_DERIVES`` and ``TAKEN_BY_THE_BASE`` owe one -- the value reaches no
      attribute of ours, so a caller who wrote ``Kind.name`` against upstream has to write
      ``Kind.NAME`` or ``Kind('name')`` here;
    * ``RE_CASES`` owes one at the NODE -- there is no class, so BOTH spellings are gone and
      the value is reached as a ``str``;
    * ``IS_THE_CANONICAL_NAME`` owes NOTHING, because the spelling upstream has is the one
      this tree has: the derived spelling already IS the ``UPPER_SNAKE`` name.

    **AND THE SANITISED SPELLING OWES AN ENTRY THAT IS NOT A REFUSAL AT ALL**, which this
    row adds: ``Background.dark_bg`` used to be an entry under "the value is not a python
    identifier" and is now an attribute this tree HAS.  A guide still carrying it as a
    refusal would send a caller to rewrite a line that works, so the guide is required to
    name the sanitised spelling as EMITTED -- the exact opposite of the entry it replaced.

    The document is read and the refusal WORDS are required to appear in it, so a reason
    added to the compiler and not to the guide reddens here.  The words are the compiler's
    own constants rather than prose quoted twice.
    """
    guide = Path(__file__).resolve().parents[1] / "docs" / "migration-from-upstream.md"
    assert guide.exists(), guide
    text = guide.read_text()

    for why in (
        lower_enum.NO_SPELLING_DERIVES,
        lower_enum.RE_CASES,
        lower_enum.TAKEN_BY_THE_BASE,
    ):
        assert why in text, why
    # The one that owes nothing is SAID to owe nothing, by name, so a reader does not have
    # to infer it from an absence.
    assert lower_enum.IS_THE_CANONICAL_NAME in text

    # The named cases, each spelled in the guide as a caller meets it.
    for spelling in ("clickTag", "Recovery.transient", "Kind.name"):
        assert spelling in text, spelling
    # **AND THE RESCUED CASE, as the attribute it now IS rather than the edit it was.**
    # ``Background.dark_bg`` is the one line of this guide this row inverts.
    assert "Background.dark_bg" in text
    assert "AdCPProtocol.media_buy" in text
    # The FOUR CLAUSES are named, because a caller who meets ``field_1_0`` or ``pass_``
    # cannot derive it from "the value verbatim" and has nowhere else to read it.
    for clause in ("field_1_0", "pass_", "media_buy", lower_enum.THEIR_PREFIX):
        assert clause in text, clause


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
