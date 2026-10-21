"""UJI PEMISAH NOMOR-JUDUL — kasus 'BAB IPENDAHULUAN' dan kerabatnya."""
import re
#  SALINAN persis logika di konversi.py (agar bisa diuji tanpa container)
_BAB_AWAL = re.compile(r'^\s*BAB\s+([IVXLC]+|\d+)\b', re.IGNORECASE)
_BAB_NEMPEL = re.compile(r'^\s*BAB\s*([IVXLC]+|\d+)(?=[A-Z]{2,})(.*)$', re.IGNORECASE)

def _urai(judul):
    m0 = _BAB_AWAL.match(judul)
    if m0:
        return (m0.group(1), '')
    mn = _BAB_NEMPEL.match(judul)
    if not mn:
        return None
    sisa = mn.group(2) or ''
    nomor = mn.group(1) or ''
    if not re.fullmatch(r'\d+', nomor):
        for k in range(len(nomor), 0, -1):
            if re.fullmatch(r'[IVXLC]+', nomor[:k], re.IGNORECASE):
                nomor = nomor[:k]
                break
    return (nomor, sisa.strip())

KASUS = [
    ('BAB I',                  ('I', '')),
    ('BAB II',                 ('II', '')),
    ('BAB III',                ('III', '')),
    ('BAB V',                  ('V', '')),
    ('BAB I PENDAHULUAN',      ('I', 'PENDAHULUAN')),
    ('BAB IPENDAHULUAN',       ('I', 'PENDAHULUAN')),
    ('BAB IITINJAUAN PUSTAKA', ('II', 'TINJAUAN PUSTAKA')),
    ('BAB IIIMETODOLOGI PENELITIAN', ('III', 'METODOLOGI PENELITIAN')),
    ('BAB IVHASIL DAN PEMBAHASAN',   ('IV', 'HASIL DAN PEMBAHASAN')),
    ('BAB VKESIMPULAN DAN SARAN',    ('V', 'KESIMPULAN DAN SARAN')),
    ('BAB VI PEMBAHASAN',      ('VI', 'PEMBAHASAN')),
    ('BAB VII KESIMPULAN',     ('VII', 'KESIMPULAN')),
    ('BAB 1 PENDAHULUAN',      ('1', 'PENDAHULUAN')),
    ('BAB 2',                  ('2', '')),
    #  ⛔ YANG HARUS DITOLAK (bukan awal bab):
    ('BAB IPENDAHULUAN1',      None),   # daftar isi (angka halaman nempel)
    ('TINJAUAN PUSTAKA',       None),   # bukan bab
    ('Daftar Isi',             None),
    ('BAB',                    None),
    ('Bab 4 dan Bab 5 dapat Anda tulis setelah hasil', None),
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
    print(f'  {inp[:42]:44s} {ada}')
print()
print(f'  {ok} LULUS / {gagal} GAGAL')
