"""UJI RESMI EDUAI 2.5 — kelompok catatan per BAB (putusan Bos 24Sep26).

Uji 2 arah (standar Bos): SEHAT LULUS + DIRUSAK GAGAL.
Bentuk input sesuai produksi: rangkai() → dict {kepala, terbaru, anak}
dengan OBJEK CatatanPembimbing (atribut, bukan dict!).
"""
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, '/opt/data/services/eduai-publishing')
from app.kelompok_catatan import kelompokkan, _label_umum  # noqa: E402

LULUS, GAGAL = 0, []


def cek(nama, kondisi):
    global LULUS
    if kondisi:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL.append(nama)
        print(f'  ❌ {nama}')


def buat_catatan(cid, judul, baru, dibuat):
    """Objek seperti CatatanPembimbing (atribut, bukan dict)."""
    class _C:
        pass
    c = _C()
    c.id = cid
    c.induk_id = None
    c.ronde = 1
    c.section_judul = judul
    c.warna = 'kuning' if baru else 'hijau'
    c.dibuat = datetime.fromisoformat(dibuat)
    return c


kini = '2026-09-27 '
rantai = [
    {'kepala': buat_catatan(1, 'BAB I PENDAHULUAN', False, kini + '10:00:00'),
     'terbaru': buat_catatan(1, 'BAB I PENDAHULUAN', False, kini + '10:00:00'),
     'anak': []},
    {'kepala': buat_catatan(3, 'BAB II TINJAUAN PUSTAKA', True, kini + '08:00:00'),
     'terbaru': buat_catatan(3, 'BAB II TINJAUAN PUSTAKA', True, kini + '08:00:00'),
     'anak': []},
    {'kepala': buat_catatan(4, 'BAB II TINJAUAN PUSTAKA', True, kini + '07:00:00'),
     'terbaru': buat_catatan(4, 'BAB II TINJAUAN PUSTAKA', True, kini + '07:00:00'),
     'anak': []},
    {'kepala': buat_catatan(5, '', False, kini + '06:00:00'),
     'terbaru': buat_catatan(5, '', False, kini + '06:00:00'),
     'anak': []},
]

print('— kasus 1: naskah berbab —')
grup = kelompokkan(rantai, ada_bab=True, hari_ini=date(2026, 9, 27))
cek('ada kelompok', bool(grup))
cek('kelompok BAB I ada',
    any('BAB 1' in g.get('label', '') or 'BAB I' in g.get('label', '')
        for g in grup))
cek("catatan tanpa bab → 'Belum disebut bab-nya'",
    any('Belum disebut' in g.get('label', '') for g in grup))
terbuka = [g for g in grup if g.get('buka')]
cek('HANYA 1 terbuka', len(terbuka) == 1)
if terbuka:
    cek('terbuka = BAB II (2 baru > 0)',
        'BAB 2' in terbuka[0]['label'] or 'BAB II' in terbuka[0]['label'])

print('— kasus 2: dokumen tanpa BAB (jurnal) → per hari —')
grup2 = kelompokkan(rantai, ada_bab=False, hari_ini=date(2026, 9, 27))
cek('kelompok tetap ada (per hari)', bool(grup2))
cek("ada label 'Hari ini'", any(g.get('label') == 'Hari ini' for g in grup2))

print('— kasus 3: label tanggal jujur —')
cek("kemarin → 'Kemarin'",
    _label_umum('2026-09-26', date(2026, 9, 27)) == 'Kemarin')
cek('tanggal rusak tidak bohong Hari ini',
    'Hari ini' not in _label_umum('tanggal-rusak', date(2026, 9, 27)))

print('— kasus 4 (uji bisa gagal): rantai kosong → hasil kosong, bukan jebol —')
try:
    g4 = kelompokkan([], ada_bab=True)
    cek('rantai kosong → []', g4 == [])
except Exception as e:
    cek(f'rantai kosong jebol: {e}', False)

print()
print(f'HASIL: {LULUS} LULUS / {len(GAGAL)} GAGAL')
if GAGAL:
    print('GAGAL:', GAGAL)
    sys.exit(1)
print('SEMUANYA LULUS ✅')
