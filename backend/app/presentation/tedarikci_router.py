from fastapi import APIRouter, Depends

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..business import tedarikci_service
from ..schemas.tedarikci import TedarikciEkleRequest, TedarikciGuncelleRequest, TedarikciKisiEkleRequest, TedarikciOdemeEkleRequest

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("")
def listele():
    with get_cursor() as (cursor, _):
        return tedarikci_service.listele(cursor)


@router.get("/{tid}")
def getir(tid: int):
    with get_cursor() as (cursor, _):
        return tedarikci_service.getir(cursor, tid)


@router.post("", status_code=201)
def ekle(body: TedarikciEkleRequest):
    with get_cursor() as (cursor, _):
        yeni_id = tedarikci_service.ekle(cursor, body)
    return {"mesaj": "Tedarikçi eklendi", "id": yeni_id}


@router.put("/{tid}")
def guncelle(tid: int, body: TedarikciGuncelleRequest):
    with get_cursor() as (cursor, _):
        tedarikci_service.guncelle(cursor, tid, body)
    return {"mesaj": "Güncellendi"}


@router.delete("/{tid}")
def sil(tid: int):
    with get_cursor() as (cursor, _):
        tedarikci_service.sil(cursor, tid)
    return {"mesaj": "Silindi"}


@router.get("/{tid}/kisiler")
def kisiler(tid: int):
    with get_cursor() as (cursor, _):
        return tedarikci_service.kisiler_listele(cursor, tid)


@router.post("/kisiler", status_code=201)
def kisi_ekle(body: TedarikciKisiEkleRequest):
    with get_cursor() as (cursor, _):
        tedarikci_service.kisi_ekle(cursor, body)
    return {"mesaj": "Kişi eklendi"}


@router.put("/kisiler/{kid}")
def kisi_guncelle(kid: int, body: TedarikciKisiEkleRequest):
    with get_cursor() as (cursor, _):
        tedarikci_service.kisi_guncelle(cursor, kid, body)
    return {"mesaj": "Güncellendi"}


@router.delete("/kisiler/{kid}")
def kisi_sil(kid: int):
    with get_cursor() as (cursor, _):
        tedarikci_service.kisi_sil(cursor, kid)
    return {"mesaj": "Silindi"}


@router.get("/{tid}/odemeler")
def odemeler(tid: int):
    with get_cursor() as (cursor, _):
        return tedarikci_service.odemeler_listele(cursor, tid)


@router.post("/odemeler", status_code=201)
def odeme_ekle(body: TedarikciOdemeEkleRequest):
    with get_cursor() as (cursor, _):
        yeni_id = tedarikci_service.odeme_ekle(cursor, body)
    return {"mesaj": "Ödeme kaydedildi", "id": yeni_id}


@router.delete("/odemeler/{odeme_id}")
def odeme_sil(odeme_id: int):
    with get_cursor() as (cursor, _):
        tedarikci_service.odeme_sil(cursor, odeme_id)
    return {"mesaj": "Silindi"}
