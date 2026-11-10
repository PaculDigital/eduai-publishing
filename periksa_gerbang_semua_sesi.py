"""Periksa gerbang offline melawan peta tersimpan SEMUA sesi kode v7.

Tanpa Jev live. Setiap sesi harus LOLOS (G1/G2/G3) untuk naskah yang
dimilikinya; bila satu sesi GAGAL, itu temuan — jangan longgarkan ambang
sampai lolos. Sesi: v7 (3 run), ab114-1.13 (fid=81), deploy (81, 115),
gerbang (2 run). Peta dibangun dari angka_live_terkumpul.json
(bab + subbab_jml); fid=81 dengan daftar bab kosong memakai daftar
baseline (sama seperti muat_peta_v7: judul BAB 81 diputuskan kode).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import gerbang_3_naskah as G


def peta_dari_terkumpul(sesi_nama):
    terkumpul = json.load(open(ROOT / 'angka_live_terkumpul.json',
                               encoding='utf-8'))
    baseline = G.muat_baseline()
    out = {}
    for fid in ('81', '112', '115'):
        runs = []
        for r in terkumpul.get(sesi_nama, {}).get(fid) or []:
            bab = list(r.get('bab') or [])
            if fid == '81' and not bab:
                bab = list(baseline['81']['bab'])
            runs.append({'bab': bab, 'subbab_jml': r.get('subbab')})
        if runs:
            out[fid] = runs
    return out


def main():
    baseline = G.muat_baseline()
    semua_lolos = True
    print('=== Uji mandiri gerbang (6 kasus) ===')
    ok_uji = G.uji_mandiri()
    semua_lolos = semua_lolos and ok_uji
    print()
    print('=== Gerbang offline per sesi tersimpan ===')
    for sesi in ('v7', 'ab114-1.13', 'deploy', 'gerbang'):
        maps = peta_dari_terkumpul(sesi)
        for fid in ('81', '112', '115'):
            if fid not in maps:
                print('  [%s] fid=%s: tidak ada run (dilewati)' % (sesi, fid))
                continue
            ok, pel, per = G.nilai_naskah(maps[fid], baseline[fid], fid)
            semua_lolos = semua_lolos and ok
            print('  [%s] fid=%s: %s %s %s' % (
                sesi, fid, 'LOLOS' if ok else 'GAGAL',
                ('pelanggaran=%s' % pel) if pel else '',
                ('peringatan=%s' % per) if per else ''))
    print()
    print('HASIL: %s' % ('SEMUA LOLOS' if semua_lolos else 'ADA YANG GAGAL'))
    return 0 if semua_lolos else 1


if __name__ == '__main__':
    sys.exit(main())
