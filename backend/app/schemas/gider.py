from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


class GiderEkleRequest(BaseModel):
    aciklama: str
    tutar: float
    kategori: Optional[str] = None
    urun_adi: Optional[str] = None
    marka: Optional[str] = None
    alis_fiyati: Optional[float] = None
    satis_fiyati: Optional[float] = None
    yil: Optional[int] = None
    maliyet_bilinmiyor: bool = False

    @field_validator("tutar")
    @classmethod
    def tutar_pozitif(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Tutar 0'dan büyük olmalıdır")
        return v


class GiderGuncelleRequest(GiderEkleRequest):
    tarih: Optional[datetime] = None
