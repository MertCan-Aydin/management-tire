from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
import datetime
from app.database import get_db
from app.models import Sale, SaleItem, Purchase, PurchaseItem, Expense, CancellationLog, Product, Supplier, Customer
from app.schemas import ReportOut, SaleReportItem, CancellationLogOut

router = APIRouter()


def _d(v) -> Decimal:
    return Decimal(str(v or 0))


def _make_report(db: Session, period: str, days: int) -> ReportOut:
    start = datetime.datetime.now() - datetime.timedelta(days=days)
    sales = db.query(Sale).filter(
        Sale.timestamp >= start, Sale.is_cancelled == False
    ).order_by(Sale.timestamp.desc()).all()

    expenses     = db.query(func.sum(Expense.amount)).filter(Expense.timestamp >= start).scalar() or 0
    total_sales  = sum(_d(s.total_amount) for s in sales)
    total_cost   = sum(_d(s.total_cost)   for s in sales)
    gross_profit = total_sales - total_cost
    net_profit   = gross_profit - _d(expenses)
    loss_count   = sum(1 for s in sales if _d(s.total_amount) < _d(s.total_cost))

    items = []
    for s in sales:
        profit = float(_d(s.total_amount) - _d(s.total_cost))
        items.append(SaleReportItem(
            id=s.id,
            timestamp=s.timestamp,
            total_amount=float(_d(s.total_amount)),
            total_cost=float(_d(s.total_cost)),
            profit=round(profit, 2),
            payment_method=s.payment_method,
            is_loss=profit < 0,
            is_cancelled=s.is_cancelled
        ))

    return ReportOut(
        period=period,
        total_sales=float(total_sales),
        total_cost=float(total_cost),
        gross_profit=float(gross_profit),
        total_expenses=float(_d(expenses)),
        net_profit=float(net_profit),
        loss_count=loss_count,
        sales=items
    )


@router.get("/daily",        response_model=ReportOut)
def daily_report(db: Session = Depends(get_db)):
    return _make_report(db, "Günlük", 1)

@router.get("/weekly",       response_model=ReportOut)
def weekly_report(db: Session = Depends(get_db)):
    return _make_report(db, "Haftalık", 7)

@router.get("/monthly",      response_model=ReportOut)
def monthly_report(db: Session = Depends(get_db)):
    return _make_report(db, "Aylık", 30)

@router.get("/cancellations", response_model=List[CancellationLogOut])
def cancellation_logs(db: Session = Depends(get_db)):
    return db.query(CancellationLog).order_by(CancellationLog.timestamp.desc()).all()


@router.get("/top-products")
def top_products(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """En çok satan ve en karlı ürünler"""
    items = db.query(SaleItem).filter(SaleItem.is_cancelled == False).all()
    stats: Dict[int, Dict] = {}
    for item in items:
        pid  = item.product_id
        name = item.product_name_snap or (item.product.name if item.product else "Silinmiş")
        brand_name  = None
        brand_model = None
        if item.product:
            try:
                brand_name = item.product.brand.name if item.product.brand else None
            except Exception:
                brand_name = None
            brand_model = getattr(item.product, "brand_model", None)
        if pid not in stats:
            stats[pid] = {"product_id": pid, "name": name,
                          "brand_name": brand_name, "brand_model": brand_model,
                          "total_qty": 0, "total_revenue": 0.0,
                          "total_cost": 0.0, "total_profit": 0.0}
        qty    = item.quantity
        rev    = float(_d(item.unit_price) * qty)
        cost   = float(_d(item.unit_cost)  * qty)
        stats[pid]["total_qty"]     += qty
        stats[pid]["total_revenue"] += rev
        stats[pid]["total_cost"]    += cost
        stats[pid]["total_profit"]  += rev - cost

    result = list(stats.values())
    for r in result:
        r["total_revenue"] = round(r["total_revenue"], 2)
        r["total_cost"]    = round(r["total_cost"],    2)
        r["total_profit"]  = round(r["total_profit"],  2)
        r["is_loss"]       = r["total_profit"] < 0
    result.sort(key=lambda x: x["total_qty"], reverse=True)
    return result


@router.get("/supplier-summary")
def supplier_summary(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Tedarikçi bazında alım özeti"""
    purchases = db.query(Purchase).filter(Purchase.is_cancelled == False).all()
    stats: Dict[int, Dict] = {}
    for p in purchases:
        sid  = p.supplier_id or 0
        name = p.supplier.name if p.supplier else "Bilinmiyor"
        if sid not in stats:
            stats[sid] = {"supplier_id": sid, "name": name,
                          "total_purchases": 0.0, "purchase_count": 0,
                          "current_debt": 0.0}
        stats[sid]["total_purchases"] += float(_d(p.total_amount))
        stats[sid]["purchase_count"]  += 1
        if p.supplier:
            stats[sid]["current_debt"] = float(_d(p.supplier.current_debt))

    result = list(stats.values())
    for r in result:
        r["total_purchases"] = round(r["total_purchases"], 2)
    result.sort(key=lambda x: x["total_purchases"], reverse=True)
    return result


@router.get("/customer-summary")
def customer_summary(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """Müşteri bazında ciro özeti"""
    sales = db.query(Sale).filter(Sale.is_cancelled == False, Sale.customer_id != None).all()
    stats: Dict[int, Dict] = {}
    for s in sales:
        cid  = s.customer_id
        name = s.customer.name if s.customer else "Bilinmiyor"
        plate = s.customer.car_plate if s.customer else ""
        if cid not in stats:
            stats[cid] = {"customer_id": cid, "name": name,
                          "car_plate": plate or "-",
                          "total_revenue": 0.0, "total_profit": 0.0,
                          "sale_count": 0}
        stats[cid]["total_revenue"] += float(_d(s.total_amount))
        stats[cid]["total_profit"]  += float(_d(s.total_amount) - _d(s.total_cost))
        stats[cid]["sale_count"]    += 1

    result = list(stats.values())
    for r in result:
        r["total_revenue"] = round(r["total_revenue"], 2)
        r["total_profit"]  = round(r["total_profit"],  2)
    result.sort(key=lambda x: x["total_revenue"], reverse=True)
    return result
