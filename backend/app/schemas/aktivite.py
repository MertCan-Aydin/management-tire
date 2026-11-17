from typing import Optional
from pydantic import BaseModel


class AktiviteLogRequest(BaseModel):
    islem_tipi: str
    sayfa: Optional[str] = None
    detay: Optional[str] = None
