"""LANGKAH C — RANCANG + UJI POLA PERBAIKAN (belum menyentuh produksi).

Pola acuan = state.py:204 (terbukti benar 16Sep26):
    r'^[ \t]*(?i:BAB)[ \t]+([IVXLC]{1,5})[ \t]*(.*)$'

Uji pada SEMUA kasus yang sudah terbukti:
  HARUS COCOK   : "BAB IPENDAHULUAN", "BAB IIIMETODOLOGI", "BAB I PENDAHULUAN"
  HARUS TOLAK   : "bab ini menjelaskan", "Tabel bab 3", "BAB IIII" (salah tulis)
  plus kasus dari naskah NYATA (daftar isi, judul menempel dgn nomor halaman).
"""
import re

KASUS_COCOK = [
    ('BAB I PENDAHULUAN', 'I', 'PENDAHULUAN'),
    ('BAB IPENDAHULUAN', 'I', 'PENDAHULUAN'),
    ('BAB IIPENDAHULUAN', 'II', 'PENDAHULUAN'),
    ('BAB IIIMETODOLOGI PENELITIAN', 'III', 'METODOLOGI PENELITIAN'),
    ('BAB IVHASIL DAN PEMBAHASAN', 'IV', 'HASIL DAN PEMBAHASAN'),
    ('BAB VKESIMPULAN DAN SARAN', 'V', 'KESIMPULAN DAN SARAN'),
    ('BAB II TINJAUAN PUSTAKA', 'II', 'TINJAUAN PUSTAKA'),
    ('Bab II Kajian Pustaka.', 'II', 'Kajian Pustaka.'),
]

KASUS_TOLAK = [
    'bab ini menjelaskan metode penelitian yang dipakai',
    'Tabel bab 3 menyajikan hasil',
    'pada bab 5 akan dibahas',
    'BAB IIII SALAH TULIS',
]

# ── POLA USULAN: tiru state.py:204 (tanpa \b, romawi huruf besar wajib) ──
POLA_USUL = re.compile(r'^[ \t]*(?i:BAB)[ \t]+([IVXLC]{1,5})[ \t]*(.*)$',
                       re.MULTILINE)

print('╔══════════ UJI POLA USULAN ══════════╗')
print(f'  POLA: {POLA_USUL.pattern}')

print('\n── HARUS COCOK ──')
lulus = gagal = 0
for teks, nomor_harap, judul_harap in KASUS_COCOK:
    m = POLA_USUL.match(teks)
    if not m:
        print(f'  ❌ {teks!r} → TIDAK COCOK (harusnya cocok)')
        gagal += 1
        continue
    nomor = m.group(1)
    judul = (m.group(2) or '').strip(' .:-\t')
    ok = (nomor == nomor_harap)
    tanda = '✅' if ok else '❌'
    if not ok:
        gagal += 1
    else:
        lulus += 1
    print(f'  {tanda} {teks!r:44s} → nomor={nomor!r} judul={judul!r}')

print('\n── HARUS DITOLAK ──')
for teks in KASUS_TOLAK:
    m = POLA_USUL.match(teks)
    if m:
        print(f'  ❌ {teks!r} → DITERIMA (harusnya ditolak!) nomor={m.group(1)!r}')
        gagal += 1
    else:
        print(f'  ✅ {teks!r:44s} → ditolak (benar)')
        lulus += 1

print(f'\n═══ HASIL: {lulus} LULUS / {gagal} GAGAL ═══')
print('\nCATATAN: pola ini SAMA dengan state.py:204 (sudah terbukti 16Sep26).')
print('         Yang perlu ditambah saat dipakai di versi.py:')
print('         penyaring daftar-isi (nomor halaman menempel) — kalau tidak,')
print('         baris "BAB II ... 12" dari daftar isi ikut tertangkap.')
