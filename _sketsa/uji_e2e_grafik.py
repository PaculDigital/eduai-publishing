#!/usr/bin/env python3
"""UJI E2E SAMBUNGAN GRAFIK — lewat JALUR PRODUKSI (_revisi_kerja).

DB SEMENTARA (jangan sentuh produksi) + AI NYATA (9router combo EduAi).
Yang diperiksa: apakah revisi dengan permintaan grafik MENGHASILKAN
gambar TERSISIP di .docx + kalimat penjelas + token ×2.
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

#  ⚠️ SET SEBELUM IMPOR app.* (jangan sentuh DB produksi)
_tmp = tempfile.mkdtemp(prefix='uji_gbr_')
os.environ['EDUAI_DATA_DIR'] = _tmp
os.environ['EDUAI_UPLOAD_DIR'] = f'{_tmp}/uploads'
os.environ['EDUAI_DB'] = f'{_tmp}/uji.sqlite3'
print(f'DB sementara: {_tmp}')

sys.path.insert(0, '/app')
import asyncio                                                # noqa: E402

from app import ai as A                                       # noqa: E402
from app.models import (Base, FileBerkas, User, engine,        # noqa: E402
                        init_db, SessionLocal)
from app import kuota as KQ                                   # noqa: E402

print('  modul ai.py dimuat:', A.__file__)

Path(os.environ['EDUAI_UPLOAD_DIR']).mkdir(parents=True, exist_ok=True)
init_db()
db = SessionLocal()

u = User(email='uji-grafik@test.local', nama='Uji Grafik',
         role='client', aktif=True)
from app.auth import hash_password as _hp
u.password_hash = _hp('rahasia123')
db.add(u)
db.commit()
print(f'  user id={u.id} · role={u.role}')

sumber = Path('/app/_naskah_bos_uji.docx')
tujuan = Path(os.environ['EDUAI_UPLOAD_DIR']) / str(u.id)
tujuan.mkdir(parents=True, exist_ok=True)
nama_simpan = 'naskah_uji_grafik.docx'
shutil.copy(sumber, tujuan / nama_simpan)
ukuran_awal = (tujuan / nama_simpan).stat().st_size

fb = FileBerkas(user_id=u.id, nama='naskah_uji_grafik.docx',
                nama_simpan=nama_simpan, ukuran=ukuran_awal)
db.add(fb)
db.commit()
print(f'  berkas id={fb.id} · {ukuran_awal:,} byte')

#  beri kuota (lewat AddOn — sistem satu pintu)
try:
    daftar_paket = getattr(KQ, 'PAKET_ADDON', None)
    print(f'  paket AddOn tersedia: {list(daftar_paket)[:4] if daftar_paket else "—"}')
    #  pakai fungsi yang ada: tambah pemakaian AddOn langsung ke DB
    from app.models import PemakaianAI
    import datetime as _dt
    bln = KQ.bulan_sekarang()
    pk = db.query(PemakaianAI).filter_by(user_id=u.id, bulan=bln).first()
    if pk is None:
        pk = PemakaianAI(user_id=u.id, bulan=bln)
        db.add(pk)
        db.commit()
    print(f'  pemakaian id={pk.id} · bulan={bln}')
except Exception as e:                                        # noqa: BLE001
    import traceback
    print(f'  ⚠️ siapkan kuota: {e}')
    traceback.print_exc()

KOMENTAR = ['Bu, pada bagian ini saya perlu grafik pertumbuhan GDP '
            '2015-2018 agar polanya terlihat. Datanya: 2015 = 30; '
            '2016 = 34; 2017 = 38; 2018 = 42 (satuan persen, sumber BPS).']

print()
print('  ── JALANKAN _revisi_kerja (AI NYATA) ──')


class _ReqTiruan:
    """Request tiruan — `_revisi_kerja` membaca body JSON dari sini."""

    def __init__(self, payload: dict):
        self._p = payload

    async def json(self):
        return self._p


hasil = None
try:
    hasil = asyncio.run(A._revisi_kerja(
        _ReqTiruan({'file_id': fb.id, 'bab': '1.5', 'komentar': KOMENTAR}),
        u, db, None))
except Exception as e:                                        # noqa: BLE001
    import traceback
    print(f'  ❌ GAGAL: {type(e).__name__}: {e}')
    traceback.print_exc()

print()
if hasil:
    print(f'  ok        : {hasil.get("ok")}')
    print(f'  bagian    : {hasil.get("bagian")}')
    print(f'  token_rev : {hasil.get("token_revisi")}')
    print(f'  gambar    : {hasil.get("gambar")}')
    print(f'  catatan   : {hasil.get("catatan_gambar")}')
    print()
    print('  ── jawaban (400 kar pertama) ──')
    print(f'  {str(hasil.get("jawaban"))[:400]}')
    print()

    ukuran_akhir = (tujuan / nama_simpan).stat().st_size
    print(f'  berkas: {ukuran_awal:,} → {ukuran_akhir:,} byte '
          f'({ukuran_akhir - ukuran_awal:+,})')

    import zipfile
    with zipfile.ZipFile(tujuan / nama_simpan) as z:
        d = z.read('word/document.xml').decode('utf-8')
        media = [n for n in z.namelist() if 'media/' in n]
        print(f'  media   : {len(media)} berkas · {[m.split("/")[-1] for m in media]}')
        print(f'  drawing : {d.count("<w:drawing>")}')
        print(f'  tabel   : {d.count("<w:tbl>")}')
    teks2 = A._teks_dari_berkas(tujuan / nama_simpan, 'x.docx')
    print(f'  terbaca : {len(teks2):,} kar · [[GAMBAR- {teks2.count("[[GAMBAR-")}')

    print()
    print('  ══ KESIMPULAN ══')
    ada_gbr = bool(hasil.get('gambar'))
    print(f'    1. grafik disisipkan     : {"✅" if ada_gbr else "❌"}')
    print(f'    2. berkas BERTAMBAH besar: '
          f'{"✅" if ukuran_akhir > ukuran_awal else "❌"}')
    print(f'    3. tabel tetap 7         : '
          f'{"✅" if d.count("<w:tbl>") == 7 else "❌"}')
    print(f'    4. token ×2 (BUAT_GRAFIK): '
          f'{"✅" if (hasil.get("token_revisi") or 0) >= 2 else "❌"} '
          f'({hasil.get("token_revisi")})')
    print(f'    5. tidak ada penanda mesin di jawaban: '
          f'{"✅" if "DATA-GRAFIK" not in str(hasil.get("jawaban")) else "❌"}')
