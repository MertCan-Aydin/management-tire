from typing import List
from pydantic import BaseModel, field_validator


class SatisKalemiRequest(BaseModel):
    urun_id: int
    urun_adi_anlik: str
    miktar: int
    birim_fiyat: float
    birim_maliyet: float

    @field_validator("miktar")
    @classmethod
    def miktar_pozitif(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Miktar 0'dan büyük olmalıdır")
        return v


class SatisEkleRequest(BaseModel):
    musteri_id: int
    odeme_yontemi: str
    indirim: float = 0.0
    kalemler: List[SatisKalemiRequest]

    @field_validator("odeme_yontemi")
    @classmethod
    def odeme_kontrol(cls, v: str) -> str:
        if v not in ("Nakit", "Kredi Kartı", "Havale"):
            raise ValueError("Geçersiz ödeme yöntemi")
        return v

    @field_validator("indirim")
    @classmethod
    def indirim_negatif_olamaz(cls, v: float) -> float:
        if v < 0:
            raise ValueError("İndirim negatif olamaz")
        return v

    @field_validator("kalemler")
    @classmethod
    def kalem_bos_olamaz(cls, v):
        if not v:
            raise ValueError("En az bir kalem gereklidir")
        return v
