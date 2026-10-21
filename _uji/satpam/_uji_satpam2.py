"""UJI SATPAM v2 — apakah satpam bisa MEMBETULKAN peta yang bengkak?

Perbandingan: peta LAMA (mesin sendiri) vs peta SETELAH satpam memutuskan.
"""
import glob
import os
import sys

sys.path.insert(0, '/app')
from pathlib import Path

from app.models import FileBerkas, SessionLocal
from app.ai import _teks_dari_berkas
from app.state import deteksi_bab_besar, deteksi_subbab, petakan
from app import satpam

NASKAH = [(9, 'TESIS_Goras'), (60, 'SKRIPSI-unmul'), (70, 'SKRIPSI-unhas-olahraga'),
          (71, 'TESIS-unhas-manajemen'), (72, 'DISERTASI-unhas-stunting'),
          (81, 'SKRIPSI-Asih')]

print('═' * 90)
print('  UJI SATPAM v2 — SATPAM MEMUTUSKAN PETA (bab besar vs sub-bab)')
print('═' * 90)
db = SessionLocal()
ring = []
try:
    for fid, nama in NASKAH:
        f = db.query(FileBerkas).filter(FileBerkas.id == fid).first()
        p = None
        for k in glob.glob(f'/app/**/{f.nama_simpan}', recursive=True)[:5]:
            if os.path.isfile(k):
                p = Path(k); break
        teks = _teks_dari_berkas(p, f.nama or p.name) or ''
        besar = deteksi_bab_besar(teks)
        kecil = deteksi_subbab(teks)
        peta_lama = petakan(teks)                       # TANPA satpam
        h = satpam.periksa(teks, peta_lama)
        peta_baru = petakan(teks, putusan_satpam=h)     # DENGAN satpam

        print(f'\n📄 [{fid}] {nama} ({len(teks):,} kar)')
        print(f'   pilihan mesin lama : {len(peta_lama):>2} bagian '
              f'({", ".join(b["section_id"] for b in peta_lama[:8])}'
              f'{"…" if len(peta_lama) > 8 else ""})')
        print(f'   bab besar ada      : {len(besar)} → '
              f'{", ".join(b["section_id"] for b in besar[:8])}')
        print(f'   sub-bab ada        : {len(kecil)}')
        print(f'   SATPAM bilang      : jumlah_bab={h["jumlah_bab"]} '
              f'conf={h["confidence"]:.3f} · pakai={h.get("pakai")} '
              f'(conf {h.get("pakai_confidence", 0):.2f})')
        print(f'   pilihan SETELAH    : {len(peta_baru):>2} bagian '
              f'({", ".join(b["section_id"] for b in peta_baru[:8])}'
              f'{"…" if len(peta_baru) > 8 else ""})')
        ubah = '✅ DIBETULKAN' if peta_baru is besar and peta_lama is kecil else \
               ('tetap' if peta_baru is peta_lama else 'berubah')
        print(f'   ⇒ {ubah} · {h.get("detik","?")} dtk')
        ring.append({'id': fid, 'nama': nama,
                     'lama': len(peta_lama), 'baru': len(peta_baru),
                     'pakai': h.get('pakai'), 'conf': h['confidence'],
                     'keputusan': h['keputusan']})
finally:
    db.close()

print()
print('═' * 90)
print('  RINGKASAN')
print('═' * 90)
for r in ring:
    tanda = '✅ dibetulkan' if r['baru'] != r['lama'] else 'sama'
    print(f"  [{r['id']:>2}] {r['nama']:26s} {r['lama']:>2} → {r['baru']:>2} bagian "
          f"· satpam: {str(r['pakai']):6s} conf {r['conf']:.2f} "
          f"· {r['keputusan']:5s} · {tanda}")
