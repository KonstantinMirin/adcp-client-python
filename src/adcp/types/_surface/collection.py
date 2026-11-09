"""The exports of the ``collection`` domain, as the compiler aggregates them.

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

from .._schemas.collection.base_collection_source import BaseCollectionSource as BaseCollectionSource
from .._schemas.collection.base_collection_source import DistributionIDsSource as DistributionIDsSource
from .._schemas.collection.base_collection_source import IdentifiersItem as DistributionIDsSourceIdentifiersItem
from .._schemas.collection.base_collection_source import PublisherCollectionsSource as PublisherCollectionsSource
from .._schemas.collection.base_collection_source import PublisherGenresSource as PublisherGenresSource
from .._schemas.collection.collection_list import CollectionList as CollectionList
from .._schemas.collection.collection_list_changed_webhook import (
    ChangeSummary as CollectionListChangedWebhookChangeSummary,
)
from .._schemas.collection.collection_list_changed_webhook import (
    CollectionListChangedWebhook as CollectionListChangedWebhook,
)
from .._schemas.collection.collection_list_filters import CollectionListFilters as CollectionListFilters
from .._schemas.collection.create_collection_list_request import (
    CreateCollectionListRequest as CreateCollectionListRequest,
)
from .._schemas.collection.create_collection_list_response import (
    CreateCollectionListResponse as CreateCollectionListResponse,
)
from .._schemas.collection.delete_collection_list_request import (
    DeleteCollectionListRequest as DeleteCollectionListRequest,
)
from .._schemas.collection.delete_collection_list_response import (
    DeleteCollectionListResponse as DeleteCollectionListResponse,
)
from .._schemas.collection.get_collection_list_request import GetCollectionListRequest as GetCollectionListRequest
from .._schemas.collection.get_collection_list_request import ObjMaxResultsCursor as GetCollectionListRequestPagination
from .._schemas.collection.get_collection_list_response import (
    CollectionsItem as GetCollectionListResponseCollectionsItem,
)
from .._schemas.collection.get_collection_list_response import GetCollectionListResponse as GetCollectionListResponse
from .._schemas.collection.list_collection_lists_request import ListCollectionListsRequest as ListCollectionListsRequest
from .._schemas.collection.list_collection_lists_response import (
    ListCollectionListsResponse as ListCollectionListsResponse,
)
from .._schemas.collection.update_collection_list_request import (
    UpdateCollectionListRequest as UpdateCollectionListRequest,
)
from .._schemas.collection.update_collection_list_response import (
    UpdateCollectionListResponse as UpdateCollectionListResponse,
)

__all__ = [
    'BaseCollectionSource',
    'CollectionList',
    'CollectionListChangedWebhook',
    'CollectionListChangedWebhookChangeSummary',
    'CollectionListFilters',
    'CreateCollectionListRequest',
    'CreateCollectionListResponse',
    'DeleteCollectionListRequest',
    'DeleteCollectionListResponse',
    'DistributionIDsSource',
    'DistributionIDsSourceIdentifiersItem',
    'GetCollectionListRequest',
    'GetCollectionListRequestPagination',
    'GetCollectionListResponse',
    'GetCollectionListResponseCollectionsItem',
    'ListCollectionListsRequest',
    'ListCollectionListsResponse',
    'PublisherCollectionsSource',
    'PublisherGenresSource',
    'UpdateCollectionListRequest',
    'UpdateCollectionListResponse',
]
