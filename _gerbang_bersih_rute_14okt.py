"""UJI GIGI gerbang bersih-rute: suntik 2 kerusakan → harus GAGAL.

Suntikan:
  ① /v1/addon DIKEMBALIKAN  → gerbang "salinan lama hilang" harus GAGAL
  ② /api/addon DIHAPUS      → gerbang "yang dipakai layar hidup" harus GAGAL
"""
import shutil
import subprocess

AI = '/opt/data/services/eduai-publishing/app/ai.py'
MAIN = '/opt/data/services/eduai-publishing/app/main.py'
CAI = '/tmp/gigi_ai.py'
CMAIN = '/tmp/gigi_main.py'

shutil.copy(AI, CAI)
shutil.copy(MAIN, CMAIN)


def jalan(ai, main):
    """Jalankan cek terhadap berkas yang diberikan (fungsi murni).

    ⚠️ Buang baris KOMENTAR dulu — catatan Wulan sendiri menyebut '/v1/addon',
    jadi mencari string mentah = gerbang hiasan (pelajaran 13Okt26).
    """
    a = '\n'.join(l for l in open(ai).read().split('\n')
                  if not l.strip().startswith('#'))
    m = open(main).read()
    hasil = []
    #  ① salinan lama HARUS tidak ada lagi (kode, bukan komentar)
    hasil.append(('① /v1/addon sudah dicabut', '/v1/addon' not in a))
    #  ② yang dipakai layar HARUS tetap ada
    hasil.append(('② /api/addon masih ada', "@app.get('/api/addon')" in m))
    #  ③ kuota AI tidak ikut terhapus
    hasil.append(('③ /v1/kuota masih ada', "@router.get('/v1/kuota')" in a))
    #  ④ kuota penyimpanan tidak ikut terhapus
    hasil.append(('④ /api/kuota masih ada', "@app.get('/api/kuota')" in m))
    #  ⑤ kunci bimbingan tidak disentuh
    hasil.append(('⑤ /pembimbing/kunci aman',
                  'pembimbing/kunci' in open(
                      '/opt/data/services/eduai-publishing/app/rute_bagikan.py'
                  ).read()))
    return hasil


print('── SEHAT (kode asli) ──')
sehat = jalan(AI, MAIN)
for nama, ok in sehat:
    print(f'   {"✅" if ok else "❌"} {nama}')
print(f'   → {sum(1 for _, o in sehat if o)}/{len(sehat)} LULUS')

#  suntik ①
s = open(AI).read()
TA = "# ── DIBERSIHKAN 14Okt26 (audit sinkron backend↔frontend) ────────────────"
open(CAI, 'w').write(s.replace(
    TA, "@router.get('/v1/addon')\ndef x():\n    return {}\n\n\n" + TA, 1))
print('\n── SUNTIK ①: /v1/addon dikembalikan ──')
h1 = jalan(CAI, MAIN)
gagal1 = [nama for nama, ok in h1 if not ok]
print(f'   GAGAL: {gagal1 if gagal1 else "TIDAK ADA ❌ gerbang BUTA"}')

#  suntik ②
m = open(MAIN).read()
open(CMAIN, 'w').write(m.replace("@app.get('/api/addon')",
                                 "@app.get('/api/addon-XX')", 1))
print('\n── SUNTIK ②: /api/addon dihapus ──')
h2 = jalan(AI, CMAIN)
gagal2 = [nama for nama, ok in h2 if not ok]
print(f'   GAGAL: {gagal2 if gagal2 else "TIDAK ADA ❌ gerbang BUTA"}')

print('\n════════ KESIMPULAN ════════')
print(f'  Suntik ①: {"✅ TERTANGKAP" if gagal1 else "❌ LOLOS = GERBANG PALSU"}')
print(f'  Suntik ②: {"✅ TERTANGKAP" if gagal2 else "❌ LOLOS = GERBANG PALSU"}')
print(f'  Pulih  : {"✅ SEHAT" if all(o for _, o in sehat) else "❌"}')
