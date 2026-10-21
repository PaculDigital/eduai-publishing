"""PERIKSA PAGAR C10 di ai.py — dijalankan DI DALAM container.

KENAPA TERPISAH: pagar ini tidak bisa diuji dari luar lewat teks kode.
    ⚠️ PELAJARAN (2× gagal): asersi yang mencari teks `log.error('[ai] C10...`
    + `raise HTTPException(503)` SELALU LULUS — sebab yang merusak pagar adalah
    `if False:` di DEPANNYA, sementara teksnya tetap terbaca. ⇒ Satu-satunya cara
    jujur: POTONG potongan pagar itu dari berkas, JALANKAN, dan pastikan ia
    benar-benar melempar HTTPException 503.
"""
import os
import re
import sys
import tempfile

_t = tempfile.mkdtemp(prefix='c10f_')
os.environ['EDUAI_DATA_DIR'] = _t
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(_t, 'up')
sys.path.insert(0, '/app')

from fastapi import HTTPException  # noqa: E402

src = open('/app/app/ai.py', encoding='utf-8').read()

#  Ambil BLOK pagar C10 berdasarkan BARIS (bukan regex rapuh):
#  mulai dari `if not (konten or '').strip():` yang diikuti penanda C10,
#  sampai baris `        })` penutup `raise HTTPException(503, detail={...})`.
baris = src.split('\n')
mulai = None
for i, b in enumerate(baris):
    if b.strip() == "if not (konten or '').strip():" and \
            "C10" in '\n'.join(baris[i:i + 4]):
        mulai = i
        break
if mulai is None:
    print('HASIL: PAGAR-TIDAK-DITEMUKAN')
    sys.exit(0)

akhir = None
for j in range(mulai + 1, min(mulai + 30, len(baris))):
    if baris[j].strip() == '})':
        akhir = j
        break
if akhir is None:
    print('HASIL: PENUTUP-TIDAK-DITEMUKAN')
    sys.exit(0)

blok_asli = baris[mulai:akhir + 1]
#  ⚠️ JANGAN dedent: blok asli ber-indentasi 4 spasi, dan di dalam
#  `def _cek()` (level 1) isi fungsi memang harus 4 spasi. Dedent membuat
#  blok keluar dari fungsi → `SyntaxError: 'return' outside function`.
blok = '\n'.join(blok_asli)

kode = (
    "def _cek(konten, fb, bab):\n"
    "    class _Log:\n"
    "        def error(self, *a, **k):\n"
    "            pass\n"
    "    log = _Log()\n"
) + blok + "\n    return 'LOLOS-TANPA-GALAT'\n"

ns = {'HTTPException': HTTPException}
try:
    exec(kode, ns)                                             # noqa: S102
except SyntaxError as e:
    print(f'HASIL: SYNTAX-ERROR {e}')
    sys.exit(0)

try:
    hasil = ns['_cek']('', None, 'BAB I')
    print('HASIL: LOLOS', hasil)
except HTTPException as e:
    print('HASIL: HTTPException', e.status_code)
except Exception as e:                                         # noqa: BLE001
    print(f'HASIL: LAIN {type(e).__name__}: {e}')
