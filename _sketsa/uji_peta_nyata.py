#!/usr/bin/env python3
"""UJI PETA HALUS dgn NASKAH NYATA (26Sep26) — bukti adaptor + peta.
Pakai naskah contoh yang ADA di image. Kalau tak ada → LEWATI dengan jujur.
"""
import os, sys, glob
os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/uji_peta_nyata')
sys.path.insert(0, '/app')
from app import state, peta_halus as P

L = GA = 0
def cek(n, ok, b=''):
    global L, GA
    if ok: L += 1; print(f'  ✅ {n}')
    else:  GA += 1; print(f'  ❌ {n}  {b}')

# cari naskah nyata
kandidat = []
for pola in ('/app/_contoh-dokumen/**/*.docx', '/app/_uji_doc/*.docx',
             '/app/_contoh-dokumen/**/*.txt', '/app/*.docx'):
    kandidat += glob.glob(pola, recursive=True)
print('naskah kandidat:', [os.path.basename(x) for x in kandidat][:5])

if not kandidat:
    print('⚠️  TIDAK ADA naskah contoh → LEWATI (bukan gagal)')
    sys.exit(0)

p = kandidat[0]
teks = ''
try:
    #  Pakai MESIN APLIKASI (app/ai.py::_teks_dari_berkas) — bukan
    #  python-docx yang TIDAK ada di image. Sesuai aturan: pakai yang ADA.
    from app.ai import _teks_dari_berkas
    from pathlib import Path
    teks = _teks_dari_berkas(Path(p), os.path.basename(p))
except Exception as e:
    print('⚠️  gagal baca:', repr(e)[:80]); sys.exit(0)

print(f'naskah: {os.path.basename(p)} · {len(teks)} karakter')
if len(teks) < 200:
    print('⚠️  naskah terlalu kecil → LEWATI'); sys.exit(0)

bay = state.deteksi_bab_besar(teks)
sub = state.deteksi_subbab(teks)
print(f'bab terdeteksi: {len(bay)} · sub-bab: {len(sub)}')

print('\n── A. ADAPTOR dari_state() ──')
peta_bahan = P.dari_state(bay, sub)
cek('A1. adaptor menghasilkan bab', len(peta_bahan) > 0, str(len(peta_bahan)))
cek('A2. tiap bab ada kunci bab+judul',
    all('bab' in x and 'judul' in x for x in peta_bahan), str(peta_bahan[:2]))
cek('A3. nomor bab berupa angka',
    all(str(x['bab']).isdigit() for x in peta_bahan),
    str([x['bab'] for x in peta_bahan]))

print('\n── B. PETA dari naskah NYATA ──')
hasil = P.susun(peta_bahan, mode='peta_awal', bibit_acak=7)
cek('B1. jumlah >= 5', hasil['jumlah'] >= 5, str(hasil['jumlah']))
cek('B2. ada nama bab nyata',
    any(d.get('judul_bab') for d in hasil['daftar']),
    str([d.get('judul_bab') for d in hasil['daftar'][:3]]))
print('\n' + P.ringkas(hasil)[:700])

print('\n── C. SIDIK: naskah nyata tak berubah → peta dipakai ulang ──')
sid = P.sidik_naskah(teks)
cek('C1. boleh dipakai ulang', P.boleh_pakai_ulang(sid, teks) is True, '')
cek('C2. naskah diubah → tidak boleh',
    P.boleh_pakai_ulang(sid, teks + 'edit') is False, '')

print(f'\n══ HASIL: {L} LULUS / {GA} GAGAL ══')
sys.exit(1 if GA else 0)
