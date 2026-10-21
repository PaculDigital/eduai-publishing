"""UJI: apakah tebakan bagian oleh parser.py bisa SALAH TEMPAT?

Ini BUKAN teori — ini menguji fungsi sungguhan `app.parser.urai()` dengan
pesan-pesan yang MAHASISWA SUNGGUHAN tulis, lalu membandingkan tebakannya
dengan bagian yang dimaksud.

═══ PERBAIKAN 06Okt26 (Wulan) — HARAPAN DIKALIBRASI KE BENTUK NYATA ═══════
CACAT LAMA skrip ini: `dimaksud` ditulis sebagai NAMA BAB ('bab4') padahal
`urai()` mengembalikan **id sub-bab** ('4.1'). Akibatnya kasus yang
PERILAKUNYA BENAR selalu ditandai "SALAH" → skor akurasi PALSU (62%).

Sebenarnya "perbaiki bab 4" → `urai` balas 4.1 dengan conf 0.27 →
`butuh_ai=True` = PERILAKU BENAR (menyebut bab saja = tempat RAGU, §4.17).
Skrip lama menandainya SALAH karena mengharap 'bab4' (tipe yang tak pernah
keluarga dari fungsi ini).

PERBAIKAN 2: kasus yang memang RAGU (tempat disebut tanpa sub-bab, atau
penunjuk kosong) dinilai lewat ATURAN PERILAKU, bukan kecocokan string:
  - menyebut BAB saja       → WAJIB butuh_ai=True   (jangan tebak sub-bab)
  - penunjuk kosong         → WAJIB butuh_ai=True
  - judul sub-bab jelas     → WAJIB butuh_ai=False  + section tepat

Jalankan DI DALAM container:
    docker exec -w /app eduai-app python3 /tmp/uji_parser.py
"""
import sys

sys.path.insert(0, '/app')

from app.parser import urai  # noqa: E402

# (pesan, mode, harapan, catatan)
#   mode 'sec'    → harapan = id sub-bab yang WAJIB keluar
#   mode 'ragu'   → harapan = True  ⇒ butuh_ai WAJIB True (tempat JANGAN ditebak)
#   mode 'yakin'  → harapan = False ⇒ butuh_ai WAJIB False + section terisi
KASUS = [
    # ── niat JELAS, sub-bab eksplisit ────────────────────────────────
    ("perbaiki 1.1 latar belakang",         "sec",   "1.1",   "nomor sub-bab disebut"),
    ("perbaiki latar belakang",             "sec",   "1.1",   "judul jelas, tanpa bab"),
    ("kesimpulan perlu diperbaiki",         "sec",   "5.1",   "judul jelas, tanpa bab"),

    # ── sebut JUDUL sub-bab DALAM bab (fix CACAT 1b) ─────────────────
    ("perbaiki kerangka berpikir di bab 2", "sec",   "2.3",   "judul sub-bab + bab"),
    ("hipotesis saya salah",                "sec",   "2.4",   "judul jelas"),
    ("tujuan penelitian perlu diperjelas",  "sec",   "1.3",   "judul jelas"),
    ("populasi dan sampel belum jelas",     "sec",   "3.2",   "judul jelas"),

    # ── keyword C-3 (05Okt26): 'hasil'/'dibahas' → 4.5 Pembahasan ────
    ("hasil penelitian belum dibahas",      "sec",   "4.5",   "C-3: 'hasil'+'dibahas' → 4.5"),
    ("perbaiki pembahasan",                 "sec",   "4.5",   "kata 'pembahasan' → 4.5"),

    # ── menyebut BAB saja = tempat RAGU (WAJIB butuh_ai) ─────────────
    ("tolong perbaiki bab 4",               "ragu",  True,    "sebut bab 4, tanpa sub-bab"),
    ("perbaiki bab 2",                      "ragu",  True,    "sebut bab 2, tanpa sub-bab"),
    ("perbaiki bab 5",                      "ragu",  True,    "sebut bab 5, tanpa sub-bab"),

    # ── ambigu (kata muncul di banyak tempat) = RAGU ─────────────────
    ("tolong perbaiki kerangka ini",        "ragu",  True,    "'kerangka' tanpa bab"),
    ("perbaiki definisi operasional",       "ragu",  True,    "'definisi' tak ada di kamus"),
    ("hasil dan pembahasan",                "ragu",  True,    "dua kata sekaligus"),

    # ── penunjuk KOSONG (tak menyebut apa pun) = RAGU ────────────────
    ("tabel perlu diperbaiki",              "ragu",  True,    "tabel ada di banyak bab"),
    ("tolong perbaiki ini",                 "ragu",  True,    "tanpa petunjuk sama sekali"),
    ("perbaiki yang tadi",                  "ragu",  True,    "merujuk hal tak ada di teks"),
    ("perbaiki bagian itu",                 "ragu",  True,    "menunjuk tanpa nama"),

    # ── keyword panjang = YAKIN (kepakai langsung tanpa AI) ──────────
    ("landasan teori tolong dirapikan",     "yakin", False,   "judul jelas, panjang"),
    ("metode penelitian kurang jelas",      "yakin", False,   "judul jelas"),
    ("perbaiki metode",                     "yakin", False,   "'metode' jelas → 3.1"),
]

print('═' * 100)
print('  UJI PARSER: tebakan bagian + PERILAKU (butuh_ai) vs yang SEBENARNYA dimaksud')
print('═' * 100)
print(f'{"pesan mahasiswa":<38} {"tebak":<10} {"conf":>5} {"butuh_ai":>9} {"":<5} | catatan')

lulus = 0
gagal = 0
for pesan, mode, harap, catatan in KASUS:
    h = urai(pesan)
    sec = h['section']
    conf = h['confidence']
    butuh = h['butuh_ai']

    if mode == 'sec':
        ok = (sec == harap)
        tanda = 'LULUS' if ok else 'GAGAL'
    elif mode == 'ragu':
        # tempat ragu → WAJIB butuh_ai=True (jangan menebak sub-bab)
        ok = (butuh is True)
        tanda = 'LULUS' if ok else 'GAGAL'
    else:  # 'yakin'
        # tempat yakin → WAJIB butuh_ai=False DAN section terisi
        ok = (butuh is False and sec != 'unknown')
        tanda = 'LULUS' if ok else 'GAGAL'

    if ok:
        lulus += 1
    else:
        gagal += 1

    print(f'{pesan:<38} {sec:<10} {conf:>5} {str(butuh):>9} {tanda:<5} | {catatan}')

print('═' * 100)
print(f'HASIL: {lulus} LULUS / {gagal} GAGAL  (total {len(KASUS)})')
print()
print('ATURAN PERILAKU yang diuji (bukan kecocokan string):')
print('  · sebut BAB saja / penunjuk kosong / ambigu → butuh_ai WAJIB True')
print('  · judul sub-bab jelas                       → butuh_ai WAJIB False')
print('  · sub-bab eksplisit                         → section WAJIB tepat')
sys.exit(0 if gagal == 0 else 1)
