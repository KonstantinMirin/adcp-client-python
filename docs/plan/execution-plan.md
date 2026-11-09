# The execution plan

The tracker holds these rows as `salesagent-3xz6e.1` through `.15`, in this order. Where the
tracker is unreachable, this file is the order and the exit conditions, and status is reported in
the session rather than written to a row.

Two documents are the authority. `docs/plan/rebuild-plan.md` decides the SEMANTICS: what each
keyword compiles to at each position, what is admitted, what refuses, how the output is graded.
`docs/plan/architecture.md` decides the STRUCTURE: the layers, the one dispatch, what crosses each
seam, and the paradigm. Every row below cites the section that decides it.

## Phase 1 -- the structure, which is the generic harness

Eight rows, in order. `architecture.md` section 14 states each one and whether it changes what the
run reports. A keyword is "done" in three independent places today; this phase makes it one.

    1  codegen/__main__.py                  arch 10,14   bytes-identical
    2  codegen/keywords.py + two readers    arch 3,5     report-changing
    3  bundle.record, our own inliner       arch 4       report-changing, loud
    4  codegen/ir.py and render.py          arch 7,8     bytes-identical
    5  codegen/schema/ with positions       arch 4,6     bytes-identical
    6  refusal as a value                   arch 2,3     report-changing
    7  lower/names.py, naming and dedup     arch 3,6     bytes-identical
    8  the cells                            arch 3       report-changing

What each one buys:

1. **`__main__`** -- the walk stops being `__main__`, so a lowering can import it. Dissolves the
   import-permission rule, the callables carried on `Module`, and the reason `compiler.py` holds
   the composition reader.
2. **`keywords.py`** -- the declaration: every keyword, every position, what it compiles to and
   whether the model renders it as a fact. The keyword screen and the verifier's compared set
   become its first two readers. Sections 5 to 7's grids are GENERATED from it.
3. **`bundle.record`** -- our own inliner, so the document of record is the bundle's document with
   references pasted and nothing else changed. Deletes the verifier's five folds and re-saves every
   packaged `.json`. Loud by design: a comparison failure stops being fold-excused.
4. **`ir.py` + `render.py`** -- the declarations become an intermediate representation with no text
   in it, and one module knows pydantic.
5. **`schema/`** -- node kinds and one parser that assigns POSITION when it builds the node.
   Position stops being recovered by parsing pointer strings, and the container/union node rewrite
   has no reason to exist.
6. **Refusal as a value** -- `Refusal` stops subclassing `Exception`; its kind is derived from the
   table cell, never chosen at a raise site. This is what re-mints the refusals the reviews found
   counted as permanent.
7. **`lower/names.py`** -- naming and content dedup as one pass over the finished module, which is
   where dedup can finally have a stated scope.
8. **The cells** -- each keyword the reviews found unwritten becomes one handler change against a
   cell that already exists, graded by the comparison without anyone wiring it.

## Phase 2 -- the keyword waves

Ordered by coverage, least-varied schemas first. One row per WAVE, because a wave is a set that
lands together: measured over the bundle, `then` and `else` each complete 0 documents alone, and
`if` beside them completes 185. Three rows yield nothing; one row yields 185.

    wave  keywords added                                                       total  schemas
      1   type enum pattern $ref allOf anyOf additionalProperties minLength       8     260
      2   properties required const format maximum minimum maxLength oneOf
          discriminator enumMetadata                                             18     487
      3   items minItems uniqueItems not contains if then propertyNames
          minProperties maxProperties                                            28     882
      4   dependencies exclusiveMinimum patternProperties                        31     919
      5   exclusiveMaximum maxItems                                              33    1002
      6   else                                                                   34    1046
      7   errorMessage                                                           35    1047

Seven registry documents are refused by section 7 and are not in the 1047. Re-measure every figure
before taking a wave: they are one bundle version's property.

## After the waves

    dedup across documents, the public surface, the version derivation
    one sweep: the retired citations and the banned vocabulary, together, last
    re-pin the interpreter and the constants

## What this replaces

Seventy-one rows, one per keyword, in no deliberate order, against a module with no position
carrier and three copies of the keyword decisions. Every row paid to re-derive its position, and
the verifier could not tell a row it had implemented nothing: three keywords the semantics document
says are rendered compiled to nothing and no check saw it.

Fifteen rows replace it. The ordering is not a preference: phase 1 exists because a wave's exit
condition is unmeasurable while "done" has three definitions.
