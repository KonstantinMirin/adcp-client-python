"""An absolute ``$ref`` that names a NODE inside another document.

`salesagent-j3k2l.14`.  A separate module from ``tests/test_emit.py`` because this
grades one mechanism end to end -- the ``#`` reading, the resolver's store, the name
a referenced node gets, and the import a referring module writes -- and because
``test_emit`` holds the metric constants that are re-measured once per epic.

**The population this mechanism serves is almost entirely GATED BEHIND OTHER STEPS,
and that is why the constructed-bundle cases below exist.**  Measured at the sha this
landed on: 19 documents are named by a fragment, 18 of them are refused on a keyword
of their own, and the one that lowers -- ``core/version-envelope.json`` -- is named by
12 referrers that are each refused on another keyword.  So the real bundle exercises
the NAMING half (two aliases in the committed tree, asserted below) and reaches the
IMPORT half zero times.  Grading the import half only against the bundle would be a
pass over an empty loop, so it is graded on a bundle this file writes, which is the
same thing ``codegen`` does for every mechanism whose population a later step opens
(D5's mapping key rule says so in as many words).
"""

from __future__ import annotations

import ast
import functools
import importlib
import json
import sys
from pathlib import Path

import pytest

from codegen import bundle, emit
from codegen.refusal import Refusal

REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "schemas" / "cache" / "3.2"
TREE = REPO / emit.TREE

DRAFT = "http://json-schema.org/draft-07/schema#"
#: The base every reference in the 3.2 bundle is spelled under.  Written out here
#: because a CONSTRUCTED bundle has to spell its references the way a real one does
#: -- ``document_for`` matches a trailing run of path segments, so a test that
#: referenced ``other.json`` bare would grade a shorter path than the bundle uses.
BASE = "https://adcontextprotocol.org/schemas/9.9.9/"


@functools.cache
def fragment_refs() -> list[tuple[str, str, str]]:
    """``(referencing document, pointer, uri)`` for every fragment-bearing absolute
    reference in the bundle, read off the one schema-position walk."""
    return [
        (document, pointer, uri)
        for document in bundle.portable(BUNDLE)
        for pointer, uri in bundle.references(bundle.read(BUNDLE, document))
        if all(bundle.split_ref(uri))
    ]


def node_at(doc: object, pointer: str) -> object:
    """The node a JSON Pointer names, or :data:`NOTHING`."""
    cur: object = doc
    for raw in [s for s in pointer.split("/") if s]:
        seg = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list) and seg.isdigit() and int(seg) < len(cur):
            cur = cur[int(seg)]
        elif isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return NOTHING
    return cur


NOTHING = object()


def kwargs_of(annotation: ast.AST) -> set[str]:
    """Every ``Field(...)`` keyword name anywhere in an annotation."""
    return {
        kw.arg
        for n in ast.walk(annotation)
        if isinstance(n, ast.Call)
        for kw in n.keywords
        if kw.arg
    }


# --------------------------------------------------------------------------- #
# the reading of the ``#``
# --------------------------------------------------------------------------- #
def test_split_ref_is_the_one_reading_of_the_hash() -> None:
    """Three callers read a ``$ref``'s two halves and they must agree.

    ``document_for`` matches the document half, ``resolved`` keys its store on it,
    and ``emit``'s binder needs both.  So the halves come from one function, and the
    two cases a caller branches on -- a LOCAL reference and an absolute one -- are
    distinguished by the document half being empty rather than by a second ``in``
    test somewhere.
    """
    assert bundle.split_ref("https://x.test/a/b.json") == ("https://x.test/a/b.json", "")
    assert bundle.split_ref("https://x.test/a/b.json#/properties/c") == (
        "https://x.test/a/b.json",
        "/properties/c",
    )
    assert bundle.split_ref("#/definitions/x") == ("", "/definitions/x")
    # A trailing ``#`` names the ROOT, which is a document reference with an empty
    # pointer and not a local one.
    assert bundle.split_ref("https://x.test/a/b.json#") == ("https://x.test/a/b.json", "")

    # ``document_for`` takes the DOCUMENT HALF and reads no ``#`` of its own, so the
    # two together are the whole resolution and there is one place the delimiter is
    # read.  Composed here the way all three callers compose them.
    known = {"core/catalog.json"}
    for uri in (
        "https://x.test/3.2.4/core/catalog.json",
        "https://x.test/3.2.4/core/catalog.json#/properties/category",
        "https://x.test/3.2.4/core/catalog.json#",
    ):
        assert bundle.document_for(bundle.split_ref(uri)[0], known) == "core/catalog.json", uri
    # A local reference names no document, which is NOT the same as an unresolvable
    # one.  The caller tells them apart on the document half being EMPTY, which is why
    # this is ``None`` and not a refusal.
    assert bundle.split_ref("#/definitions/x")[0] == ""
    assert bundle.document_for("", known) is None
    assert bundle.document_for("https://x.test/3.2.4/core/absent.json", known) is None


def test_every_fragment_reference_in_the_bundle_names_a_node_that_exists() -> None:
    """The gate this step removes was never about a missing file.

    Both halves of all 113 sites: the document half resolves to a document of this
    bundle, and the pointer half names a node that is actually in it.  Pinned at 113
    sites / 76 distinct targets / 19 target documents, because a selector that
    silently stopped matching would turn this into a pass over an empty loop -- and
    this test's whole job is to say the references are sound.
    """
    sites = fragment_refs()
    assert len(sites) == 113, len(sites)
    known = set(bundle.portable(BUNDLE))
    targets = set()
    for document, pointer, uri in sites:
        head, into = bundle.split_ref(uri)
        target = bundle.document_for(head, known)
        assert target is not None, (document, pointer, uri)
        assert node_at(bundle.read(BUNDLE, target), into) is not NOTHING, (document, uri)
        targets.add((target, into))
    assert len(targets) == 76, len(targets)
    assert len({t for t, _ in targets}) == 19, sorted({t for t, _ in targets})
    assert ("core/catalog.json", "/properties/category") in targets


def test_no_portable_documents_reference_closure_names_a_document_this_bundle_lacks() -> None:
    """``bundle.resolved``'s store loop, over the whole population, with the
    inlining left off.

    **INSTRUMENT, stated because it is not the function itself.**  ``resolved`` has a
    documented O(paths) ceiling -- the bundle holds a 9,109-byte document that
    resolves to 4.8 MB -- and calling it 1,054 times does not finish in a test.  What
    raises is the STORE loop, which is this; the inlining that follows cannot raise
    for a reference the store already holds.  ``resolved`` itself is exercised on a
    real fragment-bearing document in the next test, which is where the inlining is
    graded.

    Measured before this step: the loop raised for 151 of the 1,054 -- 88 reaching an
    absolute fragment reference and 63 more whose only unresolvable reference was a
    pointer into THEMSELVES.  Both are zero now, and 0 is the whole point: a document
    this gate closes on can be neither emitted nor refused on a keyword of its own.
    """
    known = set(bundle.portable(BUNDLE))
    read = {d: bundle.read(BUNDLE, d) for d in known}
    unresolvable: list[tuple[str, str, str]] = []
    for document in sorted(known):
        store: dict[str, dict] = {}
        queue = [read[document]]
        while queue:
            for pointer, uri in bundle.references(queue.pop()):
                head = bundle.split_ref(uri)[0]
                if not head or head in store:
                    continue
                target = bundle.document_for(head, known)
                if target is None:
                    unresolvable.append((document, pointer, uri))
                    continue
                store[head] = read[target]
                queue.append(store[head])
    assert unresolvable == [], unresolvable[:10]
    assert len(known) == 1054, len(known)


def test_resolved_inlines_the_node_a_fragment_names_and_not_the_whole_document() -> None:
    """The store is keyed on the DOCUMENT URI and the resolver follows the pointer.

    Keying it on the FULL URI is what this did, and it is the other half of the gate:
    probed on ``hypothesis_jsonschema``'s resolver, a store holding the target under
    ``<uri>#/properties/x`` raises ``_RefResolutionError`` ("does not fetch remote
    references") while the same target under ``<uri>`` inlines the node.  So removing
    the ``None`` alone would have left the reference unresolvable with its target
    read in -- which is why this asserts the inlined VALUE and not merely that
    nothing raised.

    On a real document, because the claim is about this bundle.
    ``core/catalog-selection.json`` names ``core/catalog.json#/properties/type``, and
    that node is ITSELF a ``$ref`` -- so this also grades the chain: a fragment to a
    reference resolves through to the node at the end of it, which is the enum.
    """
    document = "core/catalog-selection.json"
    known = set(bundle.portable(BUNDLE))
    uri = bundle.read(BUNDLE, document)["properties"]["type"]["$ref"]
    head, into = bundle.split_ref(uri)
    assert into == "/properties/type", uri
    target = bundle.document_for(head, known)
    assert target == "core/catalog.json", target
    got = bundle.resolved(BUNDLE, document)["properties"]["type"]
    assert "$ref" not in got, got
    # The NODE, resolved the way the TARGET's own document resolves it -- not the
    # document the node lives in.  A resolver that substituted the whole target would
    # put ``core/catalog.json``'s other properties and its title here.
    assert got == bundle.resolved(BUNDLE, target)["properties"][into.split("/")[-1]], got
    assert "properties" not in got, "the whole target document was inlined, not the node"
    assert "enum" in got, got


def test_a_local_reference_resolves_against_the_referrer_with_no_store_entry() -> None:
    """A pointer into the document itself is SKIPPED by the store loop, not looked up.

    63 documents' only unresolvable reference was one of these.  ``LocalResolver`` is
    built with ``referrer=doc``, so it inlines one from the document's own body; the
    loop raising on it was reading ``#`` as "names another document" when it means
    the opposite.

    And a document whose ONLY reference is local must still be RESOLVED: it builds an
    empty store, and the shortcut that skipped resolution when the store was empty
    would have handed it back with the ``$ref`` left in -- the one thing ``resolved``
    exists to prevent.

    **KNOWN CEILING, measured here rather than asserted away: 3 of the 13 keep a
    local reference.**  ``resolve_all_refs`` cannot inline a RECURSIVE one -- a
    ``definitions`` entry that references itself through a chain has no finite
    inlining -- and those three (``core/bidding-policy-capability.json``,
    ``core/placement-presentation.json``,
    ``governance/reported-outcome-error.json``) carry 4, 8 and 10 of them.  All three
    are refused in the lowering on ``definitions``, so no pair grades a document with
    a reference left in it; the step whose population emits one meets this, and the
    answer there is a recursive model, not a deeper resolver.
    """
    local = [
        d
        for d in bundle.portable(BUNDLE)
        if (rs := bundle.references(bundle.read(BUNDLE, d)))
        and all(not bundle.split_ref(u)[0] for _, u in rs)
    ]
    assert len(local) == 13, local
    recursive = {}
    for document in local:
        left = bundle.references(bundle.resolved(BUNDLE, document))  # raises if the gate is back
        if left:
            recursive[document] = len(left)
    assert sorted(recursive) == [
        "core/bidding-policy-capability.json",
        "core/placement-presentation.json",
        "governance/reported-outcome-error.json",
    ], recursive
    # The other 10 are fully inlined from the document's own body, with no store.
    assert len(local) - len(recursive) == 10


# --------------------------------------------------------------------------- #
# the naming: a referenced node gets a symbol in ITS OWN module
# --------------------------------------------------------------------------- #
def test_the_named_node_population_is_read_off_the_bundle_and_not_off_a_run() -> None:
    """``bundle.named_nodes`` is a function of the BUNDLE (P7).

    A module whose CONTENT varied with which other documents a run named would make
    the committed tree a function of the last population that ran, and the gate's
    byte compare would then grade whichever that was.  So the same document emitted
    ALONE and emitted with everything else produces the same module -- asserted here
    on the one named document that lowers.
    """
    named = bundle.named_nodes(BUNDLE)
    assert len(named) == 19, sorted(named)
    assert sum(len(p) for p in named.values()) == 76, sum(len(p) for p in named.values())
    assert named["core/version-envelope.json"] == frozenset(
        {"/properties/adcp_version", "/properties/adcp_major_version"}
    )
    # A local reference is not here: it names a node of its own document, so there is
    # no import and no cross-module symbol.
    assert all(d != "" for d in named)

    document = "core/version-envelope.json"
    alone = emit.emit(BUNDLE, [document])
    assert alone.files[f"{emit.module_path(document)}.py"] == (
        TREE / f"{emit.module_path(document)}.py"
    ).read_text()


def test_a_named_node_is_declared_once_in_its_own_module_and_the_property_uses_it() -> None:
    """D2 makes these two nodes annotations, so a fragment reference had nothing to
    import.  Now each has a symbol, named by D3's nested rule, and the node's
    constraints live on it ALONE -- the property references the symbol rather than
    restating the bound, so the module spells each fact once.

    On the one real document a fragment names that also lowers, and off a FRESH
    emission rather than the committed file: a test that parses the committed bytes
    grades whatever the last run wrote, so a regression in the emitter survives it
    until somebody re-emits.  The committed tree is tied to the fresh emission by the
    byte compare below, separately.  Read off the AST, not the text.
    """
    document = "core/version-envelope.json"
    tree = ast.parse(emit.emit(BUNDLE, [document]).files[f"{emit.module_path(document)}.py"])
    aliases = {
        t.target.id: t.value
        for t in tree.body
        if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
    } | {
        a.targets[0].id: a.value
        for a in tree.body
        if isinstance(a, ast.Assign) and isinstance(a.targets[0], ast.Name)
    }
    assert "AdCPVersionEnvelopeAdcpVersion" in aliases, sorted(aliases)
    assert "AdCPVersionEnvelopeAdcpMajorVersion" in aliases, sorted(aliases)

    cls = next(c for c in tree.body if isinstance(c, ast.ClassDef))
    fields = {
        t.target.id: t.annotation
        for t in cls.body
        if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
    }
    # **Each constraint the document states is on the ALIAS and on nothing else.**  On
    # the kwarg NAMES rather than on the rendered text, because a pattern's backslashes
    # are escaped twice through ``ast.unparse`` and a text match there grades a
    # spelling.  The document's own keywords, in pydantic's names, come from the
    # document.
    for key, symbol, stated in (
        ("adcp_version", "AdCPVersionEnvelopeAdcpVersion", {"pattern"}),
        ("adcp_major_version", "AdCPVersionEnvelopeAdcpMajorVersion", {"ge", "le"}),
    ):
        on_alias = kwargs_of(aliases[symbol])
        on_field = kwargs_of(fields[key])
        assert stated <= on_alias, (symbol, sorted(on_alias))
        assert not stated & on_field, (key, sorted(on_field))
        assert symbol in {n.id for n in ast.walk(fields[key]) if isinstance(n, ast.Name)}, key
        # Nothing but a name and a description rides on the property: a constraint of
        # the node has nowhere else in the module to hide.
        assert on_field <= {"description", "alias", "default", "json_schema_extra"}, (
            key,
            sorted(on_field),
        )


# --------------------------------------------------------------------------- #
# the import: on a bundle this file writes, because the real one reaches it 0 times
# --------------------------------------------------------------------------- #
def write_bundle(tmp_path: Path, documents: dict[str, dict]) -> Path:
    """A bundle directory holding exactly ``documents``, references spelled the way
    the real bundle spells them."""
    root = tmp_path / "bundle"
    for name, doc in documents.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"$schema": DRAFT, **doc}, indent=1))
    return root


TARGET = {
    "title": "Catalog Like",
    "type": "object",
    "properties": {
        # A CONSTRAINED SCALAR: D2 makes it an annotation, so it has no symbol until
        # something names it, and the constraint is what makes "an import, not a copy"
        # falsifiable.  16 of the bundle's 76 fragment targets are this shape, and
        # ``core/version-envelope.json``'s two -- the only ones in a document that
        # lowers -- are among them.
        "category": {"type": "string", "minLength": 2, "maxLength": 9},
        # An ARRAY beside it, the commonest shape among the 76 (30 of them), so the
        # import is graded on more than one of D2's annotation rows.  Unconstrained:
        # a bound INSIDE a container is D5's named-type row and refuses until
        # ``salesagent-j3k2l.12`` lands, which is a different step's gate.
        "tags": {"type": "array", "items": {"type": "string"}},
        "label": {"type": "string"},
    },
}
REFERRER = {
    "title": "Selection Like",
    "type": "object",
    "properties": {
        "kind": {"$ref": f"{BASE}core/target.json#/properties/category"},
        "marks": {"$ref": f"{BASE}core/target.json#/properties/tags"},
    },
}


def test_a_fragment_reference_is_an_import_of_the_targets_symbol_and_not_a_copy(
    tmp_path: Path,
) -> None:
    """The exit condition, on the AST: a fragment resolves to an IMPORT of a symbol
    the TARGET module declares, never to a copy.

    Both halves, because either alone passes while the other fails: the referring
    module imports ``(relative module, symbol)``, and its field names that symbol and
    carries none of the target's constraints.  ``minLength``/``maxLength`` are the
    target's, and a copy would put them here.
    """
    root = write_bundle(
        tmp_path, {"core/target.json": TARGET, "core/selection.json": REFERRER}
    )
    out = emit.emit(root, ["core/selection.json"])
    assert out.refusals == {}, out.refusals
    # The target emits too, though nothing named it: a module cannot import from a
    # module no run wrote.
    assert sorted(out.emitted) == ["core/selection.json", "core/target.json"], out.emitted

    tree = ast.parse(out.files["core/selection.py"])
    imported = {
        ("." * n.level + (n.module or ""), a.name)
        for n in ast.walk(tree)
        if isinstance(n, ast.ImportFrom)
        for a in n.names
    }
    module = emit.relative_module("core/selection.json", "core/target.json")
    cls = next(c for c in tree.body if isinstance(c, ast.ClassDef))
    fields = {
        t.target.id: t.annotation
        for t in cls.body
        if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
    }
    target_tree = ast.parse(out.files["core/target.py"])
    declared = {
        a.targets[0].id for a in target_tree.body if isinstance(a, ast.Assign)
    } | {a.target.id for a in target_tree.body if isinstance(a, ast.AnnAssign)}

    # D3: parent name + pascal_case(property), computed by the walk and not here.
    for key, symbol in (("kind", "CatalogLikeCategory"), ("marks", "CatalogLikeTags")):
        assert (module, symbol) in imported, (key, sorted(imported))
        got = fields[key]
        assert symbol in {n.id for n in ast.walk(got) if isinstance(n, ast.Name)}, key
        assert kwargs_of(got) <= {"description", "alias", "default", "json_schema_extra"}, (
            key,
            sorted(kwargs_of(got)),
        )
        # And the symbol the import names is really DECLARED there, by the target --
        # not merely present in its text and not imported into it from elsewhere.
        assert symbol in declared, (symbol, sorted(declared))

    # The unnamed property keeps its inline annotation: a node nothing references is
    # not given a symbol, so this mechanism does not rename the whole bundle.
    assert "CatalogLikeLabel" not in declared, sorted(declared)


def test_a_class_for_a_fragment_target_names_the_targets_document_and_pointer(
    tmp_path: Path,
) -> None:
    """A fragment target that IS a class carries ``__adcp_schema__`` naming the
    TARGET's document and the node's own pointer -- never the referring document.

    There is no binding table and no adapter: the class finds its schema through its
    own attribute, so a grader cannot be aimed at the wrong tree.
    """
    target = {
        "title": "Holder",
        "type": "object",
        "properties": {
            "inner": {
                "type": "object",
                "properties": {"a": {"type": "string"}},
                "required": ["a"],
            }
        },
    }
    referrer = {
        "title": "Points At Inner",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/holder.json#/properties/inner"}},
    }
    root = write_bundle(tmp_path, {"core/holder.json": target, "core/pointer.json": referrer})
    out = emit.emit(root, ["core/pointer.json"])
    assert out.refusals == {}, out.refusals
    tree = ast.parse(out.files["core/holder.py"])
    inner = next(c for c in tree.body if isinstance(c, ast.ClassDef) and c.name == "HolderInner")
    ref = next(
        ast.unparse(t.value)
        for t in inner.body
        if isinstance(t, ast.AnnAssign) and getattr(t.target, "id", None) == "__adcp_schema__"
    )
    assert "core/holder.json" in ref, ref
    assert "#/properties/inner" in ref, ref
    assert "pointer.json" not in ref, ref
    # A node that is already a class is NOT given a second symbol beside it.
    assert [c.name for c in tree.body if isinstance(c, ast.ClassDef)].count("HolderInner") == 1
    assert "HolderInner = " not in out.files["core/holder.py"]


# --------------------------------------------------------------------------- #
# the refusals: by name, pointer and keyword, with the fragment named
# --------------------------------------------------------------------------- #
def refusal_for(root: Path, document: str) -> dict[str, str]:
    out = emit.emit(root, [document])
    assert document in out.refusals, out.emitted
    return out.refusals[document]


def test_a_fragment_naming_a_node_the_walk_never_reaches_is_refused_with_it_named(
    tmp_path: Path,
) -> None:
    """A pointer into a section the lowering does not descend has no symbol, and the
    document is refused by name, pointer and keyword rather than bound to the root.

    Binding it to the root instead would import a class for the WHOLE document where
    the document names one node of it -- a model wider than its schema, silently.
    17 of the bundle's 76 fragment targets are ``definitions`` entries, which is
    exactly this case (their documents refuse on ``definitions`` first today).
    """
    target = {
        "title": "Has A Def",
        "type": "object",
        "properties": {"a": {"type": "string"}},
    }
    referrer = {
        "title": "Names A Missing Node",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/hasadef.json#/properties/nope"}},
    }
    root = write_bundle(tmp_path, {"core/hasadef.json": target, "core/names.json": referrer})
    r = refusal_for(root, "core/names.json")
    assert r["keyword"] == "$ref", r
    assert r["pointer"] == "/properties/x", r
    assert "/properties/nope" in r["detail"], r
    assert "core/hasadef.json" in r["detail"], r


def test_a_fragment_whose_target_document_is_refused_names_the_targets_own_keyword(
    tmp_path: Path,
) -> None:
    """The chain, which is what the four gate refusals in the real bundle become.

    Before this step the referrer refused on "names no document of this bundle",
    which was FALSE -- the document exists, and all four of its targets are refused
    on a keyword of their own (``pattern``, ``allOf``, ``definitions``, and a chain).
    A refusal that names the wrong cause sends the next reader to the wrong file.
    """
    target = {"title": "Refuses", "type": "object", "properties": {"a": {"const": "x"}}}
    referrer = {
        "title": "Chains",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/refuses.json#/properties/a"}},
    }
    root = write_bundle(tmp_path, {"core/refuses.json": target, "core/chains.json": referrer})
    r = refusal_for(root, "core/chains.json")
    assert r["keyword"] == "$ref", r
    assert r["pointer"] == "/properties/x", r
    # The FRAGMENT is named, not only the document: the chain fires before the node is
    # looked up, and a message naming only the file does not say which of its nodes
    # was wanted.
    assert "core/refuses.json#/properties/a is refused" in r["detail"], r
    assert "const" in r["detail"], r

    # A reference with NO fragment names the document alone, unchanged -- which is
    # every one of the bundle's 214 existing chain refusals.
    plain = {
        "title": "Chains Plainly",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/refuses.json"}},
    }
    root = write_bundle(tmp_path / "b", {"core/refuses.json": target, "core/plain.json": plain})
    assert "core/refuses.json is refused" in refusal_for(root, "core/plain.json")["detail"]


def test_a_local_fragment_reference_is_refused_by_name_pointer_and_keyword(
    tmp_path: Path,
) -> None:
    """The import half for a pointer into the document ITSELF is not built.

    0 of the documents that lower carry one: all 45 that do refuse on
    ``definitions``/``$defs``, the keyword such a reference points through.  So the
    symbol would be one the module is in the middle of writing, and the refusal says
    so by name rather than a later step finding a silent drop.
    """
    # No ``definitions`` section: that keyword refuses first in every real document
    # carrying one, so including it here would grade THAT refusal and this one would
    # never fire.  The reference is the only thing this document cannot lower.
    doc = {
        "title": "Points At Itself",
        "type": "object",
        "properties": {"x": {"$ref": "#/definitions/inner"}},
    }
    root = write_bundle(tmp_path, {"core/selfref.json": doc})
    r = refusal_for(root, "core/selfref.json")
    assert r["keyword"] == "$ref", r
    assert r["pointer"] == "/properties/x", r
    assert "#/definitions/inner" in r["detail"], r


def test_two_symbols_at_one_pointer_is_refused_rather_than_ordered() -> None:
    """A pointer names ONE node, so two symbols at one pointer would make a fragment
    reference import whichever the walk declared last.

    Measured 0 times over the whole population, so this grades the guard on a
    ``Module`` directly -- the symmetric case to the duplicate-NAME refusal beside it,
    which the same method raises.
    """
    from codegen.compiler import Module

    mod = Module(document="x.json")
    mod.declare("A", "/properties/a", "A = int")
    with pytest.raises(Refusal) as first:
        mod.declare("B", "/properties/a", "B = str")
    assert first.value.keyword == "$ref"
    assert first.value.pointer == "/properties/a"
    assert "'A'" in first.value.detail and "'B'" in first.value.detail
    with pytest.raises(Refusal) as second:
        mod.declare("A", "/properties/b", "A = str")
    assert second.value.keyword == "title"


def test_no_document_of_the_bundle_declares_two_symbols_at_one_pointer() -> None:
    """And the guard above is not firing in the real bundle: every pointer the whole
    population declares at carries exactly one symbol, which is what makes
    ``Module.declared`` a map a reference can read."""
    out = emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    double = {
        d: r for d, r in out.refusals.items() if "two nodes are declared at this pointer" in r["detail"]
    }
    assert double == {}, double


def test_the_committed_tree_is_the_fresh_emission_of_the_derived_population() -> None:
    """The byte compare, scoped to this change: the one module a named node lands in
    is the one the emitter writes, and nothing else in the tree moved.

    ``test_emit`` owns the whole-tree compare and the metric constants; this asserts
    the file THIS step touches, so a regression here names this step.
    """
    document = "core/version-envelope.json"
    rel = f"{emit.module_path(document)}.py"
    assert emit.emit(BUNDLE, [document]).files[rel] == (TREE / rel).read_text()


def test_the_emitted_module_imports() -> None:
    """The alias is real Python and the module still imports, which no AST assertion
    above would catch -- a syntactically valid annotation can still fail at import."""
    sys.path.insert(0, str(REPO / "src"))
    mod = importlib.import_module("adcp.types._schemas.core.version_envelope")
    assert mod.AdCPVersionEnvelope.model_validate({"adcp_version": "3.1"})
    assert mod.AdCPVersionEnvelope.strict_validate({"adcp_version": "3.1"})
