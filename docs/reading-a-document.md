# Reading a document

Rules for answering "what does the schema actually say here", each one written because getting
it wrong cost something measurable. `CLAUDE.md` points here rather than carrying these.

Every rule is a thing to *ask the document*, with the command that asks it. None of them is a
judgement call.

---

## 1. REQUIREDNESS IS A CONJUNCTION. Never read an arm in isolation.

A property's requiredness is the conjunction of its own node and **every ancestor that applies
to the same instance** — an `allOf` branch, or a `oneOf` arm inside a parent that itself states
`required`. draft-07 applies all of them to the instance at that pointer.

**Measured cost, twice in one session.** `creative/preview-creative-response.json`:

```
#/oneOf/1/properties/results/items
   required:   ['success', 'creative_id']          <- the PARENT requires it
   oneOf/0   "PreviewBatchResultSuccess"   required: ['response']   success: const true
   oneOf/1   "PreviewBatchResultError"     required: ['errors']     success: const false
```

Reading each arm's own `required` produced "two branches whose pinned discriminator is
optional" — a finding that does not exist. `success` is required by the parent; the arms pin it
and simply do not restate it. The same error, one level up, is why `status` looked optional on
task responses: it comes from `core/protocol-envelope.json` through an `allOf`.

**So ask through the production screen, which resolves it for you:**

```python
from adcp.types._base import _refuse_at, SchemaRef
_refuse_at(SchemaRef(document='creative/preview-creative-response.json',
                     pointer='#/oneOf/1/properties/results/items'),
           payload, 'X', module=TheClass.__module__)
```

That is the same reading `strict_validate` gives, so its answer is the SDK's answer. A hand
reading of one node is not.

---

## 2. A PINNED value is the document's. A multi-member enum default is INVENTED.

`const`, or an `enum`/`Literal` of length exactly **1**, states the value: a default equal to it
decides nothing. An `enum` of several members does not, and a default there picks one — which
is `adcp-client-python-0z0u`, 867 pairs over 624 classes.

The two live in one bundle under one property name, which is why the rule is read off the NODE
and never off the name:

```
media-buy/sync-reporting-receipts-response.json#/properties/status   const: "completed"   -> pinned
protocol/.../get-products-response.json         status: TaskStatus, 7 members              -> invented
```

Measured: 22,252 required-and-pinned property positions; 277 of them discriminators, all 277
required. See `verdicts/a-pinned-default-is-the-documents-own.md`.

---

## 3. A DISCRIMINATOR'S TAG IS EXTRACTED BEFORE DEFAULTS APPLY.

So a default cannot rescue an absent discriminator under a field-name discriminator:

```
success: Literal[True] = True            {"response": "x"} -> Unable to extract tag using discriminator 'success'
success: Literal[True] | None = None     with a CALLABLE discriminator -> dispatches, and the dump omits the None
```

If a document ever pins a discriminator and does not require it (none do today), the dispatch
must be the **callable** one the project already uses for `_BRANCH_PRESENCE`, falling back to the
arms' distinct required-key sets. And never `Optional[Literal[...]]` under a field-name
discriminator: pydantic refuses to build the adapter and takes every class of that union with it
(`adcp-client-python-82m.23`).

---

## 4. `deprecated` IS METADATA, NOT ABSENCE.

A document stating `format_ids` with `deprecated: true` **states** it. A class that suppressed it
would be narrower than its document. Seven documents state one of these as deprecated-but-present.

A corollary for the alias layer: upstream's `LegacyProduct` (60 fields) and `Product` (59) differ
by exactly such a property, and our single 60-field class carrying both is correct.

---

## 5. A PYTHON `None` IS ABSENCE. A JSON `null` IS A VALUE.

`model_validate` on a dict and keyword construction read `None` as absence;
`model_validate_json` refuses an explicit null; `ADCP_STRICT_VALIDATION` refuses both;
`strict_validate` — the document's screen — refuses either way. The serializer drops it.

**And the rule layer must agree with the type layer.** `supplied()`, which the conditional rules
ask "is this key present", counting a `None` as present is how a class came to refuse a payload
its own dump would be valid for (`core/wholesale-feed-webhook.json#/allOf/0/else/not`).

---

## 6. A REFUSAL'S REASON IS THE DOCUMENT'S OWN KEYWORD.

A test regex-matching a hand-written sentence the document does not contain is testing an SDK's
prose. 29 of upstream's failures are that, e.g. `'exact revision requests forbid aggregate
selectors'`, a phrase absent from the document that refuses the payload.

---

## 7. UPSTREAM EMITS PER POSITION; WE EMIT PER SUBJECT. N:1 IS THE DESIGN.

"Two of their words resolve to one object of ours" is not a defect — a subject reached from ten
positions carries ten of their names and one of ours. What separates design from defect is the
**field set**:

| upstream's field sets | reading |
|---|---|
| identical | one subject, several positions — correct |
| nested (≥75% shared) | ours carries the document's fuller statement — correct |
| disjoint | two subjects answered by one object — a defect |

`python -m survey collapse --wheel <their site-packages> --module adcp.types` does this reading.
Current: 20 / 7 / 10.

---

## 8. OUR OWN DUMP MUST BE DOCUMENT-VALID, AND NOTHING ASKS THAT YET.

`accepts`/`refuses` grade a constructed witness, and a witness is built to *satisfy* the
document, so it never carries a conditional's forbidden combination. The round-trip property
`dump(validate(x)) == x` holds even when the dump **adds** a key the document then refuses —
which is how three failures survived every gate (`adcp-client-python-11f1`).

---

## 9. AN APPROXIMATION RECORD IS NOT IMPLIED BY A LOSSY LOWERING.

`patternProperties`: 250 nodes state it, 147 typed in portable documents, and **6** are recorded
as approximated. The other 141 are lowered to `dict[str, Any]` with no record — an *undeclared*
widening, invisible to `./check`, which is the one screen meant to see every one. So never infer
"it will show up in `approximated`"; read the record:

```python
getattr(cls, '__adcp_approximations__', ())   # keyword, document, pointer, kind
```

---

## 10. BOTH PACKAGES ARE NAMED `adcp`. STATE THE ENVIRONMENT.

Upstream's wheel and our tree both import as `adcp`, and `PYTHONPATH=.:src` is inherited by
subprocesses — so upstream's own interpreter imports **ours** and a comparison silently compares
the tree to itself. Run theirs as `env -u PYTHONPATH /tmp/upwheel/bin/python`, and in code pass
an `env` with `PYTHONPATH` removed.

---

## 11. COMPARE RUNS ON ONE LINE OF WORK, AND OVER ONE POPULATION.

A regression is a test that **ran and passed** before. A newly collected failure has not
regressed; neither has one that was skipped. And two runs built from divergent trees attribute
one lane's change the difference between two. `python -m survey causes <out> --since <out>`
enforces both and names what it cannot attribute; `python -m survey reconcile` is the accounting
and refuses to print if it does not close.
