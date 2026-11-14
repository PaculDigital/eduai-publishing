#!/usr/bin/env python3
"""Uji asap v19 (R28 penanda bab Arab) di peta PENUH fid=81 (offline,
0 Jev, 0 LLM).

Tiga lintasan (semuanya lewat KODE PRODUKSI v19,
`peta3_jev._v16_terapkan`):
  (A) peta tersimpan apa adanya (486 baris, konteks Hakim-status nyata).
      Kriteria LULUS: 0 baris mudah rusak DAN bersih ground truth >= 0
      (GT 27 baris dari ground_truth/ground_truth_81.tsv).
      Dilaporkan juga SEMUA baris yang dikena R28 beserta teksnya.
      Harapan: R28 menembak 0x — fid=81 berpenanda Romawi semua.
  (B) REGRESI v17: simulasi jawaban agen kedua: label awal baris
      159/161/163 diubah jadi 'biasa' — persis jawaban agen kedua di
      LOG DEPLOY v16 (conf 0,9; `hasil_asap_v16_deploy.json`). R18
      harus memulihkan ketiganya ke 'paragraf' (GT 159/163).
      Kriteria LULUS: ketiganya kembali 'paragraf' DAN 0 baris mudah
      rusak di lintasan ini.
  (C) SIMULASI R28 v19: 5 judul bab fid=81 duduk sesudah penanda
      Romawi — tapi judul-judul itu BUKAN baris kandidat (labelnya
      sudah settled, tidak ada di 486 baris), jadi R28 tidak bisa
      diuji lewat peta tersimpan apa adanya. Simulasi: untuk tiap
      pasangan (penanda Romawi, judul baku) — BAB I/PENDAHULUAN,
      BAB II/TINJAUAN PUSTAKA, BAB IV/HASIL DAN PEMBAHASAN —
      penanda di konteks ditukar jadi 'Bab 1'/'Bab 2'/'Bab 4' dan
      label judul dibalik jadi 'biasa' (seperti label rantai
      AJ-1:277 yang salah); R28 harus memulihkannya ke 'bab'.
      Negatif: penanda ditukar jadi 'Bab 13' -> judul tetap 'biasa'.
      'METODE PENELITIAN' dan 'PENUTUP' TIDAK ikut simulasi: keduanya
      bukan judul baku di `_V16_JUDUL_BAB_BAKU` (keterbatasan kosakata
      R10/R28 yang sudah ada, bukan bagian v19 ini).

Vonis akhir LULUS hanya bila (A) DAN (B) DAN (C) lulus.

Keluaran: `_verifikasi_v11/hasil_asap_v19.json`.
Bila GAGAL, laporkan apa yang gagal dan BERHENTI, jangan dipaksa lolos.

Batas simulasi (sama seperti asap v18): TIDAK memakai pagar `demosi_v6`
(peta tersimpan tidak mencatat baris v6-demoted); baris yang dipromosi
ke 'subbab' dilaporkan dengan teksnya + apakah punya penanda BAB.

Pemakaian:
    python3 _sketsa/asap_v19.py
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
        raise AssertionError('asap v19 tidak boleh memanggil Jev')


sys.modules['app.satpam'] = _SatpamDiam()
_state = types.ModuleType('app.state')
_state.buang_daftar_isi = lambda t: t
sys.modules['app.state'] = _state

_spec = importlib.util.spec_from_file_location(
    '_peta3_produksi_v19_asap', str(ROOT / 'peta3_jev.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

assert os.path.realpath(P.__file__) == os.path.realpath(
    str(ROOT / 'peta3_jev.py')), P.__file__
assert P.RULE_VERSION == 'jev-peta-v19', P.RULE_VERSION

ATURAN_V19 = ('R28_penanda_bab_arab',)


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

    # Tembakan R28 di lintasan A (untuk diperiksa akalnya).
    kena_v19 = [i for i in idxs if jejak[('81', str(i))] in ATURAN_V19]
    rincian_v19 = [{'no': str(i), 'bab': bab_dari_idx(i, batas_bab),
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
                   for i in kena_v19]

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

    # ── LINTASAN C: simulasi R28 v19 (tukar penanda) ───────────────────
    #    Judul bab fid=81 BUKAN baris kandidat (tidak ada di 486 baris),
    #    jadi simulasi memakai baris judul itu langsung (di luar peta):
    #    label dibalik jadi 'biasa' (seperti label rantai AJ-1:277 yang
    #    salah) + penanda Romawi di konteks ditukar jadi 'Bab N' Arab.
    #    R28 harus memulihkan judul ke 'bab'. Negatif: 'Bab 13'.
    _romawi_ke_arab = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5}
    sim_c = []
    for _m_idx, _m_nama in batas_bab:
        _m = re.match(r'(?i)^BAB\s+([IVXLC]+)\s*$',
                      (baris[_m_idx] or '').strip())
        if not _m:
            continue
        _n = _romawi_ke_arab.get(_m.group(1).upper())
        if _n is None:
            continue
        # Judul = baris non-kosong pertama sesudah penanda (zona R10/R28).
        _t_idx = next((j for j in range(_m_idx + 1,
                                        min(len(baris), _m_idx + 7))
                       if (baris[j] or '').strip()), None)
        if _t_idx is None:
            continue
        _t_teks = (baris[_t_idx] or '').strip()
        if _t_teks.lower() not in P._V16_JUDUL_BAB_BAKU:
            sim_c.append({'penanda_asli': (baris[_m_idx] or '').strip(),
                          'judul_idx': str(_t_idx), 'judul': _t_teks,
                          'dilewati': 'bukan judul baku'})
            continue
        # Positif: penanda -> 'Bab N' Arab, label judul -> 'biasa'.
        _swap = list(baris)
        _swap[_m_idx] = f'Bab {_n}'
        _row_c = {'naskah': '81', 'no': str(_t_idx),
                  'teks_baris': baris[_t_idx], 'label_v15': 'biasa'}
        _ctx_c = {('81', str(_t_idx)): {
            'hakim_status': None, 'baris_mentah': _swap,
            'idx_mentah': _t_idx}}
        _o_c, _j_c = P._v16_terapkan(
            [_row_c], {('81', str(_t_idx)): 'biasa'}, konteks=_ctx_c)
        # Negatif: penanda -> 'Bab 13' (di luar 1-12).
        _swap13 = list(baris)
        _swap13[_m_idx] = 'Bab 13'
        _ctx13 = {('81', str(_t_idx)): {
            'hakim_status': None, 'baris_mentah': _swap13,
            'idx_mentah': _t_idx}}
        _o13, _j13 = P._v16_terapkan(
            [_row_c], {('81', str(_t_idx)): 'biasa'}, konteks=_ctx13)
        sim_c.append({'penanda_asli': (baris[_m_idx] or '').strip(),
                      'penanda_arab': f'Bab {_n}',
                      'judul_idx': str(_t_idx), 'judul': _t_teks,
                      'label_sesudah_arab': _o_c[('81', str(_t_idx))],
                      'aturan_arab': _j_c[('81', str(_t_idx))],
                      'label_sesudah_bab13': _o13[('81', str(_t_idx))],
                      'aturan_bab13': _j13[('81', str(_t_idx))],
                      'pulih': _o_c[('81', str(_t_idx))] == 'bab'
                      and _j_c[('81', str(_t_idx))]
                      == 'R28_penanda_bab_arab'
                      and _o13[('81', str(_t_idx))] == 'biasa'})
    c_lulus = (len(kena_v19) == 0
               and all(s.get('pulih') for s in sim_c
                       if 'pulih' in s)
               and any('pulih' in s for s in sim_c))

    a_lulus = len(berubah_mudah) == 0 and bersih_gt >= 0
    if a_lulus and b_lulus and c_lulus:
        vonis = 'LULUS'
        alasan = (f"Lintasan A: 0 baris mudah rusak, bersih GT "
                  f"{bersih_gt}, {len(kena_v19)} tembakan R28. "
                  f"Lintasan B (regresi R18): 159/161/163 pulih ke "
                  f"paragraf lewat {aturan_b}, 0 baris mudah rusak. "
                  f"Lintasan C (R28 tukar penanda): "
                  + '; '.join(
                      f"{s.get('penanda_asli', '?')}->{s.get('penanda_arab', '?')} "
                      f"judul {s.get('judul_idx', '?')} pulih={s.get('pulih')}"
                      for s in sim_c if 'pulih' in s))
    else:
        vonis = 'GAGAL'
        alasan = (f"Lintasan A lulus={a_lulus} (mudah rusak "
                  f"{len(berubah_mudah)}, bersih GT {bersih_gt}); "
                  f"lintasan B lulus={b_lulus} (pulih {pulih_b}, "
                  f"mudah rusak {len(berubah_mudah_b)}, bersih GT "
                  f"{bersih_gt_b}); lintasan C lulus={c_lulus} "
                  f"({[(s.get('penanda_asli'), s.get('judul_idx'), s.get('pulih')) for s in sim_c]}, "
                  f"tembakan R28 peta asli {len(kena_v19)}).")

    hasil = {
        'uji': 'uji asap v19 (R28 penanda bab Arab) di peta PENUH fid=81',
        'fid': 81, 'tanggal': '2026-11-15',
        'resep': ('peta3_jev._v16_terapkan() lewat kode produksi v19 '
                  '(RULE_VERSION jev-peta-v19, aturan R1-R28) pada 486 '
                  'baris peta tersimpan, konteks Hakim-status nyata per '
                  'baris; lintasan B mengubah label awal 159/161/163 '
                  'jadi biasa (jawaban agen kedua log deploy v16); '
                  'lintasan C menukar penanda Romawi jadi Arab di '
                  'konteks judul bab (di luar peta kandidat)'),
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
        'tembakan_v19_lintasan_a': {
            'jumlah': len(kena_v19),
            'per_aturan': dict(Counter(
                jejak[('81', str(i))] for i in kena_v19)),
            'rincian': rincian_v19,
            'catatan': ('Tiap tembakan R28 di peta penuh fid=81 harus '
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
        'lintasan_c_simulasi_r28': {
            'catatan': ('Judul bab fid=81 bukan baris kandidat, jadi '
                        'simulasi memakai baris judul itu langsung: '
                        'label dibalik jadi biasa + penanda Romawi di '
                        'konteks ditukar jadi Bab N Arab; R28 harus '
                        'memulihkannya ke bab. Negatif: Bab 13 -> tetap '
                        'biasa. Baris yang dilewati (bukan judul baku) '
                        'dicatat di simulasi.'),
            'simulasi': sim_c,
            'tembakan_r28_peta_asli': len(kena_v19),
        },
        'vonis': vonis,
        'alasan_vonis': alasan,
    }
    out = VER / 'hasil_asap_v19.json'
    json.dump(hasil, open(out, 'w'), ensure_ascii=False, indent=1)
    print(f"baris berubah: {len(berubah)}/486 "
          f"({hasil['hasil']['persen_baris_berubah']}%)")
    print(f"transisi: {dict(transisi)}")
    print(f"mudah rusak: {len(berubah_mudah)}; GT bersih: {bersih_gt} "
          f"(menuju {len(gt_menuju)}, menjauh {len(gt_menjauh)})")
    print(f"tembakan R28: {len(kena_v19)} "
          f"{dict(Counter(jejak[('81', str(i))] for i in kena_v19))}")
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
    print('lintasan C:', [(s.get('penanda_asli'), s.get('judul_idx'),
                           s.get('pulih')) for s in sim_c],
          f"tembakan R28 peta asli {len(kena_v19)}")
    print('tertulis:', out)
    return hasil


if __name__ == '__main__':
    main()
