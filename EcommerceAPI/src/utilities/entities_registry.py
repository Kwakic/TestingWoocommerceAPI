from typing import Dict, Any, Iterator, Optional, TYPE_CHECKING, Iterable, TypeVar, Generic
from collections.abc import Mapping

T = TypeVar("T")

if TYPE_CHECKING:
    # Use a non-runtime import for typing help. Adjust path if your test package root differs.
    from tests import EntityBundle  # noqa: F401


class EntitiesRegistry(Mapping[str, T], Generic[T]):
    """
    Generic Mapping[str, T] wrapper that exposes valid identifier keys as attributes.

    Purpose:
      - Reusable test helper for any dict-like mapping keyed by entity/resource name.
      - Implements Mapping so it is accepted wherever Mapping[str, SomeType] is expected.
      - Exposes attribute access for keys that are valid Python identifiers (e.g. registry.customers).
      - Keeps runtime behavior minimal and provides an explicit `.set()` for controlled updates.

    Usage examples:
      - For entity bundles:
          from EcommerceAPI.tests.helpers.entities_registry import EntitiesRegistry
          entities = EntitiesRegistry[EntityBundle].from_dict(raw_entity_dict)
          bundle = entities["customers"]            # dict-style
          bundle2 = entities.customers              # attribute-style (if 'customers' is a valid identifier)

      - For generic mapping (e.g., shared_api_resources):
          wrapper = EntitiesRegistry[Any].from_dict(shared_api_resources_dict)
          wrapper.register_resource(...)           # attribute-style access to dict key 'register_resource'
    """

    def __init__(self, mapping: Optional[Dict[str, T]] = None):
        # Keep internal mapping private to avoid accidental external mutation.
        self._map: Dict[str, T] = dict(mapping or {})

        # Expose attribute-style access for keys that are valid Python identifiers.
        for k, v in self._map.items():
            if (
                    isinstance(k, str)
                    and k.isidentifier()
                    and not hasattr(self, k)
                    and k not in ("keys", "items", "values", "get")
            ):
                object.__setattr__(self, k, v)

    # Mapping protocol methods

    def __getitem__(self, key: str) -> T:
        """Return the value stored under `key` (KeyError if missing)."""
        return self._map[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._map)

    def __len__(self) -> int:
        return len(self._map)

    # Convenience helpers commonly used in tests

    def keys(self) -> Iterable[str]:
        return self._map.keys()

    def items(self):
        return self._map.items()

    def values(self):
        return self._map.values()

    def get(self, key: str, default: Any = None) -> Any:
        return self._map.get(key, default)

    def __contains__(self, key: object) -> bool:
        return key in self._map

    def __repr__(self) -> str:
        return f"EntitiesRegistry({list(self._map.keys())})"

    # Factory

    @classmethod
    def from_dict(cls, d: Dict[str, T]) -> "EntitiesRegistry[T]":
        """Create an EntitiesRegistry wrapping a dict[str, T]."""
        return cls(mapping=d)

    # Controlled mutation helper

    def set(self, key: str, value: T) -> None:
        """
        Add or update an item at runtime.

        Ensures attribute-access remains available for valid identifier keys.
        """
        self._map[key] = value
        if isinstance(key, str) and key.isidentifier():
            object.__setattr__(self, key, value)