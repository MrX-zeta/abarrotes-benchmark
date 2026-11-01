FROM python:3.12-slim

# Versiones fijas para reproducibilidad (CLAUDE.md §6).
RUN pip install --no-cache-dir \
      pymongo==4.19.0 \
      "psycopg[binary]==3.3.6" \
      numpy==2.5.3 \
      pandas==3.0.5 \
      matplotlib==3.11.2 \
      requests==2.34.2

WORKDIR /work
