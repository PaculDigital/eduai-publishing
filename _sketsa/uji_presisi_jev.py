#!/usr/bin/env python3
"""UJI PRESISI JEV vs MESIN — 18 naskah ASLI (05Okt26).

Pertanyaan Bos: "Apakah jev sudah benar bisa baca dan presisi?
                Mesin kita sebagai fallback jika jev mati"

Uji apa:
  1. Jev melihat berapa BAB?  bandingkan dengan KENYATAAN (jumlah BAB yg
     jelas ada di naskah — diukur dari deteksi mesin + bentuk asli)
  2. Jev melihat KEDALAMAN berapa? bandingkan dengan hitungan nyata
  3. Jev setuju/tidak dengan mesin?

⚠️ Yang TIDAK dilakukan: tidak mengubah data, tidak menyentuh harga.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, '/app')
from app import satpam                                       # noqa: E402
from app.ai import _teks_dari_berkas                         # noqa: E402
from app.state import (buang_daftar_isi, deteksi_bab_besar,   # noqa: E402
                       deteksi_subbab, petakan)

KEL1 = Path('/app/_contoh-dokumen/tesis-bos-gdrive')
KEL2 = Path('/app/_contoh-dokumen')
berkas = sorted(KEL1.glob('*.pdf'))
berkas += sorted(KEL2.glob('*/*.docx'))
berkas += sorted(KEL2.glob('*/*.txt'))

_P = re.compile(
    r'^\s*([1-9]|[12]\d)((?:\.\d{1,2}){1,4})\.?\s+([A-Z][^\n]{2,110})$',
    re.MULTILINE)


def dalam(x: str) -> int:
    return len([p for p in x.strip('.').split('.') if p])


print('═' * 104)
print('  JEV vs MESIN vs KENYATAAN — 18 naskah ASLI')
print('═' * 104)
print(f'  {"berkas":26} {"BAB":>4} {"JEV":>4} {"SELISIH":>8} '
      f'{"kedalaman(mesin)":>17} {"JEV":>4} {"cocok":>6}')
print('─' * 104)

n_bab_cocok = n_bab_selisih = 0
n_kd_cocok = n_kd_selisih = n_kd_jev_none = 0
tolak = tanya = lolos = 0

for p in berkas:
    try:
        t = _teks_dari_berkas(p, p.name)
    except Exception:                                          # noqa: BLE001
        continue
    if not t.strip():
        continue
    bab = deteksi_bab_besar(t)
    pt = petakan(t)
    h = satpam.periksa(t, pt)

    # kedalaman NYATA (dari naskah, sesudah daftar isi dibuang)
    bersih = buang_daftar_isi(t)
    kd = {dalam(f'{m.group(1)}{m.group(2)}')
          for m in _P.finditer(bersih)}
    kd_maks = max(kd) if kd else 0

    jev_bab = h.get('jumlah_bab')
    jev_kd = h.get('kedalaman_subbab')
    sel = '-' if jev_bab is None else str(jev_bab - len(bab))

    cocok_bab = 'YA' if jev_bab == len(bab) else 'TIDAK'
    if jev_bab == len(bab):
        n_bab_cocok += 1
    else:
        n_bab_selisih += 1

    cocok_kd = ('-' if jev_kd is None
                else ('YA' if jev_kd == kd_maks else 'TIDAK'))
    if jev_kd is None:
        n_kd_jev_none += 1
    elif jev_kd == kd_maks:
        n_kd_cocok += 1
    else:
        n_kd_selisih += 1

    kep = h.get('keputusan')
    if kep == 'tolak':
        tolak += 1
    elif kep == 'tanya':
        tanya += 1
    else:
        lolos += 1

    print(f'  {p.name[:26]:26} {len(bab):>4} '
          f'{str(jev_bab) if jev_bab is not None else "-":>4} {sel:>8} '
          f'{kd_maks:>17} {str(jev_kd) if jev_kd is not None else "-":>4} '
          f'{cocok_kd:>6}')

print('═' * 104)
print(f'  BAB   : cocok {n_bab_cocok} · BEDA {n_bab_selisih}')
print(f'  KEDALAMAN: cocok {n_kd_cocok} · BEDA {n_kd_selisih} · '
      f'tidak dijawab {n_kd_jev_none}')
print(f'  KEPUTUSAN Jev: lolos {lolos} · tanya {tanya} · tolak {tolak}')
print('═' * 104)
