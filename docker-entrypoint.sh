#!/bin/sh
# Render allows ONE persistent disk per service. Mount it at /data; this keeps uploads, backups and
# certificate signatures on it by symlinking the paths the code expects.
set -e
if [ -d /data ]; then
  mkdir -p /data/uploads /data/backups /data/signatures
  rm -rf /app/uploads /app/backups /app/storage/signatures
  mkdir -p /app/storage
  ln -s /data/uploads /app/uploads
  ln -s /data/backups /app/backups
  ln -s /data/signatures /app/storage/signatures
  chown -R node:node /data
fi
mkdir -p /app/logs && chown node:node /app/logs
exec su-exec node "$@"
