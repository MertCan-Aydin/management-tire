# Veritabanı Yedekleme

VPS silinse, disk bozulsa ya da biri yanlışlıkla veri silse bile **MariaDB verisinin kaybolmaması** için kurulan sistem.

> **Neden var:** Daha önce VPS ücreti ödenmediği için sağlayıcı sunucuyu sildi ve veriler gitti.
> Bu sistemin temel kuralı şu: **yedek, VPS sağlayıcısından bağımsız bir yerde durur.** VPS tamamen
> ortadan kalksa bile yedek GitHub'da ve kendi bilgisayarında durmaya devam eder.

---

## Özet

```
 VPS (her 3 saatte bir, systemd timer)
 ┌──────────────────────────────────────────────────────────────┐
 │ MariaDB ──mariadb-dump──▶ .sql ──doğrula──▶ gzip ──age──▶ .age │
 └──────────────────────────────────────────────┬───────────────┘
                                                │ git push (deploy key)
                                                ▼
                               GitHub PRIVATE repo (şifreli dosyalar)
                                                │ git pull (haftada bir)
                                                ▼
                                   Kendi bilgisayarın (2. kopya)
                                   + age private key (sadece sende)
```

| Özellik | Değer |
|---|---|
| Sıklık | 3 saatte bir (00, 03, 06 … 21). Sunucu kapalıyken kaçırılan yedek açılınca hemen alınır |
| En fazla veri kaybı | ~3 saat |
| İçerik | Tüm tablolar ve veriler, stored procedure'ler, function'lar, trigger'lar, event'ler, ayrıca `backend/.env` |
| Şifreleme | `age`. VPS'te sadece **public key** var, yani VPS yedekleri şifreler ama açamaz |
| Doğrulama | Her yedekte tablo, procedure/function ve trigger sayısı DB ile karşılaştırılır. Eksik varsa yedek **başarısız** sayılır |
| Saklama | Repo'nun son halinde 30 gün. Daha eskiler **git geçmişinde** durur, hiçbiri silinmez |
| Bildirim | Yedek alınamazsa healthchecks.io üzerinden e-posta veya Telegram gelir |

### Dosyalar

| Projede | VPS'te kurulduğu yer | Görevi |
|---|---|---|
| `deploy/yedek/yedek_kurulum.sh` | — | Tek seferlik kurulum (tekrar çalıştırılabilir) |
| `deploy/yedek/yedekle.sh` | `/usr/local/sbin/lastik-yedekle` | Yedeği alır, doğrular, şifreler, push'lar |
| `deploy/yedek/geri_yukle.sh` | `/usr/local/sbin/lastik-geri-yukle` | Yedekten geri yükler |
| `deploy/yedek/lastik-yedek.service` / `.timer` | `/etc/systemd/system/` | 3 saatte bir çalıştırır |
| — | `/etc/lastik-yedek/` | Ayarlar, DB parolası, deploy key, age public key (sadece root okur) |
| — | `/var/lib/lastik-yedek/` | Yerel repo klonu, son çalışmanın logu |

---

## Kurulum

Kurulum yaklaşık 15 dakika sürer. Sırayla:

### 1. Şifreleme anahtarını üret (kendi bilgisayarında, VPS'te DEĞİL)

```bash
brew install age                 # Mac. Windows: winget install FiloSottile.age
age-keygen -o lastik-yedek-anahtar.txt
```

Çıktı:
```
Public key: age1qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqs3290gq
```

- **`age1...` (public key):** Kurulumda VPS'e yapıştırılacak. Gizli değil.
- **`lastik-yedek-anahtar.txt` içindeki `AGE-SECRET-KEY-...` (private key):** Yedekleri açan **tek** anahtar.
  - **Kaybolursa yedekler bir daha açılamaz.** Kimse açamaz, GitHub da açamaz.
  - En az **iki yerde** sakla: şifre yöneticisi (Bitwarden, 1Password, iCloud Anahtar Zinciri notu) **ve** USB bellek ya da kağıt çıktı.
  - VPS'e, GitHub'a, projeye **koyma**.
  - İstersen ikinci bir kişi için ayrı bir anahtar üretilebilir. Kurulumda birden fazla public key eklenebilir, o zaman her iki anahtar da yedekleri açar.

### 2. GitHub'da private repo aç

1. https://github.com/new
2. Name: `lastik-db-yedek`, **Private**
3. README, .gitignore **ekleme** (boş kalsın)
4. Create

> GitHub hesabında **iki adımlı doğrulama (2FA)** açık olmalı. Yedekler bu hesaptan erişilebilir.

### 3. (Önerilen) Bildirim kur: healthchecks.io

Yedek **alınamazsa** haber almak için (ücretsiz):

1. https://healthchecks.io → kayıt ol
2. **Add Check** → Name: `lastik-yedek`, **Period: 3 hours**, **Grace: 1 hour**
3. Ping URL'ini kopyala (`https://hc-ping.com/xxxxxxxx-...`)
4. Integrations kısmından e-posta (varsayılan) ya da Telegram ekle

Script her başarılı yedekte bu adrese ping atar. 4 saat boyunca ping gelmezse ya da script hata bildirirse sana haber gelir.

### 4. VPS'te kurulumu çalıştır

```bash
ssh root@194.36.85.139
cd /opt/repo            # repo nerede klonluysa
git pull
sudo bash deploy/yedek/yedek_kurulum.sh
```

Script sırasıyla:
1. `age`, `git`, `curl` paketlerini kurar
2. MariaDB'de **sadece okuma yetkili** `yedek_user` kullanıcısını açar (parolası rastgele üretilir, `/etc/lastik-yedek/my.cnf`)
3. **age public key**'i ister (1. adımdaki `age1...`)
4. Bir **deploy key** üretir ve ekrana yazar. Bu key GitHub'da şuraya eklenir:
   **Repo → Settings → Deploy keys → Add deploy key**, **"Allow write access" işaretli**.
   > Hesabın *Settings → SSH and GPG keys* kısmına **ekleme**. Oraya eklenen key bütün repolara erişir.
   > Deploy key sadece bu yedek reposuna erişebilir.
5. Repo adresini ister (`git@github.com:KULLANICI/lastik-db-yedek.git`)
6. healthchecks.io ping URL'ini ister (boş bırakılabilir)
7. Timer'ı açar ve **ilk yedeği hemen alır**

Sonunda şuna benzer bir çıktı görmelisin:
```
  tablo: 21/21  procedure+function: 112/112  trigger: 4/4
  ✓ DijitalLastikServisiDB-20261008-153012.sql.gz.age (412K, ham 3.1M)
  ✓ Push OK. GitHub'a gönderilen toplam yaklaşık 0 MB
===== Tamamlandı =====
```

GitHub'daki repoda `dumps/2026/10/...sql.gz.age` dosyası görünmelidir.

### 5. Kurulumdan hemen sonra: geri yüklemeyi bir kez dene

Yedeğin gerçekten açıldığını görmeden kurulum bitmiş sayılmaz. Aşağıdaki
[Aylık geri yükleme testi](#aylık-geri-yükleme-testi) adımlarını bir kez uygula.

### 6. (Önerilen) Kendi bilgisayarına ikinci kopya

```bash
git clone git@github.com:KULLANICI/lastik-db-yedek.git ~/lastik-db-yedek
# Haftada bir:
cd ~/lastik-db-yedek && git pull
```

Bu şu durumlara karşı korur: GitHub hesabına erişim kaybolursa, ya da VPS'e giren biri repo geçmişini silmeye çalışırsa.

### 7. (Opsiyonel) Geçmişin silinmesini engelle

VPS ele geçirilirse saldırgan deploy key ile `git push --force` yaparak geçmişi silebilir. Bunu engellemek için:
**Repo → Settings → Rules → Rulesets → New branch ruleset**, hedef `main`,
**"Restrict deletions"** ve **"Block force pushes"** işaretlenir.

> Private repolarda bu özellik **GitHub Pro** gerektirir (ya da repo bir organizasyona taşınır).
> Pro yoksa 6. adımdaki yerel kopya aynı koruma işini görür.

---

## Günlük kullanım

```bash
systemctl list-timers lastik-yedek.timer       # sonraki yedek ne zaman
cat /var/lib/lastik-yedek/son_basarili         # son başarılı yedek zamanı
cat /var/lib/lastik-yedek/son_calisma.log      # son çalışmanın çıktısı
journalctl -u lastik-yedek -n 50               # geçmiş loglar
sudo lastik-yedekle                            # şimdi elle yedek al (riskli bir işlemden önce)
```

**Kritik bir işlemden önce** (migration, toplu silme, sunucu taşıma) elle `sudo lastik-yedekle` çalıştırmak iyi bir alışkanlıktır.

---

## Geri yükleme

`lastik-geri-yukle` güvenli varsayılanlarla çalışır:
- Hedef verilmezse yedeği **`DijitalLastikServisiDB_geri`** adlı **test kopyasına** yükler. Canlı DB'ye dokunmaz.
- Önce dosyanın sağlam olduğunu kontrol eder. Bozuksa hiçbir şeyi silmez.
- Canlıya yüklerken `EVET` yazdırarak onay ister, **mevcut hali önce kaydeder**
  (`/var/lib/lastik-yedek/geri_yukleme_oncesi-*.sql.gz`), API'yi durdurur, işi bitince yeniden başlatır.

### Şifre çözme: iki yol

**A) Kendi bilgisayarında çöz, VPS'e şifresiz gönder (önerilen, private key VPS'e hiç gitmez):**
```bash
cd ~/lastik-db-yedek && git pull
age -d -i ~/lastik-yedek-anahtar.txt \
    dumps/2026/10/DijitalLastikServisiDB-20261008-150000.sql.gz.age \
    > /tmp/yedek.sql.gz
scp /tmp/yedek.sql.gz root@VPS_IP:/root/
rm /tmp/yedek.sql.gz
```

**B) Anahtarı geçici olarak VPS'e koy:**
```bash
scp ~/lastik-yedek-anahtar.txt root@VPS_IP:/root/
# ... geri yükleme ...
ssh root@VPS_IP 'shred -u /root/lastik-yedek-anahtar.txt'   # İŞ BİTİNCE MUTLAKA SİL
```

### Aylık geri yükleme testi

Hiç denenmemiş bir yedeğe güvenilmez. Ayda bir (5 dakika):

```bash
# VPS'te, A yolu ile /root/yedek.sql.gz hazırlandıktan sonra:
sudo lastik-geri-yukle /root/yedek.sql.gz
#   ✓ Yedek sağlam
#   ✓ Yüklendi: 21 tablo, 112 procedure/function, 4 trigger
#   Müşteri: 1340  Satış: 5821  Son satış tarihi: 2026-10-08 14:52:10
mariadb -e 'DROP DATABASE `DijitalLastikServisiDB_geri`;'
rm /root/yedek.sql.gz
```

Sayılar mantıklıysa (son satış tarihi yedeğin saatine yakınsa) test geçmiş demektir.

### Senaryo 1: Yanlışlıkla veri silindi, VPS çalışıyor

1. Silinmeden **önceki** en yakın yedeği bul (dosya adında tarih ve saat var).
2. Önce test kopyasına yükle, veriyi kontrol et:
   ```bash
   sudo lastik-geri-yukle /root/yedek.sql.gz
   ```
3. Sadece birkaç kayıt geri gelecekse, canlıyı komple değiştirmek yerine kayıtları test kopyasından canlıya taşı:
   ```sql
   INSERT INTO DijitalLastikServisiDB.musteriler
   SELECT * FROM DijitalLastikServisiDB_geri.musteriler WHERE id IN (...);
   ```
4. Her şey geri dönecekse (yedekten sonraki kayıtlar kaybolur):
   ```bash
   sudo lastik-geri-yukle /root/yedek.sql.gz DijitalLastikServisiDB
   ```

### Senaryo 2: VPS tamamen gitti (silindi, hacklendi, sağlayıcı kapandı)

1. Yeni bir VPS al.
2. Normal kurulumu yap: `DEPLOY.md` ya da `vps_kurulum.sh`. Bu boş bir DB, `lastik_user`, API ve nginx kurar.
3. `.env` dosyasını yedekten geri al (JWT secret vb. aynı kalsın, kullanıcıların oturumu bozulmasın):
   ```bash
   # kendi bilgisayarında:
   age -d -i ~/lastik-yedek-anahtar.txt ~/lastik-db-yedek/ek/opt_repo_backend_.env.age > env.txt
   scp env.txt root@YENI_IP:/opt/repo/backend/.env && rm env.txt
   ```
4. En son yedeği A yolu ile çöz, yeni VPS'e gönder ve **canlıya** yükle:
   ```bash
   sudo lastik-geri-yukle /root/yedek.sql.gz DijitalLastikServisiDB
   ```
5. Yedeklemeyi yeni VPS'te tekrar kur: `sudo bash deploy/yedek/yedek_kurulum.sh`.
   **Yeni deploy key** üretilir. GitHub'da eski VPS'in deploy key'ini **sil**, yenisini ekle.
6. Masaüstü ve mobil uygulamalarda sunucu IP'si değiştiyse güncelle.

### Senaryo 3: 30 günden eski bir yedek lazım

Eski dosyalar repo'nun son halinde yok ama git geçmişinde duruyor:
```bash
cd ~/lastik-db-yedek && git pull
# Belirli bir güne ait dosyaları bul:
git log --all --name-only --format='%h' -- 'dumps/2026/03/*' | grep 20260315
# Commit'ten dosyayı çıkar (çalışma klasörünü değiştirmeden):
git show <commit>:dumps/2026/03/DijitalLastikServisiDB-20260315-120000.sql.gz.age > eski.sql.gz.age
age -d -i ~/lastik-yedek-anahtar.txt eski.sql.gz.age > eski.sql.gz
```

> `git checkout <commit> -- dumps/` **kullanma**. Bu komut dosyaları repo'nun son halinin üzerine yazar.

---

## Repo dolunca

Şifreli dosyalar sıkıştırıldığı için git aralarında fark (delta) çıkaramaz. Her yedek tam boyutuyla
geçmişte kalır ve repo yavaş yavaş büyür. GitHub 1 GB üstündeki repolar için uyarı veriyor.

- Script GitHub'a gönderilen toplam boyutu takip eder ve **800 MB**'ı geçince healthchecks.io
  üzerinden uyarı gönderir. Yedek almaya devam eder.
- VPS'teki yerel klon kendi kendini küçültür (300 MB'ı geçince geçmişsiz olarak yeniden klonlanır),
  böylece VPS diski dolmaz.

Uyarı gelince (lastik dükkanı DB'si için muhtemelen yılda bir ya da daha seyrek):
1. GitHub'da yeni bir private repo aç: `lastik-db-yedek-2027`
2. Aynı deploy key'i (`cat /etc/lastik-yedek/github_key.pub`) yeni repoya **write access** ile ekle
3. VPS'te:
   ```bash
   sudo sed -i 's|^REPO_URL=.*|REPO_URL="git@github.com:KULLANICI/lastik-db-yedek-2027.git"|' /etc/lastik-yedek/yedek.conf
   sudo rm -rf /var/lib/lastik-yedek/repo /var/lib/lastik-yedek/gonderilen_toplam_kb /var/lib/lastik-yedek/ozet_*
   # yeni repo boşsa ilk commit için kurulumu tekrar çalıştırmak yeterli:
   sudo bash deploy/yedek/yedek_kurulum.sh
   ```
4. Eski repoda deploy key'i **sil**, sonra **Settings → Archive this repository** ile salt-okunur yap.
   Eski yedekler orada güvenle durur.

---

## Güvenlik: ne nerede, ne olursa ne olur

| Ne | Nerede | Kim erişir |
|---|---|---|
| age **private** key | Senin bilgisayarın + şifre yöneticisi + USB | Sadece sen |
| age public key | VPS `/etc/lastik-yedek/alicilar.txt` | Gizli değil |
| `yedek_user` parolası | VPS `/etc/lastik-yedek/my.cnf` (600) | root. Sadece okuma yetkisi var |
| Deploy key | VPS `/etc/lastik-yedek/github_key` (600) | root. Sadece yedek reposuna yazabilir |
| Yedekler | GitHub private repo + senin bilgisayarın | Şifreli. Private key olmadan anlamsız |

| Durum | Sonuç |
|---|---|
| VPS silindi | GitHub'dan geri yüklenir (Senaryo 2) |
| GitHub repo yanlışlıkla public oldu / hesap ele geçirildi | Dosyalar şifreli, müşteri verisi okunamaz (KVKK açısından kritik) |
| VPS hacklendi | Saldırgan eski yedekleri **okuyamaz** (private key VPS'te yok). Diğer GitHub repolarına **erişemez** (deploy key). Geçmişi force-push ile silmeye çalışırsa → 7. adımdaki kural ya da 6. adımdaki yerel kopya korur |
| MariaDB parolası değişti / servis durdu | Yedek başarısız olur, **eski yedekler silinmez**, healthchecks.io haber verir |
| VPS diski doluyor | 1 GB'tan az yer kalınca yedek alınmaz (MariaDB'yi çökertmemek için) ve haber verilir |
| Private key kayboldu | Yedekler **açılamaz**. Yeni anahtar üret, `alicilar.txt`'yi güncelle. Bundan sonraki yedekler yeni anahtarla açılır |

---

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| `Repo klonlanamadı` / `Push başarısız` | GitHub'da deploy key duruyor mu, "Allow write access" işaretli mi? Test: `sudo GIT_SSH_COMMAND="ssh -i /etc/lastik-yedek/github_key -o IdentitiesOnly=yes" git ls-remote <REPO_URL>` |
| `Dump'ta eksik procedure/function var` | `yedek_user` routine'leri okuyamıyor. Root ile: `GRANT SELECT ON mysql.proc TO 'yedek_user'@'localhost';` (MariaDB 11.3+: `GRANT SHOW CREATE ROUTINE ON DijitalLastikServisiDB.* TO 'yedek_user'@'localhost';`) |
| `Access denied for user 'yedek_user'` | `/etc/lastik-yedek/my.cnf`'yi sil ve `yedek_kurulum.sh`'yi tekrar çalıştır (kullanıcı ve parola yeniden oluşturulur) |
| `Diskte sadece X MB boş yer var` | `df -h`, `du -sh /var/log/* /var/lib/mysql`. Yer aç |
| Timer çalışmıyor | `systemctl status lastik-yedek.timer`, gerekirse `systemctl enable --now lastik-yedek.timer` |
| Yedek repo'ya elle push yapıldı, VPS push edemiyor | Elle push yapma. Olduysa VPS'te `sudo rm -rf /var/lib/lastik-yedek/repo`, bir sonraki çalışmada yeniden klonlanır |

---

## İşin teknik olmayan tarafı

Yedek, VPS'in silinmesine karşı korur ama **sorunu önlemez**. Bunlar da önemli:
- VPS sağlayıcısında **otomatik ödeme** açık olsun. Kartın son kullanma tarihini takvime yaz.
- Sağlayıcının fatura e-postaları **sürekli bakılan** bir adrese gelsin.
- GitHub ve VPS hesaplarında **2FA** açık olsun. Kurtarma kodları private key ile birlikte saklansın.

---

## Tasarım kararları

Bu sistem, internetten bulunan bir "MariaDB → GitHub" script'inin incelenip düzeltilmiş halidir.
Orijinal script'teki sorunlar ve çözümleri:

| Orijinal sorun | Çözüm |
|---|---|
| Dump başarısız olsa da eski yedekleri siliyordu, 24 saat sonra hiç yedek kalmıyordu | Doğrulama geçmezse script durur. Hiçbir şey silinmez, push edilmez, bildirim gelir |
| Yedekler şifresiz GitHub'a gidiyordu (müşteri telefonları, plakalar) | `age` ile şifreleme. VPS'te sadece public key var |
| SSH key hesap düzeyindeydi (bütün repolara erişim) | Sadece yedek reposuna erişen deploy key |
| DB root kullanıcısıyla dump alıyordu | Sadece okuma yetkili `yedek_user` |
| "24 kopya tutar" deniyordu ama git geçmişi sınırsız büyüyordu, VPS diski dolabilirdi | VPS klonu kendini küçültür, boyut takip edilip uyarı verilir, repo yenileme adımları yukarıda |
| Geri yükleme komutu canlı DB'yi uyarısız `DROP` ediyordu | Varsayılan hedef test kopyası. Canlı için onay istenir ve önce mevcut hal kaydedilir |
| Hata bildirimi yoktu | healthchecks.io |
| Cron sunucu kapalıyken kaçırılan yedeği hiç almıyordu | systemd timer `Persistent=true` |
