"""UJI BERGIGI gerbang_penanda_jadi_gambar.py — rusak DI MEMORI.

🚨 JEBAKAN YANG SUDAH MENIPU WULAN 3× (terukur 20 Okt 2026):
  Menyalin `jev_buku_umum.py` ke /tmp lalu mengharapkan gerbang membaca
  salinan itu TIDAK PERNAH BEKERJA. Buktinya dicetak langsung:
      MODUL: /app/jev_buku_umum.py
      POLA : \\[\\s*DIAGRAM\\s+\\d+\\.\\d+[^\\]\\n]*$
  Walau `sys.path` diarahkan ke /tmp, `jev_buku_umum` sudah terimpor
  lewat rantai impor `/app` ⇒ modul /app yang menang. Suntikan tak pernah
  terbaca ⇒ gerbang melaporkan "0 BERGIGI, 3 HIASAN" padahal kodenya
  SEHAT (gagal palsu yang menyalahkan kode sendiri).

  OBAT: jangan andalkan berkas. Rusak LANGSUNG di `sys.modules` — pola
  regex diganti pola mati `(?!)X`, lalu panggil cek gerbang. Karena
  `_pecah_penanda()` membaca atribut modul saat dipanggil, suntikan ini
  PASTI terbaca.
"""
import re
import sys

sys.path.insert(0, '/app')

import jev_buku_umum as J      # noqa: E402

print('=' * 64)
print('UJI BERGIGI — gerbang penanda ⇒ gambar (rusak di MEMORI)')
print('=' * 64)
print(f'  modul diuji: {J.__file__}')

POTONG_DIAGRAM = ('[DIAGRAM 1.1: Perjalanan Matahari dan Bayanganmu - '
                  'Gambar matahari bergerak dari timur ke barat, dengan '
                  'tongkat di tenga')
POTONG_TABEL = ('[TABEL 1.1: Pengamatan Matahari, Suhu, dan Bayangan - '
                'Waktu, Posisi')

bergigi = 0
hiasan = []


def uji_suntikan(judul, atribut, pola_mati):
    """Ganti `atribut` J dengan pola mati, cek hasil _pecah_penanda."""
    asli = getattr(J, atribut)
    try:
        setattr(J, atribut, re.compile(pola_mati))
        teks = POTONG_DIAGRAM if 'DIAGRAM' in atribut else POTONG_TABEL
        hasil = J._pecah_penanda(teks)
        jenis = [h[0] for h in hasil]
        #  Gerbang WAJIB gagal di keadaan ini: penanda jadi paragraf.
        return jenis == ['paragraf']
    finally:
        setattr(J, atribut, asli)


print()
#  ── S1: pola cadangan DIAGRAM dimatikan ⇒ harus jadi paragraf ─────────
ok = uji_suntikan('pola cadangan DIAGRAM dimatikan',
                  '_POLA_DIAGRAM_GADUH', r'(?!)X')
print(f'  {"✅ BERGIGI" if ok else "❌ HIASAN"}: S1 pola cadangan DIAGRAM '
      f'dimatikan → _pecah_penanda memberi paragraf (gerbang WAJIB gagal)')
bergigi += 1 if ok else 0
if not ok:
    hiasan.append('S1')

#  ── S2: pola cadangan TABEL dimatikan ─────────────────────────────────
ok = uji_suntikan('pola cadangan TABEL dimatikan',
                  '_POLA_TABEL_GADUH', r'(?!)X')
print(f'  {"✅ BERGIGI" if ok else "❌ HIASAN"}: S2 pola cadangan TABEL '
      f'dimatikan → penanda terpotong jadi paragraf')
bergigi += 1 if ok else 0
if not ok:
    hiasan.append('S2')

#  ── S3: pola UTAMA dibiarkan, cadangan dimatikan ⇒ HARUS beda hasil ──
#  Membuktikan pola cadangan memang yang menyelamatkan, bukan pola utama.
asli_d = J._POLA_DIAGRAM_GADUH
try:
    J._POLA_DIAGRAM_GADUH = re.compile(r'(?!)X')
    tanpa = J._pecah_penanda(POTONG_DIAGRAM)[0][0]
finally:
    J._POLA_DIAGRAM_GADUH = asli_d
dengan = J._pecah_penanda(POTONG_DIAGRAM)[0][0]
ok = (tanpa == 'paragraf' and dengan == 'diagram_marker')
print(f'  {"✅ BERGIGI" if ok else "❌ HIASAN"}: S3 tanpa cadangan '
      f'{tanpa!r} vs dengan cadangan {dengan!r} — cadangan memang penyelamat')
bergigi += 1 if ok else 0
if not ok:
    hiasan.append('S3')

#  ── S4: keadaan SEHAT — kedua penanda dikenali ────────────────────────
ok = (J._pecah_penanda(POTONG_DIAGRAM)[0][0] == 'diagram_marker'
      and J._pecah_penanda(POTONG_TABEL)[0][0] == 'tabel_marker')
print(f'  {"✅ SEHAT" if ok else "❌ RUSAK"}: S4 keadaan sehat — kedua '
      f'penanda terpotong dikenali sebagai marker')
bergigi += 1 if ok else 0
if not ok:
    hiasan.append('S4')

print()
print('=' * 64)
print(f'{{"bergigi": {bergigi}, "hiasan": {len(hiasan)}, '
      f'"rincian": {hiasan}}}')
print('=' * 64)
sys.exit(1 if hiasan else 0)
