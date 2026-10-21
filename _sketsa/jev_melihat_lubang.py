#!/usr/bin/env python3
"""SURUH JEV MELIHAT naskah yang sub-babnya 0 (perintah Bos 05Okt26).

Pertanyaan yang dijawab: Jev melihat naskah ini — apakah dia MELIHAT
bagian-bagian yang mesin LEWATKAN? Kalau ya → Jev berguna sebagai
tambahan mata (bukan pemutus). Kalau tidak → lubangnya bukan di mata.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app import satpam, state  # noqa: E402

AKAR = Path('/app')
PETA = Path('/app/_naskah_uji_teks')
d = json.loads(Path('/app/_hasil_ukur_subbab.json').read_text()
               or '{}') if Path('/app/_hasil_ukur_subbab.json').exists() else {}

# naskah sasaran: UTUH, 9 bab, TAPI 0 sub-bab (lubang nyata)
SASARAN = [
    'uin-suska-skripsi-afc395c408.txt',
    'uin-suska-skripsi-2520d0499c.txt',
    'uin-suska-skripsi-efc9f83da3.txt',
    'unhas-disertasi-977b0e0831.txt',
]
if len(sys.argv) > 1:
    SASARAN = sys.argv[1:]

for nama in SASARAN:
    p = PETA / nama
    if not p.exists():
        print(f'  (tidak ada: {nama})')
        continue
    try:
        teks = p.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:                                    # noqa: BLE001
        print(f'  {nama}: GALAT BACA {e}')
        continue

    besar = state.deteksi_bab_besar(teks)
    kecil = state.deteksi_subbab(teks)
    peta = state.petakan(teks)

    print('\n' + '═' * 104)
    print(f'  NASKAH: {nama}')
    print(f'  {len(teks):,} kar · mesin lihat: {len(besar)} BAB · '
          f'{len(kecil)} sub-bab · peta pakai {len(peta)} bagian')
    print('═' * 104)
    print('  BAB yang mesin lihat :',
          ', '.join(str(b.get('section_id')) for b in besar[:8]) or '(tidak ada)')
    print('  sub-bab mesin lihat  :',
          ', '.join(str(s.get('section_id')) for s in kecil[:10]) or '(tidak ada)')

    h = satpam.periksa(teks, peta)
    print('\n  ── JAWABAN JEV ──')
    print(f"    ok        : {h.get('ok')}")
    print(f"    keputusan : {h.get('keputusan')}")
    print(f"    keyakinan : {h.get('confidence')}")
    print(f"    jumlah    : {h.get('jumlah_bab')}")
    print(f"    alasan    : {str(h.get('alasan'))[:300]}")
    lain = {k: v for k, v in h.items()
            if k not in ('ok', 'keputusan', 'confidence', 'jumlah_bab',
                         'alasan', 'catatan')}
    if lain:
        print(f"    lain      : {json.dumps(lain, ensure_ascii=False)[:400]}")
    # apakah jev menyebut bagian yang mesin LEWATKAN?
    cat = str(h.get('catatan') or '') + ' ' + str(h.get('alasan') or '')
    if cat.strip():
        print(f"    catatan   : {cat[:300]}")
