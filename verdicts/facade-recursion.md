# The facade recursion: `adcp-client-python-tlpl`

**The recursion is gone.** 0 `RecursionError` anywhere in a full run of the substituted
tree, where 102 of 177 erroring files were that one cycle.

**The tree does not yet collect 21,668.** It collects 12,039. The recursion was masking a
second cause in the same files, and that cause is one word whose refusal is a standing,
reasoned ruling of this project — not a defect. The measurement of what overturning it
would buy is below; the decision is not taken here.

---

## 1. Which repair — measured, as asked

The bead's question was: how many names are in the same position, a domain word withheld
with only the flat word left? **Measured two ways, the answer is zero.**

```
rows of survey/adapter-surface-9.6.1.tsv whose chosen PUBLIC home is the flat surface:  2
   both of them the SAME declaration, under aliases.GetContentStandardsResponse1
                                         and aliases.GetContentStandardsSuccessResponse

emitted declarations published FLAT with no domain path at all:                         0
```

And the forcing condition has since gone. `f6607f1c1` re-pointed through the flat word
because the positional-name ruling withheld `GetContentStandardsResponseBranch0`. Trunk now
names that declaration **`GetContentStandardsResponseSuccess`** — a word read off the
document, not a position — and `adcp.types.content_standards` publishes it:

```python
>>> adcp.types.GetContentStandardsResponse1
<class 'adcp.types._schemas.content_standards.get_content_standards_response.GetContentStandardsResponseSuccess'>
>>> [a for a in adcp.types.content_standards.__all__
...  if getattr(adcp.types.content_standards, a) is that_class]
['GetContentStandardsResponseSuccess']
```

So **(b) cost nothing and needed no code**: `Join.public` already ranks the flat pair last,
a domain pair now exists, and regenerating `src/adcp/types/aliases.py` picked it up:

```diff
-from adcp.types import GetContentStandardsResponse1 as GetContentStandardsResponse1
-from adcp.types import GetContentStandardsResponse1 as GetContentStandardsSuccessResponse
+from adcp.types.content_standards import GetContentStandardsResponseSuccess as GetContentStandardsResponse1
+from adcp.types.content_standards import GetContentStandardsResponseSuccess as GetContentStandardsSuccessResponse
```

**Both repairs landed, and (a) is the one that matters.** (b) removes the instance; (a)
removes the mechanism, and the mechanism is still live — `survey/adapter_surface.py` still
records the flat surface as a public home, correctly, for a declaration that has no domain
word. The next such declaration would write the flat word again. And the instance was never
the only trigger: `src/adcp/types/projections.py` — upstream's own restored file, byte for
byte — carries `from adcp.types import Account, BusinessEntity, NotificationAuthentication,
NotificationConfig` at module scope, which is the same statement shape reaching the same two
resolvers.

---

## 2. (a) The guard: a set of what is in flight

Two resolvers call each other and neither owns the recursion. This layer's `_resolver` falls
through to the flat surface; the flat surface's own `__getattr__` — the one `install()` wraps
— falls through to the alias modules, which this layer serves. A word neither can answer
alone is passed back and forth:

```
_dropin._resolver.__getattr__  ->  adcp.types.__getattr__
  ->  _dropin._resolver.__getattr__  ->  _from_flat  ->  (the same word again)
```

`_from_flat` is the edge that closes the loop, so the guard is there:

```python
_IN_FLIGHT: set[str] = set()

def _from_flat(attr: str) -> object:
    if attr in _IN_FLIGHT:
        raise AttributeError(attr)
    _IN_FLIGHT.add(attr)
    try:
        return getattr(importlib.import_module(_FLAT), attr)
    finally:
        _IN_FLIGHT.discard(attr)
```

**It is a set of what is in flight, not a bound on depth and not a list of names.** A depth
counter answers "how far have we gone" when the question is "are we asking something we are
already asking". An allowlist would be a record of the one instance met so far. Membership
here means exactly: *a frame below this one is already resolving this word through this
surface*, which is the only condition under which asking again cannot produce a new answer.
On re-entry the frame declines, and the caller falls through to its own next source and then
to `_resolver`'s own informative `AttributeError` — which names the word and points at the
alias surface's row. The guard does not replace that message and swallows nothing. One word
may be resolved through the flat surface any number of times over a run; the set holds only
what is on the stack, and a word leaves it as its frame returns. Imports hold the import
lock, so the surrounding resolution is single-threaded by construction.

---

## 3. A third defect the repair exposed: the writer was reading OUR `src/`, not theirs

With the recursion gone, the same files failed on `ImportError: cannot import name
'UpdateMediaBuySuccessResponse' from 'adcp.types'` — **132 of them.** The recursion had been
masking it.

`survey/adapter_surface.py` exists to answer *what does upstream's kept code ask of our
surface*, and the substituted tree runs **upstream's** `src/adcp/**`. The corpus walked
**our** working tree, so every repair this project has made to one of those files deleted the
demand that file makes. `adcp-client-python-2f52` patched our `decisioning/handler.py` to
name the emitted arm; upstream's line 230 still reads
`from adcp.types import UpdateMediaBuySuccessResponse`, the pair left the census, the alias
layer bound nothing, and `adcp.decisioning` did not import.

Measured: **37 `(module, name)` pairs** upstream's own `src/adcp/**` asks of `adcp.types` at
module scope do not resolve on our surface, and the corpus could see **none** of them.

`_as_upstream_wrote_it` now reads each corpus file as upstream wrote it at the pin, falling
back to ours where their revision has no such file (`adcp/core.py` is ours alone). It is the
same correction `upstream_files` already carries one directory along, for the same reason,
and nothing is written — it is a read of their blob. The 37 pairs are now in the table, bound
where a key reaches them and refused **with a reason** where none does.

---

## 4. The figure, three ways

Upstream's baseline, reproduced on their own tree, same flags:

```
21,668 collected   18,819 passed   2,848 skipped   1 failed
```

The substituted tree, `-p deselect`:

| denominator | collected | **passed** | failed | errored | skipped |
|---|---|---|---|---|---|
| **BEHAVIOUR** | 11,601 | **8,665** | 1,135 | 14 | 1,787 |
| **BEHAVIOUR + PORT** | 11,859 | **8,821** | 1,237 | 14 | 1,787 |
| **everything collected** | 12,039 | **8,821** | 1,237 | 177 | 1,804 |

`DELETE` items surviving collection: **0**. Movement against the previous verdict: 11,681 →
12,039 collected, 8,597 → 8,821 passed, 177 → 163 erroring files, `RecursionError` 102 files
→ **0**.

**A pass-rate over 12,039 is still not comparable to one over 21,668 and is not offered as
one.**

---

## 5. What now blocks the remaining 9,629, and the number that decides it

**132 of the 163 erroring files are ONE word**, and the other causes are small:

```
132  cannot import name 'UpdateMediaBuySuccessResponse' from 'adcp.types'
  3  cannot import name 'MajorVersion'       from _schemas/protocol/get_adcp_capabilities_response.py
  2  No module named 'adcp.types.canonical_creative'   (its subject is withdrawn; expected)
  1  each: is_canonical_format_kind, SyncAccountsAccount, CanonicalFormatKindStr, BadgeRole
```

**Binding that one word takes the tree to 15,286 collected and 39 erroring files.** Measured
by hand-binding it in a scratch tree, not committed anywhere:

```
with UpdateMediaBuySuccessResponse and CreateMediaBuySuccessResponse bound:
    15,286 of 15,332 collected (46 deselected), 39 errors
```

**I did not take that decision, because the refusal is a ruling and not a bug.**
`Join.unpinned`'s own docstring is the standing reading, and it refuses this exact family by
name:

> upstream's `media_buy/create_media_buy_response.json` arm `CreateMediaBuyResponse1` pins
> `status` to `'completed'`, and the subject `document+ordinal` reaches for it — our
> `CreateMediaBuySuccess` — has no `status` element at all. … Publishing their
> `CreateMediaBuySuccessResponse` over that subject would mint a NAME over a type that
> accepts payloads the document refuses, which is worse than leaving the name unbound.

Two things have to be settled together, and both are outside what a measurement decides:

1. **Whose pin is the defect.** `adcp-client-python-0z0u` measured that upstream's
   `status: Literal['completed'] = 'completed'` is an INVENTED default: the document's
   `allOf[1]` requires `status` and its `oneOf[0]` states no value for it, so their class
   admits a payload the document refuses and ours — which requires `status` from the
   enum of nine — is the stricter of the two. If that is right, `unpinned` is refusing
   because *ours does not reproduce their defect*, which is the opposite of the harm it was
   written to prevent.
2. **Whether `denoted` may fall back.** Even with `unpinned` satisfied, the pair's subject is
   chosen from upstream's own statement, which terminates in
   `adcp.types.canonical_creative.UpdateMediaBuyResponse1` — a module this repository
   withdrew. A statement naming a module that does not exist here cannot be followed, and the
   dump still offers the generated arm as a candidate. That fallback is derivable from the
   same committed classification the withdrawal uses (`LIVE-RESTORE` ∧ absent-here), but it
   is a ruling about which reading wins when upstream's statement is unfollowable, and it
   belongs in a bead of its own with 0z0u's measurement beside it.

Either change is one short edit. Both would move the tree from 12,039 to about 15,286
collected, which is 3,247 items and the largest remaining block by far. The number is here so
the ruling can be made with it rather than around it.

The last ~6,400 to 21,668 are the 31 other erroring files and whatever they mask in turn —
the same pattern as this bead, where one cause hid another. Re-measure after the word is
settled rather than estimating now.

---

## 6. Gates

```
./check     emitted 1059 / refused 0, primary 0 / chained 0,
            approximated 383 facts in 148 documents
oom_kill    75 before and after every run
aliases.py  REGENERATED by survey/adapter_surface.py, never hand-edited
guard       a set of in-flight words; no allowlist, no try/except around the recursion,
            no depth counter
upstream's retained tests  byte-identical; deselected, never excised
```

Write scope: `survey/dropin/_dropin.py`, `survey/adapter_surface.py`,
`src/adcp/types/aliases.py` (regenerated), `verdicts/facade-recursion.md`.
`src/adcp/types/_adapter.py` and `survey/adapter-surface-9.6.1.tsv` are the same writer's
output from the same run and move with it. Nothing in `codegen/`, nothing in
`survey/regenerate.py`.
