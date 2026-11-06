"""Derive the alias surface: every upstream TYPE spelling, and the object of ours it names.

`survey/migration_notes.py` answers this question over the CONSUMER corpus -- the 503
names upstream's own examples and docs spell -- and its `ALIAS LAYER` bucket is the one it
deliberately leaves to this script (`OWED` names it: "those names are the alias layer's
business ... a guide entry for them would be a second answer to one question").  This
script ranges over upstream's WHOLE public surface instead, because an application imports
what it likes and not only what upstream's README shows.

**NO ALIAS IS WRITTEN ON A KEY NOTHING CORROBORATES**, which is `final-state.md` reading
10's rule -- "an alias is keyed on a schema subject, never on a name" -- read together with
the measurement that refutes its naive form.  **Identity equality ALONE is not a subject**:
run as the sole key it bound `Brand` to our `GetAdCPCapabilitiesResponse` and
`AdcpVersionEnvelope` to our `VerifyBrandClaimRequest`, because a one-field model's wire
alias set is shared by every other model with that one field.  That is
`migration_notes.nearest`'s own warning -- "many upstream names landing on one class of
ours is a hypothesis, not a verdict" -- arriving at exact equality rather than at overlap.

So a candidate is proposed by a WORD or by a DOCUMENT and then has to survive the subject:

* **the word**, in two forms -- our name spelled identically, or spelled with an acronym
  re-cased (`AdcpVersionEnvelope`/`AdCPVersionEnvelope`, `CssAsset`/`CSSAsset`).  Both
  sides derive a name from the bundle's own title, which is why the word is evidence here
  and is not in general;
* **the document**, where upstream's defining module is named for a bundle document ours
  also carries (`migration_notes.document_of`), or where upstream's name slugs to a
  document's own path (`Channels` -> `enums/channels.json` -> our `MediaChannel`).  This is
  the key that answers a union ROOT, whose field set is `{"root"}` and says nothing;
* and then **the subject decides whether the candidate stands**: where both sides carry an
  identity, they must be EQUAL or the row is `MEANING-DIFFERS` and no alias is written --
  `TaskStatus` is a word two unrelated subjects carry.  Where upstream carries no identity
  to compare, the row records `corroborated=none` and says so.

**AND AN IDENTITY MATCH WITH NO WORD AND NO DOCUMENT IS NOT AN ALIAS EITHER.**  Measured
against 9.6.1: 1,212 of upstream's deliberate names reach an identity of ours under a word
the bundle never gives -- `MacroDeclaration16`, `Payload6`, `AuthorizedAgents41`, and 1,026
of them a bare digit suffix.  Those are their generator disambiguating a collision rather
than a subject the schema names, they already carry the cross-check's `V1-FOLD-NONODE` and
`V2-DUP` verdicts, and binding them here would publish upstream's generator noise as our
surface.  They are counted and named in `--report`, under `ABSENT-SUBJECT-NO-WORD`.

**THE TARGET IS A NAME AT ONE DECLARED MODULE, NEVER A SPELLING** (reading 10).  Upstream
exposes one name at up to nine modules and 1,194 of its 1,446 public modules declare no
`__all__`, so its spellings outnumber its names several times over; reproducing them would
put one object at nine export paths and break reading 6 outright.  So every alias this
script writes lives at ONE module, named by `--module`, and the group a name belongs to is
reported with the module it resolves at:

    PRESENT    the upstream spelling ALREADY resolves against our wheel, at the same
               module path and the same name.  Its declared module is its own, and this
               script writes no alias for it -- an alias would be a second export path
               for a name that needs none.
    RELOCATED  the name is ours, at a different module.  Declared module: `--module`.
    RENAMED    a name of ours holds the same subject under a different word.  Declared
               module: `--module`.
    ABSENT     no subject of ours.  `survey/migration_notes.py` and
               `docs/migration-from-upstream.md` own these; this script only counts them.
    NOT-A-TYPE upstream's object is a module, a function or a constant.  Only a type gets
               an alias; the guide is where a caller is told what to call instead.

    UNRESOLVABLE-UPSTREAM
               the spelling raises on upstream's OWN wheel.  Reading 10: "a name that
               raises on upstream's own wheel is not a name we owe".

**WHAT A TARGET DISAPPEARING MEANS, because the surface shrinks and this will recur.**  When
`sdk/home2` took the surface from 1,881 names to 1,879 it removed
`DAASTTrackerConstraintsDaastTarget`, which one row aliased.  The verdict is neither "a gap
in our surface" nor "patch the row": measured, our tree still DECLARES that subject three
times -- `_schemas.core.daast_tracker_constraints.DaastTarget` and two siblings, the enum
whose value list is `{companion, linear}` -- and declares it under upstream's own word.  What
`home2` removed was a public EXPORT of one spelling, not the declaration, so no fact the
schema states was lost.  That makes the name `V1-FOLD-UNEXPORTED`: "we declare the class,
reading 6 does not export inner shapes, and the answer is an EXPORT or a NAME, never a split"
(`adcp-client-python-2m5`).  The alias layer cannot reach a private name, so the row leaves
it -- and if a caller needs the word, the repair is reading 6 exporting it, not a compat
binding to a name no public module carries.

The second removed name, `PublisherPlacementReference`, was the target of NO row before or
after -- measured, not assumed -- so its removal costs this layer nothing.

**AND A REMOVED TARGET IS NOW IMPOSSIBLE TO COMMIT**: `prove_the_targets` imports every
target before anything is written and refuses on a miss, so the failure arrives at
GENERATION time naming the row rather than at import time as an `ImportError` that takes the
whole reading-8 gate down with it.
**AN ALIAS IS A NAME AND NEVER A SECOND TYPE.**  The module this writes contains nothing
but `from ... import X as Y` statements, one `__all__` and one `__adcp_flat_only__` mapping,
so the object a consumer reaches through it IS the object the walk emitted: `isinstance`
holds across every spelling and `compat.X is domain.X`.
`tests/test_the_alias_layer_is_names.py` grades that on behaviour, and
`tests/test_the_wheel_is_the_artifact.py` grades it from the installed wheel.

**AND THE FLAT SURFACE IS 79 NAMES LARGER THAN `__all__`** (reading 10, amended 2026-11-06).
`__all__` is what THIS module declares; `__adcp_flat_only__` names the `PRESENT` rows, which
owe the flat spelling and owe no path here.  `adcp.types.__getattr__` is the one reader of
both, so the flat namespace carries PRESENT + RELOCATED + RENAMED and this module carries
RELOCATED + RENAMED.

THREE PHASES, because the two trees cannot be imported into one interpreter -- installing
both wheels interleaves `adcp/` at file granularity and `pip check` calls the wreckage
compatible (`.adcp-cache/readings/dropin-crosscheck.md` measured it):

    # phase 1, on an interpreter carrying OURS -- the wheel, not the source tree
    uv build --wheel --out-dir $T/dist
    uv venv $T/ours && uv pip install --python $T/ours/bin/python $T/dist/*.whl
    $T/ours/bin/python survey/alias_surface.py --dump-ours $T/ours.json

    # phase 2, on an interpreter carrying UPSTREAM -- never the shared `.venv`
    uv venv $T/up && uv pip install --python $T/up/bin/python adcp==9.6.1
    $T/up/bin/python survey/alias_surface.py --dump-upstream $T/up.json

    # phase 3, the join, the counts, the module and the table.  ON THE PROJECT'S OWN
    # INTERPRETER, because `prove_the_targets` imports every target before writing
    # anything -- the join itself is standard-library only, but a table nobody proved is
    # the defect that cost six gates, so being unable to import ours is a refusal here.
    PYTHONPATH=.:src ./.venv/bin/python survey/alias_surface.py \
        --ours $T/ours.json --upstream $T/up.json --deliberate-only \
        --module adcp.types.compat --write src/adcp/types/compat.py \
        --table survey/alias-surface-9.6.1.tsv --report $T/report.json

    # phase 4, the DENOMINATOR: the flat spellings consumer code actually writes, with the
    # verdict each one carries.  Reading 10 (amended 2026-11-06) grades the drop-in clause
    # over this and not over the table, because "a table can be complete against itself and
    # leave the written import failing".  Standard library only; the corpus is upstream's
    # own checkout and the OUTPUT is what the gate reads.
    ./.venv/bin/python survey/consumer_imports.py \
        --flat-table survey/consumer-flat-spellings-9.2.0.tsv \
        --corpus /path/to/upstream/checkout --corpus-version 9.2.0 \
        --verdicts $T/report.json --upstream $T/up.json

**WHICH UPSTREAM VERSION A FIGURE IS AGAINST IS RECORDED IN THE DUMP** and printed with
every count, because the project has already carried a figure read off 9.2.0 beside one
read off 9.6.1 (`adcp-client-python-2m5`'s own correction).  `--dump-upstream` writes
`importlib.metadata.version("adcp")` and phase 3 refuses to report without it.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def _public_modules(root_name: str) -> list[str]:
    """Every module of `root_name` reachable at a path with no underscore-prefixed segment.

    The public-name rule's first half, and it is the half that is about the PATH:
    `adcp.types._generated.media_buy` is not a public module however many names it binds.
    """
    import importlib
    import pkgutil

    root = importlib.import_module(root_name)
    out = [root_name]
    for found in pkgutil.walk_packages(root.__path__, root_name + "."):
        if any(seg.startswith("_") for seg in found.name.split(".")[1:]):
            continue
        out.append(found.name)
    return sorted(out)


def _public_names(mod) -> tuple[list[str], bool]:
    """The names a module exposes, and whether it DECLARED them.

    The public-name rule's second half: "either the module declares `__all__` and the name
    is in it, or the module declares none and the name does not start with `_`".  The flag
    is reading 10's `deliberate`: a name reachable only because a module forgot to declare
    what it exports "is not a name an application was invited to import, and treating it as
    one makes upstream's omission our obligation".
    """
    declared = getattr(mod, "__all__", None)
    if declared is not None:
        return [n for n in declared if isinstance(n, str)], True
    return [n for n in vars(mod) if not n.startswith("_")], False


# --------------------------------------------------------------------------- phase 1


def dump_ours(out_path: Path) -> None:
    """Our surface, by subject and by name -- `migration_notes.dump_ours` and not a copy.

    That function already writes identity -> rows and name -> rows with each row's public
    path and document, which is exactly what the join below needs.  A second dumper here
    would be a second place the identity rule lives, and the rule is the thing that must
    not fork.
    """
    import migration_notes

    migration_notes.dump_ours(out_path)
    blob = json.loads(out_path.read_text())
    blob["version"] = _version("adcp_emit")
    out_path.write_text(json.dumps(blob, indent=1))


def _version(dist: str) -> str:
    import importlib.metadata as md

    try:
        return md.version(dist)
    except Exception:
        return "unknown"


# --------------------------------------------------------------------------- phase 2


def dump_upstream(out_path: Path) -> None:
    """Upstream's whole public surface: one row per NAME, with every module exposing it.

    Keyed on the name and not on `(module, name)`, because reading 10's target is a name:
    the 8,927 deliberate spellings of 5,299 names are the same 5,299 subjects reached more
    than one way, and a row per spelling would make the count of work a count of upstream's
    indiscipline.  Every module a name is reachable at is kept on the row, because that set
    is what decides PRESENT.
    """
    import importlib

    import consumer_imports as ci
    import migration_notes

    index = ci.build_index()
    rows: dict[str, dict] = {}
    unreadable: dict[str, str] = {}
    for mod_name in _public_modules("adcp"):
        try:
            mod = importlib.import_module(mod_name)
        except BaseException as exc:  # noqa: BLE001 -- the payload is the report
            unreadable[mod_name] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
            continue
        names, declared = _public_names(mod)
        for name in names:
            row = rows.setdefault(
                name,
                {"name": name, "modules": [], "declared_at": [], "deliberate": False},
            )
            if declared:
                row["deliberate"] = True
            try:
                obj = getattr(mod, name)
            except BaseException as exc:  # noqa: BLE001 -- upstream's __getattr__ raises
                row.setdefault("raises", {})[mod_name] = (
                    f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
                )
                continue
            if mod_name not in row["modules"]:
                row["modules"].append(mod_name)
            if declared and mod_name not in row["declared_at"]:
                row["declared_at"].append(mod_name)
            if "kind" in row:
                continue
            row["kind"] = type(obj).__name__
            row["defining"] = ci.defining_module(mod_name, name, index) or mod_name
            ident = migration_notes.identity(obj)
            if ident is not None:
                row["identity_kind"] = ident[0]
                row["identity"] = sorted(ident[1])
    out_path.write_text(
        json.dumps(
            {
                "version": _version("adcp"),
                "tree": importlib.import_module("adcp").__file__,
                "unreadable_modules": unreadable,
                "names": rows,
            },
            indent=1,
        )
    )
    print(
        f"adcp {_version('adcp')}: {len(rows)} public names over "
        f"{sum(len(r['modules']) for r in rows.values())} spellings; "
        f"deliberate: {sum(1 for r in rows.values() if r['deliberate'])} names over "
        f"{sum(len(r['declared_at']) for r in rows.values())} spellings; "
        f"{len(unreadable)} modules did not import -> {out_path}"
    )


# --------------------------------------------------------------------------- phase 3


def _ours_views(blob: dict) -> tuple[dict[str, list[dict]], dict[str, list[dict]], dict[str, list[dict]]]:
    """Our surface as the three views the join keys on: identity, document, name.

    **PUBLIC PATHS ONLY**, and the filter is every underscore-prefixed segment past
    `adcp.types` -- `migration_notes.main`'s own measured reason: with `_schemas` alone,
    `AdCPBaseModel` read as a name we carry at `adcp.types._base`, which reading 6 makes
    private, and an alias to it would name a module this package does not offer.
    """

    def public(rows: list[dict]) -> list[dict]:
        out: list[dict] = []
        for row in sorted(rows, key=lambda r: (r.get("document") is None, r["path"])):
            if any(seg.startswith("_") for seg in row["path"].split(".")[2:]):
                continue
            if not any(k["path"] == row["path"] for k in out):
                # **THE WORD IS THE ONE AT THE PATH, NOT THE DUMP'S KEY**, and the two part
                # company for exactly the objects this layer is most likely to get wrong.
                # `migration_notes.dump_ours` records `path = exported[id(obj)]` -- the FIRST
                # public spelling that object was seen at -- while the row sits under the key
                # it was found by, so for an interned `Annotated`, `Literal` or enum the two
                # are different words for one object.  Keyed on the dump's key, 13 rows read
                # as RELOCATED ("the name is ours, at another module") while naming a target
                # spelled otherwise, and three of them were plainly not that name's subject
                # at all: `IanaTimezones` and `Supported` both onto our
                # `TargetingOverlayRequirementsRequired`, `RefreshCadence` onto
                # `LookbackWindow`.  What is ours there is the OBJECT, by interning, and not
                # the word -- so the word key reads the path's own tail, which is the only
                # spelling `from <module> import <word>` can actually resolve.
                out.append({**row, "name": row["path"].rsplit(".", 1)[1]})
        return out

    by_name: dict[str, list[dict]] = collections.defaultdict(list)
    for rows in blob["names"].values():
        for row in public(rows):
            if not any(k["path"] == row["path"] for k in by_name[row["name"]]):
                by_name[row["name"]].append(row)
    by_name = dict(by_name)
    by_identity = {k: p for k, rows in blob["identities"].items() if (p := public(rows))}
    # **THE DOCUMENT VIEW IS ITS ROOT AND NOT EVERY CLASS THE DOCUMENT STATES.**  A
    # document compiles to a root plus its inner shapes, and `pointer == "#"` is the root:
    # keyed on the document alone, `brand.json` would offer a reader of this view thirty
    # classes and the first one alphabetically, which is not the subject the document names.
    by_document: dict[str, list[dict]] = collections.defaultdict(list)
    for rows in blob["names"].values():
        for row in public(rows):
            if row.get("document") and row.get("pointer") == "#":
                by_document[row["document"]].append(row)
    return by_identity, dict(by_document), by_name


def norm(word: str) -> str:
    """A name with its casing and separators removed -- the ACRONYM-insensitive form.

    `AdcpVersionEnvelope`, `AdCPVersionEnvelope` and `ADCP_VERSION_ENVELOPE` all answer
    `adcpversionenvelope`.  This is the whole of what the re-casing key compares, and it is
    deliberately not a similarity measure: two names either are the same word under a
    different convention about acronyms, or they are two words.
    """
    return re.sub(r"[^a-z0-9]", "", word.lower())


def class_name(title: str) -> str:
    """`lower/names.py`'s `class_name`, which is §4's rule and the one the bundle is read
    with: pascal-case that KEEPS an acronym, so only a word's first letter is touched.

    Restated here and not imported because phase 3 must run on an interpreter that has only
    the standard library -- `codegen.bundle` imports `adcp.types._base`, which imports
    `jsonschema` -- and the rule is four lines.  `tests/test_the_alias_layer_is_names.py`
    asserts the two agree, so the copy cannot drift in silence.
    """
    words, cur = [], ""
    for ch in title:
        if ch.isalnum():
            cur += ch
        elif cur:
            words.append(cur)
            cur = ""
    if cur:
        words.append(cur)
    return "".join(w[:1].upper() + w[1:] for w in words)


def bundle_index(bundle: Path) -> dict[str, dict]:
    """The bundle's own words: every document PATH slug and every `title` it states.

    Read with `json` over the directory rather than through `codegen.bundle`, for the
    reason :func:`class_name` gives -- and what is wanted here is the bundle's vocabulary,
    which is a reading no compile is needed for.

    `stems` answers "which document does this word name" -- `Channels` ->
    `enums/channels.json`, whose root ours calls `MediaChannel`.  `titles` answers the
    weaker question "is this word one the schema uses at all", which is what separates a
    subject from `MacroDeclaration16`.
    """
    stems: dict[str, str] = {}
    titles: set[str] = set()
    documents: list[str] = []
    for path in sorted(bundle.rglob("*.json")):
        relative = str(path.relative_to(bundle))
        documents.append(relative)
        stem = relative[: -len(".json")].rsplit("/", 1)[-1]
        stems.setdefault(norm(class_name(stem)), relative)
        try:
            doc = json.loads(path.read_text())
        except ValueError:
            continue
        # **THE ROOT'S OWN TITLE IS A DOCUMENT WORD; AN INNER NODE'S IS NOT.**  This is the
        # second half of the gate above and it was measured too: keyed on any title the
        # document states, `BudgetCappingTimezoneBasis` -- an inner enum of
        # `protocol/get-adcp-capabilities-response.json` -- resolved to our
        # `GetAdCPCapabilitiesResponse`, the document's ROOT, which is not that subject at
        # all.  Those names are the cross-check's `V1-FOLD-UNEXPORTED` set: we DECLARE the
        # class and reading 6 does not export it, so the answer is an export or a name
        # (`adcp-client-python-2m5`'s own words) and never an alias onto something else.
        if isinstance(doc, dict) and isinstance(doc.get("title"), str):
            stems.setdefault(norm(class_name(doc["title"])), relative)
        stack = [doc]
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if isinstance(node.get("title"), str):
                    titles.add(norm(class_name(node["title"])))
                stack += [v for v in node.values() if isinstance(v, (dict, list))]
            elif isinstance(node, list):
                stack += [v for v in node if isinstance(v, (dict, list))]
    return {"stems": stems, "titles": titles, "documents": documents}


def _subject_agrees(row: dict, hit: dict, by_identity: dict, by_document: dict) -> str:
    """Whether the SUBJECT backs a candidate proposed by a word: the row's `corroborated`.

    Three answers and each is reported as itself:

    * `identity` -- both sides carry one and they are equal.  The strongest the two trees
      can offer, because upstream's objects carry no schema reference at all (0 of 24,134
      public rows, measured by `survey/upstream_provenance.py`).
    * `document` -- upstream's defining module is named for the document the candidate of
      ours was compiled from.
    * `none` -- upstream's object carries no identity and its module names no document, so
      nothing about the subject was available to check.  A union root is the common case:
      its field set is `{"root"}`.

    `""` is the REFUSAL: both sides carry an identity and they differ, which is
    `MEANING-DIFFERS` and not an alias.
    """
    import migration_notes

    if "identity" in row:
        key = migration_notes.ident_key(row["identity_kind"], row["identity"])
        if any(h["path"] == hit["path"] for h in by_identity.get(key, [])):
            return "identity"
    document = migration_notes.document_of(row.get("defining") or "", set(by_document))
    if document and any(h["path"] == hit["path"] for h in by_document.get(document, [])):
        return "document"
    if "identity" in row:
        return ""
    return "none"


def verdict(row: dict, views: tuple[dict, dict, dict], index: dict) -> dict:
    """One verdict for one upstream name, with the key and the corroboration on the row."""
    import migration_notes

    by_identity, by_document, by_name = views
    name = row["name"]
    if "kind" not in row:
        return {
            "bucket": "UNRESOLVABLE-UPSTREAM",
            "why": next(iter(row.get("raises", {}).values()), "reachable at no module"),
        }
    # **ONLY A TYPE GETS AN ALIAS, and the two failures this stops were both measured.**
    # `norm` drops separators as well as case, which is what makes `ADCP_MAJOR_VERSION` and
    # `AdcpMajorVersion` one word -- and it also made upstream's `media_buy`, a MODULE, the
    # re-casing of our `MediaBuy` class, so the layer bound a class to a module's name.  The
    # other is a function: upstream's 10 callables in this population would have been bound
    # to a class of ours wearing their word.  Both belong to `migration_notes`'s `NOT A
    # TYPE` bucket and `docs/migration-from-upstream.md`, which is where a caller is told
    # what to call instead.
    if row["kind"] == "module" or row["kind"] in migration_notes.NONTYPE_KINDS:
        return {
            "bucket": "NOT-A-TYPE",
            "why": f"upstream's object is a {row['kind']}, and only a type gets an alias",
        }

    # ---- a candidate, proposed by a word or by a document, in order of strength.
    hits, by = [], None
    if name in by_name:
        hits, by = by_name[name], "word"
    if not hits:
        cased = [n for n in by_name if n != name and norm(n) == norm(name)]
        if cased:
            hits, by = by_name[min(cased)], "word-recased"
    # **A DOCUMENT KEY NEEDS THE NAME TO BE A WORD THE BUNDLE GIVES, and that gate is the
    # difference between 143 renames and 2,029.**  Upstream's generated module for a
    # document binds its root, its inner shapes and its generator's disambiguations alike,
    # so without this the document key proposed our `AcceptProposalResponse` as the rename
    # of `AcceptProposalResponse1` through `AcceptProposalResponse7` -- seven aliases onto
    # one class, on the evidence that upstream filed them in one module.  A rename is a
    # DIFFERENT WORD FOR THE SAME SUBJECT, so the word has to be one the schema uses.
    if not hits:
        stem = index["stems"].get(norm(name))
        if stem and stem in by_document:
            hits, by = by_document[stem], "document"
    if not hits:
        if "identity" in row and migration_notes.ident_key(
            row["identity_kind"], row["identity"]
        ) in by_identity:
            return {
                "bucket": "ABSENT-SUBJECT-NO-WORD",
                # SHORT, because 1,212 rows carry it and this file is committed.  The
                # sentence it stands for is this module's docstring: their generator
                # disambiguating a collision rather than a subject the schema names, which
                # is the cross-check's V1-FOLD-NONODE / V2-DUP verdict.
                "why": "identity equal under a word the bundle does not give",
                "in_bundle_vocabulary": norm(name) in index["titles"],
            }
        return {"bucket": "ABSENT", "why": "no word, document or identity of ours"}

    # ---- the subject decides whether it stands.
    same = [h for h in hits if h["name"] == name]
    target = (same or hits)[0]
    agrees = _subject_agrees(row, target, by_identity, by_document)
    if not agrees:
        return {
            "bucket": "MEANING-DIFFERS",
            "by": by,
            "candidate": target["path"],
            "why": "we carry the word; the identities are not equal, so it is another subject",
        }
    got = {
        "by": by,
        "corroborated": agrees,
        "target": target["path"],
        "document": target.get("document"),
    }
    if same:
        resolved = [h["path"] for h in same if h["path"].rsplit(".", 1)[0] in row["modules"]]
        if resolved:
            return {
                **got,
                "bucket": "PRESENT",
                "target": resolved[0],
                "why": f"resolves at {resolved[0]} against our wheel already",
            }
        return {
            **got,
            "bucket": "RELOCATED",
            "why": f"upstream spells it at {', '.join(row['modules'][:3])}",
        }
    return {**got, "bucket": "RENAMED", "why": f"ours is {target['name']}"}


MODULE_HEADER = '''"""Every upstream TYPE spelling, bound to the object of ours it names.

**GENERATED by `survey/alias_surface.py` -- do not edit.**  Regenerate with the three
commands in that file's docstring.  The input it cannot re-derive is upstream's own wheel,
so this module is committed as the artifact of a run that had it, and the run records which
version: see `--report` and `docs/plan/final-state.md` reading 10.

**AN ALIAS IS A NAME AND NEVER A SECOND TYPE.**  Every statement below is a re-export, so
the object reached here IS the object the walk emitted from the document: `isinstance`
holds across both spellings and `compat.X is <domain>.X`.  Nothing here declares a class,
and reading 6's count of declarations does not move -- this module adds names, not
declarations.

**ONE MODULE AND NOT A MIRROR OF UPSTREAM'S PATHS** (reading 10).  Upstream exposes one
name at up to nine modules; reproducing that would put one object at nine export paths and
break reading 6.  So every spelling that does not already resolve resolves HERE, and a
caller porting an application changes one import line rather than every one.

A name upstream spells that ALREADY resolves against our wheel -- same module, same word --
is not bound here: it needs no alias AT THIS MODULE and a second path for it would be the
duplication this layer exists not to reintroduce.  **It still owes the FLAT spelling**, and
`__adcp_flat_only__` below is where those 79 names are declared with the module that already
carries them -- reading 10, amended 2026-11-06: "'already resolves' is measured at the
SPELLING A CONSUMER WRITES, never at the module that declares it ... a name counted present
because its domain path matches owes a flat alias exactly as a relocated one does."

Names with no subject of ours are not here either, and they are not forgotten: they carry a
verdict in `survey/migration_notes.py`'s partition and an entry in
`docs/migration-from-upstream.md`.
"""

from __future__ import annotations

'''

FLAT_ONLY_HEADER = '''
#: **THE FLAT SPELLINGS THIS MODULE DOES NOT DECLARE**: upstream name -> the module of ours
#: that already carries it under that exact word (the `PRESENT` bucket).
#:
#: `docs/plan/final-state.md` reading 10, amended 2026-11-06: **"already resolves" is
#: measured at the SPELLING A CONSUMER WRITES, never at the module that declares it.**  A
#: name upstream carries at `adcp.types.<domain>.<Name>` that we also declare there is not
#: thereby reachable, because the import an application has already written is
#: `from adcp.types import <Name>`.  So these owe a FLAT alias exactly as a relocated name
#: does -- and they owe NOTHING here, because at this module they would be a second path to
#: a name that already resolves at the one the surface gives it.
#:
#: A MAPPING AND NOT RE-EXPORT STATEMENTS, which is the whole of why they are not in
#: `__all__`: `adcp.types.__getattr__` resolves a flat name through this module, and a
#: `from adcp.types.media_buy import X as X` here would hand these names a path at
#: `adcp.types.compat` that reading 10 does not ask for and nothing imports.
__adcp_flat_only__ = {
'''

MODULE_MARKER = '''
#: **THIS MODULE IS NOT A SUBJECT OF OURS AND SAYS SO**, which is what keeps the surveys
#: from reading their own output.  `survey/alias_surface.py` derives these bindings by
#: joining upstream's surface against OURS; with no marker, its next run would find every
#: upstream spelling "already a name of ours, at `adcp.types.compat`" and bind each alias to
#: itself, and `survey/migration_notes.py` would stop owing a migration note for any name
#: this module restates.  Both skip an `adcp.types` module carrying this attribute, so the
#: rule is declared by the module rather than listed in the scripts -- a second alias module
#: needs nothing edited.
__adcp_restates_upstream__ = "adcp %(version)s"
'''


def write_module(
    path: Path, module: str, decided: dict[str, dict], report: dict, version: str
) -> None:
    """Write the alias module: one re-export statement per upstream spelling.

    The ORDER is our module and then the upstream name, so a diff of this file after a
    re-run shows which subjects moved rather than a reshuffle.
    """
    # **`PRESENT` IS NOT GROUPED HERE AND THAT IS THE DIVISION OF LABOUR**: a statement for
    # it would be a second path at this module to a name that already resolves at the one
    # the surface gives it.  Those rows go to `__adcp_flat_only__` below, which gives them
    # the ONE path reading 10's amendment says they owe -- the flat spelling.
    groups: dict[str, list[tuple[str, str]]] = collections.defaultdict(list)
    for name, got in sorted(decided.items()):
        if got["bucket"] not in ("RELOCATED", "RENAMED"):
            continue
        where, ours = got["target"].rsplit(".", 1)
        groups[where].append((ours, name))
    # **ONE STATEMENT PER ALIAS, and that is ruff's reading rather than a taste.**  Grouped
    # into one `from X import (a as b, c as d)` the module is shorter and `I001` fires on it
    # -- isort's `combine-as-imports` is off by default, so a re-export under a NEW name is
    # a statement of its own.  `pyproject.toml`'s `[tool.ruff]` says what to do about a
    # finding in generated code and it is not to exclude the file: "a finding in a generated
    # module is a row against the generator", and this is the generator, so the shape moves
    # here rather than the rule moving there.
    #
    # **TWO FINDINGS REMAIN AND ARE NOT CLOSED BY A SHAPE: `I001` once and `E501` on 11
    # lines.**  Matching isort exactly means reproducing its line-wrapping as well as its
    # order, and the only way to get that right is to RUN the formatter over this output --
    # which would make a shipped file a function of the linter version.  `pyproject.toml`
    # refuses that in the opposite direction and for the reason that applies here: "a
    # checker is an instrument and the artifact does not depend on it", which is why `ruff`
    # is the one dependency NOT pinned exactly.  So the two are recorded as this
    # generator's own row rather than closed by coupling the artifact to the checker --
    # the same standing as the 399 `I001` findings `codegen/render.py` already owns in the
    # emitted tree.  `E501` is not in the selected set at all.
    lines = [MODULE_HEADER % {"version": version}]
    lines += [
        f"from {where} import {ours} as {name}\n"
        for where in sorted(groups)
        for ours, name in sorted(groups[where], key=lambda pair: (pair[0].lower(), pair[1].lower()))
    ]
    lines.append(MODULE_MARKER % {"version": version})
    exported = sorted(n for pairs in groups.values() for _, n in pairs)
    lines.append("\n__all__ = [\n")
    lines += [f'    "{n}",\n' for n in exported]
    lines.append("]\n")
    flat_only = {
        name: got["target"].rsplit(".", 1)[0]
        for name, got in sorted(decided.items())
        if got["bucket"] == "PRESENT"
    }
    lines.append(FLAT_ONLY_HEADER)
    lines += [f'    "{name}": "{where}",\n' for name, where in sorted(flat_only.items())]
    lines.append("}\n")
    path.write_text("".join(lines))
    report["module"] = module
    report["written"] = str(path)
    report["bound"] = len(exported)
    report["flat_only"] = len(flat_only)
    report["flat_owed"] = len(exported) + len(flat_only)
    print(
        f"{len(exported)} aliases over {len(groups)} modules of ours, plus "
        f"{len(flat_only)} flat-only names -> {len(exported) + len(flat_only)} flat "
        f"spellings -> {path}"
    )


#: The buckets the table carries a row for: the three this layer OWES, plus the two that
#: are its refusals.  A refusal with no row is indistinguishable from an oversight, which
#: is why `MEANING-DIFFERS` and `ABSENT-SUBJECT-NO-WORD` are written out by name rather
#: than counted -- the question a reader asks about a name that does not resolve is "why",
#: and only the row answers it.  Plain `ABSENT` and `NOT-A-TYPE` are
#: `survey/migration_notes.py`'s partition and `docs/migration-from-upstream.md`'s, which
#: already tell a caller what to use instead; they are counted in the header rather than
#: repeated here, because a second answer to one question is how the two go out of step.
TABLED = ("PRESENT", "RELOCATED", "RENAMED", "MEANING-DIFFERS", "ABSENT-SUBJECT-NO-WORD")


def write_table(path: Path, module: str, decided: dict[str, dict], report: dict, version: str) -> None:
    """One row per decided name: the name, its bucket, the module it is DECLARED at, ours.

    `declared_at` is the answer to reading 10's "a declared set of canonical modules": for
    `PRESENT` it is the module the upstream spelling already resolves at, for `RELOCATED`
    and `RENAMED` it is `module`, and for a refusal it is empty, because a refused name is
    declared nowhere and saying otherwise would make the table claim an import that fails.

    **NO ABSOLUTE PATH IN THE HEADER, which is what makes the fixed point CHECKABLE.**  The
    header used to name the venv the dump was read off, so two runs of the same derivation
    from two throwaway venvs produced tables differing in one line -- and "re-run it and the
    table is byte-identical" then needed a `sed` to be true, which is the kind of caveat that
    hides a real difference next time.  What the committed file owes a reader is WHICH
    SURFACE, not which directory: `adcp_emit <version>, installed wheel` is the identity, and
    the absolute path stays in `--report`, which is not committed.
    """
    lines = [
        (
            f"# The alias surface, upstream adcp {version} against adcp_emit "
            f"{report.get('ours_version') or 'unknown'} (installed wheel).\n"
        ),
        (
            f"# Population: {report['population']} -- {report['names']} names over "
            f"{report['spellings']} spellings.\n"
        ),
        "# " + "  ".join(f"{b}={n}" for b, n in sorted(report["buckets"].items())) + "\n",
        "name\tbucket\tdeclared_at\tours\tkey\tcorroborated\twhy\n",
    ]
    for name, got in sorted(decided.items()):
        if got["bucket"] not in TABLED:
            continue
        if got["bucket"] == "PRESENT":
            at = got["target"].rsplit(".", 1)[0]
        elif got["bucket"] in ("RELOCATED", "RENAMED"):
            at = module
        else:
            at = ""
        ours = got.get("target") or got.get("candidate") or ""
        lines.append(
            f"{name}\t{got['bucket']}\t{at}\t{ours}\t{got.get('by') or ''}\t"
            f"{got.get('corroborated') or ''}\t{got['why']}\n"
        )
    path.write_text("".join(lines))
    print(f"{len(lines) - 4} decided names -> {path}")


#: The buckets whose target the generator imports before writing anything.  All three the
#: layer owes: `RELOCATED` and `RENAMED` because this module binds them, and `PRESENT`
#: because `__adcp_flat_only__` names the module its flat spelling is reached at.
PROVED_BUCKETS = ("PRESENT", "RELOCATED", "RENAMED")


def prove_the_targets(decided: dict[str, dict]) -> dict[str, str]:
    """Every target IMPORTED, in this interpreter, before anything is written.

    **THE DEFECT THIS EXISTS FOR, measured.**  The table was derived against a dump of our
    surface and then committed; `sdk/home2` landed meanwhile and took the surface from 1,881
    names to 1,879, removing `DAASTTrackerConstraintsDaastTarget`.  The table still named it,
    so `adcp.types.compat` raised `ImportError` at import -- which took down the whole
    reading-8 wheel gate with it ("the installed wheel's own probe exited 1, so every reading
    below is about nothing") and reported itself, through a predicate that caught the
    exception, as a missing marker.  One stale row, six gates saying nothing about the
    artifact and one diagnosis pointing at the wrong file.

    So the generator proves its own output at GENERATION time: a dangling target is a refusal
    to write, naming every row, rather than an `ImportError` a consumer finds later.  This is
    the same discipline the emitted tree already has -- a claim is checked where it is made.

    **IT IMPORTS THE TARGETS AND NEVER THE ALIAS MODULE ITSELF**, which is what keeps the
    check from depending on the file it is about -- and is why it takes no `module`
    argument: a stale or broken alias module must not be able to make this pass OR fail.

    **AND `PRESENT` IS PROVED TOO, SINCE READING 10's AMENDMENT OF 2026-11-06.**  Those 79
    rows write no statement here, but `__adcp_flat_only__` names the module each one is
    reached at and `adcp.types.__getattr__` resolves a flat spelling through it -- so a
    `PRESENT` target the surface stops carrying is the same `DAASTTrackerConstraintsDaastTarget`
    defect one layer further out, and arrives as an `AttributeError` from the flat namespace
    rather than as an `ImportError` from this module.  Proving it here is what keeps the
    repair at generation time.

    **AND BEING UNABLE TO IMPORT OURS AT ALL IS A REFUSAL, NOT A SKIP.**  Phase 3 is
    otherwise standard-library only; if `adcp.types` cannot be imported here the table cannot
    be proved, and a check that cannot run must say so rather than pass.
    """
    import importlib

    targets = {got["target"] for got in decided.values() if got["bucket"] in PROVED_BUCKETS}
    if not targets:
        return {}
    try:
        importlib.import_module("adcp.types")
    except BaseException as exc:  # noqa: BLE001
        raise SystemExit(
            f"cannot import `adcp.types` here ({type(exc).__name__}: {exc}), so the "
            f"{len(targets)} targets cannot be proved and the table must not be written.  "
            "Run phase 3 with PYTHONPATH=.:src on the project's own interpreter."
        ) from exc
    dangling: dict[str, str] = {}
    for name, got in sorted(decided.items()):
        if got["bucket"] not in PROVED_BUCKETS:
            continue
        where, ours = got["target"].rsplit(".", 1)
        try:
            found = importlib.import_module(where)
        except BaseException as exc:  # noqa: BLE001
            dangling[name] = f"{got['target']} ({type(exc).__name__}: {exc})"
            continue
        if not hasattr(found, ours):
            dangling[name] = f"{got['target']} is not a name {where} carries"
    return dangling


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dump-ours", type=Path, metavar="PATH")
    parser.add_argument("--dump-upstream", type=Path, metavar="PATH")
    parser.add_argument("--ours", type=Path, metavar="PATH")
    parser.add_argument("--upstream", type=Path, metavar="PATH")
    parser.add_argument(
        "--bundle",
        type=Path,
        default=HERE.parent / "schemas" / "cache" / "3.2",
        help="the bundle whose words decide whether a name is a subject the schema names",
    )
    parser.add_argument("--module", default="adcp.types.compat")
    parser.add_argument("--write", type=Path, metavar="PATH")
    parser.add_argument("--report", type=Path, metavar="PATH")
    parser.add_argument(
        "--table",
        type=Path,
        metavar="PATH",
        help="the committed evidence: one row per name this layer decides, with the module "
        "it is declared at.  `tests/test_the_alias_layer_is_names.py` reads it, so the gate "
        "needs no upstream wheel -- and a bead citing it is not citing a scratch directory",
    )
    parser.add_argument(
        "--deliberate-only",
        action="store_true",
        help="range over the deliberate surface only -- the names a module DECLARED",
    )
    args = parser.parse_args()
    if args.dump_ours:
        dump_ours(args.dump_ours)
        return
    if args.dump_upstream:
        dump_upstream(args.dump_upstream)
        return
    if not (args.ours and args.upstream):
        parser.error("phase 3 needs --ours and --upstream")

    sys.path.insert(0, str(HERE.parent / "tests"))
    from nodeset import claimed

    ours_blob = json.loads(args.ours.read_text())
    up_blob = json.loads(args.upstream.read_text())
    assert up_blob.get("version") not in (None, "unknown"), (
        "the upstream dump records no version, and every count below is a claim about one"
    )
    views = _ours_views(ours_blob)
    index = bundle_index(args.bundle)
    claimed(f"our surface read off {ours_blob['ours']}", views[2])
    claimed(f"upstream {up_blob['version']}'s public names", up_blob["names"])
    claimed(f"the words the bundle at {args.bundle} states", index["titles"])

    population = {
        n: r
        for n, r in up_blob["names"].items()
        if r["deliberate"] or not args.deliberate_only
    }
    decided = {n: verdict(r, views, index) for n, r in sorted(population.items())}

    buckets = collections.Counter(v["bucket"] for v in decided.values())
    keys = collections.Counter(
        (v["bucket"], v.get("by"), v.get("corroborated"))
        for v in decided.values()
        if v.get("by")
    )
    owed = {n: v for n, v in decided.items() if v["bucket"] in ("PRESENT", "RELOCATED", "RENAMED")}
    report = {
        "upstream_version": up_blob["version"],
        "ours": ours_blob["ours"],
        "ours_version": ours_blob.get("version"),
        "population": "deliberate" if args.deliberate_only else "every public name",
        "names": len(population),
        "spellings": sum(len(r["modules"]) for r in population.values()),
        "buckets": dict(buckets),
        "keys": {f"{b} by {k}, corroborated by {c}": n for (b, k, c), n in sorted(keys.items())},
        "bundle": str(args.bundle),
        "owed": len(owed),
        "verdicts": decided,
    }
    print(f"upstream adcp {up_blob['version']} vs {ours_blob['ours']}")
    print(f"  population: {report['names']} names over {report['spellings']} spellings")
    for bucket, count in buckets.most_common():
        print(f"  {bucket:24} {count:6}")
    print(f"  {'OWED (P+REL+REN)':24} {len(owed):6}")
    for key, count in report["keys"].items():
        print(f"    {key:62} {count:6}")
    dangling = prove_the_targets(decided)
    report["dangling"] = dangling
    if dangling and (args.write or args.table):
        raise SystemExit(
            f"REFUSING TO WRITE: {len(dangling)} of the {len(owed)} owed rows name a target "
            f"that does not resolve in THIS tree, so the table would be committed pointing "
            f"at nothing.\n"
            + "\n".join(f"  {name} -> {why}" for name, why in sorted(dangling.items()))
            + f"\n\nThe dump was read off {ours_blob['ours']}.  If the tree has moved since, "
            "re-run phase 1 against a wheel built from THIS tree; if the name is gone for "
            "good, that is a verdict to record and not a row to hand-patch."
        )
    if args.write:
        write_module(args.write, args.module, decided, report, up_blob["version"])
    if args.table:
        write_table(args.table, args.module, decided, report, up_blob["version"])
    if args.report:
        args.report.write_text(json.dumps(report, indent=1))
        print(f"report -> {args.report}")


if __name__ == "__main__":
    main()
