# Canonical creative format-kind validation

SDK 9 preserves `format_kind` as a string on creative and manifest models,
including values introduced after the SDK's bundled vocabulary. Known strings
also remain strings. Replace enum identity comparisons with string equality:

```python
if creative.format_kind == "image":
    handle_image(creative)
```

`CanonicalFormatKind` remains available as a vocabulary enum, and
`is_canonical_format_kind(value)` checks membership in the bundled vocabulary.
It returns a boolean; do not install that predicate directly as a Pydantic
`AfterValidator`, which must return the validated value.

## Opt into a closed application vocabulary

Use `CanonicalFormatKindStr` on application fields that must accept only the
bundled canonical kinds. It returns the original string and raises a validation
error for an unknown kind. It composes with nullable and list annotations:

```python
from pydantic import BaseModel, Field
from adcp.types import CanonicalFormatKindStr

class CreativeSelection(BaseModel):
    format_kind: CanonicalFormatKindStr
    fallback_kind: CanonicalFormatKindStr | None = None
    accepted_kinds: list[CanonicalFormatKindStr] = Field(default_factory=list)
```

For a deployment-specific vocabulary, `require_canonical_format_kind` builds a
validator and snapshots the supplied iterable so it can be reused safely:

```python
from typing import Annotated
from pydantic import AfterValidator
from adcp.types import require_canonical_format_kind

SellerKind = Annotated[
    str, AfterValidator(require_canonical_format_kind(("image", "video")))
]
```

These helpers are optional application validation. The SDK's creative models
continue to preserve unknown strings, and a versioned wire schema remains the
authority for protocol validation. A seller must also check a chosen kind
against the selected product's declared `format_options`; use
`validate_format_kind_in_options` at that application decision point.

Adopter-defined formats can use `custom` with a corresponding declaration's
`format_shape` and `format_schema`. Choose it when the creative satisfies that
contract, rather than changing an unknown value to `custom` without validation.
