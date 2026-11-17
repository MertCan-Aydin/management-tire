from typing import Optional
from fastapi import APIRouter, Depends, Query

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import taslak_service
from ..schemas.taslak import TaslakRequest, TaslakGuncelleRequest

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
def listele(form_tipi: Optional[str] = Query(None), user=Depends(get_current_user)):
    with get_cursor() as (cursor, _):
        return taslak_service.listele(cursor, user["id"], form_tipi)


@router.get("/{tid}")
def getir(tid: int):
    with get_cursor() as (cursor, _):
        return taslak_service.getir(cursor, tid)


@router.post("", status_code=201)
def ekle(body: TaslakRequest, user=Depends(get_current_user)):
    with get_cursor() as (cursor, _):
        yeni_id = taslak_service.ekle(cursor, user["id"], body.form_tipi, body.baslik, body.veri)
    return {"mesaj": "Taslak kaydedildi", "id": yeni_id}


@router.put("/{tid}")
def guncelle(tid: int, body: TaslakGuncelleRequest):
    with get_cursor() as (cursor, _):
        taslak_service.guncelle(cursor, tid, body.baslik, body.veri)
    return {"mesaj": "Taslak güncellendi"}


@router.delete("/{tid}")
def sil(tid: int):
    with get_cursor() as (cursor, _):
        taslak_service.sil(cursor, tid)
    return {"mesaj": "Taslak silindi"}
