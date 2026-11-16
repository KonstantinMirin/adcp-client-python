"""Contract for generated types whose JSON Schema root is a scalar.

A schema like ``core/property-tag.json`` — ``{"type": "string", "pattern":
"^[a-z0-9_]+$"}`` — describes a value. ``datamodel-code-generator`` emits
``RootModel[str]`` for it, which is not a ``str`` anywhere Python treats one:
``str(x)`` renders ``"root='sports'"``, ``x == "sports"`` is ``False``, and
``{x} & {"sports"}`` raises ``TypeError: unhashable type``. Four reports in
eight months (#138, #145, #155, #1077, #1086, #1087) were each fixed by
patching individual instances, and the construct came back somewhere else.

This emission answers that at the source rather than by rewriting afterwards:
``rebuild-plan.md`` §4 compiles *a scalar at a root* to **a module-level
annotated alias, not a class**, so ``PropertyTag`` IS ``Annotated[str, ...]``
and a validated value is a plain ``str``. These tests hold both halves of that
line: a scalar root is its Python scalar everywhere Python looks at one, and
the document's constraints are still enforced -- at a field, and at the alias
module's own ``strict_validate``.

See: https://github.com/adcontextprotocol/adcp-client-python/issues/1277
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from adcp.types._scalar import ScalarFloat, ScalarInt, ScalarStr
from adcp.validation.version import resolve_bundle_key

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GENERATED_DIR = _REPO_ROOT / "src" / "adcp" / "types" / "domains"
_BUNDLE_KEY = resolve_bundle_key((_REPO_ROOT / "src" / "adcp" / "ADCP_VERSION").read_text().strip())
_SCHEMA_DIR = _REPO_ROOT / "schemas" / "cache" / _BUNDLE_KEY

_SCALAR_BASES = (ScalarStr, ScalarInt, ScalarFloat)


def _generated_scalar_roots() -> dict[str, type]:
    """Every exported generated type that is now a scalar subclass."""
    from adcp.types import _generated as gen

    return {
        name: obj
        for name in dir(gen)
        if isinstance(obj := getattr(gen, name), type) and issubclass(obj, _SCALAR_BASES)
    }


# ---------------------------------------------------------------------------
# The ratchet: no scalar root may regress to a RootModel wrapper
# ---------------------------------------------------------------------------


def test_no_scalar_rootmodels_remain_in_generated_tree() -> None:
    """No generated class wraps a bare ``str``/``int``/``float`` in a RootModel.

    This is the guard that keeps the fix from eroding. ``rewrite_scalar_rootmodels``
    reports — rather than rewrites — any scalar root it does not recognize, so a
    new schema shape lands here as a failure instead of as a quietly broken type.
    """
    offenders: list[str] = []
    wrapped = {"RootModel[str]", "RootModel[int]", "RootModel[float]"}

    for path in sorted(_GENERATED_DIR.rglob("*.py")):
        source = path.read_text()
        if "RootModel[" not in source:
            continue
        for node in ast.walk(ast.parse(source)):
            if not isinstance(node, ast.ClassDef) or len(node.bases) != 1:
                continue
            base = ast.get_source_segment(source, node.bases[0])
            if base in wrapped:
                offenders.append(f"{path.relative_to(_GENERATED_DIR)}::{node.name}")

    assert offenders == [], (
        "These generated classes wrap a scalar in a RootModel, so they are not "
        "their own Python scalar. Teach scripts/post_generate_fixes.py's "
        f"_scalar_root_spec() to handle their shape: {offenders}"
    )


# ---------------------------------------------------------------------------
# The three reproductions from the issue
# ---------------------------------------------------------------------------


def test_scalar_str_root_is_a_str() -> None:
    """``PropertyTag`` is a ``str``: isinstance, ``str()``, and f-strings."""
    from adcp import PropertyTag

    tag = PropertyTag("sports")

    assert isinstance(tag, str)
    assert str(tag) == "sports"
    assert f"{tag}" == "sports"
    assert tag.upper() == "SPORTS"
    assert json.dumps({"tag": tag}) == '{"tag": "sports"}'


def test_scalar_str_root_equals_a_bare_str() -> None:
    """Equality holds in both directions against a plain ``str``."""
    from adcp import PropertyTag

    tag = PropertyTag("sports")

    assert tag == "sports"
    assert "sports" == tag
    assert tag != "news"
    assert PropertyTag("sports") == PropertyTag("sports")


def test_scalar_str_root_is_hashable_and_set_compatible() -> None:
    """Hashing matches the wrapped value, so sets and dicts interoperate."""
    from adcp import PropertyTag

    tag = PropertyTag("sports")

    assert hash(tag) == hash("sports")
    assert {tag} & {"sports"} == {"sports"}
    assert {"sports": 1}[tag] == 1
    assert len({PropertyTag("sports"), "sports"}) == 1


def test_geo_include_exclude_overlap_is_detectable() -> None:
    """The production consequence from #1277: a set intersection over geo targeting.

    ``TargetingOverlay.geo_countries`` is ``list[GeoCountry]`` and detecting an
    include/exclude overlap is a set intersection. While ``GeoCountry`` was a
    ``RootModel``, that raised ``TypeError: unhashable type``, which escaped the
    typed validation path and turned a correctable ``INVALID_REQUEST`` into an
    ``INTERNAL_ERROR`` on a field the buyer controls.
    """
    from adcp.types import TargetingOverlay

    overlay = TargetingOverlay.model_validate(
        {"geo_countries": ["US", "CA"], "geo_countries_exclude": ["US"]}
    )
    assert overlay.geo_countries is not None
    assert overlay.geo_countries_exclude is not None

    overlap = set(overlay.geo_countries) & set(overlay.geo_countries_exclude)

    assert overlap == {"US"}


def test_numeric_scalars_arrive_as_their_numbers_on_a_field() -> None:
    """A constrained numeric alias puts a plain ``float``/``int`` on the instance.

    ``pricing-options/cpv-option.json``'s ``view_threshold`` is a two-branch
    ``oneOf`` whose number branch is ``{"type": "number", "minimum": 0,
    "maximum": 1}``; §4 names that constraint in words and the surface binds it
    as ``adcp.types.constraints.FloatMin0Max1``. Nothing wraps the value, so
    arithmetic and comparison against a plain number work.

    What stood here built ``ViewThreshold(0.5)`` and ``gen.MajorVersion(3)``, the
    ``ScalarFloat``/``ScalarInt`` subclasses ``post_generate_fixes`` emitted;
    neither name nor that script exists in this emission.
    """
    from adcp.types._schemas.pricing_options.cpv_option import Parameters

    threshold = Parameters(view_threshold=0.5).view_threshold
    assert type(threshold) is float
    assert threshold == 0.5
    assert threshold * 2 == 1.0

    seconds = Parameters(view_threshold={"duration_seconds": 3}).view_threshold.duration_seconds
    assert type(seconds) is int
    assert seconds + 1 == 4
    assert {seconds} & {3} == {3}


# ---------------------------------------------------------------------------
# Validation survives the rewrite
# ---------------------------------------------------------------------------


def test_the_alias_s_two_validating_sites_enforce_the_pattern_and_the_type() -> None:
    """D2: a scalar root is an alias, so the validation is at a FIELD and at `strict_validate`.

    rebuild-plan §4, "What becomes what": *a scalar at a root* emits *"a
    module-level annotated alias, not a class"*, and *"A root scalar is an alias,
    so it has no class to carry ``strict_validate``; its module binds the same
    validation as a module-level function over the same schema reference, so a
    class and an alias cannot disagree about what their document accepts."*

    So there is no constructor to refuse at: ``PropertyTag("Invalid-Tag")`` is
    ``str("Invalid-Tag")``.  The three tests that stood here --
    ``PropertyTag("Invalid-Tag")``, ``PropertyTag(5)`` and ``PropertyTag()`` --
    graded the ``str`` subclass ``post_generate_fixes.rewrite_scalar_rootmodels``
    emitted, which this emission does not produce.  Both sites the alias DOES
    have are graded here.  The rest of this file still reads the subclass -- it
    asks an alias for ``isinstance``, ``__slots__`` and a deprecated ``root``
    keyword -- and that is a wider repair than this one.
    """
    from adcp import PropertyTag
    from adcp.types._schemas.core.property_tag import strict_validate

    class Holder(BaseModel):
        tag: PropertyTag

    for bad, expected in (("Invalid-Tag", "string_pattern_mismatch"), (5, "string_type")):
        with pytest.raises(ValidationError) as excinfo:
            Holder(tag=bad)
        assert excinfo.value.errors()[0]["type"] == expected

        with pytest.raises(ValidationError) as strict:
            strict_validate(bad)
        assert strict.value.errors()[0]["type"] in ("pattern", "type")

    assert strict_validate("sports") == "sports"


def test_the_field_enforces_the_numeric_bounds() -> None:
    """``minimum``/``maximum`` still reject out-of-range numbers, at the FIELD.

    Same reading as the test above it: a constrained scalar is an alias, so
    there is no constructor to refuse at and the refusal is the field's. Both
    bounds the document states are graded, and the sibling object branch is what
    the second error of each pair reports.
    """
    from adcp.types._schemas.pricing_options.cpv_option import Parameters

    for out_of_range, keyword in ((1.5, "less_than_equal"), (-0.1, "greater_than_equal")):
        with pytest.raises(ValidationError) as raised:
            Parameters(view_threshold=out_of_range)
        assert [error["type"] for error in raised.value.errors()] == [keyword, "model_type"]

    with pytest.raises(ValidationError):
        Parameters(view_threshold={"duration_seconds": 0})




# ---------------------------------------------------------------------------
# Behaviour inside a Pydantic model
# ---------------------------------------------------------------------------


def test_model_field_validates_coerces_and_round_trips() -> None:
    """A scalar root used as a model field validates, dumps, and reloads."""
    from adcp import PropertyTag

    class Holder(BaseModel):
        tag: PropertyTag
        tags: list[PropertyTag] = []

    holder = Holder.model_validate({"tag": "sports", "tags": ["news", "ctv"]})

    # `PropertyTag` is an alias, so it is not a second type to be an instance of:
    # the validated value is the document's own `type: string`.
    assert type(holder.tag) is str
    assert holder.tag == "sports"
    assert holder.tags == ["news", "ctv"]

    # The wire form is a bare string, both in Python and JSON mode.
    assert holder.model_dump() == {"tag": "sports", "tags": ["news", "ctv"]}
    assert type(holder.model_dump()["tag"]) is str
    assert json.loads(holder.model_dump_json()) == {"tag": "sports", "tags": ["news", "ctv"]}
    assert Holder.model_validate_json(holder.model_dump_json()) == holder

    with pytest.raises(ValidationError):
        Holder.model_validate({"tag": "Not A Tag"})


def test_model_field_preserves_instance_identity() -> None:
    """A typed value composes into a field without a round trip.

    ``RootModel`` defaulted to ``revalidate_instances="never"``, so composing an
    already-built value kept its identity. Adopters rely on that when they build
    a capability model out of public scalars — see
    ``tests/test_composability_invariant.py``.
    """
    from adcp import PropertyTag

    class Holder(BaseModel):
        tag: PropertyTag
        tags: list[PropertyTag] = []

    tag = PropertyTag("sports")
    holder = Holder(tag=tag, tags=[tag])

    assert holder.tag is tag
    assert holder.tags[0] is tag


def test_json_schema_matches_the_source_schema() -> None:
    """The emitted JSON Schema carries the schema's own keywords, less two.

    `rebuild-plan.md` §5's keyword grid states where `title` and `examples` go,
    and it is neither of them:

    * `title` -- "ROOT -> the symbol. ... Never rendered." The document's
      "Property Tag" IS the name `PropertyTag`, so re-rendering it as a keyword
      would be the same fact twice.
    * `examples` -- "Nothing on the model. The accepts check replays every one,
      at every position", which is where they are graded.

    What stood here asserted both keywords back onto the emitted schema.
    """
    from adcp import PropertyTag

    source = json.loads((_SCHEMA_DIR / "core" / "property-tag.json").read_text())
    generated = TypeAdapter(PropertyTag).json_schema()

    assert generated == {
        "type": "string",
        "pattern": source["pattern"],
        "description": source["description"],
    }
    assert source["title"] == "Property Tag"  # -> the symbol `PropertyTag`
    assert source["examples"]  # replayed by the accepts check, not rendered here


# ---------------------------------------------------------------------------
# The RootModel call sites have no shim to grade
#
# ``PropertyTag(root=...)``, ``instance.root`` and the "not both" conflict were
# the three compatibility shims ``ScalarStr`` carried for code written against
# the ``RootModel`` wrapper. A scalar root is an alias in this emission --
# ``PropertyTag`` IS ``Annotated[str, ...]`` -- so there is no class on which a
# shim could live and no deprecation for one to raise. The three tests that
# stood here graded that class and are removed rather than adapted.
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# The whole population, not just the sample above
# ---------------------------------------------------------------------------


def test_every_scalar_root_example_round_trips() -> None:
    """Where the schema supplies examples, each one constructs and compares equal.

    Exercises the real constraints of every scalar root that documents a value,
    so a mis-translated ``pattern`` or bound shows up as a rejected example.
    """
    failures: list[str] = []
    for name, cls in sorted(_generated_scalar_roots().items()):
        for example in cls._json_schema_extra.get("examples", ()):
            if not isinstance(example, cls._scalar_type):
                continue  # schema example of another type; the field tests cover those
            try:
                built = cls(example)
            except ValidationError as exc:
                failures.append(f"{name}({example!r}) rejected its own example: {exc}")
                continue
            if built != example or cls._scalar_type(built) != example:
                failures.append(f"{name}({example!r}) != {example!r}")

    assert failures == [], "\n".join(failures)


def test_scalar_root_takes_no_arbitrary_attributes() -> None:
    """``__slots__`` keeps a schema value closed, as the RootModel wrapper was.

    Without ``__slots__`` on the generated subclass it regains a ``__dict__``
    and silently accepts any attribute.
    """
    from adcp import PropertyTag

    tag = PropertyTag("sports")

    with pytest.raises(AttributeError):
        tag.workflow_id = "wf-42"


def test_scalar_root_survives_copy_and_pickle() -> None:
    """The classic str-subclass hazards: both reconstruct through ``__new__``."""
    import copy
    import pickle

    from adcp import PropertyTag

    tag = PropertyTag("sports")

    assert copy.deepcopy(tag) == tag
    restored = pickle.loads(pickle.dumps(tag))
    assert restored == tag
