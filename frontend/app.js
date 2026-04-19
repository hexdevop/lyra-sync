const API = '/api';

const $ = id => document.getElementById(id);

const sections = {
  upload: $('upload-section'),
  progress: $('progress-section'),
  karaoke: $('karaoke-section'),
};

let lines = [];        // [{start, end, text}]
let audioId = null;
let pollTimer = null;
let objectUrl = null;

// ─── Upload ────────────────────────────────────────────────────────────────

const dropZone = $('drop-zone');
const fileInput = $('file-input');

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

async function handleFile(file) {
  const allowed = ['audio/mpeg', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/x-m4a'];
  const ext = file.name.split('.').pop().toLowerCase();
  if (!['mp3', 'wav', 'm4a'].includes(ext)) { showError('Поддерживаются только MP3, WAV, M4A'); return; }
  if (file.size > 50 * 1024 * 1024) { showError('Файл превышает 50 MB'); return; }

  // Keep object URL for audio player
  if (objectUrl) URL.revokeObjectURL(objectUrl);
  objectUrl = URL.createObjectURL(file);

  showSection('progress');
  setProgress(5, 'Загрузка файла…');

  const form = new FormData();
  form.append('file', file);

  let res;
  try {
    res = await fetch(`${API}/audio/upload`, { method: 'POST', body: form });
  } catch (err) {
    showError('Ошибка соединения с сервером'); showSection('upload'); return;
  }

  if (!res.ok) {
    const e = await res.json().catch(() => ({}));
    showError(e.detail || `Ошибка ${res.status}`); showSection('upload'); return;
  }

  const data = await res.json();
  audioId = data.audio_id;

  if (data.status === 'done') {
    setProgress(100, 'Готово!');
    await loadResult(audioId);
    return;
  }

  setProgress(15, 'Файл принят, идёт обработка…');
  startPolling(audioId);
}

// ─── Polling ───────────────────────────────────────────────────────────────

const STEPS = ['Предобработка…', 'Разделение вокала…', 'Распознавание текста…', 'Поиск текста песни…', 'Синхронизация…'];
let stepIdx = 0;

function startPolling(id) {
  stepIdx = 0;
  pollTimer = setInterval(() => poll(id), 3000);
}

async function poll(id) {
  let res;
  try {
    res = await fetch(`${API}/audio/${id}/status`);
  } catch { return; }

  const data = await res.json();

  if (data.status === 'processing') {
    stepIdx = Math.min(stepIdx + 1, STEPS.length - 1);
    setProgress(20 + stepIdx * 14, STEPS[stepIdx]);
  } else if (data.status === 'done') {
    clearInterval(pollTimer);
    setProgress(100, 'Готово!');
    setTimeout(() => loadResult(id), 400);
  } else if (data.status === 'failed') {
    clearInterval(pollTimer);
    showError(data.error_message || 'Обработка завершилась с ошибкой');
    showSection('upload');
  }
}

// ─── Result ────────────────────────────────────────────────────────────────

async function loadResult(id) {
  const res = await fetch(`${API}/audio/${id}/result`);
  if (!res.ok) { showError('Не удалось получить результат'); showSection('upload'); return; }
  const data = await res.json();

  lines = data.json || [];
  $('lrc-content').textContent = data.lrc || '';
  $('srt-content').textContent = data.srt || '';

  buildLyricsUI();

  const player = $('audio-player');
  player.src = objectUrl;

  showSection('karaoke');
}

// ─── Karaoke UI ────────────────────────────────────────────────────────────

function buildLyricsUI() {
  const container = $('lyrics-container');
  container.innerHTML = '';
  lines.forEach((ln, i) => {
    const el = document.createElement('div');
    el.className = 'lyric-line';
    el.dataset.index = i;
    el.textContent = ln.text;
    el.addEventListener('click', () => {
      $('audio-player').currentTime = ln.start;
      $('audio-player').play();
    });
    container.appendChild(el);
  });
}

$('audio-player').addEventListener('timeupdate', () => {
  const t = $('audio-player').currentTime;
  let active = -1;
  for (let i = 0; i < lines.length; i++) {
    if (t >= lines[i].start && t < lines[i].end) { active = i; break; }
  }

  document.querySelectorAll('.lyric-line').forEach((el, i) => {
    const isActive = i === active;
    el.classList.toggle('active', isActive);
    if (isActive) {
      el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  });
});

// ─── Tabs ──────────────────────────────────────────────────────────────────

document.querySelectorAll('.tab').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.add('hidden'));
    btn.classList.add('active');
    $('tab-' + btn.dataset.tab).classList.remove('hidden');
  });
});

$('copy-lrc').addEventListener('click', () => copyText($('lrc-content').textContent, $('copy-lrc')));
$('copy-srt').addEventListener('click', () => copyText($('srt-content').textContent, $('copy-srt')));

function copyText(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const orig = btn.textContent;
    btn.textContent = 'Скопировано!';
    setTimeout(() => btn.textContent = orig, 1500);
  });
}

// ─── Reset ─────────────────────────────────────────────────────────────────

$('reset-btn').addEventListener('click', () => {
  clearInterval(pollTimer);
  audioId = null; lines = [];
  $('audio-player').src = '';
  $('lyrics-container').innerHTML = '';
  $('lrc-content').textContent = '';
  $('srt-content').textContent = '';
  fileInput.value = '';
  showSection('upload');
});

// ─── Helpers ───────────────────────────────────────────────────────────────

function showSection(name) {
  Object.entries(sections).forEach(([k, el]) => el.classList.toggle('hidden', k !== name));
}

function setProgress(pct, label) {
  $('progress-fill').style.width = pct + '%';
  $('progress-label').textContent = label;
}

function showError(msg) {
  const toast = $('error-toast');
  toast.textContent = msg;
  toast.classList.remove('hidden');
  setTimeout(() => toast.classList.add('hidden'), 4000);
}
