"""
İlk admin kullanıcı oluşturma scripti.
Kullanım (backend/ klasöründen):
    python -m scripts.create_admin
"""

import sys
import os
import getpass

# Projenin backend/ dizininden çalıştırılmalı
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

from app.core.config import settings
from app.core.security import hash_password
from app.core.db import get_cursor
from app.data_access import auth_dal


def main():
    print("=== Dijital Lastik Servisi — İlk Admin Kurulumu ===\n")

    kullanici_adi = input("Kullanıcı adı: ").strip()
    if not kullanici_adi:
        print("Hata: Kullanıcı adı boş olamaz.")
        sys.exit(1)

    parola = getpass.getpass("Parola (min 8 karakter): ")
    if len(parola) < 8:
        print("Hata: Parola en az 8 karakter olmalıdır.")
        sys.exit(1)

    parola2 = getpass.getpass("Parola tekrar: ")
    if parola != parola2:
        print("Hata: Parolalar eşleşmiyor.")
        sys.exit(1)

    parola_hash = hash_password(parola)

    try:
        with get_cursor() as (cursor, _):
            mevcut = auth_dal.kullanici_adi_ile_getir(cursor, kullanici_adi)
            if mevcut:
                print(f"Hata: '{kullanici_adi}' kullanıcı adı zaten mevcut.")
                sys.exit(1)
            yeni_id = auth_dal.kullanici_olustur(cursor, kullanici_adi, parola_hash, "admin")

        print(f"\nAdmin kullanıcı oluşturuldu (id={yeni_id}).")
        print("Artık uygulamaya giriş yapabilirsiniz.")
    except Exception as e:
        print(f"\nHata: {e}")
        print("DB bağlantısını ve .env dosyasını kontrol edin.")
        sys.exit(1)


if __name__ == "__main__":
    main()
