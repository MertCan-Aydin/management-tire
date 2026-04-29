from typing import Optional
from fastapi import APIRouter, Depends, Query

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import musteri_service
from ..schemas.musteri import MusteriEkleRequest

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
def listele(arama: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    with get_cursor() as (cursor, _):
        return musteri_service.listele(cursor, arama, limit, offset)


@router.get("/plaka/{plaka}")
def plaka_ara(plaka: str):
    with get_cursor() as (cursor, _):
        return musteri_service.plaka_ara(cursor, plaka.upper())


@router.get("/{mid}")
def getir(mid: int):
    with get_cursor() as (cursor, _):
        return musteri_service.getir(cursor, mid)


@router.post("", status_code=201)
def ekle(body: MusteriEkleRequest):
    with get_cursor() as (cursor, _):
        yeni_id = musteri_service.ekle(cursor, body)
    return {"mesaj": "Müşteri eklendi", "id": yeni_id}


@router.put("/{mid}")
def guncelle(mid: int, body: MusteriEkleRequest):
    with get_cursor() as (cursor, _):
        musteri_service.guncelle(cursor, mid, body)
    return {"mesaj": "Güncellendi"}


@router.delete("/{mid}")
def sil(mid: int):
    with get_cursor() as (cursor, _):
        musteri_service.sil(cursor, mid)
    return {"mesaj": "Silindi"}
