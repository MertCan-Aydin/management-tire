from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import suppliers, products, customers, sales, purchases, expenses, reports, dashboard

# Tabloları oluştur
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Management Panel API",
    description="Scalable Management Panel - FastAPI + PostgreSQL",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router,  prefix="/api/dashboard",  tags=["Dashboard"])
app.include_router(suppliers.router,  prefix="/api/suppliers",  tags=["Tedarikçiler"])
app.include_router(products.router,   prefix="/api/products",   tags=["Ürünler"])
app.include_router(customers.router,  prefix="/api/customers",  tags=["Müşteriler"])
app.include_router(sales.router,      prefix="/api/sales",      tags=["Satışlar"])
app.include_router(purchases.router,  prefix="/api/purchases",  tags=["Alımlar"])
app.include_router(expenses.router,   prefix="/api/expenses",   tags=["Giderler"])
app.include_router(reports.router,    prefix="/api/reports",    tags=["Raporlar"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Management Panel API çalışıyor"}

@app.get("/health")
def health():
    return {"status": "healthy"}
