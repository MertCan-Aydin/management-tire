from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Sale, SaleItem, Product, ProductBatch, CancellationLog
from app.schemas import SaleCreate, SaleOut, SaleItemOut

router = APIRouter()


def _build_sale_out(sale: Sale) -> SaleOut:
    items = [
        SaleItemOut(
            id=i.id,
            product_id=i.product_id,
            product_name=i.product.name if i.product else None,
            quantity=i.quantity,
            unit_price=i.unit_price,
            is_cancelled=i.is_cancelled
        )
        for i in sale.items
    ]
    return SaleOut(
        id=sale.id,
        timestamp=sale.timestamp,
        total_amount=sale.total_amount,
        discount=sale.discount,
        payment_method=sale.payment_method,
        customer_id=sale.customer_id,
        customer_name=sale.customer.name if sale.customer else None,
        is_cancelled=sale.is_cancelled,
        items=items
    )


@router.get("", response_model=List[SaleOut])
def list_sales(db: Session = Depends(get_db)):
    sales = db.query(Sale).order_by(Sale.timestamp.desc()).all()
    return [_build_sale_out(s) for s in sales]


@router.post("", response_model=SaleOut, status_code=201)
def create_sale(data: SaleCreate, db: Session = Depends(get_db)):
    # Stok kontrolü
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: ID {item_data.product_id}")
        if product.stock < item_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"'{product.name}' için yeterli stok yok! İstenen: {item_data.quantity}, Mevcut: {product.stock}"
            )

    # Toplam hesapla
    subtotal = sum(i.quantity * i.unit_price for i in data.items)
    total = max(0.0, subtotal - data.discount)

    sale = Sale(
        total_amount=total,
        discount=data.discount,
        payment_method=data.payment_method,
        customer_id=data.customer_id
    )
    db.add(sale)
    db.flush()

    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        db.add(SaleItem(
            sale_id=sale.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price
        ))
        product.stock -= item_data.quantity

        # FIFO batch düşümü
        remaining = item_data.quantity
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

    db.commit()
    db.refresh(sale)
    return _build_sale_out(sale)


@router.delete("/{sale_id}")
def cancel_sale(sale_id: int, db: Session = Depends(get_db)):
    """Son satışı geri al (undo)"""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Satış bulunamadı")
    if sale.is_cancelled:
        raise HTTPException(status_code=400, detail="Bu satış zaten iptal edilmiş")

    active_items = [i for i in sale.items if not i.is_cancelled]
    for item in active_items:
        item.is_cancelled = True
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
            last_batch = db.query(ProductBatch).filter(
                ProductBatch.product_id == product.id
            ).order_by(ProductBatch.date_added.desc()).first()
            if last_batch:
                last_batch.quantity += item.quantity
            else:
                db.add(ProductBatch(product_id=product.id, quantity=item.quantity, cost_price=product.cost_price))

    sale.is_cancelled = True
    sale.total_amount = 0.0
    db.commit()
    return {"ok": True}


@router.patch("/{sale_id}/items/{item_id}/cancel")
def cancel_sale_item(sale_id: int, item_id: int, db: Session = Depends(get_db)):
    sale_item = db.query(SaleItem).filter(
        SaleItem.id == item_id,
        SaleItem.sale_id == sale_id
    ).first()
    if not sale_item:
        raise HTTPException(status_code=404, detail="Satış kalemi bulunamadı")
    if sale_item.is_cancelled:
        raise HTTPException(status_code=400, detail="Bu kalem zaten iptal edilmiş")
    if sale_item.sale.is_cancelled:
        raise HTTPException(status_code=400, detail="Bu satış zaten tamamen iptal edilmiş")

    refund = sale_item.quantity * sale_item.unit_price
    sale_item.is_cancelled = True

    product = db.query(Product).filter(Product.id == sale_item.product_id).first()
    if product:
        product.stock += sale_item.quantity
        last_batch = db.query(ProductBatch).filter(
            ProductBatch.product_id == product.id
        ).order_by(ProductBatch.date_added.desc()).first()
        if last_batch:
            last_batch.quantity += sale_item.quantity
        else:
            db.add(ProductBatch(product_id=product.id, quantity=sale_item.quantity, cost_price=product.cost_price))

    sale_item.sale.total_amount = max(0.0, sale_item.sale.total_amount - refund)

    db.add(CancellationLog(
        record_type="SATIS_KALEM",
        record_id=sale_item.id,
        description=(
            f"SAT-{sale_id} nolu satıştan '{product.name if product else '?'}' kalemi iptal edildi. "
            f"({sale_item.quantity} adet × {sale_item.unit_price:,.2f} ₺)"
        ),
        cancelled_qty=sale_item.quantity,
        refund_amount=refund
    ))
    db.commit()
    return {"ok": True, "refund_amount": refund}


@router.patch("/{sale_id}/cancel-full")
def cancel_full_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Satış bulunamadı")
    if sale.is_cancelled:
        raise HTTPException(status_code=400, detail="Bu satış zaten iptal edilmiş")

    active_items = [i for i in sale.items if not i.is_cancelled]
    if not active_items:
        raise HTTPException(status_code=400, detail="Tüm kalemler zaten iptal edilmiş")

    total_refund = sum(i.quantity * i.unit_price for i in active_items)

    for item in active_items:
        item.is_cancelled = True
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
            last_batch = db.query(ProductBatch).filter(
                ProductBatch.product_id == product.id
            ).order_by(ProductBatch.date_added.desc()).first()
            if last_batch:
                last_batch.quantity += item.quantity
            else:
                db.add(ProductBatch(product_id=product.id, quantity=item.quantity, cost_price=product.cost_price))

    sale.is_cancelled = True
    sale.total_amount = 0.0

    db.add(CancellationLog(
        record_type="SATIS_TUMU",
        record_id=sale.id,
        description=(
            f"SAT-{sale.id} nolu satışın tamamı iptal edildi. "
            f"{len(active_items)} kalem, toplam {total_refund:,.2f} ₺ iade."
        ),
        cancelled_qty=sum(i.quantity for i in active_items),
        refund_amount=total_refund
    ))
    db.commit()
    return {"ok": True, "refund_amount": total_refund}
