"""GERBANG: hemat token asisten pembimbing (15Okt26).

MENGUJI APA:
  A. Naskah NASKAH PANJANG → yang dikirim ke AI harus JAUH lebih kecil
     dari naskah utuh (bukan klaim, diukur).
  B. Naskah PENDEK → tetap kirim utuh (pagar: tak ada gunanya memecah).
  C. Gagal apa pun → JALUR LAMA (naskah utuh). Tinjauan TIDAK pernah gagal.
  D. Bagian target DIGILIR → operasi berikutnya meninjau bagian LAIN
     (seluruh naskah kebagian, bukan cuma bab pertama).
  E. Isi bagian target BENAR-BENAR ada di teks yang dikirim.
  F. `simpan_usulan()` TETAP memakai naskah UTUH (pencari kutipan tidak
     ikut dipotong — kalau ikut, sorotan jadi palsu).

CARA JALAN (WAJIB DI DALAM CONTAINER):
    docker cp _uji_hemat_asisten.py eduai-app:/tmp/g.py
    docker exec eduai-app sh -c 'cd /app && python3 /tmp/g.py'
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, '/app')

LULUS, GAGAL = 0, 0


def cek(nama: str, syarat: bool, tambahan: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}{(" — " + tambahan) if tambahan else ""}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}{(" — " + tambahan) if tambahan else ""}')


print('═' * 70)
print('  GERBANG HEMAT TOKEN — ASISTEN PEMBIMBING')
print('═' * 70)

# ── Bangun naskah uji panjang (5 bab, mirip skripsi) ──────────────────────
def _satu_bab(n: int, judul: str) -> str:
    t = f'BAB {n} {judul}\n\n'
    for i in range(12):
        t += ('Ini paragraf %d pada bab tersebut. ' % i
              + 'Penjelasan panjang ' * 20 + '\n\n')
    return t


NASKAH_PANJANG = ''
for i, j in enumerate(['PENDAHULUAN', 'KAJIAN TEORI', 'METODE PENELITIAN',
                       'HASIL DAN PEMBAHASAN', 'KESIMPULAN'], start=1):
    NASKAH_PANJANG += _satu_bab(i, j)
JUDUL_SEMUA = ['PENDAHULUAN', 'KAJIAN TEORI', 'METODE PENELITIAN',
               'HASIL DAN PEMBAHASAN', 'KESIMPULAN']

print(f'\n[i] naskah uji: {len(NASKAH_PANJANG)} karakter\n')

from app import asisten as A                                   # noqa: E402

# ── A & E: naskah panjang dipecah, isi target ikut terkirim ───────────────
print('— A/E: naskah PANJANG → dipecah, isi target ikut —')
peta = A._bagian_dari(NASKAH_PANJANG)
cek('naskah panjang terbaca jadi >1 bagian', len(peta) > 1,
    f'{len(peta)} bagian')

#  DB tiruan sederhana untuk giliran (tanpa SQLAlchemy nyata)
class _DBTiruan:
    def __init__(self): self.data = {}
    def scalar(self, _stmt): return None
    def add(self, _obj): pass


kirim, mulai = A._siapkan_kirim(_DBTiruan(), type('B', (), {'id': 1})(),
                                NASKAH_PANJANG)
cek('yang dikirim lebih kecil dari naskah utuh', len(kirim) < len(NASKAH_PANJANG),
    f'{len(kirim)} kar vs {len(NASKAH_PANJANG)} kar')
persen = 100.0 * (len(NASKAH_PANJANG) - len(kirim)) / len(NASKAH_PANJANG)
cek('hemat minimal 30%', persen >= 30, f'hemat {persen:.1f}%')

judul_terkirim = [j for j in JUDUL_SEMUA if j in kirim]
cek('judul bab target ikut terkirim', len(judul_terkirim) >= 1,
    f'{judul_terkirim}')
cek('penanda isi bagian ada di teks kiriman',
    'ISI BAGIAN YANG DIREVISI' in kirim)
cek('penanda tugasan ada di teks kiriman', 'TUGAS SAAT INI' in kirim)
cek('penanda tetangga (konteks) ada', 'konteks' in kirim.lower())
cek('nomor bagian dikembalikan (bukan -1)', mulai != -1, f'mulai={mulai}')

# ── B: naskah pendek tetap utuh ───────────────────────────────────────────
print('\n— B: naskah PENDEK → tetap utuh —')
PENDEK = 'BAB I PENDAHULUAN\n\nNaskah pendek saja, tidak perlu dipecah.\n'
kirim2, mulai2 = A._siapkan_kirim(_DBTiruan(), type('B', (), {'id': 2})(), PENDEK)
cek('naskah pendek dikirim UTUH', kirim2 == PENDEK, f'{len(kirim2)} kar')
cek('penanda -1 (jalur lama)', mulai2 == -1)

# ── C: gagal → jalur lama ─────────────────────────────────────────────────
print('\n— C: mesin pecah GAGAL → jalur lama (naskah utuh) —')
_simpan = A._bagian_dari
A._bagian_dari = lambda _t: (_ for _ in ()).throw(RuntimeError('sengaja rusak'))
try:
    kirim3, mulai3 = A._siapkan_kirim(_DBTiruan(), type('B', (), {'id': 3})(),
                                      NASKAH_PANJANG)
    cek('gagal → kirim naskah UTUH (tinjauan tetap jalan)', kirim3 == NASKAH_PANJANG)
    cek('gagal → penanda -1', mulai3 == -1)
finally:
    A._bagian_dari = _simpan

# ── D: giliran berjalan (seluruh naskah kebagian) ─────────────────────────
print('\n— D: GILIRAN → tiap operasi meninjau bagian berbeda —')
from sqlalchemy import select as _select                       # noqa: E402
from app.models import Setelan, SessionLocal                  # noqa: E402

try:
    S = SessionLocal()
    try:
        bid = 999_001
        kunci_uji = f'asisten_giliran_{bid}'
        row = S.scalar(_select(Setelan).where(Setelan.kunci == kunci_uji))
        if row is not None:
            S.delete(row)
            S.commit()

        terlihat = []
        for _putaran in range(3):
            _kirim_n, mulai_n = A._siapkan_kirim(
                S, type('B', (), {'id': bid})(), NASKAH_PANJANG)
            S.commit()
            terlihat.append(mulai_n)
        cek('3 operasi berurutan meninjau posisi BERBEDA',
            len(set(terlihat)) > 1, f'posisi: {terlihat}')
        cek('giliran tidak diam di 0',
            any(t != 0 for t in terlihat), f'posisi: {terlihat}')

        row = S.scalar(_select(Setelan).where(Setelan.kunci == kunci_uji))
        cek('giliran benar-benar TERSIMPAN di tabel `setelan`',
            row is not None, f'nilai={getattr(row, "nilai", None)}')
        cek('kunci giliran muat di kolom String(60)', len(kunci_uji) <= 60,
            f'{len(kunci_uji)} kar')

        #  bersihkan
        if row is not None:
            S.delete(row)
            S.commit()
    finally:
        S.close()
except Exception as e:                                          # noqa: BLE001
    cek('giliran tersimpan di tabel `setelan`', False, f'{type(e).__name__}: {e}')

# ── F: pencari kutipan TETAP pakai naskah utuh ────────────────────────────
print('\n— F: pencari kutipan TIDAK ikut dipotong —')
import inspect                                                  # noqa: E402
sumber = inspect.getsource(A.simpan_usulan)
cek('simpan_usulan() masih memakai naskah_bimbingan() (utuh)',
    'naskah_bimbingan(db, b)' in sumber)
cek('simpan_usulan() TIDAK memakai _siapkan_kirim',
    '_siapkan_kirim' not in sumber)

# ── G: PAGAR — permintaan MENYELURUH → kirim UTUH (15Okt26) ───────────────
print('\n— G: PAGAR `_boleh_konteks` → permintaan menyeluruh kirim UTUH —')

#  G1: _boleh_potong() memanggil pemeriksa yang SUDAH ADA (bukan salinan)
_ada_konteks = hasattr(A, '_boleh_potong') and hasattr(A, '_catatan_terbaru')
cek('G1 asisten punya pagar `_boleh_potong` + `_catatan_terbaru`', _ada_konteks)

try:
    from app.ai import _boleh_konteks as _cek_ai            # noqa: E402
    cek('G2 asisten MENEKAN tombol yang sama dengan revisi mahasiswa '
        '(`ai._boleh_konteks` ADA)', callable(_cek_ai))
except Exception as e:                                        # noqa: BLE001
    cek('G2 `ai._boleh_konteks` bisa dipanggil', False, f'{e}')

#  G3: komentar NETRAL → boleh dipotong
_potong_netral = A._boleh_potong(['Tolong perbaiki ejaan di paragraf ini.'])
cek('G3 komentar netral → boleh dipotong (hemat tetap jalan)',
    _potong_netral is True, f'{_potong_netral}')

#  G4: komentar MENYELURUH → TIDAK boleh dipotong  ← INI INTI PAGARNYA
#  🚨 PELAJARAN 15Okt26: kalimat uji WAJIB diambil DARI DAFTAR ATURAN
#     (`parser._KATA_ALUR` × `parser._KATA_SEMUA`), JANGAN dikarang dari
#     ingatan. Wulan sempat menulis "perbaiki alur di semua bab" — itu
#     BUKAN pemicu (kata kerjanya harus 'ubah/ganti/rombak'), jadi uji
#     itu GAGAL PALSU: yang salah KALIMAT UJINYA, bukan pagarnya.
_kalimat_alur = [
    'Ubah alur seluruh naskah supaya benang ceritanya nyambung dari awal.',
    'Ganti alur seluruh dokumen jadi induktif.',
    'Rombak alur dan semua bab sekaligus.',
    'Ubah paradigma penelitian di semua bab.',
]
_hasil_alur = [(k[:36], A._boleh_potong([k])) for k in _kalimat_alur]
cek('G4 komentar pemicu ALUR+DOKUMEN → WAJIB utuh',
    all(h is False for _, h in _hasil_alur),
    ' | '.join(f'{k}→{h}' for k, h in _hasil_alur))

#  G4b: pemicu alur TANPA cakupan dokumen (×4) juga wajib utuh
cek('G4b "ubah alur" tanpa sebut cakupan → tetap utuh',
    A._boleh_potong(['Ubah alur berpikir di bab ini.']) is False)

#  G4c: KONFIRMASI ke daftar aturan — kata uji harus benar-benar ada
#       di `parser._KATA_ALUR`/`_KATA_SEMUA`. Kalau tidak, uji ini palsu.
try:
    from app.parser import _KATA_ALUR as _KA, _KATA_SEMUA as _KS  # noqa: E402
    _pemicu_ada = all(any(x in k.lower() for x in _KA) for k in _kalimat_alur)
    cek('G4c semua kalimat uji memuat pemicu NYATA dari `parser._KATA_ALUR`',
        _pemicu_ada, f'{len(_KA)} pemicu resmi diperiksa')
    cek('G4d pemicu cakupan dokumen ikut ada (`_KATA_SEMUA`)',
        any(any(x in k.lower() for x in _KS) for k in _kalimat_alur))
except Exception as e:                                        # noqa: BLE001
    cek('G4c pemicu resmi bisa dibaca', False, f'{e}')

#  G4e: kalimat yang memang BUKAN pemicu → tetap boleh dipotong.
#       Ini mengunci PERILAKU yang benar (bukan bug): 'perbaiki alur'
#       tidak menaikkan pengali — rancangan lama, di luar tugas pagar ini.
cek('G4e "perbaiki alur di semua bab" (bukan pemicu resmi) → tetap potong',
    A._boleh_potong(['Tolong perbaiki alur di semua bab.']) is True,
    'sesuai `parser._KATA_ALUR` — bukan bug')

#  G5: tidak ada komentar → boleh dipotong (target sudah jelas dari UI)
cek('G5 tanpa komentar → boleh dipotong', A._boleh_potong([]) is True)

#  G6: NYATA — `_siapkan_kirim` benar-benar MENGIRIM UTUH saat pagar menutup.
#      Caranya: palsukan `_catatan_terbaru` supaya mengembalikan komentar
#      menyeluruh, lalu pastikan teks yang dikirim == naskah utuh.
_asli_catatan = A._catatan_terbaru
A._catatan_terbaru = lambda _db, _bid, batas=12: _kalimat_alur
try:
    kirim_pagar, mulai_pagar = A._siapkan_kirim(
        _DBTiruan(), type('B', (), {'id': 4})(), NASKAH_PANJANG)
    cek('G6 pagar menutup → `_siapkan_kirim` kirim naskah UTUH',
        kirim_pagar == NASKAH_PANJANG,
        f'{len(kirim_pagar)} kar (harusnya {len(NASKAH_PANJANG)})')
    cek('G6b penanda -1 (jalur lama)', mulai_pagar == -1)
finally:
    A._catatan_terbaru = _asli_catatan

#  G7: UJI BERGIGI — kalau pagar DIMATIKAN, naskah jadi DIPOTONG lagi.
#      Ini bukti pagarnya yang bekerja, bukan kebetulan.
A._catatan_terbaru = lambda _db, _bid, batas=12: []
try:
    kirim_tanpa, mulai_tanpa = A._siapkan_kirim(
        _DBTiruan(), type('B', (), {'id': 5})(), NASKAH_PANJANG)
    cek('G7 BERGIGI: tanpa pagar naskah DIPOTONG lagi (bukti pagar bekerja)',
        len(kirim_tanpa) < len(NASKAH_PANJANG),
        f'{len(kirim_tanpa)} kar < {len(NASKAH_PANJANG)} kar')
finally:
    A._catatan_terbaru = _asli_catatan

# ── hasil ─────────────────────────────────────────────────────────────────
print('\n' + '═' * 70)
print(f'  HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 70)
sys.exit(1 if GAGAL else 0)
