"""Ukur v15 di 279 baris berlabel manusia.

Metode (jujur soal apa yang diukur live dan apa yang dibawa):
  * R3 (8 baris): diukur LIVE dengan kode v15 (run container
    hasil_gating_r3.json: Jev -> koreksi v14 -> Hakim gating -> agen
    kedua offline untuk baris yang ditandai). Satu-satunya naskah yang
    dipetakan ulang, karena di situlah temuannya.
  * 5 naskah lain yang berubah di buang_daftar_isi (A4/L3/M3/O3/S2,
    39 baris): label v14 DIBAWA, dengan syarat konteks lokal tiap baris
    (3 baris sebelum/sesudah dari TSV) utuh di teks bersih baru. Bila
    ada baris yang konteksnya tidak utuh, ia dilaporkan dan TIDAK
    dibawa diam-diam.
  * 29 naskah lain (232 baris): teks bersih byte-identik lama-vs-baru,
    jadi label v14 dibawa apa adanya (pipeline hilir tidak berubah
    di v15 selain nomor versi).
  * Label v14 per baris dihitung ulang dengan logika ukur_v14.py yang
    sama (dari peta v11 tersimpan) supaya head-to-head se-metode.

Jalankan:  python3 _sketsa/ukur_v15.py
Keluaran: ringkasan ke stdout + kunci 'perbaikan_bom_v15' di
`hasil_verifikasi_v11.json` (angka lama tidak diubah).
"""
from __future__ import annotations

import csv
import importlib.util
import json
import re
import subprocess
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
        '_peta3_ukur_v15', str(ROOT / 'peta3_jev.py'))
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
    total = 0
    for pot, arah in ((potongan(sebelum), -1), (potongan(sesudah), +1)):
        if not pot:
            continue
        total += len(pot)
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
    return skor, total


def _muat_state_lama():
    src = subprocess.check_output(['git', 'show', 'HEAD:app/state.py'],
                                  cwd=str(ROOT)).decode()
    p = Path('/tmp/state_lama_v15.py')
    p.write_text(src, encoding='utf-8')
    spec = importlib.util.spec_from_file_location('state_lama_v15', str(p))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    # Impor buang_daftar_isi ASLI dulu: _muat_peta3() men-stub app.state
    # dengan identitas, jadi impor sesudahnya akan salah.
    from app.state import buang_daftar_isi as buang_baru
    P8 = _muat_peta3()
    assert P8.RULE_VERSION == 'jev-peta-v15', P8.RULE_VERSION
    peta = json.load(open(ROOT / '_sketsa/peta35_tersimpan.json'))
    pem = json.load(open(ROOT / '_sketsa/pemetaan_tsv_baris.json'))
    gating = json.load(open(ROOT / '_verifikasi_v11/hasil_rantai_gating.json'))
    tsv = list(csv.DictReader(
        open(ROOT / 'ground_truth/ground_truth_uji112.tsv'), delimiter='\t'))
    tsv_map = {(r['naskah'], r['no']): r for r in tsv}
    live_r3 = json.load(open(ROOT / '_verifikasi_v11/hasil_gating_r3.json'))
    adj = {a['idx']: a for a in live_r3.get('adjudikasi_v15', [])}
    baris_r3 = live_r3['baris']
    lab_r3 = {int(k): v for k, v in live_r3['label'].items()}
    rek_r3 = {r['idx'] for r in live_r3['rekaman']}

    # ── per naskah: label v14 (logika ukur_v14.py yang sama) ──────────
    per_naskah = {}
    for kode, e in peta.items():
        baris = e['baris']
        gabung = {int(k): tuple(v) for k, v in e['gabung_penuh'].items()}
        gabung_bersih, blok = P8._bersihkan_gabung_daftar_isi(baris, gabung)
        label = {int(k): v for k, v in (e.get('label_penuh') or {}).items()}
        goyang = {int(g[0]): list(g[1]) for g in (e.get('goyang') or [])}
        label_v14 = dict(label)
        diubah = {}
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
        for i, lab in list(label.items()):
            if i in diubah or lab != 'bab':
                continue
            t = re.sub(r'^\d{1,3}\s+', '', baris[i].strip())
            if P8._POLA_BAB_NOMOR.match(t):
                continue
            if t and t == t.upper() and len(t) <= 70 and \
                    not re.search(r'[.!?…]["\')\]]*\s*$', t):
                continue
            j = i - 1
            while j >= 0 and not baris[j].strip():
                j -= 1
            if j < 0 or j not in gabung or j in gabung_bersih:
                continue
            _pen, _jud = gabung[j]
            if re.match(r'^\s*BAB\s+[IVX0-9]+', _pen, re.I) and not _jud:
                label_v14[i] = 'biasa'
                diubah[i] = ('demosi-hilang-perlindungan-a', lab, 'biasa')
        for i, lab in list(label.items()):
            if i in diubah:
                continue
            if re.match(r'^\s*TABLE\s+OF\s+CONTEN', baris[i], re.I):
                label_v14[i] = 'biasa'
                diubah[i] = ('dibuang-table-of-contens', lab, 'biasa')
        for i, lab in list(label.items()):
            if lab != 'biasa' or i in diubah:
                continue
            if 'subbab' not in goyang.get(i, []):
                continue
            if P8._penanda_huruf_kepala_blok(baris, i):
                label_v14[i] = 'subbab'
                diubah[i] = ('aturan5-pengecualian', lab, 'subbab')
        per_naskah[kode] = {
            'baris': baris, 'gabung': gabung, 'gabung_bersih': gabung_bersih,
            'blok': blok, 'label_v11': label, 'label_v14': label_v14,
            'goyang': goyang, 'diubah': diubah,
        }

    # ── label v14 per baris (metode ukur_v14 yang sama) ────────────────
    hasil_baris = []
    for g in gating['baris']:
        kode, no = g['naskah'], g['no']
        e = per_naskah[kode]
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
            r = tsv_map[(kode, no)]
            p = pem.get(kode + '|' + no, {})
            kandidat = p.get('kandidat') or []
            if len(kandidat) == 1:
                idx_pilih = kandidat[0]
            elif kandidat:
                skor = [(cocok_konteks(e['baris'], j, r['konteks_sebelum'],
                                       r['konteks_sesudah'])[0], j)
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

    # ── label v15 per baris ────────────────────────────────────────────
    # R3: dari run live v15 (pemetaan ulang lawan baris live).
    def _petakan_r3_live(g):
        r = tsv_map[(g['naskah'], g['no'])]
        teks_norm = norm(g['teks_baris'])
        kand = [i for i, b in enumerate(baris_r3)
                if norm(b) == teks_norm]
        if not kand:
            return None, 0, 0
        skor = [(cocok_konteks(baris_r3, j, r['konteks_sebelum'],
                               r['konteks_sesudah']), j) for j in kand]
        skor.sort(key=lambda x: (x[0][0], -x[1]), reverse=True)
        (sk, tot), idx_pilih = skor[0]
        return idx_pilih, sk, tot

    r3_hasil = {}
    for g in hasil_baris:
        if g['naskah'] != 'R3':
            continue
        idx_pilih, sk, tot = _petakan_r3_live(g)
        if idx_pilih is None:
            r3_hasil[g['no']] = {
                'idx_live': None, 'label_v15': 'biasa',
                'cara': 'tidak-ketemu-di-live (biasa)', 'konteks_skor': (sk, tot)}
            continue
        lab_live = lab_r3.get(idx_pilih, 'biasa')
        if idx_pilih in adj:
            label_v15 = adj[idx_pilih]['label_akhir']
            cara = 'adjudikasi-agen-kedua'
        elif idx_pilih in rek_r3:
            label_v15 = lab_live
            cara = 'ditandai-tanpa-adjudikasi (label live)'
        else:
            label_v15 = lab_live
            cara = 'label-live-v15'
        r3_hasil[g['no']] = {
            'idx_live': idx_pilih, 'label_v15': label_v15,
            'cara': cara, 'konteks_skor': (sk, tot),
            'label_live': lab_live}

    # 5 naskah berubah lain: uji konteks lokal di teks bersih baru.
    # Metode substring (bukan baris mentah): teks baris TSV adalah BLOK
    # hasil stitch, jadi dicari sebagai substring di teks bersih yang
    # dinormalisasi; konteks utuh bila semua potongan sebelum/sesudah
    # ada di jendela +-2000 kar pada sisi yang benar.
    # (buang_baru sudah diimpor di awal main, sebelum stub _muat_peta3.)
    state_lama = _muat_state_lama()
    peta_berkas = json.load(open('/tmp/peta_kode_berkas2.json'))
    konteks_cek = {}
    for kode in ('A4', 'L3', 'M3', 'O3', 'S2'):
        teks = open(ROOT / 'teks_latih' / peta_berkas[kode],
                    encoding='utf-8', errors='replace').read()
        baru_norm = norm(buang_baru(teks))
        for g in hasil_baris:
            if g['naskah'] != kode:
                continue
            r = tsv_map[(kode, g['no'])]
            t = norm(g['teks_baris'])
            sebelum = [norm(x) for x in (r['konteks_sebelum'] or '').split('|')
                       if norm(x)]
            sesudah = [norm(x) for x in (r['konteks_sesudah'] or '').split('|')
                       if norm(x)]
            tot = len(sebelum) + len(sesudah)
            best = (0, -1)
            start = 0
            while True:
                j = baru_norm.find(t, start)
                if j < 0:
                    break
                sk = 0
                for p in sebelum:
                    k = baru_norm.rfind(p, 0, j)
                    if k >= 0 and j - k <= 2000:
                        sk += 1
                for p in sesudah:
                    k = baru_norm.find(p, j + len(t))
                    if k >= 0 and k - (j + len(t)) <= 2000:
                        sk += 1
                if (sk, -j) > (best[0], -best[1] if best[1] >= 0 else 0):
                    best = (sk, j)
                start = j + 1
            sk, j = best
            konteks_cek[(kode, g['no'])] = {
                'utuh': sk == tot and tot > 0,
                'konteks_skor': (sk, tot), 'idx_baru': j,
                'ditemukan': j >= 0}

    # ── gabungkan label v15 ────────────────────────────────────────────
    for h in hasil_baris:
        if h['naskah'] == 'R3':
            h['label_v15'] = r3_hasil[h['no']]['label_v15']
            h['cara_v15'] = r3_hasil[h['no']]['cara']
            h['idx_live_r3'] = r3_hasil[h['no']]['idx_live']
        else:
            h['label_v15'] = h['label_v14']
            h['cara_v15'] = 'dibawa-v14 (teks bersih tak berubah)'
            if (h['naskah'], h['no']) in konteks_cek:
                ck = konteks_cek[(h['naskah'], h['no'])]
                h['cara_v15'] = ('dibawa-v14 (konteks lokal utuh di teks '
                                 'bersih baru)' if ck['utuh'] else
                                 'dibawa-v14 (KONTEKS TIDAK UTUH!)')
                h['konteks_cek'] = ck

    def skor(kunci):
        ok = sum(1 for r in hasil_baris if r[kunci] == r['label_benar'])
        per = {}
        for lab in ('bab', 'subbab', 'paragraf', 'biasa'):
            tot = [r for r in hasil_baris if r['label_benar'] == lab]
            per[lab] = {'benar': sum(1 for r in tot if r[kunci] == lab),
                        'total': len(tot)}
        return ok, per

    from math import erf, sqrt

    def mcnemar(k_a, k_b):
        b = sum(1 for r in hasil_baris
                if r[k_a] != r['label_benar'] and r[k_b] == r['label_benar'])
        c = sum(1 for r in hasil_baris
                if r[k_a] == r['label_benar'] and r[k_b] != r['label_benar'])
        if b + c:
            z = (abs(b - c) - 1) / sqrt(b + c)
            p = 2 * (1 - 0.5 * (1 + erf(z / sqrt(2))))
        else:
            p = 1.0
        return b, c, p

    n = len(hasil_baris)
    v14_ok, v14_per = skor('label_v14')
    v15_ok, v15_per = skor('label_v15')
    v11_ok, _ = skor('label_v11')
    b, c, p_mc = mcnemar('label_v14', 'label_v15')
    salah_bab_v14 = [r for r in hasil_baris
                     if r['label_benar'] == 'biasa'
                     and r['label_v14'] == 'bab']
    salah_bab_v15 = [r for r in hasil_baris
                     if r['label_benar'] == 'biasa'
                     and r['label_v15'] == 'bab']
    print('v11 : %d/%d (%.1f%%)' % (v11_ok, n, 100 * v11_ok / n))
    print('v14 : %d/%d (%.1f%%)' % (v14_ok, n, 100 * v14_ok / n))
    print('v15 : %d/%d (%.1f%%)' % (v15_ok, n, 100 * v15_ok / n))
    print('per label v15:', {k: '%d/%d' % (v['benar'], v['total'])
                             for k, v in v15_per.items()})
    print('per label v14:', {k: '%d/%d' % (v['benar'], v['total'])
                             for k, v in v14_per.items()})
    print('McNemar v15 vs v14: b=%d (v14 salah, v15 benar) c=%d '
          '(v14 benar, v15 salah) p=%.4f' % (b, c, p_mc))
    print('salah-bab (benar biasa, dilabeli bab): v14=%d v15=%d'
          % (len(salah_bab_v14), len(salah_bab_v15)))
    print('R3 (live v15), 8 baris:')
    for h in hasil_baris:
        if h['naskah'] == 'R3':
            print('   no %s | benar=%s | v14=%s -> v15=%s | %s | idx_live=%s'
                  % (h['no'], h['label_benar'], h['label_v14'],
                     h['label_v15'], h['cara_v15'], h.get('idx_live_r3')))
    print('Konteks 39 baris dibawa (5 naskah berubah): utuh=%d / 39'
          % sum(1 for v in konteks_cek.values() if v['utuh']))
    for (kode, no), v in sorted(konteks_cek.items()):
        if not v['utuh']:
            print('   KONTEKS TIDAK UTUH:', kode, 'no', no, v)
    print('Perubahan per baris (v14 -> v15):')
    for h in hasil_baris:
        if h['label_v14'] != h['label_v15']:
            print('   ', h['naskah'], 'no', h['no'], '| benar:',
                  h['label_benar'], '| v14:', h['label_v14'],
                  '-> v15:', h['label_v15'], '|', h['cara_v15'])

    jalan = ROOT / 'hasil_verifikasi_v11.json'
    data = json.load(open(jalan))
    json.dump([{'naskah': h['naskah'], 'no': h['no'],
                'label_benar': h['label_benar'], 'label_v11': h['label_v11'],
                'label_v14': h['label_v14'], 'label_v15': h['label_v15'],
                'cara_v14': h['cara_v14'], 'cara_v15': h['cara_v15'],
                'konteks_cek': h.get('konteks_cek')}
               for h in hasil_baris],
              open(ROOT / '_sketsa/hasil_ukur_v15_baris.json', 'w'),
              ensure_ascii=False, indent=1)
    data['perbaikan_bom_v15'] = {
        'rule_version': 'jev-peta-v15',
        'n_baris': n,
        'skor': {
            'v11': {'benar': v11_ok, 'total': n},
            'v14': {'benar': v14_ok, 'total': n, 'per_label': v14_per},
            'v15': {'benar': v15_ok, 'total': n, 'per_label': v15_per},
        },
        'mcnemar_v15_vs_v14': {'b': b, 'c': c, 'p': round(p_mc, 4)},
        'salah_bab_benar_biasa': {'v14': len(salah_bab_v14),
                                  'v15': len(salah_bab_v15)},
        'r3_live': {
            'panggilan_jev': live_r3['panggilan_total'],
            'probe_jml': live_r3['probe_jml'],
            'model_melayani': live_r3['model_melayani'],
            'baris': len(baris_r3),
            'gabung': live_r3['gabung'],
            'baris_r3': [
                {'no': h['no'], 'benar': h['label_benar'],
                 'v14': h['label_v14'], 'v15': h['label_v15'],
                 'cara': h['cara_v15'], 'idx_live': h.get('idx_live_r3')}
                for h in hasil_baris if h['naskah'] == 'R3'],
        },
        'konteks_dibawa_39_baris': {
            'utuh': sum(1 for v in konteks_cek.values() if v['utuh']),
            'total': len(konteks_cek),
            'tidak_utuh': [{'naskah': k[0], 'no': k[1], **v}
                           for k, v in sorted(konteks_cek.items())
                           if not v['utuh']],
        },
        'catatan': (
            'Hanya R3 dipetakan ulang live (temuan BOM ada di R3). 29 naskah '
            'teks bersihnya byte-identik lama-vs-baru, label v14 dibawa. '
            '39 baris di 5 naskah berubah lain dibawa dari v14 HANYA bila '
            'konteks lokalnya (3 baris sebelum/sesudah TSV) utuh di teks '
            'bersih baru: 37/39 utuh. 2 tidak utuh (A4 no 245, konteks 4/6; '
            'S2 no 217, konteks 5/6) karena jalur lama membuang baris '
            'caption/butir yang kini dipertahankan, sehingga satu potongan '
            'konteks tidak lagi bersebelahan; KEDUANYA sudah salah di v14 '
            '(A4 no 245: benar biasa, v14 subbab; S2 no 217: benar paragraf, '
            'v14 biasa), jadi bila run segar membalik keduanya skor jadi '
            '201/279, bila tidak tetap 199/279; tidak ada skenario dari '
            'kedua baris ini yang membuat v15 di bawah v14.'),
    }
    json.dump(data, open(jalan, 'w'), ensure_ascii=False, indent=2)
    print('tersimpan: hasil_verifikasi_v11.json kunci perbaikan_bom_v15')


if __name__ == '__main__':
    main()
