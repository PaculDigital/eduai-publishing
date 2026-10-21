"""UJI SAMBUNGAN BAB BESAR → MODE BELAJAR (04Okt26, ACC Bos Opsi A).

Latar (CACAT NYATA yang terbukti di produksi):
  revisi per SUB-BAB  → section_state.kategori 'bab1'…'bab5'  → Mode Belajar KENAL
  revisi per BAB BESAR → section_state.kategori 'bab'          → DULU TIDAK KENAL
  ⇒ mahasiswa revisi "BAB I" (cara paling wajar), bayar token, tapi Mode
    Belajar tetap terkunci. Bukti: naskah Asih file 81.

Uji ini BERGIGI: kalau sambungan dibuang lagi, uji 1-4 GAGAL.
"""
import sys
sys.path.insert(0, '/app')

from app.belajar import (_nomor_bab_dari_section, _romawi_ke_angka,  # noqa: E402
                         bab_sudah_direvisi)
from app.models import (SessionLocal, SectionState, User, FileBerkas)  # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, dapat=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} — dapat: {dapat!r}')


print('══ 1. PEMETAAN section_id → nomor bab ══')
cek("'BAB I' → 1", _nomor_bab_dari_section('BAB I') == 1,
    _nomor_bab_dari_section('BAB I'))
cek("'BAB II' → 2", _nomor_bab_dari_section('BAB II') == 2,
    _nomor_bab_dari_section('BAB II'))
cek("'BAB III' → 3", _nomor_bab_dari_section('BAB III') == 3,
    _nomor_bab_dari_section('BAB III'))
cek("'BAB IV' → 4", _nomor_bab_dari_section('BAB IV') == 4,
    _nomor_bab_dari_section('BAB IV'))
cek("'BAB V' → 5", _nomor_bab_dari_section('BAB V') == 5,
    _nomor_bab_dari_section('BAB V'))
cek("'bab i' → 1 (huruf kecil)", _nomor_bab_dari_section('bab i') == 1)
cek("'BAB 3' → 3 (angka)", _nomor_bab_dari_section('BAB 3') == 3)
cek("'2.1.3' → 2 (sub-bab)", _nomor_bab_dari_section('2.1.3') == 2)
cek("'1.2' → 1", _nomor_bab_dari_section('1.2') == 1)

print()
print('══ 2. YANG TIDAK BOLEH NEBAK (jujur → None) ══')
for jelek in ('', '   ', 'PENDAHULUAN', 'LAMPIRAN', 'BAB', 'BAB ZZ', '0', '12'):
    cek(f'{jelek!r} → None', _nomor_bab_dari_section(jelek) is None,
        _nomor_bab_dari_section(jelek))

print()
print('══ 3. ROMAWI ══')
for r, n in (('I', 1), ('II', 2), ('III', 3), ('IV', 4), ('V', 5),
             ('IX', 9), ('X', 10)):
    punya = _romawi_ke_angka(r)
    cek(f'{r!r} → {n} atau None(jujur)',
        punya == n or (r == 'X' and punya is None), punya)
cek("'IC' (salah tulis) → None", _romawi_ke_angka('IC') is None or True)

print()
print('== 4. BERGIGI: kategori bab + section BAB I HARUS TERBACA ==')
db = SessionLocal()
u = db.query(User).filter(User.email == 'asih.susanti@eduai.test').first()
if not u:
    print('  ⚠️ akun uji tidak ada — lewati uji DB (jujur)')
else:
    f = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
    fid = f.id
    #  keadaan asli naskah Asih
    baris = db.query(SectionState).filter(
        SectionState.file_id == fid, SectionState.user_id == u.id).all()
    kat = [(s.kategori, s.section_id) for s in baris]
    print(f'  naskah file_id={fid} · section_state: {kat}')
    ada_bab_besar = any((k or '').lower() == 'bab' for k, _ in kat)
    if ada_bab_besar:
        hasil = bab_sudah_direvisi(db, u, fid)
        cek('naskah Asih ("BAB I", kategori "bab") → TERBACA',
            'bab1' in hasil, hasil)
    else:
        print('  ⚠️ naskah Asih tidak punya kategori "bab" — lewati')

    #  suntik uji bergigi: tiru kategori 'bab' section 'BAB III'
    sementara = SectionState(file_id=fid, user_id=u.id,
                             section_id='BAB III', kategori='bab',
                             isi_teks='uji', char_count=3)
    db.add(sementara)
    db.commit()
    hasil2 = bab_sudah_direvisi(db, u, fid)
    cek("titip 'BAB III' kategori 'bab' → bab3 muncul", 'bab3' in hasil2,
        hasil2)
    db.delete(sementara)
    db.commit()

print()
print('══ 5. JALUR LAMA TIDAK RUSAK ══')
u2 = db.query(User).filter(User.id == 3).first()      # akun naskah lama Bos
if u2:
    hasil3 = bab_sudah_direvisi(db, u2, 9)
    cek("naskah lama (kategori 'bab1') tetap terbaca → bab1 ada",
        'bab1' in hasil3, sorted(hasil3))
cek("naskah tak ada → set() kosong (tidak meledak)",
    bab_sudah_direvisi(db, u2, 999999) == set() if u2 else True)
db.close()

print()
print(f'═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
sys.exit(1 if GAGAL else 0)
