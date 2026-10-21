"""Smoke helper P (28Sep26) — bukti helper SEHAT sebelum putaran penuh.

Arah: baseline probe 'hidup' → matikan SEMUA → 'mati' + count 0 → restore
→ daftar PERSIS. Kalau gagal: TIDAK jalan putaran C7 (hemat 40 menit).
"""
import importlib.util
import sys

spec = importlib.util.spec_from_file_location('uji_c7', '_uji_publik_komentar.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

awal = mod._id_aktif_9r()
probe1 = mod._probe_9router()
print(f'baseline : {len(awal)} aktif · probe {probe1}', flush=True)

kena = mod._set_aktif_9r(awal, 0)
sisa = mod._id_aktif_9r()
probe2 = mod._probe_9router()
print(f'dimatikan: kena {kena}/{len(awal)} · sisa {len(sisa)} · probe {probe2}', flush=True)

kembali = mod._set_aktif_9r(awal, 1)
akhir = mod._id_aktif_9r()
persis = set(akhir) == set(awal) and kembali == len(awal)
print(f'restore  : {"PERSIS" if persis else "BEDA! " + str(set(awal) ^ set(akhir))} · balik {kembali}', flush=True)

ok = (probe1 == 'hidup' and kena == len(awal) and not sisa
      and probe2 == 'mati' and persis)
print('SMOKE LULUS ✅' if ok else 'SMOKE GAGAL ❌', flush=True)
sys.exit(0 if ok else 1)
