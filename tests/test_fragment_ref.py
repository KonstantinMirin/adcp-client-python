"""A ``$ref`` that names a NODE -- inside another document, or inside this one.

`salesagent-j3k2l.14` (the absolute half) and `salesagent-j3k2l.20` (the local half).
A separate module from ``tests/test_emit.py`` because this grades one mechanism end to
end -- the ``#`` reading, the resolver's store, the name a referenced node gets, and
the import a referring module writes -- and because ``test_emit`` holds the metric
constants that are re-measured once per epic.

**One module for both halves because they are one mechanism split by the document
half.** ``bundle.split_ref`` reads the ``#`` once; ``bundle.named_nodes`` asks for a
symbol once, keyed on the document the reference RESOLVES AGAINST -- the one its
document half names, or the referrer when that half is empty; ``Module.declared`` maps
pointer to symbol once; and D3's nested rule names the node once.  They part company at
the last step and only there: an absolute reference becomes an IMPORT of a symbol the
target module declares (``emit.emit``'s binder), and a local one is a lookup in the
module being written (``compiler.local_reference``).  Grading them in two files would
be two records of one ``#``.

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
import socket
from pathlib import Path

import jsonschema
import pytest
from pydantic import ValidationError

from codegen import bundle, emit
from codegen.refusal import Kind, Refusal

from tests.nodeset import claimed, partitions

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


def constraint_aliases(source: str | None = None) -> dict[str, set[str]]:
    """``adcp.types.constraints`` symbol -> the ``Field(...)`` keywords it states.

    ``source`` is the alias module's TEXT, defaulting to the committed one.  A caller
    emitting its own bundle passes that run's ``Emitted.beside`` entry instead, for the
    reason stated above about reading a fresh emission: a constructed bundle resolves a
    shape the committed module has no reason to carry, and grading against the
    committed file there would read a population this run did not emit.

    D5's rung 3 gave a constrained scalar a THIRD place to live. A node's own alias
    used to carry its constraints as kwargs; now the alias names a type in
    ``constraints`` and that type carries them, so an assertion reading only the
    alias's own kwargs reads a spelling D5 deliberately moved. Following the
    reference keeps the claim -- the constraint is reachable from the alias, and it
    is still nowhere near the property -- without weakening either half of it.
    """
    source = Path("src/adcp/types/constraints.py").read_text() if source is None else source
    out: dict[str, set[str]] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                out[target.id] = kwargs_of(node.value)
    return out


def stated_by(annotation: ast.AST, named: dict[str, set[str]]) -> set[str]:
    """The keywords an annotation states, directly or through a named constrained
    type it references."""
    reached = {n.id for n in ast.walk(annotation) if isinstance(n, ast.Name)}
    return kwargs_of(annotation).union(*(named.get(n, set()) for n in reached), set())


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

    Both halves of every site: the document half resolves to a document of this
    bundle, and the pointer half names a node that is actually in it.  The three sets
    -- sites, distinct targets, target documents -- are asserted NON-EMPTY rather than
    sized, because what the sizes were standing in for is that a selector which
    silently stopped matching would turn this into a pass over an empty loop, and this
    test's whole job is to say the references are sound.
    """
    sites = claimed("fragment reference sites", fragment_refs())
    known = set(bundle.portable(BUNDLE))
    targets = set()
    for document, pointer, uri in sites:
        head, into = bundle.split_ref(uri)
        target = bundle.document_for(head, known)
        assert target is not None, (document, pointer, uri)
        assert node_at(bundle.read(BUNDLE, target), into) is not NOTHING, (document, uri)
        targets.add((target, into))
    claimed("distinct (document, pointer) targets", targets)
    claimed("target documents", {t for t, _ in targets})
    assert ("core/catalog.json", "/properties/category") in targets


def test_no_portable_documents_reference_closure_names_a_document_this_bundle_lacks() -> None:
    """``bundle.resolved``'s store loop, over the whole population, with the
    inlining left off.

    **INSTRUMENT, stated because it is not the function itself.**  ``resolved`` has a
    documented O(paths) ceiling -- the bundle holds a 9,109-byte document that
    resolves to 4.8 MB -- so calling it 1,054 times does not belong in a suite.  What
    RAISES is the STORE loop, which is this; the inlining that follows cannot raise
    for a reference the store already holds.  ``resolved`` itself is exercised on a
    real fragment-bearing document in the next test, and on 13 more in the one after,
    which is where the inlining is graded.

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
    claimed("bundle.portable", known)


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
    are still refused in the lowering, so no pair grades a document with a reference
    left in it -- but no longer on ``definitions``: since `salesagent-j3k2l.20` they
    refuse on ``allOf``, ``const`` and ``maxProperties``, each inside the section the
    walk now descends.  The answer when one of them emits is a recursive model, not a
    deeper resolver, and ``compiler.local_reference`` refuses the cycle by name until
    there is one.
    """
    local = [
        d
        for d in bundle.portable(BUNDLE)
        if (rs := bundle.references(bundle.read(BUNDLE, d)))
        and all(not bundle.split_ref(u)[0] for _, u in rs)
    ]
    claimed("documents whose every reference is local", local, inside=bundle.portable(BUNDLE))
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
    # The rest are fully inlined from the document's own body, with no store -- named
    # as the complement of the recursive set rather than as the difference of two
    # counts, which is what says the two halves exhaust the local documents.
    claimed("locally-referencing documents fully inlined", set(local) - set(recursive))
    assert set(recursive) <= set(local), sorted(set(recursive) - set(local))


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

    A LOCAL reference satisfies P7 for a sharper reason, and `salesagent-j3k2l.20` is
    why it is in here now: the document asking and the document asked are the same
    file, so no other document of the bundle can affect the answer at all.
    """
    named = bundle.named_nodes(BUNDLE)
    # The named nodes, in three parts that are asserted separately below: the ABSOLUTE
    # fragment references, the LOCAL ones, and the documents named by BOTH kinds.  Each
    # part is asserted non-empty, which is what the six counts were standing in for --
    # a regression that dropped either arm reddens with the arm NAMED rather than
    # moving one total.
    claimed("documents with a named node", named)
    claimed(
        "named (document, pointer) nodes",
        {(d, p) for d, ps in named.items() for p in ps},
    )
    assert named["core/version-envelope.json"] == frozenset(
        {"/properties/adcp_version", "/properties/adcp_major_version"}
    )

    # The two kinds, split by the document half the way ``split_ref`` splits it, so a
    # regression that dropped either arm reddens with the arm named rather than moving
    # one total.
    halves: dict[bool, dict[str, set[str]]] = {True: {}, False: {}}
    known = set(bundle.portable(BUNDLE))
    for document in known:
        for _, uri in bundle.references(bundle.read(BUNDLE, document)):
            head, pointer = bundle.split_ref(uri)
            if not pointer:
                continue
            target = bundle.document_for(head, known) if head else document
            if target is not None:
                halves[bool(head)].setdefault(target, set()).add(pointer)
    absolute, local_refs = halves[True], halves[False]
    claimed("documents named by an ABSOLUTE fragment reference", absolute)
    claimed("documents named by a LOCAL reference", local_refs)
    claimed("(document, pointer) named absolutely", {(d, p) for d, ps in absolute.items() for p in ps})
    claimed("(document, pointer) named locally", {(d, p) for d, ps in local_refs.items() for p in ps})
    # The overlap is the fact, and it is asserted at both granularities: some documents
    # are named by each kind, and some of those are named at the SAME pointer by each.
    # Both sets non-empty, because an empty overlap would make the two arms independent
    # and the union below would say nothing about either.
    both = claimed("documents named by both kinds", set(absolute) & set(local_refs))
    claimed(
        "pointers named by both kinds",
        {(d, p) for d in both for p in absolute[d] & local_refs[d]},
    )

    # ``core/bidding-policy-capability.json`` references only itself, 4 times.  It is
    # here now, under its OWN name and its own four pointers -- which is the whole of
    # `salesagent-j3k2l.20`'s bundle-side change, and the assertion was its ABSENCE
    # before that.
    assert named["core/bidding-policy-capability.json"] == frozenset(
        {
            "/definitions/max_bid_with_cost_per",
            "/definitions/max_bid_with_roas",
            "/definitions/policy_profile",
            "/definitions/scope_capability",
        }
    ), sorted(named["core/bidding-policy-capability.json"])
    # And it is not listed as a TARGET of anything else: a local reference names its
    # own document and never another, so no absolute half resolved to it.
    assert "core/bidding-policy-capability.json" not in absolute

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
        named = constraint_aliases()
        on_alias = stated_by(aliases[symbol], named)
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
    # The refusing keyword is ``allOf``, which is one of the four real causes above.
    # It was ``const`` until D2's ``const`` row landed (salesagent-j3k2l.16) and the
    # fixture stopped refusing -- a fixture built on a keyword the emitter is about to
    # lower grades the chain only until that happens, and then grades nothing.
    target = {
        "title": "Refuses",
        "type": "object",
        "properties": {"a": {"allOf": [{"type": "string"}]}},
    }
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
    assert "allOf" in r["detail"], r

    # A reference with NO fragment names the document alone, unchanged -- which is
    # every one of the bundle's 214 existing chain refusals.
    plain = {
        "title": "Chains Plainly",
        "type": "object",
        "properties": {"x": {"$ref": f"{BASE}core/refuses.json"}},
    }
    root = write_bundle(tmp_path / "b", {"core/refuses.json": target, "core/plain.json": plain})
    assert "core/refuses.json is refused" in refusal_for(root, "core/plain.json")["detail"]


def test_a_local_pointer_naming_no_node_of_this_document_is_refused_with_it_named(
    tmp_path: Path,
) -> None:
    """A local reference resolves against the REFERRER, so a pointer naming nothing in
    the referrer names nothing at all.

    This is :func:`compiler.local_reference`'s own "no such node", and it is the local
    twin of ``test_a_fragment_naming_a_node_the_walk_never_reaches_is_refused_with_it_named``
    above.  It must not fall back to the root: binding a pointer to the document's own
    root class would hand the property a model for the WHOLE document where the
    document names one node of it -- wider than its schema, and silent.

    The document carries NO section at all, which is the whole of the fixture: the
    pointer is spelled as if one existed, so the only thing this document cannot lower
    is the reference.
    """
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
    assert "names no node of this document" in r["detail"], r

    # And a section that exists without the entry reads the same way: the section is
    # not what is missing, the NODE is.
    doc = {**doc, "definitions": {"other": {"type": "string"}}}
    root = write_bundle(tmp_path / "b", {"core/selfref.json": doc})
    assert "names no node of this document" in refusal_for(root, "core/selfref.json")["detail"]


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
        d: r
        for d, r in out.refusals.items()
        if "two nodes are declared at this pointer" in r["detail"]
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


def test_the_emitted_module_imports_and_the_aliased_fields_still_decide() -> None:
    """The aliases are real Python and the module still imports and still VALIDATES.

    No AST assertion above catches either: an annotation can be syntactically valid
    and fail at import, and a field whose type moved to an alias can import and then
    accept what the document refuses.  So both bounds are exercised in both
    directions, through ``strict_validate`` (the schema half, D4) and through the
    constructor (the annotation).  The package is installed, so this imports it by
    name rather than putting ``src`` on the path.
    """
    mod = importlib.import_module("adcp.types._schemas.core.version_envelope")
    cls = mod.AdCPVersionEnvelope
    assert cls.strict_validate({"adcp_version": "3.1", "adcp_major_version": 3})

    # Each refusal names the FIELD whose constraint moved onto the alias, so none of
    # these can pass on an incidental error.  Both halves fire and each uses its own
    # vocabulary -- ``jsonschema``'s "does not match" and pydantic's "should match".
    for refuse, key in (
        (lambda: cls.strict_validate({"adcp_version": "3"}), "adcp_version"),
        (lambda: cls(adcp_version="3"), "adcp_version"),
        (lambda: cls.strict_validate({"adcp_major_version": 100}), "adcp_major_version"),
        (lambda: cls(adcp_major_version=100), "adcp_major_version"),
    ):
        with pytest.raises(ValidationError) as err:
            refuse()
        assert key in str(err.value), (key, str(err.value)[:200])


# --------------------------------------------------------------------------- #
# the LOCAL half (`salesagent-j3k2l.20`): a pointer into the document being written
# --------------------------------------------------------------------------- #
#: A document whose root references its own ``definitions`` entries, in the three
#: shapes the bundle's 157 local-section entries take: an object (which D2 makes a
#: class), a constrained scalar (an annotation, so it needs a name of its own), and one
#: nothing references at all.
#:
#: The constrained scalar is the same ``{string, minLength: 2, maxLength: 9}`` shape
#: :data:`TARGET` uses for the absolute half, deliberately: the two halves then grade
#: one node shape, so a divergence between them is a divergence in the mechanism rather
#: than in the fixture.
SECTIONS = {
    "title": "Catalog",
    "type": "object",
    "properties": {
        "slot": {"$ref": "#/definitions/slot"},
        "code": {"$ref": "#/definitions/code"},
        # A SECOND reference to one entry: the memo answers it, so no second symbol
        # appears for one node.
        "also_code": {"$ref": "#/definitions/code"},
        "plain": {"type": "string"},
    },
    "required": ["slot"],
    "definitions": {
        "slot": {"type": "object", "properties": {"a": {"type": "string"}}, "required": ["a"]},
        "code": {"type": "string", "minLength": 2, "maxLength": 9},
        "unused": {"type": "object", "properties": {"b": {"type": "string"}}, "required": ["b"]},
    },
}


def declared_in(source: str) -> dict[str, ast.AST]:
    """Every module-level name a rendered module BINDS, in body order.

    A class, an ``Annotated`` alias and an annotated assignment alike, because D2 makes
    a referenced node any of the three and the claims below are about the SYMBOL rather
    than about which shape it took.
    """
    out: dict[str, ast.AST] = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            out[node.name] = node
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            out[node.target.id] = node.value if node.value is not None else node
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            out[node.targets[0].id] = node.value
    return out


def fields_of(source: str, name: str) -> dict[str, ast.AST]:
    """``field -> annotation`` for the class ``name`` of a rendered module."""
    cls = next(
        c for c in ast.parse(source).body if isinstance(c, ast.ClassDef) and c.name == name
    )
    return {
        t.target.id: t.annotation
        for t in cls.body
        if isinstance(t, ast.AnnAssign) and isinstance(t.target, ast.Name)
    }


def schema_ref_of(source: str, name: str) -> str:
    """The ``__adcp_schema__`` expression in the class ``name``'s own body."""
    cls = next(
        c for c in ast.parse(source).body if isinstance(c, ast.ClassDef) and c.name == name
    )
    return next(
        ast.unparse(t.value)
        for t in cls.body
        if isinstance(t, ast.AnnAssign) and getattr(t.target, "id", None) == "__adcp_schema__"
    )


def test_a_local_reference_is_a_symbol_this_module_declares_and_not_an_import(
    tmp_path: Path,
) -> None:
    """The exit condition for the local half, and every claim here is load-bearing.

    A local reference resolves against the REFERRER, so there is no module to import
    from: the symbol is one THIS module declares, the property NAMES it, and no import
    is written for it.  Each half passes while another fails -- a symbol nothing names
    is dead code, a property restating the entry's bound spells the fact twice, and an
    import of a local symbol is an ``ImportError`` no AST assertion sees.
    """
    root = write_bundle(tmp_path, {"core/catalog.json": SECTIONS})
    out = emit.emit(root, ["core/catalog.json"])
    assert out.refusals == {}, out.refusals
    # The closure is this document ALONE: a local reference names no other document.
    assert sorted(out.emitted) == ["core/catalog.json"], out.emitted

    source = out.files["core/catalog.py"]
    declared = declared_in(source)
    # D3's nested rule with the document as the parent: root symbol + the entry's key.
    assert "CatalogSlot" in declared, sorted(declared)
    assert "CatalogCode" in declared, sorted(declared)
    assert isinstance(declared["CatalogSlot"], ast.ClassDef), "an object entry is a class"

    imported = {
        a.name
        for n in ast.walk(ast.parse(source))
        if isinstance(n, ast.ImportFrom)
        for a in n.names
    }
    assert not {"CatalogSlot", "CatalogCode"} & imported, sorted(imported)

    fields = fields_of(source, "Catalog")
    for key, symbol in (
        ("slot", "CatalogSlot"),
        ("code", "CatalogCode"),
        ("also_code", "CatalogCode"),
    ):
        got = fields[key]
        assert symbol in {n.id for n in ast.walk(got) if isinstance(n, ast.Name)}, key
        # Nothing but a name and an annotation rides on the property: the entry's own
        # bound has nowhere else in the module to hide.
        extra = kwargs_of(got) - {"description", "alias", "default", "json_schema_extra"}
        assert extra == set(), (key, sorted(extra))
    # One symbol for one node, though two properties name it.
    assert source.count("CatalogCode = ") == 1, source
    # The bound IS reachable from the alias -- here through the type D5 names it once
    # as, read off THIS run's alias module rather than the committed one.
    named = constraint_aliases(out.beside["constraints.py"])
    assert {"min_length", "max_length"} <= stated_by(declared["CatalogCode"], named), named

    # Each entry's symbol is bound BEFORE the root class that uses it, which is what
    # declaring on demand buys: the module is valid Python read top to bottom.
    names = list(declared)
    assert names.index("CatalogSlot") < names.index("Catalog"), names
    assert names.index("CatalogCode") < names.index("Catalog"), names


def test_a_local_entry_that_is_a_class_names_its_own_pointer_and_not_the_roots(
    tmp_path: Path,
) -> None:
    """Section 2's rule, at a pointer no pair had ever named before this step.

    A declared node carries ``__adcp_schema__`` naming ITS OWN node -- this document,
    and the pointer of the entry -- never the root's ``#``.  There is no binding table
    and no adapter, so the class finds its schema through its own attribute and a
    grader cannot be aimed at the wrong node.
    """
    root = write_bundle(tmp_path, {"core/catalog.json": SECTIONS})
    out = emit.emit(root, ["core/catalog.json"])
    entry = schema_ref_of(out.files["core/catalog.py"], "CatalogSlot")
    assert "core/catalog.json" in entry, entry
    assert "#/definitions/slot" in entry, entry
    # And the root's is the ROOT's, so the two are not one string.
    root_ref = schema_ref_of(out.files["core/catalog.py"], "Catalog")
    assert "#/definitions" not in root_ref, root_ref
    assert root_ref != entry

    # The pointer LANDS in the document the run writes beside the module, which is what
    # ``strict_validate`` reads: a ref naming a node the package cannot resolve would
    # be a class that raises on every validation instead of grading.
    written = json.loads(out.files["core/catalog.json"])
    assert node_at(written, "/definitions/slot") is not NOTHING
    assert node_at(written, "/definitions/slot")["properties"] == {"a": {"type": "string"}}


def test_an_entry_nothing_references_is_not_declared(tmp_path: Path) -> None:
    """**`salesagent-j3k2l.20`'s deliberate decision, asserted in both directions.**

    ``definitions`` and ``$defs`` assert nothing about an instance, so an entry no
    reference reaches cannot change what the document accepts or refuses -- and
    declaring it would emit a class no field names, nothing imports and ``__all__``
    does not export.  Its only reachable effect is the wrong one: a keyword inside a
    DEAD section would refuse the whole document.

    Measured on the bundle: 11 of the 157 entries in the 40 documents this step
    unblocks are referenced by nothing, and all 11 sit in ``a2ui/si-catalog.json``,
    whose 24 ``$ref``\\ s are all inside that dead section -- so declaring them would
    also pull that target's whole closure into a module no instance reaches.  Those
    same 24 are why that document is refused once D2's ``const`` row lets the walk
    reach it: ``bundle.resolved`` does not descend a section, so the document the
    package would carry is not locally decidable (``codegen.emit``).

    The second direction is what makes the first non-vacuous: the same keyword in a
    REFERENCED entry still refuses, so the pass below is the skip and not a hole in the
    keyword screen.
    """
    root = write_bundle(tmp_path, {"core/catalog.json": SECTIONS})
    out = emit.emit(root, ["core/catalog.json"])
    assert "CatalogUnused" not in declared_in(out.files["core/catalog.py"])
    assert "Unused" not in out.files["core/catalog.py"]

    dead = {
        **SECTIONS,
        "definitions": {
            **SECTIONS["definitions"],
            # A shape the emitter refuses SOMEWHERE inside, which is all this fixture
            # needs: the dead half asserts no refusal, the live half asserts one, and
            # the contrast is the measurement.
            #
            # **The keyword is deliberately no longer pinned, because pinning it has
            # broken this fixture twice.**  It was ``const`` until D2's ``const`` row
            # landed (salesagent-j3k2l.16); it became ``allOf`` on the ground that
            # ``allOf`` was "a keyword no row lowers at a property", and
            # salesagent-j3k2l.18 then lowered exactly that.  The shape still refuses
            # -- one level deeper, at the conjunct's own ``type`` -- so the fixture is
            # still live, but a fixture that names the keyword a row is about to claim
            # grades the skip only until that row lands.  No keyword is immune to the
            # next row, so the assertions below grade the thing this test is named for:
            # whether the entry was WALKED, read off the refusal's pointer.
            "unused": {
                "type": "object",
                "properties": {"b": {"allOf": [{"type": "string"}]}},
                "required": ["b"],
            },
        },
    }
    root = write_bundle(tmp_path / "b", {"core/catalog.json": dead})
    assert emit.emit(root, ["core/catalog.json"]).refusals == {}

    live = {
        **SECTIONS,
        "definitions": {
            **SECTIONS["definitions"],
            "slot": {
                "type": "object",
                "properties": {"a": {"allOf": [{"type": "string"}]}},
                "required": ["a"],
            },
        },
    }
    root = write_bundle(tmp_path / "c", {"core/catalog.json": live})
    r = refusal_for(root, "core/catalog.json")
    # The SAME shape, in a referenced entry, refuses -- and the refusal is INSIDE the
    # entry, which is what says the walk reached it.  Whichever keyword the emitter
    # stops on, and however deep inside the property it stops, the pointer still names
    # the entry; that is the fact the dead half's silence is contrasted against.
    assert r["keyword"], r
    assert r["pointer"].startswith("/definitions/slot/properties/a"), r


def test_a_local_reference_to_an_entry_declared_later_costs_nothing(tmp_path: Path) -> None:
    """Declared ON DEMAND, so a FORWARD reference needs no topological order.

    20 of the bundle's local references name an entry their own document lists after
    the one referring to it, across 4 documents (``brand.json`` 7,
    ``core/placement-presentation.json`` 5, ``core/registry-event.json`` 4,
    ``core/bidding-policy-capability.json`` 4).  An eager pass over the section in
    document order would need a sort over the reference graph to put each symbol in the
    module before its user; asking for the symbol is what orders them instead.
    """
    doc = {
        "title": "Chain",
        "type": "object",
        "properties": {"a": {"$ref": "#/definitions/first"}},
        "required": ["a"],
        "definitions": {
            # ``first`` is listed FIRST and references ``second``.
            "first": {
                "type": "object",
                "properties": {"x": {"$ref": "#/definitions/second"}},
                "required": ["x"],
            },
            "second": {
                "type": "object",
                "properties": {"y": {"type": "string"}},
                "required": ["y"],
            },
        },
    }
    root = write_bundle(tmp_path, {"core/chain.json": doc})
    out = emit.emit(root, ["core/chain.json"])
    assert out.refusals == {}, out.refusals
    names = list(declared_in(out.files["core/chain.py"]))
    assert {"ChainFirst", "ChainSecond", "Chain"} <= set(names), names
    assert names.index("ChainSecond") < names.index("ChainFirst") < names.index("Chain"), names


def test_a_local_reference_cycle_refuses_rather_than_recurring(tmp_path: Path) -> None:
    """Two entries naming each other is a recursive type, and nothing here spells one.

    0 documents of the bundle are in that position, which is why this refuses rather
    than growing a forward-declaration scheme -- the same answer, and the same
    in-flight shape, ``emit.emit`` already gives a cross-DOCUMENT reference cycle.
    Probed by making it fail: with ``Module.resolving`` removed, both halves below
    recurse to Python's own limit, which is a ``RecursionError`` at the gate rather
    than a document refused by name.
    """
    doc = {
        "title": "Loop",
        "type": "object",
        "properties": {"a": {"$ref": "#/definitions/one"}},
        "required": ["a"],
        "definitions": {
            "one": {
                "type": "object",
                "properties": {"x": {"$ref": "#/definitions/two"}},
                "required": ["x"],
            },
            "two": {
                "type": "object",
                "properties": {"y": {"$ref": "#/definitions/one"}},
                "required": ["y"],
            },
        },
    }
    root = write_bundle(tmp_path, {"core/loop.json": doc})
    r = refusal_for(root, "core/loop.json")
    assert r["keyword"] == "$ref", r
    # The whole chain is named, so the reader does not have to find the loop again.
    assert "local reference cycle" in r["detail"], r
    assert "#/definitions/one" in r["detail"] and "#/definitions/two" in r["detail"], r

    # A SELF reference is the one-hop case and reads the same way.
    doc = {
        **doc,
        "definitions": {
            "one": {
                "type": "object",
                "properties": {"x": {"$ref": "#/definitions/one"}},
                "required": ["x"],
            }
        },
    }
    root = write_bundle(tmp_path / "b", {"core/loop.json": doc})
    assert "local reference cycle" in refusal_for(root, "core/loop.json")["detail"]


def test_two_entry_keys_deriving_one_name_fail_the_build(tmp_path: Path) -> None:
    """``class_name`` strips punctuation, so ``a_b`` and ``a.b`` derive one symbol.

    This is why ``compiler.local_reference`` writes no identifier check of its own: an
    identifier root concatenated with ``class_name``'s alphanumerics is always an
    identifier, and what CAN go wrong is a collision, which ``Module.declare`` already
    fails the build for by naming the symbol.  Probed by making it fail, because a rule
    nothing can break is a finding about the rule.
    """
    doc = {
        "title": "Collide",
        "type": "object",
        "properties": {
            "p": {"$ref": "#/definitions/a_b"},
            "q": {"$ref": "#/definitions/a.b"},
        },
        "required": ["p", "q"],
        "definitions": {
            "a_b": {"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
            "a.b": {"type": "object", "properties": {"y": {"type": "string"}}, "required": ["y"]},
        },
    }
    root = write_bundle(tmp_path, {"core/collide.json": doc})
    r = refusal_for(root, "core/collide.json")
    assert r["keyword"] == "title", r
    assert "CollideAB" in r["detail"], r


def test_no_document_of_the_bundle_refuses_on_a_definition_section_any_more() -> None:
    """`salesagent-j3k2l.20`'s exit condition, over the whole population.

    ``definitions`` and ``$defs`` were 40 of the 653 refusals -- 35 and 5, every one at
    the root, every one answering "a later D2 row does" with no such row scheduled
    anywhere.  Each of the 40 now either emits or refuses on a keyword D2 NAMES and a
    scheduled step owns, which is what a refusal is allowed to say.

    The POPULATION is derived here rather than listed, because a keyword census alone
    cannot tell a document that moved from one the selectors stopped claiming.
    """
    portable = claimed("bundle.portable", bundle.portable(BUNDLE))
    out = emit.emit(BUNDLE, sorted(portable))
    partitions(portable, emitted=set(out.emitted), refused=set(out.refusals))
    on_sections = {
        d: r for d, r in out.refusals.items() if r["keyword"] in ("definitions", "$defs")
    }
    assert on_sections == {}, on_sections

    roots = [
        d
        for d in bundle.portable(BUNDLE)
        if any(isinstance(bundle.read(BUNDLE, d).get(k), dict) for k in bundle.DEFINITIONS)
    ]
    claimed("documents carrying a definitions section", roots, inside=portable)
    for document in roots:
        r = out.refusals.get(document)
        if r is None:
            continue
        assert r["keyword"] not in ("definitions", "$defs"), (document, r)
        assert r["keyword"] and r["pointer"] and r["detail"], (document, r)


def test_the_bundles_own_sections_are_walked_and_the_closure_follows() -> None:
    """The POSITIVE path on the real bundle, which the committed tree cannot grade.

    15 of the 45 documents emit at 0130e5fc9 -- it was 6 at 16052ffb0 and 0 of 40
    when this was written -- and the other 30 are each held by a keyword another
    step owns (``$ref`` 9, ``oneOf`` 5, ``allOf`` 4, ``anyOf`` 4,
    ``discriminator`` 3, ``properties`` 3, ``uniqueItems`` 2).  The constructed
    bundles above are what grade the declaration itself.  What the real bundle
    grades is the WALK, in the two places it is observable:

    * a refusal at a pointer INSIDE a section is proof the walk descended one.  9
      documents are in that position, and none was before: every pointer under
      ``definitions`` used to be unreachable.
    * a refusal that moved from the root to a property means the walk got FURTHER, and
      the closure then reaches what those earlier properties name.
      ``governance/policy-entry.json`` is the case: it refused at ``/`` on ``$defs``
      before any of its 8 property references was read, and now refuses at
      ``/properties/acceptance_profile`` -- so the three enum documents its earlier
      properties name are emitted over step 1, 2 and 4's population, and no member of
      that population references two of the three from anywhere else.
    """
    out = emit.emit(BUNDLE, sorted(bundle.portable(BUNDLE)))
    inside = {
        d: r["pointer"]
        for d, r in out.refusals.items()
        if r["pointer"].lstrip("/").split("/")[0] in bundle.DEFINITIONS
    }
    # 8 -> 9 at ``salesagent-j3k2l.40``, and the ninth is the walk getting FURTHER
    # rather than a new kind of refusal: ``brand.json`` refused at ``/oneOf/4`` on the
    # branch that composes, and now that a composing branch is lowered it refuses at
    # ``/definitions/default_language/allOf/0`` -- a verdict, on a base that is an
    # alias, three hops inside a section.  No member left; the other 8 are unchanged.
    #
    # 9 -> 7 at ``salesagent-j3k2l.28``, and BOTH halves of the move are the walk
    # finishing rather than stopping earlier.  Two documents LEFT because they emit:
    # ``core/bidding-policy-capability.json`` (refused at
    # ``/definitions/policy_profile/properties/supported_combinations/items/oneOf/0``)
    # and ``core/targeting-overlay-support.json`` (at
    # ``/definitions/countrySupport/anyOf/0``) -- both on the local-``$ref`` branch
    # guard that row removed.  And ``governance/reported-outcome-error.json``'s
    # pointer went DEEPER, ``/definitions/bounded_value/anyOf/0`` ->
    # ``/definitions/bounded_value_level_3/anyOf/1``, for the same reason: the first
    # branch lowers now and the walk reaches the third level.  No member joined.
    #
    # 7 -> 8 at ``salesagent-j3k2l.21``, and the eighth is the walk getting FURTHER
    # for the third time in this test's history rather than a document becoming
    # unrepresentable.  ``core/geo-place-requirement.json`` joined, and the cause is
    # MEASURED on trunk rather than inferred from the count: at 8c021bffa it refused
    # at ``/properties/systems/propertyNames`` on ``$ref``, kind ``deferred``,
    # CHAINED to ``core/geo-place-system.json``'s own refusal -- "a branch of type
    # 'string' is step 6", which is this row's ground.  That target is a root
    # ``anyOf`` of scalars and now lowers, so the chain clears and the walk descends
    # into the section, where it meets ``pattern`` on
    # ``/definitions/catalogRequirement/properties/countries/propertyNames``.
    #
    # That surviving refusal was not that row's: its detail was
    # ``salesagent-j3k2l.64``'s ground verbatim -- a constrained-str key pydantic
    # renders back as ``patternProperties``, so the symmetric comparison reported one
    # added and two missing facts -- and section 5's ``propertyNames`` row decides
    # that position: ``pattern`` -> an annotated ``str`` key.
    #
    # **``.64`` emitted that key and the document stayed, which is the walk getting
    # FURTHER a fourth time rather than the count holding still.**  It was predicted
    # here that .64 would take the count 8 -> 7; it did not, and the measurement is
    # why: with the key lowered, the walk descends ONE MORE HOP into the same
    # property and meets ``uniqueItems`` on the array inside the mapping's VALUE --
    # ``/definitions/catalogRequirement/properties/countries/additionalProperties``,
    # a verdict on an array with no class above it (``lower.containers``'s
    # ``_DISTINCT_HAS_NOWHERE_TO_LIVE``).  So the member is unchanged, the count is
    # unchanged, and the POINTER is what moved -- which is exactly why this test pins
    # pointers and not a total.
    #
    # NAMED, NOT COUNTED: the count went 7 -> 8 -> 9 -> 8 over four rows, each move a
    # document joining or leaving for a cause measured at the time, and a number going
    # back down says nothing about which document moved.  The two pointers asserted
    # below are what make this evidence of a DESCENT into the section rather than of
    # the section being read, and they are what a count could never say.
    claimed("documents refusing inside a definitions section", inside)
    assert inside["core/geo-place-requirement.json"] == (
        "/definitions/catalogRequirement/properties/countries/additionalProperties"
    )
    # Pinned by name because a count alone cannot say the pointer went INTO a
    # section.  This was ``core/response-payload-jws-envelope.json`` at
    # ``/definitions/response_payload/properties/typ``; that document EMITS as of
    # 16052ffb0, so it left this population and the pin moved to the deepest
    # section pointer the bundle still refuses at -- three hops past the section
    # name, which is what makes it evidence of a descent rather than of the
    # section being read.  It held across 0130e5fc9, where the membership of the
    # other seven changed and the count went 7 -> 8, and across
    # ``salesagent-j3k2l.40``, where ``brand.json`` joined and took it 8 -> 9.
    assert inside["core/account-identity-change-preview.json"] == (
        "/definitions/nonblocking_impacts/items/allOf/0"
    )

    entry = out.refusals["governance/policy-entry.json"]
    assert entry["pointer"] == "/properties/acceptance_profile", entry
    read = lambda d: bundle.read(BUNDLE, d)  # noqa: E731
    pop = sorted(
        {
            d
            for d in bundle.portable(BUNDLE)
            if bundle.is_leaf_object(read(d))
            or bundle.references_a_property(read(d))
            or bundle.composes_at_the_root(read(d))
        }
    )
    reached = set(emit.emit(BUNDLE, pop).emitted)
    known = set(bundle.portable(BUNDLE))
    for document in (
        "enums/governance-domain.json",
        "enums/policy-category.json",
        "enums/policy-enforcement.json",
    ):
        assert document in reached, document
        # And the reference that reaches it is one of policy-entry's own.
        assert document in {
            bundle.document_for(bundle.split_ref(u)[0], known)
            for _, u in bundle.references(read("governance/policy-entry.json"))
            if bundle.split_ref(u)[0]
        }, document


# --------------------------------------------------------------------------- #
# what the carried document owes a reference under a section
# (`salesagent-j3k2l.71`)
# --------------------------------------------------------------------------- #
#: A dead section holding a REMOTE reference, which is ``a2ui/si-catalog.json``'s shape
#: reduced to one entry: the root asserts something of its own, the section asserts
#: nothing, and the only reference in the document sits inside the dead entry.  The
#: second fixture below is this one with a ``$ref`` naming the entry, so the pair
#: differs in the one dimension the rule reads and in nothing else.
DEAD_SECTION_REMOTE = {
    "title": "Dead Section Catalog",
    "type": "object",
    "properties": {"label": {"type": "string"}},
    "definitions": {
        "Widget": {
            "type": "object",
            "properties": {"body": {"$ref": f"{BASE}core/target.json"}},
            "required": ["body"],
        }
    },
}


def _remote_under_a_section() -> dict[str, list[tuple[str, str]]]:
    """``document -> [(pointer, uri)]`` for every REMOTE reference the bundle spells
    inside a ``definitions`` / ``$defs`` entry.

    Read off the raw documents and off the one schema-position walk, so this is the
    whole set the rule below splits rather than a set some run happened to reach.
    """
    out: dict[str, list[tuple[str, str]]] = {}
    for document in bundle.portable(BUNDLE):
        doc = bundle.read(BUNDLE, document)
        entries = bundle.section_entries(doc)
        for pointer, uri in bundle.references(doc):
            if bundle.split_ref(uri)[0] and bundle.pointers_above(pointer, entries):
                out.setdefault(document, []).append((pointer, uri))
    return out


def test_a_remote_reference_under_a_section_is_owed_where_its_entry_is_declared() -> None:
    """Section 5's on-demand rule, read on the SCHEMA half.

    ``strict_validate`` decides against the document the emitter writes beside the
    module, so what the carried document owes a reference is whatever the package's own
    validation can reach.  Section 5 makes a section "nothing by itself", each entry
    "declared on demand when a ``$ref`` names it"; section 3 adds "an entry nothing
    references is not declared".  So the obligation follows DECLARATION: an entry some
    ``$ref`` names has a class at its pointer and a reference under it is reached, and
    an entry nothing names has none and is reached by nothing.

    Both halves are named here and asserted non-empty, because a rule whose admitted
    half is empty admits nothing and a rule whose counted half is empty refuses
    nothing -- and either way it reads as working.
    """
    sites = _remote_under_a_section()
    every = claimed(
        "remote references the bundle spells inside a section entry",
        {(d, p) for d, ps in sites.items() for p, _ in ps},
    )
    named = bundle.named_nodes(BUNDLE)

    counted, admitted = set(), set()
    for document, refs in sites.items():
        # The RAW document and not ``bundle.resolved``: the predicate is a function of
        # (document, named) and the references are at their own pointers either way, so
        # resolving 1,054 documents to ask a positional question would cost the whole
        # bundle's resolution for an answer that does not depend on it.
        owed = set(
            bundle.undecidable_references(
                bundle.read(BUNDLE, document), named.get(document, frozenset())
            )
        )
        for pointer, uri in refs:
            (counted if (pointer, uri) in owed else admitted).add((document, pointer))

    partitions(every, owed_resolution=counted, reached_by_nothing=admitted)
    claimed("remote references under a DECLARED entry", counted, inside=every)
    claimed("remote references under an entry nothing declares", admitted, inside=every)

    # And the split is the DECLARATION and not the document, pointer depth or spelling:
    # every admitted reference sits in an entry no ``$ref`` of the bundle names, and
    # every counted one in an entry some ``$ref`` does.
    for document, pointer in sorted(admitted):
        doc = bundle.read(BUNDLE, document)
        entries = bundle.pointers_above(pointer, bundle.section_entries(doc))
        assert entries, (document, pointer)
        assert not bundle.pointers_above(pointer, named.get(document, frozenset())), (
            document,
            pointer,
            sorted(named.get(document, frozenset())),
        )
    for document, pointer in sorted(counted):
        assert bundle.pointers_above(pointer, named.get(document, frozenset())), (
            document,
            pointer,
        )


def test_a_remote_reference_in_a_dead_section_leaves_the_document_decidable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The POSITIVE half on a bundle this file writes, and the measurement is a
    validation with the network removed.

    The document emits with the reference still in the schema it carries, and that
    schema decides: ``jsonschema`` accepts and refuses instances through it while
    ``socket.socket`` is a constructor that raises, so nothing is fetched.  A reference
    in a dead entry is therefore not a document the package cannot decide with -- which
    is what this check refused it for.
    """
    root = write_bundle(
        tmp_path, {"a2ui/catalog.json": DEAD_SECTION_REMOTE, "core/target.json": TARGET}
    )
    out = emit.emit(root, ["a2ui/catalog.json"])
    assert "a2ui/catalog.json" in out.emitted, out.refusals

    # The entry is dead, so no class is declared at its pointer -- which is what makes
    # the position unreachable, and it is asserted rather than assumed.
    source = out.files["a2ui/catalog.py"]
    assert "Widget" not in declared_in(source), sorted(declared_in(source))

    carried = json.loads(out.files["a2ui/catalog.json"])
    left = claimed(
        "remote references the carried document still holds",
        [p for p, u in bundle.references(carried) if bundle.split_ref(u)[0]],
    )
    entries = bundle.section_entries(carried)
    assert all(bundle.pointers_above(p, entries) for p in left), (
        sorted(left),
        sorted(entries),
    )

    # THE NETWORK IS REMOVED, not mocked out at the resolver: anything that tried to
    # fetch the target would have to open a socket, and this one raises on
    # construction.  So the two validations below are the measurement of "decidable
    # locally" rather than a restatement of the predicate under test.
    class Refuses(socket.socket):
        def __init__(self, *a: object, **k: object) -> None:
            raise AssertionError("the validator opened a socket")

    monkeypatch.setattr(socket, "socket", Refuses)
    jsonschema.validate({"label": "x"}, carried)
    with pytest.raises(jsonschema.ValidationError) as err:
        jsonschema.validate({"label": 1}, carried)
    assert err.value.validator == "type", err.value.validator


def test_a_remote_reference_in_a_declared_entry_is_still_refused(tmp_path: Path) -> None:
    """The NEGATIVE half, on the same fixture with the one dimension flipped.

    A ``$ref`` names the entry, so section 5 declares it, a class grades at
    ``#/definitions/Widget`` and ``_refuse_at`` evolves a validator onto that pointer --
    which descends the entry's ``properties`` and meets the reference.  The document is
    then one the package cannot decide with, and it refuses, with the kind that says the
    reference is unresolved rather than that a lowering is missing.
    """
    live = {
        **DEAD_SECTION_REMOTE,
        "properties": {
            **DEAD_SECTION_REMOTE["properties"],
            "widget": {"$ref": "#/definitions/Widget"},
        },
    }
    root = write_bundle(tmp_path, {"a2ui/catalog.json": live, "core/target.json": TARGET})
    r = refusal_for(root, "a2ui/catalog.json")
    assert r["keyword"] == "$ref", r
    assert bundle.pointers_above(
        r["pointer"], bundle.section_entries(bundle.read(root, "a2ui/catalog.json"))
    ) == ["/definitions/Widget"], r
    assert r["resolved"] is Kind.UNRESOLVED, r
    assert f"{BASE}core/target.json" in r["detail"], r


def test_a_property_named_definitions_is_a_property_and_not_a_section(tmp_path: Path) -> None:
    """``section_entries`` reads the WALK, so a segment is a section only where the
    keyword is.

    A property may legitimately be named ``definitions`` -- ``harness.formats_used``
    carries the same caution for ``default``, where a bundle met 95 of them -- and the
    pointer ``/properties/definitions/properties/body`` is then a property's property,
    which no reading of the pointer's TEXT can tell from a section entry.  The 3.2
    bundle holds 0 such properties, so this is graded on a bundle this file writes.

    What the two readings differ on is observable here and nowhere else: a reference at
    that position is REACHED by the resolver -- ``properties`` is one of the keys it
    descends, twice over -- so it is inlined and the document emits with no reference
    left to classify.  A text reading would call the position a section entry, and the
    only place that answer could still be read is a RAW document, which is what this
    file's own census and ``test_emit``'s naming of the admitted entries read.
    """
    doc = {
        "title": "Names A Property Definitions",
        "type": "object",
        "properties": {
            "definitions": {
                "type": "object",
                "properties": {"body": {"$ref": f"{BASE}core/target.json"}},
            }
        },
    }
    assert bundle.section_entries(doc) == frozenset(), bundle.section_entries(doc)
    claimed(
        "references the document spells",
        [p for p, _ in bundle.references(doc)],
    )

    root = write_bundle(tmp_path, {"a2ui/odd.json": doc, "core/target.json": TARGET})
    out = emit.emit(root, ["a2ui/odd.json"])
    assert "a2ui/odd.json" in out.emitted, out.refusals
    carried = json.loads(out.files["a2ui/odd.json"])
    assert bundle.references(carried) == [], bundle.references(carried)
    body = carried["properties"]["definitions"]["properties"]["body"]
    assert "$ref" not in body, body
    assert set(body["properties"]) == set(TARGET["properties"]), body
