"""UJI C10 — versi KOSONG dilarang + versi tua DIARSIPKAN (bukan dihapus).

KENAPA ADA (ACC Bos "1+2+3", 25Sep26):
    Saat mengerjakan C7, uji publik MENEMBAK endpoint nyata dan menemukan
    file 47 tersimpan v60 & v61 = **0 karakter**, v61 `terpakai=1` →
    NASKAH MAHASISWA KOSONG. Lebih buruk: v57 (4.522 kar) sudah DIHAPUS
    oleh "gear" sehingga tidak ada lagi yang bisa dipulihkan.

TIGA PAGAR YANG DIUJI:
    1. `versi.py simpan_versi_per_komentar()` — JANGAN matikan versi lama
       sebelum tahu ada isi layak (periksa `layak` di depan).
    2. `ai.py _revisi_kerja()` — `konten` kosong → raise 503, TIDAK simpan.
    3. `versi.py` gear — versi tua DIARSIPKAN (`diarsipkan=True`), bukan
       `db.delete()`; `daftar_versi` menyaring arsip secara bawaan.

CARA UJI: DB SEMENTARA (`DATA_DIR` → tempdir) supaya TIDAK menyentuh data
    produksi. Memanggil fungsi SUNGGUHAN, bukan membaca teks kode.
"""
import os
import re
import sys
import tempfile

#  ⚠️ WAJIB sebelum mengimpor app.* — arahkan DB ke folder sementara.
_tmp = tempfile.mkdtemp(prefix='uji_c10_')
os.environ['EDUAI_DATA_DIR'] = _tmp
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(_tmp, 'uploads')
sys.path.insert(0, '/app')

lulus = gagal = 0


def cek(nama, syarat, info=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  OK   {nama}')
    else:
        gagal += 1
        print(f'  GAGAL {nama} {info}')


print('═' * 70)
print('UJI C10 — pagar versi KOSONG + gear mengarsipkan')
print('═' * 70)

from app.models import Base, engine, SessionLocal, User, FileBerkas  # noqa: E402
from app import versi as V                                           # noqa: E402

Base.metadata.create_all(engine)

db = SessionLocal()
try:
    u = User(email='uji-c10@test.local', password_hash='x', nama='Uji C10',
             paket='berbayar')
    db.add(u)
    db.flush()
    f = FileBerkas(user_id=u.id, nama='naskah-uji.docx',
                   nama_simpan='uji-c10.docx', ukuran=100, tipe='docx')
    db.add(f)
    db.commit()
    FID = f.id
    print(f'   DB sementara: {_tmp}\n   file_id={FID} user={u.id}')
except Exception as e:                                          # noqa: BLE001
    print(f'   ⚠️ gagal siapkan data uji: {type(e).__name__}: {e}')
    raise

BAB = 'BAB I'
ISI_ASLI = ('BAB I\nPENDAHULUAN\n' + ('Kalimat asli mahasiswa yang berisi dan '
            'layak disimpan sebagai versi awal. ') * 12)
assert len(ISI_ASLI) > 400

# ── 0. Siapkan versi AWAL yang berisi ───────────────────────────────────
print('\n── 0. Versi awal berisi (4.522 kar tiruan) ──')
v0 = V.simpan_versi(db, user_id=u.id, file_id=FID, bab=BAB, isi=ISI_ASLI,
                    komentar=['versi awal'], model='uji/model-awal')
cek('0a versi awal tersimpan', v0 is not None and v0.nomor == 1, v0)
cek('0b versi awal terpakai', bool(v0 and v0.terpakai))
panjang_v0 = len(ISI_ASLI)

# ── 1. simpan_versi MENOLAK isi kosong ──────────────────────────────────
print('\n── 1. simpan_versi menolak isi KOSONG ──')
hasil = V.simpan_versi(db, user_id=u.id, file_id=FID, bab=BAB, isi='',
                       komentar=['kosong'], model='uji/model-kosong')
db.commit()
cek('1a simpan_versi kembali None (ditolak)', hasil is None, hasil)

aktif = V.daftar_versi(db, FID, BAB)
cek('1b TIDAK ada versi baru 0-karakter',
    all(len(v.isi) > 0 for v in aktif),
    [len(v.isi) for v in aktif])
cek('1c versi TERPAKAI masih yang BERISI (naskah tidak hilang)',
    (V.versi_terpakai(db, FID, BAB) or v0) and
    len(V.versi_terpakai(db, FID, BAB).isi) == panjang_v0,
    len(V.versi_terpakai(db, FID, BAB).isi) if V.versi_terpakai(db, FID, BAB) else None)
cek('1d jumlah versi aktif tetap 1 (tidak bertambah)',
    len(aktif) == 1, [v.nomor for v in aktif])

# ── 2. simpan_versi_per_komentar MENOLAK blok kosong ────────────────────
print('\n── 2. simpan_versi_per_komentar menolak blok KOSONG ──')
blok_kosong = [{'nomor': 1, 'ringkas': 'K1', 'isi': ''},
               {'nomor': 2, 'ringkas': 'K2', 'isi': '   '}]
vs = V.simpan_versi_per_komentar(db, user_id=u.id, file_id=FID, bab=BAB,
                                 blok=blok_kosong, komentar=['a', 'b'],
                                 model='uji/model-kosong')
db.commit()
cek('2a kembali [] (ditolak)', vs == [], vs)
aktif2 = V.daftar_versi(db, FID, BAB)
cek('2b versi lama TIDAK dimatikan (masih ada yang terpakai)',
    any(v.terpakai for v in aktif2), [(v.nomor, v.terpakai) for v in aktif2])
tp = V.versi_terpakai(db, FID, BAB)
cek('2c versi terpakai masih BERISI (naskah tidak kosong)',
    tp is not None and len(tp.isi) == panjang_v0,
    len(tp.isi) if tp else None)

# ── 3. Blok BERISI tetap tersimpan (perilaku lama utuh) ──────────────────
print('\n── 3. Blok BERISI tetap tersimpan (tidak ikut rusak) ──')
blok_isi = [{'nomor': 1, 'ringkas': 'K1', 'isi': 'Isi perbaikan pertama ' * 8},
            {'nomor': 2, 'ringkas': 'K2', 'isi': 'Isi perbaikan kedua ' * 8}]
vs3 = V.simpan_versi_per_komentar(db, user_id=u.id, file_id=FID, bab=BAB,
                                  blok=blok_isi, komentar=['k1', 'k2'],
                                  model='uji/model-isi')
db.commit()
cek('3a dua versi tersimpan', len(vs3) == 2, len(vs3))
tp3 = V.versi_terpakai(db, FID, BAB)
cek('3b versi terpakai BERISI', tp3 is not None and len(tp3.isi) > 50,
    len(tp3.isi) if tp3 else None)

# ── 4. GEAR: versi tua DIARSIPKAN, bukan DIHAPUS ─────────────────────────
print('\n── 4. Gear mengarsipkan, TIDAK menghapus ──')
#  Buat beberapa PUTARAN supaya gear bekerja (VERSI_SIMPAN=2 putaran).
import time as _t                                               # noqa: E402
for putaran in range(3):
    _t.sleep(1.05)             # beda detik → jadi PUTARAN tersendiri
    V.simpan_versi_per_komentar(
        db, user_id=u.id, file_id=FID, bab=BAB,
        blok=[{'nomor': 1, 'ringkas': f'P{putaran}', 'isi': f'Putaran {putaran} ' * 20}],
        komentar=[f'putaran {putaran}'], model=f'uji/putaran{putaran}')
    db.commit()

aktif4 = V.daftar_versi(db, FID, BAB)
semua4 = V.daftar_versi(db, FID, BAB, dengan_arsip=True)
cek('4a daftar AKTIF lebih sedikit dari SEMUA (ada yang diarsipkan)',
    len(aktif4) < len(semua4), f'aktif={len(aktif4)} semua={len(semua4)}')
cek('4b arsip TIDAK ikut di daftar aktif',
    all(not getattr(v, 'diarsipkan', False) for v in aktif4),
    [(v.nomor, v.diarsipkan) for v in aktif4])
cek('4c versi berisi MASIH ADA di arsip (tidak dihapus!)',
    any(len(v.isi) > 50 for v in semua4 if getattr(v, 'diarsipkan', False)),
    'tidak ada arsip berisi')
cek('4d versi awal (v1) masih bisa ditemukan',
    any(v.nomor == 1 for v in semua4), [v.nomor for v in semua4])

# ── 5. Pagar kode masih terpasang ───────────────────────────────────────
print('\n── 5. Pagar masih terpasang di kode ──')
KODE_V = re.sub(r'#[^\n]*', '', open('/app/app/versi.py', encoding='utf-8').read())
KODE_A = re.sub(r'#[^\n]*', '', open('/app/app/ai.py', encoding='utf-8').read())
#  ⚠️ PELAJARAN (asersi 5e versi-1 GAGAL): membuang komentar dengan `#[^\n]*`
#  juga memakan sisa baris di belakang `#` pada STRING (mis. '... (file=%s ...)')
#  sehingga pola tak ketemu. Untuk asersi yang menyentuh kalimat pesan, pakai
#  berkas APA ADANYA; untuk yang menyentuh struktur, pakai yang sudah dibersihkan.
KODE_V_AWAL = open('/app/app/versi.py', encoding='utf-8').read()
cek('5a versi.py: periksa `layak` SEBELUM matikan versi lama',
    bool(re.search(r'layak\s*=\s*\[.*?\]\s*\n\s*if not layak:', KODE_V, re.S)),
    'pola tidak ditemukan')
#  5b — `db.delete(v)` HANYA boleh ada di `hapus_versi_file()` (hapus berkas),
#  TIDAK boleh di jalur "gear". Bukti: hitung kemunculan di SELURUH berkas.
#  ⚠️ Pelajaran: jangan cari teks 'db.delete(v)' begitu saja — gear yang benar
#  memakai `v.diarsipkan = True`, jadi yang diperiksa JUMLAH & LOKASI.
n_hapus = len(re.findall(r'db\.delete\(v\)', KODE_V))
cek('5b db.delete(v) hanya 1× (di hapus_versi_file, bukan gear)',
    n_hapus == 1, f'ditemukan {n_hapus}×')
cek('5b2 gear memakai v.diarsipkan = True (bukan delete)',
    KODE_V.count('v.diarsipkan = True') >= 2,
    f"ditemukan {KODE_V.count('v.diarsipkan = True')}×")
cek('5c versi.py: gear memakai diarsipkan=True',
    'v.diarsipkan = True' in KODE_V)
cek('5d versi.py: daftar_versi menyaring arsip secara bawaan',
    'VersiDokumen.diarsipkan.is_(False)' in KODE_V)
cek('5e versi.py: simpan_versi menolak isi kosong (bentuk perilaku)',
    bool(re.search(r"if not \(isi or ''\)\.strip\(\):", KODE_V_AWAL)))
cek('5e2 versi.py: penolakan mengembalikan None tepat sesudahnya',
    bool(re.search(r"if not \(isi or ''\)\.strip\(\):[\s\S]{0,300}?return None",
                   KODE_V_AWAL)))
#  5f — PAGAR ai.py diuji lewat PERILAKU, bukan teks.
#  ⚠️ PELAJARAN (RUSAK-5 TIDAK bergigi 2×): asersi "teks `log.error('[ai] C10...`
#  ada, dan `raise HTTPException(503)` ada" SELALU lulus — sebab yang dirusak
#  adalah `if False:` di DEPANNYA; teksnya tetap terbaca. ⇒ Asersi teks tidak
#  bisa melihat pagar yang dimatikan. Caranya: POTONG potongan pagar itu dari
#  `/app/app/ai.py` lalu JALANKAN — harus benar-benar melempar HTTPException 503.
#  ⚠️ Skrip `_periksa_pagar_c10.py` dijalankan DI DALAM container (ia hanya
#  membaca /app/app/ai.py; TIDAK butuh `docker`).
import subprocess                                             # noqa: E402
_r = subprocess.run(['python3', '/app/_periksa_pagar_c10.py'],
                    capture_output=True, text=True, cwd='/app')
_out = (_r.stdout + _r.stderr).strip()
print('   [5f perilaku]', _out.splitlines()[-1] if _out else '(kosong)')
cek('5f ai.py: pagar C10 BENAR-BENAR melempar 503 saat konten kosong '
    '(diuji dengan MENJALANKAN potongan fungsinya)',
    'HTTPException 503' in _out, _out[-200:] or 'tak ada keluaran')

db.close()
print('\n' + '═' * 70)
print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
print('═' * 70)
sys.exit(1 if gagal else 0)
