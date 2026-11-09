"""Map upstream's classes onto ours by STRUCTURE, and record what structure cannot decide.

**THE KEY IS A SCHEMA AND NEVER A WORD.**  `docs/plan/final-state.md` reading 10: "AN ALIAS
IS KEYED ON A SCHEMA SUBJECT, NEVER ON A NAME.  The key is identity."  Every earlier
instrument in this directory proposed its candidate from a WORD and then asked a one-bit
identity question of it -- `survey/alias_surface.py`'s own docstring says so -- and the two
consequences are both measured there: a word key cannot see a subject whose two sides spell
it differently, and a one-bit identity (the field set, or the enum's value list) is shared by
every other model with that one field, so run as the sole key it bound upstream's `Brand` to
our `GetAdCPCapabilitiesResponse`.

This instrument replaces both halves with ONE key: the class's own resolved JSON schema.

**WHY `model_json_schema()` AND NOT A STUB.**  `mypy`'s `stubgen` emits the annotation AS
WRITTEN -- `list[CreativesItem] | None`, whose words are the very thing being compared, and
whose optionality and wire alias are elsewhere in the class body.  `model_json_schema()`
emits the RESOLVED structure: the wire names (`by_alias=True`), the optionality, the
defaults, the discriminators and the constraint keywords, as canonical JSON.  "Same subject"
then becomes EQUALITY OF A STRUCTURE rather than an argument about two class definitions,
which is the one thing reading 10 forbids deciding by eye ("neither verdict may be reached by
reading two class definitions side by side").

**STUBGEN'S JOB IS WHAT IS GENUINELY NOT A MODEL**: an enum answers its value list, which is
reading 10's own identity for an enum; a type alias, a `Literal` and an `Annotated` answer
the schema `pydantic.TypeAdapter` resolves for them, which is the same canonical form a model
gives; and a function, a module or a constant answers NOTHING and is reported as such rather
than given a signature it has no subject behind.

THE FOUR-WAY DECOMPOSITION, which is the whole point:

    1:1   one of theirs, one of ours, schemas EQUAL.  Same subject, different word.  A
          MECHANICAL alias and no judgment at all.
    N:1   several of theirs onto one declaration of ours.  Reading 10 still requires each
          such target to be decided by reading the bundle -- "whether it REFERENCES one node
          from the others or RESTATES it, and never by the agreement that found it" -- but
          the set to read is now SMALL and NAMED instead of a bucket to guess at.
    1:N   one of theirs onto several declarations of OURS.  **THIS IS OUR DUPLICATION** and a
          reading 4 red, found by construction rather than by hand.
    none  no structural match: the JUDGMENT TABLE.  Reading 10 as amended: "a differing
          identity is not yet a different subject, and the document says which" -- so each
          row says PER ELEMENT what differs and whether the document accounts for it.  Never
          a ratio: "a count of agreements over a denominator would let a majority decide a
          split".

**COUNTED BY DECLARATION, NEVER BY NAME AND NEVER BY `id()`.**  §1 (2026-11-03): "a gate on
this counts DECLARATIONS, not `id()` and not names.  Three readings were available and the
middle one is right", and `tests/test_the_domain_surface.declaring` is that middle one.  Its
first arm is used here unchanged -- a class carries its declaring position in `__module__`
and `__qualname__`, so a re-export and the class collapse onto one key with nothing told to
this script -- and its third arm, "anything else is its own declaration at its own
module-level statement", is the key for a non-class.  Its SECOND arm needs the run's own
`emit.Emitted.binds`, which no interpreter holding only an installed wheel has; the count of
rows that reach it is reported rather than assumed away (`binding_keyed`).
`bd memories a-name-count-is-not-an-object-count` is why this paragraph exists: three false
findings in one session, all of them a name count read as an object count.

**EVERY NORMALISATION IS A CLAIM THAT TWO THINGS ARE THE SAME, SO EACH ONE CARRIES ITS
REASON** -- :data:`NORMALISATIONS`, printed with every run and recorded in the dump.  A
normalisation nobody can see is an equality nobody can check.

    # one interpreter per tree, because installing both wheels interleaves `adcp/` at file
    # granularity and `pip check` calls the wreckage compatible
    $UP/bin/python   survey/structural_signature.py --dump $T/up.sig.json  --side upstream
    $OURS/bin/python survey/structural_signature.py --dump $T/our.sig.json --side ours

    # the join, on any interpreter: standard library only
    ./.venv/bin/python survey/structural_signature.py --join \
        --ours $T/our.sig.json --theirs $T/up.sig.json \
        --report $T/structural.json --judgment survey/judgment-9.6.1.tsv \
        --mechanical survey/mechanical-9.6.1.tsv
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

#: Every normalisation applied before two schemas are compared, with the reason it is not a
#: loss.  **A NORMALISATION IS A CLAIM THAT TWO THINGS ARE THE SAME**, so this table is part
#: of the result and not part of the implementation: it is written into both dumps and into
#: the report, and a reader who disagrees with one of these reasons knows exactly which rows
#: to distrust.
NORMALISATIONS = {
    "$defs relabelled by a structural fixpoint hash": (
        "a `$ref` names the other side's CLASS WORD -- `#/$defs/CreativesItem` against "
        "`#/$defs/Creative` -- and the word is the thing structure is replacing, so with the "
        "refs left alone NO two sides could ever compare equal however identical the "
        "subjects.  Each `$defs` entry is relabelled with the hash of its own content, "
        "iterated to a fixpoint so a ref inside a def is relabelled too; a RECURSIVE def "
        "reaches its fixpoint like any other and needs no cycle marker, which is why this is "
        "done instead of inlining"
    ),
    "`title` removed at every node": (
        "pydantic derives `title` from the CLASS NAME and from the field name, so a title is "
        "a restatement of the word under comparison.  Keeping it would make the key a word "
        "key wearing a schema's clothes"
    ),
    "`description` removed at every node": (
        "a description is prose the document states and not a type; both sides compile it "
        "from one bundle but neither promises the same whitespace, and reading 1 is about "
        "what the wire carries"
    ),
    "`examples` removed at every node": (
        "an example is a value, not a constraint on values -- a node with and without one "
        "admits exactly the same set"
    ),
    "`enum` and `const` value lists sorted": (
        "reading 10's identity for an enumeration is 'the enum's VALUE LIST' read as a set: "
        "`Recovery` admits the same three values whichever order the document lists them in, "
        "and a reordering is not a different subject"
    ),
    "`anyOf` / `oneOf` / `allOf` branch lists sorted by their canonical form": (
        "upstream's own branch NUMBERING is not document order -- measured on "
        "`build-creative-response.json`, whose six titled branches map 1->0, 2->4, 3->1, "
        "4->2, 5->3, 6->5 -- so branch position is the generator's artifact and the SET of "
        "branches is the subject"
    ),
    "`required` sorted": "a required list is a set; JSON gives no other way to spell one",
    "`ge`/`le`/`gt`/`lt` folded onto `minimum`/`maximum`/`exclusiveMinimum`/`exclusiveMaximum`": (
        "**TWO SPELLINGS OF ONE BOUND, and it is the largest single cause of inequality "
        "between the two generators**: measured over the 2,007 same-document residue, `ge` "
        "appears on upstream's side alone 585 times and `minimum` on ours alone 225 times, at "
        "the same nodes.  `ge` is pydantic's `Field(ge=...)` surfacing in the schema where "
        "ours emits JSON Schema's own keyword; the admissible set is identical and the "
        "difference is which library wrote the node"
    ),
    "numeric bounds compared by VALUE, not by JSON number type": (
        "`minimum: 0` and `minimum: 0.0` are one bound, and `minimum [kind]` -- an int on one "
        "side against a float on the other -- was 316 of the same residue.  The document "
        "states a number, not a Python type"
    ),
    "`deprecated` removed at every node": (
        "a deprecation is advisory and changes no admissible value: a node with and without "
        "it accepts exactly the same wire values, which is the same reason `title` and "
        "`description` go.  253 of the residue, almost all of them upstream's generator "
        "marking `adcp_major_version` on every inner node it touches"
    ),
    "object keys sorted (canonical JSON)": (
        "JSON object key order carries no meaning, and two dicts differing only in it are "
        "one dict"
    ),
}

#: What is NOT normalised away, listed because an omission from the table above would read as
#: an oversight: `default`, `required`, `additionalProperties`, every constraint keyword
#: (`pattern`, `minimum`, `minLength`, `format`), `discriminator`, `deprecated`, `type`,
#: `items`, `properties` and their wire names.  Those are the wire facts reading 1 is about,
#: and a key that dropped one of them would call two different subjects the same.
KEPT = (
    "default",
    "required",
    "additionalProperties",
    "pattern",
    "minimum",
    "maximum",
    "minLength",
    "maxLength",
    "minItems",
    "maxItems",
    "format",
    "discriminator",
    "deprecated",
    "type",
    "items",
    "properties",
    "prefixItems",
    "uniqueItems",
    "multipleOf",
    "exclusiveMinimum",
    "exclusiveMaximum",
    "const",
)

#: Keys dropped at every node.  Each one has its row in :data:`NORMALISATIONS`.
DROPPED = ("title", "description", "examples", "deprecated")

#: pydantic's own spelling of four JSON Schema bounds -> the keyword the bundle states.
BOUND_SPELLINGS = {
    "ge": "minimum",
    "le": "maximum",
    "gt": "exclusiveMinimum",
    "lt": "exclusiveMaximum",
}

#: The keywords whose value is a NUMBER and is compared as one.
NUMERIC = ("minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf")

#: The two normalisations that are NOT applied by default, with what each one COSTS.
#:
#: **MEASURED, AND THIS TABLE EXISTS BECAUSE THE STRICT KEY'S JUDGMENT TABLE WAS 3,844 ROWS.**
#: The diagnosis was run against 760 pairs ALREADY PROVED to be one subject by two independent
#: keys -- upstream's word and reading 10's identity, `PRESENT` and `RELOCATED` with
#: `corroborated=identity` in `survey/alias-surface-9.6.1.tsv` -- and the strict key called only
#: 202 of those 760 equal.  A key that disagrees with two agreeing keys on 558 pairs is too
#: strict, and the three causes were read off the diffs rather than guessed:
#:
#: * `AcceptProposalWorking.context`: ours `{"anyOf":[{"type":"object",...},{"type":"null"}],
#:   "default":null}`, theirs `{"$ref":...,"default":null}` -- the same node, with a `null` arm
#:   on one side only;
#: * `AccountSetupRequiredDetails.setup_steps`: ours `{"anyOf":[{array of string},{"type":
#:   "null"}],"default":null}`, theirs `{array of string,"default":null}` -- identical but for
#:   that arm;
#: * `AgentEncryptionKey.crv`: ours `{"const":"X25519","type":"string"}`, theirs the same with
#:   `"default":"X25519"` restated.
#:
#: So each is offered as a SWITCH with its cost stated, and both settings are measured and
#: reported, because "the key is too strict" and "the key is unsound" are the two failures and
#: a single setting cannot be checked against both.
RELAXATIONS = {
    "null-arm": (
        "a `{\"type\":\"null\"}` arm is dropped from an `anyOf` whose node also carries "
        "`default: null`, and the `anyOf` is unwrapped where one arm remains.  **COST: it "
        "stops distinguishing a field that admits an explicit JSON `null` from one that may "
        "only be ABSENT.**  Both sides default the field to null, so an omitted field reads "
        "identically on both and the difference is confined to whether a caller may SEND "
        "`null` -- a real admissibility difference, and the narrower reading is upstream's.  "
        "This is the single largest cause and the one whose cost is highest, which is why it "
        "is a switch and not a normalisation"
    ),
    "const-default": (
        "a `default` equal to the node's own `const` is dropped.  **COST: none that can be "
        "named.**  A `const` node admits exactly one value, so a default equal to it changes "
        "no admissible set and no wire fact -- it is their generator restating the constraint "
        "as a default"
    ),
    "inline-refs": (
        "a `$ref` to a non-recursive def is replaced by that def's own content, so a node "
        "stated INLINE on one side and behind a `$ref` on the other compares equal.  **COST: "
        "the signature grows with the sharing, so it is capped** "
        f"({'see INLINE_CAP'}) and a ref left uninlined is counted rather than hidden.  No "
        "soundness cost: inlining preserves the admissible set exactly, which is the whole "
        "reason a `$ref` is a reference"
    ),
}

#: The largest canonical form an inlined def may reach before the `$ref` is left in place.
#: A bound and not a tuning knob: `core/creative-representation-set.json` is the document that
#: has already cost this project a parked suite through an unbounded structural walk
#: (`adcp-client-python-5pb`), and an exponent is not removed by a cache.
INLINE_CAP = 200_000

#: Which of :data:`RELAXATIONS` this process is applying.  **A MODULE-LEVEL SWITCH AND NOT AN
#: ARGUMENT THREADED THROUGH THE WALK**, because the signature is computed once per object by
#: a recursion five functions deep and a parameter at every level would be five places the
#: setting could disagree with itself.  Set by :func:`main` from the command line, written into
#: the dump beside the signatures it produced, and asserted equal on both sides by the join --
#: two dumps taken at different settings are not comparable and the join refuses them.
RELAX = dict.fromkeys(RELAXATIONS, False)


# --------------------------------------------------------------------------- the signature


def _strip(node: object) -> object:
    """One node with :data:`DROPPED` gone and every set-valued list sorted.

    Recursive, and it never looks at a `$ref`'s target: relabelling is :func:`_relabel`'s
    job and keeping the two apart is what lets the fixpoint below iterate.
    """
    if isinstance(node, dict):
        out = {
            BOUND_SPELLINGS.get(k, k): _strip(v)
            for k, v in node.items()
            if k not in DROPPED
        }
        for key in NUMERIC:
            if isinstance(out.get(key), (int, float)) and not isinstance(out[key], bool):
                out[key] = float(out[key])
        for key in ("enum", "required"):
            if isinstance(out.get(key), list):
                out[key] = sorted(out[key], key=_canon)
        for key in ("anyOf", "oneOf", "allOf"):
            if isinstance(out.get(key), list):
                out[key] = sorted(out[key], key=_canon)
        if RELAX["const-default"] and "const" in out and out.get("default") == out["const"]:
            out.pop("default")
        if RELAX["null-arm"] and out.get("default", ...) is None:
            arms = out.get("anyOf")
            if isinstance(arms, list) and {"type": "null"} in arms:
                rest = [a for a in arms if a != {"type": "null"}]
                if len(rest) == 1 and isinstance(rest[0], dict):
                    out.pop("anyOf")
                    out = {**rest[0], **out}
                else:
                    out["anyOf"] = rest
        return out
    if isinstance(node, list):
        return [_strip(v) for v in node]
    return node


def _canon(node: object) -> str:
    """Canonical JSON: sorted keys, no whitespace.  The one spelling two sides compare on."""
    return json.dumps(node, sort_keys=True, separators=(",", ":"), default=str)


def _digest(node: object) -> str:
    return hashlib.sha256(_canon(node).encode()).hexdigest()[:16]


def _relabel(node: object, labels: dict[str, str]) -> object:
    """Every `#/$defs/<word>` rewritten to `#/d/<structural hash>`.

    A ref whose target is not in `labels` is left verbatim and shows up in the signature as
    itself, which is the honest outcome: an unresolvable ref is a fact about the schema and
    not something to normalise away.
    """
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/$defs/"):
            word = ref[len("#/$defs/") :]
            if word in labels:
                return {**{k: _relabel(v, labels) for k, v in node.items()}, "$ref": f"#/d/{labels[word]}"}
        return {k: _relabel(v, labels) for k, v in node.items()}
    if isinstance(node, list):
        return [_relabel(v, labels) for v in node]
    return node


def normalise(schema: dict) -> dict:
    """A JSON schema in the one form two trees can be compared in.

    **THE `$defs` FIXPOINT IS THE WHOLE OF THE METHOD AND IT REPLACES INLINING.**  Inlining a
    ref graph is exponential in the sharing and undefined on a cycle, and `core/creative-
    representation-set.json` is the document that has already cost this project a parked
    suite for exactly that shape (`adcp-client-python-5pb`).  Relabelling is linear: each
    `$defs` entry starts at one label, every entry is rehashed with the current labels
    substituted, and the iteration repeats until no label moves.  A recursive def reaches its
    fixpoint like any other -- its own hash appears inside its own body and the pair is
    stable -- so no cycle marker is needed and none is invented.

    The iteration is bounded by the number of defs plus two, and a run that has not converged
    by then records `converged: false` so a reader knows the signature is a snapshot of an
    unfinished fixpoint rather than a canonical form.  Measured over both trees: it converges
    in at most four passes.
    """
    body = {k: v for k, v in schema.items() if k != "$defs"}
    defs = dict(schema.get("$defs") or {})
    stripped = {k: _strip(v) for k, v in defs.items()}
    labels = dict.fromkeys(stripped, "0")
    converged = not stripped
    for _ in range(len(stripped) + 2):
        moved = {k: _digest(_relabel(v, labels)) for k, v in stripped.items()}
        if moved == labels:
            converged = True
            break
        labels = moved
    out = {"root": _relabel(_strip(body), labels)}
    if stripped:
        out["defs"] = {labels[k]: _relabel(v, labels) for k, v in sorted(stripped.items())}
    if not converged:
        out["converged"] = False
    if RELAX["inline-refs"]:
        out = _inline(out)
    return out


def _inline(blob: dict) -> dict:
    """Every `$ref` to a NON-RECURSIVE def replaced by that def's content.

    **THIS IS WHAT MAKES AN INLINE NODE AND A `$ref` TO THE SAME NODE COMPARE EQUAL**, which
    is the second of the three causes measured in :data:`RELAXATIONS`: our walk states a
    one-field object inline where their generator lifts it into `$defs` and points at it.  No
    admissible set changes -- that is what a reference IS -- so the only cost is size, and
    size is bounded by :data:`INLINE_CAP` rather than trusted.

    A def that reaches itself, directly or through others, is left as a `$ref` to its fixpoint
    hash, which is already canonical and already word-free.  So recursion is not approximated
    here: it keeps the key it had.
    """
    defs = blob.get("defs") or {}
    resolved: dict[str, object] = {}

    def expand(node: object, stack: frozenset[str]) -> object:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/d/"):
                label = ref[len("#/d/") :]
                if label in defs and label not in stack:
                    body = resolved.get(label)
                    if body is None:
                        body = expand(defs[label], stack | {label})
                        if len(_canon(body)) <= INLINE_CAP:
                            resolved[label] = body
                        else:
                            return node
                    rest = {k: expand(v, stack) for k, v in node.items() if k != "$ref"}
                    return {**body, **rest} if isinstance(body, dict) else body
                return node
            return {k: expand(v, stack) for k, v in node.items()}
        if isinstance(node, list):
            return [expand(v, stack) for v in node]
        return node

    root = expand(blob["root"], frozenset())
    if len(_canon(root)) > INLINE_CAP:
        return blob
    out: dict = {"root": root}
    if blob.get("converged") is False:
        out["converged"] = False
    return out


def signature(obj: object) -> tuple[str, dict | None, str]:
    """``(method, normalised schema, note)`` for one object of a type surface.

    Four methods and each is reported as itself, because "what the key was read off" is the
    first thing a disagreement about a row turns out to be about:

    * ``model`` -- a pydantic model's ``model_json_schema(by_alias=True)``.  The resolved
      structure: wire names, optionality, defaults, discriminators and constraints.
    * ``enum`` -- the value list, which is reading 10's identity for an enumeration, beside
      the member VALUES' own JSON types so ``"1"`` and ``1`` are not one subject.
    * ``adapter`` -- ``pydantic.TypeAdapter(obj).json_schema()``, for a type alias, an
      ``Annotated``, a ``Literal`` or a bare union.  The same canonical form a model gives,
      which is why a stub's text is not wanted even here.
    * ``none`` -- a function, a module, a constant or an object pydantic cannot resolve.  **No
      signature is invented for it**; it is counted and named, and reading 10 already says
      what it gets: "a name with no schema subject gets a migration note and never a class".
    """
    import enum as enum_module

    if isinstance(obj, type) and issubclass(obj, enum_module.Enum):
        members = [m.value for m in obj]
        return (
            "enum",
            {
                "root": {
                    "enum": sorted(members, key=_canon),
                    "value_types": sorted({type(m).__name__ for m in members}),
                }
            },
            "",
        )
    schema = getattr(obj, "model_json_schema", None)
    if callable(schema) and isinstance(obj, type):
        try:
            return "model", normalise(schema(by_alias=True)), ""
        except BaseException as exc:  # noqa: BLE001 -- the payload is the report
            return "none", None, f"model_json_schema raised {type(exc).__name__}: {exc}"
    try:
        from pydantic import TypeAdapter

        return "adapter", normalise(TypeAdapter(obj).json_schema()), ""
    except BaseException as exc:  # noqa: BLE001 -- the payload is the report
        return "none", None, f"{type(obj).__name__}: {type(exc).__name__}"


# --------------------------------------------------------------------------- phase 1


def dump(out_path: Path, side: str, root: str) -> None:
    """One tree's whole public type surface, keyed by DECLARATION, with its signatures.

    The surface predicates are ``survey/alias_surface.py``'s own -- ``_public_modules`` and
    ``_public_names`` -- and not a second reading of the public-name rule.
    ``bd memories use-the-projects-own-instrument-not-a-fresh-script``: four figures were
    wrong in one session because a one-liner was written where a gate with a considered
    predicate already existed.  The `deliberate` flag those return is reading 10's own and it
    travels on the row, so the join can range over the deliberate surface or over the whole
    one and SAY which.
    """
    import importlib

    import alias_surface

    declarations: dict[str, dict] = {}
    unreadable: dict[str, str] = {}
    binding_keyed = 0
    restates: dict[str, str] = {}
    # **THE SURFACE PREDICATES ARE `alias_surface`'s OWN AND ARE REACHED UNDERSCORED ON
    # PURPOSE**: `_public_modules`, `_public_names` and `_version` are that module's reading of
    # the public-name rule and of which version a figure is against, and a second reading here
    # would be a second place the rule lives.  `bd memories
    # use-the-projects-own-instrument-not-a-fresh-script` is the reason this is a `noqa` and
    # not a copy.
    for mod_name in alias_surface._public_modules(root):  # noqa: SLF001
        try:
            mod = importlib.import_module(mod_name)
        except BaseException as exc:  # noqa: BLE001 -- the payload is the report
            unreadable[mod_name] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:160]}"
            continue
        # **A MODULE THAT SAYS IT RESTATES UPSTREAM IS NOT A SUBJECT OF OURS**, which is the
        # marker's whole purpose: with no such skip this instrument would read
        # `adcp.types.compat` -- the alias layer -- as 1,038 declarations of ours carrying
        # upstream's own words, and every row of the join would be this survey reading its own
        # output.  `survey/alias_surface.py` and `survey/migration_notes.py` both skip it and
        # the rule is declared BY the module rather than listed here, so a second alias module
        # needs nothing edited.
        if (marker := getattr(mod, "__adcp_restates_upstream__", None)) is not None:
            restates[mod_name] = str(marker)
            continue
        names, declared = alias_surface._public_names(mod)  # noqa: SLF001
        for name in names:
            try:
                obj = getattr(mod, name)
            except BaseException as exc:  # noqa: BLE001 -- upstream's __getattr__ raises
                unreadable[f"{mod_name}.{name}"] = f"{type(exc).__name__}: {exc}"
                continue
            # ``declaring``'s FIRST arm for a class and its THIRD for anything else; the
            # second arm needs the run's own ``binds`` record, which an installed wheel does
            # not carry, so the rows that would reach it are counted instead.
            if isinstance(obj, type):
                key = f"{obj.__module__}.{obj.__qualname__}"
            else:
                key = f"{mod_name}.{name}"
                binding_keyed += 1
            row = declarations.get(key)
            if row is None:
                method, schema, note = signature(obj)
                row = declarations[key] = {
                    "names": [],
                    "modules": [],
                    "deliberate": False,
                    "method": method,
                    "note": note,
                    "sig": _digest(schema) if schema is not None else "",
                    "schema": _canon(schema) if schema is not None else "",
                }
            if name not in row["names"]:
                row["names"].append(name)
            if mod_name not in row["modules"]:
                row["modules"].append(mod_name)
            if declared:
                row["deliberate"] = True
    version = alias_surface._version("adcp" if side == "upstream" else "adcp_emit")  # noqa: SLF001
    out_path.write_text(
        json.dumps(
            {
                "side": side,
                "root": root,
                "version": version,
                "tree": importlib.import_module(root).__file__,
                "normalisations": NORMALISATIONS,
                "relaxations": {k: v for k, v in RELAX.items() if v},
                "kept": list(KEPT),
                "binding_keyed": binding_keyed,
                "restates_upstream": restates,
                "unreadable": unreadable,
                "declarations": declarations,
            },
            indent=1,
        )
    )
    kinds = collections.Counter(r["method"] for r in declarations.values())
    print(
        f"{side} {root} {version}: {len(declarations)} DECLARATIONS over "
        f"{sum(len(r['names']) for r in declarations.values())} names, "
        f"{sum(1 for r in declarations.values() if r['deliberate'])} of them deliberate; "
        f"signatures by method {dict(kinds)}; {len(unreadable)} unreadable, "
        f"{len(restates)} skipped as restating upstream -> {out_path}"
    )


# --------------------------------------------------------------------------- phase 2


def _elements(schema: str) -> dict[str, str]:
    """A schema's own root PROPERTIES (or enum members), element by element.

    The judgment table's per-element reading needs the elements, and reading 10 fixes what
    they are: "the field set read by wire alias, or the enum's value list".  A property's
    value is carried beside its name so a row can say the element is PRESENT ON BOTH AND
    DIFFERENT, which is a different finding from absent and gets a different answer.
    """
    try:
        blob = json.loads(schema) if schema else {}
    except ValueError:
        return {}
    root = blob.get("root") or {}
    if isinstance(root.get("enum"), list):
        return {str(v): "" for v in root["enum"]}
    props = root.get("properties")
    if isinstance(props, dict):
        return {k: _canon(v) for k, v in props.items()}
    return {}


def difference(ours_schema: str, theirs_schema: str, cap: int = 4) -> list[str]:
    """The ELEMENTS two schemas disagree on, as `<keyword> <side>` labels and never a count.

    **THIS IS READING 10's PER-ELEMENT READING, MADE MECHANICAL.**  The amendment: "for each
    element of upstream's identity, name where the document states it or state that it does
    not.  A count of agreements over a denominator would let a majority decide a split."  So
    what comes back is a LIST OF ELEMENTS and never a score: `minimum only-theirs`,
    `uniqueItems only-ours`, `required differs`.  No ratio is computed anywhere in this
    module, and the one number a row carries -- the nearest candidate's shared-element count
    -- is offered to a reader and decides nothing.

    The label drops array INDICES from the path, because `/properties/x/items/0/minimum` and
    `/properties/y/items/3/minimum` are one finding about one keyword and two rows would make
    the clustering below count positions instead of findings.
    """
    try:
        mine = (json.loads(ours_schema) if ours_schema else {}).get("root")
        yours = (json.loads(theirs_schema) if theirs_schema else {}).get("root")
    except ValueError:
        return ["unreadable"]
    out: list[str] = []

    def walk(a: object, b: object, path: str, depth: int) -> None:
        if len(out) >= cap or depth > 8:
            return
        if type(a) is not type(b):
            out.append(f"{path.rsplit('/', 1)[-1] or '(root)'} kind-differs")
            return
        if isinstance(a, dict):
            for key in sorted(set(a) | set(b)):
                if key not in a:
                    out.append(f"{key} only-theirs")
                elif key not in b:
                    out.append(f"{key} only-ours")
                else:
                    walk(a[key], b[key], f"{path}/{key}", depth + 1)
        elif isinstance(a, list):
            if len(a) != len(b):
                out.append(f"{path.rsplit('/', 1)[-1] or '(root)'} differs")
            else:
                for x, y in zip(a, b, strict=True):
                    walk(x, y, path, depth + 1)
        elif a != b:
            out.append(f"{path.rsplit('/', 1)[-1] or '(root)'} value-differs")

    walk(mine, yours, "", 0)
    return out[:cap] or ["equal"]


def document_modules(index: dict) -> dict[str, str]:
    """``core.assets.pixel_tracker_asset`` -> ``core/assets/pixel-tracker-asset.json``.

    **THE MIRROR IS DERIVED FROM THE BUNDLE'S OWN FILE LIST AND NEVER RECONSTRUCTED FROM A
    MODULE NAME**, so a module naming no document is a MISS with a reason rather than a guess.
    Our private tree mirrors the document path with `-` spelled `_`, and the direction that
    matters is document -> module: going the other way would have to invent which underscores
    were hyphens.

    Computed here rather than added to ``alias_surface.bundle_index``, because this script is
    the only reader and that one is the older instrument this one is replacing -- a key added
    there for this reader's sake would leave two instruments coupled through a third.
    """
    return {
        document[: -len(".json")].replace("-", "_").replace("/", "."): document
        for document in index["documents"]
    }


def partition(rows: list[dict], our_documents: set[str], index: dict) -> dict[str, list[dict]]:
    """The `none` bucket split three ways, because only one third is a judgment at all.

    **MEASURED, AND THIS SPLIT IS WHY THE JUDGMENT TABLE IS NOT 3,113 ROWS.**  Of upstream's
    3,113 structurally unmatched deliberate declarations on 9.6.1:

    * **1,168 are declared in a module that names NO bundle document** --
      `adcp.types.v31` (159), `adcp.types.versioned_bases.v31` (159), `adcp.types.registry`
      (142), `v30` (141 twice), `canonical_creative` (39), `guards` (31), `aliases` (19).
      Reading 10 has already answered these and it is not a judgment: "A NAME WITH NO SCHEMA
      SUBJECT GETS A MIGRATION NOTE AND NEVER A CLASS.  Where upstream's flat namespace
      carries something no document states -- a hand-written ergonomic, eager, legacy or
      registry layer -- an alias has nothing to point at, and minting a nodeless class to
      satisfy an import is the back door this ordering exists to close."
    * **75 name a bundle document OUR TREE COMPILED NOTHING FROM** -- 18 of them
      `core/localized-creative-asset.json`.  That is a question for the WALK and not for this
      layer: either the document is out of our population or it is a reading 1 gap, and
      either way no alias decides it.
    * **1,870 name a document we DO compile, and differ at depth.**  Those are the judgment,
      and they are what :func:`difference` is pointed at.

    The document is resolved by `migration_notes.document_of`, the project's own predicate,
    and never by a second reading of the module-to-document mirror.
    """
    import migration_notes

    documents = set(index["documents"])
    out: dict[str, list[dict]] = {"no-document": [], "document-not-ours": [], "same-document": []}
    for row in rows:
        document = migration_notes.document_of(row["theirs"].rsplit(".", 1)[0], documents)
        where = (
            "no-document"
            if document is None
            else "document-not-ours"
            if document not in our_documents
            else "same-document"
        )
        out[where].append({**row, "document": document})
    return out


#: **WHAT SIGNATURE IDENTITY IS EVIDENCE OF DEPENDS ON THE KIND, and mixing the kinds into
#: one table is what produced a 196-row "reading 4" bucket out of nothing**
#: (`adcp-client-python-shh0`, re-graded; `adcp-client-python-0kfk`).  The key is the same
#: canonical schema for every kind -- that is not the problem.  The problem is the INFERENCE
#: drawn from two of them being equal, and it is not the same inference.
KIND_EVIDENCE = {
    "model": (
        "STRONG.  A model's canonical schema carries its wire names, its optionality, its "
        "defaults, its discriminators and its constraint keywords.  Two models agreeing on "
        "all of that agree about a structure nobody writes twice by accident, so signature "
        "identity is real evidence of one subject and a 1:N row is a genuine reading 4 "
        "question"
    ),
    "enum": (
        "STRONG.  Reading 10's own identity for an enumeration IS the value list, so two "
        "enums with one signature admit exactly the same values by the reading's own key -- "
        "there is no further fact a document could state that this key drops"
    ),
    "adapter": (
        "NEARLY VACUOUS, and this is the finding.  An `Annotated[str, FieldInfo(...)]` "
        "answers `{\"type\": \"string\"}` plus whatever bounds it states, and `description` "
        "is removed at every node -- correctly, since a description is not a constraint.  So "
        "EVERY unbounded constrained string matches every other one.  Upstream's "
        "`CanonicalFormatKindStr` reaches seven declarations of ours -- `AxeExcludeSegment`, "
        "`AxeIncludeSegment`, `Category`, `HoursValue`, `MediaBuyTermsReference`, `Query` -- "
        "which are seven UNRELATED SUBJECTS differing only in the prose each document states. "
        "A 1:N row here means THE KEY COULD NOT DECIDE THE TARGET and never that we declared "
        "one subject twice.  `test_the_domain_surface.declaring`'s own docstring already said "
        "so: 'where several documents each state the same constrained scalar, the walk emits "
        "an independent alias statement in each ... a gate keyed on object identity reports "
        "those as a violation with NO AVAILABLE REPAIR'"
    ),
}


def by_kind(ours: dict, theirs: dict, *, deliberate_only: bool) -> dict[str, dict]:
    """The four buckets computed ONCE PER KIND, because one table cannot be read.

    **A BUCKET COUNT OVER THE MIXED POPULATION IS NOT A FINDING ABOUT EITHER KIND.**  Each
    kind is joined against ITS OWN side of the other population, so a row's bucket is decided
    only against declarations whose signature means the same sort of thing -- and the figure
    `0kfk` asks to be isolated, the MODEL-CLASS 1:N count, is this function's `model` entry.

    Restricting the population is not a normalisation and costs nothing: a model's canonical
    schema is an object and an `adapter`'s is a scalar, so a cross-kind signature equality is
    possible but rare, and the mixed join above still reports it.  What changes is the
    DENOMINATOR each row is decided against, which is the whole point.
    """
    out: dict[str, dict] = {}
    for kind in sorted(KIND_EVIDENCE):
        def only(blob: dict, kind: str = kind) -> dict:
            return {
                **blob,
                "declarations": {
                    key: row
                    for key, row in blob["declarations"].items()
                    if row["method"] == kind
                },
            }

        inner = join(only(ours), only(theirs), deliberate_only=deliberate_only)
        out[kind] = {
            "evidence": KIND_EVIDENCE[kind],
            "ours_declarations": inner["ours_declarations"],
            "theirs_declarations": inner["theirs_declarations"],
            "buckets": inner["buckets"],
            "our_own_collisions": len(inner["our_own_collisions"]),
            "one_to_n": [
                {"theirs": row["theirs"], "names": row["names"], "ours": row["ours"]}
                for row in inner["rows"]["1:N"]
            ],
        }
    return out


def resolve_by_document(report: dict, ours: dict, theirs: dict, index: dict) -> dict:
    """The 1:N rows decided by the DOCUMENT NODE, which this key drops by design.

    **THE SIGNATURE DROPS PROVENANCE ON PURPOSE AND UPSTREAM'S CLASS CARRIES IT.**  Their
    generator derives the module path from the document path, so
    `adcp.types.domains.core.account_ref.AccountReference1` names `core/account-ref.json`
    whatever the structure of the class is; our private tree mirrors the same document path.
    So where the key could not decide between several declarations of ours, the DOCUMENT can
    -- and that is `adcp-client-python-1hck`'s approved rule ("the key is the document node
    and never a word") applied as a SECONDARY key rather than as a replacement.

    **IT IS A TIE-BREAK AND NEVER A PROPOSAL.**  The candidates are exactly the declarations
    the signature already matched, so nothing is admitted that structure did not admit; the
    document only chooses among them.  A row whose candidates all name a different document
    than theirs is reported as `document-disagrees` and NOT resolved -- the structural match
    stands and the provenance does not corroborate it, which is a row for a reader.

    Both sides' document is read off the defining module through
    `migration_notes.document_of` (theirs, which resolves `bundled/` and `mcp/` projections to
    the canonical document they project) and through :func:`document_modules` (ours, which is
    the bundle's own file list and never a reconstruction).  A name upstream declares OUTSIDE
    its generated tree -- `adcp.types.CanonicalFormatKindStr`, `adcp.types.registry.*` --
    names no document at its defining module, so there is no secondary key for it and it is
    reported as `theirs-nameless`.
    """
    import migration_notes

    documents = set(index["documents"])
    mirror = document_modules(index)

    def our_document(key: str) -> str | None:
        return mirror.get(key.rsplit(".", 1)[0].removeprefix("adcp.types._schemas."))

    out: dict[str, list[dict]] = {
        "collapsed": [],
        "theirs-nameless": [],
        "document-disagrees": [],
        "still-several": [],
    }
    for row in report["rows"]["1:N"]:
        theirs_at = row["theirs"]
        document = migration_notes.document_of(theirs_at.rsplit(".", 1)[0], documents)
        agree = [key for key in row["ours"] if our_document(key) == document]
        entry = {
            "theirs": theirs_at,
            "names": row["names"],
            "method": row["method"],
            "document": document,
            "candidates": row["ours"],
            "ours_documents": [our_document(key) for key in row["ours"]],
            "agree": agree,
        }
        if document is None:
            out["theirs-nameless"].append(entry)
        elif len(agree) == 1:
            out["collapsed"].append(entry)
        elif not agree:
            out["document-disagrees"].append(entry)
        else:
            out["still-several"].append(entry)
    return out


def join(ours: dict, theirs: dict, *, deliberate_only: bool) -> dict:
    """The four-way decomposition, and the judgment table is what it leaves behind.

    **THE BUCKETS PARTITION THEIRS, WHICH IS THE ONE DIRECTION READING 10 ASKS.**  "Every
    name upstream's wheel exposes gets a verdict; the reverse is not asked.  A smaller count
    on our side is the expected outcome and not a deficit."  So 1:1, N:1 and `none` are
    counted over THEIR declarations and sum to their population; 1:N is counted over theirs
    too and reported with the declarations of OURS it names, because that is the row a
    reading 4 repair is made against.

    **AND OUR OWN SIGNATURE COLLISIONS ARE REPORTED BESIDE THE JOIN, because they are a
    reading 4 finding that does not need upstream at all.**  Two declarations of ours with one
    signature are two classes for one subject whether or not any name of theirs reaches them,
    and the 1:N bucket is only the subset upstream happens to point at.
    """
    def population(blob: dict) -> dict[str, dict]:
        return {
            k: r
            for k, r in blob["declarations"].items()
            if (r["deliberate"] or not deliberate_only) and r["sig"]
        }

    mine, yours = population(ours), population(theirs)
    by_sig_ours: dict[str, list[str]] = collections.defaultdict(list)
    for key, row in sorted(mine.items()):
        by_sig_ours[row["sig"]].append(key)
    by_sig_theirs: dict[str, list[str]] = collections.defaultdict(list)
    for key, row in sorted(yours.items()):
        by_sig_theirs[row["sig"]].append(key)

    buckets: dict[str, list[dict]] = {"1:1": [], "N:1": [], "1:N": [], "none": []}
    for key, row in sorted(yours.items()):
        hits = by_sig_ours.get(row["sig"], [])
        if not hits:
            buckets["none"].append({"theirs": key, "names": row["names"], "method": row["method"]})
            continue
        entry = {
            "theirs": key,
            "names": row["names"],
            "method": row["method"],
            "ours": hits,
            "sharing": len(by_sig_theirs[row["sig"]]),
        }
        if len(hits) > 1:
            buckets["1:N"].append(entry)
        elif entry["sharing"] > 1:
            buckets["N:1"].append(entry)
        else:
            buckets["1:1"].append(entry)
    return {
        "ours_declarations": len(mine),
        "theirs_declarations": len(yours),
        "ours_signatures": len(by_sig_ours),
        "theirs_signatures": len(by_sig_theirs),
        "buckets": {k: len(v) for k, v in buckets.items()},
        "our_own_collisions": {
            sig: keys for sig, keys in sorted(by_sig_ours.items()) if len(keys) > 1
        },
        "rows": buckets,
    }


def write_mechanical(path: Path, report: dict, theirs: dict, ours: dict) -> None:
    """The 1:1 rows: upstream's name, the declaration of ours, and that the schemas are EQUAL.

    **MECHANICAL MEANS NO JUDGMENT WAS EXERCISED, which is a property of the row and not a
    promise about it.**  One of theirs, one of ours, one signature: the alias follows with
    nothing decided, and that is the whole content of this file.  A reader who wants to check
    a row re-derives the signature; a reader who disagrees with a row disagrees with a
    normalisation, which is why :data:`NORMALISATIONS` is in the header.
    """
    lines = [
        (f"# Mechanical 1:1 structural matches, upstream adcp {theirs['version']} against "
        f"adcp_emit {ours['version']}.\n"),
        (f"# {report['theirs_declarations']} declarations of theirs against "
        f"{report['ours_declarations']} of ours, by DECLARATION and never by name or id().\n"),
        "# Normalisations applied: " + "; ".join(sorted(NORMALISATIONS)) + "\n",
        "upstream_names\ttheirs_declared_at\tours_declared_at\tsignature\tmethod\n",
    ]
    lines += [
        f"{' '.join(sorted(row['names']))}\t{row['theirs']}\t{row['ours'][0]}\t"
        f"{theirs['declarations'][row['theirs']]['sig']}\t{row['method']}\n"
        for row in report["rows"]["1:1"]
    ]
    path.write_text("".join(lines))
    print(f"{len(report['rows']['1:1'])} mechanical rows -> {path}")


def write_judgment(
    path: Path, classes_path: Path | None, report: dict, theirs: dict, ours: dict, index: dict
) -> None:
    """The rows structure could not decide -- and the DIFFERENCE CLASSES they fall into.

    **THE CLASS TABLE IS THE ARTIFACT A HUMAN READS, AND THE ROW TABLE IS WHAT IT ACCOUNTS
    FOR.**  Measured on 9.6.1 the row table is in the thousands, and a brief asking for "the
    judgment table's row count" deserves the reason that number is not the size of the
    decision: **the per-element differences CLUSTER, because one habit of upstream's
    generator produces hundreds of rows.**  `ge` against `minimum` was 585 rows and ONE
    finding; `deprecated` on every inner node was 253 rows and one finding; both are now
    normalisations with their reason in :data:`NORMALISATIONS`.  What remains clusters the
    same way -- `uniqueItems only-ours` 451, `maxLength only-ours` 269, `required differs`
    255 -- and each cluster is one statement about the two generators, not 451 of them.

    So the class table carries ONE ROW PER DIFFERENCE CLASS with the declarations it covers,
    and the row table carries one row per declaration naming its class.  Nothing is hidden by
    the grouping: the two row counts are reported side by side and the second is the first's
    expansion.

    **AND READING 10's "NEVER BY A RATIO" IS WHY THE CLASS IS A LIST OF ELEMENTS.**  A class
    is the sorted sequence of `<keyword> <side>` labels :func:`difference` returns -- the
    elements themselves -- so ruling on a class is ruling on "does the document account for
    `uniqueItems` being ours alone", which is a per-element question.  It is never "do 80% of
    the elements agree", which the amendment forbids: "a count of agreements over a
    denominator would let a majority decide a split".

    Four kinds of row, and they are four different questions:

    * ``N:1`` -- reading 10's many-to-one, "a HYPOTHESIS, not a verdict", decided by reading
      the bundle for REFERENCE vs RESTATEMENT.  The row names every sibling sharing the
      target, which is what that reading is made over.
    * ``1:N`` -- **THE KEY COULD NOT DECIDE THE TARGET.**  This header asserted "OUR
      duplication, a reading 4 red" and that was MEASURED FALSE for the bucket's dominant
      case: see :data:`KIND_EVIDENCE` for the seven unrelated constrained scalars one
      signature of upstream's reaches.  :func:`resolve_by_document` is the secondary key and
      :func:`by_kind` isolates the subset that is a reading 4 question at all.
    * ``none/same-document`` -- we compile the document and differ at depth.  The judgment.
    * ``none/no-document`` and ``none/document-not-ours`` -- NOT a judgment, and
      :func:`partition` carries the reading: a name with no schema subject takes a migration
      note and never a class, and a document we compile nothing from is a question for the
      walk.  They are written with their kind so the file is a partition of the whole `none`
      bucket rather than a selection from it.
    """
    mirror = document_modules(index)
    our_documents = {
        document
        for key, row in ours["declarations"].items()
        if row["sig"]
        and (
            document := mirror.get(key.rsplit(".", 1)[0].removeprefix("adcp.types._schemas."))
        )
    }
    split = partition(report["rows"]["none"], our_documents, index)
    ours_by_document: dict[str, list[str]] = collections.defaultdict(list)
    for key, row in sorted(ours["declarations"].items()):
        document = mirror.get(key.rsplit(".", 1)[0].removeprefix("adcp.types._schemas."))
        if document and row["sig"]:
            ours_by_document[document].append(key)

    rows: list[tuple[str, str, str, str, str, str]] = [
        (
            kind,
            " ".join(sorted(row["names"])),
            row["theirs"],
            " ".join(row["ours"]),
            f"{row.get('sharing', 1)} of theirs share this target"
            if kind == "N:1"
            else f"{len(row['ours'])} declarations of OURS -- reading 4",
            row["method"],
        )
        for kind in ("N:1", "1:N")
        for row in report["rows"][kind]
    ]
    for where, entries in split.items():
        for row in entries:
            mine = ours_by_document.get(row.get("document") or "", [])
            best, shared = "", frozenset()
            elements = frozenset(_elements(theirs["declarations"][row["theirs"]]["schema"]))
            for key in mine:
                overlap = elements & frozenset(_elements(ours["declarations"][key]["schema"]))
                if len(overlap) > len(shared) or not best:
                    best, shared = key, overlap
            label = (
                " / ".join(
                    difference(
                        ours["declarations"][best]["schema"],
                        theirs["declarations"][row["theirs"]]["schema"],
                    )
                )
                if best
                else "no declaration of ours from this document"
            )
            rows.append(
                (
                    f"none/{where}",
                    " ".join(sorted(row["names"])),
                    row["theirs"],
                    best,
                    label,
                    row["method"],
                )
            )

    lines = [
        (f"# The judgment table: upstream adcp {theirs['version']} declarations that structure "
        f"could not decide against adcp_emit {ours['version']}.\n"),
        "# kind=N:1 a many-to-one -- decided by reading the bundle for REFERENCE vs RESTATEMENT\n",
        "# kind=1:N THE KEY COULD NOT DECIDE THE TARGET, which is NOT our duplication.  Measured\n",
        "#   (adcp-client-python-shh0, re-graded; 0kfk): the bucket's dominant case is the\n",
        "#   constrained scalar, whose signature is nearly vacuous -- every bounded string matches\n",
        "#   every other with the same bounds, so upstream's CanonicalFormatKindStr reaches seven\n",
        "#   UNRELATED subjects of ours differing only in the prose their documents state.  The\n",
        "#   secondary key is the DOCUMENT NODE (--provenance), and the model-class count is the\n",
        "#   figure that is a reading 4 question at all (--by-kind).\n",
        "# kind=none/same-document the judgment: we compile the document and differ at depth\n",
        "# kind=none/no-document NOT a judgment -- reading 10's migration note, never a class\n",
        "# kind=none/document-not-ours NOT a judgment -- a question for the walk\n",
        "kind\tupstream_names\ttheirs_declared_at\tnearest_of_ours\telements\tmethod\tverdict\n",
    ]
    lines += [f"{a}\t{b}\t{c}\t{d}\t{e}\t{f}\t\n" for a, b, c, d, e, f in rows]
    path.write_text("".join(lines))
    print(f"{len(rows)} judgment ROWS -> {path}")

    if classes_path is not None:
        grouped: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
        for kind, names, theirs_at, _, label, _method in rows:
            grouped[(kind, label)].append(f"{names}@{theirs_at}")
        head = [
            (f"# The DIFFERENCE CLASSES of the judgment table, upstream adcp {theirs['version']}"
            f" against adcp_emit {ours['version']}.\n"),
            (f"# {len(grouped)} classes accounting for {len(rows)} declarations.  **ONE ROW IS "
            "ONE RULING**, and it is a per-element ruling: does the DOCUMENT account for this "
            "element differing.  Never a ratio (reading 10 as amended).\n"),
            "kind\telements\tdeclarations\texample\tverdict\n",
        ]
        head += [
            f"{kind}\t{label}\t{len(members)}\t{min(members)}\t\n"
            for (kind, label), members in sorted(
                grouped.items(), key=lambda kv: (-len(kv[1]), kv[0])
            )
        ]
        classes_path.write_text("".join(head))
        print(f"{len(grouped)} DIFFERENCE CLASSES -> {classes_path}")
    report["judgment_rows"] = len(rows)
    report["judgment_none_split"] = {k: len(v) for k, v in split.items()}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dump", type=Path, metavar="PATH")
    parser.add_argument("--side", choices=("ours", "upstream"))
    parser.add_argument("--root", default="adcp.types")
    parser.add_argument("--join", action="store_true")
    parser.add_argument("--ours", type=Path, metavar="PATH")
    parser.add_argument("--theirs", type=Path, metavar="PATH")
    parser.add_argument("--report", type=Path, metavar="PATH")
    parser.add_argument("--judgment", type=Path, metavar="PATH")
    parser.add_argument("--judgment-classes", type=Path, metavar="PATH")
    parser.add_argument(
        "--bundle",
        type=Path,
        default=HERE.parent / "schemas" / "cache" / "3.2",
        help="the bundle whose document list decides whether an unmatched name has a subject "
        "at all, which is what keeps reading 10's migration-note population out of the "
        "judgment table",
    )
    parser.add_argument("--mechanical", type=Path, metavar="PATH")
    parser.add_argument("--deliberate-only", action="store_true")
    parser.add_argument(
        "--by-kind",
        action="store_true",
        help="compute the four buckets ONCE PER KIND, because signature identity is strong "
        "evidence for a model and nearly vacuous for a constrained scalar.  Isolates the "
        "MODEL-CLASS 1:N count, which is the only part of that bucket that is a reading 4 "
        "question (adcp-client-python-0kfk)",
    )
    parser.add_argument(
        "--provenance",
        action="store_true",
        help="tie-break the 1:N rows on the DOCUMENT NODE the signature drops by design.  A "
        "tie-break over the candidates structure already admitted, never a proposal",
    )
    parser.add_argument(
        "--relax",
        default="",
        help="comma-separated names from RELAXATIONS, each with its cost stated there.  The "
        "setting is recorded in the dump and the join refuses two dumps taken at different "
        "ones",
    )
    args = parser.parse_args()
    for name in filter(None, args.relax.split(",")):
        if name not in RELAX:
            parser.error(f"--relax {name!r} is not one of {sorted(RELAX)}")
        RELAX[name] = True
    if args.dump:
        if not args.side:
            parser.error("--dump needs --side, because the version recorded differs")
        dump(args.dump, args.side, args.root)
        return
    if not (args.ours and args.theirs):
        parser.error("--join needs --ours and --theirs")
    ours = json.loads(args.ours.read_text())
    theirs = json.loads(args.theirs.read_text())
    assert theirs.get("version") not in (None, "", "unknown"), (
        "the upstream dump records no version, and every count below is a claim about one"
    )
    # **TWO DUMPS TAKEN AT DIFFERENT SETTINGS ARE NOT COMPARABLE**, and a join that proceeded
    # anyway would report a bucket decomposition in which one side had been normalised and the
    # other had not -- every row `none` for a reason belonging to the instrument.
    assert ours.get("relaxations") == theirs.get("relaxations"), {
        "the two dumps were taken at different relaxation settings": {
            "ours": ours.get("relaxations"),
            "theirs": theirs.get("relaxations"),
        }
    }
    sys.path.insert(0, str(HERE.parent / "tests"))
    from nodeset import claimed

    claimed(f"our declarations, {ours['version']}", ours["declarations"])
    claimed(f"upstream {theirs['version']}'s declarations", theirs["declarations"])
    report = join(ours, theirs, deliberate_only=args.deliberate_only)
    report["upstream_version"] = theirs["version"]
    report["ours_version"] = ours["version"]
    report["normalisations"] = NORMALISATIONS
    report["relaxations"] = {k: RELAXATIONS[k] for k, v in (ours.get("relaxations") or {}).items() if v}
    print(f"upstream adcp {theirs['version']} vs adcp_emit {ours['version']}")
    print(f"  relaxations applied: {sorted(ours.get('relaxations') or ()) or 'none (strict)'}")
    print(f"  declarations: ours {report['ours_declarations']}, theirs {report['theirs_declarations']}")
    print(f"  distinct signatures: ours {report['ours_signatures']}, theirs {report['theirs_signatures']}")
    for bucket, count in report["buckets"].items():
        print(f"  {bucket:6} {count:6}")
    print(f"  JUDGMENT TABLE {sum(report['buckets'][k] for k in ('N:1', '1:N', 'none')):6}")
    print(f"  our own signature collisions: {len(report['our_own_collisions'])}")
    if args.by_kind:
        report["by_kind"] = by_kind(ours, theirs, deliberate_only=args.deliberate_only)
        print("  THE FOUR BUCKETS, ONCE PER KIND -- the denominator each row is decided against")
        for kind, blob in report["by_kind"].items():
            counts = "  ".join(f"{k} {v}" for k, v in blob["buckets"].items())
            print(
                f"    {kind:8} theirs {blob['theirs_declarations']:5}  "
                f"ours {blob['ours_declarations']:5}  |  {counts}"
            )
            print(f"             evidence: {blob['evidence'].split('.')[0]}")
        print(f"  MODEL-CLASS 1:N = {report['by_kind']['model']['buckets']['1:N']}")
    if args.mechanical:
        write_mechanical(args.mechanical, report, theirs, ours)
    if args.provenance:
        import alias_surface

        report["provenance"] = resolve_by_document(
            report, ours, theirs, alias_surface.bundle_index(args.bundle)
        )
        print("  THE 1:N ROWS, TIE-BROKEN ON THE DOCUMENT NODE")
        for where, entries in report["provenance"].items():
            print(f"    {where:20} {len(entries):5}")
    if args.judgment:
        import alias_surface

        write_judgment(
            args.judgment,
            args.judgment_classes,
            report,
            theirs,
            ours,
            alias_surface.bundle_index(args.bundle),
        )
        print(f"  the `none` bucket, partitioned: {report['judgment_none_split']}")
    if args.report:
        args.report.write_text(json.dumps(report, indent=1))
        print(f"report -> {args.report}")


if __name__ == "__main__":
    main()
