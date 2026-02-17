from __future__ import annotations

import logging
from typing import Any, Dict

import httpx

from app.configuration.app_config import AppConfig
from app.daos.base_dao import BaseDAO
from app.exceptions.api_not_available_exception import ApiNotAvailableException
from app.exceptions.organization_not_found_exception import OrganizationNotFoundException

logger = logging.getLogger(__name__)


class OrganizationDAO(BaseDAO):
    """DAO for BeautyMarket Organizations API.

    Communicates with the external organizations service to retrieve
    and update organization data.
    """

    def __init__(self):
        super().__init__()
        self._organizations_url = AppConfig.get_key(
            "api.organizations.url",
            "/api/organizations/%s",
        )
        logger.debug(f"OrganizationDAO initialized with url={self._organizations_url}")

    def get_organization(self, organization_id: str) -> Dict[str, Any]:
        """Get organization by ID from the external API.

        Args:
            organization_id: The organization identifier.

        Returns:
            Dictionary with organization data.

        Raises:
            OrganizationNotFoundException: If the organization is not found.
            ApiNotAvailableException: If the organizations API is unavailable.
        """
        if "%s" in self._organizations_url:
            url = self._organizations_url % organization_id
        else:
            url = self._organizations_url.format(organization_id=organization_id)

        try:
            logger.info(f"Getting organization: {organization_id}")
            result = self._get(url)
            logger.info(f"Successfully retrieved organization: {organization_id}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error getting organization {organization_id}: "
                f"{e.response.status_code} - {e.response.text}"
            )
            raise OrganizationNotFoundException(
                f"Organization {organization_id} not found"
            ) from e

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error(f"Organizations API not available: {e}")
            raise ApiNotAvailableException(
                "Organizations API is not available"
            ) from e

    def update_organization_gln(self, organization_id: str, gln: str) -> Dict[str, Any]:
        """Update organization GLN in the external API.

        Args:
            organization_id: The organization identifier.
            gln: The GLN value to set.

        Returns:
            Updated organization data.

        Raises:
            OrganizationNotFoundException: If the organization is not found.
            ApiNotAvailableException: If the organizations API is unavailable.
        """
        if "%s" in self._organizations_url:
            url = self._organizations_url % organization_id
        else:
            url = self._organizations_url.format(organization_id=organization_id)

        try:
            logger.info(f"Updating GLN for organization: {organization_id}")
            result = self._patch(url, json={"gln": gln})
            logger.info(f"Successfully updated GLN for organization: {organization_id}")
            return result

        except httpx.HTTPStatusError as e:
            logger.error(
                f"HTTP error updating organization {organization_id}: "
                f"{e.response.status_code} - {e.response.text}"
            )
            raise OrganizationNotFoundException(
                f"Organization {organization_id} not found"
            ) from e

        except (httpx.ConnectError, httpx.TimeoutException) as e:
            logger.error(f"Organizations API not available: {e}")
            raise ApiNotAvailableException(
                "Organizations API is not available"
            ) from e
