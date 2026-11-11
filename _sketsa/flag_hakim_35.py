"""FLAG HAKIM 35 — himpunan flag deterministik per naskah uji (Fase A offline).

NOL panggilan Jev. Untuk tiap dari 35 naskah uji tahap 5, dari peta v11
tersimpan (hasil mentah):
  - curiga_kode: idx kandidat judul yang audit struktural Hakim Source-1
    tandai curiga (deterministik, persis).
  - tanya_kandidat: idx kandidat yang butuh tanya Jev Source-2
    (_butuh_tanya_jev, bukan curiga, cap 48/peta) — vonis ragu/sepakat
    di antaranya HANYA bisa diketahui dengan memanggil Jev (Fase A live);
    berkas ini menyimpan daftar kandidatnya saja.
  - panggilan_prediksi: ceil(len(tanya_kandidat)/24) — sama dengan rumus
    periksa_peta; totalnya harus cocok dengan hakim_panggilan tahap 5 (38).
Keluaran: _sketsa/flag_hakim_35.json.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


class _FakeSatpam:
    def tanya_bebas_mutu(self, *a, **k):
        raise RuntimeError('flag: Jev tidak boleh dipanggil')


def _stub_app():
    app = types.ModuleType('app')
    app.__path__ = [str(ROOT / 'app')]
    sys.modules['app'] = app
    ai = types.ModuleType('app.ai')
    ai.SessionLocal = object
    ai._teks_dari_berkas = lambda *a, **k: ''
    ai.UPLOAD_DIR = Path('/tmp')
    sys.modules['app.ai'] = ai
    models = types.ModuleType('app.models')
    models.FileBerkas = object
    sys.modules['app.models'] = models
    sys.modules['app.satpam'] = _FakeSatpam()
    state = types.ModuleType('app.state')
    state.buang_daftar_isi = lambda t: t
    sys.modules['app.state'] = state


def _muat(nama, jalur):
    spec = importlib.util.spec_from_file_location(nama, str(jalur))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    _stub_app()
    P = _muat('_peta3_flag', ROOT / 'peta3_jev.py')
    import app.hakim_peta as H

    mentah = {}
    for f in ['hasil_verifikasi_v11_A.json', 'hasil_verifikasi_v11_B.json',
              'hasil_verifikasi_v11_OR1.json', 'hasil_verifikasi_v11_OR2.json',
              'hasil_verifikasi_v11_OR3.json', 'hasil_verifikasi_v11_OR4.json',
              'hasil_verifikasi_v11_OR5.json']:
        d = json.load(open(ROOT / '_verifikasi_v11' / f, encoding='utf-8'))
        for e in d.get('entri', []):
            mentah[e['kode']] = e

    out = {'naskah': {}, 'total_tanya_kandidat': 0, 'total_curiga': 0,
           'total_panggilan_prediksi': 0, 'total_ragu_tersimpan': 0}
    for kode in sorted(mentah):
        e = mentah[kode]
        baris = e.get('baris') or []
        label = {int(k): v for k, v in (e.get('label_penuh') or {}).items()}
        gabung = {int(k): v for k, v in (e.get('gabung_penuh') or {}).items()}
        kand = sorted((i, baris[i]) for i in label if i < len(baris))
        sist = P._tandai_sistematika(baris, label, kand)
        peta = {'baris': baris, 'label': label, 'gabung': gabung,
                'sistematika': sorted(sist), 'p': {}}
        kj = H._kandidat_judul(peta)
        cur = H._audit_struktural(peta, kj)
        perlu = [k for k in kj
                 if k['i'] not in cur and H._butuh_tanya_jev(k)][:H.MAKS_TANYA_TOTAL]
        panggilan = (len(perlu) + H.MAKS_TANYA - 1) // H.MAKS_TANYA
        hk = e.get('hakim') or {}
        out['naskah'][kode] = {
            'curiga_kode': sorted(cur),
            'tanya_kandidat': sorted(k['i'] for k in perlu),
            'panggilan_prediksi': panggilan,
            'hakim_tersimpan': {
                'jumlah_sepakat': hk.get('jumlah_sepakat', 0),
                'jumlah_ragu': hk.get('jumlah_ragu', 0),
                'jumlah_curiga': hk.get('jumlah_curiga', 0),
                'jumlah_belum': hk.get('jumlah_belum', 0)},
        }
        out['total_tanya_kandidat'] += len(perlu)
        out['total_curiga'] += len(cur)
        out['total_panggilan_prediksi'] += panggilan
        out['total_ragu_tersimpan'] += hk.get('jumlah_ragu', 0)
    json.dump(out, open(ROOT / '_sketsa' / 'flag_hakim_35.json',
                        'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('naskah:', len(out['naskah']))
    print('total tanya_kandidat:', out['total_tanya_kandidat'],
          '| total curiga_kode:', out['total_curiga'],
          '| ragu tersimpan:', out['total_ragu_tersimpan'],
          '| panggilan prediksi:', out['total_panggilan_prediksi'])
    print('per naskah (tanya, curiga, ragu_tersimpan):',
          {k: (len(v['tanya_kandidat']), len(v['curiga_kode']),
               v['hakim_tersimpan']['jumlah_ragu'])
           for k, v in out['naskah'].items() if v['tanya_kandidat'] or v['curiga_kode']})


if __name__ == '__main__':
    main()
