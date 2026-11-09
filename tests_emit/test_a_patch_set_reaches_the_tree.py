"""A NON-EMPTY PATCH SET WITH NO EFFECT ON THE EMITTED TREE IS A DEFECT, and this is red for it.

``codegen/patch.py`` existed for nine days, carried five extractions and one addition, was
graded by two test files against the published bundle -- every entry names a defect and an
ask, every verdict is one the bundle's evidence supports, every addition fails the day the
keyword lands -- and **the emitter never saw any of it**:

::

    grep "patch.apply\\|patch.additions" codegen/*.py   ->  nothing

``codegen/__main__.py`` read ``schemas/cache/3.2`` raw, ``./check`` read it raw,
``tests/fresh.py`` read it raw.  The five documents ``patches/8525`` extracts were absent
from every bundle any run opened, so no emitted class ever moved, and
``AAODirectoryAgentPublishersInverseLookupResponsePublisherEntryPublisherDomain`` -- the
71-character per-position name the extraction exists to retire -- was still in
``adcp.types.constraints``.  Every check that could have caught that asked the MANIFEST a
question about the BUNDLE, and the manifest answered correctly each time.

**SO THIS FILE ASKS THE TREE.**  The claim is one sentence: *the tree a run emits from the
patched bundle is not the tree it emits from the published one, and each patch set of
:data:`codegen.patch.BUILD` accounts for part of the difference.*  Both halves are needed --
the first catches a patch set that is not applied at all, and the second catches a patch set
that is applied and does nothing, which is the same defect wearing a wiring.

**TWO COMPILES AND NOT THREE PER SET.**  The attribution does not need a compile per patch
set, because each KIND of entry names the symbol it is responsible for: an extraction names a
new DOCUMENT, so the patched tree holds a module for it and the published tree cannot; an
addition names a NODE, so the class at that provenance is spelled from the keyword the
addition adds.  Asking the entries is what makes the attribution per-set without paying
``len(BUILD)`` compiles of 100 s each.

**A SYMBOL IS RESOLVED BY ``__adcp_schema__`` AND NEVER BY ``__all__[0]``**: ``__all__`` is
sorted, so index 0 is the root for only 1,023 of the 1,054 modules, and that error has
produced 31 phantom failures twice in this project.
"""

from __future__ import annotations

import ast
from pathlib import Path

import fresh
from compiled import compiled

from codegen import bundle, catalogue, emit, patch
from tests.nodeset import claimed

#: The bundle a RUN reads: the published one with every patch set of ``patch.BUILD`` applied.
PATCHED = fresh.BUNDLE
#: The bundle the patch sets are written against, and the one the tree used to be emitted
#: from.  Spelled as ``tests/fresh.py`` spells the other, so the two are one checkout's paths.
PUBLISHED = fresh.REPO / "schemas" / "cache" / "3.2"


def _classes(files: dict[str, str]) -> dict[tuple[str, str], set[str]]:
    """``(document, pointer) -> the class names the tree declares there``, by PROVENANCE."""
    out: dict[tuple[str, str], set[str]] = {}
    for path in sorted(files):
        for node in ast.walk(ast.parse(files[path])):
            if not isinstance(node, ast.ClassDef):
                continue
            for statement in node.body:
                if (
                    isinstance(statement, ast.AnnAssign)
                    and isinstance(statement.target, ast.Name)
                    and statement.target.id == "__adcp_schema__"
                    and isinstance(statement.value, ast.Call)
                ):
                    named = {
                        kw.arg: ast.literal_eval(kw.value) for kw in statement.value.keywords
                    }
                    at = (str(named["document"]), str(named["pointer"]).lstrip("#"))
                    out.setdefault(at, set()).add(node.name)
    return out


def test_the_patched_tree_is_not_the_published_one() -> None:
    """The whole build's claim: applying the patch sets CHANGES the tree a consumer installs.

    Stated over the module text and not over a count, because the figure a reader needs is
    WHICH modules moved -- the message names them -- and because a count over two trees is
    the census equality ``tests/test_every_check_names_its_set.py`` rules out.

    The two compiles are the two bundles over each bundle's OWN portable set: the patched one
    holds five documents the published one does not, so a shared population would ask the
    published compile for a document it cannot read.
    """
    patched = compiled(PATCHED, claimed("the patched bundle's documents", sorted(bundle.portable(PATCHED))))
    published = compiled(PUBLISHED, claimed("the published bundle's documents", sorted(bundle.portable(PUBLISHED))))
    moved = sorted(
        path
        for path in set(patched.files) | set(published.files)
        if patched.files.get(path) != published.files.get(path)
    )
    assert moved != [], (
        "the patch sets of patch.BUILD change no module of the emitted tree: either they are "
        "not in the compile path (codegen.patch.for_build) or they have no effect, and the "
        "two are the same defect"
    )


def test_every_patch_set_of_the_build_accounts_for_part_of_the_difference() -> None:
    """Per SET, so a set that is applied and does nothing cannot hide behind one that works.

    An EXTRACTION's evidence is its document: the patched tree writes a module for it and the
    published tree has no such document to write one from.

    **An ADDITION's evidence is the class at its ENTRY's HOME and not at its own pointer**,
    and that correction is what the first run of this check measured.  A ``title`` names the
    catalogue ENTRY the node belongs to, and the entry is DECLARED at its home -- which §3a's
    home rule may put in another document entirely.  The one addition this repository carries
    titles ``brand.json#/definitions/data_subject_contestation``, whose entry is homed at
    ``core/brand-ref.json#/properties/data_subject_contestation``, so the class that moved is
    ``ObjUrlEmailLanguages`` -> ``DataSubjectContestation`` over there and nothing at all
    moved at the pointer the row names.  A check that looked only at the row's own pointer
    would call a working override inert.

    **An addition that is not a ``title`` has no claim here and says so**, rather than being
    silently skipped: ``patch.additions`` already refuses anything that is not an annotation,
    and of the annotations only a name reaches a symbol.  The assertion is then the one this
    file can honestly make -- that the patched bundle STATES it where the published one does
    not -- and the set still has to account for itself through some other entry.
    """
    sets = claimed("the patch sets the build applies", [Path(name) for name in patch.BUILD])
    patched = compiled(PATCHED, sorted(bundle.portable(PATCHED)))
    published = compiled(PUBLISHED, sorted(bundle.portable(PUBLISHED)))
    packages = bundle.package_roots(PATCHED)
    here = _classes(patched.files)
    there = _classes(published.files)
    #: position -> the position its catalogue entry is DECLARED at, over the patched bundle.
    #: Read off ``collect_shapes``' own parts and never re-derived (§3a: "a derived reading of
    #: the bundle is an argument, not something a callee recomputes").
    homed: dict[tuple[str, str], tuple[str, str]] = {}
    for entry in catalogue.collect_shapes(
        catalogue.Admitted(PATCHED), "L2", emit.standing_order(PATCHED)
    ).entries.values():
        for position in entry.positions:
            homed[position.document, position.pointer] = (entry.at.document, entry.at.pointer)
    for patch_set in sets:
        evidence: list[str] = []
        for held in patch.load(patch_set, PUBLISHED):
            # ``module_file`` answers the module's path WITHOUT a suffix (it is also the
            # import path), and ``Emitted.files`` is keyed by the file -- so the suffix is
            # added here rather than the two readings being allowed to differ silently.
            module = f"{emit.module_file(held.document, packages)}.py"
            if module in patched.files and module not in published.files:
                evidence.append(f"{module} (extracted {held.document})")
        for grows in patch.additions(patch_set, PUBLISHED):
            at = homed.get((grows.document, grows.pointer), (grows.document, grows.pointer))
            if grows.keyword == "title" and here.get(at) != there.get(at):
                evidence.append(
                    f"{at[0]}#{at[1] or '/'} declares "
                    f"{sorted(here.get(at, ()))} and declared {sorted(there.get(at, ()))}"
                )
            elif grows.keyword != "title":
                node = bundle.node_at(bundle.read(PATCHED, grows.document), grows.pointer)
                assert node.get(grows.keyword) == grows.value, (grows.document, grows.pointer)
        assert evidence != [], (
            f"{patch_set} is applied and changes nothing in the emitted tree: no document it "
            f"extracts became a module and no node it titles moved a class name. A patch set "
            f"with no effect is the defect this file exists for, whether it is unwired or "
            f"inert"
        )
