from fastapi import APIRouter, Depends, Query

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import rapor_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/dashboard")
def dashboard():
    with get_cursor() as (cursor, _):
        return rapor_service.dashboard(cursor)


@router.get("/gunluk")
def gunluk(tarih: str = Query(..., description="YYYY-MM-DD")):
    with get_cursor() as (cursor, _):
        return rapor_service.gunluk(cursor, tarih)


@router.get("/aralik")
def aralik(baslangic: str = Query(...), bitis: str = Query(...)):
    with get_cursor() as (cursor, _):
        return rapor_service.aralik(cursor, baslangic, bitis)


@router.get("/kirilim")
def kirilim(baslangic: str = Query(...), bitis: str = Query(...)):
    with get_cursor() as (cursor, _):
        return rapor_service.gunluk_kirilim(cursor, baslangic, bitis)


@router.get("/en-cok-satan")
def en_cok_satan(baslangic: str = Query(...), bitis: str = Query(...), limit: int = Query(10, ge=1, le=50)):
    with get_cursor() as (cursor, _):
        return rapor_service.en_cok_satan(cursor, baslangic, bitis, limit)


@router.get("/tedarikci-alim")
def tedarikci_alim(baslangic: str = Query(...), bitis: str = Query(...)):
    with get_cursor() as (cursor, _):
        return rapor_service.tedarikci_alim(cursor, baslangic, bitis)
