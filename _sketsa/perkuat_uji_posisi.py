"""Perkuat uji posisi: buktikan gambar TIDAK di daftar isi.

🔴 UJI LAMA LEMAH (26Sep26): hanya memeriksa "gambar sebelum 2.4" — padahal
   di DAFTAR ISI pun 2.3 ada sebelum 2.4, jadi uji LOLOS walau gambar
   ditaruh di daftar isi. Pelajaran: uji wajib memakai UKURAN yang bisa
   MEMBEDAKAN daftar isi dari isi naskah (nomor paragraf + titik-titik).
"""
import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/_sketsa/'
                 'uji_gambar_posisi.py')
s = P.read_text()

lama = """cek('A. gambar SETELAH judul 2.3', pos_gambar > pos_23, '')
cek('A. gambar SEBELUM judul 2.4', pos_gambar < pos_24, '')"""
baru = """cek('A. gambar SETELAH judul 2.3', pos_gambar > pos_23, '')
cek('A. gambar SEBELUM judul 2.4', pos_gambar < pos_24, '')

#  🔴 UJI KUAT: gambar TIDAK boleh ada di DAFTAR ISI.
#     Daftar isi = baris judul yang bertitik pengarah (".....") dan/atau
#     diakhiri nomor halaman. Buktikan paragraf tempat gambar masuk
#     BUKAN baris daftar isi.
pars_a = re.findall(r'<w:p\\b.*?</w:p>|<w:p\\b[^>]*/>', doc, re.S)
idx_gambar = next((i for i, p in enumerate(pars_a) if 'grafik_ai' in p), None)
cek('A. paragraf gambar ditemukan', idx_gambar is not None)
isi_par_gambar = ''
if idx_gambar is not None:
    #  paragraf TEPAT sebelum gambar = akhir bagian sebenarnya
    seblm = idx_gambar - 1
    while seblm >= 0:
        t = ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', pars_a[seblm])).strip()
        if t:
            isi_par_gambar = t
            break
        seblm -= 1
print(f'   paragraf sebelum gambar (ke-{seblm}): {isi_par_gambar[:70]!r}')
cek('A. TIDAK di daftar isi (tanpa titik pengarah)',
    not re.search(r'\\.{3,}', isi_par_gambar), isi_par_gambar[:50])
print(f'   indeks paragraf gambar: {idx_gambar} (daftar isi ada di 170-179)')
cek('A. gambar JAUH setelah daftar isi (idx > 200)',
    idx_gambar is not None and idx_gambar > 200, f'idx={idx_gambar}')"""
assert lama in s
s = s.replace(lama, baru, 1)
P.write_text(s)
print('✅ uji diperkuat (bukti bukan daftar isi)')
