"""LAPORAN DATA NYATA: 2 dokumen asli Bos untuk menentukan RANGE KUOTA.

Dok 1: TESIS_LENGKAP_Goras.docx  — sampai BAB III (catatan Bos)
Dok 2: SKRIPSI WULAN.docx        — skripsi FULL (Wulandari, U. Pelita Bangsa 2025)

Semua angka = HASIL UJI NYATA (token dari respons AI, bukan hitungan teori).
"""

# ══ DATA UJI NYATA (sudah dijalankan) ══
TARIF = 0.0155915      # Rp/token

print('='*88)
print('  BAGIAN 1 — ISI DOKUMEN (nyata, diukur)')
print('='*88)
print()
print(f"{'':32} {'TESIS (3 BAB)':>18} {'SKRIPSI FULL':>18}")
print('-'*88)
baris = [
    ('Ukuran file .docx',        '590.578 B (0,56 MB)', '7.648.507 B (7,29 MB)'),
    ('— gambar di dalamnya',     'kecil',               '41 berkas = 6,83 MB (94%)'),
    ('— teks yang dibaca AI',    '63.797 karakter',     '700.599 karakter'),
    ('— jumlah kata',            '~6.500',              '46.342'),
    ('Bab terdeteksi',           'BAB I (sampai III)',  'BAB I–V (lengkap)'),
]
for a,b,c in baris:
    print(f'{a:<32} {b:>18} {c:>18}')

print()
print('='*88)
print('  BAGIAN 2 — HASIL UJI NYATA (token dari respons AI)')
print('='*88)
print()
print('Model: ag/gemini-3.8-flash-high  ·  tarif Rp 0,0155915/token')
print()
print(f"{'UJI':<44} {'MASUK':>8} {'KELUAR':>8} {'BIAYA':>10} {'WAKTU':>8}")
print('-'*88)
ujis = [
    ('TESIS: BAB I saja (22.333 kar)',            5035,  636,  89,  '31,5s'),
    ('TESIS: SELURUH s.d. BAB III (63.797 kar)', 15823, 1916, 277,  '34,2s'),
    ('SKRIPSI: potongan 1 (55.000 kar)',         25596, 1979, 430,  '18,6s'),
    ('SKRIPSI: potongan 1+2 (110.000 kar)',      43389, 1657, 702, '246,7s'),
]
for n,i,o,rp,w in ujis:
    print(f'{n:<44} {i:>8,} {o:>8,} {("Rp "+format(rp,",d")):>10} {w:>8}')

print()
print('='*88)
print('  BAGIAN 3 — RASIO NYATA (dari uji)')
print('='*88)
print()
print('  Rasio token/karakter bervariasi — JANGAN pakai satu angka buta:')
print()
print(f"    tesis total   : 15.823 / 63.797  = {15823/63797:.3f} token/kar")
print(f"    skripsi pot.1 : 25.596 / 55.000  = {25596/55000:.3f} token/kar")
print(f"    skripsi pot.2 : 43.389 /110.000  = {43389/110000:.3f} token/kar")
print()
print('  → Ambil konservatif (tertinggi) = 0,465 token/karakter')

print()
print('='*88)
print('  BAGIAN 4 — PROYEKSI BIAYA TUNTAS (pakai rasio 0,465)')
print('='*88)
print()
def proyeksi(kar, bagian=55000):
    tok_in = kar*0.465
    tok_out = tok_in*0.08          # output ~8% dari input (dari uji)
    total = tok_in+tok_out
    n = (kar+bagian-1)//bagian
    return total, total*TARIF, n

for nama, kar in [('TESIS 3 bab (63.797 kar)',63797),
                  ('Skripsi full (700.599 kar)',700599),
                  ('Batas baru 15 MB, teks maks (~1,5jt kar)',1500000)]:
    tok, rp, n = proyeksi(kar)
    print(f'  {nama:<42} {tok:>10,.0f} tok  Rp {rp:>8,.0f}  ({n} bagian)')
