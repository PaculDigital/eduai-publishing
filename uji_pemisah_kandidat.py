"""UJI D — PEMISAH TEGAS antar-kandidat (usul Wulan, ACC Bos "D").

Masalah (terukur): c00 sendirian = 0,71 STABIL; begitu ada kandidat lain
→ jatuh ~0,52 dan goyang. Bukan karena isi kandidat (bahkan judul asli lain
ikut menularkan) ⇒ perhatian Jev terbagi.

Uji 4 bentuk bahan (1 panggilan masing-masing), semuanya 5 kandidat:
   P0  polos (kontrol)                — seperti sekarang
   P1  penanda bernomor tegas         — "== KANDIDAT 1 dari 5 =="
   P2  blok terpagar (--- garis ---)  — tiap kandidat dipagari
   P3  satu kandidat per BARIS SEJAJAR (tanpa header terpisah)

Ukur: c00 (L008050, JUDUL ASLI) harus naik mendekati 0,71.
"""
from __future__ import annotations

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

PENULAR = ['2020', '(Khoironi, 2023)', '2. Wawancara', '6 Sidang Skripsi']


def main() -> int:
    b = P.susun(115)['baris']

    def ix_(isi: str):
        h = [j for j, s in enumerate(b) if isi.strip() in s.strip()]
        return h[0] if h else None

    iJ = ix_('3. Tinjauan Literatur')
    print(f'c00 (judul asli) = L{iJ:06d}')

    def jendela(ix: int) -> list[str]:
        return [f'L{j:06d}| {b[j][:78]}'
                for j in range(max(0, ix - 2), min(len(b), ix + 3))]

    kand = [iJ] + [ix_(p) for p in PENULAR if ix_(p)]

    #  ── 4 bentuk bahan ────────────────────────────────────────────────
    def bahan_p0():
        out = []
        for n, ix in enumerate(kand):
            out.append(f'#### k{n:02d}')
            out.extend(jendela(ix))
        return '\n'.join(out)

    def bahan_p1():
        out = []
        for n, ix in enumerate(kand):
            out.append(f'== KANDIDAT {n + 1} dari {len(kand)} ==')
            out.append('')
            out.extend(jendela(ix))
            out.append('')
        return '\n'.join(out)

    def bahan_p2():
        out = []
        for n, ix in enumerate(kand):
            out.append('-----------------------')
            out.extend(jendela(ix))
            out.append('-----------------------')
        return '\n'.join(out)

    def bahan_p3():
        out = []
        for n, ix in enumerate(kand):
            out.extend(jendela(ix))
            out.append('')                       # satu baris kosong saja
        return '\n'.join(out)

    BENTUK = {'P0_polos': bahan_p0, 'P1_bernomor': bahan_p1,
              'P2_terpagar': bahan_p2, 'P3_kosong': bahan_p3}

    for nama, fn in BENTUK.items():
        Q = {}
        for n in range(len(kand)):
            nm = f'k{n:02d}'
            Q[nm] = {
                'type': 'noul',
                'instructions': (f'Apakah baris TENGAH untuk {nm} di atas '
                                 'adalah KEPALA BAGIAN (judul) naskah?'),
                'criteria': K5,
            }
        skor = []
        for ulang in range(3):
            jaw = jev.tanya(fn(), Q) or {}
            x = (jaw.get('k00') or {}).get('noul')
            skor.append(x)
        va = [s for s in skor if s is not None]
        rata = (sum(va) / len(va)) if va else None
        print(f'   {nama:<12} k00 = '
              + ' '.join(f'{s:.2f}' if s is not None else '?' for s in skor)
              + (f'   rata={rata:.2f}' if rata is not None else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main())
