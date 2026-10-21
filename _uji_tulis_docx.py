"""UJI app/tulis_docx.py — LANGKAH D. Dijalankan DI DALAM container.

Menguji hal yang BENAR-BENAR penting (bukan sekadar "tidak error"):
  1. Ganti SELURUH naskah (BAB_SELURUH)  → isi berubah, struktur utuh
  2. Ganti SATU bab saja                 → bab lain TIDAK tersentuh
  3. TABEL & bagian lain .docx selamat   → arsip ZIP utuh
  4. Hasil kosong → DITOLAK (jangan rusak naskah)
  5. Bab tidak ketemu → DITOLAK dengan pesan jelas
  6. Cadangan dibuat sebelum menulis
  7. XML sehat & bisa dibaca ulang (round-trip)
  8. Tidak ada berkas sementara tertinggal
"""
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, '/app')
from app.tulis_docx import peta_paragraf, rakit, terapkan_ke_berkas   # noqa: E402
from app.versi import BAB_SELURUH, deteksi_bab                        # noqa: E402

CONTOH = Path('/app/_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx')
KERJA = Path('/tmp/uji_tulis_docx')
LULUS = GAGAL = 0


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {catatan}' if catatan else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {catatan}' if catatan else ''))


def teks_dari(path):
    """Baca teks .docx (sama seperti app/ai.py) — untuk verifikasi."""
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    return ''.join(p['teks'] + '\n' for p in peta_paragraf(xml))


def main():
    if not CONTOH.exists():
        print(f'❌ dokumen contoh tidak ada: {CONTOH}')
        return 1
    if KERJA.exists():
        shutil.rmtree(KERJA)
    KERJA.mkdir(parents=True)

    print('=' * 62)
    print('UJI LANGKAH D — tulis_docx.py')
    print('=' * 62)

    # ══ 1. PETA PARAGRAF ══════════════════════════════════════════════
    print('\n[1] peta_paragraf — paragraf di dalam TABEL harus DILEWATI')
    with zipfile.ZipFile(CONTOH) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    par = peta_paragraf(xml)
    cek('paragraf terbaca (>20)', len(par) > 20, f'{len(par)} paragraf')
    semua_teks = ' '.join(p['teks'] for p in par)
    cek('teks naskah terbaca', 'MENSTRUASI' in semua_teks.upper(),
        'judul skripsi ketemu')
    # paragraf di dalam tabel tidak boleh ada di daftar
    import re
    tabel_rentang = [(m.start(), m.end()) for m in
                     re.finditer(r'<w:tbl(?=[\s>/]).*?</w:tbl>', xml, re.S)]
    di_tabel = [p for p in par if any(a <= p['awal'] < b for a, b in tabel_rentang)]
    cek('paragraf dalam tabel DILEWATI', len(di_tabel) == 0,
        f'{len(di_tabel)} bocor')

    # ══ 2. GANTI SELURUH NASKAH ═══════════════════════════════════════
    print('\n[2] Ganti SELURUH naskah (BAB_SELURUH)')
    f1 = KERJA / 'seluruh.docx'
    shutil.copy2(CONTOH, f1)
    lama_teks = teks_dari(f1)
    hasil = terapkan_ke_berkas(
        f1,
        'BAB I PENDAHULUAN\nIni hasil revisi AI untuk uji Langkah D.\n'
        'Paragraf kedua hasil revisi.',
        BAB_SELURUH,
        backup_dir=KERJA / 'cadangan',
    )
    cek('laporan ok', hasil.get('ok') is True, str(hasil.get('pesan', ''))[:70])
    cek('paragraf diganti >0', (hasil.get('paragraf_diganti') or 0) > 0,
        f"{hasil.get('paragraf_diganti')} → {hasil.get('paragraf_baru')}")
    cek('cadangan dibuat', bool(hasil.get('cadangan')))
    baru_teks = teks_dari(f1)
    cek('isi berubah', baru_teks != lama_teks)
    cek('teks baru ada', 'hasil revisi AI untuk uji' in baru_teks)
    cek('teks LAMA sudah hilang', 'MENSTRUASI' not in baru_teks.upper())

    # ══ 3. BAGIAN LAIN .docx SELAMAT ══════════════════════════════════
    print('\n[3] Bagian lain .docx (styles/media/rels) harus UTUH')
    with zipfile.ZipFile(CONTOH) as z:
        asli = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(f1) as z:
        sesudah = {n: z.read(n) for n in z.namelist()}
    cek('jumlah bagian sama', len(asli) == len(sesudah),
        f'{len(asli)} → {len(sesudah)}')
    beda = [n for n in asli if n in sesudah and asli[n] != sesudah[n]]
    cek('HANYA document.xml berubah', beda == ['word/document.xml'],
        f'berubah: {beda[:4]}')
    cek('media (gambar) utuh',
        [n for n in asli if n.startswith('word/media/')] ==
        [n for n in sesudah if n.startswith('word/media/')])

    # ══ 4. GANTI SATU BAB SAJA ════════════════════════════════════════
    print('\n[4] Ganti SATU bab saja — bab lain TIDAK boleh tersentuh')
    f2 = KERJA / 'satu_bab.docx'
    shutil.copy2(CONTOH, f2)
    bab_ada = deteksi_bab(teks_dari(f2))
    if not bab_ada:
        cek('deteksi bab (contoh tanpa bab)', True, 'dilewati — dokumen tanpa bab')
    else:
        target = bab_ada[0]
        label = target['label']
        hasil2 = terapkan_ke_berkas(
            f2, f'{label} HASIL BARU SAJA\nIsi bab ini diganti oleh AI.',
            label, target['judul'], backup_dir=KERJA / 'cadangan')
        cek(f'laporan ok ({label})', hasil2.get('ok') is True,
            str(hasil2.get('pesan', ''))[:70])
        teks2 = teks_dari(f2)
        cek('teks baru masuk', 'HASIL BARU SAJA' in teks2)
        if len(bab_ada) > 1:
            judul_lain = bab_ada[1]['judul']
            isi_lain = bab_ada[1]['isi'][:120]
            tetap = any(x in teks2 for x in isi_lain.split('\n')[:3] if len(x) > 20)
            cek(f'{bab_ada[1]["label"]} TIDAK tersentuh', tetap,
                f'judul "{judul_lain[:30]}"')
        else:
            cek('dokumen 1 bab — tidak ada bab lain', True)

    # ══ 5. PENOLAKAN AMAN (jangan rusak naskah) ═══════════════════════
    print('\n[5] Keamanan: HARUS MENOLAK, bukan menulis asal')
    f3 = KERJA / 'aman.docx'
    shutil.copy2(CONTOH, f3)
    sebelum = f3.read_bytes()

    r_kosong = terapkan_ke_berkas(f3, '   \n  \n', BAB_SELURUH)
    cek('hasil KOSONG ditolak', r_kosong.get('ok') is False,
        str(r_kosong.get('pesan', ''))[:60])
    cek('berkas TIDAK berubah', f3.read_bytes() == sebelum)

    r_bab = terapkan_ke_berkas(f3, 'isi apa pun', 'BAB XCIX')
    cek('bab tidak ada ditolak', r_bab.get('ok') is False,
        str(r_bab.get('pesan', ''))[:60])
    cek('berkas TIDAK berubah', f3.read_bytes() == sebelum)

    r_hilang = terapkan_ke_berkas(KERJA / 'tidak-ada.docx', 'x', BAB_SELURUH)
    cek('berkas hilang ditolak', r_hilang.get('ok') is False)

    # ══ 6. ROUND-TRIP: .docx masih bisa dibaca ════════════════════════
    print('\n[6] Round-trip: .docx hasil harus tetap sah')
    import xml.etree.ElementTree as ET
    with zipfile.ZipFile(f1) as z:
        xml2 = z.read('word/document.xml').decode('utf-8')
        ET.fromstring(xml2.encode('utf-8'))
        cek('document.xml sehat (XML sah)', True)
        cek('[Content_Types] ada', '[Content_Types].xml' in z.namelist())
        cek('word/_rels ada',
            any(n.startswith('word/_rels/') for n in z.namelist()))
    # python-docx (kalau ada di container) = pembaca pihak ketiga
    try:
        import docx
        d = docx.Document(str(f1))
        gab = ' '.join(p.text for p in d.paragraphs)
        cek('python-docx bisa membuka & baca',
            'hasil revisi AI untuk uji' in gab, f'{len(gab)} karakter')
    except ImportError:
        cek('python-docx (tidak ada di container)', True, 'dilewati')

    # ══ 7. TIDAK ADA BERKAS SEMENTARA TERTINGGAL ══════════════════════
    print('\n[7] Tidak ada berkas sementara tertinggal')
    sisa = [p.name for p in KERJA.iterdir() if p.name.startswith('.')]
    cek('tidak ada .tmp sisa', not sisa, str(sisa[:3]))
    cek('berkas awal utuh (tidak tertimpa)',
        CONTOH.exists() and CONTOH.stat().st_size == 52210,
        f'{CONTOH.stat().st_size} byte')

    print('\n' + '=' * 62)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('=' * 62)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
