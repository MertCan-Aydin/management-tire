from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Product, Supplier, Purchase, PurchaseItem, ProductBatch, SaleItem
from app.models import ProductType, ProductBrand, ProductBrandModel
from app.schemas import (ProductCreate, ProductUpdate, ProductOut,
                         BatchOut, BatchUpdate, BatchAdd, PriceUpdate,
                         ProductTypeOut, ProductTypeCreate,
                         ProductBrandOut, ProductBrandCreate,
                         ProductBrandModelOut, ProductBrandModelCreate)

router = APIRouter()


def _d(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _build_product_out(p: Product) -> ProductOut:
    return ProductOut(
        id=p.id,
        name=p.name,
        description=p.description,
        price=float(_d(p.price)),
        cost_price=float(_d(p.cost_price)),
        stock=p.stock,
        supplier_id=p.supplier_id,
        supplier_name=p.supplier.name if p.supplier else None,
        image_path=p.image_path,
        is_deleted=p.is_deleted,
        product_type_id=p.product_type_id,
        product_type_name=p.product_type.name if p.product_type else None,
        brand_id=p.brand_id,
        brand_name=p.brand.name if p.brand else None,
        brand_model=p.brand_model,
    )


@router.get("", response_model=List[ProductOut])
def list_products(db: Session = Depends(get_db)):
    # Sadece silinmemiş ürünleri listele
    products = db.query(Product).filter(Product.is_deleted == False).all()
    return [_build_product_out(p) for p in products]


@router.post("", response_model=ProductOut, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(
        name=data.name,
        description=data.description,
        price=float(_d(data.price)),
        cost_price=float(_d(data.cost_price)),
        stock=data.stock,
        supplier_id=data.supplier_id,
        image_path=data.image_path,
        product_type_id=data.product_type_id,
        brand_id=data.brand_id,
        brand_model=data.brand_model,
    )
    db.add(product)
    db.flush()

    if data.stock > 0:
        debt_increase = _d(data.stock) * _d(data.cost_price)
        purchase = Purchase(total_amount=float(debt_increase), supplier_id=data.supplier_id)
        db.add(purchase)
        db.flush()
        db.add(PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id,
            product_name_snap=data.name,
            quantity=data.stock,
            unit_price=float(_d(data.cost_price))
        ))
        db.add(ProductBatch(
            product_id=product.id,
            quantity=data.stock,
            cost_price=float(_d(data.cost_price))
        ))
        if data.supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == data.supplier_id).first()
            if supplier:
                supplier.current_debt = float(_d(supplier.current_debt) + debt_increase)

    db.commit()
    db.refresh(product)
    return _build_product_out(product)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    old_stock   = product.stock
    new_stock   = data.stock       if data.stock       is not None else old_stock
    cost_price  = _d(data.cost_price  if data.cost_price  is not None else product.cost_price)
    supplier_id = data.supplier_id if data.supplier_id is not None else product.supplier_id
    stock_diff  = new_stock - old_stock

    if stock_diff > 0:
        cost = cost_price * stock_diff
        purchase = Purchase(total_amount=float(cost), supplier_id=supplier_id)
        db.add(purchase)
        db.flush()
        db.add(PurchaseItem(
            purchase_id=purchase.id,
            product_id=product.id,
            product_name_snap=product.name,
            quantity=stock_diff,
            unit_price=float(cost_price)
        ))
        db.add(ProductBatch(
            product_id=product.id,
            quantity=stock_diff,
            cost_price=float(cost_price)
        ))
        if supplier_id:
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if supplier:
                supplier.current_debt = float(_d(supplier.current_debt) + cost)

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
    """Soft-delete — geçmiş satışlarda ürün adı korunur."""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    product.is_deleted = True
    product.stock = 0
    db.commit()
    return {"ok": True}


# ── Batch endpoint'leri ───────────────────────────────────────────────────────

@router.get("/{product_id}/batches", response_model=List[BatchOut])
def list_batches(product_id: int, db: Session = Depends(get_db)):
    """Ürüne ait tüm stok partilerini listele."""
    product = db.query(Product).filter(
        Product.id == product_id, Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    batches = db.query(ProductBatch).filter(
        ProductBatch.product_id == product_id
    ).order_by(ProductBatch.date_added.desc()).all()
    return batches


@router.post("/{product_id}/batches", response_model=BatchOut, status_code=201)
def add_batch(product_id: int, data: BatchAdd, db: Session = Depends(get_db)):
    """Ürüne yeni stok partisi ekle (yeni alım)."""
    product = db.query(Product).filter(
        Product.id == product_id, Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Miktar 0'dan büyük olmalı")

    batch = ProductBatch(
        product_id=product_id,
        quantity=data.quantity,
        cost_price=float(_d(data.cost_price))
    )
    db.add(batch)

    # Stok güncelle
    product.stock += data.quantity
    product.cost_price = float(_d(data.cost_price))

    # Tedarikçi borcu artır
    debt_increase = _d(data.quantity) * _d(data.cost_price)
    if product.supplier_id:
        supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
        if supplier:
            supplier.current_debt = float(_d(supplier.current_debt) + debt_increase)

    # Alım kaydı
    purchase = Purchase(total_amount=float(debt_increase), supplier_id=product.supplier_id)
    db.add(purchase)
    db.flush()
    db.add(PurchaseItem(
        purchase_id=purchase.id,
        product_id=product_id,
        product_name_snap=product.name,
        quantity=data.quantity,
        unit_price=float(_d(data.cost_price))
    ))

    db.commit()
    db.refresh(batch)
    return batch


@router.put("/{product_id}/batches/{batch_id}", response_model=BatchOut)
def update_batch(product_id: int, batch_id: int, data: BatchUpdate, db: Session = Depends(get_db)):
    """Parti miktarını ve maliyetini düzenle."""
    batch = db.query(ProductBatch).filter(
        ProductBatch.id == batch_id,
        ProductBatch.product_id == product_id
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Parti bulunamadı")

    old_qty = batch.quantity
    diff    = data.quantity - old_qty

    batch.quantity   = data.quantity
    batch.cost_price = float(_d(data.cost_price))

    # Ürün toplam stokunu güncelle
    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        product.stock = max(0, product.stock + diff)

    db.commit()
    db.refresh(batch)
    return batch


@router.delete("/{product_id}/batches/{batch_id}")
def delete_batch(product_id: int, batch_id: int, db: Session = Depends(get_db)):
    """Partiyi sil, stok ve borcu düşür."""
    batch = db.query(ProductBatch).filter(
        ProductBatch.id == batch_id,
        ProductBatch.product_id == product_id
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Parti bulunamadı")

    product = db.query(Product).filter(Product.id == product_id).first()
    if product:
        # Stok düş
        product.stock = max(0, product.stock - batch.quantity)
        # Tedarikçi borcu düş
        if product.supplier_id and batch.quantity > 0:
            supplier = db.query(Supplier).filter(Supplier.id == product.supplier_id).first()
            if supplier:
                reduction = _d(batch.quantity) * _d(batch.cost_price)
                supplier.current_debt = float(max(Decimal("0"), _d(supplier.current_debt) - reduction))

    db.delete(batch)
    db.commit()
    return {"ok": True}


# ── Fiyat güncelleme ─────────────────────────────────────────────────────────

@router.patch("/{product_id}/price")
def update_price(product_id: int, data: PriceUpdate, db: Session = Depends(get_db)):
    """Sadece satış fiyatını güncelle."""
    product = db.query(Product).filter(
        Product.id == product_id, Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    product.price = float(_d(data.price))
    db.commit()
    return {"ok": True, "product_id": product_id, "price": product.price}


# ── Ürün Tipleri ──────────────────────────────────────────────────────────────

@router.get("/types", response_model=List[ProductTypeOut])
def list_types(db: Session = Depends(get_db)):
    return db.query(ProductType).order_by(ProductType.name).all()

@router.post("/types", response_model=ProductTypeOut, status_code=201)
def create_type(data: ProductTypeCreate, db: Session = Depends(get_db)):
    if db.query(ProductType).filter(ProductType.name == data.name).first():
        raise HTTPException(status_code=400, detail="Bu tip zaten mevcut")
    t = ProductType(name=data.name)
    db.add(t); db.commit(); db.refresh(t)
    return t

@router.delete("/types/{type_id}")
def delete_type(type_id: int, db: Session = Depends(get_db)):
    t = db.query(ProductType).filter(ProductType.id == type_id).first()
    if not t: raise HTTPException(status_code=404, detail="Tip bulunamadı")
    if db.query(Product).filter(Product.product_type_id == type_id, Product.is_deleted == False).first():
        raise HTTPException(status_code=400, detail="Bu tipe ait ürünler var, silinemez")
    db.delete(t); db.commit()
    return {"ok": True}


# ── Markalar ──────────────────────────────────────────────────────────────────

@router.get("/brands", response_model=List[ProductBrandOut])
def list_brands(type_id: int = None, db: Session = Depends(get_db)):
    q = db.query(ProductBrand)
    if type_id: q = q.filter(ProductBrand.product_type_id == type_id)
    return q.order_by(ProductBrand.name).all()

@router.post("/brands", response_model=ProductBrandOut, status_code=201)
def create_brand(data: ProductBrandCreate, db: Session = Depends(get_db)):
    b = ProductBrand(product_type_id=data.product_type_id, name=data.name)
    db.add(b); db.commit(); db.refresh(b)
    return b

@router.delete("/brands/{brand_id}")
def delete_brand(brand_id: int, db: Session = Depends(get_db)):
    b = db.query(ProductBrand).filter(ProductBrand.id == brand_id).first()
    if not b: raise HTTPException(status_code=404, detail="Marka bulunamadı")
    if db.query(Product).filter(Product.brand_id == brand_id, Product.is_deleted == False).first():
        raise HTTPException(status_code=400, detail="Bu markaya ait ürünler var, silinemez")
    db.delete(b); db.commit()
    return {"ok": True}


# ── Modeller ──────────────────────────────────────────────────────────────────

@router.get("/models", response_model=List[ProductBrandModelOut])
def list_models(brand_id: int = None, db: Session = Depends(get_db)):
    q = db.query(ProductBrandModel)
    if brand_id: q = q.filter(ProductBrandModel.brand_id == brand_id)
    return q.order_by(ProductBrandModel.name).all()

@router.post("/models", response_model=ProductBrandModelOut, status_code=201)
def create_model(data: ProductBrandModelCreate, db: Session = Depends(get_db)):
    m = ProductBrandModel(brand_id=data.brand_id, name=data.name)
    db.add(m); db.commit(); db.refresh(m)
    return m

@router.delete("/models/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db)):
    m = db.query(ProductBrandModel).filter(ProductBrandModel.id == model_id).first()
    if not m: raise HTTPException(status_code=404, detail="Model bulunamadı")
    db.delete(m); db.commit()
    return {"ok": True}