# DB Migrations

Sırayla çalıştırılacak. Her dosya bir kez uygulanır.

| Dosya | İçerik |
|-------|--------|
| 001_tablolar.sql | Veritabanı oluşturma + tüm tablolar |
| 002_stored_procedures.sql | Tüm CRUD stored procedure'leri |
| 003_functions_triggers.sql | UDF fonksiyonları + trigger'lar |
| 004_indexes.sql | Performans index'leri |
| 005_auth.sql | Kullanıcı/token tabloları + auth SP'leri |
| 006_raporlar.sql | Rapor ve dashboard SP'leri |

## Uygulama

```bash
mysql -u lastik_user -p DijitalLastikServisiDB < 001_tablolar.sql
mysql -u lastik_user -p DijitalLastikServisiDB < 002_stored_procedures.sql
mysql -u lastik_user -p DijitalLastikServisiDB < 003_functions_triggers.sql
mysql -u lastik_user -p DijitalLastikServisiDB < 004_indexes.sql
mysql -u lastik_user -p DijitalLastikServisiDB < 005_auth.sql
mysql -u lastik_user -p DijitalLastikServisiDB < 006_raporlar.sql
```

> Not: İlk kurulumda `001_tablolar.sql` için admin yetkili kullanıcı gerekar (CREATE DATABASE).
> Sonraki dosyalar `lastik_user` ile çalıştırılabilir (EXECUTE + CREATE PROCEDURE için geçici ALTER yetkisi gerekebilir).
