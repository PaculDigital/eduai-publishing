"""PERBAIKI rakit_presisi(): gambar ditaruh DI TENGAH blok ganti.

ARAHAN BOS (verbatim 26Sep26):
   "Harusnya, yang benar gambar bukan di akhir. Tetapi tamplate nya:
      paragraf pembuka
      Grafik
      Paragraf keterangan grafik"

🔴 AKAR MASALAH (terukur 26Sep26):
   `rakit_presisi()` mengganti 1 paragraf dengan N paragraf dari `e.ganti`
   (dipisah '\\n'). Sementara gambar disisipkan OLEH FUNGSI LAIN (`sisip_*`)
   di tempat lain (akhir bagian / akhir dokumen). ⇒ Hasilnya gambar TIDAK
   pernah berada di antara pembuka & keterangan.

FIX (tanpa aturan baru — CUKUP di paragraf target):
   `rakit_presisi` menerima `gambar_di`: dict {nomor: png_bytes}. Kalau
   paragraf yang diganti berkaitan dengan gambar itu → paragraf gambar
   Word ditaruh TEPAT di antara baris pembuka & baris keterangan.

   Penanda gambar di dalam `e.ganti` dipasang oleh `ai.py` dengan penanda
   baris tunggal: `[[GAMBAR-PNG-n]]` (n = urutan gambar). Baris penanda itu
   TIDAK ditulis sebagai teks — diganti menjadi paragraf gambar.
"""
import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/app/tulis_docx.py')
s = P.read_text()

#  ── 1. terima parameter baru `gambar_di` ──
lama_tt = """def rakit_presisi(
    xml: str,
    editan: list,
    semua_paragraf: list[str],
) -> tuple[str, dict]:"""
baru_tt = """def rakit_presisi(
    xml: str,
    editan: list,
    semua_paragraf: list[str],
    gambar_di: dict | None = None,
) -> tuple[str, dict]:"""
assert lama_tt in s, 'tanda tangan rakit_presisi tak ketemu'
s = s.replace(lama_tt, baru_tt, 1)

#  ── 2. baris penanda gambar → paragraf gambar Word ──
lama_baris = """        #  GANTI-JADI bisa berisi BEBERAPA baris → beberapa paragraf Word.
        baris = [b for b in (e.ganti or '').split('\\n')]
        while baris and not baris[-1].strip():
            baris.pop()
        if not baris:
            tak_ketemu.append(e.nomor)
            continue
        isi_baru = ''.join(
            _par_baru(b.strip(), pPr, rPr) for b in baris if b.strip())
        if not isi_baru:
            tak_ketemu.append(e.nomor)
            continue"""
baru_baris = """        #  GANTI-JADI bisa berisi BEBERAPA baris → beberapa paragraf Word.
        baris = [b for b in (e.ganti or '').split('\\n')]
        while baris and not baris[-1].strip():
            baris.pop()
        if not baris:
            tak_ketemu.append(e.nomor)
            continue
        #  🆕 26Sep26 (arahan Bos): baris penanda `[[GAMBAR-PNG-n]]` TIDAK
        #     ditulis sebagai teks — diganti paragraf GAMBAR Word, sehingga
        #     urutannya: pembuka → GRAFIK → keterangan (di dalam bagian yang
        #     diganti, BUKAN di akhir dokumen).
        _peta_gambar = gambar_di or {}
        _potong: list[str] = []
        for b in baris:
            _m = re.match(r'^\\s*\\[\\[GAMBAR-PNG-(\\d+)\\]\\]\\s*$', b)
            if _m and int(_m.group(1)) in _peta_gambar:
                _png = _peta_gambar[int(_m.group(1))]
                _par_gbr = _par_gambar_word(_png, _peta_gambar.get('_rel',
                                                                   ''))
                if _par_gbr:
                    _potong.append(_par_gbr)
                continue
            if b.strip():
                _potong.append(_par_baru(b.strip(), pPr, rPr))
        isi_baru = ''.join(_potong)
        if not isi_baru:
            tak_ketemu.append(e.nomor)
            continue"""
assert lama_baris in s, 'blok baris rakit_presisi tak ketemu'
s = s.replace(lama_baris, baru_baris, 1)

P.write_text(s)
print('✅ rakit_presisi menerima `gambar_di` + baris [[GAMBAR-PNG-n]]')
