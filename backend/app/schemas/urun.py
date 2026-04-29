from typing import Optional
from pydantic import BaseModel, field_validator


class UrunEkleRequest(BaseModel):
    barkod_qr: Optional[str] = None
    ad: str
    ebat: Optional[str] = None
    aciklama: Optional[str] = None
    satis_fiyati: float
    maliyet_fiyati: Optional[float] = None
    stok: int = 0
    fiziksel_urun_mu: bool = True
    resim_yolu: Optional[str] = None
    urun_tipi_id: int
    marka_id: int
    marka_modeli_id: int

    @field_validator("satis_fiyati")
    @classmethod
    def fiyat_pozitif(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Satış fiyatı 0'dan büyük olmalıdır")
        return v

    @field_validator("stok")
    @classmethod
    def stok_negatif_olamaz(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Stok negatif olamaz")
        return v


class UrunGuncelleRequest(UrunEkleRequest):
    silindi_mi: bool = False


class UrunListeFiltre(BaseModel):
    arama: Optional[str] = None
    urun_tipi_id: Optional[int] = None
    marka_id: Optional[int] = None
    sadece_stoklu: bool = False
    limit: int = 50
    offset: int = 0

    @field_validator("limit")
    @classmethod
    def limit_aralik(cls, v: int) -> int:
        return min(max(v, 1), 200)


class UrunTipiEkleRequest(BaseModel):
    ad: str


class MarkaEkleRequest(BaseModel):
    urun_tipi_id: int
    ad: str


class ModelEkleRequest(BaseModel):
    marka_id: int
    ad: str
    mevsim: Optional[str] = None

    @field_validator("mevsim")
    @classmethod
    def mevsim_kontrol(cls, v: Optional[str]) -> Optional[str]:
        if v and v not in ("Yaz", "Kış", "Dört Mevsim"):
            raise ValueError("Mevsim: Yaz, Kış veya Dört Mevsim olmalıdır")
        return v


class EprelKaydetRequest(BaseModel):
    eprel_no: str
    marka: str
    model: str
    ebat: str
    mevsim: str
    satis_fiyati: float = 0.0
    maliyet_fiyati: float = 0.0

    @field_validator("mevsim")
    @classmethod
    def mevsim_kontrol(cls, v: str) -> str:
        if v not in ("Yaz", "Kış", "Dört Mevsim"):
            raise ValueError("Mevsim: Yaz, Kış veya Dört Mevsim olmalıdır")
        return v


class EprelKaydetResponse(BaseModel):
    urun_id: int
    urun_ad: str
    yeni_mi: bool
    satis_fiyati: float
    maliyet_fiyati: float
