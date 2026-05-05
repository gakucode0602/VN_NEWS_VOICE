#!/bin/sh
set -e

# ---------------------------------------------------------------------------
# SSH setup (RunPod terminal access)
# RunPod injects your SSH public key via $PUBLIC_KEY env var.
# If not set (local dev), SSH daemon still starts but no key = no access.
# ---------------------------------------------------------------------------
if [ -n "${PUBLIC_KEY}" ]; then
    mkdir -p /root/.ssh
    echo "${PUBLIC_KEY}" >> /root/.ssh/authorized_keys
    chmod 700 /root/.ssh
    chmod 600 /root/.ssh/authorized_keys
    echo "[entrypoint] SSH public key injected."
fi

# Start SSH daemon in background
/usr/sbin/sshd
echo "[entrypoint] sshd started."

# ---------------------------------------------------------------------------
# Adapter sync from MinIO (if not already present)
# ---------------------------------------------------------------------------
ADAPTER_DIR="models/vit5-qlora-adapter"
MINIO_BUCKET="${MINIO_BUCKET:-vnnewsvoice-models}"
S3_PATH="s3://${MINIO_BUCKET}/vit5-qlora-adapter"

# Only download if the adapter is not already present (e.g. from a mounted Network Volume).
if [ ! -f "${ADAPTER_DIR}/adapter_config.json" ]; then
    echo "[entrypoint] Adapter not found locally — syncing from MinIO ${MINIO_ENDPOINT_URL} ${S3_PATH} ..."
    AWS_ACCESS_KEY_ID="${MINIO_ACCESS_KEY}" \
    AWS_SECRET_ACCESS_KEY="${MINIO_SECRET_KEY}" \
    aws s3 sync "${S3_PATH}" "${ADAPTER_DIR}" \
        --endpoint-url "${MINIO_ENDPOINT_URL}"
    if [ ! -f "${ADAPTER_DIR}/adapter_config.json" ]; then
        echo "[entrypoint] WARNING: MinIO sync completed but adapter_config.json still missing."
        echo "[entrypoint] Service will start in base-model-only mode."
    else
        echo "[entrypoint] Adapter download complete."
    fi
else
    echo "[entrypoint] Adapter already present at ${ADAPTER_DIR}, skipping download."
fi

exec "$@"

