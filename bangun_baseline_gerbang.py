"""Bangun ulang baseline gerbang dari SEMUA sesi kode v7 (bukan satu sore).

Akar masalah (terbukti 10 Nov 2026): baseline lama memakai median 3 run
v7 satu sore; model Jev bergeser antar sesi, jadi ambang G2 ±5 dari
median satu sore terlalu ketat — dua sesi malam yang sama (uji deploy
21:22 dan gerbang 22:30) sepakat angkanya tapi di atas rentang v7 sore.

Sesi yang MASUK baseline (kode SAMA, b41392a; perubahan v8 sesudahnya
hanya hapus kode mati + label model, diff jalur klasifikasi kosong):
  v7, ab114-1.13 (fid=81, model 1.13.0 terverifikasi), deploy, gerbang.
Sesi kode LAMA (v5, v6) TIDAK masuk: kodenya beda (v6 tidak punya
pisah ekor subbab v7.1 dlsb.) — buktinya subbab v6 fid=115 (63, 65)
berada DI BAWAH rentang v7 (67-78). Mencampur kode lama akan
melebarkan rentang karena perubahan kode, bukan drift model, dan
melemahkan gerbang.

RUMUS AMBANG G2 (per naskah, tertulis di baseline JSON juga):
  ambang_g2 = ceil((max(subbab_run) - min(subbab_run)) / 2) + 2
  - (max-min)/2: setengah rentang run yang terukur. Median 2 run baru
    lebih stabil daripada satu run, jadi setengah rentang run adalah
    batas longgar yang wajar untuk simpangan median.
  - +2: margin untuk sesi yang belum teramati (n hanya 5-7 run, rentang
    sejati pasti lebih lebar dari yang teramati). Margin ini KECIL dan
    ditulis eksplisit: lebih kecil dari regresi terkecil yang gerbang
    wajib tangkap (+10 subbab, kasus uji mandiri 5), lebih besar dari 0.
  Gerbang tetap menangkap regresi +-10 di semua naskah (selisih 10 >
  ambang 2/6/8), tapi TIDAK bisa membedakan regresi kecil (+-5) dari
  drift model biasa — itu harga dari drift yang terukur, bukan cacat
  ambang. Dilaporkan jujur, bukan disembunyikan.

BAB baseline TIDAK diubah: daftar gabung gerbang (BAB I dan BAB VI)
bukan pengukuran yang sama dengan label Jev v7 — pelari gerbang
mengeluarkan gabungan label Jev + judul gabung kode, dan judul BAB VI
yang sama persis muncul di dua naskah berbeda. Soal BAB VI sudah masuk
paket sengketa (ground_truth_115.tsv baris 69) menunggu label manusia.
"""
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SESI_V7 = ('v7', 'ab114-1.13', 'deploy', 'gerbang')
BAB_LAMA = {
    '81': ['BAB I PENDAHULUAN', 'BAB II TINJAUAN PUSTAKA',
           'BAB III METODE PENELITIAN', 'BAB IV HASIL DAN PEMBAHASAN',
           'BAB V PENUTUP'],
    '112': ['BAB II TINJAUAN PUSTAKA', 'BAB III METODOLOGI PENELITIAN',
            'BAB IV HASIL DAN PEMBAHASAN', 'BAB V PENUTUP'],
    '115': ['BAB II TINJAUAN PUSTAKA', 'BAB III METODOLOGI PENELITIAN',
            'BAB IV HASIL DAN PEMBAHASAN', 'BAB V PENUTUP'],
}
RUMUS = 'ambang_g2 = ceil((max(subbab_run) - min(subbab_run)) / 2) + 2'


def main():
    terkumpul = json.load(open(ROOT / 'angka_live_terkumpul.json',
                               encoding='utf-8'))
    lama = json.load(open(ROOT / 'ground_truth' / 'gerbang_baseline.json',
                          encoding='utf-8'))
    baru = {}
    for fid in ('81', '112', '115', 'WULAN-1'):
        runs_sub, runs_par = [], []
        sesi_dipakai = []
        for nama in SESI_V7:
            rs = terkumpul.get(nama, {}).get(fid) or []
            if rs:
                sesi_dipakai.append('%s(%d run)' % (nama, len(rs)))
            for r in rs:
                if r.get('subbab') is not None:
                    runs_sub.append(r['subbab'])
                if r.get('paragraf') is not None:
                    runs_par.append(r['paragraf'])
        if not runs_sub:
            continue
        rentang = max(runs_sub) - min(runs_sub)
        ambang = math.ceil(rentang / 2) + 2
        # Cross-check: sebaran median sesi (yang dibandingkan gerbang).
        med_sesi = []
        for nama in SESI_V7:
            rs = terkumpul.get(nama, {}).get(fid) or []
            vals = sorted(r['subbab'] for r in rs
                          if r.get('subbab') is not None)
            if vals:
                med_sesi.append(vals[len(vals) // 2])
        entri = {
            'bab': BAB_LAMA.get(fid) or lama.get(fid, {}).get('bab', []),
            'subbab_per_run': runs_sub,
            'subbab_median': statistics.median(runs_sub),
            'paragraf_per_run': runs_par,
            'paragraf_median': statistics.median(runs_par),
            'ambang_g2': ambang,
            'rentang_subbab_run': [min(runs_sub), max(runs_sub)],
            'median_sesi': med_sesi,
            'rentang_median_sesi': ([min(med_sesi), max(med_sesi)]
                                    if med_sesi else []),
            'sumber': ('sesi kode v7 (b41392a + v8 tanpa ubah klasifikasi): '
                       + ', '.join(sesi_dipakai)),
            'rumus_ambang_g2': RUMUS,
        }
        if fid == 'WULAN-1':
            entri['catatan'] = ('referensi saja — gerbang hanya memeriksa '
                                'fid 81/112/115; WULAN-1 hanya punya 1 sesi '
                                'v7 (3 run), jadi ambangnya dari rentang run.')
        baru[fid] = entri
        print('%s: n=%d subbab %s median=%s rentang=%d-%d '
              'median_sesi=%s ambang_g2=%d' % (
                  fid, len(runs_sub), runs_sub,
                  statistics.median(runs_sub), min(runs_sub), max(runs_sub),
                  med_sesi, ambang))
    out = ROOT / 'ground_truth' / 'gerbang_baseline.json'
    json.dump(baru, open(out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('ditulis:', out)


if __name__ == '__main__':
    main()
