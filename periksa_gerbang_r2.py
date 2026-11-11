"""Periksa gerbang offline melawan peta tersimpan SEMUA sesi v9/v10.

Tanpa Jev live. Setiap sesi harus LOLOS (G1/G2/G3) untuk naskah yang
dimilikinya; bila satu sesi GAGAL, itu temuan — jangan longgarkan ambang
sampai lolos. Sesi: r2 (v9, hasil_r2_114.json), r2-sesi3 (v10,
hasil_r2_sesi3_114.json — dilewati bila berkas belum ada).
Sesi2 v9 (hasil_r2_sesi2_114.json) TIDAK diperiksa di sini: ia GAGAL G3
(3 judul BAB sampah, pra-R2-3) dan GAGAL G2 melawan baseline 2-run —
kedua kegagalan itu sudah didiagnosis (baseline dibangun ulang dari
4 run; cacat G3 diperbaiki R2-3) dan didokumentasikan di
bangun_baseline_r2_4run.py. Sesi 1.14 TIDAK diperiksa di sini
(baseline-nya sudah diganti; pemeriksanya tetap di
periksa_gerbang_114.py melawan gerbang_baseline_114.json).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import gerbang_3_naskah as G


def peta_r2():
    d = json.load(open(ROOT / 'hasil_r2_114.json', encoding='utf-8'))
    out = {}
    for fid in ('81', '112', '115'):
        out[fid] = [{'bab': list(r.get('bab') or []),
                     'subbab_jml': r['label_hitung'].get('subbab')}
                    for r in d['run'][fid]]
    return out


def peta_r2_sesi3():
    """Peta sesi3 v10 (hasil_r2_sesi3_114.json); None bila belum ada."""
    p = ROOT / 'hasil_r2_sesi3_114.json'
    if not p.exists():
        return None
    d = json.load(open(p, encoding='utf-8'))
    out = {}
    for fid in ('81', '112', '115'):
        out[fid] = [{'bab': list(r.get('bab') or []),
                     'subbab_jml': r['label_hitung'].get('subbab')}
                    for r in d['run'][fid]]
    return out


def main():
    baseline = G.muat_baseline()
    print('Baseline model:', baseline.get('model'),
          '| rule_version:', baseline.get('rule_version'),
          '| tanggal:', baseline.get('tanggal'))
    semua_lolos = True
    print('=== Uji mandiri gerbang (6 kasus) ===')
    ok_uji = G.uji_mandiri()
    semua_lolos = semua_lolos and ok_uji
    print()
    print('=== Gerbang offline per sesi v9/v10 tersimpan ===')
    sesi = [('r2', peta_r2())]
    sesi3 = peta_r2_sesi3()
    if sesi3 is not None:
        sesi.append(('r2-sesi3', sesi3))
    else:
        print('  (sesi3 v10 belum ada — jalankan verifikasi live dulu)')
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
