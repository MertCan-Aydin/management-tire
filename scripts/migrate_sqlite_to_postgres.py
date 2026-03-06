#!/usr/bin/env python3
"""
migrate_sqlite_to_postgres.py
SQLite veritabanındaki mevcut verileri PostgreSQL'e taşır.

Kullanım:
  python3 migrate_sqlite_to_postgres.py \
    --sqlite management.db \
    --postgres "postgresql://mgmt_user:SIFRE@VPS_IP:5432/management_db"
"""
import sys
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

TABLES = [
    "suppliers", "products", "product_batches", "customers",
    "sales", "sale_items", "purchases", "purchase_items",
    "expenses", "supplier_payments", "cancellation_logs"
]

def migrate(sqlite_url: str, postgres_url: str):
    print(f"SQLite: {sqlite_url}")
    print(f"PostgreSQL: {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")

    src_engine = create_engine(f"sqlite:///{sqlite_url}")
    dst_engine = create_engine(postgres_url)

    # Tabloları oluştur (models.py üzerinden)
    print("\n[1/3] PostgreSQL tabloları oluşturuluyor...")
    import importlib.util, os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    # Backend'in app/main.py'sini import et → tabloları oluştur
    try:
        from app.database import Base
        from app import models  # noqa — tabloları tanımlar
        Base.metadata.create_all(bind=dst_engine)
        print("  ✔ Tablolar oluşturuldu")
    except ImportError as e:
        print(f"  ⚠ Backend import hatası: {e}")
        print("  Bu scripti backend klasöründen çalıştırın.")
        sys.exit(1)

    src_conn = src_engine.connect()
    dst_conn = dst_engine.connect()

    print("\n[2/3] Veriler taşınıyor...")
    total_rows = 0

    for table in TABLES:
        try:
            rows = src_conn.execute(text(f"SELECT * FROM {table}")).fetchall()
            if not rows:
                print(f"  {table}: boş, atlandı")
                continue

            col_names = src_conn.execute(text(f"PRAGMA table_info({table})" if "sqlite" in sqlite_url
                                              else f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"))

            # SQLite PRAGMA ile kolon adlarını al
            pragma = src_conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            cols = [r[1] for r in pragma]

            # Satırları dict'e dönüştür
            data = [dict(zip(cols, row)) for row in rows]

            # Postgres'e ekle (mevcut verileri sil)
            dst_conn.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            dst_conn.execute(
                text(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join([':' + c for c in cols])})"),
                data
            )
            dst_conn.commit()

            # Sequence'ları güncelle (PostgreSQL'de ID'ler için)
            max_id = max(r.get("id", 0) for r in data) if data else 0
            if max_id > 0:
                dst_conn.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), {max_id})"))
                dst_conn.commit()

            print(f"  ✔ {table}: {len(data)} satır taşındı")
            total_rows += len(data)
        except Exception as e:
            print(f"  ✗ {table}: HATA — {e}")
            dst_conn.rollback()

    src_conn.close()
    dst_conn.close()

    print(f"\n[3/3] Tamamlandı! Toplam {total_rows} satır taşındı.")
    print("\nDoğrulama için:")
    print(f"  psql {postgres_url.split('@')[1] if '@' in postgres_url else postgres_url}")
    print("  \\dt   (tabloları listele)")
    print("  SELECT COUNT(*) FROM sales;")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SQLite → PostgreSQL veri göçü")
    parser.add_argument("--sqlite",   required=True, help="SQLite dosya yolu (ör: management.db)")
    parser.add_argument("--postgres", required=True, help="PostgreSQL bağlantı URL'si")
    args = parser.parse_args()
    migrate(args.sqlite, args.postgres)
