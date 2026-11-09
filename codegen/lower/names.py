"""Naming and content dedup, as ONE pass over the finished module.

``docs/plan/architecture.md`` §7: **"Naming is a pass over the module, not a thread
through the walk."**  This module takes a :class:`codegen.compiler.Module` whose
declarations are keyed by POINTER and whose ``TypeRef``\\ s name local declarations by
pointer, and returns the module with a symbol table -- by §4 of
``docs/plan/rebuild-plan.md``'s rules: the root by ``pascal_case(title)``; a nested
declaration by its OWN position (``<Property>`` at PROP, ``<Property>Item`` at ELEM,
``<Property>Value`` at MAPV, ``<Root><Key>`` at DEF); a branch by its own ``title``, else
the ``const`` it pins on the discriminating property, else its sorted ``required`` set,
else its index among the branches (``<Base>Branch<i>``).

**A nested name is its own position and not the path to it, and §4's collision rule is
what pays for that** (:data:`COLLISION`, :func:`spell`).  "The module path already
carries the document, so a nested name does not repeat it" -- so two positions of one
module can derive one name, and where N do, ALL N lengthen by their own nearest ancestor
segment until every name in the module is unique.  Before the rule was written this pass
folded every hop to the root and concatenated, which cannot collide and therefore needed
no rule: 808 of 2,118 emitted classes were longer than 30 characters, 141 longer than 50,
and one was ``GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext``.
With the rule it is 235 of 2,144 over 30, the median falls from 26 characters to 17, and
2,116 of 2,226 named positions keep the one segment §4 derives.
:func:`segments` is the same readings kept as a CHAIN so that :func:`spell` can spend as
few of them as the module requires, and the chain's whole spelling is the name the fold
gave -- which is why the refusal two indistinguishable positions earn is the same
refusal, over the same documents, as before.

**The walk computes no name, and §7 reads §4's own rule strictly.**  §4 says a name is
an input to a lowering and is never computed inside one; §7 adds "read strictly, it is
not an input either: it is assigned after".  So a handler declares at a pointer and
records the HOP its child's name is derived through (:data:`Hop` below), and nothing
before this pass holds a symbol of this module's own.  Every symbol slot in the IR --
``ClassDecl.name``, ``EnumDecl.name``, ``AliasDecl.name``, ``RootBinding.symbol``,
``ClassDecl.bases``, ``ClassDecl.branches``, ``UnionInstall``, and every ``TypeRef``
marked ``local`` -- holds a POINTER until :func:`assign` runs, and a NAME after.  A
pointer is ``""`` or begins with ``/`` and a name is an identifier, so the two cannot be
mistaken for one another, and the one slot that mixes them is ``bases``: a base is
either a pointer into this module or a symbol another module declares, and :func:`assign`
resolves the pointers and leaves the symbols.

**The SCOPE of the dedup is ONE MODULE, which is one document (D1).**  §9 of the
semantics document decides it: "do not decide one document's output by a census over
the run -- a name, a shape or an import that depends on which other documents the run
includes makes a one-document emission and a whole-bundle emission disagree about the
same document."  Two documents that inline identical content therefore keep a class
each; collapsing them would need a rule for which module owns the survivor, D1 gives a
node exactly one home, and 0 of the bundle's 1,271 identical-content groups have a ROOT
carrying that content for a ``$ref`` to reach.  :data:`SCOPE` is the sentence, and the
only inputs this pass has are the module and the reserved attribute set, so the scope is
held by the signature as well as by the sentence.

**The dedup KEY is NODE EQUALITY.**  ``codegen/schema/nodes.py`` excludes ``pointer``
and ``position`` from a node's equality, so two nodes are equal exactly when they state
the same thing about an instance -- which is §4's content dedup read off the type system
rather than off a JSON serialisation with a position bit appended (``emit.content_key``,
deleted).  Measured over the memo's own population: 7,250 nodes in 677 documents, 283
groups by the deleted key and 283 by this equality, and 0 documents whose partition
differs.  **Do not reintroduce a serialisation-based key.**

**What the dedup does with a group**: §4's own sentence.  "The class is declared under
the name of the position the walk reaches first, and every later position of the same
content binds its own derived name to that class by identity, ``X = Y``."  So one class
per group, declared at the first pointer in document order, and every later pointer
binds the name ITS OWN position derives -- never a sibling position's name, which would
read as one branch carrying another's type and would make a public symbol a function of
which key the walk reached first.

**ONE refusal is this pass's, and it is a VERDICT of the document: two pointers deriving
one name.**  A branch with no identity was the second, and §4 has the fourth naming rule
that retires it (``docs/plan/architecture.md`` §13 item 7, closed 2026-10-26): a branch
with no ``title``, no pinned ``const`` and no ``required`` set takes its **index among the
branches**, ``<Base>Branch<i>``.  A name is not an acceptance fact, so the fallback
neither widens nor narrows and costs no approximation; the index is a function of the
branch's own position in its own document, so no census over the run enters and the
refusal was minting a verdict where §4 states a fallback.

**Not EVERYTHING here runs in the pass, and the reading is which calls the WALK makes.**
Four functions are the walk's: :func:`same_node` and :func:`adopt`, because a second
occurrence's children are never lowered and the pruning is a decision about the walk;
and :func:`alias_for` and :func:`name_the_node`, because the alias a ``$ref``-named node
takes carries that node's own facts and the parent's field must reference it rather than
restate it.  All four are NAMING acts -- a name bound to a declaration, at a pointer --
which is why §7 puts them beside the rules, and none of them computes a name: each
declares at a POINTER and :func:`assign` is still the one function that binds a symbol.
:func:`name_the_node` and :func:`alias_for` arrived from ``compiler.py`` at
``adcp-client-python-3be.5``, with the walk's per-node entry (``compiler.lower_node``),
which is what stopped reaching them through ``codegen.emit``.

**The index is the LAST rung and is accepted only there.**  A positional name carries
nothing about which position it names -- the upstream v9 SDK numbers 1,092 of its 4,360
classes and renames a sibling when a branch is inserted ahead of it -- so §4 reaches for
it only after the three IDENTITY rungs have each been tried and found nothing.  A document
that gives a branch no identity at all leaves nothing else, and an index at least says
WHICH branch.  :func:`branch_identity` is the one place the order is written.
"""

from __future__ import annotations

import keyword as _keyword
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from codegen import ir
from codegen.refusal import BuildFailure, Kind, Refusal
from codegen.schema import nodes

if TYPE_CHECKING:  # pragma: no cover -- the annotation only; see :func:`assign`
    from codegen.compiler import Module

#: **The stated scope of the content DEDUP, and of the dedup alone** (§14 step 7's own
#: words for this row, and §9's rule behind it).  Read by ``tests/test_emit.py``, so the
#: sentence the code states and the sentence a check grades are one string.
#:
#: **It said "the scope" until 2026-10-30 and there are two**, which is why it now names
#: which one it is.  §1's amendment widened the COLLISION rule to the domain and left the
#: dedup exactly here: two nodes are one class within one module and nowhere else, because
#: a class carries ``__adcp_schema__`` for ITS document and a second document's node is a
#: second schema reference however equal the content.  §1's own carve-out is the reading
#: from the other side -- it reaches across modules only for "a document that is a bare
#: ``$ref`` to another document", where the two nodes ARE one node.  :data:`COLLISION_SCOPE`
#: is the other scope, and a reader who confuses them would take a collision's answer (all
#: N move) for a dedup's (one class, N names bound by identity).
#:
#: The sentence is unchanged because the reason is: no census over the RUN decides a name.
#: What changed is that a bundle-wide reading was never such a census (§9's ruling, the run
#: is not the bundle), which is what :data:`COLLISION_SCOPE` spends.
SCOPE = (
    "one module, which is one document (D1): a name, a shape or an import that depended "
    "on which other documents the run includes would make a one-document emission and a "
    "whole-bundle emission disagree about the same document (section 9)"
)

#: **The stated scope of the COLLISION rule, which is wider than the dedup's and is
#: wider than one module as of 2026-10-30** (§1's amendment, and §9's ruling behind it).
#: QUOTED by the checks that grade it, so the sentence the code states and the sentence a
#: check reports against are one string.
#:
#: §4 used to close with "the resolution is also confined to one module, never compared
#: across modules, because a name's module is its namespace and §9's rule is that a
#: document's output may not depend on which other documents the run includes".  §1 now
#: forbids the other direction of the one-path rule -- no ``adcp.types.<domain>.<Name>``
#: may name two declarations -- and a domain is many modules, so the resolution reaches
#: across them for the positions the SURFACE exports.
#:
#: **§9 is kept rather than amended, and the distinction it rests on is in its own
#: ruling: the RUN is not the BUNDLE.**  The prohibition is about the run's DOCUMENT SET,
#: the argument list, which varies between a one-document command and a whole-population
#: emission.  A domain's exported names are read off the BUNDLE -- pinned, declared, an
#: input to every run alike -- so the name is the SAME in both, which is the property §9
#: protects.  :func:`assign`'s signature carries it: what crosses into this pass is a set
#: of NAMES, and nothing here can ask which documents were asked for.
COLLISION_SCOPE = (
    "one module for every position, and the DOMAIN for a position the surface exports: "
    "no adcp.types.<domain>.<Name> may name two declarations (section 1, 2026-10-30), "
    "and the domain's other exported names are read off the BUNDLE and never off the "
    "run's document set, so a one-document emission and a whole-bundle emission derive "
    "the same name (section 9's ruling, the run is not the bundle)"
)

#: **§3a STEP 3's SCOPE: a SUBJECT the bundle named is that subject's, over the whole
#: BUNDLE, against every position that would DECLARE a second type under its name.**
#: QUOTED by the checks that grade it, for :data:`COLLISION_SCOPE`'s reason.
#:
#: §3a: "A name is minted per ENTRY and never per position.  This is what makes a role
#: word claiming a subject's name impossible by construction: a position has a role, an
#: entry has a subject, and only a subject gets a name."  A property KEY is the role a
#: subobject plays in its parent, so a name derived per position can only ever know the
#: role -- which is why an untitled capabilities block keyed ``media_buy`` took the name
#: of the entity ``core/media-buy.json`` titles "Media Buy".  The subjects are read off
#: the bundle before any name is derived, so the claim is not available to be made rather
#: than being found afterwards by a census.
#:
#: **WIDER THAN THE DOMAIN, because the defect crosses one.**  §1's rule is about an
#: export PATH and holds per domain: ``adcp.types.core.MediaBuy`` and
#: ``adcp.types.protocol.MediaBuy`` are two paths naming two objects and §1 is right to
#: allow them.  This rule is about a NAME, and the two names cannot both be the subject's.
#:
#: **NARROWER than the domain rule on the other axis**, which is what keeps it from
#: banning the word: it reaches only the positions that DECLARE.  §3a's own answer where a
#: consumer needs the protocol's word at a restating position is "an alias at its
#: position, never a second class", and an alias binds the subject's own class.
#:
#: **§9 is satisfied for :data:`COLLISION_SCOPE`'s reason and no new one.**  The subjects
#: are ``emit.rooted_subjects``, a parse of ``bundle.portable`` -- pinned, an input to
#: every run alike -- so what crosses into this pass is a set of NAMES and nothing here
#: can ask which documents the run was given.
SUBJECT_SCOPE = (
    "the whole BUNDLE for a position that DECLARES: a name the bundle gives a document "
    "root is that subject's, and a position deriving it from its own ROLE -- a property "
    "key, an item, a branch index -- lengthens by section 4's own axes rather than "
    "claiming it (section 3a step 3, a name is minted per entry and never per position). "
    "A position that BINDS the subject's own class is an alias and is untouched, and the "
    "subjects are read off the BUNDLE and never off the run's document set (section 9's "
    "ruling, the run is not the bundle)"
)

#: **The KIND reading 6's inner-node clause exports a position under**, beside ``root``,
#: ``branch`` and ``alias``.  One string, named, because three readers ask for it --
#: :func:`the_surface_exports` answers it, :func:`assign` decides the word it publishes,
#: and ``emit.domain_modules`` writes the statement -- and a fourth kind spelled three
#: times is how the three come to disagree about which positions the clause reaches.
INNER = "inner"

#: **Reading 6's inner-node clause, in the reading's own words.**  QUOTED by the checks
#: that grade it, for :data:`COLLISION_SCOPE`'s reason: the sentence the code states and
#: the sentence a failure reports against are one string.
#:
#: Reading 6 (2026-11-07, ``86f197a5d``): "**AND AN UNTITLED INNER NODE IS EXPORTED UNDER
#: ITS PARENT'S NAME AND ITS KEY, ALWAYS -- NEVER ONLY WHEN THE KEY COLLIDES.**  A domain
#: carries many a ``method``, a ``target``, an ``items``, so the key alone cannot be the
#: export for all of them. ... **REFUSE IT, because such a name is not stable under the
#: bundle's own growth:** a document arriving later with a colliding key would RENAME an
#: export an application already imports."
#:
#: **THE PARENT'S NAME IS THE PARENT'S OWN EXPORT WORD, WHICH MAKES THE RULE RECURSIVE AND
#: THE WORD THE WHOLE CHAIN.**  The clause is stated for one node, and a bundle nests them:
#: the parent of an untitled inner node is very often another untitled inner node, whose
#: own export word this same clause decides.  Read transitively the recursion bottoms out
#: at the nearest ancestor the bundle TITLES -- in this bundle always the document root --
#: so the word is :func:`segments`' whole chain joined, which is exactly "the parent's name
#: and its key" at every step of the way down.
#:
#: **MEASURED, and the measurement is why it is read transitively.**  Over bundle 3.2's
#: 1,059 emitted documents the clause reaches 1,342 declarations, and taking "the parent's
#: name" to be the parent's own SHORT segment -- the last two segments of the chain, the
#: literal depth-2 reading -- leaves **18 words that two positions of one domain both want,
#: over 38 positions, and 3 more that collide with a name the surface already exports**.
#: Taking it to be the parent's own export word leaves **0 of either**.  Reading 6's
#: "a rule that collides is not a rule" therefore selects the transitive reading, and it
#: needs no third component to do it.
#:
#: **AND THE WORD IS A FUNCTION OF THE DOCUMENT'S OWN PATH AND OF NOTHING ELSE**, which is
#: the stability the clause is about.  The parent's post-collision SYMBOL was the third
#: candidate and it is the one the clause's own reason rules out: §4's collision rule
#: lengthens a symbol against what else the MODULE declares, so an export worded from it
#: would move when an unrelated sibling arrived -- the hidden coupling reading 6 names in
#: so many words ("adding an unrelated document is a breaking change to an unrelated
#: import").  :func:`segments` is already stated as "a function of the node's PATH through
#: the document and of nothing else", so the chain is the one reading that has the property.
THE_INNER_EXPORT = (
    "an untitled inner node is exported under its parent's name and its key, ALWAYS and "
    "never only when the key collides -- and the parent's name is the parent's own EXPORT "
    "word, so the rule read transitively bottoms out at the nearest ancestor the bundle "
    "TITLES and the word is the node's whole chain through the document (reading 6, "
    "2026-11-07).  The word is a function of the document's own path and of nothing else, "
    "which is the stability the clause is about: a name chosen by what ELSE a module or a "
    "domain happens to hold is not stable under the bundle's own growth"
)


# --------------------------------------------------------------------------- #
# §4's name rules
# --------------------------------------------------------------------------- #
def title_words(title: str) -> list[str]:
    """One title's WORDS: its maximal alphanumeric runs, in order.

    The one reading of "a word of a title" in this compiler, because two readers ask and
    they must not disagree about where a word ends: :func:`class_name` spells OUR name
    from them and :func:`upstream_class_name` spells the one upstream's generator
    published from the same ones (:data:`UPSTREAM_TITLE_CASE`).  A second splitter would
    make the two spellings answers about two different word sets, and the whole claim of
    the second function is that it differs from the first in the CASING and in nothing
    else.

    ``str.isalnum`` and not a character class, so a title's non-ASCII letter is a letter:
    ``trusted-match/identity-match-response.json`` titles itself "Identity Match Response
    (Router -> Publisher)" with a real arrow, and the arrow is a separator either way --
    but a bundle writing an accented word would have it swallowed by an ASCII class and
    kept by this one.
    """
    words: list[str] = []
    cur = ""
    for ch in title:
        if ch.isalnum():
            cur += ch
        elif cur:
            words.append(cur)
            cur = ""
    if cur:
        words.append(cur)
    return words


def class_name(title: str) -> str:
    """``pascal_case`` that keeps an acronym: only the first letter of a word is
    touched, so ``TMPX Chunk`` stays ``TMPXChunk`` and does not become
    ``TmpxChunk``.

    **A keyword is NOT suffixed here, and that is measured rather than tidy**
    (``adcp-client-python-10l.37``).  A title is one SEGMENT of a chain and a keyword is
    a property of the whole SPELLING, so the guard belongs where the spelling is made
    (:func:`spelling`).  Put here it moved two symbols the grammar never objected to:
    ``core/geo-region-support.json``'s ``CountriesValueTrue`` and
    ``governance/sync-plans-request.json``'s ``BudgetTrue`` are both ``_suffixed`` onto
    their parent -- §4 names a pinned branch ``<Base><Const>`` -- so the segment is
    ``True`` and the name is not.
    """
    return "".join(w[:1].upper() + w[1:] for w in title_words(title))


#: **UPSTREAM's own normalisation of a title, which is where ``Adcp``, ``Mcp`` and ``Si``
#: came from.**  QUOTED by the checks that grade it
#: (``tests_emit/test_the_published_spelling_is_emitted.py``), for
#: :data:`COLLISION_SCOPE`'s reason: the sentence the code states and the sentence a
#: failure reports against are one string.
#:
#: :func:`class_name` touches a word's FIRST letter and leaves the rest, so an acronym the
#: bundle writes survives.  ``datamodel-code-generator`` spelled the same title with
#: Python's own ``str.title()`` over the same words -- first letter up, the REST DOWN --
#: which flattens one: ``AdCP Async Response Data`` is ``AdCPAsyncResponseData`` here and
#: was ``AdcpAsyncResponseData`` there.  The schema decides and the schema's title carries
#: the acronym, so OURS is the faithful spelling and THEIRS is the one an application
#: already imports -- which is a NAME owed, never a second type.
UPSTREAM_TITLE_CASE = (
    "upstream's generator spelled a DOCUMENT ROOT's name with Python's own str.title() "
    "over the title's words -- each word's first letter UP and the REST DOWN -- where "
    "class_name touches the first letter alone and leaves an acronym standing.  Where the "
    "two spellings of ONE title differ, the emitted module BINDS upstream's beside ours: "
    "an alias is a name and never a second type, so isinstance and __adcp_schema__ are "
    "unaffected and no declaration is added.  A title of ONE word states a class name "
    "rather than a phrase a generator re-cased, and upstream published it verbatim, so "
    "the normalisation is not re-applied to it.  The ROOT is the whole population, "
    "because a nested model is the one upstream named from its FIELD PATH and not from "
    "its title: measured against upstream's own emitted tree, its module carries this "
    "spelling for 101 of the 101 roots the rule fires on and for 0 of the 11 titled "
    "BRANCHES it would fire on"
)


def upstream_class_name(title: str) -> str | None:
    """Upstream's published spelling of ``title``, or ``None`` where it is ours already.

    :data:`UPSTREAM_TITLE_CASE` is the rule and this is the whole of it.  ``str.title()``
    per word and not ``w[:1].upper() + w[1:].lower()``, because the two disagree wherever
    a word carries a DIGIT and upstream's surface settles it: ``A2UI Component`` is
    ``A2UiComponent`` there, which is ``"A2UI".title()``, and the hand-rolled spelling
    would say ``A2ui``.

    **A title of ONE word is left alone, and that clause is measured rather than
    aesthetic.**  Re-applying the normalisation to one makes a class name the document
    STATES into mush -- ``AssetVariant`` into ``Assetvariant`` -- and upstream published
    ``AssetVariant``, so the rule would contradict the artifact it is a claim about.  Two
    of bundle 3.2's titles are single words and that one is the only contradiction among
    them; a phrase is what a generator re-cases, and a word is what it carries.

    **DERIVED FROM THE TITLE AND GRADED AGAINST UPSTREAM'S OWN ARTIFACT**, which is what
    makes this a rule rather than a census: nothing here reads a list of names, and
    upstream's emitted tree is what the claim is checked against afterwards.  Over the
    published 3.2 bundle, by::

        PYTHONPATH=.:src ./.venv/bin/python -c "
        import json, pathlib
        from codegen.lower.names import class_name, upstream_class_name
        up = {n.lower(): n for n in
              pathlib.Path('survey/upstream-flat-surface-9.6.1.txt').read_text().split()}
        fires = agree = against = 0
        for p in sorted(pathlib.Path('schemas/cache/3.2').rglob('*.json')):
            t = json.loads(p.read_text()).get('title')
            if not isinstance(t, str):
                continue
            ours, theirs = class_name(t), upstream_class_name(t)
            if theirs is None:
                continue
            fires += 1
            seen = up.get(ours.lower())
            if seen is None:
                continue
            agree += seen == theirs
            against += seen != theirs
        print(fires, agree, against)"

    the rule fires on **125** titles of the bundle; of the **68** whose spelling the
    committed record of upstream's flat surface carries up to case, it reproduces
    upstream's exactly **68** times and contradicts it **0** times.  The stronger reading
    is against upstream's tree itself, which this repository's own history holds at
    ``2954b258b`` (``git archive 2954b258b src/adcp/types/domains``): per MODULE, for the
    positions this rule reaches, upstream's counterpart declares or binds this spelling
    **101** times out of **101** and ours **0** times
    (``tests_emit/test_the_published_spelling_is_emitted.py``).

    The names that record does not carry are the half a hand list of what today's census
    happens to import could never have: a document whose title gains an acronym tomorrow
    is covered by the same sentence.
    """
    words = title_words(title)
    if len(words) < 2:
        return None
    theirs = "".join(w.title() for w in words)
    if theirs == class_name(title) or not theirs.isidentifier() or _keyword.iskeyword(theirs):
        return None
    return theirs


def _suffixed(chain: tuple[str, ...], suffix: str) -> tuple[str, ...]:
    """``chain`` with ``suffix`` spelled onto its LAST segment rather than appended as a
    segment of its own.

    §4 names three positions off their container -- ``<Property>Item`` for an element,
    ``<Property>Value`` for a mapping value, ``<Base><Const>`` for a pinned branch -- and
    each of the three is ONE segment, because ``Item``, ``Value`` and a pinned value name
    no position on their own: a collision between two elements has to lengthen past the
    container to say anything at all.

    An empty chain is the position under a mapping's KEY, which derives no name
    (:class:`Unnamed`), and the suffix is then the whole chain -- which is what the fold
    produced there before this pass had segments.
    """
    return (*chain[:-1], chain[-1] + suffix) if chain else (suffix,)


#: One WORD of a derived symbol: an acronym run, a capitalised word, or a lowercase run.
#: The acronym arm is first and refuses to eat the next word's capital, so
#: ``HTMLAssetRequirements`` is three words and not ``HTMLA`` plus ``ssetRequirements``.
#: It is the inverse of :func:`class_name`'s "only the first letter of a word is touched",
#: which is why an acronym survives the round trip.
_WORD = re.compile(r"[A-Z]+(?![a-z])|[A-Z][a-z0-9]*|[a-z0-9]+")


def _words(symbol: str) -> tuple[str, ...]:
    """A derived symbol back into the words :func:`class_name` spelled it from."""
    return tuple(_WORD.findall(symbol))


def _distinguishing(target: str, root: str) -> str:
    """**What the TARGET's name says that the ROOT's does not** -- §4's fourth branch rung.

    §4: "Where the root's name and the target's share a leading run, the branch takes the
    root's name plus the target's distinguishing remainder -- so ``AssetRequirementsImage``,
    not the target's name repeated."  The run is read at either END, because the bundle
    writes it both ways and one rule has to cover both: ``AssetRequirements`` beside
    ``ImageAssetRequirements`` shares its run as the target's SUFFIX, and
    ``GetCreativeFeaturesResponse`` beside ``GetCreativeFeaturesSuccess`` shares it as
    both names' PREFIX.  Measured over the 13 bare-``$ref`` branches of bundle 3.2 that
    reach this rung: 12 share a suffix and 1 a prefix, and 0 share both.

    **Why the remainder and not the target's name itself.**  §4's rung says "the TARGET's
    own derived name", and spelled literally that name is already TAKEN: the branch's
    second base IS the target, so the module imports the symbol, and :func:`spell`'s
    ``occupied`` is the rule that an imported name is a name taken.  A branch is a chain
    of one at this rung and has no ancestor to lengthen by, so ``occupied`` would keep the
    shadowing name rather than refuse it -- ``class ImageAssetRequirements(AssetRequirements,
    ImageAssetRequirements)`` -- and every field annotated with the import would be
    retyped.  The remainder spells the same fact onto the base's own segment, which is
    what §4's own example asks for and what the three existing suffix rungs already do
    (:func:`_suffixed`).

    Returns ``""`` where the target's name says nothing the root's does not; the rung then
    answers nothing and the branch falls to its index, exactly as §4's root-collision
    clause has a rung do.
    """
    them, mine = _words(target), _words(root)
    prefix = 0
    while prefix < min(len(them), len(mine)) and them[prefix] == mine[prefix]:
        prefix += 1
    suffix = 0
    while (
        suffix < min(len(them), len(mine)) - prefix
        and them[len(them) - 1 - suffix] == mine[len(mine) - 1 - suffix]
    ):
        suffix += 1
    # The longer shared run wins, and only one of the two is spent: a name sharing a run
    # at BOTH ends would otherwise lose the middle twice.
    if suffix > prefix:
        return "".join(them[: len(them) - suffix])
    return "".join(them[prefix:])


def spelling(chain: tuple[str, ...], depth: int) -> str:
    """One position's name carrying its last ``depth`` segments.

    ``depth`` 1 is the name §4 derives, each further step is the next nearest ancestor
    prepended (§4's collision rule, :func:`spell`), and ``len(chain)`` is the whole path
    -- which is the name this emitter gave every position before the rule was written.

    **A SPELLING PYTHON RESERVES IS SUFFIXED, which is :func:`field_name`'s own loop at
    the other half of the seam** (``adcp-client-python-10l.37``).  ``str.isidentifier``
    -- the check ``emit`` makes of a root's derived symbol -- answers ``True`` for every
    keyword, so ``class None(Base):`` passed every guard this compiler had and the
    module it was written into did not PARSE.  A keyword is a name the grammar has
    taken, which is the fact :func:`spell`'s ``occupied`` already carries for a name an
    IMPORT has taken; the two answers differ only because a position can lengthen past
    an import and none can lengthen past the grammar -- a ROOT and a titled BRANCH are
    chains of one.  So the spelling moves by the one character ``field_name`` moves it
    by, and it moves HERE rather than in :func:`class_name` because the question is
    about the whole name: a segment is not a name, and whether the JOIN of a chain is a
    keyword cannot be answered one segment at a time -- ``None`` arrives as a branch's
    own ``title`` and as nothing else in this bundle, but a chain whose last segment is
    innocuous can still spell one.  Two positions that collide after the suffix collide
    for :func:`spell` to see, because this is the function it compares.

    Nothing is lost, because a class's identity is its ``__adcp_schema__`` pointer and
    not its symbol -- the difference from a FIELD, where the wire name is kept as an
    alias because the document's accepted set depends on it.

    Measured over the committed tree: **2 positions**, the branches
    ``formats/canonical/display_tag.json#/allOf/1/oneOf/3`` and
    ``formats/canonical/image.json#/allOf/1/oneOf/3``, each titled "none".  No other
    symbol in the tree moves by one character.
    """
    name = "".join(chain[max(len(chain) - depth, 0) :])
    while _keyword.iskeyword(name):
        name += "_"
    return name


def entry_key(pointer: str) -> str:
    """The ``definitions``/``$defs`` KEY a local reference's pointer names.

    RFC 6901's two escapes, inverted.  The one reading of a pointer's last segment in
    this compiler, and it is a KEY and not a POSITION: §6 forbids recovering a position
    from a pointer string, and a DEF entry's position is the parser's (``Position.DEF``)
    -- what is read here is the name the document gave the entry, which the pointer
    carries because the pointer IS that key.
    """
    return pointer.rsplit("/", 1)[-1].replace("~1", "/").replace("~0", "~")


# --------------------------------------------------------------------------- #
# the HOPS: what the walk records instead of a name
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Root:
    """The document ROOT: ``pascal_case(title)``, and the OUTERMOST segment of every
    name derived below it (:func:`segments`)."""

    title: str


@dataclass(frozen=True)
class Property:
    """A value of ``properties``: ``<Property>``, a segment of its own."""

    parent: str
    key: str


@dataclass(frozen=True)
class Item:
    """An array's ``items``: ``<Property>Item``, spelled onto the segment the array is
    spelled with, because ``Item`` names no position on its own."""

    parent: str


@dataclass(frozen=True)
class Value:
    """A mapping's value schema: ``<Property>Value``, spelled onto the segment the
    mapping is spelled with, because ``Value`` names no position on its own."""

    parent: str


@dataclass(frozen=True)
class Entry:
    """A ``definitions``/``$defs`` entry: ``<Key>``, with the ROOT as its one ancestor.

    **The ``<Root>`` prefix was dropped on 2026-10-28** (§4 "Names"), for the sentence
    the nested rule already states: the module path carries the document, so a nested
    name does not repeat it.  ``core/verification-token-claims.json`` declares
    ``VerificationTokenGradingProfile`` and the old rule spelled it
    ``AgenticAdvertisingOrgVerificationTokenClaimsVerificationTokenGradingProfile`` --
    75 characters in a module already named ``core/verification_token_claims.py``.

    **A chain of TWO and not one, which is the whole of where the prefix went.**  The
    root is still a segment, so §4's collision rule can SPEND it where two entries of
    one module need it (:func:`spell`) -- "the prefix is what the collision rule spends
    ..., not what every entry pays up front".  Written as one joined segment the prefix
    would be unspendable and an entry colliding with the root would have nothing to
    lengthen by.

    This is a function of the ONE document and carries no dependency on a sibling set,
    so it is insertion-stable -- unlike the branch rule tried and reverted at
    ``64d0f897``.
    """

    key: str


@dataclass(frozen=True)
class Branch:
    """A branch of ``oneOf``/``anyOf``: the FACTS §4's four rules read, as values.

    §4 "Names"'s branch rules are "its own ``title``, else the ``const`` it pins on the
    discriminating property, else its sorted ``required`` set, else its index among the
    branches", and each of the first three is a
    fact of the branch's own DECLARATION.  The declaration is ``lower/union.py``'s to read
    -- §6 keeps that reading at the declaration level and
    ``tests/test_import_rule.py``'s ``MAY_READ_A_DECLARATION`` names the module -- so what
    crosses into this pass is the three facts and not the mapping.  Extracting a fact is
    not deriving a name: which fact wins, how it is spelled, and what a parent prefix is
    are all below, and a module that reads no mapping cannot come to read one.

    :attr:`pin` is the ``const`` the branch pins on the discriminating property, read over
    the property map §4 gives the rule: the branch's own, or -- for a bare ``$ref`` branch
    -- the TARGET's, because §4 says a ``$ref`` branch's fields are the target's and the
    walk is what resolved them.

    :attr:`index` is the fourth rule's own fact, and its PRESENCE is the difference
    between the two positions a branch is named at.  A ROOT union declares one class per
    branch, so a root branch needs a name of its own whatever it states and the walk
    records its index; a NESTED union is a TYPE, and a branch that lowers to an annotation
    needs no name at all, so the walk records none and §4's fourth rung has nothing to
    apply -- the branch falls back to the union's own derived name, which is what a member
    type has always been spelled with.  One field carries that difference because it IS
    that difference: a second boolean beside it would be a second copy of the decision.

    It is a FIELD and never recovered from the pointer string.  The branch's pointer ends
    in the index and §6 forbids reading a position out of a pointer -- the union is what
    knows its branch order, so the union hands the hop its index, exactly as it hands the
    branch the fact that it is a root union's branch.
    """

    parent: str
    #: The branch's own ``title``, where it states one that is a non-empty string.
    title: str | None = None
    #: **Every ``const`` the branch pins, in the order the document writes the keys**
    #: (§4, "Rung 2 reads EVERY pin the branch states", decided 2026-10-29).  It held ONE
    #: pin and declined to choose where a branch pinned several, which sent the five most
    #: heavily identified branches of the bundle to their index.  A tuple and not a scalar
    #: because the rung reads them all: one field, meaning "the pins this branch states",
    #: where a scalar beside a count would be two readings of one keyword.
    #:
    #: **Every pin the branch states, booleans included**, and which of them IDENTIFY it
    #: is :func:`identifying_pins`' reading at the rung.  A ``bool`` filtered out here
    #: would make the field mean "the pins that name something", which is a derivation
    #: wearing a walk's record -- and §4's clause is about what the RUNG does with a pin,
    #: not about which pins the document states.
    pins: tuple[Any, ...] = ()
    #: Its ``required`` set, as the document lists it.
    required: tuple[str, ...] = ()
    #: **The keys a nested ``anyOf``/``oneOf`` requires one of**, where the branch states
    #: its requiredness one level down instead of at its top level
    #: (``lower.union._requires_one_of``, which carries the reading).  §4's rung 3 reads
    #: :attr:`required` and this is NOT a second spelling of it: it is the branch's LAST
    #: rung and is reachable only by falling (:func:`_requirement_rung`, :func:`ladder`),
    #: so no branch §4's four identity rules already name takes a name from it.
    requires_one_of: tuple[str, ...] = ()
    #: **The SYMBOL a bare ``$ref`` branch's target declares** -- §4's fourth rung, which
    #: reads "where the branch is a bare ``$ref``, the TARGET's own derived name".  It is
    #: the one naming fact of a branch that no reading of the branch's own node can reach:
    #: such a branch states nothing but ``$ref``, so rungs 1 to 3 all answer ``None`` and
    #: every one of them falls to the index.  ``lower/union.py`` resolves the target
    #: already (:class:`union.Inherited`, "the SYMBOL, which is the branch's second base")
    #: and hands the resolution over rather than this pass reading a reference.
    #:
    #: ``None`` where the branch is not a bare ``$ref``, and ``None`` where the target is
    #: a node of THIS module: a local ``$ref``'s ``TypeRef.path`` is a POINTER until
    #: :func:`assign` runs, so there is no name to read and the branch keeps its index.
    #: A pointer is ``""`` or begins with ``/`` and a name is an identifier, which is this
    #: module's own convention for telling the two apart.
    target: str | None = None
    #: Its index among its union's branches, in the document's own order, where the branch
    #: is a CLASS and so needs a name of its own; ``None`` where it is a member type.
    index: int | None = None


@dataclass(frozen=True)
class Unnamed:
    """A position with NO name to derive: a mapping's KEY type.

    Not an omission and not a failure: ``propertyNames`` states a constraint on a key
    and §4's nested rule derives a name from a PROPERTY, an element or a value, so there
    is no rule to apply here.  The empty name is what the walk passed at those two call
    sites before this pass existed, and a declaration that needed one would collide with
    the other unnamed position and refuse by name.
    """


#: What the walk records for a child it lowers, instead of the child's name.  Keyed by
#: the child's POINTER on :attr:`codegen.compiler.Module.hops`.
#:
#: **A child at its PARENT's pointer needs no hop**, and two shapes are in that
#: position: a ``type``-list member and an extras store, both of which the parser builds
#: at the node's own pointer because each is the same instance re-read (§4).  They
#: inherit the entry the grandparent recorded, so there is one name per pointer and the
#: recursion below cannot meet itself.
Hop = Root | Property | Item | Value | Entry | Branch | Unnamed


# --------------------------------------------------------------------------- #
# §4's branch rules
# --------------------------------------------------------------------------- #
#: §4's boolean-pin clause, in the section's own terms.  QUOTED by the check that grades
#: it (``tests/test_names_collision.py``), so the sentence the code states and the
#: sentence a check reports against are one string.
A_BOOLEAN_PIN_NAMES_NOTHING = (
    "a boolean pin contributes no segment, because true names nothing: a pin identifies "
    "a branch by its VALUE, and a boolean's two values are the same two for every "
    "property in the bundle.  It is not a carve-out from the key-order rule -- it is the "
    "same sentence the section states for a branch, that true on both branches names "
    "neither, applied per PIN instead of per branch; so it subsumes the collision case, "
    "and a branch whose pins are all boolean answers nothing at rung 2 and falls "
    "through (section 4, decided 2026-10-29)"
)


def identifying_pins(pins: tuple[Any, ...]) -> tuple[Any, ...]:
    """The pins of ``pins`` that IDENTIFY a branch: every one that is not a boolean.

    :data:`A_BOOLEAN_PIN_NAMES_NOTHING` is the rule.  Measured over bundle 3.2: eight
    branches pin a ``true``, and reading every pin appended a segment identifying
    nothing -- four of them pin something identifying beside it
    (``PackageSignalTargetingBinary`` became ``PackageSignalTargetingBinaryTrue``) and
    four pin nothing else, so rung 2 answered ``…True`` where rung 3's ``required`` set
    names the property whose PRESENCE is what identifies them.

    ``bool`` is tested before any other type would be, which matters because
    ``isinstance(True, int)`` is true in Python: the JSON value ``true`` parses to
    ``True`` and nothing else in a document's ``const`` is a ``bool``, so this is a test
    on the document's own two values and not on a numeric coincidence.

    A tuple and not a filter on the caller's side, so the reading that "a boolean names
    nothing" is one function with one name: :func:`branch_rungs` asks for the pins that
    identify and never spells the test.
    """
    return tuple(p for p in pins if not isinstance(p, bool))


def branch_identity(hop: Branch, parent: tuple[str, ...]) -> tuple[str, ...] | None:
    """§4 "Names"'s four branch rules, in order, as the branch's own SEGMENTS, or
    ``None`` where none of them applies.

    A title names ITSELF, so it is a chain of one and the branch's ancestors are no part
    of it.  A ``const``, a required set or an index is spelled ON the parent's own last
    segment, so a branch named by any of them shares its base's spelling -- which is what
    §4 writes for the fourth rule as well, ``<Base>Branch<i>``.  The required-set key is
    deliberate: it is stable when the spec adds an OPTIONAL field and renames exactly
    when requiredness changes, which is a semantic change a caller should meet as an
    ``ImportError`` rather than as a silent repoint.

    **Which fact wins decides the SPELLING and the PLACEMENT together, which is why both
    are here.**  A caller handed the spelling alone would have to read ``hop.title``
    again to find out whether the ancestors belong in the chain, and that reading would
    be a second copy of the first rule.

    **A name is never derived from the neighbourhood.**  The rule a previous generator
    reached for -- name the sole classed branch after its PARENT -- makes a class name a
    function of what its siblings happen to be, so adding a branch renames an unrelated
    class.  §4 has no such rule, and its fourth rung is not that rule either: an index is
    a fact of the branch's OWN position, so what it reads is where this branch is and
    never what its siblings happen to state.  Inserting a branch AFTER this one moves no
    name, which is the property :data:`INDEX_IS_THE_LAST_RUNG` states and
    ``tests/test_names_collision.py`` grades.

    **The index is the LAST rung and only the last.**  It is tried after all FOUR identity
    rungs have answered nothing, because a positional name says nothing about
    what it names; where an identity exists the identity wins, and a branch whose index
    the walk did not record (a nested union's, which needs no name of its own) answers
    ``None`` and takes the union's own derived name.

    **The fourth identity rung is the bare ``$ref``'s target** (:data:`REF_TARGET_RUNG`),
    added because the index was reaching 18 branches of this bundle and 13 of them are a
    bare ``$ref`` whose target names itself -- ``image-asset-requirements.json``,
    ``video-asset-requirements.json``.  ``isinstance(req, AssetRequirementsBranch7)``
    requires counting the document's branches to learn that it means JavaScript, which is
    the usability failure a positional name IS.
    """
    rungs = branch_rungs(hop, parent)
    return rungs[0] if rungs else None


def branch_rungs(hop: Branch, parent: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """§4's four branch rules as a LADDER: every rung that answers, in the section's order.

    :func:`branch_identity` is the FIRST rung of this and is what a chain starts at.  The
    rest exist because §4 now says a rung can fail to identify: "Where a rung derives one
    name for two branches it has not identified either, so BOTH fall to the next rung",
    and "a branch colliding with its own document ROOT ... falls to the next rung"
    (both decided 2026-10-29).  Falling is not lengthening -- these chains are one segment
    with nothing to lengthen by -- so it is a second axis and :func:`spell_the_rungs`
    walks it.

    **Rung 2 is EVERY pin that IDENTIFIES, in the document's own key order**
    (:attr:`Branch.pins`, :func:`identifying_pins`).  A branch pinning ``country: FR``
    and ``system: code_postal`` is ``FRCodePostal``; one pinning ``country: US`` alone is
    ``US``, because one pin in key order is that one pin.  The order is the DOCUMENT's and
    never sorted: sorting would make a public symbol a function of spelling, which is the
    reading ``_const_pin`` declined for and the reason it answered nothing at all for
    such a branch.

    **A BOOLEAN pin contributes no segment** (:data:`A_BOOLEAN_PIN_NAMES_NOTHING`), so a
    branch whose pins are all boolean answers nothing here and falls to rung 3 -- which
    is what ``trusted-match/provider-registration.json``'s two branches need, reached now
    by one rule rather than by the collision clause below.

    **Which rungs a ROOT has: exactly one.**  A root is not a branch and never reaches
    here -- :func:`segments` answers it from :class:`Root` -- so its ladder is the single
    chain §4's D5 fixes, and "the root keeps the name" needs no clause of its own here.
    That is why the collision rule below says only "a position with a rung left advances":
    the root has none, so it cannot move, and the branch beside it is the side that does.
    """
    out: list[tuple[str, ...]] = []
    if hop.title:
        out.append((class_name(hop.title),))
    identifying = identifying_pins(hop.pins)
    if identifying:
        out.append(_suffixed(parent, "".join(class_name(str(p)) for p in identifying)))
    if hop.required:
        out.append(
            _suffixed(parent, "".join(class_name(str(k)) for k in sorted(hop.required)))
        )
    if hop.target and parent:
        # **Rung 4, and the last IDENTITY rung** (§4 "Names", the branch ladder): "else,
        # where the branch is a bare ``$ref``, the TARGET's own derived name".  Both
        # inputs -- the target's symbol and the root's own name -- are facts about the ONE
        # branch, so the rule is insertion-stable, which is §4's own criterion and what
        # the branch rule reverted at ``64d0f897`` failed: inserting a thirteenth asset
        # kind ahead of the others renames none of them.
        remainder = _distinguishing(hop.target, parent[-1])
        if remainder:
            out.append(_suffixed(parent, remainder))
    if hop.index is not None:
        out.append(_suffixed(parent, f"Branch{hop.index}"))
    # A rung spelling the same chain as the rung above it is not a rung to fall to: it
    # identifies the branch no better and the fall would not terminate.  Measured: a
    # branch whose title spells its own pin, and a one-branch union whose index repeats
    # its required set.
    return tuple(dict.fromkeys(out))


#: §4's fourth IDENTITY branch rung, in the section's own terms.  QUOTED by the check that
#: grades it (``tests/test_names_collision.py``), so the sentence the code states and the
#: sentence a check reports against are one string.
REF_TARGET_RUNG = (
    "where the branch is a bare $ref, the TARGET's own derived name; and where the root's "
    "name and the target's share a run, the branch takes the root's name plus the target's "
    "distinguishing remainder -- AssetRequirementsImage, not the target's name repeated. "
    "Both inputs are facts about the one branch, so the rule is insertion-stable "
    "(section 4)"
)

#: §4's fifth branch rule and the one ground it stands on, in the section's own terms.
#: QUOTED by the check that grades it (``tests/test_names_collision.py``), so the sentence
#: the code states and the sentence a check reports against are one string.
INDEX_IS_THE_LAST_RUNG = (
    "a branch with no title, no pinned const and no required set takes its index among "
    "the branches, <Base>Branch<i>; a name is not an acceptance fact, so the fallback "
    "neither widens nor narrows, and the index is a fact of the branch's own position, "
    "so inserting a branch after it moves no name (section 4)"
)


# --------------------------------------------------------------------------- #
# the field spelling, which is pydantic's own surface read once
# --------------------------------------------------------------------------- #
def field_name(key: str, reserved: frozenset[str] = frozenset()) -> str:
    """The Python field name for a property key, which is the key itself unless the
    model layer cannot carry a field under that name.

    A key is carried as-is or it is carried under an ALIAS, never dropped.  The bundle
    has keys a Python attribute cannot spell (``$schema``) and keys pydantic reads as
    something other than a field: a leading underscore makes a private attribute and no
    field at all, so ``core/truncation-sentinel.json``'s required ``_truncation`` was
    silently absent from the model -- the model refused the document's own instance AND
    accepted an instance omitting the required key, in the same class.

    The alias is the ONLY accepted spelling (no ``populate_by_name``), so the model's
    accepted set stays the document's: the wire name is accepted and the Python name is
    not a second way in.

    **``reserved`` is what the MODEL LAYER carries, and it is an ARGUMENT because §8
    draws the boundary where it does.**  This function read
    ``hasattr(pydantic.BaseModel, name)``, and that import was the one model-layer read
    left outside ``codegen/render.py`` -- named as a shrink-only exception in
    ``tests/test_import_rule.py``'s set.  §8 bans ``pydantic`` under ``lower/``
    outright, so moving the reading here would have GROWN that set; the set shrinks
    instead, because the reserved names are DERIVED in ``render.py`` (``render.RESERVED``)
    and handed to :func:`assign` by the run.  The fact is still read off the model layer
    and never listed by hand, and no module under ``lower/`` names pydantic.
    """
    name = "".join(c if c.isalnum() or c == "_" else "_" for c in key).lstrip("_")
    if not name or name[0].isdigit():
        name = f"f_{name}"
    while _keyword.iskeyword(name) or name.startswith("model_") or name in reserved:
        name += "_"
    return name


# --------------------------------------------------------------------------- #
# §4's content dedup: the equality, and the binding at a later position
# --------------------------------------------------------------------------- #
def same_node(mod: Module, node: nodes.Base) -> str | None:
    """The POINTER an EQUAL node already declared in this module, or ``None``.

    **§4's content dedup, keyed on NODE EQUALITY.**  §14 step 5 deleted
    ``emit.content_key`` -- ``json.dumps([the node's own mapping, node.applied])`` -- and
    ``schema/nodes.py`` says what replaces it: ``pointer`` and ``position`` are excluded
    from the kinds' equality, so two nodes are equal exactly when they state the same
    thing about an instance.  Everything else a node STATES is compared, including
    ``annotations`` (a node differing only in a ``$comment`` states a different thing to
    a reader) and ``applied`` (a node whose enclosing type word decides differently --
    which is the bit the old key appended by hand, and 1,390 of the bundle's nodes
    declare ``properties`` with no ``type``, 556 of them with that word applied and 834
    without, so both sides are populated).

    ``compiler.Module.collapsed`` is where the equality's CUT at a ``$ref`` and the
    reason the memo is a SEQUENCE are both written down: a node carries mappings and is
    not hashable, and a hash would be a second spelling of what identical means.

    **Measured over the memo's own population**, which is the nodes
    ``compiler.lower_node`` is called on: 7,250 nodes in 677 documents over the whole
    portable set, 283 groups of more than one node by the deleted key and 283 by this
    equality, and 0 documents whose partition differs.  So the replacement is a
    relocation and not a decision.

    **Asked in the WALK and not in the pass, and the reason is the pruning.**  A second
    occurrence's CHILDREN are never lowered -- they would declare a second class each,
    and their drops and their reports would be recorded twice -- so the equality has to
    be consulted before the node is decided.  What the PASS owns is everything §4
    actually decides about a group: which pointer declares, what each pointer is called,
    and that a later pointer binds the class by identity (:func:`adopt`, :func:`assign`).
    :data:`SCOPE` is the scope of all of it.

    **What SEEDS the memo is a symbol declared AT THE NODE'S OWN POINTER**, which is
    exactly D2's class and enumeration rows and :func:`name_the_node`'s alias
    (``compiler.lower_node`` is the one writer of ``mod.collapsed``).  An annotation
    declares nothing, so an identical annotation is simply decided again -- to the same
    annotation, since the inputs are the same -- and a ``$ref`` whose symbol the module
    IMPORTED is not seeded either, because the import is already in ``mod.imports`` and
    §2's rule is an import of a symbol the TARGET declares.  A node that declares a
    symbol at its pointer and then decides to a CONTAINER over it is therefore not
    seeded; a nested union is the shape that would be, and it is covered anyway because
    its BRANCHES collapse through the same entry and two identical branch lists then
    decide to one annotation.  No such pair survives the run, and clause 1 of the check
    reddens by name if one appears.
    """
    return next((at for other, at in mod.collapsed if other == node), None)


def adopt(mod: Module, pointer: str, declared: str) -> ir.TypeRef | Refusal:
    """§4's content dedup at the SECOND and later positions of one node: the class the
    first position declared, under the name THIS position's own rule derives.

    **One class, as many names as the node has positions.**  §4's dedup is a statement
    about CLASSES -- one node yields one class -- and §4's nested rule derives a name per
    POSITION, so a node at three positions has one class and three derived names.  An
    alias is a NAME BOUND TO THAT CLASS and not a second class, which is why the two
    rules do not collide and why nothing here is hand-assigned: the name is whatever
    :func:`segments` folds the adopting position's own hops to and :func:`spell`
    spells.

    What this refuses to do is type a field by a SIBLING POSITION's name.  Binding
    ``PreviewRenderHtml.dimensions`` to ``PreviewRenderUrlDimensions`` would read as the
    html branch carrying the url branch's type, and it would make the public symbol a
    function of which key the walk happened to reach first.  The upstream v9 SDK is the
    worked case of the opposite failure -- 1,092 of its 4,360 classes are numbered
    variants of content it declares over and over, ``WholesaleFeedEvent1`` through
    ``WholesaleFeedEvent9`` among them -- and the answer to that is one class aliased,
    not one class renamed.

    **The DECLARATION is an ``ir.AliasDecl``, the same statement §4's root-scalar row
    emits**, so there is one alias spelling in the emitter and not a second one here.  It
    carries no constraints, no description and no format on purpose: the node is EQUAL to
    the one the class already lowered, so every fact about it is already stated on the
    class, and a ``Field(description=...)`` wrapper here would both restate it and make
    the alias an ``Annotated`` object rather than the class itself -- which is the one
    thing a consumer must be able to rely on.  ``X = TheClass`` is the class by IDENTITY:
    ``X is TheClass``, ``isinstance`` works, and a type checker follows it.

    **Two positions take the class symbol directly rather than an alias, and
    :func:`assign` is what decides that** -- it has to be, because neither test can be
    made before the names are derived.  A position whose hops derive NO name (a mapping's
    key type) has no name to bind, and a position whose derived name IS the declared
    one would be ``X = X``.  The walk declares the alias at the adopting pointer either
    way and the pass drops the degenerate ones, mapping the adopting pointer straight
    onto the declaring class's symbol.

    **The adopting pointer IS declared**, under its own name, so a cross-document
    ``$ref`` naming the second position resolves to it -- ``emit.exported`` lists the
    symbol at every bundle-named pointer, so the import side and the export side still
    read one fact.  Before the alias this arm refused DEFERRED instead; 0 of the
    collapsed pointers are among the bundle's 216 named nodes, so the change closes a
    ceiling nothing reaches rather than moving a refusal.
    """
    collision = mod.declare(
        pointer, ir.AliasDecl(pointer, ir.TypeRef(declared, local=True))
    )
    if collision is not None:
        return collision
    return ir.TypeRef(pointer, local=True)


# --------------------------------------------------------------------------- #
# §2's rule at a node some OTHER document names: the alias that holds the symbol
# --------------------------------------------------------------------------- #
def alias_for(pointer: str, node: nodes.Base, decided: ir.Decided) -> ir.AliasDecl:
    """One node's own decision, as the alias that names it.

    Shared by the THREE rows that declare an alias -- a root
    (``compiler.declare_alias``), a node another document names
    (:func:`name_the_node`) and a container's described contents
    (``lower.containers._contents``) -- because "the annotation for this node, under this
    name" is the same question in all three and a second copy of it is how two of them
    come to carry a node's ``format`` or its ``description`` differently.  They differ
    only in what wraps the statement, which is each row's own and stays there.

    The bound and the ``format`` ride on the alias's own TYPE, exactly as a field's do
    (§2, and :attr:`codegen.ir.TypeRef.facts`): one carrier, so an alias and a property
    cannot come to spell one ``minLength`` two ways.

    **Here and not in ``compiler.py`` because an alias is a NAME BOUND TO A STATEMENT**,
    which §7 makes this module's: ":func:`adopt` and this build the same declaration, and
    the reading that tells them apart is what each binds -- ``adopt`` binds a class an
    EQUAL node already declared and carries no facts of its own, because every fact is
    already on that class; this binds the node's OWN decision, so every fact it states
    has to ride along or be dropped."
    """
    return ir.AliasDecl(
        # The POINTER in the name slot until :func:`assign` binds it (§7).
        pointer,
        replace(decided.type, facts=decided.constraints, format=decided.format),
        description=node.description,
    )


def name_the_node(
    mod: Module, pointer: str, node: nodes.Base, decided: ir.Decided
) -> ir.TypeRef | Refusal:
    """Give a node a SYMBOL in its own module, because a ``$ref`` elsewhere names it.

    A fragment reference resolves to an import of a symbol the target module declares,
    never to a copy (§2's rule).  A node D2 makes a CLASS already has one -- the walk
    declared it and ``decided.type.local`` says so -- and this is the other case: an
    array, a scalar or a mapping is an annotation with no name, so the target module has
    nothing to export and the reference has nothing to import.

    **The node's type BECOMES the symbol**, which is why the TYPE comes back rather than
    only the declaration being made: the alias carries the constraints and the referring
    property then references it, so the node's facts have ONE spelling in the module.
    Declaring the alias and leaving the parent's field to restate the same ``minLength``
    inline would be the copy P2 removes, two spellings deep in one file.

    Not ``compiler.declare_alias``, which is a ROOT's whole module -- the reference, the
    alias and the bound ``strict_validate``, all at module scope, where there is room for
    exactly one of each.  A named node is INSIDE a document that already has a root, so
    it takes the alias statement alone.  It therefore carries no ``__adcp_schema__`` of
    its own, and that is the existing arrangement rather than a gap: every nested node
    that is not a class is ungraded on its own today, and this one is graded twice over
    anyway -- inside its own document's pair, which names the whole document, and inside
    its referrer's, whose resolved schema inlines this very node at the pointer the
    reference carries.

    **No name is computed here and none is passed in** (§7, and §14 step 7): the
    declaration is made at the node's own POINTER, and :func:`assign` binds it to the
    name §4's nested rule derives for that position -- which is the hop the node's parent
    recorded when it lowered this child.

    **It returns the TYPE and not a ``Decided``, which is :func:`adopt`'s signature**, and
    the two callers are the reason as much as the symmetry is: ``lower.containers``
    answers ``ir.TypeRef | Refusal`` itself and now returns this call's result straight,
    and the walk's own entry (``compiler.lower_node``) is the one place that wraps.  It
    is also what keeps this module's arrow to ``compiler.py`` inside ``if
    TYPE_CHECKING`` -- ``compiler`` imports this module at module level, so a runtime
    name from it here would close the cycle the audit reports.
    """
    collision = mod.declare(pointer, alias_for(pointer, node, decided))
    if collision is not None:
        return collision
    return ir.TypeRef(pointer, local=True)


# --------------------------------------------------------------------------- #
# the pass
# --------------------------------------------------------------------------- #
def segments(
    pointer: str, hops: Mapping[str, Hop], seen: frozenset[str] = frozenset()
) -> tuple[str, ...] | Refusal:
    """§4's name rules for the node at ``pointer``, as the SEGMENTS of its path with the
    root first -- so the LAST segment is the name §4 derives for it and each earlier one
    is an ancestor a collision can lengthen by (:func:`spell`).

    A name is a function of the node's PATH through the document and of nothing else --
    not of its content, not of which other nodes exist, not of the order the walk
    happened to reach it in.  That is what makes it recomputable after the walk, and it
    is also §9's rule: no census over the run enters here.

    **A chain and not a name, and that is the whole of §4's "the module path already
    carries the document".**  This fold used to CONCATENATE every hop to the root, which
    needs no collision rule because it cannot collide -- and that is why 808 of 2,118
    emitted classes were longer than 30 characters and one was
    ``GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext``.  The
    segments are the same readings, kept apart, so :func:`spell` can spend exactly as
    many of them as the module's own names require.

    Three positions are a segment rather than a name of their own, and :func:`_suffixed`
    is where: an element, a mapping value and a pinned branch are each spelled onto the
    segment their container is spelled with.  A ``definitions`` entry is NOT one of them
    (2026-10-28): §4 names it ``<Key>`` and the root is its ANCESTOR segment, so the
    prefix is there for the collision rule to spend and is not paid up front.  A branch
    TITLE names itself, so it starts a chain and its ancestors are no part of it.

    **An INDEX is a fact of the node's own position and so it is a fact of its path**, and
    that is why §4's fourth branch rung does not cost this function its first paragraph: a
    branch's index is where it sits under its own combinator, not a reading of what its
    siblings state, so inserting a branch after it renames nothing.  The index arrives as
    a field on the hop (:class:`Branch`) because §6 forbids recovering a position from the
    pointer string that happens to end in it.

    ``seen`` is the pointers already on this fold, so a hop table that named a pointer
    through itself answers once rather than recurring.  The parser gives a child a
    pointer strictly below its parent's, so the population is 0; it is written because
    a fold with no base case is a crash and §9 says a crash is not an outcome.
    """
    hop = hops.get(pointer)
    if hop is None or pointer in seen:
        return ()
    if isinstance(hop, Unnamed):
        return ()
    if isinstance(hop, Root):
        return (class_name(hop.title),)
    if isinstance(hop, Entry):
        root = segments("", hops, seen | {pointer})
        if isinstance(root, Refusal):
            return root
        return (*root, class_name(hop.key))
    parent = segments(hop.parent, hops, seen | {pointer})
    if isinstance(parent, Refusal):
        return parent
    if isinstance(hop, Property):
        return (*parent, class_name(hop.key))
    if isinstance(hop, Item):
        return _suffixed(parent, "Item")
    if isinstance(hop, Value):
        return _suffixed(parent, "Value")
    derived = branch_identity(hop, parent)
    # A branch whose four rungs all answer nothing is a NESTED union's branch and nothing
    # else -- §4's fourth rung always answers for a branch that is a class, because the
    # union records its index -- and a member type takes the union's own derived name.
    # **This arm used to mint a VERDICT here**, and it was minting one where §4 states a
    # fallback; the raise site is gone with it, which is one of the hand-written
    # ``Kind`` arguments ``docs/plan/architecture.md`` §3 counts.
    return parent if derived is None else derived


#: §4's LAST branch rung, in the section's own terms.  QUOTED by the check that grades it
#: (``tests/test_names_collision.py``), so the sentence the code states and the sentence a
#: check reports against are one string.
REQUIREMENT_IS_THE_FALL_OF_LAST_RESORT = (
    "a branch stating its requiredness one level down -- anyOf: [{required: [x]}, "
    "{required: [y]}] -- requires one of x and y as plainly as a top-level required set "
    "states its own, so that key set is a name the branch has available; it is the LAST "
    "rung and is reachable only by FALLING, because section 4's four identity rules are "
    "closed and its answer for a branch none of them names is the union's own derived "
    "name -- which is a rule and not a gap, so a branch that collides with nothing keeps "
    "it.  What the rung serves is the one position in this pass that had a declared name "
    "and no second name to fall to (section 4)"
)


def _requirement_rung(hop: Branch, parent: tuple[str, ...]) -> tuple[str, ...] | None:
    """§4's LAST branch rung: the keys the branch requires ONE LEVEL DOWN, or ``None``.

    :data:`REQUIREMENT_IS_THE_FALL_OF_LAST_RESORT` is the rule and
    ``lower.union._requires_one_of`` is the reading.  Spelled exactly as rung 3 spells its
    own set -- sorted, onto the parent's last segment -- because it is the same fact about
    the same keys and a second spelling of "the branch's required set" is how the two would
    come to disagree about one document.

    **IT IS NOT AN IDENTITY RUNG, AND THE PLACEMENT IS THE DECISION.**
    :func:`branch_identity` is what a branch is CALLED and §4's four identity rules are a
    closed list; its answer for a branch none of them names is :func:`segments`' fallback,
    the union's own derived name, and that is a rule rather than a gap.  **Measured, and
    this is why the rung is a fall and not a fifth identity rule**: over bundle 3.2's 1,054
    portable documents 21 nodes state requiredness this way and three of them are branch
    positions, and as a fifth IDENTITY rule it renames two classes the bundle is shipped
    with -- ``core/targeting-overlay-requirements.json#/properties/geo_proximity/anyOf/1``
    and ``core/targeting-overlay-support.json``'s -- from
    ``TargetingOverlayRequirementsGeoProximity`` to
    ``TargetingOverlayRequirementsGeoProximityGeometryRadiusTransportModesTravelTime``.
    Neither collides with anything, so neither needs a second name, and renaming a shipped
    public symbol to close a refusal in another document is a cost with no buyer.  As a
    FALL it reaches exactly the positions that cannot keep the name they derive.

    ``parent`` is empty only under a mapping's KEY, which is :class:`Unnamed` and never a
    branch, so the suffix always lands on a segment.
    """
    if not hop.requires_one_of:
        return None
    return _suffixed(parent, "".join(class_name(str(k)) for k in sorted(hop.requires_one_of)))


def ladder(
    pointer: str, hops: Mapping[str, Any], seen: frozenset[str] = frozenset()
) -> tuple[tuple[str, ...], ...] | Refusal:
    """Every chain this position could be named by, best first: §4's rungs.

    One rung for every position but a BRANCH, which is the whole of §4's asymmetry here --
    a property, an element, a mapping value, a definitions entry and a ROOT each derive
    their name from one fact, and only a branch has a section-ordered ladder of facts to
    fall down (:func:`branch_rungs`).  So this is :func:`segments` with the branch arm
    widened, and :func:`segments` is its first rung.

    **THE REQUIREMENT RUNG IS APPENDED HERE AND NOT IN :func:`branch_rungs`, which is what
    makes it a fall** (:func:`_requirement_rung`,
    :data:`REQUIREMENT_IS_THE_FALL_OF_LAST_RESORT`).  :func:`branch_identity` is
    ``branch_rungs(...)[0]``, so a rung inside that function is the name a branch TAKES the
    moment the rungs above it answer nothing -- and §4's identity list is closed.  Appended
    to the LADDER it is a name available to a position that collides and nothing else, which
    is the one circumstance in which a branch needs a name beyond the one §4 derives for it.

    **It serves a MEMBER TYPE above all, and that position is why the rung exists.**  A
    branch §4 names after the union's own derived name has a ladder of ONE -- no identity
    rung answered and the walk recorded no index, because a member type needs no name of its
    own -- so it has nothing to lengthen by and nothing to fall to, and two such positions
    of one document are :func:`spell`'s refusal.  **MEASURED on bundle 3.3**:
    ``core/targeting-overlay-requirements.json`` refuses on ``title`` at
    ``/definitions/daypartRequirement`` because that entry and its
    ``/anyOf/1`` both derive ``TargetingOverlayRequirementsDaypartRequirement``, and the
    branch has no second name -- while the document states, one level down, that it requires
    one of ``timezone_modes`` and ``time_granularity``.  Bundle 3.2 states the same union
    with ``required: ["timezone_modes"]`` at the branch's top level and never refused.

    The PARENT chain a rung is suffixed onto is the parent's own FIRST rung, which is
    :func:`segments`' answer and the chain every other reading of the parent uses.  A
    parent that itself falls to a later rung therefore keeps its children's SHORT names
    where they were -- and a short name is what a child is declared under unless it
    collides, so the parent's fall reaches a child only through the lengthening axis.
    Measured over the portable set: of the branch positions that fall to a later rung, 0
    have a named descendant that collides, so the two axes do not interact in this bundle
    and the simpler reading is the measured one.
    """
    hop = hops.get(pointer)
    if not isinstance(hop, Branch) or pointer in seen:
        chain = segments(pointer, hops, seen)
        return chain if isinstance(chain, Refusal) else (chain,)
    parent = segments(hop.parent, hops, seen | {pointer})
    if isinstance(parent, Refusal):
        return parent
    chains = branch_rungs(hop, parent) or (parent,)
    last = _requirement_rung(hop, parent)
    # A rung spelling a chain already in the ladder is not a rung to fall to, which is
    # ``branch_rungs``' own rule at the other end -- a branch whose top-level ``required``
    # and whose nested one name the same keys identifies itself no better the second time.
    return chains if last is None or last in chains else (*chains, last)


#: §4's collision rule, in the section's own words.  QUOTED by the checks that grade it
#: (``tests/test_names_collision.py``), so the sentence the code states and the sentence
#: a check reports against are one string.
COLLISION = (
    "every position derives its short name; where N positions of one module derive the "
    "same name, ALL N lengthen -- each prepends its own nearest ancestor segment -- and "
    "the step repeats until every name in the module is unique; a position whose short "
    "name collides with nothing keeps it (section 4)"
)


def spell(
    chains: Mapping[str, tuple[str, ...]],
    occupied: frozenset[str] = frozenset(),
    surface: frozenset[str] = frozenset(),
    exports: frozenset[str] = frozenset(),
    subjects: frozenset[str] = frozenset(),
    declaring: frozenset[str] = frozenset(),
) -> dict[str, str] | Refusal:
    """§4's collision rule over the names of ONE module: pointer -> the name it is
    declared under, or the refusal of a module two of whose positions cannot be told
    apart.

    :data:`COLLISION` is the rule.  Every position starts at the name §4 derives (its
    last segment); the positions sharing a name ALL lengthen by their own nearest
    ancestor segment; the step repeats until no name is shared.

    **ALL N lengthen, and that is the whole of why this is order-independent.**
    Lengthening only the later collider would make a public symbol a function of which
    position the walk reached first, which §9 forbids and which :func:`adopt` already
    refuses for the same reason.  Lengthening all of them makes each name a function of
    the SET of colliding positions, and that set is a function of the one document --
    which is why this takes a mapping and not a module, and why nothing here can consult
    the run.

    ``occupied`` is the names the module's own IMPORTS hold: what the walk reported
    (``Module.imports``) and what the renderer brings in (``render.CARRIERS``, via
    :func:`assign`).  A module's namespace is its declarations AND what it imports -- a
    class shadowing an imported symbol retypes every field annotated with it, and
    ``class Field(StrEnum)`` beside ``from pydantic import Field`` makes
    ``Annotated[X, Field(description=…)]`` call the class -- so an imported name is a
    name taken, and a position deriving it lengthens.  Measured over the portable set
    with §4's nested rule in force: 25 positions of 2,226 derive an occupied name -- 3
    a symbol their own document's ``$ref`` imports, 5 one the renderer brings
    (``Field`` four times and ``Presence`` once), and 17 a name in the vocabulary the
    renderer could bring and this module does not.

    It is not a census over the run.  A module imports a symbol because ITS OWN ``$ref``
    names the target, so the set is a function of the one document and its closure, which
    a one-document emission writes as well; §9's rule is about the documents BEYOND that
    closure.  An import cannot lengthen, so only the positions move.

    ``surface`` is the DOMAIN's half of :data:`COLLISION_SCOPE` and it is a name taken for
    the same reason ``occupied`` is, one scope out: §1 forbids
    ``adcp.types.<domain>.<Name>`` naming two declarations, so a name another module of
    the domain exports is taken for the positions THIS module exports -- which is what
    ``exports`` narrows it to.  **The narrowing is not a refinement, it is the rule.**
    §1's amendment is stated over the export set, and a position the surface does not
    export may keep a name the surface uses elsewhere: measured over this bundle, the
    domain's root symbols are derived by 16 positions of other modules and only 6 of them
    are exported, so an unnarrowed set would move ten names §1 says nothing about --
    ``core.Format`` in ``core/account.py``, ``core.Destination`` in
    ``core/flight_item.py`` and eight more.

    Unlike ``occupied`` it is read off the BUNDLE rather than off this document's closure,
    and :data:`COLLISION_SCOPE` carries §9's ruling for why that is not a census over the
    run.  It cannot lengthen either -- the name belongs to another document -- so again
    only this module's positions move.

    **An occupied name a position cannot lengthen past is kept and does not refuse**, and
    the reason is that it is exactly the name this emitter has always given that position.
    A ROOT and a titled branch are chains of ONE -- §4 names them after the document and
    after the branch's own title -- so neither has an ancestor to prepend, and refusing
    them would refuse 99 documents of this bundle on a name no document says anything
    about -- measured by making it refuse: ``core/error.json``'s root is ``Error`` and
    the runtime exports an ``Error``, and 98 more follow it or chain behind one.
    Lengthening is an improvement where it is available and the status quo where it is
    not.  **"Cannot lengthen past" is not "has nowhere left to go", and reading it as
    though it were is what shipped 56 shadowed names**: a BRANCH is a chain of one with a
    whole LADDER under it, so where lengthening is spent the rung axis still answers and
    :func:`spell_the_rungs` -- the function the run calls -- is what spends it.  What
    reaches this function is the position with no rung left either, and a ROOT is the one
    that always has none: §4's root clause is that it keeps the name, and so does this.

    The REFUSAL is the one this pass always had, and it needs two positions: both spelled
    with their whole paths, neither with an ancestor left to prepend, and spelled alike.
    That is exactly the population the fold refused before the rule was written -- the
    full path was the name then -- so the rule moves no document into the refused set.

    ``subjects`` is §3a step 3's half (:data:`SUBJECT_SCOPE`), and it is a name taken for
    ``surface``'s reason one scope wider: a name the BUNDLE gives a document root is that
    subject's, so a position that would DECLARE a second type under it lengthens.  The two
    narrowings are the difference between the rules and not a refinement of one: §1 asks
    whether the position is EXPORTED, because its subject is an export path, and §3a asks
    whether the position DECLARES, because its subject is a name.  That is why the
    paragraph above counts ten names §1 leaves alone and §3a moves -- ``core.Destination``
    in ``core/flight_item.py`` is one of them, and the entity ``core/destination.json``
    titles "Destination" is the subject it was claiming.
    """
    spelled, shared = _lengthened(chains, occupied, surface, exports, subjects, declaring)
    # **A group of ONE is a position alone on a name an IMPORT holds**, which the
    # paragraph above is about: it is kept, so it is not what this refusal is for.  The
    # filter is here rather than in :func:`_lengthened` because the lone group is exactly
    # what :func:`spell_the_rungs` falls to the next rung, and one reading cannot be both
    # readers' answer unless each reader states what it does with it.
    unresolved = {name: ps for name, ps in shared.items() if len(ps) > 1}
    if not unresolved:
        return spelled
    # Nothing colliding can lengthen and §4's rung axis is not this function's -- see
    # :func:`spell_the_rungs`, which is what the run calls.  The pointer named is the one
    # that COLLIDED, the later of the two in declaration order, which is the pointer
    # ``Module.declare``'s symmetric check names as well.
    #
    # **IT IS REACHABLE AND BUNDLE 3.3 REACHED IT, which is the correction to the
    # measurement this comment used to carry.**  It read "MEASURED UNREACHABLE over the
    # 1,054 portable documents: 0 modules reach it" (``adcp-client-python-10l.78``) and
    # quoted §4's sentence that "rung 4 always answers, because a branch always has an
    # index" -- and both halves were true of bundle 3.2 and of nothing wider.  A MEMBER
    # TYPE has no index, because it needs no name of its own, so its ladder is a chain of
    # one; ``core/targeting-overlay-requirements.json#/definitions/daypartRequirement`` on
    # bundle 3.3 is two such positions deriving
    # ``TargetingOverlayRequirementsDaypartRequirement``, and this arm answered them --
    # one VERDICT, five more documents chained behind it, 6 of the bundle's 12 refusals.
    # A measurement over one bundle is an observation and not a property, and the second
    # bundle is what the goal grades (``tests/test_the_second_bundle.py``).
    #
    # **What closes that document is a rung and not this raise**
    # (:data:`REQUIREMENT_IS_THE_FALL_OF_LAST_RESORT`, :func:`_requirement_rung`): the
    # branch states, one level down, that it requires one of ``timezone_modes`` and
    # ``time_granularity``, so it has a name available and falls to it.  **Measured over
    # bundle 3.3's 1,138 portable documents with that rung in force: 0 modules reach this
    # arm**, which is the same reading as before and now over both bundles rather than one.
    # It is kept for the reason it always was: the positions that are NOT branches have one
    # rung each, two of them could in principle spell alike with nothing to lengthen by,
    # and §9 says a crash is not an outcome.
    #
    # **The kind is HAND-WRITTEN and this row did not derive it, deliberately.**  §9's
    # test makes it a VERDICT and not a deferral -- two positions of one document spelling
    # alike at every rung and every length is a fact about that document's own titles and
    # keys, and no unwritten row would clear it -- but ``compiler.kind_for("title", …)``
    # answers DEFERRED at every position, because ``title``'s cell is a lowering effect.
    # So the kind cannot be read off a cell here, and minting a different one to make the
    # count fall would be the ninth hand-minted verdict wearing a derivation's clothes.
    # Filed as a numbered request instead; the arm is unreachable, so no report moves
    # either way.
    at = next(p for p in chains if p in {q for ps in unresolved.values() for q in ps[1:]})
    return Refusal(
        "title",
        at,
        f"two nodes in this document derive the class name {spelled[at]!r}",
        kind=Kind.VERDICT,
    )


def _lengthened(
    chains: Mapping[str, tuple[str, ...]],
    occupied: frozenset[str],
    surface: frozenset[str] = frozenset(),
    exports: frozenset[str] = frozenset(),
    subjects: frozenset[str] = frozenset(),
    declaring: frozenset[str] = frozenset(),
) -> tuple[dict[str, str], dict[str, list[str]]]:
    """§4's collision rule run to a fixed point: the names, and the groups still COLLIDING.

    A group is the positions on one name, and the name collides when two positions share
    it, OR an import holds it -- ``occupied``, which is the namespace half §4's rule never
    stated -- OR another module of the DOMAIN exports it and one of these positions is
    exported too (``surface`` narrowed by ``exports``, which is :data:`COLLISION_SCOPE`)
    -- OR the name is a SUBJECT the bundle named and one of these positions would DECLARE
    a second type under it (``subjects`` narrowed by ``declaring``, which is
    :data:`SUBJECT_SCOPE`).  A group of one is therefore a real answer here and not an
    empty set: the one position is colliding with something that cannot move.

    **The domain arm is asked per GROUP and not per name**, which is what keeps it from
    reaching a position §1 says nothing about: a lone group whose position is not exported
    is not colliding however the domain spells that name, and a group of two already
    collides on the module scope alone.

    **THE SUBJECT ARM IS NARROWED TO THE POSITIONS THAT DECLARE, and that narrowing is the
    whole difference between §3a's rule and a ban on the word** (§3a step 3;
    :data:`SUBJECT_SCOPE`).  §3a's answer where two positions are one type is an ALIAS --
    "a restated title that a consumer needs is an alias at its position, never a second
    class" -- so a position BINDING the subject's own class may spell the subject's name
    and a position declaring a second type under it may not.  Measured over this bundle,
    the two sides are disjoint and the defect is entirely on one of them: of the 31 sites
    where a titled root's symbol was bound in another module, **0 shared that root's
    admitted key and 31 did not**, so every one of them was a second subject wearing the
    first's name and none was an honest second spelling.

    ONE reading with two readers, which is why it is split out: :func:`spell` turns a
    surviving group into the refusal, and :func:`spell_the_rungs` turns it into the set of
    positions that fall to their next rung.  Asked twice, the second ask would be a second
    reading of "which positions cannot be told apart", and the refusal and the fall would
    be free to disagree about the set.
    """
    depth = dict.fromkeys(chains, 1)
    while True:
        spelled = {p: spelling(chains[p], depth[p]) for p in chains}
        groups: dict[str, list[str]] = {}
        for pointer, name in spelled.items():
            groups.setdefault(name, []).append(pointer)
        colliding = {
            name: ps
            for name, ps in groups.items()
            if len(ps) > 1
            or name in occupied
            or (name in surface and any(p in exports for p in ps))
            or (name in subjects and any(p in declaring for p in ps))
        }
        lengthened = False
        for group in colliding.values():
            for pointer in group:
                if depth[pointer] < len(chains[pointer]):
                    depth[pointer] += 1
                    lengthened = True
        if lengthened:
            continue
        # **Every group that is still colliding, the lone occupied ones included.**  It
        # returned only the groups two positions share, which made an import a collider
        # on the LENGTHEN axis and not on the FALL one: a position alone on a name an
        # import holds, with no ancestor left to spend, was reported as resolved and kept
        # the name -- 56 of them over this bundle, each a subclass declared under the
        # symbol its own module imports.  What the two readers do with a lone group
        # differs and is each one's own business: :func:`spell_the_rungs` falls it to its
        # next rung, and :func:`spell` keeps it rather than refusing (both say so).
        return spelled, colliding


#: §4's rung rule, in the section's own words.  QUOTED by the checks that grade it, so the
#: sentence the code states and the sentence a check reports against are one string.
RUNG_FALL = (
    "where a rung derives one name for two branches it has not identified either, so "
    "both fall to the next rung; and a branch colliding with its own document ROOT loses "
    "the name -- the root keeps it, because D5 fixes a document's one exported symbol, "
    "and the branch falls the same way any colliding rung does (section 4)"
)


def spell_the_rungs(
    ladders: Mapping[str, tuple[tuple[str, ...], ...]],
    occupied: frozenset[str] = frozenset(),
    surface: frozenset[str] = frozenset(),
    exports: frozenset[str] = frozenset(),
    subjects: frozenset[str] = frozenset(),
    declaring: frozenset[str] = frozenset(),
) -> dict[str, str] | Refusal:
    """§4's two naming axes together: LENGTHEN first, and FALL where lengthening is spent.

    :data:`COLLISION` is the first axis and :data:`RUNG_FALL` the second.  A position
    starts at its first rung; :func:`_lengthened` spends ancestor segments until no name
    collides; and a group that still collides falls -- every member of it that has a
    rung left takes the next one and starts lengthening again.

    **A NAME ANOTHER MODULE OF THE DOMAIN EXPORTS is a third thing a position can collide
    with, and it reaches both axes for the same reason an import does** (§1's amendment,
    2026-10-30; :data:`COLLISION_SCOPE`).  The six it answers over this bundle are one
    shape, and §4 already decides them with no new rung: an async response's ROOT named
    ``<Task>Submitted`` against the same-named BRANCH of the corresponding sync response.
    The root's ladder has exactly one rung -- D5 fixes a document's exported symbol -- so
    it has nothing to advance and nothing to lengthen, and the branch beside it is the only
    side that can move, which is §4's root clause one scope out: "it is ANOTHER document's
    name, which this module has no standing to move".  Both names are the documents' own:
    ``media-buy/create-media-buy-async-response-submitted.json`` is titled "Create Media
    Buy - Submitted" and ``media-buy/create-media-buy-response.json``'s ``/oneOf/2`` is
    titled ``CreateMediaBuySubmitted`` and pins ``status: "submitted"``, so the branch
    falls to rung 2 and its own pin answers.

    **An IMPORT is one of the things a position can collide with, on BOTH axes.**  A
    module's namespace is its declarations and what it imports, so ``occupied`` is part of
    §4's "derive the same name" and not a second rule beside it -- and §4 already decides
    what a position colliding with something that cannot move does: it is the root clause
    one notch over, the side that can move moves, "the same way any colliding rung does".
    The axis it crossed only one of is what shipped 56 names bound twice: ``occupied`` was
    read when deciding whether to LENGTHEN and dropped before deciding whether to FALL, so
    a bare-``$ref`` branch deriving its target's own symbol -- a chain of one, nothing to
    prepend -- was reported resolved and declared a subclass under the name its module
    imports.  Those positions have three rungs below the one they took.

    **The ROOT is not special-cased and must not be.**  "The root keeps the name" is not a
    clause here: a root's ladder has exactly ONE rung, because D5 fixes a document's
    exported symbol, so it has nothing to advance and the branch beside it is the only
    side that can move.  §4's sentence is the CONSEQUENCE of the ladder's shape, and
    writing it as a test on the pointer ``""`` would be a second statement of D5 for the
    two to disagree through.

    **Lengthening is tried before falling**, which is §4's order and not a preference: the
    collision rule is stated for every position and the fall is stated for the case where
    "these chains are one segment with nothing to lengthen by".  A branch that can
    lengthen keeps the name its best rung derives, so no identity is given up while a
    cheaper fix is available -- measured, that keeps every one of this bundle's existing
    branch names except the three §4 names.

    **A SUBJECT THE BUNDLE NAMED is a fourth thing a position can collide with, and it
    reaches both axes for the same reason the other three do** (§3a step 3;
    :data:`SUBJECT_SCOPE`).  It cannot move -- the name is another document's, and §4's
    root clause already says "this module has no standing to move it" -- so only this
    module's declaring positions do, and they do it by §4's own two axes with no new rung:
    ``protocol/get-adcp-capabilities-response.json#/properties/media_buy`` spends its one
    ancestor segment and becomes ``GetAdcpCapabilitiesResponseMediaBuy``, which is what
    the position always had to spell to be honest about what it is.

    It TERMINATES because each fall strictly advances at least one position's rung index
    and :func:`branch_rungs` is finite and duplicate-free; when no member of a sharing
    group has a rung left, the refusal is :func:`spell`'s and says what it always said.
    **The subject arm does not change that, because ``subjects`` is a function of the
    BUNDLE and is constant across every round of both axes** -- unlike the domain census,
    which ``emit.domain_exports`` has to accumulate to keep monotone.  A set that does not
    move cannot make a fixed point oscillate.
    """
    rung = dict.fromkeys(ladders, 0)
    while True:
        chains = {p: ladders[p][rung[p]] for p in ladders}
        spelled, shared = _lengthened(chains, occupied, surface, exports, subjects, declaring)
        if not shared:
            return spelled
        fell = False
        for group in shared.values():
            for pointer in group:
                if rung[pointer] + 1 < len(ladders[pointer]):
                    rung[pointer] += 1
                    fell = True
        if not fell:
            return spell(chains, occupied, surface, exports, subjects, declaring)


def resolved(decided: ir.TypeRef, symbols: Mapping[str, str]) -> ir.TypeRef:
    """One decided type with every LOCAL pointer replaced by the symbol it names.

    Recursive over the type TREE and not over a rendered string: a container carries its
    members in ``of`` with a mapping's key beside them, so ``list[X] | None`` reaches
    ``X`` through two levels and neither can be read off ``path``.

    A local path that is NOT in the table is a symbol another module declares -- a
    cross-document import, which §5's ``$ref`` row makes an import of the TARGET's own
    symbol -- and it is left exactly as the walk decided it.  That is the one slot where
    a pointer and a name share a field, and the table is what tells them apart.
    """
    out = decided
    if decided.local and decided.path in symbols:
        out = replace(out, path=symbols[decided.path])
    if decided.of:
        out = replace(out, of=tuple(resolved(inner, symbols) for inner in decided.of))
    if decided.key is not None:
        out = replace(out, key=resolved(decided.key, symbols))
    return out


def _bound(declaration: ir.Declaration, symbols: Mapping[str, str]) -> ir.Declaration:
    """One declaration with every symbol slot bound: its own name, its bases, its
    branches, and every type it holds."""
    if isinstance(declaration, ir.ClassDecl):
        return replace(
            declaration,
            name=symbols[declaration.name],
            fields=tuple(
                replace(f, type=resolved(f.type, symbols)) for f in declaration.fields
            ),
            extras=(
                None
                if declaration.extras is None
                else resolved(declaration.extras, symbols)
            ),
            bases=tuple(resolved(b, symbols) for b in declaration.bases),
            branches=(
                None
                if declaration.branches is None
                else tuple(resolved(b, symbols) for b in declaration.branches)
            ),
        )
    if isinstance(declaration, ir.EnumDecl):
        return replace(declaration, name=symbols[declaration.name])
    if isinstance(declaration, ir.ValuesDecl):
        # **A value list binds no POINTER**, so there is no symbol slot to bind: §3a's
        # constant is named from its own members (``lower.enum.values_name``) and is
        # created by :func:`the_value_lists` AFTER this rewrite, so this arm is reached by
        # no declaration of this bundle.  It is written rather than left to the fall
        # through below for the reason that fall through states: a kind with no arm takes
        # another kind's rewrite silently.
        return declaration
    if isinstance(declaration, ir.AliasDecl):
        return replace(
            declaration,
            name=symbols[declaration.name],
            type=resolved(declaration.type, symbols),
        )
    if isinstance(declaration, ir.RootBinding):
        held = declaration.declaration
        return replace(
            declaration,
            symbol=symbols[declaration.symbol],
            # The two kinds a root binding can wrap, narrowed by construction rather than
            # by an ``isinstance`` standing in for a branch: ``RootBinding.declaration``
            # is ``AliasDecl | EnumDecl`` and each has its own rewrite above.
            declaration=(
                replace(
                    held,
                    name=symbols[held.name],
                    type=resolved(held.type, symbols),
                )
                if isinstance(held, ir.AliasDecl)
                else replace(held, name=symbols[held.name])
            ),
        )
    if isinstance(declaration, ir.RootModelDecl):
        # §7's third root shape, whose name and whose wrapped type are bound exactly as a
        # class's are.  An ARM of its own and not the fallthrough, because the fallthrough
        # is what the type checker reads as "everything left", and adding a declaration to
        # ``ir.Declaration`` without one here is how a new kind silently takes another
        # kind's rewrite -- which is what mypy reported the moment ``RootModelDecl`` joined
        # the union.
        return replace(
            declaration,
            name=symbols[declaration.name],
            type=resolved(declaration.type, symbols),
            branches=(
                None
                if declaration.branches is None
                else tuple(resolved(b, symbols) for b in declaration.branches)
            ),
        )
    return replace(
        declaration,
        base=resolved(declaration.base, symbols),
        branches=tuple(resolved(b, symbols) for b in declaration.branches),
    )


def _enumeration(declaration: ir.Declaration) -> ir.EnumDecl | None:
    """The ENUMERATION one declaration holds, or ``None``.

    Two declarations hold one: an :class:`codegen.ir.EnumDecl` is itself, and a
    :class:`codegen.ir.RootBinding` wraps one where the enumeration is a document's root
    (that class's own docstring says why a root enum needs the wrapper).  A reader asking
    "what does this module declare over this value list" has to see both, and the root is
    exactly the position §3a's two title conflicts sit at -- ``enums/catalog-action.json``
    and ``enums/creative-action.json`` are both roots of their own documents.
    """
    if isinstance(declaration, ir.EnumDecl):
        return declaration
    if isinstance(declaration, ir.RootBinding) and isinstance(
        declaration.declaration, ir.EnumDecl
    ):
        return declaration.declaration
    return None


def _constructed(
    declaration: ir.Declaration, found: ir.EnumDecl, values: str
) -> ir.Declaration:
    """``declaration`` with its enumeration CONSTRUCTED from the value list ``values``.

    ``found`` is :func:`_enumeration`'s answer for ``declaration``, handed in rather than
    read again: a :class:`codegen.ir.RootBinding` wraps an ``AliasDecl`` or an
    ``EnumDecl``, only one of those has a value list to construct from, and the caller has
    already asked which.  So the ROOT arm rewraps and the other arm IS ``found`` -- which
    is why nothing here has to narrow ``declaration`` a second time.
    """
    built = replace(found, values=values)
    return replace(declaration, declaration=built) if isinstance(
        declaration, ir.RootBinding
    ) else built


def the_value_lists(
    declarations: tuple[ir.Declaration, ...],
) -> tuple[ir.Declaration, ...]:
    """§3a's value list written ONCE, for two types of one module over one value list.

    ``docs/plan/architecture.md`` §3a: "the **VALUE LIST** is a module-level constant in
    the catalogue layer, written once per distinct member set; the **NAMED TYPE** is
    constructed from it at each position that needs one, keeping the name §4 derives and
    keeping the types distinct."

    **This is the SAME-MODULE case and the catalogue does not reach it** (§3a's scope
    rule: "referenced from one document -> that document's module").  The cross-document
    case is ``compiler.Module.value_lists``, filled by the run from the catalogue; this
    one is decided here because only here is the answer knowable without predicting it:

        §4's content dedup keys on NODE EQUALITY and compares a node's ``annotations``, so
        two positions of one document stating one value list under different descriptions
        are two classes to it -- and two positions stating the identical node are ONE.
        Which of the two a group is cannot be read off the bundle: ``catalogue.identity``
        ignores annotations by §3a's own rule, so a reading there says "two classes" of
        groups §4 collapses to one.  Measured over this bundle's 21 single-document
        groups: §4 keeps 5 apart and collapses or ``Literal``-renders the other 16, and a
        prediction from the catalogue would have written 16 constants nothing uses.

    So the population is the module's OWN finished declarations, which is exact, is a
    function of the document alone -- §9's "a document's output may not depend on which
    other documents the run includes" -- and leaves nothing to invalidate.

    A declaration already CONSTRUCTED from a value list is passed over: the run's table
    answered it first, which is the cross-document case, and a second constant for the
    same members would be the restatement this function removes.

    The constant is inserted immediately BEFORE the first declaration that uses it, so a
    reader meets the value list where the first type over it is written and the module
    needs no forward reference.
    """
    # **INSIDE the function, which is ``compiler.py``'s own answer to the same cycle**
    # (``from codegen.lower.decide import decide``, and two more beside it): the member
    # naming belongs to D2's enumeration row, that row's module imports ``compiler`` for
    # §4's rules, and ``compiler`` imports this pass -- so a module-level import here
    # closes a three-module ring.  One call per MODULE, not per node, so the deferral is
    # not the per-node cost §11 objected to elsewhere.
    from codegen.lower.enum import values_name

    held: dict[tuple[Any, ...], list[int]] = {}
    for i, declaration in enumerate(declarations):
        found = _enumeration(declaration)
        if found is None or found.values is not None:
            continue
        held.setdefault(tuple(m.value for m in found.members), []).append(i)
    shared = {members: at for members, at in held.items() if len(at) > 1}
    named: dict[str, tuple[Any, ...]] = {}
    for members in shared:
        spelled = values_name(members)
        if spelled in named:
            raise BuildFailure(
                f"{spelled!r} is the name both {list(named[spelled])!r} and "
                f"{list(members)!r} spell for their value list: the separator is a "
                "character a member name can hold, so the two are not told apart -- which "
                "is a defect in this compiler and not an outcome of any document"
            )
        named[spelled] = members
    out: list[ir.Declaration] = []
    written: set[str] = set()
    for declaration in declarations:
        found = _enumeration(declaration)
        if found is None or found.values is not None:
            out.append(declaration)
            continue
        members = tuple(m.value for m in found.members)
        if members not in shared:
            out.append(declaration)
            continue
        spelled = values_name(members)
        if spelled not in written:
            written.add(spelled)
            out.append(ir.ValuesDecl(name=spelled, kind=found.kind, values=members))
        out.append(_constructed(declaration, found, spelled))
    return tuple(out)


def _at(declaration: ir.Declaration) -> str | None:
    """The POINTER a declaration was declared at, which is what its name slot holds
    until this pass runs.  ``None`` for the one declaration that binds no name --
    :class:`codegen.ir.UnionInstall`, whose two statements are about symbols the module
    already declares."""
    if isinstance(
        declaration, ir.ClassDecl | ir.EnumDecl | ir.AliasDecl | ir.RootModelDecl
    ):
        return declaration.name
    if isinstance(declaration, ir.RootBinding):
        return declaration.symbol
    return None


def names_a_declaration(
    declaration: ir.Declaration, imports: Iterable[tuple[str, str]]
) -> str | None:
    """``X = Y``: the POINTER or SYMBOL this declaration merely NAMES, or ``None`` where
    it states a type of its own.

    §1 (2026-11-03): "**A gate on this counts DECLARATIONS, not ``id()`` and not names**
    ... an ``X = <bare Name>`` is a binding, not a declaration", and "the other spellings
    are the names of positions that REFERENCE it, and a position that references a class
    does not name it".  This is that sentence as a predicate, and it is HERE because the
    two readers must not drift: :func:`assign` drops the export and relocates it to the
    declaring position, and :attr:`codegen.ir.Module.binds` records the answer so the gate
    grades the same reading the compiler applied.

    **The test is for the WHOLE STATEMENT being a bare name**: an alias whose
    :class:`codegen.ir.TypeRef` holds a path and nothing else -- no container, no
    arguments, no literals, no members, no facts, no format, no validators -- AND which
    carries no description, says only "this position is that type".  That is §4's identity
    binding (:func:`adopt`) and the cross-document ``$ref`` at a named node, and both
    render as ``X = Y``, so ``X is Y`` at run time.

    **The DESCRIPTION is in the test and the measurement is why.**  An alias that carries
    one renders ``X = Annotated[Y, Field(description=...)]``, which is a different OBJECT
    from ``Y`` and a sentence this position states -- ``core.Qualifier`` over
    ``core.CanonicalMetricQualifier`` is the worked case, and reading it as a binding
    dropped a name that is nobody's second path.  A description changes no admitted
    instance, so it is out of §3a's entry key; it is a statement made HERE, so it is in
    this one.  The two tests answer different questions and must not be made to agree.

    **A D5 CONSTRAINTS ALIAS IS NOT A BINDING, and that is the whole of why reading 4 and
    reading 6 do not both claim the same symbol.**  ``DaastOffset =
    adcp.types.constraints.StrMatching38E7F7CC`` names a module the BUNDLE has no position
    in: the alias module is one spelling of a constraint set, minted by D5 over the whole
    run, so §1's "every one of those names IS the name derived at its own declaring
    position, so there is no referencing position to drop and nothing to rename" applies
    and the statement is a declaration.  What tells the two apart with no list is where
    the named symbol comes from -- this module (``local``), or a sibling module the walk
    imported for a cross-document reference (``imports``) -- and a dotted path into the
    alias module is neither.
    """
    if not isinstance(declaration, ir.AliasDecl):
        return None
    held = declaration.type
    if not held.path or any(
        (
            declaration.description,
            held.container,
            held.of,
            held.key is not None,
            held.literals,
            held.members,
            held.facts,
            held.format,
            held.validators,
        )
    ):
        return None
    if held.local:
        return held.path
    return held.path if held.path in {symbol for _, symbol in imports} else None


def _reaching(
    exports: Mapping[str, str],
    binds: Mapping[str, str],
    at: Mapping[str, ir.Declaration],
) -> dict[str, list[str]]:
    """Declaring pointer -> the EXPORTED pointers that reach it through a binding.

    §1's "one class declared once and exported twice", counted: a binding chain is
    followed to its end, so ``X = Y`` beside ``Y = Z`` charges ``Z``, and a target that is
    not a declaration of THIS module is left out -- the module that declares it is the one
    that can export it, and §9 forbids this pass to ask which other documents a run holds.

    ``at`` is the walk's own pointer table, which is what tells a LOCAL pointer from the
    SYMBOL a cross-document reference names: :func:`names_a_declaration` returns whichever
    the type carried, and only the first is a position of this module.
    """
    out: dict[str, list[str]] = {}
    for pointer in exports:
        held, seen = pointer, {pointer}
        while held in binds and binds[held] in at and binds[held] not in seen:
            held = binds[held]
            seen.add(held)
        if held != pointer:
            out.setdefault(held, []).append(pointer)
    return out


def the_surface_exports(
    pointer: str, declaration: ir.Declaration, hops: Mapping[str, object]
) -> str | None:
    """§1's export set, as the KIND one position is exported under, or ``None``.

    §1 (2026-10-30) fixes it as **every document ROOT, every union BRANCH and every D2
    type ALIAS**, and reading 6 adds the fourth arm on 2026-11-07
    (:data:`THE_INNER_EXPORT`): **every untitled INNER node too, under a word of its own.**
    The four arms are read off what the position IS and never off its name:

    * the ROOT is the empty pointer, which is D5's one exported symbol per document;
    * a BRANCH is a position whose hop is a :class:`Branch`, which is what §4's union row
      builds a class per;
    * a D2 ALIAS is an :class:`codegen.ir.AliasDecl` or the :class:`codegen.ir.RootBinding`
      wrapping one -- §4's "a scalar at a root is a module-level annotated alias, not a
      class" -- and §1 exports those because "an alias is a name an application writes";
    * an INNER node is a position that DECLARES a class or an enumeration and is none of
      the three above -- a property, an element, a mapping value or a ``definitions``
      entry whose node the bundle gives no title.

    **THE INNER ARM IS NOT "EVERY CLASS THE TREE DECLARES" UNDER A NEW NAME**, which was
    decided and withdrawn on 2026-10-30 "because it makes ``core.Status`` name one of
    fourteen declarations".  That withdrawal was about the WORD and not about the set: the
    name it would have exported is the position's own short symbol, and fourteen positions
    of ``core`` derive ``Status``.  Reading 6's clause supplies the word the withdrawal was
    missing -- the node's whole chain -- so the set returns with every one of those
    fourteen reachable and none of them spelled ``Status``.  :func:`assign` is where the
    word is minted, because a word needs the position's chain and a kind does not.

    What it deliberately does NOT reach is the per-module ``strict_validate`` helper, which
    is not a declaration of this pass at all, and §1's own reason stands: a domain name
    cannot stand for 241 functions and a caller reaches one through its class.

    **IT ANSWERS FOR THE POSITION AND NOT FOR THE DECLARATION, which is why the answer is
    not the export set on its own** (§1, 2026-11-03).  A position can be one of these
    four kinds and still declare nothing -- an identity binding is an ``AliasDecl``, so
    the third arm says ``alias`` for it -- and §1's one-path rule is about declarations.
    :func:`assign` relocates such an export onto the position that DECLARES the class,
    reading :func:`names_a_declaration`; the split is here because a kind is a property of
    one position and a relocation needs the module's whole set.

    **Here rather than in ``emit`` because the facts are here.**  §1's set is stated over
    positions and the only place a position's hop and its declaration are both in hand is
    this pass; ``emit`` holds the DOMAIN's half of the question (which names other modules
    export) and hands that in as names, which is the seam :data:`COLLISION_SCOPE`
    describes.  The answer is recorded on :attr:`codegen.ir.Module.exports` so that the
    surface, the collision rule and the check that grades them read ONE reading --
    measured, a second derivation over the emitted TEXT reads a branch as "a class one of
    whose bases this module declares" and misses a nested ``A | B`` union's arms, which
    subclass nothing local.

    The BRANCH arm is therefore the hop and never the base list: ``A | B`` at a nested
    property declares a class per arm with no shared base, and
    ``core/targeting_overlay_support.py``'s ``PlacementSelection`` is one of them -- a
    §1 collision with ``core/placement-selection.json``'s own root that a reading of the
    text cannot see.
    """
    if pointer == "":
        return "root"
    if isinstance(hops.get(pointer), Branch):
        return "branch"
    if isinstance(declaration, ir.AliasDecl | ir.RootBinding):
        return "alias"
    if isinstance(declaration, ir.ClassDecl | ir.EnumDecl):
        return INNER
    return None


def the_published_spellings(
    hops: Mapping[str, Hop],
    symbols: Mapping[str, str],
    root: str,
    occupied: frozenset[str],
) -> dict[str, str]:
    """:data:`UPSTREAM_TITLE_CASE` over one module: upstream's spelling -> OUR symbol.

    **THE POPULATION IS THE DOCUMENT ROOT, and that is MEASURED and not a convenience.**
    A :class:`Root` and a titled :class:`Branch` are the only two positions this compiler
    names from a phrase the bundle wrote -- a property KEY, an element and a mapping value
    are spelled from a snake-case key, where ``str.title()`` and :func:`class_name` agree
    by construction -- so the branch was the natural second arm.  Upstream's own tree
    refutes it: graded per module against ``2954b258b``, its counterpart module carries
    this spelling for **101 of the 101** roots the rule fires on and for **0 of the 11**
    titled branches, and OURS for none of either.  Upstream named a NESTED model from the
    field path it is reached through, so a title's normalisation is a claim about a name
    that generator never minted there, and minting one would be this rule inventing 11
    spellings nobody published.  ``tests_emit/test_the_published_spelling_is_emitted.py``
    is where both halves of that are asserted, so the branch arm cannot return unnoticed.

    **THE GUARD IS THAT OUR SYMBOL IS STILL THE TITLE'S OWN NAME, and it is what keeps
    this a rule about a title rather than a guess about a spelling.**  §4's collision rule
    can lengthen a position past its title, and the emitted symbol is then not what the
    title derives -- so upstream's normalisation of that title would be a claim about a
    name neither compiler gave this position, and the rule says nothing.
    :func:`spelling`'s keyword suffix is screened out by the same equality, with no second
    reading of what a keyword is.

    ``root`` is :attr:`codegen.ir.Module.root`, which is the symbol the root resolves to
    where this module DECLARES nothing at ``""`` -- §3a's repeated-DOCUMENT layer, where a
    non-home member re-exports the home's class.  Upstream's spelling is owed at that
    module too: the machinery imports it from the module its own layout put the document
    at, and the ``bundled/`` and ``mcp/2026-07-28/`` members of ``protocol/`` and
    ``sponsored-intelligence/`` are exactly such positions.

    ``occupied`` is every name the module's namespace already holds -- the symbols it
    declares, the symbols it imports, and the renderer's own carriers.  A word one of
    those has taken is NOT bound, and that is not a drop: the name already resolves in
    this module to something else, and shadowing a declaration to publish a second
    spelling of a third class is the one outcome worse than the absence.
    """
    hop = hops.get("")
    if not isinstance(hop, Root):
        return {}
    ours = symbols.get("") or root
    theirs = upstream_class_name(hop.title)
    if not ours or theirs is None or theirs in occupied or ours != class_name(hop.title):
        return {}
    return {theirs: ours}


def assign(
    mod: Module,
    carriers: frozenset[str] = frozenset(),
    surface: frozenset[str] = frozenset(),
    declared: Mapping[str, str] = {},
    abroad: frozenset[str] = frozenset(),
    subjects: frozenset[str] = frozenset(),
) -> ir.Module | Refusal:
    """The pass: every declaration of one module given the name §4 derives for it.

    ``mod`` is the walk's own module value, ``compiler.Module``, and the import of it is
    under ``TYPE_CHECKING``: the arrow at RUN time runs one way (``compiler`` imports this
    module for §4's rules and nothing here imports it back), so the annotation is the only
    thing that needs the name and the type checker gets it.  What this reads is four
    fields -- the declarations in declaration order, the hops, the adoptions and the
    imports -- and nothing else of the walk.

    ``carriers`` is the other half of the module's NAMESPACE: the names the renderer
    brings in, which the walk does not report (``render.CARRIERS``, handed in by the run
    for :func:`field_name`'s reason -- §8 bans ``pydantic`` under ``lower/`` and the one
    module allowed to read the model layer derives the set).  It is empty by default,
    which spells every position by §4 alone; the run passes it, so a class cannot take
    the name of an import the module's own fields are annotated with.

    THE WHOLE OF THE DEDUP IS HERE, and it is §4's own sentence: declarations whose
    NODES are equal are one class, declared under the first pointer in document order,
    and every later pointer binds its own derived name to it by identity.  The walk
    records the equality -- it must, because a second occurrence's CHILDREN are not
    lowered at all and a declaration it never made has no name to derive -- and this
    pass is what turns the record into names: it decides nothing from the order the
    walk iterated in, because the adopting pointer takes the name ITS OWN position
    derives and the declaring pointer takes its own.

    **The names are decided over the WHOLE module and not one declaration at a time**,
    because §4's collision rule is about a SET: the positions sharing a derived name all
    lengthen, so no position's name can be settled before every position's chain is
    known.  So this fold collects the chains (:func:`segments`) and :func:`spell` decides
    the names from them -- and the refusal two indistinguishable positions earn is
    :func:`spell`'s, where the whole set is in hand, rather than a first-come check that
    would name whichever the walk reached second.

    :data:`SCOPE` is the DEDUP's scope and the signature still holds it: two nodes are one
    class within one module and nowhere else.

    ``declared`` is §3a's JUDGED NAME for a catalogue entry declared at one of this
    module's pointers (``codegen/vocabularies.py``), and it enters as an EXTRA FIRST RUNG
    rather than as an override.  §3a's table admits "a stated name lengthened to avoid an
    existing class -- that is the collision rule, not a mint", and a rung is how this pass
    says that: a rung of ONE segment has nothing to prepend, so §4's own axes answer a
    collision by FALLING to the position's own chain -- the name this pass would have given
    it with no row at all.  Nothing is special-cased and no name is forced past a
    collision; the judgement is preferred and §4 still decides.

    :data:`COLLISION_SCOPE` is the COLLISION rule's, which §1's amendment widened to the
    domain for the positions the surface exports, and the signature holds that too --
    ``surface`` is a set of NAMES.  Nothing here can ask which documents the run was given,
    so §9's prohibition is structural rather than observed: ``emit`` reads the domain's
    exported names off the BUNDLE, and §9's own ruling is that the run is not the bundle.

    ``subjects`` is §3a STEP 3 (:data:`SUBJECT_SCOPE`): the names the BUNDLE gives its
    document roots, MINUS this document's own, so a position that would declare a second
    type under a subject's name lengthens by §4's axes instead.  It is a set of NAMES for
    ``surface``'s reason and under the same ruling, and the exemption is subtracted by the
    CALLER because only the run knows which subject this module is the home of.

    **It is a reservation and not an override, which is what makes step 3 constructive
    rather than a gate.**  Nothing here looks at an emitted name to see whether it claimed
    a subject; the claim is simply not among the names the collision rule leaves available.
    §3a: "a census over the output can only ever confirm a decision made once."
    """
    #: The declarations §4's dedup leaves unwritten: an adopting position that derives NO
    #: name of its own, and one whose derived name IS the declaring class's.  The first
    #: has nothing to bind and the second would be ``X = X``; both take the class symbol
    #: DIRECTLY, which is what mapping the adopting pointer onto the declaring symbol
    #: does for every type that names it.
    degenerate: set[int] = set()
    #: Pointer -> §4's RUNGS for it, best first (:func:`ladder`).  One rung for every
    #: position but a branch; :func:`spell_the_rungs` walks both axes.
    ladders: dict[str, tuple[tuple[str, ...], ...]] = {}
    #: An adopting pointer that binds no name of its own -> the pointer whose class it
    #: takes.  Resolved after :func:`spell`, because the symbol it takes is not decided
    #: until the declaring position's own name is.
    takes: dict[str, str] = {}
    #: Pointer -> the kind §1 exports it under, for the pointers its export set reaches.
    #: Two readers: ``surface`` is narrowed to these pointers (:data:`COLLISION_SCOPE`),
    #: and the symbols are recorded on :attr:`ir.Module.exports` for the surface itself.
    exports: dict[str, str] = {}
    #: Every pointer this module BINDS rather than declares -> the pointer or symbol it
    #: names (:func:`names_a_declaration`), for :attr:`ir.Module.binds`.
    binds: dict[str, str] = {}
    #: **Reading 6's INNER positions -> the chain its clause words the export from**
    #: (:data:`THE_INNER_EXPORT`).  Held APART from ``exports`` until the relocation below
    #: has run, which is the whole of the ordering this record exists for: the relocation
    #: asks whether a declaration is exported TWICE, and an inner export added before it
    #: would answer that question with its own arrival -- renaming 20 names of this bundle
    #: that reading 6 already holds for, where the clause adds none.
    inner: dict[str, tuple[str, ...]] = {}
    #: **Reading 6's inner POINTER -> the word the domain surface publishes it under**,
    #: where that word is not the private symbol (:data:`THE_INNER_EXPORT`).  Keyed by
    #: pointer here and rebound to the SYMBOL on the way out, for :attr:`ir.Module.exports`'
    #: reason: what the surface writes is ``<symbol> as <word>`` and both halves are names.
    published: dict[str, str] = {}
    for i, declaration in enumerate(mod.declarations):
        pointer = _at(declaration)
        if pointer is None:
            continue
        #: §1: "a position that references a class does not name it".  The pointer the
        #: binding names, or ``None`` where this position declares its own type.
        named = names_a_declaration(declaration, mod.imports)
        if named is not None:
            binds[pointer] = named
        kind = the_surface_exports(pointer, declaration, mod.hops)
        if kind is not None and kind != INNER:
            exports[pointer] = kind
        rungs = ladder(pointer, mod.hops)
        if isinstance(rungs, Refusal):
            return rungs
        #: The dedup comparison reads the FIRST rung, which is the name this position
        #: derives before any collision is known -- §4's dedup is about two positions
        #: stating the same NODE, and a rung is about telling two names apart, so the
        #: question this asks is settled before the rung axis is walked.
        chain = rungs[0]
        declares = mod.adopted.get(pointer)
        #: Compared over the WHOLE chain, which is this position's own longest spelling:
        #: two positions whose paths spell alike derive one name at every length, so the
        #: degenerate arm is the same arm it was when the fold returned that spelling.
        if declares is not None and "".join(chain) in (
            "",
            "".join(ladders[declares][0] if declares in ladders else ()),
        ):
            takes[pointer] = declares
            degenerate.add(i)
            continue
        #: Reading 6's clause reaches a position that DECLARES, so it is recorded on the
        #: far side of the degenerate arm above: an adoption binding no name of its own
        #: declares nothing for the clause to export and has no chain to word it from.
        if kind == INNER:
            inner[pointer] = chain
        #: §3a's judged name as rung 0, read AFTER the dedup arm above: the comparison
        #: there is §4's "two positions stating the same NODE", which a name the catalogue
        #: judged has no part in.
        name = declared.get(pointer)
        ladders[pointer] = ((name,), *rungs) if name is not None else rungs
    # **§1's one-path rule, as the RELOCATION it is (2026-11-03).**  "What remains for this
    # rule is the case it was written for -- one class declared once and EXPORTED TWICE --
    # and there the surface keeps only the declaring position's spelling.  **Applying it is
    # not purely subtractive:** for some of these the name the rule keeps is not currently
    # exported at all, because the surface assigns no kind to a declaration at a property
    # or element position, so the rename adds a name as well as removing ones."
    #
    # EXPORTED TWICE is the scope and it is the whole of why this is not simply
    # ``names_a_declaration``'s complement: a declaration the surface reaches at exactly
    # ONE path satisfies reading 6 whatever the spelling of that path is, and §1 names no
    # second name to prefer it to.  Measured over this bundle, dropping that clause renames
    # 26 further positions that reading 6 already holds for.
    for pointer, found in _reaching(exports, binds, mod.at).items():
        if len(found) + (pointer in exports) < 2:
            continue
        #: The declaring position's own kind where §1's three arms give it one, and the
        #: referencing position's otherwise -- which is the sentence above: the surface
        #: carried this class because a position reached it, and what changes is the name.
        kind = exports.get(pointer) or exports[found[0]]
        for reference in found:
            del exports[reference]
        exports[pointer] = kind
    # **AND THE SAME RULE ACROSS A MODULE BOUNDARY**, where there is nothing to add: a
    # named node that is a bare ``$ref`` to another document binds the symbol that
    # document declares, so the class is already on the surface at the DECLARING module's
    # path and this position's name is the second one §1 forbids.  ``abroad`` is what the
    # referenced modules export, which only the run can answer -- and §9 is satisfied for
    # :data:`COLLISION_SCOPE`'s reason: a reference target is in the closure of EVERY run
    # that holds this document, so the answer does not depend on the argument list.
    for pointer in [p for p in exports if p in binds and binds[p] in abroad]:
        del exports[pointer]
    # **READING 6's INNER CLAUSE, APPLIED LAST AND ONLY WHERE NO EXPORT ALREADY REACHES THE
    # CLASS** (:data:`THE_INNER_EXPORT`).  The clause adds a PATH to a class no path
    # reaches; a class some other position already exports has its one path, and a second
    # one would break the very reading this clause belongs to -- "no second way reaches the
    # same class".
    #
    # **MEASURED, and this is the error the uniform rule most plausibly introduces.**  Over
    # this bundle 1,362 positions answer ``inner`` and **20 of them declare a class the
    # surface ALREADY carries** -- §4's content dedup put the class at the first pointer in
    # document order and the surface exports the ADOPTING position's word, because the
    # relocation above leaves a declaration that is reached at exactly one path alone.
    # ``adagents``'s ``TagsValue`` is one: it is declared at
    # ``#/oneOf/1/properties/tags/additionalProperties`` and reached today at
    # ``adcp.types.adagents.SignalTagsValue``.  So the population of the clause is 1,342
    # and not 1,362, and an export per declaring POSITION rather than per unreached CLASS
    # would hand those 20 objects a second domain path.
    #
    # ``_reaching`` is the same reading the relocation above makes -- a binding chain
    # followed to the declaration it ends at -- so "already reached" and "exported twice"
    # cannot come to disagree about what reaches what.
    reached = frozenset(exports) | frozenset(_reaching(exports, binds, mod.at))
    for pointer, chain in inner.items():
        if pointer in reached:
            continue
        exports[pointer] = INNER
        #: The WHOLE chain, which is :data:`THE_INNER_EXPORT`'s transitive reading of "its
        #: parent's name and its key".  :func:`spelling` and not a join, because a chain
        #: whose join is a Python keyword is a module that does not parse and that reading
        #: is already taken once.
        published[pointer] = spelling(chain, len(chain))
    spelled = spell_the_rungs(
        ladders,
        carriers | {symbol for _, symbol in mod.imports},
        surface,
        # **The RELOCATED pointers are in §1's domain scope and the dropped ones are not**,
        # because :data:`COLLISION_SCOPE` is stated over "a position the surface exports"
        # and the surface now exports the declaring position.  A set that still held a
        # dropped name would lengthen a sibling against a name no module publishes, and
        # one that missed an added one would publish two.  So the relocation above runs
        # BEFORE the names are spelled rather than on the way out.
        #
        # **AND READING 6's INNER POSITIONS ARE NOT IN IT, because their SYMBOL is not the
        # name the surface publishes** (:data:`THE_INNER_EXPORT`).  :data:`COLLISION_SCOPE`
        # is stated over "a position the surface exports" and what it forbids two of is an
        # ``adcp.types.<domain>.<Name>``; an inner export's path carries the clause's WORD,
        # which is a function of the document's own path and collides with nothing, so its
        # symbol stays private and the domain rule has nothing to ask of it.
        #
        # **MEASURED: holding them in renames three private classes for a collision that
        # does not exist** -- ``brand/get_brand_identity_response``'s ``Tone``,
        # ``core/event_surface``'s ``Category`` and ``core/signal_definition``'s
        # ``LookbackWindow``, each lengthened against a word ANOTHER document of its domain
        # exports, while the word this clause publishes them under is unaffected.  Reading
        # 6's own reason rules it out from the other side as well: a private symbol that
        # moved because an unrelated document of the domain holds the word is the hidden
        # coupling the clause exists to remove.
        frozenset(p for p in exports if p not in published),
        subjects,
        # **§3a step 3's narrowing: the positions that DECLARE, which is ``ladders``
        # MINUS the ones that bind.**  ``binds`` is §1's own reading -- "a position that
        # references a class does not name it" (:func:`names_a_declaration`) -- so the
        # two sides are one derivation and a position cannot be read as declaring here
        # and as binding three lines up.  §3a's answer at a restating position is "an
        # alias at its position, never a second class", and an alias is exactly what is
        # on the other side of this subtraction.
        frozenset(ladders) - frozenset(binds),
    )
    if isinstance(spelled, Refusal):
        return spelled
    symbols: dict[str, str] = dict(spelled)
    for pointer, declares in takes.items():
        symbols[pointer] = symbols[declares]
    #: :data:`UPSTREAM_TITLE_CASE` over this module, read AFTER the names are settled
    #: because the rule's own guard is that the emitted symbol still IS the title's name
    #: (:func:`the_published_spellings`).  Asked of a finished table rather than mixed
    #: into the spelling, so nothing here can move a declaration's name: what it produces
    #: is a BINDING, and the collision rule has already decided every symbol it binds.
    recased = the_published_spellings(
        mod.hops,
        symbols,
        mod.root,
        frozenset(symbols.values())
        | carriers
        | {symbol for _, symbol in mod.imports}
        | {symbols.get("", mod.root)},
    )
    return ir.Module(
        document=mod.document,
        # **The walk's own root symbol where nothing is DECLARED at the root**, which is
        # §3a's repeated-DOCUMENT layer and nothing else: ``emit.lower_document`` makes
        # such a module a RE-EXPORT of the home's class, so there is no declaration at
        # ``""`` for this pass to spell and ``mod.root`` already holds the symbol the
        # import brought in.  Every other module declares at ``""`` -- a class, an
        # enumeration under a ``RootBinding``, or an alias -- so the fallback selects
        # nothing for them, and the empty string it replaced was a module with no root.
        root=symbols.get("", mod.root),
        # §3a's value list written once, for two types of this module over one value
        # list (:func:`the_value_lists`).  AFTER the binding, because the constant is
        # named from its MEMBERS and the enumerations it serves are named from their
        # positions -- two derivations that do not interact, so the order is the one that
        # lets each read a finished input.
        declarations=(
            *the_value_lists(
                tuple(
                    _bound(d, symbols)
                    for i, d in enumerate(mod.declarations)
                    if i not in degenerate
                )
            ),
            # **Upstream's spelling, LAST and as the one alias statement this emitter
            # has** (:data:`UPSTREAM_TITLE_CASE`).  An ``ir.AliasDecl`` holding a bare
            # local symbol is what :func:`adopt` already declares for §4's content dedup,
            # and the renderer writes ``X = TheClass`` for it -- the class by IDENTITY, so
            # ``isinstance`` holds and a type checker follows it.  There is no second
            # alias spelling here and no new declaration: :func:`names_a_declaration` is
            # the predicate that says so, and :attr:`codegen.ir.Module.recased` is where
            # the run records it.
            #
            # At the END of the module rather than beside the class it names, because a
            # name the bundle did not choose is not part of the document's own reading
            # order -- and the block is sorted, so a bundle that adds a title does not
            # move a line of any other module.
            *(
                ir.AliasDecl(word, ir.TypeRef(symbol, local=True))
                for word, symbol in sorted(recased.items())
            ),
        ),
        imports=frozenset(mod.imports),
        symbols=symbols,
        adopted=dict(mod.adopted),
        # §7's ``approximations`` slot, carried through unchanged: this pass assigns
        # SYMBOLS, and a declaration names a POINTER, which naming does not move.  It is a
        # tuple here because the IR is immutable and the walk's accumulator is a list.
        approximations=tuple(mod.approximations),
        # The SECTION census beside them, carried through unchanged for the same reason:
        # this pass assigns SYMBOLS, and which pointers name a section entry is a fact
        # about the document's own text that naming does not move
        # (:attr:`codegen.ir.Module.sections`).
        sections=frozenset(mod.sections),
        # §1's export set as SYMBOLS, which is what the surface re-exports and what §1
        # forbids two of.  A degenerate adoption is absent by construction: it binds no
        # name of its own, so no pointer of it reached ``exports``.
        exports={symbols[pointer]: kind for pointer, kind in exports.items()},
        # **Reading 6's inner WORD beside the kind**, symbol -> the name the domain surface
        # publishes that symbol under (:data:`THE_INNER_EXPORT`).  Only the ``inner`` kind
        # is here: for the other three the surface's word IS the symbol, and an entry
        # restating that would be a second place for the two to disagree.
        published={symbols[pointer]: word for pointer, word in published.items()},
        # §1's BINDINGS, every one this module writes and not only the exported ones --
        # which is what makes the gate on the export set non-vacuous once the repair has
        # landed: the record still names what a binding is, so a name that returns to the
        # surface is caught rather than counted.
        binds={
            symbols[pointer]: symbols.get(named, named)
            for pointer, named in binds.items()
            if pointer in symbols
        },
        # Upstream's spellings beside them, as the run's own record of the one kind of
        # binding no POSITION of the document is behind (:attr:`codegen.ir.Module.recased`).
        recased=recased,
    )
