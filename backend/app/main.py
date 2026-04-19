from fastapi import FastAPI, Depends, HTTPException, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy import inspect, text
from app.database import engine, Base
from app.config import settings
from app.routers import suppliers, products, customers, sales, purchases, expenses, reports, dashboard, auth

Base.metadata.create_all(bind=engine)


def _ensure_schema():
    """Basit runtime migration — yeni kolonlar eksikse ekler.
    Hem SQLite hem PostgreSQL ile uyumlu ALTER TABLE kullanır.
    Yetki/izin hataları backend'i düşürmesin diye yutulur (log'a yazılır)."""
    import logging
    log = logging.getLogger("uvicorn.error")
    try:
        insp = inspect(engine)
        # product_brand_models.season
        if insp.has_table("product_brand_models"):
            cols = {c["name"] for c in insp.get_columns("product_brand_models")}
            if "season" not in cols:
                try:
                    with engine.begin() as conn:
                        conn.execute(text(
                            "ALTER TABLE product_brand_models ADD COLUMN season VARCHAR(20)"
                        ))
                    log.info("Migration: product_brand_models.season eklendi")
                except Exception as e:
                    log.warning(
                        "Migration atlandi (season kolonu manuel eklenmeli): %s", e
                    )
    except Exception as e:
        log.warning("ensure_schema hata verdi, atlandi: %s", e)

_ensure_schema()

app = FastAPI(docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(key: str = Security(api_key_header)):
    if key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Geçersiz veya eksik API anahtarı")
    return key

deps = [Depends(verify_api_key)]

# Auth endpoint'leri API key gerektirmez (login için)
app.include_router(auth.router,      prefix="/api/auth")

app.include_router(dashboard.router, prefix="/api/dashboard", dependencies=deps)
app.include_router(suppliers.router, prefix="/api/suppliers", dependencies=deps)
app.include_router(products.router,  prefix="/api/products",  dependencies=deps)
app.include_router(customers.router, prefix="/api/customers", dependencies=deps)
app.include_router(sales.router,     prefix="/api/sales",     dependencies=deps)
app.include_router(purchases.router, prefix="/api/purchases", dependencies=deps)
app.include_router(expenses.router,  prefix="/api/expenses",  dependencies=deps)
app.include_router(reports.router,   prefix="/api/reports",   dependencies=deps)

@app.get("/health")
def health():
    return {"status": "healthy"}
