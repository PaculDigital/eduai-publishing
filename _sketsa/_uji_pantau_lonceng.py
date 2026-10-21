"""UJI LANGKAH C+E (pantau + lonceng) — memastikan controller-nya benar.

KENAPA UJI INI ADA (16Sep26): Wulan 3x memakai nama yang TIDAK ADA
(`tahap_selesai`, `tahap_total`, `bagian`, `sudah_dibaca`, `/v1/proses/baca`).
Semuanya adalah *AttributeError/404 di runtime* — TIDAK ketangkap gerbang
pyflakes, karena salah di DALAM string JS. Uji ini memeriksa silang:
  JS (editor.html)  ←→  ringkas() (proses.py)  ←→  kolom ProsesAI (models.py)

Tanpa uji ini, kesalahan tipe ini HANYA ketemu saat user membuka halaman.
"""
import re
import sys
from pathlib import Path

LULUS = GAGAL = 0


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {catatan}' if catatan else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {catatan}' if catatan else ''))


html = Path('/app/app/templates/editor.html').read_text(encoding='utf-8')
proses = Path('/app/app/proses.py').read_text(encoding='utf-8')
model = Path('/app/app/models.py').read_text(encoding='utf-8')
ai = Path('/app/app/ai.py').read_text(encoding='utf-8')

print('=' * 70)
print('UJI LANGKAH C+E — PANTAU & LONCENG')
print('=' * 70)

# ── 1. Setiap field yang dibaca JS harus ADA di ringkas() ──
print('\n[1] Field JS ←→ ringkas(): tidak boleh membaca field karangan')
blok = proses[proses.index("def ringkas"):]
blok = blok[:blok.index('\n\n\n')] if '\n\n\n' in blok else blok
kirim = set(re.findall(r"'([a-z_]+)':", blok))
# field yang dibaca JS dari objek proses p.*
dipakai = set(re.findall(r'\bp\.([a-z_]+)\b', html))
# hanya yang relevan ke proses (p. = objek proses di fungsi JS kita)
diabaikan = {'length', 'push', 'map', 'filter', 'join', 'status', 'kode'}
dipakai -= diabaikan
kurang = sorted(dipakai - kirim)
cek('semua field JS tersedia di ringkas()', not kurang,
    ('kurang: ' + ', '.join(kurang)) if kurang else f'{len(dipakai)} field cocok')

# ── 2. ringkas() tidak boleh menyentuh kolom yang tidak ada di model ──
print('\n[2] ringkas() ←→ kolom ProsesAI: tidak boleh mengarang kolom')
blk_model = model[model.index('class ProsesAI'):]
blk_model = blk_model[:blk_model.index('\nclass ')] if '\nclass ' in blk_model else blk_model
kolom = set(re.findall(r'^\s+([a-z_]+): Mapped', blk_model, re.M))
sumber_p = set(re.findall(r'\bp\.([a-z_]+)', blok))
karangan = sorted(sumber_p - kolom - {'isoformat'})
cek('ringkas() hanya pakai kolom NYATA', not karangan,
    ('dipakai tapi tidak ada: ' + ', '.join(karangan)) if karangan
    else f'{len(sumber_p)} atribut valid dari {len(kolom)} kolom')

# ── 3. Rute yang dipanggil JS harus ADA di server ──
print('\n[3] Rute JS ←→ server: tidak boleh memanggil rute hantu')
panggil = set(re.findall(r"fetch\('(/api/ai/v1/[^']+)'", html))
ada = set(re.findall(r"@router\.(?:get|post)\('([^']+)'", ai))
hilang = sorted(x for x in panggil
                if x.replace('/api/ai', '') not in ada)
cek('semua rute JS ada di server', not hilang,
    ('rute hantu: ' + ', '.join(hilang)) if hilang else f'{len(panggil)} rute diperiksa')

# ── 4. Elemen DOM yang diakses JS harus ADA di HTML ──
print('\n[4] getElementById ←→ elemen HTML: tidak boleh buta')
id_dipakai = set(re.findall(r"getElementById\('([^']+)'\)", html))
id_ada = set(re.findall(r'id="([^"]+)"', html)) | {'tempat-editor'}
id_hilang = sorted(id_dipakai - id_ada)
cek('semua id yang diakses JS ada', not id_hilang,
    ('id hilang: ' + ', '.join(id_hilang)) if id_hilang else f'{len(id_dipakai)} id OK')

# ── 5. Lonceng: badge & daftar ada ──
print('\n[5] Komponen lonceng (Langkah E)')
for eid in ['lonceng', 'lonceng-angka', 'lonceng-isi', 'daftar-lonceng']:
    cek(f'elemen #{eid} ada', f'id="{eid}"' in html)

# ── 6. Papan pantau (Langkah C) ──
print('\n[6] Komponen papan pantau (Langkah C)')
for eid in ['pantau', 'pantau-judul', 'pantau-tahap', 'pantau-langkah',
            'kunci-spanduk']:
    cek(f'elemen #{eid} ada', f'id="{eid}"' in html)
cek('pantau berjalan berulang (setInterval)',
    'setInterval(pantau' in html)
cek('pantau dihentikan saat halaman ditutup (cegah bocor)',
    'hentikanPantau' in html and 'clearInterval' in html)

# ── 7. Tombol terapkan (Langkah D) ──
print('\n[7] Tombol tulis hasil (Langkah D)')
cek('tombol #pai-terapkan ada', 'id="pai-terapkan"' in html)
cek('memanggil /v1/terapkan', "'/api/ai/v1/terapkan'" in html)
cek('minta konfirmasi dulu (Lapis 3 — user memutuskan)',
    'konfirmasi(' in html or 'confirm(' in html)

# ── 8. Aturan galat tidak buta ──
print('\n[8] Diagnosa: galat TIDAK boleh jadi "[object Object]"')
for fn in ['[pantau]', '[lonceng]', '[terapkan]']:
    cek(f'{fn} pakai console.error isi lengkap', fn in html)
cek('tidak ada tempat mencetak objek mentah ke pesan user',
    'pesan(e)' not in html and "'gagal: ' + e)" not in html)

# ── 9. Keamanan: teks server jangan masuk innerHTML mentah ──
print('\n[9] Keamanan — XSS')
cek('ada fungsi pelolos (aman)',
    'function aman(' in html)
cek('daftar lonceng memakai aman()',
    'aman(judul)' in html and 'aman(pesan)' in html)

# ── 10. Lonceng: baca = padamkan ──
print('\n[10] Lonceng padam setelah dibaca')
cek('JS memanggil /v1/proses/baca', "/api/ai/v1/proses/baca" in html)
cek('server menyediakan rute baca', "'/v1/proses/baca'" in ai)


# ═════════════════════════════════════════════════════════════════════════
#  [11] KELAS CSS ←→ KELAS JS  (AKAR BARU 16Sep26 — temuan MATA, bukan uji)
# ═════════════════════════════════════════════════════════════════════════
# KENAPA ADA: JS menambah kelas 'tampil' ke #pantau, tapi CSS mendefinisikan
# `#pantau.buka` → modal TIDAK PERNAH tampil. Uji kode LOLOS (26/0) karena
# JS-nya memang "ada"; yang salah cuma NAMA KELAS. Yang menemukan = MATA
# Wulan lewat potret layar + vision. Gerbang ini menutup celah itu.
print('\n[11] Kelas CSS ←→ kelas JS (jangan sampai beda nama)')
import re as _re
css_kelas = set(_re.findall(r'#([a-z-]+)\.([a-z]+)\s*\{', html))
js_add = set(_re.findall(r"getElementById\('([a-z-]+)'\)\)?\s*\n?\s*\.?\s*classList\.add\('([a-z]+)'\)", html))
peta_css = {}
for eid, kls in css_kelas:
    peta_css.setdefault(eid, set()).add(kls)

# kelas yang didefinisikan lewat KOMBINASI kelas, mis. `.pai-bab-item.pilih`
# → tetap SAH walau tidak ada `#id.pilih`. Gerbang TIDAK boleh salah lapor.
kelas_kombinasi = set(_re.findall(r'\.[a-z-]+\.([a-z]+)\s*\{', html))

# setiap 'id' yang JS tambahkan kelasnya harus punya definisi CSS dgn kelas itu
for m in _re.finditer(
        r"document\.getElementById\('([a-z-]+)'\)\.classList\.(add|remove|toggle)\('([a-z]+)'",
        html):
    eid, aksi, kls = m.group(1), m.group(2), m.group(3)
    if aksi == 'add':
        punya = kls in peta_css.get(eid, set()) or kls in kelas_kombinasi
        cek(f'{eid} + kelas "{kls}" ada di CSS', punya,
            '' if punya else f'CSS hanya punya: {sorted(peta_css.get(eid, []))}')

# variabel JS yang menampung elemen (var X = getElementById(...)) lalu di-add
for m in _re.finditer(
        r"var\s+([a-zA-Z_]+)\s*=\s*document\.getElementById\('([a-z-]+)'\)", html):
    var, eid = m.group(1), m.group(2)
    for m2 in _re.finditer(
            r'\b' + var + r'\.classList\.(add|remove|toggle)\(\'([a-z]+)\'\)', html):
        aksi, kls = m2.group(1), m2.group(2)
        if aksi in ('add', 'toggle') and eid not in ('tempat-editor',):
            punya = kls in peta_css.get(eid, set()) or kls in kelas_kombinasi
            cek(f'{eid} (via {var}) + "{kls}" ada di CSS', punya,
                '' if punya else f'CSS hanya punya: {sorted(peta_css.get(eid, []))}')

print('\n' + '=' * 70)
print(f'LULUS: {LULUS}   GAGAL: {GAGAL}')
print('=' * 70)
sys.exit(1 if GAGAL else 0)
