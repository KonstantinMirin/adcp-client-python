"""**EVERY FIELD WHERE UPSTREAM'S GENERATED CLASS CARRIES A DEFAULT THE DOCUMENT DOES NOT
STATE** -- the derived, counted set ``adcp-client-python-eknd`` owes.

    PYTHONPATH=.:src python -m survey invented_defaults --table survey/invented-defaults-9.6.1.tsv

**WHY THIS EXISTS, and what it is NOT.**  ``adcp-client-python-eknd`` measured one instance:
``media-buy/create-media-buy-response.json``'s ``allOf[1]`` declares ``status`` with
``required: ['status']``, so the conjunction requires ``status`` on every ``oneOf`` arm, and
upstream's ``CreateMediaBuyResponse1`` carries ``status: Literal['completed'] = 'completed'``
-- a default the document does not state, which makes a required field optional and makes
their class ADMIT a payload the document REFUSES.  Our class requires what the document
requires, so upstream's tests that construct a response without ``status`` cannot pass
against it.  That is a bounded, knowable set and until it is named the pass figure cannot be
read: *"passing except where upstream's tests require their generator's invented defaults"*
has no number attached to it.

**THIS MODULE CHANGES NOTHING AND FIXES NOTHING.**  It reads two artifacts and writes a
table.  An instrument that also edited its subject could not be trusted about it.

**THE THREE READINGS, and each is a question about the DOCUMENT and never about our tree.**

1. *Does upstream's class carry a default for this field?*  Read off upstream's own emitted
   text at ``2954b258b`` by AST, with inheritance resolved ACROSS modules -- upstream's arm
   classes subclass ``AdcpResponse``, ``AdcpVersionEnvelope`` and ``ProtocolEnvelope``, which
   live in three other modules, so a reader folding only within one module sees neither the
   envelope's fields nor their defaults.  (``codegen.structure.from_source`` folds within the
   module on purpose and records requiredness as "states no default", so ``published.json``
   cannot answer either half of this question; this is why the reading is new rather than a
   lookup.)

2. *Does the document REQUIRE the field?*  **The conjunction reaching the position and not
   the nearest object** -- ``status`` is required by ``allOf[1]``, not by the ``oneOf`` arm
   that carries it, so a field-local reading under-counts.  :func:`conjoined` is
   ``adcp.types._base.applied_schema``'s own walk, read for the ``required`` lists and the
   ``properties`` entries the conjunction holds, which is the precedent
   ``codegen/verify/witness.Construction.subject`` already sets.

3. *Does the document STATE that default?*  A ``default`` keyword at the property's position
   in the conjunction, or a ``const`` pinning the value.  Both are the document speaking; a
   generator's own is not.

**REQUIRED + DEFAULTED-BY-UPSTREAM-ONLY = AN INVENTED DEFAULT**, and :data:`KINDS` splits it
three ways, because the three do different amounts of harm and a single count would hide
that.  A field the document does NOT require is not in the set at all: a default on an
optional field changes no admissible payload.

**AND ``const-default`` IS NOT FREE, which refutes a sentence this repository already
carries.**  ``survey/structural_signature.RELAXATIONS['const-default']`` reads *"a default
equal to the node's own const is dropped.  COST: none that can be named.  A const node
admits exactly one value, so a default equal to it changes no admissible set"* -- true of
the PROPERTY's admissible set and false of the OBJECT's, which is the set a payload is
validated against.  Where the conjunction requires the property, the default makes an
object missing it admissible, and the document refuses that object.  :data:`KINDS`'
``const-restated`` is that case counted separately rather than relaxed away.

**AND THE SAME QUESTION ASKED OF OUR OWN TREE** -- :func:`ours`, behind ``--ours``.  The
867 are a measurement of UPSTREAM'S text and say nothing about what this compiler writes,
so a reader cannot get the ruling out of the table alone: every kind would have to be
attributed by hand, and four such attributions were wrong before measurement corrected
them.  :func:`ours` closes that by asking our tree the identical question, and it is
*cheaper* and *sharper* than the upstream reading rather than a mirror of it:

**THE POINTER IS STATED AND NOT INFERRED.**  Every class this compiler writes carries
``__adcp_schema__ = SchemaRef(document=..., pointer=...)``, so the whole candidate-matching
apparatus above -- :func:`candidates_for`, the ordinal, the unanimity rule,
``verdict-depends-on-position`` -- is not needed and not used.  There is one position per
class and the class names it.

**AND THE PREDICATE IS :func:`required_at` ONLY, WHICH IS WHAT MAKES IT
MECHANISM-INDEPENDENT.**  This was measured the hard way.  A reading that also asked about
:func:`some_arm_requires` has to decide *how* a disjunction's requiredness is carried, and
this compiler carries it four different ways -- a per-arm class whose own field is
required, a ``RequiredGroups`` rule, a ``PresenceGroups`` rule of ``Presence`` clauses, and
``BranchDispatchMixin`` dispatch to branch models.  A reader that enumerates mechanisms
under-counts by whichever one it has not met yet: three successive attempts here reported
223, then 77, then 47 "lax" pairs of ours, and every correction moved the same way, because
each had met one more mechanism.  Every one of those was the reader and not the tree.
:func:`required_at` is the CONJUNCTION alone, which no mechanism can be hiding in, so the
answer does not depend on having enumerated them.
"""

from __future__ import annotations

import argparse
import ast
import collections
import hashlib
import importlib
import json
import pkgutil
import subprocess
import sys
import tarfile
from io import BytesIO
from pathlib import Path
from typing import Any, NamedTuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from adcp.types._base import applied_schema, through_the_store  # noqa: E402

#: Upstream's published tree, as a revision of this repository's own history -- the same
#: input ``survey/published_structures.py`` reads, and for the same reason: nothing is
#: downloaded, nothing is installed, and the revision is written into the artifact.
REVISION = "2954b258b"

#: The whole of upstream's ``adcp.types`` and not only ``domains/``: an arm class's bases are
#: ``adcp.types.base.AdcpResponse`` and two ``domains/core`` envelopes, so the fields a
#: default can sit on are spread across both halves of their package.
TREE = "src/adcp/types"

#: Where the documents of record live -- ``codegen.bundle.record``'s output, committed.  Read
#: as a MAPPING and never re-parsed, which is ``docs/plan/architecture.md`` §9's reader rule.
RECORDS = ROOT / "src" / "adcp" / "types" / "_schemas"

#: The generated-module header ``datamodel-codegen`` writes, which NAMES the document the
#: module was generated from.  Upstream's own statement of the join, so the document is not
#: guessed from the module path: ``#   filename:  media_buy/create_media_buy_response.json``.
HEADER = "#   filename:"

#: What a field's default is, where the document is read against it.  **Three kinds and not
#: one count**, because they do different amounts of harm:
KINDS = {
    "invented-value": (
        "the conjunction REQUIRES the property and the document states neither a `default` "
        "nor a `const` for it, so upstream's generator both made a required field optional "
        "AND pinned a value the document never states for that position.  The worst kind: "
        "their class admits an object the document refuses, and fills it with a value no "
        "reading of the document produces.  `CreateMediaBuyResponse1.status = 'completed'` "
        "is this"
    ),
    "const-restated": (
        "the conjunction REQUIRES the property and the document pins it with `const`, and "
        "upstream's default equals that const.  The VALUE is the document's; the "
        "OPTIONALITY is upstream's generator's, and it is still laxness -- an object "
        "omitting the property is refused by the document and admitted by their class.  "
        "This is the case `survey/structural_signature.RELAXATIONS['const-default']` calls "
        "costless, which is true of the property's admissible set and false of the object's"
    ),
    "contradicts": (
        "the document states a `default` or a `const` for the property and upstream's "
        "default is NOT that value, so their class fills in something the document says is "
        "something else"
    ),
    "collapsed-disjunction": (
        "the document states `oneOf`/`anyOf` at the position and SOME arm requires the "
        "property, and upstream emitted ONE class for the whole position -- so the "
        "requirement could not be carried anywhere and their generator defaulted it.  Their "
        "class then admits an instance satisfying NO arm, which the document refuses.  This "
        "compiler emits one class per arm, so the arm's requirement is kept where the "
        "document states it; the divergence is structural and the default is its symptom"
    ),
}

#: Why a ``(class, field)`` of upstream's is NOT read.  **Every outcome is named**, which is
#: ``codegen.structure.REFUSALS``' own discipline: a pair whose verdict cannot be decided is
#: reported rather than attributed to the nearest object.
UNREAD = {
    "no-document": "the module's header names no document, so there is nothing to read against",
    "document-absent": "the header names a document this bundle's records do not hold",
    "no-defaults": "no field of the resolved class carries a default -- nothing to ask about",
    "field-absent": (
        "no position of the document declares this property at all, so the document says "
        "nothing about it and upstream's default answers to nothing of the document's.  A "
        "field their generator added on its own authority, not a default it invented"
    ),
    "verdict-depends-on-position": (
        "the positions this class could have been generated at do not AGREE about the field: "
        "one requires it and another does not, or they state different values.  So the "
        "verdict turns on which pointer the class was stamped at and this reading cannot "
        "decide that -- reported, never broken by picking a position"
    ),
}

#: The verdict for a field the document does not require.  **Not in the set**, and named so
#: the count of what was looked at is reportable: a default on an optional property changes
#: no admissible payload, which is the whole reason requiredness is reading (2).
OPTIONAL = "not-required"

#: :func:`stated_value`'s answer where the conjunction reaches SEVERAL disagreeing statements
#: of the property's value.  Not a value, so the pair it belongs to is refused.
SEVERAL = "several-stated-values"


class Field(NamedTuple):
    """One field of one of upstream's classes, as its own text states it."""

    #: The wire name -- ``Field(alias=...)`` where one is given, else the attribute.
    wire: str
    #: Is there a default at all: an assignment that is not pydantic's ``...``.
    defaulted: bool
    #: The default's value where it is a literal, as canonical JSON; ``""`` where it is not
    #: (a ``default_factory``, a call, a name) and ``"-"`` where there is no default.
    default: str
    #: The class that CONTRIBUTED this field in the MRO -- where the default was written.
    whence: str
    #: The default's own text where :attr:`default` could not read it, for
    #: :func:`with_enum_defaults` to resolve.  ``""`` where there is nothing to resolve.
    raw: str = ""


class Decl(NamedTuple):
    """One class upstream declares, with its bases resolved to other declarations."""

    module: str
    name: str
    bases: tuple[str, ...]
    own: dict[str, Field]
    document: str
    #: ``member -> its value`` where this declaration is an enumeration, so an enum-member
    #: default (``TaskStatus.submitted``) can be read as the value it denotes.
    members: dict[str, Any] = {}


# --------------------------------------------------------------------- upstream's own text


def sources(revision: str, repo: Path) -> dict[str, str]:
    """``adcp.types.domains.core.format`` -> that module's text, out of ``revision``.

    ``git archive`` and not a worktree checkout, which is
    ``survey/published_structures.tree_of``'s own reason: the revision is read without
    touching the working tree, so this is safe to run from inside any lane's checkout.
    """
    blob = subprocess.run(
        ["git", "archive", revision, TREE], cwd=repo, check=True, stdout=subprocess.PIPE
    ).stdout
    out: dict[str, str] = {}
    with tarfile.open(fileobj=BytesIO(blob)) as archive:
        for member in archive.getmembers():
            if not member.name.endswith(".py"):
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            rel = member.name[len(TREE) + 1 : -len(".py")]
            module = "adcp.types" + ("." + rel.replace("/", ".") if rel else "")
            if module.endswith(".__init__"):
                module = module[: -len(".__init__")]
            out[module] = handle.read().decode()
    return out


def document_of(text: str) -> str:
    """The document ``datamodel-codegen``'s header names, exactly as it names it.

    **UPSTREAM'S OWN STATEMENT OF THE JOIN**, which is why no rule maps a module path to a
    document: their generator wrote the filename it read into the file it wrote.  The
    spelling is left alone here and reconciled with the bundle's by :func:`document_for`,
    because the bundle does not spell its own paths one way either.
    """
    for line in text.splitlines()[:8]:
        if line.startswith(HEADER):
            named = line[len(HEADER) :].strip()
            return named if named.endswith(".json") else ""
    return ""


#: ``codegen.bundle.PROJECTIONS``: a projection re-cuts a document's nodes for one transport
#: and is not a document of its own, so a generated header naming ``bundled/protocol/x.json``
#: names the document at ``protocol/x.json``.  Quoted here rather than imported so this
#: module needs nothing of the compiler.
PROJECTIONS = ("bundled", "mcp")


def _spelling(path: str) -> str:
    """One document path under the one normalisation both spellings collapse to.

    **THE BUNDLE DOES NOT SPELL ITS OWN PATHS ONE WAY**, which is measured and not assumed:
    ``media-buy/create-media-buy-response.json`` is hyphenated and
    ``formats/canonical/audio_daast.json`` is not, and upstream's generator writes the
    underscored form for both.  A rule that hyphenated the header would miss the sixteen
    ``formats/canonical`` documents and mangle ``_base.json`` into ``-base.json``.  So the
    two spellings are joined under a key that erases the difference, and a collision would be
    two documents of the bundle differing only in a hyphen -- which :func:`records_of` counts.
    """
    head, _, rest = path.partition("/")
    if head in PROJECTIONS and rest:
        path = rest
    return path.replace("_", "-")


def document_for(named: str, records: dict[str, dict]) -> str:
    """The record ``named`` names, or ``""`` where the bundle holds no such document."""
    index = {_spelling(k): k for k in records}
    return index.get(_spelling(named), "")


def _head(node: ast.expr | None) -> str:
    """The leading NAME of an expression, qualifier dropped -- ``structure._head``'s reading."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _head(node.value)
    if isinstance(node, ast.Call):
        return _head(node.func)
    return ""


def _alias_of(*nodes: ast.expr | None) -> str | None:
    """``Field(alias='$schema')`` anywhere in a field's annotation or default."""
    for node in nodes:
        for found in ast.walk(node) if node is not None else ():
            if (
                isinstance(found, ast.keyword)
                and found.arg == "alias"
                and isinstance(found.value, ast.Constant)
            ):
                return str(found.value.value)
    return None


def _default(value: ast.expr | None) -> tuple[bool, str, str]:
    """``(is there a default, its literal as canonical JSON, its text)`` for an assignment.

    **pydantic's ``...`` IS NOT A DEFAULT and the distinction is the whole reading**:
    ``x: int = Field(..., description=...)`` is a REQUIRED field with metadata, and counting
    it as defaulted would put every annotated required field of upstream's tree into this
    set.  Measured over ``2954b258b``: upstream writes metadata as ``Annotated[X, Field(...)]``
    and the default as a bare assignment, so this arm fires rarely -- which is exactly why it
    has to be right rather than common.

    A ``default_factory``, a call or a name answers ``(True, "", its text)``: there IS a
    default and its value is not a literal of the text.  The TEXT travels so
    :func:`with_enum_defaults` can resolve the one shape that matters --
    ``task_status_1.TaskStatus.submitted``, an enum member whose value is the member's and
    not the attribute's spelling.  What stays unread stays unread, and
    :data:`UNREAD`'s own discipline applies: a value this reader does not hold is never
    compared against the document's.
    """
    if value is None:
        return False, "-", ""
    if isinstance(value, ast.Constant) and value.value is Ellipsis:
        return False, "-", ""
    if _head(value) == "Field":
        assert isinstance(value, ast.Call)
        positional = value.args[0] if value.args else None
        if positional is not None and isinstance(positional, ast.Constant):
            if positional.value is Ellipsis:
                return False, "-", ""
            return True, json.dumps(positional.value, sort_keys=True), ""
        for keyword in value.keywords:
            if keyword.arg in ("default", "default_factory"):
                try:
                    return True, json.dumps(ast.literal_eval(keyword.value), sort_keys=True), ""
                except (ValueError, TypeError, SyntaxError):
                    return True, "", ast.unparse(keyword.value)
        return (False, "-", "") if positional is None and not value.keywords else (True, "", "")
    try:
        return True, json.dumps(ast.literal_eval(value), sort_keys=True), ""
    except (ValueError, TypeError, SyntaxError):
        return True, "", ast.unparse(value)


def symbols(module: str, text: str) -> dict[str, str]:
    """Every name this module's imports bind, as ``name -> "<module>.<name>"``.

    **A BASE IS RESOLVED THROUGH THE MODULE'S OWN IMPORTS AND NEVER BY SEARCHING FOR THE
    WORD**, which is the same rule ``codegen.structure.names_bound`` states for the other
    direction: two of upstream's modules declare ``Format``, and a reader that took the first
    class anywhere with the right spelling would fold one subject's fields into another's.
    Relative imports are resolved against the module's own package, ``..core.format`` and
    ``..core import format as format_1`` alike.
    """
    out: dict[str, str] = {}
    parts = module.split(".")
    for node in ast.parse(text).body:
        if isinstance(node, ast.ImportFrom):
            if node.level:
                base = parts[: len(parts) - node.level]
                where = ".".join([*base, *(node.module.split(".") if node.module else [])])
            else:
                where = node.module or ""
            for alias in node.names:
                out[alias.asname or alias.name] = f"{where}.{alias.name}"
    return out


def declarations(src: dict[str, str]) -> dict[str, Decl]:
    """``"<module>.<Class>"`` -> :class:`Decl` over the whole of upstream's package."""
    out: dict[str, Decl] = {}
    for module, text in sorted(src.items()):
        bound = symbols(module, text)
        document = document_of(text)
        for node in ast.parse(text).body:
            if not isinstance(node, ast.ClassDef):
                continue
            own: dict[str, Field] = {}
            members: dict[str, Any] = {}
            for stmt in node.body:
                if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
                    name = stmt.target.id
                    if name.startswith("_") or _head(stmt.annotation) == "ClassVar":
                        continue
                    wire = _alias_of(stmt.annotation, stmt.value) or name.rstrip("_")
                    defaulted, literal, raw = _default(stmt.value)
                    own[wire] = Field(wire, defaulted, literal, f"{module}.{node.name}", raw)
                elif (
                    isinstance(stmt, ast.Assign)
                    and len(stmt.targets) == 1
                    and isinstance(stmt.targets[0], ast.Name)
                    and isinstance(stmt.value, ast.Constant)
                    and not stmt.targets[0].id.startswith("_")
                    and stmt.targets[0].id != "model_config"
                ):
                    members[stmt.targets[0].id] = stmt.value.value
            bases = tuple(
                bound.get(_head(b)) or f"{module}.{_head(b)}" for b in node.bases if _head(b)
            )
            out[f"{module}.{node.name}"] = Decl(module, node.name, bases, own, document, members)
    return with_enum_defaults(out, {m: symbols(m, t) for m, t in src.items()})


def with_enum_defaults(decls: dict[str, Decl], bound: dict[str, dict[str, str]]) -> dict[str, Decl]:
    """``decls`` with every enum-member default read as the VALUE that member denotes.

    ``status: Literal[task_status_1.TaskStatus.submitted] = task_status_1.TaskStatus.submitted``
    is upstream's spelling for arm 2 of ``create-media-buy-response``, and a reader that left
    it unread could not tell that default from the document's ``const: 'submitted'`` -- so the
    pair would be reported as a contradiction on no evidence.  The dotted name is resolved
    through the DECLARING MODULE'S OWN IMPORTS (``task_status_1`` -> ``..enums.task_status``),
    never by searching for the word, which is :func:`symbols`' own rule.
    """
    out: dict[str, Decl] = {}
    for key, decl in decls.items():
        fixed: dict[str, Field] = {}
        for wire, field in decl.own.items():
            value = _member(field.raw, decl.module, decls, bound) if field.raw else None
            fixed[wire] = field._replace(default=value) if value is not None else field
        out[key] = decl._replace(own=fixed)
    return out


def _member(
    text: str, module: str, decls: dict[str, Decl], bound: dict[str, dict[str, str]]
) -> str | None:
    """``"task_status_1.TaskStatus.submitted"`` -> ``'"submitted"'``, or ``None``."""
    parts = text.split(".")
    if len(parts) < 2:
        return None
    member, path = parts[-1], parts[:-1]
    where = bound.get(module, {}).get(path[0])
    if where is None:
        where = f"{module}.{path[0]}"
    key = ".".join([where, *path[1:]])
    found = decls.get(key)
    if found is None or member not in found.members:
        return None
    return json.dumps(found.members[member], sort_keys=True)


def linearised(key: str, decls: dict[str, Decl], seen: frozenset[str] = frozenset()) -> list[str]:
    """``key``'s bases in attribute-resolution order, nearest first.

    Depth-first left-to-right with a cycle guard, which is Python's own order for every
    hierarchy upstream's generator writes (no class in that tree has a diamond whose C3 order
    differs from the DFS one, and a base outside the tree contributes nothing either way).
    Resolved fields are folded in REVERSE of this, so the nearest declaration wins -- which
    is what makes "the class that contributed the default" answerable.
    """
    if key in seen or key not in decls:
        return []
    out = [key]
    for base in decls[key].bases:
        for found in linearised(base, decls, seen | {key}):
            if found not in out:
                out.append(found)
    return out


def resolved(key: str, decls: dict[str, Decl]) -> dict[str, Field]:
    """Every field ``key`` declares or inherits, keyed by WIRE name, nearest declaration won."""
    out: dict[str, Field] = {}
    for found in reversed(linearised(key, decls)):
        out.update(decls[found].own)
    return out


# ------------------------------------------------------------------- the document's reading


def conjoined(root: dict, pointer: str) -> list[dict]:
    """Every statement the document holds against the INSTANCE a class at ``pointer`` names.

    ``adcp.types._base.applied_schema`` is the walk -- the subject a class is graded against,
    and the one reading of draft-07's same-instance semantics this repository has -- and this
    is its answer flattened through ``allOf`` and through the record's own storage
    references.  ``codegen/verify/witness.Construction.subject`` reads the same walk for
    POINTERS; this reads it for the nodes, because what is wanted here is two keywords
    (``required`` and ``properties``) and not a pointer set.

    **``oneOf`` AND ``anyOf`` ARE NOT FOLLOWED, and that is the difference between a
    conjunction and a disjunction.**  A branch's ``required`` holds only of instances that
    took that branch, so folding it in would make every arm's requirements hold of every
    arm.  ``allOf`` is followed because draft-07 holds every member against the same
    instance -- which is the whole of why ``status`` is required at ``#/oneOf/0``, where the
    arm's own text never mentions it.
    """
    out: list[dict] = []
    queue = [applied_schema(root, pointer)]
    while queue:
        node = through_the_store(queue.pop(), root)
        if not isinstance(node, dict) or node in out:
            continue
        out.append(node)
        held = node.get("allOf")
        if isinstance(held, list):
            queue.extend(held)
    return out


#: The two keywords that state a DISJUNCTION about the instance a node describes.  ``allOf``
#: is not here and never could be: it is the conjunction :func:`conjoined` already walks.
DISJUNCTS = ("oneOf", "anyOf")


def arms_at(root: dict, pointer: str) -> list[list[dict]]:
    """Each disjunction the conjunction at ``pointer`` states, as its list of arm nodes."""
    out: list[list[dict]] = []
    for node in conjoined(root, pointer):
        for keyword in DISJUNCTS:
            held = node.get(keyword)
            if isinstance(held, list) and held:
                arms = [through_the_store(a, root) for a in held]
                out.append([a for a in arms if isinstance(a, dict)])
    return out


def _required(node: dict) -> frozenset[str]:
    return frozenset(n for n in (node.get("required") or ()) if isinstance(n, str))


def required_at(root: dict, pointer: str) -> frozenset[str]:
    """The properties an admissible instance at ``pointer`` MUST carry -- reading (2).

    The conjunction's own ``required`` lists, **and a property EVERY arm of a disjunction
    requires**.  The second clause is sound and the asymmetry is the reason: an instance must
    satisfy at least one arm, so a property all arms require is one every admissible instance
    carries -- while a property only SOME arm requires is not required at all, and folding it
    in would make every arm's requirements hold of every arm.  That weaker case is
    :func:`some_arm_requires`, which is a different finding and counted as one.
    """
    out = frozenset(n for node in conjoined(root, pointer) for n in _required(node))
    for arms in arms_at(root, pointer):
        out |= frozenset.intersection(*(_required(a) for a in arms))
    return out


def some_arm_requires(root: dict, pointer: str) -> frozenset[str]:
    """Properties SOME but not every arm of a disjunction at ``pointer`` requires.

    **WHAT A COLLAPSED DISJUNCTION LOSES.**  Where the document states ``oneOf`` and a
    generator emits ONE class for the whole position, every arm's own requirement becomes a
    field of that single class -- and a field required by only one arm cannot be made
    required there without refusing the other arms.  So the generator defaults it, and the
    class then admits an instance satisfying NO arm, which the document refuses.  This
    compiler emits one class PER ARM instead (``CreateMediaBuySuccess`` /
    ``CreateMediaBuyError`` / ``CreateMediaBuyResponseSubmitted``), so the requirement is
    carried where the document states it.
    """
    out: set[str] = set()
    for arms in arms_at(root, pointer):
        union = frozenset().union(*(_required(a) for a in arms))
        out |= union - frozenset.intersection(*(_required(a) for a in arms))
    return frozenset(out) - required_at(root, pointer)


def _properties(root: dict, nodes: list[dict], out: dict[str, list[dict]]) -> None:
    """``nodes``' own ``properties`` entries, folded into ``out`` and read through the store."""
    for node in nodes:
        held = node.get("properties")
        if isinstance(held, dict):
            for name, sub in held.items():
                resolved_sub = through_the_store(sub, root)
                if isinstance(resolved_sub, dict):
                    out.setdefault(name, []).append(resolved_sub)


def properties_at(root: dict, pointer: str) -> dict[str, list[dict]]:
    """``property -> every node the conjunction states for it``, outer statements included."""
    out: dict[str, list[dict]] = {}
    _properties(root, conjoined(root, pointer), out)
    return out


def properties_spanning(root: dict, pointer: str) -> dict[str, list[dict]]:
    """:func:`properties_at` with every ARM of every disjunction folded in beside it.

    **THE PROPERTY SET A COLLAPSED CLASS CARRIES.**  Where a generator emits one class for a
    position stating ``oneOf``, that class's fields are the union over the arms, so a reader
    matching a class to a position by its property set has to be able to ask for that union
    -- otherwise every collapsed class of upstream's matches nothing and falls through to a
    per-field search that cannot agree with itself.  An arm's own ``allOf`` is folded too,
    which is what makes an arm composed out of a base compare at its resolved set.
    """
    out = properties_at(root, pointer)
    for arms in arms_at(root, pointer):
        for arm in arms:
            _properties(root, _conjuncts(root, arm), out)
    return out


def _conjuncts(root: dict, node: dict) -> list[dict]:
    """``node`` and every member of its ``allOf``, transitively, through the store."""
    out: list[dict] = []
    queue = [node]
    while queue:
        found = through_the_store(queue.pop(), root)
        if not isinstance(found, dict) or found in out:
            continue
        out.append(found)
        held = found.get("allOf")
        if isinstance(held, list):
            queue.extend(held)
    return out


def stated_value(nodes: list[dict]) -> tuple[str, str]:
    """``(keyword, value as canonical JSON)`` the document states for a property -- reading (3).

    ``("", "")`` where it states neither, which is the reading that makes a default
    upstream's own.  ``const`` is looked for first and ``default`` second, because a const
    node admits exactly one value and a default beside it is the document restating its own
    constraint; where only a ``default`` is given, that default IS the document's.

    **SEVERAL DISAGREEING VALUES ARE NOT A STATED VALUE**, and the first of them is the
    arbitrary pick this module refuses everywhere else.  ``core/postal-area.json`` states a
    ``country`` ``const`` per arm; a conjunction that reaches more than one of them has not
    told this reader which one holds, so it answers :data:`SEVERAL` and the caller refuses
    the pair rather than reporting a contradiction with the first arm's value.
    """
    for keyword in ("const", "default"):
        values = {json.dumps(n[keyword], sort_keys=True) for n in nodes if keyword in n}
        if len(values) > 1:
            return SEVERAL, ""
        if values:
            return keyword, next(iter(values))
    return "", ""


class Position(NamedTuple):
    """One candidate position of a document, as the three things a class there is matched by."""

    #: The property set the conjunction reaching this position states.
    own: frozenset[str]
    #: :attr:`own` with every arm of every disjunction in that conjunction folded in -- the
    #: set a class emitted for the WHOLE position would carry.
    spanning: frozenset[str]
    #: ``(keyword, arity)`` of the disjunction this node's own text states, or ``None``.  The
    #: ARITY is what lets an ordinal be checked rather than trusted.
    disjunct: tuple[str, int] | None


_RAISES = (KeyError, IndexError, TypeError, ValueError, LookupError, RecursionError)


def object_positions(root: dict) -> dict[str, Position]:
    """Every pointer of ``root`` whose conjunction states ``properties``, with its two sets.

    The candidate set the join below matches a class's resolved field set against.  Walked
    over the record's own text -- every mapping and every list member -- rather than over
    ``codegen.bundle.subschemas``' keyword table, because the question is "which positions
    could a class have been generated at" and a generator is not bound to this compiler's
    descent column.  A pointer whose ``applied_schema`` raises is skipped: a position the
    walk cannot reach is not a position a class was stamped at.
    """
    out: dict[str, Position] = {}

    def walk(node: object, pointer: str) -> None:
        if isinstance(node, dict):
            if "properties" in node or "allOf" in node or "$ref" in node:
                try:
                    own = properties_at(root, pointer)
                    spanning = properties_spanning(root, pointer)
                except _RAISES:
                    own, spanning = {}, {}
                disjunct = next(
                    (
                        (k, len(node[k]))
                        for k in DISJUNCTS
                        if isinstance(node.get(k), list) and node[k]
                    ),
                    None,
                )
                if own or spanning:
                    out[pointer] = Position(frozenset(own), frozenset(spanning), disjunct)
            for key, sub in node.items():
                walk(sub, f"{pointer}/{key.replace('~', '~0').replace('/', '~1')}")
        elif isinstance(node, list):
            for index, sub in enumerate(node):
                walk(sub, f"{pointer}/{index}")

    walk(root, "")
    return out


# ------------------------------------------------------------------------------- the report


class Row(NamedTuple):
    """One ``(upstream class, field)`` of the set, or one refusal to read a class."""

    kind: str
    upstream: str
    field: str
    document: str
    pointer: str
    upstream_default: str
    document_states: str
    whence: str


def verdict(
    record: dict, pointer: str, wire: str, default: str, spanning: bool = False
) -> tuple[str, str]:
    """``(kind, what the document states)`` for one field at one position of one document.

    The three readings joined, and the conjunction is what reading (2) asks: ``status`` is
    required at ``#/oneOf/0`` because ``allOf[1]`` requires it, and the arm's own text never
    mentions it.

    ``spanning`` says the class was matched to this position at its ARM-UNION property set --
    one class where the document states a disjunction -- so a property only some arm requires
    is read as :data:`KINDS`' ``collapsed-disjunction`` rather than as optional.
    """
    required = required_at(record, pointer)
    if wire not in required:
        if spanning and wire in some_arm_requires(record, pointer):
            keyword, value = stated_value(properties_spanning(record, pointer).get(wire, []))
            if keyword == SEVERAL:
                return SEVERAL, "(required by some arm)"
            if not keyword:
                return "collapsed-disjunction", "nothing (required by some arm)"
            if value == default or not default:
                return "collapsed-disjunction", f"{keyword}={value} (required by some arm)"
            return "contradicts", f"{keyword}={value} (required by some arm)"
        return OPTIONAL, ""
    read = properties_spanning if spanning else properties_at
    keyword, value = stated_value(read(record, pointer).get(wire, []))
    if keyword == SEVERAL:
        return SEVERAL, ""
    if not keyword:
        return "invented-value", "nothing"
    if not default:
        # **A DEFAULT THIS READER COULD NOT READ IS NOT COMPARED.**  The document states a
        # value and upstream states one whose literal is not in the text, so the pair is
        # reported as the presence it is -- `const-restated` keeps the weaker claim, which is
        # about OPTIONALITY and needs no value -- and never as a contradiction on no evidence.
        return ("const-restated" if keyword == "const" else ""), f"{keyword}={value} (unread)"
    if value == default:
        # The document's own value, restated by their generator as a default.  Where the
        # keyword is `default` the document ALREADY made the property optional in every
        # reading a generator has, so there is nothing invented; where it is `const` the
        # value is the document's and the OPTIONALITY is not.
        return ("const-restated" if keyword == "const" else ""), f"{keyword}={value}"
    return "contradicts", f"{keyword}={value}"


def union_arms(src: dict[str, str]) -> dict[str, tuple[int, int]]:
    """``"<module>.<Arm>"`` -> ``(its index in upstream's union statement, that union's arity)``.

    **THE ORDINAL IS THE POINTER, which is ``adcp-client-python-eknd``'s own ruling and this
    is the one place it is needed.**  Upstream writes ``CreateMediaBuyResponse: TypeAlias =
    CreateMediaBuyResponse1 | CreateMediaBuyResponse2 | CreateMediaBuyResponse3``, and that
    statement lists its arms IN THE DOCUMENT'S ``oneOf`` ORDER -- so the Nth arm of their
    union is the Nth arm of the document, and no digit of any spelling is read.  A rule that
    parsed the ``1`` out of the word would be a text match on a name their generator chose.

    It answers the one question a property set cannot: at
    ``account/list-account-changes-response.json`` the root and both arms state the SAME 21
    properties -- the document redeclares every property at its root and the arms add only
    ``required`` -- so a property-set match reaches five positions whose required sets
    differ.  A class their union statement NAMES is an arm; a class it does not name is the
    whole position, which is what :func:`candidates_for` reads off this.

    The arity travels with the index so the ordinal can be CHECKED against the document's own
    arm count rather than trusted -- ``codegen.structure.bind_statements``' ``arity`` gate,
    at the one place this module needs it.
    """
    out: dict[str, tuple[int, int]] = {}
    for module, text in src.items():
        try:
            parsed = ast.parse(text)
        except SyntaxError:
            continue
        for node in parsed.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                value = node.value
            elif isinstance(node, ast.AnnAssign) and node.value is not None:
                value = node.value
            else:
                continue
            found = _union_arms(value)
            for index, arm in enumerate(found):
                out[f"{module}.{arm}"] = (index, len(found))
    return out


def _union_arms(node: ast.expr) -> list[str]:
    """``A | B | C`` as ``["A", "B", "C"]``, or ``[]`` where any arm is not a bare name.

    All-or-nothing, which is ``codegen.structure._arms_of``'s own rule: a union one of whose
    arms is a subscript or a literal is not a position table, and half of one is not either.
    """
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        left, right = _union_arms(node.left), _union_arms(node.right)
        return [*left, *right] if left and right else []
    return []


def candidates_for(
    key: str,
    want: frozenset[str],
    held: dict[str, Position],
    arm: tuple[int, int] | None,
) -> tuple[list[str], bool]:
    """``(the positions this class could be at, whether it SPANS a disjunction there)``.

    Three rules, in this order, and each is a statement one of the two sides makes:

    1. **An arm of upstream's own union statement is at that ordinal's pointer.**  Checked
       against the document's arm count, so an ordinal is never trusted past the arity gate.
    2. **A class whose fields are a position's own property set is a class at that
       position** -- the exact match, and an arm pointer enclosed by another candidate is
       dropped, because a class their module did NOT name as an arm is not one.
    3. **A class whose fields are a position's ARM-UNION set spans the disjunction there** --
       one class where the document states a choice.  Strictly weaker than (2), so it never
       shadows it.

    Everything after that is the caller's per-field fallback, under the same unanimity rule.
    """
    if arm is not None:
        index, arity = arm
        ordinal = sorted(
            f"{p}/{place.disjunct[0]}/{index}"
            for p, place in held.items()
            if place.disjunct
            and place.disjunct[1] == arity
            and f"{p}/{place.disjunct[0]}/{index}" in held
        )
        if ordinal:
            # **THE ARITY GATE PASSED AT SEVERAL POSITIONS IS STILL AN AMBIGUITY**, and the
            # property set is what breaks it: a document with two unions of the same arity
            # offers the ordinal two pointers, and binding the first would be exactly the
            # "resolved by position" ``codegen.structure.REFUSALS`` forbids.  Narrowed where
            # the class's own fields name one of them, and left ambiguous -- for the caller's
            # unanimity rule to refuse -- where they do not.
            exact_arm = [p for p in ordinal if held[p].own == want]
            return (exact_arm or ordinal), False
    exact = sorted(p for p, place in held.items() if place.own == want)
    if exact:
        enclosed = {
            f"{p}/{keyword}/{index}"
            for p in exact
            for keyword in DISJUNCTS
            for index in range(len(held))
        }
        return [p for p in exact if p not in enclosed] or exact, True
    over = sorted(p for p, place in held.items() if place.spanning == want)
    return over, True


def read(
    decls: dict[str, Decl], records: dict[str, dict], arms: dict[str, tuple[int, int]]
) -> tuple[list[Row], collections.Counter[str], dict[str, list[str]]]:
    """The set, the counts, and every ``(class, field)`` the reading could not reach.

    **THE POINTER IS NOT DISAMBIGUATED AND DOES NOT HAVE TO BE, which is what makes this
    reading independent of either generator's naming.**  A class's candidate positions are
    the positions of its document whose conjunction states EXACTLY its resolved property set;
    ``#``, ``#/allOf/0`` and ``#/allOf/1`` of a document in the ``allOf`` form all state the
    same set, because draft-07 holds every conjunct against one instance and
    ``applied_schema`` says so -- so a reading that insisted on one pointer would refuse 842
    of upstream's classes for an ambiguity that does not touch the question being asked.
    Instead the VERDICT is taken at every candidate and emitted only where they AGREE; where
    they do not, the pair is reported as ``verdict-depends-on-position`` and never decided.

    Where no position has the class's property set -- their generator split a subject across
    bases this reader could not fold, or added a field of its own -- the candidates fall back
    to every position of the document that declares the PROPERTY, under the same unanimity
    rule.  A property no position declares is ``field-absent``: the document says nothing
    about it, so upstream's default is not one it invented against the document.
    """
    rows: list[Row] = []
    counts: collections.Counter[str] = collections.Counter()
    unread: dict[str, list[str]] = collections.defaultdict(list)
    positions: dict[str, dict[str, Position]] = {}
    cohort: dict[tuple[str, frozenset[str]], list[str]] = collections.defaultdict(list)
    for key, decl in sorted(decls.items()):
        if decl.document:
            cohort[(decl.document, frozenset(resolved(key, decls)))].append(key)
    for key, decl in sorted(decls.items()):
        if not decl.document:
            continue  # not a generated module at all; counted by the caller
        fields = resolved(key, decls)
        defaulted = {w: f for w, f in fields.items() if f.defaulted}
        if not defaulted:
            unread["no-defaults"].append(key)
            continue
        document = document_for(decl.document, records)
        if not document:
            unread["document-absent"].append(f"{key}\t{decl.document}")
            continue
        # **THE JOIN MUST BE UNIQUE IN BOTH DIRECTIONS**, which is ``codegen.structure.bind``'s
        # own second check: a structure SEVERAL of upstream's words share reaches a position
        # that cannot be any one of theirs.  Measured: ``core/postal-area.json`` has five
        # ``PostalArea1NN`` classes with one property set and one ``const`` per arm, and
        # without this gate each was placed at ``#/anyOf/0`` and reported as contradicting a
        # value that belongs to a different arm.  An arm NAMED by a union statement is exempt
        # -- the ordinal is the pointer and it tells them apart.
        sharing = cohort.get((decl.document, frozenset(fields)), ())
        if len(sharing) > 1 and key not in arms:
            unread["several-classes-one-structure"].append(f"{key}\t{len(sharing)}")
            continue
        record = records[document]
        if document not in positions:
            positions[document] = object_positions(record)
        held = positions[document]
        want = frozenset(fields)
        matched, spanning = candidates_for(key, want, held, arms.get(key))
        for wire, field in sorted(defaulted.items()):
            candidates = matched or sorted(
                p for p, place in held.items() if wire in place.own or wire in place.spanning
            )
            if not candidates:
                unread["field-absent"].append(f"{key}\t{wire}")
                continue
            read_at = {
                p: verdict(record, p, wire, field.default, spanning or not matched)
                for p in candidates
            }
            # **UNANIMITY IS ON THE WHOLE ANSWER AND NOT ON THE KIND.**  Two positions that
            # both read `contradicts` against two DIFFERENT stated values have not agreed
            # about anything, and reporting the first one's value would be the arbitrary
            # pick this reading refuses.  Measured: without this clause 112 pairs were
            # reported as contradictions whose only evidence was a candidate set the
            # ordinal could not narrow.
            if len(set(read_at.values())) > 1:
                unread["verdict-depends-on-position"].append(
                    f"{key}\t{wire}\t"
                    + "; ".join(
                        f"{p or '#'}={k}{(' ' + s) if s else ''}"
                        for p, (k, s) in sorted(read_at.items())
                    )
                )
                continue
            kind, states = next(iter(read_at.values()))
            counts[kind or OPTIONAL] += 1
            if kind == SEVERAL:
                unread[SEVERAL].append(f"{key}\t{wire}\t{candidates[0] or '#'}")
                continue
            if not kind or kind == OPTIONAL:
                continue
            rows.append(
                Row(
                    kind,
                    key,
                    wire,
                    document,
                    ",".join(p or "#" for p in candidates),
                    field.default,
                    states,
                    field.whence,
                )
            )
    return rows, counts, dict(unread)


def _digest(rows: list[Row]) -> str:
    """A digest of the SET's membership, not of its size.

    **A COUNT THAT DOES NOT MOVE IS NOT EVIDENCE THE SET DID NOT MOVE** -- measured on this
    very suite today, where a resolving set changed membership at identical pass and fail
    totals.  So the artifact carries a digest of ``(kind, class, field)`` and a reader
    comparing two runs compares that.
    """
    canonical = json.dumps(sorted((r.kind, r.upstream, r.field) for r in rows), sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()[:20]


# ------------------------------------------------------------------- and the same of OURS

#: The package this compiler writes into, where a class states its own position.  Not a
#: path: the reading is over IMPORTED classes, because the question is what a class
#: *admits* and only pydantic can answer that -- and ``model_fields`` resolves inheritance
#: for free, which is the half of the upstream reading that needed its own AST fold.
OURS = "adcp.types._schemas"

#: The file-local names in :data:`RESTORED` whose before-validator may insert a key.  A
#: restored file is upstream's bytes byte for byte, so a default INVENTED IN HAND-WRITTEN
#: CODE cannot be read off ``model_fields`` at all -- the field stays required and a
#: ``model_validator(mode="before")`` fills it in before pydantic ever checks.  This is the
#: one shape the declarative reading is blind to, so it is read separately, by AST, over
#: upstream's own restored text.
RESTORED = ROOT / "src" / "adcp" / "types"


class Ours(NamedTuple):
    """One ``(class of ours, field)`` where our own class is lax about the conjunction."""

    kind: str
    ours: str
    field: str
    document: str
    pointer: str
    default: str
    document_states: str


def our_classes(package: str = OURS) -> list[tuple[str, Any]]:
    """``("<module>.<Class>", the class)`` for every class of ours that states a pointer.

    Imported and not parsed.  ``__adcp_schema__`` is this compiler's own statement of the
    join, exactly as the generated header is upstream's, and it is stronger: it names a
    POINTER and not only a document, so nothing has to be matched by property set.
    """
    root = importlib.import_module(package)
    out: list[tuple[str, Any]] = []
    for found in pkgutil.walk_packages(root.__path__, root.__name__ + "."):
        try:
            module = importlib.import_module(found.name)
        except Exception:  # noqa: BLE001 -- a module that will not import is not a reading
            continue
        for value in vars(module).values():
            if not isinstance(value, type) or getattr(value, "__module__", "") != found.name:
                continue
            if getattr(value, "model_fields", None) is None:
                continue
            if getattr(value, "__adcp_schema__", None) is None:
                continue
            out.append((f"{found.name}.{value.__name__}", value))
    return sorted(out, key=lambda pair: pair[0])


def ours(
    records: dict[str, dict], package: str = OURS
) -> tuple[list[Ours], collections.Counter[str], list[Ours]]:
    """``(our lax pairs, the counts, the disjunction bases)`` -- the 867's question of US.

    One reading, three outcomes per ``(class, field)`` where the conjunction at the class's
    own stated pointer requires the field:

    ``required-no-default``
        the field is declared and pydantic calls it required.  Our class refuses the object
        the document refuses, which is the whole claim, and no mechanism is involved.
    ``field-not-declared-here``
        the conjunction requires it and this class carries no such slot.  The instrument's
        ``field-absent`` discipline applies unchanged: a class with no field has no default,
        so there is nothing for the document to disagree with.
    a default
        the one case that needs deciding, and :func:`_disjunction_base` decides it.
    """
    lax: list[Ours] = []
    bases: list[Ours] = []
    counts: collections.Counter[str] = collections.Counter()
    for key, cls in our_classes(package):
        ref = cls.__adcp_schema__
        document = document_for(ref.document, records)
        if not document:
            counts["document-absent"] += 1
            continue
        record = records[document]
        pointer = "" if ref.pointer == "#" else ref.pointer.lstrip("#")
        try:
            required = required_at(record, pointer)
        except _RAISES:
            counts["pointer-unreadable"] += 1
            continue
        counts["classes-read"] += 1
        by_wire = {(f.alias or n): f for n, f in cls.model_fields.items()}
        for wire in sorted(required):
            counts["conjunction-required-fields"] += 1
            field = by_wire.get(wire)
            if field is None:
                counts["field-not-declared-here"] += 1
                continue
            if field.is_required():
                counts["required-no-default"] += 1
                continue
            keyword, value = stated_value(properties_at(record, pointer).get(wire, []))
            row = Ours(
                "",
                key,
                wire,
                document,
                ref.pointer,
                json.dumps(field.default, sort_keys=True, default=str),
                f"{keyword}={value}" if keyword else "nothing",
            )
            if _disjunction_base(record, pointer, wire, cls):
                counts["disjunction-base"] += 1
                bases.append(row._replace(kind="disjunction-base"))
                continue
            counts["LAX"] += 1
            lax.append(row._replace(kind="invented-by-us"))
    return lax, counts, bases


def _disjunction_base(record: dict, pointer: str, wire: str, cls: Any) -> bool:
    """Is this default the BASE's own slot, with the requirement carried by the branches?

    Two conditions, and the second is behavioural because the first cannot be trusted alone.

    1. The field is required at this position only through :func:`required_at`'s every-arm
       clause -- the conjunction's own ``required`` lists never name it.  So the position
       states a disjunction, every arm of which requires the field, and the class at the
       position is the shared base of that disjunction.
    2. **AND THE CLASS REFUSES THE OMISSION.**  Measured, not assumed: the base's own
       ``model_fields`` says ``= None`` and the refusal comes from somewhere else entirely
       -- ``BranchDispatchMixin`` dispatch, a ``RequiredGroups`` rule or a ``PresenceGroups``
       rule -- so a reading that stopped at (1) would be asserting the mechanism exists
       rather than that it works.  ``model_validate({})`` is the cheapest object that omits
       the field; a class that ACCEPTS it has no requirement left anywhere and is lax
       whatever its shape suggests.  The error's own ``loc`` names only the FIRST field it
       reached, so the loc is deliberately not read: three of eleven name the field and the
       other eight name a sibling, and requiring the name would report eight tree defects
       that are an artifact of pydantic's error order.
    """
    own = frozenset(n for node in conjoined(record, pointer) for n in _required(node))
    if wire in own:
        return False
    if not any(
        wire in frozenset.intersection(*(_required(a) for a in arms))
        for arms in arms_at(record, pointer)
    ):
        return False
    try:
        cls.model_validate({})
    except Exception:  # noqa: BLE001 -- any refusal is a refusal; the shape is not the claim
        return True
    return False


def restored_injections(where: Path = RESTORED) -> list[tuple[str, str, str]]:
    """``(file, "<Class>.<validator>", key)`` for every key a restored before-validator INSERTS.

    **THE ONE SHAPE ``model_fields`` CANNOT SEE.**  ``canonical_creative.CreateMediaBuy-
    Response1`` declares no default for ``status`` -- it inherits our emitted arm, where the
    field is required -- and a ``model_validator(mode="before")`` three lines down writes
    ``{**data, "status": "completed"}`` when the caller omitted it.  The field is required
    and the requirement is unreachable, so the declarative reading above calls the class
    correct and the class admits exactly the object the document refuses.

    Read by AST over the text, because the question is what the code WRITES and not what it
    computes.  Insertion is not weakening on its own -- ``CreativeManifest._normalize_-
    standalone_assets`` inserts ``assets`` and its class still refuses an ``assets``-less
    object -- so the caller decides, and :func:`ours` is not the reading that does it.
    """
    out: list[tuple[str, str, str]] = []
    for path in sorted(where.glob("*.py")):
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for member in node.body:
                if not isinstance(member, ast.FunctionDef):
                    continue
                if not any("before" in ast.unparse(d) for d in member.decorator_list):
                    continue
                keys = {
                    k.value
                    for found in ast.walk(member)
                    if isinstance(found, ast.Dict)
                    for k in found.keys
                    if isinstance(k, ast.Constant) and isinstance(k.value, str)
                }
                for key in sorted(keys):
                    out.append((path.name, f"{node.name}.{member.name}", key))
    return out


def records_of(where: Path) -> dict[str, dict]:
    """Every document of record, keyed by the name a generated header would name it."""
    out: dict[str, dict] = {}
    for path in sorted(where.rglob("*.json")):
        rel = path.relative_to(where).as_posix()
        try:
            out[rel] = json.loads(path.read_text())
        except ValueError:
            continue
    return out


def _report_ours(records: dict[str, dict]) -> int:
    """``--ours``: the 867's question asked of this compiler's output, printed."""
    lax, counts, bases = ours(records)
    print(f"{counts['classes-read']} classes of ours state a pointer; {len(records)} records")
    for name, n in sorted(counts.items()):
        print(f"  {n:6d}  {name}")
    print(f"INVENTED BY US: {len(lax)} (class, field) pairs")
    for row in lax:
        print("  " + "\t".join(row))
    print(f"disjunction bases, requirement carried by the branches: {len(bases)}")
    for row in bases:
        print("  " + "\t".join(row))
    injections = restored_injections()
    print(f"keys a restored before-validator INSERTS: {len(injections)}")
    for where, who, key in injections:
        print(f"  {where}\t{who}\t{key}")
    return 0



#: WHOSE each pair of the set is, which is ``adcp-client-python-0z0u``'s own question and the
#: one thing the four :data:`KINDS` do not answer.  A kind says what the document states AT
#: the position; this says who is wrong about it:
WHOSE = {
    "THEIRS": (
        "the document states no `default` for this property ANYWHERE the instance can reach "
        "-- not at the position, not in a conjunct, not through a `$ref`, not in a branch of a "
        "disjunction, not in an `if`/`then`/`else`, and not at any other position of the same "
        "document that declares the property -- and the conjunction REQUIRES it.  So the "
        "default is upstream's generator's own, and every test of theirs that omits the "
        "property cannot pass against a class that honours the document"
    ),
    "OURS": (
        "the document DOES state a `default` for this property somewhere the conjunction "
        "reaching the position holds against the same instance, and our emitted class does "
        "not carry it.  The keyword is named in the row.  This is the only outcome of the "
        "three that is a defect of this compiler"
    ),
    "ELSEWHERE": (
        "a `default` for this property is stated in the document but NOT where the "
        "conjunction at this position reaches it -- a branch of a disjunction the instance need "
        "not have taken, an `if`/`then` whose condition is not asserted here, or another "
        "position of the same document entirely.  Neither side reads it there, and neither "
        "side is wrong to: draft-07 does not hold a branch's statement against an instance that "
        "took another branch.  Reported with WHERE it is stated so the reading can be argued"
    ),
}

#: Where a widened search for a ``default`` looks, beyond what :func:`stated_value` reads.
#:
#: **EACH IS A PLACE THE ROW'S OWN QUESTION NAMES** -- "an enclosing ``allOf``, a ``$ref``
#: target, a sibling ``if``/``then``" -- and the first two are already inside
#: :func:`conjoined`, which is why only the last two are new here.  ``dependencies`` is not
#: looked in: it states a schema that applies when ANOTHER property is present, so a default
#: under it is conditioned on a key this reading has not asserted, which is the same thing an
#: branch is and would be reported as :data:`WHOSE`'s ``ELSEWHERE`` under a different name.
WIDENED = ("branch-of-a-disjunction", "if-then-else", "another-position-of-the-document")


def _default_for(node: object, field: str) -> str | None:
    """The ``default`` one node states for ``field``, as canonical JSON, or ``None``."""
    if not isinstance(node, dict):
        return None
    declared = node.get("properties")
    if not isinstance(declared, dict):
        return None
    held = declared.get(field)
    if isinstance(held, dict) and "default" in held:
        return json.dumps(held["default"], sort_keys=True)
    return None


def _conditional_nodes(root: dict, nodes: list[dict]) -> list[dict]:
    """The ``if``/``then``/``else`` sub-nodes of a conjunction, through the store.

    Read as a SEPARATE place and not folded into :func:`conjoined`, which is the distinction
    that makes the answer honest: draft-07 applies ``then`` only to an instance the ``if``
    accepts, so a ``default`` there is not one the conjunction states unconditionally.  A pair
    whose only default is here is :data:`WHOSE`'s ``ELSEWHERE`` and not ``OURS``.
    """
    out: list[dict] = []
    for node in nodes:
        for keyword in ("if", "then", "else"):
            found = through_the_store(node.get(keyword), root)
            if isinstance(found, dict):
                out.extend(_conjuncts(root, found))
    return out


def default_elsewhere(
    root: dict, pointer: str, field: str, positions: dict[str, Position]
) -> tuple[str, str, str]:
    """``(where, at, value)`` for a ``default`` this reading finds OUTSIDE the conjunction.

    ``("", "", "")`` where the document states none anywhere.  The three places are
    :data:`WIDENED`, asked in that order, so the nearest statement is the one reported.

    **ASKED OF THE PROPERTY AND NEVER OF THE FIELD NAME**: ``field`` here is the WIRE key the
    caller already resolved from upstream's own declaration, so nothing is inferred from the
    python attribute's spelling -- which is ``adcp-client-python-0z0u``'s instruction read
    literally ("derive; do not infer from the field name").
    """
    for disjunction in arms_at(root, pointer):
        for node in disjunction:
            for found in _conjuncts(root, node):
                value = _default_for(found, field)
                if value is not None:
                    return "branch-of-a-disjunction", pointer, value
    for node in _conditional_nodes(root, conjoined(root, pointer)):
        value = _default_for(node, field)
        if value is not None:
            return "if-then-else", pointer, value
    for other in sorted(positions):
        if other == pointer:
            continue
        try:
            held = conjoined(root, other)
        except _RAISES:
            continue
        for node in held:
            value = _default_for(node, field)
            if value is not None:
                return "another-position-of-the-document", other, value
    return "", "", ""


class Whose(NamedTuple):
    """One pair of the set, attributed."""

    whose: str
    kind: str
    upstream: str
    field: str
    document: str
    pointer: str
    upstream_default: str
    document_states: str
    #: Where a ``default`` was found outside the conjunction, or ``""``.
    elsewhere: str
    #: The pointer that statement sits at, or ``""``.
    elsewhere_at: str
    #: What our own emitted class does with the field: ``required``, a default, or absent.
    ours: str



def _a_rule_names(cls: Any, wire: str) -> bool:
    """Does a RULE of this class carry the requirement the annotation does not?

    **AN OPTIONAL ANNOTATION IS NOT LAXNESS WHERE A RULE REFUSES THE SAME OBJECT.**  Where the
    document states a disjunction and SOME branch requires a property, the requirement cannot
    sit on the annotation -- no branch is the whole position -- so this compiler puts it in a
    rule and the class refuses an instance satisfying none.  Measured on
    ``core/attestation-evaluation.json#/properties/action_binding``: our ``ActionBinding``
    carries ``RequiredGroups(groups=(('action_id',), ('action_digest',)), combinator='anyOf')``
    and ``strict_validate({'action_type': 'x'})`` is REFUSED, while upstream's class admits it.

    Read off the class's own ``_adcp_rules`` by the NAMES each rule holds, so a rule kind this
    does not know about answers ``False`` rather than silently passing.
    """
    for rule in getattr(cls, "_adcp_rules", ()) or ():
        for group in getattr(rule, "groups", ()) or ():
            if wire in group:
                return True
    return False

def attribute(
    rows: list[Row], records: dict[str, dict], package: str = OURS
) -> list[Whose]:
    """Each of the set's pairs as :data:`WHOSE`, with the document and pointer it is read at.

    **THE THREE OUTCOMES ARE DECIDED BY THE DOCUMENT AND NOT BY THE KIND.**  A kind is what
    the document states at the position; this asks the further question the row needs -- is
    there a ``default`` for this property anywhere, and does our class carry it:

    1. the conjunction's own reading states a ``default`` (:func:`stated_value`'s second
       keyword) and ours does not carry it -> ``OURS``, with the keyword named;
    2. a widened search finds one somewhere the conjunction does not reach ->
       ``ELSEWHERE``, with where;
    3. nothing anywhere -> ``THEIRS``.

    Our side is read off the emitted classes the same way :func:`ours` reads them, by the
    class's own ``__adcp_schema__`` and its pydantic field, so "ours does not carry it" is a
    measurement of this tree and not an assumption about it.
    """
    # **OUR SIDE IS READ WITH THE SAME THREE OUTCOMES ``ours()`` USES, and the third is the
    # one that matters here.**  A default on a class of ours is not laxness where the class is
    # a union BASE and the requirement is carried by its branches -- ``_disjunction_base`` is
    # that reading, and it is the same function ``ours()`` decides by, so the two readings of
    # our tree cannot come to disagree.  Measured: 115 of the 867 land on a class of ours that
    # defaults the field, and every one is a base of that kind.
    mine: dict[tuple[str, str, str], str] = {}
    for _key, cls in our_classes(package):
        ref = cls.__adcp_schema__
        document = document_for(ref.document, records)
        record = records.get(document) if document else None
        pointer = "" if ref.pointer == "#" else ref.pointer.lstrip("#")
        for name, info in cls.model_fields.items():
            wire = info.alias or name
            if info.is_required():
                mine[(ref.document, pointer, wire)] = "required"
                continue
            base = False
            if record is not None:
                try:
                    base = _disjunction_base(record, pointer, wire, cls)
                except _RAISES:
                    base = False
            mine[(ref.document, pointer, wire)] = (
                "disjunction-base"
                if base
                else "carried-by-a-rule"
                if _a_rule_names(cls, wire)
                else f"default={json.dumps(info.default, default=str, sort_keys=True)}"
            )

    out: list[Whose] = []
    positions: dict[str, dict[str, Position]] = {}
    for row in rows:
        document = document_for(row.document, records)
        record = records.get(document) if document else None
        # A row whose pointer column names SEVERAL candidate positions is read at the first:
        # the set's own derivation emitted it only where every candidate AGREES about the
        # field (``verdict-depends-on-position`` is the refusal for the rest), so any one of
        # them answers and the first is not a pick between disagreeing readings.
        pointer = row.pointer.split(",")[0]
        states = row.document_states
        ours_says = mine.get((row.document, pointer, row.field), "not-declared-here")
        if record is None:
            out.append(
                Whose("ELSEWHERE", row.kind, row.upstream, row.field, row.document, pointer,
                      row.upstream_default, states, "document-absent", "", ours_says)
            )
            continue
        if states.startswith("default="):
            whose = "OURS" if not ours_says.startswith("default=") else "THEIRS"
            out.append(
                Whose(whose, row.kind, row.upstream, row.field, row.document, pointer,
                      row.upstream_default, states, "", "", ours_says)
            )
            continue
        if document not in positions:
            positions[document] = object_positions(record)
        try:
            where, at, _ = default_elsewhere(record, pointer, row.field, positions[document])
        except _RAISES:
            where, at = "", ""
        if where:
            out.append(
                Whose("ELSEWHERE", row.kind, row.upstream, row.field, row.document, pointer,
                      row.upstream_default, states, where, at, ours_says)
            )
            continue
        out.append(
            Whose("THEIRS", row.kind, row.upstream, row.field, row.document, pointer,
                  row.upstream_default, states, "", "", ours_says)
        )
    return out


#: Upstream's own behavioural suite, on this branch.  ``tests/`` is THEIRS here and
#: ``tests_emit/`` is ours, which is the same reading ``./check`` makes of which directory
#: holds the suite.
UPSTREAM_TESTS = ROOT / "tests"

#: Upstream's own test files that grade THEIR GENERATOR rather than SDK behaviour, DECLARED in
#: this repository because no predicate over a path separates them.  104 of their 681
#: ``test_*.py``; the remaining 577 are the behavioural set every drop-in figure is over.
GENERATOR_TESTS = ROOT / "survey" / "dropin" / "upstream-tests-about-their-generator.txt"


def _constructs_without(call: ast.Call, field: str) -> bool:
    """Does this call construct something WITHOUT naming ``field``, and with no ``**`` splat?

    A ``**kwargs`` call cannot be read: the field may be in the mapping, so such a site is not
    counted -- the figure is a FLOOR and a site this cannot decide must not inflate it.
    """
    if any(word.arg is None for word in call.keywords):
        return False
    return all(word.arg != field for word in call.keywords)


def tests_depending_on(pairs: list[Whose], where: Path = UPSTREAM_TESTS) -> dict[str, object]:
    """How many of upstream's own behavioural TESTS depend on a ``THEIRS`` default.

    **THE FLOOR AND NOT THE TOTAL.**  A test depends on one of these defaults when it
    constructs one of the set's classes and does NOT pass the field -- the class fills it in,
    and a class honouring the document refuses the same call.  Counted per TEST FUNCTION, not
    per site, because a function is what passes or fails.

    Parsed with ``ast`` and never grepped, so a class named in a string or a comment is not a
    construction.  Two screens keep it a floor: a call carrying ``**`` is skipped (the field
    may be in the mapping), and a file on :data:`GENERATOR_TESTS` is attributed to the 104 that
    grade upstream's generator rather than to the 577 behavioural ones -- the denominator this
    repository already declares.

    **TWO IDIOMS, because one of them is the dominant one.**  A keyword construction
    ``X(a=1)`` is read from the call's own keywords; a ``X.model_validate({...})`` is read from
    the dict LITERAL's own keys, where the payload is a literal at the call site.  A payload
    built elsewhere and passed by name is not read -- the keys are not at the site -- so the
    number stays a floor, and the two idioms are counted separately so a reader can see which
    is carrying it.
    """
    by_class: dict[str, set[str]] = collections.defaultdict(set)
    for pair in pairs:
        if pair.whose == "THEIRS":
            by_class[pair.upstream.rsplit(".", 1)[1]].add(pair.field)
    declared = {
        line.strip()
        for line in GENERATOR_TESTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    behavioural: set[tuple[str, str]] = set()
    generator: set[tuple[str, str]] = set()
    files: set[str] = set()
    idioms: collections.Counter[str] = collections.Counter()
    sites = 0
    for path in sorted(where.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        name = str(path.relative_to(ROOT))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test"):
                continue
            for inner in ast.walk(node):
                if not isinstance(inner, ast.Call):
                    continue
                omitted = False
                if isinstance(inner.func, ast.Name) and by_class.get(inner.func.id):
                    omitted = any(
                        _constructs_without(inner, field) for field in by_class[inner.func.id]
                    )
                    if omitted:
                        idioms["keyword-construction"] += 1
                elif (
                    isinstance(inner.func, ast.Attribute)
                    and inner.func.attr in ("model_validate", "model_validate_json")
                    and isinstance(inner.func.value, ast.Name)
                    and by_class.get(inner.func.value.id)
                    and inner.args
                    and isinstance(inner.args[0], ast.Dict)
                ):
                    keys = {
                        k.value
                        for k in inner.args[0].keys
                        if isinstance(k, ast.Constant) and isinstance(k.value, str)
                    }
                    if None in inner.args[0].keys:
                        continue  # a ``**`` splat: the field may be in the mapping
                    omitted = any(
                        field not in keys for field in by_class[inner.func.value.id]
                    )
                    if omitted:
                        idioms["model_validate-dict-literal"] += 1
                if omitted:
                    sites += 1
                    files.add(name)
                    (generator if name in declared else behavioural).add((name, node.name))
    return {
        "classes_with_a_theirs_default": len(by_class),
        "idioms": dict(idioms),
        "sites": sites,
        "files": sorted(files),
        "behavioural_tests": sorted(behavioural),
        "generator_tests": sorted(generator),
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--revision", default=REVISION)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--records", type=Path, default=RECORDS)
    parser.add_argument("--table", type=Path, default=None)
    parser.add_argument("--unread", type=Path, default=None)
    parser.add_argument(
        "--ours",
        action="store_true",
        help="ask OUR tree the identical question instead of upstream's (survey.ours)",
    )
    parser.add_argument(
        "--attribute",
        type=Path,
        default=None,
        help="write the WHOSE attribution of every pair -- OURS, THEIRS or ELSEWHERE",
    )
    parser.add_argument(
        "--tests",
        action="store_true",
        help="count upstream's own tests that depend on a THEIRS default (needs --attribute)",
    )
    args = parser.parse_args(argv)

    if args.ours:
        return _report_ours(records_of(args.records))

    src = sources(args.revision, args.repo)
    decls = declarations(src)
    records = records_of(args.records)
    arms = union_arms(src)
    rows, counts, unread = read(decls, records, arms)

    generated = [k for k, d in decls.items() if d.document]
    print(
        f"{len(src)} modules at {args.revision}; {len(decls)} declarations, "
        f"{len(generated)} of them generated from a named document; "
        f"{len(records)} records"
    )
    print(f"INVENTED DEFAULTS: {len(rows)} (class, field) pairs")
    for kind, n in sorted(counts.items()):
        print(f"  {n:5d}  {kind}" + ("" if kind in KINDS or kind == OPTIONAL else "  [agrees]"))
    print("not read:")
    for reason, keys in sorted(unread.items()):
        print(f"  {len(keys):5d}  {reason}")
    classes = {r.upstream for r in rows}
    print(f"over {len(classes)} distinct classes; {len({r.field for r in rows})} distinct fields")
    print(f"digest {_digest(rows)}")

    if args.table:
        lines = ["\t".join(Row._fields)]
        lines += ["\t".join(str(v) for v in r) for r in sorted(rows)]
        args.table.write_text("\n".join(lines) + "\n")
        print(f"-> {args.table}")
    if args.unread:
        args.unread.write_text(
            "\n".join(f"{reason}\t{key}" for reason, keys in sorted(unread.items()) for key in keys)
            + "\n"
        )
        print(f"-> {args.unread}")

    if args.attribute or args.tests:
        pairs = attribute(rows, records)
        if not pairs:
            raise SystemExit("REFUSED: no pair attributed -- every figure over it is vacuous")
        print()
        print("WHOSE IS IT:")
        for whose, n in sorted(collections.Counter(p.whose for p in pairs).items()):
            print(f"  {n:5d}  {whose}")
        print("  by kind:")
        for key, n in sorted(collections.Counter((p.whose, p.kind) for p in pairs).items()):
            print(f"    {n:5d}  {key[0]:<10} {key[1]}")
        print("  what OUR class does with the same field:")
        by_ours = collections.Counter((p.whose, p.ours.split("=")[0]) for p in pairs)
        for key, n in sorted(by_ours.items()):
            print(f"    {n:5d}  {key[0]:<10} ours={key[1]}")
        elsewhere = collections.Counter(p.elsewhere for p in pairs if p.elsewhere)
        for key, n in sorted(elsewhere.items()):
            print(f"    {n:5d}  ELSEWHERE via {key}")
        if args.attribute:
            lines = ["\t".join(Whose._fields)]
            lines += ["\t".join(str(v) for v in p) for p in sorted(pairs)]
            args.attribute.write_text("\n".join(lines) + "\n")
            print(f"-> {args.attribute}")
        if args.tests:
            census = tests_depending_on(pairs)
            print()
            print("UPSTREAM TESTS THAT DEPEND ON A *THEIRS* DEFAULT (a floor):")
            held = census["classes_with_a_theirs_default"]
            print(f"  {held:5d}  classes of the set carrying a THEIRS default")
            print(f"  {census['sites']:5d}  sites omitting such a field, by idiom:")
            for idiom, n in sorted(census["idioms"].items()):
                print(f"      {n:5d}  {idiom}")
            print(f"  {len(census['files']):5d}  files")
            behav, gen = census["behavioural_tests"], census["generator_tests"]
            print(f"  {len(behav):5d}  TEST FUNCTIONS in the 577 behavioural files")
            print(f"  {len(gen):5d}  TEST FUNCTIONS in the 104 generator files")
            for name in census["files"]:
                print(f"      {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
