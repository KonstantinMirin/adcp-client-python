"""Reading 10's flat ALIAS arm: every upstream word the compiler recovered, exported.

**THE DEFECT.**  ``codegen/lower/names.assign`` joins upstream's published type surface onto
ours on three keys -- a title recased (``UPSTREAM_TITLE_CASE``), a structure matched
(``codegen.structure.STRUCTURAL_IDENTITY``) and a sentence upstream wrote
(``structure.bind_statements``) -- and the module it lowers STATES one ``X = <symbol>`` per
word it recovers.  862 of them over bundle 3.2.  **Not one reached a surface a consumer can
import from.**  ``protocol/get-principal-response.py`` states
``PrincipalCurrentResult = CurrentPrincipalConfiguration``, ``src/adcp/__init__.py`` lists
the word twice, and ``tests/test_principal.py`` aborted at COLLECTION on
``from adcp.types import PrincipalCurrentResult`` -- so the compiler had the answer, wrote
it into the tree, and published it nowhere.

**WHAT DECIDES WHERE THE EXPORT GOES, and it is not taste.**  ``final-state.md`` reading 10
names three layers and gives upstream's spellings to exactly one of them: "``adcp.types``
flat -- the compatibility surface: an alias for every name an application actually imports
today".  The next clause draws the boundary: "Refusing to reproduce upstream's spellings
means refusing to put one object at every module upstream happens to expose it from.  It
does not mean refusing the ONE namespace an application imports from ... One declared flat
surface is a canonical location; a name at every module that mentions it is the accident."

So the word goes on ``adcp.types._surface._flat`` -- which is what the flat facade answers
from -- and on **no** domain aggregator.  That is reading 6 being obeyed rather than an
omission, and :func:`test_no_domain_aggregator_carries_an_upstream_word` is the half of this
file that says so: 858 of the 862 statements bind a symbol ALREADY on its own module's
export set, reached at the domain under the word reading 6's inner clause minted from the
parent class and the key together (``lower/names.THE_INNER_EXPORT``).  The NAME was never
missing; the EXPORT of upstream's word was.  A second domain path to one object is what "no
second way reaches the same class" forbids outright.

**AND THE TWO REASONS TO DECLINE A WORD ARE GRADED, NOT COUNTED.**  A flat namespace has one
slot per word, so the arm declines a word the generated surface already publishes (§4
forbids us to re-word a subject the protocol named) and a word with more than one subject
(upstream's generator mints from a property KEY alone, so ``accounts`` -> ``Account`` in two
documents is one word for two distinct objects).  Reading 10: "An alias is keyed on a schema
SUBJECT, never on a name ... one flat alias cannot serve both."  A declined word is NAMED
with every subject it has -- ``__adcp_alias_declined__`` -- because a compiler that drops a
word in silence leaves the reader of a failing import nothing to read.

**THE POPULATION IS THE RUN'S OWN RECORD AND IS NOT RE-DERIVED HERE**
(:meth:`codegen.emit.Emitted.upstream_words`).  A predicate over the emitted TEXT answers
**914** rather than 862, because §4's content dedup and a root binding render the same
``X = Y`` form -- so a reading of the text cannot tell an upstream word from a position of
the document, and four measurements of this defect disagreed for exactly that reason.  The
record can, and it is the same record the arm itself reads, so the gate and the emitter
cannot disagree about which words exist.

**The tree is the FRESH one** (``tests_emit/fresh.py``), for its own reason: the committed
tree is an artifact verified by one byte-compare and is never the subject.
"""

from __future__ import annotations

import importlib

import fresh  # noqa: F401  -- imported for the conftest's binding, kept explicit here
import pytest
from compiled import compiled
from nodeset import claimed, partitions

from codegen import emit


@pytest.fixture(scope="module")
def run() -> emit.Emitted:
    """The compile every test here reads, from the shared store."""
    return compiled(fresh.BUNDLE, fresh.population())


@pytest.fixture(scope="module")
def words(run: emit.Emitted) -> dict[str, list[tuple[str, str]]]:
    """Upstream's word -> every ``(module, symbol)`` the record gives it.

    The record is keyed on the MODULE, which is how a word with two subjects is
    representable at all; this is that record inverted, which is the key the flat namespace
    is stated over.
    """
    held: dict[str, list[tuple[str, str]]] = {}
    for module, bound in sorted(run.upstream_words().items()):
        for word, symbol in sorted(bound.items()):
            held.setdefault(word, []).append((module, symbol))
    return held


@pytest.fixture(scope="module")
def flat():
    """``adcp.types._surface._flat`` of the FRESH tree, imported."""
    return importlib.import_module("adcp.types._surface._flat")


def test_every_upstream_word_is_either_bound_flat_or_declined_by_name(words, flat) -> None:
    """The arm's two outcomes PARTITION the record, so a dropped word cannot hide.

    This is the assertion the whole file turns on and it is stated as a partition rather
    than as two counts: a word in neither set is one the compiler recovered and published
    nowhere, which is the defect, and a word in both is a module that binds a name it also
    says it declined.  ``nodeset.partitions`` reports those two failures separately,
    because the arithmetic alone has been green while both were true.
    """
    every = claimed("upstream words the run's three joins recovered", words)
    partitions(
        every,
        # **A DECLINED WORD IS SUBTRACTED AND NOT INTERSECTED AWAY**, which is the one place
        # ``__all__`` cannot be read as "the arm bound this": 28 of the declined words ARE
        # in it, bound by the GENERATED surface to the class the schemas name, which is the
        # first decline reason.  Reading them as this arm's would claim a word twice and
        # would also report the arm reaching 28 words it declined.
        bound_at_the_flat_namespace=(set(flat.__all__) & every)
        - set(flat.__adcp_alias_declined__),
        declined_and_named=set(flat.__adcp_alias_declined__),
    )


def test_a_bound_word_resolves_flat_to_the_object_its_own_module_binds(words, flat) -> None:
    """``adcp.types._surface._flat.<Word>`` **is** the class the private module's statement
    binds, and ``from adcp.types import <Word>`` resolves.

    ``is`` and not merely "resolves", for reading 10's own reason: "an alias is a NAME, and
    a second object would be a second type".  The object asked for is the one the PRIVATE
    module's ``X = <symbol>`` statement binds -- the same statement the arm exported -- so a
    re-export that reached a different class of the same name would fail here while a
    resolution check passed.

    **AND THE FACADE IS ASKED SEPARATELY, BECAUSE IT IS NOT THIS ARM'S QUESTION.**
    ``adcp.types.__getattr__`` consults this module LAST, after the alias table, the
    generated adapter and the restored modules, "so nothing any of them decided is
    overridden".  A word one of those already binds therefore keeps THEIR object, which is
    the ruling and not a defect -- so what is asserted at the flat spelling is that the
    import an application wrote RESOLVES, and a word whose answer differs must come from a
    layer that is genuinely ahead of this one.  A difference no earlier layer accounts for
    is red: it would mean something shadowing the arm that nobody decided.
    """
    import adcp.types as types

    compat = importlib.import_module("adcp.types.compat")
    adapter = importlib.import_module("adcp.types._adapter")
    restored = importlib.import_module("adcp.types._restored")
    #: The layers ``adcp.types.__getattr__`` asks BEFORE this arm, as the names each decides.
    #: Read off the modules themselves rather than listed, so a layer that grows reaches this
    #: reading with nothing edited.
    ahead = (
        set(getattr(restored, "STATED", {}))
        | set(compat.__all__)
        | set(compat.__adcp_flat_only__)
        | set(adapter.__all__)
        # ``_restored`` is asked TWICE by the facade -- ``STATED`` before the table, for the
        # words upstream's own ``_eager`` binds to a restored file, and the module's whole
        # surface after the adapter.  Both are ahead of this arm, so both are here; reading
        # only the first left ``Accreditation`` and ``UpdateMediaBuyResponse2`` looking
        # unaccounted while the facade was obeying its own documented order.
        | set(restored.__all__)
    )

    bound = claimed(
        "upstream words the arm binds at the flat namespace",
        (set(flat.__all__) & set(words)) - set(flat.__adcp_alias_declined__),
        inside=words,
    )
    wrong: dict[str, str] = {}
    unresolved: list[str] = []
    for word in sorted(bound):
        module, symbol = words[word][0]
        private = importlib.import_module(f"adcp.types._schemas.{module.replace('/', '.')}")
        stated = getattr(private, word, None)
        if stated is None:
            wrong[word] = f"the private module {module} states no {word}"
            continue
        if getattr(private, symbol, None) is not stated:
            wrong[word] = f"{module}.{word} does not bind {symbol}"
            continue
        if getattr(flat, word, None) is not stated:
            wrong[word] = f"_flat.{word} is not the object {module} binds"
            continue
        answered = getattr(types, word, None)
        if answered is None:
            unresolved.append(word)
        elif answered is not stated and word not in ahead:
            wrong[word] = (
                f"adcp.types.{word} is neither this arm's object nor a word any earlier "
                "layer of the facade decides"
            )
    assert not wrong, wrong
    assert not unresolved, {
        "bound at the flat module and still raising at the spelling a consumer writes": (
            unresolved
        )
    }


def test_a_declined_word_is_named_with_every_subject_it_has(words, flat) -> None:
    """Every declined word carries its subjects, and the record agrees about which.

    The subjects are what makes the decline readable: a caller whose import raises is owed
    the pointers the word WOULD have reached, and each of those classes is reachable under
    its own ``adcp.types.<domain>`` word.  Held against the run's own record in both
    directions, so a module naming a subject the record does not give -- or omitting one it
    does -- reddens rather than reading as a shorter list.
    """
    declined = claimed(
        "upstream words the arm declines", flat.__adcp_alias_declined__, inside=words
    )
    disagrees = {
        word: {
            "the module names": sorted(flat.__adcp_alias_declined__[word]),
            "the record gives": sorted(
                f"{module.replace('/', '.')}.{symbol}" for module, symbol in words[word]
            ),
        }
        for word in sorted(declined)
        if sorted(flat.__adcp_alias_declined__[word])
        != sorted(f"{module.replace('/', '.')}.{symbol}" for module, symbol in words[word])
    }
    assert not disagrees, disagrees


def test_a_word_declined_for_two_subjects_resolves_nowhere_at_the_flat_spelling(
    words, flat
) -> None:
    """The two decline REASONS are told apart by the module's own ``__all__``, and both hold.

    A declined word that IS in ``__all__`` was declined because the generated surface
    already publishes it, and it resolves there to the class the schemas name -- which is
    the outcome §4 requires.  A declined word that is NOT must resolve nowhere at the flat
    spelling, because its subjects are distinct classes and binding either would hand a
    caller a class whose document they did not name.

    **Both arms are asserted, and the second is the one with teeth**: a first-wins pick
    would read green on the first arm alone.
    """
    import adcp.types as types

    multi = claimed(
        "words declined for having more than one subject",
        [w for w in flat.__adcp_alias_declined__ if w not in set(flat.__all__)],
        inside=words,
    )
    shadowed = claimed(
        "words declined because the generated surface already publishes them",
        [w for w in flat.__adcp_alias_declined__ if w in set(flat.__all__)],
        inside=words,
    )
    answered = {
        word: repr(getattr(flat, word))
        for word in sorted(multi)
        if getattr(flat, word, None) is not None
    }
    assert not answered, {
        "a word with more than one subject bound anyway -- a first-wins pick": answered
    }
    missing = [word for word in sorted(shadowed) if getattr(types, word, None) is None]
    assert not missing, {
        "declined to the generated surface's own word and the surface does not answer": missing
    }


def test_no_domain_aggregator_carries_an_upstream_word(words, run: emit.Emitted) -> None:
    """Reading 6 unmoved: the alias arm adds no ``adcp.types.<domain>.<Name>``.

    The class behind every one of these words already has its one domain path, under the
    word reading 6's inner clause minted from the parent class and the key together.  A
    second path to the same object in the same namespace is what that reading forbids, and
    an alias word on a domain aggregator would be exactly one -- so this is the assertion
    that keeps the arm at the layer reading 10 gives it.

    Read off the EXPORT RECORD and not off the module text, for
    :attr:`codegen.emit.Emitted.surface`'s reason; the word a domain publishes is
    ``published.get(symbol, symbol)``, which is the resolution both readers of that record
    make.
    """
    claimed("upstream words the run's three joins recovered", words)
    published: dict[str, set[str]] = {}
    for module, exported in run.surface.items():
        if not exported:
            continue
        renamed = run.published.get(module, {})
        for symbol in exported:
            published.setdefault(emit.module_domain(module), set()).add(
                renamed.get(symbol, symbol)
            )
    assert published, "no domain publishes anything -- the assertion below is vacuous"
    leaked = {
        f"{domain}.{word}": sorted(f"{m}.{s}" for m, s in words[word])
        for domain, names in sorted(published.items())
        for word in sorted(names & set(words))
        # A domain word that EQUALS an upstream word is only a leak when it is the alias
        # arm that put it there.  The §1 surface mints its own words and 28 of them happen
        # to coincide with one of upstream's -- which is the first decline reason, measured
        # -- and such a word is on the aggregator because a DOCUMENT of the domain states
        # it, which is the one path the reading wants.  The leak is a word the aggregator
        # publishes for a module the record names as the word's subject.
        if any(emit.module_domain(m) == domain and s == word for m, s in words[word])
    }
    assert not leaked, {
        "an upstream alias word published at a domain path -- reading 6's second path": leaked
    }


def test_the_rule_is_perturbed_in_both_directions_and_reddens() -> None:
    """:func:`codegen.emit._alias_words` over a record with each decline case added.

    The four tests above read a finished artifact, and an artifact can agree with a rule
    that decides nothing.  So the rule itself is called here on a record small enough to
    read: one word with one subject, one word the surface already publishes, and one word
    with two subjects.  **Both directions**: the first must bind and the other two must
    not, and a rule that bound all three or declined all three fails one of the two halves.
    """
    record = {
        "a/one": {"Unique": "TheClass", "Taken": "OtherClass", "Shared": "First"},
        "a/two": {"Shared": "Second"},
    }
    bound, declined = emit._alias_words(frozenset({"Taken"}), record)
    assert bound == {"Unique": "a.one"}, bound
    assert declined == {
        "Shared": ["a.one.First", "a.two.Second"],
        "Taken": ["a.one.OtherClass"],
    }, declined

    #: The same record with NOTHING surfaced, which is the perturbation that tells the
    #: first decline reason from a hard-coded word: ``Taken`` must come back bound.
    bound, declined = emit._alias_words(frozenset(), record)
    assert bound == {"Unique": "a.one", "Taken": "a.one"}, bound
    assert set(declined) == {"Shared"}, declined

    #: And with the second subject of ``Shared`` removed, which tells the second reason
    #: from a word blocklist: it must come back bound, and to the module that states it.
    bound, declined = emit._alias_words(frozenset({"Taken"}), {"a/one": record["a/one"]})
    assert bound == {"Unique": "a.one", "Shared": "a.one"}, bound
    assert set(declined) == {"Taken"}, declined
