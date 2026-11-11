"""The KIND-DIFFERS set: upstream exposes a non-class, we expose a model -- and WHOSE IS IT.

**THE QUESTION, and it is the only one this file answers.**  ``adcp-client-python-j0c2``'s
remaining finding is a set of flat names where upstream's ``adcp.types`` holds something that
is NOT a class -- a ``typing.Annotated`` alias, a bare ``X1 | X2`` union -- and ours holds a
pydantic model.  Measurement alone does not say who is wrong, so every row is partitioned by
**what the DOCUMENT states at the node the declaration came from**, read out of the bundle and
never inferred from the class name:

``OURS``
    the document states a thing that is NOT an object and we emit a model anyway.  The fix
    would be in the emitter.
``THEIRS``
    the document states an object with fields of its own and no composition, and upstream
    flattened it to an alias.  A drop-in note is the answer and no emitter change is owed.
``EITHER``
    the document states a COMPOSITION over OBJECT branches -- a ``oneOf``/``anyOf`` choice, or
    an ``allOf`` conjunction that resolves to one -- which is neither an object nor a scalar.
    Both renderings are faithful: upstream names the branches and binds the document's word to
    a type expression over them; we bind the document's word to a base class the branches
    extend.  The row records the branch count on each side so a reader can see the two
    renderings are over the SAME branches.

**AND THE BRANCHES ARE READ, NOT JUST THE NODE.**  A ``oneOf`` whose branches are SCALARS is
not an ``EITHER``: a model is the wrong rendering of ``{"type": "string"} | {"type":
"number"}`` whatever the node's own keyword says, and such a row would be ``OURS`` hiding
inside a composition.  :func:`branch_kinds` resolves each branch -- through a ``$ref`` to the
document it names -- and :func:`verdict_for` reads the branch kinds and not only the node's.
Measured on this set: every branch of every row is an object, which is why the partition comes
out the way it does rather than by the coarse rule alone.

**TWO INTERPRETERS, BECAUSE THE TWO TREES CANNOT BE IMPORTED INTO ONE.**  Both distributions
own the ``adcp`` import root.  So upstream's side is dumped by a run under THEIR interpreter
and classified by a run under ours, exactly as ``survey/migration_notes.py`` does it.

**THE SET IS UPSTREAM'S OWN DECLARED FLAT SURFACE AND NOT THEIR GENERATED LAYOUT**, which is
reading 10's rule: "a name reachable only because a module forgot to declare what it exports
is not a name an application was invited to import".  ``adcp.types.__all__`` on their wheel is
939 hand-written names, and that is the denominator.  A name of theirs that does not resolve
on ours is not a kind difference -- it is one of the six failure sections of
``docs/migration-from-upstream.md``.

**AND A WORD IS NOT A SUBJECT.**  A row whose two sides hold DIFFERENT subjects is not a
rendering difference and is reported separately: upstream's flat ``AuthorizedAgent`` is their
generated union over ``adagents.json``, while ours is upstream's OWN restored
``adcp.types.registry.AuthorizedAgent`` -- a hand-written class with two fields and no
document.  Counting it as a kind difference says the two sides render one thing differently,
and they do not; it is §5's subject, "where upstream's name means something else".
:func:`decide` screens on whether OUR side carries a document record at all.

**WHAT DECIDES AN ``EITHER``, measured on upstream's own suite rather than argued.**
``tests/`` on this branch IS upstream's behavioural suite.  :func:`use_sites` parses all of it
and classifies every use of one of these names by the operation: CLASS-shaped
(``X.model_validate``, ``isinstance(_, X)``, ``X(...)``) or TYPE-EXPRESSION-shaped
(``TypeAdapter(X)``, ``get_args(X)``).  That is the evidence for which rendering an adopter
needs, and it is upstream's code and not ours.

Run::

    uv venv $S/up && uv pip install --python $S/up/bin/python adcp==9.6.1
    $S/up/bin/python survey/kind_differs.py --dump-theirs $S/theirs.json
    PYTHONPATH=.:src ./.venv/bin/python survey/kind_differs.py --theirs $S/theirs.json
    PYTHONPATH=.:src ./.venv/bin/python survey/kind_differs.py --theirs $S/theirs.json --rows
    PYTHONPATH=.:src ./.venv/bin/python survey/kind_differs.py --theirs $S/theirs.json --markdown

``--dump-theirs`` imports nothing of ours and is the only mode safe to run under upstream's
interpreter; every other mode needs this tree.
"""

from __future__ import annotations

import argparse
import ast
import collections
import enum
import json
import sys
import types
import typing
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

#: The kinds that are NOT a class, so a name holding one answers no ``model_validate``, no
#: ``isinstance`` and no subclass.  The whole of what "kind differs" means.
NOT_A_CLASS = frozenset({"annotated", "uniontype", "value"})

#: The composition keywords a node can state.  ``if``/``not`` are here because a node whose
#: only structure is a conditional states no object either, and a row resting on one must not
#: be called ``THEIRS`` for lack of a ``type``.
COMPOSITIONS = ("oneOf", "anyOf", "allOf", "if", "not")

#: The compositions whose branches are ALTERNATIVES.  ``allOf`` is excluded deliberately: it
#: is a conjunction, so its branches are not a choice and its result is the intersection.
CHOICES = ("oneOf", "anyOf")

#: Attributes that only a CLASS answers.  A line of an application reaching one of these
#: through a flat name works on our side and raises on upstream's.
CLASS_ATTRS = frozenset(
    {
        "model_validate",
        "model_validate_json",
        "model_construct",
        "model_json_schema",
        "model_fields",
        "model_dump",
        "model_dump_json",
        "model_rebuild",
        "strict_validate",
        "__fields__",
    }
)

#: Upstream's own test files that grade THEIR GENERATOR, declared in this repository.
#:
#: **THE DENOMINATOR IS DECLARED AND NOT DERIVED**, which that file's own header says: "there
#: is no predicate over a path that separates ``test_versioned_bases_codegen.py`` from
#: ``test_versioned_models.py``".  104 of upstream's 681 ``test_*.py`` are in it and the
#: remaining 577 are the behavioural set every drop-in figure is stated over.  It is read here
#: so a use site can be attributed to one set or the other by the repository's own record
#: instead of by this file's judgement about what a test is "really" asserting.
GENERATOR_TESTS = HERE / "dropin" / "upstream-tests-about-their-generator.txt"

#: Callables that take a TYPE EXPRESSION.  A flat alias answers these and a base class answers
#: only the first -- which is the whole of what an ``EITHER`` row costs.
TYPE_EXPRESSION_CALLS = frozenset({"TypeAdapter", "get_args", "get_origin"})


def kind_of(obj: object) -> str:
    """One coarse kind per object, and the ordering of the tests is the point.

    ``enum`` before ``model`` because a generated ``StrEnum`` is a class and not a model;
    ``rootmodel`` before ``model`` because every ``RootModel`` is a ``BaseModel``; and the
    ``typing`` tests last, because ``typing.get_origin`` answers for things that are also
    classes.
    """
    try:
        import pydantic
    except ImportError:  # pragma: no cover -- both interpreters have it
        pydantic = None  # type: ignore[assignment]
    if isinstance(obj, type):
        if issubclass(obj, enum.Enum):
            return "enum"
        if pydantic is not None and issubclass(obj, pydantic.RootModel):
            return "rootmodel"
        if pydantic is not None and issubclass(obj, pydantic.BaseModel):
            return "model"
        return "class"
    if typing.get_origin(obj) is typing.Annotated:
        return "annotated"
    if isinstance(obj, types.UnionType) or typing.get_origin(obj) is typing.Union:
        return "uniontype"
    return "value"


def _inner(obj: object) -> object:
    """Past ``Annotated``, to the thing the metadata is about."""
    return typing.get_args(obj)[0] if typing.get_origin(obj) is typing.Annotated else obj


def wire_fields(model: object) -> list[str]:
    """A model's WIRE field set -- the alias where there is one, the attribute otherwise.

    The identity ``survey/dropin_blocking.py`` and reading 10 key on, and the one that makes
    "the two sides are over the same branches" a claim about the protocol rather than about
    two naming conventions: our branch words are titled and upstream's are numbered, so a
    comparison on class NAMES would say every row disagrees.
    """
    fields = getattr(model, "model_fields", None)
    if not isinstance(fields, dict):
        return []
    return sorted(
        (info.serialization_alias or info.alias or name) for name, info in fields.items()
    )


def branch_members(obj: object) -> list[object]:
    """The members a non-class union is over, flattened through ``Annotated``."""
    args = typing.get_args(_inner(obj))
    return list(args) if args else []


def discriminator_of(obj: object) -> str:
    """The ``discriminator`` upstream's generator put in the alias's ``FieldInfo``, if any.

    Upstream writes the choice's tagging property here, which is the same fact our union base
    carries as ``_BRANCH_DISCRIMINATOR``.  Two renderings of ONE document statement, and
    recording both is how a row shows that neither side invented it -- and why upstream's set
    splits into ``annotated`` and ``uniontype`` for a reason that is also the document's.
    """
    if typing.get_origin(obj) is not typing.Annotated:
        return ""
    for meta in typing.get_args(obj)[1:]:
        found = getattr(meta, "discriminator", None)
        if found:
            return str(found)
    return ""


def dump_theirs() -> dict[str, object]:
    """Upstream's own declared flat surface, by kind and by branch.  **Imports nothing of ours.**"""
    import importlib.metadata

    types_module = __import__("adcp.types", fromlist=["__all__"])
    rows: dict[str, dict[str, object]] = {}
    unresolved: dict[str, str] = {}
    for name in sorted(types_module.__all__):
        try:
            obj = getattr(types_module, name)
        except Exception as error:  # noqa: BLE001 -- recorded, never swallowed
            unresolved[name] = f"{type(error).__name__}: {error}"
            continue
        members = branch_members(obj)
        rows[name] = {
            "kind": kind_of(obj),
            "module": getattr(obj, "__module__", ""),
            "branches": [getattr(member, "__name__", str(member)) for member in members],
            "branch_fields": [wire_fields(member) for member in members],
            "discriminator": discriminator_of(obj),
            "own_fields": wire_fields(obj),
        }
    return {
        "version": importlib.metadata.version("adcp"),
        "declared": len(types_module.__all__),
        "rows": rows,
        "unresolved": unresolved,
    }


def our_side() -> dict[str, dict[str, object]]:
    """Every flat name of ours that resolves, by kind, with the node it was compiled from.

    The record is read from ``vars(cls)`` for the reason ``survey/alias_destinations.py``
    states: upstream's hand-written classes that SUBCLASS one of ours inherit
    ``__adcp_schema__``, so ``getattr`` would attribute a node to a class that did not come
    from it.  Here the consequence is worse than a wrong path -- it hands a row the wrong
    DOCUMENT to be judged against, which is the one input this whole partition rests on.
    """
    import importlib

    types_module = importlib.import_module("adcp.types")
    out: dict[str, dict[str, object]] = {}
    for name in types_module.__all__:
        try:
            obj = getattr(types_module, name)
        except Exception:  # noqa: BLE001 -- a name of ours that raises is no row's subject
            continue
        record = vars(obj).get("__adcp_schema__") if isinstance(obj, type) else None
        if record is None:
            module = sys.modules.get(getattr(obj, "__module__", "") or "")
            if module is not None and module.__name__.startswith("adcp.types._schemas."):
                candidate = getattr(module, "__adcp_schema__", None)
                declared = tuple(getattr(module, "__all__", ()) or ())
                if candidate is not None and candidate.pointer == "#" and len(declared) == 1:
                    record = candidate
        # **THE BRANCHES OF THIS NODE ARE NOT ``__subclasses__()``**, which is the measurement
        # artifact this reading replaces.  A base of ours is extended by its own branches AND
        # by any declaration of ANOTHER document that composes with it -- measured, ten of
        # these bases carry an ``AdCPAsyncResponseData<X>`` child declared at
        # ``core/adcp-async-response.json#/anyOf/<n>``, which is a branch of THAT document and
        # not of this one.  Counting it made ten rows look like a branch-count disagreement
        # with upstream when the disagreement was with this function.  So a branch is a direct
        # subclass whose OWN record names a pointer UNDER this node's, in this node's document.
        children = (
            sorted(obj.__subclasses__(), key=lambda c: c.__name__) if isinstance(obj, type) else []
        )
        # The pointer is kept VERBATIM: a root base's pointer is "#" and its branches are
        # "#/oneOf/0", so the prefix to test is the pointer plus "/" and stripping the "#"
        # first makes every test false -- measured, 56 of 56 rows lost their branches.
        here = (record.document, record.pointer) if record is not None else ("", "")
        def _is_a_branch_of_this_node(child: type) -> bool:
            found = vars(child).get("__adcp_schema__")
            return (
                found is not None
                and found.document == here[0]
                and found.pointer.startswith(here[1] + "/")
            )

        branches = [child for child in children if _is_a_branch_of_this_node(child)]
        out[name] = {
            "kind": kind_of(obj),
            "document": record.document if record is not None else "",
            "pointer": record.pointer if record is not None else "",
            "declared_in": getattr(obj, "__module__", ""),
            "children": [child.__name__ for child in branches],
            "child_fields": [wire_fields(child) for child in branches],
            "extended_elsewhere": [
                child.__name__ for child in children if child not in branches
            ],
            "own_fields": wire_fields(obj),
            "discriminator": getattr(obj, "_BRANCH_DISCRIMINATOR", "") or "",
            "presence": bool(getattr(obj, "_BRANCH_PRESENCE", ())),
        }
    return out


class Reader:
    """Reads the patched bundle, resolving a ``$ref`` to the node it names.

    One object rather than four functions because the document cache and the portable
    document list are the expensive halves and every branch of every row asks for them.
    """

    def __init__(self) -> None:
        from codegen import bundle, patch

        self._bundle = bundle
        self.dir = patch.for_build(ROOT / "schemas" / "cache" / "3.2")
        self.documents = sorted(bundle.portable(self.dir))
        self._cache: dict[str, dict] = {}

    def read(self, document: str) -> dict:
        if document not in self._cache:
            self._cache[document] = self._bundle.read(self.dir, document)
        return self._cache[document]

    def at(self, document: str, pointer: str) -> object:
        try:
            return self._bundle.node_at(self.read(document), pointer.lstrip("#"))
        except Exception:  # noqa: BLE001 -- an unresolvable pointer is a row's verdict
            return None

    def through_ref(self, node: object, document: str) -> object:
        """One ``$ref`` hop, where the node is a reference and nothing else.

        A node carrying a ``$ref`` BESIDE its own keywords is not a reference to follow -- the
        siblings are the statement -- so the hop is taken only where ``$ref`` is the whole of
        the structural content.
        """
        if not isinstance(node, dict) or "$ref" not in node:
            return node
        if {key for key in node if not key.startswith(("$ref", "description", "deprecated", "x-"))}:
            return node
        target, pointer = self._bundle.split_ref(node["$ref"])
        named = self._bundle.document_for(target, self.documents) if target else document
        if named is None:
            return node
        return self.at(named, pointer)


def node_kind(node: object) -> str:
    """What one node states, in the coarse vocabulary a verdict is read in."""
    if not isinstance(node, dict):
        return "absent"
    declared = node.get("type")
    kinds = [declared] if isinstance(declared, str) else list(declared or [])
    if "object" in kinds or node.get("properties") or node.get("additionalProperties"):
        return "object"
    for keyword in COMPOSITIONS:
        if keyword in node:
            return "composition"
    if kinds:
        return ",".join(kinds)
    if node.get("required") or node.get("enum") is not None or node.get("const") is not None:
        # A clause stating only `required` or only a value list states no TYPE, and in the
        # presence-only branches of this bundle it is a constraint on the sibling conjunct
        # rather than a thing of its own.  Named, not folded into "empty".
        return "clause"
    return "empty"


def states(reader: Reader, document: str, pointer: str) -> dict[str, object]:
    """What the document STATES at one node, as the facts a verdict is read off.

    Not a verdict and not a type name: the node's own keywords, its own properties, which
    compositions it carries, and -- resolving one ``$ref`` hop per branch -- what KIND each
    branch of each choice states.  Keeping the reading and the rule apart is what lets a
    reader disagree with :func:`verdict_for` without disagreeing with this.
    """
    node = reader.at(document, pointer)
    if not isinstance(node, dict):
        return {
            "found": False,
            "keywords": [],
            "own_properties": [],
            "composition": [],
            "branch_kinds": {},
            "self_kind": "absent",
        }
    composition = [key for key in COMPOSITIONS if key in node]
    branch_kinds: dict[str, list[str]] = {}
    for keyword in CHOICES + ("allOf",):
        if keyword not in node or not isinstance(node[keyword], list):
            continue
        branch_kinds[keyword] = [
            node_kind(reader.through_ref(branch, document)) for branch in node[keyword]
        ]
    return {
        "found": True,
        "keywords": sorted(node),
        "own_properties": sorted(node.get("properties") or {}),
        "composition": composition,
        "branch_kinds": branch_kinds,
        "self_kind": node_kind(node),
    }


def verdict_for(stated: dict[str, object]) -> tuple[str, str]:
    """``(verdict, why)`` for one row, from what the document states and nothing else.

    **THE RULE, stated once.**

    * no node -- the pointer does not resolve.  ``UNDECIDED``, and reported.
    * **a choice (``oneOf``/``anyOf``) or an ``allOf`` resolving to one, whose branches are
      all objects** -- the node states a CHOICE BETWEEN OBJECTS.  That is neither an object
      nor a scalar, and a renderer may legitimately bind the document's word to a type
      expression over the branches or to a base class the branches extend.  ``EITHER``.
    * **a choice with a branch that is NOT an object** -- a string, a number, an array.  A
      model is the wrong rendering of at least one branch, so the composition does not excuse
      it.  ``OURS``, with the offending branch kinds named.
    * **no composition at all and an object** -- ``type: object``, or ``properties``.  The
      document states a thing with fields and upstream flattened something that was not a
      choice.  ``THEIRS``.
    * **no composition and a non-object ``type``** -- the document states something that is
      not an object and we emit a model.  ``OURS``.
    * anything else -- the document states nothing that decides it, and the row says so
      rather than guessing.  ``UNDECIDED``.
    """
    if not stated["found"]:
        return "UNDECIDED", "the pointer does not resolve in the patched bundle"
    branch_kinds: dict[str, list[str]] = stated["branch_kinds"]  # type: ignore[assignment]
    choice = [keyword for keyword in CHOICES if keyword in branch_kinds]
    conjunction = "allOf" in branch_kinds
    if choice or conjunction:
        offending = sorted(
            {
                kind
                for keyword in (choice or ["allOf"])
                for kind in branch_kinds[keyword]
                if kind not in ("object", "composition", "clause", "empty")
            }
        )
        if offending:
            return "OURS", f"a branch of the choice states {', '.join(offending)}, not an object"
        keyword = (choice or ["allOf"])[0]
        count = len(branch_kinds[keyword])
        word = "choice" if choice else "conjunction"
        return "EITHER", f"the node states a {word} of {count} object branches ({keyword})"
    if stated["composition"]:
        composed = ", ".join(stated["composition"])  # type: ignore[arg-type]
        return "UNDECIDED", f"the node composes with {composed} and states no branch list"
    if stated["self_kind"] == "object":
        return "THEIRS", "the node states an object, with no composition, and upstream flattened it"
    if stated["self_kind"] not in ("empty", "clause", "absent", "composition"):
        return "OURS", f"the node states type: {stated['self_kind']}, which is not an object"
    return "UNDECIDED", "the node states neither a composition, an object nor a type"


def type_expression_support(names: list[str]) -> dict[str, object]:
    """What our base classes answer to the TYPE-EXPRESSION operations upstream's suite uses.

    **THIS IS WHAT AN ``EITHER`` ROW ACTUALLY COSTS, and it is two facts and not an opinion.**

    * ``TypeAdapter(X)`` -- constructs on a class exactly as on an alias, and for a model
      pydantic takes the class's OWN core schema.  So where that holds, ``TypeAdapter(X)``
      and ``X.model_validate`` are one code path and the branch dispatch
      ``tests_emit/test_union_dispatch.py`` grades is what runs.
    * ``get_args(X)`` -- answers the branch tuple on a type expression and ``()`` on a class.
      This one a base class does NOT answer, and it is the whole of the loss.
    """
    import importlib

    from pydantic import TypeAdapter

    types_module = importlib.import_module("adcp.types")
    constructs = own_schema = get_args_answers = 0
    failures: list[str] = []
    for name in names:
        obj = getattr(types_module, name)
        try:
            adapter = TypeAdapter(obj)
        except Exception as error:  # noqa: BLE001 -- a refusal here is the finding
            failures.append(f"{name}: TypeAdapter: {type(error).__name__}: {error}")
            continue
        constructs += 1
        if adapter.core_schema == getattr(obj, "__pydantic_core_schema__", None):
            own_schema += 1
        if typing.get_args(obj):
            get_args_answers += 1
    return {
        "names": len(names),
        "TypeAdapter constructs": constructs,
        "TypeAdapter takes the class's own core schema": own_schema,
        "get_args answers a branch tuple": get_args_answers,
        "failures": failures,
    }


def disagreement_reason(row: dict[str, object], their_fields: list[list[str]]) -> str:
    """Why one row's two branch sets differ -- and never "the kinds differ", which they do not.

    **A BRANCH-SET DISAGREEMENT IS A DIFFERENT FINDING OF THE SAME BEAD.**  The kind question
    is about the FLAT NAME; a field that differs inside a branch is ``j0c2``'s wire-contract
    half, already partitioned in that bead's notes, and attributing it here would double-count
    it.  So each disagreement is named by its own cause, in this order, and the first that
    holds is the row's:

    1. upstream offers fewer branches than the document states -- an upstream omission.
    2. upstream renders a branch as a ``RootModel``, whose wire field is ``root`` -- the
       "21 theirs RootModel, ours model" family of ``j0c2``'s notes.
    3. two of upstream's branches are field-INDISTINGUISHABLE where the document distinguishes
       them -- an upstream invention inside a branch.
    4. anything else: a field differs inside a branch, which is the wire-contract finding.
    """
    if row["their_branches"] != row["document_branches"]:
        return "upstream offers fewer branches than the document states"
    if any(fields == ["root"] for fields in their_fields):
        return "upstream renders a branch as a RootModel, whose wire field is `root`"
    if len({tuple(fields) for fields in their_fields}) < len(their_fields):
        return "two of upstream's branches are field-indistinguishable"
    return "a field differs inside a branch -- the wire-contract finding, not the kind one"


def use_sites(names: set[str]) -> dict[str, object]:
    """How UPSTREAM'S OWN suite uses each name: as a class, or as a type expression.

    **``tests/`` ON THIS BRANCH IS UPSTREAM'S SUITE** (``tests_emit/`` is ours -- ``./check``
    derives which is which the same way).  This is the evidence that decides an ``EITHER``,
    and it is their code: a rendering difference nothing in their suite exercises costs
    nothing, and one their suite exercises 45 times costs exactly that.

    Parsed with ``ast`` and not grepped, so ``X`` in a string or a comment is not a use.
    """
    suite = ROOT / "tests"
    files = sorted(suite.rglob("*.py"))
    about_their_generator = {
        line.strip()
        for line in GENERATOR_TESTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    found: dict[str, list[dict[str, object]]] = collections.defaultdict(list)
    unparsed: list[str] = []
    for path in files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 -- a file that will not parse is reported
            unparsed.append(str(path.relative_to(ROOT)))
            continue
        where = str(path.relative_to(ROOT))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id in names and node.attr in CLASS_ATTRS:
                    found["class-attribute"].append(
                        {
                            "file": where,
                            "line": node.lineno,
                            "name": node.value.id,
                            "op": node.attr,
                            "behavioural": where not in about_their_generator,
                        }
                    )
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            callee = node.func.id
            if callee in ("isinstance", "issubclass"):
                for argument in node.args[1:]:
                    for inner in ast.walk(argument):
                        if isinstance(inner, ast.Name) and inner.id in names:
                            found["isinstance"].append(
                                {
                                    "file": where,
                                    "line": node.lineno,
                                    "name": inner.id,
                                    "op": callee,
                                    "behavioural": where not in about_their_generator,
                                }
                            )
            elif callee in names:
                found["construction"].append(
                    {
                        "file": where,
                        "line": node.lineno,
                        "name": callee,
                        "op": "X(...)",
                        "behavioural": where not in about_their_generator,
                    }
                )
            elif callee in TYPE_EXPRESSION_CALLS:
                for argument in node.args:
                    for inner in ast.walk(argument):
                        if isinstance(inner, ast.Name) and inner.id in names:
                            found["type-expression"].append(
                                {
                                    "file": where,
                                    "line": node.lineno,
                                    "name": inner.id,
                                    "op": callee,
                                    "behavioural": where not in about_their_generator,
                                }
                            )
    return {
        "files": len(files),
        "declared_generator_tests": len(about_their_generator),
        "unparsed": unparsed,
        "sites": {k: v for k, v in found.items()},
    }


def decide(theirs: dict[str, object]) -> dict[str, object]:
    """The KIND-DIFFERS rows, partitioned, with every set it ranges over counted."""
    ours = our_side()
    their_rows: dict[str, dict[str, object]] = theirs["rows"]  # type: ignore[assignment]
    both = sorted(set(their_rows) & set(ours))

    candidates = [
        name
        for name in both
        if their_rows[name]["kind"] in NOT_A_CLASS
        and ours[name]["kind"] in ("model", "rootmodel")
    ]
    # **A WORD IS NOT A SUBJECT.**  Our side must hold a class compiled from a document for
    # the row to be ABOUT one rendering; a word whose two sides hold different subjects is
    # §5's and is reported rather than partitioned.
    not_one_subject = [name for name in candidates if not ours[name]["document"]]
    rows_in = [name for name in candidates if ours[name]["document"]]

    reader = Reader()
    rows: list[dict[str, object]] = []
    for name in rows_in:
        mine = ours[name]
        theirs_row = their_rows[name]
        stated = states(reader, str(mine["document"]), str(mine["pointer"]))
        node_here = reader.at(str(mine["document"]), str(mine["pointer"]))
        verdict, why = verdict_for(stated)
        their_fields = sorted(tuple(f) for f in theirs_row["branch_fields"])  # type: ignore[union-attr]
        our_fields = sorted(tuple(f) for f in mine["child_fields"])  # type: ignore[union-attr]
        row = {
                "name": name,
                "theirs": theirs_row["kind"],
                "ours": mine["kind"],
                "document": mine["document"],
                "pointer": mine["pointer"],
                "node": str(mine["document"]) + str(mine["pointer"]),
                "their_branches": len(theirs_row["branches"] or []),
                "our_children": len(mine["children"] or []),
                "document_branches": next(
                    (len(kinds) for key in CHOICES + ("allOf",)
                     if (kinds := stated["branch_kinds"].get(key)) is not None),
                    0,
                ),
                "extended_elsewhere": mine["extended_elsewhere"],
                "their_discriminator": theirs_row["discriminator"],
                "our_discriminator": mine["discriminator"],
                "branch_sets_agree": their_fields == our_fields,
                "document_discriminator": "discriminator" in (node_here or {}),
                "keywords": stated["keywords"],
                "own_properties": len(stated["own_properties"]),  # type: ignore[arg-type]
                "composition": stated["composition"],
                "branch_kinds": stated["branch_kinds"],
                "verdict": verdict,
                "why": why,
        }
        row["disagreement"] = (
            "" if row["branch_sets_agree"]
            else disagreement_reason(row, theirs_row["branch_fields"])  # type: ignore[arg-type]
        )
        rows.append(row)

    reverse = [
        name
        for name in both
        if ours[name]["kind"] in NOT_A_CLASS and their_rows[name]["kind"] in ("model", "rootmodel")
    ]
    return {
        "upstream_version": theirs["version"],
        "their_declared": theirs["declared"],
        "resolving_on_both": len(both),
        "same_kind": sum(1 for n in both if their_rows[n]["kind"] == ours[n]["kind"]),
        "rows": rows,
        "not_one_subject": [
            {
                "name": n,
                "ours_declared_in": ours[n]["declared_in"],
                "theirs_from": their_rows[n]["module"],
            }
            for n in not_one_subject
        ],
        "reverse_direction": reverse,
        "documents_read": len(reader._cache),
        "use_sites": use_sites({row["name"] for row in rows}),  # type: ignore[misc]
        "type_expression_support": type_expression_support([str(row["name"]) for row in rows]),
    }


def markdown(report: dict[str, object]) -> str:
    """The row table, for ``verdicts/j0c2.md``."""
    rows: list[dict[str, object]] = report["rows"]  # type: ignore[assignment]
    out = [
        "| the flat name | theirs | ours | the node it is compiled from "
        "| what the node states | branches | whose |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda r: (r["verdict"], r["name"])):
        composition = ", ".join(row["composition"]) or "—"  # type: ignore[arg-type]
        own = f" + {row['own_properties']} own props" if row["own_properties"] else ""
        agree = "=" if row["branch_sets_agree"] else "≠"
        tag = row["their_discriminator"] or row["our_discriminator"] or "—"
        out.append(
            f"| `{row['name']}` | {row['theirs']} | {row['ours']} | `{row['node']}` | "
            f"{composition}{own}, tag `{tag}` | {row['their_branches']} {agree} "
            f"{row['our_children']} | **{row['verdict']}** |"
        )
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump-theirs", type=Path, help="run under UPSTREAM's interpreter")
    parser.add_argument("--theirs", type=Path, help="the dump --dump-theirs wrote")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--rows", action="store_true")
    parser.add_argument("--sites", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()

    if args.dump_theirs:
        payload = dump_theirs()
        args.dump_theirs.write_text(json.dumps(payload, indent=1))
        counts = collections.Counter(row["kind"] for row in payload["rows"].values())  # type: ignore[union-attr]
        print(f"upstream adcp {payload['version']}: {payload['declared']} declared flat names")
        for kind, count in counts.most_common():
            print(f"  {count:>5} {kind}")
        print(f"  {len(payload['unresolved']):>5} unresolved")  # type: ignore[arg-type]
        return

    if not args.theirs:
        raise SystemExit(
            "REFUSED: --theirs is required and has no default; see this file's docstring"
        )
    theirs = json.loads(args.theirs.read_text())
    report = decide(theirs)
    rows: list[dict[str, object]] = report["rows"]  # type: ignore[assignment]
    # **EVERY SET IS CLAIMED BEFORE A FIGURE IS READ OFF IT** -- `tests_emit/nodeset.py`'s
    # rule: "a derivation that selects nothing passes every assertion over it and is
    # indistinguishable from a working check."  Three sets, and the third was empty once
    # during this row's development, when `tests/` was assumed to be ours.
    for label, members in (
        ("names resolving on both surfaces", report["resolving_on_both"]),
        ("KIND-DIFFERS rows", rows),
        ("documents read for a verdict", report["documents_read"]),
        ("upstream test files parsed", report["use_sites"]["files"]),  # type: ignore[index]
    ):
        if not members:
            raise SystemExit(f"REFUSED: {label}: empty set -- every figure over it is vacuous")

    print(f"upstream adcp {report['upstream_version']}, {report['their_declared']} declared flat")
    print(f"resolving on both surfaces                     {report['resolving_on_both']}")
    print(f"same kind on both                              {report['same_kind']}")
    print(f"KIND-DIFFERS rows (theirs non-class, ours a model)  {len(rows)}")
    print(f"  withheld: a word, not one subject            {len(report['not_one_subject'])}")
    for entry in report["not_one_subject"]:  # type: ignore[union-attr]
        print(
            f"      {entry['name']}: ours {entry['ours_declared_in']}"
            f" / theirs {entry['theirs_from']}"
        )
    for kind, count in collections.Counter(row["theirs"] for row in rows).most_common():
        print(f"  theirs {kind:<12}                        {count}")
    print("  --- the partition ---")
    for verdict, count in collections.Counter(row["verdict"] for row in rows).most_common():
        print(f"  {verdict:<10}                             {count}")
    for why, count in collections.Counter(row["why"] for row in rows).most_common():
        print(f"      {count:>3}  {why}")
    agree = sum(1 for row in rows if row["branch_sets_agree"])
    print(f"  branch WIRE field sets agree on both sides   {agree} of {len(rows)}")
    tagged = sum(1 for row in rows if row["their_discriminator"])
    stated = sum(1 for row in rows if row["document_discriminator"])
    print(f"  the DOCUMENT states a discriminator          {stated}")
    print(f"  upstream carries it in the alias's FieldInfo  {tagged}")
    for reason, count in collections.Counter(
        row["disagreement"] for row in rows if row["disagreement"]
    ).most_common():
        print(f"      {count:>3}  disagree: {reason}")
    ours_tagged = sum(1 for row in rows if row["our_discriminator"])
    print(f"  ours carries _BRANCH_DISCRIMINATOR           {ours_tagged}")
    print(f"reverse direction (ours non-class, theirs a model)  {len(report['reverse_direction'])}")
    print(f"documents read                                 {report['documents_read']}")

    support: dict[str, object] = report["type_expression_support"]  # type: ignore[assignment]
    print("\nwhat our base classes answer, over the same rows:")
    for label, value in support.items():
        if label != "failures":
            print(f"  {label:<46} {value}")
    for failure in support["failures"]:  # type: ignore[union-attr]
        print(f"  REFUSED {failure}")

    sites: dict[str, object] = report["use_sites"]  # type: ignore[assignment]
    unparsed = len(sites["unparsed"])  # type: ignore[arg-type]
    print(f"\nupstream's own suite: {sites['files']} files parsed, {unparsed} unparsable")
    print(f"  of which declared as grading THEIR generator: {sites['declared_generator_tests']}")  # type: ignore[index]
    for bucket, entries in sorted(sites["sites"].items()):  # type: ignore[union-attr]
        kinds = collections.Counter(entry["op"] for entry in entries)
        behavioural = sum(1 for entry in entries if entry["behavioural"])
        print(
            f"  {bucket:<18} {len(entries):>4}  {dict(kinds)}"
            f"  -- {behavioural} in the 577 behavioural files, "
            f"{len(entries) - behavioural} in the 104 generator files"
        )
    for bucket in ("class-attribute", "isinstance", "construction", "type-expression"):
        if bucket not in sites["sites"]:  # type: ignore[operator]
            print(f"  {bucket:<18}    0")

    if args.json:
        args.json.write_text(json.dumps(report, indent=1, default=str))
    if args.markdown:
        print()
        print(markdown(report))
    if args.rows:
        print()
        for row in sorted(rows, key=lambda r: (r["verdict"], r["name"])):
            print(
                f"  {row['verdict']:<9} {row['name']:<36} theirs={row['theirs']}"
                f"({row['their_branches']}) ours={row['ours']}({row['our_children']}) "
                f"agree={'Y' if row['branch_sets_agree'] else 'N'} {row['node']}  {row['why']}"
            )
    if args.sites:
        print()
        for bucket, entries in sorted(sites["sites"].items()):  # type: ignore[union-attr]
            for entry in entries:
                print(
                    f"  {bucket:<16} {entry['file']}:{entry['line']}"
                    f"  {entry['op']}({entry['name']})"
                )


if __name__ == "__main__":
    main()
