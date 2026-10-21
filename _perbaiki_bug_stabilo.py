"""PERBAIKAN BUG STABILO pada generate_combined_pdf (script Bos).

BUG TERUKUR (bukan tebakan):
  `generate_combined_pdf` mencari `chunk` di dalam naskah dengan
  `escaped_text.find(chunk_esc)`. TAPI `chunk` diambil dari KALIMAT
  yang dibersihkan (`' '.join(...)`) → TIDAK SAMA dengan naskah asli
  yang punya baris baru (`\n`). Akibat: find() = -1 → stabilo HILANG.

BUKTI: 9 stabilo → hanya 4 yang ketemu (5 HILANG).

OBAT: cari dengan NORMALISASI SPASI — bukan `find()` persis.
  (a) Normalisasi naskah: `\s+` → spasi tunggal, sambil SIMPAN peta
      posisi agar penggantian tetap di tempat yang benar.
  (b) Atau cari chunk per-KATA di naskah (tahan baris baru).

Cara (b) dipakai di sini: cari kata pertama chunk, lalu pastikan
potongan berikutnya cocok — toleran terhadap `\n` dan spasi ganda.
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, '/opt/data/scripts')


def normalisasi_dengan_peta(teks: str):
    """Ganti semua rentetan spasi jadi 1 spasi, kembalikan teks + peta posisi."""
    keluar = []
    peta = []          # peta[i] = indeks asli untuk tiap huruf di `keluar`
    i = 0
    while i < len(teks):
        if teks[i].isspace():
            keluar.append(' ')
            peta.append(i)
            while i < len(teks) and teks[i].isspace():
                i += 1
        else:
            keluar.append(teks[i])
            peta.append(i)
            i += 1
    return ''.join(keluar), peta


def cari_chunk(teks_bersih: str, chunk: str):
    """Cari chunk dengan spasi dinormalisasi. Kembalikan (awal, akhir) di
    `teks_bersih`, atau None."""
    potong = re.sub(r'\s+', ' ', chunk).strip()
    pos = teks_bersih.find(potong)
    if pos < 0:
        return None
    return pos, pos + len(potong)


if __name__ == '__main__':
    import fitz
    import similarity_precheck as S

    teks = open('/tmp/uji_watermark/naskah_turnitin.txt', encoding='utf-8').read()
    hasil = S.check_similarity(teks, mock_mode=True)

    esc = html.escape(teks)
    bersih, peta = normalisasi_dengan_peta(esc)

    print(f"  similarity = {hasil['similarity_index']}% · "
          f"stabilo = {len(hasil['matched_sentences'])}")
    print()
    print("  ── CARA LAMA (find persis) vs CARA BARU (spasi dinormalisasi) ──")
    lama_ok = baru_ok = 0
    for m in hasil['matched_sentences']:
        c = html.escape(m['chunk_full'])
        pos_lama = esc.find(c)
        hasil_baru = cari_chunk(bersih, m['chunk_full'])
        lama_ok += pos_lama >= 0
        baru_ok += hasil_baru is not None
        print(f"   lama={'ADA    ' if pos_lama>=0 else 'HILANG '} "
              f"baru={'ADA' if hasil_baru else 'HILANG'}  | {m['chunk_full'][:50]}")

    n = len(hasil['matched_sentences'])
    print()
    print(f"  HASIL: LAMA {lama_ok}/{n} muncul · BARU {baru_ok}/{n} muncul")
