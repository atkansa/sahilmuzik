/* ═════════════════════════════════════════════════════════
   Sahil Müzik Sistemi - Frontend Application
   ═════════════════════════════════════════════════════════ */

const API = {
    get: (url) => fetch(url).then(r => r.json()),
    post: (url, data) => fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(r => r.json()),
    delete: (url) => fetch(url, { method: 'DELETE' }).then(r => r.json()),
    put: (url, data) => fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    }).then(r => r.json()),
};

const DAY_NAMES = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar'];

// ─── State ──────────────────────────────────────────────

let state = {
    songs: [],
    schedules: [],
    playerStatus: {},
    settings: {},
    activeTab: 'player',
    statusPollInterval: null,
};

// ─── Initialization ─────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initPlayer();
    initUpload();
    initSchedule();
    initSettings();

    // İlk veri yükleme
    loadSongs();
    loadSchedules();
    loadSettings();

    // Durum izleme
    startStatusPolling();
});

// ─── Tabs ───────────────────────────────────────────────

function initTabs() {
    const tabs = document.querySelectorAll('.nav-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    state.activeTab = tabName;

    // Tab butonlarını güncelle
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Tab içeriğini güncelle
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

// ─── Player ─────────────────────────────────────────────

function initPlayer() {
    document.getElementById('btnPlayPause').addEventListener('click', togglePlayPause);
    document.getElementById('btnStop').addEventListener('click', stopPlayback);
    document.getElementById('btnNext').addEventListener('click', nextSong);
    document.getElementById('btnPrev').addEventListener('click', prevSong);

    const volumeSlider = document.getElementById('volumeSlider');
    volumeSlider.addEventListener('input', (e) => {
        document.getElementById('volumeValue').textContent = `${e.target.value}%`;
    });
    volumeSlider.addEventListener('change', (e) => {
        setVolume(parseInt(e.target.value));
    });
}

async function togglePlayPause() {
    if (state.playerStatus.is_playing) {
        await API.post('/api/player/pause');
    } else {
        await API.post('/api/player/play', { index: 0 });
    }
    updateStatus();
}

async function stopPlayback() {
    await API.post('/api/player/stop');
    updateStatus();
}

async function nextSong() {
    await API.post('/api/player/next');
    updateStatus();
}

async function prevSong() {
    await API.post('/api/player/prev');
    updateStatus();
}

async function setVolume(volume) {
    await API.post('/api/player/volume', { volume });
}

function playSongByIndex(index) {
    API.post('/api/player/play', { index }).then(() => {
        switchTab('player');
        updateStatus();
    });
}

// ─── Status Polling ─────────────────────────────────────

function startStatusPolling() {
    updateStatus();
    state.statusPollInterval = setInterval(updateStatus, 2000);
}

async function updateStatus() {
    try {
        const status = await API.get('/api/player/status');
        state.playerStatus = status;
        renderPlayerStatus(status);
    } catch (e) {
        renderOfflineStatus();
    }
}

function renderPlayerStatus(status) {
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');
    const songTitle = document.getElementById('songTitle');
    const songSubtitle = document.getElementById('songSubtitle');
    const iconPlay = document.getElementById('iconPlay');
    const iconPause = document.getElementById('iconPause');
    const vinylDisc = document.getElementById('vinylDisc');
    const progressBar = document.getElementById('progressBar');
    const currentTime = document.getElementById('currentTime');
    const totalTime = document.getElementById('totalTime');
    const scheduleBadge = document.getElementById('scheduleBadge');
    const scheduleStatusText = document.getElementById('scheduleStatusText');

    // Durum göstergesi
    if (status.is_playing && !status.is_paused) {
        statusDot.className = 'status-dot playing';
        statusText.textContent = 'Çalıyor';
    } else if (status.is_paused) {
        statusDot.className = 'status-dot active';
        statusText.textContent = 'Duraklatıldı';
    } else {
        statusDot.className = 'status-dot active';
        statusText.textContent = 'Hazır';
    }

    // Şarkı bilgisi
    if (status.current_song) {
        songTitle.textContent = cleanSongName(status.current_song.original_name);
        songSubtitle.textContent = `${status.current_index + 1} / ${status.playlist_length} şarkı`;
    } else {
        songTitle.textContent = 'Şarkı seçilmedi';
        songSubtitle.textContent = 'Müzik kütüphanesinden şarkı yükleyin';
    }

    // Play/Pause ikonu
    if (status.is_playing && !status.is_paused) {
        iconPlay.style.display = 'none';
        iconPause.style.display = 'block';
        vinylDisc.classList.add('spinning');
    } else {
        iconPlay.style.display = 'block';
        iconPause.style.display = 'none';
        vinylDisc.classList.remove('spinning');
    }

    // İlerleme
    if (status.duration > 0) {
        const percent = (status.position / status.duration) * 100;
        progressBar.style.width = `${percent}%`;
        currentTime.textContent = formatTime(status.position);
        totalTime.textContent = formatTime(status.duration);
    } else {
        progressBar.style.width = '0%';
        currentTime.textContent = '0:00';
        totalTime.textContent = '0:00';
    }

    // Ses seviyesi
    document.getElementById('volumeSlider').value = status.volume;
    document.getElementById('volumeValue').textContent = `${status.volume}%`;

    // Zamanlama durumu
    if (status.schedule_active) {
        scheduleBadge.className = 'schedule-badge active';
        scheduleStatusText.textContent = 'Zamanlama aktif';
    } else {
        scheduleBadge.className = 'schedule-badge inactive';
        scheduleStatusText.textContent = 'Zamanlama pasif';
    }

    // Şarkı listesini güncelle (çalan şarkı vurgula)
    updatePlayingSongHighlight(status);
}

function renderOfflineStatus() {
    document.getElementById('statusDot').className = 'status-dot';
    document.getElementById('statusText').textContent = 'Bağlantı kesildi';
}

function updatePlayingSongHighlight(status) {
    document.querySelectorAll('.song-item').forEach(item => {
        item.classList.remove('playing');
    });

    if (status.is_playing && status.current_song) {
        const el = document.querySelector(`[data-song-id="${status.current_song.id}"]`);
        if (el) el.classList.add('playing');
    }
}

// ─── Songs ──────────────────────────────────────────────

async function loadSongs() {
    try {
        state.songs = await API.get('/api/songs');
        renderSongList();
    } catch (e) {
        console.error('Şarkılar yüklenemedi:', e);
    }
}

function renderSongList() {
    const list = document.getElementById('songList');
    const empty = document.getElementById('emptyLibrary');
    const count = document.getElementById('songCount');

    count.textContent = `${state.songs.length} şarkı`;
    document.getElementById('totalSongs').textContent = state.songs.length;

    if (state.songs.length === 0) {
        list.style.display = 'none';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    list.style.display = 'flex';

    list.innerHTML = state.songs.map((song, idx) => `
        <div class="song-item" data-song-id="${song.id}" onclick="playSongByIndex(${idx})">
            <div class="song-number">
                <span class="song-number-text">${idx + 1}</span>
                <div class="song-playing-indicator">
                    <div class="bar"></div>
                    <div class="bar"></div>
                    <div class="bar"></div>
                </div>
            </div>
            <div class="song-info">
                <div class="song-name">${escapeHtml(cleanSongName(song.original_name))}</div>
                <div class="song-duration">${formatTime(song.duration)}</div>
            </div>
            <div class="song-actions" onclick="event.stopPropagation()">
                <button class="song-action-btn delete" onclick="deleteSong(${song.id}, '${escapeHtml(song.original_name)}')" title="Sil">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        </div>
    `).join('');

    // Çalan şarkıyı vurgula
    if (state.playerStatus.is_playing && state.playerStatus.current_song) {
        updatePlayingSongHighlight(state.playerStatus);
    }
}

async function deleteSong(id, name) {
    if (!confirm(`"${cleanSongName(name)}" şarkısını silmek istediğinize emin misiniz?`)) return;

    try {
        await API.delete(`/api/songs/${id}`);
        showToast('Şarkı silindi', 'success');
        loadSongs();
    } catch (e) {
        showToast('Şarkı silinemedi', 'error');
    }
}

// ─── Upload ─────────────────────────────────────────────

function initUpload() {
    const zone = document.getElementById('uploadZone');
    const input = document.getElementById('fileInput');

    zone.addEventListener('click', () => input.click());

    zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        zone.classList.add('drag-over');
    });

    zone.addEventListener('dragleave', () => {
        zone.classList.remove('drag-over');
    });

    zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) uploadFiles(files);
    });

    input.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFiles(e.target.files);
            input.value = '';
        }
    });
}

async function uploadFiles(files) {
    const progContainer = document.getElementById('uploadProgressContainer');
    const progFill = document.getElementById('uploadProgressFill');
    const progText = document.getElementById('uploadProgressText');

    progContainer.style.display = 'block';
    let uploaded = 0;

    for (const file of files) {
        progText.textContent = `Yükleniyor: ${file.name} (${uploaded + 1}/${files.length})`;
        progFill.style.width = `${(uploaded / files.length) * 100}%`;

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/songs/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                uploaded++;
                progFill.style.width = `${(uploaded / files.length) * 100}%`;
            } else {
                const err = await response.json();
                showToast(`${file.name}: ${err.error}`, 'error');
            }
        } catch (e) {
            showToast(`${file.name} yüklenemedi`, 'error');
        }
    }

    progFill.style.width = '100%';
    progText.textContent = `${uploaded} dosya yüklendi`;

    setTimeout(() => {
        progContainer.style.display = 'none';
        progFill.style.width = '0%';
    }, 2000);

    if (uploaded > 0) {
        showToast(`${uploaded} şarkı eklendi`, 'success');
        loadSongs();
    }
}

// ─── Schedule ───────────────────────────────────────────

function initSchedule() {
    document.getElementById('btnAddSchedule').addEventListener('click', () => openScheduleModal());
    document.getElementById('btnCloseScheduleModal').addEventListener('click', closeScheduleModal);
    document.getElementById('btnCancelSchedule').addEventListener('click', closeScheduleModal);
    document.getElementById('btnSaveSchedule').addEventListener('click', saveSchedule);

    // Modal overlay tıklama ile kapatma
    document.getElementById('scheduleModal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) closeScheduleModal();
    });
}

async function loadSchedules() {
    try {
        state.schedules = await API.get('/api/schedule');
        renderScheduleList();
    } catch (e) {
        console.error('Zamanlamalar yüklenemedi:', e);
    }
}

function renderScheduleList() {
    const list = document.getElementById('scheduleList');
    const empty = document.getElementById('emptySchedule');

    const activeCount = state.schedules.filter(s => s.is_active).length;
    document.getElementById('activeSchedules').textContent = activeCount;

    if (state.schedules.length === 0) {
        list.style.display = 'none';
        empty.style.display = 'block';
        return;
    }

    empty.style.display = 'none';
    list.style.display = 'flex';

    list.innerHTML = state.schedules.map(schedule => `
        <div class="schedule-item ${schedule.is_active ? '' : 'inactive'}" data-schedule-id="${schedule.id}">
            <div class="schedule-day">${DAY_NAMES[schedule.day_of_week]}</div>
            <div class="schedule-time">
                ${schedule.start_time} <span>→</span> ${schedule.end_time}
            </div>
            <div class="schedule-actions">
                <button class="song-action-btn" onclick="toggleSchedule(${schedule.id})" title="${schedule.is_active ? 'Devre dışı bırak' : 'Etkinleştir'}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        ${schedule.is_active
                            ? '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>'
                            : '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>'
                        }
                    </svg>
                </button>
                <button class="song-action-btn delete" onclick="removeSchedule(${schedule.id})" title="Sil">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                </button>
            </div>
        </div>
    `).join('');
}

function openScheduleModal() {
    document.getElementById('scheduleModalTitle').textContent = 'Yeni Zamanlama';
    document.getElementById('scheduleDay').value = '0';
    document.getElementById('scheduleStart').value = '09:00';
    document.getElementById('scheduleEnd').value = '22:00';
    document.getElementById('scheduleModal').style.display = 'flex';
}

function closeScheduleModal() {
    document.getElementById('scheduleModal').style.display = 'none';
}

async function saveSchedule() {
    const day = parseInt(document.getElementById('scheduleDay').value);
    const start = document.getElementById('scheduleStart').value;
    const end = document.getElementById('scheduleEnd').value;

    if (!start || !end) {
        showToast('Başlangıç ve bitiş saati gereklidir', 'error');
        return;
    }

    try {
        await API.post('/api/schedule', {
            day_of_week: day,
            start_time: start,
            end_time: end,
        });
        showToast('Zamanlama eklendi', 'success');
        closeScheduleModal();
        loadSchedules();
    } catch (e) {
        showToast('Zamanlama eklenemedi', 'error');
    }
}

async function toggleSchedule(id) {
    try {
        await API.post(`/api/schedule/${id}/toggle`);
        loadSchedules();
    } catch (e) {
        showToast('İşlem başarısız', 'error');
    }
}

async function removeSchedule(id) {
    if (!confirm('Bu zamanlamayı silmek istediğinize emin misiniz?')) return;

    try {
        await API.delete(`/api/schedule/${id}`);
        showToast('Zamanlama silindi', 'success');
        loadSchedules();
    } catch (e) {
        showToast('Zamanlama silinemedi', 'error');
    }
}

// ─── Settings ───────────────────────────────────────────

function initSettings() {
    document.querySelectorAll('input[name="repeatMode"]').forEach(radio => {
        radio.addEventListener('change', (e) => {
            API.post('/api/settings', { repeat_mode: e.target.value });
            showToast('Tekrar modu güncellendi', 'info');
        });
    });

    document.getElementById('shuffleToggle').addEventListener('change', (e) => {
        API.post('/api/settings', { shuffle: e.target.checked ? '1' : '0' });
        showToast(e.target.checked ? 'Karıştırma açık' : 'Karıştırma kapalı', 'info');
    });
}

async function loadSettings() {
    try {
        state.settings = await API.get('/api/settings');

        // Tekrar modu
        const repeatMode = state.settings.repeat_mode || 'all';
        const radio = document.querySelector(`input[name="repeatMode"][value="${repeatMode}"]`);
        if (radio) radio.checked = true;

        // Karıştırma
        document.getElementById('shuffleToggle').checked = state.settings.shuffle === '1';
    } catch (e) {
        console.error('Ayarlar yüklenemedi:', e);
    }
}

// ─── Utilities ──────────────────────────────────────────

function formatTime(seconds) {
    if (!seconds || seconds <= 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function cleanSongName(filename) {
    if (!filename) return '';
    // Uzantıyı kaldır
    return filename.replace(/\.[^.]+$/, '').replace(/_/g, ' ');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('removing');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
