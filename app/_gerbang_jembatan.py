"""GERBANG JEMBATAN PETA — surveyor→bentuk state.petakan().

Fungsi SUNGGUHAN `app.peta_jembatan`. DI DALAM container.
Jalan: docker exec -w /app eduai-app python3 app/_gerbang_jembatan.py

BERGIGI: kalau pagar dilepas → gerbang HARUS GAGAL.
"""
import sys
sys.path.insert(0, "/app")
from app import peta_jembatan as J

lulus, gagal = [], []

def cek(nama, syarat, catatan=''):
    (lulus if syarat else gagal).append(nama)
    tanda = "\u2705" if syarat else "\u274c"
    print("  " + tanda + " " + nama + ((" — " + str(catatan)) if catatan else ""))

# ── A. PAGAR P2: surveyor mati/gagal ⇒ None (pemanggil balik ke cara lama)
cek("A1 masukan None ⇒ None", J.dari_surveyor(None) is None)
cek("A2 masukan bukan dict ⇒ None", J.dari_surveyor("bukan dict") is None)
cek("A3 dict tanpa label ⇒ None", J.dari_surveyor({'baris': ['a'], 'label': {}}) is None)
cek("A4 label ada tapi baris bukan list ⇒ None",
    J.dari_surveyor({'baris': 'x', 'label': {0: 'bab'}}) is None)

# ── B. PAGAR P3: BENTUK keluaran WAJIB sama state.petakan()
W = ['section_id', 'section_title', 'kategori', 'char_count', 'isi_teks']
peta = {'baris': ['BAB I', 'PENDAHULUAN', 'isi satu', 'BAB II', 'isi dua'],
        'label': {0: 'bab', 1: 'paragraf', 3: 'bab', 4: 'paragraf'},
        #  ⚠️ bentuk NYATA peta3_jev: tuple (judul bab, nama bab).
        'gabung': {0: ('BAB I', 'PENDAHULUAN'), 3: ('BAB II', 'ISI')},
        'boleh_dipakai_fitur': [True]*5, 'sistematika': []}
h = J.dari_surveyor(peta)
cek("B1 surveyor sah ⇒ list", isinstance(h, list))
cek("B2 ada isi (bukan kosong)", bool(h))
cek("B3 KUNCI sama persis state.petakan", sorted(h[0].keys()) == sorted(W))
cek("B4 section_id dari gabung (BAB I)", h[0]['section_id'] == 'BAB I')
cek("B5 char_count = panjang isi", isinstance(h[0]['char_count'], int) and h[0]['char_count'] > 0)

# ── C. PAGAR: bagian yang DITANDAI sistematika / tidak boleh ⇒ DIBUANG
#  ⚠️ PERBAIKAN 14 Okt 2026 — data uji HARUS meniru bentuk NYATA `peta3_jev`:
#     `gabung` isinya TUPLE ('BAB I', 'PENDAHULUAN'), BUKAN string.
#     Sebelum ini gerbang memakai string ⇒ menguji bentuk yang TAK PERNAH ADA
#     di produksi (kelas gerbang palsu). `boleh_dipakai_fitur` juga DICT {i:bool},
#     bukan list.
peta2 = dict(peta)
peta2['sistematika'] = [3]                       # BAB II = daftar isi
h2 = J.dari_surveyor(peta2)
cek("C1 sistematika dibuang", len(h2) < len(h))
cek("C2 sisa = BAB I saja", h2[0]['section_id'] == 'BAB I')

peta3 = dict(peta)
peta3['boleh_dipakai_fitur'] = {0: True, 1: True, 3: False, 4: True}
h3 = J.dari_surveyor(peta3)
cek("C3 boleh_dipakai_fitur=False dibuang ⇒ 1 bagian", len(h3) == 1,
    f'dapat {len(h3)}')
cek("C3b yang tersisa = BAB I", h3 and h3[0]['section_id'] == 'BAB I')

# ── D. ATURAN BUG ke-16: JUDUL ASLI menang atas judul baku
cek("D1 section_title = judul ASLI naskah",
    h[0]['section_title'] == 'BAB I' and h2[0]['section_title'] == 'BAB I')

# ── E. TIDAK MENEBAK: nomor diambil dari teks hanya kalau ada
cek("E1 nomor '1.2' dibaca dari baris", J._nomor_dari_teks('1.2 Rumusan Masalah') == '1.2')
cek("E2 nomor 'A.' dibaca (naskah huruf)", J._nomor_dari_teks('A. Latar Belakang') == 'A')
cek("E3 tanpa nomor ⇒ '' (JANGAN menebak)", J._nomor_dari_teks('Latar Belakang') == '')

print("=" * 66)
print("HASIL GERBANG JEMBATAN: %d LULUS / %d GAGAL" % (len(lulus), len(gagal)))
sys.exit(1 if gagal else 0)
