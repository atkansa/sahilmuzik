import threading
import time
import logging
from datetime import datetime
from database import get_all_schedules, get_all_songs
from player import player

logger = logging.getLogger('sahilmuzik.scheduler')


class Scheduler:
    """Zamanlama motoru - belirli saatlerde müzik başlatır/durdurur."""

    def __init__(self, interval=15):
        self.interval = interval
        self._thread = None
        self._running = False
        self._was_playing_by_schedule = False

    def start(self):
        """Zamanlayıcıyı başlatır."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("Zamanlayıcı başlatıldı.")

        # İlk kontrolü hemen yap
        self._check_schedule()

    def stop(self):
        """Zamanlayıcıyı durdurur."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Zamanlayıcı durduruldu.")

    def _run(self):
        """Ana döngü."""
        while self._running:
            time.sleep(self.interval)
            if self._running:
                self._check_schedule()

    def _check_schedule(self):
        """Mevcut saati kontrol eder ve müziği başlatır/durdurur."""
        try:
            now = datetime.now()
            current_day = now.weekday()  # 0=Pazartesi, 6=Pazar
            current_time = now.strftime('%H:%M')

            schedules = get_all_schedules()
            songs = get_all_songs()

            if not schedules:
                # Zamanlama yoksa müdahale etme
                return

            should_play = False

            for schedule in schedules:
                if not schedule['is_active']:
                    continue
                if schedule['day_of_week'] != current_day:
                    continue

                start = schedule['start_time']
                end = schedule['end_time']

                # Gece yarısını geçen zamanlamalar (ör: 22:00 - 04:00)
                if start <= end:
                    if start <= current_time < end:
                        should_play = True
                        break
                else:
                    # Gece yarısını geçen durumda
                    if current_time >= start or current_time < end:
                        should_play = True
                        break

            if should_play and songs:
                if not player.is_playing or (not self._was_playing_by_schedule):
                    if not player.is_playing:
                        logger.info(f"Zamanlama aktif - müzik başlatılıyor. Gün: {current_day}, Saat: {current_time}")
                        player.play()
                    self._was_playing_by_schedule = True
            else:
                if self._was_playing_by_schedule and player.is_playing:
                    logger.info(f"Zamanlama bitti - müzik durduruluyor. Gün: {current_day}, Saat: {current_time}")
                    player.stop()
                self._was_playing_by_schedule = False

        except Exception as e:
            logger.error(f"Zamanlama kontrol hatası: {e}")

    def is_within_schedule(self):
        """Şu an zamanlamanın aktif olup olmadığını döndürür."""
        now = datetime.now()
        current_day = now.weekday()
        current_time = now.strftime('%H:%M')

        schedules = get_all_schedules()
        for schedule in schedules:
            if not schedule['is_active']:
                continue
            if schedule['day_of_week'] != current_day:
                continue

            start = schedule['start_time']
            end = schedule['end_time']

            if start <= end:
                if start <= current_time < end:
                    return True
            else:
                if current_time >= start or current_time < end:
                    return True

        return False


# Global scheduler instance
scheduler = Scheduler()
