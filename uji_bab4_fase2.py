"""
Uji Fase 2 BAB IV (21 Okt 2026):
  1. Layanan hasil: versi naik, Kunci Hasil membekukan yang terbaru,
     hanya satu terkunci, tarif generate 0 (jatah) lalu 5 token.
  2. Klien jembatan: kunci kosong → gagal jujur; 200 → hasil; 401/503/400
     diterjemahkan; timeout → pesan waktu.
  3. Mesin aturan peta: model mediasi sah (contoh Nura, 7 jalur) lolos;
     peta rusak (tanpa bukti, perantara terputus, jumlah tak sama,
     penguat tanpa interaksi) ketahuan; label desain dari fakta.

Jalankan dari akar repo (env boneka wajib untuk config):
  EDUAI_SECRET_KEY=x EDUAI_ROUTER_KEY=x python uji_bab4_fase2.py
"""
import sys

sys.path.insert(0, '.')

gagal = []


def cek(nama, kondisi, detail=''):
    print(('  ✓ ' if kondisi else '  ✗ GAGAL ') + nama +
          (f' — {detail}' if detail and not kondisi else ''))
    if not kondisi:
        gagal.append(nama)


print('── 1. Layanan hasil (versi + Kunci Hasil + tarif) ──')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, HasilBab4, PetaBab4
from app import bab4

eng = create_engine('sqlite://')
Base.metadata.create_all(eng, tables=[HasilBab4.__table__, PetaBab4.__table__])
db = sessionmaker(bind=eng)()

v1 = bab4.simpan_hasil(db, 1, 10, 'olah_data', 'spss', {'r2': 0.5})
v2 = bab4.simpan_hasil(db, 1, 10, 'olah_data', 'spss', {'r2': 0.6})
cek('nomor versi naik 1→2', (v1.nomor, v2.nomor) == (1, 2))
cek('tarif: generate ke-3 masih gratis',
    bab4.tarif_generate_berikutnya(db, 1, 10) == 0)
bab4.simpan_hasil(db, 1, 10, 'olah_data', 'spss', {'r2': 0.7})
bab4.simpan_hasil(db, 1, 10, 'olah_data', 'spss', {'r2': 0.8})
cek('tarif: sesudah 1+3 gratis → 5 token',
    bab4.tarif_generate_berikutnya(db, 1, 10) == 5)
k1 = bab4.kunci_hasil(db, 1, 10)
cek('kunci membekukan versi terbaru (4)',
    k1 is not None and k1.nomor == 4 and k1.status == 'terkunci')
v5 = bab4.simpan_hasil(db, 1, 10, 'olah_data', 'spss', {'r2': 0.9})
k2 = bab4.kunci_hasil(db, 1, 10)
terkunci = (db.query(HasilBab4).filter_by(status='terkunci').all())
cek('hanya SATU terkunci & itu versi 5',
    len(terkunci) == 1 and terkunci[0].nomor == 5 and k2.nomor == 5)
cek('hasil terkunci terbaca utuh',
    bab4.baca_hasil(bab4.hasil_terkunci(db, 1, 10)) == {'r2': 0.9})
cek('pra_survei dihitung terpisah dari olah_data',
    bab4.jumlah_generate(db, 1, 10, 'pra_survei') == 0)

print('── 2. Klien jembatan ──')
import httpx
from app import jembatan_statistik as js

asli_client = httpx.Client


def pabrik_client(penangan):
    def buat(*a, **k):
        k.pop('timeout', None)
        return asli_client(transport=httpx.MockTransport(penangan))
    return buat


try:
    js.kunci = lambda: ''                       # noqa: E731 — uji kunci kosong
    try:
        js.hitung({'baris': []})
        cek('kunci kosong → GagalJembatan', False)
    except js.GagalJembatan as e:
        cek('kunci kosong → GagalJembatan', 'belum dipasang' in e.pesan)

    js.kunci = lambda: 'kunci-uji'              # noqa: E731
    js.httpx.Client = pabrik_client(lambda r: httpx.Response(200, json={'r2': 1}))
    cek('200 → hasil dict', js.hitung({'baris': [{}]}) == {'r2': 1})
    js.httpx.Client = pabrik_client(lambda r: httpx.Response(401, json={}))
    try:
        js.hitung({'baris': [{}]}); cek('401 → pesan kunci ditolak', False)
    except js.GagalJembatan as e:
        cek('401 → pesan kunci ditolak', e.status == 401)
    js.httpx.Client = pabrik_client(
        lambda r: httpx.Response(400, json={'detail': 'Kolom "A" memegang dua peran.'}))
    try:
        js.hitung({'baris': [{}]}); cek('400 → detail mesin diteruskan', False)
    except js.GagalJembatan as e:
        cek('400 → detail mesin diteruskan', 'dua peran' in e.pesan)

    def lambat(r):
        raise httpx.ReadTimeout('pelan', request=r)
    js.httpx.Client = pabrik_client(lambat)
    try:
        js.hitung({'baris': [{}]}); cek('timeout → status waktu', False)
    except js.GagalJembatan as e:
        cek('timeout → status waktu', e.status == 'waktu')
finally:
    js.httpx.Client = asli_client

print('── 3. Mesin aturan peta ──')
B = 'kalimat bukti dari naskah'
peta_sah = {
    'jenis': 'kuantitatif', 'jumlah_hipotesis': 7, 'target_sampel': 100,
    'variabel': [
        {'nama': 'Keaslian Streamer', 'peran': 'X', 'bukti': B, 'indikator': []},
        {'nama': 'Interaksi Parasosial', 'peran': 'X', 'bukti': B, 'indikator': []},
        {'nama': 'Keterlibatan Pelanggan', 'peran': 'M', 'bukti': B, 'indikator': []},
        {'nama': 'Pembelian Impulsif', 'peran': 'Y', 'bukti': B, 'indikator': []},
    ],
    'jalur': [
        {'dari': 'Keaslian Streamer', 'ke': 'Keterlibatan Pelanggan', 'hipotesis': 'H1', 'jenis': 'langsung'},
        {'dari': 'Interaksi Parasosial', 'ke': 'Keterlibatan Pelanggan', 'hipotesis': 'H2', 'jenis': 'langsung'},
        {'dari': 'Keterlibatan Pelanggan', 'ke': 'Pembelian Impulsif', 'hipotesis': 'H3', 'jenis': 'langsung'},
        {'dari': 'Keaslian Streamer', 'ke': 'Pembelian Impulsif', 'hipotesis': 'H4', 'jenis': 'langsung'},
        {'dari': 'Interaksi Parasosial', 'ke': 'Pembelian Impulsif', 'hipotesis': 'H5', 'jenis': 'langsung'},
        {'dari': 'Keaslian Streamer', 'ke': 'Pembelian Impulsif', 'hipotesis': 'H6', 'jenis': 'tidak_langsung'},
        {'dari': 'Interaksi Parasosial', 'ke': 'Pembelian Impulsif', 'hipotesis': 'H7', 'jenis': 'tidak_langsung'},
    ],
}
cek('model mediasi Nura (7 jalur) LOLOS', bab4.periksa_peta(peta_sah) == [],
    str(bab4.periksa_peta(peta_sah)))

import copy
p = copy.deepcopy(peta_sah); p['variabel'][0]['bukti'] = None
cek('tanpa bukti → masalah tanpa_bukti',
    any(m['kode'] == 'tanpa_bukti' for m in bab4.periksa_peta(p)))
p = copy.deepcopy(peta_sah); p['jumlah_hipotesis'] = 6
cek('jalur ≠ hipotesis → masalah jumlah_tak_sama',
    any(m['kode'] == 'jumlah_tak_sama' for m in bab4.periksa_peta(p)))
p = copy.deepcopy(peta_sah)
p['jalur'] = [j for j in p['jalur'] if not (j['ke'] == 'Keterlibatan Pelanggan')]
p['jumlah_hipotesis'] = len(p['jalur'])
cek('perantara tanpa jalur masuk → perantara_terputus',
    any(m['kode'] == 'perantara_terputus' for m in bab4.periksa_peta(p)))
p = {'jenis': 'kuantitatif', 'jumlah_hipotesis': 2,
     'variabel': [{'nama': 'Harga', 'peran': 'X', 'bukti': B},
                  {'nama': 'Kepuasan', 'peran': 'Z', 'bukti': B},
                  {'nama': 'Loyalitas', 'peran': 'Y', 'bukti': B}],
     'jalur': [{'dari': 'Harga', 'ke': 'Loyalitas', 'hipotesis': 'H1', 'jenis': 'langsung'},
               {'dari': 'Kepuasan', 'ke': 'Loyalitas', 'hipotesis': 'H2', 'jenis': 'langsung'}]}
cek('penguat tanpa interaksi → penguat_tanpa_interaksi',
    any(m['kode'] == 'penguat_tanpa_interaksi' for m in bab4.periksa_peta(p)))
p['jalur'][1]['jenis'] = 'interaksi'
cek('penguat + interaksi → lolos', bab4.periksa_peta(p) == [])
cek('desain: perlakuan+kontrol = eksperimen',
    bab4.label_desain({'perlakuan': True, 'kelompok_kontrol': True})['desain'] == 'eksperimen')
cek('desain: sekali sebar = survei',
    bab4.label_desain({'sekali_sebar': True})['desain'] == 'survei')
cek('desain: fakta kosong = belum_jelas',
    bab4.label_desain({})['desain'] == 'belum_jelas')
cek('peta kualitatif tanpa informan → masalah',
    any(m['kode'] == 'informan_kosong' for m in bab4.periksa_peta(
        {'jenis': 'kualitatif', 'fokus': [{'nama': 'Pengalaman', 'bukti': B}]})))

print()
if gagal:
    print(f'❌ {len(gagal)} GAGAL: {gagal}')
    sys.exit(1)
print('✅ SEMUA LULUS — Fase 2 fondasi')
