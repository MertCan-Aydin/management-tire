from pydantic import BaseModel, field_validator


class LoginRequest(BaseModel):
    kullanici_adi: str
    parola: str

    @field_validator("kullanici_adi", "parola")
    @classmethod
    def bos_olamaz(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Bu alan boş bırakılamaz")
        return v.strip()


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class ParolaDegistirRequest(BaseModel):
    mevcut_parola: str
    yeni_parola: str

    @field_validator("yeni_parola")
    @classmethod
    def parola_uzunluk(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Parola en az 8 karakter olmalıdır")
        return v


class PinLoginRequest(BaseModel):
    pin: str

    @field_validator("pin")
    @classmethod
    def pin_kontrol(cls, v: str) -> str:
        v = v.strip()
        if not v.isdigit():
            raise ValueError("PIN yalnızca rakamlardan oluşmalıdır")
        if len(v) != 4:
            raise ValueError("PIN 4 haneli olmalıdır")
        return v


class KullaniciBilgi(BaseModel):
    id: int
    kullanici_adi: str
    rol: str
    aktif_mi: bool
