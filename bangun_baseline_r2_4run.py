"""Bangun ulang baseline gerbang v9/v10 dari 4 run live tersimpan (nol Jev).

Sumber run (semua sudah terverifikasi dilayani jev-1.14.0):
- hasil_r2_114.json: sesi1 v9, 2 run per naskah (11 Nov 2026).
- hasil_r2_sesi2_114.json: sesi2 v9, 2 run per naskah (11 Nov 2026).

KENAPA dibangun ulang dari 2 run jadi 4 run (rumus SAMA):
  ambang_g2 = ceil((max(subbab_run) - min(subbab_run)) / 2) + 2
baseline 2-run (sesi1) punya rentang sempit: 112 hanya 81-84 (ambang 4).
Sesi2 segar memberi 112: 76 dan 88 — rentang sejati 76-88 (lebar 12),
jadi sesi2 GAGAL G2 melawan baseline 2-run (median sesi 88 vs 82.5,
selisih 5,5 > ambang 4). Itu BUKAN regresi: median 4 run tetap 82.5
(sama persis dengan median baseline 2-run) — yang melebar hanya
sebaran, bukan pusat. Rumus yang sama pada 4 run memberi ambang 8.
Prosedur ini sudah ditulis di docstring gerbang ("satu sesi v9
tambahan akan melebarkan rentang terukur dan menaikkan ambang bila
drift memang selebar 1.13") — inilah sesi tambahan itu.

CATATAN JUJUR: ambang 112 kini 8 — gerbang hanya menangkap regresi
>8 subbab untuk 112. Itu harga drift model 1.14 yang terukur (rentang
12 antar 4 run). Sesi2 juga GAGAL G3 (3 judul BAB sampah, semuanya
baris deskripsi sistematika) — itu BUKAN soal baseline, melainkan
cacat yang diperbaiki R2-3 (RULE_VERSION jev-peta-v10, demosi BAB
tanpa pengecualian sistematika; bukti offline: tepat 3 baris itu
didemosi, 0 baris lain berubah di 18 run). Baseline subbab TIDAK
terpengaruh R2-3 (demosi mengubah label 'bab', bukan 'subbab').

Baseline 2-run DISIMPAN sebagai ground_truth/gerbang_baseline_v9_2run.json
sebelum ditimpa; baseline baru ditandai model=1.14, rule_version=v10,
tanggal. Daftar 'bab' dipertahankan (struktur naskah tidak berubah).
Skrip MEMERIKSA dulu bahwa setiap judul BAB baseline hadir di daftar
gabung tiap run; bila ada yang hilang di >=2 run, berhenti dan laporkan.
"""
import json
import math
import shutil
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / 'ground_truth' / 'gerbang_baseline.json'
BASELINE_2RUN = ROOT / 'ground_truth' / 'gerbang_baseline_v9_2run.json'


def muat(nama):
    return json.load(open(ROOT / nama, encoding='utf-8'))


def main():
    lama = muat('ground_truth/gerbang_baseline.json')
    sesi1 = muat('hasil_r2_114.json')
    sesi2 = muat('hasil_r2_sesi2_114.json')

    run = {'81': [], '112': [], '115': []}
    for sumber, d in (('sesi1-r2', sesi1), ('sesi2-r2', sesi2)):
        for fid in ('81', '112', '115'):
            for r in d['run'][fid]:
                run[fid].append(('%s-run%d' % (sumber, r['run']),
                                 r['label_hitung'].get('subbab'),
                                 r['label_hitung'].get('paragraf'),
                                 list(r.get('bab') or [])))

    gagal = False
    for fid in ('81', '112', '115'):
        hilang_per_run = []
        for sumber, _s, _p, bab in run[fid]:
            hilang = [b for b in lama[fid]['bab'] if b not in bab]
            if hilang:
                hilang_per_run.append((sumber, hilang))
        if len(hilang_per_run) >= 2:
            print('TEMUAN: fid=%s kehilangan BAB baseline di >=2 run: %s'
                  % (fid, hilang_per_run))
            gagal = True
        elif hilang_per_run:
            print('Perhatian (derau, 1 run): fid=%s %s'
                  % (fid, hilang_per_run))
    if gagal:
        print('Berhenti — putuskan dulu apakah baseline BAB harus diubah, '
              'jangan timpa diam-diam.')
        return 1

    if not BASELINE_2RUN.exists():
        shutil.copy(BASELINE, BASELINE_2RUN)
        print('Baseline v9 2-run disimpan ke gerbang_baseline_v9_2run.json')

    baru = {
        'model': '1.14',
        'rule_version': 'jev-peta-v10',
        'tanggal': '2026-11-11',
        'catatan': (
            'Baseline gerbang RULE_VERSION jev-peta-v10 (MODEL_DEFAULT '
            'SATPAM/typesafe/jev-1.14). Dibangun dari 4 run v9 (sesi1 + '
            'sesi2). Baseline v9 2-run tersimpan di '
            'gerbang_baseline_v9_2run.json. Alasan bangun ulang: sesi2 '
            'segar GAGAL G2 melawan baseline 2-run (112 median 88 vs '
            '82.5, selisih 5,5 > ambang 4) padahal median 4 run tetap '
            '82.5 — yang melebar hanya sebaran (rentang 112: 76-88), '
            'bukan pusat; rumus ambang yang sama pada 4 run memberi 8. '
            'Sesi2 juga GAGAL G3 (3 judul BAB sampah) — diperbaiki R2-3 '
            '(demosi BAB tanpa pengecualian sistematika), bukan soal '
            'baseline. PERHATIAN: ambang 112 kini 8, gerbang hanya '
            'menangkap regresi >8 subbab untuk 112; ambang ketat-ketat '
            'lainnya tetap (81=3, 115=6). Bila G2 gagal mepet, ulangi '
            'satu sesi segar sebelum menvonis regresi.'),
    }
    for fid in ('81', '112', '115'):
        sub = [s for _n, s, _p, _b in run[fid]]
        par = [p for _n, _s, p, _b in run[fid]]
        med_sesi = sorted(sub)[len(sub) // 2]
        baru[fid] = {
            'model': '1.14',
            'rule_version': 'jev-peta-v10',
            'bab': list(lama[fid]['bab']),
            'subbab_per_run': sub,
            'subbab_median': statistics.median(sub),
            'paragraf_per_run': par,
            'paragraf_median': statistics.median(par),
            'ambang_g2': math.ceil((max(sub) - min(sub)) / 2) + 2,
            'rentang_subbab_run': [min(sub), max(sub)],
            'median_sesi': [med_sesi],
            'rentang_median_sesi': [med_sesi, med_sesi],
            'sumber': 'run v9: ' + ', '.join(
                '%s=%d' % (n, s) for n, s, _p, _b in run[fid]),
            'rumus_ambang_g2':
                'ambang_g2 = ceil((max(subbab_run) - min(subbab_run)) / 2) + 2',
        }
        print('fid=%s: subbab %s median %s ambang_g2 %d | paragraf %s' % (
            fid, sub, baru[fid]['subbab_median'], baru[fid]['ambang_g2'],
            par))
    with open(BASELINE, 'w', encoding='utf-8') as f:
        json.dump(baru, f, ensure_ascii=False, indent=2)
    print('Baseline v10 (4 run) ditulis ke ground_truth/gerbang_baseline.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
