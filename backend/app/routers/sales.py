from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Tuple
from app.database import get_db
from app.models import Sale, SaleItem, Product, ProductBatch, CancellationLog
from app.schemas import SaleCreate, SaleOut, SaleItemOut

router = APIRouter()


def _d(value) -> Decimal:
    """Herhangi bir sayıyı Decimal'e çevir."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _fifo_cost(product_id: int, quantity: int, db: Session) -> Tuple[Decimal, list]:
    """
    FIFO mantığıyla verilen miktarın maliyetini hesapla.
    Batch'leri değiştirmez — sadece okur.
    Döner: (toplam_maliyet, [(batch, kullanılan_miktar), ...])
    """
    batches = db.query(ProductBatch).filter(
        ProductBatch.product_id == product_id,
        ProductBatch.quantity > 0
    ).order_by(ProductBatch.date_added.asc()).all()

    remaining = quantity
    total_cost = Decimal("0")
    used = []

    for batch in batches:
        if remaining <= 0:
            break
        take = min(batch.quantity, remaining)
        total_cost += _d(batch.cost_price) * take
        used.append((batch, take))
        remaining -= take

    # Stokta yetmiyorsa kalan miktar için mevcut cost_price kullan
    if remaining > 0:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product:
            total_cost += _d(product.cost_price) * remaining

    return total_cost, used


def _fifo_deduct(used_batches: list):
    """FIFO hesaplamada bulunan batch'lerden miktarları düş."""
    for batch, take in used_batches:
        batch.quantity -= take


def _fifo_restore(product_id: int, quantity: int, unit_cost: Decimal, db: Session):
    """
    İptal durumunda stok iadesi — en son batch'e ekle (ya da yeni batch aç).
    unit_cost: satış anında kaydedilen maliyet (birim başına).
    """
    last_batch = db.query(ProductBatch).filter(
        ProductBatch.product_id == product_id
    ).order_by(ProductBatch.date_added.desc()).first()

    if last_batch and _d(last_batch.cost_price) == unit_cost:
        last_batch.quantity += quantity
    else:
        db.add(ProductBatch(
            product_id=product_id,
            quantity=quantity,
            cost_price=float(unit_cost)
        ))


def _build_sale_out(sale: Sale) -> SaleOut:
    items = []
    for i in sale.items:
        name = i.product_name_snap or (i.product.name if i.product else "Silinmiş Ürün")
        lp = float(_d(i.unit_price) - _d(i.unit_cost)) * i.quantity
        items.append(SaleItemOut(
            id=i.id,
            product_id=i.product_id,
            product_name=name,
            quantity=i.quantity,
            unit_price=float(_d(i.unit_price)),
            unit_cost=float(_d(i.unit_cost)),
            line_profit=round(lp, 2),
            is_cancelled=i.is_cancelled
        ))

    total = float(_d(sale.total_amount))
    cost  = float(_d(sale.total_cost))
    profit = round(total - cost, 2)

    return SaleOut(
        id=sale.id,
        timestamp=sale.timestamp,
        total_amount=total,
        total_cost=cost,
        profit=profit,
        discount=float(_d(sale.discount)),
        payment_method=sale.payment_method,
        customer_id=sale.customer_id,
        customer_name=sale.customer.name if sale.customer else None,
        is_cancelled=sale.is_cancelled,
        is_loss=profit < 0,
        items=items
    )


@router.get("", response_model=List[SaleOut])
def list_sales(db: Session = Depends(get_db)):
    sales = db.query(Sale).order_by(Sale.timestamp.desc()).all()
    return [_build_sale_out(s) for s in sales]


@router.post("", response_model=SaleOut, status_code=201)
def create_sale(data: SaleCreate, db: Session = Depends(get_db)):
    # 1. Stok kontrolü
    for item_data in data.items:
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.is_deleted == False
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Ürün bulunamadı: ID {item_data.product_id}")
        if product.stock < item_data.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"'{product.name}' için yeterli stok yok! İstenen: {item_data.quantity}, Mevcut: {product.stock}"
            )

    # 2. Toplam hesapla
    subtotal = sum(_d(i.unit_price) * i.quantity for i in data.items)
    discount = _d(data.discount)
    total    = max(Decimal("0"), subtotal - discount)

    # 3. Sale kaydı oluştur
    sale = Sale(
        total_amount=float(total),
        total_cost=0.0,
        discount=float(discount),
        payment_method=data.payment_method,
        customer_id=data.customer_id
    )
    db.add(sale)
    db.flush()

    # 4. Her kalem için FIFO maliyet hesapla ve kaydet
    total_cost = Decimal("0")
    for item_data in data.items:
        product = db.query(Product).filter(Product.id == item_data.product_id).first()
        item_cost, used_batches = _fifo_cost(item_data.product_id, item_data.quantity, db)
        unit_cost = (item_cost / item_data.quantity).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        db.add(SaleItem(
            sale_id=sale.id,
            product_id=item_data.product_id,
            product_name_snap=product.name,
            quantity=item_data.quantity,
            unit_price=float(_d(item_data.unit_price)),
            unit_cost=float(unit_cost)
        ))

        product.stock -= item_data.quantity
        _fifo_deduct(used_batches)
        total_cost += item_cost

    sale.total_cost = float(total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    db.commit()
    db.refresh(sale)
    return _build_sale_out(sale)


@router.delete("/{sale_id}")
def undo_sale(sale_id: int, db: Session = Depends(get_db)):
    """Son satışı geri al (undo) — tüm stoklar iade edilir."""
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
            _fifo_restore(product.id, item.quantity, _d(item.unit_cost), db)

    sale.is_cancelled = True
    sale.total_amount = 0.0
    sale.total_cost   = 0.0
    db.commit()
    return {"ok": True}


@router.patch("/{sale_id}/items/{item_id}/cancel")
def cancel_sale_item(sale_id: int, item_id: int, db: Session = Depends(get_db)):
    """Tek kalem iptal — indirim orantılı paylaştırılır."""
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

    sale = sale_item.sale

    # İndirim orantısı: bu kalemin brüt tutarının toplam brüt tutara oranı
    active_items = [i for i in sale.items if not i.is_cancelled]
    gross_total  = sum(_d(i.unit_price) * i.quantity for i in active_items)
    item_gross   = _d(sale_item.unit_price) * sale_item.quantity
    discount     = _d(sale.discount)

    if gross_total > 0:
        item_discount = (discount * item_gross / gross_total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    else:
        item_discount = Decimal("0")

    refund    = item_gross - item_discount
    item_cost = _d(sale_item.unit_cost) * sale_item.quantity

    sale_item.is_cancelled = True

    # Stok iadesi
    product = db.query(Product).filter(Product.id == sale_item.product_id).first()
    if product:
        product.stock += sale_item.quantity
        _fifo_restore(product.id, sale_item.quantity, _d(sale_item.unit_cost), db)

    # Sale toplamını güncelle
    sale.total_amount = float(max(Decimal("0"), _d(sale.total_amount) - refund))
    sale.total_cost   = float(max(Decimal("0"), _d(sale.total_cost) - item_cost))

    product_name = sale_item.product_name_snap or (product.name if product else "?")
    db.add(CancellationLog(
        record_type="SATIS_KALEM",
        record_id=sale_item.id,
        description=(
            f"SAT-{sale_id} nolu satıştan '{product_name}' kalemi iptal edildi. "
            f"({sale_item.quantity} adet × {float(_d(sale_item.unit_price)):,.2f} ₺, "
            f"indirim payı: {float(item_discount):,.2f} ₺)"
        ),
        cancelled_qty=sale_item.quantity,
        refund_amount=float(refund),
        cost_amount=float(item_cost)
    ))
    db.commit()
    return {"ok": True, "refund_amount": float(refund), "item_discount": float(item_discount)}


@router.patch("/{sale_id}/cancel-full")
def cancel_full_sale(sale_id: int, db: Session = Depends(get_db)):
    """Tüm satışı iptal et."""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Satış bulunamadı")
    if sale.is_cancelled:
        raise HTTPException(status_code=400, detail="Bu satış zaten iptal edilmiş")

    active_items = [i for i in sale.items if not i.is_cancelled]
    if not active_items:
        raise HTTPException(status_code=400, detail="Tüm kalemler zaten iptal edilmiş")

    total_refund = _d(sale.total_amount)
    total_cost   = _d(sale.total_cost)

    for item in active_items:
        item.is_cancelled = True
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            product.stock += item.quantity
            _fifo_restore(product.id, item.quantity, _d(item.unit_cost), db)

    sale.is_cancelled = True
    sale.total_amount = 0.0
    sale.total_cost   = 0.0

    db.add(CancellationLog(
        record_type="SATIS_TUMU",
        record_id=sale.id,
        description=(
            f"SAT-{sale.id} nolu satışın tamamı iptal edildi. "
            f"{len(active_items)} kalem, toplam {float(total_refund):,.2f} ₺ iade."
        ),
        cancelled_qty=sum(i.quantity for i in active_items),
        refund_amount=float(total_refund),
        cost_amount=float(total_cost)
    ))
    db.commit()
    return {"ok": True, "refund_amount": float(total_refund)}
