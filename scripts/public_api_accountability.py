#!/usr/bin/env python3
"""Which published names still resolve, and what the evidence says about the rest.

``tests/fixtures/public_api_snapshot.json`` records every name the package
published and what it resolved to. This module answers two questions about that
file and nothing else:

1. **Does each recorded name still resolve in the live tree?**
   :func:`sweep` answers it by ``getattr`` on the recording namespace, which is
   exactly what an adopter's ``from <namespace> import <name>`` does.
2. **For a name that does not, what can be MEASURED about why?**
   :func:`evidence` gathers the facts -- is the recorded document still emitted,
   does any class in the tree carry the word, does the document state a property
   the word is ``pascal_case`` of -- and :func:`propose` reads them through an
   ordered ladder to suggest a cluster.

**A PROPOSAL IS NOT A DECLARATION.** :func:`propose` is a reading aid for whoever
writes ``tests/fixtures/public_api_declarations.json``; the gate
(``tests/test_public_api_accountability.py``) reads only the frozen name lists in
that file. A name that vanishes tomorrow is therefore RED even where this ladder
would have an opinion about it -- which is the point. A cluster rule that assigns
membership at gate time would silence the next removal automatically, and the
whole obligation is that a removal is loud.

**AND THE SNAPSHOT IS NOT AN INPUT TO THE ALIAS LAYER.** It says WHICH names
existed, not what they should alias to; feeding it back would destroy its ability
to detect an alias regression, because it would then always agree with itself
(owner, 2026-11-19; ``adcp-client-python-5wr6``). Nothing here emits a binding.

Usage::

    python scripts/public_api_accountability.py            # the cluster table
    python scripts/public_api_accountability.py --unaccounted   # names with no declaration
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.export_resolution import expand_key, snapshot_modules  # noqa: E402

__all__ = [
    "LADDER",
    "evidence",
    "load_declarations",
    "load_snapshot",
    "propose",
    "resolves",
    "sweep",
    "unaccounted",
]

REPO = Path(__file__).parent.parent
SNAPSHOT_PATH = REPO / "tests" / "fixtures" / "public_api_snapshot.json"
DECLARATIONS_PATH = REPO / "tests" / "fixtures" / "public_api_declarations.json"

#: The bundle the emitted tree is compiled from. A recorded document still
#: present here is a document the compiler still walks.
BUNDLE = REPO / "schemas" / "cache" / "3.2"

#: ``export_resolution`` strips this from a resolution key; put it back to get an
#: importable module path. The mirror makes it a real one: ``adcp.types.domains``
#: substitutes the prefix onto ``adcp.types._schemas``.
GENERATED_PREFIX = "adcp.types.domains."


def load_snapshot(path: Path = SNAPSHOT_PATH) -> dict[str, dict[str, Any]]:
    """The snapshot, verbatim. Never written by anything in this module."""
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def load_declarations(path: Path = DECLARATIONS_PATH) -> dict[str, Any]:
    """The declarations file, or an empty shell where it does not exist yet."""
    if not path.exists():
        return {"kinds": {}, "clusters": []}
    return json.loads(path.read_text())  # type: ignore[no-any-return]


def declared_names(declarations: dict[str, Any]) -> dict[tuple[str, str], dict[str, str]]:
    """``(namespace, name)`` -> the cluster that declares it.

    A name declared twice is a defect of the file and the gate says so, so this
    keeps the first and :func:`duplicate_declarations` reports the rest.
    """
    out: dict[tuple[str, str], dict[str, str]] = {}
    for cluster in declarations.get("clusters", ()):
        for namespace, names in cluster.get("names", {}).items():
            for name in names:
                out.setdefault((namespace, name), cluster)
    return out


def duplicate_declarations(declarations: dict[str, Any]) -> list[tuple[str, str, list[str]]]:
    """Names more than one cluster claims: ``(namespace, name, cluster ids)``."""
    seen: dict[tuple[str, str], list[str]] = {}
    for cluster in declarations.get("clusters", ()):
        for namespace, names in cluster.get("names", {}).items():
            for name in names:
                seen.setdefault((namespace, name), []).append(cluster["id"])
    return [(ns, name, ids) for (ns, name), ids in sorted(seen.items()) if len(ids) > 1]


# --------------------------------------------------------------------------- #
# Does it resolve?
# --------------------------------------------------------------------------- #

_modules: dict[str, Any] = {}


def _module(path: str) -> Any:
    """The imported module, or ``None`` where it does not exist.

    Cached: the sweep asks for the same module thousands of times, and importing
    the generated graph is the expensive part of the whole measurement.
    """
    if path not in _modules:
        try:
            _modules[path] = importlib.import_module(path)
        except Exception:
            _modules[path] = None
    return _modules[path]


_surfaces: tuple[str, ...] | None = None


def public_surfaces() -> tuple[str, ...]:
    """The namespaces an adopter is told to import from.

    ``adcp`` and ``adcp.types`` are the flat ones; ``adcp.types.<domain>`` is the
    per-domain one. ``CLAUDE.md`` also names ``adcp.types.domains.<domain>.<schema>``
    -- the per-DOCUMENT path -- a supported import, and :func:`where_it_resolves`
    asks that one per candidate module rather than enumerating 1,025 of them here.
    """
    global _surfaces
    if _surfaces is not None:
        return _surfaces
    names = ["adcp", "adcp.types"]
    domains = _module("adcp.types.domains")
    if domains is not None:
        try:
            names += [f"adcp.types.{domain}" for domain in sorted(domains.mirrored())]
        except Exception:
            pass
    _surfaces = tuple(names)
    return _surfaces


def where_it_resolves(name: str, defining_modules: list[str]) -> list[str]:
    """Every supported public path at which ``name`` resolves right now.

    The document paths come from where the SOURCE defines the word, mapped
    ``adcp.types._schemas.X`` -> ``adcp.types.domains.X``: the second is the
    public spelling of the first and the mirror is what makes them one module.
    """
    found = [surface for surface in public_surfaces() if resolves(surface, name)]
    for module in defining_modules:
        if module.startswith("adcp.types._schemas"):
            public = module.replace("adcp.types._schemas", "adcp.types.domains", 1)
            if resolves(public, name):
                found.append(public)
    return sorted(set(found))


def resolves(namespace: str, name: str) -> bool:
    """What ``from <namespace> import <name>`` does, asked as an expression.

    ``getattr`` and not ``name in __all__``: a lazy facade (PEP 562) binds on
    access, and a name in ``__all__`` that raises on access is the failure the
    snapshot exists to catch, not a pass.
    """
    module = _module(namespace)
    if module is None:
        return False
    try:
        getattr(module, name)
    except Exception:
        return False
    return True


def sweep(snapshot: dict[str, dict[str, Any]] | None = None) -> dict[tuple[str, str], bool]:
    """Every recorded name, and whether it resolves now."""
    snapshot = snapshot if snapshot is not None else load_snapshot()
    return {
        (namespace, name): resolves(namespace, name)
        for namespace, entry in snapshot.items()
        for name in entry["resolves"]
    }


def live_namespaces() -> set[str]:
    """The namespaces the snapshot would cover if regenerated now.

    Used only to say WHICH of the snapshot's namespaces no longer exist; the gate
    does not require the two sets to agree, because the one disagreement standing
    (``brand_discovery``, ``manifest``, ``manifest_schema`` recorded,
    ``common`` live) is ``FINDINGS-126.md`` row R16 and predates this work.
    """
    try:
        return {label for label, _ in snapshot_modules()}
    except Exception:
        return set()


# --------------------------------------------------------------------------- #
# Evidence
# --------------------------------------------------------------------------- #

_class_index: dict[str, list[str]] | None = None


def _source_index() -> dict[str, list[str]]:
    """Every top-level name ``src/adcp`` defines, and the modules defining it.

    Read off the SOURCE with ``ast`` rather than by importing: a name the tree
    defines but no namespace exports is exactly the case that distinguishes "the
    subject is gone" from "the subject is there and nothing advertises it", and
    an import-based index cannot see the second.
    """
    global _class_index
    if _class_index is not None:
        return _class_index
    import ast

    index: dict[str, set[str]] = {}
    for dirpath, _dirs, files in os.walk(REPO / "src" / "adcp"):
        for filename in files:
            if not filename.endswith(".py"):
                continue
            path = Path(dirpath) / filename
            module = str(path.relative_to(REPO / "src")).replace(os.sep, ".")[: -len(".py")]
            module = module[: -len(".__init__")] if module.endswith(".__init__") else module
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            for node in tree.body:
                if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                    index.setdefault(node.name, set()).add(module)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            index.setdefault(target.id, set()).add(module)
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    index.setdefault(node.target.id, set()).add(module)
    _class_index = {name: sorted(modules) for name, modules in index.items()}
    return _class_index


def pascal(text: str) -> str:
    """``allowed_intervals`` -> ``AllowedIntervals``, §4's own nested-name rule."""
    return "".join(part[:1].upper() + part[1:] for part in re.split(r"[^0-9a-zA-Z]+", text) if part)


def _spellings(text: str) -> set[str]:
    """``pascal_case`` of a key, with the suffixes §4 and the old generator add.

    §4 names an array element ``<Property>Item`` and a mapping value
    ``<Property>Value``; ``datamodel-code-generator`` singularised the element
    instead. Both spellings are candidates for the same document key, so both
    count as the key having produced the word.
    """
    word = pascal(text)
    out = {word, word + "s", word + "Item", word + "Value", word + "Enum"}
    if word.endswith("ies"):
        out |= {word[:-3] + "y", word[:-3] + "yItem"}
    if word.endswith("ses"):
        out |= {word[:-2], word[:-2] + "Item"}
    if word.endswith("s"):
        out |= {word[:-1], word[:-1] + "Item"}
    return out


_document_of_module: dict[str, str | None] = {}


def document_of(module_path: str) -> str | None:
    """The bundle document a generated module was compiled from.

    Read off a class's own ``__adcp_schema__.document`` -- the emitted tree's own
    statement of its provenance -- and never derived from the module path. The
    path rule would be right for 1,011 of 1,025 modules and wrong for
    ``formats/canonical/*``, whose file stems carry underscores.
    """
    if module_path in _document_of_module:
        return _document_of_module[module_path]
    document = None
    module = _module(module_path)
    mirrored = module_path.replace(GENERATED_PREFIX, "adcp.types._schemas.")
    if module is not None:
        for attribute in dir(module):
            obj = getattr(module, attribute, None)
            if getattr(obj, "__module__", None) not in (module_path, mirrored):
                continue
            schema = getattr(obj, "__adcp_schema__", None)
            if schema is not None and getattr(schema, "document", None):
                document = schema.document
                break
    if document is None and module_path.startswith(GENERATED_PREFIX):
        stem = module_path[len(GENERATED_PREFIX) :].split(".")
        document = "/".join(part.replace("_", "-") for part in stem) + ".json"
    _document_of_module[module_path] = document
    return document


_vocab: dict[str, tuple[set[str], set[str]]] = {}

#: Every ``$ref`` in the bundle is absolute against this host, so the path after
#: the version segment is the document's own path within ``BUNDLE``.
_REF = re.compile(r"https://adcontextprotocol\.org/schemas/[^/]+/(?P<document>[^#\"]+)")


def _one_document_vocabulary(document: str) -> tuple[set[str], set[str], set[str]]:
    """``(titles, keys, referenced documents)`` for ONE document.

    ``required`` entries count as keys: a ``required`` name states a property of
    the same instance (``CLAUDE.md``'s conjunction rule), and the old generator
    minted a class from a presence-only branch that names one -- which is where
    ``PublisherDomain`` came from, a word ``core/canonical-product.json`` states
    only inside ``not: {required: ["publisher_domains"]}``.
    """
    titles: set[str] = set()
    keys: set[str] = set()
    refs: set[str] = set()
    path = BUNDLE / document
    if not path.exists():
        return titles, keys, refs
    data = json.loads(path.read_text())

    def walk(node: object) -> None:
        if isinstance(node, dict):
            title = node.get("title")
            if isinstance(title, str):
                titles.update(_spellings(title))
            ref = node.get("$ref")
            if isinstance(ref, str):
                match = _REF.match(ref)
                if match:
                    refs.add(match.group("document"))
            required = node.get("required")
            if isinstance(required, list):
                for entry in required:
                    if isinstance(entry, str):
                        keys.update(_spellings(entry))
            for keyword in ("properties", "definitions", "$defs", "patternProperties"):
                sub = node.get(keyword)
                if isinstance(sub, dict):
                    for key, value in sub.items():
                        keys.update(_spellings(key))
                        walk(value)
            for keyword, value in node.items():
                if keyword in ("properties", "definitions", "$defs", "patternProperties"):
                    continue
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return titles, keys, refs


def document_vocabulary(document: str | None) -> tuple[set[str], set[str]]:
    """The words a document states: ``(from titles, from keys)``, pascal-cased.

    A ``title`` is what §4 names a ROOT from, so a word a title produced names a
    subject the document itself identifies. A property, ``definitions``, ``$defs``
    or ``required`` key is what §4 names a NESTED node from -- and what the old
    generator minted a class per, titled or not.

    **THE CLOSURE IS TRANSITIVE OVER ``$ref``, because the OLD generator's module
    was.** ``datamodel-code-generator`` wrote one module per ENTRY document and
    inlined every ``$ref`` target into it, so a class named from
    ``core/signal-listing.json`` landed in ``signals/get-signals-response``'s
    module and the snapshot recorded it there. Our compiler emits one module per
    document and imports the referenced class, so asking the entry document alone
    reports ``Art9Basis``, ``Methodology``, ``Onboarder`` and four more as words
    no document states -- which is false, and was measured.
    """
    if document is None:
        return set(), set()
    if document in _vocab:
        return _vocab[document]
    # Reserve the slot first: the bundle has reference cycles and this is a
    # depth-first walk over them.
    _vocab[document] = (set(), set())
    titles: set[str] = set()
    keys: set[str] = set()
    seen = {document}
    pending = [document]
    while pending:
        current = pending.pop()
        own_titles, own_keys, refs = _one_document_vocabulary(current)
        titles |= own_titles
        keys |= own_keys
        for ref in refs:
            if ref not in seen and (BUNDLE / ref).exists():
                seen.add(ref)
                pending.append(ref)
    _vocab[document] = (titles, keys)
    return _vocab[document]


#: **THE TREE THE SNAPSHOT RECORDED.** ``tests/fixtures/public_api_snapshot.json``
#: was last written at ``5eebb5386`` (2026-11-07); ``639134c75`` (2026-11-08)
#: "remove(types): upstream's type generation and every file it emitted" deleted
#: 1,159 files and 346,184 lines the next day and our compiler's output replaced
#: them. So the snapshot is a recording of ``datamodel-code-generator``'s tree,
#: and this commit's PARENT is where every recorded name's actual definition can
#: be read -- which beats inferring the definition from its name.
RECORDED_TREE = "639134c75^"

_old_forms: dict[str, tuple[str, str]] | None = None


def old_definitions() -> dict[str, tuple[str, str]]:
    """``"<module>|<QualName>"`` -> ``(form, detail)`` in the tree the snapshot recorded.

    ``form`` is ``class``, ``assign`` or ``annassign``; ``detail`` is the base list
    or the right-hand side. An empty mapping where git cannot reach
    :data:`RECORDED_TREE` -- the ladder's rules that read this degrade to the
    document vocabulary rather than raise, because a shallow clone is a legitimate
    checkout and this is a reading aid, not the gate.
    """
    global _old_forms
    if _old_forms is not None:
        return _old_forms
    import ast
    import subprocess

    _old_forms = {}
    try:
        listing = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", RECORDED_TREE, "src/adcp/"],
            capture_output=True,
            text=True,
            cwd=REPO,
            check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, OSError):
        return _old_forms
    present = set(listing)
    for path in sorted(present):
        if not path.endswith(".py"):
            continue
        module = path[len("src/") : -len(".py")].replace("/", ".")
        module = module[: -len(".__init__")] if module.endswith(".__init__") else module
        try:
            source = subprocess.run(
                ["git", "show", f"{RECORDED_TREE}:{path}"],
                capture_output=True,
                text=True,
                cwd=REPO,
                check=True,
            ).stdout
            tree = ast.parse(source)
        except (subprocess.CalledProcessError, OSError, SyntaxError):
            continue
        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                _old_forms[f"{module}|{node.name}"] = (
                    "class",
                    ",".join(ast.unparse(base) for base in node.bases),
                )
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        _old_forms[f"{module}|{target.id}"] = (
                            "assign",
                            ast.unparse(node.value)[:120],
                        )
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                _old_forms[f"{module}|{node.target.id}"] = (
                    "annassign",
                    ast.unparse(node.annotation)[:120],
                )
    return _old_forms


#: Bases the old generator gave a class it minted for a node that is NOT a
#: subject: an anonymous ``enum`` became a ``StrEnum`` subclass and a constrained
#: scalar became a ``Scalar*`` subclass. Our compiler lowers both -- an enum to
#: ``Literal[...]`` on the field, a constrained scalar to a named constraint
#: annotation (§2 "Constraints bind to the type, not the field"). So a word whose
#: old definition carried one of these and that no class now spells names a node
#: the tree still compiles and no longer binds a class for.
_LOWERED_BASES = ("StrEnum", "Enum", "ScalarStr", "ScalarInt", "ScalarFloat", "RootModel")


def evidence(namespace: str, name: str, stored: str) -> dict[str, Any]:
    """Everything measurable about one recorded name that no longer resolves.

    Nothing here is a judgement. ``propose`` is where the facts are read.
    """
    key = expand_key(name, stored)
    shape = "class"
    for prefix, label in (
        ("module:", "module"),
        ("union[", "union"),
        ("instance:", "instance"),
        ("value:", "value"),
        ("<", "unresolved-when-recorded"),
    ):
        if key.startswith(prefix):
            shape = label
            break
    recorded_module = recorded_qualname = None
    if shape == "class" and ":" in key:
        recorded_module, recorded_qualname = key.rsplit(":", 1)
        if not recorded_module.startswith("adcp"):
            recorded_module = GENERATED_PREFIX + recorded_module
    elif shape == "class":
        shape = "unkeyed"

    domain = namespace[len(GENERATED_PREFIX) :] if namespace.startswith(GENERATED_PREFIX) else None
    document = document_of(recorded_module) if recorded_module else None
    titles, keys = document_vocabulary(document)
    index = _source_index()
    old_definition = old_definitions().get(f"{recorded_module}|{recorded_qualname}")

    try:
        module_exists = recorded_module is not None and (
            importlib.util.find_spec(recorded_module) is not None
        )
    except Exception:
        module_exists = False

    return {
        "namespace": namespace,
        "name": name,
        "stored": stored,
        "shape": shape,
        "recorded_module": recorded_module,
        "recorded_qualname": recorded_qualname,
        "recorded_module_exists": module_exists,
        "document": document,
        "document_in_bundle": bool(document and (BUNDLE / document).exists()),
        # The snapshot recorded a word whose class had a different name, so the
        # entry was already an ALIAS when it was taken.
        "was_alias": bool(recorded_qualname and recorded_qualname != name),
        "namespace_exists": _module(namespace) is not None,
        "internal_namespace": any(part.startswith("_") for part in namespace.split(".")),
        "numbered": bool(re.search(r"\d+$", name)),
        "word_defined_in_src": sorted(index.get(name, ())),
        "target_defined_in_src": sorted(index.get(recorded_qualname, ()))
        if recorded_qualname
        else [],
        "at_recorded_path": bool(recorded_module and resolves(recorded_module, name)),
        "at_domain_surface": bool(domain and resolves(f"adcp.types.{domain}", name)),
        # Every supported path the word still answers at, the recording namespace
        # excluded -- it is the one that just said no.
        "resolves_at": [
            path
            for path in where_it_resolves(name, sorted(index.get(name, ())))
            + ([recorded_module] if recorded_module and resolves(recorded_module, name) else [])
            if path != namespace
        ],
        "word_from_title": name in titles,
        "word_from_key": name in keys,
        # Where the snapshot entry was already an alias, the word is OUR
        # disambiguating spelling and the generator's node name is the TARGET --
        # so the document's own vocabulary is asked about the target.
        "target_from_title": bool(recorded_qualname) and recorded_qualname in titles,
        "target_from_key": bool(recorded_qualname) and recorded_qualname in keys,
        "recorded_definition": old_definition,
        "recorded_definition_lowered": bool(
            old_definition
            and old_definition[0] == "class"
            and any(base in old_definition[1] for base in _LOWERED_BASES)
        ),
    }


# --------------------------------------------------------------------------- #
# The ladder
# --------------------------------------------------------------------------- #

#: An ORDERED ladder, first match wins, each rung a predicate over
#: :func:`evidence` and a kind. It PROPOSES; it does not declare. The order is
#: "say the strongest true thing": a word that still resolves somewhere is
#: relocated whatever else is true of it, and only then do the artefact rules run.
LADDER: tuple[tuple[str, str, Any], ...] = (
    (
        "namespace-retired",
        "the recording namespace no longer exists in the live tree",
        lambda e: not e["namespace_exists"],
    ),
    (
        "relocated",
        "the identical word resolves at another supported public path today",
        lambda e: bool(e["resolves_at"]),
    ),
    (
        "composed-annotation",
        "the recorded resolution was a union or other typing construct, never a class",
        lambda e: e["shape"] in ("union", "instance", "value", "module", "unkeyed"),
    ),
    (
        "never-a-documents",
        "the recorded module is hand-written: no bundle document behind the word",
        lambda e: e["document"] is None,
    ),
    (
        "retired-document",
        "the document the class was compiled from is no longer in the bundle",
        lambda e: not e["document_in_bundle"],
    ),
    (
        "generator-numbered",
        "the word carries a positional numeric suffix and the document is still emitted",
        lambda e: e["numbered"],
    ),
    (
        "enum-or-scalar-lowered",
        "the recorded definition was an anonymous enum or constrained scalar the "
        "compiler now lowers to an annotation",
        lambda e: e["recorded_definition_lowered"],
    ),
    (
        "renamed",
        "the subject is in the tree under a different word, and nothing binds this one",
        lambda e: bool(e["target_defined_in_src"]) and not e["word_defined_in_src"],
    ),
    (
        "unadvertised",
        "a class of this exact name is in the tree and no namespace exports it",
        lambda e: bool(e["word_defined_in_src"]),
    ),
    (
        "lowered-not-a-subject",
        "the word is pascal_case of a key the still-emitted document (or one it "
        "references) states, and no class in the tree carries it",
        lambda e: (
            (e["word_from_key"] and not e["word_from_title"])
            or (e["was_alias"] and e["target_from_key"] and not e["target_from_title"])
        ),
    ),
    (
        "title-no-longer-a-class",
        "the word is pascal_case of a TITLE the still-emitted document states, "
        "and no class in the tree carries it",
        lambda e: e["word_from_title"] or (e["was_alias"] and e["target_from_title"]),
    ),
)


def propose(ev: dict[str, Any]) -> tuple[str, str]:
    """The first rung whose predicate holds, or ``("unclassified", ...)``.

    An unclassified name is RED and stays RED. A declaration written to silence a
    name nobody understood reads as a decision later, which is worse than the gap
    it closed -- ``CLAUDE.md``'s opening rule is this hazard from the other side.
    """
    for kind, rule, predicate in LADDER:
        if predicate(ev):
            return kind, rule
    return "unclassified", "no rung of the ladder holds; this is the owner's to rule on"


def walk(snapshot: dict[str, dict[str, Any]] | None = None) -> Iterator[dict[str, Any]]:
    """Every recorded name that does not resolve, with its evidence and proposal."""
    snapshot = snapshot if snapshot is not None else load_snapshot()
    for namespace, entry in snapshot.items():
        for name, stored in entry["resolves"].items():
            if resolves(namespace, name):
                continue
            ev = evidence(namespace, name, stored)
            ev["kind"], ev["rule"] = propose(ev)
            yield ev


def unaccounted(
    snapshot: dict[str, dict[str, Any]] | None = None,
    declarations: dict[str, Any] | None = None,
) -> list[tuple[str, str]]:
    """``(namespace, name)`` for every recorded name that neither resolves nor is declared."""
    snapshot = snapshot if snapshot is not None else load_snapshot()
    declared = declared_names(declarations if declarations is not None else load_declarations())
    return [key for key, ok in sorted(sweep(snapshot).items()) if not ok and key not in declared]


#: The declaration kind each ladder rung proposes, and the per-cluster reason.
#: The kind words are the house vocabulary already in use by
#: ``adcp.types._adapter.__adcp_refused__`` -- ``NO-DOCUMENT-NO-SUBJECT``,
#: ``DOCUMENT-NO-WORD-NO-IDENTITY`` -- rather than a second set meaning the same
#: things. ``RENAMED-NOT-YET-BOUND`` is new and says in the word that the hole is
#: open: the subject is there, nothing binds the published spelling.
PROPOSED_KIND: dict[str, str] = {
    "namespace-retired": "NAMESPACE-RETIRED",
    "relocated": "SAME-WORD-NEW-PATH",
    "generator-numbered": "POSITIONAL-INDEX-NOT-A-NAME",
    "enum-or-scalar-lowered": "DOCUMENT-NO-WORD-NO-IDENTITY",
    "lowered-not-a-subject": "DOCUMENT-NO-WORD-NO-IDENTITY",
    "composed-annotation": "NO-DOCUMENT-NO-SUBJECT",
    "renamed": "RENAMED-NOT-YET-BOUND",
    "retired-document": "RETIRED-DOCUMENT",
    "never-a-documents": "NO-DOCUMENT-NO-SUBJECT",
}


def _main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unaccounted", action="store_true", help="list undeclared names only")
    parser.add_argument("--json", type=Path, help="write the full evidence table here")
    parser.add_argument(
        "--propose",
        type=Path,
        help="write proposed clusters for every UNACCOUNTED name here, for review. "
        "The gate never reads this; a human moves reviewed rows into the "
        "declarations file, which is what freezes them.",
    )
    args = parser.parse_args()

    snapshot = load_snapshot()
    if args.unaccounted:
        for namespace, name in unaccounted(snapshot):
            print(f"{namespace}.{name}")
        return
    if args.propose:
        open_names = set(unaccounted(snapshot))
        clusters: dict[str, dict[str, Any]] = {}
        for row in walk(snapshot):
            if (row["namespace"], row["name"]) not in open_names:
                continue
            kind = PROPOSED_KIND.get(row["kind"])
            if kind is None:
                clusters.setdefault("UNCLASSIFIED", {"names": {}})["names"].setdefault(
                    row["namespace"], []
                ).append(row["name"])
                continue
            cluster = clusters.setdefault(
                row["kind"],
                {"id": row["kind"], "kind": kind, "rule": row["rule"], "names": {}},
            )
            cluster["names"].setdefault(row["namespace"], []).append(row["name"])
        for cluster in clusters.values():
            cluster["names"] = {
                namespace: sorted(names) for namespace, names in sorted(cluster["names"].items())
            }
        args.propose.parent.mkdir(parents=True, exist_ok=True)
        args.propose.write_text(json.dumps(clusters, indent=2, sort_keys=True) + "\n")
        print(
            f"Wrote {args.propose}: {len(clusters)} proposed clusters over {len(open_names)} names"
        )
        return

    rows = list(walk(snapshot))
    total = sum(len(entry["resolves"]) for entry in snapshot.values())
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n")

    print(f"{len(snapshot)} namespaces, {total} recorded names, {total - len(rows)} resolve")
    print(f"{len(rows)} do not resolve\n")
    counts: dict[tuple[str, bool], int] = {}
    for row in rows:
        counts[(row["kind"], row["internal_namespace"])] = (
            counts.get((row["kind"], row["internal_namespace"]), 0) + 1
        )
    print(f"{'kind':26s} {'public':>8s} {'internal':>9s} {'total':>7s}")
    for kind, _rule, _predicate in (*LADDER, ("unclassified", "", None)):
        public = counts.get((kind, False), 0)
        internal = counts.get((kind, True), 0)
        if public or internal:
            print(f"{kind:26s} {public:8d} {internal:9d} {public + internal:7d}")


if __name__ == "__main__":
    _main()
