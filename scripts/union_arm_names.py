"""Schema-derived names for union arms (ARCH-ONE-SURFACE §3).

The generator throws a union arm's identity away. ``create-media-buy-response.json``
titles its three arms ``CreateMediaBuySuccess`` / ``CreateMediaBuyError`` /
``CreateMediaBuySubmitted``, and what ships is ``CreateMediaBuyResponse1`` / ``2``
/ ``3``. Verified directly, not assumed, on both candidates: feeding
datamodel-code-generator 0.64.0 a three-arm ``oneOf`` whose arms all carry
``title`` still produces ``DemoResponse1/2/3``, and this repo's own response
emitter numbers its arms by position too. A positional name is the drift channel the whole
one-surface design is about, because inserting an arm upstream silently repoints
an existing public name.

This module answers one question for one schema node — *what is this arm called* —
and nothing else. It does not rename anything and it does not touch the generated
tree, which keeps the naming rule auditable on its own and keeps whoever consumes
it free to apply it wherever the name is actually chosen. Two consumers:

* the custom response emitter in ``scripts/post_generate_fixes.py``, which is
  where the numbers come from for every response union — literally
  ``class_names = [f"{self.base}{index}" for index in range(1, len(arms) + 1)]``.
  Measured: of the schemas with a root union, the generator collapses most into a
  single class and the numbered arms are the emitter's own, so the naming decision
  has exactly one site and it is a line of this repo's code, not the generator's.
* ``main()``, which prints the classification of every root-level arm in the
  pinned bundle — the residual list ARCH-ONE-SURFACE §5 Step 3 asks the pass's
  first run to emit.

A schema transform was measured as the alternative and works on the generator in
isolation: lifting each arm into ``definitions/<DerivedName>`` and leaving a
``$ref`` makes 0.64.0 emit ``DemoSuccess`` / ``DemoError`` / ``DemoSubmitted``
instead of ``DemoResponse1/2/3``. It is not the mechanism used for responses only
because the emitter, not the generator, names those.

**Step zero — classify before naming.** An arm that introduces no property the
base schema does not already declare is a VALIDATION arm: its content is
``required``, ``not``, or a constraint refinement. It must mint no class, because
a public class for it would name something no buyer sends. Only then do the
naming rungs run, in order, first one that holds:

1. the node's ``title``;
2. the discriminator ``const`` — parent + PascalCase(const value);
3. the FULL required set — parent + PascalCase(each sorted required key). Not the
   set-difference against siblings: the difference is empty exactly where one arm
   is the conjunction of two others, and the bundle contains that case
   (``a2ui/bound-value.json`` has five arms requiring ``{literalString}``,
   ``{literalNumber}``, ``{literalBoolean}``, ``{path}``,
   ``{literalString, path}`` — arm 4 overlaps arms 0 and 3, so its difference is
   empty while the full sets are all distinct);
4. fail closed. No counter, no ledger of tolerated numbers: a counter quietly
   becomes load-bearing again.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

#: Arm kinds. ``ref`` already names the shared class it selects; ``scalar`` and
#: ``validation`` mint no class; ``type`` is the population the rungs name.
ArmKind = Literal["ref", "scalar", "validation", "type"]

#: Which rung produced a name, or ``"none"`` for a rung-4 refusal.
Rung = Literal["title", "const", "required-set", "none"]


def pascal_case(value: object) -> str:
    """PascalCase a schema string while PRESERVING interior capitals.

    Distinct from :func:`scripts.task_message_lattice.mangle_schema_title`, which
    reproduces the generator's root naming and therefore uses ``str.capitalize``
    (lower-casing the tail: ``Get AdCP Capabilities Request`` ->
    ``GetAdcpCapabilitiesRequest``). An arm title is frequently already written in
    PascalCase (``CreateMediaBuySuccess``), and ``capitalize`` would mangle it to
    ``Createmediabuysuccess``. Two inputs, two specifications, two functions.
    """
    words = [word for word in re.split(r"[^0-9a-zA-Z]+", str(value)) if word]
    return "".join(word[:1].upper() + word[1:] for word in words)


def _is_bare_ref(arm: dict[str, Any]) -> bool:
    """A ``$ref`` arm already names the shared class it selects."""
    return "$ref" in arm and not (set(arm) - {"$ref", "title", "description"})


#: Keywords by which an arm says something about a schema's shape.
_STRUCTURAL = frozenset({"properties", "$ref", "allOf", "oneOf", "anyOf"})

#: Keywords by which an arm constrains a shape it does not declare.
_CONSTRAINING = frozenset({"required", "not", "dependencies", "dependentRequired", "if"})


def _declares_a_scalar_value(arm: dict[str, Any]) -> bool:
    """The arm is a value, not an object type: a non-object type, a const, an enum."""
    declared = arm.get("type")
    if isinstance(declared, str) and declared != "object":
        return True
    if isinstance(declared, list) and "object" not in declared:
        return True
    return "const" in arm or "enum" in arm


def _introduced_properties(arm: dict[str, Any], base_properties: dict[str, Any]) -> set[str]:
    own = arm.get("properties")
    if not isinstance(own, dict):
        return set()
    return set(own) - set(base_properties)


def classify(arm: dict[str, Any], base_properties: dict[str, Any]) -> ArmKind:
    """Classify one root-level union arm. See the module docstring's step zero.

    Order matters, and the bundle proves it: ``create-media-buy-request.json``
    anyOf[2] declares only ``required`` and ``not`` — no ``type``, no
    ``properties`` — so a "nothing structural, therefore a scalar" fallback
    claims it, when it is the purest validation arm in the tree. A scalar is
    recognized by what it POSITIVELY declares; a constraining arm is recognized
    by its constraint keywords; only a genuinely empty arm falls through.
    """
    if _is_bare_ref(arm):
        return "ref"
    if _declares_a_scalar_value(arm):
        return "scalar"
    if _introduced_properties(arm, base_properties):
        return "type"
    if set(arm) & (_CONSTRAINING | _STRUCTURAL):
        return "validation"
    return "scalar"


def _discriminator_const(arm: dict[str, Any]) -> object | None:
    """The single pinned value a property of this arm carries, if any."""
    properties = arm.get("properties")
    if not isinstance(properties, dict):
        return None
    for node in properties.values():
        if not isinstance(node, dict):
            continue
        if "const" in node:
            const: object = node["const"]
            return const
        enum = node.get("enum")
        if isinstance(enum, list) and len(enum) == 1:
            single: object = enum[0]
            return single
    return None


def _parent_name(document: dict[str, Any], relative: Path) -> str:
    title = document.get("title")
    if isinstance(title, str) and title.strip():
        return pascal_case(title)
    return pascal_case(relative.stem)


def _candidate(
    document: dict[str, Any],
    arm: dict[str, Any],
    rung: Rung,
    relative: Path,
) -> str | None:
    """One rung's candidate name for one arm, or ``None`` if the rung is silent."""
    if rung == "title":
        title = arm.get("title")
        if isinstance(title, str) and title.strip():
            return pascal_case(title)
        return None
    parent = _parent_name(document, relative)
    if rung == "const":
        const = _discriminator_const(arm)
        return None if const is None else f"{parent}{pascal_case(const)}"
    if rung == "required-set":
        required = arm.get("required")
        if not isinstance(required, list) or not required:
            return None
        keys = sorted(str(key) for key in required)
        return parent + "".join(pascal_case(key) for key in keys)
    return None


#: The rungs, in the order ARCH-ONE-SURFACE §3 sets them.
_RUNGS: tuple[Rung, ...] = ("title", "const", "required-set")


def derive(
    document: dict[str, Any],
    arms: list[Any],
    index: int,
    relative: Path,
) -> tuple[str | None, Rung]:
    """The arm's name by the first rung that holds, or ``(None, "none")``.

    A rung "holds" only when it yields a name that is UNIQUE among the siblings
    at that same rung. The uniqueness test is not an extra safety belt bolted
    onto rung 3 — it is what makes every rung position-free, and the bundle needs
    it on rung 2 as well: ``core/audience-selector.json`` has three arms all
    pinning ``type: "signal"`` (binary, categorical and numeric signals), so the
    const rung names them identically and must fall through to the required set,
    which separates them. Found by the fail-closed rule rather than by reading.
    """
    arm = arms[index]
    siblings = [
        sibling
        for position, sibling in enumerate(arms)
        if position != index and isinstance(sibling, dict) and sibling.get("type") != "null"
    ]
    for rung in _RUNGS:
        mine = _candidate(document, arm, rung, relative)
        if mine is None:
            continue
        if any(_candidate(document, sibling, rung, relative) == mine for sibling in siblings):
            continue
        return mine, rung
    return None, "none"


@dataclass(frozen=True)
class ArmName:
    """One root-level union arm, classified and (if it is a type) named."""

    schema: str
    keyword: str
    index: int
    kind: ArmKind
    name: str | None
    rung: Rung

    @property
    def pointer(self) -> str:
        return f"{self.schema}#/{self.keyword}/{self.index}"


class UnnameableArmError(RuntimeError):
    """A type arm with no derivable name. Fail closed, naming the schema node."""


def classify_document(document: dict[str, Any], relative: Path) -> list[ArmName]:
    """Classify and name every root-level, non-null union arm of one schema."""
    results: list[ArmName] = []
    base_properties = document.get("properties")
    if not isinstance(base_properties, dict):
        base_properties = {}
    for keyword in ("oneOf", "anyOf"):
        arms = document.get(keyword)
        if not isinstance(arms, list):
            continue
        for index, arm in enumerate(arms):
            if not isinstance(arm, dict) or arm.get("type") == "null":
                continue
            kind = classify(arm, base_properties)
            if kind != "type":
                results.append(ArmName(relative.as_posix(), keyword, index, kind, None, "none"))
                continue
            name, rung = derive(document, arms, index, relative)
            results.append(ArmName(relative.as_posix(), keyword, index, kind, name, rung))
    _refuse_collisions(results, relative)
    return results


def _refuse_collisions(results: list[ArmName], relative: Path) -> None:
    """Two arms of one schema must not derive the same name."""
    taken: dict[str, ArmName] = {}
    for item in results:
        if item.name is None:
            continue
        clash = taken.get(item.name)
        if clash is not None:
            raise UnnameableArmError(
                f"{relative.as_posix()}: {item.pointer} and {clash.pointer} both derive "
                f"the name {item.name!r}; the rungs must name a schema node uniquely"
            )
        taken[item.name] = item


def schema_files(schema_dir: Path) -> list[Path]:
    """Every schema the pipeline reads: ``bundled/`` and ``mcp/`` are excluded.

    ``bundled/`` is self-contained by design and ``mcp/`` is a per-profile tree
    whose duplicates inflate every count taken over it.
    """
    return [
        path
        for path in sorted(schema_dir.rglob("*.json"))
        if "bundled" not in path.relative_to(schema_dir).parts
        and "mcp" not in path.relative_to(schema_dir).parts
    ]


def classify_bundle(schema_dir: Path) -> list[ArmName]:
    """Classify every root-level union arm in the bundle."""
    results: list[ArmName] = []
    for path in schema_files(schema_dir):
        document = json.loads(path.read_text())
        if not isinstance(document, dict):
            continue
        results.extend(classify_document(document, path.relative_to(schema_dir)))
    return results


def tally(results: list[ArmName]) -> Counter[str]:
    counts: Counter[str] = Counter()
    counts["root arms"] = len(results)
    for item in results:
        if item.kind != "type":
            counts[f"mints no class ({item.kind})"] += 1
        elif item.rung == "none":
            counts["rung 4: FAIL CLOSED"] += 1
        else:
            counts[f"rung: {item.rung}"] += 1
    return counts


def unnameable(results: list[ArmName]) -> list[ArmName]:
    return [item for item in results if item.kind == "type" and item.name is None]


def main(argv: list[str] | None = None) -> int:
    """Print the classification of the pinned bundle's root-level union arms."""
    argv = list(sys.argv[1:] if argv is None else argv)
    schema_dir = Path(argv[0]) if argv else Path("schemas/cache/3.2")
    results = classify_bundle(schema_dir)
    counts = tally(results)
    print(f"bundle: {schema_dir} ({len(schema_files(schema_dir))} schema files)")
    for key in sorted(counts):
        print(f"  {counts[key]:5d}  {key}")
    refused = unnameable(results)
    print(f"\nunnameable type arms: {len(refused)}")
    for item in refused:
        print(f"  {item.pointer}")
    derived = [item for item in results if item.name]
    print(f"\nnames derived (first 40 of {len(derived)}):")
    for item in derived[:40]:
        print(f"  {item.rung:13s} {item.pointer:68s} -> {item.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
