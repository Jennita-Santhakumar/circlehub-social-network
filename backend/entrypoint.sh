#!/bin/sh
set -e

echo "Waiting for postgres at ${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}..."
until python - <<'PYEOF'
import os, socket, sys
host = os.environ.get("POSTGRES_HOST", "db")
port = int(os.environ.get("POSTGRES_PORT", "5432"))
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect((host, port))
except OSError:
    sys.exit(1)
finally:
    s.close()
PYEOF
do
  sleep 1
done

case "$1" in
  daphne)
    # Only the web (ASGI) service runs migrations/collectstatic, to avoid
    # concurrent `migrate` races against the same Postgres from celery/celery-beat.
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput --clear || true
    ;;
  celery)
    echo "Waiting for web to finish migrations..."
    until python manage.py migrate --check >/dev/null 2>&1; do
      sleep 2
    done
    ;;
esac

exec "$@"
