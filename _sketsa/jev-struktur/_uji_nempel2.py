"""UJI PEMISAH v2 — perbaikan 3 cacat."""
import re

_BAB_AWAL = re.compile(r'^\s*BAB\s+([IVXLC]+|\d+)\s*(.*)$', re.IGNORECASE)
_BAB_NEMPEL = re.compile(r'^\s*BAB\s*([IVXLC]+|\d+)(?=[A-Z]{2,})(.*)$', re.IGNORECASE)

ROM = re.compile(r'^[IVXLC]+$', re.IGNORECASE)

def _urai(judul):
    """Balik (nomor, sisa_judul) atau None."""
    #  ⓵ buang angka halaman nempel (daftar isi): 'BAB I PENDAHULUAN1'
    if re.search(r'\d\s*$', judul) and not re.fullmatch(
            r'\s*BAB\s+\d+\s*$', judul, re.IGNORECASE):
        return None
    #  ⓶ tolak kalimat (mengandung kata kerja umum / huruf kecil setelah nomor)
    m0 = _BAB_AWAL.match(judul)
    if m0:
        nomor, sisa = m0.group(1), m0.group(2).strip()
        #  sisa yang diawali huruf kecil = kalimat, bukan judul
        if sisa and sisa[0].islower():
            return None
        return (nomor, sisa)
    mn = _BAB_NEMPEL.match(judul)
    if mn:
        nomor = mn.group(1) or ''
        sisa = (mn.group(2) or '').strip()
        if not re.fullmatch(r'\d+', nomor):
            for k in range(len(nomor), 0, -1):
                if ROM.match(nomor[:k]):
                    nomor = nomor[:k]
                    break
        return (nomor, sisa)
    return None

KASUS = [
    ('BAB I',                  ('I', '')),
    ('BAB II',                 ('II', '')),
    ('BAB III',                ('III', '')),
    ('BAB V',                  ('V', '')),
    ('BAB I PENDAHULUAN',      ('I', 'PENDAHULUAN')),
    ('BAB II TINJAUAN PUSTAKA',('II', 'TINJAUAN PUSTAKA')),
    ('BAB IPENDAHULUAN',       ('I', 'PENDAHULUAN')),
    ('BAB IITINJAUAN PUSTAKA', ('II', 'TINJAUAN PUSTAKA')),
    ('BAB IIIMETODOLOGI PENELITIAN', ('III', 'METODOLOGI PENELITIAN')),
    ('BAB IVHASIL DAN PEMBAHASAN',   ('IV', 'HASIL DAN PEMBAHASAN')),
    ('BAB VKESIMPULAN DAN SARAN',    ('V', 'KESIMPULAN DAN SARAN')),
    ('BAB VI PEMBAHASAN',      ('VI', 'PEMBAHASAN')),
    ('BAB VII KESIMPULAN',     ('VII', 'KESIMPULAN')),
    ('BAB 1 PENDAHULUAN',      ('1', 'PENDAHULUAN')),
    ('BAB 2',                  ('2', '')),
    ('BAB IV HASIL DAN PEMBAHASAN', ('IV', 'HASIL DAN PEMBAHASAN')),
    #  ⛔ WAJIB DITOLAK:
    ('BAB IPENDAHULUAN1',      None),
    ('BAB I PENDAHULUAN1',     None),
    ('TINJAUAN PUSTAKA',       None),
    ('Daftar Isi',             None),
    ('BAB',                    None),
    ('Bab 4 dan Bab 5 dapat Anda tulis setelah hasil', None),
    ('BAB III METODE PENELITIAN yang dipakai', None),
]
ok = gagal = 0
for inp, harap in KASUS:
    d = _urai(inp)
    if harap is None:
        lulus = d is None
        ada = 'DITOLAK ✅' if lulus else f'LOLOS ❌ -> {d}'
    else:
        lulus = d == harap
        ada = f'{d} {"✅" if lulus else "❌ harusnya " + str(harap)}'
    ok += lulus; gagal += (not lulus)
    print(f'  {inp[:44]:46s} {ada}')
print()
print(f'  {ok} LULUS / {gagal} GAGAL')
