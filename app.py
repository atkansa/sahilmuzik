import os
import uuid
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from config import MUSIC_DIR, HOST, PORT, DEBUG, ALLOWED_EXTENSIONS, MAX_CONTENT_LENGTH
from database import (
    init_db, get_all_songs, add_song, delete_song, reorder_songs,
    get_all_schedules, add_schedule, update_schedule, delete_schedule, toggle_schedule,
    get_settings, update_setting
)
from player import player
from scheduler import scheduler

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('sahilmuzik')

# Flask uygulaması
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Music klasörünü oluştur
os.makedirs(MUSIC_DIR, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_audio_duration(filepath):
    """Ses dosyasının süresini saniye olarak döndürür."""
    try:
        from mutagen import File as MutagenFile
        audio = MutagenFile(filepath)
        if audio and audio.info:
            return round(audio.info.length, 1)
    except Exception as e:
        logger.warning(f"Süre okunamadı: {e}")
    return 0


# ─── Pages ──────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ─── Songs API ──────────────────────────────────────────

@app.route('/api/songs', methods=['GET'])
def api_get_songs():
    songs = get_all_songs()
    return jsonify(songs)


@app.route('/api/songs/upload', methods=['POST'])
def api_upload_song():
    if 'file' not in request.files:
        return jsonify({'error': 'Dosya bulunamadı'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Desteklenmeyen dosya formatı'}), 400

    original_name = file.filename
    ext = original_name.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(MUSIC_DIR, filename)

    file.save(filepath)
    duration = get_audio_duration(filepath)
    song = add_song(filename, original_name, duration)

    logger.info(f"Şarkı yüklendi: {original_name}")
    return jsonify(song), 201


@app.route('/api/songs/<int:song_id>', methods=['DELETE'])
def api_delete_song(song_id):
    song = delete_song(song_id)
    if not song:
        return jsonify({'error': 'Şarkı bulunamadı'}), 404

    # Dosyayı sil
    filepath = os.path.join(MUSIC_DIR, song['filename'])
    try:
        os.remove(filepath)
    except OSError:
        pass

    logger.info(f"Şarkı silindi: {song['original_name']}")
    return jsonify({'success': True})


@app.route('/api/songs/reorder', methods=['POST'])
def api_reorder_songs():
    data = request.get_json()
    if not data or 'order' not in data:
        return jsonify({'error': 'Sıralama verisi gerekli'}), 400

    reorder_songs(data['order'])
    return jsonify({'success': True})


# ─── Schedule API ───────────────────────────────────────

@app.route('/api/schedule', methods=['GET'])
def api_get_schedules():
    schedules = get_all_schedules()
    return jsonify(schedules)


@app.route('/api/schedule', methods=['POST'])
def api_add_schedule():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Veri gerekli'}), 400

    required = ['day_of_week', 'start_time', 'end_time']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} gerekli'}), 400

    schedule = add_schedule(
        int(data['day_of_week']),
        data['start_time'],
        data['end_time'],
        data.get('is_active', 1)
    )
    logger.info(f"Zamanlama eklendi: Gün {data['day_of_week']}, {data['start_time']}-{data['end_time']}")
    return jsonify(schedule), 201


@app.route('/api/schedule/<int:schedule_id>', methods=['PUT'])
def api_update_schedule(schedule_id):
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Veri gerekli'}), 400

    schedule = update_schedule(
        schedule_id,
        day_of_week=data.get('day_of_week'),
        start_time=data.get('start_time'),
        end_time=data.get('end_time'),
        is_active=data.get('is_active')
    )
    if not schedule:
        return jsonify({'error': 'Zamanlama bulunamadı'}), 404

    return jsonify(schedule)


@app.route('/api/schedule/<int:schedule_id>', methods=['DELETE'])
def api_delete_schedule(schedule_id):
    schedule = delete_schedule(schedule_id)
    if not schedule:
        return jsonify({'error': 'Zamanlama bulunamadı'}), 404

    return jsonify({'success': True})


@app.route('/api/schedule/<int:schedule_id>/toggle', methods=['POST'])
def api_toggle_schedule(schedule_id):
    schedule = toggle_schedule(schedule_id)
    if not schedule:
        return jsonify({'error': 'Zamanlama bulunamadı'}), 404

    return jsonify(schedule)


# ─── Player API ─────────────────────────────────────────

@app.route('/api/player/status', methods=['GET'])
def api_player_status():
    status = player.get_status()
    status['schedule_active'] = scheduler.is_within_schedule()
    return jsonify(status)


@app.route('/api/player/play', methods=['POST'])
def api_player_play():
    data = request.get_json() or {}
    index = data.get('index', 0)
    success = player.play(index)
    return jsonify({'success': success})


@app.route('/api/player/pause', methods=['POST'])
def api_player_pause():
    success = player.pause()
    return jsonify({'success': success})


@app.route('/api/player/stop', methods=['POST'])
def api_player_stop():
    player.stop()
    return jsonify({'success': True})


@app.route('/api/player/next', methods=['POST'])
def api_player_next():
    success = player.next_song()
    return jsonify({'success': success})


@app.route('/api/player/prev', methods=['POST'])
def api_player_prev():
    success = player.prev_song()
    return jsonify({'success': success})


@app.route('/api/player/volume', methods=['POST'])
def api_player_volume():
    data = request.get_json()
    if not data or 'volume' not in data:
        return jsonify({'error': 'volume gerekli'}), 400

    volume = player.set_volume(data['volume'])
    return jsonify({'volume': volume})


# ─── Settings API ───────────────────────────────────────

@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    return jsonify(get_settings())


@app.route('/api/settings', methods=['POST'])
def api_update_settings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Veri gerekli'}), 400

    for key, value in data.items():
        update_setting(key, str(value))

    return jsonify(get_settings())


# ─── Başlatma ───────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    scheduler.start()
    logger.info(f"Sahil Müzik Sistemi başlatıldı - http://{HOST}:{PORT}")
    try:
        app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
    finally:
        scheduler.stop()
        player.stop()
