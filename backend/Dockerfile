# Matches backend/.python-version. No build stage needed: cryptography and cffi both
# ship manylinux wheels, so nothing here compiles.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# settings.py reads SECRET_KEY at import time with no default, so collectstatic needs
# one - a throwaway value, since nothing signed at build time outlives the build.
RUN SECRET_KEY=build-only python manage.py collectstatic --noinput

RUN useradd --create-home --uid 1000 app \
    && mkdir /data \
    && chown app:app /data
USER app

# The SQLite volume mounts here; DATABASE_URL in docker-compose.yml points at it.
VOLUME ["/data"]

EXPOSE 8000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
