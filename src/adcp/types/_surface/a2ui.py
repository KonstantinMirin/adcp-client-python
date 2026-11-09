"""The exports of the ``a2ui`` domain, as the compiler aggregates them.

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

from .._schemas.a2ui.bound_value import A2UIBoundValue as A2UIBoundValue
from .._schemas.a2ui.bound_value import A2UIBoundValueLiteralBoolean as A2UIBoundValueLiteralBoolean
from .._schemas.a2ui.bound_value import A2UIBoundValueLiteralNumber as A2UIBoundValueLiteralNumber
from .._schemas.a2ui.bound_value import A2UIBoundValueLiteralString as A2UIBoundValueLiteralString
from .._schemas.a2ui.bound_value import A2UIBoundValueLiteralStringPath as A2UIBoundValueLiteralStringPath
from .._schemas.a2ui.bound_value import A2UIBoundValuePath as A2UIBoundValuePath
from .._schemas.a2ui.component import A2UIComponent as A2UIComponent
from .._schemas.a2ui.component import ComponentValue as ComponentValue
from .._schemas.a2ui.si_catalog import ComponentsItem as SIComponentCatalogComponentsItem
from .._schemas.a2ui.si_catalog import SIComponentCatalog as SIComponentCatalog
from .._schemas.a2ui.surface import A2UISurface as A2UISurface
from .._schemas.a2ui.user_action import A2UIUserAction as A2UIUserAction
from .._schemas.a2ui.user_action import Action as A2UIUserActionAction

__all__ = [
    'A2UIBoundValue',
    'A2UIBoundValueLiteralBoolean',
    'A2UIBoundValueLiteralNumber',
    'A2UIBoundValueLiteralString',
    'A2UIBoundValueLiteralStringPath',
    'A2UIBoundValuePath',
    'A2UIComponent',
    'A2UISurface',
    'A2UIUserAction',
    'A2UIUserActionAction',
    'ComponentValue',
    'SIComponentCatalog',
    'SIComponentCatalogComponentsItem',
]
