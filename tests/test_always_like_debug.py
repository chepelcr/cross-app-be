"""Debug test for always_like functionality"""
from app.utils.search_utils import SearchUtils
from app.models.product import Product
from app.enums.product_search_filters import ProductSearchFilters

# Test parsing
print("Testing always_like functionality...")
print("="*60)

# Parse the search
filters, order = SearchUtils.parse_search_filter("name:Test", Product, ProductSearchFilters)

print(f"Number of filters: {len(filters)}")
print(f"Filter object: {filters[0] if filters else 'None'}")

# Check the criteria that was created
from app.utils.search_utils import SearchCriteria

# Let's manually create a criteria to see what happens
criteria = SearchCriteria(
    field="name",
    operation=SearchUtils._parse_criteria("name:Test", ProductSearchFilters).operation,
    value="Test",
    filter_enum_class=ProductSearchFilters
)

print(f"\nCriteria details:")
print(f"  field: {criteria.field}")
print(f"  operation: {criteria.operation}")
print(f"  value: {criteria.value}")
print(f"  search_filter: {criteria.search_filter}")
print(f"  always_like: {criteria.search_filter.always_like if criteria.search_filter else 'N/A'}")

# Now let's check what SQL is generated
from sqlalchemy import select, and_, create_engine
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
    where_clause = sql_str[where_start:where_start+200] if where_start != -1 else ""
    
    print(f"\nGenerated SQL:")
    print(f"  {where_clause}")
    print(f"  Uses ILIKE: {'ILIKE' in sql_str}")
    print(f"  Uses %%: {'%%' in sql_str}")
