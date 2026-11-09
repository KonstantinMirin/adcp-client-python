"""The compatibility ADAPTER: upstream's own module paths, served from our surface.

`survey/alias_surface.py` answers "which object of ours does an upstream NAME denote" over
upstream's whole public surface and writes ONE module, `adcp.types.compat`.  This script
answers a narrower and harder question: **which of upstream's own MODULES does their kept
machinery import at module scope, and what does each name it asks for denote here.**

THE DEMAND IS MEASURED, NEVER LISTED (:func:`census`).  Every `.py` under `src/adcp/`
outside `src/adcp/types/` is parsed and every module-scope `from adcp.types... import X`
recorded -- "module scope" meaning anything not inside a function or class body, because a
top-level `if TYPE_CHECKING:` or `try:` executes as the module body runs and a missing name
there takes the whole file.  The pair is then RESOLVED live, so the demand this script
ranges over is exactly the set that does not already work.

THE KEY IS A DOCUMENT AND A WORD THE DOCUMENT GIVES.  Upstream's class carries its
declaring module in `__module__`, and that module's path IS a bundle document's path
(`adcp.types.domains.core.product` <- `core/product.json`) -- the same arithmetic
`survey/dropin/_dropin.py` does in one line, with the projection segment dropped.  It
carries its own word in `__qualname__`, and both trees derive that word from the document.
So upstream's own name says WHICH DOCUMENT and WHICH NODE, and neither half is a guess.

NINE KEYS, each reported as itself because "what the key was read off" is the first thing a
disagreement about a row turns out to be about.  `survey/alias_surface.py`'s two are the
first three; the rest are the owner's extension (`adcp-client-python-1hck`, amended), and
each is tried in this order so a stronger key is never overridden by a weaker one:

    document+word           one document, the same word on both sides.  No judgment at all.
    document+word-recased   the same word with an acronym re-cased (`A2Ui`/`A2UI`).
    document+identity       the document proposes EVERY declaration it makes and identity
                            gates.  1hck proposed the document's ROOT; the ruling extends it
                            to the document, because `PrincipalConfiguration` is an INNER
                            node of `protocol/sync-principal-request.json` and a root key
                            cannot see it.
    document+ordinal        their generator's collision suffix.  `<Root>N` is the Nth arm of
                            the document's root union IN THE DOCUMENT'S OWN ORDER, and ours
                            emits the arms in that same order (`_branch_models`).  **GATED
                            TWICE**: their `<Root>` family must be exactly our root plus its
                            branches (`len(family) == len(branches) + 1`, the bare word
                            present), and every property BOTH sides pin a `const` on must
                            agree -- so a mis-ordered family is detected and the WHOLE family
                            refused rather than one row silently wrong.  This is the largest
                            key, 113 names, and it is what `aliases.py` is made of.
    word+identity           their word anywhere in our tree, identity gating.  This is how a
                            `$ref` is followed: their generator INLINES a referenced document
                            into the referring module, ours keeps the referenced document's
                            class, so the node is in a different document and only the word
                            plus the identity can find it.
    document+root-prefix    one document, one word, and the document ROOT's own word as a
                            prefix on one side only -- theirs says `VerifyBrandClaimPayload`
                            where ours says `Payload`, ours says
                            `GetAdCPCapabilitiesResponseAccount` where theirs says `Account`.
                            The hit must be UNIQUE in the document.
    union+value-set         they flattened an `anyOf` our tree keeps split.  For an
                            enumeration the gate is EQUALITY OF THE VALUE SET against the
                            union of ours -- `GetProductsField` is exactly
                            `FieldsItem | ProductResponseFieldsItem` and nothing less, which
                            is why the pool is the whole tree (those are two documents) and
                            why the cover must be exact in both directions.  **A UNION ALIAS
                            IS STILL A NAME**: it declares no class and reading 6's count does
                            not move.
    foreign                 their declaration is not in `adcp` at all.  `_str_enum.StrEnum`
                            dumps as `enum.StrEnum`, which their own module says it is, and
                            our generated enums subclass that very object -- so the re-export
                            is object-identical by construction and mints nothing.
    word-unique             their word, declared EXACTLY ONCE in our whole tree, where NO
                            document is known and their name IS their word.  The weakest key
                            and the most restricted: run without those two restrictions it
                            bound their `get-creative-delivery-response.json` `Creative` to
                            the capabilities document's, and their `Result` to
                            `ProvenanceVerificationItemResult`.  5 names, each listed in the
                            table with its identity corroboration, because this is the one
                            key an owner may want to read row by row.

AND A MODULE NO DOCUMENT STATES IS REFUSED WHOLE.  `adcp.types.registry` is generated from
`schemas/registry-openapi.yaml` and `adcp.types.core` is hand-written machinery; not one of
their names reaches a document ours compiles and not one has an identity of ours agreeing, so
a word firing on one of them (`ValidationResult`, which our `property` domain also happens to
declare) would be exactly the "identity equal under a word the bundle does not give" that
reading 10 refuses.  Decided per MODULE, because a wholly undocumented module's agreements are
coincidences of vocabulary.

AND IDENTITY IS A GATE ON A CANDIDATE, NEVER THE PROPOSAL.  Run as the sole key, identity
bound upstream's `Brand` to our `GetAdCPCapabilitiesResponse` (`alias_surface`'s own
measurement), because a one-field model's structure is shared by every other one-field
model.  So no key below starts from a signature; each starts from a document or a word and
reports identity as CORROBORATION -- `agrees`, `differs`, or `none`.

**A DIFFERING IDENTITY IS NOT A DIFFERENT SUBJECT WHERE THE DOCUMENT AND THE WORD BOTH
AGREE.**  Measured: our `core/product.json` root and theirs have different canonical schemas
(186 KB against 215 KB) while both compile the same document and both call it `Product`.
That disagreement is a fact about two EMISSIONS of one document -- a question for
`codegen/verify` -- and not evidence that `LegacyProduct` denotes something else.  Upstream's
own `legacy.py` says what it denotes: `from adcp.types.domains.core.product import Product as
LegacyProduct`.  The row is bound and the disagreement is counted and named.

**A NAME WITH NO SCHEMA SUBJECT GETS A REPORT AND NEVER A CLASS** (reading 10,
`adcp-client-python-cpiu`).  Upstream's `adcp.types.registry` is generated from
`schemas/registry-openapi.yaml` and upstream's `adcp.types.core` is a hand-written machinery
module; no document of the pinned bundle states either, so every name of theirs is refused
with that reason and the module raises it at the attribute.

THREE PHASES, because the two trees cannot be imported into one interpreter:

    # phase 1, on an interpreter carrying UPSTREAM -- `survey/structural_signature.py`'s own
    $UP/bin/python survey/structural_signature.py --dump $T/up.sig.json --side upstream \
        --relax null-arm,const-default,inline-refs

    # phase 2, on OURS.  The whole DECLARED tree and not only the public surface: an inner
    # shape reading 6 does not export is still a declaration an adapter may name.
    PYTHONPATH=.:src ./.venv/bin/python survey/adapter_surface.py --dump-ours $T/our.json

    # phase 3, the join, the report and the modules
    PYTHONPATH=.:src ./.venv/bin/python survey/adapter_surface.py \
        --ours $T/our.json --upstream $T/up.sig.json \
        --table survey/adapter-surface-9.6.1.tsv --write src/adcp/types
"""

from __future__ import annotations

import argparse
import ast
import collections
import importlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import structural_signature as ss  # noqa: E402

OUR_GEN = "adcp.types._schemas"
THEIR_GEN = "adcp.types.domains"
#: ``codegen.bundle.PROJECTIONS`` by ``survey/dropin/_dropin.py``'s own reading: a projection
#: re-cuts a document's nodes for one transport and is not a document to emit, so their
#: generator's path for one names a document we DO compile, at its canonical path.
PROJECTIONS = ("bundled", "mcp")

#: The relaxations both dumps must have been taken at.  Named here so a dump taken strict is
#: refused rather than joined -- ``structural_signature.main``'s own rule.
RELAX = ("const-default", "inline-refs", "null-arm")


# --------------------------------------------------------------------------- phase 1: ours


def dump_ours(out_path: Path) -> None:
    """Every class our tree DECLARES, with its signature, its public paths and its branches.

    **THE WHOLE DECLARED TREE AND NOT THE PUBLIC SURFACE**, which is the one way this dump
    differs from `structural_signature.dump`'s.  Reading 6 exports a document's ROOT, its
    union BRANCHES and its type ALIASES and no inner shape -- correctly, since a surface
    exporting all of them would make `core.Status` mean one of fourteen things -- but an
    inner shape is still a declaration, and upstream's `capabilities.py` imports 55 of them
    straight out of their generated tree under their own words.  A dump restricted to the
    public surface cannot see those rows at all, so it reports them absent when they are
    merely unexported, which is `V1-FOLD-UNEXPORTED` and a different verdict.

    `public` records which public `(module, name)` pairs reach each declaration, so the
    writer can prefer a public path and the report can say when only a private one exists.
    """
    import pkgutil

    ss.RELAX.update(dict.fromkeys(RELAX, True))
    root = importlib.import_module("adcp.types")
    gen = importlib.import_module(OUR_GEN)
    modules = [m.name for m in pkgutil.walk_packages(gen.__path__, OUR_GEN + ".")]
    public = [
        m.name
        for m in pkgutil.iter_modules(root.__path__, "adcp.types.")
        if not m.name.rpartition(".")[2].startswith("_")
    ]

    declarations: dict[str, dict] = {}
    unreadable: dict[str, str] = {}

    def add(mod_name: str, word: str, obj: object) -> None:
        key = f"{mod_name}.{word}"
        if key in declarations:
            return
        method, schema, note = ss.signature(obj)
        branch = obj.__dict__.get("_branch_models") or () if isinstance(obj, type) else ()
        declarations[key] = {
            "word": word,
            "module": mod_name,
            "method": method,
            "note": note,
            "sig": ss._digest(schema) if schema is not None else "",  # noqa: SLF001
            "schema": ss._canon(schema) if schema is not None else "",  # noqa: SLF001
            "branches": [f"{b.__module__}.{b.__qualname__}" for b in branch],
            "public": [],
        }

    def record(mod_name: str, mod: object) -> None:
        for attr, obj in list(vars(mod).items()):
            if isinstance(obj, type) and getattr(obj, "__module__", None) == mod_name:
                add(mod_name, obj.__qualname__, obj)
        # **A TYPE ALIAS IS A DECLARATION AND IS NOT A CLASS.**  §1 exports "every document
        # ROOT, every union BRANCH and every type ALIAS", and `core/property-id.json`
        # compiles to `PropertyID = Annotated[...]` -- no class object at all.  A dump that
        # read only classes reported `core.property_id` as a document we do not compile,
        # which is false and is the sort of absence this whole exercise exists to stop
        # inventing.  `__all__` is the module's own statement of what it declares.
        for word in getattr(mod, "__all__", None) or ():
            obj = getattr(mod, word, None)
            if obj is not None and not isinstance(obj, type):
                add(mod_name, word, obj)

    for mod_name in modules:
        try:
            record(mod_name, importlib.import_module(mod_name))
        except BaseException as exc:  # noqa: BLE001 -- the payload is the report
            unreadable[mod_name] = f"{type(exc).__name__}: {exc}"
    for mod_name in public + ["adcp.types._base", "adcp.types._runtime"]:
        try:
            mod = importlib.import_module(mod_name)
        except BaseException as exc:  # noqa: BLE001
            unreadable[mod_name] = f"{type(exc).__name__}: {exc}"
            continue
        record(mod_name, mod)
        for attr, obj in list(vars(mod).items()):
            if attr.startswith("_") or not isinstance(obj, type):
                continue
            key = f"{getattr(obj, '__module__', '')}.{getattr(obj, '__qualname__', '')}"
            if key in declarations:
                declarations[key]["public"].append([mod_name, attr])

    out_path.write_text(
        json.dumps(
            {
                "side": "ours",
                "relaxations": {k: True for k in RELAX},
                "modules": len(modules) + len(public),
                "unreadable": unreadable,
                "declarations": declarations,
            },
            indent=1,
        )
    )
    kinds = collections.Counter(r["method"] for r in declarations.values())
    print(
        f"ours: {len(declarations)} DECLARATIONS over {len(modules)} private and "
        f"{len(public)} public modules; by method {dict(kinds)}; "
        f"{sum(1 for r in declarations.values() if r['public'])} reachable publicly; "
        f"{sum(1 for r in declarations.values() if r['branches'])} union roots; "
        f"{len(unreadable)} unreadable -> {out_path}"
    )


# --------------------------------------------------------------------------- the census


def module_scope_imports(tree: ast.Module) -> list[ast.ImportFrom]:
    """Every `ImportFrom` that RUNS when the module is imported.

    Not inside a function or class body -- everything else is module scope, including a
    top-level `if TYPE_CHECKING:`, `try:`/`except ImportError:` or `with`.  Measured: reading
    only `tree.body` finds 760 of the 1,423 pairs and misses `adcp/__init__.py` entirely,
    whose 260 are inside a guarded block and whose absence is the largest cascade in the
    tree.
    """
    out: list[ast.ImportFrom] = []

    def walk(body: list[ast.stmt]) -> None:
        for node in body:
            if isinstance(node, ast.ImportFrom):
                out.append(node)
            elif isinstance(node, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                for attr in ("body", "orelse", "finalbody"):
                    walk(getattr(node, attr, None) or [])
                for handler in getattr(node, "handlers", None) or []:
                    walk(handler.body)

    walk(tree.body)
    return out


def census(src: Path) -> dict:
    """Every module-scope `(module, name)` import from `adcp.types*`, with its resolution.

    `src/adcp/types/` is EXCLUDED: the type layer importing itself is not the machinery's
    demand on it, and the question is what upstream's kept code asks of our surface.
    """
    pkg = src / "adcp"
    excluded = pkg / "types"
    pairs: list[tuple[str, str, str]] = []
    for path in sorted(pkg.rglob("*.py")):
        if excluded in path.parents:
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        here = path.relative_to(src).with_suffix("").parts
        for node in module_scope_imports(tree):
            mod = node.module or ""
            if node.level:
                base = list(here[: len(here) - node.level])
                mod = ".".join([*base, mod]) if mod else ".".join(base)
            if mod != "adcp.types" and not mod.startswith("adcp.types."):
                continue
            for alias in node.names:
                if alias.name != "*":
                    pairs.append((str(path.relative_to(src)), mod, alias.name))

    buckets: dict[str, list] = {
        "resolving": [],
        "missing_module": [],
        "missing_name": [],
        "other": [],
    }
    cache: dict[str, object] = {}
    for file, mod, name in pairs:
        if mod not in cache:
            try:
                cache[mod] = importlib.import_module(mod)
            except BaseException as exc:  # noqa: BLE001
                cache[mod] = exc
        held = cache[mod]
        if isinstance(held, BaseException):
            if isinstance(held, ModuleNotFoundError) and held.name == mod:
                buckets["missing_module"].append([file, mod, name])
            else:
                buckets["other"].append([file, mod, name, f"{type(held).__name__}: {held}"])
            continue
        try:
            getattr(held, name)
        except AttributeError:
            buckets["missing_name"].append([file, mod, name])
        except BaseException as exc:  # noqa: BLE001
            buckets["other"].append([file, mod, name, f"{type(exc).__name__}: {exc}"])
        else:
            buckets["resolving"].append([file, mod, name])
    return {"total": len(pairs), **buckets}


#: The marker a module of ours sets to say it restates upstream's words rather than declaring
#: a subject (`survey/alias_surface.MODULE_MARKER`).  Every adapter this script writes carries
#: it, and :func:`demand` reads it -- which is what makes the script IDEMPOTENT.
MARKER = "__adcp_restates_upstream__"

#: The two alias layers of ours, whose decisions are an OUTPUT of this project and never an
#: input to the demand.  `compat` is `survey/alias_surface.py`'s and is upstream of this
#: script; `_adapter` is this script's own.
ALIAS_LAYERS = ("adcp.types.compat", "adcp.types._adapter")


def demand(c: dict) -> dict[tuple[str, str], list[str]]:
    """Every (module, name) pair this ADAPTER owes, measured and idempotent.

    **A PAIR SERVED BY AN ADAPTER OF OURS IS STILL A DEMAND ON THE ADAPTER.**  Run naively
    the second time, the census finds the modules this script wrote and reports the demand
    EMPTY -- and the writer then truncates every one of them, which is exactly what happened
    once and is why this function exists.  So a module carrying :data:`MARKER` is read as "an
    adapter of ours answers here", its pairs re-enter the demand, and the run is a function
    of the measurement rather than of the tree's current contents.

    `adcp.types.compat` is EXCLUDED: `survey/alias_surface.py` decides those names, and a
    second instrument re-deciding them would be two answers to one question.  A flat name
    that resolves through `_adapter` is re-demanded by the same rule read one layer up.
    """
    out: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for file, mod, name in c["missing_module"] + c["missing_name"]:
        out[(mod, name)].append(file)
    adapters = set()
    for _, mod, _ in c["resolving"]:
        if mod in adapters or mod in ALIAS_LAYERS:
            continue
        try:
            held = importlib.import_module(mod)
        except BaseException:  # noqa: BLE001
            continue
        if getattr(held, MARKER, None) is not None:
            adapters.add(mod)
    flat = None
    try:
        flat = importlib.import_module("adcp.types._adapter")
    except BaseException:  # noqa: BLE001
        pass
    for file, mod, name in c["resolving"]:
        if mod in adapters or (mod == "adcp.types" and flat is not None and name in flat.__all__):
            out[(mod, name)].append(file)
    return out


def print_census(c: dict) -> None:
    blocked = c["missing_module"] + c["missing_name"]
    print(f"total module-scope pairs from adcp.types*   {c['total']}")
    print(f"  resolving                                 {len(c['resolving'])}")
    print(f"  blocked: the MODULE does not exist        {len(c['missing_module'])}")
    print(f"  blocked: the NAME is absent from it       {len(c['missing_name'])}")
    print(f"  other failure (adcp.types.domains.**)     {len(c['other'])}")
    print(f"  files with any blocked pair               {len({r[0] for r in blocked})}")
    for mod, n in collections.Counter(r[1] for r in blocked).most_common(16):
        print(f"      {n:5}  {mod}")


# --------------------------------------------------------------------------- phase 3: join


def their_document(module: str) -> str | None:
    """The bundle document upstream's declaring module names, dotted, or `None`."""
    if not module.startswith(THEIR_GEN + "."):
        return None
    rest = module[len(THEIR_GEN) + 1 :]
    head, _, tail = rest.partition(".")
    if head in PROJECTIONS and tail:
        rest = tail
    return rest


def consts(schema: str) -> dict[str, object]:
    """Every root property this schema pins a `const` on -- the discriminator and its kin.

    The ordinal key's second gate.  A union's arms are told apart by what they pin, so two
    arms claimed to be the same arm must agree wherever both pin something; where neither
    pins anything the gate is silent and says so.
    """
    try:
        root = (json.loads(schema) or {}).get("root") or {}
    except ValueError:
        return {}
    props = root.get("properties")
    if not isinstance(props, dict):
        return {}
    return {k: v["const"] for k, v in props.items() if isinstance(v, dict) and "const" in v}


class Join:
    def __init__(self, ours: dict, theirs: dict) -> None:
        assert theirs.get("version") not in (None, "", "unknown"), (
            "the upstream dump records no version, and every row below is a claim about one"
        )
        assert sorted(k for k, v in (theirs.get("relaxations") or {}).items() if v) == sorted(
            RELAX
        ), theirs.get("relaxations")
        assert sorted(k for k, v in (ours.get("relaxations") or {}).items() if v) == sorted(
            RELAX
        ), ours.get("relaxations")
        self.ours, self.theirs = ours, theirs
        self.version = theirs["version"]
        self._values: dict[str, frozenset[str]] = {}
        self._roots: dict[str, str] = {}

        self.their_modules = {m for r in theirs["declarations"].values() for m in r["modules"]}
        self.at: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
        self.their_word: dict[str, set[str]] = collections.defaultdict(set)
        self.by_their_sig: dict[str, list[str]] = collections.defaultdict(list)
        for key, row in theirs["declarations"].items():
            for mod in row["modules"]:
                for name in row["names"]:
                    self.at[(mod, name)].append(key)
            if row["sig"]:
                self.by_their_sig[row["sig"]].append(key)
            mod = self.declaring(key)
            if mod and key.startswith(mod + "."):
                self.their_word[mod].add(key[len(mod) + 1 :])
        for keys in self.by_their_sig.values():
            keys.sort(key=lambda k: (not k.startswith(THEIR_GEN + "."), k))

        D = ours["declarations"]
        self.by_doc: dict[str, list[str]] = collections.defaultdict(list)
        self.by_word: dict[str, list[str]] = collections.defaultdict(list)
        self.by_sig: dict[str, list[str]] = collections.defaultdict(list)
        self.in_module: dict[str, dict[str, str]] = collections.defaultdict(dict)
        for key, row in D.items():
            self.in_module[row["module"]][row["word"]] = key
            self.by_word[row["word"].lower()].append(key)
            if row["sig"]:
                self.by_sig[row["sig"]].append(key)
            if row["module"].startswith(OUR_GEN + "."):
                self.by_doc[row["module"][len(OUR_GEN) + 1 :]].append(key)

    def root_of(self, doc: str) -> str:
        """The word OUR tree gives that document's ROOT, derived from the document's path.

        §1 derives a module's path from the document's and the root's name from the same
        words, so the root is the camel-cased last segment -- matched case-insensitively
        against the module's own declarations so an acronym's casing
        (`get_adcp_capabilities_response` -> `GetAdCPCapabilitiesResponse`) comes from the
        tree rather than from a table of acronyms here.
        """
        if doc in self._roots:
            return self._roots[doc]
        plain = "".join(p.title() for p in doc.rpartition(".")[2].split("_"))
        words = self.in_module.get(OUR_GEN + "." + doc, {})
        self._roots[doc] = next((w for w in words if w.lower() == plain.lower()), "")
        return self._roots[doc]

    def declaring(self, key: str) -> str:
        mod = key
        while mod and mod not in self.their_modules:
            mod = mod.rsplit(".", 1)[0] if "." in mod else ""
        return mod

    def public(self, key: str) -> list[str] | None:
        paths = self.ours["declarations"][key]["public"]
        if not paths:
            return None
        return sorted(paths, key=lambda p: (len(p[0]), p[0], p[1]))[0]

    # -- the ordinal key, family by family and never row by row
    def ordinal(self, doc: str, stem: str, n: int) -> tuple[str | None, str]:
        family = set()
        for mod in self.their_word:
            if their_document(mod) == doc:
                family |= {w for w in self.their_word[mod] if re.fullmatch(re.escape(stem) + r"\d*", w)}
        root_key = self.in_module.get(OUR_GEN + "." + doc, {}).get(stem)
        branches = self.ours["declarations"][root_key]["branches"] if root_key else []
        if not branches:
            return None, f"no union root of ours spells {stem!r} in {doc}"
        if stem not in family or len(family) != len(branches) + 1:
            return None, (
                f"their {stem!r} family is {len(family)} and our branches are "
                f"{len(branches)}: not one root plus its arms"
            )
        if not 1 <= n <= len(branches):
            return None, f"{stem}{n} is outside our {len(branches)} arms"
        # the second gate: every property BOTH sides pin must agree, for the WHOLE family
        for i, branch in enumerate(branches, start=1):
            mine = consts(self.ours["declarations"][branch]["schema"])
            theirs = {}
            for key, row in self.theirs["declarations"].items():
                if f"{stem}{i}" in row["names"] and their_document(self.declaring(key)) == doc:
                    theirs = consts(row["schema"])
                    break
            shared = set(mine) & set(theirs)
            bad = {k for k in shared if mine[k] != theirs[k]}
            if bad:
                return None, (
                    f"arm {i} of {stem} disagrees on {sorted(bad)}: ours "
                    f"{ {k: mine[k] for k in bad} } theirs { {k: theirs[k] for k in bad} }"
                )
        return branches[n - 1], f"arm {n} of {len(branches)}, consts agree"

    def enum_values(self, key: str) -> frozenset[str] | None:
        row = self.ours["declarations"][key]
        if row["method"] != "enum":
            return None
        if key not in self._values:
            try:
                vals = json.loads(row["schema"])["root"].get("enum") or []
                self._values[key] = frozenset(json.dumps(v) for v in vals)
            except (ValueError, KeyError, TypeError):
                self._values[key] = frozenset()
        return self._values[key] or None

    def union(self, their_schema: str) -> list[str] | None:
        """The enumerations of ours whose value sets UNION to theirs EXACTLY, or nothing.

        **THE POOL IS THE WHOLE TREE AND NOT ONE DOCUMENT**, because the two sides of a
        flattened `anyOf` need not live in one: `GetProductsField` is their generator's fold
        of `media_buy/get-products-request.json`'s own `FieldsItem` with the field list the
        product response states, and those are two documents.  It is still bounded: only an
        enumeration whose values are a SUBSET of theirs can be a member of a union equal to
        theirs, which takes the candidates from 751 to a handful, and the cover must be
        EXACT in both directions -- a union that merely contains their values is a different
        admissible set and is refused.
        """
        import itertools

        try:
            want = frozenset(json.dumps(v) for v in (json.loads(their_schema)["root"].get("enum") or []))
        except (ValueError, KeyError, TypeError):
            return None
        if len(want) < 2:
            return None
        pool = {}
        for key in self.ours["declarations"]:
            vals = self.enum_values(key)
            if vals and vals < want:
                pool[key] = vals
        for size in (2, 3):
            for combo in itertools.combinations(sorted(pool), size):
                if frozenset().union(*(pool[k] for k in combo)) == want:
                    return list(combo)
        return None

    def resolve(self, mod: str, name: str) -> dict:
        row: dict = {"module": mod, "name": name}
        keys = self.at.get((mod, name)) or []
        if not keys:
            # Upstream's flat namespace resolves every name through `_eager`, and their
            # PRIVATE modules are not on the surface `structural_signature` walks at all -- so
            # for both the name is looked for across their whole dump and accepted only where
            # ONE declaration carries it.  Several is an ambiguity this script will not pick
            # between, and none means the name is not a type of theirs and was never measured.
            keys = [k for k, r in self.theirs["declarations"].items() if name in r["names"]]
            if len(keys) > 1 and mod != "adcp.types":
                row["verdict"] = "UPSTREAM-AMBIGUOUS"
                row["candidates"] = keys[:4]
                return row
        if not keys and mod.rpartition(".")[2].startswith("_"):
            row["verdict"] = "UPSTREAM-PRIVATE-MODULE-NOT-A-TYPE"
            return row
        if not keys:
            row["verdict"] = "UNRESOLVABLE-UPSTREAM"
            return row
        keys.sort(key=lambda k: (not k.startswith(THEIR_GEN + "."), k))
        key = keys[0]
        their = self.theirs["declarations"][key]
        # **A NAME WHOSE DECLARATION IS NOT IN `adcp` AT ALL IS THE STANDARD LIBRARY'S.**
        # Their `_str_enum.StrEnum` dumps as `enum.StrEnum`, which is what their own module
        # says it is on this interpreter ("if sys.version_info >= (3, 11): from enum import
        # StrEnum as StrEnum"), and our generated enums subclass that very object.  So the
        # re-export is OBJECT-IDENTICAL by construction and mints nothing; the key is the
        # declaring module being outside this package, read off the dump and not listed.
        if key and not key.startswith("adcp."):
            foreign_mod, _, foreign_word = key.rpartition(".")
            row.update(
                verdict="BOUND",
                how="foreign",
                their_declaring=key,
                method=their["method"],
                target=[key],
                public=[[foreign_mod, foreign_word]],
                identity="same object",
                note=f"{key} is not declared in adcp at all",
            )
            return row
        their_mod = self.declaring(key)
        word = key[len(their_mod) + 1 :] if their_mod and key.startswith(their_mod + ".") else ""
        doc = their_document(their_mod)
        # **UPSTREAM'S OWN IDENTITY SAYS WHICH DOCUMENT, where their declaring module does
        # not.**  Their `aliases.py`, `_forward_compat.py` and `versioned_bases/` declare a
        # name whose `__module__` names no document -- a type alias, a versioned restatement
        # -- and for those the document is recovered from ANOTHER declaration OF THEIRS with
        # the SAME SIGNATURE whose module IS a document's.  The key is upstream's tree
        # agreeing with itself, which is the one place exact identity is not a cross-tree
        # claim at all, and it only ever supplies the DOCUMENT: ours is still chosen by a
        # word or an identity below.
        # **GATED ON UNIQUENESS WITHIN THEIR OWN TREE**, because without it an almost-empty
        # model relocates to whatever else is almost empty: measured, their
        # `base.AdCPBaseModel` landed on `brand_discovery`'s `DefaultLanguage` and their
        # `core.Protocol` enum on `a2ui/si-catalog.json`'s `Type`.  One signature carried by
        # exactly ONE declaration of theirs in a document module is not a coincidence of that
        # kind; several is, and the row says so instead.
        if doc is None and their["sig"]:
            alts = [a for a in self.by_their_sig.get(their["sig"], []) if their_document(self.declaring(a))]
            if len(alts) == 1:
                doc = their_document(self.declaring(alts[0]))
                word = alts[0].rsplit(".", 1)[1]
                row["document_via"] = alts[0]
            elif alts:
                row["document_via_refused"] = f"{len(alts)} declarations of theirs share that signature"
        row.update(their_declaring=key, method=their["method"], document=doc, word=word)
        in_doc = self.by_doc.get(doc or "", [])
        root_word = self.root_of(doc) if doc else ""

        def bind(how: str, target, note: str = "") -> dict:
            tgts = target if isinstance(target, list) else [target]
            sigs = {self.ours["declarations"][t]["sig"] for t in tgts}
            row.update(
                verdict="BOUND",
                how=how,
                target=tgts,
                note=note,
                identity=(
                    "agrees"
                    if len(tgts) == 1 and their["sig"] and sigs == {their["sig"]}
                    else "union" if len(tgts) > 1 else "differs" if their["sig"] else "none"
                ),
                public=[self.public(t) for t in tgts],
            )
            return row

        # 1 / 2: the document, and the word the document gives
        if doc and word:
            exact = self.in_module.get(OUR_GEN + "." + doc, {}).get(word)
            if exact:
                return bind("document+word", exact)
            recased = [k for k in in_doc if self.ours["declarations"][k]["word"].lower() == word.lower()]
            if recased:
                return bind("document+word-recased", recased[0])

        # 3: the document proposes every declaration it makes, identity gates
        if doc and their["sig"]:
            gate = [k for k in in_doc if self.ours["declarations"][k]["sig"] == their["sig"]]
            if gate:
                return bind("document+identity", gate[0], f"{len(gate)} candidates agreed")

        # 4: their generator's collision suffix, by position in the document's own order
        suffix = re.fullmatch(r"(.*?)(\d+)", word or "")
        if doc and suffix:
            target, why = self.ordinal(doc, suffix.group(1), int(suffix.group(2)))
            if target:
                return bind("document+ordinal", target, why)
            row["ordinal_refused"] = why

        # 5: their word anywhere, identity gating -- this is how a `$ref` is followed
        if word and their["sig"]:
            gate = [
                k
                for k in self.by_word.get(word.lower(), [])
                if self.ours["declarations"][k]["sig"] == their["sig"]
            ]
            if gate:
                return bind("word+identity", gate[0], f"{len(gate)} candidates agreed")

        # 6: one document, one word, THE ROOT'S PREFIX ON ONE SIDE ONLY.  Both emitters
        # disambiguate an inner node by prefixing the document ROOT's word, and they do it on
        # different nodes: theirs says `VerifyBrandClaimPayload` where ours says `Payload`,
        # ours says `GetAdCPCapabilitiesResponseAccount` where theirs says `Account`.  The
        # prefix is the ROOT'S OWN WORD and nothing else is allowed to be stripped, so this
        # is one document, one word, and a prefix both sides derive from that document.
        if doc and word and root_word:
            # The prefix is the root's own word, or that word without the `Request`/`Response`
            # the document's path puts there: their `verify-brand-claim-response.json`
            # prefixes its nodes `VerifyBrandClaim` and ours leaves them bare (`Payload`), so
            # the stem is the prefix on that document and the full word is on others.  Two
            # forms, both read off the ROOT, and a hit must be UNIQUE in the document.
            stems = {root_word, re.sub(r"(Request|Response)$", "", root_word)}
            prefixed = {s + word for s in stems} | {
                word[len(s) :] for s in stems if word.startswith(s) and word != s
            }
            hit = [k for k in in_doc if self.ours["declarations"][k]["word"] in prefixed - {word}]
            if len(hit) == 1:
                return bind("document+root-prefix", hit[0], f"root word {root_word!r}")
            if len(hit) > 1:
                row["prefix_refused"] = f"{len(hit)} declarations of ours carry a prefixed form"

        # 7: they flattened a union we keep split
        if their["method"] == "enum":
            members = self.union(their["schema"])
            if members:
                return bind("union+value-set", members, "value sets union to theirs exactly")

        # 8: their word, declared EXACTLY ONCE in our whole tree.  Their generator INLINES a
        # `$ref`'s target into the referring module and ours keeps the referenced document's
        # class, so the node is in a different document and the document key cannot reach it
        # (`sync-accounts-response`'s `CreditLimit` is `core/account.json`'s).  One word with
        # one declaration behind it is not the ambiguity a word key is warned about -- the
        # warning is about a word MANY classes carry -- so uniqueness is the gate and the
        # identity is reported beside it.
        # **AND ONLY WHERE NO DOCUMENT IS KNOWN AND THEIR NAME IS THEIR WORD.**  Measured
        # unrestricted, it bound their `get-creative-delivery-response.json`'s `Creative` to
        # the one `Creative` our tree declares -- which is the CAPABILITIES document's -- and
        # their `get-principal-response.json`'s `Result` to `ProvenanceVerificationItemResult`.
        # Where the document IS known, a word in a DIFFERENT document is a cross-document
        # claim and `word+identity` above is the key that is allowed to make it.  Where their
        # name differs from their word they are asserting a refinement of one class, and
        # which refinement is a reading and not a uniqueness.
        if word and name == word and doc is None and len(self.by_word.get(word.lower(), [])) == 1:
            only = self.by_word[word.lower()][0]
            return bind("word-unique", only, "the only declaration of that word in our tree")

        row["identity_anywhere"] = (self.by_sig.get(their["sig"]) or [])[:3]
        if their["method"] == "none":
            row["verdict"] = "NOT-A-TYPE"
        elif doc and in_doc:
            row["verdict"] = "DOCUMENT-NO-WORD-NO-IDENTITY"
        elif doc:
            row["verdict"] = "DOCUMENT-WE-DO-NOT-COMPILE"
        else:
            row["verdict"] = "NO-DOCUMENT-NO-SUBJECT"
        return row


# --------------------------------------------------------------------------- the modules

#: **UPSTREAM'S `adcp.types.base` IS OUR `adcp.types.envelopes` AND NO TABLE SAYS SO.**  The
#: owner's ruling states the equivalence; the KEYS find it, which is the difference between an
#: adapter and a list.  `AdCPBaseModel`, `AdcpRequest`, `AdcpResponse` and `FailedResponse` are
#: each declared exactly once in our tree under exactly upstream's word, so `word-unique`
#: binds all four with nothing written here.  The three envelope words are added to that
#: module's `__all__` whether or not the measured demand asks for them, because the module
#: upstream published carries them and an adapter for a module owes the module's own names.
BASE_OWES = ("AdcpRequest", "AdcpResponse", "FailedResponse")


HEADER = '''"""{title}

**GENERATED by `survey/adapter_surface.py` -- do not edit.**  Regenerate with the three
commands in that file's docstring.

**AN ALIAS IS A NAME AND NEVER A SECOND TYPE.**  Every statement below is a re-export, so
the object reached here IS the object the walk emitted from the document: `isinstance` holds
across both spellings and nothing here declares a class, so reading 6's count of
declarations does not move.{example}

**WHY THIS MODULE EXISTS AT UPSTREAM'S OWN PATH.**  `adcp.types.compat` is reading 10's ONE
module for a flat spelling, and it is enough for an application that writes
`from adcp.types import <Name>`.  It is not enough for upstream's own kept machinery, which
writes `from {module} import <Name>` at MODULE SCOPE -- so an absent module takes the whole
importing file and, through `adcp/__init__.py`, the top-level public API with it.  This
module is that import satisfied, and it is derived from the demand rather than listed.

A name upstream's module carried that no document of the pinned bundle states is NOT
invented here: it raises from `__getattr__` with the reason, which is reading 10's "a name
with no schema subject gets a migration note and never a class" said at the import that asks
for it.
"""

from __future__ import annotations

#: This module restates upstream's words and declares no subject of its own, so every survey
#: that walks our surface skips it -- the marker is the declaration and not a list kept
#: elsewhere (`survey/alias_surface.py`'s own `MODULE_MARKER`).
__adcp_restates_upstream__ = "adcp {version}"
'''

#: **A NAMED TRIPLE AND NOT A TEMPLATE**, which is the sentence obeying its own clause:
#: "a path a consumer can type is a claim about the artifact, so only a path that RESOLVES
#: can be checked" (`tests_emit/test_prose_resolves.py`).  A `<placeholder>` is the one
#: spelling no import can grade, so the example names a row of THIS module's own table and a
#: module with no bound name gets no example at all.
EXAMPLE = """

The triple, read off this module's own table::

    {module}.{word} is {target}.{inner}

so `from {module} import {word}` and `from {target} import {inner}` are two spellings of one
object, and `isinstance` holds against either."""

REFUSAL = '''

#: **THE NAMES THIS MODULE CANNOT SERVE, each with the reason it cannot.**  Reading 10: "a
#: name with no schema subject gets a migration note and never a class".  Served as an
#: `AttributeError` carrying the reason, so `from {module} import X` fails where the name has
#: no subject and says WHY, rather than resolving to something that silently is not what the
#: caller asked for.
__adcp_refused__ = {refused}


def __getattr__(name: str) -> object:
    why = __adcp_refused__.get(name)
    if why is None:
        raise AttributeError(f"module {{__name__!r}} has no attribute {{name!r}}")
    raise AttributeError(
        f"{{__name__}}.{{name}} is upstream's and has no subject in the pinned bundle: {{why}}. "
        f"See docs/migration-from-upstream.md"
    )
'''


def write_modules(rows: list[dict], out: Path, version: str) -> dict[str, tuple[int, int]]:
    """One module per upstream module the demand names, with its names and its refusals.

    **A MODULE OF OURS IS NEVER OVERWRITTEN.**  `adcp.types.core` is a domain module of ours
    AND the name of a hand-written machinery module of theirs, and the domain module is
    EMITTED -- `codegen/emit.py` writes it from the compiler's own record of what it
    exported, and a gate reads it byte for byte.  So where their path is already ours, ours
    wins and the names only theirs carried are reported rather than served; see
    `survey/dropin/_dropin.py`'s "where a path is ours, ours wins", read here at file
    granularity because this writes FILES and not a loader.

    The FLAT namespace is written to `_adapter.py` for the same reason: `adcp.types`'s own
    `__init__` is the package, it is hand-written on purpose ("a package's own `__init__` IS
    the package, so it is bound before `__path__` is consulted"), and it resolves a flat name
    through a module rather than carrying a list.
    """
    by_module: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by_module[row["module"]].append(row)
    written: dict[str, tuple[int, int]] = {}
    for module, group in sorted(by_module.items()):
        leaf = "_adapter" if module == "adcp.types" else module.rpartition(".")[2]
        target = out / f"{leaf}.py"
        if module != "adcp.types" and target.exists():
            written[module] = (0, 0)
            continue
        statements: list[str] = []
        unions: list[str] = []
        names: list[str] = []
        refused: dict[str, str] = {}
        for row in sorted(group, key=lambda r: r["name"]):
            if row["verdict"] != "BOUND":
                refused[row["name"]] = row["verdict"]
                continue
            paths = [
                tuple(p) if p else tuple(k.rsplit(".", 1))
                for p, k in zip(row["public"], row["target"])
            ]
            if len(paths) == 1:
                mod, word = paths[0]
                statements.append(f"from {mod} import {word} as {row['name']}")
            else:
                # **A UNION ALIAS IS STILL A NAME.**  The arms are imported under private
                # words and joined, so nothing is declared and every arm is the object the
                # walk emitted -- `get_args` over the alias returns them by identity.
                for i, (mod, word) in enumerate(paths):
                    statements.append(f"from {mod} import {word} as _arm{i}_{row['name']}")
                arms = " | ".join(f"_arm{i}_{row['name']}" for i in range(len(paths)))
                unions.append(f"{row['name']} = {arms}")
            names.append(row["name"])
        if module == "adcp.types.base":
            # The module upstream published carries the three envelope words whether or not
            # the measured demand asks for them, and an adapter for a module owes the
            # module's own names.  `word-unique` is the key; `BASE_OWES` is the demand.
            for word in BASE_OWES:
                if word not in names:
                    statements.append(f"from adcp.types.envelopes import {word} as {word}")
                    names.append(word)
        example = ""
        if names:
            first = sorted(names)[0]
            row = next(r for r in group if r["name"] == first)
            path = row["public"][0] or row["target"][0].rsplit(".", 1)
            example = EXAMPLE.format(module=module, word=first, target=path[0], inner=path[1])
        body = HEADER.format(
            title=f"Upstream's `{module}`, served from our surface.",
            module=module,
            version=version,
            example=example,
        )
        # **THE IMPORTS COME FIRST AND THE UNIONS AFTER**, which is not cosmetic: a union
        # alias names the arms it joins, so one `sorted()` over both kinds put
        # `GetProductsField = _arm0... | _arm1...` above the lines that bind the arms and the
        # module raised `NameError` at import.
        body += "\n" + "\n".join(sorted(set(statements))) + "\n"
        if unions:
            body += "\n" + "\n".join(sorted(set(unions))) + "\n"
        body += "\n__all__ = [\n" + "".join(f'    "{n}",\n' for n in sorted(names)) + "]\n"
        body += REFUSAL.format(
            module=module,
            refused="{\n" + "".join(f'    "{k}": "{v}",\n' for k, v in sorted(refused.items())) + "}",
        )
        target.write_text(body)
        written[module] = (len(names), len(refused))
    return written


# --------------------------------------------------------------------------- main


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dump-ours", type=Path, metavar="PATH")
    parser.add_argument("--src", type=Path, default=HERE.parent / "src")
    parser.add_argument("--census", action="store_true")
    parser.add_argument("--census-json", type=Path, metavar="PATH")
    parser.add_argument("--ours", type=Path, metavar="PATH")
    parser.add_argument("--upstream", type=Path, metavar="PATH")
    parser.add_argument("--table", type=Path, metavar="PATH")
    parser.add_argument("--report", type=Path, metavar="PATH")
    parser.add_argument("--write", type=Path, metavar="DIR")
    args = parser.parse_args()

    if args.dump_ours:
        dump_ours(args.dump_ours)
        return
    if args.census or args.census_json:
        c = census(args.src)
        print_census(c)
        if args.census_json:
            args.census_json.write_text(json.dumps(c, indent=0))
        if not args.ours:
            return
    if not (args.ours and args.upstream):
        parser.error("the join needs --ours and --upstream")

    c = census(args.src)
    join = Join(json.loads(args.ours.read_text()), json.loads(args.upstream.read_text()))
    owed = demand(c)
    rows = []
    for (mod, name), files in sorted(owed.items()):
        row = join.resolve(mod, name)
        row["files"] = sorted(set(files))
        row["pairs"] = len(files)
        rows.append(row)

    # **A MODULE OF THEIRS NO DOCUMENT OF THE BUNDLE STATES IS REFUSED WHOLE**, and the test
    # is the rows themselves: not one of its names reaches a document ours compiles, and not
    # one has an identity of ours agreeing.  `adcp.types.registry` is generated from
    # `schemas/registry-openapi.yaml` and `adcp.types.core` is hand-written machinery -- so a
    # word key firing on one of their names (`ValidationResult`, which our `property` domain
    # also happens to declare) would be the "identity equal under a word the bundle does not
    # give" that reading 10 refuses.  Decided per MODULE because the subject is the module's:
    # a wholly undocumented module's agreements are coincidences of vocabulary.
    per_module: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        per_module[row["module"]].append(row)
    for module, group in per_module.items():
        if module == "adcp.types":
            continue
        if any(r.get("document") or r.get("identity") in ("agrees", "same object") for r in group):
            continue
        for row in group:
            if row["verdict"] == "BOUND":
                row.update(
                    verdict="MODULE-HAS-NO-BUNDLE-SUBJECT",
                    refused_binding={"how": row.pop("how"), "target": row.pop("target")},
                )

    print(f"upstream adcp {join.version}; demand {len(rows)} names over "
          f"{sum(r['pairs'] for r in rows)} pairs")
    for verdict, n in collections.Counter(r["verdict"] for r in rows).most_common():
        print(f"  {verdict:30} {n:5} names  "
              f"{sum(r['pairs'] for r in rows if r['verdict'] == verdict):5} pairs")
    print("  BOUND by key:")
    for how, n in collections.Counter(r.get("how") for r in rows if "how" in r).most_common():
        print(f"      {how:24} {n:5}")
    print("  identity, as corroboration and never as the proposal:")
    for i, n in collections.Counter(
        r.get("identity") for r in rows if r["verdict"] == "BOUND"
    ).most_common():
        print(f"      {i:24} {n:5}")
    private = [r for r in rows if r["verdict"] == "BOUND" and None in (r.get("public") or [1])]
    print(f"  bound to a class our surface DECLARES but does not EXPORT: {len(private)}")

    if args.table:
        cols = ("module", "name", "verdict", "how", "identity", "document", "word",
                "their_declaring", "target", "public", "pairs", "note")
        with args.table.open("w") as fh:
            fh.write(f"# survey/adapter_surface.py over upstream adcp {join.version}\n")
            fh.write("\t".join(cols) + "\n")
            for row in rows:
                fh.write("\t".join(str(row.get(c, "")).replace("\t", " ") for c in cols) + "\n")
        print(f"  table -> {args.table}")
    if args.report:
        args.report.write_text(json.dumps({"version": join.version, "rows": rows}, indent=1))
    if args.write:
        written = write_modules(rows, args.write, join.version)
        for module, n in sorted(written.items()):
            print(f"  wrote {module:34} {n[0]:5} names, {n[1]:4} refused")


if __name__ == "__main__":
    main()
