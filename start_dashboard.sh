#!/bin/sh
exec uvicorn dashboard_api.main:app --host 0.0.0.0 --port "${PORT:-8080}"
