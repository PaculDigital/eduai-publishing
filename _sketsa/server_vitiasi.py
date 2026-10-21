#!/usr/bin/env python3
"""Server VITIASI :8001 untuk uji Opsi D — SALINAN kode/DB/berkas.

Kenapa berkas, bukan `python3 -c` inline (pelajaran 29Sep26):
  · cmdline `python3 -c "..."` TIDAK memuat `--port 8001`
    → skrip pembersih tak pernah menemukannya → server sisa HIDUP
    → memegang inode DB yang sudah dihapus → uji dapat 404 PALSU.
  · Sebagai berkas, cmdline = `python3 /tmp/server_vitiasi.py 8001`
    → mudah dikenali & dibunuh.

Kenapa log_config=None + basicConfig(INFO):
  · log.app di produksi level 30 (WARNING) → jejak `OPSI D` hilang.
    Uji BUTUH jejak `pendamping pipa DIPAKAI`. Produksi TIDAK diubah.

Pemakaian: python3 server_vitiasi.py <port>
"""
import logging
import socket
import sys
import threading
import time

import uvicorn

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


def penanda():
    """Tulis penanda HANYA kalau port benar-benar bisa dihubungi."""
    for _ in range(60):
        time.sleep(0.5)
        s = socket.socket()
        terbuka = s.connect_ex(('127.0.0.1', PORT)) == 0
        s.close()
        if terbuka:
            print(f'VITIASI TERIKAT {PORT}', flush=True)
            return
    print('VITIASI GAGAL TERIKAT', flush=True)


threading.Thread(target=penanda, daemon=True).start()
uvicorn.run('app.main:app', host='127.0.0.1', port=PORT, log_config=None)
