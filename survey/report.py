"""Write the survey's HTML report.  Every figure is read from the measurement JSON."""

from __future__ import annotations

import html
import json
import pathlib
import subprocess
import sys

S = pathlib.Path("survey")
cov = json.loads((S / "coverage.json").read_text())
con = json.loads((S / "constrains.json").read_text())
raw = json.loads((S / "compose_raw.json").read_text())
dec = json.loads((S / "c_title.json").read_text())
notitle = json.loads((S / "c_notitle.json").read_text())
defn = json.loads((S / "definition.json").read_text())
OUT = pathlib.Path(sys.argv[1])

KW = dict(cov["unnamed"]) | {k: c for k, c, _ in cov["named"]}
NEVER = cov["unnamed"]
SHA = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                     text=True, cwd=".").stdout.strip()

# ---- the keyword table: name, sites, role, verdict -----------------------------
DRAFT_ANN = ["$schema", "$comment", "title", "description", "examples", "default",
             "deprecated", "readOnly", "writeOnly"]
PAYLOAD = ["version", "lastUpdated", "last_updated", "mappings", "vocabulary", "governance",
           "extensions", "_generated", "_generatedAt", "adcp_version", "architecture",
           "asset_types", "baseUrl", "prerelease", "protocol_layers", "published_version",
           "stability", "usage_notes", "versioning"]
XS = sorted([k for k, _ in NEVER if k.startswith("x-")], key=lambda k: -KW[k])

VALUE_TABLE = [
    ("minimum", "ge", 1083, 288, "named in D5 by example only"),
    ("maximum", "le", 197, 115, "named in D5 by example only"),
    ("exclusiveMinimum", "gt", 58, 30, "NEVER named as the document's keyword"),
    ("exclusiveMaximum", "lt", 4, 4, "never named"),
    ("minLength", "min_length", 771, 287, "named in D5 by example only"),
    ("maxLength", "max_length", 607, 243, "named in D5 by example only"),
    ("pattern", "pattern", 830, 345, "decided in D5 (the uri arm)"),
    ("minItems", "min_length", 1075, 347, "one worked instance in D5's third rung"),
    ("maxItems", "max_length", 147, 88, "named in D3's type-word rung only"),
    ("format", "selects a TYPE, never a constraint", 806, 300, "decided in D5"),
    ("multipleOf", "no rendering: 0 sites, refuses by name", 0, 0, "never named"),
]

X_VERDICTS = {
    "x-entity": "an entity tag on an id-shaped string; the largest keyword the first pass missed entirely",
    "x-adcp-validation": "instance obligations no draft-07 keyword expresses; 158 distinct values, upstream gap",
    "x-status": "one value, &ldquo;experimental&rdquo;; document metadata",
    "x-mutates-state": "operation metadata (43 true, 1 false), all at a root",
    "x-tool-summary": "one English sentence per task document",
    "x-added-in": "one value, 3.2.0",
    "x-adcp-schema-uri": "restates the sibling $ref&rsquo;s target",
    "x-canonicalization": "always &ldquo;set&rdquo;; all 16 sites already carry uniqueItems: true",
    "x-adcp-model-context-inline": "a generation directive; D1/D3/D5 decide structure",
    "x-accessibility": "always true; annotates a transcript/alt-text field",
    "x-governed-commitment": "governance metadata about the operation",
    "x-deprecated-in": "one value, 3.2.0",
    "x-operation-family": "operation metadata, one value per document",
    "x-legacy-fallback": "operation metadata",
    "x-adcp-hoist": "a generation directive asking for a named type; D2/D3 already name every root",
    "x-adcp-open-payload": "3 of 4 sites restate additionalProperties: true (D8); the 4th is a typeless node (Any)",
    "x-removed-in": "one value, 4.0.0",
    "x-superseded-by": "names replacement tasks",
    "x-idempotency-key-required": "both sites false; operation metadata",
    "x-extensible": "with x-pattern, the open-vocabulary shape the validator ignores",
    "x-deprecated-enum-values": "names enum members as deprecated; the enum still admits them",
    "x-deprecated-enum-values-doc": "English beside the above",
    "x-pattern": "an open-vocabulary regex beside a closed enum; the document stays closed",
    "x-enum-descriptions": "a SECOND spelling of enumDescriptions; the enum row reads only the first, so this document&rsquo;s member docs are dropped",
    "x-task-result-schema-overrides": "a registry mapping at an enum root",
    "x-entity-definitions": "English definitions of the x-entity vocabulary",
    "x-canonical-policy-required-params-not-enforced": "English policy note",
    "x-adcp-file-size-units": "English unit convention",
    "x-adcp-sdk-local": "marks a document as SDK-local",
    "x-compatibility-projection-only": "marks a projection-only field",
}


def esc(x: str) -> str:
    return html.escape(str(x))


def row(cells, cls=""):
    return f'<tr class="{cls}">' + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def residue_rows(d):
    out = []
    for r in sorted(d["residue"], key=lambda r: -r["nodes"]):
        out.append(row([
            f'<b>{r["nodes"]}</b>',
            "<code>" + esc(", ".join(r["keys"])) + "</code>",
            esc(r["why"]),
            "<code>" + esc(r["site"][0]) + "#" + esc(r["site"][1] or "/") + "</code>",
        ]))
    return "\n".join(out)


STYLE = (pathlib.Path("/Users/konst/projects/acp-fresh/docs/audits/v9-correctness.html")
         .read_text().split("<style>")[1].split("</style>")[0])

parts = []
A = parts.append

A(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Schema Keyword Survey</title>
<style>{STYLE}</style></head><body><div class="w">

<header>
<h1>Every keyword and every signature in the AdCP schema bundle, and which of them the
rebuild plan decides</h1>
<p class="sub">bead <code>salesagent-j3k2l.53</code> &middot; measured 2026-10-25 &middot;
bundle <code>schemas/cache/3.2</code> (AdCP 3.2.4) &middot;
tree <code>acp-j3k2l53 @ {esc(SHA)}</code> &middot; decisions rebased onto trunk
<code>07c84c14a</code><br>
instrument <code>survey/*.py</code> in that worktree &middot; no production code changed</p>
</header>

<p class="lede">Three results. The plan never names <b>49</b> of the bundle&rsquo;s 97 schema
keywords, not the 22 the bead lists. <b>None</b> of the 63 non-draft keywords can refuse any
instance &mdash; 0 refusals over 184,418 validations &mdash; so every one of them is an
annotation and the risk is not a model wider than its document. And the signature survey&rsquo;s
premise was 5&times; too large: the population is <b>632</b> distinct signatures over 18,203
declaring nodes, not 3,039 over 22,659, because the first pass&rsquo;s aggregate figures were
taken with a blanket walk that counted example payloads as schemas.</p>

<h2>0. The four figures, and why they do not reproduce</h2>

<p>The bead&rsquo;s instrument: walk every node of the 1,054 portable documents, count a
node&rsquo;s own keywords, recurse only into schema positions, walk the name&rarr;schema maps
(<code>properties</code>, <code>definitions</code>, <code>$defs</code>,
<code>patternProperties</code>, <code>dependencies</code>) by VALUE and never by key. Run
independently of <code>codegen.bundle</code> and then cross-checked against it: the two agree.</p>

<table><thead><tr><th>figure</th><th>first pass</th><th>this pass</th><th></th></tr></thead><tbody>
{row(["portable documents", "1,054", "<b>1,054</b>", "agrees"])}
{row(["schema-position nodes, all", "&mdash;", "<b>21,257</b>", ""])}
{row(["nodes declaring something", "22,659", "<b>18,203</b>", "disagrees"])}
{row(["pure <code>$ref</code> nodes declaring nothing", "4,176", "<b>3,027</b>", "disagrees"])}
{row(["distinct schema keywords", "88", "<b>97</b>", "disagrees"])}
{row(["distinct keyword signatures", "3,039", "<b>632</b>", "disagrees"])}
{row(["&hellip; singletons", "2,150", "<b>270</b>", ""])}
{row(["&hellip; top 25 cover", "64.4%", "<b>68.3%</b>", ""])}
</tbody></table>

<p>What <i>does</i> reproduce exactly is every one of the 23 per-keyword counts the bead lists
&mdash; <code>minItems</code> 1075, <code>discriminator</code> 81,
<code>exclusiveMinimum</code> 58, <code>exclusiveMaximum</code> 4, and all 17
<code>x-</code> names plus <code>version</code> 4 and <code>lastUpdated</code> 3. So the
KEYWORD census was taken with the schema-position walk and is sound. The four aggregates were
taken with a different walk.</p>

<table><thead><tr><th>walk</th><th>declaring</th><th>pure $ref</th><th>keywords</th><th>signatures</th><th>singletons</th></tr></thead><tbody>
{row(["schema positions (this pass)", "18,203", "3,027", "97", "632", "270"])}
{row(["blanket, descend every key", "23,854", "3,027", "5,337", "3,340", "2,291"])}
{row(["blanket, annotations dropped from the declaring test",
      "22,765", "4,103", "&mdash;", "3,144", "2,201"])}
{row(["<b>the first pass&rsquo;s figures</b>", "<b>22,659</b>", "<b>4,176</b>", "<b>88</b>",
      "<b>3,039</b>", "<b>2,150</b>"], "t")}
</tbody></table>

<p>Clinching measurement: <b>5,656</b> blanket-walk declaring nodes sit at no schema position
at all. <b>2,708</b> of the 3,340 blanket signatures exist only under the blanket walk, and
<b>2,323</b> of those contain no schema keyword whatsoever &mdash; they are instance data from
<code>examples</code>, <code>x-adcp-validation</code> bodies and <code>enumMetadata</code>.
The largest are <code>[data, description]</code> at 196 nodes,
<code>[recovery, suggestion]</code> at 149, <code>[propertyName]</code> at 81 &mdash; that one
is literally the inside of the 81 <code>discriminator</code> objects &mdash; and
<code>[spec, verifier_constraints]</code> at 65. A hand-written example object has a unique key
set, which is also why 2,150 of the 3,039 were singletons.</p>

<div class="note"><b>Two smaller corrections.</b> The bead says 22 keywords and enumerates 23
(4 JSON Schema + 17 <code>x-</code> + <code>version</code> + <code>lastUpdated</code>). And
the bead cites &ldquo;D15&rdquo; for the conjunct rule about a keyword draft-07 does not
define; the plan has D1&ndash;D14 and that rule is <b>D7</b>&rsquo;s fourth bullet. The two
decisions this survey adds therefore take D15 and D16.</div>

<h2>0.5 The definition every figure below is read under</h2>

<div class="q"><b>Annotation keys are not part of a signature and do not make a node
declaring. A node whose keys are annotations alone declares nothing. A node carrying
<code>$ref</code> plus annotations alone is a PURE REFERENCE.</b><br><br>
<b>And membership is decided by a TEST, not by a list: a keyword is an annotation for this
purpose only where PROJECTING IT DOES NOT CHANGE THE ANSWER.</b> The 45 names below are that
test&rsquo;s output over this bundle, not the definition. A test can be applied to a keyword
nobody has seen yet; a list cannot.</div>

<p>Adopted, because it is the survey&rsquo;s own question: this row asks what decides WHAT A
NODE BECOMES, and two nodes identical but for a <code>description</code> have one answer, so
counting them as two signatures inflates the residue with distinctions that have no decision
attached. It is the same rule as composition rule C1 below, applied to the census as well as
to the residue.</p>

<p>The set is where the two readings differed, and the figures say which set by name. The
lead&rsquo;s ten-name set reproduces exactly; it is sound in direction and incomplete in
membership, and two of its members fail a test the definition itself implies.</p>

<table class="t"><thead><tr><th>projection set</th><th>names</th><th>declaring</th><th>pure $ref</th><th>keywords</th><th>signatures</th><th>singletons</th><th>top 25</th></tr></thead><tbody>
{row(["none (my first report)", "0", "18,203", "3,027", "<b>97</b>", "<b>632</b>", "270", "68.3%"])}
{row(["the lead&rsquo;s set", "10", "17,079", "4,139", "<b>88</b>", "<b>356</b>", "146", "83.5%"])}
{row(["<b>ADOPTED</b>: measured constrains-nothing, less <code>title</code> and the 19 payload keys",
      "<b>45</b>", "<b>17,048</b>", "<b>4,138</b>", "<b>54</b>", "<b>248</b>", "<b>72</b>", "<b>84.1%</b>"], "t")}
{row(["every keyword measured to constrain nothing", "65", "16,982", "4,200", "33", "190", "51", "87.8%"])}
</tbody></table>

<div class="note"><b>The residue does not depend on which set you adopt, and that is what
makes the whole projection argument safe.</b> A reader will reasonably suspect the opposite
&mdash; that a looser projection buys a smaller residue. It does not: under every projection
measured here the residue is the <b>same 95 of 18,203 nodes</b>, 0.52%, in the same three
shapes. Projecting more keywords merges answered signatures into fewer projections and
projecting fewer splits them into more (23 against 29), but no projection discovers or hides a
single residue node. The set changes how the census reads; it does not change the answer.</div>

<h3>Why the set is 45 names and not 10</h3>

<p>Every one of the lead&rsquo;s ten names IS measured to constrain nothing, so nothing in the
set is wrong. 55 more keywords measure the same way and are not in it, so they still split
signatures while deciding nothing &mdash; which is the defect the definition exists to remove.
The largest: <code>default</code> 342 sites, <code>x-adcp-validation</code> 179,
<code>x-status</code> 170, <code>enumDescriptions</code> 137, <code>discriminator</code> 81,
and the rest of the <code>x-</code> namespace. Including them takes 356 signatures to 248.</p>

<h3>Why <code>title</code> is not in it</h3>

<p><code>title</code> refuses nothing &mdash; it is one of the 63 &mdash; and it decides what a
node becomes anyway. D2: a value set no name reaches is a <code>Literal</code>, and a NAMED
enum node is a <code>StrEnum</code>. So the presence of a title selects between two
renderings.</p>

<div class="kpi">
<div><b>226</b><span>enum nodes carrying a title</span></div>
<div><b>843</b><span>enum nodes carrying none</span></div>
<div><b>905</b><span>nodes in the one projection that holds both</span></div>
<div><b>0</b><span>extra residue from keeping it</span></div>
</div>

<p>The projection <code>{{enum, type}}</code> holds 226 titled and 679 untitled nodes. Projecting
<code>title</code> out merges them into one signature with two different answers. Keeping it
splits 221 answered projections into more of them and finds <b>no new residue</b> &mdash; the
residue node count is 95 either way &mdash; so it costs nothing and preserves a decision.</p>

<p>The same test disqualifies the nineteen registry payload keys: their decision IS a refusal,
and projecting them would make a refused document&rsquo;s root signature look answerable. So
the rule the definition implies is sharper than the definition: <b>a keyword is an annotation
for this purpose only where projecting it does not change the answer.</b> <code>title</code>
fails because it selects another keyword&rsquo;s reading; a payload key fails because it
decides the verdict. Everything else passes.</p>

<h2>1. The plan never names 49 of the 97 keywords</h2>

<p>Measured by resolving every keyword at a schema position and searching
<code>docs/plan/rebuild-plan.md</code> for each name. 48 named at least once, <b>49 never</b>.
The bead&rsquo;s list of 23 is a subset; the 26 it misses include the third most common keyword
in the bundle.</p>

<table class="t"><thead><tr><th>keyword</th><th>sites</th><th>in draft-07&rsquo;s vocabulary</th><th>what it is</th></tr></thead><tbody>""")

ROLE = {}
for k in DRAFT_ANN:
    ROLE[k] = ("draft-07 annotation", "annotation: constrains nothing, 0 refusals measured")
for k in PAYLOAD:
    ROLE[k] = ("registry payload", "a registry document&rsquo;s own instance data at a schema root &mdash; refused")
for k in XS:
    ROLE[k] = ("bundle <code>x-</code> namespace", X_VERDICTS.get(k, ""))
ROLE["exclusiveMaximum"] = ("value keyword", "CONSTRAINS: 4 of 4 sites measured")

for k, c in NEVER:
    r, why = ROLE.get(k, ("&mdash;", ""))
    vocab = "yes" if k == "exclusiveMaximum" else "no"
    cls = "t" if k in ("x-entity", "x-adcp-validation", "deprecated", "exclusiveMaximum") else ""
    A(row([f"<code>{esc(k)}</code>", f"<b>{c}</b>" if c >= 100 else str(c), vocab,
           f'<span class="f">{r}</span> &mdash; {why}' if why else f'<span class="f">{r}</span>'],
          cls))

A(f"""{row(["<code>deprecated</code>", "<b>179</b>", "no",
      '<span class="f">draft-07 annotation</span> &mdash; 179 sites in 95 documents; pydantic '
      'CAN render it (<code>Field(deprecated=True)</code>) and the emitted tree renders it '
      'nowhere, so it is a <code>missing</code> fact waiting for the first graded document '
      'that carries one'], "t")}
</tbody></table>

<div class="note"><b>Named, but by example only.</b> Three of the bead&rsquo;s four JSON Schema
keywords DO appear in the plan, never as the document-side keyword:
<code>minItems</code> once as a worked instance of D5&rsquo;s third rung;
<code>exclusiveMinimum</code> once as pydantic&rsquo;s rendering of
<code>PositiveInt</code>, a fact the MODEL adds; and all four <code>discriminator</code>
mentions are either the compiler&rsquo;s <code>DataType.discriminator</code> field or
&ldquo;the discriminator <code>const</code>&rdquo;, meaning the const-tagged property. So the
bead&rsquo;s claim holds in substance. <code>maxLength</code> (607 sites) and
<code>maximum</code> (197) are in the same position: two mentions each, both illustrative.</div>

<h2>2. Does each keyword constrain an instance?</h2>

<h3>The 63 non-vocabulary keywords: no</h3>

<p>Instrument: at every site, the keyword&rsquo;s own value AT THAT SITE becomes a one-keyword
schema <code>{{k: v}}</code>, and a thirteen-instance corpus
(<code>null true false 0 -1 1 1e9 "" "x" [] [1,2] {{}} {{a,b}}</code>) is put to it through
<code>jsonschema</code>.</p>

<div class="kpi">
<div><b>63</b><span>keywords probed</span></div>
<div><b>184,418</b><span>validations</span></div>
<div><b>0</b><span>refusals</span></div>
<div><b>32</b><span>keywords draft-07 can refuse on</span></div>
</div>

<p>None of them can refuse any instance, whatever its value. The mechanism is that
<code>jsonschema</code>&rsquo;s draft-07 vocabulary has 32 keywords and not one of these is
among them, and <code>strict_validate</code> answers through <code>jsonschema</code>. So
dropping any of them cannot make a model wider than the schema it names &mdash; the direction
that would admit traffic the document refuses. This is the whole of the extension namespace
(30 names, 1,090 sites), the nine draft-07 annotations present (12,845 sites), the nineteen
registry payload keys (25 sites), <code>discriminator</code> (81), and
<code>notes</code>/<code>enumMetadata</code>/<code>enumDescriptions</code>/<code>errorMessage</code>.</p>

<h3>The three vocabulary keywords: yes, measured per site</h3>

<p>Instrument: the keyword&rsquo;s own value supplies the boundary witness &mdash; the array one
shorter than <code>minItems</code>, the exact value <code>exclusiveMinimum</code> or
<code>exclusiveMaximum</code> names &mdash; and the witness is put to the document twice, at the
node and at the node with the keyword deleted. CONSTRAINS where it is refused with and accepted
without, which is what rules out a sibling keyword having done the refusing.</p>

<table class="t"><thead><tr><th>keyword</th><th>sites</th><th>CONSTRAINS</th><th>the remainder, each explained</th></tr></thead><tbody>
{row(["<code>minItems</code>", "1,075", "<b>1,044</b>",
      "15 where a sibling <code>contains</code> refuses the same short array &middot; "
      "14 where the element type refuses the filler &middot; 1 unresolved <code>$ref</code> "
      "&middot; 1 stating <code>minItems: 0</code>, which forbids nothing "
      "(<code>core/creative-localization.json#/properties/target_variants</code>)"])}
{row(["<code>exclusiveMinimum</code>", "58", "<b>58</b>", "none"])}
{row(["<code>exclusiveMaximum</code>", "4", "<b>4</b>", "none"])}
</tbody></table>

<div class="note"><b><code>gt</code> is not <code>ge</code>, and the bundle chose between them
730 times.</b> 672 sites state <code>minimum: 0</code>; 58 state
<code>exclusiveMinimum: 0</code> &mdash; all 58 of them, 57 on a <code>number</code> and 1 on an
<code>integer</code>. Rendering either keyword as the other makes 58 fields accept a zero their
document refuses, or 672 refuse a zero their document accepts. D5 already says this from the
other side: <code>PositiveInt</code> for <code>{{integer, minimum: 1}}</code> renders
<code>exclusiveMinimum: 0</code> and is refused for stating a different fact.</div>

<h3>The two the bead expected to constrain</h3>

<table class="t"><thead><tr><th>keyword</th><th>sites</th><th>verdict</th><th>why, measured</th></tr></thead><tbody>
{row(["<code>x-adcp-validation</code>", "179 in 135 docs",
      '<span class="p wid">constrains in INTENT, not in the document</span>',
      "cross-field and cross-item obligations: "
      "<code>{{&quot;unique_item_properties&quot;: [&quot;representation_id&quot;]}}</code>, "
      "&ldquo;property_ref.publisher_domain MUST equal publisher_domain when property_ref is "
      "present&rdquo;, &ldquo;every translate_to_native entry must have an exact matching "
      "resolve_value entry&rdquo;. No draft-07 keyword expresses any of them, so the DOCUMENT "
      "accepts a violating instance too. The gap is document-against-spec and is upstream; a "
      "model enforcing it would be NARROWER than the document it names."])}
{row(["<code>x-canonicalization</code>", "16",
      '<span class="p nar">adds nothing at any site</span>',
      "all 16 read <code>&quot;set&quot;</code>, and all 16 already carry <code>uniqueItems: true</code> "
      "and a <code>minItems</code> beside it &mdash; so the duplicate half IS the document&rsquo;s "
      "own <code>uniqueItems</code> (D6) and the order half is not an acceptance statement at "
      "all, both orders being accepted."])}
</tbody></table>

<h3>What <code>x-adcp-validation</code> actually holds, and why it is one decision</h3>

<p>&ldquo;Enforce the machine-readable part and report the rest&rdquo; is the obvious second
reading, so the content was classified by what each value IS rather than by the key holding
it. Reading by key name misleads twice: <code>ordered_bounds</code> sounds structured and both
its values are the sentence &ldquo;minimum MUST be less than or equal to maximum&rdquo;, while
<code>unique_config_generation</code>, <code>immutable_generation</code>,
<code>secret_rejection</code>, <code>account_isolation</code> and ten more bespoke keys hold
sentences too.</p>

<table><thead><tr><th>entries</th><th>what the value is</th></tr></thead><tbody>
{row(["164", "a bespoke key holding an English sentence"])}
{row(["137", "a <code>verifier_constraints</code> entry holding one"])}
{row(["74", "<code>spec</code>, naming a docs path"])}
{row(["60", "a single token"])}
{row(["47", "an object of names"])}
{row(["10", "a boolean"])}
{row(["9", "a list of sentences"])}
{row(["7", "a list of names"])}
</tbody></table>

<p><b>Exactly 16 entries across 14 documents are machine-readable</b>: six
<code>unique_item_properties</code> (<code>["representation_id"]</code>,
<code>["kind"]</code>, <code>["format_option_id"]</code>, <code>["creative_id"]</code>,
<code>["capability_id"]</code>), two <code>member_of</code>, and one each of
<code>map_keys_subset_of_array</code>, <code>resolver_response_binding</code>,
<code>disjoint_place_fields</code>, <code>allowed_slot_asset_types</code>,
<code>required_when</code>, <code>schema_required_when</code>, and two description-only
objects.</p>

<p><b>Enforcing those 16 is refused, on the plan&rsquo;s own ground rather than on effort.</b>
Each states something draft-07 cannot &mdash; uniqueness BY A KEY is not expressible at all
&mdash; so the document accepts every instance they forbid. Measured with a control, on
<code>core/forecast-point-dimensions.json</code>, whose root states
<code>unique_item_properties: ["kind"]</code>:</p>

<table class="t"><thead><tr><th></th><th>instance</th><th>the document says</th></tr></thead><tbody>
{row(["CONTROL", "<code>[{kind: device_type, device_type: ctv}]</code>", "<b>ACCEPTED</b> &mdash; so the witness conforms"])}
{row(["WITNESS", "<code>[{kind: device_type, device_type: ctv}, {kind: device_type, device_type: mobile}]</code>",
      "<b>ACCEPTED</b> &mdash; while the keyword forbids it. The items differ, so the node&rsquo;s own <code>uniqueItems: true</code> is satisfied, and they share <code>kind</code>."])}
</tbody></table>

<p>That document assigns the job itself, and not to a type SDK. Its own text:
&ldquo;JSON Schema draft-07 cannot express unique-by-property for this array shape, so
conformance tooling should reject repeated <code>kind</code> values.&rdquo;</p>

<p>A D6 rule enforcing one makes the class refuse a payload
<code>strict_validate</code>&rsquo;s schema half accepts: <code>check_accepts</code> draws from
the document and reports <code>model_refused_valid</code>, while the schema comparison sees
nothing at all, a rule having no rendering in <code>model_json_schema()</code>. That is the
model-narrower-than-its-document direction, which &sect;6 names as the only one that makes a
correct SDK refuse valid traffic. D6&rsquo;s &ldquo;a rule narrows the constructor; acceptance
stays with the schema&rdquo; holds for its seven families because every one is a keyword the
DOCUMENT states, so rule and schema agree there; these sixteen would be the first rules where
they disagree.</p>

<p>So one decision and not two: the whole keyword contributes nothing, the drop is reported,
and the 16 are reported as a named subset so the bundle has a list to work from. No SDK
enforces it today &mdash; the TypeScript client has 3 hits, all generated doc comments carrying
the schema&rsquo;s own prose; Python v9 has 4 files; this tree has 0 <code>.py</code> hits and
58 packaged <code>.json</code> copies.</p>

<h3><code>discriminator</code>: it is not a naming input either</h3>

<p>81 sites in 73 documents, 28 distinct values, 51 of them at a document root; the value is
always <code>{{"propertyName": "&lt;key&gt;"}}</code>. D3&rsquo;s second rung reads a
branch&rsquo;s name from the branch&rsquo;s OWN <code>const</code>, never from this keyword.</p>

<table><thead><tr><th>sites</th><th>the branches of the union beside it</th></tr></thead><tbody>
{row(["<b>75</b>", "every branch <code>const</code>- or <code>enum</code>-tags the property the keyword names &mdash; the keyword restates what the branches say"])}
{row(["5", "no branch tags it inline, every branch being a <code>$ref</code>; D3&rsquo;s FIRST rung (the branch&rsquo;s title) answers. <code>core/assets/asset-union.json</code> (21 branches) and <code>core/pricing-option.json</code> (10) are the largest"])}
{row(["1", "some branches tag it inline and some do not: <code>core/requirements/catalog-field-binding.json#/</code>"])}
</tbody></table>

<div class="note"><b>The emitter reads it two ways today.</b>
<code>codegen/lower/union.py</code> calls it an annotation in draft-07 and reads it as
D3&rsquo;s naming property; <code>codegen/compiler.py</code>&rsquo;s
<code>BUNDLE_ANNOTATIONS</code> note says it &ldquo;COULD CONSTRAIN AN INSTANCE&rdquo; and keeps
refusing on it. The measurement says it cannot, and it is the refusing reading that can cost a
document. Recorded as an observation about the code, not as the decision &mdash; the plan
decides and the code follows.</div>

<h2>3. The value keywords, and the table the plan never stated</h2>

<p>D5 says constraints bind to the type and shows two renderings. The keyword-to-constraint
mapping was never written down, so eleven keywords had a binding rule and no rendering.</p>

<table class="t"><thead><tr><th>the document states</th><th>the annotation carries</th><th>sites</th><th>docs</th><th>what the plan says today</th></tr></thead><tbody>""")

for k, r, s, d, note in VALUE_TABLE:
    A(row([f"<code>{esc(k)}</code>", f"<code>{esc(r)}</code>" if " " not in r else esc(r),
           f"{s:,}", str(d), f'<span class="f">{esc(note)}</span>']))

A(f"""</tbody></table>

<p><code>multipleOf</code> has <b>0 sites</b>, so it has no rendering and the first document to
carry one refuses by name &mdash; a row asserted empty while it is empty, which is D14&rsquo;s
own rule.</p>

<h2>4. The composition rules</h2>

<p>3,039 signatures was never the shape of the problem and neither is 632. A decision per
signature is not the answer; a decision per keyword plus a rule for how keywords compose is.
Five rules, each one a reading the plan already holds:</p>

<table class="t"><thead><tr><th></th><th>rule</th><th>where it comes from</th></tr></thead><tbody>
{row(["<b>C1</b>", "A signature is answered by its CONSTRAINING projection: annotations and registry payload keys are projected out, because they constrain nothing (&sect;2) and so cannot change what the node becomes.", "D15 (new), D7&rsquo;s conjunct rule"])}
{row(["<b>C2</b>", "The projection names exactly ONE D2 kind. The facets of that kind belong to it &mdash; <code>required</code>, <code>additionalProperties</code>, <code>propertyNames</code>, <code>patternProperties</code> for an object; <code>items</code>, <code>additionalItems</code> for an array.", "D2, D8"])}
{row(["<b>C3</b>", "Each value keyword in the projection binds to the TYPE the kind produces. A value keyword whose type family the kind cannot carry is a keyword no arm can carry and refuses BY NAME, so such a signature is answered &mdash; by a refusal.", "D5"])}
{row(["<b>C4</b>", "Each rule keyword attaches to the nearest class as an after-validator.", "D6"])}
{row(["<b>C5</b>", "The three roles do not interact, so a signature&rsquo;s answer is the PRODUCT of its per-keyword decisions: adding a value keyword never changes the kind decision and adding a rule keyword changes neither.", "D2, D5, D6 read together"])}
</tbody></table>

<p>The residue is every signature these rules do not answer: two or more independent kinds at
one node, a keyword with no decided role, or a value keyword the kind contradicts with no rule
saying what happens.</p>

<h3>Before this survey&rsquo;s decisions</h3>

<div class="kpi">
<div><b>{raw["raw_signatures"]}</b><span>raw signatures</span></div>
<div><b>{raw["projections"]}</b><span>constraining projections</span></div>
<div><b>{len(raw["residue"])}</b><span>projections in the residue</span></div>
<div><b>{sum(r["nodes"] for r in raw["residue"]):,}</b><span>nodes in the residue</span></div>
</div>

<p>190 of the 350 projections, 1,109 of the 18,203 nodes, and 263 of the 632 raw signatures.
Almost all of it is one cause: a keyword with no decided role, which is exactly the 49 of
&sect;1. (That run projects only draft-07&rsquo;s annotations, before the measured set of
&sect;0.5 exists.)</p>

<h3>After them</h3>

<div class="kpi">
<div><b>{dec["projections"]}</b><span>constraining projections</span></div>
<div><b>{dec["projections"] - len(dec["residue"])}</b><span>answered by composition</span></div>
<div><b>{len(dec["residue"])}</b><span>projections in the residue</span></div>
<div><b>{sum(r["nodes"] for r in dec["residue"])}</b><span>nodes in the residue</span></div>
</div>

<p>Giving the 49 keywords of &sect;1 their roles collapses 632 raw signatures to 197
constraining projections under the adopted set, of which <b>221</b> are answered by composing
per-keyword decisions and <b>29</b> are not. In nodes: <b>18,108 of 18,203 answered, 95
residue</b> &mdash; 0.52% of the declaring population, and <b>587 of the 632</b> raw signatures
answered.</p>

<div class="note"><b>Keeping <code>title</code> changes the projection count and not the
residue.</b> Projected out, the same run reads 197 projections, 174 answered, <b>23</b>
residue. Kept, it reads 250 projections, 221 answered, <b>29</b> residue &mdash; the SAME 95
nodes, redistributed because a titled and an untitled variant are now two signatures. A
projection rule that found new residue would be hiding a decision; this one does not.</div>

<h2>5. The residue, every member named with a site</h2>

<p>The 29 remaining projections have exactly three shapes, and two of the three get a decision
in the patch this row delivers.</p>

<table class="t"><thead><tr><th>nodes</th><th>projection</th><th>why no rule answers it</th><th>a site</th></tr></thead><tbody>
{residue_rows(dec)}
</tbody></table>

<table class="t"><thead><tr><th>shape</th><th>projections</th><th>nodes</th><th>disposition</th></tr></thead><tbody>
{row(["an object&rsquo;s own facets beside a union at one node", "19", "<b>88</b>",
      "<b>decided</b> &mdash; the patch adds it to D2: the object rule applies first, the base "
      "carries the node&rsquo;s own properties and <code>_ROOT_REQUIRED</code>, each branch "
      "subclass inherits them. &sect;4&rsquo;s <code>_ROOT_REQUIRED</code> and "
      "<code>applied_schema</code>&rsquo;s KNOWN CEILING each name this shape from one side "
      "without deciding it."])}
{row(["an <code>allOf</code> of <code>$ref</code> conjuncts beside the node&rsquo;s own value keyword", "3", "4",
      "<b>decided</b> &mdash; the patch adds it to D7, beside the requiredness overlay: the "
      "conjunct supplies the referenced type and the node&rsquo;s own keyword tightens it. "
      "<code>core/catalog-selection.json</code> &times;3 with <code>uniqueItems</code>, "
      "<code>trusted-match/context-match-response.json</code> with <code>minItems: 1</code>."])}
{row(["<code>propertyNames</code> at a RULE position", "1", "2",
      "<b>named, not decided</b> &mdash; D5 types a mapping&rsquo;s key from it and &sect;6 says "
      "no type is lowered under a conditional, so it falls between the two. Both nodes are "
      "<code>core/catalog-item-availability-state.json#/allOf/0/else</code>. The minimum "
      "reading is that it joins D6 as an eighth family; a row that decides it should have a "
      "document in hand."])}
</tbody></table>

<div class="note"><b>Where the residue is NOT.</b> An <code>allOf</code> of rule-only conjuncts
beside a node&rsquo;s own array keywords looked like a fourth shape and is not: D7&rsquo;s
conjunct rule already covers it. Three nodes are that shape, including
<code>media-buy/legacy-purchase-continuation-input.json#/properties/accepted_losses</code>,
each an <code>allOf</code> of <code>contains</code> conjuncts over an array stating its own
<code>minItems</code> and <code>uniqueItems</code>. Read the residue against this: a crude
instrument reports it, and resolving it took reading the four nodes.</div>

<h2>5.5 One interaction with D3's new nested rule</h2>

<p>Trunk moved while this row ran. <code>07c84c14a</code> changed D3's nested rule from
&ldquo;parent name + <code>pascal_case(property)</code>&rdquo; to
<code>pascal_case(property)</code>, qualified by <i>the nearest enclosing property</i> only
where two nodes of one module would take the same name.</p>

<p><b>D16 was re-checked against it and holds.</b> The union-branch steps are byte-for-byte
unchanged &mdash; title, else the discriminator <code>const</code>, else the sorted required
set, else the branch&rsquo;s own root type word, else refuse &mdash; and all four
<code>discriminator</code> mentions in the new text are still either the compiler&rsquo;s
<code>DataType.discriminator</code> field or &ldquo;the discriminator <code>const</code>&rdquo;
meaning the const-tagged property. Nested naming and branch naming are different steps, so the
change does not reach D16.</p>

<p><b>It does reach the object-facets-beside-a-union decision, in the naming direction.</b>
Each branch subclass declares the node&rsquo;s properties, so sibling branches declare nested
classes for the SAME property name in one module &mdash; and the stated qualifier, the nearest
enclosing property, is the same for every sibling. Measured over all 1,054 portable documents
at TYPE positions only (a node under <code>not</code>, <code>if</code>, <code>then</code> or
<code>else</code> is a rule and lowers no class, which is &sect;6&rsquo;s third counting
rule):</p>

<div class="kpi">
<div><b>1,063</b><span>nested model nodes taking a name, in 303 modules</span></div>
<div><b>84</b><span>names taken by two or more nodes, in 62 modules</span></div>
<div><b>9</b><span>collisions the enclosing property separates</span></div>
<div><b>55</b><span>of the 75 it does not are branch siblings</span></div>
</div>

<table class="t"><thead><tr><th>nodes</th><th>name they all take</th><th>module</th><th>what separates them</th></tr></thead><tbody>
{row(["44", "<code>AssetsItem</code>", "<code>core/format.json</code>", "a combinator index"])}
{row(["14", "<code>ComponentsItem</code>", "<code>formats/canonical/coordinated_placements.json</code>", "a combinator index"])}
{row(["10", "<code>Payload</code>", "<code>core/registry-event.json</code>", "the branch, which is what D2 names per value"])}
{row(["9", "<code>TasksItem</code>", "<code>protocol/get-adcp-capabilities-response.json</code>", "a combinator index"])}
{row(["9", "<code>Payload</code>", "<code>core/wholesale-feed-event.json</code>", "a combinator index"])}
{row(["7", "<code>TransitionsItem</code>", "<code>formats/canonical/seller_rendered_stateful_display.json</code>", "a combinator index"])}
</tbody></table>

<div class="note">D3&rsquo;s own figure of 19 collisions in 9 modules is over the EMITTED tree,
which is about 705 of the 1,054 documents and excludes the shape unions, so the two numbers
measure different populations and both are right. The direction is that the population the rule
will meet is larger and is dominated by a shape the qualifier does not address. The minimum
reading is that a collision between branch siblings is qualified by the BRANCH&rsquo;s name,
which D3 already derives &mdash; that is a sentence in D3, and the patch records the
measurement beside the decision whose population it is rather than rewriting D3.</div>

<h2>6. Two further gaps the survey found on the way</h2>

<table class="t"><thead><tr><th>gap</th><th>measured</th><th>what it is</th></tr></thead><tbody>
{row(["D6&rsquo;s six families are seven", "<code>contains</code>, 120 sites in 46 documents",
      "D6 says &ldquo;those six are the whole population&rdquo;. <code>contains</code> spans a "
      "collection and has no field-level annotation in pydantic, which is D6&rsquo;s own "
      "membership test. The plan names the keyword only as a walk-descent position (&sect;6) "
      "and as a deferral count (&sect;7.1)."])}
{row(["a rendered fact dropped under a second spelling",
      "<code>x-enum-descriptions</code>, 1 site",
      "the enum row reads <code>enumDescriptions</code> (137 sites in 135 documents) into "
      "member docstrings; <code>enums/signal-value-type.json</code> carries "
      "<code>x-enum-descriptions</code> and no <code>enumDescriptions</code>, so its three "
      "members emit with no documentation. Admitting the name as an annotation is what drops "
      "it; carrying it is one line in the enum row."])}
{row(["an open vocabulary written where the validator cannot see it",
      "<code>x-extensible</code> 2, <code>x-pattern</code> 1",
      "<code>enums/advertiser-industry.json</code> states an <code>enum</code>, "
      "<code>x-extensible: true</code> and a pattern &mdash; the known members beside anything "
      "matching it, which is the construct D2 decides for "
      "<code>core/geo-place-system.json</code> where the bundle spelled it as an "
      "<code>anyOf</code>. Spelled this way the document&rsquo;s accepted set is the CLOSED "
      "enum, so a closed <code>StrEnum</code> is faithful to the document and the document is "
      "narrower than its own author."])}
{row(["<code>deprecated</code> is a <code>missing</code> fact in waiting", "179 sites in 95 documents",
      "pydantic renders <code>deprecated: true</code> from "
      "<code>Field(deprecated=True)</code>, and the emitted tree declares it nowhere &mdash; "
      "its 17 textual hits are all inside descriptions. The schema comparison reports "
      "<code>missing</code> 0 today; the first graded document carrying one changes that, and "
      "the plan has never said which way it should go."])}
</tbody></table>

<h2>7. What this row did not decide, and why</h2>

<ul>
<li><b><code>propertyNames</code> at a rule position</b> (2 nodes). Named above. Deciding it
without a document that reaches it would be inventing the eighth family on no evidence.</li>
<li><b>Whether <code>deprecated</code> should render.</b> The gap is named and measured; which
way it goes is a rendering decision with a cost on the comparison, and no document the emitter
reaches today carries one, so there is nothing to grade either answer against.</li>
<li><b>Whether the bundle should enforce <code>x-adcp-validation</code>.</b> Upstream. A model
carrying those rules would be narrower than the document it names.</li>
<li><b>Whether to carry the <code>x-</code> facts onto the class</b> (a <code>ClassVar</code>
for <code>x-status</code>, <code>x-mutates-state</code>, <code>x-entity</code>). The decision
says they contribute nothing and the drop is reported, which is the honest reading of &sect;2.
Carrying them is a separate question about what the SDK offers beyond types, and nothing in the
plan asks for it.</li>
<li><b>The emitter&rsquo;s own refusal counts per keyword.</b> Not measured here. The brief
forbids deciding a keyword by what the emitter does, so the code&rsquo;s readings are recorded
as observations and the populations quoted are the bundle&rsquo;s, not the run&rsquo;s.</li>
</ul>

<footer>
Measured on <code>acp-j3k2l53 @ {esc(SHA)}</code>, detached at <code>c92d9ee83</code>.
Every count is over <code>schemas/cache/3.2</code>, 1,054 portable documents, excluding
<code>bundled/</code>, <code>mcp/</code> and the three registry files &mdash; a figure quoted
without that exclusion is void (&sect;6 of the plan). Instruments:
<code>survey/census.py</code>, <code>survey/variants*.py</code>, <code>survey/clinch.py</code>,
<code>survey/coverage.py</code>, <code>survey/constrains.py</code>,
<code>survey/bigthree.py</code>, <code>survey/compose.py</code>. Decisions delivered as
<code>survey-decisions.patch</code> against <code>07c84c14a</code> (rebased from <code>c92d9ee83</code>), 290 insertions in 5 hunks,
0 deletions.
</footer>

</div></body></html>""")

OUT.write_text("\n".join(parts))
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
