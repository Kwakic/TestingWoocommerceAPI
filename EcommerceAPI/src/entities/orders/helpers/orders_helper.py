"""Orders domain helper.

This module contains domain-level orchestration for the WooCommerce Orders
API. ``OrdersHelper`` prepares operation arguments and delegates HTTP requests
to ``OrdersApi``; it does not own transport details or response validation.

Architecture
------------
Test / Fixture
    ↓
OrderFactory / OrderBuilder / OrderStateBuilder
    ↓
OrderProvisioner / OrderStateProvisioner
    ↓
OrdersHelper
    ↓
OrdersApi
    ↓
APIClient
    ↓
WooCommerce

Responsibilities
----------------
- Orchestrate Order operations through ``OrdersApi``.
- Accept already-prepared creation and update payloads.
- Return parsed JSON by default or ``HttpResponse`` when requested.
- Delegate collection pagination to ``paginate_all_results``.
- Apply Order-specific status and creation-date filters to list results.

Non-responsibilities
--------------------
- Generate Order test data or build scenario-specific state.
- Call ``APIClient`` request methods directly or define endpoint paths.
- Validate response schemas or business expectations.
- Register resource ownership, perform cleanup, or use pytest fixtures.
- Access the database or make test assertions.

Data preparation belongs to ``OrderFactory``, ``OrderBuilder``, and
``OrderStateBuilder``. System-boundary setup belongs to the Order provisioners
and the calling fixture. Validation belongs to the Order validator layer.

Public operations
-----------------
``create_order`` and ``update_order`` accept prepared mappings and optional
keyword fields. ``get_order_by_id`` and ``delete_order`` operate on an existing
Order. ``list_orders_paginated`` returns an aggregated collection. The
``call_update_an_order`` method preserves the contract currently used by
``OrderStateProvisioner``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from EcommerceAPI.src.core.http_response import HttpResponse
from EcommerceAPI.src.entities.orders.api.orders_api import OrdersApi
from EcommerceAPI.src.utils.date_timestamp_utils import safe_parse_utc_datetime
from EcommerceAPI.src.utils.exceptions import (
    SchemaValidationError,
    UnexpectedStatusCodeError,
)
from EcommerceAPI.src.utils.pagination_utils import paginate_all_results

logger = logging.getLogger(__name__)

VALID_ORDER_STATUSES = frozenset(
    {
        "pending",
        "processing",
        "on-hold",
        "completed",
        "cancelled",
        "refunded",
        "failed",
        "trash",
        "any",
    }
)


class OrdersHelper:
    """Provide business-facing Order operations through ``OrdersApi``.

    The helper receives prepared payloads and does not create test data. Order
    creation data is prepared by the factory/builder, while partial state for
    an existing Order is prepared by ``OrderStateBuilder``.

    ``OrdersApi`` is injected so the helper uses the framework's configured
    API client and keeps endpoint paths and HTTP verbs in the API layer.
    """

    def __init__(self, orders_api: OrdersApi) -> None:
        """Initialize the helper with the configured Orders API wrapper.

        Args:
            orders_api: API layer responsible for Order endpoints and
                delegation to the configured ``APIClient``.
        """
        self.orders_api = orders_api

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def create_order(
        self,
        payload: Optional[Dict[str, Any]] = None,
        return_http_response: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any] | HttpResponse:
        """Create an Order from already-prepared data.

        Args:
            payload: Optional complete payload prepared by the caller.
            return_http_response: Return the framework response when true;
                otherwise return the parsed response body.
            **kwargs: Additional Order fields, overriding matching payload
                keys. Supported for provisioners and simple API-oriented calls.

        Returns:
            The created Order JSON, or ``HttpResponse`` when requested.

        Raises:
            UnexpectedStatusCodeError: If the API failure has no usable
                structured response to return.
            SchemaValidationError: If the API failure has no usable structured
                response to return.

        Notes:
            This method does not generate data, validate the response, or
            register the created Order for cleanup.
        """
        final_payload: Dict[str, Any] = {}

        # Accept a complete prepared payload or individual Order fields.
        if payload:
            final_payload.update(payload)

        # Explicit keyword arguments take precedence over matching payload keys.
        final_payload.update(kwargs)

        logger.debug("Creating Order with payload keys: %r", list(final_payload))

        try:
            http_response = self.orders_api.create_order(payload=final_payload)
        except (UnexpectedStatusCodeError, SchemaValidationError) as error:
            logger.warning("Order creation raised %s: %s", type(error).__name__, error)

            # Prefer structured JSON already attached by the API exception.
            response_json = getattr(error, "response_json", None)
            response = getattr(error, "response", None)

            # HttpResponse has a parsed JSON attribute; a raw response exposes
            # json() as a method. ValueError means that body is not valid JSON.
            if response_json is None and response is not None:
                if isinstance(response, HttpResponse):
                    response_json = response.json
                else:
                    try:
                        response_json = response.json()
                    except ValueError as parse_error:
                        logger.warning(
                            "Could not parse the Order creation error body as JSON: %s",
                            parse_error,
                        )

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            # Preserve the original API exception when no structured response
            # body is available.
            raise

        if return_http_response:
            return http_response
        return http_response.json

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def get_order_by_id(
        self,
        order_id: int,
        return_http_response: bool = False,
    ) -> Dict[str, Any] | HttpResponse:
        """Retrieve an Order by its WooCommerce ID.

        Args:
            order_id: WooCommerce Order ID.
            return_http_response: Return ``HttpResponse`` when true; otherwise
                return its parsed JSON body.

        Returns:
            The retrieved Order JSON or the complete ``HttpResponse``.
        """
        logger.debug("Retrieving Order %s", order_id)
        http_response = self.orders_api.get_order(order_id)

        if return_http_response:
            return http_response
        return http_response.json

    def list_orders_paginated(
        self,
        params: Optional[Dict[str, Any]] = None,
        max_pages: int = 1000,
        created_before: Optional[str] = None,
        created_after: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch Orders through the shared pagination utility.

        Args:
            params: Additional WooCommerce query parameters. A copy is made
                before this method adds pagination and filter values.
            max_pages: Safety limit passed to ``paginate_all_results``.
            created_before: Optional ISO 8601 upper bound for Order creation
                time. The API receives it as ``before`` and the results are
                checked against ``date_created_gmt``.
            created_after: Optional ISO 8601 lower bound for Order creation
                time. The API receives it as ``after`` and the results are
                checked against ``date_created_gmt``.
            status: Optional WooCommerce Order status from
                ``VALID_ORDER_STATUSES``.

        Returns:
            All fetched Orders that pass the requested date filters. Invalid
            date bounds produce an empty list, matching the other entity
            helpers.

        Raises:
            ValueError: If ``status`` is not a supported Order status.

        Notes:
            Pagination and HTTP requests are delegated to the shared utility
            and the injected API client's endpoint. This method returns an
            aggregated list, so there is no single ``HttpResponse`` to expose.
        """
        query_params = params.copy() if params else {}
        query_params.setdefault("per_page", 100)

        if status:
            if status not in VALID_ORDER_STATUSES:
                allowed_statuses = ", ".join(sorted(VALID_ORDER_STATUSES))
                raise ValueError(
                    f"Invalid Order status '{status}'. Supported values: "
                    f"{allowed_statuses}."
                )
            query_params["status"] = status

        if created_after:
            query_params["after"] = created_after

        if created_before:
            query_params["before"] = created_before

        logger.debug("Listing Orders through the shared pagination utility")
        orders = paginate_all_results(
            api_client=self.orders_api.api_client,
            endpoint=self.orders_api.ENDPOINT,
            params=query_params,
            max_pages=max_pages,
        )

        cutoff_before = cutoff_after = None
        if created_before:
            try:
                cutoff_before = safe_parse_utc_datetime(created_before)
            except ValueError:
                logger.warning("Invalid 'created_before' format. Use ISO 8601.")
                return []

        if created_after:
            try:
                cutoff_after = safe_parse_utc_datetime(created_after)
            except ValueError:
                logger.warning("Invalid 'created_after' format. Use ISO 8601.")
                return []

        filtered_orders: List[Dict[str, Any]] = []
        for order in orders:
            created_gmt = order.get("date_created_gmt")
            try:
                created_at = (
                    safe_parse_utc_datetime(created_gmt) if created_gmt else None
                )
                if created_at:
                    if cutoff_before and created_at >= cutoff_before:
                        continue
                    if cutoff_after and created_at <= cutoff_after:
                        continue
                filtered_orders.append(order)
            except (TypeError, ValueError, OverflowError) as error:
                logger.warning(
                    "Could not parse 'date_created_gmt' for Order ID %s: %s",
                    order.get("id"),
                    error,
                )

        return filtered_orders

    # ------------------------------------------------------------------
    # UPDATE
    # ------------------------------------------------------------------

    def update_order(
        self,
        order_id: int,
        payload: Optional[Dict[str, Any]] = None,
        return_http_response: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any] | HttpResponse:
        """Update an Order with already-prepared partial state.

        Args:
            order_id: WooCommerce Order ID to update.
            payload: Prepared partial state, normally built by
                ``OrderStateBuilder``.
            return_http_response: Return the complete framework response when
                true; otherwise return parsed JSON.
            **kwargs: Additional update fields that override matching payload
                keys.

        Returns:
            The updated Order JSON or ``HttpResponse`` when requested.

        Raises:
            UnexpectedStatusCodeError: If no structured response is available
                for the API failure.
            SchemaValidationError: If no structured response is available for
                the API failure.

        Notes:
            Response validation and resource lifecycle remain with the caller.
        """
        final_payload: Dict[str, Any] = {}

        if payload:
            final_payload.update(payload)

        final_payload.update(kwargs)

        logger.debug(
            "Updating Order %s with payload keys: %r",
            order_id,
            list(final_payload),
        )

        try:
            http_response = self.orders_api.update_order(
                order_id=order_id,
                payload=final_payload,
            )
        except (UnexpectedStatusCodeError, SchemaValidationError) as error:
            logger.warning("Order update raised %s: %s", type(error).__name__, error)

            response_json = getattr(error, "response_json", None)
            response = getattr(error, "response", None)

            if response_json is None and response is not None:
                if isinstance(response, HttpResponse):
                    response_json = response.json
                else:
                    try:
                        response_json = response.json()
                    except ValueError as parse_error:
                        logger.warning(
                            "Could not parse the Order update error body as JSON: %s",
                            parse_error,
                        )

            if return_http_response and response is not None:
                return response

            if response_json is not None:
                return response_json

            raise

        if return_http_response:
            return http_response
        return http_response.json

    def call_update_an_order(
        self,
        order_id: int,
        payload: Dict[str, Any],
    ) -> HttpResponse:
        """Update an Order and return ``HttpResponse`` for the state provisioner.

        This method preserves the established ``OrderStateProvisioner``
        contract. New direct callers should use ``update_order``.

        Args:
            order_id: WooCommerce Order ID to update.
            payload: Prepared partial Order state.

        Returns:
            The framework ``HttpResponse`` from ``OrdersApi``.
        """
        return self.update_order(
            order_id=order_id,
            payload=payload,
            return_http_response=True,
        )

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def delete_order(
        self,
        order_id: int,
        return_http_response: bool = False,
        force: bool = True,
    ) -> Dict[str, Any] | HttpResponse:
        """Delete an Order by ID, using WooCommerce's hard-delete option.

        Args:
            order_id: WooCommerce Order ID.
            return_http_response: Return the complete framework response when
                true; otherwise return parsed JSON.
            force: Pass WooCommerce's ``force`` query parameter. Defaults to
                true to match the existing entity-helper conventions.

        Returns:
            The delete response JSON or ``HttpResponse`` when requested.
        """
        logger.debug("Deleting Order %s (force=%s)", order_id, force)
        http_response = self.orders_api.delete_order(order_id, force=force)

        if return_http_response:
            return http_response
        return http_response.json
