# 🏖️ Sahil Müzik Sistemi

Raspberry Pi 4B üzerinde çalışan, web tabanlı sahil ses sistemi yönetim ve zamanlama uygulaması.

## ✨ Özellikler

- **Web Arayüzü**: Herhangi bir cihazdan tarayıcı ile müzik yönetimi
- **Müzik Yükleme**: Drag & drop ile müzik dosyası yükleme (MP3, WAV, OGG, FLAC, M4A)
- **Zamanlama**: Gün ve saat bazında müzik çalma zamanlaması
- **Otomatik Başlatma**: Elektrik kesintisi sonrası saate göre otomatik çalma
- **Uzaktan Kontrol**: Çal, duraklat, sonraki, önceki, ses seviyesi
- **Karıştırma & Tekrar**: Playlist karıştırma ve tekrar modları

## 🔧 Gereksinimler

- Raspberry Pi 4B (veya 3B+)
- Raspberry Pi OS (Bullseye veya üstü)
- 3.5mm jack kablo ile ses sistemi bağlantısı
- İnternet bağlantısı (kurulum için)

## 🚀 Kurulum

### 1. Dosyaları Raspberry Pi'ye Kopyalayın

```bash
# USB ile veya SCP ile
scp -r sahilmuzik/ pi@<RaspberryPi-IP>:/home/pi/
```

### 2. Kurulum Scriptini Çalıştırın

```bash
cd /home/pi/sahilmuzik
chmod +x install.sh
./install.sh
```

Kurulum tamamlandığında ekranda web arayüzü adresi gösterilecektir.

### 3. Web Arayüzüne Erişin

Tarayıcınızdan açın:
```
http://<RaspberryPi-IP>:5000
```

## 📖 Kullanım

### Müzik Ekleme
1. **Kütüphane** sekmesine gidin
2. Müzik dosyalarını sürükleyip bırakın veya tıklayarak seçin
3. Dosyalar otomatik yüklenecektir

### Zamanlama Ayarlama
1. **Zamanlama** sekmesine gidin
2. **"Yeni Ekle"** butonuna tıklayın
3. Gün, başlangıç ve bitiş saatlerini seçin
4. Kaydedin

### Çalma Kontrolleri
- **Çalıcı** sekmesinden çal/duraklat/durdur/sonraki/önceki
- Ses seviyesini slider ile ayarlayın

## ⚡ Elektrik Kesintisi

Cihaz yeniden başladığında:
1. Sistem otomatik olarak başlar (systemd)
2. Mevcut saati kontrol eder
3. Zamanlamaya uygunsa müzik çalmaya başlar
4. Zamanlama dışındaysa bekler

## 🛠️ Faydalı Komutlar

```bash
# Servis durumu
sudo systemctl status sahilmuzik

# Logları izle
sudo journalctl -u sahilmuzik -f

# Yeniden başlat
sudo systemctl restart sahilmuzik

# Durdur
sudo systemctl stop sahilmuzik
```

## 📁 Dosya Yapısı

```
sahilmuzik/
├── app.py              # Ana uygulama
├── config.py           # Konfigürasyon
├── database.py         # Veritabanı işlemleri
├── player.py           # Müzik çalma motoru
├── scheduler.py        # Zamanlama motoru
├── install.sh          # Kurulum scripti
├── requirements.txt    # Python bağımlılıkları
├── music/              # Müzik dosyaları
├── static/
│   ├── css/style.css   # Stiller
│   └── js/app.js       # Frontend mantığı
└── templates/
    └── index.html      # Ana sayfa
```
