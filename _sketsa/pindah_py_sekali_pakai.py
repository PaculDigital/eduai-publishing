#!/usr/bin/env python3
"""PINDAHKAN berkas .py SEKALI-PAKAI dari root → `_sketsa/` (Opsi B, 07Okt26).

ATURAN KERAS (keselamatan lebih penting dari kerapian):
  1. DAFTAR PUTIH — hanya nama yang terdaftar di bawah yang boleh dipindah.
     Tidak ada "tebak pola" (mis. `_uji_*.py`) — bisa menyeret yang penting.
  2. JANGAN pindah kalau masih DIRUJUK berkas lain (cek ulang saat jalan).
  3. JANGAN pindah: sot.py · 17 gerbang resmi · dirujuk jalankan.sh/Dockerfile.
  4. Pindah = `mv` (bukan hapus) → tetap ada, cuma pindah tempat.
  5. Tulis daftar SEBELUM/SESUDAH ke _arsip untuk jejak.

Pakai:
    python3 _sketsa/pindah_py_sekali_pakai.py           # SIMULASI
    python3 _sketsa/pindah_py_sekali_pakai.py --jalan    # EKSEKUSI
"""
from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import sys

BASE = pathlib.Path('/opt/data/services/eduai-publishing')
TUJUAN = BASE / '_sketsa'

#  ── DAFTAR PUTIH: hanya ini yang boleh dipindah ────────────────────────
SEKALI_PAKAI = [
    #  Akun & naskah uji (sekali pakai)
    '_akun_asih.py', '_ambil_asih.py', '_ambil_asih2.py', '_cek_bab_asih.py',
    '_uji_alur_asih.py', '_bersih_user_uji.py', '_siapkan_data_uji.py',
    '_siapkan_uji_belajar.py', '_siapkan_dok_sah.py',
    #  Bedah / cari (investigasi sekali)
    '_bedah2.py', '_bedah_9router.py', '_bedah_pn.py', '_bedah_pn2.py',
    '_bedah_translator.py', '_bedah_translator2.py',
    '_cari_jalur_resmi.py', '_cari_modelid.py', '_cari_provider_kustom.py',
    '_banding_pembagi.py', '_analisa_risiko.py', '_lapor_range.py',
    '_prediksi_percakapan.py', '_ukur_percakapan.py',
    #  Cek sekali pakai
    '_cek400.py', '_cek_9router.py', '_cek_endpoint_decisions.py',
    '_cek_err_jev.py', '_cek_jev113.py', '_cek_jev_bos.py', '_cek_key.py',
    '_cek_kunci_jev.py', '_cek_tuntas_1.py',
    '_cek_tuntas_2.py', '_celah1.py', '_celah2.py',
    #  Uji JEку (nilai balasan) — sudah dicabut/diganti
    '_uji_jev_1x.py', '_uji_jev_2b.py', '_uji_jev_3.py',
    '_uji_jev_9router_1.py', '_uji_jev_9router_2.py',
    '_uji_jev_asih_1.py', '_uji_jev_asih_2.py', '_uji_jev_asih_3.py',
    '_uji_jev_provider_bos.py', '_uji_jev_lapor.py', '_uji_jev_nilai_balasan.py',
    '_cek_kunci_jev.py',
    #  Uji combo / model / provider
    '_buat_combo.py', '_uji_combo_32k.py', '_uji_combo_9router.py',
    '_uji_combo_baru.py', '_uji_gemini_kandidat.py',
    '_uji_gemini_vs_deepseek.py', '_uji_model_inferhub.py',
    '_uji_lintas_provider.py', '_uji_fallback.py', '_uji_tier2.py',
    '_cek_koneksi_or.py', '_peta_provider.py', '_katalog_harga.py',
    #  Uji fase lama
    '_uji_fase2.py', '_uji_fase4.py', '_uji_final_opsiA.py', '_uji_lapis2.py',
    '_uji_dropdown_produksi.py', '_uji_skripsi_full.py', '_uji_web_final.py',
    '_uji_tabel_fase2.py', '_uji_batas15.py', '_uji_ide5rb.py',
    #  Uji kecil / eksperimen
    '_uji_gerbang_kode.py', '_uji_konsistensi.py', '_uji_loop_bagian.py',
    '_uji_mutu_potongan.py', '_uji_nyata_token.py', '_uji_pagar_presisi.py',
    '_uji_pantau_hidup.py', '_uji_pantau_lonceng.py', '_uji_paragraf_docx.py',
    '_uji_pembaca_pdf.py', '_uji_pemeriksa.py', '_uji_penempel.py',
    '_uji_pipa.py', '_uji_pola_subbab.py', '_uji_pola_subbab_badai.py',
    '_uji_publik_latar.py', '_uji_reasoning.py', '_uji_sambungan.py',
    '_uji_semantik.py', '_uji_tiga_jalur.py', '_uji_token_nyata.py',
    '_uji_ukur_8000.py', '_uji_notif_wa_presisi.py', '_uji_baca_kunci_volume.py',
    '_uji_cocok_bab.py', '_uji_bab_besar.py', '_uji_publik_komentar.py',
    '_uji_simulasi.py', '_uji_klik_alur.py', '_ují_tautan_garuda.py',
    '_uji_parser_salah_tempat.py', '_uji_t33_kunci_arsip.py',
    '_uji_t33_alur_http.py', '_uji_insight_belajar.py', '_uji_bank_soal.py',
    '_ukur_batas_struktur.py',
    #  Render / popup (sekali pakai)
    '_render_gratis.py', '_render_gratis_host.py', '_render_popup.py',
    '_render_sadar.py', '_popup_render_final.py', '_suntik_dan_render.py',
    '_perbaiki_vision.js', '_buka_komentar.py', '_bikin_docx_komentar.py',
    '_audit_konsistensi.py', '_tarif_ekstrem.py', '_tarif_revisi.py',
    '_e2e_addon.py', '_e2e_saran.py',
    '_cadangan_ai_tahap3_dibatalkan.py',
    #  Simulasi / ukur biaya (bukan `.py` produksi)
    'simulasi_agentic_bab1.py', 'simulasi_agentic_tools.py',
    'simulasi_perbandingan_bab.py', 'ukur_biaya_nyata.py',
    'verifikasi_biaya.py',
]

#  🛡️ JANGAN PERNAH dipindah (walau ada di daftar putih karena salah tulis)
LARANGAN = {
    'sot.py', '_gerbang_sot.py', '_gerbang_anti_bikin_baru.py',
    '_gerbang_jurnal.py', '_gerbang_jurnal2.py', '_gerbang_jurnal3.py',
    '_gerbang_jatah.py', '_gerbang_rute_jurnal.py',
    '_gerbang_halaman_referensi.py', '_gerbang_kata_referensi.py',
    '_gerbang_ikon_referensi.py', '_gerbang_ikon_semua.py',
    '_gerbang_ikon_asli.py', '_gerbang_pagar_artikel.py',
    '_gerbang_unduh_workspace.py', '_gerbang_e2e_unduh_http.py',
    '_gerbang_unduh_dobel.py', '_gerbang_unduh_dobel_e2e.py',
    '_gerbang_link_jurnal.py', '_gerbang_deteksi_bab.py', '_gerbang_visual.py',
    '_gerbang_pdf_nyata_workspace.py',
}


def dirujuk(nama: str) -> list[str]:
    """Berkas LAIN yang menyebut nama ini (tanpa ekstensi).

    ⚠️ JEBAKAN TERUKUR (07Okt26): skrip ini MENYEBUT SEMUA nama di dalam
    DAFTAR PUTIH-nya ⇒ tanpa pengecualian, `dirujuk()` menemukan DIRINYA
    SENDIRI dan SEMUA berkas dilewati ("dirujuk: ./_sketsa/pindah_...py").
    ⇒ kecualikan: skrip ini, berkas _arsip/, dan dokumen LAPORAN/arsip.
    """
    batang = nama[:-3] if nama.endswith('.py') else nama
    keluar = subprocess.run(
        ['grep', '-rl', '--include=*.sh', '--include=*.py', '--include=*.md',
         '--include=Dockerfile', r'\b' + re.escape(batang) + r'\b', '.'],
        cwd=BASE, capture_output=True, text=True).stdout.strip().split('\n')
    buang = []
    for x in keluar:
        if not x:
            continue
        if x == f'./{nama}':                      #  dirinya sendiri
            continue
        if '/_arsip/' in x or x.startswith('./_arsip'):
            continue                              #  backup/jejak (bukan rujukan)
        if pathlib.Path(x).name == pathlib.Path(__file__).name:
            continue                              #  skrip ini sendiri
        buang.append(x)
    return buang


def main() -> None:
    jalan = '--jalan' in sys.argv
    mode = 'EKSEKUSI' if jalan else 'SIMULASI'
    print(f'{"═"*72}\n  PINDAH .py SEKALI-PAKAI → _sketsa/  [{mode}]\n{"═"*72}')

    pindah, lewat, takada = [], [], []
    for nama in sorted(set(SEKALI_PAKAI)):
        p = BASE / nama
        if nama in LARANGAN:
            lewat.append((nama, '🛡️ DILARANG (gerbang/inti)')); continue
        if not p.exists():
            takada.append(nama); continue
        r = dirujuk(nama)
        if r:
            lewat.append((nama, f'🛡️ dirujuk: {r[0]}')); continue
        pindah.append(nama)

    print(f'\n  AKAN DIPINDAH: {len(pindah)}')
    for n in pindah:
        print(f'     📦 {n}')
    print(f'\n  DILEWATI: {len(lewat)}')
    for n, alasan in lewat:
        print(f'     {alasan:34} {n}')
    print(f'\n  TIDAK ADA di root: {len(takada)}')
    for n in takada:
        print(f'     ❓ {n}')

    if not jalan:
        print('\n  (SIMULASI — tidak ada yang dipindah. Tambah --jalan untuk eksekusi)')
        return

    D = BASE / '_arsip' / f'pre-pindah-py-{__import__("datetime").datetime.now():%Y%m%d-%H%M%S}'
    D.mkdir(parents=True, exist_ok=True)
    (D / 'SESUDAH.txt').write_text('\n'.join(pindah))
    ok = 0
    for n in pindah:
        try:
            shutil.move(str(BASE / n), str(TUJUAN / n))
            ok += 1
        except Exception as e:                      # noqa: BLE001
            print(f'  ❌ gagal {n}: {e}')
    print(f'\n  ✅ dipindah: {ok} · jejak: {D}/SESUDAH.txt')
    print(f'  .py di root sekarang: '
          f'{len(list(BASE.glob("*.py")))}')


if __name__ == '__main__':
    main()
