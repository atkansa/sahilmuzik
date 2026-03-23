import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(BASE_DIR, 'music')
DB_PATH = os.path.join(BASE_DIR, 'sahilmuzik.db')

# İzin verilen müzik dosyası uzantıları
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac', 'm4a', 'aac', 'wma'}

# Flask ayarları
HOST = '0.0.0.0'
PORT = 5000
DEBUG = False

# Maksimum dosya boyutu (100 MB)
MAX_CONTENT_LENGTH = 100 * 1024 * 1024

# Zamanlayıcı kontrol aralığı (saniye)
SCHEDULER_INTERVAL = 15

# mpv socket yolu
MPV_SOCKET = '/tmp/sahilmuzik_mpv.sock'

# Ses çıkışı (alsa analog)
AUDIO_OUTPUT = 'alsa'
AUDIO_DEVICE = 'default'
