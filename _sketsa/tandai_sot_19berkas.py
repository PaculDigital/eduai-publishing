#!/usr/bin/env python3
"""Tandai 19 berkas di luar pengawasan satpam SOT (putusan Bos: Opsi A).

KENAPA: satpam `sot.py --periksa` hanya memeriksa 3 dokumen induk
(FLAG/MASTER_PLAN/CATATAN_PROYEK). 19 berkas lain memuat kata "status /
belum / selesai" tapi DI LUAR pengawasan ⇒ kalau bertabrakan, tak ada yang
tahu. Label ini menyatakan: "berkas ini BUKAN penentu status".

ATURAN: jangan hapus isi lama — hanya SISIPKAN blok penanda di kepala.
"""
from __future__ import annotations

import pathlib
import re

BASE = pathlib.Path('/opt/data/services/eduai-publishing')

#  Label per jenis berkas — SESUAI KEADAAN NYATA, bukan seragam.
LABEL = {
    #  LAPORAN/BUKTI pekerjaan → catatan peristiwa
    'LAPORAN_KEASLIAN_IKON_06OKT2026.md': 'laporan',
    'LAPORAN_RAPI_BERKAS_UJI_04OKT2026.md': 'laporan',
    'LAPORAN_TAHAP1_1_KOLOM_JURNAL_06OKT2026.md': 'laporan',
    'LAPORAN_UNDUH_WORKSPACE_06OKT2026.md': 'laporan',
    'DOKUMENTASI_JARINGAN_DAN_EDITOR_16SEP26.md': 'laporan',
    'DOKUMENTASI_PARSER_DAN_GERBANG_05OKT2026.md': 'laporan',
    'DOKUMENTASI_PEMBIMBING_AI_03OKT2026.md': 'laporan',
    'DOKUMENTASI_SINKRON_KODE_06OKT2026.md': 'laporan',
    'CARA_MESIN_TAHU_ISI_ARTIKEL_06OKT2026.md': 'laporan',
    'TEMUAN_REVISI_RINGAN_VS_BERAT_24SEP2026.md': 'laporan',
    #  PETA lama → riwayat
    'PETA_PERCABANGAN_24SEP2026.md': 'peta-lama',
    'PETA_HALUS_STATUS_26SEP2026.md': 'peta-lama',
    'DOKUMEN_ARSITEKTUR.md': 'peta-lama',
    'FLAG_SESI_24SEP2026.md': 'peta-lama',
    #  RENCANA/diskusi belum dikerjakan → bukan penentu status
    'RENCANA_PEMBIMBING_AI_SEDERHANA.md': 'rencana-tuntas',
    'RENCANA_KOLABORASI_PEMBIMBING_23SEP2026.md': 'rencana',
    'CATATAN_DISKUSI_PEMBIMBING_22SEP2026.md': 'rencana',
    #  Aturan format/sitasi → bukan soal status proyek
    'ATURAN_FORMAT_PEDOMAN_26SEP2026.md': 'aturan',
    'ATURAN_SITASI_PEDOMAN_26SEP2026.md': 'aturan',
}

#  Isi tiap label. `{tgl}` = tanggal berkas, `{status}` = catatan khusus.
TEMPLAT = {
    'laporan': """<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> **Berkas ini merekam APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) di dalamnya **wajar berbeda** dari
> keadaan **kini** — itu BUKAN kesalahan, itu memang rekaman.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.
""",
    'peta-lama': """<!-- 🗄️ SOT: BUKAN PENENTU STATUS -->
> # 🗄️ PETA/ARSIP LAMA — BUKAN penentu status proyek.
> Berkas ini memetakan keadaan pada **tanggal di namanya**. Banyak isinya
> **sudah berubah**. Sah untuk **pelajaran/jejak**, ❌ **JANGAN** dipakai
> sebagai keadaan kini.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.
""",
    'rencana': """<!-- ⏸️ SOT: RENCANA — BELUM DIKERJAKAN -->
> # ⏸️ RENCANA / BAHAN DISKUSI — belum dikerjakan, BUKAN penentu status.
> Isi berkas ini = **usulan/keputusan yang MENUNGGU perintah Bos**.
> Belum tentu dikode. ❌ **JANGAN** dibaca sebagai keadaan kini.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.
""",
    'rencana-tuntas': """<!-- ⚠️ SOT: RENCANA SUDAH TUNTAS — JANGAN PERCAYA "BELUM DIKODE" -->
> # ⚠️ RENCANA INI **SUDAH DIKODE & LIVE** (03 Okt 2026) — BUKAN penentu status.
> 🚩 **PENTING:** baris **"Status: RENCANA — BELUM DIKODE"** di bawah ini
> **SUDAH BASI**. Pembimbing AI **sudah LIVE di produksi** sejak 03 Okt 2026
> (`pembimbing_ai.py` + `rute_pembimbing_ai.py`, disambung `main.py:33,105,106`).
> Berkas ini kini **catatan putusan D1–D9** (rujukan), bukan rencana tertunda.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.
""",
    'aturan': """<!-- 📏 SOT: ATURAN FORMAT/SITASI — bukan penentu status -->
> # 📏 ATURAN FORMAT/SITASI — bukan penentu status proyek.
> Berkas ini berisi **pedoman penulisan** (format/sitasi). Isinya **tidak**
> melaporkan progress atau keadaan proyek.
>
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.
""",
}


def sisip(p: pathlib.Path, teks: str) -> str:
    """Sisipkan label SESUDAH baris judul `#` pertama (biar judul tetap di atas)."""
    isi = p.read_text('utf-8')
    if 'SOT: ' in isi[:900]:
        return 'SUDAH ADA'
    baris = isi.split('\n')
    #  Cari judul utama pertama (`# ...`)
    idx = None
    for i, b in enumerate(baris[:12]):
        if re.match(r'^#\s+\S', b):
            idx = i
            break
    if idx is None:
        baru = teks + '\n' + isi
    else:
        baru = '\n'.join(baris[:idx + 1]) + '\n\n' + teks + '\n' + \
               '\n'.join(baris[idx + 1:])
    p.write_text(baru, 'utf-8')
    return 'OK'


def main() -> None:
    hasil = {}
    for nama, jenis in LABEL.items():
        p = BASE / nama
        if not p.exists():
            hasil[nama] = 'TIDAK ADA'
            continue
        hasil[nama] = sisip(p, TEMPLAT[jenis])
    for nama in sorted(hasil):
        print(f'  {hasil[nama]:10} {nama}')


if __name__ == '__main__':
    main()
