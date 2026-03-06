from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import datetime
from app.database import get_db
from app.models import Sale, CancellationLog
from app.schemas import ReportOut, SaleReportItem, CancellationLogOut

router = APIRouter()


def _make_report(db: Session, period: str, days: int) -> ReportOut:
    start = datetime.datetime.now() - datetime.timedelta(days=days)
    sales = db.query(Sale).filter(
        Sale.timestamp >= start,
        Sale.is_cancelled == False
    ).order_by(Sale.timestamp.desc()).all()

    items = [
        SaleReportItem(
            id=s.id,
            timestamp=s.timestamp,
            total_amount=s.total_amount,
            payment_method=s.payment_method
        )
        for s in sales
    ]
    total = sum(s.total_amount for s in sales)
    return ReportOut(period=period, total=total, sales=items)


@router.get("/daily", response_model=ReportOut)
def daily_report(db: Session = Depends(get_db)):
    return _make_report(db, "Günlük", 1)


@router.get("/weekly", response_model=ReportOut)
def weekly_report(db: Session = Depends(get_db)):
    return _make_report(db, "Haftalık", 7)


@router.get("/monthly", response_model=ReportOut)
def monthly_report(db: Session = Depends(get_db)):
    return _make_report(db, "Aylık", 30)


@router.get("/cancellations", response_model=List[CancellationLogOut])
def cancellation_logs(db: Session = Depends(get_db)):
    return db.query(CancellationLog).order_by(CancellationLog.timestamp.desc()).all()
