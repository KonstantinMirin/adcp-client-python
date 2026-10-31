"""The public types of the ``collection`` domain.

Every name here is the class, root model, enumeration or alias the schema document
of that name compiles to, re-exported from the private module at the document's own
path.  This is the one import path for each of them, and the object is the same one
the runtime validates into -- ``isinstance`` against a union branch imported from
here is true.

Generated from the compiler's own record of what it exported: every document ROOT,
every union BRANCH and every type ALIAS the documents of this domain declare.  A
document added upstream appears here with nothing edited.
"""

from __future__ import annotations

from ._schemas.collection.base_collection_source import (
    BaseCollectionSource as BaseCollectionSource,
    DistributionIDsSource as DistributionIDsSource,
    PublisherCollectionsSource as PublisherCollectionsSource,
    PublisherGenresSource as PublisherGenresSource,
)
from ._schemas.collection.collection_list import (
    CollectionList as CollectionList,
)
from ._schemas.collection.collection_list_changed_webhook import (
    CollectionListChangedWebhook as CollectionListChangedWebhook,
)
from ._schemas.collection.collection_list_filters import (
    CollectionListFilters as CollectionListFilters,
)
from ._schemas.collection.create_collection_list_request import (
    CreateCollectionListRequest as CreateCollectionListRequest,
)
from ._schemas.collection.create_collection_list_response import (
    CreateCollectionListResponse as CreateCollectionListResponse,
)
from ._schemas.collection.delete_collection_list_request import (
    DeleteCollectionListRequest as DeleteCollectionListRequest,
)
from ._schemas.collection.delete_collection_list_response import (
    DeleteCollectionListResponse as DeleteCollectionListResponse,
)
from ._schemas.collection.get_collection_list_request import (
    GetCollectionListRequest as GetCollectionListRequest,
)
from ._schemas.collection.get_collection_list_response import (
    CoverageGapsValueItem as CoverageGapsValueItem,
    GetCollectionListResponse as GetCollectionListResponse,
)
from ._schemas.collection.list_collection_lists_request import (
    ListCollectionListsRequest as ListCollectionListsRequest,
)
from ._schemas.collection.list_collection_lists_response import (
    ListCollectionListsResponse as ListCollectionListsResponse,
)
from ._schemas.collection.update_collection_list_request import (
    UpdateCollectionListRequest as UpdateCollectionListRequest,
)
from ._schemas.collection.update_collection_list_response import (
    UpdateCollectionListResponse as UpdateCollectionListResponse,
)

__all__ = [
    'BaseCollectionSource',
    'CollectionList',
    'CollectionListChangedWebhook',
    'CollectionListFilters',
    'CoverageGapsValueItem',
    'CreateCollectionListRequest',
    'CreateCollectionListResponse',
    'DeleteCollectionListRequest',
    'DeleteCollectionListResponse',
    'DistributionIDsSource',
    'GetCollectionListRequest',
    'GetCollectionListResponse',
    'ListCollectionListsRequest',
    'ListCollectionListsResponse',
    'PublisherCollectionsSource',
    'PublisherGenresSource',
    'UpdateCollectionListRequest',
    'UpdateCollectionListResponse',
]
