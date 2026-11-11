"""Gabung hasil gelombang OR5 (E3 + AJ-1, 2 naskah terakhir tahap 5) ke
hasil_verifikasi_v11.json.

Mengikuti pola buat_hasil_verifikasi_v11_or.py, tapi HANYA menambah:
- per_kode_openrouter: 15 -> 17 (AJ-1, E3 ditambah, diurutkan per kode)
- agregat_openrouter_17_naskah (baru; agregat_openrouter_15_naskah
  dipertahankan apa adanya sebagai potret kelompok OR sebelum OR5)
- agregat_gabungan_35_naskah (baru; agregat_gabungan_33_naskah
  dipertahankan apa adanya)
- hitungan terverifikasi: OR 15 -> 17, total 33 -> 35, belum_dicoba []
- anggaran + biaya kelompok OR (gelombang OR5 ditambah)
- klaim_v11_openrouter diperbarui hanya bila E3/AJ-1 mengubah vonis
  klaim (dihitung dari data, dicek manual sebelum tulis)
- vonis_gabungan_35_naskah (baru; vonis_gabungan_33_naskah dipertahankan)

TIDAK BOLEH mengubah: per_kode (18 TypeSafe), agregat_18_naskah,
klaim_v11, vonis awal, dan 15 entri per_kode_openrouter yang sudah ada.
Tanpa Jev, tanpa label baru.
"""
import json
import sys
from pathlib import Path

ROOT = Path('/home/hatch/workspace/jev-v5')
sys.path.insert(0, str(ROOT))
from _verifikasi_v11.banding_v10_v11 import (  # noqa: E402
    muat_v10, klasifikasi_bab)
from _verifikasi_v11.buat_hasil_verifikasi_v11_or import (  # noqa: E402
    bangun_per_kode, agregat, HARGA_PER_PANGGILAN_RP)

OR5_PATH = ROOT / '_verifikasi_v11' / 'hasil_verifikasi_v11_OR5.json'


def muat_v11_or5():
    d = json.load(open(OR5_PATH, encoding='utf-8'))
    berhasil = {}
    for e in d['entri']:
        if e.get('status') == 'berhasil':
            berhasil[e['kode']] = e
    return d, berhasil


def main():
    v10 = muat_v10()
    d5, v11or5 = muat_v11_or5()
    assert set(v11or5) == {'E3', 'AJ-1'}, \
        'OR5 harus E3 + AJ-1, dapat %s' % sorted(v11or5)
    assert all((e.get('model_melayani') ==
                'typesafe/jev-1.14-20261014') for e in v11or5.values()), \
        'ada run OR5 yang tidak dilayani typesafe/jev-1.14-20261014!'
    assert all(e.get('sidik_berubah') is False for e in v11or5.values()), \
        'ada run OR5 yang mengubah DB!'
    assert not any(e.get('model_override') for e in v11or5.values()), \
        'ada run OR5 dengan model_override'

    per_baru, s10_baru, s11_baru = bangun_per_kode(v10, v11or5)
    assert len(per_baru) == 2

    out_path = ROOT / 'hasil_verifikasi_v11.json'
    hasil = json.load(open(out_path, encoding='utf-8'))
    # ── JANGAN sentuh angka 33 sebelumnya ──
    assert len(hasil['per_kode']) == 18, 'per_kode TypeSafe berubah!'
    assert hasil['agregat_18_naskah']['goyang_v10'] == 1411
    assert len(hasil['per_kode_openrouter']) == 15, \
        'per_kode_openrouter berubah sebelum OR5!'
    assert hasil['agregat_openrouter_15_naskah']['goyang_v10'] == 1249
    assert hasil['agregat_gabungan_33_naskah']['goyang_v10'] == 2660
    assert hasil['naskah_terverifikasi'] == 33
    assert hasil['naskah_belum_dicoba'] == ['AJ-1', 'E3']

    per_or17 = sorted(hasil['per_kode_openrouter'] + per_baru,
                      key=lambda p: p['kode'])
    assert [p['kode'] for p in per_or17] == sorted(
        p['kode'] for p in per_or17)
    agr_or17 = agregat(per_or17,
                       hasil['agregat_openrouter_15_naskah']['sampah_bab_v10'] + s10_baru,
                       hasil['agregat_openrouter_15_naskah']['sampah_bab_v11'] + s11_baru)
    agr_ts = hasil['agregat_18_naskah']
    agr_gabung35 = {
        'panggilan_v10': agr_ts['panggilan_v10'] + agr_or17['panggilan_v10'],
        'panggilan_v11': agr_ts['panggilan_v11'] + agr_or17['panggilan_v11'],
        'goyang_v10': agr_ts['goyang_v10'] + agr_or17['goyang_v10'],
        'goyang_v11': agr_ts['goyang_v11'] + agr_or17['goyang_v11'],
        'sampah_bab_v10': agr_ts['sampah_bab_v10'] + agr_or17['sampah_bab_v10'],
        'sampah_bab_v11': agr_ts['sampah_bab_v11'] + agr_or17['sampah_bab_v11'],
        'hakim_sepakat': agr_ts['hakim_sepakat'] + agr_or17['hakim_sepakat'],
        'hakim_ragu': agr_ts['hakim_ragu'] + agr_or17['hakim_ragu'],
        'hakim_curiga': agr_ts['hakim_curiga'] + agr_or17['hakim_curiga'],
        'pendapat_kedua_total': (agr_ts['pendapat_kedua_total'] +
                                 agr_or17['pendapat_kedua_total']),
        'antrean_jml': agr_ts['antrean_jml'] + agr_or17['antrean_jml'],
        'peringatan_campuran': (
            'Agregat gabungan MENCAMPUR dua ID model: 18 naskah dilayani '
            'jev-1.14.0 resmi (TypeSafe) + 17 naskah dilayani '
            'openrouter/typesafe/jev-1.14-20261014. Bobot fallback belum '
            'terbukti identik dengan jev-1.14.0 resmi, jadi selisih '
            'v10-vs-v11 kelompok OR bisa berasal dari model, bukan dari '
            'lapisan v11. Pakai agregat per kelompok untuk vonis; agregat '
            'gabungan hanya ringkasan.'),
    }

    total_or5 = d5['panggilan_total']
    total_or_baru = hasil['anggaran_panggilan_kelompok_openrouter']['total'] + total_or5

    hasil['naskah_terverifikasi_openrouter'] = 17
    hasil['naskah_terverifikasi'] = 35
    hasil['naskah_belum_dicoba'] = []
    hasil['naskah_belum_terverifikasi_alasan'] = {
        'E3': 'terverifikasi di gelombang OR5',
        'AJ-1': 'terverifikasi di gelombang OR5',
        'butuh_tambahan': ('tidak ada lagi: 35 dari 36 naskah uji '
                           'terverifikasi; 1 sisanya AD3 duplikat berkas Y2, '
                           'sengaja tidak dihitung ganda.'),
    }
    hasil['per_kode_openrouter'] = per_or17
    hasil['agregat_openrouter_17_naskah'] = agr_or17
    hasil['agregat_gabungan_35_naskah'] = agr_gabung35
    hasil['anggaran_panggilan_kelompok_openrouter']['gelombang_OR5_E3_AJ-1'] = total_or5
    hasil['anggaran_panggilan_kelompok_openrouter']['total'] = total_or_baru
    hasil['anggaran_panggilan_kelompok_openrouter']['keterangan'] = (
        'Batas ~250 untuk kelompok OR1-OR4 (total 252 incl. 2 probe awal) '
        'ditambah gelombang OR5 (E3 + AJ-1, %d panggilan, Gas Boss 11 Nov '
        '2026) sehingga total kelompok OR %d panggilan.'
        % (total_or5, total_or_baru))
    hasil['anggaran_panggilan']['total_tahap5_semua_kelompok'] = (
        hasil['anggaran_panggilan']['total'] + total_or_baru)
    hasil['biaya_perkiraan_rp_kelompok_openrouter'] = {
        'metode': ('jangkar ukur_biaya_3_naskah + tahap 1: ~Rp10 per '
                   'panggilan, batas atas chars/4, $0,042/1 jt token, '
                   'kurs Rp18.100/USD, output gratis, Jev tidak '
                   'mengembalikan pemakaian token'),
        'total_panggilan': total_or_baru,
        'perkiraan_rp': total_or_baru * HARGA_PER_PANGGILAN_RP,
        'rentang_rp': [int(total_or_baru * HARGA_PER_PANGGILAN_RP * 0.72),
                       total_or_baru * HARGA_PER_PANGGILAN_RP],
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
        'Gelombang OR5 (E3 + AJ-1) menutup tahap 5: 35 dari 36 naskah uji '
        'terverifikasi; 1 sisanya AD3 duplikat berkas Y2.')

    json.dump(hasil, open(out_path, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('ditulis:', out_path)
    print('terverifikasi:', hasil['naskah_terverifikasi'], '(TS 18 + OR 17)')
    print('OR17 agregat panggilan v10->v11:', agr_or17['panggilan_v10'], '->',
          agr_or17['panggilan_v11'])
    print('OR17 agregat goyang v10->v11:', agr_or17['goyang_v10'], '->',
          agr_or17['goyang_v11'])
    print('OR17 sampah bab v10->v11:', agr_or17['sampah_bab_v10'], '->',
          agr_or17['sampah_bab_v11'])
    print('gabungan35 goyang:', agr_gabung35['goyang_v10'], '->',
          agr_gabung35['goyang_v11'], '| sampah:',
          agr_gabung35['sampah_bab_v10'], '->', agr_gabung35['sampah_bab_v11'])
    print('total panggilan OR:', total_or_baru, '| biaya ~Rp',
          total_or_baru * HARGA_PER_PANGGILAN_RP)
    print('total panggilan tahap 5 semua kelompok:',
          hasil['anggaran_panggilan']['total_tahap5_semua_kelompok'])


if __name__ == '__main__':
    main()
