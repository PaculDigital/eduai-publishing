"""Uji Fase 3: rute BAB IV ujung-ke-ujung.

App FastAPI kecil memuat app/bab4_rute.py ASLI; login & db diganti
(sqlite memori + user boneka) — pola menimpa dependensi FastAPI.
Mesin hitung = server Statistik Lab lokal berkode Fase 1 (kunci e2e).
Jalan: EDUAI_STATISTIK_URL=http://127.0.0.1:8799 \
       EDUAI_STATISTIK_KUNCI=kunci-e2e EDUAI_SECRET_KEY=x \
       EDUAI_ROUTER_KEY=x python uji_bab4_fase3.py
"""
import sys, types, json
sys.path.insert(0, '.')
import numpy as np
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import (Base, DataLapanganBab4, FileBerkas, HasilBab4,
                        PetaBab4, User)
from app import bab4_rute
from app.auth import wajib_login_api
from app.models import get_db

gagal = []
def cek(nama, kondisi, info=''):
    print(('  ✓ ' if kondisi else '  ✗ GAGAL ') + nama +
          ('' if kondisi else f' → {info}'))
    if not kondisi:
        gagal.append(nama)

from sqlalchemy.pool import StaticPool
eng = create_engine('sqlite://', connect_args={'check_same_thread': False},
                    poolclass=StaticPool)
Base.metadata.create_all(eng)  # semua tabel: relasi FileBerkas ikut dimuat rute
Sesi = sessionmaker(bind=eng)
db0 = Sesi()
db0.add(User(id=1, email='uji@contoh.id', nama='Penguji', password_hash='x'))
db0.add(FileBerkas(id=10, user_id=1, nama='skripsi-uji.docx', nama_simpan='skripsi-uji.docx', ukuran=100))
db0.commit(); db0.close()

def _db():
    s = Sesi()
    try:
        yield s
    finally:
        s.close()

app = FastAPI()
app.include_router(bab4_rute.router)
app.dependency_overrides[wajib_login_api] = lambda: types.SimpleNamespace(id=1)
app.dependency_overrides[get_db] = _db
k = TestClient(app, raise_server_exceptions=False)
H = {'Content-Type': 'application/json'}

B = [{'kalimat': 'ditemukan di naskah', 'bab': 'III'}]
peta = {
    'jenis': 'kuantitatif', 'metode': 'PLS-SEM', 'jumlah_hipotesis': 3,
    'variabel': [
        {'nama': 'Keaslian Streamer', 'peran': 'X', 'bukti': B,
         'indikator': ['Streamer tampil apa adanya.', 'Streamer jujur soal produk.']},
        {'nama': 'Keterlibatan Pelanggan', 'peran': 'M', 'bukti': B,
         'indikator': ['Saya aktif berkomentar.', 'Saya merasa terlibat.']},
        {'nama': 'Pembelian Impulsif', 'peran': 'Y', 'bukti': B,
         'indikator': ['Saya membeli tanpa rencana.', 'Saya tergoda membeli.']},
    ],
    'jalur': [
        {'dari': 'Keaslian Streamer', 'ke': 'Keterlibatan Pelanggan',
         'hipotesis': 'H1', 'jenis': 'langsung'},
        {'dari': 'Keterlibatan Pelanggan', 'ke': 'Pembelian Impulsif',
         'hipotesis': 'H2', 'jenis': 'langsung'},
        {'dari': 'Keaslian Streamer', 'ke': 'Pembelian Impulsif',
         'hipotesis': 'H3', 'jenis': 'tidak_langsung',
         'lewat': 'Keterlibatan Pelanggan'},
    ],
}

print('── Rute BAB IV ujung-ke-ujung ──')
r = k.post('/api/bab4/peta', json={'file_id': 10, 'peta': peta}, headers=H)
cek('POST /peta tersimpan tanpa masalah', r.status_code == 200 and r.json()['masalah'] == [], r.text[:150])
r = k.post('/api/bab4/peta/sahkan', json={'file_id': 10}, headers=H)
cek('POST /peta/sahkan → disahkan', r.status_code == 200 and r.json()['status'] == 'disahkan', r.text[:150])
r = k.get('/api/bab4/instrumen', params={'file_id': 10})
kolom = r.json()['kolom_template']
cek('GET /instrumen → 6 kolom pola mesin', kolom == [
    'Keaslian_Streamer_1', 'Keaslian_Streamer_2',
    'Keterlibatan_Pelanggan_1', 'Keterlibatan_Pelanggan_2',
    'Pembelian_Impulsif_1', 'Pembelian_Impulsif_2'], str(kolom))
r = k.get('/api/bab4/instrumen/template.csv', params={'file_id': 10})
cek('unduh template.csv berisi kepala kolom', r.status_code == 200 and 'Keaslian_Streamer_1' in r.text, r.text[:80])

rng = np.random.default_rng(5)
def buat(n, sampah=False):
    x = rng.normal(size=n); m = 0.7*x + rng.normal(scale=0.6, size=n)
    y = 0.6*m + rng.normal(scale=0.6, size=n)
    def lik(v, k=0.4): return np.clip(np.round(3 + v + rng.normal(scale=k, size=n)), 1, 5).astype(int)
    baris = []
    for i in range(n):
        baris.append([int(lik(x)[i]), int(lik(x)[i]), int(lik(m)[i]),
                      int(lik(m)[i]), int(lik(y)[i]),
                      int(rng.integers(1, 6)) if sampah else int(lik(y)[i])])
    return baris

r = k.put('/api/bab4/data', json={'file_id': 10, 'tahap': 'pra',
          'kolom': kolom, 'baris': buat(25, sampah=True)}, headers=H)
cek('PUT data pra (25 baris)', r.status_code == 200, r.text[:120])
r = k.post('/api/bab4/pra-survei', json={'file_id': 10}, headers=H)
j = r.json() if r.status_code == 200 else {}
cek('POST /pra-survei → kartu kesehatan keluar', r.status_code == 200 and 'per_variabel' in j.get('kartu', {}), r.text[:200])
cek('butir sampah Pembelian_Impulsif_2 terdeteksi lemah',
    any('Pembelian_Impulsif_2' == b.get('butir') or 'Pembelian_Impulsif_2' in str(b)
        for b in j.get('kartu', {}).get('butir_lemah', [])), str(j.get('kartu', {}).get('butir_lemah')))

r = k.put('/api/bab4/data', json={'file_id': 10, 'tahap': 'utama',
          'kolom': kolom, 'baris': buat(60), 'target_responden': 80}, headers=H)
cek('PUT data utama (60 baris, target 80)', r.status_code == 200, r.text[:120])
r = k.post('/api/bab4/olah-data', json={'file_id': 10}, headers=H)
j = r.json() if r.status_code == 200 else {}
cek('POST /olah-data → versi 1, tarif 0 (jatah paket)', r.status_code == 200 and j.get('versi') == 1 and j.get('tarif_dikenakan') == 0, r.text[:250])
r = k.post('/api/bab4/kunci-hasil', json={'file_id': 10}, headers=H)
cek('POST /kunci-hasil → versi 1 terkunci', r.status_code == 200 and r.json().get('versi_terkunci') == 1, r.text[:150])
r = k.post('/api/bab4/kunci-hasil', json={'file_id': 10}, headers=H)
cek('kunci-hasil kedua tanpa data baru → 409 (BUG 1 tidak kambuh di rute)', r.status_code == 409, str(r.status_code))
r = k.get('/api/bab4/ringkasan', params={'file_id': 10})
cek('ringkasan: terkunci=1, data utama 60 baris', r.json().get('versi_terkunci') == 1 and r.json()['data']['utama']['baris'] == 60, r.text[:200])
r = k.get('/api/bab4/instrumen', params={'file_id': 999})
cek('berkas bukan milik → 404', r.status_code == 404, str(r.status_code))

print('── Regresi 5 bug review Fase 3 ──')
from app import bab4 as _b4, bab4_rute as _br, jembatan_statistik as _jb
from app.models import HasilBab4 as _HB

# BUG 3 (unit): Harga vs Harga Diskon — tak boleh tertukar
pl = _b4.susun_payload_hitung(
    {'metode': 'Regresi', 'variabel': [
        {'nama': 'Harga', 'peran': 'X'}, {'nama': 'Harga Diskon', 'peran': 'Y'}],
     'jalur': []},
    ['Harga_1', 'Harga_2', 'Harga_Diskon_1', 'Harga_Diskon_2'])
cek('BUG3 peran kolom Harga murni X1, Diskon murni Y1',
    pl['peran'] == {'Harga_1': 'X1', 'Harga_2': 'X1',
                    'Harga_Diskon_1': 'Y1', 'Harga_Diskon_2': 'Y1'},
    str(pl.get('peran')))
cek('BUG1 payload SPSS tanpa kolom_y daftar', 'kolom_y' not in pl and 'kolom_x' not in pl)

# BUG 4-5 (unit): jumlah_butir aneh
ins = _b4.buat_instrumen({'variabel': [
    {'nama': 'Aneh', 'peran': 'X', 'jumlah_butir': -3},
    {'nama': 'Teks', 'peran': 'Y', 'jumlah_butir': 'abc'},
    {'nama': 'Normal', 'peran': 'Y', 'jumlah_butir': 3}]})
cek('BUG4-5 jumlah_butir -3/abc jatuh aman (4), normal tetap 3',
    [len(b['butir']) for b in ins['kuesioner']] == [4, 4, 3],
    str([len(b['butir']) for b in ins['kuesioner']]))

# BUG 1 (e2e): peta SPSS mediasi di berkas kedua
db1 = Sesi(); db1.add(FileBerkas(id=11, user_id=1, nama='spss.docx',
                                 nama_simpan='spss.docx', ukuran=10)); db1.commit(); db1.close()
peta_spss = {'jenis': 'kuantitatif', 'metode': 'Regresi', 'jumlah_hipotesis': 3,
             'variabel': [
                 {'nama': 'Kualitas', 'peran': 'X', 'bukti': B,
                  'indikator': ['Produk awet.', 'Produk rapi.']},
                 {'nama': 'Kepuasan', 'peran': 'M', 'bukti': B,
                  'indikator': ['Saya puas.', 'Sesuai harapan.']},
                 {'nama': 'Minat', 'peran': 'Y', 'bukti': B,
                  'indikator': ['Beli lagi.', 'Rekomendasi.']}],
             'jalur': [
                 {'dari': 'Kualitas', 'ke': 'Kepuasan', 'hipotesis': 'H1', 'jenis': 'langsung'},
                 {'dari': 'Kepuasan', 'ke': 'Minat', 'hipotesis': 'H2', 'jenis': 'langsung'},
                 {'dari': 'Kualitas', 'ke': 'Minat', 'hipotesis': 'H3', 'jenis': 'langsung'}]}
r = k.post('/api/bab4/peta', json={'file_id': 11, 'peta': peta_spss}, headers=H)
r2 = k.post('/api/bab4/peta/sahkan', json={'file_id': 11}, headers=H)
kolom2 = k.get('/api/bab4/instrumen', params={'file_id': 11}).json()['kolom_template']
k.put('/api/bab4/data', json={'file_id': 11, 'tahap': 'utama',
      'kolom': kolom2, 'baris': buat(60)}, headers=H)
r = k.post('/api/bab4/olah-data', json={'file_id': 11}, headers=H)
j = r.json() if r.status_code == 200 else {}
cek('BUG1 olah data SPSS (mediasi) JALAN — versi 1 terbit',
    r.status_code == 200 and j.get('versi') == 1, r.text[:250])
cek('BUG1 hasil SPSS memuat angka (r2/koefisien)',
    bool(j.get('hasil')) and ('r2' in str(j['hasil'])[:2000] or 'koef' in str(j['hasil'])[:2000]),
    str(j.get('hasil'))[:200])

# BUG 2 (unit rute): mesin gagal → token 5 kembali
db2 = Sesi()
for i in range(4):
    db2.add(_HB(user_id=1, file_id=11, jenis='olah_data', mode='spss',
                nomor=i + 1, status='draf', hasil='{}'))
db2.commit(); db2.close()
catatan = {}
_asli_potong, _asli_kembali = _br.kuota.potong_banyak, _br.kuota.kembalikan_banyak
_asli_hitung = _jb.hitung
_br.kuota.potong_banyak = lambda db, u, jml, jenis_addon='ai': catatan.update(potong=jml) or {'dipotong': jml}
_br.kuota.kembalikan_banyak = lambda db, u, jml, ja='ai': catatan.update(kembali=jml) or {'dikembalikan': jml}
def _mati(payload, timeout=None):
    raise _jb.GagalJembatan('Mesin statistik tidak menjawab.', 502)
_jb.hitung = _mati
try:
    r = k.post('/api/bab4/olah-data', json={'file_id': 11}, headers=H)
finally:
    _br.kuota.potong_banyak, _br.kuota.kembalikan_banyak = _asli_potong, _asli_kembali
    _jb.hitung = _asli_hitung
cek('BUG2 mesin mati → 502 dan token 5 DIKEMBALIKAN',
    r.status_code == 502 and catatan.get('potong') == 5 and catatan.get('kembali') == 5,
    f'{r.status_code} {catatan}')

print('── Regresi ronde 3 review Fase 3 ──')
# BUG BARU 1: hasil SPSS rute (berkas 11) membawa peta hipotesis
ph = j.get('hasil', {}).get('peta_hipotesis', [])
cek('BUG BARU 1 hasil olah-data memuat peta_hipotesis H1-H3, semua ketemu',
    [e['hipotesis'] for e in ph] == ['H1', 'H2', 'H3'] and all(e['ketemu'] for e in ph),
    str(ph)[:200])
cek('BUG BARU 1 H3 (langsung X→Y) terpetakan dari koefisien regresi',
    ph and ph[2]['jenis'] == 'langsung' and ph[2]['b'] is not None,
    str(ph[2]) if len(ph) > 2 else 'kosong')
# cabang tidak_langsung: bentuk hasil PERSIS tangkapan mesin asli
_hasil_tiru = {'mode': 'spss',
               'koef': [{'nama': 'X1', 'b': 0.44, 'p': 0.0},
                        {'nama': 'M1', 'b': 0.58, 'p': 0.0}],
               'kaitan': {'mediasi': [
                   {'x': 'X1', 'm': 'M1', 'y': 'Y1',
                    'a': {'b': 0.60, 'p': 0.0},
                    'tidak_langsung': {'b': 0.349, 'lo': 0.20, 'hi': 0.51}}]}}
_peta_tiru = {'variabel': [{'nama': 'X', 'peran': 'X'}, {'nama': 'Med', 'peran': 'M'},
                           {'nama': 'Y', 'peran': 'Y'}],
              'jalur': [{'dari': 'X', 'ke': 'Med', 'hipotesis': 'H1', 'jenis': 'langsung'},
                        {'dari': 'Med', 'ke': 'Y', 'hipotesis': 'H2', 'jenis': 'langsung'},
                        {'dari': 'X', 'ke': 'Y', 'hipotesis': 'H3', 'jenis': 'tidak_langsung',
                         'lewat': 'Med'}]}
_pm = _b4.petakan_hasil_ke_hipotesis(_peta_tiru, _hasil_tiru)
cek('BUG BARU 1 cabang tidak_langsung: efek 0.349, signifikan dari rentang CI',
    _pm[2]['ketemu'] and _pm[2]['b'] == 0.349 and _pm[2]['signifikan'] is True,
    str(_pm[2]))
cek('BUG BARU 1 cabang X→M terpetakan dari jalur a mediasi',
    _pm[0]['ketemu'] and _pm[0]['b'] == 0.60, str(_pm[0]))

# BUG BARU 3: tabrakan nama kolom tertolak periksa_peta
p_tabrak = {'jenis': 'kuantitatif', 'jumlah_hipotesis': 1,
            'variabel': [{'nama': 'Kualitas Produk', 'peran': 'X', 'bukti': B},
                         {'nama': 'Kualitas_Produk', 'peran': 'Y', 'bukti': B}],
            'jalur': [{'dari': 'Kualitas Produk', 'ke': 'Kualitas_Produk',
                       'hipotesis': 'H1', 'jenis': 'langsung'}]}
cek('BUG BARU 3 Kualitas Produk vs Kualitas_Produk → kolom_tabrakan',
    any(m['kode'] == 'kolom_tabrakan' for m in _b4.periksa_peta(p_tabrak)),
    str(_b4.periksa_peta(p_tabrak)))

# BUG BARU 2: bukti mesin — dua perantara terpisah + moderasi terbaca
rng2 = np.random.default_rng(3)
_lik = lambda v: np.clip(np.round(3 + v + rng2.normal(scale=.4, size=len(v))), 1, 5).astype(int)
_x = rng2.normal(size=90); _m1 = .7*_x + rng2.normal(scale=.6, size=90)
_m2 = .5*_x + rng2.normal(scale=.6, size=90); _z = rng2.normal(size=90)
_y = .4*_m1 + .4*_m2 + .3*_x + rng2.normal(scale=.6, size=90)
_k8 = ['X_1','X_2','A_1','A_2','Bb_1','Bb_2','Y_1','Y_2']
_b8 = [[int(_lik(_x)[i]), int(_lik(_x)[i]), int(_lik(_m1)[i]), int(_lik(_m1)[i]),
        int(_lik(_m2)[i]), int(_lik(_m2)[i]), int(_lik(_y)[i]), int(_lik(_y)[i])] for i in range(90)]
_h8 = _jb.hitung({'tahap': 'utama', 'mode': 'spss', 'bentuk_mediasi': 'lengkap',
                  'peran': {'X_1':'X1','X_2':'X1','A_1':'M1','A_2':'M1','Bb_1':'M2','Bb_2':'M2','Y_1':'Y1','Y_2':'Y1'},
                  'baris': _b4.baris_ke_objek(_k8, _b8)})
cek('BUG BARU 2 dua perantara → dua entri mediasi terpisah (M1 & M2)',
    sorted(e['m'] for e in _h8['kaitan']['mediasi']) == ['M1', 'M2'],
    str(_h8.get('kaitan', {}).get('mediasi'))[:150])
_k9 = ['X_1','X_2','M_1','M_2','Z_1','Z_2','Y_1','Y_2']
_b9 = [[int(_lik(_x)[i]), int(_lik(_x)[i]), int(_lik(_m1)[i]), int(_lik(_m1)[i]),
        int(_lik(_z)[i]), int(_lik(_z)[i]), int(_lik(_y)[i]), int(_lik(_y)[i])] for i in range(90)]
_h9 = _jb.hitung({'tahap': 'utama', 'mode': 'spss', 'bentuk_mediasi': 'lengkap',
                  'peran': {'X_1':'X1','X_2':'X1','M_1':'M1','M_2':'M1','Z_1':'Z1','Z_2':'Z1','Y_1':'Y1','Y_2':'Y1'},
                  'baris': _b4.baris_ke_objek(_k9, _b9)})
cek('BUG BARU 2 mediasi+moderasi → entri moderasi terbaca mesin',
    bool(_h9['kaitan'].get('moderasi')), str(list(_h9.get('kaitan', {}).keys())))

print()
print('❌ GAGAL: ' + ', '.join(gagal) if gagal else '✅ SEMUA LULUS — Fase 3 inti (rute BAB IV)')
sys.exit(1 if gagal else 0)
