#!/usr/bin/env python3
"""BANDING BASELINE — Regression corpus peta3 (usul Bos 09 Okt 2026).

Tujuan: tiap kali prompt/aturan diubah, jalankan skrip ini. Kalau angka
TURUN dibanding baseline → ketahuan langsung (pelajaran insiden prompt korup).

Cara pakai (DI DALAM container eduai-app):
    docker cp _banding_baseline.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _banding_baseline.py 81 ASIH

Baseline disimpan di BASELINE_PETA3.json. Kalau file itu belum ada,
skrip ini MEMBUAT-nya (dari run sekarang) — jadi run pertama = kunci baseline.
"""
import json
import os
import sys

BAS = '/app/BASELINE_PETA3.json'

# ── ambang TURUN yang dianggap regresi (bukan goyang normal) ──
TOLERANSI = {
    'bab': 0,          # bab TIDAK BOLEH berubah
    'subbab': 5,       # boleh goyang ≤5
    'paragraf': 8,
    'goyang': 6,
}


def ambil(fid):
    import peta3_jev
    r = peta3_jev.petakan(fid, None, None)
    hitung = {}
    for _i, v in r['label'].items():
        hitung[v] = hitung.get(v, 0) + 1
    return {
        'bab': hitung.get('bab', 0),
        'subbab': hitung.get('subbab', 0),
        'paragraf': hitung.get('paragraf', 0),
        'biasa': hitung.get('biasa', 0),
        'kandidat': r['kand_jml'],
        'buang': len(r['buang']),
        'goyang': len(r['goyang']),
        'sistematika': sorted(r.get('sistematika') or []),
    }


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 81
    jdl = sys.argv[2] if len(sys.argv) > 2 else 'ASIH'
    sekarang = ambil(fid)

    print('=' * 64)
    print('BANDING BASELINE — %s (fid=%d)' % (jdl, fid))
    print('=' * 64)

    if not os.path.exists(BAS):
        with open(BAS, 'w') as f:
            json.dump({jdl: sekarang}, f, indent=2, ensure_ascii=False)
        print('📌 BASELINE BARU DIKUNCI:')
        for k, v in sekarang.items():
            print('   %-12s : %s' % (k, v))
        print('\n   disimpan di %s' % BAS)
        return 0

    with open(BAS) as f:
        bas = json.load(f)
    lama = bas.get(jdl)
    if not lama:
        bas[jdl] = sekarang
        with open(BAS, 'w') as f:
            json.dump(bas, f, indent=2, ensure_ascii=False)
        print('📌 baseline untuk %s ditambahkan.' % jdl)
        return 0

    regresi = []
    print('   %-12s %10s %10s   %s' % ('unsur', 'baseline', 'sekarang', 'beda'))
    print('   ' + '-' * 52)
    for k in ('bab', 'subbab', 'paragraf', 'biasa', 'kandidat', 'buang', 'goyang'):
        a, b = lama.get(k), sekarang.get(k)
        d = (b - a) if (a is not None and b is not None) else None
        tanda = ''
        if d is not None:
            if k in TOLERANSI:
                if k == 'bab' and d != 0:
                    tanda = '🔴 BAB BERUBAH!'
                    regresi.append(k)
                elif abs(d) > TOLERANSI[k]:
                    tanda = '🔴 TURUN/NAIK TERLALU JAUH'
                    regresi.append(k)
                elif d:
                    tanda = '🟡 goyang kecil'
                else:
                    tanda = '✅'
            else:
                tanda = 'ℹ️  (info)'
        print('   %-12s %10s %10s   %s' % (k, a, b, tanda))

    print()
    if regresi:
        print('🔴 REGRESI TERDETEKSI: %s — PERIKSA SEBELUM LANJUT!' % ', '.join(regresi))
        return 1
    print('✅ TIDAK ADA REGRESI — aman lanjut.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
