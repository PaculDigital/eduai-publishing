"""UJI BERGIGI: Jev menilai balasan AI — pagar tetap kuat?

Menguji `app.satpam.nilai_balasan()` dengan 9router DIPALSUKAN (tanpa panggilan
nyata) supaya cepat & bisa diulang. Yang diperiksa BUKAN teks, tapi KEPUTUSAN:

  1. Pagar P8: rasio > batas KERAS → tolak TANPA memanggil jev (hemat + aman)
  2. Jev bilang "ngawur" (yakin) → TOLAK
  3. Jev bilang "wajar" (yakin ≥0,80) → LOLOS
  4. Jev bilang "wajar" TAPI ragu (<0,80) → TOLAK (P7, pagar tetap kuat)
  5. Jev tidak bisa dihubungi → TOLAK (perilaku lama)
  6. Jev balas sampah → TOLAK (P7)
  7. Pagar MATI (AKTIF=0) → TOLAK (perilaku lama persis)

Cara palsukan: ganti `satpam.urllib.request.urlopen` dengan palsu.
"""
import io
import json
import sys
import types

sys.path.insert(0, '/app')
from app import satpam  # noqa: E402


def _balasan(choice: str, conf: float, sesuai: str = 'ya',
             sisip: str = 'tidak') -> str:
    """Bentuk balasan 9router yang berisi 3 jawaban jev.

    Jejak uji 05Okt26: uji pertama hanya mengisi 'ngawur', padahal jev
    SUNGGUHAN menjawab 3 pertanyaan sekaligus — uji harus menirukan ketiganya.
    """
    isi = json.dumps({'answers': {
        'ngawur': {'choice': choice, 'confidence': conf, 'noul': 'test'},
        'sesuai_tugas': {'choice': sesuai, 'confidence': 0.9, 'noul': 'test'},
        'menyisipkan': {'choice': sisip, 'confidence': 0.9, 'noul': 'test'},
    }})
    return json.dumps({'choices': [{'message': {'content': isi}}]})


def palsukan(balasan: str | None, naikkan_galat: bool = False):
    """Pasang urlopen palsu. balasan=None + naikkan_galat=True → galat jaringan."""
    def urlopen(req, timeout=None):
        if naikkan_galat:
            raise OSError('Connection refused (palsu)')
        return io.BytesIO(balasan.encode())
    asli = satpam.urllib.request.urlopen
    satpam.urllib.request.urlopen = urlopen
    return asli


def pulihkan(asli):
    satpam.urllib.request.urlopen = asli


kutip = 'Penelitian ini bertujuan mengetahui pengaruh harga terhadap keputusan.'
paragraf = kutip + ' Data dikumpulkan dari 200 responden di Kota Bandung. '
ganti_panjang = 'Latar belakang penelitian ini sangat penting. ' * 60   # ~2.700 kar

tugas = 'PERDALAM'

# (nama, balasan_palsu, galat_jaringan, rasio, batas, harus)
KASUS = [
    ('P8: rasio 18× > batas keras 10× → tolak TANPA panggil jev',
     _balasan('tidak_sah_wajar', 0.99), False, 18.0, 336, 'tolak'),
    ('jev: NGAWUR yakin 0,95 → TOLAK',
     _balasan('ya_ngawur', 0.95), False, 8.0, 336, 'tolak'),
    ('jev: WAJAR yakin 0,90 → LOLOS',
     _balasan('tidak_sah_wajar', 0.90), False, 8.0, 336, 'lolos'),
    ('jev: WAJAR tapi RAGU 0,60 → TOLAK (P7)',
     _balasan('tidak_sah_wajar', 0.60), False, 8.0, 336, 'tolak'),
    ('jev: tidak bisa dihubungi → TOLAK (perilaku lama)',
     None, True, 8.0, 336, 'tolak'),
    ('jev: balasan sampah → TOLAK (P7)',
     'ini bukan json sama sekali', False, 8.0, 336, 'tolak'),
    ('jev: pilihan tak dikenal → TOLAK (P7)',
     _balasan('entahlah', 0.99), False, 8.0, 336, 'tolak'),
    ('jev: WAJAR tapi TIDAK sesuai tugas → TOLAK',
     _balasan('tidak_sah_wajar', 0.95, sesuai='tidak'), False, 8.0, 336, 'tolak'),
    ('jev: WAJAR tapi MENYISIPKAN bagian baru → TOLAK',
     _balasan('tidak_sah_wajar', 0.95, sisip='ya'), False, 8.0, 336, 'tolak'),
]

print('═' * 100)
print('  UJI BERGIGI: jev menilai balasan AI (9router DIPALSUKAN)')
print('═' * 100)
lulus = gagal = 0
for nama, b, err, rasio, batas, harus in KASUS:
    asli = palsukan(b, err)
    try:
        h = satpam.nilai_balasan(kutip, paragraf, ganti_panjang, tugas, rasio, batas)
        dapat = h.get('keputusan')
    finally:
        pulihkan(asli)
    ok = (dapat == harus)
    lulus += ok
    gagal += (not ok)
    print(f'  {"✅" if ok else "❌"} {nama:<52} → {dapat:<7} (harus {harus})')

# ── Pagar MATI → perilaku lama persis ────────────────────────────────────
print()
print('── PAGAR MATI (EDUAI_JEV_NILAI_AKTIF=0) → TOLAK, perilaku lama persis ──')
aktif_asli = satpam.AKTIF_NILAI
satpam.AKTIF_NILAI = False
asli = palsukan(_balasan('tidak_sah_wajar', 0.99))
try:
    h = satpam.nilai_balasan(kutip, paragraf, ganti_panjang, tugas, 8.0, 336)
    dapat = h.get('keputusan')
finally:
    pulihkan(asli)
    satpam.AKTIF_NILAI = aktif_asli
ok = (dapat == 'tolak')
lulus += ok
gagal += (not ok)
print(f'  {"✅" if ok else "❌"} {"jev dimatikan → tetap TOLAK":<52} → {dapat:<7} (harus tolak)')
print(f'        alasan: {h.get("alasan")}')

print()
print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
sys.exit(0 if gagal == 0 else 1)
