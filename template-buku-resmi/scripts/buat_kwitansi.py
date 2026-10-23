#!/usr/bin/env python3
"""KWITANSI MUTU OTOMATIS (barang 16 RENCANA-BANGUN-SSOT).

Satu berkas bukti per buku: mengumpulkan hasil SEMUA gerbang yang
berlaku + statistik isi + status nomor terukur, ditulis sebagai
<buku>.kwitansi.md di samping buku. Prinsip dokumen acuan: nomor
dicentang hanya dengan bukti — kwitansi mencatat HASIL, bukan janji;
bagian yang butuh peninjau dicatat sebagai MENUNGGU PENINJAU.

Pakai:
    python3 buat_kwitansi.py buku.docx --profil=../jenis/monograf/profil.json
"""
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path

SINI = Path(__file__).resolve().parent


def jalan(skrip, *args):
    r = subprocess.run([sys.executable, str(SINI / skrip), *args],
                       capture_output=True, text=True)
    m = re.search(r'RINGKAS: (\d+) LULUS / (\d+) GAGAL', r.stdout)
    return (f'{m.group(1)} LULUS / {m.group(2)} GAGAL' if m else 'TIDAK TERBACA'), r


def teks_para(p):
    return ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p)).strip()


def gaya_para(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    return m.group(1) if m else ''


def statistik(path):
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    paras = [(gaya_para(p), teks_para(p))
             for p in re.findall(r'<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>', doc, re.S)]
    bab = {}
    kini = '(pembuka)'
    for g, t in paras:
        if g == 'Heading1':
            kini = t
            bab.setdefault(kini, 0)
        elif t:
            bab[kini] = bab.get(kini, 0) + len(t.split())
    n_gambar = len(re.findall(r'<a:blip', doc))
    n_tabel = len(re.findall(r'<w:tbl>', doc))
    toc_angka = len(re.findall(r'PAGEREF', doc))
    return bab, n_gambar, n_tabel, toc_angka


def main():
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    profil_arg = next((a.split('=', 1)[1] for a in sys.argv[1:]
                       if a.startswith('--profil=')), None)
    if not arg or not profil_arg:
        sys.exit(__doc__)
    import json
    buku = Path(arg[0])
    profil = json.loads(Path(profil_arg).read_text(encoding='utf-8'))

    g_format, _ = jalan('periksa_buku_template.py', str(buku),
                        f'--profil={profil_arg}', '--wajib-pustaka')
    g_tulis, _ = jalan('periksa_tulisan.py', str(buku), f'--profil={profil_arg}')
    g_mirip, _ = jalan('cek_kemiripan.py', str(buku))
    _, r_font = jalan('periksa_font.py', '--profil', profil_arg)
    m_font = re.search(r'RINGKAS: (\d+)/(\d+) font ada', r_font.stdout)
    font_status = (f'{m_font.group(1)}/{m_font.group(2)} font profil terpasang di mesin ini'
                   if m_font else 'tidak terbaca')
    _, r_verif = jalan('verifikasi_sitasi.py', str(buku))
    m_verif = re.search(r'RINGKAS: (\d+) entri \| TIDAK-DITEMUKAN: (\d+)', r_verif.stdout)
    verif_status = (f'{m_verif.group(1)} entri; TIDAK-DITEMUKAN (DOI 404): {m_verif.group(2)}; '
                    'sisanya per status di laporan verifikasi (TERBUKTI/PERLU-MANUAL)'
                    if m_verif else 'tidak terbaca')

    bab, n_gambar, n_tabel, toc_angka = statistik(buku)
    baris = [
        f'# KWITANSI MUTU — {buku.name}',
        '',
        f'- Tanggal terbit kwitansi: {datetime.now().strftime("%d %B %Y %H:%M")}',
        f'- Jenis buku / profil: {profil["id"]} (profil versi {profil.get("versi", "?")})',
        f'- Ukuran berkas: {buku.stat().st_size:,} byte'.replace(',', '.'),
        '',
        '## Hasil gerbang (terukur)',
        f'- Gerbang format (profil): **{g_format}**',
        f'- Gerbang tulisan: **{g_tulis}**',
        f'- Gate kemiripan lokal: **{g_mirip}** (bukan Turnitin; korpus = buku sendiri)',
        f'- Gerbang font: {font_status} — buku hanya sah dicetak dari mesin berfont lengkap',
        f'- Verifikasi sitasi lapis 1–2 (Crossref): {verif_status}',
        '- Verifikasi sitasi lapis 3 (makna): **MENUNGGU PENINJAU** — bahan kalimat '
        'pemakai tersedia dari verifikasi_sitasi.py',
        '',
        '## Isi buku',
        f'- Total kata: {sum(bab.values()):,}'.replace(',', '.') + ' kata',
    ]
    for nama, n in bab.items():
        baris.append(f'  - {nama}: {n:,} kata'.replace(',', '.'))
    baris += [
        f'- Gambar: {n_gambar} · Tabel: {n_tabel}',
        f'- Penanda halaman daftar isi (PAGEREF): {toc_angka} entri — angka terukur '
        'ditempel generator dari render (barang 7); periksa konsistensi terhadap PDF render terakhir',
        '',
        '*Kwitansi ini dihasilkan mesin dari hasil gerbang yang benar-benar dijalankan.*',
    ]
    keluar = buku.with_suffix('.kwitansi.md')
    keluar.write_text('\n'.join(baris) + '\n', encoding='utf-8')
    print('\n'.join(baris))
    print(f'\nKWITANSI TERTULIS: {keluar}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
