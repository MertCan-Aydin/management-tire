from sqlalchemy import Column, Integer, String, Numeric, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
import datetime
from app.database import Base

# Numeric(12,2) kullanıyoruz — float yerine kesin para hesabı


class Supplier(Base):
    __tablename__ = "suppliers"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(255), nullable=False, index=True)
    contact_info = Column(Text, nullable=True)
    current_debt = Column(Numeric(12, 2), default=0)
    is_deleted   = Column(Boolean, default=False)   # soft-delete

    products  = relationship("Product",         back_populates="supplier")
    purchases = relationship("Purchase",         back_populates="supplier")
    payments  = relationship("SupplierPayment",  back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price       = Column(Numeric(12, 2), nullable=False)
    cost_price  = Column(Numeric(12, 2), default=0)
    stock       = Column(Integer, default=0)
    image_path  = Column(String(512), nullable=True)
    is_deleted  = Column(Boolean, default=False)    # soft-delete

    supplier_id    = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    supplier       = relationship("Supplier",       back_populates="products")
    batches        = relationship("ProductBatch",   back_populates="product", cascade="all, delete-orphan")
    sale_items     = relationship("SaleItem",       back_populates="product")
    purchase_items = relationship("PurchaseItem",   back_populates="product")


class ProductBatch(Base):
    __tablename__ = "product_batches"

    id         = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity   = Column(Integer, default=0)
    cost_price = Column(Numeric(12, 2), nullable=False)
    date_added = Column(DateTime, default=datetime.datetime.now)

    product = relationship("Product", back_populates="batches")


class Customer(Base):
    __tablename__ = "customers"

    id        = Column(Integer, primary_key=True, index=True)
    name      = Column(String(255), nullable=False, index=True)
    phone     = Column(String(50),  nullable=True)
    car_brand = Column(String(100), nullable=True)
    car_plate = Column(String(50),  nullable=True)
    notes     = Column(Text,        nullable=True)

    sales = relationship("Sale", back_populates="customer")


class Sale(Base):
    __tablename__ = "sales"

    id             = Column(Integer, primary_key=True, index=True)
    timestamp      = Column(DateTime, default=datetime.datetime.now)
    total_amount   = Column(Numeric(12, 2), nullable=False)  # satış fiyatı (indirim sonrası)
    total_cost     = Column(Numeric(12, 2), default=0)       # FIFO maliyet toplamı
    discount       = Column(Numeric(12, 2), default=0)
    payment_method = Column(String(50), default="Nakit")
    customer_id    = Column(Integer, ForeignKey("customers.id"), nullable=True)
    is_cancelled   = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="sales")
    items    = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")

    @property
    def profit(self):
        """Brüt kar: satış - maliyet"""
        return (self.total_amount or 0) - (self.total_cost or 0)

    @property
    def is_loss(self):
        return self.profit < 0


class SaleItem(Base):
    __tablename__ = "sale_items"

    id                = Column(Integer, primary_key=True, index=True)
    sale_id           = Column(Integer, ForeignKey("sales.id"))
    product_id        = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name_snap = Column(String(255), nullable=True)  # ürün silinse de isim kalır
    quantity          = Column(Integer, nullable=False)
    unit_price        = Column(Numeric(12, 2), nullable=False)   # satış fiyatı
    unit_cost         = Column(Numeric(12, 2), default=0)        # FIFO maliyet (satış anında)
    is_cancelled      = Column(Boolean, default=False)

    sale    = relationship("Sale",    back_populates="items")
    product = relationship("Product", back_populates="sale_items")

    @property
    def line_profit(self):
        return (self.unit_price - self.unit_cost) * self.quantity


class Purchase(Base):
    __tablename__ = "purchases"

    id           = Column(Integer, primary_key=True, index=True)
    timestamp    = Column(DateTime, default=datetime.datetime.now)
    total_amount = Column(Numeric(12, 2), nullable=False)
    supplier_id  = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    is_cancelled = Column(Boolean, default=False)

    supplier = relationship("Supplier",     back_populates="purchases")
    items    = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")


class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id          = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"))
    product_id  = Column(Integer, ForeignKey("products.id"), nullable=True)
    product_name_snap = Column(String(255), nullable=True)
    quantity    = Column(Integer, nullable=False)
    unit_price  = Column(Numeric(12, 2), nullable=False)

    purchase = relationship("Purchase",  back_populates="items")
    product  = relationship("Product",   back_populates="purchase_items")


class Expense(Base):
    __tablename__ = "expenses"

    id          = Column(Integer, primary_key=True, index=True)
    description = Column(String(255), nullable=False)
    amount      = Column(Numeric(12, 2), nullable=False)
    timestamp   = Column(DateTime, default=datetime.datetime.now)


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"

    id          = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    amount      = Column(Numeric(12, 2), nullable=False)
    timestamp   = Column(DateTime, default=datetime.datetime.now)

    supplier = relationship("Supplier", back_populates="payments")


class CancellationLog(Base):
    __tablename__ = "cancellation_logs"

    id            = Column(Integer, primary_key=True, index=True)
    timestamp     = Column(DateTime, default=datetime.datetime.now)
    record_type   = Column(String(20),  nullable=False)
    record_id     = Column(Integer,     nullable=False)
    description   = Column(Text,        nullable=False)
    cancelled_qty = Column(Integer,     nullable=True)
    refund_amount = Column(Numeric(12, 2), nullable=True)
    cost_amount   = Column(Numeric(12, 2), nullable=True)  # iade edilen maliyeti de tut
    cancelled_by  = Column(String(100), default="Kullanıcı")
