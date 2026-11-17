"""**THE GATE FOR §3a's BARE ANNOTATED ``$ref``**: such a position declares no class.

``docs/plan/architecture.md`` §3a, *"A COMPOSITION WHOSE ONLY CONJUNCT IS A ``$ref`` IS
THAT REFERENCE, AND MINTS NOTHING"*. In draft-07 a keyword stated beside a ``$ref`` is
ignored, so an author with a sentence to write about a reference has one idiom::

    {"allOf": [{"$ref": ".../core/duration.json"}],
     "description": "Post-click attribution window."}

That node states no property, no ``required`` and no narrowing keyword. It admits exactly
what its target admits, so by §3a's own admission test -- *in the key if and only if some
instance turns on it* -- it is a §5 ``$ref`` row and the type there is the target's.

**WHY NO EXISTING LAYER CATCHES THEM, traced one step at a time.** This is the answer to
*how was this not discovered when the types were surveyed*, and each step is measured
rather than reasoned:

1. the position is **not an L2 stating position at all** -- L2 collects OBJECT types and
   such a node states no ``properties`` of its own. Measured: of the 53 non-root bare
   annotated ``$ref`` positions, **0 appear in ``Shapes.positions``** for L2, so
   ``test_catalogue.py``'s L2 gate never ranges over one;
2. **L2C is the layer that covers a composed node, and it collects 0 entries.** Its
   evidence rule is that the bundle must ``title`` every stating position of a group with
   one and the same word -- which is right, and which stops a coincidental overlap between
   DISTINCT nodes being collapsed into one class. Measured, it returns **0 entries and 28
   untitled groups**;
3. so **no layer collapses them**, and the walk mints a class at each.

**AND L2C's TITLE RULE IS NOT THE THING TO WEAKEN**, which is why this gate is separate
from it. That rule asks for evidence that two distinct nodes are one subject. A bare
annotated ``$ref`` is not that question: the subject is named already, on the document the
reference reaches. Nothing here needs a title, and nothing here collapses two nodes
together -- it removes a second definition of one node.

**THE LOWERING ROW ALSO ALREADY DECIDED THIS, AND THE DECISION IS REFUTED BY THE TREE AND
NOT BY THIS GATE'S OPINION.** ``codegen/lower/composition.py``'s
``declares_nothing_its_base_does_not`` is the collapse and already returns the target as
the node's own type where the node adds nothing. Its own census of this shape -- 235
single-``$ref`` ``allOf`` nodes, 108 at a root, 7 of the 127 non-root stating only a
``NOTHING`` keyword and **50 stating a bare ``description``** -- decided to KEEP the class
at those 50, because §6 makes a node's own ``description`` authoritative at its own pointer
and dropping it would lose a fact the document states.

**That premise does not hold: the description is ALREADY on the field.**
``core/frequency_cap.py`` emits it twice, once as ``class Window(Duration)``'s docstring
and once as ``window: Annotated[Window | None, Field(description='Time window for the
max_impressions cap …')]``, and the field's copy is present at ``PostClick``, ``Bidding``
and ``TimeBudget`` too. So the collapse drops nothing -- ``Annotated[Duration | None,
Field(description=…)]`` keeps the sentence exactly where §6 wants it -- and the 27 below are
defects rather than a decision to re-open. **Reading that row first is what tells a defect
from a decision**, which is ``CLAUDE.md``'s opening rule and was skipped when this gate was
first written.

**A DOCUMENT ROOT IS EXEMPT, AND THAT IS NOT A LOOPHOLE.** §3a: *"A DOCUMENT ROOT IS
ALREADY A HOME"*. A root is a public named type and the wrapper is what gives the
operation its own word -- ``BuyProductsSubmitted`` on ``{allOf: [$ref
core/compact-task-submitted.json]}`` is a service to a consumer, not a duplicate. Measured,
18 of the 45 declaring positions are roots.

**THE DEFECTS ARE ENUMERATED AND NOT COUNTED**, which is ``test_catalogue.py``'s standing
rule for this file: *"there are N of these" freezes the tree and "this cannot happen"
survives a refactor*. So :data:`MINTS_A_WRAPPER` is the exact set, asserted exactly: a NEW
wrapper reddens this gate, and a wrapper that stops being minted reddens it too, naming
the line to delete. Neither direction can pass silently.
"""

from __future__ import annotations

import ast
import json

import fresh
from nodeset import claimed

from codegen import bundle

BUNDLE = fresh.BUNDLE

#: ``(document, pointer)`` -> the class a fresh run declares at a position whose only
#: assertion is a single bare ``$ref``, and the document that ``$ref`` names.
#:
#: **EVERY LINE IS A DEFECT AND THE NAMING COLLAPSE IS WHY IT IS LEGIBLE.** ``Bidding`` is
#: minted SEVEN times over, every one of them referencing ``core/bidding-policy.json``;
#: ``Window`` three times and ``EstimatedWait`` twice, both over ``core/duration.json``.
#: Counting ``PostClick``, ``PostView``, ``Suppress``, ``TimeBudget`` and ``Period``,
#: **``core/duration.json`` is one concept emitted as eight differently-named classes** --
#: so a consumer holding a ``FrequencyCap.window`` cannot pass it where an
#: ``AttributionWindow.post_click`` is wanted, though the document says they are the same
#: duration. That is the defect §3a's catalogue exists to remove, arriving at the layer
#: whose key was missing.
MINTS_A_WRAPPER: dict[tuple[str, str], tuple[str, str]] = {
    ("compliance/comply-test-controller-request.json",
     "/properties/params/properties/dooh_metrics"): (
        "core/delivery-metrics.json#/properties/dooh_metrics", "ParamsDoohMetrics"),
    ("compliance/comply-test-controller-request.json",
     "/properties/params/properties/viewability"): (
        "core/delivery-metrics.json#/properties/viewability", "ParamsViewability"),
    ("core/attribution-window.json", "/properties/post_click"): ("core/duration.json", "PostClick"),
    ("core/attribution-window.json", "/properties/post_view"): ("core/duration.json", "PostView"),
    ("core/canonical-proposal.json", "/properties/forecast"): (
        "core/canonical-delivery-forecast.json", "Forecast"),
    ("core/delivery-metrics.json", "/properties/reach_window/properties/period"): (
        "core/duration.json", "Period"),
    ("core/frequency-cap.json", "/properties/suppress"): ("core/duration.json", "Suppress"),
    ("core/frequency-cap.json", "/properties/window"): ("core/duration.json", "Window"),
    ("core/media-buy-features.json", "/properties/bidding_policy"): (
        "core/bidding-policy-capability.json", "MediaBuyFeaturesBiddingPolicy"),
    ("core/media-buy.json", "/properties/bidding"): ("core/bidding-policy.json", "Bidding"),
    ("core/optimization-goal.json", "/oneOf/0/properties/target_frequency/properties/window"): (
        "core/duration.json", "Window"),
    ("core/optimization-goal.json", "/oneOf/0/properties/vendor"): (
        "core/brand-ref.json", "Vendor"),
    ("core/optimization-goal.json", "/oneOf/1/properties/attribution_window"): (
        "core/attribution-window.json", "OptimizationGoalEventAttributionWindow"),
    ("core/outcome-measurement.json", "/properties/window"): ("core/duration.json", "Window"),
    ("core/package.json", "/properties/bidding"): ("core/bidding-policy.json", "Bidding"),
    ("core/planned-delivery.json", "/properties/bidding"): ("core/bidding-policy.json", "Bidding"),
    ("core/targeting-overlay-support.json", "/properties/frequency_cap_support"): (
        "core/frequency-cap-constraints.json", "FrequencyCapSupport"),
    ("media-buy/create-media-buy-request.json", "/properties/bidding"): (
        "core/bidding-policy.json", "Bidding"),
    ("media-buy/create-media-buy-response.json", "/oneOf/0/properties/bidding"): (
        "core/bidding-policy.json", "Bidding"),
    ("media-buy/get-media-buy-delivery-response.json",
     "/properties/media_buy_deliveries/items/properties/windows/items/properties/totals"): (
        "core/delivery-metrics.json", "WindowsItemTotals"),
    ("media-buy/get-media-buys-response.json", "/properties/media_buys/items/properties/bidding"): (
        "core/bidding-policy.json", "MediaBuysItemBidding"),
    ("media-buy/get-media-buys-response.json",
     "/properties/media_buys/items/properties/packages/items/properties/bidding"): (
        "core/bidding-policy.json", "PackagesItemBidding"),
    ("media-buy/get-products-request.json", "/properties/time_budget"): (
        "core/duration.json", "TimeBudget"),
    ("media-buy/get-products-response.json",
     "/properties/incomplete/items/properties/estimated_wait"): (
        "core/duration.json", "EstimatedWait"),
    ("media-buy/package-request.json", "/properties/bidding"): (
        "core/bidding-policy.json", "Bidding"),
    ("media-buy/update-media-buy-response.json", "/oneOf/0/properties/bidding"): (
        "core/bidding-policy.json", "Bidding"),
    ("signals/get-signals-response.json",
     "/properties/incomplete/items/properties/estimated_wait"): (
        "core/duration.json", "EstimatedWait"),
}


def test_a_bare_annotated_reference_declares_no_class() -> None:
    """A non-root position asserting one bare ``$ref`` declares no class of its own.

    **The classification is ``survey/composites.py``'s and is not restated here**, which
    is the reason that module takes all three of its readings off the compiler: the
    document screen is ``catalogue.stating``, the walk is ``bundle.nodes_at``, and the
    annotation set is ``catalogue.ANNOTATIONS``. A test with its own walk would be a second
    answer to the same question, and the first draft of that module proved what that costs
    -- its hand-rolled walk read 125 documents no layer collects from and joined to the
    emitted tree on a pointer with no leading ``#``, so it matched the roots alone and
    reported the PROP positions as already handled.

    **Read off the CLASS STATEMENTS of a FRESH emission**, which is §9's rule that the
    subject of grading is a fresh emit and never the committed tree, and keyed on the
    ``__adcp_schema__`` each class binds rather than on a name two modules might spell
    alike.
    """
    from compiled import compiled

    from survey.composites import compositions

    bare = claimed(
        "non-root positions asserting one bare annotated $ref",
        (
            (row["document"], row["pointer"].lstrip("#"))
            for row in compositions(BUNDLE)
            if row["group"] == "is_the_reference" and row["pointer"] != "#"
        ),
    )

    out = compiled(BUNDLE, sorted(bundle.portable(BUNDLE)))
    declaring: dict[tuple[str, str], list[str]] = {}
    for text in out.files.values():
        for node in ast.parse(text).body:
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                if not (
                    isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                    and statement.target.id == "__adcp_schema__"
                    and isinstance(statement.value, ast.Call)
                ):
                    continue
                said = {k.arg: k.value for k in statement.value.keywords}
                document, pointer = said.get("document"), said.get("pointer")
                if isinstance(document, ast.Constant) and isinstance(pointer, ast.Constant):
                    at = (document.value, pointer.value.lstrip("#"))
                    declaring.setdefault(at, []).append(node.name)

    minting = {at: declaring[at] for at in sorted(bare) if at in declaring}

    #: **ASSERTED EXACTLY, so neither direction passes silently.**  A position that starts
    #: minting is a regression; a position that stops is the fix, and the line owed to
    #: :data:`MINTS_A_WRAPPER` is named here rather than left for a later reader to find.
    appeared = {f"{d}{p}": names for (d, p), names in minting.items()
                if (d, p) not in MINTS_A_WRAPPER}
    assert not appeared, (
        "a bare annotated $ref declares a class at a position §3a says is a $ref row:\n"
        + json.dumps(appeared, indent=2)
    )
    fixed = {
        f"{d}{p}": f"was {cls} -> {target}; delete this line from MINTS_A_WRAPPER"
        for (d, p), (target, cls) in sorted(MINTS_A_WRAPPER.items())
        if (d, p) not in minting
    }
    assert not fixed, (
        "these positions no longer mint a wrapper, so the enumeration is stale:\n"
        + json.dumps(fixed, indent=2)
    )
