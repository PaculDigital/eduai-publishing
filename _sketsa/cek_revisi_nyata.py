"""Uji jalur revisi dengan NASKAH SUNGGUHAN (file 47) — tanpa menyentuh produksi.

KENAPA: proses id 94/95 gagal 1 detik, token 0, padahal 9router HIDUP.
    Harus diketahui: yang kosong itu JAWABAN AI, atau yang dibuang oleh
    `bersihkan_jawaban_ai()`.

MEMAKAI DB SEMENTARA + panggil `_revisi_dengan_failover` apa adanya.
"""
import asyncio
import os
import sqlite3
import sys
import tempfile
import time

_t = tempfile.mkdtemp(prefix='c7_')
os.environ['EDUAI_DATA_DIR'] = _t
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(_t, 'up')
sys.path.insert(0, '/app')

from app import ai as A                                        # noqa: E402

#  Ambil naskah file 47 dari DB produksi (HANYA BACA).
c = sqlite3.connect('/app/data/eduai.db')
c.row_factory = sqlite3.Row
row = c.execute('select isi from versi_dokumen where file_id=47 '
                "and nomor=57").fetchone()
naskah = row['isi'] if row else ''
c.close()
print(f'  naskah file 47 v57 = {len(naskah):,} kar')

#  Bangun pesan seperti app membangunnya (tanpa riwayat/ingatan).
prompt = (
    'Kamu editor naskah akademik. Perbaiki naskah sesuai komentar.\n\n'
    'KOMENTAR:\n[K1] Perbaiki tata bahasa dan ejaan paragraf.\n\n'
    'NASKAH:\n' + naskah + '\n\n'
    'ATURAN: balas HANYA naskah hasil perbaikan, awali dengan penanda [K1]. '
    'JANGAN menyalin naskah apa adanya — wajib ada perubahan.'
)
print(f'  panjang pesan = {len(prompt):,} kar')
print('\n── panggil _revisi_dengan_failover (SUNGGUHAN) ──')

t0 = time.monotonic()
try:
    konten, model, info = asyncio.run(
        A._revisi_dengan_failover(prompt, 1, naskah_banding=naskah))
    dt = time.monotonic() - t0
    print(f'  ✅ jawaban {len(konten):,} kar · model={model!r} · {dt:.1f} dtk')
    print(f'  token: in={info.get("token_in")} out={info.get("token_out")}')
    print(f'\n  --- 300 kar pertama ---\n  {konten[:300]}')
except Exception as e:                                         # noqa: BLE001
    dt = time.monotonic() - t0
    print(f'  ❌ GAGAL ({dt:.1f} dtk) → {type(e).__name__}: {str(e)[:400]}')
