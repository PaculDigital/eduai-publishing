#!/usr/bin/env python3
"""Ukur v17 (beku dari main 3b6fa0d) DENGAN konteks sintetis gt35.

Tujuan: garis dasar v17 yang relevan dengan produksi. Ukur v17 lama
(255/279) memakai konteks=None, sehingga pagar zona R10 (yang di
produksi selalu jalan karena _v16_koreksi_petakan selalu membangun
konteks dari peta penuh) tidak terukur. Skrip ini mengukur v17
dengan konteks yang sama seperti ukur v18, untuk melihat apakah
ada baris yang di produksi sebenarnya tidak diperbaiki R10.

0 Jev, 0 LLM. Memakai bangun_konteks() dari ukur_rantai_v18.py.
Modul v17 dimuat dari /tmp/peta3_jev_v17.py (git show main:peta3_jev.py).

Pemakaian:
    git show main:peta3_jev.py > /tmp/peta3_jev_v17.py
    python3 _sketsa/ukur_v17_dengan_konteks.py
"""
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_sketsa'))

app = types.ModuleType('app')
app.__path__ = [str(ROOT / 'app')]
sys.modules['app'] = app
_ai = types.ModuleType('app.ai')
_ai.SessionLocal = object
_ai._teks_dari_berkas = lambda *a, **k: ''
_ai.UPLOAD_DIR = Path('/tmp')
sys.modules['app.ai'] = _ai
_models = types.ModuleType('app.models')
_models.FileBerkas = object
sys.modules['app.models'] = _models


class _SatpamDiam:
    def tanya_bebas_mutu(self, *a, **k):
        raise AssertionError('harness tidak boleh memanggil Jev')


sys.modules['app.satpam'] = _SatpamDiam()
_state = types.ModuleType('app.state')
_state.buang_daftar_isi = lambda t: t
sys.modules['app.state'] = _state

_spec = importlib.util.spec_from_file_location(
    '_peta3_produksi_v17_beku', '/tmp/peta3_jev_v17.py')
P17 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P17)
assert P17.RULE_VERSION == 'jev-peta-v17', P17.RULE_VERSION

import aturan_v16  # noqa: E402
import ukur_rantai_v18 as U18  # noqa: E402  (bangun_konteks saja)


def main():
    rows, _ = aturan_v16.muat()
    assert len(rows) == 279
    benar = {(r['naskah'], str(r['no'])): r['label_benar'] for r in rows}
    rantai = {(r['naskah'], str(r['no'])): r['label_rantai'] for r in rows}
    konteks, info = U18.bangun_konteks(rows)

    lama = json.load(open(ROOT / '_verifikasi_v11'
                          / 'hasil_rantai_v17_aturan_baru.json'))
    lab_lama = {(k.split(':')[0], k.split(':')[1]): v for k, v in
                lama['label_akhir']['aturan_baru_dari_rantai'].items()}

    lab17, jejak17 = P17._v16_terapkan(rows, rantai, konteks=konteks)
    skor17 = sum(1 for r in rows
                 if lab17[(r['naskah'], str(r['no']))] == r['label_benar'])
    beda = []
    for r in rows:
        k = (r['naskah'], str(r['no']))
        if lab17[k] != lab_lama[k]:
            beda.append({'baris': f"{r['naskah']}:{r['no']}",
                         'teks': r['teks_baris'][:80],
                         'tanpa_konteks_255': lab_lama[k],
                         'dengan_konteks': lab17[k],
                         'jejak': jejak17[k],
                         'label_benar': benar[k]})
    print('v17 beku DENGAN konteks:', skor17, '/279 (tanpa konteks: 255)')
    print('baris yang berubah vs ukur 255:')
    for b in beda:
        print(' ', b)
    print('silang konteks:', info)


if __name__ == '__main__':
    main()
