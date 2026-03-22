from __future__ import annotations

import base64
import logging
import uuid
from decimal import Decimal
from typing import Optional

from app.dtos.requests.product_request_dto import ProductRequestDTO
from app.dtos.files import ImageDTO
from app.dtos.responses.product_dto import (
    CabysResponse,
    CategoryResponse,
    ProductCodeResponse,
    ProductDiscountResponse,
    ProductListResponse,
    ProductResponse,
    ProductTaxResponse,
    TaxAmountResponse,
    TaxFactorResponse,
    TaxRateResponse,
    TaxSpecialFieldsResponse,
)
from app.dtos.responses.pagination_dto import PaginationResponse
from app.enums.product_search_filters import ProductSearchFilters
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.services import cabys_service
from app.services.pdf_service import upload_file_to_s3
from app.utils.product_calculations import (
    calculate_product_totals,
    validate_discounts,
    validate_taxes,
)
from app.utils.search_utils import SearchUtils

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_TYPES = {
    "image/png": "png",
    "image/jpeg": "jpeg",
    "image/jpg": "jpg",
    "image/gif": "gif",
    "image/webp": "webp",
}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB


def _validate_cabys_code(code: str) -> None:
    """Raises ValueError if code is not exactly 13 digits."""
    if not code.isdigit() or len(code) != 13:
        raise ValueError(
            f"CABYS code must be exactly 13 digits. Received: '{code}'"
        )


def _validate_unique_codes(
    organization_id: str, codes: list, product_id: Optional[str], repo: ProductRepository
) -> None:
    """Validate that no code type+number combination is duplicated across products.
    
    Args:
        organization_id: Organization ID
        codes: List of code dicts with codeTypeId and number
        product_id: Current product ID (None for create, ID for update)
        repo: Repository instance to use for lookups
        
    Raises:
        ValueError: If a duplicate code is found
    """
    if not codes:
        return
    
    for code_entry in codes:
        code_type = code_entry.get("codeTypeId")
        code_number = code_entry.get("number")
        
        if not code_type or not code_number:
            continue
        
        # Check if another product has this code type + number combination
        existing = repo.find_by_company_and_code(
            organization_id, 
            code_type, 
            code_number,
            exclude_product_id=product_id  # Exclude current product for updates
        )
        
        if existing:
            raise ValueError(
                f"Product code conflict: Another product (ID: {existing.id}) already has "
                f"code type '{code_type}' with number '{code_number}'"
            )


def _coerce_list(val) -> list:
    return val if isinstance(val, list) else []


def get_products(
    company_id: str,
    page: int = 1,
    page_size: int = 12,
    search: str = None,
) -> ProductListResponse:
    """Get paginated products for a company with optional search filters."""
    search_filters = None
    order_by = None

    if search:
        filters, order_result = SearchUtils.parse_search_filter(
            search, Product, ProductSearchFilters
        )
        if filters:
            search_filters = filters
        if order_result:
            order_by = order_result

    with ProductRepository() as repo:
        products, total = repo.find_all_by_company(
            company_id,
            search_filters=search_filters,
            order_by=order_by,
            page=page,
            page_size=page_size,
        )
        data = [_map_product(p) for p in products]

    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    return ProductListResponse(
        data=data,
        pagination=PaginationResponse(
            page=page,
            pageSize=page_size,
            totalElements=total,
            totalPages=total_pages,
        ),
    )


def get_product(organization_id: str, product_id: str) -> Optional[ProductResponse]:
    """Get a single product by ID."""
    with ProductRepository() as repo:
        product = repo.find_by_id_and_company(product_id, organization_id)
        if not product:
            return None
        return _map_product(product)


def get_product_by_code(
    organization_id: str, hacienda_code: str, code: str
) -> Optional[ProductResponse]:
    """Get a single product by Hacienda code type and code number."""
    with ProductRepository() as repo:
        product = repo.find_by_company_and_code(organization_id, hacienda_code, code)
        if not product:
            return None
        return _map_product(product)


def create_product(organization_id: str, dto: ProductRequestDTO) -> ProductResponse:
    """Create a new product."""
    with ProductRepository() as repo:
        category_id = dto.category_id or repo._ensure_default_category(organization_id)

        product = Product(
            id=str(uuid.uuid4()),
            organization_id=organization_id,
            name=dto.name or dto.description or "",
            description=dto.description or dto.name or "",
            price=dto.price or 0,
            category_id=category_id,
            status=ProductStatus.ACTIVE,
            units_per_box=dto.units_per_box,
        )
        repo.session.add(product)
        repo.session.flush()

        if dto.image and dto.image.data:
            url = _save_product_image(organization_id, product.id, dto.image)
            product.image_url = url
            repo.session.flush()

        _apply_fiscal_fields(product, dto, repo)
        repo.session.flush()

        return _map_product(product)


def update_product(
    organization_id: str, product_id: str, dto: ProductRequestDTO
) -> ProductResponse:
    """Update an existing product."""
    with ProductRepository() as repo:
        product = repo.find_by_id_and_company(product_id, organization_id)
        if not product:
            raise LookupError(f"Product '{product_id}' not found")

        if dto.name is not None:
            product.name = dto.name
        if dto.description is not None:
            product.description = dto.description
        if dto.units_per_box is not None:
            product.units_per_box = dto.units_per_box
        if dto.price is not None:
            product.price = dto.price
        if dto.category_id is not None:
            product.category_id = dto.category_id

        if dto.image and dto.image.data:
            url = _save_product_image(organization_id, product.id, dto.image)
            product.image_url = url

        _apply_fiscal_fields(product, dto, repo)
        repo.save(product)
        return _map_product(product)


def update_product_status(
    organization_id: str, product_id: str, status: int
) -> ProductResponse:
    """
    Update a product's status.
    
    Args:
        organization_id: Organization ID
        product_id: Product ID
        status: New status (1=Active, 2=Inactive, 3=Deleted)
        
    Returns:
        Updated product response
        
    Raises:
        LookupError: If product not found
        ValueError: If status is invalid
    """
    from app.enums.product_status import ProductStatus
    
    # Validate status
    if not ProductStatus.is_valid(status):
        valid_statuses = ProductStatus.get_valid_statuses()
        raise ValueError(
            f"Invalid status value: {status}. Must be one of {valid_statuses} "
            f"(1=Active, 2=Inactive, 3=Deleted)"
        )
    
    with ProductRepository() as repo:
        product = repo.find_by_id_and_company(product_id, organization_id)
        if not product:
            raise LookupError(f"Product '{product_id}' not found")

        product.status = status
        repo.save(product)
        return _map_product(product)


def _apply_fiscal_fields(product: Product, dto: ProductRequestDTO, repo) -> None:
    """Apply all fiscal/Hacienda fields from dto onto product (mutates in place)."""

    # 1. CABYS lookup / upsert (shares the caller's session for a single transaction)
    if dto.cabys is not None:
        _validate_cabys_code(dto.cabys.code)
        cabys_dto = cabys_service.get_or_create_cabys(
            dto.cabys.code,
            dto.cabys.name,
            dto.cabys.type,
            session=repo.session,
        )
        product.cabys_id = uuid.UUID(cabys_dto.id)

    # 2. Scalar fiscal fields (only set if provided)
    if dto.unit_id is not None:
        product.unit_id = dto.unit_id
    if dto.commercial_unit_measure is not None:
        product.commercial_unit_measure = dto.commercial_unit_measure
    if dto.is_packaged is not None:
        product.is_packaged = dto.is_packaged
    if dto.quantity is not None:
        product.quantity = Decimal(str(dto.quantity))
    if dto.unit_price is not None:
        product.unit_price = Decimal(str(dto.unit_price))
    if dto.customs_part is not None:
        product.customs_part = dto.customs_part

    # 3. Packaged validation
    if product.is_packaged:
        if product.quantity is None or product.unit_price is None:
            raise ValueError(
                "When is_packaged is True both quantity and unit_price are required."
            )

    # 4. Build raw dicts from DTOs (no 'amount' key — computed below)
    discounts_raw = [d.model_dump(by_alias=True) for d in (dto.discounts or [])]
    taxes_raw = [t.model_dump(by_alias=True) for t in (dto.taxes or [])]

    validate_discounts(discounts_raw)
    validate_taxes(taxes_raw)

    # calculate_product_totals mutates discounts_raw and taxes_raw in-place,
    # embedding a computed "amount" key in each entry.
    base_amount, sale_price = calculate_product_totals(
        price=Decimal(str(product.price)),
        quantity=Decimal(str(product.quantity or 1)),
        is_packaged=bool(product.is_packaged),
        discounts=discounts_raw,
        taxes=taxes_raw,
        cabys_code=dto.cabys.code if dto.cabys else None,
        manual_base_amount=(
            Decimal(str(dto.base_amount)) if dto.base_amount is not None else None
        ),
    )

    # 5. Set codes array (validate uniqueness if codes are provided)
    if dto.codes is not None:
        codes_array = [c.model_dump(by_alias=True) for c in dto.codes]
        # Validate uniqueness (exclude current product if it has an ID)
        _validate_unique_codes(product.organization_id, codes_array, product.id, repo)
        product.codes = codes_array
    
    product.discounts = discounts_raw   # contain computed "amount" per entry
    product.taxes = taxes_raw           # contain computed "amount" per entry
    product.base_amount = base_amount
    product.sale_price = sale_price


def _save_product_image(organization_id: str, product_id: str, image: ImageDTO) -> str:
    """Validate, decode, and upload a product image to S3."""
    if not image.data:
        raise ValueError("Image data is empty")

    content_type = (image.content_type or "").lower().strip()
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError(
            f"Invalid image type '{content_type}'. "
            f"Allowed: {', '.join(ALLOWED_IMAGE_TYPES.keys())}"
        )

    ext = ALLOWED_IMAGE_TYPES[content_type]

    # Strip data URL prefix if present (e.g. "data:image/png;base64,...")
    data = image.data
    if data.startswith("data:"):
        if "," in data:
            data = data.split(",", 1)[1]

    try:
        decoded = base64.b64decode(data)
    except Exception:
        raise ValueError("Invalid base64 image data")

    if len(decoded) > MAX_IMAGE_SIZE:
        raise ValueError(
            f"Image size ({len(decoded)} bytes) exceeds maximum allowed "
            f"({MAX_IMAGE_SIZE // (1024 * 1024)}MB)"
        )

    key = f"organizations/{organization_id}/products/{product_id}/image.{ext}"
    return upload_file_to_s3(decoded, key, content_type)


def _map_product(product: Product) -> ProductResponse:
    category = None
    if product.category:
        category = CategoryResponse(
            categoryId=product.category_id,
            name=product.category.name if hasattr(product.category, "name") else None,
        )

    cabys_response = None
    if product.cabys:
        cabys_response = CabysResponse(
            id=str(product.cabys.id),
            code=product.cabys.code,
            name=product.cabys.name,
            type=product.cabys.type,
        )

    codes = [
        ProductCodeResponse(
            codeTypeId=c.get("codeTypeId", ""),
            number=c.get("number", ""),
            description=c.get("description"),
        )
        for c in _coerce_list(product.codes)
    ]

    discounts = [
        ProductDiscountResponse(
            discountTypeId=d.get("discountTypeId", ""),
            percentage=d.get("percentage"),
            amount=d.get("amount"),
            reason=d.get("reason"),
            isAmount=d.get("isAmount"),
        )
        for d in _coerce_list(product.discounts)
    ]

    taxes = []
    for t in _coerce_list(product.taxes):
        tax_rate = None
        if t.get("taxRate"):
            tax_rate = TaxRateResponse(
                id=t["taxRate"].get("id"),
                percentage=t["taxRate"].get("percentage", 0),
            )
        tax_factor = None
        if t.get("taxFactor"):
            tax_factor = TaxFactorResponse(
                id=t["taxFactor"].get("id", ""),
                factor=t["taxFactor"].get("factor", 0),
            )
        special_fields = None
        if t.get("specialFields"):
            sf = t["specialFields"]
            tax_amount_resp = None
            if sf.get("taxAmount"):
                tax_amount_resp = TaxAmountResponse(
                    id=sf["taxAmount"].get("id", ""),
                    amount=sf["taxAmount"].get("amount", 0),
                )
            special_fields = TaxSpecialFieldsResponse(
                quantity=sf.get("quantity"),
                percentage=sf.get("percentage"),
                proportion=sf.get("proportion"),
                volumeConsumption=sf.get("volumeConsumption"),
                taxAmount=tax_amount_resp,
            )
        taxes.append(
            ProductTaxResponse(
                taxTypeId=t.get("taxTypeId", ""),
                amount=t.get("amount"),
                taxRate=tax_rate,
                taxFactor=tax_factor,
                otherTaxType=t.get("otherTaxType"),
                specialFields=special_fields,
                isAmount=t.get("isAmount"),
            )
        )

    return ProductResponse(
        productId=product.id,
        companyId=product.organization_id,
        name=product.name,
        description=product.description,
        unitsPerBox=product.units_per_box,
        price=product.price,
        imageUrl=product.image_url,
        category=category,
        cabys=cabys_response,
        unitId=product.unit_id,
        commercialUnitMeasure=product.commercial_unit_measure,
        isPackaged=product.is_packaged,
        quantity=float(product.quantity) if product.quantity is not None else None,
        unitPrice=float(product.unit_price) if product.unit_price is not None else None,
        customsPart=product.customs_part,
        codes=codes,
        discounts=discounts,
        taxes=taxes,
        baseAmount=float(product.base_amount) if product.base_amount is not None else None,
        salePrice=float(product.sale_price) if product.sale_price is not None else None,
    )
