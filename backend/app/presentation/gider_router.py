from typing import Optional
from fastapi import APIRouter, Depends, Query

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import gider_service
from ..schemas.gider import GiderEkleRequest, GiderGuncelleRequest

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
def listele(
    baslangic: Optional[str] = Query(None),
    bitis: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    with get_cursor() as (cursor, _):
        return gider_service.listele(cursor, baslangic, bitis, limit, offset)


@router.get("/{gid}")
def getir(gid: int):
    with get_cursor() as (cursor, _):
        return gider_service.getir(cursor, gid)


@router.post("", status_code=201)
def ekle(body: GiderEkleRequest):
    with get_cursor() as (cursor, _):
        yeni_id = gider_service.ekle(cursor, body)
    return {"mesaj": "Gider eklendi", "id": yeni_id}


@router.put("/{gid}")
def guncelle(gid: int, body: GiderGuncelleRequest):
    with get_cursor() as (cursor, _):
        gider_service.guncelle(cursor, gid, body)
    return {"mesaj": "Güncellendi"}


@router.delete("/{gid}")
def sil(gid: int):
    with get_cursor() as (cursor, _):
        gider_service.sil(cursor, gid)
    return {"mesaj": "Silindi"}
