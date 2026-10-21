"""GERBANG LAYAR SAMBUNGAN B — tombol "Tulis isi bab" di panel AI (13Okt26).

Menjaga janji:
  L1 tombol ada di panel Asisten AI (editor.html)
  L2 label tombol menyebut ARTIKEL (bukan "kerangka") — bahasa awam
  L3 tombol TERPISAH dari "Revisi dengan AI" (dua guna, jangan tertukar)
  L4 kirim ke rute yang ADA (`/api/ai/v1/kerangka/kerjakan`)
  L5 kirim NOMOR bab, bukan label ('BAB III' → '3') — bangun_isi hanya
     mengerti angka (AKAR kegagalan pertama)
  L6 tulisan AI ditampilkan (elHasil.textContent = d.tulisan_ai)
  L7 kutipan yang dibuang DIBERITAHU ke user (bukan didiamkan)
  L8 wadah hasil dipakai ulang (wadahHasil) — tidak bikin wadah baru
  L9 keterangan biaya: sebut Token Revisi

Uji gigi: cabut konversi nomor & cabut tampilan kutipan → harus GAGAL.
"""
import re
import sys

P = '/opt/data/services/eduai-publishing/app/templates/editor.html'
s = open(P).read()

#  Buang komentar HTML/JS dulu supaya asersi tidak tertipu teks komentar
#  (pelajaran 13Okt26: gerbang palsu karena cocok dengan komentar sendiri).
tanpa_komentar = re.sub(r'\{#.*?#\}', '', s, flags=re.S)
tanpa_komentar = re.sub(r'/\*.*?\*/', '', tanpa_komentar, flags=re.S)
tanpa_komentar = re.sub(r'<!--.*?-->', '', tanpa_komentar, flags=re.S)
tanpa_komentar = re.sub(r'^\s*//.*$', '', tanpa_komentar, flags=re.M)

lulus, gagal = [], []


def cek(nama, syarat, info=''):
    (lulus if syarat else gagal).append(nama)
    print(f'  {"LULUS" if syarat else "GAGAL"}  {nama} {info}')


print('═══ GERBANG LAYAR SAMBUNGAN B ═══')
print()
print('── L1–L3: tombol ada, jelas, terpisah ──')
cek('L1 tombol "pai-tulis-bab" ada', 'id="pai-tulis-bab"' in s)
cek('L2 label menyebut "artikel"',
    'Tulis isi bab dari artikel saya' in s)
cek('L2b label TIDAK berbunyi "kerangka" di tombol',
    'Tulis isi bab dari artikel' in s and 'Susun kerangka BAB I →' not in
    s[s.find('id="pai-tulis-bab"'):s.find('id="pai-tulis-bab"') + 400])
cek('L3 terpisah dari tombol Revisi', 'id="pai-jalan"' in s
    and 'id="pai-tulis-bab"' in s)

print()
print('── L4–L5: panggil rute yang ADA + kirim NOMOR bab ──')
cek('L4 kirim ke /api/ai/v1/kerangka/kerjakan',
    "'/api/ai/v1/kerangka/kerjakan'" in tanpa_komentar)
cek('L5a ada fungsi nomorDariLabel', 'function nomorDariLabel' in tanpa_komentar)
cek('L5b yang dikirim `bab: nomorBab` (BUKAN label)',
    'bab: nomorBab' in tanpa_komentar
    and 'bab: namaBab' not in tanpa_komentar)
cek('L5c romawi dipetakan', 'III: 3' in tanpa_komentar or 'III:3' in tanpa_komentar)

print()
print('── L6–L7: hasil tampil + kutipan jujur ──')
cek('L6 tulisan AI masuk ke kotak hasil',
    'elHasil.textContent = teks' in tanpa_komentar)
cek('L7a kutipan dibuang DITAMPILKAN ke user (DIPANGGIL, bukan cuma ada)',
    'tampilkanBuang(buang, d.sitasi_dipakai || []);' in tanpa_komentar
    and 'Dibuang karena tidak ada di artikelmu' in tanpa_komentar)
cek('L7b kutipan sah disebut juga',
    'Kutipan dari artikelmu' in tanpa_komentar)

print()
print('── L8–L9: pakai wadah yang ada + jujur soal biaya ──')
cek('L8 pakai wadahHasil (bukan wadah baru)',
    'wadahHasil.hidden = false' in tanpa_komentar)
cek('L9 sebut Token Revisi',
    'Token Revisi' in s and '1 Token Revisi' in s)

print()
print('── L10: tanpa artikel → jangan paksa AI ──')
cek('L10 ada pesan "belum ada artikel berabstrak"',
    'Belum ada artikel berabstrak' in tanpa_komentar
    and 'Referensi' in s)

print()
print(f'HASIL: {len(lulus)} LULUS · {len(gagal)} GAGAL')
if gagal:
    print('   GAGAL: ' + ', '.join(gagal))
    sys.exit(1)
print('   ✅ Layar Sambungan B utuh: tombol jelas + nomor bab benar + '
      'kutipan jujur.')
