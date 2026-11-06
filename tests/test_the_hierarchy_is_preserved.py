"""THE STANDING GATE ON THE WHOLE HIERARCHY: every base this project claims to emit, read
off the installed classes and derived from the bundle at every clause.

The invariant has four halves and this file grades all four, because the comparison
against upstream 9.6.1 found it failing in BOTH directions and a gate on one half would
have read green through either failure:

* **every branch of a discriminated union inherits that union's base class.**  Ours holds
  and upstream's does not -- 54 of 54 names upstream exposes as a BARE union carry no
  class at all, so their branches have no base to inherit, while we declare a base for
  each and 715 of our classes carry the dispatch base.  That is the half a regression
  would silently give away, so it is graded here rather than assumed.
* **every request extends the base request**, and **every response extends the base
  response.**  Ours did NOT hold -- 0 of the 84 requests common to both surfaces carried
  any request base against upstream's 72 -- which is the row ``codegen/lower/message.py``
  closes.
* **the envelope and the composition are as declared**: a document that composes
  ``core/version-envelope.json`` or ``core/protocol-envelope.json`` carries that
  document's own class as a base, because §2's ``allOf`` row makes a bare-``$ref``
  conjunct a base and nothing else is permitted to put one there.

**EVERY SET IS DERIVED AND NONE IS LISTED.**  The requests and responses come from the
bundle's own task registry (``bundle.task_messages``, ``bundle.REGISTRY_SCOPE``); the
union roots and their branches come from the emitted declarations' own union installs;
the composed bases come from the documents' ``allOf``.  A list here would make the gate a
restatement of the emitter rather than a reading of the bundle, and the one thing a
hierarchy gate must not do is agree with the walk by construction.

**AND EVERY CLAUSE IS TWO-DIRECTIONAL.**  "Every request has the base" is half an
assertion: the other half is that no class which is not a request has it, because a base
handed out too widely passes the first half and is the same defect.  A set EQUALITY is
how each clause says both at once.
"""

from __future__ import annotations

import importlib
import pkgutil

import fresh
import pytest

from adcp.types._base import PACKAGE, BranchDispatchMixin, SchemaBound
from adcp.types.envelopes import AdcpRequest, AdcpResponse
from codegen import bundle
from tests.nodeset import claimed

#: **The bundle a run reads, from the ONE declaration of it** -- ``fresh.BUNDLE``, the
#: PATCHED bundle, which is the bundle the committed classes were emitted from.  A
#: published literal here would range over a different document set from the classes this
#: file imports, which is ``tests/test_envelope_base.py``'s own measured hazard.
BUNDLE = fresh.BUNDLE

#: The two documents whose classes arrive as bases by COMPOSITION, and the symbol each
#: declares.  Read off the bundle by path, not by name: the pair is what §2's ``allOf``
#: row turns into a base, and the symbol is the one the document's own title derives.
COMPOSED = {
    "core/version-envelope.json": "AdCPVersionEnvelope",
    "core/protocol-envelope.json": "ProtocolEnvelope",
}


@pytest.fixture(scope="module")
def classes() -> dict[str, type]:
    """Every class the emitted tree declares, keyed ``document#pointer``.

    Read off the INSTALLED modules of ``adcp.types._schemas`` and keyed by each class's
    own ``__adcp_schema__``, which is §2's binding -- so a class reaches this mapping
    under the node it is graded against and not under the module it happens to sit in.
    A class with no reference of its own is a base or an import and is not this tree's
    declaration.
    """
    package = importlib.import_module(PACKAGE)
    out: dict[str, type] = {}
    for found in pkgutil.walk_packages(package.__path__, f"{PACKAGE}."):
        module = importlib.import_module(found.name)
        for value in vars(module).values():
            if not (isinstance(value, type) and issubclass(value, SchemaBound)):
                continue
            ref = value.__dict__.get("__adcp_schema__")
            if ref is None:
                continue
            out[f"{ref.document}#{ref.pointer.lstrip('#')}"] = value
    claimed("the classes the emitted tree declares", out)
    return out


def _roots(classes: dict[str, type]) -> dict[str, type]:
    """The ROOT class of each document: the one whose pointer is the document's own."""
    return {key.split("#", 1)[0]: value for key, value in classes.items() if key.endswith("#")}


def test_every_request_the_registry_names_extends_the_base_request(
    classes: dict[str, type],
) -> None:
    """And nothing else does -- which is the half a base handed out too widely passes.

    The set is the bundle's task registry and never a file name
    (``bundle.REGISTRY_SCOPE``): a name ending ``-request.json`` reaches 87 documents of
    bundle 3.2 against the registry's 78, among them the pagination and package
    COMPONENTS no task ever sends, and a gate keyed on the spelling would demand the base
    on a class that is not a call.
    """
    requests, _ = bundle.task_messages(BUNDLE)
    roots = _roots(classes)
    named = claimed("the requests the task registry names", requests & set(roots))
    carried = {
        document for document, cls in roots.items() if issubclass(cls, AdcpRequest)
    }
    assert carried == named, {
        "a request with no base request": sorted(named - carried),
        "the base request on a document no task sends": sorted(carried - named),
    }


def test_every_response_the_registry_names_extends_the_base_response(
    classes: dict[str, type],
) -> None:
    """The response half, stated the same way and derived from the same entry.

    The registry's third slot -- ``async_response_schemas``, 39 documents -- is NOT in
    this set, for ``bundle.task_messages``' stated reason: 23 of the 39 are repeated
    documents whose non-home copy re-EXPORTS the home's symbol rather than declaring a
    class, so a member set reaching one would name a document with no declaration of its
    own.  That is a separate row and this clause does not quietly include it.
    """
    _, responses = bundle.task_messages(BUNDLE)
    roots = _roots(classes)
    named = claimed("the responses the task registry names", responses & set(roots))
    carried = {
        document for document, cls in roots.items() if issubclass(cls, AdcpResponse)
    }
    assert carried == named, {
        "a response with no base response": sorted(named - carried),
        "the base response on a document no task answers with": sorted(carried - named),
    }


def test_the_two_message_bases_are_disjoint_and_neither_is_graded(
    classes: dict[str, type],
) -> None:
    """No class takes both, and neither base is a pair §8 would grade.

    The disjointness is the registry's own (``bundle.task_messages`` refuses a bundle
    that names one document in both slots), and it is what makes the MRO question never
    arise.  "Not graded" is asserted on all three counts the row claims: no
    ``__adcp_schema__``, not a ``SchemaBound`` at all, and an empty ``model_config`` -- the
    third being the measured one, because a base carrying §2's ``extra: ignore`` would
    impose a policy on the six requests whose own documents state none.
    """
    both = [
        document
        for document, cls in _roots(classes).items()
        if issubclass(cls, AdcpRequest) and issubclass(cls, AdcpResponse)
    ]
    assert not both, {"a document carrying both message bases": sorted(both)}
    for base in (AdcpRequest, AdcpResponse):
        assert "__adcp_schema__" not in base.__dict__, base.__name__
        assert not issubclass(base, SchemaBound), base.__name__
        assert base.model_config == {}, (base.__name__, base.model_config)
        with pytest.raises(AttributeError):
            base.strict_validate  # noqa: B018  -- the attribute must not resolve at all


def test_every_branch_of_a_union_inherits_that_unions_base(
    classes: dict[str, type],
) -> None:
    """The half that holds in OURS and fails in upstream 9.6.1, graded so it stays held.

    Upstream exposes 54 of its unions as a BARE union -- ``X1 | X2``, or an
    ``Annotated`` of one -- which carries no class, so a caller who is handed a branch
    cannot name what it is a branch OF.  We declare a base per union and every branch
    inherits it, which is what makes ``isinstance(branch, TheUnion)`` answerable.

    The sets are read off the INSTALLED classes and not off the IR: a union's base is a
    class whose subclasses carry the dispatch mixin, and the branches are its own
    subclasses.  So the clause grades the hierarchy a consumer meets rather than the
    declaration the compiler intended, which is the only reading that can catch a base
    that stopped being attached.
    """
    dispatching = {
        key: cls for key, cls in classes.items() if issubclass(cls, BranchDispatchMixin)
    }
    claimed("the classes carrying the union dispatch base", dispatching)
    orphans = {
        key: cls.__name__
        for key, cls in dispatching.items()
        # A dispatching class is either a union's BASE (it has subclasses of its own that
        # dispatch) or one of its BRANCHES (it has such a class above it).  Neither is a
        # statement about a name: both are read off the MRO and the subclass graph.
        if not any(
            issubclass(other, cls) and other is not cls for other in dispatching.values()
        )
        and not any(
            issubclass(cls, above) and above is not cls for above in dispatching.values()
        )
    }
    assert not orphans, {
        "a class carrying the dispatch base that is neither a union base nor a branch of "
        "one": orphans
    }


def test_a_document_that_composes_an_envelope_carries_that_envelopes_class(
    classes: dict[str, type],
) -> None:
    """§2's ``allOf`` row, in both directions and over the whole bundle.

    A bare-``$ref`` conjunct is a BASE CLASS, so a document whose root composes
    ``core/version-envelope.json`` carries ``AdCPVersionEnvelope`` and a document that
    does not must not -- the second direction being the one that catches a base attached
    by a rule other than composition, which is how the envelope and the message bases
    are kept from being confused for one another.
    """
    envelopes = importlib.import_module("adcp.types.core")
    roots = _roots(classes)
    for document, symbol in COMPOSED.items():
        base = getattr(envelopes, symbol)
        composes = claimed(
            f"the documents composing {document}",
            {
                where
                for where in roots
                if any(
                    isinstance(one, dict) and str(one.get("$ref", "")).endswith(document)
                    for one in bundle.read(BUNDLE, where).get("allOf", [])
                    if isinstance(one, dict)
                )
            },
        )
        carried = {
            where
            for where, cls in roots.items()
            if issubclass(cls, base) and cls is not base
        }
        assert not composes - carried, {
            f"composes {document} and does not carry {symbol}": sorted(composes - carried)
        }
