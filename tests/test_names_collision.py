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

from codegen import emit
from codegen.lower import names
from codegen.refusal import Refusal

from tests.nodeset import claimed, ratchet

REPO = Path(__file__).resolve().parents[1]
TREE = REPO / emit.TREE


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
    entry is ``<Root><Key>``, which is one segment for the same reason the element is --
    the section states the prefix as part of the name.
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
        "/definitions/budget": "MediaBuyBudget",
        "/properties/key/propertyNames": "",
    }, spelled
    # And the whole chain is the name the fold gave before the rule was written, which
    # is what makes the refusal below the same refusal over the same documents.
    assert names.spelling(names.segments("/properties/packages/items", hops), 2) == (
        "MediaBuyPackagesItem"
    )


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
    """§4's three branch rules, as the segments each one places.

    A title names ITSELF, so it starts a chain and the branch's ancestors are no part of
    it; a ``const`` pin and a required set are spelled ON the parent's own segment, so a
    branch named by either shares its base's spelling.  Which fact wins decides the
    spelling and the placement together, which is why ``branch_identity`` returns both.
    """
    parent = ("MediaBuy", "TransitionsItem")
    assert names.branch_identity(names.Branch(parent="/x", title="Timer Transition"), parent) == (
        ("TimerTransition",)
    )
    assert names.branch_identity(names.Branch(parent="/x", pin="media_event"), parent) == (
        "MediaBuy",
        "TransitionsItemMediaEvent",
    )
    assert names.branch_identity(
        names.Branch(parent="/x", required=("trigger", "input")), parent
    ) == ("MediaBuy", "TransitionsItemInputTrigger")
    assert names.branch_identity(names.Branch(parent="/x"), parent) is None


# --------------------------------------------------------------------------- #
# the two properties that are about the whole tree, read off its own text
# --------------------------------------------------------------------------- #
def _modules() -> dict[str, ast.Module]:
    """Every module of the committed tree, parsed.  The TEXT and not the emitter, so
    what is graded is what a consumer imports."""
    return {
        str(path.relative_to(TREE)): ast.parse(path.read_text())
        for path in sorted(TREE.rglob("*.py"))
        if path.name != "__init__.py"
    }


def test_no_module_of_the_tree_declares_two_symbols_under_one_name() -> None:
    """The acceptance criterion of the row, over the tree rather than over a hop table:
    §1 gives a class ONE import path, so one name in one module names one thing."""
    modules = _modules()
    claimed("the committed tree's modules", modules)
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
    assert twice == {}, twice


def test_no_module_of_the_tree_declares_a_name_it_imports() -> None:
    """A declaration that shadows an import retypes every field annotated with it.

    The failure is silent in the type checker and loud at import -- a ``StrEnum`` named
    ``Field`` is called as ``Field(description=…)`` -- and §4's short nested rule is what
    makes it reachable: ``names.spell``'s ``occupied`` is the guard and this is the
    measurement over the output.
    """
    modules = _modules()
    claimed("the committed tree's modules", modules)
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
    assert shadowed == {}, shadowed


def test_the_long_name_is_the_exception_and_not_the_rule() -> None:
    """A RATCHET and not a pin, because §4's own acceptance criterion is a direction:
    "the median name length falls and the count over 40 chars falls sharply; both are
    reported as measurements, not pinned".

    Measured on the tree this row produced: 2,092 classes, median 17, mean 18.29, max
    76, and 221 / 64 / 13 / 7 longer than 30 / 40 / 50 / 60 characters -- against 2,066
    classes, median 26, mean 28.66 and 778 / 347 / 135 / 46 before it.  A ceiling, so a
    row that emits more documents may raise the COUNT of long names and not the share.
    """
    classes = claimed(
        "every class statement of the committed tree",
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
            "and is 3% of its 2,092 after.  A ceiling on the SHARE and not the count, "
            "because a row that emits more documents moves the count and not the rule"
        ),
    )
