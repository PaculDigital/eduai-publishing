"""Uji prompt agen kedua v14 (BARU) live — diagnostik, bukan jalur produksi.

Memanggil agen kedua (Gemini 2.5 Flash PINNED via OpenRouter langsung)
dengan prompt v14 yang tajam pada 63 baris:
  * 42 baris salah-bab v11 (benarnya `biasa`, dilabeli `bab`) — prompt baru
    harus menjawab `biasa`,
  * 21 baris benar-bab (benarnya `bab`) — prompt baru TIDAK boleh menjawab
    `biasa` untuk bab asli (cek negatif palsu).
Konteks dibangun seperti wiring Lapis 2 live (3 baris sebelum/sesudah +
judul bab terdekat dari gabung/label). Suara Jev TIDAK ditunjukkan ke agen
(jawaban independen, seperti produksi).

Pembanding prompt LAMA: hanya 3 baris bab yang ditandai Hakim di v13 dan
dijawab agen (hasil_rantai_gating.json): 1/3 benar. Denominator berbeda —
dilaporkan apa adanya, bukan sebagai head-to-head setara.

Jalankan:  python3 _sketsa/uji_prompt_v14.py
Keluaran: _verifikasi_v11/hasil_prompt_v14.json (per baris) + ringkasan
ke stdout + sub-kunci 'uji_prompt' di hasil_verifikasi_v11.json.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_sketsa'))

import app.agen_kedua as AK
from agen_kedua_openrouter import buat_penanya


def norm(s):
    return ' '.join(str(s or '').split())


def cocok_konteks(baris, idx, sebelum, sesudah):
    def pot(s):
        return [norm(x) for x in (s or '').split('|') if norm(x)]
    sk = 0
    for p, arah in ((pot(sebelum), -1), (pot(sesudah), +1)):
        if not p:
            continue
        tet = []
        k = idx + arah
        while 0 <= k < len(baris) and len(tet) < 3:
            if norm(baris[k]):
                tet.append(norm(baris[k]))
            k += arah
        for x in p:
            if any(t == x or t.startswith(x) or x.startswith(t)
                   for t in tet):
                sk += 1
    return sk


def main():
    peta = json.load(open(ROOT / '_sketsa/peta35_tersimpan.json'))
    pem = json.load(open(ROOT / '_sketsa/pemetaan_tsv_baris.json'))
    gating = json.load(open(ROOT / '_verifikasi_v11/hasil_rantai_gating.json'))
    tsv = list(csv.DictReader(
        open(ROOT / 'ground_truth/ground_truth_uji112.tsv'), delimiter='\t'))
    tsv_map = {(r['naskah'], r['no']): r for r in tsv}

    dipilih = []
    for g in gating['baris']:
        if g['label_benar'] == 'biasa' and g['label_v11'] == 'bab':
            dipilih.append((g, 'salah-bab'))
        elif g['label_benar'] == 'bab':
            dipilih.append((g, 'benar-bab'))
    print('baris dipilih: %d (salah-bab %d, benar-bab %d)'
          % (len(dipilih),
             sum(1 for _, k in dipilih if k == 'salah-bab'),
             sum(1 for _, k in dipilih if k == 'benar-bab')), flush=True)

    penanya = buat_penanya()
    hasil = []
    for g, kelompok in dipilih:
        kode, no = g['naskah'], g['no']
        e = peta[kode]
        baris = e['baris']
        label_penuh = {int(k): v for k, v in (e.get('label_penuh') or {}).items()}
        gabung = {int(k): tuple(v) for k, v in e['gabung_penuh'].items()}
        if g['idx_peta'] is not None:
            idx = g['idx_peta']
        else:
            r = tsv_map[(kode, no)]
            p = pem.get(kode + '|' + no, {})
            kandidat = p.get('kandidat') or []
            if len(kandidat) == 1:
                idx = kandidat[0]
            elif kandidat:
                skor = [(cocok_konteks(baris, j, r['konteks_sebelum'],
                                       r['konteks_sesudah']), j)
                        for j in kandidat]
                skor.sort(reverse=True)
                idx = skor[0][1]
            else:
                idx = None
        if idx is None:
            print('  LEWATI %s no %s (tanpa idx)' % (kode, no), flush=True)
            continue
        sebelum = [baris[k] for k in range(max(0, idx - 3), idx)]
        sesudah = [baris[k]
                   for k in range(idx + 1, min(len(baris), idx + 4))]
        judul = None
        for k in range(idx - 1, -1, -1):
            if k in gabung:
                judul = ' '.join(gabung[k]).strip()
                break
            if label_penuh.get(k) == 'bab':
                judul = baris[k]
                break
        konteks = {'sebelum': sebelum, 'sesudah': sesudah,
                   'judul_bab_terdekat': judul}
        t0 = time.time()
        jawab = AK.tanya_agen_kedua(g['teks_baris'], konteks,
                                    penanya=penanya)
        dt = round(time.time() - t0, 2)
        benar = bool(jawab) and jawab['label'] == g['label_benar']
        hasil.append({
            'naskah': kode, 'no': no, 'kelompok': kelompok,
            'teks': g['teks_baris'], 'label_benar': g['label_benar'],
            'idx': idx, 'label_v11': g['label_v11'],
            'jawaban_prompt_baru': jawab, 'benar': benar,
            'detik': dt,
        })
        print('  %s no %s [%s] benar=%s -> %s (%.1f dtk)'
              % (kode, no, kelompok, g['label_benar'],
                 (jawab or {}).get('label'), dt), flush=True)

    salah = [h for h in hasil if h['kelompok'] == 'salah-bab']
    benar_bab = [h for h in hasil if h['kelompok'] == 'benar-bab']
    ok_salah = sum(1 for h in salah if h['benar'])
    ok_benar = sum(1 for h in benar_bab if h['benar'])
    gagal = [h for h in hasil if h['jawaban_prompt_baru'] is None]
    print('\nHASIL PROMPT BARU v14:')
    print('  salah-bab (jawab biasa): %d/%d' % (ok_salah, len(salah)))
    print('  benar-bab (jawab bab): %d/%d' % (ok_benar, len(benar_bab)))
    print('  total: %d/%d' % (ok_salah + ok_benar, len(hasil)))
    print('  gagal (None): %d' % len(gagal))
    print('  jawaban salah pada salah-bab:')
    for h in salah:
        if not h['benar']:
            print('    ', h['naskah'], 'no', h['no'], '|',
                  repr(h['teks'][:55]), '->',
                  (h['jawaban_prompt_baru'] or {}).get('label'))
    print('  jawaban salah pada benar-bab:')
    for h in benar_bab:
        if not h['benar']:
            print('    ', h['naskah'], 'no', h['no'], '|',
                  repr(h['teks'][:55]), '->',
                  (h['jawaban_prompt_baru'] or {}).get('label'))

    out = ROOT / '_verifikasi_v11/hasil_prompt_v14.json'
    json.dump({'model': 'google/gemini-2.5-flash',
               'transport': 'openrouter',
               'prompt': 'v14 (ATURAN_BAB_TAJAM)',
               'n': len(hasil),
               'salah_bab_benar': ok_salah, 'salah_bab_total': len(salah),
               'benar_bab_benar': ok_benar, 'benar_bab_total': len(benar_bab),
               'gagal_none': len(gagal),
               'baris': hasil}, open(out, 'w'), ensure_ascii=False, indent=1)
    print('tersimpan:', out)

    jalan = ROOT / 'hasil_verifikasi_v11.json'
    data = json.load(open(jalan))
    data.setdefault('perbaikan_bab_v14', {})['uji_prompt'] = {
        'model': 'google/gemini-2.5-flash', 'transport': 'openrouter',
        'prompt': 'v14 (ATURAN_BAB_TAJAM)',
        'salah_bab': {'benar': ok_salah, 'total': len(salah)},
        'benar_bab': {'benar': ok_benar, 'total': len(benar_bab)},
        'gagal_none': len(gagal),
        'pembanding_prompt_lama': {
            'catatan': ('hanya 3 baris bab yang ditandai Hakim di v13 dan '
                        'dijawab agen: 1/3 benar (AL-2 no 92 paragraf, '
                        'O3 no 101 biasa [benar], P2 no 109 subbab); '
                        'denominator berbeda, bukan head-to-head setara.'),
            'benar': 1, 'total': 3},
    }
    json.dump(data, open(jalan, 'w'), ensure_ascii=False, indent=2)
    print('ringkasan tersimpan di hasil_verifikasi_v11.json '
          'kunci perbaikan_bab_v14.uji_prompt')


if __name__ == '__main__':
    main()
