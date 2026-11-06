"""THE DECISION PER CROSS-DOCUMENT DUPLICATE GROUP, as DATA and never as a branch.

``docs/plan/architecture.md``, "THE JUDGMENT IS DATA, NEVER CODE": collection is
deterministic and so is generation, and *"the only thing that is not is whether two
identical-looking types are the same subject"*.
``tests/test_one_node_is_one_declaration.py`` measures the groups -- the declarations of the
emitted tree that are one type under the five-part key -- and asserts the same-document ones
away.  **The CROSS-document ones were reported and nothing asserted over them**, which is
the state this table ends: a group a reader has to go and look up in a bead comment is a
judgment the build does not apply, and "AN OVERRIDE THE BUILD DOES NOT APPLY IS A LIE, AND
THE GATE IS ON THE ARTIFACT" is the same sentence read from the decision's side.

**SO EVERY ROW IS KEYED ON SCHEMA NODES.**  :attr:`Decided.at` is the ``(document,
pointer)`` set the group's members name through ``__adcp_schema__`` -- never a class name,
never a module, never a count.  A row whose position set no group of the tree forms is
RED and is to be DELETED, which is the architecture's removability clause for a kind of
entry that adds no document: an extraction fails when its document arrives upstream, an
addition fails when its node states the keyword, and a decision fails **when the group it
decides is gone**.

**AND THE EVIDENCE IS AN OBLIGATION PER OUTCOME, because a verdict without one is the
error this epic has made four times.**  A shared key is a HYPOTHESIS.  Two classes
refusing one payload for *different reasons* are not the same type, and a matching verdict
on a payload nobody printed is no evidence at all.  So each of the four outcomes carries a
different evidence form and the gate grades it:

* :data:`SPLIT` -- two or more SUBJECTS.  Proved either by a ``payload`` one member's own
  DOCUMENT admits and another's refuses, or by ``titles``: two different ``title`` strings
  the bundle itself states over the group's own positions.  The second form goes red the
  day upstream unifies the two words, which is the day the split stops being the bundle's.
* :data:`PENDING_A_NAME` -- §3a's third local state, *"separate types pending a name ...
  the positions are plausibly one subject and nothing in the bundle names it"*, and
  "'DISTINCT' AND 'UNNAMEABLE' ARE DIFFERENT, AND ONLY ONE IS TERMINAL".  The evidence is
  the bundle's SILENCE: no position of the group carries a ``title`` and the positions are
  named by two or more different words, so there is nothing to transcribe and a title here
  would be ours.  The ask is the title, and the row dies the day it lands.
* :data:`NOT_ONE_TYPE` -- the group is not a duplicate at all: it exists because a fact the
  member's own document STATES was dropped from the class, so the two classes agree only
  because one of them lost its document's narrowing.  The evidence is the payload the class
  ADMITS through ``model_validate`` and its own document REFUSES through
  ``strict_validate``.  Ours, with an owner, and the row dies the day the fact is carried.
* :data:`COLLAPSE` -- one subject declared twice and ours to collapse.  The evidence is in
  three parts and all are required: no payload makes the members disagree, **no payload
  makes any member disagree with ITS OWN DOCUMENT**, and the bundle NAMES the subject at a
  position it states a ``title`` at, so collapsing mints nothing.  The middle part is the
  one a member-versus-member reading cannot give and is what separates a collapse from a
  dropped fact wearing one: the three :data:`NOT_ONE_TYPE` groups agree with each other on
  every derived payload, which is exactly why ``adcp-client-python-y4j`` first read them as
  collapses, and they disagree with their own documents at once.

**THE TABLE'S SIZE IS A DEBT FIGURE AND IT RATCHETS DOWN.**  8 rows, and every one of them
names the ask that deletes it.  For a bundle that titles what it restates and a compiler
that declares a type once, this tuple is EMPTY.

**AND THERE IS NO :data:`COLLAPSE` ROW LEFT, which is the clause closed rather than the
debt merely shrunk.**  A ``COLLAPSE`` is the one outcome whose defect is OURS -- one
subject declared twice, and the bundle names it -- so a ``COLLAPSE`` row is precisely *an
override the build does not apply*.  All three are gone, each because the BUILD applies the
judgment now and the tree stops forming the group:

* ``adcp-client-python-8212`` -- a nested key a narrowing never mentions takes the base's
  own field instead of a second decision of the base's node;
* ``adcp-client-python-nlkz`` -- a non-root node that declares nothing its base does not
  already declare identically declares no class;
* ``adcp-client-python-e4z`` -- **a stating position is read as the type the DOCUMENT
  APPLIES there** (§3a's layer L2A, ``catalogue.collect_applied``), so a ``oneOf`` branch
  that narrows a property its root states is one type with the position that spells the
  composition inline, and it is declared at the entry's own derived home.

The gate reddened on all three with "a row whose group the tree no longer forms -- DELETE
it", which is what retiring a row looks like.  **What is left is eight rows none of which
is ours to collapse**: three ``NOT ONE TYPE`` rows awaiting a dropped conjunct, three
``SPLIT`` rows the bundle's own words decide, and two ``PENDING A NAME`` rows whose ask is
upstream's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

#: One position of a group: the ``(document, pointer)`` a member names through
#: ``__adcp_schema__``.  The pointer is the record's own spelling -- ``"#"`` for a root --
#: because that is what the class carries and what a reader can go and look at.
POSITION = tuple[str, str]

SPLIT = "SPLIT"
PENDING_A_NAME = "PENDING A NAME"
NOT_ONE_TYPE = "NOT ONE TYPE"
COLLAPSE = "COLLAPSE"

#: A sentinel for "this row offers no payload", kept apart from ``None`` because ``None``
#: is a payload a check offers and a root model may admit.
NO_PAYLOAD = object()


@dataclass(frozen=True)
class Decided:
    """One cross-document duplicate group, its outcome, its evidence and its ask."""

    #: The group, keyed on schema nodes.  A frozenset because the group is a SET of
    #: positions and the tree's declaration order is not a fact about it.
    at: frozenset[POSITION]
    outcome: str
    #: The UPSTREAM or COMPILER defect this row compensates for, as a sentence about the
    #: bundle or about the walk.  §3a: "an entry with no named defect is not a judgment, it
    #: is a preference, and it does not belong in the table."
    defect: str
    #: What retires the row: an upstream issue, or the bead that owns the repair here.
    ask: str
    #: SPLIT and NOT ONE TYPE: the value that proves the outcome.  Written down and not
    #: derived, because the derived set does not find it -- measured on
    #: ``adcp-client-python-6h1``, where a payload set derived from the group's shared
    #: schema found 0 of these and a payload built from the bundle's own words found them
    #: all.  The gate prints both verdicts and both reasons.
    payload: Any = NO_PAYLOAD
    #: COLLAPSE: where the bundle NAMES the subject -- ``(document, pointer, title)``.  The
    #: gate asserts the bundle a RUN reads still states that title there, so the row goes
    #: red the day upstream renames or drops it and the collapse stops being licensed by
    #: anything.
    names_the_subject: tuple[str, str, str] | None = None
    #: A sentence a reader needs that no derivation carries: why this outcome and not the
    #: neighbouring one.
    note: str = ""


#: ``account/sync-accounts-request.json``, ``protocol/sync-agent-notification-configs-
#: request.json`` and ``protocol/sync-principal-request.json`` each state
#: ``{"if": {"required": ["authentication"]}, "then": {...credentials...}}`` as an ``allOf``
#: CONJUNCT at the referring position; ``media-buy/sync-catalogs-response.json`` states an
#: ``if``/``then`` over ``code`` the same way.  The conjunct is dropped from the class and
#: declared nowhere, so the class admits what its own document refuses.
_DROPPED_CONJUNCT = (
    "the bundle states a narrowing as an allOf CONJUNCT at the referring position and the "
    "compiler drops it from the class without declaring a widening, so the class admits a "
    "value its own document refuses -- the group is an artifact of the dropped fact and "
    "not a duplicate"
)

#: The one ask for the three notification groups, over the five documents
#: ``adcp-client-python-c510`` names.  Ours first, because an unfiled gap is ours.
_NOTIFICATION_ASK = (
    "adcp-client-python-wvod (ours: carry the conjunct's `if`, or declare the widening); "
    "adcp-client-python-c510 (upstream: one webhook-subscription concept, two contracts)"
)


DECIDED: tuple[Decided, ...] = (
    # ----------------------------------------------------------------- PENDING A NAME
    Decided(
        at=frozenset(
            {
                ("formats/canonical/display_tag.json", "#/properties/sizes/items"),
                ("formats/canonical/html5.json", "#/properties/sizes/items"),
                ("formats/canonical/image.json", "#/properties/sizes/items"),
                ("formats/canonical/native_in_feed.json", "#/properties/main_image_sizes/items"),
            }
        ),
        outcome=PENDING_A_NAME,
        defect="the bundle states `{width, height}` with `minimum: 1` at four positions in "
        "four formats documents, calls three of them `sizes` and one `main_image_sizes`, "
        "joins the four by no $ref and titles none of them -- so nothing in it tells a "
        "shared subject from a coincidental overlap",
        ask="adcontextprotocol/adcp#8735 (a title at these four positions)",
        note="the catalogue's L2 layer holds ONE key over EIGHT positions here, and the "
        "bundle titles three of the other four differently -- Canonical, Publisher and "
        "Product DOOH Screen Resolution.  So `{width, height}` is at least three subjects "
        "by the bundle's own words, and collapsing these four would be a fourth claim it "
        "does not make.  The entry is outside §3a's PENDING set for the same reason: that "
        "set takes an L2 entry the bundle titles at NO position, and this one it titles at "
        "three, which is 'a decision brought to the owner' rather than a silence",
    ),
    Decided(
        at=frozenset(
            {
                ("core/rights-attestation-evaluation.json", "#/properties/reference"),
                ("core/rights-constraint.json", "#/properties/attestation_refs/items"),
            }
        ),
        outcome=PENDING_A_NAME,
        defect="the bundle states `{allOf: [{$ref: core/attestation-reference.json}, {a "
        "narrowing pinning claim_type, issuer.type and the subject's required set}]}` at two "
        "positions in two documents, BYTE FOR BYTE the same text, calls one of them "
        "`reference` and the other `attestation_refs`, joins the two by no $ref and titles "
        "neither",
        ask="adcontextprotocol/adcp#8735 (a title at these two positions -- BARE: the ask's "
        "own denominator is §3a's L2 and L3 PENDING sets and this position is L2C, a node "
        "that states its object type through its CONJUNCTS, which that pass does not read)",
        note="a property name is the FIELD's role and never the type's name, so two words "
        "over one structure is the bundle's silence and not its verdict",
    ),
    # ----------------------------------------------------------------------- NOT ONE TYPE
    Decided(
        at=frozenset(
            {
                ("core/agent-notification-config.json", "#"),
                (
                    "protocol/sync-agent-notification-configs-request.json",
                    "#/properties/notification_configs/items",
                ),
                (
                    "protocol/sync-principal-request.json",
                    "#/properties/configuration/properties/notification_configs/items",
                ),
            }
        ),
        outcome=NOT_ONE_TYPE,
        defect=_DROPPED_CONJUNCT,
        ask=_NOTIFICATION_ASK,
        payload={
            "subscriber_id": "s",
            "url": "https://x.example/hook",
            "event_types": ["capabilities.changed"],
            "authentication": {"schemes": ["Bearer"]},
        },
        note="core/agent-notification-config.json's root ADMITS this; both referring "
        "documents REFUSE it for `required: authentication.credentials`, and both classes "
        "admit it",
    ),
    Decided(
        at=frozenset(
            {
                ("core/notification-config.json", "#"),
                (
                    "account/sync-accounts-request.json",
                    "#/properties/accounts/items/properties/notification_configs/items",
                ),
            }
        ),
        outcome=NOT_ONE_TYPE,
        defect=_DROPPED_CONJUNCT,
        ask=_NOTIFICATION_ASK,
        payload={
            "subscriber_id": "s",
            "url": "https://x.example/hook",
            "event_types": ["creative.status_changed"],
            "authentication": {"schemes": ["Bearer"]},
        },
        note="the event type is the one THIS pair's documents admit; the agent pair's "
        "payload is refused by both of these for a third reason, which is why one payload "
        "per group and not one for the family",
    ),
    Decided(
        at=frozenset(
            {
                ("core/error.json", "#"),
                (
                    "media-buy/sync-catalogs-response.json",
                    "#/oneOf/1/properties/errors/items",
                ),
            }
        ),
        outcome=NOT_ONE_TYPE,
        defect=_DROPPED_CONJUNCT,
        ask="adcp-client-python-wvod (ours: the same dropped `if` at a FOURTH site, over "
        "`code` rather than over `authentication`)",
        payload={"code": "REFERENCE_NOT_FOUND", "message": "nope"},
        note="core/error.json's root ADMITS this; the referring document REFUSES it for the "
        "`anyOf` its `then` states for REFERENCE_NOT_FOUND, and the class admits it",
    ),
    # ------------------------------------------------------------------------------ SPLIT
    Decided(
        at=frozenset(
            {
                (
                    "collection/base-collection-source.json",
                    "#/oneOf/0/properties/identifiers/items",
                ),
                ("core/collection-distribution.json", "#/properties/identifiers/items"),
            }
        ),
        outcome=SPLIT,
        defect="NONE of the bundle's: `collection/base-collection-source.json` states "
        "`not: {properties: {type: {const: platform_channel_id}}, required: [type]}` at its "
        "position and `core/collection-distribution.json` does not, and the bundle says WHY "
        "in its own enumDescriptions -- 'identity is the tuple (publisher_domain, value), so "
        "this type is only meaningful inside a distribution entry'.  What is ours is that "
        "the `not` does not reach the class",
        ask="none owed upstream: the bundle distinguishes the two subjects itself.  The "
        "class-side half is adcp-client-python-wvod's kind and is why the key groups them",
        payload={"type": "platform_channel_id", "value": "x"},
        note="this is the payload adcp-client-python-s44.1's own comment asked for and "
        "could not produce from the group's shared schema",
    ),
    Decided(
        at=frozenset(
            {
                ("core/placement.json", "#/definitions/ProductDoohScreenResolution"),
                (
                    "core/placement-definition.json",
                    "#/definitions/PublisherDoohScreenResolution",
                ),
            }
        ),
        outcome=SPLIT,
        defect="NONE: the bundle names BOTH subjects, differently, in its own definitions -- "
        "'Product DOOH Screen Resolution' and 'Publisher DOOH Screen Resolution'.  Two named "
        "subjects with identical structure are correctly two types",
        ask="none owed: nothing is missing from the bundle here",
        note="the cleanest case in the whole duplicate question, and the one that shows why "
        "identical structure is a hypothesis: §3a's L2 layer holds these two in ONE key with "
        "six other positions",
    ),
    Decided(
        at=frozenset(
            {
                ("protocol/get-principal-response.json", "#/properties/result/oneOf/3"),
                ("protocol/sync-principal-response.json", "#/properties/result/oneOf/2"),
            }
        ),
        outcome=SPLIT,
        defect="NONE: the bundle titles both branches, differently -- 'Failed principal "
        "read' and 'Failed principal sync'.  A failed READ and a failed SYNC are two "
        "operations the bundle names in its own text",
        ask="none owed: nothing is missing from the bundle here",
        note="`result` is the FIELD's role at both positions and was argued about as a role "
        "word; it never had to be.  The bundle states the two names one segment in",
    ),
)


def at_of(cls: Any) -> POSITION | None:
    """The ``(document, pointer)`` a class names, read off ``__adcp_schema__``.

    The same reading ``test_one_node_is_one_declaration.ref_of`` takes, and it is a
    function here so the TABLE's key and the GATE's key cannot come apart.
    """
    ref = getattr(cls, "__adcp_schema__", None)
    document = getattr(ref, "document", None)
    pointer = getattr(ref, "pointer", None)
    if isinstance(document, str) and isinstance(pointer, str):
        return (document, pointer)
    return None


def key_for(members: list[Any]) -> frozenset[POSITION]:
    """The position set that identifies a group, which is a row's own key."""
    return frozenset(at for member in members if (at := at_of(member)) is not None)


def by_position() -> dict[frozenset[POSITION], Decided]:
    """The table, keyed the way a group is.  A duplicated key here is a table defect."""
    out: dict[frozenset[POSITION], Decided] = {}
    for row in DECIDED:
        assert row.at not in out, f"two rows decide one group: {sorted(row.at)}"
        out[row.at] = row
    return out
