"""Uji Fase 4 EduAi: alur kualitatif + campuran dua putaran.

App kecil memuat bab4_rute ASLI; matriks dihitung server Statistik Lab
lokal sungguhan (deterministik). Panggilan AI koding diganti boneka
(pintu AI-nya sendiri sudah diuji di repo statistik-lab).
"""
import sys, types, json
sys.path.insert(0, '.')
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, FileBerkas, User
from app import bab4_rute, jembatan_statistik
from app.auth import wajib_login_api
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
for fid, nm in ((20, 'kual.docx'), (21, 'swot.docx'), (30, 'campur.docx')):
    db0.add(FileBerkas(id=fid, user_id=1, nama=nm, nama_simpan=nm, ukuran=100))
db0.commit(); db0.close()

def _db():
    s = Sesi()
    try:
        yield s
    finally:
        s.close()

app = FastAPI()
app.include_router(bab4_rute.router)
app.dependency_overrides[wajib_login_api] = lambda: types.SimpleNamespace(id=1, email='uji@contoh.id', nama='Penguji', role='user')
app.dependency_overrides[get_db] = _db
k = TestClient(app, raise_server_exceptions=False)
H = {'Content-Type': 'application/json'}
B = [{'kalimat': 'tertulis di naskah', 'bab': 'III'}]

# AI koding boneka (pintu AI asli teruji di repo statistik-lab)
def _ai_palsu(fokus, catatan):
    return {'usulan': [
        {**c, 'indeks': i, 'kode_usulan': 'kode ' + str(i),
         'tema_usulan': 'Mutu Layanan' if i < 2 else 'Tekanan Harga'}
        for i, c in enumerate(catatan)], 'jumlah': len(catatan)}
jembatan_statistik.usulkan_koding = _ai_palsu

# potong token dicatat saja (saldo uji kosong) — pola ronde 5
potongan = []
bab4_rute.kuota.potong_banyak = lambda db, u, jml, jenis_addon='ai': potongan.append(jml) or {'dipotong': jml}
bab4_rute.kuota.kembalikan_banyak = lambda db, u, jml, jenis_addon='ai': {'dikembalikan': jml}

print('── Kualitatif tematik (file 20) ──')
peta_k = {'jenis': 'kualitatif', 'fokus': [{'nama': 'mutu layanan warung', 'bukti': B}],
          'informan': [{'jenis': 'pelanggan', 'bukti': B},
                       {'jenis': 'pemilik', 'bukti': B}]}
r = k.post('/api/bab4/peta', json={'file_id': 20, 'peta': peta_k}, headers=H)
cek('peta kualitatif bersih', r.status_code == 200 and r.json()['masalah'] == [], r.text[:150])
r = k.post('/api/bab4/peta/sahkan', json={'file_id': 20}, headers=H)
cek('peta kualitatif disahkan', r.status_code == 200, r.text[:120])

catatan = [
    {'informan': 'Pelanggan A', 'teknik': 'wawancara', 'jenis': 'eksternal', 'teks': 'pelayanannya lambat sekali'},
    {'informan': 'Pelanggan B', 'teknik': 'observasi', 'jenis': 'eksternal', 'teks': 'antre panjang di kasir'},
    {'informan': 'Pemilik', 'teknik': 'wawancara', 'jenis': 'internal', 'teks': 'staf kami memang kurang'},
    {'informan': 'Pelanggan A', 'teknik': 'wawancara', 'jenis': 'eksternal', 'teks': 'harga naik terus'},
]
r = k.put('/api/bab4/kualitatif/catatan', json={'file_id': 20, 'catatan': catatan}, headers=H)
cek('catatan tersimpan di EduAi', r.status_code == 200 and r.json()['jumlah'] == 4, r.text[:120])
r = k.put('/api/bab4/kualitatif/catatan', json={'file_id': 20, 'catatan': [{'teks': '  '}]}, headers=H)
cek('potongan tanpa teks -> 422', r.status_code == 422, r.text[:120])
r = k.post('/api/bab4/kualitatif/usulkan-koding', json={'file_id': 20}, headers=H)
cek('usulan koding pulang (AI hanya mengusulkan)', r.status_code == 200 and r.json()['usulan'][0]['tema_usulan'] == 'Mutu Layanan', r.text[:150])

# peneliti mengesahkan: betulkan tema segmen 3 jadi Mutu Layanan juga
segmen = [
    {'teks': c['teks'], 'informan': c['informan'], 'teknik': c['teknik'], 'jenis': c['jenis'],
     'kode': 'kode sah ' + str(i), 'tema': 'Mutu Layanan' if i < 3 else 'Tekanan Harga'}
    for i, c in enumerate(catatan)]
r = k.put('/api/bab4/kualitatif/segmen', json={'file_id': 20, 'segmen': segmen}, headers=H)
cek('segmen tersahkan tersimpan', r.status_code == 200, r.text[:120])
r = k.post('/api/bab4/kualitatif/matriks', json={'file_id': 20, 'jenis': 'tematik'}, headers=H)
j = r.json() if r.status_code == 200 else {}
tri = ((j.get('hasil') or {}).get('triangulasi') or {})
ml = [x for x in tri.get('tema', []) if x['tema'] == 'Mutu Layanan']
cek('matriks tematik terhitung mesin (versi 1)', r.status_code == 200 and j.get('versi') == 1, r.text[:150])
cek('Mutu Layanan kuat+tertriangulasi dari hitungan server', bool(ml) and ml[0]['kuat'] and ml[0]['tertriangulasi'], str(ml)[:150])
r = k.post('/api/bab4/kunci-hasil', json={'file_id': 20, 'jenis': 'kualitatif_tematik'}, headers=H)
cek('hasil kualitatif bisa dikunci', r.status_code == 200 and r.json()['versi_terkunci'] == 1, r.text[:120])
r = k.post('/api/bab4/narasi', json={'file_id': 20, 'sumber': 'kualitatif_tematik'}, headers=H)
teks = r.json().get('teks', '') if r.status_code == 200 else ''
cek('narasi kualitatif lahir dari matriks terkunci', r.status_code == 200 and 'Mutu Layanan' in teks and '4.3' in teks, r.text[:150])
cek('narasi pertama bertarif 30 (pola harga final)', potongan[-1:] == [30], str(potongan))

print('── SWOT (file 21) ──')
r = k.post('/api/bab4/peta', json={'file_id': 21, 'peta': peta_k}, headers=H)
r = k.post('/api/bab4/peta/sahkan', json={'file_id': 21}, headers=H)
faktor = [{'kelompok': 'S', 'teks': 'rasa enak', 'bobot': 0.6, 'rating': 4},
          {'kelompok': 'W', 'teks': 'tempat sempit', 'bobot': 0.4, 'rating': 2},
          {'kelompok': 'O', 'teks': 'ojek online', 'bobot': 0.5, 'rating': 3},
          {'kelompok': 'T', 'teks': 'saingan baru', 'bobot': 0.5, 'rating': 2}]
r = k.put('/api/bab4/kualitatif/faktor', json={'file_id': 21, 'faktor': faktor}, headers=H)
cek('faktor SWOT tersimpan', r.status_code == 200, r.text[:120])
r = k.put('/api/bab4/kualitatif/faktor', json={'file_id': 21, 'faktor': [{'kelompok': 'X', 'teks': 'aneh'}]}, headers=H)
cek('kelompok aneh -> 422', r.status_code == 422, r.text[:120])
r = k.post('/api/bab4/kualitatif/matriks', json={'file_id': 21, 'jenis': 'swot'}, headers=H)
sw = ((r.json().get('hasil') or {}).get('swot') or {}) if r.status_code == 200 else {}
cek('matriks SWOT: IFAS 3.20 & kuadran I', r.status_code == 200 and sw.get('ifas', {}).get('total_skor') == 3.2 and (sw.get('kuadran') or {}).get('kode') == 'I', r.text[:150])

print('── Campuran dua putaran (file 30) ──')
peta_c = {'jenis': 'campuran', 'metode': 'SPSS', 'jumlah_hipotesis': 1,
          'variabel': [
              {'nama': 'Harga', 'peran': 'X', 'bukti': B, 'indikator': ['Harga sesuai kantong.']},
              {'nama': 'Keputusan', 'peran': 'Y', 'bukti': B, 'indikator': ['Saya memutuskan membeli.']}],
          'jalur': [{'dari': 'Harga', 'ke': 'Keputusan', 'hipotesis': 'H1', 'jenis': 'langsung'}],
          'fokus': [{'nama': 'alasan keputusan pembeli', 'bukti': B}],
          'informan': [{'jenis': 'pembeli', 'bukti': B}]}
r = k.post('/api/bab4/peta', json={'file_id': 30, 'peta': peta_c}, headers=H)
cek('peta campuran bersih (dua belahan diperiksa)', r.status_code == 200 and r.json()['masalah'] == [], r.text[:200])
peta_c_rusak = json.loads(json.dumps(peta_c)); peta_c_rusak['fokus'] = [{'nama': 'x', 'bukti': []}]
r = k.post('/api/bab4/peta', json={'file_id': 30, 'peta': peta_c_rusak}, headers=H)
cek('fokus campuran tanpa bukti -> masalah tanpa_bukti', any(m['kode'] == 'tanpa_bukti' for m in r.json()['masalah']), r.text[:200])
r = k.post('/api/bab4/peta', json={'file_id': 30, 'peta': peta_c}, headers=H)
r = k.post('/api/bab4/peta/sahkan', json={'file_id': 30}, headers=H)
cek('peta campuran disahkan', r.status_code == 200, r.text[:120])
r = k.put('/api/bab4/kualitatif/segmen', json={'file_id': 30, 'segmen': segmen}, headers=H)
r = k.post('/api/bab4/kualitatif/matriks', json={'file_id': 30, 'jenis': 'tematik'}, headers=H)
cek('GERBANG: putaran 2 tertahan sebelum putaran 1 dikunci (409)', r.status_code == 409, r.text[:130])
r = k.post('/api/bab4/campuran/pendalaman', json={'file_id': 30}, headers=H)
cek('pendalaman juga tertahan tanpa kunci kuantitatif (409)', r.status_code == 409, r.text[:130])
# tanam hasil kuantitatif terkunci langsung lewat layanan (alur olah
# data sungguhan sudah teruji di suite Fase 3)
from app import bab4 as _b4
s = Sesi()
isi = {'peta_hipotesis': [
    {'hipotesis': 'H1', 'dari': 'Harga', 'ke': 'Keputusan', 'jenis': 'langsung',
     'ketemu': True, 'b': 0.11, 'p': 0.42, 'signifikan': False, 'ringkas': ''}]}
h = _b4.simpan_hasil(s, 1, 30, 'olah_data', 'spss', isi)
_b4.kunci_hasil(s, 1, 30)
s.close()
r = k.post('/api/bab4/campuran/pendalaman', json={'file_id': 30}, headers=H)
qs = r.json().get('pertanyaan', []) if r.status_code == 200 else []
cek('pendalaman lahir dari hasil terkunci', r.status_code == 200 and len(qs) == 1, r.text[:150])
cek('jalur tak signifikan -> pertanyaan menggali sebab lapangan',
    bool(qs) and 'belum terbukti' in qs[0]['pertanyaan'] and 'Harga' in qs[0]['pertanyaan'], str(qs)[:170])
r = k.post('/api/bab4/kualitatif/matriks', json={'file_id': 30, 'jenis': 'tematik'}, headers=H)
cek('putaran 2 jalan sesudah putaran 1 terkunci', r.status_code == 200, r.text[:130])
r = k.post('/api/bab4/kunci-hasil', json={'file_id': 30, 'jenis': 'kualitatif_tematik'}, headers=H)
r = k.post('/api/bab4/narasi', json={'file_id': 30, 'sumber': 'campuran'}, headers=H)
teks = r.json().get('teks', '') if r.status_code == 200 else ''
cek('narasi campuran: ada 4.3 kualitatif + 4.4 terpadu', r.status_code == 200 and 'Hasil Kualitatif (Putaran 2)' in teks and 'Pembahasan Terpadu' in teks, r.text[:150])

print()
print('❌ GAGAL: ' + ', '.join(gagal) if gagal else '✅ SEMUA LULUS — Fase 4 (kualitatif + campuran)')
sys.exit(1 if gagal else 0)
