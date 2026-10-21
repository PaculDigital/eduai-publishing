#!/usr/bin/env bash
# UJI PAGAR: apakah PEMBIMBING bisa masuk /edit/{fid} naskah mahasiswa?
# dan apakah bisa menyimpan via /oo/simpan?
cd /opt/data/services/eduai-publishing || exit 1

echo "=== A. Pagar rute /edit/{fid} ==="
sed -n '/async def halaman_editor/,/^async def /p' app/main.py | head -35
