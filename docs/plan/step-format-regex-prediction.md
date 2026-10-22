# Prediction: `format` selects a type, and the regex engine is derived per class

Written and committed BEFORE any measurement of the change. Graded at the bottom of this
file after.

Branch `emit/format-regex`, base `81e132aee`. Worktree `/Users/konst/projects/acp-trunk`.

## The baseline this is stated against

Measured at `81e132aee` with `env -u VIRTUAL_ENV uv run --no-sync python -m pytest
tests/test_emit.py -q`: **68 passed in 51.21 s**. Python 3.14.6, pydantic 2.13.5,
jsonschema 4.26.0, datamodel-code-generator 0.86.0.

Denominators, all derived from `schemas/cache/3.2` and none written by hand:

| quantity | value | how selected |
|---|---|---|
| bundle, portable | 1,054 documents | `bundle.portable` — every document published under its own identity (`bundled/`, `mcp/` and the three registry files excluded) |
| named population | 334 | 85 `is_leaf_object` ∪ 249 `references_a_property` |
| **N, emitted** | **43** | `emit.emit(BUNDLE, population()).emitted` — 38 named, 5 reached through a `$ref` |
| refused | 331 | the complement, each by name, pointer and keyword |
| graded pairs | 44 | 43 roots (one per emitted document) + 1 nested class |

The three checks at the baseline: 42 pairs `pass`, 2 `no_constraint_to_step`
(`error-details/audience-too-small.json#`, `error-details/budget-too-low.json#`, both
documents `steps()` finds no keyword in), refuses-check denominator 3,758 instances,
schema comparison 486 document facts compared, 57 model-only facts examined, 0 of them a
narrowing.

Population facts the change is aimed at, measured off the bundle at the baseline:

* **14 format sites** in the 43 emitted documents: `date-time` 7, `uri` 5, `date` 2.
  13 of 14 carry no constraint beside the format; the one that does is
  `core/platform-extension-ref.json#/properties/uri`, which carries a `pattern`.
* **11 distinct patterns at 19 sites.** One distinct pattern uses look-around
  (`^P(?!$)(\d+Y)?...`), at 2 sites, both in `core/sla-window.json`.
* **5 scalar roots** (D2 aliases). 2 carry a `pattern` (`core/brand-id.json`,
  `core/property-id.json`, both `^[a-z0-9_]+$`); **0 carry look-around**.

## What I am changing

1. `rfc3339-validator` and `rfc3987` become dependencies, and both halves that validate a
   document pass the document's own draft's `FORMAT_CHECKER`: `_refuse` in
   `src/adcp/types/_base.py` (the schema half of `strict_validate` and of `strict_alias`)
   and `conforms` / `violated_keywords` / `check_refuses` in `codegen/harness.py`.
2. `format` selects a type where a checker asserts it: `date-time` → `pydantic.AwareDatetime`,
   `date` → `datetime.date`. A format with no checker available selects nothing and stays an
   annotation, so the dependency is load-bearing rather than decorative.
3. `uri` keeps an annotated `str` carrying the format. Reasoning in full in the report; in
   short, `AnyUrl` renders a `minLength: 1` its document does not state, which the symmetric
   comparison reports as an added fact, and D5 admits a standard type only when it states the
   document's own facts.
4. `AdCPBaseModel.model_config` drops `regex_engine="python-re"` and keeps `extra="ignore"`.
   The compiler's model layer already derives the engine per class from that class's own
   fields' patterns; the suite grades that derivation against one computed independently from
   each document's own nodes.

## Predictions

Each is a number or a named outcome, so each can be wrong.

**P1 — N does not move. 43 emitted, 331 refused, over 334 named out of 1,054 portable.**
Nothing in this change adds or removes a refusal: `format` is not a keyword the walk refuses
on (it is already in `decide_type`'s handled set) and no refusal reason is touched.

**P2 — the refusal histogram is byte-identical.** All 331 rows keep their keyword, pointer
and detail.

**P3 — 44 pairs, 42 `pass`, 2 `no_constraint_to_step`, and the two are the same two
documents.**

**P4 — the schema comparison's three totals are unchanged: 486 compared, 57 model-only
facts, 0 added.** `compared` counts facts the DOCUMENT states and so cannot move. The
format-derived types state exactly `{"type": "string", "format": "..."}`, which is what the
document states and what `json_schema_extra` stated before, so neither `model_facts` nor
`added` moves. **If `added` is non-zero the change is wrong**, and `AnyUrl` is the reason I
expect it to be: `AnyUrl` would put `minLength` there.

**P5 — the refuses-check denominator stays 3,758, and if it moves it moves UP, never
down.** Up is possible and legitimate: an instance the control previously excused because
the document asserted nothing for its `format` now violates `format` and is graded. Down
would mean an instance stopped reaching the model, which nothing here does. I expect
unchanged, because no steppable keyword sits at a `date-time` or `date` site (13 of 14
format sites carry no constraint, and the one that does carries `pattern` at a `uri` site,
whose step pops `format`, so those instances were already graded on `pattern`).

**P6 — exactly 1 of 43 emitted modules carries `regex_engine="python-re"`, and it is
`core/sla_window.py`.** 42 take pydantic's default Rust engine. The 10 non-look-around
distinct patterns all compile under Rust.

**P7 — the two engines agree on the accepted set for all 10 patterns Rust compiles**, over a
corpus containing both matches and non-matches, and the eleventh **refuses to build** under
Rust rather than mis-matching. That second half is the whole reason the default engine is
the one to want, so it is asserted rather than quoted.

**P8 — a `date-time` payload with no offset is refused by the SCHEMA half**, with
`errors()[0]["type"] == "format"`, on a real emitted class, and the same payload is admitted
by the same document when no checker is passed. The type agrees: `AwareDatetime` refuses it
too. Before this change the document admitted it and only the constructor would have
refused — which is the state the previous lane correctly backed the types out of.

**P9 — the accepts check stays green at all 14 format sites.** `hypothesis_jsonschema`
honours a format it knows when generating, so the instances it draws for `date-time`, `date`
and `uri` conform to the format and the new assertion refuses none of them.
`rep.missing_formats` stays `[]` for all 44 pairs.

**P10 — 5 modules import `AwareDatetime` and 1 imports `datetime`**, from the 7 `date-time`
sites and 2 `date` sites: `core/agent_signing_key.py`, `core/datetime_range.py`,
`core/limited_series.py`, `core/material_deadline.py`, `core/placement_evidence.py` and
`core/date_range.py` respectively. 5 `uri` sites keep `json_schema_extra={'format': 'uri'}`.

## Risks I expect to have to report

**R1 — the `uri` strategy.** If `hypothesis_jsonschema`'s `uri` strategy emits a string
`rfc3987` refuses, P9 fails at a `uri` site and the accepts check reports
`model_refused_valid` on a value the generator believed valid. I predict it does not.

**R2 — RFC 3339 admits values pydantic refuses.** A leap second (`23:59:60`) is a valid
RFC 3339 `date-time` and I expect `AwareDatetime` to refuse it. If the generator never draws
one, every check stays green and the narrowing is real but ungraded — a ceiling to name, not
a pass. I will probe it directly rather than let the generator decide whether it exists.

**R3 — an alias with look-around has no config slot.** `render_alias` emits a module-level
`Annotated`, and `strict_alias` builds a `TypeAdapter` at import, so a scalar root carrying a
look-around pattern would fail to import once the base stops forcing `python-re`. 0 of this
population's 5 aliases carry one, so this is a ceiling for the step whose population reaches
one, and it fails loudly (ImportError at the gate) rather than silently.

**R4 — the brief's format census does not reproduce.** The brief states 6,626 format uses
(uri 3,955, date-time 2,089, date 203, email 326, hostname 37, uuid 14, uri-template 2). I
measure 806 over the 1,054 portable documents and 16,293 over all 1,625 `.json` files in the
bundle directory. I expect to report this as a contradiction rather than adopt either number.

## Grade

Filled in after the measurement, in the same file, with each prediction marked and the
measured value beside it.
