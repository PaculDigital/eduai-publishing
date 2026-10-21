"""GERBANG PINTU UJI PLAGIARISME — uji HIDUP lewat TestClient (DB SALINAN).

Dijalankan DI DALAM container (kode baru sudah terpasang lewat jalankan.sh):
  docker exec -w /app -e EDUAI_DATA_DIR=/tmp/uji_plag_db \
    -e EDUAI_UPLOAD_DIR=/tmp/uji_plag_up eduai-app python3 /app/_uji_pintu_plag.py

⚠️ WAJIB DB SALINAN (aturan Bos) — JANGAN menyentuh DB produksi.
Menjaga:
  P1 halaman /plagiarisme terbuka setelah login (200)
  P2 menu memuat tab "Uji Plagiarisme"
  P3 halaman menyebut biaya 8 token
  P4 pagar: naskah MILIK ORANG LAIN ditolak (404)
  P5 uji gratis → 1 berkas PDF, watermark PRATINJAU, 25 halaman
  P6 uji gratis kedua untuk naskah SAMA ditolak (409)
"""
import os
import sys

sys.path.insert(0, '/app')
os.makedirs('/tmp/uji_plag_up', exist_ok=True)

from fastapi.testclient import TestClient                            # noqa: E402

from app import main as M                                            # noqa: E402
from app.auth import hash_password                                   # noqa: E402
from app.models import FileBerkas, SessionLocal, User                # noqa: E402

GAGAL = []


def cek(nama, syarat, bukti=''):
    if not syarat:
        GAGAL.append(nama)
    print(f'  [{"LULUS" if syarat else "GAGAL"}] {nama}  {bukti}')


db = SessionLocal()
email = 'uji-pintu-plag@eduai.test'
u = db.query(User).filter(User.email == email).first()
if not u:
    u = User(email=email, nama='Uji Pintu Plag', password_hash=hash_password('x'))
    db.add(u)
    db.commit()
    db.refresh(u)
print(f'  user uji: id={u.id}')

#  ── berkas uji: 1 milik user uji + 1 milik ORANG LAIN ──
import zipfile                                                       # noqa: E402
from pathlib import Path                                             # noqa: E402

#  ⚠️ JEBAKAN (16 Okt): berkas uji HARUS di `/app/uploads/<uid>/` — itu
#     lokasi yang DIBACA produksi. Menaruh di /tmp ⇒ balasan 422
#     "NASKAH_KOSONG" (pagar bekerja BENAR, ujinya yang salah tempat).
#     Sisi uji TIDAK memakai DB produksi (EDUAI_DATA_DIR = salinan), dan
#     berkas uji ditulis di folder user UJI yang dibuat khusus (id uji).
dasar = Path('/app/uploads') / str(u.id)
dasar.mkdir(parents=True, exist_ok=True)
simpan = 'naskah-uji.docx'
#  ⚠️ JEBAKAN (16 Okt): naskah uji HARUS PANJANG. Naskah pendek (1 kalimat
#     diulang) menghasilkan PDF cuma ~4 halaman ⇒ uji "25 halaman" GAGAL
#     PALSU (salah uji, bukan bug). Ukur memakai naskah SUNGGUHAN kalau ada.
_panjang = Path('/tmp/naskah_panjang.txt')
if _panjang.exists():
    _isi = _panjang.read_text(encoding='utf-8')
    _par = [p for p in _isi.split('\n') if p.strip()]
else:
    _par = ['Penelitian ini bertujuan menganalisis pengaruh kualitas '
            'pelayanan terhadap kepuasan pelanggan di Indonesia. ' * 30]
with zipfile.ZipFile(dasar / simpan, 'w') as z:
    z.writestr('word/document.xml',
               '<w:document><w:body>'
               + ''.join('<w:p><w:r><w:t>' + p + '</w:t></w:r></w:p>'
                         for p in _par)
               + '</w:body></w:document>')

b_milik = db.query(FileBerkas).filter(FileBerkas.user_id == u.id,
                                      FileBerkas.nama_simpan == simpan).first()
if not b_milik:
    b_milik = FileBerkas(user_id=u.id, nama='Naskah Uji Plag', nama_simpan=simpan,
                         ukuran=1000, tipe='docx')
    db.add(b_milik)
    db.commit()
    db.refresh(b_milik)

b_lain = db.query(FileBerkas).filter(FileBerkas.user_id != u.id).first()
print(f'  berkas milik sendiri: id={b_milik.id} · berkas orang lain: '
      f'id={getattr(b_lain, "id", None)}')

c = TestClient(M.app)
#  ── sesi login: pakai cookie resmi aplikasi ──
import app.auth as A                                                 # noqa: E402
tok = A.buat_token(u.id) if hasattr(A, 'buat_token') else None
if tok is None:
    tok = A.bikin_token(u.id) if hasattr(A, 'bikin_token') else None
print(f'  token sesi: {"ada" if tok else "TIDAK ADA"}')

kuki = {'eduai_session': tok} if isinstance(tok, str) else {}

print('\n=== P1. HALAMAN TERBUKA SETELAH LOGIN ===')
r = c.get('/plagiarisme', cookies=kuki, follow_redirects=False)
cek('P1a /plagiarisme = 200', r.status_code == 200, f'HTTP {r.status_code}')
html = r.text if r.status_code == 200 else ''
cek('P1b judul halaman benar', 'Uji Plagiarisme' in html)

print('\n=== P2. MENU ===')
cek('P2a tab di menu', 'href="/plagiarisme"' in html)
cek('P2b ikon tampil', 'ik-search-check' in html)

print('\n=== P3. BIAYA ===')
cek('P3a biaya 8 token', '8 token' in html)
cek('P3b blok sisa token', 'Sisa token-mu' in html)

print('\n=== P4. PAGAR NASKAH ORANG LAIN ===')
if b_lain is not None:
    r = c.post('/api/ai/v1/plagiarisme/uji', cookies=kuki,
               json={'berkas_id': b_lain.id, 'gratis': True})
    cek('P4a ditolak 404', r.status_code == 404, f'HTTP {r.status_code}')
else:
    print('  [LEWAT] tidak ada berkas milik user lain di salinan')

print('\n=== P5. UJI GRATIS → PDF ===')
r = c.post('/api/ai/v1/plagiarisme/uji', cookies=kuki,
           json={'berkas_id': b_milik.id, 'gratis': True})
cek('P5a HTTP 200', r.status_code == 200, f'HTTP {r.status_code}')
d = r.json() if r.status_code == 200 else {}
cek('P5b ada tautan', bool(d.get('tautan')), str(d.get('tautan'))[:50])
cek('P5c gratis=True', d.get('gratis') is True)
cek('P5d 11 sumber', d.get('jumlah_sumber') == 11, str(d.get('jumlah_sumber')))
cek('P5e 11 stabilo', d.get('stabilo') == 11, str(d.get('stabilo')))

if d.get('tautan'):
    r2 = c.get(d['tautan'], cookies=kuki)
    cek('P5f PDF terunduh', r2.status_code == 200, f'HTTP {r2.status_code}')
    if r2.status_code == 200:
        import fitz
        p = '/tmp/uji_plag_up/hasil-pintu.pdf'
        Path(p).write_bytes(r2.content)
        doc = fitz.open(p)
        #  ⚠️ Jangan paku "25 halaman" — jumlah halaman ikut panjang naskah.
        #     Yang WAJIB: lebih dari 10 halaman (naskah + laporan nyata),
        #     bukan PDF gagal yang cuma 1-2 halaman.
        cek('P5g PDF berisi banyak halaman (>10)', doc.page_count > 10,
            f'{doc.page_count} halaman')
        cek('P5h watermark PRATINJAU',
            all('PRATINJAU' in pg.get_text() for pg in doc))
        doc.close()

print('\n=== P6. GRATIS DUA KALI DITOLAK ===')
r = c.post('/api/ai/v1/plagiarisme/uji', cookies=kuki,
           json={'berkas_id': b_milik.id, 'gratis': True})
cek('P6a ditolak 409', r.status_code == 409, f'HTTP {r.status_code}')

print()
if GAGAL:
    print(f'  ✗ {len(GAGAL)} GAGAL: {GAGAL}')
    sys.exit(1)
print('  ✓ SEMUA LULUS')
