from typing import Optional
from pydantic import BaseModel, field_validator


class TedarikciEkleRequest(BaseModel):
    ad: str
    iletisim_bilgisi: Optional[str] = None
    guncel_borc: float = 0.0


class TedarikciGuncelleRequest(TedarikciEkleRequest):
    silindi_mi: bool = False


class TedarikciKisiEkleRequest(BaseModel):
    tedarikci_id: int
    ad_soyad: str
    gorevi: Optional[str] = None
    telefon: Optional[str] = None
    eposta: Optional[str] = None
    notlar: Optional[str] = None


class TedarikciOdemeEkleRequest(BaseModel):
    tedarikci_id: int
    tutar: float

    @field_validator("tutar")
    @classmethod
    def tutar_pozitif(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Tutar 0'dan büyük olmalıdır")
        return v
