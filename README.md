# LyraSync

Веб-сервис для автоматической транскрипции песен с точными таймкодами и встроенным karaoke-плеером.

Загрузите аудиофайл → сервис отделит вокал, распознает речь через Whisper, подтянет текст песни с Genius и синхронизирует каждое слово с временной шкалой. На выходе — JSON, LRC и SRT с таймкодами.

---

## Архитектура

```
Browser
  │
  ▼
Nginx :80          ← React SPA + reverse proxy
  │
  ├─► FastAPI :8000   ← REST API (upload / status / result)
  │       │
  │       └─► PostgreSQL  ← хранение статусов задач
  │       └─► Redis       ← очередь задач (RQ)
  │       └─► MinIO       ← хранение аудио и результатов (S3-совместимый)
  │
  └─► RQ Worker          ← асинхронный pipeline обработки
          │
          ├─ FFmpeg          (препроцессинг аудио)
          ├─ Demucs          (отделение вокала)
          ├─ Faster-Whisper  (speech-to-text, CUDA)
          ├─ Genius API      (получение текста песни)
          └─ aeneas          (выравнивание аудио и текста)
```

---

## Требования

### Для запуска через Docker (рекомендуется)

| Компонент | Версия |
|-----------|--------|
| Docker | 24+ |
| Docker Compose | v2.20+ |
| NVIDIA GPU | с поддержкой CUDA 12.1+ |
| NVIDIA Container Toolkit | последняя |

> **Без GPU:** замените `WHISPER_DEVICE=cuda` на `WHISPER_DEVICE=cpu` в `.env`
> и удалите блок `deploy.resources` из секции `worker` в `docker-compose.yml`.

### Для ручной установки

| Компонент | Версия |
|-----------|--------|
| Python | 3.10 (обязательно — aeneas несовместим с 3.11+) |
| Node.js | 20+ |
| FFmpeg | любая актуальная |
| espeak | + libespeak-dev |
| PostgreSQL | 14+ |
| Redis | 7+ |

---

## Быстрый старт (Docker)

### 1. Клонируйте репозиторий

```bash
git clone <repo-url>
cd LyraSync
```

### 2. Создайте файл `.env`

```bash
cp .env.example .env
```

Откройте `.env` и заполните обязательные поля:

```env
# Получить токен: https://genius.com/api-clients
GENIUS_TOKEN=your_genius_token_here

# Для CPU-режима (без GPU):
# WHISPER_DEVICE=cpu
# WHISPER_MODEL=base   # large-v3 слишком медленный без GPU
```

### 3. Соберите и запустите

```bash
docker compose up --build
```

Первый запуск занимает 10–20 минут: скачиваются образы CUDA (~5 GB), PyTorch, Demucs, Whisper.

### 4. Откройте браузер

```
http://localhost
```

MinIO-консоль доступна по адресу `http://localhost:9001` (minioadmin / minioadmin).

---

## Конфигурация

Все настройки задаются через `.env`:

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `DATABASE_URL` | `postgresql+asyncpg://lyrasync:lyrasync@postgres:5432/lyrasync` | Строка подключения к PostgreSQL |
| `REDIS_URL` | `redis://redis:6379/0` | Строка подключения к Redis |
| `S3_ENDPOINT` | `http://minio:9000` | Endpoint MinIO/S3 |
| `S3_ACCESS_KEY` | `minioadmin` | Access key |
| `S3_SECRET_KEY` | `minioadmin` | Secret key |
| `S3_BUCKET` | `lyrasync` | Имя бакета |
| `GENIUS_TOKEN` | — | **Обязательный.** API-токен Genius |
| `WHISPER_MODEL` | `large-v3` | Модель Whisper (tiny/base/small/medium/large-v3) |
| `WHISPER_DEVICE` | `cuda` | Устройство (`cuda` или `cpu`) |
| `MAX_FILE_SIZE_MB` | `50` | Максимальный размер загружаемого файла |
| `MAX_DURATION_SEC` | `900` | Максимальная длительность (секунды) |
| `RATE_LIMIT_PER_MINUTE` | `10` | Rate limit на IP в минуту |

---

## API

Base URL: `http://localhost/api`

### POST `/audio/upload`

Загрузить аудиофайл на обработку.

**Тело запроса:** `multipart/form-data`, поле `file` (MP3, WAV, M4A, макс. 50 МБ).

**Ответ `202 Accepted`:**
```json
{
  "audio_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

---

### GET `/audio/{audio_id}/status`

Проверить статус обработки.

**Ответ `200 OK`:**
```json
{
  "audio_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "error_message": null
}
```

Возможные статусы: `pending` → `queued` → `processing` → `done` / `failed`.

---

### GET `/audio/{audio_id}/result`

Получить результат (доступно только при `status: done`).

**Ответ `200 OK`:**
```json
{
  "audio_id": "...",
  "status": "done",
  "json": [
    { "start": 12.4, "end": 14.1, "text": "Hello darkness my old friend" }
  ],
  "lrc": "[00:12.40]Hello darkness my old friend\n...",
  "srt": "1\n00:00:12,400 --> 00:00:14,100\nHello darkness my old friend\n..."
}
```

---

### GET `/health`

Проверка работоспособности сервера. Возвращает `{"status": "ok"}`.

---

## Ручная установка (без Docker)

### Backend

```bash
cd backend

# Создайте виртуальное окружение с Python 3.10
python3.10 -m venv venv
source venv/bin/activate

# Установите системные зависимости (Ubuntu/Debian)
sudo apt-get install ffmpeg build-essential

# Установите зависимости
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Скопируйте и настройте .env
cp ../.env.example ../.env
# Отредактируйте ../.env: укажите DATABASE_URL, REDIS_URL, GENIUS_TOKEN

# Запустите API
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# В отдельном терминале — запустите worker
rq worker pipeline --url redis://localhost:6379/0
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # development с hot-reload на :5173
# или
npm run build    # production-сборка в dist/
```

---

## Разработка

### Запуск тестов (backend)

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### Пересборка конкретного сервиса

```bash
docker compose build api
docker compose up -d api
```

### Просмотр логов

```bash
docker compose logs -f worker   # логи RQ-worker
docker compose logs -f api      # логи FastAPI
```

### Остановка и очистка

```bash
docker compose down              # остановить контейнеры
docker compose down -v           # + удалить volumes (все данные)
```

---

## Устранение проблем

### Нет GPU / `driver: nvidia` not found

Уберите блок `deploy.resources` из секции `worker` в `docker-compose.yml` и поставьте:
```env
WHISPER_DEVICE=cpu
WHISPER_MODEL=base
```

### MinIO bucket не создаётся автоматически

Бакет создаётся приложением при первом запросе. Если этого не произошло — откройте консоль `http://localhost:9001` и создайте бакет `lyrasync` вручную.

### `connection refused` на postgres/redis при старте api

Healthcheck-зависимости обычно решают это. Если нет — подождите 30 секунд и выполните:
```bash
docker compose restart api worker
```
