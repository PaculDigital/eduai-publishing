"""GERBANG BUKTI-bukan-TEBAPAN — 2 arah (ACC Bos 29Sep26).

A. SEHAT : cocok_bukti() hanya menyalin bukti harfiah; endpoint /v1/petunjuk
   menjaga 401 (tanpa sesi) / 403 (akun gratis) / 200 + bukti sesuai.
B. DIRUSAK: salinan parser.py dengan logika dibalik ("mesin memilih tanpa
   bukti") → gerbang ini HARUS GAGAL (exit 1). Gerbang yang tak bisa gagal
   tidak menjaga apa pun.

JALAN (salinan DB, TIDAK menyentuh produksi):
  EDUAI_DATA_DIR=/tmp/uji_bukti_data python3 _uji_bukti.py
  APP_ROOT=/tmp/bukti_rusak EDUAI_DATA_DIR=/tmp/uji_bukti_data2 \
      python3 _uji_bukti.py          # arah B — harus exit 1
"""
import os
import sys

APP_ROOT = os.path.abspath(os.getenv('APP_ROOT', '.'))
sys.path.insert(0, APP_ROOT)

LULUS: list[str] = []
GAGAL: list[str] = []


def cek(nama, kondisi, keterangan=''):
    if kondisi:
        LULUS.append(nama)
        print(f'  LULUS  {nama}' + (f' — {keterangan}' if keterangan else ''))
    else:
        GAGAL.append(nama)
        print(f'  GAGAL  {nama}' + (f' — {keterangan}' if keterangan else ''))


# ── PAGAR: hanya boleh jalan di salinan DB ────────────────────────────────
from app.config import DB_PATH                                             # noqa: E402

if 'uji' not in str(DB_PATH).casefold():
    print(f'TOLAK: DB dianggap produksi ({DB_PATH}). Pakai EDUAI_DATA_DIR salinan.')
    sys.exit(2)

from app.parser import cocok_bukti as C                                    # noqa: E402

# ── A. SEHAT ──────────────────────────────────────────────────────────────
print('=== A. cocok_bukti (aturan bukti harfiah) ===')
LB = ['BAB I PENDAHULUAN', '3.1 Metode Penelitian', 'BAB III METODE',
      '5.1 Kesimpulan', 'Lampiran Kuesioner', '2.4 Hipotesis']

cek('nomor tertulis → ada',
    [h['label'] for h in C('rapikan bagian 3.1 ya', LB)] == ['3.1 Metode Penelitian'])
cek('koma ≈ titik → tetap ada',
    len(C('rapikan 3,1 dong', LB)) == 1)
cek('judul verbatim → ada (boleh lebih dari satu yang terbukti)',
    '3.1 Metode Penelitian' in [h['label'] for h in C('ubah metode penelitian', LB)])
cek('romawi vs angka (ejaan) → ada',
    [h['label'] for h in C('perbaiki bab 3 saja', LB)] == ['BAB III METODE'])
cek('dua bukti di satu komentar → KEDUANYA tampil (mesin tidak memilihkan)',
    len(C('BAB III metode penelitian', LB)) >= 1 and len(C('BAB III', LB)) == 1)

cek('tanpa bukti → KOSONG', C('perbaiki paragraf ini', LB) == [])
cek('induk ≠ subbab → KOSONG', C('perbaiki subbab 3', LB) == [])
cek('kata umum pendek (saran) bukan bukti', C('tambahkan saran', LB) == [])
cek('komentar kosong → KOSONG', C('', LB) == [])
cek('tanpa bukti walau dekat judul (metode ≠ metode penelitian)',
    C('ubah metode', ['3.1 Metode Penelitian']) == [])
cek('bukti membawa katanya (bukan hanya label)',
    all(h.get('bukti') for h in C('rapikan bagian 3.1 ya', LB)))

# ── B. ENDPOINT /v1/petunjuk ──────────────────────────────────────────────
print('=== B. endpoint /api/ai/v1/petunjuk ===')
NASKAH = (
    'BAB I PENDAHULUAN\n\n'
    'Penelitian ini membahas pengaruh motivasi terhadap prestasi belajar '
    'mahasiswa. Latar belakang dipilih karena banyak mahasiswa mengalami '
    'penurunan motivasi selama perkuliahan daring. Rumusan masalah penelitian '
    'ini adalah bagaimana pengaruh motivasi terhadap prestasi belajar.\n\n'
    'BAB III METODE\n\n'
    'Penelitian ini menggunakan pendekatan kualitatif deskriptif. Populasi '
    'penelitian adalah mahasiswa angkatan 2022 berjumlah 120 orang. Sampel '
    'diambil dengan teknik purposive sampling. Instrumen berupa pedoman '
    'wawancara mendalam yang telah divalidasi ahli.\n\n'
    'BAB II LANDASAN TEORI\n\n'
    'Landasan teori motivasi menjelaskan bahwa dorongan dalam diri seseorang '
    'menentukan tingkah lakunya. Teori ini rujukan utama penelitian.\n')
try:
    from fastapi.testclient import TestClient
    from app.main import app as app_utama
    from app import models as M
    from app.models import Base, engine, SessionLocal
    from app.auth import buat_token
    from app.config import SESSION_COOKIE
    import asyncio

    asyncio.get_event_loop().close() if False else None
    Base.metadata.create_all(engine)
    db = SessionLocal()

    def ambil(email, paket, role='client'):
        u = db.query(M.User).filter(M.User.email == email).first()
        if not u:
            u = M.User(email=email, password_hash='$2b$12$uji', paket=paket,
                       role=role)
            db.add(u)
            db.commit()
        return u

    bayar = ambil('uji-bukti-bayar@uji.test', 'pro')
    gratis = ambil('uji-bukti-gratis@uji.test', 'gratis')

    klien = TestClient(app_utama)
    URL = '/api/ai/v1/petunjuk'
    B = {'naskah': NASKAH, 'komentar': ['perbaiki BAB III metode saja']}

    r = klien.post(URL, json=B)
    cek('tanpa sesi → 401', r.status_code == 401, f'kode {r.status_code}')

    klien.cookies.clear()
    klien.cookies.set(SESSION_COOKIE, buat_token(gratis.id))
    r = klien.post(URL, json=B)
    cek('akun gratis → 403', r.status_code == 403, f'kode {r.status_code}')

    klien.cookies.clear()
    klien.cookies.set(SESSION_COOKIE, buat_token(bayar.id))
    r = klien.post(URL, json=B)
    isi = r.json() if r.status_code == 200 else {}
    cek('akun member → 200 ok', r.status_code == 200 and isi.get('ok') is True,
        f'kode {r.status_code}')
    cek('bukti ketemu & label sesuai dokumen',
        'BAB III' in [x.get('label') for x in isi.get('cocok', [])],
        str(isi.get('cocok')))
    cek('semua yang terbukti tampil (mesin TIDAK memilihkan)',
        len(isi.get('cocok', [])) >= 1,
        str(len(isi.get('cocok', []))))

    r = klien.post(URL, json={'naskah': NASKAH,
                              'komentar': ['perbaiki paragraf ketiga']})
    cek('tanpa bukti → cocok kosong (server tidak mengarang)',
        r.status_code == 200 and r.json().get('cocok') == [],
        str(r.json().get('cocok')))

    r = klien.post(URL, json={'naskah': NASKAH,
                              'komentar': ['ganti metode jadi kualitatif']})
    cek('intent ×3 → pengali > 1 (layar menahan saran bagian)',
        r.status_code == 200 and float(r.json().get('pengali') or 1) > 1,
        str(r.json().get('pengali')))

    r = klien.post(URL, json={'naskah': NASKAH, 'komentar': []})
    cek('komentar kosong → 200 + cocok [] + jumlah_bab 0',
        r.status_code == 200 and r.json().get('cocok') == [])
    db.close()
except ImportError as e:
    print(f'  LEWAT : jalur HTTP tak tersedia ({e})')
except Exception as e:                                                     # noqa: BLE001
    GAGAL.append(f'jalur HTTP berhenti: {e!r}')
    print(f'  GAGAL  jalur HTTP berhenti: {e!r}')

print(f'\nRINGKAS: {len(LULUS)} LULUS / {len(GAGAL)} GAGAL')
sys.exit(1 if GAGAL else 0)
