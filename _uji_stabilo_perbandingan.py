"""UJI: PERBAIKAN BUG STABILO di dalam generate_combined_pdf (SALINAN).

Tidak menyentuh script asli. Kita bajak fungsinya di memori:
  · generate_combined_pdf versi LAMA (asli)  → stabilo hilang
  · generate_combined_pdf versi BARU (spasi dinormalisasi) → stabilo muncul

Lalu bandingkan PDF keduanya dengan MATA (PNG).
"""
import html
import re
import sys
from pathlib import Path

sys.path.insert(0, '/opt/data/scripts')

import fitz
import similarity_precheck as S

OUT = Path('/tmp/uji_watermark')

TEKS = open('/tmp/uji_watermark/naskah_turnitin.txt', encoding='utf-8').read()


# ─────────────────────────────────────────────────────────────────
#  VERSI BARU: tidak pakai find() persis, tapi cari per-kata di naskah
# ─────────────────────────────────────────────────────────────────
def sisipkan_stabilo(escaped_text: str, hasil: dict):
    """Sisipkan <span class=hl> ke naskah. TAHAN baris-baru/spasi ganda."""
    turnitin_colors = [
        ("#ff0000", "#ffdddd"), ("#e70cd6", "#f8d8f8"), ("#8b05ff", "#eed8ff"),
        ("#00aaaa", "#d0f0f0"), ("#00aa00", "#d0f0d0"), ("#ab6f00", "#f8eed0"),
        ("#792e05", "#f0d8d0"), ("#054679", "#d0d8f0"), ("#993399", "#f0d8f0"),
        ("#4e7501", "#e8f0d0"), ("#231c9a", "#d0d0f0"),
    ]
    domain_to_num = {s["domain"]: i + 1 for i, s in enumerate(hasil["sources"])}

    #  Normalisasi spasi + PETA posisi asli
    keluar, peta = [], []
    i = 0
    while i < len(escaped_text):
        if escaped_text[i].isspace():
            keluar.append(' ')
            peta.append(i)
            while i < len(escaped_text) and escaped_text[i].isspace():
                i += 1
        else:
            keluar.append(escaped_text[i])
            peta.append(i)
            i += 1
    bersih = ''.join(keluar)

    matches = []
    for m in hasil.get("matched_sentences", []):
        chunk = m.get("chunk_full", m.get("chunk", ""))
        potong = re.sub(r'\s+', ' ', html.escape(chunk)).strip()
        pos_b = bersih.find(potong)
        if pos_b < 0:
            continue
        #  terjemahkan posisi di `bersih` → posisi di `escaped_text`
        a = peta[pos_b]
        akhir_b = pos_b + len(potong) - 1
        b_pos = peta[akhir_b] + (peta[akhir_b + 1] - peta[akhir_b]
                                 if akhir_b + 1 < len(peta) else 1)
        src = m["sources"][0] if m["sources"] else ""
        num = domain_to_num.get(src, 1)
        fg, bg = turnitin_colors[(num - 1) % len(turnitin_colors)]
        matches.append((a, b_pos, html.escape(chunk), num, fg, bg))

    matches.sort(key=lambda x: -x[0])
    for a, b_pos, chunk_esc, num, fg, bg in matches:
        ganti = (f'<span class="hl" style="background:{bg};">'
                 f'<span class="hl-num" style="background:{fg};">{num}</span>'
                 f'{chunk_esc}</span>')
        escaped_text = escaped_text[:a] + ganti + escaped_text[b_pos:]

    return escaped_text, len(matches)


if __name__ == '__main__':
    hasil = S.check_similarity(TEKS, mock_mode=True)
    print(f"  similarity={hasil['similarity_index']}% · "
          f"stabilo={len(hasil['matched_sentences'])}")

    doc_title = 'BAB 2 Identifikasi Masalah, Tujuan, dan Perumusan Riset Pemasaran'

    #  (1) PDF versi ASLI
    asli = OUT / 'bug_asli.pdf'
    S.generate_combined_pdf(TEKS, hasil, str(asli), doc_title)
    a = fitz.open(str(asli))
    ada_asli = sum(1 for p in a if '<span class="hl"' in ''
                   )  # placeholder

    #  (2) Cek berapa stabilo masuk ke HTML asli
    import inspect
    src = inspect.getsource(S.generate_combined_pdf)
    esc = html.escape(TEKS)
    masuk = 0
    for m in hasil['matched_sentences']:
        if esc.find(html.escape(m['chunk_full'])) >= 0:
            masuk += 1
    print(f"  ASLI  : {masuk}/{len(hasil['matched_sentences'])} stabilo masuk")

    #  (3) PDF versi PERBAIKAN — bajak di memori
    teks_baru, jumlah = sisipkan_stabilo(html.escape(TEKS), hasil)
    print(f"  BARU  : {jumlah}/{len(hasil['matched_sentences'])} stabilo masuk")
