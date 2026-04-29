from typing import Optional, List
from pydantic import BaseModel, field_validator


class AlimKalemiRequest(BaseModel):
    urun_id: int
    urun_adi_anlik: str
    miktar: int
    birim_fiyat: float

    @field_validator("miktar")
    @classmethod
    def miktar_pozitif(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Miktar 0'dan büyük olmalıdır")
        return v

    @field_validator("birim_fiyat")
    @classmethod
    def fiyat_negatif_olamaz(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Birim fiyat negatif olamaz")
        return v


class AlimEkleRequest(BaseModel):
    tedarikci_id: int
    kalemler: List[AlimKalemiRequest]

    @field_validator("kalemler")
    @classmethod
    def kalem_bos_olamaz(cls, v):
        if not v:
            raise ValueError("En az bir kalem gereklidir")
        return v
