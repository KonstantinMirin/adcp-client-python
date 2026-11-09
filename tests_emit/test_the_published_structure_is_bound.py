"""Upstream's PUBLISHED word for a position no title names resolves, joined on STRUCTURE.

``codegen.structure.STRUCTURAL_IDENTITY`` is the key and this file is what grades it.  It is
the complement of ``codegen.lower.names.UPSTREAM_TITLE_CASE``: that rule DERIVES upstream's
spelling of a document ROOT from the bundle's own title and is measured at 101 of 101, and
this one cannot derive anything, because upstream's generator named a union branch leaf, an
array element and a nested model from the FIELD PATH it reached them through and numbered the
siblings it met (``Assets``, ``Assets9`` ... ``Assets28``; ``Fields``; ``Field1``).

**WHY THERE IS NO NAMING RULE HERE, MEASURED AND NOT ASSUMED** (``adcp-client-python-zwqa``).
The derivable rule for a nested name is "name it after the nearest ancestor property key,
first taker unnumbered".  Read against upstream's own emitted tree it mints 482 bindings, of
which that tree carries the word 150 times and NOT 332; and at ``Assets`` -- the one name the
whole epic turns on -- its first taker is ``AssetsItemIndividual``, the discriminator BRANCH,
and not the branch LEAF an application constructs.  So the word is READ off the tree that
published it and matched to ours by structure.

**WHAT MAKES THE 6,143 THE SIZE IT IS, AND WHY THIS FILE EXISTS AT ALL.**
``src/adcp/utils/__init__.py`` imports ``adcp.utils.format_assets`` at MODULE scope and that
module asks for ``Assets``; ``src/adcp/__init__.py`` is a PEP 562 lazy facade whose
``__getattr__`` reaches ``adcp.utils`` at attribute-access time.  So one absent word took the
whole ``adcp.utils`` package and, through the facade, every ``from adcp import <anything>``.
:func:`test_the_facade_resolves_through_the_package_the_word_took` is the funnel itself,
asserted as an import rather than as a count.

**WHAT IS ASSERTED.**  Four things, and the first two are the ones that make the rest
non-vacuous:

* the committed index is what a fresh read of upstream's revision produces, so the artifact
  cannot drift from the tree it claims to be a reading of;
* the run's record is what an INDEPENDENT reader of the run's own emitted TEXT computes --
  one notion of structure, two producers (``from_declarations`` off the IR and
  ``from_source`` off the AST), compared over every module the run wrote;
* the join BINDS the case the epic turns on, and REFUSES the four a word-keyed join gets
  wrong, by name and with the reason;
* and every bound word resolves to the same object as our own symbol, by ``is`` and by
  ``issubclass`` in both directions -- an alias is a name and never a second type.
"""

from __future__ import annotations

import collections
import importlib
import pathlib

import pytest
from compiled import compiled
from nodeset import claimed

from adcp.types._base import SchemaRef
from codegen import bundle, emit, patch, render, structure
from survey import published_structures

#: The bundle a RUN reads: the published one with the build's patch sets applied, which is
#: ``./check``'s derivation and ``tests_emit/fresh.py``'s.
BUNDLE = patch.for_build(pathlib.Path("schemas/cache/3.2"))

#: **THE CASE THE WHOLE EPIC TURNS ON, as the one pair this file states by hand.**
#: ``adcp-client-python-klsk`` measured 6,143 of upstream's 6,423 suite errors -- 96% --
#: attributable to this single absent word, two orders of magnitude beyond the next cause.
#: Upstream's ``class Assets(BaseIndividualAsset)`` carries ``item_type='individual'``,
#: ``asset_type='image'`` and ``requirements: ImageAssetRequirements``; ours is at
#: ``core/format.json#/properties/assets/items/oneOf/0/oneOf/0``.  It is NOT
#: ``AssetsItemIndividual``, which sits at ``.../oneOf/0`` and carries ``item_type`` alone --
#: the binding ``klsk`` proposed from the POINTER and which the structure refutes.
THE_CASE = ("core/format", "Assets", "IndividualImageAsset")

#: **THE FOUR A NAME-KEYED JOIN BINDS WRONGLY -- where upstream declares each, and the
#: refusal owed.**  Every one of these was reached by matching on the WORD alone and every
#: one is a different subject, so each row names the module upstream declares the word in and
#: the verdict this join must reach there.  The verdicts are three different KINDS of
#: refusal, which is the point: a single "not bound" claim would pass vacuously on a word
#: upstream never published.
#:
#: * ``GeoPostalAreas`` -- upstream's is a MODEL keyed ``US``/``GB``/``CA``/``DE``, declared
#:   in a module of their ``bundled/`` projection our tree compiles nothing from; ours is
#:   ``Annotated[list[PostalArea], ...]``, which has no element set at all.  Owed:
#:   ``outside`` -- no module of ours is that module's counterpart -- and bound NOWHERE else.
#: * ``SiCapabilities`` -- upstream's ``adcp/types/capabilities.py`` re-aliases
#:   ``get_adcp_capabilities_response``'s ``Capabilities`` under this word, and their
#:   generated tree also spells ``si-capabilities.json``'s ROOT with it.  A root is the TITLE
#:   rule's population, which binds it there by derivation (``SiCapabilities =
#:   SICapabilities``); so this join must find the word already taken.  Owed:
#:   ``ours-already``.
#: * ``Format`` at ``canonical_creative`` -- upstream DECLARES it BY HAND in a module outside
#:   their generated tree, so there is no published word at a position any document states.
#:   Owed: ``outside``.  (Their generated tree does publish ``Format`` as a NESTED word in
#:   other documents, and those are this join's business and are bound -- which is why the
#:   row is keyed on the module and not on the bare word.)
#: * ``IdentityMatchResponse`` -- no rule exists: of the 13 documents whose title carries a
#:   parenthesised qualifier upstream carries OUR spelling 9 times, and their generated tree
#:   spells this one ``IdentityMatchResponseRouterPublisher`` exactly as we do.  Owed:
#:   ``never-published`` -- the word is in no module of their generated tree, so nothing may
#:   bind it anywhere.
REFUSED_BY_STRUCTURE = {
    ("bundled/protocol/get_adcp_capabilities_response", "GeoPostalAreas"): "outside",
    ("sponsored_intelligence/si_capabilities", "SiCapabilities"): "ours-already",
    ("canonical_creative", "Format"): "outside",
    ("trusted_match/identity_match_response", "IdentityMatchResponse"): "never-published",
}


@pytest.fixture(scope="module")
def run() -> emit.Emitted:
    return compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))


@pytest.fixture(scope="module")
def minted(run: emit.Emitted) -> dict[tuple[str, str], str]:
    """``(module, upstream's word) -> our symbol``, off the RUN's own record.

    ``Emitted.restructured`` and not a second join, for the reason
    ``tests_emit/test_the_published_spelling_is_emitted.py`` reads ``Emitted.recased``: a
    second derivation is how two readings of one rule come to disagree.  The one place a
    second derivation IS wanted is
    :func:`test_the_run_s_record_is_what_a_reader_of_its_own_text_computes`, where the two
    readers of the key are compared on purpose.
    """
    return {
        (module, word): symbol
        for module, words in run.restructured.items()
        for word, symbol in words.items()
    }


def test_the_committed_index_is_a_faithful_read_of_upstream_s_own_revision() -> None:
    """``codegen/published.json`` equals a fresh read of ``2954b258b:…/domains``.

    **THE ONE ASSERTION THAT MAKES EVERY OTHER FIGURE IN THIS FILE A CLAIM ABOUT UPSTREAM'S
    ARTIFACT.**  The index is committed because the RUN cannot reach a revision of this
    repository's history -- a compiler that shelled out to git would be a compiler with git
    in its input set -- so what keeps it honest is that the suite CAN, and does: the whole
    index is re-derived here from the revision the index itself names, and compared entry
    for entry.

    It is also the fire probe for the structural notion.  Change
    ``codegen.structure.from_source`` and this reddens immediately, because the committed
    digests were taken under the old reading -- which is exactly the signal wanted: a key
    nobody regenerated the index under is a key the run is joining on by accident.
    """
    header = structure.provenance()
    fresh = published_structures.index(header["named"], pathlib.Path.cwd())
    assert fresh["revision"] == header["revision"], (
        "the index names a revision this checkout resolves differently",
        header,
        fresh["revision"],
    )
    committed = structure.published()
    claimed("published modules the index carries", committed)
    assert sorted(fresh["modules"]) == sorted(committed)
    differ = sorted(m for m in committed if fresh["modules"][m] != committed[m])
    assert not differ, (
        "the committed index disagrees with a fresh read of the revision it names; "
        f"regenerate it with `python -m survey published_structures`: {differ[:8]}"
    )


def test_the_run_s_record_is_what_a_reader_of_its_own_text_computes(run: emit.Emitted) -> None:
    """ONE notion of structure, TWO producers, compared over every module the run wrote.

    **THIS IS THE GAP THE DESIGN HAS AND THIS IS WHERE IT IS CLOSED.**  Upstream's side of
    the join is read off their published TEXT (``structure.from_source``, an AST reading) and
    ours is read off this compiler's IR (``structure.from_declarations``), because the naming
    pass runs before a module is rendered and the IR is the only thing it has.  Two readers
    of one key is an arrangement that can be quietly wrong in either of them, so the join is
    recomputed here with the AST reader on BOTH sides -- the text the run itself produced
    against the index -- and asserted equal to the run's record, module for module.

    A disagreement is reported as the three sets it can be: a module whose bindings differ, a
    word bound by one reader and not the other, and a word bound to two different symbols.
    """
    index = structure.published()
    roots = bundle.package_roots(BUNDLE)
    at = {emit.module_path(document): document for document in run.emitted}
    # §3a's shared value lists, which live in their own modules and which an enumeration's
    # members are indexes into (``structure.value_lists``).  Read over the run's WHOLE file
    # set, because the module that declares the list is not the module that uses it.
    vocabularies = structure.value_lists(
        text for name, text in sorted(run.files.items()) if name.endswith(".py")
    )
    disagree: dict[str, dict[str, object]] = {}
    for module, words in sorted(run.restructured.items()):
        text = run.files.get(f"{emit.module_file(at[module], roots)}.py")
        if text is None:
            continue
        ours = structure.from_source(text, vocabularies)
        # The ROOT is excluded from the candidates by the same reading the run used -- the
        # symbol §1 exports under the ``root`` kind, which ``Emitted.surface`` records.
        root = next((s for s, kind in run.surface.get(module, {}).items() if kind == "root"), "")
        # ``occupied`` is the rendered module's WHOLE namespace (``structure.names_bound``)
        # less this join's own statements, which is the namespace as the naming pass saw it:
        # the title rule's words are left IN, because the pass runs that rule first and
        # hands its words to this one.
        occupied = (structure.names_bound(text) | render.CARRIERS) - frozenset(words)
        again, _ = structure.bind(ours, index.get(module, {}), root, occupied)
        if again != words:
            disagree[module] = {
                "the run recorded": {k: v for k, v in words.items() if again.get(k) != v},
                "the text reads": {k: v for k, v in again.items() if words.get(k) != v},
            }
    claimed("modules whose bindings the two readers were compared on", run.restructured)
    assert not disagree, (
        "the IR reader and the AST reader of one structural key disagree -- "
        f"{structure.STRUCTURAL_IDENTITY}\n{dict(sorted(disagree.items())[:4])}"
    )


def test_the_case_the_epic_turns_on_is_bound(minted: dict[tuple[str, str], str]) -> None:
    """``Assets`` is ``IndividualImageAsset`` and the asset union does not collapse.

    Both halves, because the second is what the const values in the key are FOR: with them
    dropped, ``Assets`` reaches thirteen declarations of ours at once -- measured -- and the
    whole individual-asset union becomes one subject.  So the pair is asserted, and so is
    that each of upstream's numbered siblings reached a DIFFERENT class of ours.
    """
    module, word, ours = THE_CASE
    assert minted.get((module, word)) == ours, {
        "what the run bound": minted.get((module, word)),
        "what upstream's own tree publishes at this structure": ours,
    }
    siblings = {
        bound: word
        for (at, word), bound in minted.items()
        if at == module and word.startswith("Assets")
    }
    claimed("upstream's numbered asset siblings, by the class each reached", siblings)
    collapsed = collections.Counter(
        word for (at, word) in minted if at == module and word.startswith("Assets")
    )
    assert len(siblings) == sum(collapsed.values()), (
        "two of upstream's numbered asset words reached one class of ours, which is the "
        "const-value collapse STRUCTURAL_IDENTITY exists to prevent"
    )


def test_the_four_a_word_keyed_join_gets_wrong_are_refused(
    run: emit.Emitted, minted: dict[tuple[str, str], str]
) -> None:
    """None of :data:`REFUSED_BY_STRUCTURE` is bound, and each refusal has a REASON.

    **A REFUSAL WITH NO REASON IS AN ABSENCE AND NOT A DECISION**, so the word is required
    to be either outside this join's population -- upstream declares it nowhere in their
    generated tree, which is the whole of the answer for ``canonical_creative.Format`` and
    for ``trusted_match.IdentityMatchResponse`` -- or present in the run's ``unbound``
    record under one of ``codegen.structure.REFUSALS``.
    """
    index = structure.published()
    outcomes: dict[str, str] = {}
    for (module, word), owed in sorted(REFUSED_BY_STRUCTURE.items()):
        at = f"{module}.{word}"
        assert minted.get((module, word)) is None, (
            f"{at} was BOUND to {minted.get((module, word))}; a word key gets this one wrong"
        )
        if owed == "never-published":
            carried = sorted(m for m, words in index.items() if word in words)
            assert not carried, (
                f"{word} is now published in upstream's generated tree at {carried}, so this "
                "row's reason has changed and the verdict owed has to be re-derived"
            )
            anywhere = sorted(m for (m, w) in minted if w == word)
            assert not anywhere, f"{word} was bound at {anywhere} and upstream publishes it nowhere"
            outcomes[at] = "never-published: no module of upstream's generated tree carries it"
        elif owed == "outside":
            assert module not in run.restructured and module not in run.unbound, (
                f"our run now writes a module at {module}, so {word} is inside the population "
                "and the verdict owed has to be re-derived"
            )
            outcomes[at] = "outside: this run writes no module at that path, so nothing joins"
        else:
            assert module in index and word in index[module], (
                f"{word} is no longer declared at {module} in upstream's published tree, so "
                "this row is grading nothing"
            )
            reason = run.unbound.get(module, {}).get(word)
            assert reason == owed, {at: reason, "owed": owed}
            outcomes[at] = f"{reason}: {structure.REFUSALS[reason].split('.')[0]}"
    claimed("the four a word key binds wrongly, with the reason each is refused", outcomes)


def test_every_bound_word_is_a_word_upstream_published_at_that_module(
    run: emit.Emitted, minted: dict[tuple[str, str], str]
) -> None:
    """Nothing is bound that upstream's own module does not declare.

    The join can only propose a word the index carries, so this is a check on the WIRING and
    not on the rule: a record keyed on the wrong module, or an index entry read for a
    neighbouring document, would show up here as a word upstream published somewhere else.
    """
    index = structure.published()
    stray = sorted((module, word) for (module, word) in minted if word not in index.get(module, {}))
    assert not stray, f"bound a word upstream's own module at that path does not declare: {stray}"
    claimed("bindings upstream's published tree confirms", minted)


def test_an_upstream_word_is_a_name_and_never_a_second_type(
    run: emit.Emitted, minted: dict[tuple[str, str], str]
) -> None:
    """``is``, ``issubclass`` both ways, and one ``__adcp_schema__``: one object, two names.

    Read as BEHAVIOUR and not as text, exactly as the title rule's own gate reads it: a
    re-export written per name could still have been a second class per name, and these are
    the assertions no second class satisfies.
    """
    at: dict[str, dict[str, str]] = {}
    for (module, word), ours in minted.items():
        document = next((d for d, _ in run.emitted.items() if emit.module_path(d) == module), None)
        if document is not None:
            at.setdefault(emit.module_name(document), {})[word] = ours
    claimed("modules owed one of upstream's published words", at)
    absent: list[str] = []
    for module, words in sorted(at.items()):
        carried = importlib.import_module(module)
        for word, ours in sorted(words.items()):
            theirs, mine = getattr(carried, word, None), getattr(carried, ours, None)
            if theirs is None or mine is None:
                absent.append(f"{module}.{word}")
                continue
            assert theirs is mine, f"{module}: {word} is not {ours}"
            ref = getattr(mine, "__adcp_schema__", None)
            assert getattr(theirs, "__adcp_schema__", None) is ref
            if isinstance(ref, SchemaRef) and isinstance(mine, type):
                assert isinstance(theirs, type) and issubclass(theirs, mine)
                assert issubclass(mine, theirs)
    assert not absent, f"the run recorded these and the module does not carry them: {absent}"


def test_the_two_rules_partition_upstream_s_surface(run: emit.Emitted) -> None:
    """A word is the TITLE rule's or this join's and never both.

    The two reach upstream's surface by different keys -- a derivation from the bundle's
    title, and a join on structure -- and an overlap would mean one module writing two
    statements for one word, which the renderer would emit twice.  The join is handed the
    title rule's words in ``occupied`` precisely so that cannot happen, and this is that
    guard read off the OUTPUT rather than trusted at the call site.
    """
    both = sorted(
        (module, word)
        for module, words in run.restructured.items()
        for word in words
        if word in run.recased.get(module, {})
    )
    assert not both, f"one word claimed by both name rules: {both}"
    roots = sorted(
        (module, word)
        for module, words in run.unbound.items()
        for word, why in words.items()
        if why == "the-root's-question"
    )
    claimed("published words refused because the structure is the document ROOT's", roots)


def test_the_facade_resolves_through_the_package_the_word_took() -> None:
    """``from adcp import get_format_assets`` -- the funnel, asserted as an import.

    **THE REAL GATE, because the facade is the funnel.**  ``src/adcp/__init__.py`` is a PEP
    562 lazy facade whose ``__getattr__`` imports ``adcp.utils`` at ATTRIBUTE-ACCESS time;
    ``src/adcp/utils/__init__.py`` imports ``adcp.utils.format_assets`` at module scope; and
    that module's line 24 asks ``adcp.types.domains.core.format`` for ``Assets``.  So a
    single absent word took the whole ``adcp.utils`` package and, through the facade, every
    ``from adcp import <anything>``.  Nothing upstream wrote is edited to make this pass --
    the substitution is a DROP-IN and the word is bound on our side of the seam.
    """
    import adcp
    import adcp.utils

    assert callable(adcp.utils.get_format_assets)
    assert callable(adcp.get_format_assets)
    model = importlib.import_module("adcp.types.domains.core.format")
    assert model.Assets is model.IndividualImageAsset
