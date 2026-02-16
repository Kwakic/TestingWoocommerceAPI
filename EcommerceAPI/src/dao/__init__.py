# To ensure this works, your EcommerceAPI/src/dao/__init__.py must expose those classes, like this:

from EcommerceAPI.src.dao.customers.customers_dao import CustomersDAO
from EcommerceAPI.src.dao.products.products_dao import ProductsDAO
from EcommerceAPI.src.dao.coupons.coupons_dao import CouponsDAO
from EcommerceAPI.src.dao.orders.orders_dao import OrdersDao

__all__ = ["CustomersDAO", "ProductsDAO", "CouponsDAO", "OrdersDao"]

# This allows wildcard or grouped imports to resolve correctly.

