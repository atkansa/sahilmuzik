#!/bin/bash
# ═══════════════════════════════════════════════════
# Sahil Müzik Sistemi - Raspberry Pi Kurulum Scripti
# ═══════════════════════════════════════════════════

set -e

echo "╔══════════════════════════════════════╗"
echo "║   🏖️  Sahil Müzik Sistemi Kurulumu   ║"
echo "╚══════════════════════════════════════╝"
echo ""

# Renk kodları
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Mevcut kullanıcıyı al
CURRENT_USER=$(whoami)
INSTALL_DIR=$(pwd)

echo -e "${YELLOW}[1/6]${NC} Sistem paketleri güncelleniyor..."
sudo apt update -qq

echo -e "${YELLOW}[2/6]${NC} Gerekli paketler yükleniyor..."
sudo apt install -y mpv python3-pip python3-venv

echo -e "${YELLOW}[3/6]${NC} Python sanal ortam oluşturuluyor..."
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[4/6]${NC} Python bağımlılıkları yükleniyor..."
pip install -r requirements.txt

echo -e "${YELLOW}[5/6]${NC} Müzik klasörü oluşturuluyor..."
mkdir -p music

echo -e "${YELLOW}[6/6]${NC} Systemd servisi kuruluyor..."

# Service dosyasını güncelle (kullanıcı ve dizin)
sudo bash -c "cat > /etc/systemd/system/sahilmuzik.service << EOF
[Unit]
Description=Sahil Müzik Sistemi
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=${CURRENT_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python3 ${INSTALL_DIR}/app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF"

# Analog ses çıkışını zorla (3.5mm jack)
echo -e "${YELLOW}[*]${NC} Analog ses çıkışı ayarlanıyor..."
sudo amixer cset numid=3 1 2>/dev/null || true

# Servisi etkinleştir ve başlat
sudo systemctl daemon-reload
sudo systemctl enable sahilmuzik
sudo systemctl start sahilmuzik

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ Kurulum tamamlandı!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
echo ""

# IP adresini göster
IP_ADDR=$(hostname -I | awk '{print $1}')
echo -e "   🌐 Web Arayüzü: ${GREEN}http://${IP_ADDR}:5000${NC}"
echo ""
echo -e "   📋 Faydalı komutlar:"
echo -e "      Durumu gör:    ${YELLOW}sudo systemctl status sahilmuzik${NC}"
echo -e "      Logları gör:   ${YELLOW}sudo journalctl -u sahilmuzik -f${NC}"
echo -e "      Yeniden başlat:${YELLOW}sudo systemctl restart sahilmuzik${NC}"
echo -e "      Durdur:        ${YELLOW}sudo systemctl stop sahilmuzik${NC}"
echo ""
