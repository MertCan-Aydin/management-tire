from fastapi import APIRouter, Depends, Query

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import lastik_oteli_service
from ..schemas.lastik_oteli import LastikOteliEkleRequest, LastikOteliTeslimRequest

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
def listele(
    sadece_aktif: bool = Query(True),
    arama: str = Query(""),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    with get_cursor() as (cursor, _):
        return lastik_oteli_service.listele(cursor, sadece_aktif, arama, limit, offset)


@router.get("/raf/{raf_kodu}")
def raf_sorgula(raf_kodu: str):
    """Raf koduna göre aktif kaydı döner. Boşsa 404."""
    with get_cursor() as (cursor, _):
        sonuc = lastik_oteli_service.raf_sorgula(cursor, raf_kodu)
    if not sonuc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Bu raf boş")
    return sonuc


@router.get("/{kayit_id}")
def getir(kayit_id: int):
    with get_cursor() as (cursor, _):
        return lastik_oteli_service.getir(cursor, kayit_id)


@router.post("", status_code=201)
def ekle(body: LastikOteliEkleRequest):
    with get_cursor() as (cursor, _):
        return lastik_oteli_service.ekle(cursor, body)


@router.put("/{kayit_id}/teslim")
def teslim_et(kayit_id: int, body: LastikOteliTeslimRequest):
    with get_cursor() as (cursor, _):
        lastik_oteli_service.teslim_et(cursor, kayit_id, body.cikis_tarihi)
    return {"mesaj": "Teslim edildi"}


@router.delete("/{kayit_id}")
def sil(kayit_id: int):
    with get_cursor() as (cursor, _):
        lastik_oteli_service.sil(cursor, kayit_id)
    return {"mesaj": "Silindi"}
