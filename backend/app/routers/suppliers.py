from decimal import Decimal, ROUND_HALF_UP
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Supplier, SupplierPayment
from app.schemas import SupplierCreate, SupplierUpdate, SupplierOut, SupplierPaymentCreate, SupplierPaymentOut

router = APIRouter()


def _d(v) -> Decimal:
    return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@router.get("", response_model=List[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).filter(Supplier.is_deleted == False).all()


@router.post("", response_model=SupplierOut, status_code=201)
def create_supplier(data: SupplierCreate, db: Session = Depends(get_db)):
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.put("/{supplier_id}", response_model=SupplierOut)
def update_supplier(supplier_id: int, data: SupplierUpdate, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.is_deleted == False
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.is_deleted == False
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı")
    if _d(supplier.current_debt) > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Tedarikçinin {float(_d(supplier.current_debt)):,.2f} ₺ ödenmemiş borcu var!"
        )
    supplier.is_deleted = True
    db.commit()
    return {"ok": True}


@router.post("/{supplier_id}/pay", response_model=SupplierPaymentOut)
def pay_supplier_debt(supplier_id: int, data: SupplierPaymentCreate, db: Session = Depends(get_db)):
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.is_deleted == False
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı")

    amount = _d(data.amount)
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Ödeme tutarı sıfırdan büyük olmalıdır")
    if amount > _d(supplier.current_debt):
        raise HTTPException(
            status_code=400,
            detail=f"Ödeme tutarı ({float(amount):,.2f} ₺) mevcut borçtan ({float(_d(supplier.current_debt)):,.2f} ₺) fazla olamaz"
        )

    supplier.current_debt = float(max(Decimal("0"), _d(supplier.current_debt) - amount))
    payment = SupplierPayment(supplier_id=supplier_id, amount=float(amount))
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


@router.delete("/{supplier_id}/payments/{payment_id}")
def undo_supplier_payment(supplier_id: int, payment_id: int, db: Session = Depends(get_db)):
    payment  = db.query(SupplierPayment).filter(SupplierPayment.id == payment_id).first()
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not payment or not supplier:
        raise HTTPException(status_code=404, detail="Kayıt bulunamadı")
    supplier.current_debt = float(_d(supplier.current_debt) + _d(payment.amount))
    db.delete(payment)
    db.commit()
    return {"ok": True, "restored_debt": float(_d(supplier.current_debt))}
