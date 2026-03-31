"""
Product and category management endpoints.
All operations are tenant-scoped.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ns_crm.core.dependencies import get_current_user, get_tenant_id
from ns_crm.db.session import get_db
from ns_crm.models.crm import Product, ProductCategory, ProductType
from ns_crm.models.user import User
from ns_crm.schemas.crm import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)

router = APIRouter(tags=["Products / Бүтээгдэхүүн"])


# ==================== Categories ====================

@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ангиллын жагсаалт / List product categories."""
    result = await db.execute(
        select(ProductCategory)
        .where(ProductCategory.tenant_id == tenant_id)
        .order_by(ProductCategory.name)
    )
    return result.scalars().all()


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Шинэ ангилал үүсгэх / Create a product category."""
    if payload.parent_id:
        parent = await db.execute(
            select(ProductCategory).where(
                ProductCategory.id == payload.parent_id,
                ProductCategory.tenant_id == tenant_id,
            )
        )
        if not parent.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Эцэг ангилал олдсонгүй / Parent category not found.")

    category = ProductCategory(tenant_id=tenant_id, **payload.model_dump())
    db.add(category)
    await db.flush()
    await db.refresh(category)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ангилал шинэчлэх / Update category."""
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.id == category_id, ProductCategory.tenant_id == tenant_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ангилал олдсонгүй / Category not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)

    await db.flush()
    await db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ангилал устгах / Delete category (only if no products linked)."""
    result = await db.execute(
        select(ProductCategory).where(ProductCategory.id == category_id, ProductCategory.tenant_id == tenant_id)
    )
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ангилал олдсонгүй / Category not found.")

    # Check for linked products
    product_count = (await db.execute(
        select(func.count()).where(Product.category_id == category_id)
    )).scalar() or 0

    if product_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Энэ ангилалд {product_count} бүтээгдэхүүн бүртгэлтэй байна. Эхлээд бүтээгдэхүүнүүдийг шилжүүлнэ үү. / Category has {product_count} products. Move them first.",
        )

    await db.delete(category)


# ==================== Products ====================

@router.get("/products", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    product_type: ProductType | None = None,
    category_id: uuid.UUID | None = None,
    search: str | None = None,
    active_only: bool = True,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Бүтээгдэхүүний жагсаалт / List products."""
    query = select(Product).where(Product.tenant_id == tenant_id)

    if active_only:
        query = query.where(Product.is_active == True)
    if product_type:
        query = query.where(Product.product_type == product_type)
    if category_id:
        query = query.where(Product.category_id == category_id)
    if search:
        query = query.where(Product.name.ilike(f"%{search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Product.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return ProductListResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Шинэ бүтээгдэхүүн бүртгэх / Create a new product or service."""
    if payload.category_id:
        cat = await db.execute(
            select(ProductCategory).where(
                ProductCategory.id == payload.category_id,
                ProductCategory.tenant_id == tenant_id,
            )
        )
        if not cat.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ангилал олдсонгүй / Category not found.")

    product = Product(tenant_id=tenant_id, **payload.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return product


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Бүтээгдэхүүний мэдээлэл / Get product details."""
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бүтээгдэхүүн олдсонгүй / Product not found.")
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: uuid.UUID,
    payload: ProductUpdate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Бүтээгдэхүүн шинэчлэх / Update product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бүтээгдэхүүн олдсонгүй / Product not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.flush()
    await db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Бүтээгдэхүүн устгах (идэвхгүй болгох) / Soft-delete product."""
    result = await db.execute(
        select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
    )
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Бүтээгдэхүүн олдсонгүй / Product not found.")

    product.is_active = False
