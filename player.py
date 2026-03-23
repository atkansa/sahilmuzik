import subprocess
import json
import os
import threading
import time
import logging
from config import MUSIC_DIR, MPV_SOCKET, AUDIO_OUTPUT, AUDIO_DEVICE
from database import get_all_songs, get_settings, update_setting

logger = logging.getLogger('sahilmuzik.player')


class MusicPlayer:
    """mpv tabanlı müzik çalıcı."""

    def __init__(self):
        self.process = None
        self.current_song = None
        self.current_index = -1
        self.is_playing = False
        self.is_paused = False
        self.playlist = []
        self._lock = threading.Lock()
        self._monitor_thread = None
        self._stop_monitor = False

    def _send_command(self, command):
        """mpv IPC socket üzerinden komut gönderir."""
        try:
            import socket
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(2)
            sock.connect(MPV_SOCKET)
            cmd = json.dumps({"command": command}) + "\n"
            sock.sendall(cmd.encode())
            response = sock.recv(4096).decode()
            sock.close()
            return json.loads(response)
        except Exception as e:
            logger.debug(f"IPC komut hatası: {e}")
            return None

    def _get_property(self, prop):
        """mpv'den bir özellik değeri alır."""
        result = self._send_command(["get_property", prop])
        if result and 'data' in result:
            return result['data']
        return None

    def _build_playlist(self):
        """Veritabanından playlist oluşturur."""
        songs = get_all_songs()
        settings = get_settings()
        shuffle = settings.get('shuffle', '0') == '1'

        self.playlist = songs
        if shuffle:
            import random
            random.shuffle(self.playlist)

    def _start_mpv(self, start_index=0):
        """mpv sürecini başlatır."""
        with self._lock:
            self.stop()

            self._build_playlist()
            if not self.playlist:
                logger.warning("Playlist boş, çalma iptal edildi.")
                return False

            # Playlist dosyası oluştur
            playlist_path = '/tmp/sahilmuzik_playlist.txt'
            with open(playlist_path, 'w') as f:
                for song in self.playlist:
                    filepath = os.path.join(MUSIC_DIR, song['filename'])
                    if os.path.exists(filepath):
                        f.write(filepath + '\n')

            settings = get_settings()
            volume = settings.get('volume', '80')
            repeat = settings.get('repeat_mode', 'all')

            cmd = [
                'mpv',
                '--no-video',
                '--no-terminal',
                f'--input-ipc-server={MPV_SOCKET}',
                f'--volume={volume}',
                f'--ao={AUDIO_OUTPUT}',
                f'--playlist={playlist_path}',
                f'--playlist-start={start_index}',
            ]

            if repeat == 'all':
                cmd.append('--loop-playlist=inf')
            elif repeat == 'one':
                cmd.append('--loop-file=inf')

            try:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                self.is_playing = True
                self.is_paused = False
                self.current_index = start_index
                if start_index < len(self.playlist):
                    self.current_song = self.playlist[start_index]

                # Monitor thread başlat
                self._stop_monitor = False
                self._monitor_thread = threading.Thread(target=self._monitor_playback, daemon=True)
                self._monitor_thread.start()

                logger.info(f"Müzik çalmaya başladı. Playlist: {len(self.playlist)} şarkı")
                return True
            except FileNotFoundError:
                logger.error("mpv bulunamadı! Lütfen 'sudo apt install mpv' ile kurun.")
                return False
            except Exception as e:
                logger.error(f"mpv başlatma hatası: {e}")
                return False

    def _monitor_playback(self):
        """Çalma durumunu izler ve mevcut şarkıyı günceller."""
        while not self._stop_monitor and self.process and self.process.poll() is None:
            try:
                idx = self._get_property('playlist-pos')
                if idx is not None and idx != self.current_index:
                    self.current_index = idx
                    if 0 <= idx < len(self.playlist):
                        self.current_song = self.playlist[idx]

                paused = self._get_property('pause')
                if paused is not None:
                    self.is_paused = paused

            except Exception:
                pass
            time.sleep(1)

        # Süreç bitti
        if not self._stop_monitor:
            self.is_playing = False
            self.is_paused = False
            self.current_song = None

    def play(self, index=0):
        """Çalmayı başlatır."""
        return self._start_mpv(index)

    def pause(self):
        """Çalmayı duraklatır/devam ettirir."""
        if self.process and self.process.poll() is None:
            current_pause = self._get_property('pause')
            if current_pause is not None:
                self._send_command(["set_property", "pause", not current_pause])
                self.is_paused = not current_pause
                return True
        return False

    def stop(self):
        """Çalmayı durdurur."""
        self._stop_monitor = True
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
            self.process = None

        # Socket temizle
        try:
            os.remove(MPV_SOCKET)
        except OSError:
            pass

        self.is_playing = False
        self.is_paused = False
        self.current_song = None
        self.current_index = -1

    def next_song(self):
        """Sonraki şarkıya geçer."""
        if self.process and self.process.poll() is None:
            self._send_command(["playlist-next", "weak"])
            return True
        return False

    def prev_song(self):
        """Önceki şarkıya geçer."""
        if self.process and self.process.poll() is None:
            self._send_command(["playlist-prev", "weak"])
            return True
        return False

    def set_volume(self, volume):
        """Ses seviyesini ayarlar (0-100)."""
        volume = max(0, min(100, int(volume)))
        update_setting('volume', str(volume))
        if self.process and self.process.poll() is None:
            self._send_command(["set_property", "volume", volume])
        return volume

    def get_status(self):
        """Çalma durumunu döndürür."""
        status = {
            'is_playing': False,
            'is_paused': False,
            'current_song': None,
            'position': 0,
            'duration': 0,
            'volume': 80,
            'playlist_length': len(self.playlist),
            'current_index': self.current_index,
        }

        settings = get_settings()
        status['volume'] = int(settings.get('volume', '80'))
        status['repeat_mode'] = settings.get('repeat_mode', 'all')
        status['shuffle'] = settings.get('shuffle', '0') == '1'

        if self.process and self.process.poll() is None:
            status['is_playing'] = True
            status['is_paused'] = self.is_paused

            pos = self._get_property('time-pos')
            dur = self._get_property('duration')
            vol = self._get_property('volume')

            if pos is not None:
                status['position'] = round(pos, 1)
            if dur is not None:
                status['duration'] = round(dur, 1)
            if vol is not None:
                status['volume'] = round(vol)

            if self.current_song:
                status['current_song'] = self.current_song
        else:
            self.is_playing = False
            self.is_paused = False

        return status

    def reload_playlist(self):
        """Playlist'i yeniden yükler (şarkı eklendiğinde/silindiğinde)."""
        if self.is_playing and not self.is_paused:
            current_pos = self._get_property('time-pos')
            self._build_playlist()
            # Çalıyorsa yeniden başlat
            self._start_mpv(0)
        else:
            self._build_playlist()


# Global player instance
player = MusicPlayer()
