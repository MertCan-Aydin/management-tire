from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TOKEN_EXPIRE_HOURS = 12


class PinSetupRequest(BaseModel):
    pin: str           # 4 haneli

class PinLoginRequest(BaseModel):
    pin: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _create_token() -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode({"sub": "user", "exp": expire}, settings.SECRET_KEY, algorithm="HS256")


def _pin_is_set() -> bool:
    return bool(settings.PIN_HASH)


@router.get("/status")
def auth_status():
    """PIN kurulu mu? Frontend buna göre setup veya login ekranı açar."""
    return {"pin_set": _pin_is_set()}


@router.post("/setup", response_model=TokenOut)
def setup_pin(data: PinSetupRequest):
    """İlk kurulum — PIN henüz yoksa çalışır."""
    if _pin_is_set():
        raise HTTPException(status_code=400, detail="PIN zaten kurulu. Önce sıfırlayın.")
    if len(data.pin) != 4 or not data.pin.isdigit():
        raise HTTPException(status_code=400, detail="PIN 4 haneli rakam olmalıdır.")

    hashed = pwd_context.hash(data.pin)

    # .env dosyasına yaz
    env_path = "/opt/management_panel/.env"
    try:
        with open(env_path, "r") as f:
            lines = f.readlines()
        # PIN_HASH satırı varsa güncelle, yoksa ekle
        pin_found = False
        new_lines = []
        for line in lines:
            if line.startswith("PIN_HASH="):
                new_lines.append(f"PIN_HASH={hashed}\n")
                pin_found = True
            else:
                new_lines.append(line)
        if not pin_found:
            new_lines.append(f"PIN_HASH={hashed}\n")
        with open(env_path, "w") as f:
            f.writelines(new_lines)
        # settings'i yenile
        settings.__init__()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ENV yazma hatası: {e}")

    return TokenOut(access_token=_create_token())


@router.post("/login", response_model=TokenOut)
def login(data: PinLoginRequest):
    if not _pin_is_set():
        raise HTTPException(status_code=400, detail="PIN kurulmamış.")
    if len(data.pin) != 4 or not data.pin.isdigit():
        raise HTTPException(status_code=400, detail="Geçersiz PIN formatı.")
    if not pwd_context.verify(data.pin, settings.PIN_HASH):
        raise HTTPException(status_code=401, detail="Hatalı PIN.")
    return TokenOut(access_token=_create_token())


@router.post("/verify")
def verify_token(data: dict):
    token = data.get("token", "")
    try:
        jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return {"valid": True}
    except Exception:
        raise HTTPException(status_code=401, detail="Geçersiz veya süresi dolmuş token.")
