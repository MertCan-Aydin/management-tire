from typing import Optional
from fastapi import APIRouter, Depends, Query, Request

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import aktivite_service
from ..schemas.aktivite import AktiviteLogRequest

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.post("", status_code=201)
def log_ekle(body: AktiviteLogRequest, request: Request, user=Depends(get_current_user)):
    ip = request.client.host if request.client else None
    with get_cursor() as (cursor, _):
        aktivite_service.logla(cursor, user["id"], body.islem_tipi, body.sayfa, body.detay, ip)
    return {"mesaj": "Log kaydedildi"}


@router.get("")
def listele(
    kullanici_id: Optional[int] = Query(None),
    islem_tipi: Optional[str] = Query(None),
    baslangic: Optional[str] = Query(None),
    bitis: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_cursor() as (cursor, _):
        return aktivite_service.listele(cursor, kullanici_id, islem_tipi, baslangic, bitis, limit, offset)
