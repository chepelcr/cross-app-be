"""Quick test script for session products functionality."""
import sys
sys.path.insert(0, '.')

from app.repositories.session_product_repository import SessionProductRepository

# Test that the repository can be instantiated
try:
    with SessionProductRepository() as repo:
        print("✅ SessionProductRepository instantiated successfully")
        print(f"✅ Model: {repo.model.__name__}")
        print(f"✅ Table: {repo.model.__tablename__}")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
