# Dijital Lastik Servisi — Mimari Özeti

## Yığın (Stack)

| Katman | Teknoloji |
|--------|-----------|
| Veritabanı | MySQL / MariaDB (Stored Procedure ile) |
| Backend | Python 3.x + FastAPI |
| Masaüstü | PyQt6 |
| Mobil | Flutter |
| Reverse Proxy | Nginx + Let's Encrypt |
| Servis Yönetimi | systemd |

## N-Katmanlı Mimari

```
Presentation  →  Business  →  Data Access  →  MariaDB
(Router)          (Service)      (DAL)         (SP only)
```

**Kural:** Hiçbir katmanda `SELECT/INSERT/UPDATE/DELETE` yazmak yasak.
Tüm veritabanı erişimi yalnızca DAL'dan, yalnızca `CALL sp_...()` ile.

## Klasör Yapısı

```
management-tire/
├── backend/          # FastAPI (BL + DAL)
├── db/
│   └── migrations/   # Versiyonlu SQL scriptleri
├── desktop/          # PyQt6 masaüstü uygulaması
├── mobile/           # Flutter mobil uygulaması
└── deploy/           # Nginx, systemd, kurulum scriptleri
```

## Deploy Akışı

```
git push  →  VPS: git pull  →  pip install (gerekirse)
          →  migration uygula (gerekirse)
          →  systemctl restart management-tire-api
```

## Güvenlik Kuralları

- `.env` dosyası repoya girmez (yalnızca VPS'te)
- DB kullanıcısı (`lastik_user`) yalnızca `EXECUTE` yetkisine sahip
- JWT (access 60dk + refresh 30gün, DB'de revoke edilebilir)
- Şifre: `argon2id`
- HTTPS zorunlu, MariaDB sadece localhost dinler
- SSH key-only, UFW (22/80/443), fail2ban
