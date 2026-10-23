#!/usr/bin/env python3
"""GERBANG TULISAN TERUKUR (barang 10 RENCANA-BANGUN-SSOT).

Memeriksa hal tulisan yang BISA dibuktikan mesin, dari profil jenis:
  T1  sitasi dua arah tanpa yatim — setiap entri DAFTAR PUSTAKA dirujuk
      di teks bab, dan setiap sitasi di teks punya entri pustakanya.
  T2  kata terlarang budaya tidak muncul di teks
      (profil: aturan_tulisan.kata_terlarang_teks).
  T3  bagian wajib tulisan hadir (profil: cek_teks_wajib — pola teks).

Yang TIDAK diukur di sini (makna sitasi, mutu argumen, rasa bahasa)
tetap tugas peninjau — lihat barang 12 (verifikasi 3 lapis + kwitansi).

Pakai:
    python3 periksa_tulisan.py buku.docx --profil=../jenis/monograf/profil.json
EXIT 0 = lulus, 1 = gagal.
"""
import json
import html
import re
import sys
import zipfile
from pathlib import Path

LULUS = GAGAL = 0


def ok(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f'  -> {info}' if info else ''))


def teks_para(p):
    return html.unescape(''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p))).strip()


def gaya_para(p):
    m = re.search(r'<w:pStyle w:val="([^"]+)"', p)
    return m.group(1) if m else ''


def kunci_entri(entri):
    """Himpunan (nama_keluarga, tahun) dari satu entri pustaka APA.

    Semua nama keluarga penulis (bukan hanya penulis pertama) dipasangkan
    ke tahun entri — sitasi naratif menyebut semua penulis ("Sari dan
    Putra, 2022"), jadi kunci entri harus mengenal keduanya.
    """
    m = re.search(r'\((\d{4})[a-z]?\)', entri) or re.search(r'\b((?:19|20)\d{2})\b', entri)
    tahun = m.group(1) if m else ''
    depan = entri[:m.start()] if m else entri
    nama2 = {k.lower() for k in re.findall(r"[A-Z][a-zA-Z'\-]{2,}", depan)}
    return {(n, tahun) for n in nama2}


def sitasi_di_teks(teks):
    """Himpunan (nama, tahun) dari sitasi kurung & naratif."""
    hasil = set()
    for m in re.finditer(r'\(([^)]*?)(\d{4})[a-z]?\)', teks):
        dalam, tahun = m.group(1), m.group(2)
        for nama in re.findall(r"[A-Z][a-zA-Z'\-]+", dalam):
            hasil.add((nama.lower(), tahun))
    for m in re.finditer(r"([A-Z][a-zA-Z'\-]+)(?:\s+(?:&|dan)\s+([A-Z][a-zA-Z'\-]+))?\s*\((\d{4})", teks):
        hasil.add((m.group(1).lower(), m.group(3)))
        if m.group(2):
            hasil.add((m.group(2).lower(), m.group(3)))
    return hasil


def periksa(path, profil):
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    paras = [(gaya_para(p), teks_para(p))
             for p in re.findall(r'<w:p(?: [^>]*)?>.*?</w:p>|<w:p(?: [^>]*)?/>', doc, re.S)]
    print(f'BERKAS: {path}')
    print(f"PROFIL: {profil['id']}")

    idx_dp = next((i for i, (g, t) in enumerate(paras)
                   if g == 'Heading1' and t.upper() == 'DAFTAR PUSTAKA'), None)
    idx_bab = next((i for i, (g, t) in enumerate(paras)
                    if g == 'Heading1' and t.upper().startswith('BAB ')), None)
    idx_pen = next((i for i, (g, t) in enumerate(paras)
                    if g == 'Heading1' and t.upper().startswith('TENTANG PENULIS')), None)

    print('\n== SITASI DUA ARAH ==')
    if idx_dp is None or idx_bab is None:
        ok('T1 sitasi dua arah', False, 'DAFTAR PUSTAKA / BAB tidak ditemukan')
    else:
        teks_bab = ' '.join(t for _, t in paras[idx_bab:idx_dp])
        batas = idx_pen if idx_pen is not None else len(paras)
        entri = [t for _, t in paras[idx_dp + 1:batas] if t]
        tercitasi = sitasi_di_teks(teks_bab)
        kunci_entri_list = [kunci_entri(e) for e in entri]
        semua_kunci = set().union(*kunci_entri_list) if kunci_entri_list else set()
        yatim_pustaka = [entri[i][:48] for i, k in enumerate(kunci_entri_list)
                         if not (k & tercitasi)]
        yatim_sitasi = sorted(f'{n} ({t})' for (n, t) in tercitasi
                              if (n, t) not in semua_kunci)
        ok(f'T1a semua {len(entri)} entri pustaka dirujuk di teks',
           not yatim_pustaka, f'tidak dirujuk: {yatim_pustaka[:3]}')
        ok(f'T1b semua sitasi di teks ({len(tercitasi)}) punya entri pustaka',
           not yatim_sitasi, f'tanpa entri: {yatim_sitasi[:3]}')

    print('\n== LARANGAN BUDAYA DI TEKS ==')
    terlarang = profil.get('aturan_tulisan', {}).get('kata_terlarang_teks', [])
    semua = ' '.join(t for _, t in paras)
    ketemu = [k for k in terlarang
              if re.search(rf'\b{re.escape(k)}\b', semua, re.I)]
    ok(f'T2 kata terlarang tidak muncul ({len(terlarang)} kata dipantau)',
       not ketemu, f'ditemukan: {ketemu}')

    print('\n== BAGIAN WAJIB TULISAN ==')
    for cek in profil.get('cek_teks_wajib', []):
        ok(f"T3 hadir: {cek['label']}",
           bool(re.search(cek['pola'], semua, re.I)),
           f"pola '{cek['pola']}' tidak ditemukan di teks")

    print(f'\nRINGKAS: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    profil_path = next((a.split('=', 1)[1] for a in sys.argv[1:]
                        if a.startswith('--profil=')), None)
    if not arg or not profil_path:
        sys.exit(__doc__)
    profil = json.loads(Path(profil_path).read_text(encoding='utf-8'))
    sys.exit(periksa(Path(arg[0]), profil))
