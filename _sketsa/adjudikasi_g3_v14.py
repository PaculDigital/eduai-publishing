"""Adjudikasi agen kedua (prompt v14) untuk baris RELEVAN v14 dari run
live G3 — hanya 2 baris, bukan seluruh 40 rekaman.

Yang diadili:
  * idx 193 'd. Mengenali Emosi Orang Lain' (G3 no 255) — kasus ATURAN 5:
    Jev live 'subbab' (suara [paragraf, subbab]). Bila agen sepakat,
    label 'subbab' dipakai; bila beda (bukan soal judul bab), keputusan
    agen yang dipakai; bila beda soal judul bab, antrean manusia.
  * idx 60 'Berisi tentang pembahasan...' — satu-satunya baris wilayah
    sistematika (46-60) yang ditandai Hakim; label live 'paragraf'.

38 baris rekaman lain adalah baris gating v13 biasa (perilaku v13 sudah
diukur di 279 baris; tidak diadili ulang agar hemat panggilan).
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

TARGET = (193, 60)


def main():
    g3 = json.load(open(ROOT / '_verifikasi_v11/hasil_gating_g3.json'))
    lab = {int(k): v for k, v in g3['label'].items()}
    rek = {r['idx']: r for r in g3['rekaman']}
    penanya = buat_penanya()
    out = []
    for idx in TARGET:
        r = rek[idx]
        jawab = AK.tanya_agen_kedua(r['teks'], r['konteks'],
                                    penanya=penanya)
        jev = lab.get(idx)
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
    g3['adjudikasi_v14'] = out
    json.dump(g3, open(ROOT / '_verifikasi_v11/hasil_gating_g3.json', 'w'),
              ensure_ascii=False, indent=1)
    print('tersimpan di hasil_gating_g3.json kunci adjudikasi_v14')


if __name__ == '__main__':
    main()
