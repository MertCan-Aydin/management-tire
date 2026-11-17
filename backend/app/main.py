import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pymysql

from .core.config import settings
from .core.db import _new_connection, get_cursor
from .core.security import decode_access_token
from .presentation import (
    auth_router,
    urun_router,
    tedarikci_router,
    musteri_router,
    alim_router,
    satis_router,
    gider_router,
    rapor_router,
    lastik_oteli_router,
    lastik_veri_router,
    aktivite_router,
)

# ── Loglama ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("management-tire")


# ── Uygulama ─────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Uygulama başlatıldı. Ortam: %s", settings.APP_ENV)
    yield
    logger.info("Uygulama kapatıldı.")


app = FastAPI(
    title="Dijital Lastik Servisi API",
    version="1.0.0",
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.APP_DEBUG else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Hata Yönetimi (stack trace sızdırmama) ────────────────────────────

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    cid = str(uuid.uuid4())[:8]
    request.state.cid = cid
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid

    if request.method in ("POST", "PUT", "DELETE") and 200 <= response.status_code < 300:
        try:
            kullanici_id = None
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                payload = decode_access_token(auth[7:])
                if payload:
                    kullanici_id = payload.get("id")
            ip = request.client.host if request.client else None
            from .data_access import aktivite_dal
            with get_cursor() as (cursor, _):
                aktivite_dal.log_ekle(
                    cursor, kullanici_id, request.method,
                    request.url.path, None, ip,
                )
        except Exception:
            pass

    return response


@app.exception_handler(pymysql.Error)
async def db_error_handler(request: Request, exc: pymysql.Error):
    cid = getattr(request.state, "cid", "-")
    logger.error("[%s] DB hatası: %s", cid, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Veritabanı işlemi sırasında hata oluştu.", "cid": cid},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    cid = getattr(request.state, "cid", "-")
    logger.exception("[%s] Beklenmeyen hata: %s %s", cid, request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Sunucu hatası. Tekrar deneyin.", "cid": cid},
    )


# ── Router'lar ───────────────────────────────────────────────────────────────

app.include_router(auth_router.router,      prefix="/api/auth",         tags=["Auth"])
app.include_router(urun_router.router,      prefix="/api/urunler",      tags=["Ürünler"])
app.include_router(tedarikci_router.router, prefix="/api/tedarikciler",  tags=["Tedarikçiler"])
app.include_router(musteri_router.router,   prefix="/api/musteriler",   tags=["Müşteriler"])
app.include_router(alim_router.router,      prefix="/api/alimlar",      tags=["Alımlar"])
app.include_router(satis_router.router,     prefix="/api/satislar",     tags=["Satışlar"])
app.include_router(gider_router.router,     prefix="/api/giderler",     tags=["Giderler"])
app.include_router(rapor_router.router,       prefix="/api/raporlar",      tags=["Raporlar"])
app.include_router(lastik_oteli_router.router, prefix="/api/lastik-oteli", tags=["Lastik Oteli"])
app.include_router(lastik_veri_router.router,  prefix="/api/lastik-verileri", tags=["Lastik Verileri"])
app.include_router(aktivite_router.router,     prefix="/api/loglar",          tags=["Aktivite Logları"])


# ── Sağlık Kontrolü ──────────────────────────────────────────────────────────

@app.get("/health", tags=["Sistem"])
def health():
    try:
        conn = _new_connection()
        conn.ping(reconnect=False)
        conn.close()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "db": "ok" if db_ok else "error",
        "env": settings.APP_ENV,
    }
