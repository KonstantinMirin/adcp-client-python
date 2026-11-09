"""PROBE ONLY -- not part of the tree.  Resolves the 159 blocking (module, name) pairs
through the node-keyed map fwvm measured, so the suite can be asked what lies BEHIND them.
Binds the object our walk emitted; declares nothing; `is` holds.
"""
import importlib.abc, importlib.machinery, importlib.util, json, os, pathlib, sys, types

_MISS = set()


def _sentinel(attr):
    """CENSUS ONLY: stands in for an unresolved name so ONE pass enumerates every miss."""
    return type("_AbsentFromOurSurface_" + attr, (), {"__adcp_census_sentinel__": attr})


import atexit


@atexit.register
def _write_misses():
    if os.environ.get("MOVEIT_CENSUS") == "1":
        with open(os.environ["MOVEIT_CENSUS_OUT"], "w") as fh:
            fh.write("\n".join(sorted(_MISS)) + "\n")


_MAP = json.loads((pathlib.Path(__file__).parent / "probe_map.json").read_text())
_filled = {}


def _patch(dropin):
    # f99s's rule: a PROJECTION is a second spelling of a document we already compile, so
    # its path resolves to the CANONICAL document instead of to a second compile.  Same
    # for upstream's private `_brand_discovery.json`, whose nodes `brand.json` states.
    _doc = dropin._document_module

    def _document_module(fullname):
        out = _doc(fullname)
        if out is None:
            return None
        rest = out[len("adcp.types._schemas") + 1 :]
        for proj in ("bundled.", "mcp."):
            if rest.startswith(proj):
                rest = rest[len(proj) :]
        if rest == "brand_discovery":
            rest = "brand"
        return "adcp.types._schemas" + ("." + rest if rest else "")

    dropin._document_module = _document_module
    original = dropin._resolver

    def _resolver(fullname, document):
        base = original(fullname, document)

        def __getattr__(attr):
            try:
                return _machinery(base(attr))
            except AttributeError:
                row = _MAP.get(f"{fullname}:{attr}")
                if row is None:
                    derived = _derived(fullname, attr)
                    if derived is not None:
                        return derived
                    _MISS.add(f"{fullname}:{attr}")
                    if os.environ.get("MOVEIT_CENSUS") == "1":
                        return _sentinel(attr)
                    raise
                return _machinery(getattr(importlib.import_module(row[0]), row[1]))

        return __getattr__

    dropin._resolver = _resolver

    # **UPSTREAM REFLECTS OVER THE MODULE'S `vars()`.**  `aliases.py:1692` scans
    # `vars(adcp.types.domains.core.format).values()` for the class whose `asset_type`
    # default matches -- so a module that "holds no name of its own" answers with an empty
    # dict and raises.  An ALIAS MODULE has to BIND its names, not only resolve them.
    _exec = dropin._AliasLoader.exec_module

    def exec_module(self, module):
        _exec(self, module)
        inner = module.__getattr__

        def __getattr__(attr):
            if not _filled.get(module.__name__):
                _filled[module.__name__] = True
                doc = dropin._document_module(module.__name__)
                if doc:
                    try:
                        owner = importlib.import_module(doc)
                    except Exception:
                        owner = None
                    if owner is not None:
                        for k, v in vars(owner).items():
                            if not k.startswith("__"):
                                module.__dict__.setdefault(k, _machinery(v))
                pre = module.__name__ + ":"
                for key, row in _MAP.items():
                    if key.startswith(pre):
                        name = key[len(pre):]
                        try:
                            module.__dict__.setdefault(
                                name, getattr(importlib.import_module(row[0]), row[1]))
                        except Exception:
                            pass
                if attr in module.__dict__:
                    return module.__dict__[attr]
            return inner(attr)

        module.__getattr__ = __getattr__

    dropin._AliasLoader.exec_module = exec_module
    # `_dropin` calls `install()` at the bottom of its own body, so `_Finder` is already
    # at `meta_path[0]` by the time this runs -- and `_Finder` serves `_generated` from
    # the real file.  Go in front of it.
    sys.meta_path.insert(0, _GenPatcher())
    sys.meta_path.insert(0, _AliasesPatcher())



#: PROBE PATCH 3, recorded and NOT a decision this lane is entitled to make.  Upstream's
#: generator gives a NAME to a tagged union it declares at a `core/format.json` node:
#: `FormatAssetUnion` at `#/properties/assets/items/oneOf/0` and `GroupFormatAssetUnion` at
#: `#/properties/assets/items/oneOf/1/properties/assets/items`.  Our walk states the SAME
#: node as a dispatching base class and an inline field annotation, so the subject is there
#: and the WORD is not -- which is reading 6's "an EXPORT or a NAME, never a split", and
#: section 4 forbids a lane choosing either.  So the probe RESOLVES THE OBJECT OUR OWN CLASS
#: ALREADY CARRIES, derived from the field annotation and never written out as a list of
#: branches: nothing is declared, nothing is widened, and `is` holds against our branches.
#: `adcp.types.aliases` imports both at module scope, so these two names decide whether the
#: drop-in imports at all.
#: AND TWO MORE OF EXACTLY THE SAME SHAPE, found by asking `_eager` -- upstream's own flat
#: authority -- what it cannot import.  `Refine` at
#: `media-buy/get-products-request.json#/properties/refine/items` and `RefinementApplied` at
#: `media-buy/get-products-response.json#/properties/refinement_applied/items` are each an
#: `Annotated[A | B | C, Field(discriminator='scope')]` upstream gives a word to; our walk
#: states all three branches and carries the union as the field's own annotation with no
#: module-level statement.  Same subject, same missing word, same remedy owed by reading 6.
_DERIVED = {
    ("adcp.types.domains.core.format", "FormatAssetUnion"):
        ("adcp.types._schemas.core.format", "AssetsItemIndividual", None),
    ("adcp.types.domains.core.format", "GroupFormatAssetUnion"):
        ("adcp.types._schemas.core.format", "RepeatableGroupAsset", "assets"),
    ("adcp.types.domains.media_buy.get_products_request", "Refine"):
        ("adcp.types._schemas.media_buy.get_products_request",
         "GetProductsRequest", "refine"),
    ("adcp.types.domains.media_buy.get_products_response", "RefinementApplied"):
        ("adcp.types._schemas.media_buy.get_products_response",
         "GetProductsResponse", "refinement_applied"),
}


def _derived(fullname, attr):
    row = _DERIVED.get((fullname, attr))
    if row is None:
        return None
    module, name, field = row
    owner = getattr(importlib.import_module(module), name)
    if field is None:
        return owner
    import types as _t
    import typing
    annotation = owner.model_fields[field].annotation
    # Walk IN to the union our class carries: an optional field is `list[U] | None` and a
    # required one is `list[U]`, so strip the `None` arm and strip the container, and stop
    # at the first union of more than one model.  Derived from the annotation and never
    # written out as a list of branches -- `is` holds against our own branches.
    seen = [annotation]
    while seen:
        node = seen.pop(0)
        args = [a for a in typing.get_args(node) if a is not type(None)]
        origin = typing.get_origin(node)
        if origin in (_t.UnionType, typing.Union) and len(args) > 1:
            return node if len(args) == len(typing.get_args(node)) else typing.Union[tuple(args)]
        seen.extend(args)
    return annotation


_GEN = json.loads((pathlib.Path(__file__).parent / "gen_bind.json").read_text())

#: PROBE APPROXIMATION, recorded and not hidden.  Upstream's kept machinery reaches TWO
#: private validators their generator wrote onto a generated class -- machinery this
#: project does not emit and cannot derive from a schema (reading 10).  The probe supplies
#: a pass-through so the suite can be asked what lies behind the names; it is NOT an alias
#: and it is NOT a decision.
#:
#: **AND IT HAS TO BE APPLIED ON THE ROUTE THAT IS ACTUALLY TAKEN, which it was not.**  The
#: first draft applied it only where `adcp.types._generated` hands a class back, and
#: `_forward_compat.py:84` does not go that way -- it writes
#: `from adcp.types.domains.core.creative_manifest import CreativeManifest` and then reads
#: `CreativeManifest._coerce_standalone_assets` at :243.  So the whole of
#: `tests/test_manifest_response_readback.py` -- 86 items, NONE of them passing -- failed on
#: `AttributeError: _coerce_standalone_assets` rather than on anything about a value, and the
#: residue table read the junit's first line and filed 31 of them under a cause that was not
#: theirs.  The pass-through is now applied on the alias route as well.  **It is identity**,
#: so a test that asserts on the COERCED value still fails and still counts: what the
#: extension removes is the import error standing in front of the question.
_MACHINERY = {
    "_validate_country_system_pairing",
    "_coerce_standalone_assets",
}


def _machinery(obj):
    for name in _MACHINERY:
        if isinstance(obj, type) and not hasattr(obj, name):
            try:
                setattr(obj, name, classmethod(lambda cls, value: value))
            except Exception:
                pass
    return obj


class _LazyGenerated(importlib.abc.Loader):
    """`_generated` as the ALIAS MODULE it is: 2,971 re-exports resolved ON DEMAND.

    Upstream's file is 2,971 `from <document module> import <Name>` statements and ten
    assignments -- nothing else.  Eager, one absent name takes the whole module and with
    it `aliases.py`, which imports it at module scope.  Lazy, only the names the SDK and
    its tests actually ASK for have to resolve, and the count of those is what this probe
    is measuring.
    """

    def create_module(self, spec):
        return types.ModuleType(spec.name)

    def exec_module(self, module):
        module.__adcp_upstream_machinery__ = "adcp 9.6.1"
        module.__all__ = _GEN["all"]

        def __getattr__(attr):
            if attr in _GEN["assign"]:
                return getattr(module, _GEN["assign"][attr])
            row = _GEN["bind"].get(attr)
            if row is None:
                raise AttributeError(attr)
            return _machinery(getattr(importlib.import_module(row[0]), row[1]))

        module.__getattr__ = __getattr__


class _GenPatcher(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname != "adcp.types._generated":
            return None
        return importlib.machinery.ModuleSpec(fullname, _LazyGenerated())


#: PROBE PATCH 2, recorded.  `aliases.py:_format_asset_class` scans our classes for one
#: whose `asset_type` FieldInfo carries `default == "image"`.  `core/format.json` states
#: `asset_type` as `const` AND `required`, so our field is required and a required field
#: has no default -- supplying one would make it optional and readmit a value the document
#: refuses, which reading 1 forbids outright.  The probe makes the predicate read the
#: Literal's own argument instead, which is the same schema fact; nothing is widened.
def _lit(field, want):
    import typing
    if field is None:
        return False
    if field.default == want:
        return True
    seen = [field.annotation]
    while seen:
        a = seen.pop()
        if typing.get_origin(a) is typing.Literal:
            if want in typing.get_args(a):
                return True
        else:
            seen.extend(typing.get_args(a) or ())
    return False


#: PROBE PATCH 4, recorded.  `aliases.py` imports `TmpxMacro` at MODULE SCOPE from two of
#: their generated modules, SOLELY to re-export it under two flat words.  Their own generator
#: calls it a "Deprecated 3.1.8 registered macro-name compatibility model"; bundle 3.2 -- the
#: bundle this tree compiles -- states no node with its constraint set (`max_length` 64 with
#: `^[A-Z][A-Z0-9_]*$`; the nearest named bound of ours, `ReportingAdjustmentReceiptRejectionCode`,
#: is 128).  So it is NODELESS, and reading 10 is explicit: "a name with no schema subject gets
#: a migration note and NEVER A CLASS ... minting a nodeless class to satisfy an import is the
#: back door this ordering exists to close."  The probe therefore GUARDS THE IMPORT exactly as
#: upstream already guards `DurationUnit` in this same file (`try/except ModuleNotFoundError`
#: with a fallback) rather than minting the type: the two flat words then do not resolve, which
#: is what a nodeless name must do, and any test asking for one fails and is COUNTED.
_ALIASES_PATCHES = [
    ("""from adcp.types.domains.trusted_match.identity_match_response import (
    TmpxMacro as IdentityMatchTmpxMacro,
)
from adcp.types.domains.trusted_match.provider_registration import (
    TmpxMacro as ProviderRegistrationTmpxMacro,
)""",
     "# PROBE: nodeless against bundle 3.2 -- a migration note, never a class."),
    ("field is not None and field.default == asset_type",
     "__import__('sitecustomize')._lit(field, asset_type)"),
    ('field is not None and field.default == "repeatable_group"',
     "__import__('sitecustomize')._lit(field, 'repeatable_group')"),
]


#: PROBE PATCH 5, recorded, and it is `adcp-client-python-oswm`.  `_forward_compat.py`'s two
#: PRECONDITIONS assert that our field's annotation IS a class their generator emitted -- a
#: "bundled clone", from a directory `codegen.bundle.PROJECTIONS` excludes by its own words
#: ("projections of those documents ... neither is a document to emit").  Our class states the
#: same node and carries its own annotation, so the guard raises at MODULE SCOPE and takes
#: `_eager` -- upstream's OWN authority for every flat name, `adcp/types/__init__.py`'s
#: `__getattr__` resolving through it -- down with it.  Conforming means emitting a class no
#: document states, which reading 1 forbids outright, and fabricating an annotation object for
#: their inspection to read is the same widening wearing a helper's clothes.  So the probe
#: applies the UPSTREAM ASK the bead already states: let the patch be a NO-OP where the
#: annotation is already canonical.  The bridge is skipped, our `model_fields` is NOT mutated,
#: nothing is widened and no class is minted -- a guard whose purpose is to refuse to bridge a
#: shape that needs no bridging should not raise.
_FORWARD_COMPAT_PATCHES = [
    (
        """        actual = None if field is None else field.annotation
        raise RuntimeError(
            f"forward compatibility: {model.__name__}.{field_name} lost its "
            f"bundled {bundled_model.__name__} annotation (got {actual!r})"
        )""",
        "        return  # PROBE: no bundled clone to bridge; ours is already canonical.",
    ),
    (
        """        actual = None if field is None else field.annotation
        raise RuntimeError(
            f"forward compatibility: {model.__name__}.targeting_overlay lost its "
            f"TargetingOverlayInput | None annotation (got {actual!r})"
        )""",
        "        return  # PROBE: no compatibility union to bridge; ours is already canonical.",
    ),
]

#: PROBE PATCH 6, recorded, and it is `adcp-client-python-m88n` read at `_eager` instead of
#: at `aliases`.  `_eager.py` -- upstream's own authority for every flat name -- imports 901
#: names at MODULE SCOPE, and three of them have no subject in the bundle this tree compiles:
#: the two deprecated-3.1.8 `TmpxMacro` re-exports `m88n` names (nodeless: `max_length` 64
#: with `^[A-Z][A-Z0-9_]*$`, which bundle 3.2 states nowhere), and `ProductCard`, whose
#: `a2ui/si-catalog.json` node our walk reads as a component-TYPE enum and not as an object.
#: Reading 10 is explicit -- "a name with no schema subject gets a migration note and NEVER A
#: CLASS ... minting a nodeless class to satisfy an import is the back door this ordering
#: exists to close" -- so the probe DROPS THE IMPORT rather than minting the type.  The three
#: words then do not resolve, which is what a name with no subject must do, and any test
#: asking for one FAILS AND IS COUNTED rather than being discarded.
_EAGER_PATCHES = [
    ("\n    ProductCard,\n", "\n"),
    ("\n    IdentityMatchTmpxMacro,\n", "\n"),
    ("\n    ProviderRegistrationTmpxMacro,\n", "\n"),
]

#: One source patch set per module, so a module that needs none is left to the real loader.
_SOURCE_PATCHES = {
    "adcp.types.aliases": ("aliases.py", _ALIASES_PATCHES),
    "adcp.types._forward_compat": ("_forward_compat.py", _FORWARD_COMPAT_PATCHES),
    "adcp.types._eager": ("_eager.py", _EAGER_PATCHES),
}


class _AliasesPatcher(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname not in _SOURCE_PATCHES:
            return None
        leaf, patches = _SOURCE_PATCHES[fullname]
        src = pathlib.Path(
            importlib.import_module("adcp.types").__path__[0]) / leaf
        text = src.read_text()
        hit = False
        for a, b in patches:
            if a in text:
                text = text.replace(a, b); hit = True
        if not hit:
            return None
        code = compile(text, str(src), "exec")

        class L(importlib.abc.Loader):
            def create_module(self, s):
                return None

            def exec_module(self, module):
                module.__file__ = str(src)
                exec(code, module.__dict__)

        return importlib.machinery.ModuleSpec(fullname, L(), origin=str(src))


class _Patcher(importlib.abc.MetaPathFinder):
    TARGET = "adcp.types._dropin"

    def find_spec(self, fullname, path=None, target=None):
        if fullname != self.TARGET:
            return None
        sys.meta_path.remove(self)
        try:
            spec = importlib.util.find_spec(fullname)
        finally:
            sys.meta_path.insert(0, self)
        if spec is None or spec.loader is None:
            return None
        inner = spec.loader

        class L(importlib.abc.Loader):
            def create_module(self, s):
                return inner.create_module(s)

            def exec_module(self, module):
                inner.exec_module(module)
                _patch(module)

        spec.loader = L()
        return spec


if os.environ.get("FWVM_PROBE") == "1":
    sys.meta_path.insert(0, _Patcher())
