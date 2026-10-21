"""UJI FASE 3 — state.py (26 sub-bab) + tabel baru. DI DALAM container.

UJI DENGAN DOKUMEN NYATA: tesis Bos & skripsi Wulandari (7,29 MB).
"""
import sys
sys.path.insert(0, '/app')

from app import state
from app.models import (SectionState, RevisiHistory, ProfilDokumen,
                        init_db, SessionLocal)
from sqlalchemy import inspect

print('=' * 68)
print('UJI A — peta 26 sub-bab + get_category_for')
print('=' * 68)
print(f'  jumlah sub-bab terdaftar: {len(state.semua_section_id())}')
peta_uji = [
    ('1.1', 'bab1'), ('2.4', 'bab2'), ('3.4', 'bab3'),
    ('4.5', 'bab4'), ('5.3', 'bab5'), ('abstrak', 'meta'),
    ('lampiran_kuesioner', 'lampiran'), ('xxx', 'bab'), ('', 'bab'), (None, 'bab'),
]
salah = 0
for sid, harus in peta_uji:
    dpt = state.get_category_for(sid)
    ok = dpt == harus
    if not ok:
        salah += 1
    print(f'  {str(sid):20s} -> {dpt:9s} (harus {harus}) {"OK" if ok else "SALAH"}')
print(f'  HASIL: {"SEMUA BENAR" if salah == 0 else f"{salah} SALAH"}')

print()
print('=' * 68)
print('UJI B — judul baku')
print('=' * 68)
for sid in ['1.1', '2.3', '4.5', '5.1']:
    print(f'  {sid} -> {state.title_for(sid)!r}')
print(f'  tak dikenal -> {state.title_for("9.9", "Fallback")!r}')

print()
print('=' * 68)
print('UJI C — deteksi sub-bab dari TEKS NASKAH NYATA')
print('=' * 68)

# Baca teks dokumen nyata dari disk produksi
from app.ai import _teks_dari_berkas
from pathlib import Path
from app.config import UPLOAD_DIR

kandidat = []
for d in sorted(UPLOAD_DIR.glob('*')):
    if d.is_dir():
        for f in sorted(d.glob('*')):
            if f.suffix.lower() in ('.docx', '.pdf', '.txt') and f.stat().st_size > 10000:
                kandidat.append(f)

print(f'  berkas uji tersedia: {len(kandidat)}')
for f in kandidat[:4]:
    print(f'    {f.stat().st_size:>10,} byte  {f.name}')

for f in kandidat[:3]:
    print()
    print(f'  ── {f.name} ({f.stat().st_size/1048576:.2f} MB) ──')
    try:
        teks = _teks_dari_berkas(f, f.name)
    except Exception as e:
        print(f'     gagal ekstrak: {type(e).__name__}: {e}')
        continue
    if not teks:
        print('     teks kosong')
        continue
    print(f'     teks: {len(teks):,} karakter')
    peta = state.petakan(teks)
    print(f'     terdeteksi: {len(peta)} bagian')
    for p in peta[:12]:
        print(f'       {p["section_id"]:12s} {p["section_title"][:30]:30s} '
              f'{p["char_count"]:>8,} kar  [{p["kategori"]}]')
    if len(peta) > 12:
        print(f'       … dan {len(peta)-12} lagi')
    tot = sum(p['char_count'] for p in peta)
    print(f'     total karakter terpetakan: {tot:,} (dari {len(teks):,})')

print()
print('=' * 68)
print('UJI D — tabel section_state & revisi_history')
print('=' * 68)
init_db()
insp = inspect(SessionLocal().bind)
tabel = insp.get_table_names()
for nama in ['section_state', 'revisi_history']:
    ada = nama in tabel
    print(f'  {nama:18s}: {"ADA" if ada else "TIDAK ADA"}')
    if ada:
        kol = [c['name'] for c in insp.get_columns(nama)]
        print(f'    {len(kol)} kolom: {", ".join(kol[:10])}…')
        uq = [u['name'] for u in insp.get_unique_constraints(nama)]
        if uq:
            print(f'    unique: {uq}')
print(f'  TOTAL tabel DB: {len(tabel)}')

print()
print('=' * 68)
print('UJI E — cascade mendaftarkan kedua tabel?')
print('=' * 68)
from app import cascade
anak = [m.__name__ for m in cascade._ANAK_FILE]
print(f'  _ANAK_FILE: {anak}')
print(f'  SectionState  : {"YA" if SectionState in cascade._ANAK_FILE else "TIDAK"}')
print(f'  RevisiHistory : {"YA" if RevisiHistory in cascade._ANAK_FILE else "TIDAK"}')
