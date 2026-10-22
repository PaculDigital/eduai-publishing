#!/usr/bin/env python3
"""GERBANG: periksa .docx buku terhadap TEMPLATE BUKU RESMI.

WAJIB lulus sebelum .docx buku diserahkan. Membandingkan:
  H1 ukuran halaman (14 x 20 cm)
  H2 batas halaman (atas/bawah/kanan 1,6 cm · kiri 1,02 cm · gutter 0,89 cm)
  F1 font isi = Palatino Linotype
  F2 ukuran isi = 10 pt
  F3 isi rata kanan-kiri (both)
  F4 judul bab = Trajan Pro, 22 pt, tebal
  F5 sub bab = 13 pt, tebal
  S1 jarak baris isi TIDAK melebihi template (line <= 240 auto)

Pakai:
    python3 periksa_buku_template.py buku.docx
    python3 periksa_buku_template.py --wajib-lebih-1 buku.docx   # untuk uji bergigi

EXIT 0 = LULUS, EXIT 1 = GAGAL (cetak alasan).
"""
import re
import sys
import zipfile
from pathlib import Path

TWIP_CM = 567.0
LULUS = GAGAL = 0
MASALAH = []


def ok(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f'  -> {info}' if info else ''))
        MASALAH.append(f'{nama}: {info}')


def tw(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def cm(v):
    n = tw(v)
    return None if n is None else round(n / TWIP_CM, 2)


def ambil(t, p, b=None):
    m = re.search(p, t, re.S)
    return m.group(1) if m else b


def periksa(path, wajib_lebih=0):
    z = zipfile.ZipFile(path)
    doc = z.read('word/document.xml').decode('utf-8')
    sty = z.read('word/styles.xml').decode('utf-8')

    print(f'BERKAS: {path}')

    # ── HALAMAN ────────────────────────────────────────────────────────
    pgsz = ambil(doc, r'<w:pgSz([^/]*)/>') or ''
    w = tw(ambil(pgsz, r'w:w="(\d+)"'))
    h = tw(ambil(pgsz, r'w:h="(\d+)"'))
    print(f'\n== HALAMAN == {cm(w)} x {cm(h)} cm')
    ok('H1 lebar halaman = 14,00 cm', cm(w) == 14.0, f'{cm(w)} cm (wajib 14,0)')
    ok('H2 tinggi halaman = 20,00 cm', cm(h) == 20.0, f'{cm(h)} cm (wajib 20,0)')

    # ── BATAS ──────────────────────────────────────────────────────────
    pgmar = ambil(doc, r'<w:pgMar([^/]*)/>') or ''
    wajib = {'top': 1.6, 'bottom': 1.6, 'right': 1.6, 'left': 1.02, 'gutter': 0.89}
    print('\n== BATAS ==')
    for k, harus in wajib.items():
        v = ambil(pgmar, rf'w:{k}="(\d+)"')
        dapat = cm(v)
        print(f'  {k:7s} {dapat} cm (wajib {harus})')
        ok(f'M {k} = {harus} cm', dapat == harus, f'{dapat} cm')

    # ── GAYA: font isi dari PARAGRAF ISI (bukan dari Normal) ───────────
    # ⚠️ JEBAKAN TERUKUR: paragraf Daftar Isi memakai FIELD Word sehingga
    # teksnya "Web</w:r>..." (sisa XML) dan panjangnya menipu. WAJIB dibuang
    # dulu, kalau tidak gerbang menuduh template asli salah (gagal palsu).
    paras = re.findall(r'<w:p[ >].*?</w:p>', doc, re.S)
    isi = []
    dibuang_field = dibuang_toc = dibuang_kutipan = 0
    for p in paras:
        if 'w:fldChar' in p or 'w:instrText' in p:
            dibuang_field += 1
            continue
        if ambil(p, r'<w:pStyle w:val="(TOC\d+|TOCHeading)"'):
            dibuang_toc += 1
            continue
        teks = ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p)).strip()
        if len(teks) < 150:
            continue
        if ambil(p, r'<w:pStyle w:val="([^"]+)"'):
            continue                      # judul, bukan isi
        # ⚠️ PENGECUALIAN BERALASAN (terukur dari template asli):
        # blok QUOTES penutup buku memakai 16 pt (sz=32) rata TENGAH —
        # memang beda dari isi buku, bukan cacat. Dikenali dari jc=center
        # ATAU sz=32. Tanpa pengecualian ini gerbang menuduh template asli
        # salah (gagal palsu).
        _sz = tw(ambil(p, r'<w:sz w:val="(\d+)"'))
        _jc = ambil(p, r'<w:jc w:val="([^"]+)"')
        if _sz == 32 or (_jc == 'center' and _sz and _sz > 20):
            dibuang_kutipan += 1
            continue
        d = {'font': ambil(p, r'w:ascii="([^"]+)"'),
             'sz': ambil(p, r'<w:sz w:val="(\d+)"'),
             'jc': ambil(p, r'<w:jc w:val="([^"]+)"'),
             'sp': ambil(p, r'<w:spacing ([^/>]*)/?>')}
        isi.append(d)
    print(f'\n== ISI BUKU == {len(isi)} paragraf isi '
          f'(dibuang: {dibuang_field} field, {dibuang_toc} TOC, '
          f'{dibuang_kutipan} kutipan)')
    if not isi:
        ok('F0 ada paragraf isi', False, 'tidak ada paragraf >=150 karakter')
    else:
        salah_font = [d for d in isi if d['font'] != 'Palatino Linotype']
        ok('F1 font isi = Palatino Linotype', not salah_font,
           f'{len(salah_font)}/{len(isi)} paragraf salah font: '
           f'{[d["font"] for d in salah_font][:3]}')
        salah_sz = [d for d in isi if tw(d['sz']) != 20]
        ok('F2 ukuran isi = 10 pt', not salah_sz,
           f'{len(salah_sz)}/{len(isi)} salah ukuran: {[d["sz"] for d in salah_sz][:3]}')
        salah_jc = [d for d in isi if d['jc'] != 'both']
        ok('F3 isi rata kanan-kiri (both)', not salah_jc,
           f'{len(salah_jc)}/{len(isi)} tidak justify: {[d["jc"] for d in salah_jc][:3]}')
        # S1 jarak baris: line harus <= 240 (template = 240 auto / warisi)
        lewat = []
        for d in isi:
            if not d['sp']:
                continue
            ln = tw(ambil(d['sp'], r'w:line="(\d+)"'))
            if ln is not None and ln > 240:
                lewat.append(ln)
        ok('S1 jarak baris isi tidak melebihi template (<= 240)', not lewat,
           f'{len(lewat)} paragraf line>240: {lewat[:4]}')

    # ── JUDUL ──────────────────────────────────────────────────────────
    gaya = {}
    for m in re.finditer(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*>(.*?)</w:style>',
                         sty, re.S):
        gaya[m.group(1)] = m.group(2)
    h1 = gaya.get('Heading1') or ''
    h2 = gaya.get('Heading2') or ''
    print('\n== JUDUL ==')
    ok('F4 Heading1 font = Trajan Pro',
       ambil(h1, r'w:ascii="([^"]+)"') == 'Trajan Pro',
       str(ambil(h1, r'w:ascii="([^"]+)"')))
    ok('F4b Heading1 ukuran = 22 pt', tw(ambil(h1, r'<w:sz w:val="(\d+)"')) == 44,
       f'{ambil(h1, r"<w:sz w:val=.(\\d+).")} (wajib 44 = 22 pt)')
    ok('F4c Heading1 tebal', '<w:b/>' in h1, 'tidak tebal')
    ok('F5 Heading2 ukuran = 13 pt', tw(ambil(h2, r'<w:sz w:val="(\d+)"')) == 26,
       f'{ambil(h2, r"<w:sz w:val=.(\\d+).")} (wajib 26 = 13 pt)')
    ok('F5b Heading2 tebal', '<w:b/>' in h2, 'tidak tebal')

    # ── HIRARKI ────────────────────────────────────────────────────────
    judul = [(ambil(p, r'<w:pStyle w:val="([^"]+)"'),
              ''.join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.S)).strip())
             for p in paras]
    judul = [(g, t) for g, t in judul if g in ('Heading1', 'Heading2') and t]
    print(f'\n== HIRARKI == {len(judul)} judul')
    for g, t in judul[:10]:
        print(f'  {g}: {t[:50]}')
    ok('J1 ada minimal 1 Heading1', any(g == 'Heading1' for g, _ in judul),
       'tidak ada judul bab')

    # ── J2: JUDUL BAB DUA BARIS (putusan Bos 22 Okt 2026) ──────────────
    #  Template asli menulis "BAB I" <w:br/> "JUDUL BAB PERTAMA" dalam SATU
    #  paragraf Heading1. <w:br/> = pemutus baris ⇒ tampil DUA BARIS.
    #  Yang DILARANG: menyatu tanpa pemutus ("BAB IJUDUL" satu baris).
    # ⚠️ ROMAWI diuji ke BAGIAN AWAL saja (sebelum penanda «BR»).
    ROMAWI = re.compile(r'^BAB\s+[IVXLC]+(?=\s*$|«BR»|\s)')
    print('\n== J2 JUDUL BAB DUA BARIS ==')
    #  Ganti <w:br/> jadi penanda «BR» SEBELUM ekstraksi teks, karena
    #  re.findall('<w:t…>') MEMBUANG <w:br/> sehingga judul terbaca menyatu.
    peta = []
    for p in paras:
        if not ambil(p, r'<w:pStyle w:val="(Heading1)"'):
            continue
        p2 = re.sub(r'<w:br\s*/>', '<w:t>«BR»</w:t>', p)
        t = ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p2)).strip()
        if t:
            peta.append((t, p))
    print(f'  Heading1 ditemukan: {len(peta)}')
    #  ⚠️ JANGAN menyaring dengan ROMAWI di sini! Kalau disaring, judul yang
    #  RUSAK ("BAB IJUDUL…") justru TERBUANG dari daftar -> lolos tanpa diperiksa.
    #  Ambil SEMUA judul berawalan BAB, baru hakimi.
    bab = [(t, p) for t, p in peta if t.upper().startswith('BAB')]
    if not bab:
        print(f'  (dilewati) tidak ada judul BAB; contoh: {[t[:28] for t, _ in peta][:4]}')
    else:
        ada_br, tanpa_br = [], []
        for t, p in bab:
            (ada_br if ('<w:br/>' in p or '<w:br />' in p) else tanpa_br).append(t)
        ok('J2a SEMUA judul bab pakai <w:br/> (dua baris)',
           not tanpa_br, f'{len(tanpa_br)} judul TANPA pemutus: {tanpa_br[:3]}')
        #  J2b: run PERTAMA pada tiap judul WAJIB angka Romawi sah.
        romawi_sah = re.compile(r'^BAB\s+[IVXLC]+$')
        nomor, salah = [], []
        for t, _ in bab:
            awal = t.split('«BR»')[0].strip()
            nomor.append(awal)
            if not romawi_sah.match(awal):
                salah.append(awal)
        ok('J2b nomor bab = angka Romawi SAH (BAB I/II/III…)',
           not salah, f'tidak sah: {salah[:4]} dari {nomor[:4]}')
        #  J2c: jumlah baris harus 2 (satu <w:br/>) -> nomor + judul.
        dua_baris = [t for t, _ in bab if t.count('«BR»') == 1]
        ok('J2c tiap judul bab = tepat 2 baris (satu pemutus)',
           len(dua_baris) == len(bab),
           f'{len(dua_baris)}/{len(bab)} punya tepat 1 <w:br/>')

    # ── UJI BERGIGI (memaksa GAGAL untuk membuktikan gerbang bergigi) ──
    if wajib_lebih:
        print(f'\n== UJI BERGIGI: wajib_lebih={wajib_lebih} ==')
        ok('X1 uji bergigi sengaja GAGAL', False,
           f'wajib_lebih={wajib_lebih} -> gerbang TERBUKTI bisa gagal')

    print('\n' + '=' * 62)
    if MASALAH:
        print('MASALAH:')
        for x in MASALAH:
            print('  •', x)
    print(f'RINGKAS: {LULUS} LULUS / {GAGAL} GAGAL')
    return 1 if GAGAL else 0


if __name__ == '__main__':
    arg = [a for a in sys.argv[1:] if not a.startswith('--')]
    lebih = 0
    for a in sys.argv[1:]:
        if a.startswith('--wajib-lebih'):
            lebih = int(a.split('=')[-1]) if '=' in a else 1
    if not arg:
        sys.exit(__doc__)
    p = Path(arg[0])
    if not p.exists():
        sys.exit(f'Berkas tidak ada: {p}')
    sys.exit(periksa(p, lebih))
