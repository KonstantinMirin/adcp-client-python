"""The public domain module is a COMPOSITION and nothing else, byte for byte.

**WHY THIS FILE EXISTS, and it is a cost the ruling it serves states openly.**
``codegen/emit.py``'s ``SURFACE`` moved §1's domain aggregator to
``adcp.types._surface.core`` -- a file the compiler owns outright -- so that
``adcp.types.core`` could stay the public path and serve upstream's 444 lines of
hand-written SDK machinery beside 1,522 emitted names.  The two name sets may share a
module PATH and must not share one FILE: ``emit.write`` is handed a FRESH EMPTY directory,
so a read-modify-write emitter's output can never equal the committed file, and a marked
region would force ``test_emit.test_the_committed_tree_is_what_a_fresh_run_emits`` down
from "every byte of every file" to "a region" -- which cannot see a hand edit outside the
markers nor a marker moved inward.

The honest cost is that the 23 public modules LEAVE that byte compare, because they stop
being files the compiler writes.  **This file is what stands over them instead, and it is a
byte compare too**: the composition is DERIVED here, once, from the domain list the
compiler itself records and from ``adcp/_client_types.py``'s own declarations, and every
committed public module's WHOLE TEXT must equal it.  So a name added to one of those files
by hand reddens, a docstring edited reddens, and the machinery list cannot go stale against
the module it re-exports -- which a hand-maintained list in those files could.

**WHAT ``__all__`` IS, because the choice is forced by another gate rather than taken
here.**  The public module's ``__all__`` is the aggregator's, which is the COMPILER's
export set.  ``test_the_domain_surface.py`` reads that list as "every name resolves at
exactly one private ``adcp.types._schemas`` path and IS the object that path holds", and
``test_the_surface_provenance.py`` reads it as "every class advertised was declared inside
the emitted tree".  Upstream's ``TaskResult`` answers neither -- it has no document and
``adcp._client_types`` declared it -- so putting it in ``__all__`` would make both of those
gates red for a name that is correctly present.  It is importable at
``adcp.types.core`` in the ``X as X`` form a type checker reads as a re-export, and it is
advertised only where the compiler put a name.  :func:`test_the_machinery_is_importable_and_not_advertised`
holds both halves, and the finding that goes with it is in
``/srv/ws/.adcp-scratch/verdicts/surface.md``.

Perturbed in :func:`test_the_text_compare_reddens_on_a_hand_edit`, which calls the SAME
derivation the green direction calls over a mutated copy of a real file's text.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path

import fresh
import pytest
from nodeset import claimed

from codegen import bundle, emit

from compiled import compiled

#: ``src/adcp/types``, the directory holding both halves of the seam.
TYPES = Path(__file__).resolve().parents[1] / "src" / "adcp" / "types"

#: Upstream's restored hand-written SDK types, at the SDK's own namespace.
#:
#: The path and not the name set: what the composition re-exports is derived from this
#: file's own declarations below, so a release that adds one of upstream's types adds a
#: re-export with nothing here edited -- and a release that removes one reddens.
CLIENT_TYPES = TYPES.parent / "_client_types.py"

#: The domain whose word upstream also used for hand-written machinery.
#:
#: ONE, and derived rather than asserted: :func:`test_one_domain_composes_the_machinery`
#: measures that ``core`` is the only domain of the compiler's whose word names a module
#: upstream hand-wrote outside the generated tree, which is this lane's own reading of
#: ``survey/upstream-machinery-9.6.1.tsv``'s six restored rows plus ``core``.
COMPOSES_MACHINERY = "core"


def domains() -> list[str]:
    """The public domain modules, off the compiler's own export record.

    The same derivation ``test_emit.test_the_committed_tree_is_what_a_fresh_run_emits``
    and ``test_the_surface_provenance.py`` use, so no two of the three can disagree about
    which public modules exist.
    """
    out = compiled(fresh.BUNDLE, sorted(bundle.portable(fresh.BUNDLE)))
    return sorted({emit.module_domain(m) for m, exported in out.surface.items() if exported})


def machinery() -> list[str]:
    """The names ``adcp/_client_types.py`` makes public, from its own source.

    A module-scope ``class``, ``def`` or assignment whose name is public, plus an
    ``X as X`` import -- which is upstream's own re-export of
    ``DEFAULT_MAX_RESPONSE_BYTES`` and is the one form PEP 484 reads as public.  A plain
    ``import`` is machinery the module needed and not a name it offers, and a ``TypeVar``
    is dropped for ``test_emit._is_type_variable``'s reason: it is a parameter, never
    imported anywhere, and counting it would put a name in the composition that no
    consumer writes.
    """
    found: set[str] = set()
    for node in ast.parse(CLIENT_TYPES.read_text(encoding="utf8")).body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                found.add(node.name)
        elif isinstance(node, ast.Assign):
            value = node.value
            if isinstance(value, ast.Call) and getattr(value.func, "id", "") == "TypeVar":
                continue
            found.update(
                t.id for t in node.targets if isinstance(t, ast.Name) and not t.id.startswith("_")
            )
        elif isinstance(node, ast.ImportFrom):
            found.update(
                a.name for a in node.names if a.asname == a.name and not a.name.startswith("_")
            )
    return sorted(found)


def composition(domain: str, restored: list[str]) -> str:
    """The WHOLE TEXT of ``src/adcp/types/<domain>.py``, derived.

    Two statements for every domain -- the star import, which is the eager half the
    ruling requires, and the aggregator's own ``__all__``, which is what makes the public
    module advertise exactly §1's export set.  Neither names a type.

    ``restored`` is the machinery the domain composes, in the ``X as X`` form.  Empty for
    every domain but one, and the text is one function so that the composition cannot
    come to differ between the domain that needs the extra statements and the 22 that do
    not.
    """
    lines = [
        f'"""The public path of the ``{domain}`` domain: §1\'s one import path for its classes.',
        "",
        "The names are the compiler's, re-exported in one line from the aggregator it owns",
        f"outright and compares byte for byte, ``adcp.types._surface.{domain}``.  This file is the",
        "COMPOSITION: it declares nothing, lists nothing, and the object reached at a name here",
        "is the class the private per-document module built.  Why the aggregator is a second",
        "file rather than this one is in ``adcp.types``' own docstring and in the ruling",
        "``codegen/emit.py``'s ``SURFACE`` carries.",
    ]
    if restored:
        lines += [
            "",
            "**AND THIS IS THE ONE DOMAIN WHOSE WORD UPSTREAM ALSO USED FOR HAND-WRITTEN",
            "MACHINERY.**  Upstream's module at this path was 444 lines of the SDK's own types --",
            "``TaskResult``, ``AgentConfig``, ``DebugInfo``, ``Member`` -- and no bundle document",
            "states any of them.  They are restored at ``adcp._client_types``, the SDK's own",
            "namespace, and re-exported below in the ``X as X`` form a type checker reads as a",
            "re-export, so that ``from adcp.types.core import TaskResult`` resolves to upstream's",
            "class and not to something invented for the word.",
            "",
            "**They are deliberately NOT in ``__all__``, and the reason is another gate's",
            "reading rather than taste.**  ``__all__`` here is the aggregator's, which is the",
            'COMPILER\'s export set: ``tests_emit/test_the_domain_surface.py`` reads it as "every',
            'name resolves at exactly one private path and IS the object that path holds", and a',
            "name with no document behind it answers neither half.  A name is importable here",
            "and advertised only where the compiler put it.",
            "",
            "**``TaskStatus`` and ``Protocol`` are the same WORD as ours and a different concept,",
            "and nothing is aliased between them.**  Upstream's ``TaskStatus`` has five members",
            "including ``needs_input``; ours, from ``enums/task-status.json``, has nine including",
            "``input-required``, and neither set contains the other.  Ours stays at",
            "``adcp.types.enums`` and upstream's resolves here.  Upstream's ``Protocol`` is",
            "``{a2a, mcp}``, a transport selector, against a protocol-domain enumeration of ours",
            "with no shared value.  See ``docs/migration-from-upstream.md`` §5, which is written",
            "from this exact case.",
        ]
    lines += ['"""', ""]
    body = [
        f"from ._surface.{domain} import *  # noqa: F403",
        f"from ._surface.{domain} import __all__ as __all__",
    ]
    if restored:
        body = [
            *(f"from .._client_types import {name} as {name}" for name in restored),
            "",
            *body,
        ]
    return "\n".join([*lines, *body, ""])


def expected(domain: str) -> str:
    """The composition for ``domain``, with the machinery the one domain composes."""
    return composition(domain, machinery() if domain == COMPOSES_MACHINERY else [])


# --------------------------------------------------------------------------- #
# the populations are real, so nothing below holds vacuously
# --------------------------------------------------------------------------- #
def test_each_clause_has_a_population() -> None:
    """The domains, the machinery names, and the aggregator the compiler writes beside."""
    found = claimed("public domain modules", domains())
    claimed("names upstream's restored machinery makes public", machinery())
    assert COMPOSES_MACHINERY in found, (COMPOSES_MACHINERY, sorted(found))
    # The aggregator package is where the compiler writes, read off the emitter.
    assert (TYPES / emit.SURFACE / "__init__.py").is_file(), emit.SURFACE
    assert sorted(p.stem for p in (TYPES / emit.SURFACE).glob("*.py") if p.stem != "__init__") == (
        sorted(found)
    )


# --------------------------------------------------------------------------- #
# the reading: the committed public module IS the derived composition
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("domain", domains())
def test_the_public_module_is_exactly_the_derived_composition(domain: str) -> None:
    """One subject per domain, so a hand edit lands under the module it was made to.

    The whole file and every byte of it, against text derived from the compiler's domain
    record and from ``adcp/_client_types.py``'s own declarations.  This is the compare the
    public module lost when it stopped being a file the compiler writes.
    """
    path = TYPES / f"{domain}.py"
    assert path.is_file(), f"{path} is the public path of a domain the compiler aggregates"
    assert path.read_text(encoding="utf8") == expected(domain), (
        f"src/adcp/types/{domain}.py is not the composition it is derived from. It is a "
        "hand-written file at a public path and this is the only compare over it: either "
        "the edit belongs in the aggregator the compiler owns, or in this derivation."
    )


def test_the_composition_names_no_type_of_its_own() -> None:
    """Every statement of every public module is an import, and nothing is declared.

    Read off the AST rather than off the text, so it is a second reading of the same
    property and not a restatement of the compare above: a public module that declared a
    class would be a hand-written type at a path a consumer takes for the compiler's.
    """
    for domain in domains():
        tree = ast.parse((TYPES / f"{domain}.py").read_text(encoding="utf8"))
        kinds = {type(node).__name__ for node in tree.body}
        assert kinds <= {"Expr", "ImportFrom"}, (domain, sorted(kinds))
        for node in tree.body:
            if isinstance(node, ast.ImportFrom):
                assert node.level in (1, 2), (domain, node.module, node.level)


def test_one_domain_composes_the_machinery() -> None:
    """``core`` is the only domain whose word upstream also used for a hand-written module.

    Derived from ``survey/upstream-machinery-9.6.1.tsv`` -- upstream's own classification of
    its 49 non-generated ``types/`` files -- intersected with the compiler's domain list, so
    a seventh restored module landing on a domain's word reddens here rather than being
    served silently by one composition and not another.
    """
    rows = (TYPES.parents[2] / "survey" / "upstream-machinery-9.6.1.tsv").read_text(
        encoding="utf8"
    )
    hand_written = {
        line.split("\t")[0]
        for line in rows.splitlines()
        if line and not line.startswith("#") and not line.startswith("module\t")
        and line.split("\t")[7] == "0"  # generated_header: upstream names no generator
    }
    claimed("upstream's hand-written types/ modules", hand_written)
    collide = hand_written & set(domains())
    # ``core`` is the one, and the four curated topic modules are NOT: they re-export the
    # same subjects we emit and nothing of upstream's source imports one, which is this
    # lane's reading of the TSV's own src-importer columns.  So the set is checked for the
    # one name that needs a composition rather than for emptiness.
    assert COMPOSES_MACHINERY in collide, sorted(collide)
    composed = {d for d in domains() if "from .._client_types import" in expected(d)}
    assert composed == {COMPOSES_MACHINERY}, sorted(composed)


# --------------------------------------------------------------------------- #
# the seam, at run time
# --------------------------------------------------------------------------- #
def test_the_public_all_is_the_aggregators() -> None:
    """The public module advertises exactly the compiler's export set, per domain.

    Not a subset and not a superset: the list is the aggregator's own object, so a
    composition that rebuilt it could not drift, and this reading is what says the
    rebuilding never happens.
    """
    for one in domains():
        public = importlib.import_module(f"adcp.types.{one}")
        inner = importlib.import_module(f"adcp.types.{emit.SURFACE}.{one}")
        assert public.__all__ == inner.__all__, one
        assert public.__all__ is inner.__all__, f"{one} rebuilt the export set"


@pytest.mark.parametrize("domain", domains())
def test_one_object_across_the_seam(domain: str) -> None:
    """A name reachable at three paths is ONE object, for every advertised class.

    The public path, the aggregator the compiler owns, and the private per-document
    module the class was declared in.  This is §1's one-path rule asked of the seam: a
    composition that minted or copied anything would hand a consumer a class whose
    ``isinstance`` is false against what the runtime validates into.
    """
    public = importlib.import_module(f"adcp.types.{domain}")
    inner = importlib.import_module(f"adcp.types.{emit.SURFACE}.{domain}")
    checked = 0
    for name in public.__all__:
        obj = getattr(public, name)
        assert obj is getattr(inner, name), f"adcp.types.{domain}.{name}"
        home = getattr(obj, "__module__", "") if isinstance(obj, type) else ""
        if home.startswith("adcp.types._schemas"):
            # The WORD a domain publishes and the SYMBOL the private module declares are
            # two names by construction (``lower/names.THE_INNER_EXPORT``), so the private
            # side is asked under the class's OWN ``__name__`` -- which is what Python
            # bound when the ``class`` statement ran -- and not under the public word.
            declared = getattr(importlib.import_module(home), obj.__name__, None)
            assert declared is obj, f"{home}.{obj.__name__} is not {domain}.{name}"
            checked += 1
    assert checked, f"adcp.types.{domain} advertises no class with a private module"


def test_the_machinery_is_importable_and_not_advertised() -> None:
    """Both halves of the one deliberate asymmetry, so neither can drift unreported.

    IMPORTABLE: every name ``adcp/_client_types.py`` makes public resolves at
    ``adcp.types.core`` and IS the object that module declared -- which is what the 112
    collection errors in upstream's own suite were asking for.

    NOT ADVERTISED: none of them is in ``adcp.types.core.__all__``, because that list is
    the compiler's export set and two other gates read it as such.  Stated as an
    assertion rather than a sentence, so the day someone adds one, this file says which
    gate will go red and why.
    """
    public = importlib.import_module(f"adcp.types.{COMPOSES_MACHINERY}")
    restored = importlib.import_module("adcp._client_types")
    for name in claimed("machinery names the public path serves", machinery()):
        assert hasattr(public, name), f"adcp.types.{COMPOSES_MACHINERY}.{name} does not resolve"
        assert getattr(public, name) is getattr(restored, name), name
        assert name not in public.__all__, (
            f"{name} is in adcp.types.{COMPOSES_MACHINERY}.__all__, which is the compiler's "
            "export set: test_the_domain_surface would then ask which document declares it "
            "and test_the_surface_provenance would report it as a class the compiler did "
            "not declare. Both would be right."
        )


def test_the_two_task_status_enumerations_are_both_intact_and_nothing_is_aliased() -> None:
    """The same WORD, two concepts, and no binding between them.

    ``docs/migration-from-upstream.md`` §5 is written from this case: upstream's five
    members include ``needs_input``, ours include ``input-required``, and neither set
    contains the other -- so an alias would answer a caller comparing against
    ``needs_input`` with an enumeration that has no such member.  Asserted on the VALUES,
    because the defect is silent and a check on the names would not see it.
    """
    theirs = importlib.import_module(f"adcp.types.{COMPOSES_MACHINERY}").TaskStatus
    ours = importlib.import_module("adcp.types.enums").TaskStatus
    left = {m.value for m in theirs}
    right = {m.value for m in ours}
    assert theirs is not ours
    assert "needs_input" in left and "needs_input" not in right, (sorted(left), sorted(right))
    assert not left <= right and not right <= left, (sorted(left), sorted(right))


# --------------------------------------------------------------------------- #
# the red direction: built, not argued
# --------------------------------------------------------------------------- #
def test_the_text_compare_reddens_on_a_hand_edit() -> None:
    """The same derivation the green direction calls, over three mutated texts.

    A name bound by hand, a machinery re-export removed, and a docstring sentence
    changed.  All three are what a region compare inside one file could not see, which is
    the whole reason the aggregator and the composition are two files.
    """
    text = expected(COMPOSES_MACHINERY)
    assert (TYPES / f"{COMPOSES_MACHINERY}.py").read_text(encoding="utf8") == text

    added = text + "\nTaskResultLike = TaskResult\n"
    dropped = text.replace("from .._client_types import TaskResult as TaskResult\n", "")
    reworded = text.replace("neither set contains the other", "the sets agree")
    for mutated in (added, dropped, reworded):
        assert mutated != text, "the mutation did not change the text"

    # And the AST clause reddens on the first of them, which the text compare alone
    # cannot distinguish from a whitespace change.
    kinds = {type(node).__name__ for node in ast.parse(added).body}
    assert not kinds <= {"Expr", "ImportFrom"}, sorted(kinds)
