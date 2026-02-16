"""Order Status Enum."""

from enum import Enum


class OrderStatus(str, Enum):
    """Order status values."""
    
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
