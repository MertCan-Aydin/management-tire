from typing import Optional
from fastapi import APIRouter, Depends, Query

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import alim_service
from ..schemas.alim import AlimEkleRequest

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
def listele(
    baslangic: Optional[str] = Query(None),
    bitis: Optional[str] = Query(None),
    tedarikci_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_cursor() as (cursor, _):
        return alim_service.listele(cursor, baslangic, bitis, tedarikci_id, limit, offset)


@router.get("/{alim_id}")
def getir(alim_id: int):
    with get_cursor() as (cursor, _):
        return alim_service.getir(cursor, alim_id)


@router.post("", status_code=201)
def ekle(body: AlimEkleRequest):
    with get_cursor() as (cursor, _):
        yeni_id = alim_service.ekle(cursor, body)
    return {"mesaj": "Alım kaydedildi", "id": yeni_id}


@router.delete("/{alim_id}")
def iptal(alim_id: int):
    with get_cursor() as (cursor, _):
        alim_service.iptal(cursor, alim_id)
    return {"mesaj": "Alım iptal edildi"}
