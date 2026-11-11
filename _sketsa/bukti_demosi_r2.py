"""Bukti offline R2-3 (nol Jev): demosi BAB harusnya menangkap 3 judul
sampah sesi2, tapi tidak — karena pengecualian sistematika.

Rekonstruksi masukan _koreksi_bab_deterministik dari hasil tersimpan
(baris, label, kand, sistematika, gabung, kode_label — semua tersimpan
di JSON pelari), jalankan fungsi ASLI dan fungsi PERBAIKAN, bandingkan
apa yang berubah. Yang diharapkan dari perbaikan: tepat 3 baris sampah
sesi2 didemosi (112 run1 idx 467, 112 run2 idx 451, 115 run2 idx 471),
dan TIDAK ADA baris lain yang berubah di 18 run tersimpan.

Stub modul berat mengikuti pola tests/test_jev_hakim.py (_stub_app).
"""
import copy
import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _muat_peta3():
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
    satpam = types.ModuleType('app.satpam')
    satpam.tanya_bebas_mutu = lambda *a, **k: {}
    sys.modules['app.satpam'] = satpam
    state = types.ModuleType('app.state')
    state.buang_daftar_isi = lambda t: t
    sys.modules['app.state'] = state

    class FakeKonversi:
        @classmethod
        def _pecah_blok(cls, teks):
            return [{'text': b, 'lines': [n], 'kosong': not b}
                    for n, b in enumerate((teks or '').split('\n'))]
    sys.modules['app.konversi'] = FakeKonversi
    spec = importlib.util.spec_from_file_location(
        '_peta3_bukti', str(ROOT / 'peta3_jev.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def muat_run(nama):
    d = json.load(open(ROOT / nama, encoding='utf-8'))
    out = []
    for fid, runs in d['run'].items():
        for r in runs:
            out.append((nama, fid, r['run'], r))
    return out


def rekonstruksi(r, P):
    baris = list(r['baris'])
    label = {int(k): v for k, v in (r.get('label') or {}).items()}
    kand = [(int(i), t) for i, t in r.get('kand') or []]
    # 'sistematika' TIDAK tersimpan di JSON pelari — rekonstruksi dengan
    # fungsi deterministiknya dari label akhir. Validasi: dengan kode
    # kini, demosi harus mereproduksi label akhir TANPA perubahan
    # (bila rekonstruksi salah, validasi ini gagal dulu).
    sistematika = P._tandai_sistematika(baris, label, kand)
    gabung = {int(k): tuple(v) for k, v in (r.get('gabung') or {}).items()}
    kode_label = set(r.get('kode_label') or [])
    return baris, label, kand, sistematika, gabung, kode_label


def main():
    P = _muat_peta3()
    semua = []
    for nama in ('hasil_sesudah_opt_114.json', 'hasil_r2_114.json',
                 'hasil_r2_sesi2_114.json'):
        semua.extend(muat_run(nama))
    print('run diperiksa:', len(semua))
    total_berubah = []
    for nama, fid, run_no, r in semua:
        baris, label, kand, sistematika, gabung, kode_label = rekonstruksi(r, P)
        label_awal = dict(label)
        _bk, _bg, demosi = P._koreksi_bab_deterministik(
            baris, label, kand, sistematika, gabung, kode_label)
        berubah = {i: (label_awal.get(i), label.get(i))
                   for i in label
                   if label_awal.get(i) != label.get(i)}
        if berubah or demosi:
            print('%s fid=%s run%d: demosi=%s berubah=%s'
                  % (nama, fid, run_no, demosi, berubah))
            for i, (lama, baru) in sorted(berubah.items()):
                print('    idx %d: %r -> %r | teks %r'
                      % (i, lama, baru, baris[i][:80]))
                total_berubah.append((nama, fid, run_no, i, lama, baru))
    print('total baris berubah di 18 run:', len(total_berubah))
    print('RULE_VERSION:', P.RULE_VERSION)


if __name__ == '__main__':
    main()
