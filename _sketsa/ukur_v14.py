"""Ukur v14 di 279 baris berlabel manusia (tanpa petakan ulang Jev).

Simulasi deterministik dari peta v11 tersimpan (`_sketsa/peta35_tersimpan.json`):
  (a) demosi blok daftar isi/sistematika (label bab/subbab -> biasa),
  (b) aturan fragmen titik-dua,
  (c) aturan fragmen gambar (demosi langkah 3),
  (d) rekonstruksi pra-demosi: label akhir 'paragraf' di blok yang suara
      Jev-nya mengandung 'bab' -> 'biasa' (demosi v14 jalan SEBELUM demosi,
      jadi baris itu tidak pernah jadi 'paragraf'),
  (e) pengecualian ATURAN 5 (ASUMSI: label pra-koreksi tidak tersimpan;
      bila helper True dan 'subbab' ada di suara Jev dan label akhir
      'biasa', diasumsikan pemenangnya 'subbab' yang didemosi ATURAN 5),
  (f) pembersihan gabung (dedupe + hapus blok + hapus artefak nomor halaman)
      untuk baris gabung-saja.
Baris yang TIDAK diubah aturan deterministik memakai keluaran rantai v13
(label_rantai) apa adanya — gating Hakim v13 + prompt lama diasumsikan
sama; efek prompt baru diukur live terpisah (bukan di skor ini).

Jalankan:  python3 _sketsa/ukur_v14.py
Keluaran: ringkasan ke stdout + kunci 'perbaikan_bab_v14' di
`hasil_verifikasi_v11.json` (angka lama tidak diubah).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _muat_peta3():
    """Muat peta3_jev.py seperti tests/test_jev_hakim.py (stub modul berat)."""
    app = types.ModuleType('app')
    app.__path__ = [str(ROOT / 'app')]
    sys.modules['app'] = app
    ai = types.ModuleType('app.ai')
    ai.SessionLocal = object
    ai._teks_dari_berkas = lambda *a, **k: ''
    ai.UPLOAD_DIR = Path('/tmp')
    sys.modules['app.ai'] = ai
    models = types.ModuleType('app.models')
    models.FileBerkas = object
    sys.modules['app.models'] = models
    satpam = types.ModuleType('app.satpam')
    satpam.tanya_bebas_mutu = lambda *a, **k: {}
    sys.modules['app.satpam'] = satpam
    state = types.ModuleType('app.state')
    state.buang_daftar_isi = lambda t: t
    sys.modules['app.state'] = state
    konversi = types.ModuleType('app.konversi')
    konversi._pecah_blok = lambda t: [
        {'text': b, 'lines': [n], 'kosong': not b}
        for n, b in enumerate((t or '').split('\n'))]
    sys.modules['app.konversi'] = konversi
    spec = importlib.util.spec_from_file_location(
        '_peta3_ukur_v14', str(ROOT / 'peta3_jev.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def norm(s):
    return ' '.join(str(s or '').split())


def cocok_konteks(baris, idx, sebelum, sesudah):
    """Salinan _sketsa/petakan_tsv.py: skor kecocokan konteks TSV."""
    def potongan(s):
        return [norm(x) for x in (s or '').split('|') if norm(x)]
    skor = 0
    for pot, arah in ((potongan(sebelum), -1), (potongan(sesudah), +1)):
        if not pot:
            continue
        tetangga = []
        k = idx + arah
        while 0 <= k < len(baris) and len(tetangga) < 3:
            if norm(baris[k]):
                tetangga.append(norm(baris[k]))
            k += arah
        for p in pot:
            if any(t == p or t.startswith(p) or p.startswith(t)
                   for t in tetangga):
                skor += 1
    return skor


def main():
    P8 = _muat_peta3()
    assert P8.RULE_VERSION == 'jev-peta-v14', P8.RULE_VERSION
    peta = json.load(open(ROOT / '_sketsa/peta35_tersimpan.json'))
    pem = json.load(open(ROOT / '_sketsa/pemetaan_tsv_baris.json'))
    gating = json.load(open(ROOT / '_verifikasi_v11/hasil_rantai_gating.json'))
    tsv = list(csv.DictReader(
        open(ROOT / 'ground_truth/ground_truth_uji112.tsv'), delimiter='\t'))
    tsv_map = {(r['naskah'], r['no']): r for r in tsv}

    # ── per naskah: gabung bersih + blok + label per baris terkoreksi ──
    per_naskah = {}
    for kode, e in peta.items():
        baris = e['baris']
        gabung = {int(k): tuple(v) for k, v in e['gabung_penuh'].items()}
        gabung_bersih, blok = P8._bersihkan_gabung_daftar_isi(baris, gabung)
        label = {int(k): v for k, v in (e.get('label_penuh') or {}).items()}
        goyang = {int(g[0]): list(g[1]) for g in (e.get('goyang') or [])}
        label_v14 = dict(label)
        diubah = {}  # idx -> (alasan, label_lama, label_baru)
        for i, lab in list(label.items()):
            if i in blok and lab in ('bab', 'subbab'):
                label_v14[i] = 'biasa'
                diubah[i] = ('blok', lab, 'biasa')
        for i, lab in list(label.items()):
            if i in diubah:
                continue
            t = norm(baris[i])
            if lab in ('bab', 'subbab') and P8._POLA_FRAGMEN_TITIK_DUA.match(t):
                label_v14[i] = 'biasa'
                diubah[i] = ('fragmen-titik-dua', lab, 'biasa')
        for i, lab in list(label.items()):
            if i in diubah or lab != 'bab':
                continue
            t = re.sub(r'^\d{1,3}\s+', '', baris[i].strip())
            if P8._POLA_BAB_NOMOR.match(t):
                continue
            j = i - 1
            while j >= 0 and not baris[j].strip():
                j -= 1
            if j < 0:
                continue
            if j in gabung:
                _pen, _jud = gabung[j]
                if re.match(r'^\s*BAB\s+[IVX0-9]+', _pen, re.I) and not _jud:
                    continue
            if not re.match(r'^(?:Pada\s+)?(?:Gambar|Tabel|Grafik)\b',
                            baris[j].strip(), re.I):
                continue
            if t and t == t.upper() and len(t) <= 70 and \
                    not re.search(r'[.!?…]["\')\]]*\s*$', t):
                label_v14[i] = 'biasa'
                diubah[i] = ('fragmen-gambar', lab, 'biasa')
        for i, lab in list(label.items()):
            if i in diubah or lab != 'paragraf':
                continue
            if i in blok and 'bab' in goyang.get(i, []):
                label_v14[i] = 'biasa'
                diubah[i] = ('paragraf-di-blok-suara-bab', lab, 'biasa')
        # (g) demosi kehilangan perlindungan (a): judul salinan yang di v13
        #     dilindungi pengecualian (a) (baris sebelumnya penanda BAB polos
        #     di gabung) kehilangan perlindungan itu di v14 bila entri gabung
        #     penandanya terhapus (blok/dedupe) — demosi langkah 3 lalu
        #     mendemosinya, kecuali masih dilindungi pengecualian (b)
        #     (huruf BESAR pendek) atau cocok _POLA_BAB_NOMOR.
        for i, lab in list(label.items()):
            if i in diubah or lab != 'bab':
                continue
            t = re.sub(r'^\d{1,3}\s+', '', baris[i].strip())
            if P8._POLA_BAB_NOMOR.match(t):
                continue
            if t and t == t.upper() and len(t) <= 70 and \
                    not re.search(r'[.!?…]["\')\]]*\s*$', t):
                continue  # masih dilindungi (b)
            j = i - 1
            while j >= 0 and not baris[j].strip():
                j -= 1
            if j < 0 or j not in gabung or j in gabung_bersih:
                continue
            _pen, _jud = gabung[j]
            if re.match(r'^\s*BAB\s+[IVX0-9]+', _pen, re.I) and not _jud:
                label_v14[i] = 'biasa'
                diubah[i] = ('demosi-hilang-perlindungan-a', lab, 'biasa')
        # (h) dibuang TABLE OF CONTEN (v14): baris judul daftar isi itu
        #     sendiri bukan kandidat di v14 -> efektif 'biasa'.
        for i, lab in list(label.items()):
            if i in diubah:
                continue
            if re.match(r'^\s*TABLE\s+OF\s+CONTEN', baris[i], re.I):
                label_v14[i] = 'biasa'
                diubah[i] = ('dibuang-table-of-contens', lab, 'biasa')
        # (e) pengecualian ATURAN 5 — ASUMSI (lihat docstring).
        asumsi_aturan5 = []
        for i, lab in list(label.items()):
            if lab != 'biasa' or i in diubah:
                continue
            if 'subbab' not in goyang.get(i, []):
                continue
            if P8._penanda_huruf_kepala_blok(baris, i):
                label_v14[i] = 'subbab'
                diubah[i] = ('aturan5-pengecualian', lab, 'subbab')
                asumsi_aturan5.append(i)
        per_naskah[kode] = {
            'baris': baris, 'gabung': gabung, 'gabung_bersih': gabung_bersih,
            'blok': blok, 'label_v11': label, 'label_v14': label_v14,
            'goyang': goyang, 'diubah': diubah,
            'asumsi_aturan5': asumsi_aturan5,
        }

    # ── skor 279 baris ──
    hasil_baris = []
    for g in gating['baris']:
        kode, no = g['naskah'], g['no']
        e = per_naskah[kode]
        benar = g['label_benar']
        if g['idx_peta'] is not None:
            i = g['idx_peta']
            det = e['label_v14'].get(i, 'biasa')
            if i in e['diubah']:
                label_v14 = det
                cara = e['diubah'][i][0]
            else:
                label_v14 = g['label_rantai']
                cara = 'rantai-v13'
            hasil_baris.append({**g, 'label_v14': label_v14,
                                'cara_v14': cara, 'idx_dipakai': i})
        else:
            # gabung-saja: pilih kemunculan lewat konteks, lalu cek gabung v14
            r = tsv_map[(kode, no)]
            p = pem.get(kode + '|' + no, {})
            kandidat = p.get('kandidat') or []
            if len(kandidat) == 1:
                idx_pilih = kandidat[0]
            elif kandidat:
                skor = [(cocok_konteks(e['baris'], j, r['konteks_sebelum'],
                                       r['konteks_sesudah']), j)
                        for j in kandidat]
                skor.sort(reverse=True)
                idx_pilih = skor[0][1]
            else:
                idx_pilih = None
            det = 'biasa'
            if idx_pilih is not None:
                if idx_pilih in e['gabung_bersih']:
                    det = 'bab'
                elif any(norm(jud) == norm(g['teks_baris'])
                         for _pen, jud in e['gabung_bersih'].values() if jud):
                    det = 'bab'
            if det != g['label_v11']:
                label_v14 = det
                cara = 'gabung-bersih'
            else:
                label_v14 = g['label_rantai']
                cara = 'rantai-v13'
            hasil_baris.append({**g, 'label_v14': label_v14,
                                'cara_v14': cara, 'idx_dipakai': idx_pilih})

    def skor(label_kunci):
        benar_jml = sum(1 for r in hasil_baris
                        if r[label_kunci] == r['label_benar'])
        per_label = {}
        for lab in ('bab', 'subbab', 'paragraf', 'biasa'):
            tot = [r for r in hasil_baris if r['label_benar'] == lab]
            ok = [r for r in tot if r[label_kunci] == lab]
            per_label[lab] = {'benar': len(ok), 'total': len(tot)}
        return benar_jml, per_label

    v11_ok, v11_per = skor('label_v11')
    v13_ok, v13_per = skor('label_rantai')
    v14_ok, v14_per = skor('label_v14')
    n = len(hasil_baris)
    # McNemar v14 vs v13 (berpasangan): b = v13 salah & v14 benar,
    # c = v13 benar & v14 salah.
    b = sum(1 for r in hasil_baris
            if r['label_rantai'] != r['label_benar']
            and r['label_v14'] == r['label_benar'])
    c = sum(1 for r in hasil_baris
            if r['label_rantai'] == r['label_benar']
            and r['label_v14'] != r['label_benar'])
    from math import erf, sqrt
    if b + c:
        z = (abs(b - c) - 1) / sqrt(b + c)
        p_mc = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))
    else:
        p_mc = 1.0

    # ── fokus bab: 42 salah-bab + 21 benar-bab ──
    salah_bab_v13 = [r for r in hasil_baris
                     if r['label_benar'] == 'biasa'
                     and r['label_rantai'] == 'bab']
    salah_bab_v14 = [r for r in hasil_baris
                     if r['label_benar'] == 'biasa'
                     and r['label_v14'] == 'bab']
    benar_bab_v13 = [r for r in hasil_baris
                     if r['label_benar'] == 'bab'
                     and r['label_rantai'] == 'bab']
    benar_bab_v14 = [r for r in hasil_baris
                     if r['label_benar'] == 'bab'
                     and r['label_v14'] == 'bab']
    antrean_v13 = [r for r in hasil_baris
                   if r.get('putusan_rantai') == 'antrean-manusia']
    antrean_v14 = [r for r in hasil_baris
                   if r.get('putusan_rantai') == 'antrean-manusia'
                   and r['cara_v14'] == 'rantai-v13']

    # ── ringkasan gabung/blok per naskah ──
    gabung_ringkas = {}
    for kode, e in per_naskah.items():
        gabung_ringkas[kode] = {
            'gabung_v11': len(e['gabung']),
            'gabung_v14': len(e['gabung_bersih']),
            'blok_baris': len(e['blok']),
            'label_diubah': len(e['diubah']),
            'asumsi_aturan5': e['asumsi_aturan5'],
        }

    print('v11 : %d/%d (%.1f%%)' % (v11_ok, n, 100 * v11_ok / n))
    print('v13 : %d/%d (%.1f%%)' % (v13_ok, n, 100 * v13_ok / n))
    print('v14 : %d/%d (%.1f%%)' % (v14_ok, n, 100 * v14_ok / n))
    print('per label v14:', {k: '%d/%d' % (v['benar'], v['total'])
                             for k, v in v14_per.items()})
    print('per label v13:', {k: '%d/%d' % (v['benar'], v['total'])
                             for k, v in v13_per.items()})
    print('McNemar v14 vs v13: b=%d (v13 salah, v14 benar) c=%d '
          '(v13 benar, v14 salah) p=%.4f' % (b, c, p_mc))
    print('salah-bab (benar biasa, dilabeli bab): v13=%d v14=%d'
          % (len(salah_bab_v13), len(salah_bab_v14)))
    print('benar-bab tertangkap: v13=%d/21 v14=%d/21'
          % (len(benar_bab_v13), len(benar_bab_v14)))
    print('antrean manusia: v13=%d v14=%d'
          % (len(antrean_v13), len(antrean_v14)))
    print('baris diubah deterministik: %d (per naskah: %s)'
          % (sum(len(e['diubah']) for e in per_naskah.values()),
             {k: len(e['diubah']) for k, e in per_naskah.items()
              if e['diubah']}))
    print('salah-bab v14 yang tersisa:')
    for r in salah_bab_v14:
        print('  ', r['naskah'], 'no', r['no'], '|', repr(r['teks_baris'][:60]),
              '| cara:', r['cara_v14'], '| idx:', r['idx_dipakai'])
    print('benar-bab yang HILANG di v14 (regresi):')
    for r in hasil_baris:
        if r['label_benar'] == 'bab' and r['label_rantai'] == 'bab' \
                and r['label_v14'] != 'bab':
            print('  ', r['naskah'], 'no', r['no'], '|',
                  repr(r['teks_baris'][:60]), '| cara:', r['cara_v14'])
    print('perubahan per baris (v13 -> v14):')
    for r in hasil_baris:
        if r['label_rantai'] != r['label_v14']:
            print('  ', r['naskah'], 'no', r['no'], '| benar:',
                  r['label_benar'], '| v13:', r['label_rantai'],
                  '-> v14:', r['label_v14'], '| cara:', r['cara_v14'])

    # ── simpan ke hasil_verifikasi_v11.json (kunci baru, angka lama utuh) ──
    jalan = ROOT / 'hasil_verifikasi_v11.json'
    data = json.load(open(jalan))
    data['perbaikan_bab_v14'] = {
        'rule_version': 'jev-peta-v14',
        'n_baris': n,
        'skor': {
            'v11': {'benar': v11_ok, 'total': n, 'per_label': v11_per},
            'v13': {'benar': v13_ok, 'total': n, 'per_label': v13_per},
            'v14': {'benar': v14_ok, 'total': n, 'per_label': v14_per},
        },
        'mcnemar_v14_vs_v13': {'b': b, 'c': c, 'p': round(p_mc, 4)},
        'salah_bab_benar_biasa': {'v13': len(salah_bab_v13),
                                  'v14': len(salah_bab_v14)},
        'benar_bab_tertangkap': {'v13': len(benar_bab_v13),
                                 'v14': len(benar_bab_v14),
                                 'total': 21},
        'antrean_manusia': {'v13': len(antrean_v13),
                            'v14': len(antrean_v14)},
        'baris_diubah_deterministik': sum(
            len(e['diubah']) for e in per_naskah.values()),
        'asumsi_aturan5_idx': {
            k: e['asumsi_aturan5'] for k, e in per_naskah.items()
            if e['asumsi_aturan5']},
        'gabung_per_naskah': gabung_ringkas,
        'salah_bab_v14_tersisa': [
            {'naskah': r['naskah'], 'no': r['no'],
             'teks': r['teks_baris'], 'cara': r['cara_v14']}
            for r in salah_bab_v14],
        'catatan': (
            'Simulasi deterministik dari peta v11 tersimpan; label pra-koreksi '
            'tidak tersimpan sehingga pengecualian ATURAN 5 memakai asumsi '
            '(suara Jev mengandung subbab + label akhir biasa = pemenang '
            'subbab yang didemosi ATURAN 5). Efek prompt agen kedua yang baru '
            'TIDAK termasuk di skor ini; diukur live terpisah.'),
    }
    json.dump(data, open(jalan, 'w'), ensure_ascii=False, indent=2)
    print('tersimpan: hasil_verifikasi_v11.json kunci perbaikan_bab_v14')


if __name__ == '__main__':
    main()
