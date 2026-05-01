import re
from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator


class LastikOteliEkleRequest(BaseModel):
    musteri_id: Optional[int] = None
    musteri_adi_anlik: str
    arac_plakasi: Optional[str] = None
    raf_kodu: str
    lastik_bilgisi: Optional[str] = None
    lastik_adedi: int = 4
    sezon: str
    giris_tarihi: date
    notlar: Optional[str] = None

    @field_validator("raf_kodu")
    @classmethod
    def raf_kodu_format(cls, v: str) -> str:
        v = v.strip().upper()
        if not re.match(r'^[A-Z]+\d+$', v):
            raise ValueError("Raf kodu harf+sayı formatında olmalıdır (ör: A3, B12)")
        return v

    @field_validator("sezon")
    @classmethod
    def sezon_kontrol(cls, v: str) -> str:
        if v not in ("Yaz", "Kış"):
            raise ValueError("Sezon Yaz veya Kış olmalıdır")
        return v

    @field_validator("lastik_adedi")
    @classmethod
    def adet_pozitif(cls, v: int) -> int:
        if v < 1:
            raise ValueError("Lastik adedi en az 1 olmalıdır")
        return v


class LastikOteliTeslimRequest(BaseModel):
    cikis_tarihi: date


class LastikOteliResponse(BaseModel):
    id: int
    raf_kodu: str
    musteri_id: Optional[int]
    musteri_adi: str
    arac_plakasi: Optional[str]
    lastik_bilgisi: Optional[str]
    lastik_adedi: int
    sezon: str
    giris_tarihi: date
    cikis_tarihi: Optional[date]
    notlar: Optional[str]
    aktif_mi: bool
