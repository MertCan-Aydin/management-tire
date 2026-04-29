from typing import Optional
from fastapi import APIRouter, Depends, Query

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import urun_service
from ..schemas.urun import (
    UrunEkleRequest, UrunGuncelleRequest, UrunListeFiltre,
    UrunTipiEkleRequest, MarkaEkleRequest, ModelEkleRequest,
)

router = APIRouter(dependencies=[Depends(get_current_user)])

# ── Ürün Tipleri ──────────────────────────────────────────────────────────────

@router.get("/tipler")
def tipler_listele():
    with get_cursor() as (cursor, _):
        return urun_service.tipleri_listele(cursor)


@router.post("/tipler", status_code=201)
def tip_ekle(body: UrunTipiEkleRequest):
    with get_cursor() as (cursor, _):
        urun_service.tip_ekle(cursor, body.ad)
    return {"mesaj": "Ürün tipi eklendi"}


@router.put("/tipler/{tip_id}")
def tip_guncelle(tip_id: int, body: UrunTipiEkleRequest):
    with get_cursor() as (cursor, _):
        urun_service.tip_guncelle(cursor, tip_id, body.ad)
    return {"mesaj": "Güncellendi"}


@router.delete("/tipler/{tip_id}")
def tip_sil(tip_id: int):
    with get_cursor() as (cursor, _):
        urun_service.tip_sil(cursor, tip_id)
    return {"mesaj": "Silindi"}


# ── Markalar ──────────────────────────────────────────────────────────────────

@router.get("/markalar")
def markalar_listele(tip_id: Optional[int] = Query(None)):
    with get_cursor() as (cursor, _):
        return urun_service.markalari_listele(cursor, tip_id)


@router.post("/markalar", status_code=201)
def marka_ekle(body: MarkaEkleRequest):
    with get_cursor() as (cursor, _):
        urun_service.marka_ekle(cursor, body.urun_tipi_id, body.ad)
    return {"mesaj": "Marka eklendi"}


@router.put("/markalar/{marka_id}")
def marka_guncelle(marka_id: int, body: MarkaEkleRequest):
    with get_cursor() as (cursor, _):
        urun_service.marka_guncelle(cursor, marka_id, body.urun_tipi_id, body.ad)
    return {"mesaj": "Güncellendi"}


@router.delete("/markalar/{marka_id}")
def marka_sil(marka_id: int):
    with get_cursor() as (cursor, _):
        urun_service.marka_sil(cursor, marka_id)
    return {"mesaj": "Silindi"}


# ── Modeller ──────────────────────────────────────────────────────────────────

@router.get("/modeller")
def modeller_listele(marka_id: Optional[int] = Query(None)):
    with get_cursor() as (cursor, _):
        return urun_service.modelleri_listele(cursor, marka_id)


@router.post("/modeller", status_code=201)
def model_ekle(body: ModelEkleRequest):
    with get_cursor() as (cursor, _):
        urun_service.model_ekle(cursor, body.marka_id, body.ad, body.mevsim)
    return {"mesaj": "Model eklendi"}


@router.put("/modeller/{model_id}")
def model_guncelle(model_id: int, body: ModelEkleRequest):
    with get_cursor() as (cursor, _):
        urun_service.model_guncelle(cursor, model_id, body.marka_id, body.ad, body.mevsim)
    return {"mesaj": "Güncellendi"}


@router.delete("/modeller/{model_id}")
def model_sil(model_id: int):
    with get_cursor() as (cursor, _):
        urun_service.model_sil(cursor, model_id)
    return {"mesaj": "Silindi"}


# ── Ürünler ───────────────────────────────────────────────────────────────────

@router.get("")
def urunler_listele(
    arama: Optional[str] = Query(None),
    urun_tipi_id: Optional[int] = Query(None),
    marka_id: Optional[int] = Query(None),
    sadece_stoklu: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    filtre = UrunListeFiltre(
        arama=arama, urun_tipi_id=urun_tipi_id, marka_id=marka_id,
        sadece_stoklu=sadece_stoklu, limit=limit, offset=offset,
    )
    with get_cursor() as (cursor, _):
        return urun_service.urunleri_listele(cursor, filtre)


@router.get("/barkod/{barkod}")
def barkod_ara(barkod: str):
    with get_cursor() as (cursor, _):
        return urun_service.barkod_ara(cursor, barkod)


@router.get("/{urun_id}")
def urun_getir(urun_id: int):
    with get_cursor() as (cursor, _):
        return urun_service.urun_getir(cursor, urun_id)


@router.post("", status_code=201)
def urun_ekle(body: UrunEkleRequest):
    with get_cursor() as (cursor, _):
        yeni_id = urun_service.urun_ekle(cursor, body.model_dump())
    return {"mesaj": "Ürün eklendi", "id": yeni_id}


@router.put("/{urun_id}")
def urun_guncelle(urun_id: int, body: UrunGuncelleRequest):
    with get_cursor() as (cursor, _):
        urun_service.urun_guncelle(cursor, urun_id, body.model_dump())
    return {"mesaj": "Güncellendi"}


@router.delete("/{urun_id}")
def urun_sil(urun_id: int):
    with get_cursor() as (cursor, _):
        urun_service.urun_sil(cursor, urun_id)
    return {"mesaj": "Silindi"}
