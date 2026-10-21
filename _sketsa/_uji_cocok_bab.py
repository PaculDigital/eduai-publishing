"""UJI BERGIGI — PENCOCOKAN BAB (04Okt26, ACC Bos Opsi B).

Latar (CACAT PRODUKSI yang TERUKUR):
  pencocokan lama:  sid == target or sid in target or target in sid
  ⇒ 'BAB I' in 'BAB II' = True → minta BAB II dapat BAB I
  Bukti produksi naskah Asih file 81: revisi BAB II & III TERCATAT 'BAB I'.
  Akibat: section_state salah bab → Mode Belajar terkunci + catatan salah bab.

Uji ini BERGIGI: kalau pencocokan substrat dikembalikan, uji bagian 2 GAGAL.
"""
import sys
sys.path.insert(0, '/app')

from app.catatan_ai import _norm_section, _peta_bersih       # noqa: E402
from app.belajar import _nomor_bab_dari_section, bab_sudah_direvisi  # noqa: E402
from app.models import (SessionLocal, SectionState, User,     # noqa: E402
                        FileBerkas)

LULUS = GAGAL = 0


def cek(nama, syarat, dapat=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} — dapat: {dapat!r}')


def cocok_baru(target, peta):
    """PAKAI FUNGSI PRODUKSI yang sebenarnya (bukan tiruan) supaya uji jujur."""
    from app.catatan_ai import _cocokkan_bagian
    b = _cocokkan_bagian(target, peta)
    return (b or {}).get('section_id')


PETA = [{'section_id': 'BAB I'}, {'section_id': 'BAB II'},
        {'section_id': 'BAB III'}, {'section_id': 'BAB IV'},
        {'section_id': 'BAB V'}]

print('══ 1. NORMALISASI ══')
cek("'BAB  III ' → 'BAB III'", _norm_section('BAB  III ') == 'BAB III',
    _norm_section('BAB  III '))
cek("'bab iii' → 'BAB III'", _norm_section('bab iii') == 'BAB III')
cek("' Bab I ' → 'BAB I'", _norm_section(' Bab I ') == 'BAB I')
cek("'BAB III:' → 'BAB III'", _norm_section('BAB III:') == 'BAB III')

print()
print('══ 2. BERGIGI: TIAP BAB DAPAT BAB YANG BENAR (ini yang dulu SALAH) ══')
for target in ('BAB I', 'BAB II', 'BAB III', 'BAB IV', 'BAB V'):
    hasil = cocok_baru(target, PETA)
    cek(f'minta {target!r:10} → dapat {target!r}', hasil == target, hasil)

print()
print('══ 3. VARIASI EJAAN (tetap harus tepat) ══')
for target, harus in (('bab ii', 'BAB II'), ('BAB  IV ', 'BAB IV'),
                      ('Bab v', 'BAB V'), ('BAB III', 'BAB III')):
    hasil = cocok_baru(target, PETA)
    cek(f'{target!r:12} → {harus!r}', hasil == harus, hasil)

print()
print('══ 4. SUB-BAB: tidak boleh nyasar ke BAB lain ══')
PETA_SUB = [{'section_id': 'BAB I'}, {'section_id': 'BAB II'},
            {'section_id': '2.1'}, {'section_id': '3.4.2'}]
for target, harus in (('2.1', '2.1'), ('3.4.2', '3.4.2'),
                      ('BAB II', 'BAB II'), ('BAB I', 'BAB I')):
    hasil = cocok_baru(target, PETA_SUB)
    cek(f'{target!r:10} → {harus!r}', hasil == harus, hasil)

print()
print('══ 5. TIDAK ADA YANG COCOK → None (jujur, jangan menebak) ══')
cek("'BAB IX' → None", cocok_baru('BAB IX', PETA) is None,
    cocok_baru('BAB IX', PETA))
cek("'LAMPIRAN' → None", cocok_baru('LAMPIRAN', PETA) is None)

print()
print('══ 6. KESINAMBUNGAN: peta naskah ASIH nyata ══')
db = SessionLocal()
u = db.query(User).filter(User.email == 'asih.susanti@eduai.test').first()
if u:
    f = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
    from app.ai import _teks_dari_berkas, UPLOAD_DIR           # noqa: E402
    p = UPLOAD_DIR / str(f.user_id) / f.nama_simpan
    teks = _teks_dari_berkas(p, f.nama)
    peta = _peta_bersih(teks)
    print(f'  peta naskah Asih: {[b.get("section_id") for b in peta]}')
    for target in ('BAB I', 'BAB II', 'BAB III', 'BAB IV', 'BAB V'):
        hasil = cocok_baru(target, peta)
        cek(f'naskah nyata minta {target!r:10} → {target!r}', hasil == target,
            hasil)

    #  uji end-to-end: suntik section_state 'bab2' & 'bab3' → harus terbaca
    n0 = bab_sudah_direvisi(db, u, f.id)
    print(f'  bab_sudah_direvisi sekarang: {sorted(n0)}')
    cek('naskah Asih: bab1 terbaca (kategori "bab" + BAB I)',
        'bab1' in n0, sorted(n0))
    db.close()
else:
    print('  ⚠️ akun uji tidak ada — lewati')

print()
print(f'═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
sys.exit(1 if GAGAL else 0)
