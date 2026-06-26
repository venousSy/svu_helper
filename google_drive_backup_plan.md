# Automated MongoDB → Google Drive Backup

A self-contained backup system that runs as a **dedicated Docker container** alongside the bot.
Every 6 hours (configurable), it dumps the MongoDB database, compresses it, and uploads it to Google Drive.
All 6 flow issues from the original review have been addressed.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  docker-compose                                             │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌─────────────────────────┐ │
│  │   bot    │   │  mongo   │◄──│  backup (this service)  │ │
│  └──────────┘   └──────────┘   │                         │ │
│                                │  1. mongodump (auth URI) │ │
│                                │  2. tar.gz compress      │ │
│                                │  3. Upload → Google Drive│ │
│                                │  4. Prune old backups    │ │
│                                │  5. Notify admins        │ │
│                                └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

The `backup` service is **fully isolated** — it has its own `Dockerfile.backup`,
`backup/requirements.txt`, and `backup/config.py`. It does not import anything
from the main bot project (no aiogram, no motor, no Redis).

---

## Files Created / Modified

| File | Status | Purpose |
|------|--------|---------|
| `Dockerfile.backup` | NEW | Two-stage build with `mongo-tools` + Python deps |
| `backup/__init__.py` | NEW | Python package marker |
| `backup/config.py` | NEW | Standalone pydantic-settings config |
| `backup/gdrive.py` | NEW | Drive client: credentials, upload, cleanup |
| `backup/runner.py` | NEW | Core backup logic (dump → compress → upload → notify) |
| `backup/main.py` | NEW | Entrypoint + APScheduler |
| `backup/requirements.txt` | NEW | Pinned Python dependencies |
| `docker-compose.yml` | MODIFIED | Added `backup` service + explicit network |
| `.gitignore` | MODIFIED | Added `credentials/` + `gdrive.json` |
| `tests/test_backup.py` | NEW | 18 unit tests (all mocked) |

---

## Flow Issues Fixed

| # | Issue | Fix Applied |
|---|-------|-------------|
| 1 | `mongodump` had no auth | URI built as `mongodb://user:pass@mongo:27017/?authSource=admin` |
| 2 | No Docker network declaration | Explicit `networks: default` + named network in compose |
| 3 | `credentials/` file won't work on Railway | Base64 env var (`GDRIVE_CREDENTIALS_B64`) decoded at runtime |
| 4 | No admin alert on failure | `try/except` sends ❌ Telegram message via `aiohttp` |
| 5 | Temp files left on disk after upload failure | `finally:` block calls `shutil.rmtree()` unconditionally |
| 6 | Large uploads would fail / hit rate limits | `MediaFileUpload(resumable=True, chunksize=10MB)` |

---

## One-Time Setup (Railway)

> [!IMPORTANT]
> **Step 1 — Google Cloud Console**
> 1. Create a project → Enable **Google Drive API**
> 2. Go to **Credentials** → **Create Credentials** → **Service Account**
> 3. Download the JSON key as `gdrive.json`
>
> **Step 2 — Google Drive**
> 4. Create a folder (e.g. `SVU_Backups`)
> 5. Share it with the Service Account email (`xxx@yyy.iam.gserviceaccount.com`)
> 6. Copy the **Folder ID** from the Drive URL: `drive.google.com/drive/folders/`**`THIS_PART`**
>
> **Step 3 — Generate the base64 string**
>
> On Windows (PowerShell):
> ```powershell
> [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\gdrive.json")) | Set-Clipboard
> ```
> On Linux/Mac:
> ```bash
> base64 -w 0 gdrive.json | pbcopy
> ```
>
> **Step 4 — Add Railway environment variables**
>
> | Variable | Value |
> |----------|-------|
> | `GDRIVE_CREDENTIALS_B64` | (paste from clipboard) |
> | `GDRIVE_FOLDER_ID` | (from Drive folder URL) |
> | `MONGO_USER` | your MongoDB username |
> | `MONGO_PASS` | your MongoDB password |
> | `BACKUP_RETENTION_DAYS` | `7` (optional, default is 7) |
> | `BACKUP_INTERVAL_HOURS` | `6` (optional, default is 6) |

---

## Notifications

On every backup cycle, the bot sends a Telegram message to all admin IDs:

**Success (✅):**
```
✅ Backup Successful
📦 File: svu_helper_backup_2026-06-26_14-00-00.tar.gz
📁 Size: 42.3 MB
🕒 Time: 2026-06-26 14:00 UTC
⏱ Duration: 18s
🗑 Old backups pruned: 1
```

**Failure (❌):**
```
❌ Backup FAILED
🕒 Time: 2026-06-26 14:00 UTC
💥 Reason: RuntimeError: mongodump exited with code 1: auth failed

Check Railway logs for full stack trace.
```

---

## Running Tests

```bash
pytest tests/test_backup.py -v
```

All 18 tests run with no network calls, no Google Drive API, no Telegram API,
and no real `mongodump` execution.
