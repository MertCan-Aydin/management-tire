#!/bin/bash
# ============================================================
# Dijital Lastik Servisi — Yedekten Geri Yükleme
#
# Kullanım (root):
#   lastik-geri-yukle <yedek> [hedef_db] [-i age_anahtar.txt]
#
#   <yedek>    .sql.gz.age (şifreli, -i gerekir) | .sql.gz | .sql
#   [hedef_db] varsayılan: DijitalLastikServisiDB_geri  (test kopyası, canlıya dokunmaz)
#              Canlıya yüklemek için açıkça DijitalLastikServisiDB yazılmalı.
#
# Örnekler:
#   lastik-geri-yukle DijitalLastikServisiDB-20261008-150000.sql.gz.age -i /root/anahtar.txt
#   lastik-geri-yukle DijitalLastikServisiDB-20261008-150000.sql.gz DijitalLastikServisiDB
#
# Ayrıntı: docs/veritabani-yedekleme.md
# ============================================================
set -euo pipefail
umask 077

CANLI_DB="DijitalLastikServisiDB"
SERVIS="management-tire-api"
DURUM_DIR="/var/lib/lastik-yedek"

kullanim() { sed -n '4,15p' "$0" | sed 's/^# \{0,1\}//'; exit 1; }
fail() { echo "  ✗ HATA: $*" >&2; exit 1; }

YEDEK=""; HEDEF=""; ANAHTAR=""
while (( $# )); do
    case "$1" in
        -i) ANAHTAR="${2:-}"; shift 2 ;;
        -h|--help) kullanim ;;
        *) if [[ -z "$YEDEK" ]]; then YEDEK="$1"; elif [[ -z "$HEDEF" ]]; then HEDEF="$1"; else kullanim; fi; shift ;;
    esac
done
[[ -n "$YEDEK" ]] || kullanim
[[ -r "$YEDEK" ]] || fail "Dosya okunamıyor: $YEDEK"
HEDEF="${HEDEF:-${CANLI_DB}_geri}"
[[ "$HEDEF" =~ ^[A-Za-z0-9_]+$ ]] || fail "Geçersiz DB adı: $HEDEF"
[ "$EUID" -eq 0 ] || fail "Root olarak çalıştır"

SQL=(mariadb)
DUMP=(mariadb-dump)
if ! "${SQL[@]}" -e "SELECT 1;" &>/dev/null; then
    echo -n "  MariaDB root parolası: "; read -rs P; echo ""
    SQL=(mariadb -uroot "-p$P"); DUMP=(mariadb-dump -uroot "-p$P")
    "${SQL[@]}" -e "SELECT 1;" &>/dev/null || fail "MariaDB bağlantısı başarısız"
fi

# Yedeği düz SQL akışı olarak oku
ac() {
    case "$YEDEK" in
        *.age)
            [[ -r "$ANAHTAR" ]] || fail "Şifreli yedek için -i <age private key dosyası> gerekli"
            age -d -i "$ANAHTAR" "$YEDEK" | gunzip -c ;;
        *.gz)  gunzip -c "$YEDEK" ;;
        *.sql) cat "$YEDEK" ;;
        *)     fail "Tanınmayan uzantı: $YEDEK" ;;
    esac
}

# Önce dosyanın sağlam olduğunu kontrol et (canlı DB silinmeden önce!)
echo "  Yedek kontrol ediliyor..."
SON_SATIR="$(ac | tail -n 1)"
[[ "$SON_SATIR" == "-- Dump completed"* ]] || fail "Yedek dosyası bozuk ya da yarım (ya da anahtar yanlış)"
echo "  ✓ Yedek sağlam"

SERVIS_DURDU=0
if [[ "$HEDEF" == "$CANLI_DB" ]]; then
    echo ""
    echo "  ⚠️  CANLI veritabanı ($CANLI_DB) SİLİNİP bu yedekle değiştirilecek."
    echo "     Yedekten sonra girilen tüm satış/alım kayıtları kaybolur."
    echo -n "  Devam etmek için büyük harflerle EVET yaz: "
    read -r ONAY
    [[ "$ONAY" == "EVET" ]] || fail "Vazgeçildi"

    if "${SQL[@]}" -e "USE \`$CANLI_DB\`;" &>/dev/null; then
        mkdir -p "$DURUM_DIR"
        ONCEKI="$DURUM_DIR/geri_yukleme_oncesi-$(date +%Y%m%d-%H%M%S).sql.gz"
        echo "  Mevcut hali güvenlik için kaydediliyor: $ONCEKI"
        "${DUMP[@]}" --single-transaction --routines --triggers --events "$CANLI_DB" | gzip > "$ONCEKI"
    fi

    if systemctl is-active --quiet "$SERVIS" 2>/dev/null; then
        systemctl stop "$SERVIS"
        SERVIS_DURDU=1
        echo "  API durduruldu ($SERVIS)"
    fi
elif "${SQL[@]}" -e "USE \`$HEDEF\`;" &>/dev/null; then
    echo -n "  '$HEDEF' zaten var, silinip yeniden oluşturulacak. Devam? (e/h): "
    read -r ONAY
    [[ "$ONAY" == "e" ]] || fail "Vazgeçildi"
fi

servisi_geri_ac() {
    if (( SERVIS_DURDU )); then
        systemctl start "$SERVIS" && echo "  API yeniden başlatıldı ($SERVIS)"
    fi
}
trap servisi_geri_ac EXIT

echo "  '$HEDEF' yükleniyor..."
"${SQL[@]}" -e "DROP DATABASE IF EXISTS \`$HEDEF\`;
                CREATE DATABASE \`$HEDEF\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
ac | "${SQL[@]}" "$HEDEF"

"${SQL[@]}" -N -B -e "
    SELECT CONCAT('  ✓ Yüklendi: ',
      (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='$HEDEF' AND TABLE_TYPE='BASE TABLE'), ' tablo, ',
      (SELECT COUNT(*) FROM information_schema.ROUTINES WHERE ROUTINE_SCHEMA='$HEDEF'), ' procedure/function, ',
      (SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA='$HEDEF'), ' trigger');"
"${SQL[@]}" -N -B "$HEDEF" -e "
    SELECT CONCAT('  Müşteri: ', (SELECT COUNT(*) FROM musteriler),
                  '  Satış: ', (SELECT COUNT(*) FROM satislar),
                  '  Son satış tarihi: ', IFNULL((SELECT MAX(tarih) FROM satislar), '-'));" 2>/dev/null || true

if [[ "$HEDEF" != "$CANLI_DB" ]]; then
    echo ""
    echo "  Test kopyası hazır. İnceledikten sonra silmek için:"
    echo "    mariadb -e 'DROP DATABASE \`$HEDEF\`;'"
fi
