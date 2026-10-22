FROM node:22-slim AS frontend
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
ENV VITE_API_URL=/
RUN npm run build

FROM python:3.11-slim-trixie AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 GHOST_MODE=hosted PORT=8000
WORKDIR /app
COPY requirements.txt ./
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y setuptools wheel pip \
    && rm -rf /usr/local/lib/python3.11/ensurepip/_bundled \
    && useradd --create-home --uid 10001 ghost \
    && mkdir -p /app/data /app/logs \
    && chown ghost:ghost /app/data /app/logs
COPY server.py server_auth.py server_db.py ./
COPY ghost/ ./ghost/
COPY --from=frontend /ui/build ./frontend/build
USER ghost
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/health', timeout=3)"
CMD ["sh", "-c", "exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers --forwarded-allow-ips=${FORWARDED_ALLOW_IPS:-127.0.0.1}"]
