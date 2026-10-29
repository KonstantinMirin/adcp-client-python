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
    # §4's FOURTH rung, ``<Base>Branch<i>`` (``adcp-client-python-10l.41``).  It is the
    # LAST one and reached only here: the three rungs above each answered nothing, and a
    # document that gives a branch no identity at all leaves nothing else to read.
    assert names.branch_identity(names.Branch(parent="/x", index=3), parent) == (
        "MediaBuy",
        "TransitionsItemBranch3",
    )
    # And the index never OUTRANKS an identity, which is the whole of why it is accepted:
    # the same hop carrying a title takes the title, and carrying a pin takes the pin.
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
    # The ONE hop left with no name at all is a NESTED union's branch, whose index the
    # walk does not record because a member type needs no name of its own; ``segments``
    # gives it the union's own derived name and nothing refuses.
    assert names.branch_identity(names.Branch(parent="/x"), parent) is None


def test_inserting_a_branch_after_an_indexed_one_moves_no_existing_name() -> None:
    """The row's own acceptance criterion: every branch class name is a function of the
    branch node ALONE, so adding a sibling branch renames nothing already emitted.

    :data:`names.INDEX_IS_THE_LAST_RUNG` is the sentence.  A positional name is normally
    the defect -- the upstream v9 SDK numbers 1,092 of its 4,360 classes and renames a
    sibling when a branch is inserted ahead of it -- and §4 accepts it only as the last
    rung, where there is nothing else to read.  What makes it safe at that rung is that
    an index is a fact of the branch's OWN position: it is never derived from what the
    siblings state, so a branch APPENDED to the combinator adds a name and moves none.

    Insertion in the MIDDLE does move the names after it, and that is the honest limit of
    the rung -- §4 says "stable under insertion only at the end" -- so this grades the
    property the section claims and not a stronger one.  A document that wants a stable
    name under reordering states a ``title``, which is rung 1 and is what the upstream
    candidate asks for.
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
    # The APPENDED branch adds a name and moves none: the row renames nothing but adds.
    assert {p: n for p, n in four.items() if p in three} == three, four
    assert four["/anyOf/3"] == "AssetRequirementsBranch3", four


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

    Measured on the tree ``adcp-client-python-10l.50`` produced: 2,092 classes, median
    17, mean 18.29, max 76, and 221 / 64 / 13 / 7 longer than 30 / 40 / 50 / 60
    characters -- against 2,066 classes, median 26, mean 28.66 and 778 / 347 / 135 / 46
    before it.  A ceiling, so a row that emits more documents may raise the COUNT of long
    names and not the share: ``adcp-client-python-10l.41`` emitted 5 documents more and
    the tree is 2,165 classes, median 17, mean 18.39, max 76 and 223 / 64 / 13 / 7 -- the
    count over 30 moved by 2 and the share over 40 did not move at all.
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
            "and is 3% of its 2,165 after.  A ceiling on the SHARE and not the count, "
            "because a row that emits more documents moves the count and not the rule"
        ),
    )


# --------------------------------------------------------------------------- #
# §4's RUNG axis (``adcp-client-python-10l.78``)
# --------------------------------------------------------------------------- #
def _ladders(hops: dict[str, names.Hop]) -> dict[str, tuple[tuple[str, ...], ...]]:
    """Every pointer with §4's RUNGS for it, which is what ``spell_the_rungs`` takes."""
    out = {}
    for pointer in hops:
        rungs = names.ladder(pointer, hops)
        assert not isinstance(rungs, Refusal), rungs
        out[pointer] = rungs
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


def test_a_rung_that_collides_has_not_identified_the_branch_so_both_fall() -> None:
    """§4: "Where a rung derives one name for two branches it has not identified either,
    so both fall to the next rung."

    ``trusted-match/provider-registration.json``'s own shape: two branches pinning
    ``context_match: true`` and ``identity_match: true``.  The value ``true`` is the same
    on both and names neither, so rung 2 answers ONE name for the pair and rung 3's
    ``required`` set is what identifies them.  Both halves are asserted, because the
    second means nothing without the first: that the rung really does collide, and that
    the fall lands on the required set.
    """
    hops = {
        "": names.Root("TMP Provider Registration"),
        "/anyOf/0": names.Branch(
            parent="", pins=(True,), required=("context_match",), index=0
        ),
        "/anyOf/1": names.Branch(
            parent="", pins=(True,), required=("identity_match",), index=1
        ),
    }
    base = ("TMPProviderRegistration",)
    assert names.branch_identity(hops["/anyOf/0"], base) == names.branch_identity(
        hops["/anyOf/1"], base
    ), "rung 2 must collide for the fall to be what resolves this"
    spelled = names.spell_the_rungs(_ladders(hops))
    assert not isinstance(spelled, Refusal), spelled
    assert spelled == {
        "": "TMPProviderRegistration",
        "/anyOf/0": "TMPProviderRegistrationContextMatch",
        "/anyOf/1": "TMPProviderRegistrationIdentityMatch",
    }, spelled


def test_a_branch_colliding_with_its_own_root_loses_the_name_and_the_root_keeps_it() -> None:
    """§4: "the root keeps the name and the branch falls to the next rung".

    ``core/postal-area.json``'s own shape: the root is titled "Postal Area" and its
    ``/anyOf/0`` is titled "PostalArea", so both derive ``PostalArea`` and neither has an
    ancestor segment to spend.  This refused as a hand-minted VERDICT, writing off the
    document and the 31 chained behind it for a naming choice this compiler makes.

    **The root is not special-cased and the assertion is written so that one would be
    visible.**  What makes the root keep the name is that its LADDER has one rung, which
    is D5 fixing a document's exported symbol -- so the ladder lengths are asserted beside
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
    ladders = _ladders(hops)
    assert len(ladders[""]) == 1, "a root has ONE rung: D5 fixes the exported symbol"
    assert len(ladders["/anyOf/0"]) > 1, "a titled branch has rungs to fall to"
    spelled = names.spell_the_rungs(ladders)
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
    ladders = _ladders(hops)
    assert ladders["/properties/a/anyOf/0"][0] == ("Doc", "AX"), ladders
    spelled = names.spell_the_rungs(ladders)
    assert not isinstance(spelled, Refusal), spelled
    assert spelled["/properties/a/anyOf/0"] == "DocAX", spelled
    assert spelled["/properties/b/properties/aX"] == "BAX", spelled
    # The identity is the PIN's and was not given up: the required set would have spelled
    # ``AQ`` and the index ``ABranch0``, and neither appears.
    assert "Q" not in spelled["/properties/a/anyOf/0"]
    assert "Branch" not in spelled["/properties/a/anyOf/0"]


def test_a_bare_ref_branch_takes_its_targets_distinguishing_name_and_not_its_index() -> None:
    """§4's FOURTH rung: "where the branch is a bare ``$ref``, the TARGET's own derived
    name"; and "where the root's name and the target's share a run, the branch takes the
    root's name plus the target's distinguishing remainder".

    ``core/requirements/asset-requirements.json``'s own shape, which is what the rung is
    written for: twelve branches, every one of them a bare ``$ref`` with no ``title``, no
    ``const`` pin and no ``required`` set, so rungs 1 to 3 answer nothing and all twelve
    reached the index.  ``isinstance(req, AssetRequirementsBranch7)`` requires counting the
    document's branches to learn that it means JavaScript, which is the usability failure a
    positional name IS -- and the fact the rung reads was sitting in the branch's second
    base the whole time.

    **The run is read at either END, because the bundle writes it both ways.**  The target
    carries it as a SUFFIX here (``ImageAssetRequirements`` beside ``AssetRequirements``)
    and as a PREFIX in ``creative/get-creative-features-response.json``
    (``GetCreativeFeaturesSuccess`` beside ``GetCreativeFeaturesResponse``), and one rule
    covers both: 12 of the bundle's 13 such branches share a suffix, 1 a prefix, 0 both.

    **Why the remainder and not the target's name spelled straight.**  The branch's second
    base IS the target, so the module imports that symbol, and :func:`names.spell`'s
    ``occupied`` says an imported name is a name taken.  A branch is a chain of ONE at this
    rung and has no ancestor to lengthen by, so ``occupied`` would keep the shadowing name
    rather than refuse it -- which is a shape the bundle already has at rung 1 and
    ``test_no_module_of_the_tree_declares_a_name_it_imports`` is red on
    (``core/vendor_pricing_option.py``, five branches titled exactly as their targets).
    """
    hops = {
        "": names.Root("Asset Requirements"),
        "/anyOf/0": names.Branch(parent="", target="ImageAssetRequirements", index=0),
        "/anyOf/1": names.Branch(parent="", target="JavaScriptAssetRequirements", index=1),
        "/anyOf/2": names.Branch(parent="", target="DAASTAssetRequirements", index=2),
    }
    spelled = names.spell_the_rungs(_ladders(hops))
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
    prefixed = names.spell_the_rungs(
        _ladders(
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
    unrelated = names.spell_the_rungs(
        _ladders({"": names.Root("Doc"), "/oneOf/0": names.Branch(parent="", target="Other", index=0)})
    )
    assert not isinstance(unrelated, Refusal), unrelated
    assert unrelated["/oneOf/0"] == "DocOther", unrelated

    # A target whose name says NOTHING the root's does not leaves the rung answering
    # nothing, and the branch keeps its index -- the same shape §4's root-collision clause
    # has: a rung that identifies nothing is not a rung to fall to.
    same = names.spell_the_rungs(
        _ladders({"": names.Root("Doc"), "/oneOf/0": names.Branch(parent="", target="Doc", index=0)})
    )
    assert not isinstance(same, Refusal), same
    assert same["/oneOf/0"] == "DocBranch0", same


def test_the_ref_target_rung_outranks_the_index_and_nothing_else() -> None:
    """The rung's PLACE in the ladder, which is what keeps the rename set bounded.

    It sits below the three declared-identity rungs and above the index, so the only
    branches it can move are the ones that were reaching the index -- which is why the
    measured rename census over bundle 3.2 is 13 classes in 2 documents and 3,449 classes
    before and after.  A sibling named by a ``title``, a pin or a required set does not
    move, which is what ``core/postal-country-system.json``'s four single-pin branches
    (``US``, ``GB``, ``CA``, ``Plz``) need.

    Insertion stability is unchanged and is the reason the rung is admissible at all: both
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
    # and not a name, so neither reaches this rung and both answer nothing.
    assert names.branch_identity(names.Branch(parent=""), parent) is None

    # Appending a branch moves no existing name, because no rung reads a sibling.
    def hops(targets: tuple[str, ...]) -> dict[str, names.Hop]:
        table: dict[str, names.Hop] = {"": names.Root("Asset Requirements")}
        for i, target in enumerate(targets):
            table[f"/anyOf/{i}"] = names.Branch(parent="", target=target, index=i)
        return table

    two = names.spell_the_rungs(_ladders(hops(("ImageAssetRequirements", "VideoAssetRequirements"))))
    three = names.spell_the_rungs(
        _ladders(hops(("ImageAssetRequirements", "VideoAssetRequirements", "AudioAssetRequirements")))
    )
    assert not isinstance(two, Refusal) and not isinstance(three, Refusal)
    assert {p: n for p, n in three.items() if p in two} == two, three
    assert three["/anyOf/2"] == "AssetRequirementsAudio", three
