"""THE N:1 NAME TABLE: every name upstream publishes for a document, against OUR class for it.

**THE RELATION IS N:1 AND PIGEONHOLE SAYS SO BEFORE ANY MEASUREMENT.** Upstream's tree holds
3,226 classes and ours 2,500, both generated from one bundle, so some of our classes must
answer for several of their names. Measured: 89 of ours absorb 265 of theirs, up to 16:1
(`SIComponentCatalog`), because their generator promotes every inner node of a document to a
top-level class where we emit one class per subject. A 1:1 join cannot express that, and a
1:1 join was what this project had -- which is why 265 names read as an irreducible residue
for agents rather than as a fan-out.

**THE MODULE PATH IS THE DOCUMENT, and that is the whole key for half of it.** Their
`domains/brand/verify_brand_claims_request.py` and our
`_schemas/brand/verify_brand_claims_request.py`
are one document; 767 module paths are shared. Our classes carry `__adcp_schema__`, so OUR
side already knows its subject exactly. Nothing has to be inferred about it.

So the table is five rules, each a fact and none a comparison of class definitions:

``collapse``       the module holds ONE class of ours, so every name they publish for that
                   document denotes it. 423 modules, 522 names, and nothing to choose between.
``signature``      several of ours: the field-and-required set picks one, where it is unique.
``branch-order``   their ``X1`` is branch 0, ``X2`` is branch 1 -- their ordinal IS document
                   order, and our pointers carry the same index. 348 names.
``name``           the word is the same on both sides and unique in the module.
``property-key``   their generator names an inner class from a property KEY, so ``Setup``
                   is ``properties/setup`` and our class at that pointer is the match.  It
                   SINGULARISES an array's item type, so ``Invoice`` is ``invoices/items``.

And four more that look across the WHOLE tree, because the module is not the last word --
``_cross_tree``'s own docstring carries them:

``cross-name``     exactly one class of ours carries that word, in whatever module.
``cross-subject``  exactly one carries that field-and-required set.
``cross-required`` exactly one carries that required set.
``their-default``  the field sets are EQUAL and their required set is a strict SUBSET of
                   ours -- their invented default seen from the names rather than the fields.

Measured over bundle 3.2 against upstream 9.6.1: **2,175 of 2,574 names, 84%**, by

    signature 827   collapse 522   branch-order 348   their-default 140   name 127
    cross-name 96   cross-subject 60   cross-required 47   property-key 8

**399 are RESIDUE and are reported, never guessed at.** No tenth rule is invented to absorb
them: a rule written to clear a residue is how a join starts binding wrong subjects, which is
what a field-set key did when it bound upstream's ``Brand`` to our
``GetAdCPCapabilitiesResponse``. At 84% the remainder is small enough to READ.
"""

import collections
import json
import pathlib
import re

up = json.loads(pathlib.Path("/tmp/bind_up.json").read_text())
ours = json.loads(pathlib.Path("/tmp/bind_ours.json").read_text())


def rel(p, m):
    g = re.search(rf"adcp\.types\.{m}\.(.+)\.[A-Za-z_]\w*$", p)
    return g.group(1) if g else None


theirs_by_module = collections.defaultdict(list)
ours_by_module = collections.defaultdict(list)
#: **AND EVERY BINDING OF THEIRS, not only the ones under ``domains/``.**  A name in their
#: hand-written layer -- ``aliases``, ``_eager``, ``guards``, ``registry``, ``base`` -- has no
#: document and so no module to pair with ours, but it is still a word their code and their
#: tests import.  Scoped to ``domains`` the loop never saw it:
#: ``UpdateMediaBuySuccessResponse`` is re-exported from three such modules and 298 of their
#: tests fail on it.  A binding with no shared module path goes straight to ``_cross_tree``.
elsewhere = []
for p, r in up.items():
    k = rel(p, "domains")
    if k:
        theirs_by_module[k].append(r)
    else:
        elsewhere.append(r)
for p, r in ours.items():
    k = rel(p, "_schemas")
    if k:
        ours_by_module[k].append({"path": p, **r})


def snake(name):
    """their inner class name -> the property key their generator took it from"""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


ENVELOPE = frozenset({"adcp_version", "adcp_major_version"})
#: Their generator adds these at every position, so they are not part of a subject and every
#: field comparison below subtracts them.  Measured: with them left in, the subject signature
#: of a document root never equals ours.


def _plurals(key):
    """The keys their singularised inner class could have come from."""
    yield key
    yield key + "s"
    yield key + "es"
    if key.endswith("y"):
        yield key[:-1] + "ies"


def _index(records):
    """Our classes indexed every way a rule asks for them."""
    by_name, by_sig, by_req, flat = (
        collections.defaultdict(list),
        collections.defaultdict(list),
        collections.defaultdict(list),
        [],
    )
    # **AMONG OUR CANDIDATES FOR A WORD, THE DECLARED ONE IS THE SUBJECT.**  Our own surface
    # re-exports every class several times -- `_schemas/...`, `_surface/<domain>`, `_flat` --
    # so a by-name lookup finds three or four rows for one object and a "unique or nothing"
    # rule answers nothing.  Measured: `UpdateMediaBuyResponse1` is the target of the
    # re-export 298 of their tests need, and it read as ambiguous for exactly this reason.
    # Only the row where the object was DEFINED goes in the name index; the rest are our own
    # spellings of it and say nothing new.
    for path, row in records.items():
        fields = tuple(sorted(set(row["fields"]) - ENVELOPE))
        required = tuple(sorted(set(row["required"]) - ENVELOPE))
        by_name[row["name"]].append((path, row))
        by_sig[(fields, required)].append((path, row))
        by_req[required].append((path, row))
        flat.append((path, row, set(fields), set(required)))
    return by_name, by_sig, by_req, flat


def _one(candidates):
    """The one path among our candidates for a word, or None where the word is ambiguous.

    **OUR OWN SURFACE RE-EXPORTS EVERY CLASS SEVERAL TIMES** -- `_schemas/...`,
    `_surface/<domain>`, `_flat` -- so a by-name lookup finds three or four rows for ONE
    object and a "unique or nothing" rule answers nothing.  Measured: restricting the index to
    declarations instead lost 2,223 rows, because many of our words are only reachable as a
    re-export.  So every row stays in the index and the DECLARATION disambiguates: where the
    candidates are several spellings of one object, the row that DEFINED it is the answer;
    where they are genuinely different objects, there is no unique declaration and the word is
    ambiguous, which is the honest verdict.
    """
    rows = candidates or []
    if len(rows) == 1:
        return rows[0][0]
    declared = [path for path, row in rows if row.get("declared")]
    if len(declared) == 1:
        return declared[0]
    # **SEVERAL ROWS THAT NAME ONE OBJECT ARE NOT AN AMBIGUITY.**  A word of ours bound by an
    # ALIAS has `declared` false everywhere -- `UpdateMediaBuyResponse1 = UpdateMediaBuySuccess`
    # puts the object's `__module__` at the definition, so all three of our spellings read as
    # undeclared and the rule above cannot choose.  But `points_at` is the same object in all
    # three, so there is nothing to choose BETWEEN: the answer is that object.  Only where the
    # candidates point at DIFFERENT objects is the word genuinely ambiguous.
    targets = {row.get("points_at") for _path, row in rows if row.get("points_at")}
    if len(targets) == 1:
        return next(iter(targets))
    return None


def _cross_tree(theirs):
    """Our class for one of their names, looked for across the WHOLE tree.

    Four readings, strongest first, and each returns only where it is UNIQUE -- an ambiguous
    answer is no answer and goes to the residue rather than to a tie-break:

    ``cross-name``     exactly one class of ours carries that word.
    ``cross-subject``  exactly one carries that field-and-required set.
    ``cross-required``  exactly one carries that required set, where the field sets differ
                       because one side holds optional members the other does not.
    ``their-default``  the field sets are EQUAL and their required set is a strict SUBSET of
                       ours.  That is their invented default seen from the other side: a
                       ``default`` makes a required field optional, so their class is ours with
                       a requirement removed, and the subject is identical.  Measured on this
                       bundle it resolves 138 names, and the missing requirement is
                       ``authorization_type`` -- a discriminator -- in every sample.  It is the
                       same 867 pairs ``verdicts/invented-defaults.md`` attributes to their
                       generator, confirmed from the names rather than from the fields.
    """
    name = theirs["name"]
    hit = _one(OUR_NAME.get(name))
    if hit:
        return hit, "cross-name"
    # **A RE-EXPORT OF THEIRS IS ANSWERED BY ITS TARGET, one hop.**  16,763 of their 21,496
    # bindings are re-exports, and the target's own word is what the rest of this table
    # already resolves.  `UpdateMediaBuySuccessResponse` is the measured case: not a class on
    # their side at all, re-exported from `_eager`, `aliases` and `guards`, every one pointing
    # at `canonical_creative.UpdateMediaBuyResponse1`.  Chasing the target's NAME -- not its
    # module, which this branch deleted -- reaches our class, and 298 of their tests turn on it.
    if not theirs.get("declared") and theirs.get("points_at"):
        target = str(theirs["points_at"]).rsplit(".", 1)[-1]
        if target != name:
            hit = _one(OUR_NAME.get(target))
            if hit:
                return hit, "their-reexport"
    fields = tuple(sorted(set(theirs["fields"]) - ENVELOPE))
    required = tuple(sorted(set(theirs["required"]) - ENVELOPE))
    hit = OUR_SIG.get((fields, required)) or []
    if len(hit) == 1:
        return hit[0][0], "cross-subject"
    hit = OUR_REQ.get(required) or []
    if len(hit) == 1:
        return hit[0][0], "cross-required"
    want_f, want_r = set(fields), set(required)
    hit = [path for path, _row, ours_f, ours_r in OUR_FLAT if ours_f == want_f and want_r < ours_r]
    if len(hit) == 1:
        return hit[0], "their-default"
    return None, None


rows, residue = [], []
OUR_NAME, OUR_SIG, OUR_REQ, OUR_FLAT = _index(ours)
for mod in sorted(set(theirs_by_module) & set(ours_by_module)):
    theirs, mine = theirs_by_module[mod], ours_by_module[mod]
    if len(mine) == 1:
        for t in theirs:
            rows.append({"their": t["name"], "ours": mine[0]["path"], "how": "collapse"})
        continue
    by_sig = collections.defaultdict(list)
    by_name = collections.defaultdict(list)
    by_tail = collections.defaultdict(list)  # last path segment of our pointer
    branches = []  # our branch classes, in document order
    for o in mine:
        by_sig[(tuple(o["fields"]), tuple(o["required"]))].append(o)
        by_name[o["name"]].append(o)
        ptr = o["pointer"] or ""
        tail = ptr.rstrip("/").split("/")[-1] if ptr else ""
        by_tail[tail].append(o)
        g = re.search(r"#/(?:oneOf|anyOf)/(\d+)$", ptr)
        if g:
            branches.append((int(g.group(1)), o))
    branches.sort(key=lambda pair: pair[0])
    for t in theirs:
        sig = (tuple(t["fields"]), tuple(t["required"]))
        pick = how = None
        cand = by_sig.get(sig) or []
        if len(cand) == 1:
            pick, how = cand[0]["path"], "signature"
        elif len(by_name.get(t["name"], [])) == 1:
            pick, how = by_name[t["name"]][0]["path"], "name"
        else:
            g = re.match(r"^(.*?)(\d+)$", t["name"])
            if g and branches:
                k = int(g.group(2)) - 1  # their X1 is branch 0
                if 0 <= k < len(branches):
                    pick, how = branches[k][1]["path"], "branch-order"
            if pick is None:
                key = snake(t["name"])
                hit = by_tail.get(key) or []
                if len(hit) == 1:
                    pick, how = hit[0]["path"], "property-key"
        if pick is None:
            # **THE MODULE IS NOT THE LAST WORD, because WE EMIT PER SUBJECT AND THEY EMIT PER
            # POSITION.**  §3a: collect every type the bundle states, deduplicate, name each
            # subject once.  So `credit_limit` belongs to `core/account.json` and we emit ONE
            # class there, which every position reaching that subject points at; their
            # generator emits a fresh class at each position, so `CreditLimit` exists in
            # `core.account` for them AND again in `sync_accounts_response`.  Their 3,226
            # against our 2,500 is largely that.  A module-scoped lookup therefore reports a
            # name as unplaceable when our class for it is simply one module over.
            pick, how = _cross_tree(t)
        if pick:
            rows.append({"their": t["name"], "ours": pick, "how": how})
        else:
            residue.append(
                {"their": t["name"], "module": mod, "ours_in_module": [o["name"] for o in mine]}
            )
# the hand-written layer: no document, so the module-scoped rules cannot apply
seen = {r["their"] for r in rows}
for r in elsewhere:
    if r["name"] in seen:
        continue
    pick, how = _cross_tree(r)
    if pick:
        rows.append({"their": r["name"], "ours": pick, "how": how})
        seen.add(r["name"])
    else:
        residue.append({"their": r["name"], "module": r["module"], "ours_in_module": []})

total = sum(len(v) for k, v in theirs_by_module.items() if k in ours_by_module) + len(
    {r["name"] for r in elsewhere}
)
print(f"their names in shared modules : {total}")
print(f"  MAPPED                      : {len(rows)}  ({100 * len(rows) // total}%)")
for h, c in collections.Counter(r["how"] for r in rows).most_common():
    print(f"      {h:14s} {c}")
print(f"  residue for agents          : {len(residue)}")
pathlib.Path("survey/name-table-9.6.1.json").write_text(json.dumps({"rows": rows, "residue":
residue}, indent=1))
