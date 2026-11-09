"""The exports of the ``registries`` domain, as the compiler aggregates them.

Every name here is the class, root model, enumeration or alias the schema document
of that name compiles to, re-exported from the private module at the document's own
path.  The object is the same one the runtime validates into -- ``isinstance``
against a union branch imported from here is true.

Generated from the compiler's own record of what it exported: every document ROOT,
every union BRANCH and every type ALIAS the documents of this domain declare.  A
document added upstream appears here with nothing edited.

**NOT the path a consumer writes.**  This file is the compiler's outright and is
compared byte for byte, so that the domain's PUBLIC module can compose it in one
line and serve a hand-written name set beside it where the domain's word is also a
word upstream kept machinery under.  The public module is the one import path for
every name here.
"""

from __future__ import annotations

from .._schemas.registries.v1_canonical_mapping import V2 as V1V2CanonicalFormatMappingRegistryMappingsItemV2
from .._schemas.registries.v1_canonical_mapping import (
    Dimensions as V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructuralDimensions,
)
from .._schemas.registries.v1_canonical_mapping import MappingsItem as V1V2CanonicalFormatMappingRegistryMappingsItem
from .._schemas.registries.v1_canonical_mapping import (
    ParameterMappingsItem as V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItem,
)
from .._schemas.registries.v1_canonical_mapping import (
    Structural as V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructural,
)
from .._schemas.registries.v1_canonical_mapping import (
    Transform as V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItemTransform,
)
from .._schemas.registries.v1_canonical_mapping import V1PatternFormatIdGlob as V1PatternFormatIdGlob
from .._schemas.registries.v1_canonical_mapping import V1PatternStructural as V1PatternStructural
from .._schemas.registries.v1_canonical_mapping import (
    V1V2CanonicalFormatMappingRegistry as V1V2CanonicalFormatMappingRegistry,
)

__all__ = [
    'V1PatternFormatIdGlob',
    'V1PatternStructural',
    'V1V2CanonicalFormatMappingRegistry',
    'V1V2CanonicalFormatMappingRegistryMappingsItem',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructural',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV1PatternStructuralStructuralDimensions',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV2',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItem',
    'V1V2CanonicalFormatMappingRegistryMappingsItemV2ParameterMappingsItemTransform',
]
