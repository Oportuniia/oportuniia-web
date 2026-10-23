#!/bin/sh
set -eu
# No scan is marked clean if signature refresh fails.
freshclam --stdout
exec python scan_batch.py
