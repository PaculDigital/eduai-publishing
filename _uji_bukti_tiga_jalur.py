"""BUKTI 4 HAL — jalur tiga jalur BAB. Salinan saja, produksi tak disentuh.

  (1) tabel .docx  → keluar TABEL ASLI atau cuma teks?
  (2) 3.1.1       → boleh jadi isi, TAPI BUKAN pilihan terpisah (naskah NYATA)
  (3) bab='BAB III' ujung-ke-ujung (hitung + revisi, AI DIPALSUKAN = Rp 0)
  (4) daftar bagian terdeteksi ULANG setelah berkas naskah berubah

PAKAI:
  docker exec -e APP_ROOT=/tmp/tj -e EDUAI_DATA_DIR=/tmp/tj_data \
      -e EDUAI_UPLOAD_DIR=/tmp/tj_up eduai-app python3 /tmp/_uji_bukti_tiga_jalur.py
"""
import os
import re
import sys
import time
import zipfile
from pathlib import Path

APP_ROOT = os.environ.get('APP_ROOT', '/app')
sys.path.insert(0, APP_ROOT)

_DATA = os.environ.get('EDUAI_DATA_DIR', '')
if 'uji' not in _DATA and 'tj' not in _DATA:
    print(f'STOP: EDUAI_DATA_DIR={_DATA!r} bukan salinan uji.')
    sys.exit(2)

GAGAL = []


def cek(nama, ok, info=''):
    print(('  LULUS  ' if ok else '  GAGAL  ') + nama +
          (' → ' + str(info)[:240] if info != '' else ''))
    if not ok:
        GAGAL.append(nama)


# ── umum ─────────────────────────────────────────────────────────────────
from fastapi.testclient import TestClient                                # noqa: E402
from app.main import app as APP_UTAMA                                    # noqa: E402
from app.auth import buat_token                                          # noqa: E402
from app.config import SESSION_COOKIE                                    # noqa: E402
import app.ai as AI                                                      # noqa: E402
from app.ai import _teks_dari_body, konteks_dari_bab                      # noqa: E402
from app.versi import _deteksi_bagian, ambil_bab, deteksi_bab             # noqa: E402
from app.models import User                                              # noqa: E402
from sqlalchemy import create_engine                                     # noqa: E402
from sqlalchemy.orm import sessionmaker                                  # noqa: E402

_klien = TestClient(APP_UTAMA)
_cookie = {SESSION_COOKIE: buat_token(7)}
_URL = '/api/ai/v1'
_db = sessionmaker(bind=create_engine('sqlite:///' + os.path.join(_DATA, 'eduai.db')))()
_u = _db.query(User).filter(User.id == 7).first()
NASKAH, _fb, _err = _teks_dari_body(_db, _u, {'file_id': 78})
if _err:
    print('berkas 78 tidak terbaca:', _err)
    sys.exit(3)
print(f'naskah asli: {len(NASKAH)} kar')

# ═══ (2) SUB-SUB-BAB — pakai naskah NYATA ═══════════════════════════════
print('=== (2) sub-sub-bab 3.1.1 (naskah nyata) ===')
halus = [str(b.get('label')) for b in _deteksi_bagian(NASKAH)]
besar = [str(b.get('label')) for b in deteksi_bab(NASKAH)]
pol3 = re.compile(r'\b\d+\.\d+\.\d+\b')
cek('naskah asli: TIDAK ada label tiga tingkat (3.1.1)',
    not any(pol3.search(x) for x in halus + besar), halus[:8])
cek('naskah asli: label dua tingkat (3.1) ada → deteksi bekerja',
    any(re.fullmatch(r'\d+\.\d+', x.strip()) for x in halus),
    [x for x in halus if re.fullmatch(r'\d+\.\d+', x.strip())][:6])

NASKAH_311 = NASKAH + ('\n\n3.1.1 Teknik Uji Tambahan\n\n'
                       'Paragraf pengujian tingkat tiga yang ditambahkan uji.\n')
halus2 = [str(b.get('label')) for b in _deteksi_bagian(NASKAH_311)]
besar2 = [str(b.get('label')) for b in deteksi_bab(NASKAH_311)]
cek('3.1.1 yang disisipkan TIDAK jadi pilihan terpisah',
    not any('3.1.1' in x for x in halus2 + besar2), halus2[:8])
cek('pilihan lama TIDAK hilang setelah disisip (deteksi ulang)',
    len(halus2) >= len(halus), f'{len(halus)} → {len(halus2)}')

# ═══ (3a) jalur `bab='BAB III'` di sisi mesin ═══════════════════════════
print('=== (3a) jalur BAB III di sisi mesin ===')
cek('konteks_dari_bab("BAB III") = bab (Pintu A)',
    konteks_dari_bab('BAB III') == 'bab')
_daftar_besar = deteksi_bab(NASKAH)
print(f'    deteksi_bab(naskah asli): {len(_daftar_besar)} bagian, kunci='
      + repr(sorted(_daftar_besar[0].keys())) if _daftar_besar else '    kosong')
for _b in _daftar_besar:
    _isi = _b.get('isi') or ''
    print(f"      {_b['label']}: isi={len(_isi)}kar awal=" + repr(_isi[:70]))
print('=== (2x) diagnosa posisi potongan HALUS (sub-bab) ===')
for _b in _deteksi_bagian(NASKAH):
    _isi = _b.get('isi') or ''
    _pos = NASKAH.find(_isi[:50]) if _isi else -1
    print(f"      {_b['label']}: isi={len(_isi)}kar pos={_pos} awal=" + repr(_isi[:60]))
for _tanda in ('BAB III', 'BAB IV'):
    _semua = [m for m in __import__('re').finditer(__import__('re').escape(_tanda), NASKAH)]
    print(f"    kemunculan {_tanda}: pos={[m.start() for m in _semua]}")
sebelum, isi, sesudah = ambil_bab(NASKAH, 'BAB III')
if not isi:
    #  labelnya mungkin bentuk lain (mis. 'BAB III METODE'); cari dari daftar
    for b in besar:
        if 'BAB III' in b.get('label', ''):
            sebelum, isi, sesudah = ambil_bab(NASKAH, b['label'], b.get('judul', ''))
            break
cek('isi BAB III kepotong (bukan seluruh naskah)', bool(isi) and len(isi) < len(NASKAH),
    f'{len(isi)}/{len(NASKAH)} kar')
cek('BAB III di dalam isi', 'BAB III' in isi)
cek('BAB IV TIDAK ikut di isi', 'BAB IV' not in isi)
if isi:
    print('    isi BAB III: ' + isi[:160].replace('\n', ' | ') + ' ...')
cek('BAB III + sebelum + sesudah disusun ulang = naskah utuh',
    (sebelum + isi + sesudah) == NASKAH and bool(isi),
    f'sebelum={len(sebelum)} isi={len(isi)} sesudah={len(sesudah)} kar')

# ═══ (4) ubah berkas → daftar bagian terdeteksi ulang ═══════════════════
print('=== (4) deteksi ulang setelah naskah berubah ===')
r_bab = _klien.post(f'{_URL}/bab', json={'file_id': 78}, cookies=_cookie)
lbl_sebelum = [b.get('label') for b in r_bab.json().get('bab', [])] if r_bab.status_code == 200 else []
print(f'    sebelum: {lbl_sebelum}')

from sqlalchemy import text as _sql_text
_row = _db.execute(_sql_text(
    "select user_id, nama_simpan from files where id=78")).fetchone()
_p = (Path(os.environ['EDUAI_UPLOAD_DIR']) / str(_row[0]) / _row[1]
       if _row else Path('__tidak_ada__'))
print(f'    berkas asli: {_p}')
if not _p.exists():
    _p = Path('__tidak_ada__')      #  jangan asal pilih berkas lain
if _p.exists():
    tag = '<w:p><w:r><w:t xml:space="preserve">3.9 Subbab Uji Deteksi Ulang</w:t></w:r></w:p>'
    z = zipfile.ZipFile(_p)
    isi_z = {n: z.read(n) for n in z.namelist()}
    z.close()
    xml = isi_z['word/document.xml'].decode('utf-8', 'replace')
    isi_z['word/document.xml'] = xml.replace('</w:body>', tag + '</w:body>').encode('utf-8')
    with zipfile.ZipFile(_p, 'w', zipfile.ZIP_DEFLATED) as zo:
        for n, v in isi_z.items():
            zo.writestr(n, v)
    r2 = _klien.post(f'{_URL}/bab', json={'file_id': 78}, cookies=_cookie)
    lbl_sesudah = [b.get('label') for b in r2.json().get('bab', [])] if r2.status_code == 200 else []
    print(f'    sesudah: {lbl_sesudah}')
    cek('daftar ikut terdeteksi ulang (3.9 muncul)',
        r2.status_code == 200 and any('3.9' in str(x) for x in lbl_sesudah),
        f'kode {r2.status_code}')
else:
    cek('berkas naskah ditemukan (ujian 4)', False, str(_p))

# ═══ (1)+(3b) revisi dengan AI DIPALSUKAN → takdir TABEL ════════════════
print('=== (1)+(3b) /v1/hitung + /v1/revisi (AI dipalsukan, Rp 0) ===')


def _par_terpanjang(teks):
    # naskah ini dipisah PER BARIS (bukan selalu '\n\n') → ambil baris terpanjang
    k = [p.strip() for p in re.split(r'\n+', teks) if len(p.split()) >= 12]
    return max(k, key=len) if k else ''


_PAR = _par_terpanjang(ambil_bab(NASKAH, 'BAB III')[1])   # kutip harus di DALAM bab yang diuji
_JAWAB = ('[PROFIL] Paradigma=kuantitatif; Desain=survei\n\n'
          '[K1-KUTIP-ASLI]\n' + _PAR + '\n[K1-GANTI-JADI]\n' + _PAR +
          ' (Paragraf ini sudah diperbarui.)\n\n'
          '| Variabel | Keterangan |\n|---|---|\n| X | Motivasi |\n| Y | Prestasi |\n')


async def _stubs_ai(user_msg, timeout, system=None, gambar=None):
    return _JAWAB, {'model': 'uji-stub-tanpa-biaya', 'token_in': 100, 'token_out': 40}


AI._panggil_router = _stubs_ai
print(f'    kutipan {len(_PAR)} kar dari naskah asli')

r_h = _klien.post(f'{_URL}/hitung', json={'file_id': 78, 'bab': 'BAB III'},
                  cookies=_cookie)
d_h = r_h.json() if r_h.status_code == 200 else {}
cek('/v1/hitung bab=BAB III diterima',
    r_h.status_code == 200 and d_h.get('ok') is True,
    f"kode {r_h.status_code} bab={d_h.get('bab')!r} pintu={d_h.get('konteks')!r}")

r_0 = _klien.post(f'{_URL}/hitung', json={'file_id': 78, 'bab': ''}, cookies=_cookie)
d_0 = r_0.json() if r_0.status_code == 200 else {}
cek('/v1/hitung bab kosong = jalur lama tetap jalan',
    r_0.status_code == 200 and d_0.get('ok') is True,
    f"kode {r_0.status_code} bab={d_0.get('bab')!r}")


def _jumlah_tbl(path):
    z = zipfile.ZipFile(path)
    x = z.read('word/document.xml').decode('utf-8', 'replace')
    z.close()
    return x.count('<w:tbl')


tbl_sebelum = _jumlah_tbl(_p) if _p.exists() else -1
r_r = _klien.post(f'{_URL}/revisi',
                  json={'file_id': 78, 'bab': 'BAB III',
                        'komentar': ['buatkan tabel ringkasan variabel'],
                        'tunggu': '1'},
                  cookies=_cookie)
teks_r = r_r.text[:400]
hasil = r_r.json() if r_r.status_code == 200 else {}
print(f'    /v1/revisi mode tunggu: kode {r_r.status_code} · {teks_r[:250]}')
cek('jalur bab=BAB III ujung-ke-ujung sampai selesai (mode tunggu)',
    r_r.status_code == 200 and not (hasil.get('gagal')
                                    or hasil.get('status') == 'gagal'),
    teks_r[:250])

print('=== (3c) pembanding: jalur sub-bab 1.1 (harus SUKSES) ===')
_, isi_11, _ = ambil_bab(NASKAH, '1.1')
_par11 = ''
for _l in isi_11.split('\n'):
    _l = _l.strip()
    if len(_l.split()) >= 12:
        _par11 = _l
        break
print(f'    paragraf di 1.1: {len(_par11)} kar')
_JAWAB = ('[PROFIL] Paradigma=kuantitatif; Desain=survei\n\n'
          '[K1-KUTIP-ASLI]\n' + _par11 + '\n[K1-GANTI-JADI]\n' + _par11
          + ' (Paragraf ini sudah diperbarui.)\n\n'
          '| Variabel | Keterangan |\n|---|---|\n| X | Motivasi |\n')
r2 = _klien.post(f'{_URL}/revisi',
                 json={'file_id': 78, 'bab': '1.1',
                       'komentar': ['buatkan tabel ringkasan variabel'],
                       'tunggu': '1'},
                  cookies=_cookie)
teks2 = r2.text[:400]
b2 = r2.json() if r2.status_code == 200 else {}
print(f'    /v1/revisi mode tunggu: kode {r2.status_code} · {teks2[:250]}')
cek('jalur bab="1.1" ujung-ke-ujung sampai selesai (mode tunggu)',
    r2.status_code == 200 and not (b2.get('gagal')
                                    or b2.get('status') == 'gagal'),
    teks2[:250])

tbl_sesudah = _jumlah_tbl(_p) if _p.exists() else -1
print(f'    <w:tbl> sebelum={tbl_sebelum} sesudah={tbl_sesudah}')
if tbl_sebelum >= 0:
    cek('(1) jawaban AI berbentuk tabel TIDAK menciptakan <w:tbl> baru '
        '→ "tabel" masih jadi teks, jangan dijanjikan layar',
        tbl_sesudah == tbl_sebelum, f'{tbl_sebelum} → {tbl_sesudah}')

print(f'\nRINGKAS: {len(GAGAL)} GAGAL ' +
      (', '.join(GAGAL) if GAGAL else '(semua lulus)'))
sys.exit(1 if GAGAL else 0)
