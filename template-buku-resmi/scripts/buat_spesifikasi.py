#!/usr/bin/env python3
"""Buat SPESIFIKASI-DARI-PROFIL.md dari profil.json (barang 3 RENCANA-BANGUN-SSOT).

Prinsip SSOT: dokumen spesifikasi adalah TURUNAN. Semua angka di berkas
hasil dibaca dari profil.json — tidak ada angka yang diketik tangan di sini.
Kalau profil berubah, jalankan ulang skrip ini; dokumen ikut berubah.

Pakai:
    python3 buat_spesifikasi.py ../jenis/monograf/profil.json
Menghasilkan SPESIFIKASI-DARI-PROFIL.md di folder yang sama dengan profil.
"""
import json
import sys
from pathlib import Path


def nilai(x):
    return "— (MENUNGGU KEPUTUSAN)" if x is None else str(x)


def render(p):
    f = p["format"]
    u = f["ukuran"]
    m = f["margin_twip"]
    fj = f.get("font_judul")
    baris_judul = (
        f"| Font judul bab | {fj['nama']} {fj['pt']} pt (`w:sz` {fj['sz']}) |"
        if fj else "| Font judul bab | — (MENUNGGU KEPUTUSAN) |"
    )
    spasi = f["spasi"]
    spasi_teks = (
        f"kelipatan {spasi['nilai']} (line {spasi['line_twip']})"
        if spasi["jenis"] == "kelipatan" else f"tetap, line {spasi['line_twip']}"
    )
    th = f.get("target_halaman")
    th_teks = (
        f"{th['min']}–{th['maks']} halaman" if th and th.get("maks")
        else (f"min {th['min']} halaman" if th else "—")
    )
    ekstra = ""
    alt = u.get("alternatif_a5")
    if alt:
        ekstra += (f"| Ukuran alternatif | A5 ({alt['lebar_twip']} × {alt['tinggi_twip']} twip, "
                   f"area teks {alt['area_teks_twip']}) |\n")
    ft = f.get("font_tiu_tik")
    if ft:
        ekstra += f"| Font TIU/TIK | {ft['nama']} {ft['pt']} pt miring (`w:sz` {ft['sz']}) |\n"
    fd = f.get("font_daftar")
    if fd:
        ekstra += (f"| Font daftar | {fd['nama']} {fd['pt']} pt (`w:sz` {fd['sz']}), "
                   f"spasi sebelum/sesudah {fd['space_pt']} pt, spasi baris {fd['spasi']} |\n")
    if f.get("indentasi_gantung_daftar_twip"):
        ekstra += f"| Indentasi gantung daftar (twip) | {f['indentasi_gantung_daftar_twip']} |\n"
    unsur = "\n".join(f"- {x}" for x in p["unsur_wajib"])
    tunggu = "\n".join(f"- {x}" for x in p["menunggu_keputusan"]) or "- (tidak ada)"
    at = p["aturan_tulisan"]
    return f"""# SPESIFIKASI (DARI PROFIL) — {p['nama']}

> ⚠️ **BERKAS TURUNAN — JANGAN EDIT TANGAN.**
> Dihasilkan oleh `scripts/buat_spesifikasi.py` dari `profil.json` di
> folder ini. Sumber kebenaran = `profil.json`. Ubah di sana, lalu
> jalankan ulang skripnya.
> Sumber keputusan: {p['sumber_keputusan']}

## Format

| Item | Nilai |
|---|---|
| Ukuran | {u['nama']} — {u['lebar_cm']} × {u['tinggi_cm']} cm ({u['lebar_twip']} × {u['tinggi_twip']} twip) |
| Margin (twip) | atas {m['atas']} · bawah {m['bawah']} · kiri {m['kiri']} · kanan {m['kanan']} |
| Gutter (twip) | {nilai(f.get('gutter_twip'))} |
| Area teks (twip) | {f['area_teks_twip']} |
| Font isi | {f['font_isi']['nama']} {f['font_isi']['pt']} pt (`w:sz` {f['font_isi']['sz']}) |
{baris_judul}
{ekstra}| Spasi baris | {spasi_teks} |
| Target halaman | {th_teks} |
| Target bab | {f.get('target_bab') or '—'} |

## Unsur wajib

{unsur}

## Aturan tulisan

- Tone: {nilai(at.get('tone'))}
- Sitasi: {at.get('sitasi', '—')}
- Larangan teks: {at.get('larangan_teks', '—')}

## Menunggu keputusan

{tunggu}
"""


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    path = Path(sys.argv[1])
    profil = json.loads(path.read_text(encoding="utf-8"))
    out = path.parent / "SPESIFIKASI-DARI-PROFIL.md"
    out.write_text(render(profil), encoding="utf-8")
    print(f"tertulis {out} (dari {path.name}, id={profil['id']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
