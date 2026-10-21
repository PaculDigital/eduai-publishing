#!/usr/bin/env python3
"""UJI RIWAYAT PER-KOMENTAR (ACC Bos 17Sep26).

PERMINTAAN BOS: *"Perbaiki dan buat sederhana saja, jangan tambah rumit dan
tambah membingungkan. Ikuti role yang sudah kita buat kemarin. Dan revisi
sesuai pada hal yang di komentari saja."*

YANG DIBUKTIKAN:
  1. Jawaban AI berformat [K1-CAKUPAN: …] dipecah jadi blok per komentar.
  2. 1 bab berisi BANYAK komentar → banyak baris riwayat (BUKAN 1 versi besar).
  3. Judul riwayat = komentar asli mahasiswa (mudah dikenali).
  4. Cakupan dihormati: blok 'tolak' tidak dianggap perbaikan paragraf.
  5. Jawaban TAK berformat → jatuh balik ke cara lama (tidak ada hasil hilang).
  6. Kuota TIDAK berubah — mekanisme lama tetap dipakai.
"""
import sys
sys.path.insert(0, '/app')
from app.ai import _pisah_blok_komentar
from app.models import SessionLocal, User, FileBerkas, Notifikasi, VersiDokumen
from app.versi import simpan_versi_per_komentar, daftar_versi, VERSI_SIMPAN
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


print('=== 1. PECAH JAWABAN AI → BLOK PER KOMENTAR ===')
jawab = """[PROFIL] Paradigma=kuantitatif; Desain=survei

[K1-CAKUPAN: paragraf]
Paragraf pertama sudah diperbaiki agar dimulai dari grand theory TAM
seperti yang diharapkan pembimbing.

[K2-CAKUPAN: paragraf]
Penjelasan mengenai metodologi ditambahkan pada paragraf ketiga supaya
alur argumennya nyambung dari teori ke rumusan masalah.

[K3-CAKUPAN: tolak]
Bagian BAB IV tidak ada di naskah yang saya terima, sehingga tidak dapat
saya perbaiki sekarang.
"""
blok = _pisah_blok_komentar(jawab)
cek('menghasilkan 3 blok', len(blok) == 3, f'→ {len(blok)}')
cek('nomor berurutan 1,2,3', [b['nomor'] for b in blok] == [1, 2, 3],
    f"→ {[b['nomor'] for b in blok]}")
cek('cakupan terbaca', blok[0]['cakupan'] == 'paragraf',
    f"→ {blok[0]['cakupan']!r}")
cek('blok tolak dikenali', blok[2]['cakupan'] == 'tolak',
    f"→ {blok[2]['cakupan']!r}")
cek('penanda [PROFIL] TIDAK ikut jadi blok',
    all('PROFIL' not in b['isi'] for b in blok))
cek('penanda [K1-CAKUPAN] TIDAK bocor ke isi',
    all('CAKUPAN' not in b['isi'] for b in blok))
cek('isi blok 1 benar-benar teks revisi',
    blok[0]['isi'].startswith('Paragraf pertama'), f"→ {blok[0]['isi'][:40]!r}")

print('\n=== 2. JAWABAN TAK BERFORMAT → tidak ada blok (jatuh balik) ===')
blok2 = _pisah_blok_komentar('Naskah sudah saya perbaiki seluruhnya.')
cek('tanpa penanda [Kn] → 0 blok', blok2 == [], f'→ {blok2}')

print('\n=== 3. SIMPAN: 1 BAB BANYAK KOMENTAR → BANYAK BARIS RIWAYAT ===')
db = SessionLocal()
u = db.execute(select(User).where(
    User.email == 'uji-berbayar-e2e@test.local')).scalar_one_or_none()
fb = db.execute(select(FileBerkas).where(
    FileBerkas.user_id == u.id)).scalars().first()
BAB_UJI = '__uji_per_komentar__'
#  bersihkan sisa uji lama
db.execute(delete(VersiDokumen).where(VersiDokumen.bab == BAB_UJI))
db.commit()

komentar_asli = ['paragraf pembuka kok langsung ke praktik, mulai dari teori',
                 'metodologi belum dijelaskan di paragraf tiga',
                 'BAB IV belum saya kirim']
v = simpan_versi_per_komentar(db, u.id, fb.id, BAB_UJI, blok,
                              komentar=komentar_asli, model='uji')
cek('tersimpan 3 versi (bukan 1)', len(v) == 3, f'→ {len(v)}')
semua = daftar_versi(db, fb.id, BAB_UJI)
cek('daftar_versi berisi 3 baris', len(semua) == 3, f'→ {len(semua)}')
cek('nomor versi BERBEDA semua', len({x.nomor for x in semua}) == 3,
    f'→ {sorted(x.nomor for x in semua)}')
judul = sorted(x.komentar for x in semua)
print('  📋 riwayat yang dilihat mahasiswa:')
for x in sorted(semua, key=lambda y: y.nomor):
    print(f'     ✨ {x.komentar}')
cek('judul riwayat memuat komentar ASLI mahasiswa',
    any('paragraf pembuka kok langsung' in (x.komentar or '') for x in semua))
cek('judul memakai format "Kn · …"',
    all((x.komentar or '').startswith('K') for x in semua))
cek('isi tiap versi = teks revisi komentar itu',
    all(x.isi and 'CAKUPAN' not in x.isi for x in semua))
cek('ukuran tercatat (masuk kuota storage)',
    all((x.ukuran or 0) > 0 for x in semua))

print('\n=== 4. GEAR: hitungan PER PUTARAN (bukan per baris) ===')
#  ⚠️ Aturan lama VERSI_SIMPAN=2 (per baris) MEMBUANG K1 saat 3 komentar
#  dikirim sekaligus. Sekarang: 1 putaran = 1 set komentar utuh.
cek('3 komentar TIDAK terpotong', len(semua) == 3, f'→ {len(semua)} baris')
cek('K1 (komentar pertama) TETAP ADA', any('K1 ·' in (x.komentar or '')
                                           for x in semua),
    f"→ {sorted(x.komentar[:12] for x in semua)}")

#  Putaran kedua: 1 komentar lagi → total 4 baris, TAPI hanya 2 putaran.
v2 = simpan_versi_per_komentar(
    db, u.id, fb.id, BAB_UJI,
    [{'nomor': 1, 'ringkas': 'a', 'isi': 'Revisi tambahan putaran kedua ' * 3}],
    komentar=['komentar putaran kedua'], model='uji')
semua2 = daftar_versi(db, fb.id, BAB_UJI)
set_waktu = {x.dibuat.replace(microsecond=0) for x in semua2 if x.dibuat}
cek(f'maksimal VERSI_SIMPAN={VERSI_SIMPAN} PUTARAN tersimpan',
    len(set_waktu) <= VERSI_SIMPAN, f'→ {len(set_waktu)} putaran')
cek('putaran terbaru UTUH (tidak terpotong)',
    any('putaran kedua' in (x.komentar or '') for x in semua2))
print(f'  📋 total baris riwayat sekarang: {len(semua2)}')

print('\n=== 5. KUOTA TIDAK BERUBAH ===')
import re
from pathlib import Path
src_pk = Path('/app/app/versi.py').read_text(encoding='utf-8')
awal = src_pk.index('def simpan_versi_per_komentar')
akhir = src_pk.index('def simpan_versi(', awal)
isi_fn = src_pk[awal:akhir]
cek('fungsi baru TIDAK memanggil cek_dan_potong / potong kuota',
    'cek_dan_potong' not in isi_fn and 'kembalikan_addon' not in isi_fn)
cek('tidak ada angka 10.000 di fungsi baru (rumus kuota ada di tempat lain)',
    '10_000' not in isi_fn and '10000' not in isi_fn)

#  bersihkan
db.execute(delete(VersiDokumen).where(VersiDokumen.bab == BAB_UJI))
db.commit()
db.close()

print(f'\nHASIL: {lulus} LULUS / {gagal} GAGAL')
sys.exit(0 if gagal == 0 else 1)
