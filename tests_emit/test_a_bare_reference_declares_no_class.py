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
Field(description=…)]`` keeps the sentence exactly where §6 wants it -- and the 27 were
defects rather than a decision to re-open. **Reading that row first is what tells a defect
from a decision**, which is ``CLAUDE.md``'s opening rule and was skipped when this gate was
first written.

**AND THE ROW'S SCREEN IS VACUOUS AT PROP, which is why the fix is the position and not a
list of admitted words.** ``Effect.ANNOTATION`` has exactly four members at PROP --
``description``, ``deprecated``, ``enumDescriptions``, ``x-enum-descriptions`` -- against
``NOTHING``'s 67, and the collapse destroys the carrier of none of them: the first two ride
the enclosing ``Field(...)``, which survives, and the last two are the enum MEMBER
docstrings of the ``$ref`` target's own type, which the wrapper never held. At ELEM there is
no per-element ``Field``, so the screen still runs there; at ROOT the row declines already.

**A DOCUMENT ROOT IS EXEMPT, AND THAT IS NOT A LOOPHOLE.** §3a: *"A DOCUMENT ROOT IS
ALREADY A HOME"*. A root is a public named type and the wrapper is what gives the
operation its own word -- ``BuyProductsSubmitted`` on ``{allOf: [$ref
core/compact-task-submitted.json]}`` is a service to a consumer, not a duplicate. Measured,
18 of the 45 declaring positions are roots.

**THE DEFECTS WERE ENUMERATED AND NOT COUNTED**, which is ``test_catalogue.py``'s standing
rule for this file: *"there are N of these" freezes the tree and "this cannot happen"
survives a refactor*. ``MINTS_A_WRAPPER`` was that exact set, asserted exactly in both
directions -- a NEW wrapper reddened this gate and a wrapper that stopped being minted
reddened it too, naming the line to delete. All 27 are now gone, so the enumeration is
gone with them and what is left is the rule with no exceptions: **a non-root position
asserting one bare ``$ref`` declares no class**, and the first class to appear at one
reddens this gate.
"""

from __future__ import annotations

import ast
import json

import fresh
from nodeset import claimed

from codegen import bundle

BUNDLE = fresh.BUNDLE

#: **THE ENUMERATION IS GONE BECAUSE ITS 27 ENTRIES ARE**, and the invariant it guarded is
#: the assertion below, now unconditional.
#:
#: Every line named a position whose only assertion was a single bare ``$ref`` and which
#: declared a class anyway, and the naming collapse is what made the set legible:
#: ``Bidding`` was minted SEVEN times over, every one of them referencing
#: ``core/bidding-policy.json``; ``Window`` three times and ``EstimatedWait`` twice, both
#: over ``core/duration.json``.  Counting ``PostClick``, ``PostView``, ``Suppress``,
#: ``TimeBudget`` and ``Period``, **``core/duration.json`` was one concept emitted as eight
#: differently-named classes** -- so a consumer holding a ``FrequencyCap.window`` could not
#: pass it where an ``AttributionWindow.post_click`` was wanted, though the document says
#: they are the same duration.
#:
#: What took all 27 is ``codegen/lower/composition.py``'s
#: ``declares_nothing_its_base_does_not``, whose annotation screen now reads the node's
#: POSITION: at PROP -- which is where every one of the 27 was -- ``Effect.ANNOTATION`` has
#: four members and the collapse destroys the carrier of none of them, because
#: ``description`` and ``deprecated`` ride the ENCLOSING FIELD and the two enum-description
#: keywords belong to the target's own enum type.  So the sentence each wrapper carried as
#: a docstring stays on the field it was already on, and the type is the target's:
#: ``window: Annotated[Duration | None, Field(description='Time window for the
#: max_impressions cap …')]``.


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

    #: **NOTHING IS ENUMERATED, SO THE INVARIANT IS THE WHOLE ASSERTION.**  There were 27
    #: exceptions and :data:`MINTS_A_WRAPPER` held them so that neither direction could
    #: pass silently -- a new wrapper reddened this, and a wrapper that stopped being
    #: minted reddened it too, naming the line to delete.  All 27 are gone, so the
    #: subtraction has nothing left to subtract and the second assertion has nothing left
    #: to assert: what remains is §3a's rule itself, unqualified.
    appeared = {f"{d}{p}": names for (d, p), names in minting.items()}
    assert not appeared, (
        "a bare annotated $ref declares a class at a position §3a says is a $ref row:\n"
        + json.dumps(appeared, indent=2)
    )
