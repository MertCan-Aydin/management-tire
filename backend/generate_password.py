#!/usr/bin/env python3
"""
Kullanim: python3 generate_password.py
Ciktidaki hash'i .env dosyasina APP_PASSWORD_HASH olarak ekleyin.
"""
from passlib.context import CryptContext
import getpass

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
password = getpass.getpass("Yeni sifrenizi girin: ")
confirm  = getpass.getpass("Tekrar girin: ")

if password != confirm:
    print("Sifreler eslesmiyor!")
else:
    hashed = pwd_context.hash(password)
    print(f"\nHash olusturuldu. .env dosyasina ekleyin:\n")
    print(f"APP_PASSWORD_HASH={hashed}\n")
