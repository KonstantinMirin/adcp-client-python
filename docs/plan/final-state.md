# The final state

**NINE READINGS. Each is a statement about the finished artifact, and each names what decides it.**

This file holds the target and nothing else. It carries no measurement, no progress, no row — those
go stale on the next merge, and a stale number in a rule document gets believed. **Current status
lives in `bd`.** Ask `bd` what holds today; ask this what holding means.

## What belongs here

**A READING IS OBSERVABLE IN THE ARTIFACT.** A consumer who has only the installed wheel and the
bundle can check it. A property of `codegen/` that no consumer can observe is not a reading and
must not be gated: there are unboundedly many wrong internal structures, enumerating a few proves
nothing, and gating them freezes the structure against the refactor the gate was meant to
encourage.

**A READING HOLDS OR IT DOES NOT.** Never M of N. A fraction is a statement about the instrument,
not about the artifact.

**A READING NAMES WHAT DECIDES IT**, and that must be something that fails when the reading fails.
A check that passes when nothing happens decides nothing.

**A ROW THAT MOVES NO READING IS NOT BRIEFED.**

---

## 1. Every class states exactly what its document states

Every class accepts every value its document admits, refuses every value its document refuses, and
what it dumps validates against that document again.

This is the deliverable's correctness and the definition of "the schemas produced classes".
Emission is not this: a document emits when the walk produces a class for it, which says nothing
about what the class states.

**Decided by** the draw, over every pair of a class and the document and pointer it names. The
verdict is per pair and names the value. A pair the instrument cannot grade is not a pair that
passes: a budget cut is reported as a cut, and no pair passes by leaving the check unexecuted.

## 2. Every exception to reading 1 is a declared widening, proved by a value

A model may be wider than its document and never tighter. Each widening is declared at its own
pointer in the emitted module, the declared set equals the set a run mints in both directions, and
**every declaration holds a value that demonstrates it**. A declaration with no value behind it is
an allowlist wearing a measurement.

**Decided by** the set equality in both directions, and by the store of proving values containing
one for each declaration — where an entry recording a budget cut is not a value.

## 3. Every union root dispatches

A payload offered to a union base resolves to its branch, for every payload the document admits.
The dispatch key is one that **determines** the branch, which requires the document to guarantee
its presence in every instance it admits — pinning a key is not determining it.

**Decided by** constructing every union base's dispatch over the whole tree and requiring that none
raises, plus: no union dispatches on a key its document lets an instance omit.

## 4. Each distinct vocabulary is one type

A set of values stated at more than one position is written once and referenced, never restated.
The named type is constructed from that one value list, and the entry lives in the narrowest
namespace containing every position that references it.

Two positions stating the same values are not automatically the same concept: where they are
judged distinct they keep separate types over the one value list, and where the only candidate name
comes from a description they get none — a description states what a thing IS, not what it is
CALLED.

**Decided by** the catalogue's own gate: no value list appears twice in the emitted tree.

## 5. The record states each distinct subtree once

A document of record stores each distinct subtree once and references it at every occurrence. **The
pointers readers spell do not change** — the storage is a DAG, the pointer language is not, because
the corpus key hashes the pointer and a respelling discards every held value.

**Decided by** the record's own size: no record exceeds its source document by more than the
references it resolves.

## 6. Every class is importable at exactly one path

`from adcp.types.<domain> import <Name>` reaches every class the tree declares — roots, union
branches and aliases alike — at exactly one such path, with the domain derived from the document's
own path. No second way reaches the same class, and no name in one namespace means two classes.

**Decided by** resolving every export and requiring exactly one path each, and requiring the object
reached to be the same object as the private path's.

## 7. The package declares its types to a consumer's type checker

`py.typed` ships, so every annotation the compiler derives — constraint, branch type, enum member —
is visible at the boundary it was built for. It ships with its errors declared rather than waiting
for zero.

**Decided by** running a type checker over a consumer module importing from `adcp.types.<domain>`
in an environment that has only the installed wheel, and requiring a wrong assignment to be an
error.

## 8. The wheel is the artifact

The wheel builds, installs into an environment that has never seen this repository, and every
exported name imports from it.

Until this holds, no claim about what ships is verified — including readings 6 and 7, which are
otherwise measured against the source tree, and packaging decides which files a wheel contains.

**Decided by** building, installing clean, and importing every exported name.

## 9. Every approximated fact is attributed

Each declared fact is ours with a decision recorded, or upstream with an issue that exists. An
unfiled gap is ours. And every narrowing taken deliberately is admitted by an enumerated registry
compared by equality against the narrowings the run actually takes — admitted by nothing else,
because a predicate waiver is invisible and permanent.

**Decided by** every `upstream` attribution naming a live issue, and by that registry's equality in
both directions.

---

## How to change this file

Change a reading when the **target** changes, not when progress is made against it. If a sentence
here would read differently next week because something landed, it is status and belongs in `bd`.

To add a reading, state the fact about the artifact and name what decides it. If nothing decides it
yet, say so and name what would — a reading whose check is imagined is a wish, and this file holds
the target.
