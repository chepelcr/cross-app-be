import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()


class AppConfig:
    """Simple configuration client using environment variables"""

    @classmethod
    def get_key(cls, key: str, default: Any = None) -> Any:
        """
        Get configuration value from environment variables
        
        Supports dot notation:
        - get_key("database.host") -> DATABASE_HOST
        - get_key("database.port", 5432) -> DATABASE_PORT with default
        
        Args:
            key: Configuration key in dot notation
            default: Default value if not found
            
        Returns:
            Configuration value or default
        """
        env_key = key.replace(".", "_").upper()
        value = os.getenv(env_key)
        
        if value is None:
            return default
            
        # Try to convert to int if it looks like a number
        if isinstance(default, int) and value.isdigit():
            return int(value)
            
        return value
