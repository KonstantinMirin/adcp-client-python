"""A POSITION IS NOT A NAME: no ordinal is DECLARED, anywhere in the emitted tree.

``<Base>Branch<i>`` and ``<Sibling><n>`` say where a thing sat in a list and nothing about
what it is, so a caller writing ``isinstance(req, AssetRequirementsBranch7)`` has to count
a document's branches to learn that the branch means JavaScript.  The rule is stated in
``docs/plan/rebuild-plan.md`` section 4's branch candidate list, in
``docs/plan/architecture.md`` section 5, and in ``docs/plan/final-state.md`` readings 4
and 6, and all three say the same three things:

* **The prohibition is on the SYMBOL, never on its final segment.**
  ``PostalAreaBranch9System`` carries an ancestor's index and demands the same count, and
  ``BuyProductsRequestBranch1AccountAccountId`` demands it three segments early.
* **It holds for a PRIVATE spelling as much as a public one.**  A module's reader and a
  validation error both quote the declared name, so withholding an ordinal from
  ``__all__`` does not stop it being the name of the thing.
* **Where every naming candidate answers nothing the compiler REFUSES the document.**  A
  branch stating no ``title``, no pin, no ``required``, no ``$ref`` target, no
  ``description`` and no ``properties`` says nothing about itself; refusing is countable
  in ``./check``'s figure, and minting an index is not.

**THE ONE ORDINAL THAT IS ADMISSIBLE IS UPSTREAM'S OWN PUBLISHED WORD, and it is admitted
as a RECORD and not as an exception.**  Upstream's generator numbers its anonymous variant
classes -- ``BuildCreativeResponse1``, ``Assets162``, ``Type11`` -- and an application has
already written ``from adcp.types import BuildCreativeResponse1`` against that wheel.  A
module-scope ``X = <symbol>`` statement RECORDS that commitment; it does not mint one.  So
the admissible set is :meth:`codegen.emit.Emitted.upstream_words` -- the run's own record
of the three joins ``lower/names.assign`` runs against upstream's published surface -- and
not a list in this file.  An ordinal the compiler binds that is NOT in that record is a
name this compiler invented, which is the defect, and no edit to this file can admit one.

**EVERY TEST HERE READS THE EMITTED SOURCE TEXT AND NOT THE IMPORTED NAMESPACE.**  The
subject is which names the compiler WRITES, so a facade, an alias layer or a lazy
``__getattr__`` must not be able to change the answer; ``ast`` over the module bodies is
the one reading that cannot be.  And the predicate is DERIVED rather than spelled: a
trailing digit run is an ordinal when the name without it is bound by the same module, so
``Html5``, ``Base64`` and ``V2`` are not swept up by a pattern and are not excused by a
word list either -- ``Html`` is not a sibling of ``Html5``, and that is the whole test.

**BOTH SPELLINGS ARE READ, which is the half its predecessor missed.**  A positionally
named branch is a ``class`` statement and an ordinal alias is an ``X = <symbol>``
assignment.  The earlier gate read the compiler's record of positional CLASS names only,
and asked of them one question -- are they public -- so 395 ordinal aliases and three
public ``Branch1``-bearing classes were emitted under a green suite.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import fresh
import pytest
from compiled import compiled
from nodeset import claimed

from codegen import emit

#: One spelling of the bundle, re-exported from ``tests_emit/fresh.py`` for
#: ``test_the_domain_surface.py``'s reason: a file that spells its own path can come to
#: range over a different bundle from the compile it reads.
BUNDLE = fresh.BUNDLE

#: **EVERY TREE THE COMPILER WRITES, and not only the private one.**  The committed text and
#: not only a fresh emit, because the subject is the SOURCE TEXT a consumer installs;
#: :func:`test_the_fresh_emit_states_no_index_either` grades the run, and the two must agree.
#:
#: ``_surface/`` is here because it is the half that PUBLISHES a name: it re-exports each
#: private symbol under the word the domain gives it and lists that word in ``__all__``.  A
#: gate reading ``_schemas/`` alone passed while ``_surface/core.py`` published
#: ``PostalAreaBranch9System`` and ``_surface/media_buy.py`` published three
#: ``BuyProductsRequestBranch1...`` names, because the re-export spells the name again at a
#: file the gate never opened.  Both trees, one rule.
TREES = (Path("src/adcp/types/_schemas"), Path("src/adcp/types/_surface"))

#: **An index ANYWHERE in the symbol**, which is the first of the rule's three clauses.
#: Searched and not anchored, so an ancestor's index is the same finding as a leaf's.
POSITIONAL = re.compile(r"Branch\d+")

#: A trailing run of digits, with the name it would be without them.  Whether that stem is
#: BOUND by the same module is what makes the name an ordinal, so this pattern alone
#: decides nothing -- see :func:`_ordinals`.
TRAILING = re.compile(r"^(?P<stem>.*[A-Za-z])(?P<index>\d+)$")


def _bound(tree: ast.Module) -> set[str]:
    """Every name the module binds at MODULE SCOPE: a class statement or an assignment."""
    out: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out.add(node.name)
        elif isinstance(node, ast.Assign):
            out |= {t.id for t in node.targets if isinstance(t, ast.Name)}
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out.add(node.target.id)
    return out


def _ordinals(bound: set[str]) -> dict[str, str]:
    """The ordinal names of one module -> the sibling stem that makes each one ordinal.

    A name is an ordinal when stripping its trailing digits leaves a name THIS MODULE also
    binds: ``AcceptancePolicyRequirement1`` beside ``AcceptancePolicyRequirement`` is the
    index of a sibling, while ``Html5`` has no ``Html`` beside it and is a word the schema
    spells.  Derived from the module's own bindings, so no name needs excusing and none
    can be excused by editing a set here.
    """
    found = {}
    for name in bound:
        match = TRAILING.match(name)
        if match and match.group("stem") in bound:
            found[name] = match.group("stem")
    return found


@pytest.fixture(scope="module")
def modules() -> dict[str, set[str]]:
    """Module path -> the names it binds, over the whole emitted tree."""
    return {
        f"{tree.name}/{path.relative_to(tree).as_posix()}": _bound(
            ast.parse(path.read_text())
        )
        for tree in TREES
        for path in sorted(tree.rglob("*.py"))
        if path.name != "__init__.py"
    }


@pytest.fixture(scope="module")
def run() -> emit.Emitted:
    """One compile, shared: ``tests_emit/compiled.py`` holds it per document set."""
    return compiled(BUNDLE, fresh.population())


@pytest.fixture(scope="module")
def upstream(run: emit.Emitted) -> set[str]:
    """Every word upstream's wheel published that the run RECORDS a statement for.

    :meth:`emit.Emitted.upstream_words` is module -> word -> symbol; the admissible set is
    the words, because the question an ordinal raises is whether the SPELLING is upstream's
    commitment, and upstream binds its own numbered classes in their own modules.
    """
    return {word for words in run.upstream_words().values() for word in words}


def test_the_tree_binds_names_at_all(modules: dict[str, set[str]]) -> None:
    """The gate's own non-vacuity, asserted before any claim about the names.

    Every assertion below is a statement about a set derived from these bindings, so a
    reading that found no modules, or modules binding nothing, would pass all of them while
    grading nothing.  ``ast`` over a tree whose path moved is exactly how that happens.
    """
    claimed(
        "the emitted tree this gate reads",
        {"modules": len(modules), "names": sum(len(b) for b in modules.values())},
    )
    assert len(modules) > 500, f"only {len(modules)} modules under {TREES}"
    assert sum(len(b) for b in modules.values()) > 5_000


def test_no_declared_name_carries_an_index(modules: dict[str, set[str]]) -> None:
    """Clause one: ``Branch<i>`` appears in no name the tree binds, at any segment.

    No exception and no carve-out, because this spelling is never upstream's word: it is
    the one the candidate list used to fall to when every candidate about the branch
    answered nothing, and the rule is that the compiler refuses the document instead.
    """
    offending = sorted(
        f"{module}::{name}"
        for module, bound in modules.items()
        for name in bound
        if POSITIONAL.search(name)
    )
    claimed(
        "names the emitted tree declares",
        {f"{module}::{name}" for module, bound in modules.items() for name in bound},
    )
    assert not offending, {
        "a position is not a name": offending,
        "the rule": (
            "rebuild-plan section 4: no candidate is a position, and where the candidates "
            "are exhausted the compiler refuses the document"
        ),
    }


def test_every_ordinal_alias_is_upstream_s_own_word(
    modules: dict[str, set[str]], upstream: set[str]
) -> None:
    """Clause two: an ``<Sibling><n>`` binding exists only where upstream published it.

    Such a binding RECORDS a commitment upstream's wheel already made, so the word has to
    be in the run's own record of their surface.  One this compiler invented answers no
    caller that exists and gives a reader an index where a subject belongs -- and because
    the admissible set is the record, admitting one means teaching the compiler that
    upstream published it, which it cannot do by itself.
    """
    invented = sorted(
        f"{module}::{name} (sibling of {stem})"
        for module, bound in modules.items()
        for name, stem in _ordinals(bound).items()
        if name not in upstream
    )
    claimed(
        "ordinal aliases the tree binds",
        {
            f"{module}::{name}"
            for module, bound in modules.items()
            for name in _ordinals(bound)
        },
    )
    assert not invented, {
        "these ordinals are this compiler's own invention": invented[:40],
        "count": len(invented),
        "the rule": (
            "final-state reading 4: an alias is admissible only where upstream's wheel "
            "already ships the spelling -- the commitment is theirs and the statement "
            "records it; a re-minted spelling answers no caller"
        ),
    }


def test_the_fresh_emit_states_no_index_either(run: emit.Emitted) -> None:
    """And the FRESH emit agrees with the committed tree, which is what makes it a gate.

    ``architecture.md`` section 2: "the subject of grading is a FRESH EMIT, never the
    committed tree".  The tests above read the committed text because that is what a
    consumer installs; this one reads the run, so a tree that happens to be clean while the
    compiler still mints an index cannot hide behind it.
    """
    offending = sorted(
        f"{module}::{name}"
        for module, text in run.files.items()
        for name in _bound(ast.parse(text))
        if POSITIONAL.search(name)
    )
    claimed(
        "names the fresh emit declares",
        {
            f"{module}::{name}"
            for module, text in run.files.items()
            for name in _bound(ast.parse(text))
        },
    )
    assert not offending, offending
