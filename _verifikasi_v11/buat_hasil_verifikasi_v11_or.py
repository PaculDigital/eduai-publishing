"""Gabung hasil kelompok OpenRouter (OR1-OR4, 15 naskah) ke hasil_verifikasi_v11.json.

Memperbarui hasil_verifikasi_v11.json TANPA mengubah angka 18 naskah
TypeSafe pertama (per_kode, agregat_18_naskah, klaim_v11, vonis awal
dipertahankan apa adanya; yang ditambah: per_kode_openrouter, agregat
OpenRouter 15, agregat gabungan 33 yang DITANDAI campuran dua ID model,
klaim lanjutan, anggaran + biaya sesi OR). Tanpa Jev, tanpa label baru.
"""
import json
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

ANGGARAN_OR = {
    'probe_awal_satpam_dan_or_langsung': 2,
    'gelombang_OR1_W3_AA3': 38,
    'gelombang_OR2_A4_AC2_G3_AN-1_M3': 57,
    'gelombang_OR3_AP-3_C4_AK-3_AO-2_N3': 74,
    'gelombang_OR4_AE2_D3_S2': 81,
}
HARGA_PER_PANGGILAN_RP = 10  # jangkar ukur_biaya_3_naskah + tahap 1 (~Rp10)


def muat_v11_or():
    berhasil = {}
    for tag in ('OR1', 'OR2', 'OR3', 'OR4'):
        p = ROOT / '_verifikasi_v11' / ('hasil_verifikasi_v11_%s.json' % tag)
        d = json.load(open(p, encoding='utf-8'))
        for e in d['entri']:
            if e.get('status') == 'berhasil':
                berhasil[e['kode']] = e
    return berhasil


def bangun_per_kode(v10, v11):
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
            'model_melayani': b.get('model_melayani'),
            'model_diminta_jalan': b.get('model_diminta_jalan'),
            'model_override': b.get('model_override'),
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
    return per_kode, tot_sampah10, tot_sampah11


def agregat(per_kode, s10, s11):
    return {
        'panggilan_v10': sum(p['panggilan_v10'] for p in per_kode),
        'panggilan_v11': sum(p['panggilan_v11'] for p in per_kode),
        'goyang_v10': sum(p['goyang_v10'] for p in per_kode),
        'goyang_v11': sum(p['goyang_v11'] for p in per_kode),
        'sampah_bab_v10': s10,
        'sampah_bab_v11': s11,
        'hakim_sepakat': sum(p['hakim']['jumlah_sepakat'] for p in per_kode),
        'hakim_ragu': sum(p['hakim']['jumlah_ragu'] for p in per_kode),
        'hakim_curiga': sum(p['hakim']['jumlah_curiga'] for p in per_kode),
        'pendapat_kedua_total': sum(p['pendapat_kedua_jml'] for p in per_kode),
        'antrean_jml': sum(1 for p in per_kode if p['antrean_manusia']),
    }


def main():
    v10 = muat_v10()
    v11or = muat_v11_or()
    assert len(v11or) == 15, 'OR berhasil harus 15, dapat %d' % len(v11or)
    assert all((e.get('model_melayani') ==
                'typesafe/jev-1.14-20261014') for e in v11or.values()), \
        'ada run OR yang tidak dilayani typesafe/jev-1.14-20261014!'
    assert all(e.get('sidik_berubah') is False for e in v11or.values()), \
        'ada run OR yang mengubah DB!'
    assert not any(e.get('model_override') for e in v11or.values()), \
        'ada run OR dengan model_override (TypeSafe sempat terisi lagi?)'
    per_or, s10or, s11or = bangun_per_kode(v10, v11or)
    agr_or = agregat(per_or, s10or, s11or)
    # Beda label per baris (grup3 saja).
    beda_baris = {}
    for k in sorted(v11or):
        a = v10.get(k)
        b = v11or[k]
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

    out_path = ROOT / 'hasil_verifikasi_v11.json'
    hasil = json.load(open(out_path, encoding='utf-8'))
    # ── JANGAN sentuh angka 18 pertama: per_kode + agregat_18 + klaim + vonis.
    assert len(hasil['per_kode']) == 18, 'per_kode TypeSafe berubah!'
    assert hasil['agregat_18_naskah']['goyang_v10'] == 1411
    agr_ts = hasil['agregat_18_naskah']
    agr_gabung = {
        'panggilan_v10': agr_ts['panggilan_v10'] + agr_or['panggilan_v10'],
        'panggilan_v11': agr_ts['panggilan_v11'] + agr_or['panggilan_v11'],
        'goyang_v10': agr_ts['goyang_v10'] + agr_or['goyang_v10'],
        'goyang_v11': agr_ts['goyang_v11'] + agr_or['goyang_v11'],
        'sampah_bab_v10': agr_ts['sampah_bab_v10'] + agr_or['sampah_bab_v10'],
        'sampah_bab_v11': agr_ts['sampah_bab_v11'] + agr_or['sampah_bab_v11'],
        'hakim_sepakat': agr_ts['hakim_sepakat'] + agr_or['hakim_sepakat'],
        'hakim_ragu': agr_ts['hakim_ragu'] + agr_or['hakim_ragu'],
        'hakim_curiga': agr_ts['hakim_curiga'] + agr_or['hakim_curiga'],
        'pendapat_kedua_total': (agr_ts['pendapat_kedua_total'] +
                                 agr_or['pendapat_kedua_total']),
        'antrean_jml': agr_ts['antrean_jml'] + agr_or['antrean_jml'],
        'peringatan_campuran': (
            'Agregat gabungan MENCAMPUR dua ID model: 18 naskah dilayani '
            'jev-1.14.0 resmi (TypeSafe) + 15 naskah dilayani '
            'openrouter/typesafe/jev-1.14-20261014. Bobot fallback belum '
            'terbukti identik dengan jev-1.14.0 resmi, jadi selisih '
            'v10-vs-v11 kelompok OR bisa berasal dari model, bukan dari '
            'lapisan v11. Pakai agregat per kelompok untuk vonis; agregat '
            'gabungan hanya ringkasan.'),
    }
    total_or = sum(ANGGARAN_OR.values())
    hasil['model_diminta_openrouter'] = (
        'SATPAM/typesafe/jev-1.14 (jatuh ke openrouter '
        'typesafe/jev-1.14-20261014 karena TypeSafe 402)')
    hasil['model_melayani_openrouter'] = 'openrouter/typesafe/jev-1.14-20261014'
    hasil['naskah_terverifikasi_typesafe'] = 18
    hasil['naskah_terverifikasi_openrouter'] = 15
    hasil['naskah_terverifikasi'] = 33
    hasil['naskah_gagal_probe_openrouter'] = []
    hasil['naskah_belum_dicoba'] = ['AJ-1', 'E3']
    hasil['naskah_duplikat_tidak_dihitung'] = [
        'AD3 duplikat berkas Y2 (Y2 sudah terverifikasi di kelompok TypeSafe, '
        '10 panggilan); AD3 tidak dipetakan lagi dan tidak dihitung ganda.',
    ]
    hasil['naskah_belum_terverifikasi_alasan'] = {
        'E3': 'anggaran kelompok OR habis (v10 30 panggilan, termahal kedua)',
        'AJ-1': 'anggaran kelompok OR habis (v10 32 panggilan, termahal)',
        'butuh_tambahan': ('~60-66 panggilan Jev lagi untuk E3 + AJ-1 '
                           '(petakan v10 30+32, ditambah probe + hakim).'),
    }
    hasil['per_kode_openrouter'] = per_or
    hasil['beda_label_per_baris_grup3_openrouter'] = beda_baris
    hasil['agregat_openrouter_15_naskah'] = agr_or
    hasil['agregat_gabungan_33_naskah'] = agr_gabung
    hasil['klaim_v11_openrouter'] = {
        'a_romawi_tanpa_bab': {
            'vonis': 'TERBUKTI SEBAGIAN (lanjutan: kini 3 kasus Romawi)',
            'bukti': (
                'W3 (profil romawi, pakai kata BAB): gabung v11 memuat 5 '
                'judul BAB utuh (BAB I-V) sama seperti v10; label bab Jev '
                'tambah 1 (Tinjauan Pustaka, judul BAB II tanpa awalan BAB). '
                'AA3: 8 bab_semua di v10 maupun v11; 4 judul Romawi tanpa '
                'kata BAB tetap dilabel bab, TAPI 1 dari 4 berganti '
                '(v10: III. KOMISI PERTANIAN DAN PANGAN; v11: IV. KOMISI '
                'TRANSPORTASI DAN INFRASTRUKTUR) — label Romawi goyang '
                'antar versi. Y2 (romawi_tanpa_bab, kelompok TypeSafe) '
                'tetap satu-satunya kasus Romawi-tanpa-BAB yang '
                'deterministik di gabung.'),
            'naskah': ['W3', 'AA3'],
        },
        'b_chapter_inggris': {
            'vonis': 'TIDAK ADA KASUS BARU (T3 satu-satunya, kelompok TypeSafe)',
            'bukti': ('Tidak satu pun dari 15 naskah OR memakai CHAPTER; '
                      'klaim (b) tidak berubah dari laporan 18 pertama.'),
            'naskah': [],
        },
        'c_pemisah_bom': {
            'vonis': 'TERBUKTI PENUH (15/15 kelompok OR; 33/33 gabungan)',
            'bukti': (
                '0 baris pemisah dilabel bab; 0 karakter BOM tersisa di '
                'baris maupun gabung (A4 bom profil 3, AC2 4, C4 5, D3 5, '
                'M3 5, S2 5, AE2 1 — semuanya bersih di baris hasil). Judul '
                'ganda akibat BOM runtuh: C4 18->5, D3 20->5, M3 20->5, '
                'S2 20->5 bab_semua.'),
            'naskah': sorted(v11or),
        },
        'd_antrean_manusia': {
            'vonis': 'TIDAK TERUJI live (0/15 kelompok OR; 0/33 gabungan)',
            'bukti': ('Tidak satu pun dari 15 naskah OR masuk antrean; '
                      'aturan antrean hanya teruji offline. Hakim curiga '
                      '5 kali (W3 2 butir-bertanya, S2 2 nomor-loncat, '
                      'AE2 1 awal-sitasi), semuanya log saja.'),
            'naskah': [],
        },
    }
    hasil['anggaran_panggilan_kelompok_openrouter'] = dict(
        ANGGARAN_OR, total=total_or, batas=250,
        keterangan=('Batas ~250 untuk kelompok OR: 250 panggilan gelombang '
                    'OR1-OR4 + 2 probe awal = 252 total sesi ini (lewat 2 '
                    'karena 2 probe awal sebelum gelombang). E3 + AJ-1 '
                    'tidak dijalankan karena anggaran habis.'))
    hasil['anggaran_panggilan']['total_tahap5_semua_kelompok'] = (
        hasil['anggaran_panggilan']['total'] + total_or)
    hasil['biaya_perkiraan_rp_kelompok_openrouter'] = {
        'metode': ('jangkar ukur_biaya_3_naskah + tahap 1: ~Rp10 per '
                   'panggilan, batas atas chars/4, $0,042/1 jt token, '
                   'kurs Rp18.100/USD, output gratis, Jev tidak '
                   'mengembalikan pemakaian token'),
        'total_panggilan': total_or,
        'perkiraan_rp': total_or * HARGA_PER_PANGGILAN_RP,
        'rentang_rp': [int(total_or * HARGA_PER_PANGGILAN_RP * 0.72),
                       total_or * HARGA_PER_PANGGILAN_RP],
    }
    hasil['biaya_perkiraan_rp_tahap5_semua_kelompok'] = {
        'metode': hasil['biaya_perkiraan_rp_kelompok_openrouter']['metode'],
        'total_panggilan': hasil['anggaran_panggilan']['total_tahap5_semua_kelompok'],
        'perkiraan_rp': (hasil['anggaran_panggilan']['total_tahap5_semua_kelompok']
                         * HARGA_PER_PANGGILAN_RP),
    }
    hasil['pemblokir']['status_akhir_kelompok_or'] = (
        'TypeSafe resmi MASIH 402 di setiap probe kelompok OR (jejak satpam '
        'tiap run: resmi jev-1.14.0 GAGAL HTTP 402, openrouter DIPAKAI). '
        'Kredit TIDAK terisi lagi selama run; jalur model_override (butir 5) '
        'tidak pernah terpicu (0 kali). E3 + AJ-1 tertunda karena anggaran, '
        'bukan karena probe.')
    hasil['vonis_gabungan_33_naskah'] = {
        'ringkas': (
            'v11 TIDAK TERBUKTI menaikkan presisi keseluruhan di naskah uji '
            '(33 naskah: 18 TypeSafe + 15 OpenRouter). Goyang naik sedikit '
            'di KEDUA kelompok (TypeSafe 1411->1414, OpenRouter 1249->1283, '
            'gabungan 2660->2697, +1,4%); panggilan turun tipis (526->511, '
            '-2,9%); label subbab/paragraf bergerak dua arah dalam rentang '
            'noise. Yang terbukti naik hanya kebersihan artefak: 0 pemisah '
            'dilabel bab dan 0 BOM di 33/33 naskah, judul bab ganda akibat '
            'BOM runtuh (C4/D3/M3/S2 18-20 -> 5), sampah bab 64->50 (-22%). '
            'Catatan: selisih kelompok OR bisa berasal dari model fallback '
            '(bobot belum terbukti identik), bukan dari v11 — tapi kelompok '
            'TypeSafe sendiri juga tidak menunjukkan perbaikan goyang, jadi '
            'vonis tidak bergantung pada kelompok OR.'),
        'naik': ['pembersihan pemisah/BOM (33/33, 0 baris pemisah dilabel bab, 0 BOM)',
                 'judul bab ganda akibat BOM runtuh ke 5 (C4/D3/M3/S2 kelompok OR; F4/J3/L3 TypeSafe)',
                 'sampah bab total 64->50 (-22%)',
                 'judul Romawi deterministik di gabung (Y2, kelompok TypeSafe)'],
        'tidak_naik': ['goyang dalam-run (gabungan 2660->2697, +1,4%; naik di kedua kelompok)',
                       'panggilan Jev (526->511, -2,9%)',
                       'label subbab/paragraf (bergerak dua arah, noise; beda per baris grup3 didominasi geser indeks stitch + tukar paragraf/biasa)',
                       'label bab Romawi tanpa kata BAB masih goyang (AA3: 1 dari 4 judul berganti v10->v11)',
                       'sampah bab masih 50 di 33 naskah (AN-1 3, G3 4, AA3 2, W3 1, N3 1)',
                       'Lapis 2 pendapat_kedua: 0 kali jalan live (33/33)',
                       'antrean manusia: 0 kali terpicu live (33/33)'],
        'belum_terverifikasi': ['E3 (anggaran habis)', 'AJ-1 (anggaran habis)',
                                'AD3 duplikat Y2 (sengaja tidak dihitung ganda)'],
        'catatan': ('Skor teks lawan label manusia TIDAK MUNGKIN dihitung '
                    '(0 label uji). Vonis memakai agregat + cek deterministik, '
                    'bukan skor presisi manusia.'),
    }
    json.dump(hasil, open(out_path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('ditulis:', out_path)
    print('terverifikasi:', hasil['naskah_terverifikasi'], '(TS 18 + OR 15)',
          '| belum:', hasil['naskah_belum_dicoba'])
    print('OR agregat panggilan v10->v11:', agr_or['panggilan_v10'], '->',
          agr_or['panggilan_v11'])
    print('OR agregat goyang v10->v11:', agr_or['goyang_v10'], '->',
          agr_or['goyang_v11'])
    print('OR sampah bab v10->v11:', s10or, '->', s11or)
    print('gabungan goyang:', agr_gabung['goyang_v10'], '->',
          agr_gabung['goyang_v11'], '| sampah:',
          agr_gabung['sampah_bab_v10'], '->', agr_gabung['sampah_bab_v11'])
    print('total panggilan sesi OR:', total_or, '| biaya ~Rp',
          total_or * HARGA_PER_PANGGILAN_RP)


if __name__ == '__main__':
    main()
