from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from ..core.db import get_cursor
from ..presentation.auth_router import get_current_user
from ..data_access import lastik_veri_dal

router = APIRouter(dependencies=[Depends(get_current_user)])


class _AdModel(BaseModel):
    ad: str


class _EbatModel(BaseModel):
    ebat: str
    kategori: str = "Otomobil"


@router.get("/markalar")
def markalar():
    with get_cursor() as (cursor, _):
        return lastik_veri_dal.markalar_listele(cursor)


@router.post("/markalar", status_code=201)
def marka_ekle(body: _AdModel):
    with get_cursor() as (cursor, _):
        yeni_id = lastik_veri_dal.marka_ekle(cursor, body.ad.strip())
    return {"id": yeni_id}


@router.get("/modeller")
def modeller():
    with get_cursor() as (cursor, _):
        return lastik_veri_dal.modeller_listele(cursor)


@router.post("/modeller", status_code=201)
def model_ekle(body: _AdModel):
    with get_cursor() as (cursor, _):
        yeni_id = lastik_veri_dal.model_ekle(cursor, body.ad.strip())
    return {"id": yeni_id}


@router.get("/ebatlar")
def ebatlar(kategori: str = Query(default=None)):
    with get_cursor() as (cursor, _):
        return lastik_veri_dal.ebatlar_listele(cursor, kategori)


@router.post("/ebatlar", status_code=201)
def ebat_ekle(body: _EbatModel):
    with get_cursor() as (cursor, _):
        yeni_id = lastik_veri_dal.ebat_ekle(cursor, body.ebat.strip(), body.kategori.strip())
    return {"id": yeni_id}
