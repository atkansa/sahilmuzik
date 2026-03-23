import sqlite3
import os
from config import DB_PATH

def get_db():
    """Veritabanı bağlantısı döndürür."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    """Veritabanı tablolarını oluşturur."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            original_name TEXT NOT NULL,
            duration REAL DEFAULT 0,
            position INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Varsayılan ayarlar
    defaults = {
        'volume': '80',
        'repeat_mode': 'all',
        'shuffle': '0',
    }
    for key, value in defaults.items():
        cursor.execute(
            'INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)',
            (key, value)
        )

    conn.commit()
    conn.close()

# ─── Songs CRUD ─────────────────────────────────────────

def get_all_songs():
    conn = get_db()
    songs = conn.execute('SELECT * FROM songs ORDER BY position ASC, id ASC').fetchall()
    conn.close()
    return [dict(s) for s in songs]

def add_song(filename, original_name, duration=0):
    conn = get_db()
    # Sıradaki pozisyon
    max_pos = conn.execute('SELECT COALESCE(MAX(position), 0) FROM songs').fetchone()[0]
    conn.execute(
        'INSERT INTO songs (filename, original_name, duration, position) VALUES (?, ?, ?, ?)',
        (filename, original_name, duration, max_pos + 1)
    )
    conn.commit()
    song_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    song = conn.execute('SELECT * FROM songs WHERE id = ?', (song_id,)).fetchone()
    conn.close()
    return dict(song)

def delete_song(song_id):
    conn = get_db()
    song = conn.execute('SELECT * FROM songs WHERE id = ?', (song_id,)).fetchone()
    if song:
        conn.execute('DELETE FROM songs WHERE id = ?', (song_id,))
        conn.commit()
        conn.close()
        return dict(song)
    conn.close()
    return None

def reorder_songs(song_ids):
    """song_ids listesindeki sıraya göre pozisyonları günceller."""
    conn = get_db()
    for idx, song_id in enumerate(song_ids):
        conn.execute('UPDATE songs SET position = ? WHERE id = ?', (idx + 1, song_id))
    conn.commit()
    conn.close()

# ─── Schedule CRUD ──────────────────────────────────────

def get_all_schedules():
    conn = get_db()
    schedules = conn.execute('SELECT * FROM schedule ORDER BY day_of_week, start_time').fetchall()
    conn.close()
    return [dict(s) for s in schedules]

def add_schedule(day_of_week, start_time, end_time, is_active=1):
    conn = get_db()
    conn.execute(
        'INSERT INTO schedule (day_of_week, start_time, end_time, is_active) VALUES (?, ?, ?, ?)',
        (day_of_week, start_time, end_time, is_active)
    )
    conn.commit()
    schedule_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    schedule = conn.execute('SELECT * FROM schedule WHERE id = ?', (schedule_id,)).fetchone()
    conn.close()
    return dict(schedule)

def update_schedule(schedule_id, day_of_week=None, start_time=None, end_time=None, is_active=None):
    conn = get_db()
    current = conn.execute('SELECT * FROM schedule WHERE id = ?', (schedule_id,)).fetchone()
    if not current:
        conn.close()
        return None

    updates = {
        'day_of_week': day_of_week if day_of_week is not None else current['day_of_week'],
        'start_time': start_time if start_time is not None else current['start_time'],
        'end_time': end_time if end_time is not None else current['end_time'],
        'is_active': is_active if is_active is not None else current['is_active'],
    }

    conn.execute(
        'UPDATE schedule SET day_of_week=?, start_time=?, end_time=?, is_active=? WHERE id=?',
        (updates['day_of_week'], updates['start_time'], updates['end_time'], updates['is_active'], schedule_id)
    )
    conn.commit()
    schedule = conn.execute('SELECT * FROM schedule WHERE id = ?', (schedule_id,)).fetchone()
    conn.close()
    return dict(schedule)

def delete_schedule(schedule_id):
    conn = get_db()
    schedule = conn.execute('SELECT * FROM schedule WHERE id = ?', (schedule_id,)).fetchone()
    if schedule:
        conn.execute('DELETE FROM schedule WHERE id = ?', (schedule_id,))
        conn.commit()
        conn.close()
        return dict(schedule)
    conn.close()
    return None

def toggle_schedule(schedule_id):
    conn = get_db()
    schedule = conn.execute('SELECT * FROM schedule WHERE id = ?', (schedule_id,)).fetchone()
    if schedule:
        new_val = 0 if schedule['is_active'] else 1
        conn.execute('UPDATE schedule SET is_active = ? WHERE id = ?', (new_val, schedule_id))
        conn.commit()
        updated = conn.execute('SELECT * FROM schedule WHERE id = ?', (schedule_id,)).fetchone()
        conn.close()
        return dict(updated)
    conn.close()
    return None

# ─── Settings ───────────────────────────────────────────

def get_settings():
    conn = get_db()
    rows = conn.execute('SELECT * FROM settings').fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}

def update_setting(key, value):
    conn = get_db()
    conn.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()
