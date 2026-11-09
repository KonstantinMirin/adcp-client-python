"""Nothing hand-written is reachable as though the compiler had emitted it.

**THE DEFECT THIS PREVENTS, and it is a consequence of a decision that has been taken
rather than a hazard imagined here.**  ``adcp.types.core`` is a public module our compiler
emits for the ``core`` schema domain, and it is also the path upstream kept a 444-line
hand-written module at -- the SDK's own ``AgentConfig``, ``Protocol``, ``TaskResult``,
``DebugInfo`` and ``TaskStatus``, none of which is on the wire and none of which any bundle
document states.  Whatever mechanism serves both name sets at that path, the result is a
public type surface carrying emitted classes and hand-written ones side by side, and a
consumer reading ``from adcp.types.core import X`` cannot tell which kind they have:
one validates by the document and names it in ``__adcp_schema__``, the other validates by
whatever its author wrote.

So the obligation is not "the graded population stays clean" -- :func:`test_the_graded_population_cannot_admit_a_hand_written_class`
below measures that it cannot be otherwise -- it is that **a hand-written model does not
appear at a path the compiler owns.**

**THE DISCRIMINATOR IS PROVENANCE AND NOT SHAPE, which is the whole of why this file is
short.**  A predicate over an object's shape -- does it carry ``__adcp_schema__``, does it
subclass the base -- is a claim a hand-written class can satisfy by writing two lines, and
:func:`test_a_mimicked_marker_does_not_launder_provenance` builds exactly that class.
``__module__`` is set by Python from the module whose body executed the ``class``
statement, so it is the one property a re-export cannot change and an author cannot fake
without moving the file.  :data:`EMITTED_ROOTS` is where the compiler writes, read off the
emitter rather than written down.

**AND THE ONE EXEMPTION IS DERIVED.**  130 of the 3,221 names the domain surface exports
are type ALIASES -- ``Annotated[...]``, a ``X | Y`` union -- and a typing construct carries
the module of the construct (``typing``, ``types``) and not of the module that declared it.
They are exempt because ``isinstance(obj, type)`` is false for them, which is a question
about what they ARE; there is no list of alias names here, and a hand-written pydantic
model is a ``type`` and cannot reach the exemption.
:func:`test_the_exemption_is_typing_constructs_and_nothing_else` holds both halves.

**WHAT THIS DOES NOT GRADE.**  Whether a type inside the emitted tree is a PAIR -- carries
the marker and the validator -- which is
``test_emit.test_the_pairing_is_intrinsic_to_every_class_the_tree_carries``'s reading and
has two live exceptions of its own (``brand.SearchBrandsRequest`` and
``creative.ValidateInputRequest``, both on ``AdcpRequest``).  Mixing the two would make
this file red for a reason that has nothing to do with hand-written content.

Perturbed in :func:`test_the_reading_reddens_on_a_constructed_mixture`, which calls the
SAME function the green direction calls over a module built to hold the defect.  A rule
nothing can break is a finding about the rule.
"""

from __future__ import annotations

import importlib
import types as _types
import typing
from typing import Annotated

import fresh
import pytest
from nodeset import claimed
from pydantic import BaseModel, Field, RootModel

from codegen import bundle, emit

from compiled import compiled

#: Where the compiler writes, and therefore the only provenance a name on the public type
#: surface may have.  ``emit.TREE`` is the private per-document tree; the two beside it
#: hold the types that belong to no document (D5's aliases, and the envelope bases), so a
#: name re-exported from either is still this compiler's output.  Derived from
#: :mod:`codegen.emit` rather than spelled, so a fourth place the compiler writes to joins
#: this set by itself.
EMITTED_ROOTS = (
    # ``emit.TREE`` is a filesystem path (``src/adcp/types/_schemas``); the dotted name is
    # its parts from ``adcp`` onward, so the two cannot drift apart if the tree moves.
    ".".join(emit.TREE.parts[emit.TREE.parts.index("adcp") :]),
    "adcp.types.constraints",
    "adcp.types.envelopes",
)


def domains() -> list[str]:
    """The public domain modules, off the compiler's own export record.

    The same derivation ``test_emit.test_the_committed_tree_is_what_a_fresh_run_emits``
    uses for the files it compares -- a module the run wrote that exports nothing
    contributes no domain -- so this file and that one cannot disagree about which public
    modules exist.
    """
    out = compiled(fresh.BUNDLE, sorted(bundle.portable(fresh.BUNDLE)))
    return sorted({emit.module_domain(m) for m, exported in out.surface.items() if exported})


def foreign(module: object) -> list[tuple[str, str]]:
    """Every name ``module`` advertises whose object was DECLARED outside the emitted tree.

    ``(name, the module that declared it)``.  A non-``type`` is skipped -- it is a typing
    construct, which is the derived exemption this file's docstring states -- and
    everything else is judged on ``__module__`` alone.

    This is the predicate, and it is a function so that the red direction below can call
    it over a module built to fail it.  A restated predicate proves that a copy of the
    check reddens, which is not the claim.
    """
    found = []
    for name in getattr(module, "__all__", ()):
        obj = getattr(module, name)
        if not isinstance(obj, type):
            continue
        home = getattr(obj, "__module__", "") or ""
        if not home.startswith(EMITTED_ROOTS):
            found.append((name, home))
    return found


def aliases(module: object) -> list[str]:
    """The names ``module`` advertises that are not classes: the exemption, by shape."""
    return [name for name in getattr(module, "__all__", ()) if not isinstance(getattr(module, name), type)]


# --------------------------------------------------------------------------- #
# the population is real, so no reading below can pass vacuously
# --------------------------------------------------------------------------- #
def test_the_population_is_the_compilers_own_export_record() -> None:
    """The domains, the names and both halves of the partition each have members."""
    found = claimed("public domain modules", domains())
    names, classes, constructs = [], [], []
    for domain in sorted(found):
        module = importlib.import_module(f"adcp.types.{domain}")
        advertised = getattr(module, "__all__", None)
        assert advertised, f"adcp.types.{domain} advertises nothing"
        names.extend(advertised)
        constructs.extend(aliases(module))
        classes.extend(n for n in advertised if isinstance(getattr(module, n), type))
    claimed("names the domain surface exports", set(names))
    claimed("of them, classes and enumerations", set(classes))
    # The EXEMPTION is claimed too: empty, the `isinstance` clause would be a dead branch
    # and nobody would notice it going wrong.
    claimed("of them, typing constructs", set(constructs))
    assert len(classes) > len(constructs) * 5, (len(classes), len(constructs))


@pytest.mark.parametrize("domain", domains())
def test_no_name_of_the_domain_surface_was_declared_outside_the_emitted_tree(domain: str) -> None:
    """One subject per domain, so a defect lands under the module it is reachable at.

    This is the reading.  A hand-written model re-exported here -- by an import line, by a
    module-level ``__getattr__``, by a loader that composes two name sets, or by any other
    mechanism -- is a class whose ``__module__`` is not the compiler's, and it is named
    with where it actually came from so the repair is obvious from the failure.
    """
    module = importlib.import_module(f"adcp.types.{domain}")
    assert foreign(module) == [], (
        f"adcp.types.{domain} advertises a class the compiler did not declare: "
        f"{foreign(module)}. A name reachable at a path the compiler owns must come from "
        f"{EMITTED_ROOTS}; hand-written machinery belongs at a path of its own."
    )


def test_the_exemption_is_typing_constructs_and_nothing_else() -> None:
    """Both halves of the one exemption, because the clause is what a mimic would aim at.

    Every exempt name IS a typing construct -- so the exemption cannot be reached by a
    class -- and the set is non-empty, so the clause is live rather than a branch that
    would be equally green if it were wrong.
    """
    exempt = []
    for domain in domains():
        module = importlib.import_module(f"adcp.types.{domain}")
        for name in aliases(module):
            obj = getattr(module, name)
            assert not isinstance(obj, type), (domain, name)
            # ``get_origin`` is the typing module's OWN answer to "is this a parameterised
            # construct", so the clause is not a list of the alias classes this release of
            # CPython happens to use: measured over the surface, 112 ``Annotated``, 14
            # ``Union``, 2 ``Literal``, one ``X | Y`` and one ``list[...]``, and the
            # ``__module__`` of those five spans ``typing``, ``types`` and ``builtins`` --
            # which is exactly why provenance is read off CLASSES only.
            assert typing.get_origin(obj) is not None, (domain, name, type(obj).__name__)
            exempt.append(f"{domain}.{name}")
    claimed("names exempt as typing constructs", set(exempt))


# --------------------------------------------------------------------------- #
# the graded population, which is a different question with a different answer
# --------------------------------------------------------------------------- #
def test_the_graded_population_cannot_admit_a_hand_written_class() -> None:
    """MEASURED, and the reason this file does not gate the graded population.

    ``codegen.harness.pairs`` is the suite's only pairing and it takes a value only when
    four things hold at once: the module is one it enumerated under the private emitted
    tree, the object subclasses ``adcp.types._base.SchemaBound``, the marker is in the
    object's OWN ``__dict__``, and ``__module__`` equals the enumerated module.  Upstream's
    conventions satisfy none of them -- plain ``BaseModel``, ``RegistryBaseModel``,
    ``CanonicalBoundaryModel``, ``RootModel`` -- and ``SchemaBound`` is a private module of
    ours their code neither imports nor could.

    So a check asserting "no restored class is in the graded population" would be green
    whatever any lane restores, and would be exactly the test that passes when nothing
    happens.  This reading states the closure instead, with the walk itself as the
    instrument: a package built to look like restored machinery yields ZERO pairs.
    """
    from codegen import harness

    probe = _handwritten_module("probe_for_the_graded_population")
    probe.__path__ = []  # a package the walk can enumerate, holding nothing
    found, unimportable = harness.pairs(probe)
    assert unimportable == {}, unimportable
    assert found == [], found
    # And the predicate's own conjuncts, each measured on the classes rather than argued:
    from adcp.types._base import SchemaBound

    for name in probe.__all__:
        obj = getattr(probe, name)
        assert not issubclass(obj, SchemaBound), name
        assert not hasattr(obj, "strict_validate"), name


# --------------------------------------------------------------------------- #
# the red direction: built, not argued
# --------------------------------------------------------------------------- #
def test_the_reading_reddens_on_a_constructed_mixture() -> None:
    """The same :func:`foreign` the green direction calls, over a module built to fail it.

    Three classes, one per convention this repository will meet after upstream's
    hand-written modules come back: a plain ``BaseModel``, a ``RootModel`` subclass (the
    base this project deliberately never emits, because ``extra`` cannot be changed on
    one), and a class that carries ``__adcp_schema__`` anyway.  All three are reported, and
    the emitted name beside them is not.
    """
    mixture = _handwritten_module("constructed_mixture")
    import adcp.types.core

    mixture.Account = adcp.types.core.Account  # an emitted class, the control
    mixture.__all__ = [*mixture.__all__, "Account"]
    reported = dict(foreign(mixture))
    assert set(reported) == {"PlainModel", "Rooted", "Mimic"}, reported
    assert all(home == "constructed_mixture" for home in reported.values()), reported
    assert "Account" not in reported, "the emitted control was reported as foreign"


def test_a_mimicked_marker_does_not_launder_provenance() -> None:
    """A hand-written class that writes the marker and takes the base is STILL reported.

    This is why the discriminator is ``__module__``.  A shape predicate asks a question
    the author of the class answers; provenance asks one Python answers.
    """
    from adcp.types._base import SchemaBound

    class Laundered(SchemaBound):  # type: ignore[misc]
        __adcp_schema__ = "core/account.json"

    module = _types.ModuleType("laundered_module")
    module.Laundered = Laundered
    module.__all__ = ["Laundered"]
    assert foreign(module) == [("Laundered", __name__)], foreign(module)


def _handwritten_module(name: str) -> _types.ModuleType:
    """A module holding upstream's three conventions, for the readings that need one."""
    module = _types.ModuleType(name)

    class PlainModel(BaseModel):
        status: str

    class Rooted(RootModel[str]):
        pass

    class Mimic(BaseModel):
        __adcp_schema__ = "core/account.json"
        status: Annotated[str, Field()] = ""

    for cls in (PlainModel, Rooted, Mimic):
        cls.__module__ = name  # as if its body had executed in that module
        setattr(module, cls.__name__, cls)
    module.__all__ = ["PlainModel", "Rooted", "Mimic"]
    return module
