"""Hasil akhir verifikasi live v11 (tahap 5) -> hasil_verifikasi_v11.json.

Menggabungkan hasil_verifikasi_v11_A/B (18 berhasil), C2/C3 (13 gagal
probe: TypeSafe 402 kredit habis), banding v10 (hasil_latih_grup1-4),
dan bukti 4 klaim v11. Tanpa Jev, tanpa label manusia baru.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path('/home/hatch/workspace/jev-v5')
sys.path.insert(0, str(ROOT))
from _verifikasi_v11.banding_v10_v11 import (  # noqa: E402
    muat_v10, klasifikasi_bab, cek_baris_v11)

TEST36 = ('AO-2 AP-3 AJ-1 T3 R3 S2 AN-1 AM-2 U3 AL-2 AI-2 AK-3 Q3 O3 P2 M3 '
          'N3 L3 B4 D3 F4 X3 AA3 AD3 A4 W3 Z3 E3 J3 AE2 C4 AC2 G3 I4 Y2 '
          'H1').split()

# Anggaran panggilan tahap 5 sesi ini (dicatat dari log tiap run).
ANGGARAN = {
    'pilot_AD3_pelari_lama': 12,
    'gelombang1_gagal_sebelum_perbaikan_pelari_R3_T3': 28,
    'smoke2_AD3_pelari_baru': 12,
    'gelombang_A': 164,
    'gelombang_B': 166,
    'gelombang_C2_gagal_probe': 24,
    'konfirmasi_C3_AC2': 2,
}
HARGA_PER_PANGGILAN_RP = 10  # jangkar ukur_biaya_3_naskah + tahap 1 (~Rp10)


def muat_v11_semua():
    berhasil, gagal = {}, {}
    for tag in ('A', 'B', 'C2', 'C3'):
        p = ROOT / '_verifikasi_v11' / ('hasil_verifikasi_v11_%s.json' % tag)
        d = json.load(open(p, encoding='utf-8'))
        for e in d['entri']:
            if e.get('status') == 'berhasil':
                berhasil[e['kode']] = e
            else:
                gagal[e['kode']] = {
                    'kode': e['kode'], 'tag': tag,
                    'alasan': e.get('alasan'),
                    'bukti_model': e.get('bukti_model'),
                    # Tiap entri gagal = 2 percobaan probe, 0 petakan.
                    'panggilan_probe': 2,
                }
    return berhasil, gagal


def main():
    v10 = muat_v10()
    v11, gagal = muat_v11_semua()
    per_kode = []
    tot_sampah10 = tot_sampah11 = 0
    for k in sorted(v11):
        a, b = v10[k], v11[k]
        s10 = [t for t in a['bab_semua'] if klasifikasi_bab(t)[0] == 'sampah']
        s11 = [t for t in b['bab_semua'] if klasifikasi_bab(t)[0] == 'sampah']
        tot_sampah10 += len(s10)
        tot_sampah11 += len(s11)
        cek = cek_baris_v11(b)
        per_kode.append({
            'kode': k, 'bidang': b['bidang'],
            'panggilan_v10': a['panggilan'], 'panggilan_v11': b['panggilan_total'],
            'goyang_v10': a['goyang'], 'goyang_v11': b['goyang_jml'],
            'label_v10': a['label'], 'label_v11': dict(b['label']),
            'bab_semua_v10': a['bab_semua'], 'bab_semua_v11': list(b['bab_semua']),
            'sampah_v10': s10, 'sampah_v11': s11,
            'bab_label_v11': list(b['bab_label']),
            'gabung_v11': b.get('gabung_penuh') or {},
            'profil_penomonan': b['profil_bentuk']['penomoran_bab'],
            'bom_jml_profil': b['profil_bentuk'].get('bom_jml'),
            'pemisah_jml_profil': b['profil_bentuk'].get('pemisah_gabung_jml'),
            'cek_baris': cek,
            'antrean_manusia': b['antrean_manusia'],
            'pendapat_kedua_jml': b['pendapat_kedua_jml'],
            'bab_demosi_jml': b['bab_demosi_jml'],
            'hakim': b['hakim'],
        })
    total_panggilan = sum(ANGGARAN.values())
    klaim = {
        'a_romawi_tanpa_bab': {
            'vonis': 'TERBUKTI SEBAGIAN, premis awal salah',
            'bukti': ('Y2: v10 sudah 5 bab Romawi (bukan 0), v11 tetap 5, '
                      'kini deterministik di gabung + BOM terkelupas '
                      '(baris[0]=I. PENDAHULUAN bersih). W3 (romawi 5) dan '
                      'AA3 (romawi 8) BELUM terverifikasi live: gagal probe '
                      '402. Hanya 1 kasus Romawi independen terverifikasi.'),
            'naskah': ['Y2'],
        },
        'b_chapter_inggris': {
            'vonis': 'TERBUKTI SEBAGIAN, belum bersih',
            'bukti': ('T3: bab_semua 35->11, sampah 15->6; 5 judul isi kini '
                      'tepat tergabung di gabung (CHAPTER I INTRODUCTION '
                      'dst, tanpa BOM). Sisa: 5 duplikat halaman daftar isi '
                      'CHAPTER x: ... + TABLE OF CONTENS masih dilabel bab '
                      'oleh Jev. T3 satu-satunya naskah CHAPTER di uji.'),
            'naskah': ['T3'],
        },
        'c_pemisah_bom': {
            'vonis': 'TERBUKTI PENUH (18/18)',
            'bukti': ('0 baris pemisah dilabel bab; 0 karakter BOM tersisa '
                      'di baris maupun gabung; judul ganda akibat BOM '
                      'runtuh: F4 20->5, J3 22->5, L3 20->5, U3 16->7, '
                      'X3 9->5 bab_semua.'),
            'naskah': sorted(v11),
        },
        'd_antrean_manusia': {
            'vonis': 'TIDAK TERUJI live (0/18 masuk antrean)',
            'bukti': ('Tidak satu pun dari 18 naskah uji masuk antrean; '
                      'aturan antrean hanya teruji offline.'),
            'naskah': [],
        },
    }
    # Beda label per baris (grup3 saja, label_penuh v10 ada).
    beda_baris = {}
    for k in sorted(v11):
        a = v10.get(k)
        b = v11[k]
        if not a or not a.get('label_penuh') or not b.get('label_penuh'):
            continue
        l10 = {int(i): v for i, v in a['label_penuh'].items()}
        l11 = {int(i): v for i, v in b['label_penuh'].items()}
        beda = Counter()
        for i in sorted(set(l10) | set(l11)):
            if l10.get(i) != l11.get(i):
                beda[(l10.get(i), l11.get(i))] += 1
        beda_baris[k] = {('%s->%s' % (x, y)): c for (x, y), c in
                         sorted(beda.items(), key=lambda kv: -kv[1])}
    hasil = {
        'tahap': 'tahap 5 verifikasi live v11',
        'rule_version': 'jev-peta-v11',
        'model_diminta': 'SATPAM/typesafe/jev-1.14 (bukti jev-1.14.0)',
        'naskah_uji_total': 36,
        'naskah_terverifikasi': len(v11),
        'naskah_gagal_probe': sorted(gagal),
        'naskah_belum_dicoba': sorted(set(TEST36) - set(v11) - set(gagal)),
        'per_kode': per_kode,
        'beda_label_per_baris_grup3': beda_baris,
        'gagal_probe': gagal,
        'klaim_v11': klaim,
        'agregat_18_naskah': {
            'panggilan_v10': sum(p['panggilan_v10'] for p in per_kode),
            'panggilan_v11': sum(p['panggilan_v11'] for p in per_kode),
            'goyang_v10': sum(p['goyang_v10'] for p in per_kode),
            'goyang_v11': sum(p['goyang_v11'] for p in per_kode),
            'sampah_bab_v10': tot_sampah10,
            'sampah_bab_v11': tot_sampah11,
            'hakim_sepakat': sum(p['hakim']['jumlah_sepakat'] for p in per_kode),
            'hakim_ragu': sum(p['hakim']['jumlah_ragu'] for p in per_kode),
            'hakim_curiga': sum(p['hakim']['jumlah_curiga'] for p in per_kode),
            'pendapat_kedua_total': sum(p['pendapat_kedua_jml'] for p in per_kode),
            'antrean_jml': sum(1 for p in per_kode if p['antrean_manusia']),
        },
        'skor_teks_lawan_label_manusia': {
            'status': 'TIDAK MUNGKIN',
            'alasan': ('ground_truth_latih112.tsv berisi 254 baris dari 63 '
                       'naskah LATIH; 0 baris dari 36 naskah UJI. Tidak ada '
                       'label kebenaran dasar manusia untuk naskah uji, '
                       'sesuai rancangan tahap 3 (label hanya naskah latih, '
                       'tanpa kebocoran).'),
        },
        'anggaran_panggilan': dict(ANGGARAN, total=total_panggilan,
                                   batas=600, sisa=600 - total_panggilan),
        'biaya_perkiraan_rp': {
            'metode': ('jangkar ukur_biaya_3_naskah + tahap 1: ~Rp10 per '
                       'panggilan, batas atas chars/4, $0,042/1 jt token, '
                       'kurs Rp18.100/USD, output gratis, Jev tidak '
                       'mengembalikan pemakaian token'),
            'total_panggilan': total_panggilan,
            'perkiraan_rp': total_panggilan * HARGA_PER_PANGGILAN_RP,
            'rentang_rp': [int(total_panggilan * HARGA_PER_PANGGILAN_RP * 0.72),
                           total_panggilan * HARGA_PER_PANGGILAN_RP],
        },
        'pemblokir': {
            'jenis': 'TypeSafe HTTP 402 kredit habis',
            'pesan': ('Your organization has no available TypeSafe API '
                      'credits. Please add more credits and/or set up '
                      'auto-reload at https://console.typesafe.ai/settings/billing'),
            'dampak': ('Penyedia resmi gagal sejak gelombang C2 (~04:15 WIB); '
                       'satpam jatuh ke OpenRouter yang melayani '
                       'typesafe/jev-1.14-20261014; probe menolak karena '
                       'bukan jev-1.14.0 persis. 12 naskah gagal probe '
                       '(24 panggilan probe, 0 petakan) + 1 konfirmasi '
                       '(2 panggilan).'),
            'pilihan_lanjut': [
                'Isi ulang kredit TypeSafe, lalu jalankan 18 naskah sisa '
                'dengan probe jev-1.14.0 yang sama.',
                'Atau Boss menyetujui fallback OpenRouter '
                'typesafe/jev-1.14-20261014 sebagai setara 1.14 (perlu '
                'keputusan eksplisit; bobot belum terbukti identik).',
            ],
        },
        'vonis': {
            'ringkas': ('v11 TIDAK TERBUKTI menaikkan presisi keseluruhan di '
                        'naskah uji. Yang terbukti: pembersihan artefak '
                        '(pemisah/BOM) penuh, judul CHAPTER/Romawi lebih '
                        'rapi di gabung, sampah bab turun 49->39. Yang tidak '
                        'terbukti: goyang tidak turun (1411->1414), panggilan '
                        'tidak turun (299->292), label bergerak dalam rentang '
                        'noise, sampah bab masih ada di 8 dari 18 naskah.'),
            'naik': ['pembersihan pemisah/BOM (18/18)',
                     'judul bab ganda akibat BOM runtuh ke 5 (F4/J3/L3)',
                     'judul CHAPTER isi tergabung bersih (T3, gabung)',
                     'judul Romawi deterministik di gabung (Y2)',
                     'sampah bab total 49->39'],
            'tidak_naik': ['goyang dalam-run (1411->1414, identik)',
                           'panggilan Jev (299->292, -2%)',
                           'label subbab/paragraf (bergerak dua arah, noise)',
                           'sampah bab masih 39 di 8/18 naskah',
                           'Lapis 2 pendapat_kedua: 0 kali jalan live',
                           'antrean manusia: 0 kali terpicu live'],
            'catatan': ('Skor teks lawan label manusia TIDAK MUNGKIN dihitung '
                        '(0 label uji). Vonis di atas memakai agregat + cek '
                        'deterministik, bukan skor presisi manusia.'),
        },
    }
    out = ROOT / 'hasil_verifikasi_v11.json'
    json.dump(hasil, open(out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('ditulis:', out)
    print('terverifikasi:', len(v11), '| gagal probe:', len(gagal),
          '| belum dicoba:', len(set(TEST36) - set(v11) - set(gagal)))
    print('goyang v10->v11:',
          hasil['agregat_18_naskah']['goyang_v10'], '->',
          hasil['agregat_18_naskah']['goyang_v11'])
    print('panggilan v10->v11:',
          hasil['agregat_18_naskah']['panggilan_v10'], '->',
          hasil['agregat_18_naskah']['panggilan_v11'])
    print('sampah bab v10->v11:', tot_sampah10, '->', tot_sampah11)
    print('total panggilan tahap 5:', total_panggilan,
          '| biaya ~Rp', total_panggilan * HARGA_PER_PANGGILAN_RP)


if __name__ == '__main__':
    main()
