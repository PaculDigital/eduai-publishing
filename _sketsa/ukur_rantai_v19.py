#!/usr/bin/env python3
"""Ukur 279 baris sengketa lewat KODE PRODUKSI v19 (R28 penanda bab
Arab, 15 Nov 2026). Bandingkan dengan v18 (267/279,
`_verifikasi_v11/hasil_rantai_v18.json`).

0 Jev, 0 LLM, 0 baca DB produksi. Masukan lokal:
`_verifikasi_v11/hasil_rantai_revisihemat.json` lewat
`aturan_v16.muat()` + konteks tetangga dari `_sketsa/gt35.json`.

KONTEKS: gt35 menyimpan +-3 baris NON-KOSONG terdekat tiap sisi
(digabung ' | '); harness membangun `baris_mentah` =
sebelum + [teks] + sesudah, `idx_mentah` = len(sebelum). Aturan v19
melewati baris kosong (nearest-non-blank), jadi perilaku offline
sama dengan produksi (peta penuh, kosong dilewati). Tiga skor
dilaporkan untuk memisahkan efeknya:
  (1) 267 baseline v18 dengan konteks (dari berkas sebelumnya);
  (2) v19 dengan konteks=None — R10 tanpa konteks SUDAH memperbaiki
      AJ-1:277 (judul baku tanpa pagar zona), jadi R28 tidak menambah
      apa-apa di sini (harapan 259 = sama seperti v18 tanpa konteks);
  (3) v19 dengan konteks sintetis — skor penuh (harapan 268).
      Inilah angka yang jujur (produksi selalu punya konteks):
      nilai R28 hanya terlihat dengan konteks, di pagar zona Arab.
Perubahan label antara (2) dan (3) pada baris yang TIDAK diklaim
aturan v19 dilaporkan terpisah: itu efek konteks pada R4
(gerombol) / R10 (zona) saja, bukan aturan baru.

Harapan (dihitung dari bedah 1 baris, BUKAN target yang dipaksakan):
  R28: 1 (AJ-1:277), 0 dirusak -> 267 + 1 = 268.
Bila skor menyimpang dari harapan, selidiki dan laporkan, jangan
dipaksakan cocok.

Batas yang sama seperti ukur v18: simulasi TIDAK memakai pagar
`demosi_v6` (data 279 tidak mencatat baris v6-demoted). R28
menyentuh label 'bab' hanya sebagai promosi ke 'bab' (no-op bila
sudah 'bab'), jadi pagar `_V16_BOLEH_DARI_BAB` tidak mengubah skor
di sini.

Keluaran: `_verifikasi_v11/hasil_rantai_v19.json`.

Pemakaian:
    python3 _sketsa/ukur_rantai_v19.py
"""
import importlib.util
import json
import os
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_sketsa'))

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
        raise AssertionError('harness ukur 279 tidak boleh memanggil Jev')


sys.modules['app.satpam'] = _SatpamDiam()
_state = types.ModuleType('app.state')
_state.buang_daftar_isi = lambda t: t
sys.modules['app.state'] = _state

_spec = importlib.util.spec_from_file_location(
    '_peta3_produksi_v19', str(ROOT / 'peta3_jev.py'))
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)

assert os.path.realpath(P.__file__) == os.path.realpath(
    str(ROOT / 'peta3_jev.py')), P.__file__
assert P.RULE_VERSION == 'jev-peta-v19', P.RULE_VERSION

import aturan_v16  # noqa: E402  (pemuat data 279 saja)

ATURAN_BARU_V19 = ('R28_penanda_bab_arab',)
HARAPAN_PER_ATURAN = {'R28_penanda_bab_arab': 1}
HARAPAN_SISA_SALAH = ['AE2:165', 'AP-3:267', 'Q3:32', 'Y2:63', 'P2:112',
                      'B4:125', 'S2:217', 'C4:228', 'A4:243',
                      'A4:245', 'AP-3:270']
# AJ-1:277 TIDAK lagi sisa salah: R28 (penanda Arab 'Bab 5') memperbaikinya
# — itulah satu-satunya target v19. Sisa 11 baris jadi kandidat antrean
# manusia.


def skor(labels, rows):
    return sum(1 for r in rows
               if labels[(r['naskah'], str(r['no']))] == r['label_benar'])


def bangun_konteks(rows):
    """Konteks sintetis dari gt35.json: +-3 non-kosong terdekat tiap
    sisi. Kembalikan (konteks, info_silang)."""
    gt = json.load(open(ROOT / '_sketsa' / 'gt35.json'))
    gt_map = {}
    for kode, ns in gt['naskah'].items():
        for b in ns['baris']:
            gt_map[(kode, str(b['no']))] = b
    konteks = {}
    hilang = []
    for r in rows:
        k = (r['naskah'], str(r['no']))
        b = gt_map.get(k)
        if b is None:
            hilang.append(f"{k[0]}:{k[1]}")
            continue
        assert (b.get('teks_baris') or '') == (r.get('teks_baris') or ''), k
        assert b.get('label_benar') == r['label_benar'], k
        seb = [s for s in (b.get('konteks_sebelum') or '').split(' | ')
               if s.strip()]
        ses = [s for s in (b.get('konteks_sesudah') or '').split(' | ')
               if s.strip()]
        mentah = seb + [r['teks_baris']] + ses
        konteks[k] = {'hakim_status': None, 'baris_mentah': mentah,
                      'idx_mentah': len(seb)}
    # Silang dengan jendela mentah +-3 (39 baris bertanda di JSON
    # rantai): tetangga non-kosong terdekat harus sama.
    cocok_seb = cocok_ses = banding_seb = banding_ses = 0
    beda = []
    for r in rows:
        if not r.get('konteks'):
            continue
        k = (r['naskah'], str(r['no']))
        b = gt_map.get(k)
        if b is None:
            continue
        mentah_j = r['konteks']['sebelum']
        nonblank_j = [s for s in mentah_j if s.strip()]
        if nonblank_j:
            banding_seb += 1
            seb_gt = (b.get('konteks_sebelum') or '').split(' | ')
            seb_gt = [s.strip() for s in seb_gt if s.strip()]
            if seb_gt and seb_gt[-1] == nonblank_j[-1].strip():
                cocok_seb += 1
            else:
                beda.append(f"{k[0]}:{k[1]} sebelum")
        mentah_j2 = r['konteks']['sesudah']
        nonblank_j2 = [s for s in mentah_j2 if s.strip()]
        if nonblank_j2:
            banding_ses += 1
            ses_gt = (b.get('konteks_sesudah') or '').split(' | ')
            ses_gt = [s.strip() for s in ses_gt if s.strip()]
            if ses_gt and ses_gt[0] == nonblank_j2[0].strip():
                cocok_ses += 1
            else:
                beda.append(f"{k[0]}:{k[1]} sesudah")
    info = {'baris_tanpa_gt35': hilang,
            'silang_tetangga_sebelum': f"{cocok_seb}/{banding_seb}",
            'silang_tetangga_sesudah': f"{cocok_ses}/{banding_ses}",
            'silang_beda': beda}
    return konteks, info


def main():
    rows, _v2map = aturan_v16.muat()
    assert len(rows) == 279, len(rows)
    benar = {(r['naskah'], str(r['no'])): r['label_benar'] for r in rows}
    v15 = {(r['naskah'], str(r['no'])): r['label_v15'] for r in rows}
    rantai = {(r['naskah'], str(r['no'])): r['label_rantai'] for r in rows}

    konteks, info_silang = bangun_konteks(rows)
    assert not info_silang['baris_tanpa_gt35'], info_silang['baris_tanpa_gt35']

    lama = json.load(open(ROOT / '_verifikasi_v11'
                          / 'hasil_rantai_v18.json'))
    assert lama['v18_dengan_konteks_dari_rantai_benar'] == 267, lama['v18_dengan_konteks_dari_rantai_benar']
    assert lama['v18_dengan_konteks_dari_v15_benar'] == 261, lama['v18_dengan_konteks_dari_v15_benar']
    lab_lama_rantai = {(k.split(':')[0], k.split(':')[1]): v for k, v in
                       lama['label_akhir']['v18_dengan_konteks_dari_rantai'].items()}
    lab_lama_v15 = {(k.split(':')[0], k.split(':')[1]): v for k, v in
                    lama['label_akhir']['v18_dengan_konteks_dari_v15'].items()}

    # (2) v19 tanpa konteks: R28 menembak judul baku (seperti R10).
    lab_a_rantai, jejak_a = P._v16_terapkan(rows, rantai, konteks=None)
    lab_a_v15, _jejak_a15 = P._v16_terapkan(rows, v15, konteks=None)
    # (3) v19 dengan konteks sintetis: skor penuh.
    lab_b_rantai, jejak_b = P._v16_terapkan(rows, rantai, konteks=konteks)
    lab_b_v15, _jejak_b15 = P._v16_terapkan(rows, v15, konteks=konteks)

    # (3b) v18 BEKU dengan konteks yang sama (berkas /tmp/peta3_jev_v18.py
    # — dibuat dari `git show main:peta3_jev.py`). Ini perbandingan
    # jujur: v19 vs v18, keduanya DENGAN konteks seperti produksi.
    # Tanpa berkas ini, perbandingan dilewati.
    v18_konteks = None
    lab18_konteks = None
    if os.path.exists('/tmp/peta3_jev_v18.py'):
        _spec18 = importlib.util.spec_from_file_location(
            '_peta3_produksi_v18_beku', '/tmp/peta3_jev_v18.py')
        P18 = importlib.util.module_from_spec(_spec18)
        _spec18.loader.exec_module(P18)
        assert P18.RULE_VERSION == 'jev-peta-v18', P18.RULE_VERSION
        lab18_konteks, _j18 = P18._v16_terapkan(rows, rantai,
                                               konteks=konteks)
        v18_konteks = skor(lab18_konteks, rows)

    def benar_list(labels):
        return [labels[(r['naskah'], str(r['no']))] == r['label_benar']
                for r in rows]

    def per_aturan(jejak, labels_lama, labels_baru):
        out = []
        for nama, pola, _ in P._V16_ATURAN_P:
            kena, diperbaiki, dirusak, noop = [], [], [], []
            for r in rows:
                k = (r['naskah'], str(r['no']))
                if jejak[k] != nama:
                    continue
                kena.append(f"{r['naskah']}:{r['no']}")
                if labels_baru[k] == benar[k] \
                        and labels_lama[k] != benar[k]:
                    diperbaiki.append(f"{r['naskah']}:{r['no']}")
                elif labels_baru[k] != benar[k] \
                        and labels_lama[k] == benar[k]:
                    dirusak.append(f"{r['naskah']}:{r['no']}")
                else:
                    noop.append(f"{r['naskah']}:{r['no']}")
            out.append({'nama': nama, 'pola': pola, 'kena': len(kena),
                        'diperbaiki': len(diperbaiki),
                        'dirusak': len(dirusak),
                        'noop_sudah_benar': len(noop),
                        'baris_kena': kena,
                        'baris_diperbaiki': diperbaiki,
                        'baris_dirusak': dirusak})
        return out

    per_b = per_aturan(jejak_b, lab_lama_rantai, lab_b_rantai)
    per_a = per_aturan(jejak_a, lab_lama_rantai, lab_a_rantai)
    per_b_v15 = per_aturan(_jejak_b15, lab_lama_v15, lab_b_v15)

    # Efek konteks pada R4/R10 saja: label berubah antara (2) dan (3)
    # pada baris yang TIDAK diklaim aturan v19 di (3).
    efek_konteks = []
    for r in rows:
        k = (r['naskah'], str(r['no']))
        if jejak_b[k] in ATURAN_BARU_V19:
            continue
        if lab_a_rantai[k] != lab_b_rantai[k]:
            efek_konteks.append({
                'baris': f"{r['naskah']}:{r['no']}",
                'tanpa_konteks': lab_a_rantai[k],
                'dengan_konteks': lab_b_rantai[k],
                'jejak_tanpa': jejak_a[k],
                'jejak_dengan': jejak_b[k],
                'label_benar': benar[k],
            })

    skor_a = skor(lab_a_rantai, rows)
    skor_a_v15 = skor(lab_a_v15, rows)
    skor_b = skor(lab_b_rantai, rows)
    skor_b_v15 = skor(lab_b_v15, rows)

    beda_sama_konteks = None
    mcnemar_sama_konteks = None
    if lab18_konteks is not None:
        beda_sama_konteks = []
        for r in rows:
            k = (r['naskah'], str(r['no']))
            if lab18_konteks[k] != lab_b_rantai[k]:
                beda_sama_konteks.append({
                    'baris': f"{r['naskah']}:{r['no']}",
                    'v18_dengan_konteks': lab18_konteks[k],
                    'v19_dengan_konteks': lab_b_rantai[k],
                    'jejak_v19': jejak_b[k],
                    'label_benar': benar[k],
                    'v19_memperbaiki': lab_b_rantai[k] == benar[k],
                    'v19_merusak': lab18_konteks[k] == benar[k]
                                    and lab_b_rantai[k] != benar[k],
                })
        mcnemar_sama_konteks = aturan_v16.mcnemar(
            benar_list(lab18_konteks), benar_list(lab_b_rantai))

    sisa_salah = [f"{r['naskah']}:{r['no']}" for r in rows
                  if lab_b_rantai[(r['naskah'], str(r['no']))]
                  != r['label_benar']]
    per_v19 = {a['nama']: a for a in per_b if a['nama'] in ATURAN_BARU_V19}
    cocok_per_aturan = all(
        per_v19[n]['diperbaiki'] == HARAPAN_PER_ATURAN[n]
        and per_v19[n]['dirusak'] == 0 for n in ATURAN_BARU_V19)

    hasil = {
        'tahap': ('ukur 279 baris sengketa lewat KODE PRODUKSI v19 '
                  '(15 Nov 2026, branch '
                  'agen/wulan/aturan-v19-arab, belum '
                  'push/merge/deploy)'),
        'metode': ('peta3_jev._v16_terapkan() pada label_rantai dan '
                   'label_v15, dua kali: konteks=None lalu '
                   'konteks sintetis dari _sketsa/gt35.json '
                   '(+-3 non-kosong tiap sisi); 0 panggilan Jev; skrip '
                   '_sketsa/ukur_rantai_v19.py; pembanding v18 dengan '
                   'konteks dari '
                   '_verifikasi_v11/hasil_rantai_v18.json'),
        'n': 279,
        'rule_version': P.RULE_VERSION,
        'v15_benar': skor(v15, rows),
        'rantai_benar': skor(rantai, rows),
        'v18_dengan_konteks_dari_rantai_benar': 267,
        'v18_dengan_konteks_dari_v15_benar': 261,
        'v19_tanpa_konteks_dari_rantai_benar': skor_a,
        'v19_tanpa_konteks_dari_v15_benar': skor_a_v15,
        'v19_dengan_konteks_dari_rantai_benar': skor_b,
        'v19_dengan_konteks_dari_v15_benar': skor_b_v15,
        'harapan_tanpa_konteks_dari_rantai': 259,
        'harapan_dengan_konteks_dari_rantai': 268,
        'cocok_harapan_tanpa_konteks': skor_a == 259,
        'cocok_harapan_dengan_konteks': skor_b == 268,
        'cocok_per_aturan': cocok_per_aturan,
        'mcnemar_v19_vs_v18_dengan_konteks': aturan_v16.mcnemar(
            benar_list(lab_lama_rantai), benar_list(lab_b_rantai)),
        'mcnemar_v19_konteks_vs_tanpa_konteks': aturan_v16.mcnemar(
            benar_list(lab_a_rantai), benar_list(lab_b_rantai)),
        'mcnemar_v19_dari_v15_vs_v15': aturan_v16.mcnemar(
            benar_list(v15), benar_list(lab_b_v15)),
        'v18_beku_dengan_konteks_dari_rantai_benar': v18_konteks,
        'mcnemar_v19_vs_v18_sama_konteks': mcnemar_sama_konteks,
        'beda_v19_vs_v18_sama_konteks': beda_sama_konteks,
        'per_aturan_v19_dari_rantai': per_b,
        'per_aturan_v19_dari_v15': per_b_v15,
        'per_aturan_tanpa_konteks_dari_rantai': per_a,
        'efek_konteks_bukan_v19': efek_konteks,
        'info_konteks': info_silang,
        'label_akhir': {
            'v19_tanpa_konteks_dari_rantai': {
                f"{k[0]}:{k[1]}": v for k, v in lab_a_rantai.items()},
            'v19_dengan_konteks_dari_rantai': {
                f"{k[0]}:{k[1]}": v for k, v in lab_b_rantai.items()},
            'v19_dengan_konteks_dari_v15': {
                f"{k[0]}:{k[1]}": v for k, v in lab_b_v15.items()},
        },
        'sisa_salah_setelah_v19': sisa_salah,
        'harapan_sisa_salah': HARAPAN_SISA_SALAH,
        'cocok_sisa_salah': sorted(sisa_salah) == sorted(HARAPAN_SISA_SALAH),
        'batas_simulasi': (
            'Sama seperti ukur v18: simulasi TIDAK memakai pagar '
            'demosi_v6 (data 279 tidak mencatat baris v6-demoted). '
            'R28 hanya mempromosi ke bab (no-op bila sudah bab), jadi '
            'pagar _V16_BOLEH_DARI_BAB tidak mengubah skor di sini. '
            'Konteks sintetis memakai +-3 non-kosong dari gt35; '
            'produksi memakai peta penuh dan aturan melewati baris '
            'kosong dengan cara yang sama. Perbandingan jujur adalah '
            'v19 vs v18 SAMA-SAMA dengan konteks (268 vs 267, beda '
            'bersih +1, 0 dirusak). R28 tanpa konteks tidak menambah '
            'apa-apa karena R10 tanpa konteks sudah memperbaiki '
            'AJ-1:277 duluan — angka tanpa konteks bukan bukti '
            'ketangguhan, hanya kontrol.'),
        'vonis': ('COCOK' if skor_b == 268 and cocok_per_aturan
                  and sorted(sisa_salah) == sorted(HARAPAN_SISA_SALAH)
                  else 'MENYIMPANG DARI HARAPAN — selidiki sebelum lapor'),
    }
    out = ROOT / '_verifikasi_v11' / 'hasil_rantai_v19.json'
    json.dump(hasil, open(out, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('dari rantai: v18 dengan konteks 267 -> v19 tanpa konteks', skor_a,
          '(harapan 259) -> v19 dengan konteks', skor_b, '(harapan 268)')
    print('dari v15: v18 dengan konteks 261 -> v19 tanpa konteks', skor_a_v15,
          '-> v19 dengan konteks', skor_b_v15)
    for n in ATURAN_BARU_V19:
        a = per_v19[n]
        print(f"  {n}: kena={a['kena']} perbaiki={a['diperbaiki']} "
              f"rusak={a['dirusak']} {a['baris_diperbaiki']}")
    print('McNemar v19 vs v18 (dengan konteks):',
          hasil['mcnemar_v19_vs_v18_dengan_konteks'])
    if v18_konteks is not None:
        print('v18 beku DENGAN konteks:', v18_konteks,
              '-> v19 dengan konteks:', skor_b,
              '(beda bersih:', skor_b - v18_konteks, ')')
        print('McNemar v19 vs v18 (sama-sama konteks):',
              mcnemar_sama_konteks)
        print('beda v19 vs v18 sama konteks:',
              [(d['baris'], d['v18_dengan_konteks'],
                d['v19_dengan_konteks']) for d in beda_sama_konteks])
    else:
        print('CATATAN: /tmp/peta3_jev_v18.py tidak ada — perbandingan '
              'v19 vs v18 sama-sama-konteks dilewati')
    print('McNemar konteks vs tanpa konteks:',
          hasil['mcnemar_v19_konteks_vs_tanpa_konteks'])
    print('efek konteks bukan v19 (R4/R10):', len(efek_konteks),
          [e['baris'] for e in efek_konteks])
    print('silang konteks gt35 vs JSON:', info_silang)
    print('sisa salah:', len(sisa_salah), sisa_salah)
    print('vonis:', hasil['vonis'])
    print('tulis:', out)


if __name__ == '__main__':
    main()
