from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product, Supplier, Purchase, PurchaseItem, ProductBatch, SaleItem
from app.schemas import ProductCreate, ProductUpdate, ProductOut

router = APIRouter()


def _build_product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        name=p.name,
        description=p.description,
        price=p.price,
        cost_price=p.cost_price,
        stock=p.stock,
        supplier_id=p.supplier_id,
        supplier_name=p.supplier.name if p.supplier else None,
        image_path=p.image_path
    )


@router.get("", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return [_build_product_out(p) for p in products]


@router.post("", response_model=ProductOut, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        name=data.name,
        description=data.description,
        price=data.price,
        cost_price=data.cost_price,
        stock=data.stock,
        supplier_id=data.supplier_id,
        image_path=data.image_path
    )
    db.add(product)
    db.flush()

    if data.stock > 0:
        debt_increase = data.stock * data.cost_price
        purchase = Purchase(total_amount=debt_increase, supplier_id=data.supplier_id)
        db.add(purchase)
        db.flush()
        db.add(PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id,
            quantity=data.stock,
            unit_price=data.cost_price
        ))
        db.add(ProductBatch(
            product_id=product.id,
            quantity=data.stock,
            cost_price=data.cost_price
        ))
        if data.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == data.supplier_id).first()
            if supplier:
                supplier.current_debt += debt_increase

    db.commit()
    db.refresh(product)
    return _build_product_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    old_stock = product.stock
    new_stock  = data.stock if data.stock is not None else old_stock
    cost_price = data.cost_price if data.cost_price is not None else product.cost_price
    supplier_id = data.supplier_id if data.supplier_id is not None else product.supplier_id

    stock_diff = new_stock - old_stock

    if stock_diff > 0:
        cost = cost_price * stock_diff
        purchase = Purchase(total_amount=cost, supplier_id=supplier_id)
        db.add(purchase)
        db.flush()
        db.add(PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id,
            quantity=stock_diff,
            unit_price=cost_price
        ))
        db.add(ProductBatch(
            product_id=product.id,
            quantity=stock_diff,
            cost_price=cost_price
        ))
        if supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if supplier:
                supplier.current_debt += cost

    elif stock_diff < 0:
        remaining = abs(stock_diff)
        batches = db.query(ProductBatch).filter(
            ProductBatch.product_id == product.id,
            ProductBatch.quantity > 0
        ).order_by(ProductBatch.date_added.asc()).all()
        for batch in batches:
            if remaining <= 0:
                break
            if batch.quantity >= remaining:
                batch.quantity -= remaining
                remaining = 0
            else:
                remaining -= batch.quantity
                batch.quantity = 0

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return _build_product_out(product)


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    sale_count = db.query(SaleItem).filter(SaleItem.product_id == product_id).count()
    db.delete(product)
    db.commit()
    return {"ok": True, "had_sales": sale_count > 0}
