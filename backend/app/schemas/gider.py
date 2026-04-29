from typing import Optional
from datetime import datetime
from pydantic import BaseModel, field_validator


class GiderEkleRequest(BaseModel):
    aciklama: str
    tutar: float

    @field_validator("tutar")
    @classmethod
    def tutar_pozitif(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Tutar 0'dan büyük olmalıdır")
        return v


class GiderGuncelleRequest(GiderEkleRequest):
    tarih: Optional[datetime] = None
