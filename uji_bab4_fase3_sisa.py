"""Uji Fase 3 SISA: simulasi sungguhan, narasi, layar.

Pola sama uji_bab4_fase3.py (app kecil + tindih dependensi + server
Statistik Lab lokal hidup berkode terbaru, termasuk pintu simulasi).
AI polesan narasi sengaja dibiarkan gagal (tanpa kunci router) untuk
membuktikan jalur mundur deterministik tetap menghasilkan narasi.
"""
import sys, types
sys.path.insert(0, '.')
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, FileBerkas, User
from app import bab4_rute, bab4_narasi
from app.auth import wajib_login_api, wajib_login
from app.models import get_db

gagal = []
def cek(nama, kondisi, info=''):
    print(('  ✓ ' if kondisi else '  ✗ GAGAL ') + nama +
          ('' if kondisi else f' → {info}'))
    if not kondisi:
        gagal.append(nama)

eng = create_engine('sqlite://', connect_args={'check_same_thread': False},
                    poolclass=StaticPool)
Base.metadata.create_all(eng)
Sesi = sessionmaker(bind=eng)
db0 = Sesi()
db0.add(User(id=1, email='uji@contoh.id', nama='Penguji', password_hash='x'))
db0.add(FileBerkas(id=20, user_id=1, nama='sim.docx',
                   nama_simpan='sim.docx', ukuran=10))
db0.commit(); db0.close()

def _db():
    s = Sesi()
    try:
        yield s
    finally:
        s.close()

app = FastAPI()
app.include_router(bab4_rute.router)
app.include_router(bab4_rute.router_layar)
_palsu = types.SimpleNamespace(id=1)
app.dependency_overrides[wajib_login_api] = lambda: _palsu
app.dependency_overrides[wajib_login] = lambda: _palsu
app.dependency_overrides[get_db] = _db
k = TestClient(app, raise_server_exceptions=False)
H = {'Content-Type': 'application/json'}
B = [{'kalimat': 'ada di naskah', 'bab': 'III'}]
peta = {'jenis': 'kuantitatif', 'metode': 'Regresi', 'jumlah_hipotesis': 3,
        'variabel': [
            {'nama': 'Harga', 'peran': 'X', 'bukti': B,
             'indikator': ['Harga terjangkau.', 'Harga sesuai kualitas.']},
            {'nama': 'Kepuasan', 'peran': 'M', 'bukti': B,
             'indikator': ['Saya puas.', 'Sesuai harapan.']},
            {'nama': 'Keputusan', 'peran': 'Y', 'bukti': B,
             'indikator': ['Beli lagi.', 'Rekomendasi.']}],
        'jalur': [
            {'dari': 'Harga', 'ke': 'Kepuasan', 'hipotesis': 'H1', 'jenis': 'langsung'},
            {'dari': 'Kepuasan', 'ke': 'Keputusan', 'hipotesis': 'H2', 'jenis': 'langsung'},
            {'dari': 'Harga', 'ke': 'Keputusan', 'hipotesis': 'H3', 'jenis': 'tidak_langsung',
             'lewat': 'Kepuasan'}]}

print('── Fase 3 sisa ──')
k.post('/api/bab4/peta', json={'file_id': 20, 'peta': peta}, headers=H)
k.post('/api/bab4/peta/sahkan', json={'file_id': 20}, headers=H)
template = k.get('/api/bab4/instrumen', params={'file_id': 20}).json()['kolom_template']

r = k.post('/api/bab4/simulasi/buat', json={'file_id': 20, 'n': 60,
           'efek': {'H1': 'kuat', 'H2': 'kuat', 'H3': 'nol'}}, headers=H)
j = r.json() if r.status_code == 200 else {}
cek('simulasi mediasi: 60 baris dibuat mesin', r.status_code == 200 and j.get('jumlah_baris') == 60, r.text[:250])
cek('kolom simulasi SAMA PERSIS template instrumen', j.get('kolom') == template,
    f"{j.get('kolom')} vs {template}")
r = k.get('/api/bab4/data/unduh.csv', params={'file_id': 20, 'tahap': 'simulasi'})
cek('unduh CSV simulasi: kepala = template', r.status_code == 200 and r.text.splitlines()[0] == ','.join(template), r.text[:100])
r = k.post('/api/bab4/olah-data', json={'file_id': 20, 'tahap': 'simulasi'}, headers=H)
cek('data simulasi bisa diolah (alur latihan utuh)', r.status_code == 200, r.text[:200])

# narasi: sebelum kunci → 409
r = k.post('/api/bab4/narasi', json={'file_id': 20}, headers=H)
cek('narasi sebelum Kunci Hasil → 409', r.status_code == 409, str(r.status_code))

# pakai data simulasi sebagai data utama untuk alur kunci (uji saja)
d_sim = k.get('/api/bab4/data', params={'file_id': 20, 'tahap': 'simulasi'}).json()
k.put('/api/bab4/data', json={'file_id': 20, 'tahap': 'utama',
      'kolom': d_sim['kolom'], 'baris': d_sim['baris'], 'target_responden': 80}, headers=H)
k.post('/api/bab4/olah-data', json={'file_id': 20}, headers=H)
k.post('/api/bab4/kunci-hasil', json={'file_id': 20}, headers=H)

# potong token dicatat saja (saldo uji kosong) — pola ronde 5
catatan = []
_asli = bab4_rute.kuota.potong_banyak
bab4_rute.kuota.potong_banyak = lambda db, u, jml, jenis_addon='ai': catatan.append(jml) or {'dipotong': jml}
try:
    r = k.post('/api/bab4/narasi', json={'file_id': 20}, headers=H)
    j = r.json() if r.status_code == 200 else {}
    cek('narasi pertama: tarif 30, teks 4.1–4.4 lahir dari hasil terkunci',
        r.status_code == 200 and j.get('tarif_dikenakan') == 30
        and '## 4.1' in j.get('teks', '') and '## 4.4' in j.get('teks', ''), r.text[:250])
    cek('narasi memuat angka hasil (H1/H2/H3 + putusan)',
        all(h in j.get('teks', '') for h in ('H1', 'H2', 'H3')), j.get('teks', '')[:200])
    r = k.post('/api/bab4/narasi', json={'file_id': 20}, headers=H)
    cek('narasi buat ulang: tarif 5', r.status_code == 200 and r.json().get('tarif_dikenakan') == 5,
        r.text[:200])
finally:
    bab4_rute.kuota.potong_banyak = _asli
r = k.put('/api/bab4/narasi/teks', json={'file_id': 20, 'teks': '# BAB IV\n\nSuntingan manual saya.'}, headers=H)
cek('suntingan manual narasi gratis & berversi', r.status_code == 200 and r.json().get('tarif_dikenakan') == 0, r.text[:150])
r = k.get('/api/bab4/hasil', params={'file_id': 20, 'jenis': 'narasi'})
cek('narasi terbaca kembali lewat GET /hasil', r.status_code == 200 and len(r.json().get('meta', [])) >= 3, r.text[:150])

# layar
r = k.get('/bab4/20')
cek('layar HTML /bab4/20 tampil (200, ada Data Lapangan & Narasi)',
    r.status_code == 200 and 'Data Lapangan' in r.text and 'Narasi BAB IV' in r.text,
    f'{r.status_code}')
r = k.get('/bab4/999')
cek('layar berkas orang lain → 404', r.status_code == 404, str(r.status_code))

print()
print('❌ GAGAL: ' + ', '.join(gagal) if gagal else '✅ SEMUA LULUS — Fase 3 sisa (simulasi, narasi, layar)')
sys.exit(1 if gagal else 0)
