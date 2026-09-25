from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar


T = TypeVar("T")


class BaseFactory(ABC, Generic[T]):
    """
    Base class for in-memory test-data factories.

    Factories are responsible for generating valid, unique test data.

    They must NOT:
        - call APIs
        - access the database
        - register cleanup resources
        - depend on pytest fixtures
        - perform provisioning

    A factory produces test data only.
    """

    @abstractmethod
    def build(self, **overrides: Any) -> T:
        """
        Build a valid test-data object.

        Args:
            **overrides:
                Fields that should replace generated defaults.

        Returns:
            T:
                Domain-specific test-data object.
        -------------------------------------------------------
        This method is a blueprint and cannot be used directly.
        Any child class that inherits from this class must
        provide its own implementation of this method, or Python
        will raise an error when you try to instantiate it.
        """
        raise NotImplementedError
