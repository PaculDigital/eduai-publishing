"""UJI PEMISAH v3 — pagar kalimat: tolak hanya pola KALIMAT JELAS.

Prinsip: judul bab = FRASA (tak ada kata kerja bantu/kata sambung kalimat).
Kalimat = ada 'yang/dapat/akan/untuk/dll' + kata biasa.
"""
import re
_BAB_AWAL = re.compile(r'^\s*BAB\s+([IVXLC]+|\d+)\s*(.*)$', re.IGNORECASE)
_BAB_NEMPEL = re.compile(r'^\s*BAB\s*([IVXLC]+|\d+)(?=[A-Za-z]{2,})(.*)$', re.IGNORECASE)
ROM = re.compile(r'^[IVXLC]+$', re.IGNORECASE)
#  Kata yang HANYA muncul di kalimat, tak pernah di judul bab
_KATA_KALIMAT = re.compile(
    r'\b(yang|dapat|akan|untuk|adalah|telah|sudah|bisa|harus|oleh|pada|'
    r'dengan cara|seperti|misalnya|karena|agar|supaya|tetapi|namun|'
    r'silahkan|mohon|jangan|tulis|tuliskan|gunakan|lihat)\b', re.IGNORECASE)

def _urai(judul):
    if re.search(r'\d\s*$', judul) and not re.fullmatch(
            r'\s*BAB\s+\d+\s*$', judul, re.IGNORECASE):
        return None
    m0 = _BAB_AWAL.match(judul)
    if m0:
        nomor, sisa = m0.group(1), m0.group(2).strip()
        if sisa and sisa[0].islower():
            return None
        #  sisa memuat kata kalimat -> BUKAN judul
        if sisa and _KATA_KALIMAT.search(sisa):
            return None
        return (nomor, sisa)
    mn = _BAB_NEMPEL.match(judul)
    if mn:
        nomor = mn.group(1) or ''
        sisa = (mn.group(2) or '').strip()
        if sisa and _KATA_KALIMAT.search(sisa):
            return None
        if not re.fullmatch(r'\d+', nomor):
            for k in range(len(nomor), 0, -1):
                if ROM.match(nomor[:k]):
                    nomor = nomor[:k]; break
        return (nomor, sisa)
    return None

KASUS = [
    ('BAB I', ('I','')), ('BAB II', ('II','')), ('BAB III', ('III','')),
    ('BAB V', ('V','')),
    ('BAB I PENDAHULUAN', ('I','PENDAHULUAN')),
    ('BAB II TINJAUAN PUSTAKA', ('II','TINJAUAN PUSTAKA')),
    ('BAB IPENDAHULUAN', ('I','PENDAHULUAN')),
    ('BAB IITINJAUAN PUSTAKA', ('II','TINJAUAN PUSTAKA')),
    ('BAB IIIMETODOLOGI PENELITIAN', ('III','METODOLOGI PENELITIAN')),
    ('BAB IVHASIL DAN PEMBAHASAN', ('IV','HASIL DAN PEMBAHASAN')),
    ('BAB VKESIMPULAN DAN SARAN', ('V','KESIMPULAN DAN SARAN')),
    ('BAB VI PEMBAHASAN', ('VI','PEMBAHASAN')),
    ('BAB 1 PENDAHULUAN', ('1','PENDAHULUAN')), ('BAB 2', ('2','')),
    #  gaya campuran (harus LOLOS — umum di kampus):
    ('BAB IV Hasil dan Pembahasan', ('IV','Hasil dan Pembahasan')),
    ('BAB II Tinjauan Pustaka', ('II','Tinjauan Pustaka')),
    ('BAB III Metode Penelitian', ('III','Metode Penelitian')),
    #  ⛔ WAJIB DITOLAK:
    ('BAB IPENDAHULUAN1', None), ('BAB I PENDAHULUAN1', None),
    ('TINJAUAN PUSTAKA', None), ('Daftar Isi', None), ('BAB', None),
    ('Bab 4 dan Bab 5 dapat Anda tulis setelah hasil', None),
    ('BAB III METODE PENELITIAN yang dipakai', None),
    ('BAB IV HASIL DAN PEMBAHASAN yang akan dibahas', None),
    ('BAB V KESIMPULAN DAN SARAN untuk peneliti', None),
]
ok=gagal=0
for inp,h in KASUS:
    d=_urai(inp)
    if h is None:
        l = d is None; a='DITOLAK ✅' if l else f'LOLOS ❌ -> {d}'
    else:
        l = d==h; a=f'{d} {"✅" if l else "❌ harusnya "+str(h)}'
    ok+=l; gagal+=(not l)
    print(f'  {inp[:46]:48s} {a}')
print()
print(f'  {ok} LULUS / {gagal} GAGAL')
