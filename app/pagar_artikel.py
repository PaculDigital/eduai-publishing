"""PAGAR ARTIKEL — anti-halusinasi saat AI menulis dari artikel (06 Okt 2026).

KENAPA ADA (jawaban pertanyaan Bos, verbatim):
    "saya bingung bagaimana jika berkas tidak bisa diunduh, script/bot bisa
     tahu isinya tanpa halusinasi?"

JAWABAN: mesin tahu isi dari **ABSTRAK** (ringkasan yang ditulis penulis
artikelnya sendiri — data NYATA, bukan tebakan). Tapi abstrak saja tidak
cukup: AI tetap bisa mengarang di luar abstrak. ⇒ 3 PAGAR:

  PAGAR 1 — HANYA YANG ADA
    Yang boleh dipakai AI: judul + abstrak + jurnal + tahun.
    Artikel TANPA abstrak → dilarang jadi dasar kalimat temuan.

  PAGAR 2 — TANDA "ISI TERBATAS"
    Abstrak kosong → artikel ditandai `isi_terbatas=True`.
    Dipakai halaman (tanda ⚠️) DAN aturan prompt.

  PAGAR 3 — TAMPILKAN SUMBERNYA
    Abstrak disertakan ke layar supaya user bisa MEMBUKTIKAN sendiri
    (3 pilar Bos: NYATA · TERKELOMPOK · TERPAGAR).

Modul ini SENGAJA kecil & murni (tanpa jaringan, tanpa DB) supaya bisa
diuji bergigi: suntik artikel tanpa abstrak → pagar HARUS menolak.
"""
from __future__ import annotations

#  Panjang abstrak minimum agar boleh jadi dasar temuan.
MIN_ABSTRAK = 80


def abstrak_ada(artikel: dict) -> bool:
    """True kalau artikel punya abstrak yang cukup untuk jadi dasar."""
    if not isinstance(artikel, dict):
        return False
    teks = (artikel.get('abstract') or '').strip()
    return len(teks) >= MIN_ABSTRAK


def isi_terbatas(artikel: dict) -> bool:
    """True kalau artikel TIDAK punya abstrak yang layak (PAGAR 2)."""
    return not abstrak_ada(artikel)


def tandai(artikel: list[dict]) -> list[dict]:
    """Salin daftar artikel + tambahkan penanda `isi_terbatas` (PAGAR 2).

    Tidak mengubah masukan (murni) — supaya aman dipakai berulang.
    """
    keluar = []
    for a in (artikel or []):
        if not isinstance(a, dict):
            continue
        b = dict(a)
        b['isi_terbatas'] = isi_terbatas(a)
        keluar.append(b)
    return keluar


def layak_sitasi(artikel: dict) -> bool:
    """True kalau artikel boleh jadi DASAR KALIMAT TEMUAN (PAGAR 1).

    Syarat: punya abstrak cukup. (Audit DOI/verifikasi diurus pagar lain
    yang SUDAH ADA — `pustaka.daftar_pustaka_apa7`.)
    """
    return abstrak_ada(artikel)


def bagi(artikel: list[dict]) -> dict:
    """Pisahkan artikel: yang LAYAK jadi dasar vs yang ISI TERBATAS.

    Kembalikan {'layak': [...], 'terbatas': [...], 'jumlah': {...}}.
    """
    layak, terbatas = [], []
    for a in tandai(artikel):
        (layak if not a['isi_terbatas'] else terbatas).append(a)
    return {'layak': layak, 'terbatas': terbatas,
            'jumlah': {'layak': len(layak), 'terbatas': len(terbatas),
                       'total': len(layak) + len(terbatas)}}


def teks_untuk_ai(artikel: list[dict], maks: int = 8) -> str:
    """Susun bahan NYATA untuk AI: judul + abstrak + jurnal + tahun (PAGAR 1).

    ⚠️ Hanya artikel BERABSTRAK yang dimasukkan sebagai bahan temuan.
    Artikel "isi terbatas" tetap ditulis judulnya di bagian TERPISAH
    dengan keterangan tegas supaya AI TIDAK memakainya sebagai temuan.
    """
    b = bagi(artikel)
    baris = []
    for i, a in enumerate(b['layak'][:maks], 1):
        ab = (a.get('abstract') or '').strip()
        if len(ab) > 900:                                     # jaga panjang
            ab = ab[:900].rsplit(' ', 1)[0] + '…'
        baris.append(f'[{i}] {a.get("title") or "(tanpa judul)"}\n'
                     f'    {a.get("authors") or "-"} ({a.get("year") or "-"}) · '
                     f'{a.get("journal") or "-"}\n'
                     f'    ABSTRAK: {ab}')
    teks = '\n\n'.join(baris)
    if b['terbatas']:
        judul_terbatas = '; '.join(
            (a.get('title') or '(tanpa judul)') for a in b['terbatas'][:maks])
        teks += ('\n\n--- ARTIKEL TANPA ABSTRAK (JANGAN dijadikan dasar '
                 'temuan, hanya boleh disebut judulnya di daftar pustaka) ---\n'
                 + judul_terbatas)
    return teks


def aturan_prompt() -> str:
    """Kalimat aturan yang DISISIPKAN ke prompt AI (PAGAR 1)."""
    return ('ATURAN SUMBER (WAJIB DIPATUHI):\n'
            '1. Tulis HANYA berdasarkan JUDUL dan ABSTRAK yang diberikan.\n'
            '2. JANGAN menambah temuan, angka, nama penulis, atau tahun yang '
            'tidak ada di bahan di atas.\n'
            '3. Kalau bahan tidak cukup untuk satu klaim → JANGAN tulis '
            'klaim itu; tulis lebih umum atau lewati.\n'
            '4. Artikel pada bagian "TANPA ABSTRAK" HANYA boleh disebut '
            'judulnya, TIDAK boleh dijadikan dasar temuan.')
