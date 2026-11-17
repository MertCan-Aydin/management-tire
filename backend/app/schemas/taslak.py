from typing import Optional, Any
from pydantic import BaseModel


class TaslakRequest(BaseModel):
    form_tipi: str
    baslik: Optional[str] = None
    veri: dict[str, Any]


class TaslakGuncelleRequest(BaseModel):
    baslik: Optional[str] = None
    veri: dict[str, Any]
