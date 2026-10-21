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

# ── Kontrak layar (penengah sengketa review ronde 7) ──
print('── Kontrak layar ↔ rute ──')
import re as _re
_html = open('app/templates/bab4.html', encoding='utf-8').read()
_dipanggil = set(_re.findall(r"/api/bab4/[a-z0-9./_-]+", _html))
_terdaftar = {'/api/bab4' + (r.path[len('/api/bab4'):] if r.path.startswith('/api/bab4') else r.path)
              for r in bab4_rute.router.routes}
_hilang = {u for u in _dipanggil
           if not any(u == t or u.startswith(t + '/') or t.startswith(u.rstrip('/'))
                      for t in _terdaftar)
           and u not in ('/api/bab4/instrumen/kuesioner.md', '/api/bab4/instrumen/template.csv',
                         '/api/bab4/data/unduh.csv')}
cek('semua URL yang dipanggil layar terdaftar sebagai rute', not _hilang,
    f'yatim: {_hilang}')
cek('layar memanggil GET /hasil (BUG 2)', '/api/bab4/hasil' in _html)
cek('layar memanggil GET /profil (BUG 3)', '/api/bab4/profil' in _html)


print('── Isi narasi kata-per-kata (ronde 8) ──')
_bahan = {'hasil': {'r2': 0.42, 'peta_hipotesis': [
    {'hipotesis': 'H1', 'dari': 'Harga', 'ke': 'Kepuasan', 'jenis': 'langsung',
     'ketemu': True, 'b': -0.043379, 'p': 0.605672, 'signifikan': False,
     'ringkas': 'b=-0.043379, p=0.605672 → tidak signifikan'},
    {'hipotesis': 'H3', 'dari': 'Harga', 'ke': 'Keputusan', 'jenis': 'tidak_langsung',
     'ketemu': True, 'b': 0.006458, 'p': None, 'signifikan': True,
     'lo': 0.001, 'hi': 0.02,
     'ringkas': 'b=0.006458, rentang kepercayaan 95% [0.001, 0.02] → signifikan'},
    {'hipotesis': 'H9', 'dari': 'Harga', 'ke': 'Keputusan', 'jenis': 'langsung',
     'ketemu': True, 'b': 0.1, 'p': None, 'signifikan': None, 'ringkas': ''}]},
    'versi_terkunci': 1, 'mode': 'spss', 'peta': {'variabel': []},
    'responden_masuk': 60, 'target': 80, 'pengembalian': 75.0, 'kartu_pra': None}
_teks = bab4_narasi.susun_draf(_bahan)
cek('BUG 1 tidak ada label dobel "H1: H1"', 'H1: H1' not in _teks and 'H3: H3' not in _teks)
cek('BUG 4 kata "None" tidak bocor ke teks', 'None' not in _teks)
cek('BUG 2 tidak ada tanda pisah dobel "— —"', '— —' not in _teks)
cek('tidak ada spasi dobel di seluruh teks narasi', '  ' not in _teks.replace('  ', '  ', 0) or all('  ' not in b for b in _teks.splitlines()))
_bahan_ci_lewat = {'hasil': {'r2': 0.3, 'peta_hipotesis': [
    {'hipotesis': 'H3', 'dari': 'Harga', 'ke': 'Keputusan', 'jenis': 'tidak_langsung',
     'ketemu': True, 'b': 0.01, 'p': None, 'signifikan': False,
     'lo': -0.017, 'hi': 0.0327, 'ringkas': ''}]},
    'versi_terkunci': 1, 'mode': 'spss', 'peta': {'variabel': []},
    'responden_masuk': 50, 'target': 60, 'pengembalian': 83.3, 'kartu_pra': None}
_teks2 = bab4_narasi.susun_draf(_bahan_ci_lewat)
cek('CI melewati nol → satu spasi & vonis ditolak',
    '] melewati nol' in _teks2 and ']  melewati' not in _teks2 and 'ditolak' in _teks2)
_baris_h3 = [b for b in _teks.splitlines() if b.strip().startswith('- H3')]
_baris_h9 = [b for b in _teks.splitlines() if b.strip().startswith('- H9')]
cek('BUG 3 efek tidak langsung tanpa p → disebut CI + diterima (bukan vonis p)',
    bool(_baris_h3) and 'rentang kepercayaan' in _baris_h3[0] and 'diterima' in _baris_h3[0],
    str(_baris_h3)[:160])
cek('BUG 3 tanpa p & tanpa CI → "belum dapat diambil", BUKAN ditolak',
    bool(_baris_h9) and 'belum dapat diambil' in _baris_h9[0] and 'ditolak' not in _baris_h9[0],
    str(_baris_h9)[:160])

print()
print('❌ GAGAL: ' + ', '.join(gagal) if gagal else '✅ SEMUA LULUS — Fase 3 sisa (simulasi, narasi, layar)')
sys.exit(1 if gagal else 0)
