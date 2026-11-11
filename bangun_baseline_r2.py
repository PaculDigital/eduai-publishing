"""Bangun baseline gerbang v9 (RULE_VERSION jev-peta-v9) dari run live
tersimpan (nol Jev).

Sumber run v9 (semua sudah terverifikasi dilayani jev-1.14.0):
- hasil_r2_114.json: 2 run baru per naskah (81, 112, 115),
  Gas Bos 11 Nov 2026, 132 panggilan petakan + 6 probe.

KENAPA baseline harus dibangun ulang (bukan longgarkan ambang):
gerbang v9 GAGAL melawan baseline 1.14 (v8): 112 median run 84 vs
baseline 80.0 (selisih 4,0 > ambang 3), 115 median 87 vs 75.5
(selisih 11,5 > ambang 3). Itu BUKAN regresi: kedua run 112 (84, 81)
dan 115 (87, 80) SAMA-SAMA di atas baseline v8 — pergeseran
sistematis dari aturan baru, bukan derau. Mekanismenya terukur:
R2-2 mempertahankan ~6 judul bernomor 1 tingkat per naskah sebagai
kandidat subbab terpisah (sebelumnya tertelan jadi ekor paragraf;
label kebenaran dasar membenarkan: '2. Manfaat Praktis' benar=subbab),
R2-1 memisahkan ~25 butir dash per run (sebagian dilabeli subbab
oleh Jev). Skor-teks tidak turun (112: benar absolut 92->97,
115: rata-rata 57,5%->59,2%), goyang antar-run turun — jadi yang
berubah adalah HITUNGAN yang benar, bukan mutu. Baseline yang
dibangun dari aturan lama tidak lagi mengukur aturan baru; preseden
yang sama dipakai saat 1.13->1.14.

Rumus ambang G2 SAMA seperti baseline 1.13/1.14:
  ambang_g2 = ceil((max(subbab_run) - min(subbab_run)) / 2) + 2
Median baseline = statistics.median (seperti 1.13/1.14).
Baseline 1.14 DISIMPAN sebagai ground_truth/gerbang_baseline_114.json
sebelum ditimpa; baseline baru ditandai model=1.14, rule_version=v9,
tanggal. Daftar 'bab' baseline dipertahankan dari 1.14 (struktur
naskah tidak berubah dengan aturan).
Skrip ini MEMERIKSA dulu bahwa setiap judul BAB baseline hadir di
daftar gabung tiap run v9; bila ada yang hilang di >=2 run, berhenti
dan laporkan (itu temuan, bukan untuk disembunyikan).
"""
import json
import math
import shutil
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / 'ground_truth' / 'gerbang_baseline.json'
BASELINE_114 = ROOT / 'ground_truth' / 'gerbang_baseline_114.json'


def muat(nama):
    return json.load(open(ROOT / nama, encoding='utf-8'))


def main():
    lama = muat('ground_truth/gerbang_baseline.json')
    r2 = muat('hasil_r2_114.json')

    run = {'81': [], '112': [], '115': []}
    for fid in ('81', '112', '115'):
        for r in r2['run'][fid]:
            run[fid].append(('r2-run%d' % r['run'],
                             r['label_hitung'].get('subbab'),
                             r['label_hitung'].get('paragraf'),
                             list(r.get('bab') or [])))

    # Periksa G1: setiap judul BAB baseline harus hadir di tiap run.
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

    # Simpan baseline 1.14 sebelum ditimpa.
    if not BASELINE_114.exists():
        shutil.copy(BASELINE, BASELINE_114)
        print('Baseline 1.14 disimpan ke gerbang_baseline_114.json')

    baru = {
        'model': '1.14',
        'rule_version': 'jev-peta-v9',
        'tanggal': '2026-11-11',
        'catatan': (
            'Baseline gerbang RULE_VERSION jev-peta-v9 (MODEL_DEFAULT '
            'SATPAM/typesafe/jev-1.14). Baseline 1.14 (v8) tersimpan di '
            'gerbang_baseline_114.json. Alasan bangun ulang: gerbang v9 '
            'GAGAL melawan baseline v8 (112 median 84 vs 80.0, 115 median '
            '87 vs 75.5) karena pergeseran SISTEMATIS dari aturan baru '
            '(R2-2 mempertahankan judul bernomor 1 tingkat sebagai subbab, '
            'R2-1 memisahkan butir dash) — bukan regresi: skor-teks tidak '
            'turun, goyang antar-run turun. PERHATIAN: tiap naskah baru '
            'punya 2 run, jadi rentang antar-run adalah batas bawah dan '
            'ambang G2 ketat — sesi v9 berikutnya bisa duduk di batas '
            'karena drift model. Bila G2 gagal mepet, ulangi satu sesi '
            'segar sebelum menvonis regresi.'),
    }
    for fid in ('81', '112', '115'):
        sub = [s for _n, s, _p, _b in run[fid]]
        par = [p for _n, _s, p, _b in run[fid]]
        med_sesi = sorted(sub)[len(sub) // 2]  # median cara gerbang (upper)
        baru[fid] = {
            'model': '1.14',
            'rule_version': 'jev-peta-v9',
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
    print('Baseline v9 ditulis ke ground_truth/gerbang_baseline.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
