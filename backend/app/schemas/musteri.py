from typing import Optional
from pydantic import BaseModel


class MusteriEkleRequest(BaseModel):
    ad_soyad: str
    telefon: str
    arac_markasi: Optional[str] = None
    arac_plakasi: Optional[str] = None
    notlar: Optional[str] = None
