#!/bin/sh

set -e

echo "⏳ Waiting for database..."

until python manage.py showmigrations > /dev/null 2>&1; do
    echo "  Database not ready — retrying in 2 seconds..."
    sleep 2
done

echo "✅ Database ready"

echo "🔄 Running migrations..."
python manage.py migrate --noinput

# ── collectstatic uploads to S3 in production ─────────────────────────────────
# When USE_S3=True, collectstatic sends files to S3 instead of local filesystem
# Nginx doesn't need to serve them — browser fetches directly from S3 URL
# In local dev (USE_S3=False), this writes to /app/staticfiles/ as usual
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🚀 Starting: $@"
exec "$@"