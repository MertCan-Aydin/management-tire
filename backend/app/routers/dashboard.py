from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Sale, Expense, SupplierPayment
from app.schemas import DashboardOut

router = APIRouter()


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    total_sales    = db.query(func.sum(Sale.total_amount)).scalar() or 0.0
    total_expenses = db.query(func.sum(Expense.amount)).scalar() or 0.0
    total_payments = db.query(func.sum(SupplierPayment.amount)).scalar() or 0.0
    net_balance    = total_sales - total_expenses - total_payments

    return DashboardOut(
        total_sales=total_sales,
        total_expenses=total_expenses,
        total_payments=total_payments,
        net_balance=net_balance
    )
