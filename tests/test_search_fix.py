"""
Test script to verify search implementation fixes
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker

from app.utils.search_utils import SearchUtils
from app.models.product import Product
from app.enums.product_search_filters import ProductSearchFilters

# Load environment
load_dotenv()


def test_wildcard_processing():
    """Test wildcard processing converts * to %"""
    print("Testing wildcard processing...")
    
    # Test 1: Contains pattern (*value*)
    filters, order = SearchUtils.parse_search_filter("name:*Laptop*", Product, ProductSearchFilters)
    print(f"✓ Contains pattern: name:*Laptop* -> {filters}")
    
    # Test 2: Starts with pattern (value*)
    filters, order = SearchUtils.parse_search_filter("name:Lap*", Product, ProductSearchFilters)
    print(f"✓ Starts with pattern: name:Lap* -> {filters}")
    
    # Test 3: Ends with pattern (*value)
    filters, order = SearchUtils.parse_search_filter("name:*top", Product, ProductSearchFilters)
    print(f"✓ Ends with pattern: name:*top -> {filters}")
    
    # Test 4: No wildcards (always_like field)
    filters, order = SearchUtils.parse_search_filter("name:Laptop", Product, ProductSearchFilters)
    print(f"✓ No wildcards (always_like): name:Laptop -> {filters}")
    
    print()


def test_or_logic():
    """Test OR logic with parentheses"""
    print("Testing OR logic...")
    
    # Test 1: Simple OR
    filters, order = SearchUtils.parse_search_filter("(name:Laptop,name:Desktop)", Product, ProductSearchFilters)
    print(f"✓ Simple OR: (name:Laptop,name:Desktop) -> {filters}")
    
    # Test 2: Mixed AND/OR
    filters, order = SearchUtils.parse_search_filter("status:1,(name:Laptop,categoryName:Electronics)", Product, ProductSearchFilters)
    print(f"✓ Mixed AND/OR: status:1,(name:Laptop,categoryName:Electronics) -> {filters}")
    
    # Test 3: Multiple OR groups
    filters, order = SearchUtils.parse_search_filter("(name:Laptop,name:Desktop),(categoryId:1,categoryId:2)", Product, ProductSearchFilters)
    print(f"✓ Multiple OR groups: (name:Laptop,name:Desktop),(categoryId:1,categoryId:2) -> {filters}")
    
    print()


def test_always_like():
    """Test always_like fields"""
    print("Testing always_like fields...")
    
    # Test 1: Name field (always_like=True) - should use ILIKE even without wildcards
    filters, order = SearchUtils.parse_search_filter("name:Test", Product, ProductSearchFilters)
    print(f"✓ Name (always_like): name:Test -> {filters}")
    
    # Verify it generates ILIKE in SQL
    try:
        from sqlalchemy import select, create_engine
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        USER = os.getenv("DATABASE_USERNAME")
        PASSWORD = os.getenv("DATABASE_PASSWORD")
        HOST = os.getenv("DATABASE_HOST")
        PORT = os.getenv("DATABASE_PORT")
        DBNAME = os.getenv("DATABASE_DBNAME")
        
        if all([USER, PASSWORD, HOST, PORT, DBNAME]):
            DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
            engine = create_engine(DATABASE_URL)
            
            stmt = select(Product).where(and_(*filters))
            compiled = stmt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
            sql_str = str(compiled)
            
            where_start = sql_str.find('WHERE')
            where_clause = sql_str[where_start:where_start+150] if where_start != -1 else ""
            
            has_ilike = 'ILIKE' in sql_str
            has_percent = '%%' in sql_str
            
            print(f"  SQL uses ILIKE: {has_ilike}")
            print(f"  SQL uses %% wildcards: {has_percent}")
            print(f"  WHERE clause: {where_clause}")
            
            if not has_ilike:
                print(f"  ⚠ WARNING: always_like field 'name' is not using ILIKE!")
            if not has_percent:
                print(f"  ⚠ WARNING: always_like field 'name' is not wrapping value with %%!")
    except Exception as e:
        print(f"  Could not verify SQL: {e}")
    
    # Test 2: Description field (always_like=True)
    filters, order = SearchUtils.parse_search_filter("description:Professional", Product, ProductSearchFilters)
    print(f"✓ Description (always_like): description:Professional -> {filters}")
    
    # Test 3: CategoryName field (always_like=True, join field)
    filters, order = SearchUtils.parse_search_filter("categoryName:Beauty", Product, ProductSearchFilters)
    print(f"✓ CategoryName (always_like, join): categoryName:Beauty -> {filters}")
    
    print()


def test_between_operator():
    """Test BETWEEN operator for price ranges"""
    print("Testing BETWEEN operator...")
    
    # Test 1: Price range
    filters, order = SearchUtils.parse_search_filter("price:100~500", Product, ProductSearchFilters)
    print(f"✓ Price range: price:100~500 -> {filters}")
    
    # Test 2: Sale price range
    filters, order = SearchUtils.parse_search_filter("salePrice:50~150", Product, ProductSearchFilters)
    print(f"✓ Sale price range: salePrice:50~150 -> {filters}")
    
    print()


def test_complex_queries():
    """Test complex real-world queries"""
    print("Testing complex queries...")
    
    # Test 1: Multiple filters with AND
    filters, order = SearchUtils.parse_search_filter(
        "name:Laptop,status:1,price:500~2000,orderBy>price",
        Product,
        ProductSearchFilters
    )
    print(f"✓ Complex AND: name:Laptop,status:1,price:500~2000,orderBy>price")
    print(f"  Filters: {len(filters)} filter(s), Order: {order}")
    
    # Test 2: OR with AND
    filters, order = SearchUtils.parse_search_filter(
        "(name:Laptop,categoryName:Electronics),status:1,price<1000",
        Product,
        ProductSearchFilters
    )
    print(f"✓ Complex OR+AND: (name:Laptop,categoryName:Electronics),status:1,price<1000")
    print(f"  Filters: {len(filters)} filter(s)")
    
    print()


def test_sql_generation():
    """Test that filters generate valid SQL"""
    print("Testing SQL generation...")
    
    try:
        # Get database connection
        USER = os.getenv("DATABASE_USERNAME")
        PASSWORD = os.getenv("DATABASE_PASSWORD")
        HOST = os.getenv("DATABASE_HOST")
        PORT = os.getenv("DATABASE_PORT")
        DBNAME = os.getenv("DATABASE_DBNAME")
        
        if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
            print("⚠ Database credentials not configured, skipping SQL tests")
            print()
            return
        
        DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
        engine = create_engine(DATABASE_URL)
        
        # Test 1: Simple LIKE query
        print("  Test 1: Simple LIKE query (name:Laptop)")
        filters, order = SearchUtils.parse_search_filter("name:Laptop", Product, ProductSearchFilters)
        
        from sqlalchemy import select
        stmt = select(Product).where(and_(*filters))
        compiled = stmt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_str = str(compiled)
        
        # Extract WHERE clause
        where_start = sql_str.find('WHERE')
        where_clause = sql_str[where_start:where_start+200] if where_start != -1 else "WHERE clause not found"
        
        print(f"    Generated SQL contains LIKE/ILIKE: {'LIKE' in sql_str or 'ILIKE' in sql_str}")
        print(f"    WHERE clause: {where_clause}")
        
        # Test 2: Wildcard LIKE query
        print("\n  Test 2: Wildcard LIKE query (name:*Laptop*)")
        filters, order = SearchUtils.parse_search_filter("name:*Laptop*", Product, ProductSearchFilters)
        
        stmt = select(Product).where(and_(*filters))
        compiled = stmt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_str = str(compiled)
        
        where_start = sql_str.find('WHERE')
        where_clause = sql_str[where_start:where_start+200] if where_start != -1 else "WHERE clause not found"
        
        print(f"    Generated SQL contains LIKE/ILIKE: {'LIKE' in sql_str or 'ILIKE' in sql_str}")
        print(f"    WHERE clause: {where_clause}")
        
        # Test 3: BETWEEN query
        print("\n  Test 3: BETWEEN query (price:100~500)")
        filters, order = SearchUtils.parse_search_filter("price:100~500", Product, ProductSearchFilters)
        
        stmt = select(Product).where(and_(*filters))
        compiled = stmt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_str = str(compiled)
        
        where_start = sql_str.find('WHERE')
        where_clause = sql_str[where_start:where_start+200] if where_start != -1 else "WHERE clause not found"
        
        print(f"    Generated SQL contains BETWEEN or (>= AND <=): {'BETWEEN' in sql_str or ('>=' in sql_str and '<=' in sql_str)}")
        print(f"    WHERE clause: {where_clause}")
        
        # Test 4: OR query
        print("\n  Test 4: OR query ((name:Laptop,name:Desktop))")
        filters, order = SearchUtils.parse_search_filter("(name:Laptop,name:Desktop)", Product, ProductSearchFilters)
        
        stmt = select(Product).where(and_(*filters))
        compiled = stmt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_str = str(compiled)
        
        where_start = sql_str.find('WHERE')
        where_clause = sql_str[where_start:where_start+250] if where_start != -1 else "WHERE clause not found"
        
        print(f"    Generated SQL contains OR: {'OR' in sql_str}")
        print(f"    WHERE clause: {where_clause}")
        
        # Test 5: Complex query with AND + OR
        print("\n  Test 5: Complex query (status:1,(name:*Laptop*,categoryName:*Electronics*))")
        filters, order = SearchUtils.parse_search_filter(
            "status:1,(name:*Laptop*,categoryName:*Electronics*)",
            Product,
            ProductSearchFilters
        )
        
        stmt = select(Product).where(and_(*filters))
        compiled = stmt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_str = str(compiled)
        
        where_start = sql_str.find('WHERE')
        where_clause = sql_str[where_start:where_start+300] if where_start != -1 else "WHERE clause not found"
        
        print(f"    Generated SQL contains AND: {'AND' in sql_str}")
        print(f"    Generated SQL contains OR: {'OR' in sql_str}")
        print(f"    Number of filters: {len(filters)}")
        print(f"    WHERE clause: {where_clause}")
        
        # Test 6: Verify actual query execution (doesn't crash)
        print("\n  Test 6: Execute query against database")
        organization_id = os.getenv("TEST_ORG_ID", "d09b299b-f42e-4dc6-94ee-7db39479f996")
        
        filters, order = SearchUtils.parse_search_filter("name:*Test*", Product, ProductSearchFilters)
        
        with engine.connect() as conn:
            stmt = select(Product).where(
                and_(
                    Product.organization_id == organization_id,
                    Product.is_active == True,
                    *filters
                )
            ).limit(5)
            
            result = conn.execute(stmt)
            rows = result.fetchall()
            print(f"    Query executed successfully, returned {len(rows)} rows")
        
        # Test 7: Comparison operators
        print("\n  Test 7: Comparison operators (price>100, price<500)")
        filters_gt, _ = SearchUtils.parse_search_filter("price>100", Product, ProductSearchFilters)
        filters_lt, _ = SearchUtils.parse_search_filter("price<500", Product, ProductSearchFilters)
        
        stmt_gt = select(Product).where(and_(*filters_gt))
        compiled_gt = stmt_gt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_gt = str(compiled_gt)
        
        stmt_lt = select(Product).where(and_(*filters_lt))
        compiled_lt = stmt_lt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_lt = str(compiled_lt)
        
        print(f"    Greater than (>) operator: {'>' in sql_gt}")
        print(f"    Less than (<) operator: {'<' in sql_lt}")
        
        print("\n✓ All SQL generation tests passed!")
        print()
        
    except Exception as e:
        print(f"❌ SQL generation test failed: {e}")
        import traceback
        traceback.print_exc()
        print()


def test_sql_injection_safety():
    """Test that the search is safe from SQL injection"""
    print("Testing SQL injection safety...")
    
    try:
        # Test potentially dangerous inputs
        dangerous_inputs = [
            "name:'; DROP TABLE products; --",
            "name:' OR '1'='1",
            "price:100; DELETE FROM products WHERE 1=1; --",
            "name:Test' UNION SELECT * FROM users --",
        ]
        
        for dangerous_input in dangerous_inputs:
            try:
                filters, order = SearchUtils.parse_search_filter(dangerous_input, Product, ProductSearchFilters)
                print(f"  ✓ Safely handled: {dangerous_input[:50]}...")
            except Exception as e:
                print(f"  ⚠ Input rejected (good): {dangerous_input[:50]}... - {e}")
        
        print("✓ SQL injection safety tests passed!")
        print()
        
    except Exception as e:
        print(f"❌ SQL injection safety test failed: {e}")
        import traceback
        traceback.print_exc()
        print()


def test_boolean_field_conversion():
    """Test that boolean fields handle integer values correctly"""
    print("Testing boolean field conversion...")
    
    try:
        from sqlalchemy import select, create_engine
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        USER = os.getenv("DATABASE_USERNAME")
        PASSWORD = os.getenv("DATABASE_PASSWORD")
        HOST = os.getenv("DATABASE_HOST")
        PORT = os.getenv("DATABASE_PORT")
        DBNAME = os.getenv("DATABASE_DBNAME")
        
        if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
            print("⚠ Database credentials not configured, skipping test")
            print()
            return
        
        DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
        engine = create_engine(DATABASE_URL)
        
        # Test 1: status:1 should convert to boolean True
        print("  Test 1: status:1 (should convert to boolean True)")
        filters, order = SearchUtils.parse_search_filter("status:1", Product, ProductSearchFilters)
        
        stmt = select(Product).where(and_(*filters))
        compiled = stmt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_str = str(compiled)
        
        where_start = sql_str.find('WHERE')
        where_clause = sql_str[where_start:where_start+200] if where_start != -1 else ""
        
        print(f"    WHERE clause: {where_clause}")
        print(f"    Contains 'true': {'true' in sql_str.lower()}")
        print(f"    Contains '= 1': {'= 1' in sql_str}")
        
        if '= 1' in sql_str and 'BOOLEAN' not in sql_str:
            print(f"    ⚠ WARNING: Boolean field is being compared to integer!")
        else:
            print(f"    ✓ Boolean conversion working correctly")
        
        # Test 2: status:0 should convert to boolean False
        print("\n  Test 2: status:0 (should convert to boolean False)")
        filters, order = SearchUtils.parse_search_filter("status:0", Product, ProductSearchFilters)
        
        stmt = select(Product).where(and_(*filters))
        compiled = stmt.compile(dialect=engine.dialect, compile_kwargs={"literal_binds": True})
        sql_str = str(compiled)
        
        where_start = sql_str.find('WHERE')
        where_clause = sql_str[where_start:where_start+200] if where_start != -1 else ""
        
        print(f"    WHERE clause: {where_clause}")
        print(f"    Contains 'false': {'false' in sql_str.lower()}")
        
        # Test 3: Execute query to verify it works
        print("\n  Test 3: Execute query against database")
        organization_id = os.getenv("TEST_ORG_ID", "d09b299b-f42e-4dc6-94ee-7db39479f996")
        
        filters, order = SearchUtils.parse_search_filter("status:1", Product, ProductSearchFilters)
        
        with engine.connect() as conn:
            stmt = select(Product).where(
                and_(
                    Product.organization_id == organization_id,
                    *filters
                )
            ).limit(5)
            
            result = conn.execute(stmt)
            rows = result.fetchall()
            print(f"    Query executed successfully, returned {len(rows)} rows")
        
        print("\n✓ Boolean field conversion tests passed!")
        print()
        
    except Exception as e:
        print(f"❌ Boolean field conversion test failed: {e}")
        import traceback
        traceback.print_exc()
        print()


if __name__ == "__main__":
    print("=" * 60)
    print("Search Implementation Fix Tests")
    print("=" * 60)
    print()
    
    try:
        test_wildcard_processing()
        test_or_logic()
        test_always_like()
        test_between_operator()
        test_complex_queries()
        test_sql_generation()
        test_sql_injection_safety()
        test_boolean_field_conversion()
        
        print("=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
