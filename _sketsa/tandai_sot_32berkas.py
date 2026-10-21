#!/usr/bin/env python3
"""Tandai 32 berkas LAIN di luar pengawasan satpam SOT (lanjutan putusan Bos A).

Ditemukan oleh pemeriksa baru `periksa_berkas_luar_pengawasan()`:
berkas yang menyinggung kata "status/belum dikode/sudah live" tapi belum
ber-penanda SOT. Mayoritas: `PUTUSAN_*` (keputusan terkunci),
`IDE_*` (⠸ belum dikoding), `CATATAN_DISKUSI_*`, `DOKUMENTASI_*`.

ATURAN: jangan hapus isi lama — hanya SISIPKAN blok penanda di kepala.
"""
from __future__ import annotations

import pathlib
import re

BASE = pathlib.Path('/opt/data/services/eduai-publishing')

JENIS = {
    #  ⛔ IDE — DILARANG dikoding sampai Bos bilang mulai
    'IDE_FILE_LINK_JURNAL_PER_WORKSPACE_06OKT2026.md': 'ide',
    'IDE_FLEKSIBEL_DALAM_PAGAR_06OKT2026.md': 'ide',
    'IDE_HARVEST_UNDUH_KE_WORKSPACE_06OKT2026.md': 'ide',
    'IDE_MESIN_PENCARI_2_JALUR_06OKT2026.md': 'ide',
    'IDE_PAGAR_TIKET_COBA_ULANG_06OKT2026.md': 'ide',
    'IDE_PENCARIAN_JURNAL_BERBAYAR_06OKT2026.md': 'ide',
    'IDE_PENCARIAN_PER_VARIABEL_06OKT2026.md': 'ide',
    'IDE_TAB_REFERENSI_DUA_JALUR_06OKT2026.md': 'ide',
    #  ✅ PUTUSAN — keputusan Bos terkunci (rujukan, bukan status)
    'JAWABAN_BOS_9_PERTANYAAN_06OKT2026.md': 'putusan',
    'PUTUSAN_ATURAN_PORSI_8_ARTIKEL_06OKT2026.md': 'putusan',
    'PUTUSAN_AUTO_AI_06OKT2026.md': 'putusan',
    'PUTUSAN_FINAL_PAGAR_PENCARIAN_06OKT2026.md': 'putusan',
    'PUTUSAN_LENGKAP_9_PERTANYAAN_06OKT2026.md': 'putusan',
    'PUTUSAN_PAGAR_2X_PER_MINGGU_06OKT2026.md': 'putusan',
    'PUTUSAN_PAGAR_TIKET_2X_06OKT2026.md': 'putusan',
    'FITUR_PLAN_JURNAL_WORKSPACE_06OKT2026.md': 'putusan',
    'MULAI_URUTAN_KERJA_JURNAL_06OKT2026.md': 'putusan',
    #  🗄️ LAPORAN/DOKUMENTASI — catatan peristiwa
    'CATATAN_DISKUSI_HARVEST_JURNAL_06OKT2026.md': 'catatan',
    'CATATAN_DISKUSI_WORKSPACE_06OKT2026.md': 'catatan',
    'CATATAN_JEV_FITUR_JURNAL_06OKT2026.md': 'catatan',
    'CELAH_PROFIL_DRAFT_26SEP2026.md': 'laporan',
    'DOKUMENTASI_ANTREAN_BOTTLENECK_HANTU_25SEP2026.md': 'laporan',
    'DOKUMENTASI_ATURAN_SALIN_RESTART_24SEP2026.md': 'laporan',
    'DOKUMENTASI_JEV_NILAI_BALASAN_05OKT2026.md': 'laporan',
    'DOKUMENTASI_REBRANDING.md': 'laporan',
    'DOKUMENTASI_UJI_MODE_BACA_03OKT2026.md': 'laporan',
    'DOKUMENTASI_UJI_TOMBOL_AI_03OKT2026.md': 'laporan',
    'HASIL_CEK_TEMPAT_SIMPAN_ARTIKEL_06OKT2026.md': 'laporan',
    'LAPORAN_UJI_JEV_PENILAI_BALASAN_05OKT2026.md': 'laporan',
    #  ⏸️ RANCANGAN — menunggu keputusan
    'RANCANGAN_JEMBATAN_SATPAM_JEV_05OKT2026.md': 'rancangan',
    'RANCANGAN_SATPAM_JEV_04OKT2026.md': 'rancangan',
    'RENCANA_AGENTIC_TELEGRAM_WA.md': 'rancangan',
}

EKOR = """
> **PENENTU STATUS proyek hanya:** `SOT.md` · `FLAG_LANJUT_DISINI.md` ·
> `MASTER_PLAN.md` · `CATATAN_PROYEK.md`, dijaga `python3 sot.py --periksa`.
"""

TEMPLAT = {
    'ide': """<!-- ⛔ SOT: IDE — DILARANG DIKODING -->
> # ⛔ IDE / USULAN — **DILARANG dikoding** sampai Bos bilang "mulai".
> Isi berkas ini = **gagasan menunggu putusan Bos**, BUKAN keadaan kini dan
> BUKAN rencana kerja aktif. ❌ JANGAN dibaca sebagai status proyek.
""" + EKOR,
    'putusan': """<!-- ✅ SOT: PUTUSAN BOS — rujukan, bukan status -->
> # ✅ PUTUSAN BOS (TERKUNCI) — rujukan keputusan, BUKAN penentu status.
> Berkas ini mencatat **keputusan yang sudah dikunci Bos** pada tanggalnya.
> Isinya **tidak** melaporkan progress terkini. Kalau ragu soal "sedang
> dikerjakan atau belum" → periksa kode, bukan berkas ini.
""" + EKOR,
    'catatan': """<!-- 📝 SOT: CATATAN DISKUSI — bukan penentu status -->
> # 📝 CATATAN DISKUSI — BUKAN penentu status proyek.
> Berkas ini merekam **bahan pembicaraan** saat itu. Sebagian bisa sudah
> dikerjakan, sebagian belum. ❌ JANGAN dipakai sebagai keadaan kini.
""" + EKOR,
    'laporan': """<!-- 🗄️ SOT: LAPORAN/BUKTI — bukan penentu status -->
> # 🗄️ LAPORAN / BUKTI PEKERJAAN — BUKAN penentu status proyek.
> Berkas ini merekam **APA YANG TERJADI saat itu** (catatan peristiwa).
> Angka (image, tabel, gerbang, tanggal) **wajar berbeda** dari keadaan
> **kini** — itu memang rekaman, bukan kesalahan.
""" + EKOR,
    'rancangan': """<!-- ⏸️ SOT: RANCANGAN — belum dijalankan -->
> # ⏸️ RANCANGAN — belum dijalankan, BUKAN penentu status.
> Isi berkas ini = **usulan/rancangan yang MENUNGGU keputusan Bos**.
> ❌ JANGAN dibaca sebagai keadaan kini.
""" + EKOR,
}


def sisip(p: pathlib.Path, teks: str) -> str:
    isi = p.read_text('utf-8')
    if 'SOT: ' in isi[:1200]:
        return 'SUDAH ADA'
    baris = isi.split('\n')
    idx = None
    for i, b in enumerate(baris[:12]):
        if re.match(r'^#\s+\S', b):
            idx = i
            break
    if idx is None:
        baru = teks + '\n' + isi
    else:
        baru = ('\n'.join(baris[:idx + 1]) + '\n\n' + teks + '\n'
                + '\n'.join(baris[idx + 1:]))
    p.write_text(baru, 'utf-8')
    return 'OK'


def main() -> None:
    ok = sudah = hilang = 0
    for nama, jenis in sorted(JENIS.items()):
        p = BASE / nama
        if not p.exists():
            print(f'  TIDAK ADA  {nama}')
            hilang += 1
            continue
        h = sisip(p, TEMPLAT[jenis])
        if h == 'OK':
            ok += 1
        else:
            sudah += 1
    print(f'\n  ✅ ditandai: {ok} · sudah ada: {sudah} · tidak ada: {hilang}')


if __name__ == '__main__':
    main()
