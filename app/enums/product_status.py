"""
Product status enumeration.

Defines the possible status values for products in the system.
"""

from enum import IntEnum


class ProductStatus(IntEnum):
    """
    Product status codes.
    
    Values:
        ACTIVE (1): Product is active and available
        INACTIVE (2): Product is inactive but not deleted
        DELETED (3): Product is soft-deleted
    """
    
    ACTIVE = 1
    INACTIVE = 2
    DELETED = 3
    
    @classmethod
    def is_valid(cls, status: int) -> bool:
        """
        Check if a status value is valid.
        
        Args:
            status: The status value to validate
            
        Returns:
            True if the status is valid, False otherwise
        """
        return status in [s.value for s in cls]
    
    @classmethod
    def get_valid_statuses(cls) -> list[int]:
        """
        Get list of all valid status values.
        
        Returns:
            List of valid status integers
        """
        return [s.value for s in cls]
    
    @classmethod
    def from_boolean(cls, is_active: bool) -> int:
        """
        Convert boolean is_active to status code.
        
        Args:
            is_active: Boolean active status
            
        Returns:
            ACTIVE (1) if True, INACTIVE (2) if False
        """
        return cls.ACTIVE if is_active else cls.INACTIVE
    
    def to_boolean(self) -> bool:
        """
        Convert status to boolean (for backward compatibility).
        
        Returns:
            True if ACTIVE, False otherwise
        """
        return self == ProductStatus.ACTIVE
    
    @property
    def label(self) -> str:
        """Get human-readable label for the status."""
        labels = {
            ProductStatus.ACTIVE: "Active",
            ProductStatus.INACTIVE: "Inactive",
            ProductStatus.DELETED: "Deleted"
        }
        return labels.get(self, "Unknown")
