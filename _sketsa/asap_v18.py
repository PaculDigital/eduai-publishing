#!/usr/bin/env python3
"""Uji asap v18 (R20-R27) di peta PENUH fid=81 (offline, 0 Jev, 0 LLM).

Tiga lintasan (semuanya lewat KODE PRODUKSI v18,
`peta3_jev._v16_terapkan`):
  (A) peta tersimpan apa adanya (486 baris, konteks Hakim-status nyata).
      Kriteria LULUS: 0 baris mudah rusak DAN bersih ground truth >= 0
      (GT 27 baris dari ground_truth/ground_truth_81.tsv).
      Dilaporkan juga SEMUA baris yang dikena aturan v18 (R20-R27)
      beserta teksnya, supaya tiap tembakan bisa diperiksa akalnya.
  (B) REGRESI v17: simulasi jawaban agen kedua: label awal baris
      159/161/163 diubah jadi 'biasa' — persis jawaban agen kedua di
      LOG DEPLOY v16 (conf 0,9; `hasil_asap_v16_deploy.json`). R18
      harus memulihkan ketiganya ke 'paragraf' (GT 159/163).
      Kriteria LULUS: ketiganya kembali 'paragraf' DAN 0 baris mudah
      rusak di lintasan ini.
  (C) SIMULASI PENGAMAN v18: untuk tiap pengaman R24/R25/R26, cari
      baris fid=81 yang polanya cocok DAN label tersimpannya benar
      (sesuai GT bila ada, atau label peta bila tidak ada GT).
      Balik labelnya seperti kesalahan agen di 279 (R24: paragraf ->
      subbab; R25: biasa -> paragraf; R26: paragraf -> biasa), lalu
      penerapan ulang harus memulihkannya. Bila tidak ada baris
      fid=81 yang cocok polanya, dilaporkan apa adanya — pengaman
      itu terbukti hanya di 279, bukan di asap.

Vonis akhir LULUS hanya bila (A) DAN (B) DAN (C) lulus.

Keluaran: `_verifikasi_v11/hasil_asap_v18.json`.
Bila GAGAL, laporkan apa yang gagal dan BERHENTI, jangan dipaksa lolos.

Batas simulasi (sama seperti asap v17): TIDAK memakai pagar `demosi_v6`
(peta tersimpan tidak mencatat baris v6-demoted); baris yang dipromosi
ke 'subbab' dilaporkan dengan teksnya + apakah punya penanda BAB.

Pemakaian:
    python3 _sketsa/asap_v18.py
"""
import csv
import importlib.util
import json
import os
import re
import sys
import types
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VER = ROOT / '_verifikasi_v11'
sys.path.insert(0, str(ROOT))

# Jev di-mock: modul berat di-stub sebelum memuat peta3_jev.py root.
app = types.ModuleType('app')
app.__path__ = [str(ROOT / 'app')]
sys.modules['app'] = app
_ai = types.ModuleType('app.ai')
_ai.SessionLocal = object
_ai._teks_dari_berkas = lambda *a, **k: ''
_ai.UPLOAD_DIR = Path('/tmp')
sys.modules['app.ai'] = _ai
_models = types.ModuleType('app.models')
_models.FileBerkas = object
sys.modules['app.models'] = _models


class _SatpamDiam:
    def tanya_bebas_mutu(self, *a, **k):
        raise AssertionError('asap v18 tidak boleh memanggil Jev')


sys.modules['app.satpam'] = _SatpamDiam()
_state = types.ModuleType('app.state')
_state.buang_daftar_isi = lambda t: t
sys.modules['app.state'] = _state

_spec = importlib.util.spec_from_file_location(
    '_peta3_produksi_v18_asap', str(ROOT / 'peta3_jev.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

assert os.path.realpath(P.__file__) == os.path.realpath(
    str(ROOT / 'peta3_jev.py')), P.__file__
assert P.RULE_VERSION == 'jev-peta-v18', P.RULE_VERSION

ATURAN_V18 = ('R20_konektif_lanjutan', 'R21_repetisi_awal',
              'R22_untuk_tanpa_diatas', 'R23_temporal_tahun',
              'R24_butir_tanya_kalimat', 'R25_awalan_kapital_dua',
              'R26_dash_hyphen_kalimat', 'R27_penanda_halaman')


def muat_peta():
    peta = json.load(open(VER / 'peta81_tersimpan.json'))
    baris = peta['baris']
    label = peta['label']
    goyang = {int(i) for i, _ in peta['goyang']}
    hakim = {h['i']: h for h in peta['hakim_bagian']}
    sepakat = {i for i, h in hakim.items() if h['status'] == 'sepakat'}
    ragu = {i for i, h in hakim.items() if h['status'] == 'ragu'}
    return peta, baris, label, goyang, hakim, sepakat, ragu


def muat_gt():
    gt = {}
    with open(ROOT / 'ground_truth' / 'ground_truth_81.tsv',
              encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            gt[int(r['baris_no'])] = r['label_benar']
    assert len(gt) == 27, len(gt)
    return gt


def bab_dari_idx(idx, batas_bab):
    bab = 'BAB-?'
    for b_idx, nama in batas_bab:
        if idx >= b_idx:
            bab = nama
    return bab


def main():
    peta, baris, label, goyang, hakim, sepakat, ragu = muat_peta()
    gt = muat_gt()
    batas_bab = [(i, t.strip().replace(' ', '-'))
                 for i, t in enumerate(baris)
                 if re.match(r'(?i)^BAB\s+[IVXLC]+\s*$', (t or '').strip())]
    idxs = sorted(int(k) for k in label)
    assert len(idxs) == 486, len(idxs)
    assert set(gt) <= set(idxs)

    rows = [{'naskah': '81', 'no': str(i), 'teks_baris': baris[i],
             'label_v15': label[str(i)]} for i in idxs]
    label_awal = {('81', str(i)): label[str(i)] for i in idxs}
    konteks = {('81', str(i)): {
        'hakim_status': hakim[i]['status'] if i in hakim else None,
        'baris_mentah': baris, 'idx_mentah': i} for i in idxs}

    # ── LINTASAN A: peta tersimpan apa adanya ─────────────────────────
    label_akhir, jejak = P._v16_terapkan(rows, label_awal, konteks)

    def lab(i, d):
        return d[('81', str(i))]

    berubah = [i for i in idxs if lab(i, label_akhir) != lab(i, label_awal)]
    transisi = Counter(f"{lab(i, label_awal)}->{lab(i, label_akhir)}"
                       for i in berubah)
    per_bab_berubah = Counter(bab_dari_idx(i, batas_bab) for i in berubah)
    berubah_goyang = [i for i in berubah if i in goyang]
    berubah_tidak_goyang = [i for i in berubah if i not in goyang]
    berubah_mudah = [i for i in berubah
                     if i not in goyang and i in sepakat]
    berubah_melawan_hakim = [i for i in berubah if i in sepakat]
    berubah_ragu = [i for i in berubah if i in ragu]
    berubah_tidak_diaudit = [i for i in berubah if i not in hakim]
    berubah_sejalan_hakim = [i for i in berubah
                             if i in hakim and hakim[i]['label']
                             == lab(i, label_akhir)]

    def rincian_baris(idxs_):
        return [{'no': str(i), 'bab': bab_dari_idx(i, batas_bab),
                 'teks': (baris[i] or '')[:200],
                 'label_sebelum': lab(i, label_awal),
                 'label_sesudah': lab(i, label_akhir),
                 'aturan': jejak[('81', str(i))],
                 'goyang': i in goyang,
                 'hakim_status': hakim[i]['status'] if i in hakim else None,
                 'hakim_label': hakim[i]['label'] if i in hakim else None,
                 'label_benar_gt81': gt.get(i),
                 'punya_penanda_bab': bool(
                     P._POLA_BAB_NOMOR.match((baris[i] or '').strip())),
                 }
                for i in idxs_]

    gt_diubah = [i for i in gt if lab(i, label_akhir) != lab(i, label_awal)]
    gt_menuju = [i for i in gt_diubah
                 if lab(i, label_awal) != gt[i]
                 and lab(i, label_akhir) == gt[i]]
    gt_menjauh = [i for i in gt_diubah
                  if lab(i, label_awal) == gt[i]
                  and lab(i, label_akhir) != gt[i]]
    gt_salah_ke_salah = [i for i in gt_diubah
                         if lab(i, label_awal) != gt[i]
                         and lab(i, label_akhir) != gt[i]]

    naik_subbab = [i for i in berubah if lab(i, label_akhir) == 'subbab']
    naik_subbab_berpenanda = [i for i in naik_subbab
                              if P._POLA_BAB_NOMOR.match(
                                  (baris[i] or '').strip())]
    naik_subbab_tanpa_penanda = [i for i in naik_subbab
                                 if i not in naik_subbab_berpenanda]

    bersih_gt = len(gt_menuju) - len(gt_menjauh)

    # Tembakan aturan v18 di lintasan A (untuk diperiksa akalnya).
    kena_v18 = [i for i in idxs if jejak[('81', str(i))] in ATURAN_V18]
    rincian_v18 = [{'no': str(i), 'bab': bab_dari_idx(i, batas_bab),
                    'teks': (baris[i] or '')[:200],
                    'label_sebelum': lab(i, label_awal),
                    'label_sesudah': lab(i, label_akhir),
                    'aturan': jejak[('81', str(i))],
                    'goyang': i in goyang,
                    'hakim_status': hakim[i]['status']
                    if i in hakim else None,
                    'label_benar_gt81': gt.get(i),
                    'punya_penanda_bab': bool(
                        P._POLA_BAB_NOMOR.match((baris[i] or '').strip())),
                    }
                   for i in kena_v18]

    # ── LINTASAN B: regresi v17 (159/161/163 -> 'biasa') ──────────────
    dep = json.load(open(VER / 'hasil_asap_v16_deploy.json'))
    _log_b = {e['idx']: e['label_kedua'] for e in dep['log_agen_kedua']}
    assert _log_b[159] == 'biasa' and _log_b[161] == 'biasa' \
        and _log_b[163] == 'biasa', _log_b
    label_awal_b = dict(label_awal)
    for _i in (159, 161, 163):
        label_awal_b[('81', str(_i))] = 'biasa'
    label_akhir_b, jejak_b = P._v16_terapkan(rows, label_awal_b, konteks)

    def lab_b(i):
        return label_akhir_b[('81', str(i))]

    berubah_b = [i for i in idxs
                 if lab_b(i) != label_awal_b[('81', str(i))]]
    berubah_mudah_b = [i for i in berubah_b
                       if i not in goyang and i in sepakat]
    gt_diubah_b = [i for i in gt
                   if lab_b(i) != label_awal_b[('81', str(i))]]
    gt_menuju_b = [i for i in gt_diubah_b
                   if label_awal_b[('81', str(i))] != gt[i]
                   and lab_b(i) == gt[i]]
    gt_menjauh_b = [i for i in gt_diubah_b
                    if label_awal_b[('81', str(i))] == gt[i]
                    and lab_b(i) != gt[i]]
    bersih_gt_b = len(gt_menuju_b) - len(gt_menjauh_b)
    pulih_b = {str(i): lab_b(i) for i in (159, 161, 163)}
    aturan_b = {str(i): jejak_b[('81', str(i))] for i in (159, 161, 163)}
    b_lulus = (all(v == 'paragraf' for v in pulih_b.values())
               and len(berubah_mudah_b) == 0)

    # ── LINTASAN C: simulasi pengaman v18 ─────────────────────────────
    #    R24: pola cocok pada label 'paragraf' -> balik ke 'subbab'
    #    (kesalahan agen di T3:73), pengaman harus kembalikan 'biasa'.
    #    R25: pola cocok pada label 'biasa' -> balik ke 'paragraf'
    #    (kesalahan agen di AL-2:92), pengaman harus kembalikan 'biasa'.
    #    R26: pola cocok pada label 'paragraf' -> balik ke 'biasa'
    #    (kesalahan agen di AP-3:268), pengaman harus kembalikan
    #    'paragraf'.
    #    Pola dicek langsung lewat fungsi pengaman pada label yang
    #    benar (bukan lewat jejak — jejak hanya mencatat yang kena
    #    pada label awal peta).
    row_by_i = {int(r['no']): r for r in rows}
    ctx_by_i = {int(k[1]): v for k, v in konteks.items()}
    sim_c = []
    for nama, fn, lab_benar, lab_balik, lab_pulih in (
            ('R24_butir_tanya_kalimat', P._v16_r24_butir_tanya_kalimat,
             'paragraf', 'subbab', 'biasa'),
            ('R25_awalan_kapital_dua', P._v16_r25_awalan_kapital_dua,
             'biasa', 'paragraf', 'biasa'),
            ('R26_dash_hyphen_kalimat', P._v16_r26_dash_hyphen_kalimat,
             'paragraf', 'biasa', 'paragraf')):
        cocok = []
        for i in idxs:
            # label benar = GT bila ada, kalau tidak label peta.
            benar_i = gt.get(i, label[str(i)])
            if benar_i != lab_benar:
                continue
            if fn(row_by_i[i], lab_benar, ctx_by_i[i]) is None:
                continue
            cocok.append(i)
        sim_c.append({'pengaman': nama,
                      'label_benar': lab_benar,
                      'label_balik_agen': lab_balik,
                      'label_pulih_harapan': lab_pulih,
                      'baris_cocok_pola': [str(i) for i in cocok]})
    # Jalankan simulasi gabungan: semua baris cocok dibalik sekaligus.
    label_awal_c = dict(label_awal)
    for s in sim_c:
        for _i in s['baris_cocok_pola']:
            label_awal_c[('81', _i)] = s['label_balik_agen']
    label_akhir_c, jejak_c = P._v16_terapkan(rows, label_awal_c, konteks)

    def lab_c(i):
        return label_akhir_c[('81', str(i))]

    for s in sim_c:
        s['label_sesudah_simulasi'] = {
            i: lab_c(int(i)) for i in s['baris_cocok_pola']}
        s['pulih'] = all(
            lab_c(int(i)) == s['label_pulih_harapan']
            for i in s['baris_cocok_pola']) if s['baris_cocok_pola'] else None
    berubah_c = [i for i in idxs
                 if lab_c(i) != label_awal_c[('81', str(i))]]
    berubah_mudah_c = [i for i in berubah_c
                       if i not in goyang and i in sepakat]
    c_lulus = (all(s['pulih'] for s in sim_c if s['pulih'] is not None)
               and len(berubah_mudah_c) == 0)

    a_lulus = len(berubah_mudah) == 0 and bersih_gt >= 0
    if a_lulus and b_lulus and c_lulus:
        vonis = 'LULUS'
        alasan = (f"Lintasan A: 0 baris mudah rusak, bersih GT "
                  f"{bersih_gt}, {len(kena_v18)} tembakan v18. "
                  f"Lintasan B (regresi R18): 159/161/163 pulih ke "
                  f"paragraf lewat {aturan_b}, 0 baris mudah rusak. "
                  f"Lintasan C (pengaman): "
                  + '; '.join(
                      f"{s['pengaman']} {len(s['baris_cocok_pola'])} baris "
                      f"pulih={s['pulih']}" for s in sim_c))
    else:
        vonis = 'GAGAL'
        alasan = (f"Lintasan A lulus={a_lulus} (mudah rusak "
                  f"{len(berubah_mudah)}, bersih GT {bersih_gt}); "
                  f"lintasan B lulus={b_lulus} (pulih {pulih_b}, "
                  f"mudah rusak {len(berubah_mudah_b)}, bersih GT "
                  f"{bersih_gt_b}); lintasan C lulus={c_lulus} "
                  f"({[(s['pengaman'], s['baris_cocok_pola'], s['pulih']) for s in sim_c]}, "
                  f"mudah rusak {len(berubah_mudah_c)}).")

    hasil = {
        'uji': 'uji asap v18 (R20-R27) di peta PENUH fid=81',
        'fid': 81, 'tanggal': '2026-11-14',
        'resep': ('peta3_jev._v16_terapkan() lewat kode produksi v18 '
                  '(RULE_VERSION jev-peta-v18, aturan R1-R27) pada 486 '
                  'baris peta tersimpan, konteks Hakim-status nyata per '
                  'baris; lintasan B mengubah label awal 159/161/163 '
                  'jadi biasa (jawaban agen kedua log deploy v16); '
                  'lintasan C membalik label baris berpola pengaman '
                  'seperti kesalahan agen di 279'),
        'sumber_peta': {
            'peta_tersimpan': 'peta81_tersimpan.json (ProfilDokumen '
                              'file_id=81, dibaca BACA-SAJA)',
            'baris_peta_surveyor': len(baris),
            'jumlah_baris_kandidat': len(idxs),
            'label_sebelum': dict(Counter(label[str(i)] for i in idxs)),
            'baris_goyang': len(goyang),
            'hakim': {'sepakat': len(sepakat), 'ragu': len(ragu),
                      'curiga': 0, 'belum': 0,
                      'baris_ragu': [str(i) for i in sorted(ragu)]},
            'ground_truth': 'ground_truth/ground_truth_81.tsv (27 baris)',
            'batas_bab': [f"{n}@{i}" for i, n in batas_bab],
        },
        'panggilan': {'panggilan_jev': 0, 'panggilan_llm': 0,
                      'bukti_0_jev_0_llm': [
                          'driver hanya membaca berkas JSON/TSV lokal dan '
                          'memanggil peta3_jev._v16_terapkan() (regex + '
                          'hitung panjang)',
                          'tidak ada impor app.jev / app.agen_kedua, tidak '
                          'ada panggilan HTTP, tidak ada baca DB produksi, '
                          'tidak ada baca naskah dari DB',
                      ]},
        'hasil': {
            'baris_BERUBAH': len(berubah),
            'persen_baris_berubah': round(100 * len(berubah) / len(idxs), 2),
            'transisi': dict(transisi),
            'per_bab_berubah': dict(per_bab_berubah),
            'label_sesudah': dict(Counter(lab(i, label_akhir)
                                          for i in idxs)),
            'rincian_baris_berubah': rincian_baris(berubah),
        },
        'tembakan_v18_lintasan_a': {
            'jumlah': len(kena_v18),
            'per_aturan': dict(Counter(
                jejak[('81', str(i))] for i in kena_v18)),
            'rincian': rincian_v18,
            'catatan': ('Tiap tembakan v18 di peta penuh fid=81 harus '
                        'diperiksa akalnya dari teksnya di atas.'),
        },
        'rincian_vs_hakim_dan_goyang': {
            'berubah_dan_goyang_baris_sengketa': len(berubah_goyang),
            'berubah_dan_TIDAK_goyang_baris_mudah': len(berubah_tidak_goyang),
            'berubah_dan_mudah_rusak_bukan_goyang_dan_hakim_sepakat':
                len(berubah_mudah),
            'berubah_dan_hakim_SEPAKAT_melawan_hakim':
                len(berubah_melawan_hakim),
            'berubah_dan_hakim_RAGU': len(berubah_ragu),
            'berubah_dan_TIDAK_diaudit_hakim': len(berubah_tidak_diaudit),
            'berubah_dan_SEJALAN_dengan_hakim': len(berubah_sejalan_hakim),
            'hakim_sepakat_tidak_diubah':
                len(sepakat) - len(berubah_melawan_hakim),
            'catatan': ('MUDAH = bukan goyang DAN Hakim sepakat. Baris '
                        'mudah yang berubah = kerusakan: labelnya sudah '
                        'settled dan disepakati Hakim.'),
        },
        'ground_truth': {
            'gt_diubah': [str(i) for i in gt_diubah],
            'gt_menuju_benar': [str(i) for i in gt_menuju],
            'gt_menjauh_dari_benar': [str(i) for i in gt_menjauh],
            'gt_salah_ke_salah': [str(i) for i in gt_salah_ke_salah],
            'bersih': bersih_gt,
        },
        'pagar_demosi_v6': {
            'catatan': ('Asap ini TIDAK memakai pagar demosi_v6 (peta '
                        'tersimpan tidak mencatat baris mana yang v6 '
                        'demosi). Baris yang dipromosi ke subbab diperiksa '
                        'satu per satu: bila teksnya punya penanda BAB, '
                        'baris itu PASTI bukan demosi v6.'),
            'naik_ke_subbab': [str(i) for i in naik_subbab],
            'naik_ke_subbab_berpenanda_bab': [str(i) for i in
                                              naik_subbab_berpenanda],
            'naik_ke_subbab_tanpa_penanda_caveat': [str(i) for i in
                                                    naik_subbab_tanpa_penanda],
        },
        'lintasan_b_regresi_r18': {
            'catatan': ('Label awal 159/161/163 diubah jadi biasa '
                        '(jawaban agen kedua log deploy v16, conf 0,9); '
                        'R18 harus memulihkannya ke paragraf.'),
            'label_awal_diubah': {str(i): 'biasa' for i in (159, 161, 163)},
            'label_sesudah': pulih_b,
            'aturan': aturan_b,
            'pulih_semua_ke_paragraf': all(
                v == 'paragraf' for v in pulih_b.values()),
            'baris_BERUBAH': len(berubah_b),
            'transisi': dict(Counter(
                f"{label_awal_b[('81', str(i))]}->{lab_b(i)}"
                for i in berubah_b)),
            'mudah_rusak': len(berubah_mudah_b),
            'gt_diubah': [str(i) for i in gt_diubah_b],
            'gt_menuju_benar': [str(i) for i in gt_menuju_b],
            'gt_menjauh_dari_benar': [str(i) for i in gt_menjauh_b],
            'bersih': bersih_gt_b,
        },
        'lintasan_c_simulasi_pengaman': {
            'catatan': ('Baris fid=81 yang polanya cocok dengan pengaman '
                        'dibalik seperti kesalahan agen di 279, lalu '
                        'penerapan ulang harus memulihkannya. Bila suatu '
                        'pengaman tidak punya baris cocok di fid=81, '
                        'pulih=None dan pengaman itu terbukti hanya di '
                        '279.'),
            'simulasi': sim_c,
            'baris_BERUBAH': len(berubah_c),
            'mudah_rusak': len(berubah_mudah_c),
        },
        'vonis': vonis,
        'alasan_vonis': alasan,
    }
    out = VER / 'hasil_asap_v18.json'
    json.dump(hasil, open(out, 'w'), ensure_ascii=False, indent=1)
    print(f"baris berubah: {len(berubah)}/486 "
          f"({hasil['hasil']['persen_baris_berubah']}%)")
    print(f"transisi: {dict(transisi)}")
    print(f"mudah rusak: {len(berubah_mudah)}; GT bersih: {bersih_gt} "
          f"(menuju {len(gt_menuju)}, menjauh {len(gt_menjauh)})")
    print(f"tembakan v18: {len(kena_v18)} "
          f"{dict(Counter(jejak[('81', str(i))] for i in kena_v18))}")
    print(f"naik ke subbab: {[str(i) for i in naik_subbab]}; "
          f"berpenanda: {[str(i) for i in naik_subbab_berpenanda]}; "
          f"tanpa penanda (caveat): "
          f"{[str(i) for i in naik_subbab_tanpa_penanda]}")
    for r in hasil['hasil']['rincian_baris_berubah']:
        print(f"  baris {r['no']} ({r['bab']}): "
              f"{r['label_sebelum']}->{r['label_sesudah']} "
              f"[{r['aturan']}] goyang={r['goyang']} "
              f"hakim={r['hakim_status']} gt={r['label_benar_gt81']} "
              f"teks={r['teks'][:80]!r}")
    print('VONIS:', vonis)
    print('lintasan B: pulih', pulih_b, 'aturan', aturan_b,
          f'mudah rusak {len(berubah_mudah_b)}, GT bersih {bersih_gt_b}')
    print('lintasan C:', [(s['pengaman'], s['baris_cocok_pola'],
                           s['pulih']) for s in sim_c],
          f'mudah rusak {len(berubah_mudah_c)}')
    print('tertulis:', out)
    return hasil


if __name__ == '__main__':
    main()
