#!/usr/bin/env python3
"""UJI OPSI C — PEMBATALAN KUOTA SAAT ROLLBACK (ACC Bos 17Sep26).

Memeriksa ATURAN + PAGAR anti-penggilingan:

  SYARAT (semua harus terpenuhi agar kuota dibalikkan):
    1. hasil belum pernah dibuka (proses_ai.dibaca == 0)
    2. hasil belum diterapkan ke dokumen (versi belum terpakai)
    3. belum pakai hak ini untuk naskah ini HARI INI (maks 1×/naskah/hari)

  PAGAR:
    · jeda 20 menit sejak revisi selesai
    · kuota tidak pernah kembali lebih dari yang dipotong

  WAJIB: notifikasi selalu dikirim apa pun hasilnya.
"""
import sys
sys.path.insert(0, '/app')
from datetime import datetime, timedelta
from app.models import (SessionLocal, User, FileBerkas, ProsesAI,
                        VersiDokumen, PembatalanKuota, Notifikasi)
from app.pembatalan import boleh_dibalikkan, JEDA_MENIT, MAKS_HARI_INI
from app import notifikasi as N
from sqlalchemy import select, delete

lulus = gagal = 0


def cek(nama, syarat, bukti=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  ✅ {nama} {bukti}')
    else:
        gagal += 1
        print(f'  ❌ {nama} {bukti}')


db = SessionLocal()
u = db.execute(select(User).where(
    User.email == 'uji-berbayar-e2e@test.local')).scalar_one_or_none()
UID = u.id
fb = db.execute(select(FileBerkas).where(
    FileBerkas.user_id == UID).order_by(FileBerkas.id.desc())).scalars().first()
if fb is None:
    print('❌ berkas uji tidak ada'); sys.exit(1)
FID = fb.id
KODE = 'UJI-OPSIC-0001'
print(f'=== OPSI C (user={UID} file={FID}) ===')
print(f'    JEDA_MENIT={JEDA_MENIT} · MAKS_HARI_INI={MAKS_HARI_INI}')

# ── Siapkan proses BERSIH: selesai, belum dibuka, baru saja ──────────────
db.execute(delete(PembatalanKuota).where(PembatalanKuota.user_id == UID,
                                         PembatalanKuota.file_id == FID))
lama = db.execute(select(ProsesAI).where(ProsesAI.kode == KODE)).scalar_one_or_none()
if lama:
    db.delete(lama)
db.commit()

p = ProsesAI(kode=KODE, user_id=UID, file_id=FID, status='selesai',
             tahap='Selesai', dibaca=0, token_revisi=2, jumlah_bagian=2,
             selesai=datetime.utcnow(), dibuat=datetime.utcnow())
db.add(p)
db.commit()

print('\n=== 1. SEMUA SYARAT TERPENUHI → kuota DIBALIKKAN ===')
boleh, alasan, jumlah = boleh_dibalikkan(db, UID, FID, KODE)
cek('boleh=True', boleh is True, f'→ {alasan}')
cek('jumlah = token yang dipotong (2)', jumlah == 2, f'→ {jumlah}')

print('\n=== 2. SYARAT 1: hasil SUDAH DIBUKA → TIDAK dibalikkan ===')
p.dibaca = 1
db.commit()
boleh, alasan, jumlah = boleh_dibalikkan(db, UID, FID, KODE)
cek('boleh=False', boleh is False, f'→ {alasan}')
cek('alasan = hasil_sudah_dibuka', alasan == 'hasil_sudah_dibuka')
p.dibaca = 0
db.commit()

print('\n=== 3. PAGAR: JEDA 20 MENIT ===')
p.selesai = datetime.utcnow() - timedelta(minutes=JEDA_MENIT + 1)
db.commit()
boleh, alasan, _j = boleh_dibalikkan(db, UID, FID, KODE)
cek(f'lewat {JEDA_MENIT} menit → TIDAK dibalikkan', boleh is False,
    f'→ {alasan}')
cek('alasan = lewat_jeda_waktu', alasan == 'lewat_jeda_waktu')
# tepi: 19 menit masih boleh
p.selesai = datetime.utcnow() - timedelta(minutes=JEDA_MENIT - 1)
db.commit()
boleh2, alasan2, _j2 = boleh_dibalikkan(db, UID, FID, KODE)
cek(f'{JEDA_MENIT-1} menit MASIH boleh', boleh2 is True, f'→ {alasan2}')
p.selesai = datetime.utcnow()
db.commit()

print('\n=== 4. SYARAT 3: HARI INI SUDAH PAKAI HAK → tidak lagi ===')
#  Tiru pembatalan sukses hari ini (jumlah_kembali > 0)
db.add(PembatalanKuota(user_id=UID, file_id=FID, kode_proses=KODE,
                       jumlah_kembali=2, alasan='boleh'))
db.commit()
boleh, alasan, jumlah = boleh_dibalikkan(db, UID, FID, KODE)
cek('pemakaian ke-2 hari ini DITOLAK', boleh is False, f'→ {alasan}')
cek('alasan = sudah_pakai_hak_hari_ini',
    alasan == 'sudah_pakai_hak_hari_ini')

print('\n=== 5. PAGAR: 1× per NASKAH (bukan per akun) ===')
#  Naskah LAIN harus tetap boleh (belum pakai haknya)
fb2 = db.execute(select(FileBerkas).where(
    FileBerkas.user_id == UID, FileBerkas.id != FID)).scalars().first()
if fb2:
    boleh3, alasan3, _j3 = boleh_dibalikkan(db, UID, fb2.id, KODE)
    cek('naskah BERBEDA tetap boleh', boleh3 is True, f'→ {alasan3}')
else:
    print('  ℹ️  hanya 1 berkas → dilewati (tidak bisa diuji)')

print('\n=== 6. SYARAT 2: hasil sudah DITERAPKAN → tidak dibalikkan ===')
db.execute(delete(PembatalanKuota).where(PembatalanKuota.user_id == UID,
                                         PembatalanKuota.file_id == FID))
db.commit()
db.add(VersiDokumen(user_id=UID, file_id=FID, bab='__seluruh__', nomor=9999,
                    isi='hasil revisi uji', komentar='uji', model='uji',
                    terpakai=True, sumber='ai', ukuran=10,
                    dibuat=datetime.utcnow()))
db.commit()
boleh, alasan, _j = boleh_dibalikkan(db, UID, FID, KODE)
cek('versi terpakai → TIDAK dibalikkan', boleh is False, f'→ {alasan}')
cek('alasan = hasil_sudah_diterapkan',
    alasan == 'hasil_sudah_diterapkan')
#  bersihkan versi uji
db.execute(delete(VersiDokumen).where(VersiDokumen.nomor == 9999))
db.commit()

print('\n=== 7. KALIMAT NOTIFIKASI (dikte Bos verbatim) ===')
t_pakai = N.pesan('naskah_kembali_kuota_terpakai')
print(f'  [kuota TIDAK kembali] "{t_pakai["judul"]}"')
print(f'      isi: "{t_pakai["isi"]}"')
cek('memuat "Kuota revisi sudah terpakai"',
    'Kuota revisi sudah terpakai' in t_pakai['isi'])
cek('memuat "Naskah kamu telah kembali"',
    'Naskah kamu telah kembali' in t_pakai['isi'])
cek('memuat "bisa dirapikan kapan saja"',
    'bisa dirapikan kapan saja' in t_pakai['isi'])
cek('DILARANG memuat "sudah pernah kamu lihat" (tolak Bos)',
    'pernah kamu lihat' not in t_pakai['isi'] and
    'karena' not in t_pakai['isi'].lower())

t_balik = N.pesan('naskah_kembali_kuota_balik', jumlah=2)
print(f'  [kuota KEMBALI] "{t_balik["judul"]}"')
print(f'      isi: "{t_balik["isi"]}"')
cek('menyebut jumlah Token Revisi', '2 Token Revisi' in t_balik['isi'])
#  ⚠️ Sebutan "EduAi" ada di JUDUL, bukan di isi — uji harus memeriksa
#  KEDUANYA. (Versi pertama uji ini salah ukur: hanya cek `isi` → GAGAL PALSU.
#  Pelajaran: jangan asal tunjuk satu field; periksa teks yang benar-benar
#  dilihat mahasiswa = judul + isi.)
_teks_balik = f"{t_balik['judul']} {t_balik['isi']}"
cek('memakai sebutan EduAi (judul atau isi)', 'EduAi' in _teks_balik,
    f'→ judul: "{t_balik["judul"]}"')
cek('DILARANG menyebut "AI" polos / "Wulan"',
    'Wulan' not in _teks_balik and
    ' AI ' not in _teks_balik.replace('EduAi', 'X'))
cek('nada kabar baik', t_balik['nada'] == 'kabar')

print('\n=== 8. NOTIFIKASI SELALU DIKIRIM ===')
db.execute(delete(PembatalanKuota).where(PembatalanKuota.user_id == UID,
                                         PembatalanKuota.file_id == FID))
#  ⚠️ WAJIB bersihkan notifikasi LAMA dulu. `catat()` punya ANTI-SPAM 24 jam
#  (kunci sama → ditolak). Versi pertama uji ini lupa membersihkan, jadi
#  panggilan ke-2 mengembalikan False → GAGAL PALSU. Anti-spam-nya sendiri
#  TERBUKTI BEKERJA di uji_pemicu_notifikasi.py kelompok 3.
db.execute(delete(Notifikasi).where(
    Notifikasi.user_id == UID,
    Notifikasi.jenis.in_(['naskah_kembali_kuota_terpakai',
                          'naskah_kembali_kuota_balik'])))
db.commit()
d1 = N.catat(db, UID, 'naskah_kembali_kuota_terpakai', file_id=FID)
db.commit()
cek('notifikasi kuota-terpakai tersimpan', d1 is True, f'→ {d1}')
d2 = N.catat(db, UID, 'naskah_kembali_kuota_balik', jumlah=2, file_id=FID)
db.commit()
cek('notifikasi kuota-balik tersimpan', d2 is True, f'→ {d2}')
#  Anti-spam: kirim ulang jenis yang sama → harus DITOLAK.
d3 = N.catat(db, UID, 'naskah_kembali_kuota_terpakai', file_id=FID)
db.commit()
cek('kiriman ULANG jenis sama ditolak (anti-spam)', d3 is False, f'→ {d3}')

#  bersihkan
db.execute(delete(PembatalanKuota).where(PembatalanKuota.user_id == UID,
                                         PembatalanKuota.file_id == FID))
db.execute(delete(ProsesAI).where(ProsesAI.kode == KODE))
db.execute(delete(Notifikasi).where(
    Notifikasi.user_id == UID,
    Notifikasi.jenis.in_(['naskah_kembali_kuota_terpakai',
                          'naskah_kembali_kuota_balik'])))
db.commit()
db.close()

print(f'\nHASIL: {lulus} LULUS / {gagal} GAGAL')
sys.exit(0 if gagal == 0 else 1)
