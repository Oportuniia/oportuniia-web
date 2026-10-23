FROM python:3.12-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends clamav ca-certificates coreutils \
    && rm -rf /var/lib/apt/lists/* \
    && freshclam
WORKDIR /app
COPY backend/requirements-private.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app
COPY deploy/scanner/run.sh /app/run-scan.sh
RUN chmod 755 /app/run-scan.sh
ENV WEB_SCAN_MODE=local-clamscan
USER clamav
# Bounds each invocation including signature update and all pending documents.
CMD ["timeout", "--signal=TERM", "--kill-after=10s", "900s", "/app/run-scan.sh"]
