# salesagent-j3k2l.31 — the prediction, written before the change exists

Base `ac9175209`, worktree `/Users/konst/projects/acp-j3k2l31`, branch
`sdk/j3k2l31-exports`. Every number below names the run it came from.

## The resolution I expect to take

**The first one: the symbols SHOULD be exported.** The emitter's import side already
has a stated rule — `emit.emit`'s binder resolves a fragment reference to
`mod.declared[into]`, "an import of a symbol the target DECLARES" — and the export
side writes `__all__ = [root]` alone. Two sides, two answers about one module's
public surface.

The second resolution is excluded on the plan's own grounds and needs no
measurement to exclude. Its two readings are:

* *reach the alias through its owning module* — that IS the import under
  discussion, so this is not a change;
* *emit the alias where it is used* — a second name for the same node, which P2
  forbids, and 6 of today's 16 violations are an `enum` CLASS
  (`ReportingDeliveryOfferingReportingFeedPurpose`) imported by 6 modules, so
  copying would be 7 classes for one document node. That is the
  flatten-a-`$ref`-into-a-copy defect `test_a_cross_document_reference_is_an_import_and_not_a_copy`
  exists to catch.

## The shape of the fix

`__all__` becomes the root symbol, then the symbols the module declares at the
pointers the bundle NAMES: `mod.named` (from `bundle.named_nodes`) intersected with
`mod.declared`. Both are already on `Module` and both are functions of (bundle,
document), so P7 holds and `render` needs no new argument.

I expect this set to be EXACTLY what a `$ref` can import, by construction rather
than by today's population: `named_nodes` is computed from every `$ref` in the
bundle, and the binder only ever asks for `mod.declared[into]` where `into` came
from a `$ref` fragment — so every symbol the import side can ask for is in the
export set. That is why I do not expect to export every declared symbol: a nested
class the walk declared because a field needed a type was asked for by nothing, is
reached through its parent's annotation, and exporting it would also put a second
name in 228 of the tree's 677 modules.

## The numbers I predict

* **The alias population does not move.** The fix changes what `__all__` holds, not
  what any module imports, so the count stays at what I measured on the base.
* **957, not 910, over the `graded()` population of the 677-module tree.** Measured
  on the base `ac9175209` with the test's own walk: 957 relative-import aliases, of
  which **16** name a symbol the target declares and does not export. The brief and
  the test's pin both say 910/15; those were measured at `0130e5fc9` and the emitted
  population has grown since. I predict `assert checked == 957` passes and that if I
  am wrong the test names the real number.
* **Modules whose `__all__` grows: between 10 and 60**, out of 677. The 7 target
  modules in the violation list are certain
  (`core/reporting_canonicalization_contract`, `reporting_dataset_share_destination`,
  `reporting_delivery_method`, `reporting_resource`, `reporting_delivery_offering`,
  `reporting_coverage`, `reporting_schedule`).
* **`core/product_change_map.py` is NOT among them.** It is the one alias-root module
  (module-level `__adcp_schema__`) that declares a second symbol — the nested enum
  `ProductChangeMapValue` — and `tests/test_emit.py:214`'s `graded()` does
  `(symbol,) = module.__all__`, so a second name there would break `graded()` and
  with it every test in `tests/test_enum.py`. I predict the document has no named
  node and the unpack survives.

## The other tests I predict move

* `tests/test_emit.py::test_the_committed_tree_is_what_a_fresh_run_emits` — red until
  I commit the fresh emit, green after.
* `tests/test_emit.py::_symbol` (line 1790) also unpacks `__all__` as one name, and I
  predict it **reddens** the tests that call it for a document whose module now
  exports more than one name. I cannot fix it: `tests/test_emit.py` is held by
  salesagent-j3k2l.36. The minimal patch is `module.__all__[0]` at that one site,
  which is why the root symbol goes FIRST rather than sorted in with the rest.
* `tests/test_comparison_document_side.py`, `tests/test_comparison_folds.py`,
  `tests/test_import_rule.py`, `tests/test_fragment_ref.py` — no movement. None reads
  `__all__` (`test_fragment_ref.py`'s only match is a comment).
* The **five** failures already in `tests/test_enum.py` on the base — enum class count
  482 vs pin 447, member names 2892 vs 2692, nodes 541 vs 501, sites/documents
  (128, 78, 0) vs (124, 76, 2), and `reached == 1` vs 0 — stay red. They are stale
  population pins, not `__all__`, and the population they count is produced by
  `codegen/lower/*` and `codegen/compiler.py`, which this lane does not hold.
