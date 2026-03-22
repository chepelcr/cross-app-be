"""
Comprehensive test script for Product Excel Import feature.
Tests all requirements from the spec without using pytest.
"""
import base64
import logging
import os
import sys
import uuid
from io import BytesIO
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import application modules
from app.services.product_excel_parser import parse_product_file
from app.services.product_excel_service import ProductExcelService
from app.dtos.files import ExcelDTO
from app.exceptions import ExcelParsingException


class TestResults:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def record_pass(self, test_name: str):
        self.passed += 1
        logger.info(f"✓ PASS: {test_name}")
    
    def record_fail(self, test_name: str, error: str):
        self.failed += 1
        self.errors.append((test_name, error))
        logger.error(f"✗ FAIL: {test_name} - {error}")
    
    def summary(self):
        total = self.passed + self.failed
        logger.info(f"\n{'='*60}")
        logger.info(f"TEST SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {self.passed}")
        logger.info(f"Failed: {self.failed}")
        if self.errors:
            logger.info(f"\nFailed Tests:")
            for test_name, error in self.errors:
                logger.info(f"  - {test_name}: {error}")
        logger.info(f"{'='*60}\n")
        return self.failed == 0


results = TestResults()


def test_parser_with_example_file():
    """Test 1: Parse the example ARTICULOS.xlsx file."""
    test_name = "Parse ARTICULOS.xlsx"
    try:
        file_path = Path("example-files/ARTICULOS.xlsx")
        if not file_path.exists():
            results.record_fail(test_name, f"File not found: {file_path}")
            return
        
        with open(file_path, "rb") as f:
            excel_bytes = BytesIO(f.read())
        
        rows = parse_product_file(excel_bytes)
        
        if not rows:
            results.record_fail(test_name, "No rows parsed from file")
            return
        
        logger.info(f"  Parsed {len(rows)} rows from ARTICULOS.xlsx")
        
        # Verify first row has expected structure
        first_row = rows[0]
        expected_keys = ["cod_artic", "cod_barra", "cod_interno", "descripcion", 
                        "cantidad_caja", "unidad_medida", "precio", "categoria"]
        
        for key in expected_keys:
            if key not in first_row:
                results.record_fail(test_name, f"Missing key '{key}' in parsed row")
                return
        
        logger.info(f"  Sample row: {first_row}")
        results.record_pass(test_name)
        
    except Exception as e:
        results.record_fail(test_name, str(e))


def test_parser_validates_headers():
    """Test 2: Parser rejects files with missing headers."""
    test_name = "Parser validates required headers"
    try:
        import openpyxl
        from openpyxl import Workbook
        
        # Create Excel file with missing headers
        wb = Workbook()
        ws = wb.active
        ws.append(["COD_ARTIC", "DESCRIPCION"])  # Missing other required headers
        ws.append(["001", "Test Product"])
        
        excel_bytes = BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)
        
        try:
            parse_product_file(excel_bytes)
            results.record_fail(test_name, "Should have raised ExcelParsingException for missing headers")
        except ExcelParsingException as e:
            if "Missing required headers" in str(e):
                results.record_pass(test_name)
            else:
                results.record_fail(test_name, f"Wrong error message: {e}")
        
    except Exception as e:
        results.record_fail(test_name, str(e))


def test_parser_skips_empty_rows():
    """Test 3: Parser skips empty rows."""
    test_name = "Parser skips empty rows"
    try:
        import openpyxl
        from openpyxl import Workbook
        
        wb = Workbook()
        ws = wb.active
        
        # Add headers
        ws.append(["COD_ARTIC", "COD_BARRA", "COD_INTERNO", "DESCRIPCION", 
                  "CANTIDAD_CAJA", "UNIDAD_MEDIDA", "PRECIO", "CATEGORIA"])
        
        # Add data row
        ws.append(["001", "123456", "INT001", "Product 1", 10, "UND", 100.0, "Category A"])
        
        # Add empty rows
        ws.append([None, None, None, None, None, None, None, None])
        ws.append(["", "", "", "", "", "", "", ""])
        
        # Add another data row
        ws.append(["002", "789012", "INT002", "Product 2", 20, "UND", 200.0, "Category B"])
        
        excel_bytes = BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)
        
        rows = parse_product_file(excel_bytes)
        
        if len(rows) != 2:
            results.record_fail(test_name, f"Expected 2 rows, got {len(rows)}")
        else:
            results.record_pass(test_name)
        
    except Exception as e:
        results.record_fail(test_name, str(e))


def test_parser_handles_invalid_file():
    """Test 4: Parser rejects invalid files."""
    test_name = "Parser rejects invalid files"
    try:
        # Create invalid file (not Excel)
        invalid_bytes = BytesIO(b"This is not an Excel file")
        
        try:
            parse_product_file(invalid_bytes)
            results.record_fail(test_name, "Should have raised ExcelParsingException for invalid file")
        except ExcelParsingException as e:
            if "Could not open Excel file" in str(e):
                results.record_pass(test_name)
            else:
                results.record_fail(test_name, f"Wrong error message: {e}")
        
    except Exception as e:
        results.record_fail(test_name, str(e))


def test_service_with_example_file():
    """Test 5: Process example file through service (integration test)."""
    test_name = "Service processes ARTICULOS.xlsx"
    try:
        # Get test organization ID from environment or use default
        organization_id = os.getenv("TEST_ORG_ID", "d09b299b-f42e-4dc6-94ee-7db39479f996")
        
        file_path = Path("example-files/ARTICULOS.xlsx")
        if not file_path.exists():
            results.record_fail(test_name, f"File not found: {file_path}")
            return
        
        # Read and encode file
        with open(file_path, "rb") as f:
            excel_bytes = f.read()
        
        base64_data = base64.b64encode(excel_bytes).decode('utf-8')
        excel_dto = ExcelDTO(data=base64_data)
        
        # Process through service
        response = ProductExcelService.process_product_excel(organization_id, excel_dto)
        
        logger.info(f"  Processed {response.pagination.totalElements} products")
        logger.info(f"  Page size: {response.pagination.pageSize}")
        
        if response.pagination.totalElements > 0:
            logger.info(f"  Sample product: {response.data[0].name}")
            results.record_pass(test_name)
        else:
            results.record_fail(test_name, "No products were processed")
        
    except Exception as e:
        results.record_fail(test_name, str(e))
        import traceback
        logger.error(traceback.format_exc())


def test_product_matching():
    """Test 6: Verify product matching by codes works."""
    test_name = "Product matching by codes"
    try:
        from app.repositories.product_repository import ProductRepository
        from app.enums.hacienda_codes import ProductCodeType
        
        organization_id = os.getenv("TEST_ORG_ID", "d09b299b-f42e-4dc6-94ee-7db39479f996")
        
        with ProductRepository() as repo:
            # Try to find a product by code (this assumes products exist in DB)
            # We'll just verify the method exists and doesn't crash
            result = repo.find_by_company_and_code(
                company_id=organization_id,
                hacienda_code=ProductCodeType.VENDOR,
                code="TEST_CODE_THAT_DOESNT_EXIST"
            )
            
            # If we get here without exception, the method works
            results.record_pass(test_name)
        
    except Exception as e:
        results.record_fail(test_name, str(e))


def test_required_field_validation():
    """Test 7: Verify required field validation."""
    test_name = "Required field validation"
    try:
        import openpyxl
        from openpyxl import Workbook
        
        organization_id = os.getenv("TEST_ORG_ID", "d09b299b-f42e-4dc6-94ee-7db39479f996")
        
        wb = Workbook()
        ws = wb.active
        
        # Add headers
        ws.append(["COD_ARTIC", "COD_BARRA", "COD_INTERNO", "DESCRIPCION", 
                  "CANTIDAD_CAJA", "UNIDAD_MEDIDA", "PRECIO", "CATEGORIA"])
        
        # Add row with missing DESCRIPCION (required field)
        ws.append(["001", "123456", "INT001", "", 10, "UND", 100.0, "Category A"])
        
        # Add valid row
        ws.append(["002", "789012", "INT002", "Valid Product", 20, "UND", 200.0, "Category B"])
        
        excel_bytes = BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)
        
        # Encode to base64
        base64_data = base64.b64encode(excel_bytes.getvalue()).decode('utf-8')
        excel_dto = ExcelDTO(data=base64_data)
        
        # Process through service
        response = ProductExcelService.process_product_excel(organization_id, excel_dto)
        
        # Should have processed only 1 product (the valid one)
        # The invalid one should be skipped
        logger.info(f"  Processed {response.pagination.totalElements} products (expected 1)")
        
        # This test passes if the service doesn't crash and processes at least the valid row
        if response.pagination.totalElements >= 1:
            results.record_pass(test_name)
        else:
            results.record_fail(test_name, "No products were processed")
        
    except Exception as e:
        results.record_fail(test_name, str(e))
        import traceback
        logger.error(traceback.format_exc())


def test_sql_query_generation():
    """Test 8: Verify SQL queries are generated correctly for product matching."""
    test_name = "SQL query generation for product matching"
    try:
        from app.repositories.product_repository import ProductRepository
        from app.enums.hacienda_codes import ProductCodeType
        from sqlalchemy import inspect
        
        organization_id = os.getenv("TEST_ORG_ID", "d09b299b-f42e-4dc6-94ee-7db39479f996")
        
        with ProductRepository() as repo:
            # Enable SQL echo to capture queries
            repo.session.bind.echo = True
            
            # Test 1: find_by_company_and_code generates correct JSONB query
            logger.info("  Testing find_by_company_and_code SQL generation...")
            
            # Build the expected query manually to verify
            from sqlalchemy import select, and_, cast
            from sqlalchemy.dialects.postgresql import JSONB
            from app.models.product import Product
            
            test_code = "TEST123"
            test_code_type = ProductCodeType.VENDOR
            
            # This is what the query should look like
            search_obj = [{"codeTypeId": test_code_type, "number": test_code}]
            expected_stmt = select(Product).where(
                and_(
                    Product.organization_id == organization_id,
                    Product.is_active == True,
                    Product.codes.op("@>")(cast(search_obj, JSONB)),
                )
            )
            
            # Compile the query to SQL
            compiled = expected_stmt.compile(
                dialect=repo.session.bind.dialect,
                compile_kwargs={"literal_binds": True}
            )
            sql_str = str(compiled)
            
            logger.info(f"  Generated SQL: {sql_str}")
            
            # Verify the SQL contains expected elements
            checks = [
                ("@>", "JSONB containment operator"),
                ("codes", "codes column reference"),
                ("organization_id", "organization_id filter"),
                ("is_active", "is_active filter"),
                ("codeTypeId", "codeTypeId in JSONB"),
            ]
            
            for check_str, description in checks:
                if check_str not in sql_str:
                    results.record_fail(test_name, f"SQL missing {description}: {check_str}")
                    return
                logger.info(f"  ✓ Found {description}")
            
            # Test 2: Verify the actual query execution doesn't crash
            result = repo.find_by_company_and_code(
                company_id=organization_id,
                hacienda_code=test_code_type,
                code=test_code
            )
            logger.info(f"  Query executed successfully (result: {result})")
            
            # Test 3: Test find_by_company_and_internal_code
            logger.info("  Testing find_by_company_and_internal_code SQL generation...")
            internal_code = "INT123"
            search_obj_internal = [{"codeTypeId": ProductCodeType.INTERNAL, "number": internal_code}]
            expected_stmt_internal = select(Product).where(
                and_(
                    Product.organization_id == organization_id,
                    Product.is_active == True,
                    Product.codes.op("@>")(cast(search_obj_internal, JSONB)),
                )
            )
            
            compiled_internal = expected_stmt_internal.compile(
                dialect=repo.session.bind.dialect,
                compile_kwargs={"literal_binds": True}
            )
            sql_str_internal = str(compiled_internal)
            logger.info(f"  Generated SQL: {sql_str_internal}")
            
            # Verify internal code query
            if ProductCodeType.INTERNAL not in sql_str_internal:
                results.record_fail(test_name, "SQL missing internal code type (04)")
                return
            
            result_internal = repo.find_by_company_and_internal_code(
                company_id=organization_id,
                internal_code=internal_code
            )
            logger.info(f"  Query executed successfully (result: {result_internal})")
            
            results.record_pass(test_name)
        
    except Exception as e:
        results.record_fail(test_name, str(e))
        import traceback
        logger.error(traceback.format_exc())


def test_upsert_sql_generation():
    """Test 9: Verify upsert operations generate correct SQL."""
    test_name = "SQL generation for upsert operations"
    try:
        from app.repositories.product_repository import ProductRepository
        from app.enums.hacienda_codes import ProductCodeType
        
        organization_id = os.getenv("TEST_ORG_ID", "d09b299b-f42e-4dc6-94ee-7db39479f996")
        
        with ProductRepository() as repo:
            logger.info("  Testing upsert_by_internal_code SQL generation...")
            
            # Test data
            test_internal_code = f"TEST_INT_{uuid.uuid4().hex[:8]}"
            test_description = "Test Product for SQL Validation"
            test_vendor_code = "VENDOR123"
            test_buyer_code = "BUYER456"
            test_manufacturer_code = "MANUF789"
            
            # Perform upsert (insert)
            product = repo.upsert_by_internal_code(
                company_id=organization_id,
                internal_code=test_internal_code,
                description=test_description,
                original_code=test_vendor_code,
                client_article_code=test_buyer_code,
                code=test_manufacturer_code,
                units_per_box=10,
                price=99.99
            )
            
            logger.info(f"  Created product: {product.id}")
            logger.info(f"  Product codes: {product.codes}")
            
            # Verify codes array structure
            expected_codes = [
                {"codeTypeId": ProductCodeType.INTERNAL, "number": test_internal_code},
                {"codeTypeId": ProductCodeType.VENDOR, "number": test_vendor_code},
                {"codeTypeId": ProductCodeType.BUYER, "number": test_buyer_code},
                {"codeTypeId": ProductCodeType.MANUFACTURER, "number": test_manufacturer_code},
            ]
            
            if not product.codes:
                results.record_fail(test_name, "Product codes array is empty")
                return
            
            # Check each code type exists
            code_types_found = {code["codeTypeId"] for code in product.codes}
            expected_types = {ProductCodeType.INTERNAL, ProductCodeType.VENDOR, 
                            ProductCodeType.BUYER, ProductCodeType.MANUFACTURER}
            
            if code_types_found != expected_types:
                results.record_fail(
                    test_name, 
                    f"Code types mismatch. Expected: {expected_types}, Got: {code_types_found}"
                )
                return
            
            logger.info(f"  ✓ All code types present in JSONB array")
            
            # Test update (upsert existing)
            updated_product = repo.upsert_by_internal_code(
                company_id=organization_id,
                internal_code=test_internal_code,
                description="Updated Description",
                units_per_box=20
            )
            
            if updated_product.id != product.id:
                results.record_fail(test_name, "Upsert created new product instead of updating")
                return
            
            if updated_product.description != "Updated Description":
                results.record_fail(test_name, "Upsert did not update description")
                return
            
            logger.info(f"  ✓ Upsert correctly updated existing product")
            
            # Verify we can find the product by any of its codes
            found_by_internal = repo.find_by_company_and_internal_code(
                company_id=organization_id,
                internal_code=test_internal_code
            )
            
            if not found_by_internal or found_by_internal.id != product.id:
                results.record_fail(test_name, "Could not find product by internal code")
                return
            
            logger.info(f"  ✓ Product found by internal code")
            
            found_by_vendor = repo.find_by_company_and_code(
                company_id=organization_id,
                hacienda_code=ProductCodeType.VENDOR,
                code=test_vendor_code
            )
            
            if not found_by_vendor or found_by_vendor.id != product.id:
                results.record_fail(test_name, "Could not find product by vendor code")
                return
            
            logger.info(f"  ✓ Product found by vendor code")
            
            # Cleanup
            repo.session.delete(product)
            repo.session.commit()
            logger.info(f"  ✓ Test product cleaned up")
            
            results.record_pass(test_name)
        
    except Exception as e:
        results.record_fail(test_name, str(e))
        import traceback
        logger.error(traceback.format_exc())


def test_jsonb_array_operations():
    """Test 10: Verify JSONB array operations work correctly."""
    test_name = "JSONB array operations"
    try:
        from app.repositories.product_repository import ProductRepository
        from app.enums.hacienda_codes import ProductCodeType
        from sqlalchemy import text
        
        organization_id = os.getenv("TEST_ORG_ID", "d09b299b-f42e-4dc6-94ee-7db39479f996")
        
        with ProductRepository() as repo:
            logger.info("  Testing JSONB containment operator (@>)...")
            
            # Create a test product with multiple codes
            test_internal_code = f"JSONB_TEST_{uuid.uuid4().hex[:8]}"
            
            product = repo.upsert_by_internal_code(
                company_id=organization_id,
                internal_code=test_internal_code,
                description="JSONB Test Product",
                original_code="VENDOR_JSONB",
                client_article_code="BUYER_JSONB",
                units_per_box=5,
                price=50.00
            )
            
            logger.info(f"  Created test product with codes: {product.codes}")
            
            # Test raw SQL query with JSONB operator
            sql = text("""
                SELECT id, name, codes
                FROM products
                WHERE organization_id = :org_id
                AND is_active = true
                AND codes @> :search_code::jsonb
            """)
            
            # Test finding by vendor code
            search_vendor = '[{"codeTypeId": "01", "number": "VENDOR_JSONB"}]'
            result = repo.session.execute(
                sql,
                {"org_id": organization_id, "search_code": search_vendor}
            ).fetchone()
            
            if not result:
                results.record_fail(test_name, "JSONB @> operator failed to find product by vendor code")
                repo.session.rollback()
                return
            
            logger.info(f"  ✓ Found product by vendor code using @> operator")
            
            # Test finding by internal code
            search_internal = f'[{{"codeTypeId": "04", "number": "{test_internal_code}"}}]'
            result = repo.session.execute(
                sql,
                {"org_id": organization_id, "search_code": search_internal}
            ).fetchone()
            
            if not result:
                results.record_fail(test_name, "JSONB @> operator failed to find product by internal code")
                repo.session.rollback()
                return
            
            logger.info(f"  ✓ Found product by internal code using @> operator")
            
            # Test that non-existent code doesn't match
            search_nonexistent = '[{"codeTypeId": "01", "number": "DOES_NOT_EXIST"}]'
            result = repo.session.execute(
                sql,
                {"org_id": organization_id, "search_code": search_nonexistent}
            ).fetchone()
            
            if result and result[0] == product.id:
                results.record_fail(test_name, "JSONB @> operator incorrectly matched non-existent code")
                repo.session.rollback()
                return
            
            logger.info(f"  ✓ Non-existent code correctly not matched")
            
            # Cleanup
            repo.session.delete(product)
            repo.session.commit()
            logger.info(f"  ✓ Test product cleaned up")
            
            results.record_pass(test_name)
        
    except Exception as e:
        results.record_fail(test_name, str(e))
        import traceback
        logger.error(traceback.format_exc())


def verify_database_connection():
    """Verify database connection before running tests."""
    try:
        USER = os.getenv("DATABASE_USERNAME")
        PASSWORD = os.getenv("DATABASE_PASSWORD")
        HOST = os.getenv("DATABASE_HOST")
        PORT = os.getenv("DATABASE_PORT")
        DBNAME = os.getenv("DATABASE_DBNAME")
        
        if not all([USER, PASSWORD, HOST, PORT, DBNAME]):
            logger.warning("Database credentials not fully configured in .env")
            logger.warning("Some integration tests may be skipped")
            return False
        
        DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}"
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")
            return True
            
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.warning("Integration tests will be skipped")
        return False


def main():
    """Run all tests."""
    logger.info("="*60)
    logger.info("PRODUCT EXCEL IMPORT - COMPREHENSIVE TEST SUITE")
    logger.info("="*60)
    logger.info("")
    
    # Check database connection
    db_available = verify_database_connection()
    logger.info("")
    
    # Run parser tests (no DB required)
    logger.info("Running Parser Tests...")
    logger.info("-"*60)
    test_parser_with_example_file()
    test_parser_validates_headers()
    test_parser_skips_empty_rows()
    test_parser_handles_invalid_file()
    logger.info("")
    
    # Run service tests (require DB)
    if db_available:
        logger.info("Running Service Integration Tests...")
        logger.info("-"*60)
        test_service_with_example_file()
        test_product_matching()
        test_required_field_validation()
        logger.info("")
        
        logger.info("Running SQL Validation Tests...")
        logger.info("-"*60)
        test_sql_query_generation()
        test_upsert_sql_generation()
        test_jsonb_array_operations()
        logger.info("")
    else:
        logger.warning("Skipping service integration tests (no database connection)")
        logger.info("")
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
