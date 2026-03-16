"""Client for the AdCP registry API (brand, property, member, and policy lookups)."""

from __future__ import annotations

import asyncio
import re
from typing import Any

import httpx
from pydantic import ValidationError

from adcp.exceptions import RegistryError
from adcp.types.core import (
    Member,
    Policy,
    PolicyHistory,
    PolicySummary,
    ResolvedBrand,
    ResolvedProperty,
)

DEFAULT_REGISTRY_URL = "https://agenticadvertising.org"
MAX_BULK_DOMAINS = 100
MAX_BULK_POLICIES = 100


class RegistryClient:
    """Client for the AdCP registry API.

    Provides brand, property, and member lookups against the central AdCP registry.

    Args:
        base_url: Registry API base URL.
        timeout: Request timeout in seconds.
        client: Optional httpx.AsyncClient for connection pooling.
            If provided, caller is responsible for client lifecycle.
        user_agent: User-Agent header for requests.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_REGISTRY_URL,
        timeout: float = 10.0,
        client: httpx.AsyncClient | None = None,
        user_agent: str = "adcp-client-python",
    ):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._external_client = client
        self._owned_client: httpx.AsyncClient | None = None
        self._user_agent = user_agent

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create httpx client."""
        if self._external_client is not None:
            return self._external_client
        if self._owned_client is None:
            self._owned_client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                ),
            )
        return self._owned_client

    async def close(self) -> None:
        """Close owned HTTP client. No-op if using external client."""
        if self._owned_client is not None:
            await self._owned_client.aclose()
            self._owned_client = None

    async def __aenter__(self) -> RegistryClient:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def lookup_brand(self, domain: str) -> ResolvedBrand | None:
        """Resolve a domain to its brand identity.

        Works for any domain — brand houses, sub-brands, and operators
        (agencies, DSPs) are all brands in the registry.

        Args:
            domain: Domain to resolve (e.g., "nike.com", "wpp.com").

        Returns:
            ResolvedBrand if found, None if not in the registry.

        Raises:
            RegistryError: On HTTP or parsing errors.

        Example:
            brand = await registry.lookup_brand(request.brand.domain)
        """
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self._base_url}/api/brands/resolve",
                params={"domain": domain},
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise RegistryError(
                    f"Brand lookup failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            if data is None:
                return None
            return ResolvedBrand.model_validate(data)
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(f"Brand lookup timed out after {self._timeout}s") from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Brand lookup failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(f"Brand lookup failed: invalid response: {e}") from e

    async def lookup_brands(self, domains: list[str]) -> dict[str, ResolvedBrand | None]:
        """Bulk resolve domains to brand identities.

        Automatically chunks requests exceeding 100 domains.

        Args:
            domains: List of domains to resolve.

        Returns:
            Dict mapping each domain to its ResolvedBrand, or None if not found.

        Raises:
            RegistryError: On HTTP or parsing errors.
        """
        if not domains:
            return {}

        chunks = [
            domains[i : i + MAX_BULK_DOMAINS] for i in range(0, len(domains), MAX_BULK_DOMAINS)
        ]

        chunk_results = await asyncio.gather(
            *[self._lookup_brands_chunk(chunk) for chunk in chunks]
        )

        merged: dict[str, ResolvedBrand | None] = {}
        for result in chunk_results:
            merged.update(result)
        return merged

    async def _lookup_brands_chunk(self, domains: list[str]) -> dict[str, ResolvedBrand | None]:
        """Resolve a single chunk of brand domains (max 100)."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self._base_url}/api/brands/resolve/bulk",
                json={"domains": domains},
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code != 200:
                raise RegistryError(
                    f"Bulk brand lookup failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            results_raw = data.get("results", {})
            results: dict[str, ResolvedBrand | None] = {d: None for d in domains}
            for domain, brand_data in results_raw.items():
                if brand_data is not None:
                    results[domain] = ResolvedBrand.model_validate(brand_data)
            return results
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(f"Bulk brand lookup timed out after {self._timeout}s") from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Bulk brand lookup failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(f"Bulk brand lookup failed: invalid response: {e}") from e

    async def lookup_property(self, domain: str) -> ResolvedProperty | None:
        """Resolve a publisher domain to its property info.

        Args:
            domain: Publisher domain to resolve (e.g., "nytimes.com").

        Returns:
            ResolvedProperty if found, None if the domain is not in the registry.

        Raises:
            RegistryError: On HTTP or parsing errors.
        """
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self._base_url}/api/properties/resolve",
                params={"domain": domain},
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise RegistryError(
                    f"Property lookup failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            if data is None:
                return None
            return ResolvedProperty.model_validate(data)
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(f"Property lookup timed out after {self._timeout}s") from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Property lookup failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(f"Property lookup failed: invalid response: {e}") from e

    async def lookup_properties(self, domains: list[str]) -> dict[str, ResolvedProperty | None]:
        """Bulk resolve publisher domains to property info.

        Automatically chunks requests exceeding 100 domains.

        Args:
            domains: List of publisher domains to resolve.

        Returns:
            Dict mapping each domain to its ResolvedProperty, or None if not found.

        Raises:
            RegistryError: On HTTP or parsing errors.
        """
        if not domains:
            return {}

        chunks = [
            domains[i : i + MAX_BULK_DOMAINS] for i in range(0, len(domains), MAX_BULK_DOMAINS)
        ]

        chunk_results = await asyncio.gather(
            *[self._lookup_properties_chunk(chunk) for chunk in chunks]
        )

        merged: dict[str, ResolvedProperty | None] = {}
        for result in chunk_results:
            merged.update(result)
        return merged

    async def _lookup_properties_chunk(
        self, domains: list[str]
    ) -> dict[str, ResolvedProperty | None]:
        """Resolve a single chunk of property domains (max 100)."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self._base_url}/api/properties/resolve/bulk",
                json={"domains": domains},
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code != 200:
                raise RegistryError(
                    f"Bulk property lookup failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            results_raw = data.get("results", {})
            results: dict[str, ResolvedProperty | None] = {d: None for d in domains}
            for domain, prop_data in results_raw.items():
                if prop_data is not None:
                    results[domain] = ResolvedProperty.model_validate(prop_data)
            return results
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(f"Bulk property lookup timed out after {self._timeout}s") from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Bulk property lookup failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(f"Bulk property lookup failed: invalid response: {e}") from e

    async def list_members(self, limit: int = 100) -> list[Member]:
        """List organizations registered in the AAO member directory.

        Args:
            limit: Maximum number of members to return.

        Returns:
            List of Member objects.

        Raises:
            RegistryError: On HTTP or parsing errors.
        """
        if limit < 1:
            raise ValueError(f"limit must be at least 1, got {limit}")

        client = await self._get_client()
        try:
            response = await client.get(
                f"{self._base_url}/api/members",
                params={"limit": limit},
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code != 200:
                raise RegistryError(
                    f"Member list failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            return [Member.model_validate(m) for m in data.get("members", [])]
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(f"Member list timed out after {self._timeout}s") from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Member list failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(f"Member list failed: invalid response: {e}") from e

    async def get_member(self, slug: str) -> Member | None:
        """Get a single AAO member by their slug.

        Args:
            slug: Member slug (e.g., "adgentek").

        Returns:
            Member if found, None if not in the registry.

        Raises:
            RegistryError: On HTTP or parsing errors.
            ValueError: If slug contains path-traversal characters.
        """
        if not slug or not re.fullmatch(r"[a-zA-Z0-9_-]+", slug):
            raise ValueError(f"Invalid member slug: {slug!r}")
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self._base_url}/api/members/{slug}",
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise RegistryError(
                    f"Member lookup failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            if data is None:
                return None
            return Member.model_validate(data)
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(f"Member lookup timed out after {self._timeout}s") from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Member lookup failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(f"Member lookup failed: invalid response: {e}") from e

    # ========================================================================
    # Policy Registry Operations
    # ========================================================================

    async def list_policies(
        self,
        search: str | None = None,
        category: str | None = None,
        enforcement: str | None = None,
        jurisdiction: str | None = None,
        vertical: str | None = None,
        domain: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PolicySummary]:
        """List governance policies with optional filtering.

        Args:
            search: Full-text search on policy name and description.
            category: Filter by category ("regulation" or "standard").
            enforcement: Filter by enforcement level ("must", "should", "may").
            jurisdiction: Filter by jurisdiction with region alias matching.
            vertical: Filter by industry vertical.
            domain: Filter by governance domain ("campaign", "creative", etc.).
            limit: Results per page (default 20, max 1000).
            offset: Pagination offset.

        Returns:
            List of PolicySummary objects.

        Raises:
            RegistryError: On HTTP or parsing errors.
        """
        client = await self._get_client()
        params: dict[str, str | int] = {"limit": limit, "offset": offset}
        if search is not None:
            params["search"] = search
        if category is not None:
            params["category"] = category
        if enforcement is not None:
            params["enforcement"] = enforcement
        if jurisdiction is not None:
            params["jurisdiction"] = jurisdiction
        if vertical is not None:
            params["vertical"] = vertical
        if domain is not None:
            params["domain"] = domain

        try:
            response = await client.get(
                f"{self._base_url}/api/policies/registry",
                params=params,
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code != 200:
                raise RegistryError(
                    f"Policy list failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            return [PolicySummary.model_validate(p) for p in data.get("policies", [])]
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(f"Policy list timed out after {self._timeout}s") from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Policy list failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(f"Policy list failed: invalid response: {e}") from e

    async def resolve_policy(
        self,
        policy_id: str,
        version: str | None = None,
    ) -> Policy | None:
        """Resolve a single policy by ID.

        Args:
            policy_id: Policy identifier (e.g., "gdpr_consent").
            version: Optional version pin; returns None if current version differs.

        Returns:
            Policy if found, None if not in the registry.

        Raises:
            RegistryError: On HTTP or parsing errors.
        """
        client = await self._get_client()
        params: dict[str, str] = {"policy_id": policy_id}
        if version is not None:
            params["version"] = version

        try:
            response = await client.get(
                f"{self._base_url}/api/policies/resolve",
                params=params,
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise RegistryError(
                    f"Policy resolve failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            if data is None:
                return None
            return Policy.model_validate(data)
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(f"Policy resolve timed out after {self._timeout}s") from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Policy resolve failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(f"Policy resolve failed: invalid response: {e}") from e

    async def resolve_policies(
        self,
        policy_ids: list[str],
    ) -> dict[str, Policy | None]:
        """Bulk resolve policies by ID.

        Automatically chunks requests exceeding 100 policy IDs.

        Args:
            policy_ids: List of policy identifiers to resolve.

        Returns:
            Dict mapping each policy_id to its Policy, or None if not found.

        Raises:
            RegistryError: On HTTP or parsing errors.
        """
        if not policy_ids:
            return {}

        chunks = [
            policy_ids[i : i + MAX_BULK_POLICIES]
            for i in range(0, len(policy_ids), MAX_BULK_POLICIES)
        ]

        chunk_results = await asyncio.gather(
            *[self._resolve_policies_chunk(chunk) for chunk in chunks]
        )

        merged: dict[str, Policy | None] = {}
        for result in chunk_results:
            merged.update(result)
        return merged

    async def _resolve_policies_chunk(
        self, policy_ids: list[str]
    ) -> dict[str, Policy | None]:
        """Resolve a single chunk of policy IDs (max 100)."""
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self._base_url}/api/policies/resolve/bulk",
                json={"policy_ids": policy_ids},
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code != 200:
                raise RegistryError(
                    f"Bulk policy resolve failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            results_raw = data.get("results", {})
            results: dict[str, Policy | None] = {pid: None for pid in policy_ids}
            for pid, policy_data in results_raw.items():
                if policy_data is not None:
                    results[pid] = Policy.model_validate(policy_data)
            return results
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(
                f"Bulk policy resolve timed out after {self._timeout}s"
            ) from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Bulk policy resolve failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(
                f"Bulk policy resolve failed: invalid response: {e}"
            ) from e

    async def policy_history(
        self,
        policy_id: str,
        limit: int = 20,
        offset: int = 0,
    ) -> PolicyHistory | None:
        """Retrieve edit history for a policy.

        Args:
            policy_id: Policy identifier.
            limit: Maximum revisions to return (default 20, max 100).
            offset: Pagination offset.

        Returns:
            PolicyHistory if found, None if the policy doesn't exist.

        Raises:
            RegistryError: On HTTP or parsing errors.
        """
        client = await self._get_client()
        try:
            response = await client.get(
                f"{self._base_url}/api/policies/history",
                params={"policy_id": policy_id, "limit": limit, "offset": offset},
                headers={"User-Agent": self._user_agent},
                timeout=self._timeout,
            )
            if response.status_code == 404:
                return None
            if response.status_code != 200:
                raise RegistryError(
                    f"Policy history failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            data = response.json()
            if data is None:
                return None
            return PolicyHistory.model_validate(data)
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(
                f"Policy history timed out after {self._timeout}s"
            ) from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Policy history failed: {e}") from e
        except (ValidationError, ValueError) as e:
            raise RegistryError(
                f"Policy history failed: invalid response: {e}"
            ) from e

    async def save_policy(
        self,
        policy_id: str,
        version: str,
        name: str,
        category: str,
        enforcement: str,
        policy: str,
        *,
        auth_token: str,
        description: str | None = None,
        jurisdictions: list[str] | None = None,
        region_aliases: dict[str, list[str]] | None = None,
        verticals: list[str] | None = None,
        channels: list[str] | None = None,
        effective_date: str | None = None,
        sunset_date: str | None = None,
        governance_domains: list[str] | None = None,
        source_url: str | None = None,
        source_name: str | None = None,
        guidance: str | None = None,
        exemplars: dict[str, Any] | None = None,
        ext: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create or update a community-contributed policy.

        Requires authentication. Cannot edit registry-sourced or pending policies.

        Args:
            policy_id: Policy identifier (lowercase alphanumeric with underscores).
            version: Semantic version string.
            name: Human-readable policy name.
            category: "regulation" or "standard".
            enforcement: "must", "should", or "may".
            policy: Natural language policy text.
            auth_token: API key for authentication.
            description: Policy description.
            jurisdictions: ISO jurisdiction codes.
            region_aliases: Region alias mappings (e.g., {"EU": ["DE", "FR"]}).
            verticals: Industry verticals.
            channels: Media channels.
            effective_date: ISO 8601 date when enforcement begins.
            sunset_date: ISO 8601 date when enforcement ends.
            governance_domains: Applicable domains ("campaign", "creative", etc.).
            source_url: URL of the source regulation/standard.
            source_name: Name of the source.
            guidance: Implementation guidance text.
            exemplars: Pass/fail calibration scenarios.
            ext: Extension data.

        Returns:
            Dict with success, message, policy_id, and revision_number.

        Raises:
            RegistryError: On HTTP or parsing errors (400, 401, 409, 429).
        """
        client = await self._get_client()
        body: dict[str, Any] = {
            "policy_id": policy_id,
            "version": version,
            "name": name,
            "category": category,
            "enforcement": enforcement,
            "policy": policy,
        }
        for key, value in [
            ("description", description),
            ("jurisdictions", jurisdictions),
            ("region_aliases", region_aliases),
            ("verticals", verticals),
            ("channels", channels),
            ("effective_date", effective_date),
            ("sunset_date", sunset_date),
            ("governance_domains", governance_domains),
            ("source_url", source_url),
            ("source_name", source_name),
            ("guidance", guidance),
            ("exemplars", exemplars),
            ("ext", ext),
        ]:
            if value is not None:
                body[key] = value

        try:
            response = await client.post(
                f"{self._base_url}/api/policies/save",
                json=body,
                headers={
                    "User-Agent": self._user_agent,
                    "Authorization": f"Bearer {auth_token}",
                },
                timeout=self._timeout,
            )
            if response.status_code != 200:
                raise RegistryError(
                    f"Policy save failed: HTTP {response.status_code}",
                    status_code=response.status_code,
                )
            result: dict[str, Any] = response.json()
            return result
        except RegistryError:
            raise
        except httpx.TimeoutException as e:
            raise RegistryError(
                f"Policy save timed out after {self._timeout}s"
            ) from e
        except httpx.HTTPError as e:
            raise RegistryError(f"Policy save failed: {e}") from e
