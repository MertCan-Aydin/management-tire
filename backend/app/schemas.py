from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ── Supplier ──────────────────────────────────────────────────────────────────
class SupplierCreate(BaseModel):
    name: str
    contact_info: Optional[str] = None

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact_info: Optional[str] = None

class SupplierOut(BaseModel):
    id: int
    name: str
    contact_info: Optional[str]
    current_debt: float

    class Config:
        from_attributes = True


# ── Product ───────────────────────────────────────────────────────────────────
class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    cost_price: float = 0.0
    stock: int = 0
    supplier_id: Optional[int] = None
    image_path: Optional[str] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost_price: Optional[float] = None
    stock: Optional[int] = None
    supplier_id: Optional[int] = None
    image_path: Optional[str] = None

class ProductOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    cost_price: float
    stock: int
    supplier_id: Optional[int]
    supplier_name: Optional[str] = None
    image_path: Optional[str]

    class Config:
        from_attributes = True


# ── Customer ──────────────────────────────────────────────────────────────────
class CustomerCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    car_brand: Optional[str] = None
    car_plate: Optional[str] = None
    notes: Optional[str] = None

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    car_brand: Optional[str] = None
    car_plate: Optional[str] = None
    notes: Optional[str] = None

class CustomerOut(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    car_brand: Optional[str]
    car_plate: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


# ── Sale ──────────────────────────────────────────────────────────────────────
class SaleItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class SaleCreate(BaseModel):
    items: List[SaleItemCreate]
    discount: float = 0.0
    payment_method: str = "Nakit"
    customer_id: Optional[int] = None

class SaleItemOut(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    is_cancelled: bool

    class Config:
        from_attributes = True

class SaleOut(BaseModel):
    id: int
    timestamp: datetime
    total_amount: float
    discount: float
    payment_method: str
    customer_id: Optional[int]
    customer_name: Optional[str] = None
    is_cancelled: bool
    items: List[SaleItemOut] = []

    class Config:
        from_attributes = True


# ── Purchase ──────────────────────────────────────────────────────────────────
class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

class PurchaseCreate(BaseModel):
    items: List[PurchaseItemCreate]
    supplier_id: Optional[int] = None

class PurchaseItemOut(BaseModel):
    id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True

class PurchaseOut(BaseModel):
    id: int
    timestamp: datetime
    total_amount: float
    supplier_id: Optional[int]
    supplier_name: Optional[str] = None
    is_cancelled: bool
    items: List[PurchaseItemOut] = []

    class Config:
        from_attributes = True


# ── Expense ───────────────────────────────────────────────────────────────────
class ExpenseCreate(BaseModel):
    description: str
    amount: float

class ExpenseOut(BaseModel):
    id: int
    description: str
    amount: float
    timestamp: datetime

    class Config:
        from_attributes = True


# ── Supplier Payment ──────────────────────────────────────────────────────────
class SupplierPaymentCreate(BaseModel):
    amount: float

class SupplierPaymentOut(BaseModel):
    id: int
    supplier_id: int
    amount: float
    timestamp: datetime

    class Config:
        from_attributes = True


# ── Cancellation Log ──────────────────────────────────────────────────────────
class CancellationLogOut(BaseModel):
    id: int
    timestamp: datetime
    record_type: str
    record_id: int
    description: str
    cancelled_qty: Optional[int]
    refund_amount: Optional[float]

    class Config:
        from_attributes = True


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardOut(BaseModel):
    total_sales: float
    total_expenses: float
    total_payments: float
    net_balance: float


# ── Reports ───────────────────────────────────────────────────────────────────
class SaleReportItem(BaseModel):
    id: int
    timestamp: datetime
    total_amount: float
    payment_method: str

class ReportOut(BaseModel):
    period: str
    total: float
    sales: List[SaleReportItem]
