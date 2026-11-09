# `salesagent-j3k2l.28`, fourth part: the three one-sided folds and the last 2 `missing`

Committed before any of the change below exists, so it can be graded rather than
rationalised. Base `760e898c6` (`emit/from-scratch`).

## The base, re-measured in this worktree, both instruments named

`codegen.emit.emit` over `bundle.portable(schemas/cache/3.2)`:
portable 1054, emitted 691, refused 363 (verdict 297, deferred 65, unresolved 1),
verdicts 297, pending 66, accounted 988.

`codegen.harness.compare_schema` per graded pair (`tests/test_emit.graded` +
`pair_of`): graded pairs 1055, added 0, missing 2, differs 0. Both `missing` are
`additionalProperties/description` — `a2ui/component.json#` at
`/properties/component/additionalProperties/description` and `a2ui/surface.json#` at
`/properties/components/items/properties/component/additionalProperties/description`,
each "the document says 'Component properties'".

Every figure matched the one I was handed.

## The population the three mechanisms refuse, measured at the base

The brief names three DOCUMENTS. The three refusal predicates refuse **twenty**, by
`detail` substring over `emit.emit(...).refusals`:

| mechanism | documents |
|---|---|
| the union fold (`union._refuse_a_shape_the_comparison_cannot_read`) | 9 |
| the local `$ref` (`union._refuse_a_local_reference_branch`) | 8 |
| the conditional (`compiler.conditional_only`) | 3 |

All 20 are `DEFERRED`. Seven of them are CHAINED — refused because a document they
reference is refused — so the three named documents gate the other four plus two
of their own family:

```
UNION_FOLD   creative/creative-feature-result.json          /properties/value
UNION_FOLD   property/property-feature-value.json           /properties/value
UNION_FOLD   compliance/get-creative-features-completion.json        (chained)
UNION_FOLD   creative/get-creative-features-terminal-success.json    (chained)
UNION_FOLD   property/property-feature-result.json                   (chained)
UNION_FOLD   formats/canonical/audio_hosted.json            /properties/duration_ms_range/items
UNION_FOLD   formats/canonical/video_hosted.json            /properties/duration_ms_range/items
UNION_FOLD   media-buy/package-control.json                 /properties/bidding
UNION_FOLD   media-buy/package-update.json                  /properties/bidding
LOCAL_REF    core/bidding-policy-capability.json            /definitions/policy_profile/.../oneOf/0
LOCAL_REF    core/placement-presentation.json               /properties/decorations/items/oneOf/0
LOCAL_REF    core/canonical-media-buy-features.json                  (chained)
LOCAL_REF    core/media-buy-features.json                            (chained)
LOCAL_REF    core/targeting-overlay-requirements.json       /properties/geo_regions/anyOf/0
LOCAL_REF    core/targeting-overlay-support.json            /definitions/countrySupport/anyOf/0
LOCAL_REF    governance/get-plan-audit-logs-response.json    /properties/plans/.../error
LOCAL_REF    governance/reported-outcome-error.json         /definitions/bounded_value/anyOf/0
CONDITIONAL  sponsored-intelligence/si-ui-element.json      /
CONDITIONAL  sponsored-intelligence/si-initiate-session-response.json (chained)
CONDITIONAL  sponsored-intelligence/si-send-message-response.json     (chained)
```

**So my brief's predicted delta is wrong before I start, in the direction of being
too small.** It predicts "emitted rises by 2 to 4 ... pending falls by 3 to 6". The
input population is 20 documents, not 3.

## What I predict, and why, per mechanism

### 1 The union fold is STALE, in BOTH its arms

The refusal's stated reason is that `harness._normalize` "folds exactly that shape
off the model's side". That is a claim about a harness that `.32` and `.33` changed.
Read at this base, `_normalize` is called on both sides — `compare_schema` normalizes
the DOCUMENT first with `declared_null=True` and then the model against it — and
`_UNION_KEYWORDS` is `("anyOf", "oneOf")`, so the document's own `oneOf` is read by
the same fold. Each branch is read through `_uncanonicalized` one level down, which
is precisely the "one level down inside the branch it folded" the refusal says is
owed.

* the **bare-type arm**: the document's `{"oneOf": [{"type": "boolean"},
  {"type": "number"}, {"type": "string"}]}` folds to
  `{"type": ["boolean", "number", "string"]}` and the model's `anyOf` of the same
  three folds to the same node. The `oneOf`-specific `integer`/`number` overlap
  guard does not fire — `integer` is not among the three.
* the **null arm**: at `formats/canonical/{audio,video}_hosted.json`'s
  `/properties/duration_ms_range/items` the document's
  `[{"type": "integer", "minimum": 0}, {"type": "null"}]` folds with
  `declared_null=True` to `{"type": ["integer", "null"], "minimum": 0}`; the model
  side then reads `declared_null=_declares_null(doc)` off that, gets `True`, and
  folds identically.

PREDICTED: the predicate is deleted, not narrowed. All 9 emit and grade green.

### 2 The local `$ref` is STALE

`_normalize` resolves a `$ref` against `root`, and `root` is per-side: `compare_schema`
takes `document` and `pair_of` supplies `schema_at(SchemaRef(g.ref.document, "#"))`,
which is the whole resolved document a `#/definitions/x` is relative to. The 43
`added` facts the refusal was measured at therefore have no site left.

PREDICTED: the predicate is deleted. All 8 emit and grade green.

### 3 The conditional is GENUINELY OPEN, and section 6 decides it the same way

`compiler.conditional_only` refuses because `Rules.properties` makes the class
declare a field for a key only a conditional names, while `_composed` folds a
conjunct's UNCONDITIONAL facts and a bare `if`/`then` conjunct states none. So the
field is `added`.

Section 6's exit says a fold applies to both sides "including one level down, inside
a branch it folded". `_composed` folds the `allOf`; one level down inside the branch
it folded, `/allOf/7/then/properties/apps` is the document's own DECLARATION of that
property. So the document side declares it too, and the two halves agree.

The fold is a DECLARATION and not a requirement: a conditional's `required` stays
conditional and is not unioned into the node's `required`, because draft-07 applies
it only when the `if` holds. And the two sides must read the declaration by the SAME
rule — `rules.conditional_properties` already takes annotations-only where two
branches declare one key differently, and a harness reading that took the first
branch's facts instead would report `missing` at every such key.

PREDICTED: all 3 emit and grade green. `added` stays 0 — this is the one change of the
three that ADDS a document-side fact, so it is the one that could move `missing`
instead if the two readings disagree.

### 4 The last 2 `missing`: the cause is not `description`

`compiler.Decided` carries `type`, `constraints` and `format` and **no annotation**.
`containers._inner` REFUSES a constraint or a format it cannot carry inside a
container, by name, and an annotation on the same node is dropped silently with no
refusal at all. `a2ui/component.json`'s `/properties/component/additionalProperties`
is `{"type": "object", "description": "Component properties"}`; the value lowers to
`dict[str, Any]` and the description has no slot to ride in.

Section 6 decides which side changes: "A `description` is NEVER folded ... Where the
comparison reports one, the emitter is wrong and the emitter is what changes." So the
emitter carries the annotation on the inner type. `description` is not special-cased;
what is closed is the missing annotation slot, and `description` is the only
annotation in `harness.FACTS` that reaches it in this bundle.

PREDICTED: missing 2 → 0, added stays 0.

## The numbers

| | base | predicted |
|---|---|---|
| portable | 1054 | 1054 |
| emitted | 691 | 705–711 |
| verdicts | 297 | 297 |
| pending | 66 | 46–52 |
| accounted | 988 | 1002–1008 |
| graded pairs | 1055 | > 1055, re-measured not predicted |
| added | 0 | 0 |
| missing | 2 | 0 |
| differs | 0 | 0 |

`emitted` and `verdicts` are separate numbers and are not added: I predict `verdicts`
does **not** move at all, because nothing here mints a verdict — every document above
is `DEFERRED` and clearing a deferral is an EMISSION or it is nothing. The range on
`emitted` is 14–20 because some of the 20 may refuse on a second keyword once the
first refusal is lifted; the floor assumes 6 do.

## The risks I am naming before running

1. **A new document emits a node the comparison reads differently.** Every one of the
   20 is currently ungraded, so each brings pairs the comparison has never run on.
   `added` rising is the signal; the fold that fires at that node is the cause.
2. **The conditional fold could over-declare.** A conditional's `if` is walked by
   `conditional_properties` as well as its `then`/`else`, so the document-side reading
   has to walk the same three keywords or the two disagree at a key only an `if`
   tests on.
3. **An inner annotation slot could change the 1055 existing pairs.** Any node inside
   a container that states a `description` renders one where it did not before. If a
   document does NOT state it at that pointer the new fact is `added`; I predict no
   such site, because the annotation is read off the document's own node.
