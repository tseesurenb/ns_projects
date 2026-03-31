"""
Pydantic schemas for CRM endpoints.
Supports bilingual validation messages (Mongolian / English).
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, field_validator

from ns_crm.models.crm import CompanyStatus, StaffStatus, ProductType


# --- Bilingual error messages ---

ERRORS = {
    "mn": {
        "company_name_required": "Байгууллагын нэр оруулна уу.",
        "first_name_required": "Нэр оруулна уу.",
        "last_name_required": "Овог оруулна уу.",
        "product_name_required": "Бүтээгдэхүүний нэр оруулна уу.",
        "product_type_required": "Бүтээгдэхүүний төрөл сонгоно уу.",
        "unit_price_negative": "Үнэ сөрөг байж болохгүй.",
        "category_name_required": "Ангиллын нэр оруулна уу.",
        "stock_negative": "Нөөцийн тоо сөрөг байж болохгүй.",
    },
    "en": {
        "company_name_required": "Company name is required.",
        "first_name_required": "First name is required.",
        "last_name_required": "Last name is required.",
        "product_name_required": "Product name is required.",
        "product_type_required": "Product type is required.",
        "unit_price_negative": "Unit price cannot be negative.",
        "category_name_required": "Category name is required.",
        "stock_negative": "Stock quantity cannot be negative.",
    },
}


# ==================== Company ====================

class CompanyCreate(BaseModel):
    name: str
    registration_number: str | None = None
    industry: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    website: str | None = None
    status: CompanyStatus = CompanyStatus.ACTIVE
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError(ERRORS["mn"]["company_name_required"])
        return v.strip()


class CompanyUpdate(BaseModel):
    name: str | None = None
    registration_number: str | None = None
    industry: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    website: str | None = None
    status: CompanyStatus | None = None
    notes: str | None = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    registration_number: str | None
    industry: str | None
    phone: str | None
    email: str | None
    address: str | None
    website: str | None
    status: CompanyStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyListResponse(BaseModel):
    items: list[CompanyResponse]
    total: int
    page: int
    per_page: int


# ==================== Staff ====================

class StaffCreate(BaseModel):
    first_name: str
    last_name: str
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    is_primary_contact: bool = False
    status: StaffStatus = StaffStatus.ACTIVE

    @field_validator("first_name")
    @classmethod
    def first_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError(ERRORS["mn"]["first_name_required"])
        return v.strip()

    @field_validator("last_name")
    @classmethod
    def last_name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError(ERRORS["mn"]["last_name_required"])
        return v.strip()


class StaffUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    position: str | None = None
    email: str | None = None
    phone: str | None = None
    is_primary_contact: bool | None = None
    status: StaffStatus | None = None


class StaffResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    first_name: str
    last_name: str
    position: str | None
    email: str | None
    phone: str | None
    is_primary_contact: bool
    status: StaffStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StaffListResponse(BaseModel):
    items: list[StaffResponse]
    total: int
    page: int
    per_page: int


# ==================== Product Category ====================

class CategoryCreate(BaseModel):
    name: str
    description: str | None = None
    parent_id: uuid.UUID | None = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError(ERRORS["mn"]["category_name_required"])
        return v.strip()


class CategoryUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    parent_id: uuid.UUID | None = None


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    parent_id: uuid.UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ==================== Product ====================

class ProductCreate(BaseModel):
    name: str
    product_type: ProductType
    category_id: uuid.UUID | None = None
    sku: str | None = None
    description: str | None = None
    unit_price: Decimal = Decimal("0")
    currency: str = "MNT"
    unit: str = "ширхэг"
    stock_quantity: int | None = None
    is_active: bool = True

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError(ERRORS["mn"]["product_name_required"])
        return v.strip()

    @field_validator("unit_price")
    @classmethod
    def price_not_negative(cls, v):
        if v < 0:
            raise ValueError(ERRORS["mn"]["unit_price_negative"])
        return v

    @field_validator("stock_quantity")
    @classmethod
    def stock_not_negative(cls, v):
        if v is not None and v < 0:
            raise ValueError(ERRORS["mn"]["stock_negative"])
        return v


class ProductUpdate(BaseModel):
    name: str | None = None
    product_type: ProductType | None = None
    category_id: uuid.UUID | None = None
    sku: str | None = None
    description: str | None = None
    unit_price: Decimal | None = None
    currency: str | None = None
    unit: str | None = None
    stock_quantity: int | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID | None
    name: str
    product_type: ProductType
    sku: str | None
    description: str | None
    unit_price: Decimal
    currency: str
    unit: str
    stock_quantity: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    per_page: int
