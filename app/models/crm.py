"""
CRM models — Companies, Staff, Product Categories, and Products.
All tenant-scoped for strict data isolation.
"""

import enum

from sqlalchemy import Boolean, Column, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.db.base import BaseModel, UUIDType


# --- Enums ---

class CompanyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEAD = "lead"


class StaffStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ProductType(str, enum.Enum):
    GOODS = "goods"
    SERVICE = "service"


# --- Models ---

class Company(BaseModel):
    """A customer/partner company managed by the tenant."""

    __tablename__ = "companies"

    tenant_id = Column(UUIDType(), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100), nullable=True)
    industry = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    status = Column(Enum(CompanyStatus), default=CompanyStatus.ACTIVE, nullable=False)
    notes = Column(Text, nullable=True)

    # Relationships
    staff = relationship("Staff", back_populates="company", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Company {self.name} (tenant={self.tenant_id})>"


class Staff(BaseModel):
    """A contact person at a customer company."""

    __tablename__ = "staff"

    tenant_id = Column(UUIDType(), ForeignKey("tenants.id"), nullable=False, index=True)
    company_id = Column(UUIDType(), ForeignKey("companies.id"), nullable=False, index=True)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    position = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_primary_contact = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(StaffStatus), default=StaffStatus.ACTIVE, nullable=False)

    # Relationships
    company = relationship("Company", back_populates="staff")

    def __repr__(self) -> str:
        return f"<Staff {self.first_name} {self.last_name} (company={self.company_id})>"


class ProductCategory(BaseModel):
    """Product/service category with optional parent for tree structure."""

    __tablename__ = "product_categories"

    tenant_id = Column(UUIDType(), ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    parent_id = Column(UUIDType(), ForeignKey("product_categories.id"), nullable=True)

    # Relationships
    parent = relationship("ProductCategory", remote_side="ProductCategory.id", backref="children")
    products = relationship("Product", back_populates="category", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ProductCategory {self.name} (tenant={self.tenant_id})>"


class Product(BaseModel):
    """A product (goods) or service offered by the tenant."""

    __tablename__ = "products"

    tenant_id = Column(UUIDType(), ForeignKey("tenants.id"), nullable=False, index=True)
    category_id = Column(UUIDType(), ForeignKey("product_categories.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    product_type = Column(Enum(ProductType), nullable=False)
    sku = Column(String(100), nullable=True)  # for goods
    description = Column(Text, nullable=True)
    unit_price = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(10), default="MNT", nullable=False)
    unit = Column(String(50), default="ширхэг", nullable=False)  # piece, hour, month, etc.
    stock_quantity = Column(Integer, nullable=True)  # for goods; null for services
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    category = relationship("ProductCategory", back_populates="products")

    def __repr__(self) -> str:
        return f"<Product {self.name} ({self.product_type.value}, tenant={self.tenant_id})>"
