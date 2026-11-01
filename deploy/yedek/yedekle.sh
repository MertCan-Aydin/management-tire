#!/bin/bash
# ============================================================
# Dijital Lastik Servisi — MariaDB Yedekleme
#
# MariaDB dump → doğrula → gzip → age ile şifrele → GitHub'a push
# lastik-yedek.timer ile 3 saatte bir çalışır. Elle: sudo lastik-yedekle
#
# Kurulum ve geri yükleme: docs/veritabani-yedekleme.md
# ============================================================
set -Eeuo pipefail
umask 077

AYAR_DOSYASI="${LASTIK_YEDEK_AYAR:-/etc/lastik-yedek/yedek.conf}"
if [[ ! -r "$AYAR_DOSYASI" ]]; then
    echo "HATA: $AYAR_DOSYASI okunamıyor. Önce yedek_kurulum.sh çalıştırılmalı." >&2
    exit 1
fi
# shellcheck source=/dev/null
source "$AYAR_DOSYASI"

# ── Varsayılanlar (yedek.conf içinden değiştirilebilir) ─────
: "${REPO_URL:?yedek.conf içinde REPO_URL yok}"
: "${DB_NAME:=DijitalLastikServisiDB}"
: "${AYAR_DIR:=/etc/lastik-yedek}"
: "${MYCNF:=$AYAR_DIR/my.cnf}"
: "${ALICILAR:=$AYAR_DIR/alicilar.txt}"
: "${SSH_ANAHTAR:=$AYAR_DIR/github_key}"
: "${KNOWN_HOSTS:=$AYAR_DIR/known_hosts}"
: "${DURUM_DIR:=/var/lib/lastik-yedek}"
: "${REPO_DIR:=$DURUM_DIR/repo}"
: "${SAKLAMA_GUN:=30}"           # repo'nun son halinde kaç günlük dosya dursun (eskiler git geçmişinde kalır)
: "${MIN_BOS_ALAN_MB:=1024}"     # diskte bundan az yer varsa yedek alınmaz, MariaDB'nin diski dolmasın
: "${YEREL_REPO_MAX_MB:=300}"    # VPS'teki klon bunu geçerse geçmişsiz (shallow) yeniden klonlanır
: "${UZAK_REPO_UYARI_MB:=800}"   # GitHub'a gönderilen toplam boyut bunu geçince uyarı verilir
: "${EK_DOSYALAR:=}"             # DB dışında şifrelenip yedeklenecek dosyalar (örn. backend/.env)
: "${HC_URL:=}"                  # healthchecks.io ping adresi (boşsa bildirim yok)

LOG="$DURUM_DIR/son_calisma.log"
CALISMA=""

mkdir -p "$DURUM_DIR"
: > "$LOG"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

hc_ping() {
    [[ -n "$HC_URL" ]] || return 0
    curl -fsS -m 15 --retry 3 -o /dev/null --data-binary "@$LOG" "${HC_URL}$1" || true
}

hata() {
    log "HATA: $*"
    exit 1
}

# ── Aynı anda tek yedek ─────────────────────────────────────
exec 9> /run/lastik-yedek.lock
if ! flock -n 9; then
    log "Başka bir yedekleme sürüyor, bu çalışma atlandı."
    exit 0
fi

bitis() {
    local kod=$?
    [[ -n "$CALISMA" && -d "$CALISMA" ]] && rm -rf "$CALISMA"
    if (( kod == 2 )); then
        hc_ping /fail   # yedek alındı ama repo boyutu uyarısı var
    elif (( kod != 0 )); then
        log "===== YEDEKLEME BAŞARISIZ (çıkış kodu $kod) ====="
        hc_ping /fail
    fi
}
trap bitis EXIT
trap 'log "HATA: satır $LINENO: $BASH_COMMAND"' ERR

hc_ping /start
log "===== Yedekleme başladı: $DB_NAME ====="

# ── Ön kontroller ───────────────────────────────────────────
DUMP_BIN="$(command -v mariadb-dump || command -v mysqldump || true)"
SQL_BIN="$(command -v mariadb || command -v mysql || true)"
[[ -n "$DUMP_BIN" && -n "$SQL_BIN" ]] || hata "mariadb-dump / mariadb bulunamadı"
command -v age >/dev/null || hata "age kurulu değil (apt install age)"
[[ -r "$MYCNF" ]] || hata "$MYCNF okunamıyor"
[[ -s "$ALICILAR" ]] || hata "$ALICILAR boş ya da yok: şifreleme anahtarı (age public key) gerekli"

BOS_MB=$(df -Pm "$DURUM_DIR" | awk 'NR==2 {print $4}')
(( BOS_MB >= MIN_BOS_ALAN_MB )) || hata "Diskte sadece ${BOS_MB} MB boş yer var (en az ${MIN_BOS_ALAN_MB} MB gerekli)"

export GIT_SSH_COMMAND="ssh -i $SSH_ANAHTAR -o IdentitiesOnly=yes -o UserKnownHostsFile=$KNOWN_HOSTS -o StrictHostKeyChecking=accept-new -o BatchMode=yes"

# ── Yerel repo hazırlığı ────────────────────────────────────
gonderilmemis_commit_var() {
    git -C "$REPO_DIR" rev-parse --verify -q origin/main >/dev/null || return 0
    [[ -n "$(git -C "$REPO_DIR" rev-list origin/main..HEAD)" ]]
}

if [[ -d "$REPO_DIR/.git" ]]; then
    YEREL_MB=$(du -sm "$REPO_DIR/.git" | cut -f1)
    if (( YEREL_MB > YEREL_REPO_MAX_MB )) && ! gonderilmemis_commit_var; then
        log "Yerel klon ${YEREL_MB} MB, geçmişsiz olarak yeniden klonlanıyor (GitHub'daki geçmiş korunur)"
        rm -rf "$REPO_DIR"
    fi
fi

if [[ ! -d "$REPO_DIR/.git" ]]; then
    git clone --quiet --depth 1 --branch main "$REPO_URL" "$REPO_DIR" \
        || hata "Repo klonlanamadı: $REPO_URL (deploy key eklendi mi?)"
    git -C "$REPO_DIR" config user.name "Lastik VPS Yedek"
    git -C "$REPO_DIR" config user.email "yedek@$(hostname)"
fi

# ── Dump ────────────────────────────────────────────────────
mkdir -p "$DURUM_DIR/tmp"
CALISMA="$(mktemp -d "$DURUM_DIR/tmp/calisma.XXXXXX")"
ZAMAN="$(date +%Y%m%d-%H%M%S)"
HAM="$CALISMA/$DB_NAME.sql"

# --databases KULLANILMIYOR: dump içinde CREATE/DROP DATABASE olmaz,
# böylece yedek istenen isimde (örn. test) bir DB'ye yüklenebilir.
if ! "$DUMP_BIN" --defaults-file="$MYCNF" \
        --single-transaction --quick --skip-lock-tables \
        --routines --triggers --events \
        --no-tablespaces --hex-blob \
        --default-character-set=utf8mb4 \
        "$DB_NAME" > "$HAM" 2> "$CALISMA/dump.err"; then
    cat "$CALISMA/dump.err" | tee -a "$LOG" >&2
    hata "mariadb-dump başarısız"
fi

# ── Doğrulama: dump eksiksiz mi? ────────────────────────────
tail -n 1 "$HAM" | grep -q '^-- Dump completed' \
    || hata "Dump yarım kalmış (son satırda 'Dump completed' yok)"

# Routine sayısı mysql.proc'tan okunur: yetki eksikse information_schema.ROUTINES
# routine'leri gizler ve 0/0 "eşleşir"; mysql.proc ise hata verir.
SAYILAR="$("$SQL_BIN" --defaults-file="$MYCNF" -N -B -e "
    SELECT
      (SELECT COUNT(*) FROM information_schema.TABLES
         WHERE TABLE_SCHEMA = '$DB_NAME' AND TABLE_TYPE = 'BASE TABLE'),
      (SELECT COUNT(*) FROM mysql.proc WHERE db = '$DB_NAME'),
      (SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA = '$DB_NAME');" \
      2> "$CALISMA/sayim.err")" \
    || hata "Beklenen nesne sayıları okunamadı (yedek_user yetkisi eksik olabilir): $(grep ERROR "$CALISMA/sayim.err" | tail -n 1)"
read -r BEK_TABLO BEK_RUTIN BEK_TRIGGER <<< "$SAYILAR"
DUMP_TABLO=$(grep -c '^CREATE TABLE `' "$HAM" || true)
DUMP_RUTIN=$(grep -cE '^CREATE .*(PROCEDURE|FUNCTION) `' "$HAM" || true)
DUMP_TRIGGER=$(grep -cE '^/\*!50003 CREATE\*/ .*TRIGGER ' "$HAM" || true)

log "  tablo: $DUMP_TABLO/$BEK_TABLO  procedure+function: $DUMP_RUTIN/$BEK_RUTIN  trigger: $DUMP_TRIGGER/$BEK_TRIGGER"
(( BEK_TABLO > 0 )) || hata "Veritabanında hiç tablo görünmüyor (yetki sorunu ya da yanlış DB adı?)"
(( DUMP_TABLO >= BEK_TABLO ))     || hata "Dump'ta eksik tablo var"
(( DUMP_RUTIN >= BEK_RUTIN ))     || hata "Dump'ta eksik procedure/function var (yedek_user yetkilerini kontrol et)"
(( DUMP_TRIGGER >= BEK_TRIGGER )) || hata "Dump'ta eksik trigger var"

# ── Sıkıştır + şifrele ──────────────────────────────────────
HEDEF_DIR="$REPO_DIR/dumps/$(date +%Y/%m)"
HEDEF="$HEDEF_DIR/$DB_NAME-$ZAMAN.sql.gz.age"
while [[ -e "$HEDEF" ]]; do   # aynı saniyede ikinci elle yedek öncekini ezmesin
    sleep 1
    ZAMAN="$(date +%Y%m%d-%H%M%S)"
    HEDEF="$HEDEF_DIR/$DB_NAME-$ZAMAN.sql.gz.age"
done
mkdir -p "$HEDEF_DIR"

gzip -9 -c "$HAM" | age -R "$ALICILAR" -o "$HEDEF.part"
[[ -s "$HEDEF.part" ]] || hata "Şifreli dosya boş çıktı"
mv "$HEDEF.part" "$HEDEF"
log "  ✓ $(basename "$HEDEF") ($(du -h "$HEDEF" | cut -f1), ham $(du -h "$HAM" | cut -f1))"

# ── Ek dosyalar (.env vb.): sadece değiştiğinde eklenir ─────
for DOSYA in $EK_DOSYALAR; do
    if [[ ! -r "$DOSYA" ]]; then
        log "  ! ek dosya bulunamadı, atlandı: $DOSYA"
        continue
    fi
    AD="$(echo "${DOSYA#/}" | tr '/' '_')"
    OZET_DOSYASI="$DURUM_DIR/ozet_$AD"
    YENI_OZET="$(sha256sum "$DOSYA" | cut -d' ' -f1)"
    if [[ "$(cat "$OZET_DOSYASI" 2>/dev/null)" != "$YENI_OZET" || ! -f "$REPO_DIR/ek/$AD.age" ]]; then
        mkdir -p "$REPO_DIR/ek"
        age -R "$ALICILAR" -o "$REPO_DIR/ek/$AD.age" "$DOSYA"
        echo "$YENI_OZET" > "$OZET_DOSYASI"
        log "  ✓ ek dosya güncellendi: $DOSYA"
    fi
done

# ── Eski dosyaları repo'nun son halinden çıkar ──────────────
# (git geçmişinden silinmez; eski yedekler her zaman geri alınabilir)
# Yaş dosya adındaki tarihten okunur (yeniden klonlamada dosya tarihleri sıfırlanır).
SINIR="$(date -d "-$SAKLAMA_GUN days" +%Y%m%d)"
SILINEN=0
while IFS= read -r ESKI; do
    if [[ "$(basename "$ESKI")" =~ -([0-9]{8})-[0-9]{6}\.sql\.gz\.age$ ]] \
            && [[ "${BASH_REMATCH[1]}" < "$SINIR" ]]; then
        rm -f "$ESKI"
        SILINEN=$((SILINEN + 1))
    fi
done < <(find "$REPO_DIR/dumps" -type f -name '*.sql.gz.age')
find "$REPO_DIR/dumps" -mindepth 1 -type d -empty -delete
(( SILINEN == 0 )) || log "  $SILINEN dosya ${SAKLAMA_GUN} günden eski, son halden çıkarıldı (geçmişte duruyor)"

# ── Commit + push ───────────────────────────────────────────
cd "$REPO_DIR"
git add -A
git commit --quiet -m "yedek $ZAMAN"
if ! git push --quiet origin HEAD:main 2>> "$LOG"; then
    hata "Push başarısız. Commit yerelde duruyor, bir sonraki çalışmada tekrar gönderilecek."
fi

# GitHub'a gönderilen toplam boyutu takip et (repo yenileme zamanı için)
TOPLAM_KB_DOSYASI="$DURUM_DIR/gonderilen_toplam_kb"
TOPLAM_KB=$(( $(cat "$TOPLAM_KB_DOSYASI" 2>/dev/null || echo 0) + $(du -k "$HEDEF" | cut -f1) ))
echo "$TOPLAM_KB" > "$TOPLAM_KB_DOSYASI"
TOPLAM_MB=$(( TOPLAM_KB / 1024 ))
log "  ✓ Push OK. GitHub'a gönderilen toplam yaklaşık ${TOPLAM_MB} MB"

date '+%Y-%m-%d %H:%M:%S' > "$DURUM_DIR/son_basarili"
log "===== Tamamlandı ====="

if (( TOPLAM_MB >= UZAK_REPO_UYARI_MB )); then
    log "UYARI: GitHub repo'su ${UZAK_REPO_UYARI_MB} MB sınırını geçti. Yeni repo'ya geçme zamanı:"
    log "       docs/veritabani-yedekleme.md → 'Repo dolunca'"
    exit 2
fi

hc_ping ""
