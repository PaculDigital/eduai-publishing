"""Adjudikasi agen kedua (prompt v14) untuk baris R3 yang ditandai Hakim
di run live v15 — hanya baris yang relevan dengan 8 baris TSV R3.

Yang diadili: idx 66 'terdiri dari : Kesimpulan dan Saran.' (R3 no 8) —
satu-satunya baris TSV R3 yang masuk rekaman Hakim. Label live Jev
'biasa'; bila agen sepakat, label 'biasa' dipakai; bila beda (bukan
soal judul bab), keputusan agen dipakai; bila beda soal judul bab,
antrean manusia. 7 baris TSV R3 lainnya tidak ditandai Hakim, jadi
label live dipakai apa adanya (tidak diadili, hemat panggilan).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / '_sketsa'))

import app.agen_kedua as AK
from agen_kedua_openrouter import buat_penanya

TARGET = (66,)


def main():
    r3 = json.load(open(ROOT / '_verifikasi_v11/hasil_gating_r3.json'))
    lab = {int(k): v for k, v in r3['label'].items()}
    rek = {r['idx']: r for r in r3['rekaman']}
    penanya = buat_penanya()
    out = []
    for idx in TARGET:
        r = rek[idx]
        jawab = AK.tanya_agen_kedua(r['teks'], r['konteks'],
                                    penanya=penanya)
        jev = lab.get(idx, 'biasa')
        if jawab is None:
            putusan, akhir = 'antrean-manusia (agen gagal)', jev
        elif jawab['label'] == jev:
            putusan, akhir = 'sepakat (label Jev dipakai)', jev
        elif jev == 'bab' or jawab['label'] == 'bab':
            putusan, akhir = 'antrean-manusia (beda soal judul bab)', jev
        else:
            putusan, akhir = 'keputusan agen dipakai', jawab['label']
        print('idx %d | Jev=%s | agen=%s | %s -> label akhir %s'
              % (idx, jev, (jawab or {}).get('label'), putusan, akhir))
        print('   alasan agen:', (jawab or {}).get('alasan'))
        out.append({'idx': idx, 'teks': r['teks'], 'label_jev_live': jev,
                    'jawaban_agen': jawab, 'putusan': putusan,
                    'label_akhir': akhir})
    r3['adjudikasi_v15'] = out
    json.dump(r3, open(ROOT / '_verifikasi_v11/hasil_gating_r3.json', 'w'),
              ensure_ascii=False, indent=1)
    print('tersimpan di hasil_gating_r3.json kunci adjudikasi_v15')


if __name__ == '__main__':
    main()
