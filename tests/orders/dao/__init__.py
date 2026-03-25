# To ensure this works, your EcommerceAPI/src/dao/__init__.py must expose those classes, like this:

from .customers_dao import CustomersDAO
from .products_dao import ProductsDAO
from .coupons_dao import CouponsDAO
from .orders_dao import OrdersDao

__all__ = ["CustomersDAO", "ProductsDAO", "CouponsDAO", "OrdersDao"]

# This allows wildcard or grouped imports to resolve correctly.
