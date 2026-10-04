# Generated-types delta

## Field changes

- `core/catalog.py`
  - **classes removed**: Category, Gtins, Ids, Query, Tags, Type
- `core/catalog_selection.py`
  - `Gtin`: `+__slots__`, `+_constraints` `-root`
- `core/delivery_metrics.py`
  - **classes added**: DoohMetrics1, Viewability1
  - **classes removed**: DoohMetrics, Viewability
- `core/package_delivery_metric_value.py`
  - `PackageDeliveryMetricValue`: `-clicks`, `-completed_views`, `-conversion_value`, `-conversions`, `-impressions`, `-measurable_impressions`, `-metric_id`, `-scope`, `-spend`, `-value`, `-viewable_impressions`
- `core/product_offer_filters.py`
  - **classes added**: GeoProximityItem, Geometry, Radius, TravelTime, Type
- `core/targeting.py`
  - **classes removed**: AudienceExclude, AudienceInclude, AxeExcludeSegment, AxeIncludeSegment, Browser, BrowserExclude, DaypartTargets, DevicePlatform, DevicePlatformExclude, DeviceType, DeviceTypeExclude, GeoCountries, GeoCountriesExclude, GeoMetrosExclude, GeoPlaces, GeoPlacesExclude, GeoPostalAreas, GeoPostalAreasExclude, GeoProximity, GeoProximityItem2, GeoRegions, GeoRegionsExclude, PlacementSelection, StoreCatchments
- `core/targeting_input.py`
  - **classes removed**: AgeRestriction
  - `GeoCountry`: `+__slots__`, `+_constraints` `-root`
  - `GeoRegion`: `+__slots__`, `+_constraints` `-root`
- `core/version_envelope.py`
  - **classes removed**: AdcpMajorVersion, AdcpVersion
- `error_details/vast_version_mismatch.py`
  - **classes removed**: ObservedDocumentVastVersion
- `media_buy/product_purchase.py`
  - **classes removed**: AgencyEstimateNumber, AudienceEvidencePins, Budget, CatalogIds, DailyBudgetCap, EndTime, FormatOptionRefs, MinSpendTarget, OptimizationGoals, Pacing, PerformanceStandards, StartTime
- `media_buy/product_purchase_input.py`
  - `CatalogId`: `+__slots__`, `+_constraints` `-root`
