from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Customer, Sale
from app.schemas import CustomerCreate, CustomerUpdate, CustomerOut, SaleOut, SaleItemOut

router = APIRouter()


@router.get("", response_model=List[CustomerOut])
def list_customers(search: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Customer)
    if search:
        term = f"%{search}%"
        query = query.filter(
            Customer.name.ilike(term) |
            Customer.phone.ilike(term) |
            Customer.car_plate.ilike(term) |
            Customer.car_brand.ilike(term)
        )
    return query.all()


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    customer = Customer(**data.model_dump())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.put("/{customer_id}", response_model=CustomerOut)
def update_customer(customer_id: int, data: CustomerUpdate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(customer, field, value)
    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}")
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Müşteri bulunamadı")
    db.delete(customer)
    db.commit()
    return {"ok": True}


@router.get("/{customer_id}/sales")
def get_customer_sales(customer_id: int, db: Session = Depends(get_db)):
    sales = db.query(Sale).filter(Sale.customer_id == customer_id).order_by(Sale.timestamp.desc()).all()
    result = []
    for sale in sales:
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
        result.append(SaleOut(
            id=sale.id,
            timestamp=sale.timestamp,
            total_amount=sale.total_amount,
            discount=sale.discount,
            payment_method=sale.payment_method,
            customer_id=sale.customer_id,
            is_cancelled=sale.is_cancelled,
            items=items
        ))
    return result
