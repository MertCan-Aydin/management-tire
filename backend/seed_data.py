import os
import sys
import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app.models import Supplier, ProductType, ProductBrand, Product, Customer, Expense

# Tabloları oluştur
Base.metadata.create_all(bind=engine)

def seed_data():
    db = SessionLocal()
    try:
        # Daha önce veri var mı diye kontrol et (Eğer veritabanı doluysa bir şey yapma)
        if db.query(Supplier).first():
            print("Veritabanında zaten veri var. İşlem iptal edildi.")
            return

        print("Test verileri ekleniyor...")
        
        # --- 1. TEDARİKÇİLER ---
        sup1 = Supplier(name="Lassa Fabrika", contact_info="Ahmet Bey - 0532 111 2233", current_debt=0)
        sup2 = Supplier(name="Michelin Türkiye", contact_info="İstanbul Merkez", current_debt=15000.0)
        sup3 = Supplier(name="Petlas Toptan", contact_info="Kırşehir Fabrika", current_debt=5000.0)
        db.add_all([sup1, sup2, sup3])
        db.commit()

        # --- 2. ÜRÜN TİPLERİ ---
        type_tire = ProductType(name="Binek Araç Lastiği")
        type_commercial = ProductType(name="Ticari Araç Lastiği")
        type_battery = ProductType(name="Akü")
        type_rim = ProductType(name="Jant")
        db.add_all([type_tire, type_commercial, type_battery, type_rim])
        db.commit()

        # --- 3. ÜRÜN MARKALARI ---
        brand_lassa = ProductBrand(name="Lassa", product_type_id=type_tire.id)
        brand_michelin = ProductBrand(name="Michelin", product_type_id=type_tire.id)
        brand_petlas = ProductBrand(name="Petlas", product_type_id=type_commercial.id)
        brand_mutlu = ProductBrand(name="Mutlu Akü", product_type_id=type_battery.id)
        db.add_all([brand_lassa, brand_michelin, brand_petlas, brand_mutlu])
        db.commit()

        # --- 4. ÜRÜNLER ---
        prod1 = Product(name="Lassa 205/55 R16 Snoways 4", description="Kışlık Binek Lastik", price=1500.0, cost_price=1200.0, stock=50, product_type_id=type_tire.id, brand_id=brand_lassa.id, brand_model="Snoways 4", supplier_id=sup1.id)
        prod2 = Product(name="Michelin 225/45 R17 CrossClimate", description="Dört Mevsim Kaliteli Lastik", price=2500.0, cost_price=2000.0, stock=24, product_type_id=type_tire.id, brand_id=brand_michelin.id, brand_model="CrossClimate", supplier_id=sup2.id)
        prod3 = Product(name="Petlas 215/75 R16C Fullpower", description="Hafif Ticari Yazlık Lastik", price=2200.0, cost_price=1800.0, stock=30, product_type_id=type_commercial.id, brand_id=brand_petlas.id, brand_model="Fullpower PT825", supplier_id=sup3.id)
        prod4 = Product(name="Mutlu Akü 12V 72Ah Dar Kutu", description="Start Stop Akü", price=2500.0, cost_price=2000.0, stock=15, product_type_id=type_battery.id, brand_id=brand_mutlu.id, brand_model="12V 72Ah", supplier_id=sup1.id)
        db.add_all([prod1, prod2, prod3, prod4])
        db.commit()

        # --- 5. MÜŞTERİLER ---
        cust1 = Customer(name="Ahmet Emin Yılmaz", phone="0555 555 55 55", car_brand="Toyota Corolla", car_plate="06 ABC 123", notes="Sadık Müşteri")
        cust2 = Customer(name="Mehmet Şoför", phone="0533 333 33 33", car_brand="Fiat Egea", car_plate="34 T 9999", notes="Taksici")
        cust3 = Customer(name="Kurumsal Lojistik A.Ş.", phone="0212 212 12 12", car_brand="Ford Ducato", car_plate="35 KRM 01", notes="Aylık ödeme yapar")
        db.add_all([cust1, cust2, cust3])
        db.commit()

        # --- 6. GİDERLER ---
        exp1 = Expense(description="Dükkan Aylık Kirası", amount=15000.0, timestamp=datetime.datetime.now())
        exp2 = Expense(description="Enerjisa Ekim Faturası", amount=2500.0, timestamp=datetime.datetime.now())
        exp3 = Expense(description="Haftalık Çay Kahve", amount=500.0, timestamp=datetime.datetime.now())
        db.add_all([exp1, exp2, exp3])
        db.commit()

        print("🎉 Tüm test verileri başarıyla eklendi!")

    except Exception as e:
        print(f"Hata oluştu: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
