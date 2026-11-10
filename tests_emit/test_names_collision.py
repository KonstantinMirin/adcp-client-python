"""§4's name rules read as a POSITION and §4's collision rule that pays for it.

``adcp-client-python-10l.50``.  The section says "``<Property>`` for a property,
``<Property>Item`` for an array element, ``<Property>Value`` for a mapping value,
``<Root><Key>`` for a ``definitions`` entry -- the module path already carries the
document, so a nested name does not repeat it", and the emitter folded every hop to the
root and concatenated instead.  Measured on the committed tree: 778 of its 2,066 classes
longer than 30 characters, 135 longer than 50, and one
``GetMediaBuyArtifactsResponseArtifactsMediaBuyIdArtifactsItemBrandContext``.

**A separate module from ``tests/test_emit.py`` because the subject is one function of
one input.**  ``names.segments`` is a function of the node's PATH and
``names.spell`` of the SET of paths one module holds -- not of the content, not of the
walk order, not of which other documents the run includes -- so the rule is graded on
hop tables written here, and the two properties that are about the whole tree (no module
declares one name twice, and no module declares a name it imports) are read off the
COMMITTED tree's text.  Neither half needs the walk.
"""

from __future__ import annotations

import ast
import collections
from pathlib import Path

import fresh

from codegen.lower import names, union
from codegen.refusal import Refusal
from nodeset import claimed, ratchet

REPO = Path(__file__).resolve().parents[1]

#: The tree a FRESH run emits (``docs/plan/architecture.md``, 2026-10-29).  A collision
#: is a property of the compiler, so the text read here is the text this compiler wrote:
#: three of the four import-path collisions on the board when that was decided were
#: invisible in ``src/`` and visible in a fresh run.  ``tests/fresh.py`` owns the tree and
#: ``tests/test_emit.py``'s byte-compare is what keeps the committed one equal to it.
TREE = fresh.TREE


def _chains(hops: dict[str, names.Hop]) -> dict[str, tuple[str, ...]]:
    """Every pointer of a hop table with the segments §4 derives for it, which is the
    input ``names.spell`` takes -- in the hop table's own order, so a test can hand the
    same set in two orders and compare."""
    chains = {}
    for pointer in hops:
        chain = names.segments(pointer, hops)
        assert not isinstance(chain, Refusal), chain
        chains[pointer] = chain
    return chains


#: One document's hops as the walk records them: an ``artifacts`` array whose element
#: holds a ``brand`` object with a ``context``, and a second ``brand`` with a
#: ``context`` at the root.  The bead's own case, and §4's: both derive ``Context``.
_TWO_CONTEXTS: dict[str, names.Hop] = {
    "": names.Root("Get Media Buy Artifacts Response"),
    "/properties/artifacts": names.Property("", "artifacts"),
    "/properties/artifacts/items": names.Item("/properties/artifacts"),
    "/properties/artifacts/items/properties/brand": names.Property(
        "/properties/artifacts/items", "brand"
    ),
    "/properties/artifacts/items/properties/brand/properties/context": names.Property(
        "/properties/artifacts/items/properties/brand", "context"
    ),
    "/properties/brand": names.Property("", "brand"),
    "/properties/brand/properties/context": names.Property("/properties/brand", "context"),
}


def test_a_nested_name_is_the_position_and_not_the_path_to_it() -> None:
    """§4's four nested spellings, each read off the position's OWN hop.

    The root is ``pascal_case(title)``; a property is ``<Property>``; an element is
    ``<Property>Item`` and a mapping value ``<Property>Value``, which are ONE segment
    each because ``Item`` and ``Value`` name no position on their own; a ``definitions``
    entry is ``<Key>`` and NOT ``<Root><Key>`` (§4, 2026-10-28) -- the module path already
    carries the document, so the entry does not repeat it.

    **The root is still a SEGMENT of the entry's chain, and that is where the prefix
    went**: §4 makes the prefix "what the collision rule spends when two entries of one
    module need it, not what every entry pays up front", so the chain is two deep and
    ``spelling`` at depth 2 is the name the old rule gave.  Asserted here beside the
    short name, because a one-segment entry would spell the same at depth 1 and the two
    readings are only told apart by what a collision can reach.
    """
    hops: dict[str, names.Hop] = {
        "": names.Root("Media Buy"),
        "/properties/packages": names.Property("", "packages"),
        "/properties/packages/items": names.Item("/properties/packages"),
        "/properties/targets": names.Property("", "targets"),
        "/properties/targets/additionalProperties": names.Value("/properties/targets"),
        "/definitions/budget": names.Entry("budget"),
        "/properties/key/propertyNames": names.Unnamed(),
    }
    spelled = names.spell(_chains(hops))
    assert spelled == {
        "": "MediaBuy",
        "/properties/packages": "Packages",
        "/properties/packages/items": "PackagesItem",
        "/properties/targets": "Targets",
        "/properties/targets/additionalProperties": "TargetsValue",
        "/definitions/budget": "Budget",
        "/properties/key/propertyNames": "",
    }, spelled
    # And the whole chain is the name the fold gave before the rule was written, which
    # is what makes the refusal below the same refusal over the same documents.
    assert names.spelling(names.segments("/properties/packages/items", hops), 2) == (
        "MediaBuyPackagesItem"
    )
    # The dropped ``<Root>`` prefix is the entry's ANCESTOR segment and the collision rule
    # can still spend it, which is the half the short name above cannot show.
    assert names.segments("/definitions/budget", hops) == ("MediaBuy", "Budget")
    assert names.spelling(names.segments("/definitions/budget", hops), 2) == "MediaBuyBudget"


def test_all_n_colliders_lengthen_and_a_name_is_not_a_function_of_the_order() -> None:
    """§4: "where N positions of one module derive the same name, ALL N lengthen".

    Lengthening only the later collider would make the public symbol a function of which
    position the walk reached first, which §9 forbids.  So the same set of positions is
    handed in in two orders and the names are compared -- and both members of each
    colliding pair are checked to have moved, because lengthening one of the two is the
    arrangement that passes an order-independence check while still being first-come.
    """
    forward = _chains(_TWO_CONTEXTS)
    backward = {p: forward[p] for p in reversed(list(forward))}
    spelled, reversed_spelled = names.spell(forward), names.spell(backward)
    assert not isinstance(spelled, Refusal), spelled
    assert spelled == reversed_spelled, (names.COLLISION, spelled, reversed_spelled)

    collided = claimed(
        "the positions of this module that derive one name",
        [p for p, chain in forward.items() if chain[-1] in ("Brand", "Context")],
    )
    assert {p: spelled[p] for p in sorted(collided)} == {
        "/properties/artifacts/items/properties/brand": "ArtifactsItemBrand",
        "/properties/artifacts/items/properties/brand/properties/context": (
            "ArtifactsItemBrandContext"
        ),
        "/properties/brand": "GetMediaBuyArtifactsResponseBrand",
        "/properties/brand/properties/context": "GetMediaBuyArtifactsResponseBrandContext",
    }, {p: spelled[p] for p in sorted(collided)}
    # Neither collider kept the short name, and the pair that still collided after one
    # step took a second -- the rule repeats until the module's names are unique.
    assert all(spelled[p] != forward[p][-1] for p in collided), spelled


def test_a_position_colliding_with_nothing_keeps_the_name_section_4_derives() -> None:
    """§4's third sentence, which is the whole point of the row: the long name is the
    exception a collision buys and not the rule."""
    spelled = names.spell(_chains(_TWO_CONTEXTS))
    assert not isinstance(spelled, Refusal), spelled
    kept = claimed(
        "the positions this module spells with one segment",
        [p for p, name in spelled.items() if name in ("Artifacts", "ArtifactsItem")],
    )
    assert sorted(kept) == ["/properties/artifacts", "/properties/artifacts/items"], (
        names.COLLISION,
        sorted(kept),
    )


def test_two_positions_whose_whole_paths_spell_alike_refuse_rather_than_being_ordered() -> None:
    """The refusal this pass always had, and the rule does not move it: a position
    spelled with its whole path has no ancestor left to prepend, so two positions whose
    paths spell alike are a document this emitter cannot name.

    Which of the two a referrer would import would otherwise be decided by the order the
    walk reached them in, which is what §1's one-import-path rule forbids.
    """
    hops: dict[str, names.Hop] = {
        "": names.Root("X"),
        "/properties/a": names.Property("", "same"),
        "/properties/b": names.Property("", "same"),
    }
    refusal = names.spell(_chains(hops))
    assert isinstance(refusal, Refusal), refusal
    assert refusal.keyword == "title"
    # The pointer named is the one that COLLIDED, which is the later of the two in
    # declaration order, and the name is the whole-path spelling both reached.
    assert refusal.pointer == "/properties/b", refusal
    assert "derive the class name 'XSame'" in refusal.detail, refusal.detail


def test_a_class_does_not_take_a_name_the_module_imports() -> None:
    """A module's namespace is its declarations AND its imports.

    ``class Field(StrEnum)`` beside ``from pydantic import Field`` makes every
    ``Annotated[X, Field(description=…)]`` in that module call the CLASS, and the module
    then fails to import at all.  So a name an import holds is a name taken and the
    position lengthens -- and where it cannot (a ROOT and a titled branch are chains of
    one), it keeps the name this emitter has always given it rather than refusing a
    document over a name no document states anything about.
    """
    hops: dict[str, names.Hop] = {
        "": names.Root("Macro Declaration"),
        "/properties/location": names.Property("", "location"),
        "/properties/location/properties/field": names.Property(
            "/properties/location", "field"
        ),
    }
    chains = _chains(hops)
    # §4 alone spells the property ``Field``, which is the measured case:
    # ``core/macro-declaration.json`` and three documents like it.
    assert names.spell(chains)["/properties/location/properties/field"] == "Field"
    spelled = names.spell(chains, frozenset({"Field"}))
    assert spelled == {
        "": "MacroDeclaration",
        "/properties/location": "Location",
        "/properties/location/properties/field": "LocationField",
    }, spelled
    # A chain of ONE cannot lengthen, and the name stands rather than refusing: a
    # document titled ``Error`` beside the runtime's own ``Error`` is 3 of this bundle.
    root_only = _chains({"": names.Root("Error")})
    assert names.spell(root_only, frozenset({"Error"})) == {"": "Error"}


def test_section_4s_branch_rules_name_the_branch_and_not_the_path_to_it() -> None:
    """§4's four branch rules, as the segments each one places.

    A title names ITSELF, so it starts a chain and the branch's ancestors are no part of
    it; a ``const`` pin, a required set and an index are spelled ON the parent's own
    segment, so a branch named by any of them shares its base's spelling.  Which fact
    wins decides the spelling and the placement together, which is why
    ``branch_identity`` returns both.
    """
    parent = ("MediaBuy", "TransitionsItem")
    assert names.branch_identity(names.Branch(parent="/x", title="Timer Transition"), parent) == (
        ("TimerTransition",)
    )
    assert names.branch_identity(names.Branch(parent="/x", pins=("media_event",)), parent) == (
        "MediaBuy",
        "TransitionsItemMediaEvent",
    )
    assert names.branch_identity(
        names.Branch(parent="/x", required=("trigger", "input")), parent
    ) == ("MediaBuy", "TransitionsItemInputTrigger")
    # §4's LAST resort, ``<Base>Branch<i>`` (``adcp-client-python-10l.41``), which is a
    # PRIVATE declaration name and never a name an application may import (the owner's
    # ruling of 2026-11-10, :data:`names.A_POSITIONAL_NAME_IS_PRIVATE`).  It is reached
    # only here: the rules above each answered nothing, and a document that gives a branch
    # no identity at all leaves nothing else to read -- so the class still has to be
    # DECLARED under some name, or the union loses a branch and the model refuses a payload
    # the document admits.  What the ruling removes is the publication, not the name.
    placeholder = names.Branch(parent="/x", index=3)
    assert names.branch_identity(placeholder, parent) == (
        "MediaBuy",
        "TransitionsItemBranch3",
    )
    # And the name this rule derives is recognised as positional, which is the whole of
    # how it comes to be withheld: ``the_positional_names`` asks whether a settled name is
    # a spelling of this position's own positional chain, and
    # ``tests_emit/test_no_positional_name_is_public.py`` is what grades the surface.
    assert names.positional_chain(placeholder, parent) == ("MediaBuy", "TransitionsItemBranch3")
    assert names.spelled_from(
        names.positional_chain(placeholder, parent), "TransitionsItemBranch3"
    )
    assert names.spelled_from(
        names.positional_chain(placeholder, parent), "MediaBuyTransitionsItemBranch3"
    )
    # And the index never OUTRANKS an identity, which is the whole of why it is kept at
    # all: the same hop carrying a title takes the title, and carrying a pin takes the pin,
    # and such a name is PUBLIC -- it says what it names, so the ruling has nothing to
    # withhold.
    assert names.branch_identity(
        names.Branch(parent="/x", title="Timer Transition", index=3), parent
    ) == ("TimerTransition",)
    assert names.branch_identity(names.Branch(parent="/x", pins=("media_event",), index=3), parent) == (
        "MediaBuy",
        "TransitionsItemMediaEvent",
    )
    assert names.branch_identity(
        names.Branch(parent="/x", required=("trigger",), index=3), parent
    ) == ("MediaBuy", "TransitionsItemTrigger")
    # ... and the ban reaches none of those three, which is the other direction of the
    # ruling and the half that keeps it from being a ban on the WORD: the positional chain
    # exists for each of them -- every one of these hops carries an index -- and the name
    # each one SETTLED on is not a spelling of it, so nothing is withheld.
    for identified in (
        names.Branch(parent="/x", title="Timer Transition", index=3),
        names.Branch(parent="/x", pins=("media_event",), index=3),
        names.Branch(parent="/x", required=("trigger",), index=3),
    ):
        chain = names.positional_chain(identified, parent)
        assert chain is not None
        derived = names.branch_identity(identified, parent)
        assert derived is not None
        assert not names.spelled_from(chain, names.spelling(derived, len(derived)))
    # The ONE hop left with no name at all is a NESTED union's branch, whose index the
    # walk does not record because a member type needs no name of its own; ``segments``
    # gives it the union's own derived name and nothing refuses.
    assert names.branch_identity(names.Branch(parent="/x"), parent) is None


def test_inserting_a_branch_after_an_indexed_one_moves_no_existing_name() -> None:
    """The row's own acceptance criterion: every branch class name is a function of the
    branch node ALONE, so adding a sibling branch renames nothing already emitted.

    :data:`names.INDEX_IS_THE_LAST_CANDIDATE` is the sentence.  A positional name is the
    defect -- the upstream v9 SDK numbers 1,092 of its 4,360 classes and renames a
    sibling when a branch is inserted ahead of it -- and §4 reaches for it only as the
    last resort, where there is nothing else to read.  **AND THE NAME IT MINTS THERE IS
    PRIVATE AND NEVER PUBLIC** (the owner's ruling of 2026-11-10,
    :data:`names.A_POSITIONAL_NAME_IS_PRIVATE`): the class is declared, because deleting
    it would drop a branch from the union and refuse payloads the document admits, and the name is
    withheld from §1's export set, because a name minted for want of a subject must not
    become a name an application depends on.

    **SO WHAT THIS TEST CLAIMS IS NOT THAT THE NAME IS RIGHT, ONLY THAT IT IS STABLE.**
    It used to assert ``AssetRequirementsBranch0`` as the expected OUTPUT of the name
    rule, which is the claim the ruling denies; the derivation is still graded here
    because the compiler still has to declare the class under a stable symbol, and the
    second half -- that no such symbol may be published -- is asserted where the surface
    is, in ``tests_emit/test_no_positional_name_is_public.py``.

    What makes the symbol safe at all is that an index is a fact of the branch's OWN
    position: it is never derived from what the siblings state, so a branch APPENDED to
    the combinator adds a declaration and moves none.  Insertion in the MIDDLE does move
    the names after it, and that is the honest limit -- §4 says "stable under insertion
    only at the end" -- so this grades the property the section claims and not a stronger
    one.  A document that wants a stable name under reordering states a ``title``, which
    is the first rule and is what the upstream candidate asks for.
    """
    def hops(count: int) -> dict[str, names.Hop]:
        """A root union of ``count`` identity-less branches, as the walk records them."""
        table: dict[str, names.Hop] = {"": names.Root("Asset Requirements")}
        for i in range(count):
            table[f"/anyOf/{i}"] = names.Branch(parent="", index=i)
        return table

    three = names.spell(_chains(hops(3)))
    four = names.spell(_chains(hops(4)))
    assert not isinstance(three, Refusal), three
    assert not isinstance(four, Refusal), four
    assert three == {
        "": "AssetRequirements",
        "/anyOf/0": "AssetRequirementsBranch0",
        "/anyOf/1": "AssetRequirementsBranch1",
        "/anyOf/2": "AssetRequirementsBranch2",
    }, three
    # The APPENDED branch adds a declaration and moves none: the row renames nothing.
    assert {p: n for p, n in four.items() if p in three} == three, four
    assert four["/anyOf/3"] == "AssetRequirementsBranch3", four
    # **AND NONE OF THE FOUR IS A NAME THE SURFACE MAY CARRY**, which is the assertion
    # that replaces "this is the expected output": every one of them is recognised as
    # positional off the walk's own hop table, so §1's export set holds the ROOT and
    # nothing else of this document.
    assert names.the_positional_names(hops(4), four) == frozenset(
        {
            "AssetRequirementsBranch0",
            "AssetRequirementsBranch1",
            "AssetRequirementsBranch2",
            "AssetRequirementsBranch3",
        }
    )
    assert "AssetRequirements" not in names.the_positional_names(hops(4), four)


# --------------------------------------------------------------------------- #
# the two properties that are about the whole tree, read off its own text
# --------------------------------------------------------------------------- #
def _modules(root: Path = TREE) -> dict[str, ast.Module]:
    """Every module of the tree, parsed.  The TEXT and not the emitter, so what is graded
    is what a consumer imports.

    **A PACKAGE ROOT IS A DOCUMENT'S MODULE, so ``__init__.py`` is NOT a name to filter
    on** (``adcp-client-python-bxu``, the reading, and ``-5uz``, this site).
    ``emit.module_file``'s layout rule writes a document whose own path is also a
    DIRECTORY of the bundle to ``<path>/__init__.py``, so ``brand.json``'s module is
    ``brand/__init__.py``.  The by-name filter was written when every ``__init__.py`` of
    the tree was a 0-byte layout marker, and by bundle 3.2 it was the one filter that
    discarded the DENSEST MODULE IN THE TREE from §1's one-import-path reading: measured
    here, 1,057 modules and 2,992 class statements with it against 1,089 and 3,103
    without -- the 111 ``brand/__init__.py`` declares, 68 pydantic classes and 44 enums,
    read by no check below.

    No filter at all and not a narrower one: ``rglob`` sees every file, including the
    tree's own root -- ``_schemas/__init__.py``, the empty marker ``emit.write`` writes --
    which has nothing to collide and nothing to shadow and is a module of the tree like
    the other 30 markers.  (That is the one difference from the ``pkgutil`` walks of
    ``tests/_imports_a_tree.py`` and ``tests/test_union_dispatch.py``, which cannot yield
    the root because they enumerate a package's CHILDREN.)

    **The root is a PARAMETER** so that the readings below can be run over a tree built to
    carry a known defect, which is the only thing that says they reach one:
    :func:`test_the_tree_readings_reach_a_module_that_is_a_package_root` is that A/B, and
    the real tree is green either way.
    """
    return {
        path.relative_to(root).as_posix(): ast.parse(path.read_text())
        for path in sorted(root.rglob("*.py"))
    }


def _declared_more_than_once(modules: dict[str, ast.Module]) -> dict[str, list[str]]:
    """Every module with a name it declares twice, and the names.  §1's reading."""
    twice = {}
    for module, tree in modules.items():
        counted = collections.Counter(
            node.name if isinstance(node, ast.ClassDef) else node.targets[0].id
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            or (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id[:1].isupper()
            )
        )
        repeated = [name for name, n in counted.items() if n > 1]
        if repeated:
            twice[module] = sorted(repeated)
    return twice


def _declarations_shadowing_an_import(modules: dict[str, ast.Module]) -> dict[str, list[str]]:
    """Every module declaring a name it also imports, and the names."""
    shadowed = {}
    for module, tree in modules.items():
        imported = {
            alias.asname or alias.name
            for node in tree.body
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        declared = {node.name for node in tree.body if isinstance(node, ast.ClassDef)} | {
            node.targets[0].id
            for node in tree.body
            if isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
        }
        if imported & declared:
            shadowed[module] = sorted(imported & declared)
    return shadowed


def test_no_module_of_the_tree_declares_two_symbols_under_one_name() -> None:
    """The acceptance criterion of the row, over the tree rather than over a hop table:
    §1 gives a class ONE import path, so one name in one module names one thing.

    **THIS GATE HAS NO SECOND DERIVATION**, which is why the A/B below exists.  It is an
    absence over one enumeration of the tree's text, so a walk that cannot see part of the
    tree reports green for free on that part and no equality disagrees.  ``claimed``
    refuses only an EMPTY population.
    """
    modules = _modules()
    claimed("every module of the tree a fresh run emits", modules)
    twice = _declared_more_than_once(modules)
    assert twice == {}, twice


def test_no_module_of_the_tree_declares_a_name_it_imports() -> None:
    """A declaration that shadows an import retypes every field annotated with it.

    The failure is silent in the type checker and loud at import -- a ``StrEnum`` named
    ``Field`` is called as ``Field(description=…)`` -- and §4's short nested rule is what
    makes it reachable: ``names.spell``'s ``occupied`` is the guard and this is the
    measurement over the output.
    """
    modules = _modules()
    claimed("every module of the tree a fresh run emits", modules)
    shadowed = _declarations_shadowing_an_import(modules)
    assert shadowed == {}, shadowed


def test_the_tree_readings_reach_a_module_that_is_a_package_root(tmp_path: Path) -> None:
    """``adcp-client-python-5uz``: the two readings above over a tree whose PACKAGE ROOT
    is where the defects are.

    §9: a rule nothing can break is a finding about the rule.  Both gates are green with
    the ``!= "__init__.py"`` filter and green without it -- the previous lane A/B'd them
    and the tree is clean behind the filter -- so **their own green says nothing about
    which modules they read**, and a later edit could restore the filter without reddening
    anything.  Here the package root carries a defect of each shape, so the readings
    either name it or do not.

    The population is a hand-built tree and not the bundle's, for
    ``tests/test_the_tree_imports.py``'s reason: what is graded is the READING and not the
    compiler, and four files answer the question instantly where the real tree is 1,089.
    Its shape is ``brand/``'s -- a document's module written to the package's own
    ``__init__.py``, with the directory's documents as its submodules -- which is
    ``adcp-client-python-bxu``'s fixture adapted to the defects THESE gates report: a name
    declared twice (§1's one import path) and a declaration shadowing an import.

    ``rooted/under.py`` beside it is the near miss that makes "not reported" informative:
    it declares ``Spin`` ONCE and imports ``Field`` WITHOUT declaring it, so a reading
    that reached it and miscounted would be red here.  ``plain.py`` is the same control
    for a module that is not under a package at all, and the tree's own root is the empty
    marker.

    **By behaviour and never by inspection**: nothing here reads :func:`_modules`' source
    or asks how it walks.  The claim is that a known package module's declarations are
    READ, and what says so is a collision reported from inside one.
    """
    tree = tmp_path / "a_tree_with_a_package_root"
    (tree / "rooted").mkdir(parents=True)
    (tree / "__init__.py").write_text("")  # the tree's own root, as ``emit.write`` writes it
    clean = (
        "from __future__ import annotations\n"
        "from pydantic import Field\n"
        "from adcp.types._base import AdCPBaseModel\n"
        "class Spin(AdCPBaseModel):\n    a: str = Field(description='x')\n"
    )
    # ``brand/__init__.py``'s position, carrying one defect of each shape: ``Spin``
    # declared twice, and ``Field`` declared over the name it imports.
    (tree / "rooted" / "__init__.py").write_text(
        clean + "class Spin(AdCPBaseModel):\n    b: str\n" + "class Field(AdCPBaseModel):\n    c: str\n"
    )
    (tree / "rooted" / "under.py").write_text(clean)
    (tree / "plain.py").write_text(clean)

    modules = _modules(tree)
    # **BOTH DEFECTS IN THE PACKAGE ROOT ARE REPORTED**, by name and from that module
    # alone: the two clean modules are reached and report nothing, which is what says the
    # filter never cost recursion -- ``rooted/under.py`` is BELOW the package root and was
    # always visible, so a reading short only of the root's own body is exactly the loss.
    # With the by-name filter restored both of these are ``{}``.
    assert _declared_more_than_once(modules) == {"rooted/__init__.py": ["Spin"]}
    assert _declarations_shadowing_an_import(modules) == {"rooted/__init__.py": ["Field"]}

    # **AND THE WHOLE TREE WAS READ**, as an equality between two derivations and not a
    # count (``tests/test_every_check_names_its_set.py``'s first rule): the modules the
    # reading keyed, against the ``.py`` files on disk read off the directory as POSIX
    # paths so a package root is distinguishable from a plain module.  With the filter
    # restored this is short by the root and by ``rooted/__init__.py`` -- which is
    # ``brand/__init__.py``, in miniature.
    assert set(modules) == {p.relative_to(tree).as_posix() for p in tree.rglob("*.py")}, sorted(
        modules
    )


def test_the_long_name_is_the_exception_and_not_the_rule() -> None:
    """A RATCHET and not a pin, because §4's own acceptance criterion is a direction:
    "the median name length falls and the count over 40 chars falls sharply; both are
    reported as measurements, not pinned".

    Measured on the tree ``adcp-client-python-10l.50`` produced: 2,092 classes, median
    17, mean 18.29, max 76, and 221 / 64 / 13 / 7 longer than 30 / 40 / 50 / 60
    characters -- against 2,066 classes, median 26, mean 28.66 and 778 / 347 / 135 / 46
    before it.  A ceiling, so a row that emits more documents may raise the COUNT of long
    names and not the share: ``adcp-client-python-10l.41`` emitted 5 documents more and
    the tree is 2,165 classes, median 17, mean 18.39, max 76 and 223 / 64 / 13 / 7 -- the
    count over 30 moved by 2 and the share over 40 did not move at all.

    **THE RATCHET'S OWN BLINDNESS, and it is the shape ``adcp-client-python-bxu`` is
    really about.**  Numerator and denominator both come out of :func:`_modules`, so while
    that walk filtered ``__init__.py`` by name this was a SHARE over a tree it could not
    see all of: 132 of 2,992 names, reported as 4%, where the tree's own figure is 133 of
    3,103 -- also 4%.  Two blind halves agreeing is indistinguishable from two sighted
    halves agreeing, and that is precisely why the direction held through it.  The reading
    is now over every module (median 18, max 85, 133 over 40), and the ceiling is unmoved.
    """
    classes = claimed(
        "every class statement of the tree a fresh run emits",
        [
            (module, node.name)
            for module, tree in _modules().items()
            for node in tree.body
            if isinstance(node, ast.ClassDef)
        ],
    )
    ratchet(
        "the share of class names longer than 40 characters",
        round(100 * sum(1 for _, name in classes if len(name) > 40) / len(classes)),
        at_most=5,
        because=(
            "§4's nested rule names a position and not the path to it, so a name is "
            "long only where the module's own names collide or where a branch's "
            "required set is long; it was 17% of the tree's 2,066 names before the rule "
            "and is 3% of its 2,165 after.  A ceiling on the SHARE and not the count, "
            "because a row that emits more documents moves the count and not the rule"
        ),
    )


# --------------------------------------------------------------------------- #
# §4's CANDIDATE axis (``adcp-client-python-10l.78``)
# --------------------------------------------------------------------------- #
def _candidate_names(hops: dict[str, names.Hop]) -> dict[str, tuple[tuple[str, ...], ...]]:
    """Every pointer with §4's CANDIDATES for it, which is what ``spell_the_candidates`` takes."""
    out = {}
    for pointer in hops:
        candidates = names.candidate_names(pointer, hops)
        assert not isinstance(candidates, Refusal), candidates
        out[pointer] = candidates
    return out


def test_rung_two_reads_every_pin_the_branch_states_in_the_documents_key_order() -> None:
    """§4: "A branch pinning a ``const`` on several properties derives from all of them,
    in the order the document writes the keys."

    The one-pin reading declined to choose between two and fell through to the index,
    which named the most heavily identified branches of the bundle positionally.  Both
    halves are asserted: several pins concatenate, and ONE pin is still just that pin --
    "one pin in key order is that one pin" -- which is what keeps the four single-pin
    branches of ``core/postal-country-system.json`` spelling ``US``, ``GB``, ``CA``
    and ``Plz``.
    """
    parent = ("PostalCountrySystem",)
    assert names.branch_identity(
        names.Branch(parent="/x", pins=("FR", "code_postal")), parent
    ) == ("PostalCountrySystemFRCodePostal",)
    assert names.branch_identity(names.Branch(parent="/x", pins=("US",)), parent) == (
        ("PostalCountrySystemUS",)
    )
    # The ORDER is the document's and is never sorted.  Asserted on a pair whose two
    # orders SPELL DIFFERENTLY, so a sort snuck in later reddens here: sorted, these two
    # names would swap.
    assert names.branch_identity(
        names.Branch(parent="/x", pins=("ZA", "postal_code")), parent
    ) == ("PostalCountrySystemZAPostalCode",)
    assert names.branch_identity(
        names.Branch(parent="/x", pins=("postal_code", "ZA")), parent
    ) == ("PostalCountrySystemPostalCodeZA",)


def test_a_boolean_pin_contributes_no_segment_because_true_names_nothing() -> None:
    """§4, decided 2026-10-29: :data:`names.A_BOOLEAN_PIN_NAMES_NOTHING`.

    A pin identifies a branch by its VALUE, and a boolean's two values are the same two
    for every property in the bundle -- so this is not a carve-out from the key-order
    rule, it is the section's own sentence that ``true`` on both branches "names
    neither", applied per PIN instead of per branch.

    Both halves of the measured population are asserted, because the rule reaches two
    structures and a reading that dropped the whole candidate would pass only one:

    * a branch pinning something IDENTIFYING beside a ``true`` keeps the identifying pin
      and loses the boolean -- ``core/package-signal-targeting.json``'s
      ``PackageSignalTargetingBinaryTrue`` becomes ``PackageSignalTargetingBinary``;
    * a branch whose pins are ALL boolean answers nothing at candidate 2 and falls through --
      ``governance/sync-plans-request.json``'s ``BudgetTrue`` becomes
      ``BudgetReallocationUnlimited``, the property whose PRESENCE identifies it.

    The second half is also how the rule SUBSUMES the collision case rather than sitting
    beside it (§4): ``trusted-match/provider-registration.json``'s two branches pin
    ``context_match: true`` and ``identity_match: true``, which the collision clause
    reached by deriving one name for the pair and falling.  Candidate 2 now answers nothing
    for either, so ONE rule gets them there -- asserted below as the candidate answering
    ``None``, which is what tells the two routes apart.
    """
    base = ("PackageSignalTargeting",)
    # Identifying beside a boolean: the boolean goes, the identifying pin stays.
    assert names.branch_identity(
        names.Branch(parent="/x", pins=("binary", True), index=0), base
    ) == ("PackageSignalTargetingBinary",)
    # And the rule is on the VALUE, not on the position: a trailing identifying pin keeps
    # its place in the document's key order.
    assert names.branch_identity(
        names.Branch(parent="/x", pins=(True, "binary"), index=0), base
    ) == ("PackageSignalTargetingBinary",)
    assert names.identifying_pins((True, "binary", False)) == ("binary",)
    # ``0`` and ``1`` are not booleans, and ``isinstance(True, int)`` is why this is
    # asserted: a test on the wrong type would swallow a numeric pin.
    assert names.identifying_pins((0, 1)) == (0, 1)

    # All-boolean: candidate 2 answers NOTHING, so the branch falls -- one rule, not two.
    hops = {
        "": names.Root("TMP Provider Registration"),
        "/anyOf/0": names.Branch(
            parent="", pins=(True,), required=("context_match",), index=0
        ),
        "/anyOf/1": names.Branch(
            parent="", pins=(True,), required=("identity_match",), index=1
        ),
    }
    registration = ("TMPProviderRegistration",)
    assert (
        names.branch_candidates(hops["/anyOf/0"], registration)[0]
        == ("TMPProviderRegistrationContextMatch",)
    ), "candidate 2 must answer NOTHING, so the required set is the FIRST candidate and not a fall"
    spelled = names.spell_the_candidates(_candidate_names(hops))
    assert not isinstance(spelled, Refusal), spelled
    assert spelled == {
        "": "TMPProviderRegistration",
        "/anyOf/0": "TMPProviderRegistrationContextMatch",
        "/anyOf/1": "TMPProviderRegistrationIdentityMatch",
    }, spelled


def test_a_rung_that_collides_has_not_identified_the_branch_so_both_fall() -> None:
    """§4: "Where a candidate derives one name for two branches it has not identified either,
    so both fall to the next candidate."

    The clause STANDS after the boolean rule subsumed its measured population
    (``trusted-match/provider-registration.json``, now reached by candidate 2 answering
    nothing), so it is graded on two branches pinning the same IDENTIFYING value -- which
    is the general shape and the one the boolean rule does not reach.  Both halves are
    asserted, because the second means nothing without the first: that the candidate really
    does collide, and that the fall lands on the required set.
    """
    hops = {
        "": names.Root("Doc"),
        "/anyOf/0": names.Branch(
            parent="", pins=("shared",), required=("context_match",), index=0
        ),
        "/anyOf/1": names.Branch(
            parent="", pins=("shared",), required=("identity_match",), index=1
        ),
    }
    base = ("Doc",)
    assert names.branch_identity(hops["/anyOf/0"], base) == names.branch_identity(
        hops["/anyOf/1"], base
    ), "candidate 2 must collide for the fall to be what resolves this"
    spelled = names.spell_the_candidates(_candidate_names(hops))
    assert not isinstance(spelled, Refusal), spelled
    assert spelled == {
        "": "Doc",
        "/anyOf/0": "DocContextMatch",
        "/anyOf/1": "DocIdentityMatch",
    }, spelled


def test_two_positions_deriving_one_definitions_key_both_spend_the_root_prefix() -> None:
    """§4's dropped ``<Root>`` prefix is "what the collision rule spends when two entries
    of one module need it, not what every entry pays up front" (2026-10-28).

    ``brand.json``'s own measured shape: ``/definitions/contact`` and
    ``/definitions/brand/properties/contact`` both derive ``Contact``, so ALL N lengthen
    -- the entry spends its root segment and the property spends its own nearest ancestor.
    That is the collision rule unchanged; what the decision moved is that the entry pays
    it only HERE, and its 50 siblings in the same module do not.
    """
    hops: dict[str, names.Hop] = {
        "": names.Root("Brand Discovery"),
        "/definitions/contact": names.Entry("contact"),
        "/definitions/brand": names.Entry("brand"),
        "/definitions/brand/properties/contact": names.Property(
            "/definitions/brand", "contact"
        ),
        "/definitions/domain": names.Entry("domain"),
    }
    spelled = names.spell(_chains(hops))
    assert not isinstance(spelled, Refusal), spelled
    assert spelled == {
        "": "BrandDiscovery",
        "/definitions/contact": "BrandDiscoveryContact",
        "/definitions/brand": "Brand",
        "/definitions/brand/properties/contact": "BrandContact",
        "/definitions/domain": "Domain",
    }, spelled


def test_a_branch_colliding_with_its_own_root_loses_the_name_and_the_root_keeps_it() -> None:
    """§4: "the root keeps the name and the branch falls to the next candidate".

    ``core/postal-area.json``'s own shape: the root is titled "Postal Area" and its
    ``/anyOf/0`` is titled "PostalArea", so both derive ``PostalArea`` and neither has an
    ancestor segment to spend.  This refused as a hand-minted VERDICT, writing off the
    document and the 31 chained behind it for a naming choice this compiler makes.

    **The root is not special-cased and the assertion is written so that one would be
    visible.**  What makes the root keep the name is that its CANDIDATE LIST has one candidate, which
    is D5 fixing a document's exported symbol -- so the candidate list lengths are asserted beside
    the names.  A reading that tested the pointer ``""`` instead would pass the name
    assertions and state D5 a second time, and this is the assertion that tells them
    apart.
    """
    hops = {
        "": names.Root("Postal Area"),
        "/anyOf/0": names.Branch(
            parent="", title="PostalArea", required=("country", "system", "values"), index=0
        ),
        "/anyOf/1": names.Branch(parent="", title="PostalAreaWithFusedSystem", index=1),
    }
    candidate_lists = _candidate_names(hops)
    assert len(candidate_lists[""]) == 1, "a root has ONE candidate: D5 fixes the exported symbol"
    assert len(candidate_lists["/anyOf/0"]) > 1, "a titled branch has candidates to fall to"
    spelled = names.spell_the_candidates(candidate_lists)
    assert not isinstance(spelled, Refusal), spelled
    assert spelled[""] == "PostalArea", "the ROOT keeps it"
    assert spelled["/anyOf/0"] == "PostalAreaCountrySystemValues", "the BRANCH fell"
    # The sibling collided with nothing and keeps its own title, which is the other half
    # of §4's collision rule: a position whose short name collides with nothing keeps it.
    assert spelled["/anyOf/1"] == "PostalAreaWithFusedSystem"


def test_lengthening_is_tried_before_falling_so_an_identity_is_not_given_up_early() -> None:
    """§4's order: the collision rule LENGTHENS, and the fall is for the chains that have
    nothing to lengthen by.

    A pinned branch is spelled onto its parent's own segment, so it has the parent's
    ancestors to spend -- unlike a TITLED branch, which names itself and is a chain of
    one.  Here a pinned branch and an unrelated property both derive ``AX``; lengthening
    separates them, and the branch must come out still carrying the identity its PIN
    derived rather than having fallen to its required set or its index.
    """
    hops = {
        "": names.Root("Doc"),
        "/properties/a": names.Property(parent="", key="a"),
        "/properties/b": names.Property(parent="", key="b"),
        "/properties/a/anyOf/0": names.Branch(
            parent="/properties/a", pins=("x",), required=("q",), index=0
        ),
        "/properties/b/properties/aX": names.Property(parent="/properties/b", key="aX"),
    }
    candidate_lists = _candidate_names(hops)
    assert candidate_lists["/properties/a/anyOf/0"][0] == ("Doc", "AX"), candidate_lists
    spelled = names.spell_the_candidates(candidate_lists)
    assert not isinstance(spelled, Refusal), spelled
    assert spelled["/properties/a/anyOf/0"] == "DocAX", spelled
    assert spelled["/properties/b/properties/aX"] == "BAX", spelled
    # The identity is the PIN's and was not given up: the required set would have spelled
    # ``AQ`` and the index ``ABranch0``, and neither appears.  Asked of the RECORD rather
    # than of the string -- ``the_positional_names`` compares the settled name against this
    # position's own positional chain, so the claim is "this branch did not fall to its
    # index" and not "the characters B-r-a-n-c-h are absent".
    assert "Q" not in spelled["/properties/a/anyOf/0"]
    assert not names.the_positional_names(hops, spelled)


def test_a_bare_ref_branch_takes_its_targets_distinguishing_name_and_not_its_index() -> None:
    """§4's FOURTH candidate: "where the branch is a bare ``$ref``, the TARGET's own derived
    name"; and "where the root's name and the target's share a run, the branch takes the
    root's name plus the target's distinguishing remainder".

    ``core/requirements/asset-requirements.json``'s own structure, which is what the candidate is
    written for: twelve branches, every one of them a bare ``$ref`` with no ``title``, no
    ``const`` pin and no ``required`` set, so candidates 1 to 3 answer nothing and all twelve
    reached the index.  ``isinstance(req, AssetRequirementsBranch7)`` requires counting the
    document's branches to learn that it means JavaScript, which is the usability failure a
    positional name IS -- and the fact the candidate reads was sitting in the branch's second
    base the whole time.

    **The run is read at either END, because the bundle writes it both ways.**  The target
    carries it as a SUFFIX here (``ImageAssetRequirements`` beside ``AssetRequirements``)
    and as a PREFIX in ``creative/get-creative-features-response.json``
    (``GetCreativeFeaturesSuccess`` beside ``GetCreativeFeaturesResponse``), and one rule
    covers both: 12 of the bundle's 13 such branches share a suffix, 1 a prefix, 0 both.

    **Why the remainder and not the target's name spelled straight.**  The branch's second
    base IS the target, so the module imports that symbol, and :func:`names.spell`'s
    ``occupied`` says an imported name is a name taken.  A branch is a chain of ONE at this
    candidate and has no ancestor to lengthen by, so ``occupied`` would keep the shadowing name
    rather than refuse it -- which is a structure the bundle already has at candidate 1 and
    ``test_no_module_of_the_tree_declares_a_name_it_imports`` is red on
    (``core/vendor_pricing_option.py``, five branches titled exactly as their targets).
    """
    hops = {
        "": names.Root("Asset Requirements"),
        "/anyOf/0": names.Branch(parent="", target="ImageAssetRequirements", index=0),
        "/anyOf/1": names.Branch(parent="", target="JavaScriptAssetRequirements", index=1),
        "/anyOf/2": names.Branch(parent="", target="DAASTAssetRequirements", index=2),
    }
    spelled = names.spell_the_candidates(_candidate_names(hops))
    assert not isinstance(spelled, Refusal), spelled
    assert spelled == {
        "": "AssetRequirements",
        "/anyOf/0": "AssetRequirementsImage",
        "/anyOf/1": "AssetRequirementsJavaScript",
        # The acronym survives, because the word split is the inverse of ``class_name``'s
        # "only the first letter of a word is touched".
        "/anyOf/2": "AssetRequirementsDAAST",
    }, spelled
    # No branch is spelled as its own target, which is the shadowing the remainder avoids.
    assert not {spelled[p] for p in spelled} & {
        "ImageAssetRequirements", "JavaScriptAssetRequirements", "DAASTAssetRequirements"
    }, spelled

    # The run read at the other END: a shared PREFIX, and the remainder is the tail.
    prefixed = names.spell_the_candidates(
        _candidate_names(
            {
                "": names.Root("Get Creative Features Response"),
                "/oneOf/0": names.Branch(
                    parent="", target="GetCreativeFeaturesSuccess", index=0
                ),
            }
        )
    )
    assert not isinstance(prefixed, Refusal), prefixed
    assert prefixed["/oneOf/0"] == "GetCreativeFeaturesResponseSuccess", prefixed

    # A target sharing NO run with the root spells its whole name onto the base's segment,
    # rather than standing alone and shadowing the import.
    unrelated = names.spell_the_candidates(
        _candidate_names({"": names.Root("Doc"), "/oneOf/0": names.Branch(parent="", target="Other", index=0)})
    )
    assert not isinstance(unrelated, Refusal), unrelated
    assert unrelated["/oneOf/0"] == "DocOther", unrelated

    # A target whose name says NOTHING the root's does not leaves the rule answering
    # nothing, and the branch falls to its index -- the same structure §4's root-collision
    # clause has: a rule that identifies nothing is not one to fall to.  **That is a
    # PRIVATE declaration name and the one outcome of this candidate list a consumer never sees**
    # (the owner's ruling of 2026-11-10, :data:`names.A_POSITIONAL_NAME_IS_PRIVATE`): the
    # class is still declared, and the name is withheld from §1's export set.
    silent_target = {
        "": names.Root("Doc"),
        "/oneOf/0": names.Branch(parent="", target="Doc", index=0),
    }
    same = names.spell_the_candidates(_candidate_names(silent_target))
    assert not isinstance(same, Refusal), same
    assert same["/oneOf/0"] == "DocBranch0", same
    assert names.the_positional_names(silent_target, same) == frozenset({"DocBranch0"})
    # ... and the branch above, which the rule DID name, is public: the ban is on the
    # name the last resort mints and not on every branch of a union.
    assert not names.the_positional_names(
        {"": names.Root("Doc"), "/oneOf/0": names.Branch(parent="", target="Other", index=0)},
        unrelated,
    )


def test_the_ref_target_rung_outranks_the_index_and_nothing_else() -> None:
    """The candidate's PLACE in the candidate list, which is what keeps the rename set bounded.

    It sits below the three declared-identity candidates and above the index, so the only
    branches it can move are the ones that were reaching the index -- which is why the
    measured rename census over bundle 3.2 is 13 classes in 2 documents and 3,449 classes
    before and after.  A sibling named by a ``title``, a pin or a required set does not
    move, which is what ``core/postal-country-system.json``'s four single-pin branches
    (``US``, ``GB``, ``CA``, ``Plz``) need.

    Insertion stability is unchanged and is the reason the candidate is admissible at all: both
    inputs -- the target's symbol and the root's own name -- are facts about the ONE
    branch, which is §4's own criterion and what the branch rule reverted at ``64d0f897``
    failed.
    """
    parent = ("AssetRequirements",)
    # Each declared identity still wins over the target.
    assert names.branch_identity(
        names.Branch(parent="", title="Image Asset", target="ImageAssetRequirements", index=0),
        parent,
    ) == ("ImageAsset",)
    assert names.branch_identity(
        names.Branch(parent="", pins=("image",), target="ImageAssetRequirements", index=0), parent
    ) == ("AssetRequirementsImage",)
    assert names.branch_identity(
        names.Branch(parent="", required=("width",), target="ImageAssetRequirements", index=0),
        parent,
    ) == ("AssetRequirementsWidth",)
    # With none of the three, the target wins over the index.
    assert names.branch_identity(
        names.Branch(parent="", target="ImageAssetRequirements", index=0), parent
    ) == ("AssetRequirementsImage",)
    # A NESTED union's branch records no index and a local ``$ref``'s target is a POINTER
    # and not a name, so neither reaches this candidate and both answer nothing.
    assert names.branch_identity(names.Branch(parent=""), parent) is None

    # Appending a branch moves no existing name, because no candidate reads a sibling.
    def hops(targets: tuple[str, ...]) -> dict[str, names.Hop]:
        table: dict[str, names.Hop] = {"": names.Root("Asset Requirements")}
        for i, target in enumerate(targets):
            table[f"/anyOf/{i}"] = names.Branch(parent="", target=target, index=i)
        return table

    two = names.spell_the_candidates(_candidate_names(hops(("ImageAssetRequirements", "VideoAssetRequirements"))))
    three = names.spell_the_candidates(
        _candidate_names(hops(("ImageAssetRequirements", "VideoAssetRequirements", "AudioAssetRequirements")))
    )
    assert not isinstance(two, Refusal) and not isinstance(three, Refusal)
    assert {p: n for p, n in three.items() if p in two} == two, three
    assert three["/anyOf/2"] == "AssetRequirementsAudio", three


def test_a_member_type_colliding_with_its_union_falls_to_what_it_requires_one_level_down() -> None:
    """§4's LAST branch candidate (:data:`codegen.lower.names.REQUIREMENT_IS_THE_FALL_OF_LAST_RESORT`).

    **Bundle 3.3's own shape, and its only hard verdict** (``adcp-client-python-82m.59``).
    ``core/targeting-overlay-requirements.json`` states
    ``/definitions/daypartRequirement`` as ``anyOf: [{$ref: #/definitions/required},
    {<object>}]`` and titles neither position, so the definitions ENTRY and the object
    BRANCH both derive ``TargetingOverlayRequirementsDaypartRequirement``.  The branch is a
    MEMBER TYPE -- a nested union's branch, which needs no name of its own, so the walk
    records no index -- and with no title, no pin, no top-level ``required`` and no ``$ref``
    its candidate list was a chain of ONE.  Nothing to lengthen by and nothing to fall to is
    ``names.spell``'s refusal, which the compiler reported as ``title`` VERDICT at that
    pointer with five more documents chained behind it.

    Bundle 3.2 states the same union with ``required: ["timezone_modes"]`` at the branch's
    top level and never refused -- candidate 3 named it ``DaypartRequirementTimezoneModes``.  3.3
    added ``time_granularity`` and moved the requiredness into a nested
    ``anyOf: [{required: [timezone_modes]}, {required: [time_granularity]}]``, so the candidate
    went silent on a node whose requiredness the document states as plainly as 3.2's did.

    Both halves are asserted, because the second means nothing without the first: that the
    two positions really do collide and that the candidate list really is spent WITHOUT the candidate,
    and that WITH it the branch falls and the entry keeps the name it derives.
    """
    hops: dict[str, names.Hop] = {
        "": names.Root("Targeting Overlay Requirements"),
        "/definitions/daypartRequirement": names.Entry("daypartRequirement"),
        "/definitions/daypartRequirement/anyOf/1": names.Branch(
            parent="/definitions/daypartRequirement"
        ),
    }
    silent = dict(hops)
    silent["/definitions/daypartRequirement/anyOf/1"] = names.Branch(
        parent="/definitions/daypartRequirement"
    )
    assert names.candidate_names("/definitions/daypartRequirement/anyOf/1", silent) == (
        ("TargetingOverlayRequirements", "DaypartRequirement"),
    ), "without the candidate the member type has ONE chain, which is why this refused"
    assert isinstance(names.spell_the_candidates(_candidate_names(silent)), Refusal), (
        "the two positions must collide with the candidate absent, or the fall below is not "
        "what resolves them"
    )

    hops["/definitions/daypartRequirement/anyOf/1"] = names.Branch(
        parent="/definitions/daypartRequirement",
        requires_one_of=("timezone_modes", "time_granularity"),
    )
    candidate_lists = _candidate_names(hops)
    candidates = candidate_lists["/definitions/daypartRequirement/anyOf/1"]
    assert candidates[0] == ("TargetingOverlayRequirements", "DaypartRequirement"), candidates
    assert candidates[-1] != candidates[0], "the requirement candidate has to be a chain to FALL to"
    spelled = names.spell_the_candidates(candidate_lists)
    assert not isinstance(spelled, Refusal), spelled
    # The ENTRY keeps the name §4 derives for it and SHORTENS back to it, because once the
    # branch has fallen nothing collides and a position whose short name collides with
    # nothing keeps it -- which is the pair of names the run emits for bundle 3.3.
    assert spelled == {
        "": "TargetingOverlayRequirements",
        "/definitions/daypartRequirement": "DaypartRequirement",
        "/definitions/daypartRequirement/anyOf/1": (
            "DaypartRequirementTimeGranularityTimezoneModes"
        ),
    }, spelled


def test_requiredness_one_level_down_is_a_fall_and_never_the_name_a_branch_takes() -> None:
    """The candidate's PLACEMENT, which is the whole decision and not an implementation detail.

    Read as a fifth IDENTITY rule the same fact renames classes that collide with nothing:
    ``core/targeting-overlay-requirements.json#/properties/geo_proximity/anyOf/1`` is a
    member type with the identical shape -- four properties and
    ``anyOf: [{required: [radius]}, {required: [travel_time]}, {required: [geometry]},
    {required: [transport_modes]}]`` -- and bundle 3.2 ships it as
    ``TargetingOverlayRequirementsGeoProximity``.  §4's identity rules are a CLOSED list and
    its answer for a branch none of them names is the union's own derived name, which is a
    rule and not a gap; so a branch that collides with nothing keeps it, and the candidate is a
    name available only to one that cannot.
    """
    hops: dict[str, names.Hop] = {
        "": names.Root("Targeting Overlay Requirements"),
        "/properties/geo_proximity": names.Property("", "geo_proximity"),
        "/properties/geo_proximity/anyOf/1": names.Branch(
            parent="/properties/geo_proximity",
            requires_one_of=("radius", "travel_time", "geometry", "transport_modes"),
        ),
    }
    hop = hops["/properties/geo_proximity/anyOf/1"]
    parent = ("TargetingOverlayRequirements", "GeoProximity")
    assert hop.requires_one_of, "the fact must be present, or the claim below is vacuous"
    assert names.branch_identity(hop, parent) is None, (
        "the candidate must not reach branch_identity: that is the name a branch TAKES"
    )
    assert names.branch_candidates(hop, parent) == ()
    # The union at the PROPERTY declares nothing -- it decides to an annotation,
    # ``Required | GeoProximity | None`` -- and ``names.assign`` asks for a candidate list at the
    # pointers that DECLARE, so that position is not one of them.  The candidate_lists are built
    # over the same two, because handing in a pointer the module never declares would
    # invent a collision the run does not have.
    candidate_lists = _candidate_names(hops)
    at = "/properties/geo_proximity/anyOf/1"
    assert candidate_lists[at][0] == ("TargetingOverlayRequirements", "GeoProximity"), (
        "the FIRST candidate is the union's own derived chain, which is what the branch is "
        "named by -- the requirement candidate is below it"
    )
    spelled = names.spell_the_candidates({p: candidate_lists[p] for p in ("", at)})
    assert not isinstance(spelled, Refusal), spelled
    # Spelled at depth 1 because nothing in this table collides; the shipped module
    # lengthens it to ``TargetingOverlayRequirementsGeoProximity`` for a collision outside
    # these two positions, and the lengthening axis is not what this test is about.  What
    # it is about is that the name comes off the chain above and never off the four keys.
    assert spelled[at] == "GeoProximity", spelled
    assert "Radius" not in spelled[at] and "TravelTime" not in spelled[at]


def test_the_reading_of_requiredness_one_level_down_is_the_declarations_and_not_a_guess() -> None:
    """``lower.union._requires_one_of``: what is read and what is refused.

    Every clause of the narrowing is load-bearing and each is graded here, because each one
    is what keeps the reading off a node that requires nothing of the sort.  A ``required``
    inside an ``if`` is the ANTECEDENT of an implication -- bundle 3.3's own daypart branch
    states ``allOf: [{if: {required: [iana_timezones]}, then: ...}]`` beside the ``anyOf``
    this reads, and ``iana_timezones`` is not required at all.
    """
    properties = {"a": {}, "b": {}}
    requires = union._requires_one_of
    assert requires(
        {"properties": properties, "anyOf": [{"required": ["a"]}, {"required": ["b"]}]}
    ) == ("a", "b")
    assert requires(
        {"properties": properties, "oneOf": [{"required": ["a"]}, {"required": ["b"]}]}
    ) == ("a", "b")
    # A member that states anything beside ``required`` is a subschema in its own right.
    assert requires(
        {"properties": properties, "anyOf": [{"required": ["a"]}, {"required": ["b"], "type": "object"}]}
    ) == ()
    # EVERY member or none: a member requiring nothing makes the combinator require nothing.
    assert requires({"properties": properties, "anyOf": [{"required": ["a"]}, {}]}) == ()
    # A CONDITIONAL is never read, which the "required alone" clause is what refuses.
    assert requires(
        {"properties": properties, "allOf": [{"if": {"required": ["a"]}, "then": {"required": ["b"]}}]}
    ) == ()
    assert requires({"properties": properties, "not": {"required": ["a"]}}) == ()
    # A key the branch declares no property for says nothing about the branch's own fields,
    # and a node with no property map is not this shape at all.
    assert requires({"properties": properties, "anyOf": [{"required": ["a"]}, {"required": ["z"]}]}) == ()
    assert requires({"anyOf": [{"required": ["a"]}, {"required": ["b"]}]}) == ()
    # Where the branch states ``required`` ITSELF, candidate 3 answers and this reads nothing.
    assert requires(
        {"properties": properties, "required": ["a"], "anyOf": [{"required": ["a"]}, {"required": ["b"]}]}
    ) == ()
