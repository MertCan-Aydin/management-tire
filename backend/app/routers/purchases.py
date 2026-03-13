from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Purchase, PurchaseItem, Product, ProductBatch, Supplier, CancellationLog
from app.schemas import PurchaseOut, PurchaseItemOut

router = APIRouter()


def _d(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _build_purchase_out(p: Purchase) -> PurchaseOut:
    items = [
        PurchaseItemOut(
            id=i.id,
            product_id=i.product_id,
            product_name=i.product_name_snap or (i.product.name if i.product else "Silinmiş Ürün"),
            quantity=i.quantity,
            unit_price=float(_d(i.unit_price))
        )
        for i in p.items
    ]
    return PurchaseOut(
        id=p.id,
        timestamp=p.timestamp,
        total_amount=float(_d(p.total_amount)),
        supplier_id=p.supplier_id,
        supplier_name=p.supplier.name if p.supplier else None,
        is_cancelled=p.is_cancelled,
        items=items
    )


@router.get("", response_model=List[PurchaseOut])
def list_purchases(db: Session = Depends(get_db)):
    purchases = db.query(Purchase).order_by(Purchase.timestamp.desc()).all()
    return [_build_purchase_out(p) for p in purchases]


@router.patch("/{purchase_id}/cancel")
def cancel_purchase(purchase_id: int, db: Session = Depends(get_db)):
    purchase = db.query(Purchase).filter(Purchase.id == purchase_id).first()
    if not purchase:
        raise HTTPException(status_code=404, detail="Alım bulunamadı")
    if purchase.is_cancelled:
        raise HTTPException(status_code=400, detail="Bu alım zaten iptal edilmiş")

    total_cost = sum(_d(i.quantity) * _d(i.unit_price) for i in purchase.items)
    supp_name  = purchase.supplier.name if purchase.supplier else "Bilinmiyor"

    for item in purchase.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock = max(0, product.stock - item.quantity)
            # FIFO batch'ten düş
            remaining = item.quantity
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

    if purchase.supplier:
        new_debt = max(Decimal("0"), _d(purchase.supplier.current_debt) - total_cost)
        purchase.supplier.current_debt = float(new_debt)

    purchase.is_cancelled = True

    db.add(CancellationLog(
        record_type="ALIM",
        record_id=purchase.id,
        description=(
            f"ALIM-{purchase.id} nolu alım iptal edildi. "
            f"Tedarikçi: {supp_name}. "
            f"Toplam {float(total_cost):,.2f} ₺ borçtan düşüldü."
        ),
        cancelled_qty=sum(i.quantity for i in purchase.items),
        refund_amount=float(total_cost),
        cost_amount=float(total_cost)
    ))
    db.commit()
    return {"ok": True}
