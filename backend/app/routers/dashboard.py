from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Sale, Expense, SupplierPayment, CancellationLog
from app.schemas import DashboardOut

router = APIRouter()


def _d(v) -> Decimal:
    return Decimal(str(v or 0))


@router.get("", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    # Aktif (iptal edilmemiş) satışlar
    active_sales = db.query(Sale).filter(Sale.is_cancelled == False).all()

    total_sales = sum(_d(s.total_amount) for s in active_sales)
    total_cost  = sum(_d(s.total_cost)   for s in active_sales)
    gross_profit = total_sales - total_cost

    # Ödeme türüne göre ayrım
    cash_sales = sum(_d(s.total_amount) for s in active_sales if s.payment_method == "Nakit")
    card_sales = sum(_d(s.total_amount) for s in active_sales if s.payment_method != "Nakit")

    # Giderler ve ödemeler
    total_expenses = _d(db.query(func.sum(Expense.amount)).scalar())
    total_payments = _d(db.query(func.sum(SupplierPayment.amount)).scalar())

    # Net kar = brüt kar - operasyonel giderler (tedarikçi ödemesi borç kapatma, gider değil)
    net_profit = gross_profit - total_expenses

    # Kasa = tüm satış gelirleri - giderler - tedarikçiye ödenenler
    net_balance = total_sales - total_expenses - total_payments

    # İptal edilen satışların toplam iadesi
    total_cancelled_refund = _d(
        db.query(func.sum(CancellationLog.refund_amount)).filter(
            CancellationLog.record_type.in_(["SATIS_TUMU", "SATIS_KALEM"])
        ).scalar()
    )

    return DashboardOut(
        total_sales=float(total_sales),
        total_cost=float(total_cost),
        gross_profit=float(gross_profit),
        total_expenses=float(total_expenses),
        total_payments=float(total_payments),
        net_profit=float(net_profit),
        net_balance=float(net_balance),
        cash_sales=float(cash_sales),
        card_sales=float(card_sales),
        total_cancelled_refund=float(total_cancelled_refund)
    )
