"""Alat bedah C7 — tarik BUKTI kegagalan dari log + DB produksi.

Dipakai SETELAH `_uji_publik_komentar.py` selesai, untuk mencari AKAR
(bukan menambal): semua baris GAGAL + konteksnya, plus jejak nyata di DB
(proses_ai: status/token/model/galat; versi_dokumen 0 kar = C9; log server).

JALANKAN: python3 _sketsa/bedah_c7.py <log-c7>
"""
from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter

LOG = sys.argv[1] if len(sys.argv) > 1 else '_arsip/c7_pascapagar_28sep.log'


def docker(cmd: str) -> str:
    r = subprocess.run(['docker', 'exec', 'eduai-app', 'sh', '-c', cmd],
                       capture_output=True, text=True, timeout=60)
    return r.stdout + r.stderr


def main() -> int:
    isi = open(LOG, encoding='utf-8', errors='replace').read()

    print('=' * 78)
    print('1. RINGKASAN UJI')
    print('=' * 78)
    m = re.search(r'HASIL:\s*(\d+)\s*LULUS\s*/\s*(\d+)\s*GAGAL', isi)
    print(f'  {m.group(0) if m else "ringkasan tidak ditemukan"}')

    print('\n' + '=' * 78)
    print('2. SEMUA BARIS GAGAL (dengan konteks 1 baris sebelumnya)')
    print('=' * 78)
    baris = isi.splitlines()
    gagal = [i for i, b in enumerate(baris) if '❌' in b]
    if not gagal:
        print('  (tidak ada ❌ — uji bersih)')
    for i in gagal:
        sebelum = baris[i - 1].strip() if i else ''
        print(f'  ── konteks: {sebelum[:150]}')
        print(f'     {baris[i].strip()[:220]}')

    print('\n' + '=' * 78)
    print('3. JEJAK NYATA DI DB (proses_ai terakhir)')
    print('=' * 78)
    print(docker(
        "python3 -c \"import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
        "[print(r) for r in c.execute("
        "'SELECT id,status,jumlah_bagian,model_ai,token_in,token_out,"
        "token_revisi,substr(coalesce(galat,\\'\\'),1,120) FROM proses_ai "
        "ORDER BY id DESC LIMIT 12')]\""))

    print('=' * 78)
    print('4. VERSI 0 KAR (C9) + saldo tersisa')
    print('=' * 78)
    print(docker(
        "python3 -c \"import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
        "print('versi 0 kar:', c.execute(\\\"SELECT COUNT(*) FROM versi_dokumen "
        "WHERE length(coalesce(isi,''))<40\\\").fetchone()[0]);"
        "print('saldo user6:', c.execute('SELECT sisa FROM saldo_token "
        "WHERE user_id=6 ORDER BY id DESC LIMIT 1').fetchone()[0])\""))

    print('=' * 78)
    print('5. LOG SERVER — galat AI / pipa / penolakan (200 baris terakhir)')
    print('=' * 78)
    log = docker(
        "grep -E 'gagal|ERROR|WARNING|pipa|tolak|503|timeout|fallback' "
        "/proc/1/fd/1 2>/dev/null | tail -80")
    if not log.strip():
        log = docker(
            "grep -rE 'gagal|ERROR|pipa|tolak|503|fallback' "
            "/var/log 2>/dev/null | tail -40")
    print(log[-6000:] if log.strip() else '  (log container tak terjangkau via fd)')

    print('=' * 78)
    print('6. SEBARAN MODEL DIPAKAI (siapa yang gagal?)')
    print('=' * 78)
    models = re.findall(r'model=([A-Za-z0-9_./:-]+)', isi)
    print(' ', dict(Counter(models)) if models else '  (tidak ada label model)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
