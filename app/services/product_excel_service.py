from __future__ import annotations

import base64
import logging
from io import BytesIO
from typing import Optional

from app.dtos.files import ExcelDTO
from app.dtos.responses.pagination_dto import PaginationResponse
from app.dtos.responses.product_dto import ProductListResponse
from app.enums.hacienda_codes import ProductCodeType
from app.exceptions import ExcelParsingException
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.services.product_excel_parser import parse_product_file

logger = logging.getLogger(__name__)


class ProductExcelService:
    """Service for processing product Excel imports."""

    @staticmethod
    def process_product_excel(
        organization_id: str, 
        excel_dto: ExcelDTO
    ) -> ProductListResponse:
        """
        Process Excel file and create/update products.

        Args:
            organization_id: Organization identifier
            excel_dto: DTO containing base64-encoded Excel file

        Returns:
            ProductListResponse with all created/updated products

        Raises:
            ExcelParsingException: If file is invalid or headers missing
            ValueError: If base64 decoding fails
        """
        # Decode base64 Excel file
        try:
            excel_bytes = base64.b64decode(excel_dto.data)
            excel_file = BytesIO(excel_bytes)
        except Exception as e:
            logger.error(f"Failed to decode base64 Excel file: {e}")
            raise ValueError(f"Invalid base64 data: {e}")

        # Parse Excel file
        try:
            rows = parse_product_file(excel_file)
        except ExcelParsingException as e:
            logger.error(f"Excel parsing failed: {e}")
            raise

        # Process each row independently
        products = []
        created_count = 0
        updated_count = 0
        error_count = 0
        
        with ProductRepository() as repo:
            for idx, row in enumerate(rows, start=2):  # Start at 2 (row 1 is headers)
                try:
                    # Validate required fields
                    cod_artic = row.get("cod_artic", "").strip()
                    descripcion = row.get("descripcion", "").strip()
                    
                    if not cod_artic and not descripcion:
                        logger.warning(f"Row {idx}: Missing required fields COD_ARTIC and DESCRIPCION, skipping")
                        error_count += 1
                        continue
                    
                    if not descripcion:
                        logger.warning(f"Row {idx}: Missing required field DESCRIPCION, skipping")
                        error_count += 1
                        continue
                    
                    # Find existing product by codes
                    existing_product = ProductExcelService._find_existing_product(
                        organization_id=organization_id,
                        cod_artic=cod_artic,
                        cod_barra=row.get("cod_barra", "").strip(),
                        cod_interno=row.get("cod_interno", "").strip(),
                        repo=repo,
                    )
                    
                    if existing_product:
                        # Update existing product
                        updated = ProductExcelService._update_product_category(
                            product=existing_product,
                            category_name=row.get("categoria", ""),
                            repo=repo,
                        )
                        products.append(updated)
                        updated_count += 1
                        logger.debug(f"Row {idx}: Updated product {updated.id}")
                    else:
                        # Create new product
                        created = ProductExcelService._create_product_from_row(
                            organization_id=organization_id,
                            row_data=row,
                            repo=repo,
                        )
                        products.append(created)
                        created_count += 1
                        logger.debug(f"Row {idx}: Created product {created.id}")
                
                except Exception as e:
                    # Log error and continue processing
                    logger.error(f"Row {idx}: Error processing row - {e}", exc_info=True)
                    error_count += 1
                    continue
            
            # Commit all changes
            repo.session.commit()
            
            # Eagerly load all relationships before session closes
            from sqlalchemy.orm import joinedload
            from sqlalchemy import select
            
            if products:
                product_ids = [p.id for p in products]
                stmt = (
                    select(Product)
                    .options(
                        joinedload(Product.category),
                        joinedload(Product.cabys)
                    )
                    .where(Product.id.in_(product_ids))
                )
                products = list(repo.session.execute(stmt).scalars().unique())
        
        # Log import summary
        total_rows = len(rows)
        logger.info(
            f"Import completed: {total_rows} rows processed, "
            f"{created_count} created, {updated_count} updated, {error_count} errors"
        )
        
        # Convert products to ProductResponse using _map_product
        from app.services.product_service import _map_product
        product_responses = [_map_product(p) for p in products]
        
        # Return ProductListResponse
        return ProductListResponse(
            data=product_responses,
            pagination=PaginationResponse(
                page=1,
                pageSize=len(product_responses),
                totalElements=len(product_responses),
                totalPages=1,
            )
        )

    @staticmethod
    def _find_existing_product(
        organization_id: str,
        cod_artic: str,
        cod_barra: str,
        cod_interno: str,
        repo: ProductRepository,
    ) -> Optional[Product]:
        """
        Search for existing product using any of the three code types.
        Priority: COD_INTERNO (04) > COD_BARRA (03) > COD_ARTIC (01)

        Args:
            organization_id: Organization identifier
            cod_artic: Vendor code (Hacienda type 01)
            cod_barra: Barcode/manufacturer code (Hacienda type 03)
            cod_interno: Internal code (Hacienda type 04)
            repo: ProductRepository instance

        Returns:
            Matched Product or None
        """
        # Priority 1: COD_INTERNO (type 04)
        if cod_interno:
            product = repo.find_by_company_and_code(
                company_id=organization_id,
                hacienda_code=ProductCodeType.INTERNAL,
                code=cod_interno,
            )
            if product:
                logger.debug(f"Found product by COD_INTERNO: {cod_interno}")
                return product

        # Priority 2: COD_BARRA (type 03)
        if cod_barra:
            product = repo.find_by_company_and_code(
                company_id=organization_id,
                hacienda_code=ProductCodeType.MANUFACTURER,
                code=cod_barra,
            )
            if product:
                logger.debug(f"Found product by COD_BARRA: {cod_barra}")
                return product

        # Priority 3: COD_ARTIC (type 01)
        if cod_artic:
            product = repo.find_by_company_and_code(
                company_id=organization_id,
                hacienda_code=ProductCodeType.VENDOR,
                code=cod_artic,
            )
            if product:
                logger.debug(f"Found product by COD_ARTIC: {cod_artic}")
                return product

        return None

    @staticmethod
    def _create_product_from_row(
        organization_id: str,
        row_data: dict,
        repo: ProductRepository,
    ) -> Product:
        """
        Create new product from Excel row data.

        Args:
            organization_id: Organization identifier
            row_data: Dictionary with Excel row data
            repo: ProductRepository instance

        Returns:
            Created Product instance
        """
        from app.dtos.requests.category_request_dto import CategoryRequestDTO
        from app.repositories.category_repository import CategoryRepository
        from app.services.category_service import create_category
        import uuid

        # Build codes array from Excel columns
        codes_array = []
        cod_artic = row_data.get("cod_artic", "").strip()
        cod_barra = row_data.get("cod_barra", "").strip()
        cod_interno = row_data.get("cod_interno", "").strip()

        if cod_artic:
            codes_array.append({
                "codeTypeId": ProductCodeType.VENDOR,
                "number": cod_artic
            })
        if cod_barra:
            codes_array.append({
                "codeTypeId": ProductCodeType.MANUFACTURER,
                "number": cod_barra
            })
        if cod_interno:
            codes_array.append({
                "codeTypeId": ProductCodeType.INTERNAL,
                "number": cod_interno
            })

        # Handle category lookup/creation
        category_name = row_data.get("categoria", "").strip()
        category_id = None

        if category_name:
            # Look up category by name (case-insensitive)
            with CategoryRepository() as cat_repo:
                from sqlalchemy import func, select, and_
                from app.models.category import Category
                
                stmt = select(Category).where(
                    and_(
                        func.lower(Category.name) == category_name.lower(),
                        Category.organization_id == organization_id,
                    )
                )
                existing_category = cat_repo.session.execute(stmt).scalar_one_or_none()
                
                if existing_category:
                    category_id = existing_category.id
                    logger.debug(f"Found existing category: {category_name} -> {category_id}")
                else:
                    # Create new category
                    logger.info(f"Creating new category: {category_name}")
                    # Generate slug from name (lowercase, spaces to hyphens)
                    slug = category_name.lower().replace(" ", "-")
                    category_dto = CategoryRequestDTO(
                        name=category_name,
                        slug=slug,
                        description="",
                        sort_order=0,
                    )
                    new_category = create_category(organization_id, category_dto)
                    category_id = new_category.category_id
        else:
            # Use default "uncategorized" category
            category_id = repo._ensure_default_category(organization_id)
            logger.debug("Using default uncategorized category")

        # Extract other fields from Excel
        description = row_data.get("descripcion", "").strip()
        units_per_box = row_data.get("cantidad_caja")
        unit_of_measure = row_data.get("unidad_medida", "").strip()

        # Create product instance
        product = Product(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            name=description or cod_interno or cod_artic or "Producto sin nombre",
            description=description or "",
            price=0,  # Do NOT set price from Excel
            category_id=category_id,
            is_active=True,
            units_per_box=units_per_box if units_per_box is not None else 0,
            commercial_unit_measure=unit_of_measure if unit_of_measure else None,
            codes=codes_array,
        )

        # Save product
        product = repo.save(product)
        logger.info(f"Created product: {product.id} - {product.name}")
        
        return product

    @staticmethod
    def _update_product_category(
        product: Product,
        category_name: str,
        repo: ProductRepository,
    ) -> Product:
        """
        Update product category only, preserving all other fields.

        Args:
            product: Product instance to update
            category_name: Category name from Excel
            repo: ProductRepository instance

        Returns:
            Updated Product instance
        """
        from app.dtos.requests.category_request_dto import CategoryRequestDTO
        from app.repositories.category_repository import CategoryRepository
        from app.services.category_service import create_category
        from sqlalchemy import func, select, and_
        from app.models.category import Category

        # Handle category lookup/creation
        category_name = category_name.strip()
        category_id = None

        if category_name:
            # Look up category by name (case-insensitive)
            with CategoryRepository() as cat_repo:
                stmt = select(Category).where(
                    and_(
                        func.lower(Category.name) == category_name.lower(),
                        Category.organization_id == product.organization_id,
                    )
                )
                existing_category = cat_repo.session.execute(stmt).scalar_one_or_none()
                
                if existing_category:
                    category_id = existing_category.id
                    logger.debug(f"Found existing category: {category_name} -> {category_id}")
                else:
                    # Create new category
                    logger.info(f"Creating new category: {category_name}")
                    # Generate slug from name (lowercase, spaces to hyphens)
                    slug = category_name.lower().replace(" ", "-")
                    category_dto = CategoryRequestDTO(
                        name=category_name,
                        slug=slug,
                        description="",
                        sort_order=0,
                    )
                    new_category = create_category(product.organization_id, category_dto)
                    category_id = new_category.category_id
        else:
            # Use default "uncategorized" category
            category_id = repo._ensure_default_category(product.organization_id)
            logger.debug("Using default uncategorized category")

        # Update ONLY the category_id field, preserve all other fields
        product.category_id = category_id

        # Save product
        product = repo.save(product)
        logger.info(f"Updated product category: {product.id} - {product.name} -> category {category_id}")
        
        return product
