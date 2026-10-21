#!/usr/bin/env python3
"""UJI JEV-MUTU SUNGGUHAN — naskah Asih BETULAN (bukan palsu).

WAJIB dari DALAM container:
    docker cp _uji_jev_mutu_sungguhan.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _uji_jev_mutu_sungguhan.py

Mengukur: WAKTU + MODEL ASLI + panjang prompt + daftar poin KURANG.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, '/app')

from app import konversi                                                   # noqa: E402

ASIH = Path('/app/uploads/8/3dbd8babe72c6098.docx')


def main() -> int:
    print('══ UJI JEV-MUTU SUNGGUHAN — NASKAH ASIH ══')
    if not ASIH.is_file():
        print(f'❌ tidak ada: {ASIH}')
        return 2

    teks = konversi.baca_docx(ASIH) if hasattr(konversi, 'baca_docx') else ''
    if not teks:
        #  pakai pembaca naskah milik app (butuh nama berkas juga)
        from app import ai
        teks = ai._teks_dari_berkas(str(ASIH), ASIH.name) or ''
    print(f'naskah : {ASIH.name} ({len(teks):,} karakter)')

    hasil = konversi.periksa_mutu(None, 81, teks)
    print(f'\n--- HASIL JEV-MUTU ---')
    print(f'model  : {hasil.get("model")}')
    print(f'waktu  : {hasil.get("detik")} detik')
    print(f'skor   : {hasil.get("skor")}')
    print(f'keputusan: {hasil.get("keputusan")}')
    print(f'alasan : {hasil.get("alasan")}')

    print(f'\n--- POIN YANG ADA ({len(hasil.get("ada") or {})}) ---')
    for label, nilai in (hasil.get('ada') or {}).items():
        tanda = '✅' if nilai >= konversi.AMBANG_ADA else '⚠️'
        print(f'  {tanda} {label:50} {nilai}')

    print(f'\n--- BELUM ADA ({len(hasil.get("kurang") or [])}) ---')
    for label in (hasil.get('kurang') or []):
        print(f'  ❌ {label}')

    print(f'\n--- PERLU DIPERIKSA ({len(hasil.get("ragu") or [])}) ---')
    for label in (hasil.get('ragu') or []):
        print(f'  ⚠️  {label}')

    print(f'\n--- PESAN KE USER (harus LAPOR, bukan vonis) ---')
    print(konversi.rangkum_mutu(hasil))

    #  bukti
    Path('/tmp/jev_mutu.json').write_text(
        json.dumps(hasil, ensure_ascii=False, indent=2))
    print('\n(bukti: /tmp/jev_mutu.json)')
    return 0 if hasil.get('ok') else 1


if __name__ == '__main__':
    sys.exit(main())
