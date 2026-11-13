# The rule layer's reading of a `None`, and the 3 regressions it caused

The route split gave the TYPE layer and the SERIALISER one reading of a Python `None` at
a property whose document does not admit `null` — absence. `supplied()` gave the RULE
layer another: it built its key set from `__pydantic_fields_set__` without looking at the
value, so a `None` counted as a key the payload supplied.

## The readers, censused

Ten rule kinds read a key set. Every one of them is handed it from `supplied()`, so the
change is in one reader and not in ten rules:

| rule kind | how it reads presence |
|---|---|
| `ConditionalRequired`, `Dependencies`, `NegatedConditional` | `name in keys`, twice each |
| `ForbiddenGroups`, `RequiredGroups`, `Match`, `UniqueItems` | `name in keys`, once each |
| `Presence` | `name in keys`, twice |
| `PresenceGroups` | delegates to `Presence` |
| `PropertyCount` | `len(keys)` |

Three call sites, and all three draw from `supplied()`:
`RuleBound._enforce_adcp_rules` (`_runtime.py:951`) for a model, `_members`
(`_runtime.py:141`) for a nested value, and `BranchDispatchMixin._presence_tag`
(`_base.py:2343`) for the branch a presence union dispatches to. **One reader changed.**

Both directions, measured over the derived population (every field a bound rule names):

* 1,842 rule-named fields carry the marker — a `None` now reads **absent** at all of
  them, 0 still present;
* 195 rule-named fields whose document admits `null` — a `None` still reads **present**
  at all of them, 0 dropped. The test is the MARKER and never `value is None`:
  `codegen.ir.admits_null` is the one reader that decides which, and the two cases are
  the same Python object.

## What moved, attributed per commit

The drop-in at `/srv/ws/dropin-presence2` spans two commits of this lane, so the headline
`+52` is not one change's. Isolated by reverting `supplied()` in the drop-in tree and
re-running the six files that moved:

| commit | fixed | regressed |
|---|---|---|
| `18242501f` — `is_no_explicit_null` over both marker spellings | 41, all in `tests/test_no_explicit_null.py` | 0 |
| `cd95e2969` — `supplied()` | 14 | **3** |

## THE 3 REGRESSIONS, and why they are upstream contradicting itself

All three are in `tests/test_product_format_declaration.py`, all three are the same
mechanism, and all three assert the pre-split reading at the rule layer:

```
test_every_root_rule_rejects_with_its_schema_keyword[changes4]  {"tracker_execution_contract": None}
test_every_root_rule_rejects_with_its_schema_keyword[changes5]  {"format_shape": None}
test_explicit_presence_is_distinguished_from_an_unset_default   {"tracker_execution_contract": None}
```

They fail with `DID NOT RAISE`. The rules that stopped firing are
`ConditionalRequired(when=Match(key='tracker_execution_contract', present=True),
require=('format_option_id',))` — `core/product-format-declaration.json#/allOf/0` — and
`NegatedConditional` for `#/allOf/2/else`, which forbids `format_shape` at a non-custom
kind.

**The document asks for absence and absence is what it now gets.**
`format_shape`'s own description: *"REQUIRED when `format_kind: "custom"`; otherwise MUST
be absent."* The payload is a Python call passing `format_shape=None`; the marker reads
that as absence; the model's dump carries no `format_shape`; and that dump is admitted by
the document. Before the change the model REFUSED a payload whose own serialisation it
accepts — one class answering two ways about one value.

`test_every_root_rule_rejects_with_its_schema_keyword`'s method is where the two readings
meet: it takes the oracle from `validator.iter_errors(payload)` — a **JSON-Schema**
validator reading the dict as a document, where `None` is `null` and the key is present —
and requires `model_validate(payload)` — the **Python** route, where `None` is absence —
to agree with it. That is the same defect already reported in `codegen/harness.py`:
grading the Python route with a JSON oracle.

**And upstream's own suite states the opposite contract twice over.**
`tests/test_no_explicit_null.py`'s module docstring:

> The rule is about the wire: a JSON document carrying `null` is refused […] A Python
> `None` — keyword construction, `model_validate` on a dict — stays the SDK's spelling of
> "not supplied".

`tests/test_rc3_media_buy_runtime.py::test_a_meaningless_explicit_null_is_still_dropped`
(fixed by this change) is the sharper one, because it is the same situation with the
opposite expectation: `canceled=None` passed explicitly, `"canceled" in
model_fields_set` asserted, and `"canceled" not in wire` required. A key that is not on
the wire cannot be present to a rule that reads the wire — so that test's contract
implies `test_explicit_presence_is_distinguished_from_an_unset_default`'s is wrong, and
its comment (*"an explicitly supplied null does [fire]"*) is the pre-split sentence.

## A SEPARATE FINDING, uncovered while measuring and NOT caused by this change

**At a branch dispatcher the JSON route is downgraded to the Python route, so the null
arm is unstruck behind it.** `BranchDispatchMixin._dispatch` (`_base.py:2462`) calls
`cls._branch_adapter().validate_python(value)` unconditionally, and the hook that reaches
it is `core_schema.no_info_wrap_validator_function` (`_base.py:2360`) — so the route is
not merely discarded, it is not even visible to the dispatcher.

Measured:

```
ProductFormatDeclaration.model_validate_json('{"format_kind":"image","params":{},"format_shape":null}')
    -> ADMITTED, format_shape in fields_set
ImageFormatDeclaration.model_validate_json(same)          # the arm it dispatches to
    -> REFUSED  string_type @ ('format_shape',)
```

The arm is right and the dispatcher loses it. Population: **762 branch dispatchers**
carrying 52,218 marked fields on their arms; of the 13 whose arms a payload could be
built for without filling a required field, **11 admit a JSON `null` at a marked arm
field and 2 refuse**. Reading 1 therefore does not hold on the JSON route behind any
dispatcher.

This is not reachable by patching `_dispatch`'s call: pydantic-core's `validate_python`
takes no route, so the honest shape is to generate the branch union as a nested schema
under the wrap validator and dispatch through the `handler` the hook is already given —
which preserves the entry route because it is the same validator instance. That is a
change to the dispatch mechanism (`adcp-client-python-j0fr`'s) and to what `_no_branch`
reports, so it is reported here rather than started.
