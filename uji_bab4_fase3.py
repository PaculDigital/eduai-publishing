"""Uji Fase 3: rute BAB IV ujung-ke-ujung.

App FastAPI kecil memuat app/bab4_rute.py ASLI; login & db diganti
(sqlite memori + user boneka) — pola menimpa dependensi FastAPI.
Mesin hitung = server Statistik Lab lokal berkode Fase 1 (kunci e2e).
Jalan: EDUAI_STATISTIK_URL=http://127.0.0.1:8799 \
       EDUAI_STATISTIK_KUNCI=kunci-e2e EDUAI_SECRET_KEY=x \
       EDUAI_ROUTER_KEY=x python uji_bab4_fase3.py
"""
import sys, types, json, copy
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

print('── Regresi ronde 4: moderasi & presisi ──')
# unit: bentuk moderasi PERSIS tangkapan mesin asli
_hmod = {'mode': 'spss', 'koef': [],
         'kaitan': {'moderasi': [
             {'x': 'X1', 'z': 'Z1', 'y': 'Y1', 'delta_r2': 0.132073,
              'jenis': 'memoderasi', 'arah': 'memperkuat',
              'kalimat': 'Z1 MEMPERKUAT pengaruh X1 terhadap Y1.',
              'dengan_interaksi': {'r2': 0.336138,
                                   'interaksi': {'b': 0.67477, 't': 4.37, 'p': 3.1e-05}}}]}}
_pmod = {'variabel': [{'nama': 'X', 'peran': 'X'}, {'nama': 'Z', 'peran': 'Z'},
                      {'nama': 'Y', 'peran': 'Y'}],
         'jalur': [{'dari': 'Z', 'ke': 'Y', 'hipotesis': 'H2', 'jenis': 'interaksi'}]}
_em = _b4.petakan_hasil_ke_hipotesis(_pmod, _hmod)[0]
cek('BUG BARU 1 interaksi terisi: b, p, signifikan, delta_r2, kalimat',
    _em['ketemu'] and _em['b'] == 0.67477 and _em['signifikan'] is True
    and _em['delta_r2'] == 0.132073 and bool(_em['ringkas']), str(_em))

# unit presisi: koef 4-desimal vs kaitan penuh → pilih kaitan
_hpres = {'mode': 'spss',
          'koef': [{'nama': 'X1', 'b': 0.4390, 'p': 0.0}],
          'kaitan': {'mediasi': [
              {'x': 'X1', 'm': 'M1', 'y': 'Y1', 'a': {'b': 0.599145, 'p': 0.0},
               'cp': {'b': 0.438984, 'p': 4.3e-05},
               'tidak_langsung': {'b': 0.348885, 'lo': 0.2, 'hi': 0.51}}]}}
_ep = _b4.petakan_hasil_ke_hipotesis(_peta_tiru, _hpres)
_dir = [e for e in _ep if e['hipotesis'] == 'H3'][0] if False else None
_pdir = {'variabel': [{'nama': 'X', 'peran': 'X'}, {'nama': 'Med', 'peran': 'M'},
                      {'nama': 'Y', 'peran': 'Y'}],
         'jalur': [{'dari': 'X', 'ke': 'Y', 'hipotesis': 'H9', 'jenis': 'langsung'}]}
_ed = _b4.petakan_hasil_ke_hipotesis(_pdir, _hpres)[0]
cek('BUG BARU 2 X→Y langsung mengambil presisi penuh kaitan (cp), bukan koef 4-desimal',
    _ed['b'] == 0.438984 and _ed.get('sumber') == 'kaitan', str(_ed))

# e2e: peta moderasi lewat rute (berkas 12)
db3 = Sesi(); db3.add(FileBerkas(id=12, user_id=1, nama='mod.docx',
                                 nama_simpan='mod.docx', ukuran=10)); db3.commit(); db3.close()
peta_mod = {'jenis': 'kuantitatif', 'metode': 'Regresi', 'jumlah_hipotesis': 2,
            'variabel': [
                {'nama': 'Kualitas', 'peran': 'X', 'bukti': B,
                 'indikator': ['Produk awet.', 'Produk rapi.']},
                {'nama': 'Kepercayaan', 'peran': 'Z', 'bukti': B,
                 'indikator': ['Percaya merek.', 'Percaya penjual.']},
                {'nama': 'Minat', 'peran': 'Y', 'bukti': B,
                 'indikator': ['Beli lagi.', 'Rekomendasi.']}],
            'jalur': [
                {'dari': 'Kualitas', 'ke': 'Minat', 'hipotesis': 'H1', 'jenis': 'langsung'},
                {'dari': 'Kepercayaan', 'ke': 'Minat', 'hipotesis': 'H2', 'jenis': 'interaksi'}]}
k.post('/api/bab4/peta', json={'file_id': 12, 'peta': peta_mod}, headers=H)
k.post('/api/bab4/peta/sahkan', json={'file_id': 12}, headers=H)
kolom3 = k.get('/api/bab4/instrumen', params={'file_id': 12}).json()['kolom_template']
rng3 = np.random.default_rng(7)
_x3 = rng3.normal(size=100); _z3 = rng3.normal(size=100)
_y3 = 0.5*_x3 + 0.4*_x3*_z3 + rng3.normal(scale=.7, size=100)
_l3 = lambda v: np.clip(np.round(3 + v + rng3.normal(scale=.4, size=100)), 1, 5).astype(int)
_b12 = [[int(_l3(_x3)[i]), int(_l3(_x3)[i]), int(_l3(_z3)[i]), int(_l3(_z3)[i]),
         int(_l3(_y3)[i]), int(_l3(_y3)[i])] for i in range(100)]
k.put('/api/bab4/data', json={'file_id': 12, 'tahap': 'utama',
      'kolom': kolom3, 'baris': _b12}, headers=H)
r = k.post('/api/bab4/olah-data', json={'file_id': 12}, headers=H)
ph3 = r.json().get('hasil', {}).get('peta_hipotesis', []) if r.status_code == 200 else []
h2 = next((e for e in ph3 if e['hipotesis'] == 'H2'), {})
cek('e2e moderasi: H2 interaksi terpetakan dengan angka (b & signifikan terisi)',
    r.status_code == 200 and h2.get('ketemu') and h2.get('b') is not None
    and h2.get('signifikan') is not None, f'{r.status_code} {h2}')

print('── Regresi ronde 5: pintu masuk ──')
# BUG 1: data bentuk OBJEK diterima & dinormalisasi, olah data jalan
db4 = Sesi(); db4.add(FileBerkas(id=13, user_id=1, nama='obj.docx',
                                 nama_simpan='obj.docx', ukuran=10)); db4.commit(); db4.close()
k.post('/api/bab4/peta', json={'file_id': 13, 'peta': peta_spss}, headers=H)
k.post('/api/bab4/peta/sahkan', json={'file_id': 13}, headers=H)
kolom4 = k.get('/api/bab4/instrumen', params={'file_id': 13}).json()['kolom_template']
baris_obj = [dict(zip(kolom4, b)) for b in buat(40)]
r = k.put('/api/bab4/data', json={'file_id': 13, 'tahap': 'utama',
          'kolom': kolom4, 'baris': baris_obj}, headers=H)
cek('BUG 1 PUT data bentuk objek diterima rapi (200)', r.status_code == 200, r.text[:150])
d_obj = k.get('/api/bab4/data', params={'file_id': 13}).json()
cek('BUG 1 data tersimpan sebagai daftar (ternormalisasi)',
    isinstance(d_obj['baris'][0], list), str(d_obj['baris'][0])[:60])
r = k.post('/api/bab4/olah-data', json={'file_id': 13}, headers=H)
cek('BUG 1 olah data dari data objek JALAN (bukan 500 KeyError)',
    r.status_code == 200 and r.json().get('versi') == 1, r.text[:200])

# BUG 3: sel teks ditolak di pintu dengan 422
r = k.put('/api/bab4/data', json={'file_id': 13, 'tahap': 'utama',
          'kolom': kolom4, 'baris': [[None, 'abc', 3, 4, 5, 1]]}, headers=H)
cek('BUG 3 sel teks "abc" ditolak 422 saat simpan', r.status_code == 422, f'{r.status_code} {r.text[:120]}')

# BUG 2: jumlah_hipotesis bukan angka → masalah peta, bukan 500
p_aneh = copy.deepcopy(peta_spss); p_aneh['jumlah_hipotesis'] = 'tiga'
r = k.post('/api/bab4/peta', json={'file_id': 13, 'peta': p_aneh}, headers=H)
cek('BUG 2 POST /peta jumlah "tiga" → 200 + masalah jumlah_hipotesis_salah',
    r.status_code == 200 and any(m['kode'] == 'jumlah_hipotesis_salah'
                                 for m in r.json().get('masalah', [])), r.text[:200])
r = k.post('/api/bab4/peta/sahkan', json={'file_id': 13}, headers=H)
cek('BUG 2 sahkan peta "tiga" → 422 (bukan 500)', r.status_code == 422, str(r.status_code))

# BUG 4: bentrok awalan Harga vs Harga 1
p_bentrok = {'jenis': 'kuantitatif', 'jumlah_hipotesis': 1,
             'variabel': [{'nama': 'Harga 1', 'peran': 'X', 'bukti': B},
                          {'nama': 'Harga', 'peran': 'Y', 'bukti': B}],
             'jalur': [{'dari': 'Harga 1', 'ke': 'Harga', 'hipotesis': 'H1',
                        'jenis': 'langsung'}]}
cek('BUG 4 Harga vs Harga 1 → kolom_tabrakan',
    any(m['kode'] == 'kolom_tabrakan' for m in _b4.periksa_peta(p_bentrok)),
    str(_b4.periksa_peta(p_bentrok)))

# BUG 5: kartu kesehatan tahan bentuk aneh
try:
    _k1 = _b4.kartu_kesehatan({'variabel': 'teks'})
    _k2 = _b4.kartu_kesehatan({'variabel': [{'nama': 'A', 'butir': {'x': 1}}]})
    _k3 = _b4.kartu_kesehatan(None)
    cek('BUG 5 kartu_kesehatan tahan bentuk aneh (tidak meledak)',
        isinstance(_k1, dict) and isinstance(_k2, dict) and isinstance(_k3, dict))
except Exception as e:
    cek('BUG 5 kartu_kesehatan tahan bentuk aneh (tidak meledak)', False, str(e))

print()
print('❌ GAGAL: ' + ', '.join(gagal) if gagal else '✅ SEMUA LULUS — Fase 3 inti (rute BAB IV)')
sys.exit(1 if gagal else 0)
