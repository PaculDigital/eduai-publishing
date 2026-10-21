"""Cek sintaks JS referensi.html SETELAH perubahan pakai-ulang bab (13Okt26).

Pelajaran lama: JS rusak = SELURUH skrip mati, tapi HTTP tetap 200 dan
konsol cuma 404 favicon. Jadi WAJIB `node --check` pada skrip HASIL RENDER
(render Jinja dulu), JANGAN regex malas.

Jalankan di HOST (node ada di /usr/local/bin/node).
"""
import re
import subprocess
import sys
import tempfile

P = '/opt/data/services/eduai-publishing/app/templates/referensi.html'
isi = open(P, encoding='utf-8').read()
gagal = []


def cek(nama, benar, tanda=''):
    tanda = f' {tanda}' if tanda else ''
    print(f'{nama}{tanda}  {"✅" if benar else "❌"}')
    if not benar:
        gagal.append(nama)


#  ── 1. tag <script> seimbang ──
buka, tutup = isi.count('<script>'), isi.count('</script>')
cek('1. tag <script> seimbang', buka == tutup, f'({buka} vs {tutup})')

#  ── 2. node --check atas JS HASIL RENDER ──
js = isi.split('<script>')[-1].split('</script>')[0]
js_bersih = re.sub(r'\{\{.*?\}\}', '0', js, flags=re.S)
js_bersih = re.sub(r'\{%.*?%\}', '', js_bersih, flags=re.S)

with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                 encoding='utf-8') as f:
    f.write(js_bersih)
    tmp = f.name

r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True)
cek('2. sintaks JS (node --check)', r.returncode == 0)
if r.returncode != 0:
    print('   ' + (r.stderr or '').strip()[:700])

#  ── 3. fungsi baru benar-benar ada ──
for nama in ('bukaPakai', 'tutupPakai', 'simpanPakai', 'esc'):
    ada = (f'function {nama}(' in isi) or (f'async function {nama}(' in isi)
    cek(f'3. fungsi {nama}()', ada)

#  ── 4. wadah + gaya ada ──
cek('4. wadah #kotak-pakai', 'id="kotak-pakai"' in isi)
cek('5. gaya .pakai-kotak', '.pakai-kotak{' in isi)
cek('6. gaya .bab-cek', '.bab-cek{' in isi)

#  ── 5. tombol dipanggil dari kartu artikel ──
cek('7. tombol bukaPakai() di kartu', 'onclick="bukaPakai(' in isi)

#  ── 6. rute baru ada di server ──
R = '/opt/data/services/eduai-publishing/app/rute_jurnal.py'
rute = open(R, encoding='utf-8').read()
cek("8. rute GET '/pakai-di'", "@router.get('/pakai-di')" in rute)
cek("9. rute POST '/pakai-di'", "@router.post('/pakai-di')" in rute)

#  ── 7. mesin: fungsi pakai_di_banyak ada ──
J = '/opt/data/services/eduai-publishing/app/jurnal.py'
jur = open(J, encoding='utf-8').read()
cek('10. mesin pakai_di_banyak()', 'def pakai_di_banyak(' in jur)

print()
if gagal:
    print(f'HASIL: {len(gagal)} GAGAL — {", ".join(gagal)}')
    sys.exit(1)
print('HASIL: SEMUA LULUS ✅')
sys.exit(0)
