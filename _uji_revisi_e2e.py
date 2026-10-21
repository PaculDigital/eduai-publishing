"""UJI UJUNG-KE-UJUNG REVISI: potong token BENAR-BENAR (salinan DB, AI dipalsukan).

Pola SAMA dengan _uji_c7_dompet.py (sudah terbukti): pakai SALINAN DB supaya
DB produksi tidak disentuh; AI dipalsukan supaya tidak ada biaya nyata.
Yang dibuktikan: token BERKURANG dari saldo, artikrl berubah, riwayat tercatat,
dan kegagalan teknis MENGEMBALIKAN token.
"""
import sys, os, json, shutil, sqlite3, tempfile, asyncio
sys.path.insert(0, '/app')

LULUS = GAGAL = 0
def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1; print(f'  ✅ {nama}')
    else:
        GAGAL += 1; print(f'  ❌ {nama}  {bukti}')

# ── 1. SALIN DB ke tempat sementara (jangan sentuh produksi) ──
ASLI = '/app/data/eduai.db'
TMP = tempfile.mkdtemp(prefix='ujirev_')
SALIN = os.path.join(TMP, 'uji.db')
shutil.copy2(ASLI, SALIN)
print(f'DB salinan: {SALIN}')

os.environ['EDUAI_DB'] = SALIN
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
engine = create_engine(f'sqlite:///{SALIN}')
Sesi = sessionmaker(bind=engine)

#  ── buat user uji + 1 baris konversi "beres" (data SINTETIS) ──
import app.models as M
db = Sesi()
u = db.query(M.User).filter(M.User.email == 'uji-revisi@contoh.id').first()
if u is None:
    #  ⚠️ `password_hash` NOT NULL (terukur: IntegrityError saat diisi None) —
    #  data uji WAJIB mengisi kolom itu, walau user ini tak akan login.
    u = M.User(email='uji-revisi@contoh.id', nama='Uji Revisi',
               paket='penulis', password_hash='uji-tidak-dipakai')
    db.add(u); db.commit()
print(f'user uji id={u.id} paket={u.paket}')

fb = db.query(M.FileBerkas).filter(M.FileBerkas.user_id == u.id).first()
if fb is None:
    #  ⚠️ Kolom aslinya: nama, nama_simpan, ukuran, tipe (BUKAN ukuran_mb/jalur)
    #  — terukur dari FileBerkas.__table__.columns. Jangan karang nama kolom.
    fb = M.FileBerkas(user_id=u.id, nama='uji-revisi.docx',
                      nama_simpan='uji-revisi.docx', ukuran=0.1,
                      tipe='docx')
    db.add(fb); db.commit()
print(f'naskah id={fb.id}')

ART = {'judul': 'JUDUL LAMA', 'abstrak_id': 'Abstrak lama sekali.',
       'metode': 'Metode lama.', 'pendahuluan': 'Pendahuluan lama.',
       'elemen': {'novelty': 'Novelty lama', 'gap': 'Gap lama'}}
k = db.query(M.KonversiNaskah).filter(
    M.KonversiNaskah.user_id == u.id,
    M.KonversiNaskah.file_id == fb.id,
    M.KonversiNaskah.status == 'beres').first()
if k is None:
    k = M.KonversiNaskah(file_id=fb.id, user_id=u.id, status='beres',
                         jenis='kuantitatif', token_dipotong=1,
                         hasil_json=json.dumps({'artikel': ART}))
    db.add(k); db.commit()
print(f'baris konversi id={k.id}')

# ── 2. ISI SALDO supaya ada yang dipotong ──
from app import saldo as S
sebelum = S.sisa(db, u)
print(f'saldo sebelum: {sebelum}')
TAMBAH = 10
#  ⚠️ Nama fungsinya `masuk` (BUKAN `tambah`) — terukur dari app/saldo.py.
#  Wulan 2× salah karang nama fungsi; SELALU grep dulu sebelum dipakai.
S.masuk(db, u, TAMBAH, sumber='uji', catatan='saldo uji revisi')
db.commit()
saldo0 = S.sisa(db, u)
print(f'saldo sesudah ditambah: {saldo0}')

# ── 3. PALSUKAN AI (jangan panggil jaringan) ──
import app.konversi as kv
import app.ai as ai_mod

async def _palsu(pesan, timeout, system=''):
    return (json.dumps({'abstrak_id': 'ABSTRAK BARU DARI REVISI',
                        'elemen': {'novelty': 'NOVELTY BARU'}}),
            {'model': 'UJI-PALSU', 'token_in': 10, 'token_out': 10})
ai_mod._panggil_router = _palsu

# ── 4. JALANKAN: biaya -> potong -> panggil -> simpan ──
from app import kuota as K

pilihan = ['abstrak_id', 'elemen:novelty']
cek_b = kv.biaya_revisi_valid(pilihan, S.sisa(db, u))
cek('biaya 2 item = 4 token', cek_b['ok'] and cek_b['token'] == 4, cek_b)
butuh = cek_b['token']

info = K.potong_banyak(db, u, butuh, 'ai')
db.commit()
saldo1 = S.sisa(db, u)
cek('token BENAR-BENAR berkurang (10 -> 6)', saldo1 == saldo0 - butuh,
    f'{saldo0} -> {saldo1}')

hasil = asyncio.run(kv.jalankan_revisi(db, u, fb.id, ART, pilihan, 'sederhanakan'))
cek('AI palsu dipakai (model benar)', hasil['ok'] and hasil['model'] == 'UJI-PALSU', hasil)
cek('abstrak BERUBAH', hasil['artikel']['abstrak_id'] == 'ABSTRAK BARU DARI REVISI',
    hasil['artikel'].get('abstrak_id'))
cek('judul TIDAK berubah', hasil['artikel']['judul'] == 'JUDUL LAMA',
    hasil['artikel'].get('judul'))

simpan = kv.catat_revisi(db, u, fb.id, hasil['artikel'], pilihan, butuh,
                         hasil['model'])
db.commit()
cek('riwayat revisi tercatat', simpan.get('tersimpan'), simpan)
db.refresh(k)
wadah = json.loads(k.hasil_json or '{}')
cek('riwayat ada di hasil_json', len(wadah.get('revisi') or []) >= 1, wadah.keys())
cek('artikel tersimpan di baris', (wadah.get('artikel') or {}).get('abstrak_id')
    == 'ABSTRAK BARU DARI REVISI', '')

# ── 5. UJI GAGAL TEKNIS -> token KEMBALI ──
async def _gagal(pesan, timeout, system=''):
    raise RuntimeError('jaringan putus (uji)')
ai_mod._panggil_router = _gagal

saldo_sebelum_gagal = S.sisa(db, u)
info2 = K.potong_banyak(db, u, 4, 'ai')
db.commit()
cek('potong 4 token lagi', S.sisa(db, u) == saldo_sebelum_gagal - 4, '')
hasil2 = asyncio.run(kv.jalankan_revisi(db, u, fb.id, ART, pilihan, ''))
cek('jalankan_revisi GAGAL (sesuai harapan)', hasil2['ok'] is False, hasil2.get('galat'))
K.kembalikan_banyak(db, u, 4, 'ai')
db.commit()
cek('token DIKEMBALIKAN penuh',
    S.sisa(db, u) == saldo_sebelum_gagal,
    f'{saldo_sebelum_gagal} -> {S.sisa(db, u)}')

# ── 6. PAGAR SALDO KURANG ──
#  ⚠️ Saldo saat ini 18. Uji dengan 6 item (12 token) DENGAN SALDO 12 → harus
#  LOLOS (12 <= 18). Yang harus DITOLAK = 10 item (20 token) karena 20 > 18.
sisa_kini = S.sisa(db, u)
print(f'saldo sekarang: {sisa_kini}')
cek_k = kv.biaya_revisi_valid(
    ['abstrak_id', 'judul', 'metode', 'pendahuluan', 'kesimpulan',
     'daftar_pustaka'], sisa_kini)
cek(f'6 item (12 token) <= saldo {sisa_kini} -> LOLOS (tidak kebablasan)',
    cek_k['ok'] is True and cek_k['token'] == 12, cek_k)

semua = ['judul', 'abstrak_id', 'abstract_en', 'pendahuluan', 'metode',
         'hasil_pembahasan', 'kesimpulan', 'daftar_pustaka',
         'elemen:hook', 'elemen:novelty']
cek_k2 = kv.biaya_revisi_valid(semua, 4)          # saldo kecil -> harus TOLAK
cek('10 item (20 token) > saldo 4 -> TOLAK + sebut kurang',
    cek_k2['ok'] is False and cek_k2.get('kurang') == 16, cek_k2)

db.close()
shutil.rmtree(TMP, ignore_errors=True)
print()
print('═' * 60)
print(f'  HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 60)
sys.exit(1 if GAGAL else 0)
