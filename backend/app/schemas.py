from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ── Supplier ──────────────────────────────────────────────────────────────────
class SupplierContactCreate(BaseModel):
    name:  str
    title: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None

class SupplierContactOut(BaseModel):
    id:          int
    supplier_id: int
    name:        str
    title:       Optional[str]
    phone:       Optional[str]
    email:       Optional[str]
    notes:       Optional[str]

    class Config:
        from_attributes = True

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
    is_deleted: bool = False

    class Config:
        from_attributes = True


# ── Product Type / Brand / Model ─────────────────────────────────────────────
class ProductTypeOut(BaseModel):
    id:   int
    name: str
    class Config: from_attributes = True

class ProductTypeCreate(BaseModel):
    name: str

class ProductBrandOut(BaseModel):
    id:              int
    product_type_id: int
    name:            str
    class Config: from_attributes = True

class ProductBrandCreate(BaseModel):
    product_type_id: int
    name:            str

class ProductBrandModelOut(BaseModel):
    id:       int
    brand_id: int
    name:     str
    class Config: from_attributes = True

class ProductBrandModelCreate(BaseModel):
    brand_id: int
    name:     str

# ── Product ───────────────────────────────────────────────────────────────────
class ProductCreate(BaseModel):
    name:            str
    description:     Optional[str] = None
    price:           float
    cost_price:      float = 0.0
    stock:           int = 0
    supplier_id:     Optional[int] = None
    image_path:      Optional[str] = None
    product_type_id: Optional[int] = None
    brand_id:        Optional[int] = None
    brand_model:     Optional[str] = None

class ProductUpdate(BaseModel):
    name:            Optional[str] = None
    description:     Optional[str] = None
    price:           Optional[float] = None
    cost_price:      Optional[float] = None
    stock:           Optional[int] = None
    supplier_id:     Optional[int] = None
    image_path:      Optional[str] = None
    product_type_id: Optional[int] = None
    brand_id:        Optional[int] = None
    brand_model:     Optional[str] = None

class ProductOut(BaseModel):
    id:              int
    name:            str
    description:     Optional[str]
    price:           float
    cost_price:      float
    stock:           int
    supplier_id:     Optional[int]
    supplier_name:   Optional[str] = None
    image_path:      Optional[str]
    is_deleted:      bool = False
    product_type_id: Optional[int] = None
    product_type_name: Optional[str] = None
    brand_id:        Optional[int] = None
    brand_name:      Optional[str] = None
    brand_model:     Optional[str] = None

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
    product_id: Optional[int]
    product_name: Optional[str] = None   # product_name_snap'ten gelir
    quantity: int
    unit_price: float
    unit_cost: float = 0.0
    line_profit: float = 0.0
    is_cancelled: bool

    class Config:
        from_attributes = True

class SaleOut(BaseModel):
    id: int
    timestamp: datetime
    total_amount: float
    total_cost: float = 0.0
    profit: float = 0.0
    discount: float
    payment_method: str
    customer_id: Optional[int]
    customer_name: Optional[str] = None
    is_cancelled: bool
    is_loss: bool = False
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
    product_id: Optional[int]
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
    cost_amount: Optional[float] = None

    class Config:
        from_attributes = True


# ── Product Batch ─────────────────────────────────────────────────────────────
class BatchOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    cost_price: float
    date_added: datetime

    class Config:
        from_attributes = True

class BatchUpdate(BaseModel):
    quantity: int
    cost_price: float

class BatchAdd(BaseModel):
    quantity: int
    cost_price: float

class PriceUpdate(BaseModel):
    price: float

# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardOut(BaseModel):
    # Gelir
    total_sales: float           # toplam satış tutarı
    total_cost: float            # toplam satış maliyeti (FIFO)
    gross_profit: float          # brüt kar = satış - maliyet
    # Giderler
    total_expenses: float        # operasyonel giderler
    total_payments: float        # tedarikçi ödemeleri
    # Net
    net_profit: float            # net kar = brüt kar - giderler
    net_balance: float           # kasa = satış - gider - ödeme
    # Ödeme türleri
    cash_sales: float
    card_sales: float
    # İptal özeti
    total_cancelled_refund: float


# ── Reports ───────────────────────────────────────────────────────────────────
class SaleReportItem(BaseModel):
    id: int
    timestamp: datetime
    total_amount: float
    total_cost: float = 0.0
    profit: float = 0.0
    payment_method: str
    is_loss: bool = False
    is_cancelled: bool = False

class ReportOut(BaseModel):
    period: str
    total_sales: float
    total_cost: float
    gross_profit: float
    total_expenses: float
    net_profit: float
    loss_count: int       # zararlı satış adedi
    sales: List[SaleReportItem]