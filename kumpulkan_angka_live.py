"""Kumpulkan angka live tersimpan per naskah per sesi (tanpa Jev live).

Sesi kode v7 (b41392a; v8 sesudahnya hanya hapus kode mati + label model,
tidak menyentuh jalur klasifikasi — diff terbukti kosong di
peta3_jev.py, app/sambung_kode.py, app/jev.py):
  - v7:        hasil_v7_live.json        (3 run/naskah)
  - ab114-113: hasil_ab114_fid81.json    (1 run, fid=81, model 1.13.0 terverifikasi)
  - deploy:    hasil_deploy_live.json    (1 run, fid=81, 115)
  - gerbang:   hasil_gerbang_live.json   (2 run/naskah)
Sesi kode LAMA (hanya pembanding, TIDAK masuk baseline — kodenya beda):
  - v6 run1/run2, v5 run2.

Keluaran: angka_live_terkumpul.json + tabel ringkas ke stdout.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _run(r):
    lab = r.get('label') or {}
    pang = r.get('panggilan_total')
    if pang is None:
        p = r.get('panggilan') or {}
        pang = sum(p.values()) if isinstance(p, dict) else None
    return {
        'subbab': r.get('subbab_jml', lab.get('subbab')),
        'paragraf': r.get('paragraf_jml', lab.get('paragraf')),
        'goyang': r.get('goyang'),
        'panggilan': pang,
        'wall': r.get('wall'),
        'bab': list(r.get('bab') or r.get('bab_judul') or []),
    }


def _sesi(nama, berkas, fids):
    d = json.load(open(ROOT / berkas, encoding='utf-8'))
    out = {}
    for fid in fids:
        node = d.get(fid)
        if node is None:
            continue
        runs = node if isinstance(node, list) else [node]
        out[fid] = [_run(r) for r in runs]
    return out


def _sesi_ab114():
    d = json.load(open(ROOT / 'hasil_ab114_fid81.json', encoding='utf-8'))
    r = d['jev_1_13']
    return {'81': [{**_run(r), 'bab': list(r.get('bab_judul') or [])}]}


def main():
    fids = ('81', '112', '115', 'WULAN-1')
    sesi = {
        'v5-run2': _sesi('v5-run2', 'hasil_v5_live.json', fids),
        'v6-run1': _sesi('v6-run1', 'hasil_v6_live_run1.json', fids),
        'v6-run2': _sesi('v6-run2', 'hasil_v6_live.json', fids),
        'v7': _sesi('v7', 'hasil_v7_live.json', fids),
        'ab114-1.13': _sesi_ab114(),
        'deploy': _sesi('deploy', 'hasil_deploy_live.json', fids),
        'gerbang': _sesi('gerbang', 'hasil_gerbang_live.json', fids),
    }
    json.dump(sesi, open(ROOT / 'angka_live_terkumpul.json', 'w',
                         encoding='utf-8'),
              ensure_ascii=False, indent=2)

    print('%-12s %-8s %s' % ('sesi', 'fid', 'subbab / paragraf / goyang / panggilan'))
    for nama, data in sesi.items():
        for fid in fids:
            runs = data.get(fid)
            if not runs:
                continue
            for i, r in enumerate(runs):
                print('%-12s %-8s run%d: subbab=%s paragraf=%s goyang=%s panggilan=%s'
                      % (nama, fid, i + 1, r['subbab'], r['paragraf'],
                         r['goyang'], r['panggilan']))
    print()
    print('=== BASELINE KODE v7: v7 + ab114-1.13 + deploy + gerbang ===')
    for fid in ('81', '112', '115', 'WULAN-1'):
        vals = []
        for nama in ('v7', 'ab114-1.13', 'deploy', 'gerbang'):
            for r in sesi[nama].get(fid, []):
                vals.append(r)
        if not vals:
            continue
        sub = [r['subbab'] for r in vals if r['subbab'] is not None]
        par = [r['paragraf'] for r in vals if r['paragraf'] is not None]
        goy = [r['goyang'] for r in vals if r['goyang'] is not None]
        pang = [r['panggilan'] for r in vals if r['panggilan'] is not None]
        print('%s: n=%d  subbab %s median=%s rentang=%d-%d  '
              'paragraf median=%s rentang=%d-%d  goyang median=%s rentang=%d-%d  '
              'panggilan %s' % (
                  fid, len(vals), sub,
                  statistics.median(sub), min(sub), max(sub),
                  statistics.median(par), min(par), max(par),
                  statistics.median(goy), min(goy), max(goy), pang))


if __name__ == '__main__':
    main()
