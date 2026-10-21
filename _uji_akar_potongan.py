"""Uji AKAR POTONGAN — 2 arah, salinan saja, produksi tak disentuh.

ARAH SEHAT (kode baru harus lulus):
  A1 'BAB III' terpotong UTUH (bukan baris daftar isi 650 kar)
  A2 label bab besar = bab nyata (BAB I..III)
  A3 tak ada bagian yang mulai di BAGIAN PEMBUKA (daftar isi)
  A4 label halus tetap 1.1..3.2 (tidak ada pilihan hilang)
  A5 potongan 1.1 bukan baris daftar (dotted)
  A6 sebelum+isi+sesudah == teks utuh (untuk SEMUA label)
  B  regresi korpus: dokumen TANPA pembuka → hasil IDENTIK versi lama
  C  /v1/bab tetap melayani label yang sama

ARAH RUSAK (harus GAGAL — kalau lulus, uji tak bergigi):
  D1 asersi A dijalankan terhadap KODE LAMA → wajib GAGAL
  D2 suntik: _potong_pembuka dimatikan → A1 wajib GAGAL
"""
import importlib
import os
import re
import sys
import zipfile
from pathlib import Path

APP_ROOT = os.environ.get('APP_ROOT', '/app')
sys.path.insert(0, APP_ROOT)

GAGAL: list[str] = []


def cek(nama: str, ok: bool, info: str = '') -> None:
    print(('  LULUS  ' if ok else '  GAGAL  ') + nama + (' → ' + str(info) if info else ''))
    if not ok:
        GAGAL.append(nama)


from app import versi as V                                     # noqa: E402
from app.versi import (_deteksi_bagian, ambil_bab, deteksi_bab)  # noqa: E402
from app.state import awal_isi_naskah                          # noqa: E402

UPLOAD = Path(os.environ.get('EDUAI_UPLOAD_DIR', '/app/uploads'))


def teks_berkas(p: Path) -> str:
    """Teks dari extractor APLIKASI bila bisa; kalau tidak, docx mentah."""
    try:
        from app.ai import _teks_dari_berkas
        t = _teks_dari_berkas(p, p.name) or ''
        if len(t) > 500:
            return t
    except Exception as e:                                     # noqa: BLE001
        print(f'    (extractor app tidak dipakai: {e})')
    z = zipfile.ZipFile(p)
    xml = z.read('word/document.xml').decode('utf-8', 'replace')
    z.close()
    return '\n'.join(''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', b, re.S))
                     for b in re.findall(r'<w:p[ >].*?</w:p>', xml, re.S))


P78 = UPLOAD / '7' / 'f04505099df1f0a8.docx'
TEKS = teks_berkas(P78)
OFS = awal_isi_naskah(TEKS)
print(f'naskah file78: {len(TEKS)} kar · awal isi naskah = {OFS}\n')

print('=== A) KODE BARU (arah sehat) ===')
isi3 = ambil_bab(TEKS, 'BAB III')[1]
cek('A1 BAB III terpotong UTUH, bukan baris daftar isi',
    len(isi3) > 5000 and 'Hipotesis' in isi3
    and not isi3[:120].strip().endswith(('.',)) and '.....' not in isi3[:120],
    f'{len(isi3)} kar · awal={isi3[:60]!r}')
besar = deteksi_bab(TEKS)
lbl_besar = [b['label'] for b in besar]
cek('A2 label bab besar = bab nyata saja', lbl_besar == ['BAB I', 'BAB II', 'BAB III'],
    lbl_besar)
halus = _deteksi_bagian(TEKS)
cek('A3 tak ada bagian mulai di pembuka (daftar isi)',
    bool(besar + halus) and all(b['posisi'] >= OFS for b in besar + halus),
    f"min posisi={min([b['posisi'] for b in besar + halus], default=-1)} vs ofs={OFS}")
lbl_halus = [b['label'] for b in halus]
cek('A4 label halus tetap 1.1..3.2',
    lbl_halus == ['1.1', '1.2', '1.3', '1.4', '2.1', '2.2', '3.1', '3.2'], lbl_halus)
isi11 = ambil_bab(TEKS, '1.1')[1]
cek('A5 potongan 1.1 bukan baris daftar gambar',
    '.....' not in isi11[:200] and not isi11[:40].strip().startswith('Gambar'),
    f'{len(isi11)} kar · awal={isi11[:60]!r}')
identik = True
for lab in lbl_besar + lbl_halus:
    s, i, e = ambil_bab(TEKS, lab)
    if s + i + e != TEKS or not i:
        identik = False
        print(f'      putus: {lab} ({len(i)} kar)')
cek('A6 sebelum+isi+sesudah == teks utuh (semua label)', identik)

print('\n=== B) REGRESI KORPUS (dokumen lain yang terpasang) ===')
try:
    LAMA = importlib.import_module('app.versi_lama')
except Exception as e:                                        # noqa: BLE001
    LAMA = None
    print(f'    (versi_lama tidak bisa dimuat: {e})')
n_total = n_lama_sama = n_bedabaru = 0
if LAMA:
    for p in sorted(UPLOAD.glob('*/*')):
        if p.suffix.lower() not in ('.docx', '.txt', '.doc'):
            continue
        try:
            t = teks_berkas(p)
        except Exception:                                     # noqa: BLE001
            continue
        if len(t) < 500:
            continue
        n_total += 1
        o = awal_isi_naskah(t)
        def _ambil(mod, t=t):
            return ([(b['label'], b['posisi'], b['isi']) for b in mod.deteksi_bab(t)],
                    [(b['label'], b['posisi'], b['isi']) for b in mod._deteksi_bagian(t)])
        b_besar, b_halus = _ambil(V)
        l_besar, l_halus = _ambil(LAMA)
        if o == 0:
            sama = (b_besar == l_besar) and (b_halus == l_halus)
            n_lama_sama += 1 if sama else 0
            cek(f'B1 {p.name[:28]} (tanpa pembuka) IDENTIK versi lama', sama,
                f'besar {len(b_besar)}/{len(l_besar)} · halus {len(b_halus)}/{len(l_halus)}')
        else:
            # HILANGNYA label hanya sah kalau label lama itu berada di PEMBUKA
            # (hantu daftar isi) — label nyata tidak boleh lenyap.
            pos_lama = {lab: pos for lab, pos, _ in l_besar + l_halus}
            punya_baru = {lab for lab, _, _ in b_besar + b_halus}
            hilang = [lab for lab in pos_lama if lab not in punya_baru]
            hantu = [lab for lab in hilang if pos_lama[lab] < o]
            cek(f'B2 {p.name[:28]} label nyata tidak hilang',
                len(hantu) == len(hilang),
                f'hilang={hilang} · hantu-daftar={hantu} · ofs={o}')
            n_bedabaru += 1
            ubah = [x[0] for x in b_halus if x not in l_halus] or \
                   [x[0] for x in b_besar if x not in l_besar]
            print(f'    ({p.name[:30]} · ofs={o} · ada pembuka · label berubah: {ubah or "tidak"})')
print(f'    korpus: {n_total} berkas · tanpa pembuka {n_lama_sama} identik · '
      f'dengan pembuka {n_bedabaru} (diperiksa manual di atas)')

print('\n=== C) /v1/bab tetap melayani ===')
from fastapi.testclient import TestClient                       # noqa: E402
from app.auth import buat_token                                 # noqa: E402
from app.config import SESSION_COOKIE                           # noqa: E402
from app.main import app as APP_UTAMA                           # noqa: E402
_k = TestClient(APP_UTAMA)
_ck = {SESSION_COOKIE: buat_token(7)}
r = _k.post('/api/ai/v1/bab', json={'file_id': 78}, cookies=_ck)
lbl_api = [b.get('label') for b in (r.json() or {}).get('bab', [])] if r.status_code == 200 else []
cek('C1 /v1/bab 200 + label halus sama dengan mesin',
    r.status_code == 200 and lbl_api == lbl_halus, f'{r.status_code} {lbl_api}')

print('\n=== D) ARAH RUSAK (harus GAGAL) ===')
d1_gagal: list[str] = []
for lab, sumber in (('BAB III', LAMA), ('1.1', LAMA)):
    if not sumber:
        continue
    if lab == 'BAB III':
        isi = sumber.ambil_bab(TEKS, lab)[1]
        ok = len(isi) > 5000 and 'Hipotesis' in isi
    else:
        isi = sumber.ambil_bab(TEKS, lab)[1]
        ok = '.....' not in isi[:200]
    print(f'  {"lulus" if ok else "gagal"}  D1-lama {lab} ({len(isi)} kar)')
    if ok:
        d1_gagal.append(lab)
cek('D1 KODE LAMA harus TIDAK lolos asersi A (uji bergigi)',
    bool(d1_gagal) is False and bool(LAMA),
    f'lolos padahal salah: {d1_gagal}')

_asli = V._potong_pembuka
V._potong_pembuka = lambda t: (0, t)          # suntik: potongan dimatikan
isi_rusak = ambil_bab(TEKS, 'BAB III')[1]
besar_rusak = [b['label'] for b in deteksi_bab(TEKS)]
V._potong_pembuka = _asli
d2_ok = not (len(isi_rusak) > 5000 and 'Hipotesis' in isi_rusak)
print(f'    suntik mati: BAB III = {len(isi_rusak)} kar, label={besar_rusak}')
cek('D2 suntik mematikan potongan → A1 jadi GAGAL (bergigi)', d2_ok)

print(f'\nRINGKAS: {len(GAGAL)} GAGAL ' + (', '.join(GAGAL) if GAGAL else '(semua lulus)'))
sys.exit(1 if GAGAL else 0)
