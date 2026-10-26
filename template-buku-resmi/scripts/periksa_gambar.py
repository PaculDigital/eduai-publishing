#!/usr/bin/env python3
"""PEMERIKSA GAMBAR TERUKUR (barang 15 RENCANA-BANGUN-SSOT).

Lapis 1 (mesin, di skrip ini) — yang bisa dibuktikan angka:
  G1 berkas terbaca sebagai gambar (PNG/JPEG) dan tidak kosong.
  G2 lebar gambar pada 150 dpi tidak melebihi area teks profil.
  G3 latar putih dominan (untuk gaya latar putih): fraksi piksel
     nyaris-putih >= 0,30.

Lapis 2 (peninjau) — kesesuaian ISI gambar dengan brief TIDAK bisa
diangkakan skrip ini. Skrip mencetak daftar periksa kata kunci dari
brief untuk peninjau (manusia / vision), dan vonis lapis 2 dicatat
di kwitansi mutu (barang 16). Gambar yang lolos lapis 1 tapi meleset
dari brief tetap harus dibuat ulang — keputusan peninjau.

Pakai:
    python3 periksa_gambar.py gambar.png --profil=../jenis/monograf/profil.json
    python3 periksa_gambar.py gambar.png --brief="teks brief di sini"
EXIT 0 = lapis 1 lulus, 1 = gagal.
"""
import re
import sys
from pathlib import Path

LULUS = GAGAL = 0


def ok(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f'  -> {info}' if info else ''))


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not arg:
        sys.exit(__doc__)
    path = Path(arg[0])
    profil = None
    for a in sys.argv[1:]:
        if a.startswith('--profil='):
            import json
            profil = json.loads(Path(a.split('=', 1)[1]).read_text(encoding='utf-8'))
    brief = next((a.split('=', 1)[1] for a in sys.argv[1:]
                  if a.startswith('--brief=')), '')

    print(f'GAMBAR: {path}')
    try:
        from PIL import Image
        im = Image.open(path)
        im.load()
    except Exception as e:
        ok('G1 berkas terbaca sebagai gambar', False, str(e))
        print(f'\nRINGKAS: {LULUS} LULUS / {GAGAL} GAGAL')
        return 1
    ok(f'G1 berkas terbaca ({im.format}, {im.size[0]}x{im.size[1]} px)',
       im.size[0] > 0 and im.size[1] > 0)

    if profil:
        area_cm = profil['format']['area_teks_twip'] / 1440 * 2.54
        maks_px = area_cm / 2.54 * 150
        ok(f'G2 lebar <= area teks profil ({area_cm:.2f} cm @150dpi = {maks_px:.0f} px)',
           im.size[0] <= maks_px + 1, f'lebar {im.size[0]} px')

    kecil = im.convert('RGB')
    kecil.thumbnail((200, 200))
    px = list(kecil.getdata())
    putih = sum(1 for r, g, b in px if r >= 245 and g >= 245 and b >= 245)
    fraksi = putih / len(px) if px else 0
    ok(f'G3 latar putih dominan (fraksi nyaris-putih {fraksi:.2f} >= 0.30)',
       fraksi >= 0.30, f'fraksi hanya {fraksi:.2f}')

    print('\n== LAPIS 2 (PENINJAU) ==')
    if brief:
        kata = sorted({w.lower() for w in re.findall(r'[a-zA-Z]{4,}', brief)})
        print('  Periksa mata/vision: gambar harus memuat & sesuai brief.')
        print(f'  Kata kunci brief: {", ".join(kata[:18])}')
    else:
        print('  Periksa mata/vision: gambar sesuai brief-nya? '
              '(beri --brief= untuk daftar kata kunci)')
    print('  Vonis lapis 2 dicatat di kwitansi mutu (barang 16).')

    print(f'\nRINGKAS: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
