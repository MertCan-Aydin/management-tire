from typing import Optional
from fastapi import APIRouter, Depends, Query

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import satis_service
from ..schemas.satis import SatisEkleRequest

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
def listele(
    baslangic: Optional[str] = Query(None),
    bitis: Optional[str] = Query(None),
    musteri_id: Optional[int] = Query(None),
    odeme_yontemi: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_cursor() as (cursor, _):
        return satis_service.listele(cursor, baslangic, bitis, musteri_id, odeme_yontemi, limit, offset)


@router.get("/{satis_id}")
def getir(satis_id: int):
    with get_cursor() as (cursor, _):
        return satis_service.getir(cursor, satis_id)


@router.post("", status_code=201)
def ekle(body: SatisEkleRequest):
    with get_cursor() as (cursor, _):
        yeni_id = satis_service.ekle(cursor, body)
    return {"mesaj": "Satış kaydedildi", "id": yeni_id}


@router.delete("/{satis_id}")
def iptal(satis_id: int):
    with get_cursor() as (cursor, _):
        satis_service.iptal(cursor, satis_id)
    return {"mesaj": "Satış iptal edildi"}


@router.delete("/kalemler/{kalem_id}")
def kalem_iptal(kalem_id: int):
    with get_cursor() as (cursor, _):
        satis_service.kalem_iptal(cursor, kalem_id)
    return {"mesaj": "Kalem iptal edildi"}
