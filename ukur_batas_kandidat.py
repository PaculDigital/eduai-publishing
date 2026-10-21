"""UKUR BATAS AMAN — berapa kandidat BERBEDA per panggilan sebelum Jev turun?

Vonis Bos: "B — ukur batas aman (5, 6, 7 kandidat; 3 panggilan murah)"

Sudah terukur (TEMUAN_KEKABURAN_MENULAR):
   1 → 0,70 · 2 → 0,69 · 4 → 0,65 · 8 → 0,50 · 16 → 0,49
⇒ antara 4 dan 8 ada tempat jatuh. Ukur 5, 6, 7.

CARA: satu penanda (c00) SELALU = L008050 ('3. Tinjauan Literatur', JUDUL ASLI).
Sisanya kandidat lain (butir/pecahan nyata) mengisi sampai N.
Ukur 3× per N supaya tidak salah baca getaran sesaat (aturan: uji Jev rapuh).
"""
from __future__ import annotations

import json
import sys

sys.path.insert(0, '/app')

from app import jev                                       # noqa: E402
import peta3_jev as P                                     # noqa: E402

K5 = {
    'true': ('Baris adalah JUDUL BAGIAN dari kerangka naskah. Ciri: berisi nama '
             'topik bahasan (bukan nama kegiatan/langkah), nomornya menandai '
             'kedudukan bagian dalam kerangka tulisan seperti 2.1 atau BAB II '
             'atau nomor polos tanpa titik yang sejajar dengan judul bab lain '
             'di dokumen ini, dan baris berikutnya mulai dengan paragraf '
             'penjelasan baru.'),
    'false': ('Baris adalah SATU LANGKAH KEGIATAN atau SATU BUTIR dari sebuah '
              'daftar cara kerja, atau bagian lain yang bukan kepala tulisan: '
              'deret angka di dalam tabel, sel dan kolom, keterangan bernama '
              'di atas tabel atau gambar, potongan kutipan wawancara, nama '
              'sumber, atau sambungan kalimat sebelumnya yang belum selesai.'),
}

#  c00 SELALU judul asli; sisanya kandidat lain (butir/pecahan nyata dari naskah)
LAIN = [
    '2020',                                       # angka
    '(Khoironi, 2023)',                           # sitasi
    '2. Wawancara',                               # butir kegiatan
    '6 Sidang Skripsi',                           # butir kegiatan
    'Threats (Decision-Making Theory).',          # fragmen
    'Hijab yang menjadi trend',                   # butir lanjutan
    'Kekuatan (Strength)',                        # kepala kuadran tabel
    'Kategori Hasil Kutipan Informan',            # header tabel
    '1. Informan (Ulan – Pengelola AyuMeera)',    # butir punya anak
    '3. Informan (Anie – Div. Chemical)',
    '4. Informan (April – Konsumen)',
    'Tabel 4. 1 Tabel Analisis SWOT Hijab Tape AyuMeera',
    '(David, 2010) dalam (Andika, 2020).',
    '4. Threats (Ancaman)',
    '2. Informan (Regina – Div. AyuMeera)',
]

UKUR = (5, 6, 7, 8)          # 4 & 8 sudah ada; 5-7 = yang diminta Bos


def main() -> int:
    b = P.susun(115)['baris']

    def idx_(isi: str):
        hit = [j for j, s in enumerate(b) if isi.strip() in s.strip()]
        return hit[0] if hit else None

    i_judul = idx_('3. Tinjauan Literatur')
    print(f'c00 (judul asli) = L{i_judul:06d}')
    if i_judul is None:
        print('❌ judul tidak ketemu — batal')
        return 1

    def jendela(ix: int) -> str:
        return '\n'.join(f'L{j:06d}| {b[j][:78]}'
                         for j in range(max(0, ix - 2), min(len(b), ix + 3)))

    hasil = {}
    for N in UKUR:
        skor = []
        for ulang in range(3):
            kandidat = [i_judul]
            for nm in LAIN:
                if len(kandidat) >= N:
                    break
                j = idx_(nm)
                if j is not None and j != i_judul:
                    kandidat.append(j)
            Q, potong = {}, []
            for n, ix in enumerate(kandidat):
                nm = f'k{n:02d}'
                Q[nm] = {
                    'type': 'noul',
                    'instructions': (f'Apakah baris TENGAH untuk {nm} di atas '
                                     'adalah KEPALA BAGIAN (judul) naskah?'),
                    'criteria': K5,
                }
                potong.append(f'#### {nm}')
                potong.append(jendela(ix))
            jaw = jev.tanya('\n'.join(potong), Q) or {}
            x = (jaw.get('k00') or {}).get('noul')
            skor.append(x)
        valid = [s for s in skor if s is not None]
        hasil[N] = skor
        rata = (sum(valid) / len(valid)) if valid else None
        tanda = '' if rata is None else ('  ✅ judul' if rata >= 0.60
                                         else '  ⚠️ RAGU' if rata >= 0.30
                                         else '  ❌ CURIGA (didemosi)')
        print(f'   {N:2d} kandidat → {["%.2f" % s if s is not None else "?" for s in skor]}'
              f'  rata={rata:.2f}{tanda}' if rata is not None
              else f'   {N:2d} kandidat → tidak ada jawaban')

    json.dump({'hasil': hasil, 'i_judul': i_judul},
              open('/app/HASIL_BATAS_KANDIDAT.md.json', 'w'), ensure_ascii=False, indent=1)
    return 0


if __name__ == '__main__':
    sys.exit(main())
