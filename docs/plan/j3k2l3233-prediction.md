PREDICTION, written before the change exists (2026-10-23).
Worktree /Users/konst/projects/acp-j3k2l3233, branch sdk/j3k2l3233-comparison,
base 9e9da67e1.  Graded afterwards, naming every prediction that was wrong.

THE EXPOSURE, measured first, because it decides what the change can move.
Instrument: walk every document node of every graded pair (schema_at(g.ref)),
count the three shapes the new readings fire at.

  graded pairs walked                    1034
  document nodes visited                 46147
  nodes holding a document-side local $ref   0
  nodes holding _normalize's UNWRAP arm      0   (1 null + 1 live branch)
  nodes holding _normalize's RESTORE arm     0   (<=1 null, >1 live, all bare)

Independently: over all 1054 portable documents of the RAW bundle there are 405
local-$ref sites in 45 documents, and the only keys ever beside one are
`description` (58) and `deprecated` (4) -- 0 sites carry a constraint keyword
beside a local $ref.  Pointer shapes: `#/definitions/<name>` 301,
`#/$defs/<name>` 101, and 3 six-part pointers
(`brand/get-brand-identity-response.json` -> `#/oneOf/0/properties/fonts/definitions/font_role`),
which is why the reading walks the pointer rather than taking the last segment.

P1. INSTRUMENT A -- compare_schema over T.graded(), max_steps=0, guards still in
place (they are in codegen/lower/union.py, which I do not own).

  baseline  pairs=1034 added=0 missing=11 differs=43
  predicted pairs=1034 added=0 missing=11 differs=43   -- NO CHANGE, all four

  Confidence HIGH, and it rests on the exposure above rather than on the fix:
  0 of 46147 nodes hold a shape either reading fires at, so the change is a
  no-op over the population.  THE COROLLARY IS THE UNCOMFORTABLE HALF: the real
  population grades nothing about this change, so the probes in P3 are its whole
  grading, and a reading that passes P1 and fails P3 is worthless.

P2. INSTRUMENT B -- the 11 documents .26's two guards refuse, emitted into a
temporary tree with the guards disabled AT RUNTIME (monkeypatched, so no file I
do not own is edited), then graded by compare_schema with the fix.

  .32's 4 documents (core/bidding-policy-capability.json,
  core/placement-presentation.json, core/canonical-media-buy-features.json,
  core/media-buy-features.json):      43 added  ->  0 added
  .33's 7 documents:                   9 added  ->  0 added
                                       (5 bare-type arm + 4 null arm)

  AND ONE THING I PREDICT DOES NOT CLEAR.  The const-vs-one-member-enum symptom
  at creative/get-creative-features-terminal-success.json (3 missing + 3 added)
  is compiler.name_the_node's RENDERING, not a comparison reading, so I predict
  it survives: with both guards off, added = 3 and not 0, and missing rises by 3.
  .33's own note already calls it a separate rendering question.  If added comes
  back 0 there, my reading resolved more than it should have and P3 is where that
  shows.

  .33's note says both guards off gives "added 51 over 9 pairs"; 43+5+4+3 = 55,
  so that figure and this decomposition disagree by 4.  I do not reconcile it
  from the note -- I measure it, and report both numbers with their instruments.

  I predict NOTHING about the emitted COUNT (697): the emitter is not my file and
  I am not re-measuring it.

P3. INSTRUMENT C -- the probes that must still REPORT.  A reading that resolves
the document until it matches whatever the model says drives added to 0 for a
broken tree too, and P1 cannot see that.  For each new reading:

  .32  document {"$ref": "#/definitions/x"} whose target states a fact the model
       OMITS            -> predicted `missing` names it
  .32  ... whose target states a fact the model CONTRADICTS
                        -> predicted `differs` names it
  .32  ... whose target states a fact the model does not carry at all and the
       model adds one of its own
                        -> predicted `added` names it
  .32  an UNRESOLVABLE local $ref (no such target)
                        -> predicted the node is left alone, so the model's facts
                           read as `added` and the pair reddens (fail safe)
  .33  the same three, one level down inside the folded combinator branch
  .33  a model that DROPS the document's branch-declared null
                        -> predicted `differs` at /type, NOT green
  .33  a document anyOf the fold must NOT touch (two live branches, one carrying
       more than a type word)
                        -> predicted left alone, compared as it is

  And one ceiling I predict I will STATE rather than code, because its measured
  population is 0 of 405: a CONSTRAINT keyword beside a local $ref is ignored by
  draft-07, and letting the sibling win would let the document excuse a model
  narrowing.  `description` winning is not optional -- the compiler transcribes
  the sibling, and 58 of 405 sites carry one.

P4. THE GATE -- 27 passed on trunk; predicted 27 + (my new cases), 0 failed.

P5. SHAPE OF THE CHANGE.  One function does both tickets: _normalize, called on
the DOCUMENT's node as well as the model's, with the $ref resolution turned into
a JSON-pointer walk against a root supplied per side.  I predict I need to widen
two signatures -- Pair gains an optional `document`, compare_schema a keyword --
and one line in tests/test_emit.py's pair_of to supply the document root, because
a nested pair's schema is a sub-node and a local $ref is relative to the document
ROOT.  If that turns out to need a file I do not own, I stop and write it up.

# ========================================================================= #
# THE GRADING, 2026-10-23, on sdk/j3k2l3233-comparison.  Every prediction
# named, the wrong ones first.
# ========================================================================= #

WRONG, 1 of 5, and it is P5's last clause.

P5 said the change would be `_normalize` called on both sides with a pointer
walk, Pair gaining a `document`, compare_schema gaining a keyword, and one line
in `pair_of`.  All of that is right.  What it MISSED is that the reading, built
exactly as predicted, fired on the 2 documents that STATE the bare-type union
and on NONE of the 3 that reference one -- because the resolver writes a finite
type out as its members while inlining, so the same union is
`{"type": "boolean"}` in one document and `{"enum": [false, true]}` in another.
Instrument B caught it: added came back 6, not the predicted 3.  The fix is the
THIRD canonicalization (`_uncanonicalized`) applied to the BRANCH rather than a
fourth rule, and `added` then fell to 3.  **A reading half-done is the same
defect it was built to close**, and the prediction had no line for it because I
read the two stating documents and not the three referencing ones.

P3 also understated the work, in the direction it was right about.  It listed
the probes that must still report and predicted I would STATE the
constraint-sibling ceiling rather than code it -- both correct.  What it did not
predict is that reading the document's union would make a pair comparable in
the OTHER direction for the first time and that the pre-existing unwrap was
wrong there: a model declaring `v: bool | float | str | None` at a property its
document REQUIRES and types `[boolean, number, string]` compared byte-identical
to the faithful `v: bool | float | str`, both `pass`.  So the change would have
BOUGHT `added == 0` at the cost of a new green cell for a widened model at 3
measured bundle positions -- the trap the brief names, in its narrowest form.
Closed with `null_is_absence`, read off the `required` axis `compare` already
carries.  Found by my own probe failing, which is the only reason it is in this
file rather than in the next lane's.

RIGHT, 4 of 5.

P1 -- a no-op over the real population, all four figures.
     baseline  pairs=1034 added=0 missing=11 differs=43
     after     pairs=1034 added=0 missing=11 differs=43
     and the per-ROW sets are identical, not merely the counts.  The exposure
     measurement is why: 0 of 46147 document nodes across the 1034 graded pairs
     hold a shape either reading fires at.  The corollary P1 stated also held --
     the population graded nothing about this change, and both defects above
     were found by constructed probes and by Instrument B.

P2 -- the unlocked documents.  All 11 emit; emitted 697 with both guards off,
     690 with localref off, 693 with fold off, each matching .26 exactly.
     Graded on the SAME emitted tree, one variable:
       base comparison   23 pairs  added=55  missing=3  differs=4
       with the readings 23 pairs  added=3   missing=3  differs=4
     and the predicted decomposition of 55 was right to the row: 43 for the
     local `$ref` (12 at core/bidding-policy-capability.json, 31 at
     core/placement-presentation.json), 5 for the bare-type arm, 4 for the
     null arm, 3 for the const-vs-enum rendering.

P2's SECOND HALF -- the const-vs-one-member-enum symptom does NOT clear, and
     added lands at 3 rather than 0.  Predicted, and it is now
     `salesagent-j3k2l.35`.  P2 also predicted the note's own figure of 51
     would not reconcile and refused to adopt it: measured 55, which is the
     note's 51 plus 4.

P4 -- the gate.  27 passed before, 27 + 25 of this lane's own cases after,
     0 failed.

ONE PRE-EXISTING FAILURE, outside the gate and not this change's:
     tests/test_applied_schema.py:351 asserts `len(out.emitted) == 674` and
     the tree emits 686.  `salesagent-j3k2l.29` owns that constant as item 8
     of its own list (it re-measured it 425 -> 580 on an earlier tree), the
     test imports nothing this lane changed, and 686 is the figure .26's
     delivery note quotes.  Left alone, with the measurement recorded on .29.
