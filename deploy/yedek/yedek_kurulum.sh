#!/bin/bash
# ============================================================
# Dijital Lastik Servisi — Yedekleme Kurulumu (VPS)
#
# Kullanım (repo klasöründen, root olarak):
#   sudo bash deploy/yedek/yedek_kurulum.sh
#
# Tekrar çalıştırılabilir: hazır olan adımlar atlanır.
# Ayrıntı: docs/veritabani-yedekleme.md
# ============================================================
set -euo pipefail
umask 077

RED='\033[0;31m'; GREEN='\033[0;32m'
YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✓ $1${NC}"; }
warn() { echo -e "${YELLOW}  ! $1${NC}"; }
step() { echo -e "\n${CYAN}══ $1 ══${NC}"; }
fail() { echo -e "${RED}  ✗ HATA: $1${NC}"; exit 1; }

DB_NAME="DijitalLastikServisiDB"
YEDEK_DB_USER="yedek_user"
AYAR_DIR="/etc/lastik-yedek"
DURUM_DIR="/var/lib/lastik-yedek"
BURADA="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

[ "$EUID" -eq 0 ] || fail "Root olarak çalıştır: sudo bash $0"

# ═══════════════════════════════════════════════════════════
step "1/7 — Paketler"
# ═══════════════════════════════════════════════════════════
export DEBIAN_FRONTEND=noninteractive
EKSIK=()
for p in age git curl; do command -v "$p" >/dev/null || EKSIK+=("$p"); done
command -v flock >/dev/null || EKSIK+=(util-linux)
if (( ${#EKSIK[@]} )); then
    apt-get update -qq
    apt-get install -y -qq "${EKSIK[@]}" || fail "Paketler kurulamadı: ${EKSIK[*]}"
fi
ok "age, git, curl, flock hazır"

install -d -m 700 "$AYAR_DIR" "$DURUM_DIR"

# ═══════════════════════════════════════════════════════════
step "2/7 — Sadece okuma yetkili DB kullanıcısı ($YEDEK_DB_USER)"
# ═══════════════════════════════════════════════════════════
if mariadb -e "SELECT 1;" &>/dev/null; then
    ROOT_SQL=(mariadb)
else
    echo -n "  MariaDB root parolası: "
    read -rs ROOT_PAROLA; echo ""
    ROOT_SQL=(mariadb -uroot "-p$ROOT_PAROLA")
    "${ROOT_SQL[@]}" -e "SELECT 1;" &>/dev/null || fail "MariaDB root bağlantısı başarısız"
fi
"${ROOT_SQL[@]}" -e "USE \`$DB_NAME\`;" || fail "Veritabanı $DB_NAME bulunamadı"

if [[ -f "$AYAR_DIR/my.cnf" ]]; then
    ok "$AYAR_DIR/my.cnf zaten var, kullanıcı yeniden oluşturulmadı"
else
    YEDEK_PAROLA="$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 32)"
    "${ROOT_SQL[@]}" <<SQL
CREATE USER IF NOT EXISTS '$YEDEK_DB_USER'@'localhost' IDENTIFIED BY '$YEDEK_PAROLA';
ALTER USER '$YEDEK_DB_USER'@'localhost' IDENTIFIED BY '$YEDEK_PAROLA';
GRANT SELECT, SHOW VIEW, TRIGGER, EVENT, LOCK TABLES ON \`$DB_NAME\`.* TO '$YEDEK_DB_USER'@'localhost';
SQL
    # Procedure/function gövdelerini okuyabilmesi için (sürüme göre biri geçerli)
    "${ROOT_SQL[@]}" -e "GRANT SELECT ON mysql.proc TO '$YEDEK_DB_USER'@'localhost';" 2>/dev/null || true
    "${ROOT_SQL[@]}" -e "GRANT SHOW CREATE ROUTINE ON \`$DB_NAME\`.* TO '$YEDEK_DB_USER'@'localhost';" 2>/dev/null || true
    "${ROOT_SQL[@]}" -e "FLUSH PRIVILEGES;"

    cat > "$AYAR_DIR/my.cnf" <<EOF
[client]
user=$YEDEK_DB_USER
password=$YEDEK_PAROLA
EOF
    chmod 600 "$AYAR_DIR/my.cnf"
    ok "$YEDEK_DB_USER oluşturuldu, parola $AYAR_DIR/my.cnf içinde (sadece root okuyabilir)"
fi
mariadb --defaults-file="$AYAR_DIR/my.cnf" -e "USE \`$DB_NAME\`; SELECT 1;" >/dev/null \
    || fail "$YEDEK_DB_USER ile bağlanılamadı"

# ═══════════════════════════════════════════════════════════
step "3/7 — Şifreleme anahtarı (age public key)"
# ═══════════════════════════════════════════════════════════
if [[ -s "$AYAR_DIR/alicilar.txt" ]]; then
    ok "Kayıtlı anahtar(lar):"
    sed 's/^/      /' "$AYAR_DIR/alicilar.txt"
else
    echo "  Kendi bilgisayarında üret:  age-keygen -o lastik-yedek-anahtar.txt"
    echo "  Çıktıdaki 'Public key: age1...' satırındaki age1... değerini buraya yapıştır."
    echo "  (Birden fazla anahtar eklenebilir, bitirmek için boş satır gir.)"
    : > "$AYAR_DIR/alicilar.txt.yeni"
    while true; do
        echo -n "  age public key: "
        read -r ANAHTAR
        [[ -z "$ANAHTAR" ]] && break
        if [[ "$ANAHTAR" =~ ^age1[a-z0-9]{58}$ ]]; then
            echo "$ANAHTAR" >> "$AYAR_DIR/alicilar.txt.yeni"
            ok "eklendi"
        else
            warn "Geçersiz. 'age1' ile başlayan public key olmalı (AGE-SECRET-KEY DEĞİL!)"
        fi
    done
    [[ -s "$AYAR_DIR/alicilar.txt.yeni" ]] || fail "En az bir anahtar gerekli"
    mv "$AYAR_DIR/alicilar.txt.yeni" "$AYAR_DIR/alicilar.txt"
    ok "Anahtar kaydedildi"
fi

# ═══════════════════════════════════════════════════════════
step "4/7 — GitHub deploy key ve repo"
# ═══════════════════════════════════════════════════════════
KEY="$AYAR_DIR/github_key"
if [[ ! -f "$KEY" ]]; then
    ssh-keygen -q -t ed25519 -N "" -C "lastik-yedek@$(hostname)" -f "$KEY"
    ok "Deploy key oluşturuldu"
fi

MEVCUT_URL=""
[[ -f "$AYAR_DIR/yedek.conf" ]] && MEVCUT_URL="$(sed -n 's/^REPO_URL="\(.*\)"$/\1/p' "$AYAR_DIR/yedek.conf")"
if [[ -n "$MEVCUT_URL" ]]; then
    REPO_URL="$MEVCUT_URL"
    ok "Repo: $REPO_URL"
else
    echo ""
    echo "  1) GitHub'da PRIVATE bir repo aç (örn. lastik-db-yedek), içi BOŞ olsun (README ekleme)."
    echo "  2) Repo → Settings → Deploy keys → Add deploy key"
    echo "     Title: VPS yedek    'Allow write access' İŞARETLİ"
    echo "     Key:"
    echo ""
    echo -e "     ${YELLOW}$(cat "$KEY.pub")${NC}"
    echo ""
    echo "  NOT: Bu key'i hesabın 'SSH and GPG keys' kısmına EKLEME, sadece bu repoya."
    echo ""
    echo -n "  Repo SSH adresi (git@github.com:KULLANICI/REPO.git): "
    read -r REPO_URL
    [[ "$REPO_URL" =~ ^git@github\.com:[A-Za-z0-9._-]+/[A-Za-z0-9._-]+\.git$ ]] \
        || fail "Adres git@github.com:KULLANICI/REPO.git biçiminde olmalı"
fi

export GIT_SSH_COMMAND="ssh -i $KEY -o IdentitiesOnly=yes -o UserKnownHostsFile=$AYAR_DIR/known_hosts -o StrictHostKeyChecking=accept-new -o BatchMode=yes"
until git ls-remote "$REPO_URL" &>/dev/null; do
    warn "Repo'ya erişilemedi. Deploy key eklendi mi, 'Allow write access' işaretli mi?"
    echo -n "  Ekledikten sonra Enter'a bas (vazgeçmek için Ctrl+C) "
    read -r _
done
ok "GitHub erişimi tamam"

if [[ -z "$(git ls-remote --heads "$REPO_URL" main)" ]]; then
    ILK="$(mktemp -d)"
    git -C "$ILK" init -q -b main
    cat > "$ILK/README.md" <<'EOF'
# Dijital Lastik Servisi — Veritabanı Yedekleri

Bu repo VPS tarafından otomatik doldurulur. Elle push YAPMA.

- `dumps/YYYY/MM/*.sql.gz.age` — MariaDB yedekleri (age ile şifreli)
- `ek/*.age` — .env gibi yardımcı dosyalar (şifreli)

Şifre çözme ve geri yükleme: ana projede `docs/veritabani-yedekleme.md`
EOF
    git -C "$ILK" add README.md
    git -C "$ILK" -c user.name="Lastik VPS Yedek" -c user.email="yedek@$(hostname)" commit -q -m "ilk commit"
    git -C "$ILK" push -q "$REPO_URL" main || fail "İlk push başarısız (deploy key'de 'Allow write access' işaretli mi?)"
    rm -rf "$ILK"
    ok "Repo hazırlandı (main dalı)"
fi

# ═══════════════════════════════════════════════════════════
step "5/7 — Ayar dosyası"
# ═══════════════════════════════════════════════════════════
if [[ -f "$AYAR_DIR/yedek.conf" ]]; then
    ok "$AYAR_DIR/yedek.conf zaten var, korunuyor"
else
    EK=""
    for f in /opt/repo/backend/.env /opt/management-tire/backend/.env; do
        [[ -f "$f" ]] && EK="$f" && break
    done
    echo "  Bildirim için healthchecks.io'da bir check oluştur (Period: 3 saat, Grace: 1 saat)"
    echo "  ve ping adresini yapıştır. Şimdilik istemiyorsan boş bırak."
    echo -n "  Ping URL (https://hc-ping.com/...): "
    read -r HC_URL
    cat > "$AYAR_DIR/yedek.conf" <<EOF
# Dijital Lastik Servisi — yedek ayarları (lastik-yedekle okur)
REPO_URL="$REPO_URL"
DB_NAME="$DB_NAME"
HC_URL="$HC_URL"
# Şifreli olarak yedeklenecek ek dosyalar (boşlukla ayır)
EK_DOSYALAR="$EK"
# Repo'nun son halinde tutulacak gün (daha eskiler git geçmişinde durur)
SAKLAMA_GUN=30
EOF
    chmod 600 "$AYAR_DIR/yedek.conf"
    ok "Ayarlar yazıldı"
fi

# ═══════════════════════════════════════════════════════════
step "6/7 — Script ve zamanlayıcı"
# ═══════════════════════════════════════════════════════════
install -m 755 "$BURADA/yedekle.sh" /usr/local/sbin/lastik-yedekle
install -m 755 "$BURADA/geri_yukle.sh" /usr/local/sbin/lastik-geri-yukle
install -m 644 "$BURADA/lastik-yedek.service" /etc/systemd/system/lastik-yedek.service
install -m 644 "$BURADA/lastik-yedek.timer" /etc/systemd/system/lastik-yedek.timer
systemctl daemon-reload
systemctl enable --now lastik-yedek.timer >/dev/null
ok "lastik-yedek.timer aktif (3 saatte bir)"

# ═══════════════════════════════════════════════════════════
step "7/7 — İlk yedek (şimdi)"
# ═══════════════════════════════════════════════════════════
if systemctl start lastik-yedek.service; then
    cat "$DURUM_DIR/son_calisma.log"
    ok "İlk yedek alındı ve GitHub'a gönderildi"
else
    cat "$DURUM_DIR/son_calisma.log" 2>/dev/null || true
    fail "İlk yedek başarısız. Log: journalctl -u lastik-yedek -n 50"
fi

echo ""
echo -e "${GREEN}  Kurulum tamam.${NC}"
echo "  Sonraki yedek:  systemctl list-timers lastik-yedek.timer"
echo "  Elle yedek:     sudo lastik-yedekle"
echo "  Log:            journalctl -u lastik-yedek -n 50"
echo ""
echo -e "${YELLOW}  UNUTMA: age PRIVATE key'in (AGE-SECRET-KEY-...) olmadan yedekler AÇILAMAZ.${NC}"
echo -e "${YELLOW}  En az iki yerde sakla (şifre yöneticisi + USB/kağıt). VPS'e KOYMA.${NC}"
