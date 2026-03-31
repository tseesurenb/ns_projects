"""
Staff/contact management endpoints.
Staff are nested under companies.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_tenant_id
from app.db.session import get_db
from app.models.crm import Company, Staff, StaffStatus
from app.models.user import User
from app.schemas.crm import (
    StaffCreate,
    StaffListResponse,
    StaffResponse,
    StaffUpdate,
)

router = APIRouter(tags=["Staff / Ажилтнууд"])


@router.get("/companies/{company_id}/staff", response_model=StaffListResponse)
async def list_staff(
    company_id: uuid.UUID,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: str | None = None,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Байгууллагын ажилтнуудын жагсаалт / List staff at a company."""
    # Verify company belongs to tenant
    company = await _get_company_or_404(db, company_id, tenant_id)

    query = select(Staff).where(Staff.company_id == company_id, Staff.tenant_id == tenant_id)

    if search:
        query = query.where(
            (Staff.first_name.ilike(f"%{search}%")) | (Staff.last_name.ilike(f"%{search}%"))
        )

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Staff.created_at.desc())
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    items = result.scalars().all()

    return StaffListResponse(items=items, total=total, page=page, per_page=per_page)


@router.post("/companies/{company_id}/staff", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    company_id: uuid.UUID,
    payload: StaffCreate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Шинэ ажилтан бүртгэх / Add a staff member."""
    await _get_company_or_404(db, company_id, tenant_id)

    staff = Staff(
        tenant_id=tenant_id,
        company_id=company_id,
        **payload.model_dump(),
    )
    db.add(staff)
    await db.flush()
    await db.refresh(staff)
    return staff


@router.get("/staff/{staff_id}", response_model=StaffResponse)
async def get_staff(
    staff_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ажилтны мэдээлэл / Get staff details."""
    result = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.tenant_id == tenant_id)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ажилтан олдсонгүй / Staff not found.")
    return staff


@router.put("/staff/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: uuid.UUID,
    payload: StaffUpdate,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ажилтны мэдээлэл шинэчлэх / Update staff."""
    result = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.tenant_id == tenant_id)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ажилтан олдсонгүй / Staff not found.")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(staff, field, value)

    await db.flush()
    await db.refresh(staff)
    return staff


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_staff(
    staff_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ажилтан устгах (идэвхгүй болгох) / Soft-delete staff."""
    result = await db.execute(
        select(Staff).where(Staff.id == staff_id, Staff.tenant_id == tenant_id)
    )
    staff = result.scalar_one_or_none()
    if not staff:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ажилтан олдсонгүй / Staff not found.")

    staff.status = StaffStatus.INACTIVE


# --- Helpers ---

async def _get_company_or_404(db: AsyncSession, company_id: uuid.UUID, tenant_id: uuid.UUID) -> Company:
    result = await db.execute(
        select(Company).where(Company.id == company_id, Company.tenant_id == tenant_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Байгууллага олдсонгүй / Company not found.")
    return company
