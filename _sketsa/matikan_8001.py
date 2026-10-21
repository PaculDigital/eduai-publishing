#!/usr/bin/env python3
"""Matikan SEMUA proses server vitiasi :8001 di dalam container eduai-app.

🚨 PELAJARAN 29Sep26 (terbukti, 2× salah ukur):
   · Container TIDAK punya biner `kill` / `ps`.
   · Kode python `-c` inline di dalam bash sering tak menemukan prosesnya
     → server sisa HIDUP → port bentrok / memegang inode DB terhapus
     → uji lama menghasilkan 404 PALSU (salah menyudahi "kode rusak").
   Jadi: kode mati ditaruh di BERKAS, dijalankan sebagai file.

Aman untuk produksi: proses yang dibunuh HANYA yang cmdline-nya memuat
`--port 8001` (server produksi memakai `--port 8000`).

Pemakaian: python3 matikan_8001.py [port]
Keluar 0 = tidak ada lagi yang tersisa.
"""
import os
import signal
import sys
import time

PORT = sys.argv[1] if len(sys.argv) > 1 else '8001'
# GAYA PENGGANTUNG yang dipakai launcher — cocokkan SEMUANYA.
# (Satu gaya saja = server lolos dari pembersih → 404 palsu, 29Sep26.)
TANDA = (f'--port {PORT}', f'port={PORT}', f'server_vitiasi.py {PORT}')
LEWAT = ('matikan_8001.py',)   # jangan bunuh diri sendiri


def cari():
    ketemu = []
    for p in os.listdir('/proc'):
        if not p.isdigit():
            continue
        try:
            # 🚨 NUL-SEP: /proc/<pid>/cmdline memisahkan argumen dengan \x00
            #    → '--port\x008001' TIDAK cocok dengan '--port 8001' (spasi).
            #    Akibat: python-nya tak pernah ketemu, cuma bungkus `sh` yang
            #    dibunuh → anaknya yatim hidup terus (29Sep26, 2× salah ukur).
            cmd = open(f'/proc/{p}/cmdline', 'rb').read().replace(b'\x00', b' ').decode('utf8', 'ignore')
        except OSError:
            continue
        if any(t in cmd for t in TANDA) and not any(x in cmd for x in LEWAT):
            ketemu.append((p, cmd.replace('\x00', ' ').strip()[:110]))
    return ketemu


awal = cari()
print(f'kandidat port {PORT}: {len(awal)}')
for p, cmd in awal:
    print(f'  {p}: {cmd}')
for p, _ in awal:
    try:
        os.kill(int(p), signal.SIGKILL)
        print(f'  → dibunuh {p}')
    except Exception as e:                                  # noqa: BLE001
        print(f'  → GAGAL {p}: {e}')
time.sleep(1.5)
sisa = cari()
print(f'sisa setelah dibunuh: {len(sisa)} {sisa}')
sys.exit(0 if not sisa else 1)
