"""UJI BERGIGI gerbang tata paragraf — suntik 3 kerusakan nyata.

Dikirim sebagai BERKAS (bukan `python - <<PY`) supaya tidak gagal senyap.
Bukti gerbang bergigi (bukan hiasan):
  ① ambang kalimat dinaikkan 7 → 100  ⇒ B2/B3/B6 HARUS gagal
  ② inden 1 em diganti 0              ⇒ konstanta berubah (dicek gerbang lain)
  ③ tanda baca butir dicampur          ⇒ D4 HARUS gagal
"""
import json
import os
import subprocess
import sys

SRC = '/app/tata_paragraf.py'
CAD = SRC + '.asli'
GEB = '/app/gerbang_tata_paragraf.py'


def jalankan():
    r = subprocess.run([sys.executable, GEB], capture_output=True, text=True)
    out = r.stdout + r.stderr
    gagal = [b for b in out.split('\n') if b.strip().startswith('GAGAL')]
    return r.returncode, gagal


def suntik(ubah):
    asli = open(CAD).read()
    baru = ubah(asli)
    assert baru != asli, 'SUNTIKAN TIDAK MENGUBAH KODE — uji ini akan jadi HIASAN'
    open(SRC, 'w').write(baru)
    return jalankan()


#  simpan asli sekali
if not os.path.exists(CAD):
    open(CAD, 'w').write(open(SRC).read())

hasil = {}

#  ── 0. SEHAT dulu ──────────────────────────────────────────────────────
open(SRC, 'w').write(open(CAD).read())
kode, gagal = jalankan()
hasil['sehat'] = {'exit': kode, 'gagal': len(gagal)}
print('SEHAT      : exit', kode, '| gagal', len(gagal), gagal)

#  ── 1. ambang kalimat dinaikkan 7 → 100 ────────────────────────────────
kode, gagal = suntik(lambda s: s.replace(
    'PARA_MAKS_KALIMAT = 7', 'PARA_MAKS_KALIMAT = 100'))
hasil['ambang_100'] = {'exit': kode, 'gagal': len(gagal)}
print('AMBANG 100 : exit', kode, '| gagal', len(gagal), gagal)

#  ── 2. inden 1 em → 0 ─────────────────────────────────────────────────
kode, gagal = suntik(lambda s: s.replace(
    'INDEN_EM = 11.0', 'INDEN_EM = 0.0'))
hasil['inden_nol'] = {'exit': kode, 'gagal': len(gagal)}
print('INDEN 0    : exit', kode, '| gagal', len(gagal), gagal)

#  ── 3. tanda baca butir dicampur ──────────────────────────────────────
def _campur(s):
    """Buat 1 butir TANPA titik walau butir lain bertitik = tidak seragam."""
    lama = "    baris = [f'• {b}' for b in butir]"
    baru = ("    if butir and len(butir) > 1:\n"
            "        butir[0] = butir[0].rstrip('.')   # SUNTIKAN: campur gaya\n"
            "    baris = [f'• {b}' for b in butir]")
    assert lama in s, 'pola baris poin tidak ketemu'
    return s.replace(lama, baru)


kode, gagal = suntik(_campur)
hasil['butir_campur'] = {'exit': kode, 'gagal': len(gagal)}
print('BUTIR CMPR : exit', kode, '| gagal', len(gagal), gagal)

#  ── pulihkan ───────────────────────────────────────────────────────────
open(SRC, 'w').write(open(CAD).read())
os.remove(CAD)

#  ── putusan ────────────────────────────────────────────────────────────
boleh = (hasil['sehat']['exit'] == 0
         and hasil['ambang_100']['exit'] != 0
         and hasil['inden_nol']['exit'] != 0
         and hasil['butir_campur']['exit'] != 0)
print('\n' + '=' * 60)
print(json.dumps({'bergigi': boleh, 'rincian': hasil}, ensure_ascii=False))
sys.exit(0 if boleh else 1)
