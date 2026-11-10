"""The flat surface upstream's own machinery asks of ``adcp.types``, from the modules
restored at upstream's own paths.

**THE DEMAND, measured.**  95 of upstream's own test files write
``from adcp.types import MEDIA_BUY_LEGACY_STATUS_VALUES``, and that constant is not a
schema subject: it is a ``frozenset`` of six lifecycle words that upstream's own docstring
explains by SUBTRACTION -- ``completed`` is excluded because it is also the 3.1
task-envelope success status -- so a set derived from the bundle's enumeration would have
been a different set and wrong.  The only thing that can serve it is the file that declares
it, and that file is restored at ``adcp.types.media_buy_status_helpers`` byte for byte.

**WHY THE FLAT SPELLING NEEDS A MODULE OF ITS OWN.**  Upstream serves it from their own
``_eager``, and that module is not restorable here: measured, it carries 16 imports of
their generated ``_generated`` aggregator plus ``_ergonomic``, ``_forward_compat``,
``projections``, ``aliases`` and ``guards``, and the aggregator stays deleted along with
the generator that wrote it.  So the flat surface has to reach the restored files directly,
and ``adcp.types.compat`` cannot do it --
that module is the ALIAS table, keyed on a document and the word the document gives, and
none of these names has a document.

**IT NAMES MODULES AND NEVER NAMES.**  :data:`MODULES` is the whole of what is written
down, and :func:`offered` derives the names from each module's own ``__all__`` or, where it
declares none -- four of the six do not -- from what the module itself DECLARED.  So a name
upstream adds to one of these files is reachable flat with nothing here edited, and a name
removed stops being reachable rather than becoming a stale alias.  ``tests_emit/
test_the_restored_flat_surface.py`` holds :data:`MODULES` against
``survey/upstream-machinery-9.6.1.tsv``'s own ``restored`` column -- which is BYTE IDENTITY
against upstream's commit and not "a file exists at the path" -- in both directions, so a
seventh restored module joins this surface by a run reporting it.

**CONSULTED LAST**, after ``compat`` and ``_adapter`` (``adcp.types.__getattr__``), so no
name either of those decides can be overridden here; and LAZILY, for the reason that
package's own docstring gives: nothing may import the generated tree while
``adcp/types/__init__.py``'s body runs.  Measured and not assumed -- none of the six
imports ``adcp.types`` at all, so consulting this module costs no generated import even
when it answers.

**TWO PREDICATES, AND THEY ARE NOT THE SAME ONE.**  :data:`MODULES` is PROVENANCE -- are
these upstream's bytes, answered by byte identity against upstream's commit -- and what
this surface OFFERS is SUBJECT: does the word already name a document's own class
somewhere a consumer reaches.  The two agreed for nine modules and separated on the tenth:
``canonical_creative`` is restored and 30 of its 42 names are OUR document classes
subclassed, so deriving the offer from ``restored`` alone put a second spelling of thirty
subjects onto one namespace.  :func:`_surface` answers the subject question by asking the
layers that own subjects -- a word ``compat`` or ``_adapter`` binds is not offered here.

**AND IT IS THE WORD AND NOT THE VALUE.**  Screening on the value instead (``no
__adcp_schema__``) was tried and measured: it drops ``MediaBuyPackage``, which is upstream's
canonical word for ``get-media-buys-response.json``'s ``Package`` and which no earlier
layer binds -- so the screen withheld the only path to it and the kept-machinery gate lost
a resolving pair.  A document-backed name is a second spelling only where the first one
exists.

**AND PRECEDENCE IS A TIE-BREAK AND NOT A PRIORITY** (`adcp-client-python-y34k`, the
correction that :data:`STATED` is).  Asking the earlier layers alone -- "is this word one
``compat`` or ``_adapter`` binds" -- answers the subject question for a word UPSTREAM SAYS
NOTHING ABOUT, and gets it exactly backwards for a word upstream's own ``_eager`` binds to
one of these files: an earlier layer does bind it, so this surface declined to offer it, so
the flat word stayed the document's class -- which is not what upstream's flat word denotes.
Measured against upstream's 13,586-passing run: **262 of the 866 remaining
``ValidationError`` tests are that one defect, on 25 bindings over 14 words**, and every one
says the same sentence -- upstream's flat ``Format`` is ``canonical_creative.Format``,
hand-written and holding no document, while ours was ``core/format.json``'s root.

So the order of the two questions is: **upstream's own statement first, and precedence only
where upstream states nothing.**  :data:`STATED` is the first; :func:`_surface`'s
subtraction is the second.
"""

from __future__ import annotations

import importlib
import types

#: The restored modules of ``adcp.types``, by MODULE.
#:
#: Upstream's own hand-written machinery, put back at upstream's own path byte for byte,
#: which is ``survey/upstream-machinery-9.6.1.tsv``'s ``restored`` verdict.  Thirteen today.
#: Written here because a shipped package cannot read a survey table, and held against
#: that table by the gate named in this module's docstring -- so the authority is byte
#: identity against upstream's commit and this tuple is the derivation's cached answer
#: rather than its source.
#:
#: ``base`` and its leaf ``_geo_place_keys`` joined on `adcp-client-python-1zmw`, and what
#: they add to the flat surface is the one thing worth reading twice: ``AdCPBaseModel`` is
#: unbound on ``adcp.types`` today and binds here now, to UPSTREAM's class -- which under
#: that ruling is the class ``adcp.types._base``'s own derives from, so the flat spelling,
#: upstream's module path and every emitted model are one lineage and ``isinstance`` holds
#: against any of the three.  The 10 names only upstream's ``base.py`` declares arrive with
#: it (``defer_model_rebuild``, ``inherit_field``, ``NoExplicitNull``, ``WireUrl`` and the
#: rest); nothing else in ``src/adcp/`` declares any of them.
#:
#: ``_product_format_declaration`` joined beside them as ``canonical_creative``'s last
#: MECHANICAL blocker (`adcp-client-python-rqjo`): 102 lines, no ``adcp.types`` import at
#: all, and its one import of ours -- ``adcp.validation.schema_loader.get_named_validator``
#: -- resolves here already.  It brings ``PRODUCT_FORMAT_DECLARATION_SCHEMA`` and
#: ``check_declaration_rules``, which an adapter could never have served because one is a
#: hand-written function and the other is a document path a re-export has no name for.
#:
#: ``canonical_creative`` is the one this epic's #1 item was about (`adcp-client-python-eh82`):
#: 1,386 lines, 36 classes and 17 functions, and the path was served by a 2.5 KB re-export
#: adapter -- which is why ``Format``, ``CanonicalBoundaryModel``,
#: ``strip_legacy_creative_identity`` and the 31-entry ``PRIMARY_CANONICAL_MODELS`` tuple
#: were simply absent.  An adapter restates names; it cannot supply a function, a tuple of
#: model types, or a base class.
#:
#: ``registry`` is VENDORED rather than restored-and-reproducible: upstream generates it
#: from an OpenAPI spec that is not a document of the bundle this compiler compiles, so its
#: 155 classes are unreproducible here whatever the emitter does.  It reaches this tuple by
#: the same byte-identity reading as the other twelve, because provenance is the only question
#: this tuple answers.
#:
#: **AND 150 OF ITS NAMES ARE OFFERED FLAT HERE WHERE UPSTREAM OFFERS THEM ONLY AT THE
#: MODULE PATH, which is an open question and not a decision.**  Upstream's own machinery
#: writes ``from adcp.types.registry import BrandActivity``, which works either way;
#: whether ``adcp.types.BrandActivity`` should ALSO answer is a surface question nobody has
#: ruled on.  The survey's recorded flat surface cannot settle it -- measured, that
#: 939-name reading omits ``MEDIA_BUY_LEGACY_STATUS_VALUES``, which 95 of upstream's own
#: test files import flat and which this module exists for, so it is a filtered population
#: and not upstream's whole flat surface.
#:
#: ``projections`` and ``variants`` joined on `adcp-client-python-knnw`, and they are the
#: first pair where one restore is the OTHER's only blocker.  ``projections`` is the file
#: ``project_geo_postal_areas`` lives in -- 242 lines, 4 classes and 7 functions, and the
#: function is a hand-written PROJECTION between two shapes of one capability declaration
#: (AdCP 3.1's country-keyed ``{"US": ["zip"]}`` and 3.0's fused ``{"us_zip": true}``), so
#: no re-export could ever have served it: a table of eleven native/legacy pairs and the
#: rule that a legacy ``False`` is absence rather than support are statements of upstream's,
#: not of any document's.  It also carries ``BusinessEntityResponse`` and
#: ``AccountResponse``, which enforce the bundle's own ``writeOnly: true`` on
#: ``BusinessEntity.bank`` and on notification credentials by TYPE -- a projection the
#: emitted tree does not make, because ``writeOnly`` constrains a direction of flow and not
#: what a node admits.  ``variants`` is its blocker and nothing else: 52 lines, no ``adcp``
#: import of any kind, and one ``SchemaVariant`` marker class whose ``__getitem__``
#: collapses to its argument -- which is why the adapter layer records it ``NOT-A-TYPE``
#: and why only upstream's own bytes can answer for it.
MODULES = (
    "_geo_place_keys",
    "_legacy_assets",
    "_product_format_declaration",
    "_scalar",
    "_str_enum",
    "_wire",
    "base",
    "canonical_creative",
    "error_narrowing",
    "media_buy_status_helpers",
    "projections",
    "registry",
    "variants",
)


#: **THE WORDS UPSTREAM'S OWN FLAT SURFACE TAKES FROM A RESTORED MODULE**, by word.
#:
#: Upstream's ``_eager.py`` reads, in its own statements::
#:
#:     Format               = _canonical_creative.Format                # _eager.py
#:     PackageRequest       = _canonical_creative.PackageRequest
#:     SyncCreativesRequest = _canonical_creative.SyncCreativesRequest
#:
#: so ``from adcp.types import Format`` is upstream's HAND-WRITTEN canonical class and not
#: ``core/format.json``'s root -- two subjects, one word, and the flat one is theirs.  Each
#: entry below names the restored module whose declaration their chain
#: (``adcp.types`` -> ``_eager`` -> ``_generated`` -> ``domains.<document>``) terminates in,
#: which is the only thing that can decide it: the same word is bound at three of their
#: modules to two different subjects, so a reading of ONE statement answers for whichever
#: line it met first, and the TERMINAL is what upstream's flat word means.
#:
#: **DERIVED, AND THIS IS THE DERIVATION'S CACHED ANSWER RATHER THAN ITS SOURCE** -- the same
#: arrangement :data:`MODULES` has and for the same reason, that a shipped package cannot
#: parse upstream's git tree.  The source is ``survey/upstream_aliases.flat_statements``
#: over ``survey/upstream_machinery.restored_paths`` (byte identity against upstream's
#: commit), and ``tests_emit/test_the_restored_flat_surface.py`` holds this mapping against
#: that derivation in BOTH directions -- a word upstream states and this mapping omits
#: reddens, and a word here upstream does not state reddens.  So a word upstream MOVES into
#: or out of one of these files is a run reporting it, and no name is here because somebody
#: read a failure list: 37 words are stated, the 25 failing bindings name 14 of them, and the
#: other 23 are owed by the same sentence.
#:
#: ``MEDIA_BUY_LEGACY_STATUS_VALUES`` and ``project_geo_postal_areas`` are in here too, and
#: they are the reading that shows this is not a second screen bolted onto the first: both
#: were already offered flat -- no earlier layer binds either -- so for them the two
#: questions agree and this mapping changes nothing.  11 of the 37 are that case; the other
#: 26 are the ones the precedence subtraction was taking away.
STATED = {
    "AccountResponse": "projections",
    "BrandSource": "registry",
    "BusinessEntityResponse": "projections",
    "CanonicalFormatKindStr": "canonical_creative",
    "CreateMediaBuyResponse": "canonical_creative",
    "CreateMediaBuyResponse1": "canonical_creative",
    "Creative": "canonical_creative",
    "CreativeAsset": "canonical_creative",
    "CreativeFilters": "canonical_creative",
    "CreativeManifest": "canonical_creative",
    "CreativeVariant": "canonical_creative",
    "Format": "canonical_creative",
    "GetCreativeDeliveryResponse": "canonical_creative",
    "GetMediaBuyDeliveryResponse": "canonical_creative",
    "GetMediaBuysResponse": "canonical_creative",
    "GetProductsRequest": "canonical_creative",
    "GetProductsResponse": "canonical_creative",
    "ListCreativesRequest": "canonical_creative",
    "ListCreativesResponse": "canonical_creative",
    "MEDIA_BUY_LEGACY_STATUS_VALUES": "media_buy_status_helpers",
    "Package": "canonical_creative",
    "PackageRequest": "canonical_creative",
    "PackageUpdate": "canonical_creative",
    "Placement": "canonical_creative",
    "Product": "canonical_creative",
    "ProductFilters": "canonical_creative",
    "ProductFormatDeclaration": "canonical_creative",
    "SchemaVariant": "variants",
    "SyncCreativesRequest": "canonical_creative",
    "UpdateMediaBuyResponse": "canonical_creative",
    "UpdateMediaBuyResponse1": "canonical_creative",
    "UpdateMediaBuyResponse3": "canonical_creative",
    "is_canonical_format_kind": "canonical_creative",
    "project_geo_postal_areas": "projections",
    "require_canonical_format_kind": "canonical_creative",
    "to_account_response": "projections",
    "unwrap_enum_value": "media_buy_status_helpers",
}


def offered(module: types.ModuleType) -> dict[str, object]:
    """What ``module`` offers the flat surface: its ``__all__``, or what it DECLARED.

    ``__all__`` first, because a module that declares one has said what it offers and the
    answer is not this function's to improve -- ``_wire`` and ``error_narrowing`` are the
    two of the six that do.

    Otherwise the names a reader would call the module's own, and the discriminator is the
    one Python answers rather than one a list would: a class or a function carries the
    ``__module__`` of the body that created it, so ``typing.Any``,
    ``collections.abc.Mapping`` and ``pydantic.RootModel`` imported into a restored file
    are excluded without being named, and a name with no ``__module__`` at all is the
    module's own DATA -- which is exactly what ``MEDIA_BUY_LEGACY_STATUS_VALUES`` is, a
    ``frozenset`` instance, and what a rule written over ``__module__`` alone would have
    dropped.  A submodule bound by an ``import`` is excluded as a module.
    """
    advertised = getattr(module, "__all__", None)
    if advertised is not None:
        held = {name: getattr(module, name) for name in advertised if hasattr(module, name)}
    else:
        held = {}
        for name, value in vars(module).items():
            if name.startswith("_") or isinstance(value, types.ModuleType):
                continue
            home = getattr(value, "__module__", None)
            if home is None or home == module.__name__:
                held[name] = value
    # A name no ``import`` statement could spell is not a name this surface can offer.
    # Measured: the ``base`` restore put ``AdCPRootModel[Any]`` into ``__all__``, which
    # ``adcp.types.__dir__`` then advertised -- a parametrized generic is a key in that
    # module's namespace and is not an identifier.
    return {name: value for name, value in held.items() if name.isidentifier()}


def _surface() -> dict[str, object]:
    """Every name the restored modules offer, in :data:`MODULES` order.

    Earlier modules win, which is :data:`MODULES`' own order and is a decision only in
    the sense that a collision has to resolve somehow: measured over the six, there is
    none, and ``tests_emit/test_the_restored_flat_surface.py`` asserts that rather than
    leaving the order to carry the weight.

    **AND A WORD AN EARLIER LAYER DECIDES IS NOT OFFERED HERE UNLESS UPSTREAM'S OWN
    STATEMENT SAYS IT IS THIS MODULE'S** -- precedence said in the ``__all__`` and not only
    in the lookup, and :data:`STATED` said ahead of precedence.  Two words and two different
    answers, which is the whole of the distinction:

    ``MediaBuy`` is declared by ``canonical_creative`` and is NOT stated: upstream's own
    chain for the flat word runs ``_eager.py:56`` -> ``_generated.py:1500`` ->
    ``domains/core/media_buy.py``, so their flat ``MediaBuy`` is their GENERATED class and
    the word here is a second spelling of a subject the alias table already carries.
    Precedence decides and the word is subtracted: advertising it would make ``__all__`` a
    promise this module does not keep, and ``adcp.types.__dir__`` unions all four lists.
    Ten words are that case, which is also what makes :data:`STATED` a reading of upstream's
    statements rather than "everything ``canonical_creative`` declares".

    ``Format`` is a word ``compat`` binds to ``core/format.json``'s root and upstream's
    ``_eager`` binds to ``canonical_creative.Format`` -- hand-written, holding no document,
    requiring ``format_kind`` and ``params`` where the document's root requires ``format_id``
    and ``name``.  Upstream STATES it, so the subtraction does not reach it and the flat word
    is upstream's subject.  This is the trap the epic fell into three times from the other
    side: screening on the value (``no __adcp_schema__``) passes ``Format`` for the wrong
    reason, and screening on precedence alone refuses it for the wrong reason.  The property
    is upstream's own statement about the WORD.

    No import is added by this: ``adcp.types.__getattr__`` consults ``compat`` and
    ``_adapter`` for every word this one does not state, so both are in ``sys.modules``
    whenever this function runs and ``import_module`` on a loaded module is a dict lookup.
    """
    found: dict[str, object] = {}
    for module in MODULES:
        for name, value in offered(importlib.import_module(f"{__package__}.{module}")).items():
            found.setdefault(name, value)
    for module in ("compat", "_adapter"):
        held = importlib.import_module(f"{__package__}.{module}")
        for name in (*getattr(held, "__all__", ()), *getattr(held, "__adcp_flat_only__", {})):
            if name not in STATED:
                found.pop(name, None)
    return found


def __getattr__(name: str) -> object:
    """A restored module's own name, or ``AttributeError``.

    ``__all__`` is answered here too, through PEP 562, so the set is derived at the moment
    it is asked for and this module holds no second copy of it.
    """
    if name == "__all__":
        return sorted(_surface())
    if name.startswith("__"):
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        return _surface()[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None


def __dir__() -> list[str]:
    return sorted(_surface())
