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

print()
print('❌ GAGAL: ' + ', '.join(gagal) if gagal else '✅ SEMUA LULUS — Fase 3 inti (rute BAB IV)')
sys.exit(1 if gagal else 0)
