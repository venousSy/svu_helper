# Automate MongoDB Backups to Google Drive

This plan details the implementation of an automated backup system that dumps the MongoDB database every 6 hours, compresses it, and uploads it to a specified folder in your Google Drive. 

## User Review Required

> [!IMPORTANT]
> **Google Drive Setup Required**
> Automating uploads to Google Drive requires a **Google Cloud Service Account**. Since this cannot be done automatically, you will need to:
> 1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
> 2. Create a new Project and enable the **Google Drive API**.
> 3. Go to "Credentials" -> "Create Credentials" -> "Service Account".
> 4. Create a key (JSON format) and download it.
> 5. Open your Google Drive, create a folder for backups (e.g., `SVU_Backups`), and **share it** with the Service Account email address.
> 6. Add the JSON contents as a single-line string to your `.env` file (`GDRIVE_CREDENTIALS_JSON='{...}'`), along with the `GDRIVE_FOLDER_ID`.

> [!WARNING]
> **Docker Image Changes**
> We need to install `mongo-tools` inside the `bot` container so it can run the `mongodump` command against the database container. This requires rebuilding your Docker image (`docker-compose build`).

## Proposed Changes

### Configuration and Dependencies
- **requirements.txt**: Add `apscheduler`, `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`.
- **config.py**: Add `GDRIVE_CREDENTIALS_JSON` and `GDRIVE_FOLDER_ID`.
- **Dockerfile**: Install `mongo-tools` via `apt-get` for `mongodump`.

### Application Logic
- **backup_service.py** [NEW]: Service to run `mongodump`, compress to `.tar.gz`, and upload to Google Drive using the Service Account.
- **main.py**: Schedule `AsyncIOScheduler` to run `backup_service.run_backup()` every 6 hours.
