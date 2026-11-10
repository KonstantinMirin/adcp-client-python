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

AND WHICH DECLARATION OF THEIRS A PAIR DENOTES IS PRIOR TO EVERY KEY, SO IT IS DECIDED BY
IDENTITY AND NEVER BY A SPELLING (:meth:`Join.denoted`, `adcp-client-python-sj14`).  The
dump indexes a declaration by its `names` and its `modules`, which it records as two
INDEPENDENT lists, so the index built over them is a CROSS PRODUCT and for 94 pairs of 9.6.1
it offers more than one candidate: `core/format.json`'s `Format` is `LegacyFormat` in the
flat namespace and `Format` in its own module, and the product therefore claims that
declaration at `('adcp.types', 'Format')`, where upstream's runtime answers with
`canonical_creative`'s canonical class instead.  The pairing is not recoverable from the
dump -- both candidates are models and both carry the word -- and the tie-break that stood
in for it, prefer their generated tree then alphabetical, decided 33 of the 94 wrong.  So
the subject is read off UPSTREAM'S OWN STATEMENT, confirmed against the dump's own
candidates for that pair, and reported in its own column (`pair_ambiguous`); the keys below
are unchanged and are asked about the declaration that reading names.

THIRTEEN KEYS, each reported as itself because "what the key was read off" is the first thing
a disagreement about a row turns out to be about.  `survey/alias_surface.py`'s two are the
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
    restored-module+word    their declaring module names no document and is OUR tree's file
                            at UPSTREAM'S OWN BYTES (`upstream_machinery.restored_paths`), so
                            the subject is upstream's own declaration and not a candidate to
                            be found.  Keyed on the MODULE their own statement names, which
                            is why the `canonical_creative` restore -- which makes `Creative`
                            and `CreativeManifest` declared twice -- does not tie it the way
                            it ties `word-unique`.  Only where no document is known, so
                            `core/format.json`'s `Format` still beats their hand-written one.
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
    document+pointer-identity   THE POINTERS THE DOCUMENT STATES.  The pool is
                            :meth:`Join.pointer_pool` -- every declaration of ours the
                            document states, inline at a pointer of its own or through a
                            `$ref` THAT DOCUMENT states -- and the gate is schema equality,
                            unique in the pool.  This is the key the `$ref` hop needed and
                            `word+identity` could only reach when the two trees happened to
                            agree on the word: `ExperimentalFeature` is
                            `core/experimental-feature-id.json` at
                            `#/properties/experimental_features/items`, and our word for it
                            is `ExperimentalFeatureID`.
    document+pointer-structure  the same pool, selected by the DOCUMENT'S OWN STRUCTURE
                            (:func:`shape`) where the two emissions disagree about a leaf
                            nobody read off the document: their `Accreditation` and our
                            `AccreditationsItem` are one items node and differ only in what
                            each generator added to `evidence_url`.  Property names, nesting
                            and enumerated values only; unique in the pool; silent where the
                            structure names nothing (:func:`names_nothing`).

    document+pointer-constraint THE DOCUMENT'S CONSTRAINED-SCALAR POSITIONS, where our tree
                            declares NOTHING and the two keys above therefore have no
                            candidate to gate.  The pool is §3a's L1 catalogue --
                            ``codegen.catalogue.collect_scalars``, the compiler's own record
                            of the symbol it lowered at each pointer -- and the selector is
                            the document's own node against their canonical root schema,
                            annotations dropped.  `AcceptancePolicyProfileId` is
                            `core/acceptance-policy-profile-ids.json` at `/items`, which our
                            walk lowers to `constraints.StrMinLen1`.  Unique in the DOCUMENT,
                            which is the gate that does the work: a constraint set carries no
                            name, so the type cannot discriminate and only the position can.

**AND NO POINTER KEY READS A LETTER OF EITHER SIDE'S SPELLING, which is what keeps them
from binding two unrelated subjects.**  `Accreditation`/`AccreditationsItem` and
`Metric`/`MetricsItem` look like suffix artefacts and are not matched as any; the pool is
bounded by ONE document -- their own declaring module's -- and by the references that
document states, and a tie refuses the row (`pointer_refused`) instead of picking.  A key
that matched on spelling would bind two subjects the first time two documents shared a word.

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
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import structural_signature as ss  # noqa: E402
import upstream_aliases as ua  # noqa: E402
import upstream_machinery as um  # noqa: E402

OUR_GEN = "adcp.types._schemas"
THEIR_GEN = "adcp.types.domains"
#: **WHERE A TYPE DERIVED FROM A CONSTRAINT LIVES, and it is not under a document.**
#: ``adcp.types.constraints``' own first paragraph: "A type derived from a CONSTRAINT belongs
#: to no document, so there is no such module for it and it lives here instead, public".
#: Named here because key 12's target is a symbol of that module and of no other.
OUR_CONSTRAINTS = "adcp.types.constraints"
#: **THE CROSS-DOMAIN FLAT SURFACE, which is a public home the per-domain scan cannot see.**
#: :func:`dump_ours` reads public paths off ``pkgutil.iter_modules(adcp.types)``, which returns
#: the 23 domain aggregators and skips every ``_``-prefixed child -- so ``codegen/emit.py``'s
#: own consolidation contributed no ``public`` pair, although every word in its ``__all__`` is
#: reachable at ``adcp.types.<word>`` through the facade's ``__getattr__``.
#:
#: Measured, on the run that needed it: the positional-name ruling (``581b5924f``) withheld
#: ``GetContentStandardsResponseBranch0`` from ``adcp.types.content_standards``, and that was
#: the only public home recorded for ``content_standards/get-content-standards-response.json``'s
#: first branch -- so this writer went on importing a word its own surface no longer carries
#: and the import raised, taking 14 of ``tests_emit`` with it on one cause.  The DECLARATION
#: was never withheld: it is published flat, under the word ``GetContentStandardsResponse1``.
OUR_FLAT = "adcp.types._surface._flat"
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
    #: **WHICH DECLARATION AN OBJECT ON A PUBLIC MODULE IS, BY IDENTITY.**  A class answers
    #: that with `__module__` and `__qualname__`; a type ALIAS has neither, so the public
    #: path of `core/experimental-feature-id.json`'s root was invisible and the adapter
    #: imported it from `adcp.types._schemas` -- a PRIVATE path, in a generated module whose
    #: whole purpose is to be the supported spelling.  A re-export binds the same object, so
    #: `id()` is the reading, and it is exact where equality would not be: two `Annotated`
    #: aliases over one type compare equal and are different declarations.
    by_id: dict[int, str] = {}

    def add(mod_name: str, word: str, obj: object) -> None:
        key = f"{mod_name}.{word}"
        if key in declarations:
            return
        by_id.setdefault(id(obj), key)
        method, schema, note = ss.signature(obj)
        branch = obj.__dict__.get("_branch_models") or () if isinstance(obj, type) else ()
        # **THE DOCUMENT AND THE POINTER THE CLASS ITSELF CARRIES**, which is this project's
        # own statement of what a declaration IS (`adcp.types._base.SchemaRef`) and the one
        # fact about a declaration that is neither a word nor a signature.  Off `__dict__`
        # and not `getattr`, because a subclass inherits its base's ref and would report a
        # pointer no document states for it.  A declaration that is not a class carries
        # none: a root type ALIAS binds its ref at MODULE scope and a nested one binds none
        # at all (`codegen/render.py`), so attributing the module's ref to every alias in
        # `__all__` would hand several declarations one pointer.
        ref = obj.__dict__.get("__adcp_schema__") if isinstance(obj, type) else None
        declarations[key] = {
            "word": word,
            "module": mod_name,
            "method": method,
            "note": note,
            "ref": list(ref) if isinstance(ref, tuple) else None,
            "sig": ss._digest(schema) if schema is not None else "",  # noqa: SLF001
            "schema": ss._canon(schema) if schema is not None else "",  # noqa: SLF001
            "branches": [f"{b.__module__}.{b.__qualname__}" for b in branch],
            "public": [],
        }

    def record(mod_name: str, mod: object) -> None:
        # **AN ADAPTER OF OURS DECLARES NOTHING, SO NOTHING IS RECORDED FROM IT.**  The
        # class arm below is already safe -- a re-exported class still names its own
        # `__module__` -- but a type ALIAS has no module of its own, so the `__all__` arm
        # recorded `adcp.types.capabilities.ExperimentalFeature` as a DECLARATION the moment
        # this writer bound that name, and the next run's word and signature indexes then
        # carried its own last output as a candidate.  Measured: one declaration on the run
        # after the write, and the count is stable across two runs with this clause.
        if getattr(mod, MARKER, None) is not None:
            return
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
        # **A MODULE'S OWN `__adcp_schema__` IS ITS ROOT'S, AND WHOSE IT IS IS GATED ON
        # UNIQUENESS.**  A root with a class says so itself; an ENUM root and a scalar ALIAS
        # root have nowhere to put a `ClassVar`, so `codegen/render.py` binds the ref at
        # MODULE scope beside `strict_validate` -- `enums/specialism.py` is
        # `__adcp_schema__ = SchemaRef('enums/specialism.json', '#')` and
        # `class AdCPSpecialism(StrEnum)`.  Attributed only where no declaration of the
        # module already claims the root pointer and exactly ONE carries no ref at all:
        # measured, `core/postal_area_support.py` holds the root `PostalAreaSupport` (which
        # claims `#` itself) beside the inner `PostalAreaSupportValueItem`, and an
        # ungated reading handed the inner enum the document's root pointer.
        mine = [k for k in declarations if declarations[k]["module"] == mod_name]
        at_root = getattr(mod, "__adcp_schema__", None)
        refless = [k for k in mine if declarations[k]["ref"] is None]
        if (
            isinstance(at_root, tuple)
            and len(refless) == 1
            and not any((declarations[k]["ref"] or [None, None])[1] == "#" for k in mine)
        ):
            declarations[refless[0]]["ref"] = list(at_root)

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
        # **AN ADAPTER OF OURS IS NOT A PUBLIC HOME FOR A DECLARATION.**  A module carrying
        # :data:`MARKER` restates upstream's words and declares nothing, so recording it as
        # a `public` path makes this writer's own last output an input to its next run: the
        # statement for `CpmAuctionPricingOption` named `adcp.types.compat` -- the OTHER
        # alias layer -- rather than the emitted `adcp.types.pricing_options`, which is one
        # adapter importing another and is a second answer to one question.  Measured: 31
        # rows of the table were reaching an alias layer that way, and all 31 now name the
        # module the compiler wrote -- the same rule `demand` reads one layer down, and what
        # makes a second run of the writer reproduce the first.
        if getattr(mod, MARKER, None) is None:
            for attr, obj in list(vars(mod).items()):
                if attr.startswith("_"):
                    continue
                key = (
                    f"{getattr(obj, '__module__', '')}.{getattr(obj, '__qualname__', '')}"
                    if isinstance(obj, type)
                    else by_id.get(id(obj), "")
                )
                if key in declarations:
                    declarations[key]["public"].append([mod_name, attr])

    # **AND THE FLAT WORD IS A PUBLIC PATH TOO, recorded at the spelling a consumer writes**
    # (:data:`OUR_FLAT`).  The module itself is private and its words are not: the facade
    # resolves every one of them at `adcp.types.<word>`, so the pair recorded is
    # `("adcp.types", word)` and never the `_surface` path.  Ranked LAST by `Join.public`, so
    # a declaration a domain publishes keeps its domain spelling and this reaches only the
    # declarations no domain carries.
    try:
        flat = importlib.import_module(OUR_FLAT)
    except BaseException as exc:  # noqa: BLE001 -- the payload is the report
        unreadable[OUR_FLAT] = f"{type(exc).__name__}: {exc}"
    else:
        for attr in getattr(flat, "__all__", ()):
            obj = getattr(flat, attr, None)
            key = (
                f"{getattr(obj, '__module__', '')}.{getattr(obj, '__qualname__', '')}"
                if isinstance(obj, type)
                else by_id.get(id(obj), "")
            )
            if key in declarations:
                declarations[key]["public"].append(["adcp.types", attr])

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


def upstream_files(prefix: str, rev: str | None = None) -> frozenset[Path]:
    """The paths under `prefix` that are UPSTREAM'S FILES -- their path, at their commit.

    `survey/upstream_machinery.restored_paths` answers a DIFFERENT question over the
    `types/` modules and answers it by blob identity, because a path in there may hold OUR
    emitted module under a name upstream also used; that clause is untouched and still
    governs `src/adcp/types/` in :func:`corpus`.

    **THE VERDICT HERE IS THE PATH AND NOT THE BYTES, and the measurement is why**
    (`adcp-client-python-2f52`'s first commit).  Blob identity was the reading, and this
    project repairs upstream's own tests -- 53 files of `tests/` now differ from upstream's
    at the pin, every one of them by a commit of ours.  Each one dropped out of the corpus,
    so the demand it makes on this adapter went invisible, so the next run TRUNCATED the
    name it needs: `adcp.types.legacy.LegacyPreviewCreativeBatchResponse` is asked for at
    module scope by `tests/test_preview_html.py` and by nothing else in the corpus, the
    writer dropped it, and two of upstream's test modules then failed to COLLECT -- which is
    the exact failure this clause's own docstring says the `tests/` widening exists to
    prevent ("a pair the census cannot see is a collection error the gate reports and the
    table does not mention").

    An edit of OURS to upstream's test does not make the IMPORT ours: the file is still
    upstream's test asking upstream's question of this surface, and a repair to its fixtures
    neither adds nor removes a `from adcp.types import X`.  So the population is the paths
    upstream has at the pin, and a file upstream does not have -- a test of ours, under
    `tests_emit/` or added here -- is still outside it.
    """
    rev = rev or um.rows()[0]
    listing = um.git("ls-tree", "-r", rev, "--", prefix)
    root = HERE.parent
    out = set()
    for line in listing.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob":
            here = root / path
            if here.is_file():
                out.add(here.resolve())
    return frozenset(out)


def corpus(src: Path, suite: Path | None = None) -> list[Path]:
    """**UPSTREAM'S OWN CODE, SELECTED BY PROVENANCE AND NEVER BY PATH**
    (`adcp-client-python-6qlc`).

    The question this instrument answers is what upstream's KEPT code asks of our surface,
    and the corpus was drawn by path: `src/adcp/` with `src/adcp/types/` cut out.  Two
    measurements say that boundary is in the wrong place, and both are widenings:

    * **`src/adcp/types/` holds upstream's restored files.**  6qlc's reading.  The reasoning
      for cutting the subtree is sound for OUR emitted surface -- the type layer importing
      itself says nothing about a consumer's demand -- and false the moment one of upstream's
      own modules is restored into it, because that file is a CONSUMER of the adapter
      surface and the instrument was structurally unable to see what it asks for.  So the
      test is provenance: a file under `types/` is in the corpus iff its bytes are
      upstream's (`survey/upstream_machinery.restored_paths`), which self-adjusts as the
      restore lane lands modules and keeps every emitted module of ours out.
    * **`tests/` is upstream's whole suite, and it was not read at all.**  Measured on this
      tree: 246 of `tests/**/*.py` import `adcp.types*` at module scope and 192
      `(module, name)` pairs are asked ONLY from there -- so the largest single block of
      demand on this adapter was invisible to the instrument that exists to measure it.  And
      that suite is the GRADE: a pair the census cannot see is a collection error the gate
      reports and the table does not mention.

    Neither clause reads a module name or a directory name, which is the whole point: the
    corpus is "upstream's own code, as upstream's own objects name it".  The two clauses ask
    provenance in the two different ways their two questions need, and
    :func:`upstream_files`' own docstring is the measurement that separated them: under
    `types/` a path may hold OUR emitted module, so the test is the BYTES; under `tests/`
    every path is upstream's test file, and this project's own repairs to 53 of them were
    silently deleting the demand those files make.
    """
    pkg = src / "adcp"
    inside_types = pkg / "types"
    restored = um.restored_paths()
    out: list[Path] = []
    for path in sorted(pkg.rglob("*.py")):
        if inside_types not in path.parents or path.resolve() in restored:
            out.append(path)
    if suite is not None and suite.is_dir():
        theirs = upstream_files(f"{suite.name}/")
        out += [p for p in sorted(suite.rglob("*.py")) if p.resolve() in theirs]
    return out


def census(src: Path, suite: Path | None = None) -> dict:
    """Every module-scope `(module, name)` import from `adcp.types*`, with its resolution.

    The corpus is :func:`corpus` -- upstream's own code, selected by provenance.  A pair is
    keyed by the file that asks for it so the report can say WHICH of upstream's files a
    missing name takes, and resolved live so the demand is exactly the set that does not
    already work.
    """
    pairs: list[tuple[str, str, str]] = []
    for path in corpus(src, suite):
        #: A relative import is resolved against the asking file's OWN package, so the
        #: anchor is the import root the file sits under -- `src/` for the package and the
        #: repository root for the suite, whose `tests.foo` is a top-level module.  One
        #: derivation per file rather than one for the whole corpus, because the corpus now
        #: spans two roots.
        anchor = src if src in path.parents else HERE.parent
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        here = path.relative_to(anchor).with_suffix("").parts
        for node in module_scope_imports(tree):
            mod = node.module or ""
            if node.level:
                base = list(here[: len(here) - node.level])
                mod = ".".join([*base, mod]) if mod else ".".join(base)
            if mod != "adcp.types" and not mod.startswith("adcp.types."):
                continue
            for alias in node.names:
                if alias.name != "*":
                    pairs.append((str(path.relative_to(anchor)), mod, alias.name))

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
    #: **AND THE `other` BUCKET IS DEMAND TOO.**  A pair whose module raises something that
    #: is not `ModuleNotFoundError(mod)` was dropped from the demand entirely, and the three
    #: readings of why it raised are all demand: `adcp.types.versioned_bases.v31` fails
    #: because its PARENT package is absent, so the error names `versioned_bases` and not
    #: the module asked for; `adcp.types.domains.bundled.protocol...` fails because the
    #: mirror's prefix substitution finds no `_schemas.bundled`.  Measured: 8 pairs upstream's
    #: own suite asks for had no row of the table at all, for no reason except which
    #: exception the import raised.  The pair is what the file asks for, however the import
    #: failed.
    out: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for row in c["missing_module"] + c["missing_name"] + c["other"]:
        file, mod, name = row[0], row[1], row[2]
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


#: The keywords a STRUCTURE is read off, split by how draft-07 spells what they hold.  Three
#: tuples and not a walk of every key, because the whole point is that everything NOT named
#: here is dropped: `minLength`, `maxLength`, `format`, `default`, `description`, `title`,
#: `examples` and `uniqueItems` are what the two generators add on their own authority, and
#: they are exactly where two emissions of ONE document disagree.
SHAPE_LEAF = ("type", "enum", "const")
SHAPE_BY_NAME = ("properties", "patternProperties", "definitions")
SHAPE_IN_LIST = ("oneOf", "anyOf", "allOf", "prefixItems")
SHAPE_ONE = ("items", "additionalProperties", "contains", "additionalItems")


def shape(node: object) -> tuple:
    """**THE DOCUMENT'S OWN STRUCTURE AT A NODE**: its names, its nesting, its values.

    The identity key asks whether two emissions produced the same schema; this asks the
    weaker and more durable question -- whether they describe the same NODE OF THE DOCUMENT
    -- and it is the only reading that survives two generators disagreeing about a leaf.
    Measured: upstream's `Accreditation` says `evidence_url` is `{"format": "uri",
    "minLength": 1}` and ours says `{"format": "uri", "maxLength": 2048}`; the document
    itself says `{"type": "string", "format": "uri"}` and neither emitter is quoting it.
    The property NAMES, the nesting and the enumerated VALUES are the document's own
    vocabulary and no generator invents them, so they are what is kept.

    Recursive and position-keyed: a branch is identified by its index in the list, a
    property by its name, so two nodes with the same names in a different arrangement do not
    agree.  Sorted where the document holds a BAG (`properties`) and in order where it holds
    a LIST (`oneOf`), which is the same split `codegen.bundle.subschemas` reads off the
    descent table.
    """
    if isinstance(node, bool):
        return ("bool", node)
    if not isinstance(node, dict):
        return ("scalar",)
    out: list[tuple] = []
    for keyword in SHAPE_LEAF:
        if keyword in node:
            held = node[keyword]
            out.append(
                (keyword, tuple(sorted(map(repr, held))) if isinstance(held, list) else repr(held))
            )
    for keyword in SHAPE_BY_NAME:
        held = node.get(keyword)
        if isinstance(held, dict):
            out.append((keyword, tuple(sorted((k, shape(v)) for k, v in held.items()))))
    for keyword in SHAPE_IN_LIST:
        held = node.get(keyword)
        if isinstance(held, list):
            out.append((keyword, tuple(shape(v) for v in held)))
    for keyword in SHAPE_ONE:
        if keyword in node:
            out.append((keyword, shape(node[keyword])))
    if isinstance(node.get("required"), list):
        out.append(("required", tuple(sorted(node["required"]))))
    return tuple(out)


def root_shape(canon: str) -> tuple:
    """:func:`shape` of a dump's canonical schema, which carries the node under `root`."""
    try:
        return shape((json.loads(canon) or {}).get("root"))
    except ValueError:
        return ()


def admits(node: dict) -> tuple[tuple[str, object], ...]:
    """A scalar node as the keywords that decide what it ADMITS, sorted.

    §3a's identity rule read over one node: ``codegen.catalogue.ANNOTATIONS`` -- `title`,
    `description`, `examples`, `default`, `$comment`, `deprecated` -- are dropped "because
    an annotation does not change what a node admits", and so is every ``x-`` extension,
    which `core/acceptance-policy-profile-ids.json`'s ``x-entity`` is one of.  What is left
    is the type word, the ``format`` and the bounds, which is exactly the key §3a's L1 layer
    is collected on -- so a node of the DOCUMENT and a canonical root schema of UPSTREAM'S
    reduce to the same tuple when the two describe one acceptance.

    Flat on purpose: this is a SCALAR's reading, and a node with any nested keyword
    (``properties``, ``items``, ``oneOf``) reduces to a tuple no constrained-scalar position
    can equal, so key 12 is silent there rather than wrong.
    """
    from codegen import catalogue as _catalogue

    return tuple(
        sorted(
            (k, json.dumps(v, sort_keys=True))
            for k, v in node.items()
            if k not in _catalogue.ANNOTATIONS and not k.startswith(("x-", "$"))
        )
    )


def names_nothing(sh: tuple) -> bool:
    """A structure with no NAMES and no VALUES cannot tell two subjects apart.

    The one guard the structure key needs, and it is measured rather than cautionary: every
    scalar alias of a document dumps as `{"type": "string"}` once the leaf keywords are
    dropped, so `core/experimental-feature-id.json`, `core/domain-name.json`,
    `core/country-code.json` and four more share one structure.  The key is silent there and
    identity -- which separates all seven -- is what binds them.
    """
    return not ({k for k, _ in sh} & {"properties", "patternProperties", "definitions", "enum"})


class Join:
    def __init__(
        self,
        ours: dict,
        theirs: dict,
        bundle_dir: Path | None = None,
        aliases: ua.Oracle | None = None,
    ) -> None:
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
        #: **UPSTREAM'S OWN SOURCE, FOR THE NAMES THEIR RUNTIME CANNOT ANSWER FOR**
        #: (`survey/upstream_aliases.py`).  Optional, because the keys below are complete
        #: without it and a run that has no git object to read still produces every row it
        #: produced before; where it IS supplied, a name upstream BINDS rather than declares
        #: stops being `NO-DOCUMENT-NO-SUBJECT` and becomes the document and the word their
        #: own statement names.
        self.aliases = aliases
        self._values: dict[str, frozenset[str]] = {}
        self._roots: dict[str, str] = {}
        self._shapes: dict[str, tuple] = {}
        self._pools: dict[str, dict[str, str]] = {}
        #: :meth:`restored_declarations`' answer, taken once; see that method for why it is
        #: not read in this constructor.
        self._restored: frozenset[tuple[str, str]] | None = None
        #: :meth:`scalar_pool`'s collection, taken once over the whole bundle.
        self._scalars: dict[str, dict[str, tuple[tuple[tuple[str, object], ...], str]]] | None = (
            None
        )
        self.bundle_dir = bundle_dir
        #: The bundle's own documents, dotted as a module path is, so a document named in
        #: these rows is turned back into the PATH the bundle holds it at without a second
        #: spelling rule -- `sponsored_intelligence.si_capabilities` is a document only
        #: because `sponsored-intelligence/si-capabilities.json` is a file.
        self.documents: dict[str, str] = {}
        if bundle_dir is not None:
            from codegen import bundle as _bundle

            for path in _bundle.portable(bundle_dir):
                self.documents[path[: -len(".json")].replace("-", "_").replace("/", ".")] = path

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

    def restored_declarations(self) -> frozenset[tuple[str, str]]:
        """``(module, word)`` for every declaration of ours sitting at UPSTREAM'S OWN BYTES.

        The intersection of two readings neither of which this function makes: the PATHS
        where upstream's own hand-written file is on disk byte for byte
        (:func:`survey.upstream_machinery.restored_paths`, blob identity against the commit
        the classification pins) and the declarations :func:`dump_ours` walked out of our
        live tree.  A module is in iff its file is upstream's; a word is in iff that module
        declares it.  Nothing is listed, so a module the restore lane lands tomorrow joins
        this set on the next run and a module whose bytes drift leaves it in the same breath.

        Keyed on the module and not on the word, which is the whole of why it is not
        :meth:`by_word`'s uniqueness with the gate relaxed -- see key 8.

        Cached on the instance beside the other indexes rather than computed in
        ``__init__``: the reading takes a ``git ls-tree`` and a row of the classification
        table, and a ``Join`` built to resolve one row owes neither.
        """
        if self._restored is not None:
            return self._restored
        prefix = "adcp.types."
        here = HERE.parent / "src" / "adcp" / "types"
        restored = {
            prefix + p.relative_to(here).with_suffix("").as_posix().replace("/", ".")
            for p in um.restored_paths()
        }
        self._restored = frozenset(
            (row["module"], row["word"])
            for row in self.ours["declarations"].values()
            if row["module"] in restored
        )
        return self._restored

    def is_restored(self, key: str) -> bool:
        """Is that declaration of ours upstream's own, in a file carrying upstream's bytes?

        The same reading as :meth:`restored_declarations`, asked of one candidate -- which is
        what the word keys need, because their question is "may this candidate be PROPOSED by
        a word" and not "which module did their statement name".
        """
        row = self.ours["declarations"].get(key)
        return row is not None and (row["module"], row["word"]) in self.restored_declarations()

    def shape_of(self, key: str) -> tuple:
        if key not in self._shapes:
            self._shapes[key] = root_shape(self.ours["declarations"][key]["schema"])
        return self._shapes[key]

    def root_declaration(self, doc: str) -> str | None:
        """The declaration of ours that document's ROOT compiles to, by its POINTER.

        `__adcp_schema__` is the class's own answer and `#` is the root pointer, so a class
        says this about itself.  A root type ALIAS carries no class attribute to say it with
        (`codegen/render.py` binds its ref at module scope), and for those the root is the
        word :func:`root_of` derives from the document's own path -- the derivation already
        in this file, not a second one.
        """
        path = self.documents.get(doc)
        for word, key in self.in_module.get(OUR_GEN + "." + doc, {}).items():
            ref = self.ours["declarations"][key].get("ref")
            if ref and list(ref) == [path, "#"]:
                return key
            if ref is None and word == self.root_of(doc):
                return key
        return None

    def pointer_pool(self, doc: str) -> dict[str, str]:
        """**EVERY DECLARATION OF OURS THE DOCUMENT STATES, AND THE POINTER THAT STATES IT.**

        Upstream's generator and ours read ONE document and disagree about where a node's
        class goes, in exactly one way: at a `$ref` theirs INLINES the referenced document
        into the referring module and ours keeps the referenced document's own class.  So
        the subjects a document states are of two kinds, and both are pointers IN THAT
        DOCUMENT:

        * a node the document declares inline -- ours is the declaration in the document's
          own module, carrying that pointer in its `__adcp_schema__`;
        * a node the document states a `$ref` at -- ours is the ROOT declaration of the
          document referenced, and the pointer is where the reference stands.

        `codegen.bundle.references` is the reference census, which is the project's one walk
        over the descent table, and `document_for` resolves a reference's URI to the
        document the bundle holds -- so the pool is read off the DOCUMENT and not off either
        tree's module graph.  A reference at a RULE position is kept here deliberately: the
        pool is a candidate set gated below, not a claim that a type was lowered.

        Returns our declaration key -> the pointer in `doc` that reaches it.  Empty when no
        bundle was given, which makes the keys that read it silent rather than wrong.
        """
        if doc in self._pools:
            return self._pools[doc]
        pool: dict[str, str] = {}
        path = self.documents.get(doc)
        if self.bundle_dir is None or path is None:
            self._pools[doc] = pool
            return pool
        from codegen import bundle as _bundle

        for key in self.by_doc.get(doc, []):
            ref = self.ours["declarations"][key].get("ref")
            pool[key] = ref[1] if ref and ref[0] == path else ""
        document = _bundle.read(self.bundle_dir, path)
        for pointer, uri, _position in _bundle.references(document):
            target = _bundle.document_for(uri, list(self.documents.values()))
            if not target:
                continue
            dotted = target[: -len(".json")].replace("-", "_").replace("/", ".")
            root = self.root_declaration(dotted)
            if root is not None and root not in pool:
                pool[root] = pointer or "#"
        self._pools[doc] = pool
        return pool

    def scalar_pool(self, doc: str) -> dict[str, tuple[tuple[tuple[str, object], ...], str]]:
        """**EVERY CONSTRAINED-SCALAR POSITION THE DOCUMENT STATES, AND WHAT WE LOWERED IT TO.**

        ``pointer -> (what the position admits, the symbol ``adcp.types.constraints``
        declares for it)``, for the one document.  The source is §3a's L1 catalogue read
        exactly as ``codegen/emit.py`` reads it -- ``catalogue.collect_scalars(bundle,
        constraints.SPELLING's keywords, constraints.symbol)`` -- so the symbol at a pointer
        is the compiler's own answer and not a derivation of this script's.

        One collection for the whole bundle, cached, because the layer is a reading of the
        BUNDLE and not of a document (that module's own sentence) and 568 documents state
        one.  Empty when no bundle was given, which makes key 12 silent rather than wrong.
        """
        if self._scalars is None:
            self._scalars = collections.defaultdict(dict)
            if self.bundle_dir is not None:
                from codegen import catalogue as _catalogue
                from codegen import constraints as _constraints

                layer = _catalogue.collect_scalars(
                    self.bundle_dir,
                    frozenset(kw for kw, _ in _constraints.SPELLING),
                    _constraints.symbol,
                )
                for entry in layer.entries.values():
                    for at in entry.positions:
                        node = {"type": at.kind, **dict(at.constraints)}
                        if at.format is not None:
                            node["format"] = at.format
                        dotted = at.document[: -len(".json")].replace("-", "_").replace("/", ".")
                        self._scalars[dotted][at.pointer] = (admits(node), entry.name)
        return self._scalars.get(doc, {})

    def public(self, key: str) -> list[str] | None:
        """The public path to prefer for a declaration, or ``None`` where only a private one is.

        **A DOMAIN SPELLING BEATS THE FLAT ONE, which is the ordering and not the length.**
        ``adcp.types`` is the shortest module name on the surface, so the plain
        ``(len, name, word)`` sort made the flat word win for every declaration a domain also
        publishes -- which is the one answer this project has never given: the supported path
        for a declaration the bundle states is its DOMAIN's, and ``adcp.types.<word>`` is
        reading 10's compatibility spelling.  So the flat pair (:data:`OUR_FLAT`, recorded at
        ``adcp.types``) sorts last and reaches only the declarations no domain carries --
        ``content_standards/get-content-standards-response.json``'s first branch is the
        measured one, withheld from its domain by the positional-name ruling and still
        published flat.
        """
        paths = self.ours["declarations"][key]["public"]
        if not paths:
            return None
        return sorted(paths, key=lambda p: (p[0] == "adcp.types", len(p[0]), p[0], p[1]))[0]

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

    #: **A UNION OF ARMS IS A NAME FOR A UNION AND NEVER FOR AN ENUMERATION**, and the
    #: distinction is the KIND of the thing upstream published rather than the values it
    #: admits (`adcp-client-python-69mi`).  Measured, and it cost 105 of upstream's files
    #: and ~1,797 test functions: the writer bound `GetProductsField` to
    #: `FieldsItem | ProductResponseFieldsItem`, whose 53 admissible values are EXACTLY
    #: upstream's 53 -- derived both ways, with our two arms overlapping on
    #: `media_buy_support` and `overlay_support` -- and upstream's own
    #: `decisioning/_get_products_helpers.py:66` writes
    #: `frozenset(f.value for f in GetProductsField)`, which raises
    #: `TypeError: 'types.UnionType' object is not iterable` at MODULE SCOPE in a module
    #: `adcp/decisioning/__init__.py` imports.  So the whole `decisioning` package died at
    #: import over a name whose value set was right.
    #:
    #: **AND THE REPAIR IS NOT A DIFFERENT ARM.**  It was proposed that their
    #: `GetProductsField` is our 17-member `FieldsItem`, read off their comment's "38 + 17
    #: members"; their own next clause refutes it -- "the public ``GetProductsField`` alias
    #: resolves to a third, 53-member enum that the request never holds" -- and so does
    #: their runtime, where the name is `domains.media_buy.get_products_request.Field1`
    #: with 53 members.  Binding it to the 17 would take
    #: `_GET_PRODUCTS_FIELD_VALUES` from 53 values to 17 and move 36 of `Product`'s fields
    #: into that helper's `_PASSTHROUGH`, so a buyer asking for two fields would be sent
    #: thirty-eight more: a wire-behaviour change dressed as a name.
    #:
    #: **AND NO DECLARATION OF OURS IS THAT ENUMERATION, which is a fact about the
    #: DOCUMENT.**  `media-buy/get-products-request.json`'s `fields.items` is an `anyOf` of
    #: two enumerations, so the bundle states two and our tree lowers two; upstream's
    #: generator flattened the `anyOf` into one and deduplicated the two shared values.  A
    #: 53-member enumeration of ours would be a type with no node behind it, which reading
    #: 10 refuses outright.  So the row is REFUSED with the value-set agreement recorded as
    #: the finding, and what would serve the name is a lowering of that `anyOf` -- owed by
    #: whoever owns emission and not by an alias layer.
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

    # -- the fourteenth key: upstream's own statement, where their runtime carried no answer
    def stated(self, mod: str, name: str) -> dict | None:
        """**WHAT UPSTREAM'S OWN SOURCE SAYS THIS NAME IS, resolved to a subject of ours.**

        The thirteen keys above all start from upstream's RUNTIME dump, where a class says its
        own declaring module and word.  A name upstream BINDS rather than DECLARES says
        neither: `adcp.types.legacy.LegacyCreateMediaBuyResponse` is a union `TypeAlias`, so
        the dump recorded it with no module at all and the table's verdict was
        `NO-DOCUMENT-NO-SUBJECT` -- while their `legacy.py:85` states the document in one
        line.  So this key's proposal is READ off upstream's statement
        (`survey/upstream_aliases.Oracle.trace`) and its chain is reported beside the row as
        the evidence, which is what makes it a reading and not a guess.

        **AND IT RESOLVES NOTHING ITSELF.**  Every arm below ends in one of the thirteen keys
        above, re-entered at the name UPSTREAM'S OWN STATEMENT names -- so a binding this
        key reports was still decided by a document and a node, and the hazard the pointer
        keys exist to refuse (a word matched across the tree) is refused here too.  Three
        arms, because upstream's statement terminates in three different kinds of thing:

        * a **declaration** of theirs.  `self.resolve` is re-entered at their declaring
          module and their word -- the strong case, 86 rows, and `how` carries both halves
          (`upstream-source -> document+word`) so the report says which key actually bound it.
        * a **document ROOT union**: their generator's own `<Root> = <Root>1 | ... | <Root>N`
          inside a document's module.  Bound to OUR root declaration of that document, gated
          three ways -- the stem must be the word :meth:`root_of` derives for that document,
          every arm must bind through :meth:`ordinal` (which is itself gated on the family
          being one root plus its arms with every shared `const` agreeing), and the arm count
          must equal our branch count.  A union whose stem is NOT the document's root is an
          inner node and is refused here with that reason: `Refine1 | Refine2 | Refine3` is
          `media_buy/get-products-request.json`'s `refine` property and not its root.
        * a **plain union** they composed by hand, every arm of which resolves to exactly one
          subject of ours.  `PublisherPropertiesAll | PublisherPropertiesById |
          PublisherPropertiesByTag` is three declarations joined, and the alias is their
          three names under one -- which is what `union+value-set` already does for an
          enumeration, with the same rule that a partial cover refuses the whole row.

        **AND A DISCRIMINATED UNION IS REFUSED, WITH THE DISCRIMINATOR AS THE REASON.**
        Their `aliases.py:361` is `_Annotated[ImageAsset | ... | DaastTrackerAsset,
        Discriminator("asset_type")]`, and the bare union under that metadata admits a
        different set of documents from the discriminated one -- so porting the arms and
        dropping the `Discriminator` would publish their name over a type they did not
        write.  Reported (`stated_refused`) and left unbound, which is reading 10's rule
        said about an expression instead of about a name.
        """
        if self.aliases is None:
            return None
        terminal, chain = self.aliases.trace(mod, name)
        if not chain:
            return None
        evidence = {
            #: `` ;; `` and not `` | ``: a statement's own text is often a UNION, so a
            #: pipe separator made the chain unsplittable -- measured, the gate reading it
            #: back split `BuildCreativeResponse1 | BuildCreativeResponse2` into two links.
            "stated_by": " ;; ".join(str(s) for s in chain),
            "stated_terminal": f"{terminal.kind} {terminal.module}.{terminal.name}",
        }

        def refuse(why: str) -> dict:
            return {**evidence, "stated_refused": why}

        if terminal.kind in ("declared-class", "declared-function"):
            if (terminal.module, terminal.name) == (mod, name):
                return None  # upstream declares the asked name itself: nothing is aliased
            inner = self.resolve(terminal.module, terminal.name)
            if inner.get("verdict") != "BOUND":
                return refuse(
                    f"upstream declares it at {terminal.module}.{terminal.name}, which is "
                    f"{inner.get('verdict')}"
                )
            unpinned = self.unpinned(terminal, inner)
            if unpinned:
                return refuse(
                    f"their {terminal.name} pins {unpinned} and the subject it reaches "
                    f"({inner['target']}) pins nothing there: a name over a type that "
                    f"accepts what the document refuses is worse than an unbound name"
                )
            return {
                **inner,
                "module": mod,
                "name": name,
                "how": f"upstream-source -> {inner['how']}",
                **evidence,
            }

        if terminal.kind != "expression":
            return refuse(f"upstream's own tree says {terminal.kind}")
        if terminal.discriminator:
            return refuse(
                f"upstream's expression pins discriminator {terminal.discriminator!r}: the "
                "bare union under it admits a different set"
            )
        if terminal.annotated:
            return refuse("upstream's expression carries Annotated metadata to port")
        if not terminal.arms or any(arm.startswith("?") for arm in terminal.arms):
            return refuse(
                f"upstream's expression names no arms to resolve: {terminal.expression[:80]}"
            )

        document, stem = terminal.document, terminal.family_stem
        if stem and document:
            if stem != self.root_of(document):
                return refuse(
                    f"{stem!r} is not the word our tree gives {document}'s root "
                    f"({self.root_of(document)!r}): an inner union, not the document's own"
                )
            arms = [self.ordinal(document, stem, i) for i in range(1, len(terminal.arms) + 1)]
            bad = [why for target, why in arms if not target]
            if bad:
                return refuse(f"their root family does not join ours arm for arm: {bad[0]}")
            root = self.root_declaration(document)
            if root is None:
                return refuse(f"no root declaration of ours carries {document}'s root pointer")
            row = {"module": mod, "name": name, "document": document, "word": stem}
            return {
                **self._bound(row, "upstream-source+document-root", [root],
                              f"their {stem} is the union of all {len(terminal.arms)} arms of "
                              f"{document}, which is our root"),
                **evidence,
            }

        targets: list[str] = []
        for arm in terminal.arms:
            at, _ = self.aliases.trace(terminal.module, arm)
            if at.kind != "declared-class":
                return refuse(f"arm {arm!r} of their union is {at.kind} and not a declaration")
            inner = self.resolve(at.module, at.name)
            if inner.get("verdict") != "BOUND" or len(inner["target"]) != 1:
                return refuse(f"arm {arm!r} of their union is {inner.get('verdict')}")
            targets.append(inner["target"][0])
        row = {"module": mod, "name": name}
        return {
            **self._bound(row, "upstream-source+union", targets,
                          f"their {len(targets)} arms, each resolved to one subject of ours"),
            **evidence,
        }

    # -- WHICH DECLARATION THE PAIR DENOTES, where the dump offers more than one
    def denoted(self, mod: str, name: str, keys: list[str]) -> tuple[str, str]:
        """**WHICH of several declarations of theirs the name AT THAT MODULE denotes.**

        Every key below starts from a declaration of theirs -- its document, its word, its
        signature -- and :meth:`_by_dump` has to pick that declaration out of
        :attr:`at`.  **AND `at` IS A CROSS PRODUCT, so for some pairs it is not a reading at
        all.**  `structural_signature.dump` records a declaration's `names` and its
        `modules` as two INDEPENDENT lists -- `core/format.json`'s `Format` carries
        `names: ['LegacyFormat', 'Format']` and `modules: ['adcp.types',
        'adcp.types.domains.core.format', 'adcp.types.legacy']`, because it is `LegacyFormat`
        in the flat namespace and `Format` in its own module -- so the index built over the
        product claims that declaration at `('adcp.types', 'Format')`, where upstream's
        runtime answers with a different class entirely.  The pairing is not in the dump and
        cannot be recovered from it: both candidates are models, both carry that word, and
        nothing in either row says which the flat name is bound to.

        Measured on 9.6.1: **94 pairs carry more than one candidate**, 50 of them in the flat
        namespace, and the tie-break that stood here -- prefer `domains.`, then alphabetical
        -- decided every one of them on a MODULE PATH'S SPELLING.  `final-state.md` reading
        10 is about exactly this: "AN ALIAS IS KEYED ON A SCHEMA SUBJECT, NEVER ON A NAME.  A
        name resolves to a DIFFERENT class of ours depending on which upstream module the
        import came from".  33 of the 94 were decided WRONG, `adcp.types.Format` among them:
        it took `core/format.json`'s deprecated registered format, whose required pair is
        `format_id` + `name`, where upstream's `_eager.py:939` reads
        `Format = _canonical_creative.Format` and the required pair is `format_kind` +
        `params`.

        So the subject is read off UPSTREAM'S OWN STATEMENT (`survey/upstream_aliases`),
        which is the same oracle key 14 is made of and the one place upstream says, in its
        own source, which object a name of theirs is.  **AND BOTH READINGS MUST CONFIRM IT**:
        the statement's terminal has to be one of the dump's own candidates for the pair.
        Upstream's source can name a declaration their public surface does not carry at that
        module at all -- measured, `_eager` reaches `adcp.types.CreateMediaBuyRequest` and
        `adcp.types.UpdateMediaBuyRequest` through `_forward_compat`, a private module the
        dump never walked, and `adcp.types.Result` through
        `content_standards/validate-content-delivery-response.json`, whose declaration does
        not record the flat namespace among its modules -- and choosing a subject the dump
        does not corroborate is a different and larger claim than choosing among the
        candidates it offers.  Where the two readings disagree, or where upstream's statement
        terminates in anything but a declaration, this returns nothing and the dump's own
        order answers exactly as before; the row carries the reason either way.

        **AND IT IS NOT AN IDENTITY GATE ON THE DOCUMENT KEYS, which was measured and is
        wrong.**  Reading 10's identity belongs to the choice of SUBJECT, not to the
        agreement of two emissions about one document: this script's own standing ruling is
        that "a differing identity is not a different subject where the document and the word
        both agree" (`core/product.json` compiles to 186 KB here and 215 KB there, and both
        are `Product`).  Gating `document+word` on signature equality was run: 93 of its 131
        rows report `differs`, BOUND falls from 327 names to 267, and `LegacyProduct`,
        `LegacyFormat`, `LegacyPackage` and `LegacyProductFilters` -- the legacy spellings
        that are supposed to keep the deprecated subject reachable -- all go
        `DOCUMENT-NO-WORD-NO-IDENTITY`.  The defect is upstream of the keys, and so is the fix.

        Returns `(declaration, why)` where `declaration` is one of `keys`, or `("", why)`.
        """
        if self.aliases is None:
            return "", "no upstream source was read, so the dump's own order answers"
        terminal, chain = self.aliases.trace(mod, name)
        if terminal.kind not in ("declared-class", "declared-function"):
            return "", (
                f"upstream's own statement ends in {terminal.kind}, which names no "
                "declaration, so the dump's own order answers"
            )
        said = f"{terminal.module}.{terminal.name}"
        if said not in keys:
            return "", (
                f"upstream's own statement names {said}, which the dump does not record as "
                f"carrying {name!r} at {mod}: the dump's own order answers"
            )
        return said, (
            f"upstream's own statement names {said} -- "
            + " ;; ".join(str(s) for s in chain)
        )

    def unpinned(self, terminal: ua.Terminal, inner: dict) -> dict[str, object]:
        """**WHAT UPSTREAM'S DECLARATION PINS THAT THE SUBJECT IT REACHES DOES NOT.**

        The middle term of a composition is where this key can do real harm, and the
        structural lane measured the case: upstream's
        `media_buy/create_media_buy_response.json` arm `CreateMediaBuyResponse1` pins
        `status` to `'completed'`, and the subject `document+ordinal` reaches for it --
        our `CreateMediaBuySuccess` -- has no `status` element at all.  25 of their 26
        elements agree.  Publishing their `CreateMediaBuySuccessResponse` over that subject
        would mint a NAME over a type that accepts payloads the document refuses, which is
        worse than leaving the name unbound.

        So this key refuses where upstream pins a property and the subject pins NOTHING
        there, and names the property.  Asymmetric on purpose, and the asymmetry is the
        whole reading: a DISAGREEMENT about a pinned value is what :meth:`ordinal`'s second
        gate already catches, and this is the other half -- a pin present on one side only,
        where that gate is silent because the intersection is empty.  Those are wire facts
        owed by whoever owns branch lowering and they are not words to alias around.

        Read off the two dumps' canonical schemas (:func:`consts`) and never off a spelling.
        """
        key = f"{terminal.module}.{terminal.name}"
        their = self.theirs["declarations"].get(key)
        if their is None or not their.get("schema"):
            return {}
        pinned = consts(their["schema"])
        if not pinned:
            return {}
        ours: dict[str, object] = {}
        for target in inner.get("target") or ():
            held = self.ours["declarations"].get(target)
            if held and held.get("schema"):
                ours.update(consts(held["schema"]))
        return {k: v for k, v in pinned.items() if k not in ours}

    def _bound(self, row: dict, how: str, targets: list[str], note: str) -> dict:
        """The BOUND row :meth:`resolve`'s own `bind` writes, for a key outside its body."""
        row.update(
            verdict="BOUND",
            how=how,
            target=targets,
            note=note,
            identity="union" if len(targets) > 1 else "stated",
            public=[self.public(t) for t in targets],
        )
        return row

    def resolve(self, mod: str, name: str, _stated: bool = True) -> dict:
        row = self._by_dump(mod, name)
        if row.get("verdict") == "BOUND" or not _stated or self.aliases is None:
            return row
        better = self.stated(mod, name)
        if better is None:
            return row
        if better.get("verdict") == "BOUND":
            return better
        return {**row, **better}

    def _by_dump(self, mod: str, name: str) -> dict:
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
        # **AND WHERE THE DUMP OFFERS SEVERAL DECLARATIONS FOR ONE PAIR, WHICH ONE THE NAME
        # DENOTES IS A QUESTION OF IDENTITY AND NOT OF SPELLING** (:meth:`denoted`).  The
        # sort above is a tie-break over MODULE PATHS -- prefer their generated tree, then
        # alphabetical -- and where the pair is ambiguous that is the one place this script
        # keyed a subject on a name.  `denoted` reads upstream's own statement instead, and
        # the row carries both readings.
        chosen = ""
        if len(keys) > 1:
            said, why = self.denoted(mod, name, keys)
            row["pair_ambiguous"] = (
                f"{len(keys)} declarations of theirs carry {name!r} at {mod}; {why}"
            )
            if said:
                key, chosen = said, "stated-subject -> "
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
                how=chosen + how,
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

        # 7: they flattened a union we keep split -- AND A UNION OF ARMS IS NOT AN
        # ENUMERATION, which is what this key was measured to get wrong
        # (`adcp-client-python-69mi`).  The value-set reading was right and is kept as the
        # finding; what it licensed was not.  See :meth:`flattened`.
        if their["method"] == "enum":
            members = self.union(their["schema"])
            if members:
                row["flattened_enum"] = (
                    f"their one enumeration's values are exactly the union of "
                    f"{len(members)} of ours ({', '.join(members)}), and a union of arms is "
                    f"not an enumeration: `for f in <name>` and `<name>.MEMBER` are the "
                    f"contract their own code uses and `A | B` has neither"
                )

        # 8: THEIR OWN DECLARING MODULE, SITTING IN OUR TREE AT THEIR OWN BYTES.  Upstream's
        # name resolves to a declaration in a module of THEIRS that no document states -- a
        # hand-written one -- and the restore lane has put that very file at that very path
        # byte for byte (`survey/upstream_machinery.restored_paths`, which is blob identity
        # against the commit the classification pins and not "a file is at the path").  So
        # the subject is not a candidate to be found: it is upstream's own declaration, and
        # `isinstance` against it holds for the same reason it holds for `foreign` above --
        # the object is the one upstream's source created.
        #
        # **WHY THIS IS NOT `word-unique` WITH A WEAKER GATE, and the measurement that says
        # so.**  `word-unique` keys on a word being declared ONCE in our whole tree, and the
        # restore lane breaks that gate wherever one of upstream's hand-written classes
        # subclasses ours under a word our generated tree also carries: measured on
        # `dropin/lastthree`, the `canonical_creative` restore made `Creative`,
        # `CreativeManifest` and `ProductFormatDeclaration` each declared TWICE, and all
        # three rows -- bound by `word-unique` while that file was absent -- fell to
        # `NO-DOCUMENT-NO-SUBJECT` on the next run, to be answered by a flat spelling off
        # `adcp.types._restored` with nothing recording the subject.  This key keys on the
        # MODULE, which upstream's own statement names (`_eager.py:965
        # UpdateMediaBuySuccessResponse = _canonical_creative.UpdateMediaBuyResponse1`), so a
        # second declaration of the word elsewhere in our tree is not a tie at all.
        #
        # **AND ONLY WHERE NO DOCUMENT IS KNOWN**, which is an ordering between the keys and
        # NOT a rule about which word reaches them.  This clause used to carry the sentence
        # "which is the clause that keeps `adcp.types.Format` the document's", and
        # `adcp-client-python-sj14` is the row that says the sentence was both false as a
        # description and wrong as a ruling.  False, because `adcp.types.Format` never
        # reached this key to be turned away: :meth:`_by_dump` had already chosen
        # `domains/core/format.py`'s declaration as the row's SUBJECT off a tie-break over
        # module-path spellings, so the document the keys above read was `core/format.json`
        # and the clause was never consulted.  Wrong, because upstream's own `_eager.py:939`
        # reads `Format = _canonical_creative.Format` -- `format_kind` + `params`, where
        # `core/format.json`'s registered format is `format_id` + `name` and is marked
        # `deprecated: true` by the bundle itself.  With the subject chosen by upstream's
        # statement (:meth:`denoted`) the row arrives here with no document, this key
        # answers, and `ProductFormatDeclaration` -- which subclasses that very class --
        # satisfies `isinstance` against the flat word.  The ordering below is unchanged and
        # is still right: a word a document gives IS decided by the document keys above.
        # What moved is which declaration "the document" is read off.
        if doc is None and word and (their_mod, word) in self.restored_declarations():
            return bind(
                "restored-module+word",
                f"{their_mod}.{word}",
                f"{their_mod} is upstream's own file in our tree byte for byte",
            )

        # 9: their word, declared EXACTLY ONCE in our whole tree.  Their generator INLINES a
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
        # **AND THE POOL EXCLUDES OUR TREE'S COPIES OF UPSTREAM'S OWN FILES, which is the
        # symmetric half of this script's standing rule about THEIR undocumented modules.**
        # That rule refuses `adcp.types.registry` on their side because "a word firing on one
        # of them would be exactly the 'identity equal under a word the bundle does not give'
        # that reading 10 refuses"; the same module is now VENDORED into our tree, so the same
        # word fires from our side and this key cannot tell the two cases apart.  Measured on
        # `dropin/lastthree`: the vendoring made `AuthorizedAgent` the only declaration of
        # that word in our tree, and this key bound upstream's `aliases.AuthorizedAgent` --
        # the `adagents.json` union of six arms -- to the registry OpenAPI model of that name,
        # identity `differs`, two unrelated subjects under one word.  A declaration of ours
        # that is upstream's own bytes is reached at upstream's own MODULE PATH (key 8) and
        # never by a word search.  `word+identity` above is left alone: its gate is exact
        # signature equality, which upstream's hand-written subclass of one of our classes
        # does not meet, and where it did meet it the object would be the right one.
        pool = [k for k in self.by_word.get(word.lower(), []) if not self.is_restored(k)]
        if word and name == word and doc is None and len(pool) == 1:
            return bind("word-unique", pool[0], "the only declaration of that word in our tree")

        # 10 / 11: THE POINTERS THE DOCUMENT STATES, which is where their generator's INLINED
        # node and our referenced document's class are one subject under two words.  Not one
        # letter of either side's spelling is read: the pool is
        # :meth:`pointer_pool` -- the declarations of ours the document states, inline or
        # through its own `$ref` -- and the selector is the declaration's own content.  Two
        # selectors in strength order, each required to be UNIQUE in the pool:
        #
        #   document+pointer-identity  the canonical schemas are EQUAL.  `ExperimentalFeature`
        #                              is `core/experimental-feature-id.json`, referenced at
        #                              `#/properties/experimental_features/items`, and the two
        #                              emissions agree to the digest.
        #   document+pointer-structure the DOCUMENT'S OWN structure agrees (:func:`shape`):
        #                              names, nesting, enumerated values, with every keyword a
        #                              generator adds dropped.  This is the key for a node two
        #                              emitters describe differently -- their `Accreditation`
        #                              and our `AccreditationsItem` are both the document's
        #                              `.../metrics/items/properties/accreditations/items`
        #                              and disagree only on what each added to `evidence_url`.
        #
        # **IT CANNOT BIND TWO UNRELATED SUBJECTS**, and the two reasons are the two halves:
        # the pool is bounded by ONE document -- their own declaring module's -- and by the
        # references THAT document states, so nothing outside what the document names is a
        # candidate at all; and the selector is the document's own vocabulary, where a tie
        # refuses the row instead of picking (`pointer_refused`).  A structure that names
        # nothing (:func:`names_nothing`) is refused outright, because every scalar alias of
        # a document shares it.
        if doc:
            pool = self.pointer_pool(doc)
            want = root_shape(their["schema"])
            if their["sig"]:
                hit = [k for k in pool if self.ours["declarations"][k]["sig"] == their["sig"]]
                if len(hit) == 1:
                    return bind(
                        "document+pointer-identity",
                        hit[0],
                        f"the document states it at {pool[hit[0]] or '#'}",
                    )
                if len(hit) > 1:
                    row["pointer_refused"] = (
                        f"{len(hit)} pointers of the document carry that schema"
                    )
            if not names_nothing(want) and "pointer_refused" not in row:
                hit = [k for k in pool if self.shape_of(k) == want]
                if len(hit) == 1:
                    return bind(
                        "document+pointer-structure",
                        hit[0],
                        f"the document states it at {pool[hit[0]] or '#'}",
                    )
                if len(hit) > 1:
                    row["pointer_refused"] = (
                        f"{len(hit)} pointers of the document carry that structure"
                    )

        # 12: THE DOCUMENT'S CONSTRAINED-SCALAR POSITIONS, which the two keys above cannot
        # reach because at such a position OUR TREE DECLARES NOTHING.
        #
        # `core/acceptance-policy-profile-ids.json` is an array of `{type: string,
        # minLength: 1}` and our walk lowers the root to `AcceptancePolicyProfileIDs` and the
        # ELEMENT to `constraints.StrMinLen1` -- an `Annotated[str, Field(min_length=1)]`
        # that belongs to no document, which is `adcp.types.constraints`' own first
        # paragraph.  So the pointer pool above holds the root and nothing else, and
        # `document+pointer-identity` has no candidate to gate: upstream's class is a
        # declaration where ours is an annotation.  That is the structural lane's own
        # refusal said precisely -- "the array-ELEMENT and root-model cases need a different
        # KEY, not a looser one".
        #
        # **THE POOL IS §3a's L1 CATALOGUE, which is the COMPILER'S OWN RECORD of what it
        # lowered at each pointer** (`codegen.catalogue.collect_scalars`, the same call
        # `codegen/emit.py` makes to build `Module.constrained`).  So the candidate at a
        # pointer is not inferred here; it is the symbol the run emitted there.
        #
        # **AND THE SELECTOR IS THE DOCUMENT'S OWN NODE against THEIR emission.**  The
        # catalogue position states a type word and a constraint set; upstream's declaration
        # dumps a canonical root schema; the two are compared as the acceptance-bearing
        # keywords they are, with `codegen.catalogue.ANNOTATIONS` dropped for §3a's reason
        # (an annotation does not change what a node admits).  Not one letter of either
        # side's spelling is read, which is what keeps this off the two rules this epic has
        # already refuted: `x-entity` names an entity KIND and is stated at 3,338 sites, so
        # it cannot identify a node; and de-pluralising the document's name is a TEXT rule.
        # The pointer is neither.
        #
        # **UNIQUE IN THE DOCUMENT, and that is the gate doing the work.**  A constraint set
        # carries no name -- `StrMinLen1` stands for every `minLength: 1` string in the
        # bundle -- so the TYPE cannot discriminate and only the position can.  One document
        # stating two positions with one constraint set refuses the row and says so, rather
        # than handing upstream's word whichever came first.
        if doc and their.get("schema") and "pointer_refused" not in row:
            scalars = self.scalar_pool(doc)
            want = admits(json.loads(their["schema"]).get("root") or {})
            hit = sorted({(p, n) for p, (states, n) in scalars.items() if states == want})
            if len(hit) == 1:
                pointer, symbol = hit[0]
                key = f"{OUR_CONSTRAINTS}.{symbol}"
                row.update(
                    verdict="BOUND",
                    how="document+pointer-constraint",
                    target=[key],
                    public=[[OUR_CONSTRAINTS, symbol]],
                    identity="document",
                    note=(
                        f"the document states that constraint at {pointer or '#'} and "
                        f"nowhere else in it, and our walk lowers it to {symbol}"
                    ),
                )
                return row
            if len(hit) > 1:
                row["pointer_refused"] = (
                    f"{len(hit)} positions of the document state that constraint"
                )

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

#: **THE MODULE UPSTREAM PUBLISHES AS A NAMESPACE IS SERVED BY OURS**, or `None` where
#: upstream's module is not one.  Measured off their own source and never listed: of every
#: module in their hand-written type layer, exactly two bind nothing but plain re-exports of
#: their generated tree and declare no class or function of their own -- `_generated`
#: (2,981 bindings, 2,969 of them straight out of `adcp.types.domains`) and `error_details`
#: (98 and 96).  A module whose whole content is "every generated name" owes every generated
#: name, and a census over module-SCOPE imports cannot measure that: `adcp/server/mcp_tools`
#: reaches into it with `getattr`, so the demand showed 30 names and the suite then stopped
#: on `_generated.ValidateInputRequest` with every one of the 30 present.
__adcp_delegates_to__ = {delegate}


def __getattr__(name: str) -> object:
    why = __adcp_refused__.get(name)
    if why is not None:
        raise AttributeError(
            f"{{__name__}}.{{name}} is upstream's and has no subject in the pinned bundle: "
            f"{{why}}. See docs/migration-from-upstream.md"
        )
    # **DELEGATION IS A NAME AND NOT A SECOND ANSWER.**  The namespace reached here is OUR
    # own flat surface, whose names one lane already decided; this adds no decision of its
    # own, declares nothing, and is lazy -- so a module of 3,477 names costs nothing at
    # import.  The refusal table is read FIRST, because a verdict about this name at this
    # module outranks the namespace's answer to the same word.
    if __adcp_delegates_to__ is not None:
        import importlib

        held = importlib.import_module(__adcp_delegates_to__)
        try:
            return getattr(held, name)
        except AttributeError:
            pass
    raise AttributeError(f"module {{__name__!r}} has no attribute {{name!r}}")


def __dir__() -> list[str]:
    if __adcp_delegates_to__ is None:
        return sorted(__all__)
    import importlib

    return sorted(set(__all__) | set(dir(importlib.import_module(__adcp_delegates_to__))))
'''


def owner(module: str, target: Path, restored: frozenset[Path]) -> str | None:
    """Who holds this path, where it is NOT this writer's to write: the reason, or `None`.

    **THE WRITER OWNS A PATH THAT IS ABSENT OR THAT CARRIES ITS OWN MARKER, AND NOTHING
    ELSE.**  Read as a predicate over the path rather than as "the file exists", which is
    the distinction `adcp-client-python-smzq` is about: `target.exists()` is true of the
    writer's OWN last output, so skipping on it meant the instrument could never ADD A NAME
    to a module it had written -- a schema bump moved the table beside it and left every
    adapter module at its old contents, with nothing saying so.  The two clauses here are
    the two things that skip was standing in for, each said as what it actually is:

    * **upstream's own file, restored** (`survey/upstream_machinery.restored_paths`): the
      bytes at the path are upstream's at the commit the classification names.  Measured on
      this tree: six paths, and five of them -- `_legacy_assets`, `_scalar`, `_str_enum`,
      `_wire`, `error_narrowing` -- are paths this writer's own demand names.  Derived from
      the classification and never listed, so a module restored tomorrow is protected
      without this file changing.
    * **a module of OURS**: a path that exists, carries no marker of an adapter, and is not
      upstream's restored file either -- which is our EMITTED domain surface
      (`adcp.types.core` is a document's module of ours AND the name of a hand-written
      machinery module of theirs) or any other hand-authored module of the layer.  Where
      their path is already ours, ours wins (`survey/dropin/_dropin.py`'s own rule), read
      here at file granularity because this writes FILES and not a loader.

    Neither clause reads a module NAME, because the hazard is a path: upstream's
    `versioned_bases/_runtime.py` and our `_runtime.py` are two files whose module leaf is
    one word, and a name-keyed exclusion would protect ours as though it were theirs.

    And a third clause, which is this writer's own reach rather than someone's ownership:
    **A MODULE A LOADER ALREADY ANSWERS FOR IS NOT A FILE THIS WRITER CAN WRITE, and the
    import system is asked rather than the filesystem.**  `adcp.types.domains` is a package
    served by a FINDER that goes in front of `PathFinder` (`adcp/types/domains/__init__.py`
    binds `<mirror>.<rest>` to the built module `adcp.types._schemas.<rest>`), so EVERY
    module of that subtree is answered by the loader and not by a file -- including the ones
    whose directory exists.

    This clause read `target.parent.is_dir()` and that was measured wrong: `domains/` is a
    real directory, so the writer created `domains/core.py` and `domains/creative.py`, and
    both are files no import reaches.  `from adcp.types.domains.core import DomainBreakdown`
    raised `ImportError ... from 'adcp.types._schemas.core'` with that file sitting on disk,
    because the finder had already answered -- two modules written, two names served, zero
    imports satisfied, and nothing saying so.  `importlib.util.find_spec` is the reading that
    cannot be wrong about it: where a spec comes back whose origin is not this path, something
    else is already serving the name.
    """
    if target.resolve() in restored:
        return "upstream's own file, restored"
    #: **THE FLAT NAMESPACE IS THE ONE ROW WHOSE TARGET IS NOT ITS MODULE'S OWN FILE**, by
    #: this writer's own design: `adcp.types`'s `__init__` IS the package and is hand-written
    #: on purpose, so the flat names go to `_adapter.py` and that `__init__` imports them.
    #: A loader answering for `adcp.types` is therefore OUR `__init__` consuming this
    #: writer's output and not something else serving the name, which is the only case where
    #: the clause below would read a collaboration as a collision.
    try:
        spec = None if module == "adcp.types" else importlib.util.find_spec(module)
    except BaseException:  # noqa: BLE001 -- an unimportable parent is not a claim on the path
        spec = None
    if spec is not None and spec.origin not in (None, "built-in", "frozen"):
        #: **THE READING IS THE MODULE'S OWN PATH AGAINST THE ORIGIN'S, AND NEVER THE TARGET
        #: FILE'S.**  A loader that MAPS a module serves it from somewhere its own dotted
        #: name does not name -- `adcp.types.domains.core` is answered out of
        #: `types/_schemas/core/__init__.py` -- and that mismatch is the whole signal.  The
        #: target file is not the comparison, because this function is also asked about a
        #: tree that is not the live package (the gate writes into `tmp_path`), where the
        #: live origin is never the target and the clause would then refuse every path.
        leaf = "/".join(module[len("adcp.types") :].lstrip(".").split("."))
        origin = str(Path(spec.origin).as_posix())
        if not origin.endswith((f"/{leaf}.py", f"/{leaf}/__init__.py")):
            return f"a loader already answers for {module}, at {spec.origin}"
    if not target.parent.is_dir():
        return f"no directory at {target.parent.name}/ -- the module is served by a loader"
    if not target.exists():
        return None
    if MARKER in target.read_text():
        return None
    return "a module of ours, which this writer did not write"


#: Where a NAMESPACE module of upstream's is served from.  One entry, because our flat
#: surface is one namespace; the KEYS are measured (:func:`namespaces`) and never listed.
OUR_NAMESPACE = "adcp.types"


def namespaces(oracle: ua.Oracle | None) -> frozenset[str]:
    """Which modules of upstream's are PURE RE-EXPORT NAMESPACES of their generated tree.

    Read off their own source, as a property rather than as a list: every module-scope
    binding is a plain `import` out of `adcp.types.domains`, and the module declares no
    class and no function of its own.  Measured on 9.6.1: `adcp.types._generated` (2,981
    bindings, 2,969 from the generated tree) and `adcp.types.error_details` (98 and 96), and
    nothing else clears 0.75.  The threshold is `>= 0.9` with at least twenty bindings, and
    the declaration screen is what keeps a topic module with a few re-exports out.
    """
    if oracle is None:
        return frozenset()
    per: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    for (module, _name), statement in oracle.bindings.items():
        if module.startswith(ua.THEIR_GEN):
            continue
        kind = statement.kind
        if kind in ("import", "import-as"):
            kind += "-gen" if statement.ref_module.startswith(ua.THEIR_GEN) else "-other"
        per[module][kind] += 1
    out = set()
    for module, kinds in per.items():
        total = sum(kinds.values())
        from_gen = kinds["import-gen"] + kinds["import-as-gen"]
        if total >= 20 and from_gen / total >= 0.9 and not (kinds["class"] or kinds["function"]):
            out.add(module)
    return frozenset(out)


def write_modules(
    rows: list[dict],
    out: Path,
    version: str,
    restored: frozenset[Path] | None = None,
    delegating: frozenset[str] = frozenset(),
) -> tuple[dict[str, tuple[int, int]], dict[str, str]]:
    """One module per upstream module the demand names, with its names and its refusals.

    **A PATH THIS WRITER DOES NOT OWN IS NEVER WRITTEN, AND A PATH IT OWNS IS REWRITTEN**
    (:func:`owner`, and `adcp-client-python-smzq` for the defect that is).  Those are the
    two halves of one repair and neither works alone: without the ownership reading a
    re-run overwrites upstream's restored machinery with generated re-exports, and with a
    blanket "the target exists" skip the instrument cannot add a name to its own module and
    stops being derived at the first schema bump.  A refusal is REPORTED with its reason
    (:func:`main` prints it) rather than recorded as a module written with no names.

    The FLAT namespace is written to `_adapter.py` for the same reason: `adcp.types`'s own
    `__init__` is the package, it is hand-written on purpose ("a package's own `__init__` IS
    the package, so it is bound before `__path__` is consulted"), and it resolves a flat name
    through a module rather than carrying a list.
    """
    #: Measured live by default (`survey/upstream_machinery.restored_paths`) and a PARAMETER
    #: so the gate can hand this function a tree of its own: the one thing worth proving
    #: about the clause is that a run targeting a restored path leaves its bytes alone, and
    #: a check that proved it against `src/adcp/types` would destroy the tree when it failed.
    restored = um.restored_paths() if restored is None else restored
    by_module: dict[str, list[dict]] = collections.defaultdict(list)
    for row in rows:
        by_module[row["module"]].append(row)
    written: dict[str, tuple[int, int]] = {}
    refused_paths: dict[str, str] = {}
    for module, group in sorted(by_module.items()):
        # **THE WHOLE MODULE PATH AND NOT ITS LEAF.**  A leaf collapses
        # `adcp.types.domains.core.format` onto `format.py` beside `capabilities.py`, which
        # is a file at a path no module names; the demand reached a nested module for the
        # first time on this branch and the flattening would have written four such files.
        rest = module[len("adcp.types") :].lstrip(".")
        target = (
            out / "_adapter.py" if not rest else out.joinpath(*rest.split(".")).with_suffix(".py")
        )
        held = owner(module, target, restored)
        if held is not None:
            refused_paths[module] = f"{target.name}: {held}"
            continue
        statements: list[str] = []
        unions: list[str] = []
        names: list[str] = []
        refused: dict[str, str] = {}
        for row in sorted(group, key=lambda r: r["name"]):
            if row["verdict"] != "BOUND":
                # **THE REASON IS THE RICHEST ONE THE ROW HOLDS, not the verdict alone.**
                # A verdict names the CLASS of refusal; the sentences below name THIS name's
                # own obstruction, and the obstruction is what a caller reading an
                # `AttributeError` needs.  Measured on the name that cost the most:
                # `GetProductsField` read `DOCUMENT-NO-WORD-NO-IDENTITY`, which says nothing
                # about the `anyOf` of two enumerations behind it.
                detail = row.get("flattened_enum") or row.get("stated_refused") or ""
                refused[row["name"]] = (
                    f"{row['verdict']}: {detail}" if detail else row["verdict"]
                )
                continue
            paths = [
                tuple(p) if p else tuple(k.rsplit(".", 1))
                for p, k in zip(row["public"], row["target"])
            ]
            if len(paths) == 1:
                mod, word = paths[0]
                statements.append(f"from {mod} import {word} as {row['name']}")
            elif row.get("method") == "enum":
                # **AND NEVER FOR AN ENUMERATION**, the second half of the clause below and
                # the one `adcp-client-python-69mi` is about.  Refused HERE as well as at the
                # key, because this is the line that wrote the type: a union of arms has
                # neither `for f in <name>` nor `<name>.MEMBER`, so standing it in for an
                # enumeration changes the KIND of the name and costs an importing module its
                # whole package.  Defence in depth and not a duplicate reading -- the key
                # decides a binding, this decides whether a STATEMENT may be written.
                refused[row["name"]] = (
                    "UNION-OF-ARMS-IS-NOT-AN-ENUMERATION: upstream published one "
                    f"enumeration and the subject is {len(paths)} of ours"
                )
                continue
            else:
                # **A UNION ALIAS IS STILL A NAME.**  The arms are imported under private
                # words and joined, so nothing is declared and every arm is the object the
                # walk emitted -- `get_args` over the alias returns them by identity.  Only
                # where upstream published a UNION: see the `enum` arm above.
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
        # **A MODULE WITH NO NAME TO SERVE IS NOT CREATED, and one that already exists is
        # still rewritten.**  Both halves measured.  A refusal-only module buys exactly one
        # thing -- the import that fails says WHY -- and `from <module> import X` fails
        # either way, so it moves no blocked file: of the 19 of upstream's files this run
        # unblocked, none was unblocked by one.  What it costs is a module of the surface
        # that exports nothing, which `tests_emit/test_the_surface_exports_something.py`
        # calls a defect in its first sentence and reddens on twice; creating four of them
        # turned 6 of its failures into 14.  So the predicate is "no bound name AND no file
        # there yet": nothing new is minted, and `registry`, `guards` and
        # `canonical_creative` -- already on the tree, already red there -- keep being
        # rewritten, because a path this writer owns going stale is `smzq` all over again.
        if not names and not target.exists():
            refused_paths[module] = (
                f"{target.name}: every one of its {len(refused)} rows is refused, and a "
                "module of the surface that exports nothing is a defect of its own"
            )
            continue
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
            delegate=f'"{OUR_NAMESPACE}"' if module in delegating else "None",
        )
        target.write_text(body)
        written[module] = (len(names), len(refused))
    return written, refused_paths


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
    #: **THE BUNDLE A RUN READS**, which is the published one with the build's patch sets
    #: applied (`codegen.patch.for_build`) -- the same derivation `./check` and
    #: `tests_emit/fresh.py` take, so the pointers the keys below read off a document are the
    #: pointers the emitter wrote into `__adcp_schema__`.  Named rather than assumed: the
    #: unpatched bundle is a different document set and would state different references.
    parser.add_argument("--bundle", type=Path, default=HERE.parent / "schemas/cache/3.2")
    #: **UPSTREAM'S SUITE IS PART OF THE CORPUS** (:func:`corpus`), and it is named rather
    #: than assumed: on this branch `tests/` is upstream's own suite byte for byte and
    #: `tests_emit/` is ours, so the directory that holds the DEMAND is upstream's.
    parser.add_argument("--suite", type=Path, default=HERE.parent / "tests")
    #: The oracle for a name upstream BINDS rather than declares, read off their own source
    #: at the commit the machinery classification pins.  `--no-upstream-source` runs the
    #: thirteen dump-keys alone, which is how the key's own yield is measured.
    parser.add_argument("--no-upstream-source", action="store_true")
    args = parser.parse_args()

    if args.dump_ours:
        dump_ours(args.dump_ours)
        return
    if args.census or args.census_json:
        c = census(args.src, args.suite)
        print_census(c)
        if args.census_json:
            args.census_json.write_text(json.dumps(c, indent=0))
        if not args.ours:
            return
    if not (args.ours and args.upstream):
        parser.error("the join needs --ours and --upstream")

    from codegen import patch

    c = census(args.src, args.suite)
    oracle = None if args.no_upstream_source else ua.Oracle.at()
    if oracle is not None:
        print(
            f"upstream's own source at {oracle.rev}: "
            f"{len(oracle.bindings)} module-scope bindings"
        )
    join = Join(
        json.loads(args.ours.read_text()),
        json.loads(args.upstream.read_text()),
        patch.for_build(args.bundle),
        oracle,
    )
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
    stated = [r for r in rows if r.get("stated_by")]
    print(f"  upstream's own source was read for: {len(stated)} names  "
          f"({sum(1 for r in stated if r['verdict'] == 'BOUND')} bound, "
          f"{sum(1 for r in stated if r.get('stated_refused'))} refused with a reason)")
    for why, n in collections.Counter(
        (r.get("stated_refused") or "").split(":")[0] for r in stated if r.get("stated_refused")
    ).most_common(8):
        print(f"      {n:5}  {why[:92]}")

    if args.table:
        #: `method` is upstream's own KIND for the name -- `model`, `enum`, `adapter`,
        #: `none` -- read off their dump and recorded because `adcp-client-python-69mi` is a
        #: defect of KIND and not of name: a union of arms over the right values is still
        #: the wrong thing where upstream published an enumeration, and a table with no
        #: `method` column cannot be asked whether that happened.
        cols = ("module", "name", "verdict", "how", "identity", "method", "document", "word",
                "their_declaring", "target", "public", "pairs", "note",
                #: **WHICH DECLARATION THE PAIR DENOTES, where the dump offered several**
                #: (:meth:`Join.denoted`).  Reported as its own column because the subject a
                #: key was asked about is prior to the key: a row bound by `document+word`
                #: off the wrong one of two candidates reads identically to a right one, and
                #: `adcp-client-python-sj14` is that row.
                "pair_ambiguous",
                "flattened_enum", "stated_by", "stated_terminal", "stated_refused")
        with args.table.open("w") as fh:
            fh.write(f"# survey/adapter_surface.py over upstream adcp {join.version}\n")
            fh.write("\t".join(cols) + "\n")
            for row in rows:
                fh.write("\t".join(str(row.get(c, "")).replace("\t", " ") for c in cols) + "\n")
        print(f"  table -> {args.table}")
    if args.report:
        args.report.write_text(json.dumps({"version": join.version, "rows": rows}, indent=1))
    if args.write:
        delegating = namespaces(oracle)
        print(f"  modules upstream publishes as a NAMESPACE, measured: {sorted(delegating)}")
        written, refused_paths = write_modules(
            rows, args.write, join.version, delegating=delegating
        )
        for module, n in sorted(written.items()):
            print(f"  wrote {module:34} {n[0]:5} names, {n[1]:4} refused")
        for module, why in sorted(refused_paths.items()):
            print(f"  NOT WRITTEN {module:28} {why}")


if __name__ == "__main__":
    main()
