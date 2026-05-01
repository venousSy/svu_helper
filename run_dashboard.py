"""
Dashboard entrypoint — reads PORT from environment so Railway can inject it.
Avoids shell $PORT expansion issues entirely.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "dashboard_api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )
