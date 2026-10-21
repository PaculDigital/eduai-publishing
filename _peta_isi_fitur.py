"""PETA ISI 5 FITUR EDUAI — dibaca dari KODE template di image (tanpa sandi).

Keluar: untuk setiap fitur → tombol/tab/form yang BENAR-BENAR tayang.
Ini alasan sah "sudah jalan", bukan klaim.
"""
from __future__ import annotations

import re
import subprocess

FITUR = {
    'naskah':     'naskah.html',
    'referensi':  'referensi.html',
    'artikel':    'artikel.html',
    'konversi':   'artikel_konversi.html',
    'kolaborasi': 'kolaborasi.html',
    'belajar':    'belajar.html',
    'editor':     'editor.html',
    'tinjau':     'tinjau.html',
}


def baca(nama: str) -> str:
    try:
        out = subprocess.run(
            ['docker', 'exec', 'eduai-app', 'sh', '-c',
             f'cat /app/app/templates/{nama}'],
            capture_output=True, text=True, timeout=40)
        return out.stdout
    except Exception as e:                                        # noqa: BLE001
        return f'GALAT {e}'


print('=' * 78)
print('  PETA ISI FITUR EDUAI (dibaca dari kode template di image)')
print('=' * 78)

for nama, berkas in FITUR.items():
    isi = baca(berkas)
    if isi.startswith('GALAT') or not isi.strip():
        print(f'\n  ── {nama} ({berkas}) → TIDAK BISA DIBACA')
        continue
    judul = re.findall(r'<h1[^>]*>([^<]{3,70})</h1>', isi)
    h2 = re.findall(r'<h2[^>]*>([^<]{3,70})</h2>', isi)
    tombol = [t.strip() for t in
              re.findall(r'<button[^>]*>\s*([^<]{2,45}?)\s*</button>', isi)]
    tombol = [t for t in tombol if t]
    tab = [t.strip() for t in
           re.findall(r'class="[^"]*\btab\b[^"]*"[^>]*>\s*([^<]{2,30}?)\s*<',
                      isi)]
    form = re.findall(r'<form[^>]*action="([^"]*)"', isi)
    panggil = sorted(set(re.findall(r'fetch\(\s*[`\'"]([^`\'"]{3,60})', isi)))

    print(f'\n  ── {nama:<11} ({berkas}, {len(isi):,} kar)')
    if judul:
        print(f'     judul : {judul[:3]}')
    if h2:
        print(f'     bagian: {h2[:6]}')
    print(f'     tombol({len(tombol)}): {tombol[:10]}')
    if tab:
        print(f'     tab   ({len(tab)}): {tab[:8]}')
    if form:
        print(f'     form  : {form[:5]}')
    if panggil:
        print(f'     API   ({len(panggil)}): {panggil[:8]}')

    belum = sorted(set(re.findall(
        r'(segera hadir|coming soon|belum tersedia|dalam pengembangan|'
        r'akan datang)', isi, re.I)))
    if belum:
        print(f'     ⚠️  BELUM JADI: {belum}')
