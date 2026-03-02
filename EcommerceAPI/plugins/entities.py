"""
Pytest entities plugin (framework-level).

This module is the SINGLE SOURCE OF TRUTH for entity discovery, registration,
and cross-domain access within the test framework.

──────────────────────────────────────────────────────────────────────────────
ARCHITECTURAL PRINCIPLES
──────────────────────────────────────────────────────────────────────────────

• Framework owns discovery → framework owns generic access
  - Dynamic discovery of helpers and DAOs happens ONLY here.
  - Generic access (entity_helper / entity_dao) is provided at framework level.

• Domains own ergonomics, NOT reuse
  - Domain-specific fixtures (e.g. customer_helper) live in domain test packages.
  - Cross-team reuse MUST go through framework fixtures, never domain conftests.

• No fixture leakage across test domains
  - tests/customers fixtures are NOT imported or reused by tests/orders.
  - This prevents tight coupling and ownership violations between teams.

• No coupling between teams
  - Orders tests can use customers via entity_helper("customers")
    without importing or depending on customer test code.

• Zero breaking changes
  - Existing tests using all_resources.<entity>.helper continue to work.
  - Dict-style access via shared_api_resources is preserved.

• Production-grade observability
  - Deterministic, convention-based discovery
  - Explicit discovery logging
  - Optional fail-fast strict discovery mode (CI-friendly)

──────────────────────────────────────────────────────────────────────────────
WHAT THIS MODULE PROVIDES
──────────────────────────────────────────────────────────────────────────────

1. Dynamic entity discovery
   - Discovers *_helper.py and *_dao.py pairs by convention
   - Bundles them into EntityBundle(helper, dao, delete_method)

2. Framework-level fixtures
   - shared_api_resources  → low-level dict-based access + cleanup
   - all_resources         → ergonomic attribute-style access
   - entity_helper(name)   → generic cross-domain helper accessor
   - entity_dao(name)      → generic cross-domain DAO accessor

3. Cleanup guarantees
   - Tracks created resources per module
   - Automatically cleans up unless explicitly marked as deleted
   - Safe for parallel execution (pytest-xdist)

──────────────────────────────────────────────────────────────────────────────
USAGE EXAMPLES
──────────────────────────────────────────────────────────────────────────────

✔ Domain-specific tests (preferred within a domain)

    def test_customer(customer_helper):
        customer = customer_helper.create_customer()
        assert customer["id"]


✔ Cross-team reuse (orders using customers)

    def test_order_creation(entity_helper):
        customer_helper = entity_helper("customers")
        customer = customer_helper.create_customer()
        order = create_order(customer_id=customer["id"])
        assert order["customer_id"] == customer["id"]


✔ Parametrized framework / infra tests

    @pytest.mark.parametrize("entity", ["customers", "orders"])
    def test_all_entities_have_dao(entity_dao, entity):
        assert entity_dao(entity) is not None


──────────────────────────────────────────────────────────────────────────────
IMPORTANT RULES FOR TEST AUTHORS
──────────────────────────────────────────────────────────────────────────────

✔ Use domain fixtures (customer_helper) inside the domain
✔ Use entity_helper/entity_dao for cross-domain or generic tests
✘ Do NOT import fixtures from another domain's conftest
✘ Do NOT bypass the framework registry

If you need a new entity:
  - Add <entity>_helper.py under src/helpers
  - Add <entity>_dao.py under src/dao
  - Follow naming conventions
  - No framework changes required

──────────────────────────────────────────────────────────────────────────────
This module is intentionally conservative.
Changes here affect the entire test platform.
──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import logging
import os
import pytest
from typing import Callable, TypedDict, Any, Dict, Optional, Mapping
from collections import defaultdict
import importlib
import pkgutil
from dataclasses import dataclass
from enum import Enum

import EcommerceAPI.src

from EcommerceAPI.src.clients.api_client import APIClient
from EcommerceAPI.src.utilities.entities_registry import EntitiesRegistry

log = logging.getLogger(__name__)

# ----------------------------------------------------------------
# Strict discovery mode (opt-in, CI friendly)
# ----------------------------------------------------------------
STRICT_ENTITY_DISCOVERY = os.getenv("STRICT_ENTITY_DISCOVERY", "0").lower() in ("1", "true", "yes", "on",)


# ----------------------------------------------------------------
# Resource type enum
# ----------------------------------------------------------------
class ResourceType(str, Enum):
    """
    Standardized resource type names used when registering or cleaning up created test resources.
    """
    CUSTOMER = "customers"
    PRODUCT = "products"
    COUPON = "coupons"
    ORDER = "orders"
    # Add new resource types as needed, matching entity naming conventions


# ----------------------------------------------------------------
# Entity Registry and API Protocol Abstraction
# ----------------------------------------------------------------
@dataclass
class EntityBundle:
    """
    Container that groups a helper instance, a DAO instance, and a delete method for a particular entity.

    Fields:
      helper: API helper object for the entity (tests call helper methods).
      dao: DAO object used to validate records in the database.
      delete_method: Callable used to delete resources during teardown.

    Notes:
      - EntityBundle instances are created by discover_entities() and stored in the registry returned by that function.

    Example usage in a test:
        helper = all_resources.entities["customers"].helper
        dao = all_resources.entities["customers"].dao
        customer = helper.create_customer()
        db_record = dao.get_customer_by_id(customer["id"])

    """
    helper: Any
    dao: Any
    delete_method: Callable[[str], Any]


class SharedAPIResources(TypedDict, total=False):
    """
    TypedDict for shared API resources (helpers, DAOs, utility functions).
    TypedDict — a way to describe what keys (and value types) an ordinary Python dict is expected to contain.

    Why it is there?:
    Many fixtures return a dictionary of helpers / utilities (instead of an object).
    TypedDict just documents what keys exist and what types those values are — it doesn’t change runtime behavior.

    Meaning of parts:
    - total=False — all keys are optional (the dict may include some or none of them).
    - register_resource: function used by tests to register created resources.
    - mark_resource_deleted: function to mark a resource as deleted.
    - api_client: shared APIClient instance.
    - _entity_registry: internal dict mapping entity names to EntityBundle instances.

    Note: Kept as TypedDict for runtime compatibility; use AllResources for ergonomic attribute access.

    """
    register_resource: Callable[[str, str], None]
    mark_resource_deleted: Callable[[str, str], None]
    api_client: Any
    _entity_registry: Dict[str, EntityBundle]  # Internal plumbing, not for tests


# ----------------------------------------------------------------
# Dynamic Helper/DAO/Protocol Discovery & Registry
# ----------------------------------------------------------------
def discover_entities(api_client: APIClient) -> Dict[str, EntityBundle]:
    """
    Discover helper and DAO modules under EcommerceAPI.src.helpers and EcommerceAPI.src.dao

    The goal of this function is deterministic, convention-based discovery:
      - For each *_helper module, locate a corresponding DAO module/class.
      - Instantiate the helper and DAO.
      - Bundle them together with the appropriate delete method.
      - Never crash test collection; errors are logged and discovery continues.

    This version follows a clear, conservative lookup strategy:
      1. Identify helper classes matching <entity>Helper.
      2. Try locating DAO modules using predictable filename patterns.
      3. Search inside the matched module for narrow, case-insensitive DAO class names.
      4. Fallback to an exact class name like <EntityName>DAO in any DAO module (CamelCase).
      5. Short-circuit on first reasonable match to avoid ambiguous results.

    Returns:
        Dict[str, EntityBundle]: entity name → EntityBundle(helper, dao, delete_method)
    """

    # -------------------------------------------------------------
    # Scan the entire src package and dynamically import them (domain-based structure)
    # -------------------------------------------------------------
    base_path = EcommerceAPI.src.__path__

    # Registry to populate
    entities: Dict[str, EntityBundle] = {}

    # Known protocol → utility mapping
    api_protocol_map = {
        "customers": "api_client",
        "products": "api_client",
        "orders": "api_client",
        "coupons": "api_client",
    }
    protocol_utils = {"api_client": api_client}

    # -------------------------------------------------------------
    # Discover ALL modules under src and dynamically import all modules(domain-agnostic). It supports subpackages, e.g.
    # helpers/customers/customers_helper.py)
    # This supports:
    #   src/customers/helpers/customers_helper.py
    #   src/orders/api/orders_api.py
    #   etc.
    # -------------------------------------------------------------
    all_modules = {
        modname: importlib.import_module(modname)
        for _, modname, _ in pkgutil.walk_packages(
            base_path,
            prefix="EcommerceAPI.src.",
        )
    }

    # -------------------------------------------------------------
    # Filter modules by role using naming convention
    # -------------------------------------------------------------

    # Helper modules → *_helper.py
    helper_modules = {
        name.rsplit(".", 1)[-1]: mod
        for name, mod in all_modules.items()
        if name.endswith("_helper")
    }

    # DAO modules → *_dao.py
    dao_modules = {
        name.rsplit(".", 1)[-1]: mod
        for name, mod in all_modules.items()
        if name.endswith("_dao")
    }

    # API modules → *_api.py
    api_modules = {
        name.rsplit(".", 1)[-1]: mod
        for name, mod in all_modules.items()
        if name.endswith("_api")
    }

    # ---------------------------------------------------------------------
    # DAO resolution logic extracted for clarity and maintainability
    # ---------------------------------------------------------------------
    def _to_camel(s: str) -> str:
        # Convert snake_case -> CamelCase for exact class name lookup
        return "".join(part.capitalize() for part in s.split("_"))

    def _find_dao_class(entity_name: str) -> Optional[Any]:
        """
        Resolve the DAO class/object for a given entity name.

        Lookup strategy:
          1. Try predictable DAO module filenames:
                <entity>_dao
                <entity>s_dao
             (entity may be plural or singular; both are tried)
          2. If a module is found, scan for a class whose name:
                - starts with the singular-ish prefix, and
                - ends with 'dao' (case-insensitive)
             Prefer classes over other objects when available.
          3. Fallback: search all DAO modules for an exact class name:
                <EntityName>DAO (CamelCased from snake_case)
        """
        entity_lower = entity_name.lower()

        # Conservative singular prefix (customers -> customer)
        prefix = entity_lower[:-1] if entity_lower.endswith("s") and len(entity_lower) > 1 else entity_lower

        # Step 1: predictable module filename candidates (deduped)
        candidate_modules = list(
            dict.fromkeys(
                [
                    f"{prefix}_dao",
                    f"{prefix}s_dao",
                    f"{entity_lower}_dao",
                    f"{entity_lower}s_dao",
                ]
            )
        )

        dao_mod = None
        for modname in candidate_modules:
            if modname in dao_modules:
                dao_mod = dao_modules[modname]
                break

        # Step 2: if module found, search narrowly for attributes that look like DAOs
        if dao_mod:
            non_class_candidate = None
            for attr in dir(dao_mod):
                name = attr.lower()
                if name.startswith(prefix) and name.endswith("dao"):
                    val = getattr(dao_mod, attr)
                    if isinstance(val, type):
                        # Prefer returning a class if found
                        return val
                    if non_class_candidate is None:
                        non_class_candidate = val
            if non_class_candidate is not None:
                return non_class_candidate

        # Step 3: exact match first (fast + deterministic)
        exact_name = f"{_to_camel(entity_name)}DAO"
        for mod in dao_modules.values():
            if hasattr(mod, exact_name):
                return getattr(mod, exact_name)

        # Step 4: flexible fallback (folder-agnostic)
        for mod in dao_modules.values():
            for attr in dir(mod):
                name = attr.lower()
                if name.startswith(prefix) and name.endswith("dao"):
                    val = getattr(mod, attr)
                    if isinstance(val, type):
                        return val

        return None

    # ---------------------------------------------------------------------
    # Core entity discovery loop
    # ---------------------------------------------------------------------
    for helper_name, helper_mod in helper_modules.items():
        if not helper_name.endswith("_helper"):
            continue

        # Derive entity (e.g., "customers_helper" -> "customers")
        entity = helper_name.replace("_helper", "")

        # Locate helper class (case-insensitive suffix match)
        helper_cls = next(
            (
                getattr(helper_mod, attr)
                for attr in dir(helper_mod)
                if attr.lower().startswith(entity.lower()) and attr.lower().endswith("helper")
            ),
            None,
        )
        if not helper_cls:
            continue

        # Resolve DAO class or object
        dao_cls = _find_dao_class(entity)
        if not dao_cls:
            msg = f"No DAO found for entity '{entity}'."

            if STRICT_ENTITY_DISCOVERY:
                raise RuntimeError(
                    f"[STRICT_ENTITY_DISCOVERY] {msg} "
                    f"Ensure a matching DAO exists or disable strict mode."
                )

            log.debug("%s Skipping discovery for this helper.", msg)
            continue

        # Resolve protocol and delete method
        protocol_key = api_protocol_map.get(entity)
        protocol_util = protocol_utils.get(protocol_key)
        delete_method = getattr(protocol_util, "delete", None) if protocol_util else None

        if not delete_method:
            msg = f"No delete method found for entity '{entity}'."

            if STRICT_ENTITY_DISCOVERY:
                raise RuntimeError(
                    f"[STRICT_ENTITY_DISCOVERY] {msg} "
                    f"Entities must be fully deletable in strict mode."
                )

            log.warning("%s Skipping entity registration.", msg)
            continue

        # Instantiate helper + DAO
        try:
            # Step 1: Try to load the dedicated API client
            try:
                api_module_name = f"{entity}_api"
                api_module = api_modules.get(api_module_name)

                if not api_module:
                    continue

                api_class_name = f"{_to_camel(entity)}Api"
                api_cls = getattr(api_module, api_class_name, None)

                if not api_cls:
                    continue

                api_instance = api_cls(api_client)
                log.debug("✅ [%s] Loaded API client: %s", entity, api_class_name)

            except Exception as e:
                log.warning("⚠️  [%s] Failed to load API: %s — skipping", entity, e)
                continue

            # Step 2: Instantiate helper with an API client
            try:
                helper_instance = helper_cls(api_instance)
                log.debug("✅ [%s] Instantiated helper with API client", entity)
            except TypeError as e:
                log.error("❌ [%s] Helper signature incompatible with API client: %s", entity, e)
                continue

            # Step 3: Instantiate DAO if it's a class
            if isinstance(dao_cls, type):
                try:
                    dao_instance = dao_cls()
                except (TypeError, OSError, RuntimeError) as e:
                    logging.getLogger(__name__).warning(
                        "Failed to instantiate DAO %s: %s. Using the class object directly.",
                        getattr(dao_cls, "__name__", str(dao_cls)),
                        e,
                        exc_info=True,
                    )
                    dao_instance = dao_cls
            else:
                dao_instance = dao_cls

            # Step 4: Register the entity bundle
            entities[entity] = EntityBundle(
                helper=helper_instance,
                dao=dao_instance,
                delete_method=delete_method
            )

        except (ImportError, TypeError, ValueError, RuntimeError) as e:
            logging.getLogger(__name__).exception(
                "Discovery: failed to prepare entity bundle for '%s': %s", entity, e
            )

    # Build discovery summary
    summary_lines = []

    for helper_name in sorted(helper_modules.keys()):
        entity_clean = helper_name.replace("_helper", "")

        # Determine actual status FIRST
        is_ready = entity_clean in entities

        if is_ready:
            status = "✅  READY"
        else:
            # Diagnose WHY it was skipped
            api_module_name = f"{entity_clean}_api"
            api_module = api_modules.get(api_module_name)
            api_class_name = f"{_to_camel(entity_clean)}Api"

            if not api_module:
                reason = "missing API module"
            elif not hasattr(api_module, api_class_name):
                reason = f"{api_class_name} class not found in {api_module_name}"
            elif not _find_dao_class(entity_clean):
                reason = "missing DAO"
            else:
                reason = "unknown"

            status = f"⏭️ SKIPPED ({reason})"

        summary_lines.append(f"{entity_clean:<12} | {status}")

    log.info("🔍 ENTITY DISCOVERY SUMMARY")
    for line in summary_lines:
        log.info("   %s", line)

    return entities


# ----------------------------------------------------------------
# Shared API resource fixture with cleanup support
# ----------------------------------------------------------------
@pytest.fixture(scope="module")
def shared_api_resources(api_client: APIClient) -> SharedAPIResources:
    """
    Module-scoped fixture that discovers and exposes API helpers, DAOs, and resource tracking utilities.

    Gives each test module:
      - Ready-to-use API helpers for orders, products, coupons, customers.
      - Matching DAOs for checking the database.
      - Functions to track created resources, so they can be cleaned up later.
      - Smart cleanup:
        → If nothing was created, cleanup is skipped.
        → If something *was* created, it’s deleted automatically.
      - This fixture now consumes the session-scoped `api_client` fixture and passes it into discover_entities
        so discovered bundles use the same APIClient instance.

    When pytest imports conftest.py it defines fixtures. The shared_api_resources fixture calls discover_entities()
    that dynamically import all *_helper.py and *_dao.py modules, instantiates their classes, and returns a registry.
    The all_resources fixture reads that registry and exposes it as all_resources.entities. Your test then does
    "customer_helper = all_resources.customers.helper or .dao"

    Exposed mapping:
      - "<entity>_helper": helper instance for the entity
      - "<entity>_dao": DAO instance for the entity
      - "api_client": the shared APIClient instance
      - "register_resource": function to register created resource ids for teardown
      - "mark_resource_deleted": function to mark resources as already deleted
      - "_entity_registry": mapping of entity name to EntityBundle

    Teardown:
      - When resources were registered during the module run, they're conditionally cleaned up at fixture teardown time.
    """
    # Discover entities via helper/DAO registry. Pass the shared api_client into discover_entities
    entity_registry = discover_entities(api_client)

    # Optional strict discovery validation (fail-fast in CI if enabled)
    if STRICT_ENTITY_DISCOVERY:
        if not entity_registry:
            raise RuntimeError(
                "❌ No API entities discovered. "
                "Check helper/DAO naming conventions."
            )

        incomplete = [
            name for name, bundle in entity_registry.items()
            if not bundle.helper or not bundle.dao or not bundle.delete_method
        ]

        if incomplete:
            raise RuntimeError(
                f"❌ Incomplete entity bundles discovered: {incomplete}"
            )

    # log.debug(f"Entity registry keys: {list(entity_registry.keys())}")
    # Internal tracking for created and deleted resources
    tracked_resources = defaultdict(list)
    deleted_resources = defaultdict(set)

    def register_resource(res_type: str, resource_id: str):
        """Register a resource ID created during the test for cleanup later."""
        if resource_id not in tracked_resources[res_type]:
            tracked_resources[res_type].append(resource_id)
        else:
            log.warning("⚠️ Duplicate %s ID %s already registered — ignoring.", res_type[:-1], resource_id)

    def mark_resource_deleted(res_type: str, resource_id: str):
        """Mark a resource as already deleted manually — will be skipped during teardown."""
        deleted_resources[res_type].add(resource_id)

    # Wrap the registry in an EntitiesRegistry immediately
    wrapped_registry = EntitiesRegistry.from_dict(entity_registry)

    # The resource fixture exposes helpers, DAOs, delete methods, and tracking utilities
    data = {
        **{f"{entity}_helper": bundle.helper for entity, bundle in entity_registry.items()},
        **{f"{entity}_dao": bundle.dao for entity, bundle in entity_registry.items()},
        "api_client": api_client,
        "register_resource": register_resource,
        "mark_resource_deleted": mark_resource_deleted,
        "_entity_registry": wrapped_registry,  # <-- now always an EntitiesRegistry
    }

    yield data

    # ------------------------------
    # Conditional teardown (run only if something was created)
    # ------------------------------
    if any(tracked_resources.values()):
        log.info("🔧 Starting teardown of created test resources...")
        summary_log = []
        for resource_type, resource_ids in tracked_resources.items():
            if not resource_ids:
                continue
            bundle = entity_registry.get(resource_type)
            if not bundle:
                log.warning(f"No entity bundle for {resource_type} — skipping teardown.")
                continue
            delete_func = bundle.delete_method
            already_deleted_ids = deleted_resources.get(resource_type, set())
            total_created = len(set(resource_ids))
            # Import cleanup_items only when needed (to avoid import cycles)
            from EcommerceAPI.src.shared.helpers.cleanup_helpers import cleanup_items
            cleanup_items(
                resource_type=resource_type,
                resource_ids=resource_ids,
                delete_method=delete_func,
                label=resource_type[:-1],
                summary_log=summary_log,
                total_created=total_created,
                already_deleted_ids=already_deleted_ids
            )

        # Print teardown summary
        created_counts = {rtype: len(set(ids)) for rtype, ids in tracked_resources.items()}
        log.info("\n\n🧹 ====================================== CLEANUP SUMMARY ======================================")
        log.info(f"📊 Created during test run: {created_counts}")
        log.info("🧾 Cleanup total summary:")
        for line in summary_log:
            log.info(f"   • {line}")
        log.info("✅ All test data cleanup completed.\n")
    else:
        # No resources were created — skip all teardown logs
        log.debug("🧹 No test data created — skipping teardown.")


# ----------------------------------------------------------------
# Optional ergonomic wrapper for shared_api_resources
# ----------------------------------------------------------------
@pytest.fixture(scope="module")
def shared_api_resources_obj(shared_api_resources: SharedAPIResources) -> EntitiesRegistry[Any]:
    """
    Optional wrapper that exposes both Mapping and attribute-style access for the shared_api_resources fixture
    produced elsewhere in conftest.

    - Non-breaking: existing code using dict-style access continues to work.
    - Ergonomic: tests that request this fixture get attribute access:
        shared_api_resources_obj.register_resource(...)
      or still use dict-style:
        shared_api_resources_obj["register_resource"](...)
    """
    return EntitiesRegistry.from_dict(shared_api_resources)  # EntitiesRegistry accepts any dict-like


# ----------------------------------------------------------------
# All-resources wrapper and fixture
# ----------------------------------------------------------------
@dataclass
class AllResources:
    """
    Aggregates the entity registry and core utilities for use in tests.

    Attributes:
        entities: Mapping[str, EntityBundle] — the runtime registry of entities
        api_client: shared APIClient instance (transport + orchestration layer)
        register: Function to register a test-created resource for teardown.
        mark_deleted: Mark a resource as already deleted (skip in cleanup).

    Runtime attribute access:
      - This class implements __getattr__ so attribute-style lookups (e.g. all_resources.customers) will proxy to the
        entities mapping at runtime. That makes test code simple instead of building as a dictionary e.g.:
            customer_helper = all_resources.customers.helper
            dao = all_resources.customers.dao
    IDE ergonomics:
      - __dir__ includes entity keys (valid Python identifiers) so editors that rely on dir()
        can offer completions for discovered entity names. This class intentionally keeps
        a small, conservative exception handling surface in __dir__ to avoid masking real errors.
    """

    entities: Mapping[str, "EntityBundle"]
    api_client: Any
    register: Callable[[str, str], None]
    mark_deleted: Callable[[str, str], None]

    def __getattr__(self, name: str):
        """
        Provide attribute-style access to entries in `entities`. If `name` is a key in the mapping, return the
        corresponding EntityBundle. Otherwise, raise AttributeError to preserve standard attribute semantics.

        Returns:
            EntityBundle for `name` if present in entities mapping.

        Raises:
            AttributeError if entities are not set yet or `name` is not a key in entities.
        """
        try:
            entities = object.__getattribute__(self, "entities")
        except AttributeError:
            # entities not set yet — preserve AttributeError semantics
            raise AttributeError(name)

        # Only return a value if the key exists in the mapping
        if isinstance(name, str) and name in entities:
            return entities[name]

        raise AttributeError(f"{type(self).__name__!s} object has no attribute {name!r}")

    def __dir__(self):
        """
        Extend the default dir() with discovered entity keys (valid Python identifiers)
        to help IDE completion. Only the minimal, expected exceptions are caught so that
        unrelated errors surface during development.
        """
        default_dir = set(super().__dir__())

        # Safely access entities; if missing, return default dir
        try:
            entities = object.__getattribute__(self, "entities")
        except AttributeError:
            return sorted(default_dir)

        # Get keys() safely — handle mapping-like objects only
        try:
            keys_iter = entities.keys()
        except AttributeError:
            return sorted(default_dir)
        except TypeError:
            return sorted(default_dir)

        # Filter keys to valid Python identifiers and merge with default dir.
        # Narrow exception handling to avoid masking unrelated issues.
        try:
            valid_keys = []
            for k in keys_iter:
                if isinstance(k, str) and k.isidentifier():
                    valid_keys.append(k)
        except (TypeError, RuntimeError, AttributeError, ValueError):
            return sorted(default_dir)

        return sorted(default_dir | set(valid_keys))


@pytest.fixture(scope="module")
def all_resources(shared_api_resources: SharedAPIResources) -> AllResources:
    """
    Provide AllResources using the already wrapped EntitiesRegistry supplied by shared_api_resources.

    This avoids double-wrapping and ensures attribute-style access to entities is consistently available across
    all fixtures.
    """
    registry = shared_api_resources["_entity_registry"]  # Already EntitiesRegistry

    return AllResources(
        entities=registry,
        api_client=shared_api_resources["api_client"],
        register=shared_api_resources["register_resource"],
        mark_deleted=shared_api_resources["mark_resource_deleted"],
    )


# ----------------------------------------------------------------
# Generic cross-domain entity access fixtures
# ----------------------------------------------------------------

@pytest.fixture
def entity_helper(all_resources) -> Callable[[str], Any]:
    """
    Generic, cross-domain accessor for entity helpers.

    Usage:
        helper = entity_helper("customers")

    Intended for:
      - Cross-team usage (orders → customers)
      - Parametrized or generic tests
      - Framework / infra-level tests

    Prefer domain-scoped fixtures (e.g. customer_helper)
    when writing domain-specific tests.
    """

    def _get(entity_name: str):
        try:
            return all_resources.entities[entity_name].helper
        except KeyError:
            raise KeyError(
                f"Entity '{entity_name}' not found. "
                f"Available entities: {list(all_resources.entities.keys())}"
            )

    return _get


@pytest.fixture
def entity_dao(all_resources) -> Callable[[str], Any]:
    """
    Generic, cross-domain accessor for entity DAOs.

    Usage:
        dao = entity_dao("customers")
    """

    def _get(entity_name: str):
        try:
            return all_resources.entities[entity_name].dao
        except KeyError:
            raise KeyError(
                f"Entity '{entity_name}' not found. "
                f"Available entities: {list(all_resources.entities.keys())}"
            )

    return _get
