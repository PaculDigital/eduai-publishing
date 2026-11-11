"""Arm B pilot rantai 3 langkah — agen kedua (OpenRouter, Gemini 2.5 Flash)
pada 16 baris BERLABEL manusia yang ditandai Hakim (ragu/curiga).

Jalankan dari VM (bukan container): memakai penanya OpenRouter langsung
(_sketsa/agen_kedua_openrouter.py) + app.agen_kedua. NOL panggilan Jev.

Label v11 tiap baris diverifikasi dari hasil latih tersimpan: kandidat
judul Hakim berarti label v11 'bab' ATAU 'subbab' (LABEL_JUDUL Hakim);
'bab' bila teksnya cocok dengan bab_label/bab_gabung naskah itu, selainnya
'subbab'. Bila tidak terkonfirmasi, dicatat 'tidak-terkonfirmasi'.

Konteks Arm B: konteks_sebelum/sesudah dari TSV saja (judul bab terdekat
TIDAK tersedia di TSV — dicatat jujur; rantai live punya judul terdekat
dari wiring Lapis 2).

Keluaran: _verifikasi_v11/hasil_rantai3_armb.json
"""
import csv
import json
import re
import sys
from collections import Counter

sys.path.insert(0, '.')
sys.path.insert(0, '_sketsa')

from app import agen_kedua as AK
from agen_kedua_openrouter import buat_penanya

NO_SAMPEL = [8, 49, 86, 129, 158, 174, 193, 210, 219, 241,
             15, 28, 50, 108, 118, 157]


def _norm(s):
    return re.sub(r'\s+', ' ', (s or '').replace('\ufeff', '').strip())


def _label_v11(naskah, teks, bab):
    t = _norm(teks)
    for b in bab.get(naskah, []):
        if t and (t in b or b in t):
            return 'bab'
    return 'subbab'


def utama():
    rows = list(csv.DictReader(
        open('ground_truth/ground_truth_latih112.tsv'), delimiter='\t'))
    # bab_label + bab_gabung per naskah (hasil latih tersimpan)
    bab = {}
    for g in (1, 2, 3, 4):
        d = json.load(open('hasil_latih_grup%d.json' % g))
        for e in d['entri']:
            lst = [re.sub(r'\s+', ' ', str(x)).strip()
                   for x in (e.get('bab_label') or [])]
            for v in (e.get('bab_gabung') or []):
                lst.append(re.sub(r'\s+', ' ', ' '.join(v)).strip())
            bab[e['kode']] = lst
    sampel = [r for r in rows if int(r['no']) in NO_SAMPEL]
    assert len(sampel) == len(NO_SAMPEL), len(sampel)
    penanya = buat_penanya()
    print('model agen kedua:', penanya.model, flush=True)
    hasil = {'arm': 'B (baris ditandai Hakim, agen kedua OpenRouter)',
             'model_agen_kedua': penanya.model,
             'transport': 'openrouter',
             'catatan_konteks': ('konteks TSV saja (sebelum/sesudah); judul '
                                'bab terdekat TIDAK tersedia di TSV'),
             'entri': []}
    total_kar = 0
    for r in sampel:
        ctx = {'sebelum': [b for b in r['konteks_sebelum'].split(' | ')
                           if b.strip()],
               'sesudah': [b for b in r['konteks_sesudah'].split(' | ')
                           if b.strip()],
               'judul_bab_terdekat': None}
        total_kar += len(r['teks_baris']) + len(r['konteks_sebelum']) \
            + len(r['konteks_sesudah'])
        j = AK.tanya_agen_kedua(r['teks_baris'], ctx, penanya=penanya)
        v11 = _label_v11(r['naskah'], r['teks_baris'], bab)
        ent = {'no': int(r['no']), 'jenis_sengketa': r['jenis_sengketa'],
               'naskah': r['naskah'], 'teks_baris': r['teks_baris'],
               'label_benar': r['label_benar'], 'label_v11': v11,
               'label_kedua': j['label'] if j else None,
               'confidence_kedua': j['confidence'] if j else None,
               'alasan_kedua': j['alasan'] if j else '',
               'model_kedua': j['model'] if j else '',
               'v11_benar': v11 == r['label_benar'],
               'kedua_benar': (j['label'] == r['label_benar']) if j else False,
               'kedua_gagal': j is None}
        hasil['entri'].append(ent)
        print('%s %s | benar=%s v11=%s kedua=%s (%.2f)'
              % (r['no'], r['naskah'], r['label_benar'], v11,
                 ent['label_kedua'],
                 ent['confidence_kedua'] or 0), flush=True)
    n = len(hasil['entri'])
    hasil['ringkas'] = {
        'n': n,
        'v11_benar': sum(e['v11_benar'] for e in hasil['entri']),
        'kedua_benar': sum(e['kedua_benar'] for e in hasil['entri']),
        'kedua_gagal': sum(e['kedua_gagal'] for e in hasil['entri']),
        'per_label_benar': {k: {'n': v, 'kedua_benar': sum(
            e['kedua_benar'] for e in hasil['entri']
            if e['label_benar'] == k)}
            for k, v in Counter(e['label_benar']
                                for e in hasil['entri']).items()},
    }
    # Biaya: jembatan tidak mengembalikan token; perkiraan lokal chars/4.
    hasil['perkiraan_biaya'] = {
        'metode': 'chars/4 (batas atas), $0,30/1 juta masuk, '
                  '$2,50/1 juta keluar, kurs Rp18.100/USD',
        'kar_total_prompt': total_kar,
        'token_masuk_perkiraan': round(total_kar / 4),
    }
    json.dump(hasil, open('_verifikasi_v11/hasil_rantai3_armb.json', 'w'),
              ensure_ascii=False, indent=2)
    print('RINGKAS: v11 %d/%d benar, agen kedua %d/%d benar, gagal %d'
          % (hasil['ringkas']['v11_benar'], n,
             hasil['ringkas']['kedua_benar'], n,
             hasil['ringkas']['kedua_gagal']), flush=True)


if __name__ == '__main__':
    utama()
