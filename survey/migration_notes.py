"""Partition every name consumer code imports, and grade the migration guide against it.

`survey/consumer_imports.py` answers *how much* of what a caller spells this package
ships.  This answers the next question, which is the one a reader porting an application
asks: **for each name individually, is there something of ours to use instead, or is there
nothing?**  The answer is `docs/migration-from-upstream.md`, and the last thing this script
does is grade that document: every name in a bucket the guide owes an entry for must be
named in it, or this exits non-zero.

**THE JOIN IS ON IDENTITY AND NEVER ON A NAME**, which is `docs/plan/final-state.md`
reading 10's rule: "an alias is keyed on a schema subject, never on a name.  The key is
identity: the field set read by wire alias, or the enum's value list."  A name decides
nothing here -- `TaskStatus` is a word two unrelated subjects carry -- and the consequence
worth having is that this partition does not move when a class of ours is renamed.

TWO PHASES, because the two trees cannot be imported into one interpreter: installing both
wheels interleaves `adcp/` at file granularity and `pip check` reports the wreckage as
compatible.  So each side dumps its identities and the join is offline.

    # phase 1, on an interpreter carrying OURS
    PYTHONPATH=.:src ./.venv/bin/python survey/migration_notes.py \
        --dump-ours $TMPDIR/ours-identities.json

    # phase 2, on an interpreter carrying UPSTREAM -- never the shared `.venv`
    uv venv $TMPDIR/up && uv pip install --python $TMPDIR/up/bin/python adcp==9.6.1
    $TMPDIR/up/bin/python survey/migration_notes.py \
        --corpus /srv/ws/wt-v92 \
        --ours $TMPDIR/ours-identities.json \
        --guide docs/migration-from-upstream.md

**AND THE EMPTY CORPUS IS AN ERROR AND NEVER A PASS, which is the defect this paragraph
exists for.**  Run against `/srv/ws/adcp-upstream` -- a sparse, blobless clone whose
`sparse-checkout` is `static/schemas` and `scripts`, with no `examples/` and no `docs/` --
an earlier form of this script reported "names every one of the 0 names it owes an entry
for" and exited 0, **and went on reporting it after an owed name was deleted from the
guide.**  So in that environment the gate could not fail for any content of the document,
which is `final-state.md`'s "a check that passes when nothing happens decides nothing"
arriving inside the check written to enforce it.  The three sets this run ranges over are
therefore passed through `tests/nodeset.claimed`, the idiom this repository already has for
refusing an empty one, and each names the corpus path it looked in.  `--corpus` is a
REQUIRED argument for the same reason: a default would make the corpus an inference, and
the inference is what was wrong.

`--out` defaults under `TMPDIR` and never the working directory: invoked from the
repository root, the earlier form wrote `migration-partition.json` into the worktree.
"""

from __future__ import annotations

import argparse
import collections
import enum
import importlib
import importlib.metadata as md
import json
import os
import pkgutil
import re
import sys
import tempfile
from pathlib import Path

#: A RootModel's field set.  It says nothing about the subject, so it is not an identity.
ROOTONLY = frozenset({"root"})

#: Upstream's own layers under `adcp.types` that no document states.  Read off the DEFINING
#: module, which is the only thing that separates a class upstream generated from a schema
#: from one a person wrote: `adcp.types.domains.*` and `adcp.types.generated_poc.*` are
#: generated, and these are not.
HANDWRITTEN = (
    "adcp.types.base",
    "adcp.types.core",
    "adcp.types.aliases",
    "adcp.types.legacy",
    "adcp.types._legacy_assets",
    "adcp.types.registry",
    "adcp.types.guards",
    "adcp.types.validation",
    "adcp.types.variants",
    "adcp.types.capabilities",
    "adcp.types.canonical_creative",
    "adcp.types.versioned_bases",
    "adcp.types._eager",
    "adcp.types._wire",
    "adcp.types._scalar",
    "adcp.types.error_details",
)

NONTYPE_KINDS = {
    "function",
    "builtin_function_or_method",
    "method",
    "partial",
    "str",
    "int",
    "float",
    "bool",
    "bytes",
    "tuple",
    "list",
    "set",
    "dict",
    "frozenset",
    "NoneType",
}
CLASS_KINDS = {"ModelMetaclass", "type", "ABCMeta", "EnumType", "EnumMeta", "_ProtocolMeta"}

#: The kinds a `typing` alias DECLARATION is, as against `typing.Annotated` itself.  An
#: alias reports `__module__ == "typing"` no matter who declared it, so the kind is the only
#: thing that separates "a declaration of ours" from "a name this module imported".
ALIAS_KINDS = {
    "_AnnotatedAlias",
    "_UnionGenericAlias",
    "_GenericAlias",
    "_LiteralGenericAlias",
    "UnionType",
    "TypeAliasType",
}

#: Buckets the guide owes an entry for.  `ALIAS LAYER` is the one that is absent, on
#: purpose: those names are the alias layer's business (`adcp-client-python-82m.7`) and a
#: guide entry for them would be a second answer to one question.
OWED = (
    "MACHINERY",
    "NOT ON UPSTREAM'S WHEEL",
    "NOT A TYPE",
    "MEANING DIFFERS",
    "NO SCHEMA SUBJECT",
    "UNDECIDED",
)


#: **A MODULE THAT RESTATES UPSTREAM'S WORDS IS NOT A SUBJECT OF OURS.**  The alias layer
#: (`survey/alias_surface.py`, `adcp.types.compat`) binds upstream's spellings to classes
#: this tree already declares, so counting its names here would make this partition read
#: every aliased name as "a name we carry" and stop owing it a migration note -- on the
#: evidence of a file derived FROM this partition's own sibling.  The module declares its
#: nature in `__adcp_restates_upstream__` and this reads the declaration, so the rule lives
#: in one place and a second alias module needs nothing edited here.
RESTATES = "__adcp_restates_upstream__"

#: `restatement`'s three answers.  **THREE AND NOT TWO, AND THE MISSING THIRD COST A
#: DIAGNOSIS.**  The first form of this predicate answered a BOOLEAN and caught every
#: exception into `False`, so a module that does not IMPORT read as "not an alias layer" --
#: and when `adcp.types.compat` was merged against a surface that had dropped one of its
#: targets, the gate reported "does not declare `__adcp_restates_upstream__`" about a module
#: whose line 1012 declares exactly that.  A reader is then sent after a missing marker
#: instead of after the `ImportError` that is the actual cause.
#:
#: The dangerous direction is the other one and it is why the state is reported rather than
#: raised: "cannot tell" silently spelled "no" would, for a module that DOES import with its
#: marker renamed, feed our own aliases back into the partition as our surface.
RESTATES_ANSWERS = ("restates", "ours", "unimportable")


def restatement(mod_name: str) -> tuple[str, str]:
    """`(answer, detail)` -- which of :data:`RESTATES_ANSWERS` `mod_name` is, and why.

    * `("restates", <the marker's value>)` -- an alias layer, to be skipped by any reading
      of OUR surface;
    * `("ours", "")` -- a module of ours, to be read;
    * `("unimportable", "<ExceptionType>: <message>")` -- **neither answer is available**,
      which is a finding and never a skip reached by accident.
    """
    import importlib

    try:
        mod = importlib.import_module(mod_name)
    except BaseException as exc:  # noqa: BLE001 -- the payload is the report
        return ("unimportable", f"{type(exc).__name__}: {str(exc).splitlines()[0][:200]}")
    if hasattr(mod, RESTATES):
        return ("restates", str(getattr(mod, RESTATES)))
    return ("ours", "")


def restates_upstream(mod_name: str) -> bool:
    """Whether `mod_name` is an alias layer rather than a surface of ours.

    **`False` here means "a module of ours" and nothing else.**  A caller that must not
    confuse that with "could not be read" asks :func:`restatement` for the third answer --
    which every caller in this file now does, so the skip is reported with its reason.
    """
    return restatement(mod_name)[0] == "restates"


def ident_key(kind: str, members) -> str:
    """One hashable spelling of an identity, so the two phases join on equality."""
    return json.dumps([kind, sorted(members)])


def identity(obj) -> tuple[str, frozenset[str]] | None:
    """`("enum", values)` or `("model", wire aliases)` -- reading 10's key, or None."""
    if isinstance(obj, type) and issubclass(obj, enum.Enum):
        return ("enum", frozenset(str(m.value) for m in obj))
    fields = getattr(obj, "model_fields", None)
    if isinstance(fields, dict) and fields:
        wire = frozenset(
            (getattr(f, "alias", None) or getattr(f, "serialization_alias", None) or n)
            for n, f in fields.items()
        )
        if wire and wire != ROOTONLY:
            return ("model", wire)
    return None


def walk(root_name: str) -> list[str]:
    root = importlib.import_module(root_name)
    return [root_name, *(m.name for m in pkgutil.walk_packages(root.__path__, root_name + "."))]


# --------------------------------------------------------------------------- phase 1


def dump_ours(out_path: Path) -> None:
    """identity -> every (name, import path, document) of ours that holds it.

    **EVERY MODULE THIS DECLINES TO READ IS RECORDED WITH ITS REASON**, under `skipped` in
    the dump and printed at the end.  A silent `except Exception: continue` is what made a
    broken alias module indistinguishable from a deliberately excluded one: the surface read
    the same either way, so a dump taken over a tree whose `adcp.types.compat` raised was
    reported as a complete reading of ours.  The three reasons are different facts --
    `restates upstream` is a decision, `does not import` is a defect, `private tree` is the
    rule -- and `tests/test_the_alias_layer_is_names.py` grades that they stay distinct.
    """
    table: dict[str, list[dict[str, str | None]]] = collections.defaultdict(list)
    names: dict[str, list[dict[str, str | None]]] = {}
    exported: dict[int, str] = {}
    skipped: dict[str, str] = {}
    for mod_name in walk("adcp.types"):
        if "._schemas" in mod_name:
            continue
        answer, detail = restatement(mod_name)
        if answer != "ours":
            skipped[mod_name] = f"{answer}: {detail}" if detail else answer
            continue
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        for name, obj in vars(mod).items():
            if name.startswith("_"):
                continue
            try:
                exported.setdefault(id(obj), f"{mod_name}.{name}")
            except TypeError:
                continue
    seen: set[tuple[str, str]] = set()
    for mod_name in walk("adcp.types"):
        if restatement(mod_name)[0] != "ours":
            continue  # already recorded with its reason by the loop above
        try:
            mod = importlib.import_module(mod_name)
        except Exception:
            continue
        ref = getattr(mod, "__adcp_schema__", None)
        for name, obj in vars(mod).items():
            if name.startswith("_") or (mod_name, name) in seen:
                continue
            seen.add((mod_name, name))
            # **A MODULE'S `vars()` HOLDS WHAT IT IMPORTED**, so without a filter the names
            # recorded against `core/context.json` were `Annotated`, `Any` and `SchemaRef`
            # beside the declaration that document states.  Two cases and they separate on
            # different facts: a CLASS of ours is defined under `adcp.types`, so its
            # `__module__` says so; an `Annotated[...]` alias of ours reports
            # `__module__ == "typing"` whatever module declared it, so for those the
            # object's KIND is what distinguishes a declaration (`_AnnotatedAlias`,
            # `_UnionGenericAlias`) from `typing.Annotated` itself (a bare `type`).
            if type(obj).__name__ in ALIAS_KINDS:
                pass
            elif not (
                isinstance(obj, type)
                and str(getattr(obj, "__module__", "")).startswith("adcp.types")
            ):
                continue
            own = getattr(obj, "__adcp_schema__", None) or ref
            row = {
                "name": name,
                "path": exported.get(id(obj), f"{mod_name}.{name}"),
                "document": getattr(own, "document", None),
                "pointer": getattr(own, "pointer", None),
            }
            if row not in names.setdefault(name, []):
                names[name].append(row)
            # **A UNION ROOT'S FIELD SET IS `{"root"}` AND SAYS NOTHING**, so it has no
            # identity and is recorded under `names` only.  Dropping it from `names` too
            # was the first version of this dump and it made `AccountReference` read as a
            # name we carry nowhere, which is false.
            ident = identity(obj)
            if ident is None:
                continue
            key = ident_key(*ident)
            if row not in table[key]:
                table[key].append(row)
    # The TREE and not a version string: this side is usually a source checkout, so what a
    # reader needs recorded is which `adcp/types` the identities were read off.
    where = importlib.import_module("adcp.types").__path__[0]
    out_path.write_text(
        json.dumps(
            {"ours": where, "identities": table, "names": names, "skipped": skipped},
            indent=1,
        )
    )
    print(
        f"{len(table)} distinct identities and {len(names)} names read off {where}, "
        f"written to {out_path}"
    )
    for mod_name, why in sorted(skipped.items()):
        print(f"  not read: {mod_name} -- {why}")


# --------------------------------------------------------------------------- phase 2


def resolve(ci, index: dict[int, str], mod_name: str, name: str) -> dict:
    """What upstream's installed wheel actually gives for one spelling.

    **Attribution is `consumer_imports.defining_module`'s and not a second copy of it**,
    which matters for one kind of object and was measured on it: `adcp.WholesaleFeedEvent` is a
    `typing.Annotated` union, so its `__module__` is `typing` and a naive fallback to the
    module it was spelled at attributes it to `adcp` -- machinery -- when it is a type.
    That instrument resolves it to `adcp.types` by object identity.  Two attributions would
    disagree on nine names of the 503 and the README's table would stop adding up.
    """
    defining = ci.defining_module(mod_name, name, index)
    if defining is None:
        # `RAISED` holds the exception the NAME raised.  No entry means the MODULE did not
        # import, which is a different finding and is reported as one.
        try:
            importlib.import_module(mod_name)
        except Exception as exc:
            fallback = f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
        else:
            fallback = "resolves to nothing, and raised nothing"
        return {"err": ci.RAISED.get((mod_name, name), fallback)}
    obj = getattr(importlib.import_module(mod_name), name)
    row = {"kind": type(obj).__name__, "defining": defining}
    ident = identity(obj)
    if ident is not None:
        row["identity_kind"] = ident[0]
        row["identity"] = sorted(ident[1])
    return row


#: Upstream's generated prefixes.  A module under one of these is named for a bundle
#: document, which is how a name with no identity match still gets a subject named.
GENERATED = (
    "adcp.types.domains.bundled.",
    "adcp.types.domains.",
    "adcp.types.generated_poc.bundled.",
    "adcp.types.generated_poc.",
    "adcp._generated_poc_alias.",
)


def document_of(defining: str, documents: set[str]) -> str | None:
    """The bundle document upstream's defining module is named for, or None.

    `adcp.types.domains.core.account_ref` -> `core/account-ref.json`.  The candidate set is
    the documents OURS carries, so a hit means both sides name the same document and a miss
    is reported as a miss rather than guessed at.
    """
    for prefix in GENERATED:
        if defining.startswith(prefix):
            tail = defining[len(prefix) :].split(".")
            break
    else:
        return None
    for cut in range(len(tail), 0, -1):
        stem = "/".join(tail[:cut])
        for candidate in (stem.replace("_", "-") + ".json", stem + ".json"):
            if candidate in documents:
                return candidate
    return None


def nearest(kind: str, members, ours: dict[str, list[dict]], top: int = 3) -> list[dict]:
    """The classes of ours whose identity most nearly agrees, as EVIDENCE and not a verdict.

    Reading 10: "many upstream names landing on one class of ours is a hypothesis, not a
    verdict", and partial agreement is exactly that.  So this reports the overlap with its
    number, for a reader to decide by reading the document -- it decides nothing.
    """
    want = set(members)
    scored: list[tuple[float, dict]] = []
    for key, rows in ours.items():
        their_kind, their_members = json.loads(key)
        if their_kind != kind:
            continue
        theirs = set(their_members)
        overlap = len(want & theirs) / len(want | theirs)
        if overlap > 0.0:
            scored.append((overlap, rows[0]))
    scored.sort(key=lambda t: -t[0])
    return [
        {
            "path": row["path"],
            "document": row["document"],
            "agreement": round(score, 2),
        }
        for score, row in scored[:top]
    ]


def classify(row: dict, ours: dict[str, list[dict]]) -> dict:
    if "err" in row:
        return {"bucket": "NOT ON UPSTREAM'S WHEEL", "why": row["err"]}
    defining = row["defining"] or ""
    if not (defining == "adcp.types" or defining.startswith("adcp.types.")):
        return {"bucket": "MACHINERY", "why": f"defined by `{defining}`"}
    if row["kind"] in NONTYPE_KINDS or (
        row["kind"] not in CLASS_KINDS and "identity" not in row
    ):
        what = "a function" if "function" in row["kind"] or row["kind"] == "method" else (
            f"a value of type `{row['kind']}`"
        )
        return {"bucket": "NOT A TYPE", "why": f"{what}, defined by `{defining}`"}
    hand = defining.startswith(HANDWRITTEN)
    if "identity" in row:
        key = ident_key(row["identity_kind"], row["identity"])
        hit = ours.get(key)
        if hit:
            return {"bucket": "ALIAS LAYER", "targets": hit, "why": "identity equal"}
    return _no_match(row, defining, hand=hand)


def _no_match(row: dict, defining: str, *, hand: bool) -> dict:
    # **"MEANING DIFFERS" NEEDS TWO IDENTITIES, and one of them was missing.**  A union
    # root's field set is `{"root"}`, so upstream's `PropertyTag` carries no identity at
    # all -- and calling that a disagreement reports a comparison that never happened.
    # Measured: it claimed two names differ where neither side had anything to compare.
    if row.get("name_in_ours") and "identity" in row:
        return {
            "bucket": "MEANING DIFFERS",
            "why": f"we carry the word, defined by `{defining}`; the identities disagree",
        }
    if "identity" not in row:
        return {
            "bucket": "NO SCHEMA SUBJECT" if hand else "UNDECIDED",
            "why": (
                f"defined by `{defining}`, and upstream's object carries no identity to "
                "join on -- a union root's field set says nothing about its subject"
            ),
        }
    if hand:
        return {"bucket": "NO SCHEMA SUBJECT", "why": f"defined by `{defining}`"}
    return {
        "bucket": "UNDECIDED",
        "why": (
            f"`{defining}` is upstream's generated tree, so a document states a subject, "
            "and no identity of ours equals it"
        ),
    }


def cli() -> argparse.Namespace:
    """The arguments, every one of them named.

    **`--corpus` IS REQUIRED AND HAS NO DEFAULT**, which is the whole point: the corpus was
    an inference before, and the inference is what produced a gate that could not fail.  A
    reader handing this the wrong tree now gets an error naming the tree.
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--dump-ours",
        type=Path,
        metavar="PATH",
        help="phase 1, on an interpreter carrying OURS: write this tree's identities here",
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        metavar="CHECKOUT",
        help="phase 2: upstream's v9.2.0 checkout, WITH its examples/ and docs/ -- a sparse "
        "clone carrying only static/schemas yields nothing and is refused",
    )
    parser.add_argument(
        "--ours", type=Path, metavar="PATH", help="phase 2: the file --dump-ours wrote"
    )
    parser.add_argument(
        "--guide",
        type=Path,
        metavar="PATH",
        help="phase 2: grade this document and exit 1 on any owed name it does not name",
    )
    parser.add_argument(
        "--out",
        type=Path,
        metavar="PATH",
        default=Path(os.environ.get("TMPDIR") or tempfile.gettempdir())
        / "migration-partition.json",
        help="where the partition is written; defaults under TMPDIR and never the working "
        "directory, which an earlier form of this script littered",
    )
    args = parser.parse_args()
    if args.dump_ours is None and not (args.corpus and args.ours):
        parser.error("phase 2 needs --corpus and --ours (or use --dump-ours for phase 1)")
    return args


def main() -> None:
    args = cli()
    if args.dump_ours is not None:
        dump_ours(args.dump_ours)
        return

    here = Path(__file__).parent
    sys.path.insert(0, str(here))
    sys.path.insert(0, str(here.parent / "tests"))
    import consumer_imports as ci
    from nodeset import claimed

    checkout = args.corpus
    ours_blob = json.loads(args.ours.read_text())
    ours = ours_blob["identities"]
    # **PUBLIC PATHS ONLY, and the filter is every underscore-prefixed segment and not
    # just `_schemas`.**  Measured: with `_schemas` alone, `AdCPBaseModel` read as a name we
    # carry -- at `adcp.types._base`, which reading 6 makes private -- and the entry for it
    # would have told a reader to import a module this package does not offer.
    ours_by_name: dict[str, list[dict]] = {}
    for name, rows in ours_blob["names"].items():
        public: list[dict] = []
        for r in sorted(rows, key=lambda r: r["document"] is None):
            if any(seg.startswith("_") for seg in r["path"].split(".")[2:]):
                continue
            if not any(p["path"] == r["path"] for p in public):
                public.append(r)
        if public:
            ours_by_name[name] = public
    our_names = set(ours_by_name)
    # **FROM `names` AND NOT FROM `identities`, and the difference was measured.**  A union
    # root has no identity, so `core/context.json` was absent from this set and
    # `document_of` reported "no document" for a name whose document this package compiles.
    # The candidate set has to be every document ours carries, not every document ours
    # carries a comparable identity for.
    by_document: dict[str, set[str]] = collections.defaultdict(set)
    for rows in ours_blob["names"].values():
        for r in rows:
            if r["document"]:
                by_document[r["document"]].add(r["path"])
    documents = set(by_document)

    # **THE CORPUS IS CLAIMED IN TWO HALVES, and separately, because a checkout can have
    # one and not the other.**  `/srv/ws/adcp-upstream` has `README.md` and no `examples/`;
    # claiming only the total would be satisfied by the README's fences alone and would
    # still grade a corpus missing the 80 example files the figures are stated over.
    fragments = ci.corpus(checkout)
    claimed(
        f"example and skill sources under {checkout} (examples/**/*.py, skills/**/*.py)",
        [label for label, _ in fragments if label.endswith(".py")],
    )
    claimed(
        f"documentation fences under {checkout} "
        "(README.md, llms.txt, MIGRATION*.md, docs/**/*.md, skills/**/*.md)",
        [label for label, _ in fragments if "#fence" in label],
    )

    spellings: dict[str, set[str]] = collections.defaultdict(set)
    for label, src in fragments:
        for mod_name, name, _ in ci.parse(label, src):
            if name:
                spellings[name].add(mod_name)
    claimed(f"names imported from `adcp` by the corpus under {checkout}", spellings)

    index = ci.build_index()
    partition: dict[str, dict] = {}
    for name, mods in sorted(spellings.items()):
        row: dict = {"err": "never spelled"}
        errors: dict[str, str] = {}
        for mod_name in sorted(mods):
            row = resolve(ci, index, mod_name, name)
            if "err" not in row:
                break
            errors[mod_name] = row["err"]
        row["name_in_ours"] = name in our_names
        verdict = classify(row, ours)
        verdict["spelled_at"] = sorted(mods)
        if "err" in row:
            # EVERY spelling's error, not the last one tried: `FormatCategory` raises
            # upstream's own `ImportError` at `adcp` and is a missing module at the other
            # path it is spelled at, and a note quoting one of those is quoting half of it.
            verdict["errors"] = errors
        verdict["defining"] = row.get("defining")
        if "identity" in row:
            verdict["upstream_identity"] = row["identity"]
            verdict["upstream_identity_kind"] = row["identity_kind"]
        if verdict["bucket"] not in ("MACHINERY", "NOT ON UPSTREAM'S WHEEL", "ALIAS LAYER"):
            document = document_of(row.get("defining") or "", documents)
            if document:
                verdict["document"] = document
                verdict["our_classes_for_that_document"] = sorted(
                    by_document.get(document, ())
                )
            if "identity" in row:
                verdict["nearest"] = nearest(row["identity_kind"], row["identity"], ours)
        if verdict["bucket"] in OWED and ours_by_name.get(name):
            # **A WORD AND NOT A VERDICT.**  Reading 10: "a name is the thing being aliased,
            # not the thing that decides what it aliases to".  Reported so an entry can
            # tell a reader where to look, labelled so nobody mistakes it for a decision.
            verdict["we_carry_the_word_at"] = [
                {"path": r["path"], "document": r["document"]}
                for r in ours_by_name[name]
            ]
        partition[name] = verdict

    counts = collections.Counter(v["bucket"] for v in partition.values())
    print(f"upstream wheel: {md.version('adcp')}   ours read off: {ours_blob['ours']}")
    print(f"consumer-imported distinct names: {len(partition)}")
    for bucket, n in counts.most_common():
        owed = " (the guide owes an entry)" if bucket in OWED else ""
        print(f"  {bucket:26s} {n:4d}{owed}")
    # **AND THE OWED SET ITSELF, which is the one that actually bit.**  Every assertion the
    # grade makes is over this set, so an empty one is a green run that decided nothing --
    # and it stayed green with an owed name deleted from the guide, which is the proof that
    # it was grading the emptiness and not the document.
    owed_names = sorted(
        claimed(
            f"names owed an entry, derived from the corpus under {checkout} "
            f"({', '.join(OWED)})",
            (n for n, v in partition.items() if v["bucket"] in OWED),
            inside=partition,
        )
    )
    print(f"names the guide owes an entry: {len(owed_names)}")

    by_module: collections.Counter[str] = collections.Counter()
    for v in partition.values():
        if v["bucket"] == "MACHINERY":
            by_module[v["defining"]] += 1
    print(f"machinery names by defining module: {len(by_module)} modules")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {
                "upstream_version": md.version("adcp"),
                "corpus": str(checkout),
                "corpus_python_files": sum(1 for lb, _ in fragments if lb.endswith(".py")),
                "corpus_doc_fences": sum(1 for lb, _ in fragments if "#fence" in lb),
                "distinct_names": len(partition),
                "counts": dict(counts),
                "owed": owed_names,
                "partition": partition,
            },
            indent=1,
            sort_keys=True,
        )
    )
    print(f"partition written to {args.out}")

    if args.guide is not None:
        sys.exit(grade(args.guide, owed_names))


def grade(guide: Path, owed_names: list[str]) -> int:
    """0 when the guide names every name it owes an entry for, 1 otherwise.

    A name counts as named when it appears inside a backticked span, which is how this
    document writes every name -- so prose that happens to use the word "Format" in a
    sentence does not satisfy the entry the guide owes for `Format`.
    """
    text = guide.read_text()
    named: set[str] = set()
    for span in re.findall(r"`([^`]+)`", text):
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", span):
            named.add(token)
    missing = [n for n in owed_names if n not in named]
    print()
    if missing:
        print(
            f"{guide} is missing an entry for {len(missing)} of {len(owed_names)} names "
            f"it owes one for: {missing}"
        )
        return 1
    print(f"{guide} names every one of the {len(owed_names)} names it owes an entry for.")
    return 0


if __name__ == "__main__":
    # **`nodeset.claimed` RAISES, and a traceback is a true report that a reader skims.**
    # The refusal is the one message that has to be read rather than scrolled past -- it is
    # the difference between fixing the invocation and believing a green -- so it is printed
    # as itself, on stderr, with the exit code the assertion already implies.  Nothing is
    # swallowed: the message is `claimed`'s own, verbatim.
    try:
        main()
    except AssertionError as refusal:
        print(f"\nREFUSED: {refusal}", file=sys.stderr)
        print(
            "This run grades nothing, so it is an error and not a pass. `--corpus` must be "
            "upstream's v9.2.0 checkout WITH its `examples/` and docs tree; a sparse clone "
            "limited to `static/schemas` yields no imports and nothing to owe an entry for.",
            file=sys.stderr,
        )
        sys.exit(1)
