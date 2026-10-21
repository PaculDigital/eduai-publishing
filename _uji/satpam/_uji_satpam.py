"""UJI SATPAM — pakai fungsi SUNGGUHAN app.satpam pada naskah nyata.

Dijalankan DI DALAM container eduai-app (agar bisa baca berkas naskah).
"""
import glob
import json
import os
import sys

sys.path.insert(0, '/app')

from pathlib import Path

from app.models import FileBerkas, SessionLocal
from app.ai import _teks_dari_berkas
from app.state import petakan
from app import satpam

NASKAH = [(9, 'TESIS_Goras'), (60, 'SKRIPSI-unmul'), (70, 'SKRIPSI-unhas-olahraga'),
          (71, 'TESIS-unhas-manajemen'), (72, 'DISERTASI-unhas-stunting'),
          (81, 'SKRIPSI-Asih')]

print('═' * 84)
print('  UJI SATPAM (app/satpam.py) — fungsi SUNGGUHAN, 6 naskah nyata')
print('═' * 84)
print(f'  AKTIF={satpam.AKTIF} · BASE={satpam.BASE}')
print(f'  MODEL={satpam.MODEL} · AMBANG_LOLOS={satpam.AMBANG_LOLOS}')
print()

db = SessionLocal()
ringkas = []
try:
    for fid, nama in NASKAH:
        f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
        if not f:
            print(f'[{fid}] berkas tidak ada'); continue
        p = None
        for k in glob.glob(f'/app/**/{f.nama_simpan}', recursive=True)[:5]:
            if os.path.isfile(k):
                p = Path(k); break
        if p is None:
            print(f'[{fid}] naskah fisik tidak ketemu'); continue
        teks = _teks_dari_berkas(p, f.nama or p.name) or ''
        if not teks:
            print(f'[{fid}] teks kosong'); continue

        peta = petakan(teks)
        h = satpam.periksa(teks, peta)
        print(f'📄 [{fid}] {nama} ({len(teks):,} kar)')
        print(f'   mesin lama temukan : {len(peta)} bagian '
              f'({", ".join(b["section_id"] for b in peta[:9])})')
        print(f'   satpam             : {h["keputusan"].upper()} '
              f'· keyakinan {h["confidence"]:.3f} · {h.get("detik", "?")} dtk')
        print(f'   jumlah bab (Jev)   : {h["jumlah_bab"]} '
              f'(mesin bilang {h["jumlah_bab_mesin"]}) '
              f'{"✅ SAMA" if h["jumlah_bab"] == h["jumlah_bab_mesin"] else "⚠️ BEDA"}')
        print(f'   romawi sah         : {h["romawi_sah"]} · berurutan: {h["berurutan"]}')
        print(f'   alasan             : {h["alasan"]}')
        print()
        ringkas.append({'id': fid, 'nama': nama,
                        'mesin': len(peta), 'jev': h['jumlah_bab'],
                        'keputusan': h['keputusan'], 'conf': h['confidence']})
finally:
    db.close()

print('═' * 84)
lolos = sum(1 for r in ringkas if r['keputusan'] == 'lolos')
print(f'  LOLOS {lolos}/{len(ringkas)} · keputusan: '
      f'{[(r["keputusan"]) for r in ringkas]}')
print(f'  jumlah bab Jev == mesin lama: '
      f'{sum(1 for r in ringkas if r["jev"] == r["mesin"])}/{len(ringkas)}')
