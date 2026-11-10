"""Periksa gerbang offline melawan peta tersimpan SEMUA sesi 1.14.

Tanpa Jev live. Setiap sesi harus LOLOS (G1/G2/G3) untuk naskah yang
dimilikinya; bila satu sesi GAGAL, itu temuan — jangan longgarkan ambang
sampai lolos. Sesi: baseline114 (2 run x 3 naskah), verifikasi114
(fid=81, 1 run), ab114-1.14 (fid=81, 1 run). Sesi 1.13 TIDAK diperiksa
di sini (baselinenya sudah diganti 1.14; pemeriksanya tetap di
periksa_gerbang_semua_sesi.py melawan gerbang_baseline_113.json).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import gerbang_3_naskah as G


def peta_baseline114():
    d = json.load(open(ROOT / 'hasil_baseline114.json', encoding='utf-8'))
    out = {}
    for fid in ('81', '112', '115'):
        out[fid] = [{'bab': list(r.get('bab') or []),
                     'subbab_jml': r.get('subbab_jml')}
                    for r in d['run'][fid]]
    return out


def peta_satu_run_81(nama_berkas, kunci_label):
    """Satu run fid=81 tanpa daftar bab tersimpan -> pakai daftar bab
    baseline (judul BAB 81 diputuskan kode, sama seperti pola
    periksa_gerbang_semua_sesi.py)."""
    d = json.load(open(ROOT / nama_berkas, encoding='utf-8'))
    baseline = G.muat_baseline()
    if kunci_label == 'label':
        subbab = d['label']['subbab']
    else:
        subbab = d[kunci_label]['label']['subbab']
    return {'81': [{'bab': list(baseline['81']['bab']),
                    'subbab_jml': subbab}]}


def main():
    baseline = G.muat_baseline()
    print('Baseline model:', baseline.get('model'),
          '| tanggal:', baseline.get('tanggal'))
    semua_lolos = True
    print('=== Uji mandiri gerbang (6 kasus) ===')
    ok_uji = G.uji_mandiri()
    semua_lolos = semua_lolos and ok_uji
    print()
    print('=== Gerbang offline per sesi 1.14 tersimpan ===')
    sesi = [
        ('baseline114', peta_baseline114()),
        ('verifikasi114', peta_satu_run_81('hasil_114_fid81.json',
                                           'label')),
        ('ab114-1.14', peta_satu_run_81('hasil_ab114_fid81.json',
                                        'jev_1_14')),
    ]
    for nama, maps in sesi:
        for fid in ('81', '112', '115'):
            if fid not in maps:
                print('  [%s] fid=%s: tidak ada run (dilewati)'
                      % (nama, fid))
                continue
            ok, pel, per = G.nilai_naskah(maps[fid], baseline[fid], fid)
            semua_lolos = semua_lolos and ok
            print('  [%s] fid=%s: %s %s %s' % (
                nama, fid, 'LOLOS' if ok else 'GAGAL',
                ('pelanggaran=%s' % pel) if pel else '',
                ('peringatan=%s' % per) if per else ''))
    print()
    print('HASIL: %s' % ('SEMUA LOLOS' if semua_lolos else 'ADA YANG GAGAL'))
    return 0 if semua_lolos else 1


if __name__ == '__main__':
    sys.exit(main())
