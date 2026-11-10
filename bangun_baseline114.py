"""Bangun baseline gerbang 1.14 dari run live tersimpan (nol Jev).

Sumber run 1.14 (semua sudah terverifikasi dilayani jev-1.14.0):
- hasil_baseline114.json: 2 run baru per naskah (81, 112, 115),
  Gas Bos 10 Nov 2026, 170 panggilan petakan + 6 probe.
- hasil_114_fid81.json: 1 run verifikasi fid=81 (subbab 129).
- hasil_ab114_fid81.json: sisi 1.14 run A/B fid=81 (subbab 130).

Rumus ambang G2 SAMA seperti baseline 1.13:
  ambang_g2 = ceil((max(subbab_run) - min(subbab_run)) / 2) + 2
Median baseline = statistics.median (seperti 1.13: 115 median 72.5
dari 6 run). median_sesi = median cara gerbang (sorted[len//2],
upper-middle untuk n genap), seperti 1.13.

Baseline 1.13 DISIMPAN sebagai ground_truth/gerbang_baseline_113.json
sebelum ditimpa; baseline baru ditandai model=1.14 + tanggal.
Daftar 'bab' baseline dipertahankan dari 1.13 (struktur naskah tidak
berubah dengan model): 81 = I-V, 112/115 = II-V (label Jev; BAB I/VI
dari jalur gabung kode sengaja TIDAK masuk, seperti keputusan 1.13).
Skrip ini MEMERIKSA dulu bahwa setiap judul BAB baseline hadir di
daftar gabung tiap run 1.14; bila ada yang hilang di >=2 run, berhenti
dan laporkan (itu temuan, bukan untuk disembunyikan).
"""
import json
import math
import shutil
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / 'ground_truth' / 'gerbang_baseline.json'
BASELINE_113 = ROOT / 'ground_truth' / 'gerbang_baseline_113.json'


def muat(nama):
    return json.load(open(ROOT / nama, encoding='utf-8'))


def main():
    lama = muat('ground_truth/gerbang_baseline.json')
    baru114 = muat('hasil_baseline114.json')
    verif81 = muat('hasil_114_fid81.json')
    ab114 = muat('hasil_ab114_fid81.json')

    # Kumpulkan run per naskah: (sumber, subbab, paragraf, bab_gabung)
    run = {'81': [], '112': [], '115': []}
    for r in baru114['run']['81']:
        run['81'].append(('baseline114-run%d' % r['run'],
                          r['subbab_jml'], r['paragraf_jml'], r['bab']))
    for r in baru114['run']['112']:
        run['112'].append(('baseline114-run%d' % r['run'],
                           r['subbab_jml'], r['paragraf_jml'], r['bab']))
    for r in baru114['run']['115']:
        run['115'].append(('baseline114-run%d' % r['run'],
                           r['subbab_jml'], r['paragraf_jml'], r['bab']))
    # fid=81: dua run 1.14 lama (daftar bab tidak tersimpan -> pakai
    # baseline, seperti pola periksa_gerbang_semua_sesi.py).
    bab81 = list(lama['81']['bab'])
    run['81'].append(('verifikasi114',
                      verif81['label']['subbab'],
                      verif81['label']['paragraf'], bab81))
    run['81'].append(('ab114-1.14',
                      ab114['jev_1_14']['label']['subbab'],
                      ab114['jev_1_14']['label']['paragraf'], bab81))

    # Periksa G1: setiap judul BAB baseline harus hadir di tiap run.
    for fid in ('81', '112', '115'):
        for sumber, _s, _p, bab in run[fid]:
            hilang = [b for b in lama[fid]['bab'] if b not in bab]
            if hilang:
                print('TEMUAN: fid=%s %s kehilangan BAB baseline: %s'
                      % (fid, sumber, hilang))
                print('Berhenti — putuskan dulu apakah baseline BAB '
                      'harus diubah, jangan timpa diam-diam.')
                return 1

    # Simpan baseline 1.13 sebelum ditimpa.
    if not BASELINE_113.exists():
        shutil.copy(BASELINE, BASELINE_113)
        print('Baseline 1.13 disimpan di:', BASELINE_113.name)
    else:
        print('Baseline 1.13 sudah tersimpan di:', BASELINE_113.name)

    def med_gate(vals):
        s = sorted(vals)
        return s[len(s) // 2]

    hasil = {'model': '1.14',
             'tanggal': '2026-11-10',
             'catatan': ('Baseline gerbang model 1.14 (MODEL_DEFAULT '
                         'SATPAM/typesafe/jev-1.14, RULE_VERSION '
                         'jev-peta-v7). Baseline 1.13 tersimpan di '
                         'gerbang_baseline_113.json. PERHATIAN: 112/115 '
                         'baru punya 2 run, jadi rentang antar-run adalah '
                         'batas bawah dan ambang G2=3 ketat — sesi 1.14 '
                         'berikutnya bisa duduk di batas karena drift '
                         'model (lebar drift 1.13: 112=7, 115=11). Bila '
                         'G2 gagal mepet, ulangi satu sesi segar sebelum '
                         'menvonis regresi.')}

    for fid in ('81', '112', '115'):
        sub = [s for _n, s, _p, _b in run[fid]]
        par = [p for _n, _s, p, _b in run[fid]]
        med = statistics.median(sub)
        rentang = [min(sub), max(sub)]
        ambang = math.ceil((max(sub) - min(sub)) / 2) + 2
        # median per sesi (cara gerbang): verif, ab114, baseline114.
        sesi = {}
        for nama, s, _p, _b in run[fid]:
            kunci = nama.split('-')[0]
            sesi.setdefault(kunci, []).append(s)
        med_sesi = [med_gate(v) for v in sesi.values()]
        hasil[fid] = {
            'model': '1.14',
            'bab': list(lama[fid]['bab']),
            'subbab_per_run': sub,
            'subbab_median': med,
            'paragraf_per_run': par,
            'paragraf_median': statistics.median(par),
            'ambang_g2': ambang,
            'rentang_subbab_run': rentang,
            'median_sesi': med_sesi,
            'rentang_median_sesi': [min(med_sesi), max(med_sesi)],
            'sumber': ('run 1.14: ' + ', '.join(
                '%s=%s' % (n, s) for n, s, _p, _b in run[fid])),
            'rumus_ambang_g2': ('ambang_g2 = ceil((max(subbab_run) - '
                                 'min(subbab_run)) / 2) + 2'),
        }
        print('fid=%s subbab %s median %s rentang %s ambang_g2 %s | '
              'paragraf %s median %s | median_sesi %s'
              % (fid, sub, med, rentang, ambang, par,
                 statistics.median(par), med_sesi))

    # WULAN-1: belum ada run 1.14 — bawa dari 1.13, ditandai jelas.
    w = dict(lama['WULAN-1'])
    w['model'] = '1.13'
    w['catatan'] = ('referensi 1.13 saja — belum ada run 1.14 untuk '
                    'WULAN-1; gerbang tidak memeriksanya.')
    hasil['WULAN-1'] = w

    with open(BASELINE, 'w', encoding='utf-8') as f:
        json.dump(hasil, f, ensure_ascii=False, indent=2)
    print('Baseline 1.14 ditulis ke:', BASELINE)
    return 0


if __name__ == '__main__':
    sys.exit(main())
