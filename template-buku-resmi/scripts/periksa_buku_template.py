#!/usr/bin/env python3
"""GERBANG v2: periksa .docx buku terhadap TEMPLATE BUKU RESMI.

WAJIB lulus sebelum .docx buku diserahkan. Membandingkan:
  H1/H2   ukuran halaman (14 x 20 cm) — DARI sectPr PERTAMA (kompat lama)
  M       batas halaman (atas/bawah/kanan 1,6 cm · kiri 1,02 cm · gutter 0,89 cm)
  F1-F3   font/ukuran/rata isi dari paragraf isi >= 150 karakter (kompat lama)
  S1      jarak baris isi tidak melebihi template (line <= 240)
  F4/F5   Heading1 Trajan Pro 22 pt tebal · Heading2 13 pt tebal (styles.xml)
  J1/J2   hirarki + judul bab dua baris <w:br/> + nomor Romawi ketat

BARU di v2 (menutup lubang audit 22 Okt 2026 — 6 mutasi yang dulu
LOLOS 20/20 sekarang wajib tertangkap):
  G1-G3   SEMUA sectPr diperiksa (ukuran + batas + header/footer 720),
          bukan hanya yang pertama
  G4/G5   titlePg aktif · settings mirrorMargins + evenAndOddHeaders aktif
  K1-K3   footer1/footer2 ADA, berisi field PAGE, dan dirujuk sectPr
          (nomor halaman genap/ganjil = bagian dari desain template)
  T1-T5   kelengkapan + urutan struktur: KATA PENGANTAR, DAFTAR ISI
          (+ field TOC), BAB, TENTANG PENULIS
  Y1-Y8   gaya lengkap: Normal (TNR 12), spasi & garis bawah Heading1,
          font tema + latar F2F2F2 + garis + keepNext Heading2,
          tab TOC1/TOC2 (right, dot, 5938)
  F6/F7   SEMUA run teks paragraf isi zona konten (>= 40 karakter)
          diperiksa font & ukurannya — bukan hanya run pertama,
          bukan hanya paragraf >= 150 karakter
  P1-P4   muka buku: judul sampul (run 35 pt), teks ISBN, Cetakan Pertama,
          ukuran run teks zona depan hanya yang terukur di template
          (sz 19/22/28/30/70 — di luar itu = muka buku diubah)

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


def teks_para(p):
    """Teks paragraf AMAN (regex [^<]* — jebakan J1)."""
    return ''.join(re.findall(r'<w:t(?:\s[^>]*)?>([^<]*)</w:t>', p)).strip()


def periksa(path, wajib_lebih=0):
    z = zipfile.ZipFile(path)
    nama_berkas = set(z.namelist())
    doc = z.read('word/document.xml').decode('utf-8')
    sty = z.read('word/styles.xml').decode('utf-8')
    settings = (z.read('word/settings.xml').decode('utf-8')
                if 'word/settings.xml' in nama_berkas else '')

    print(f'BERKAS: {path}')

    # ── HALAMAN (sectPr pertama — kompat gerbang lama) ──────────────────
    pgsz = ambil(doc, r'<w:pgSz([^/]*)/>') or ''
    w = tw(ambil(pgsz, r'w:w="(\d+)"'))
    h = tw(ambil(pgsz, r'w:h="(\d+)"'))
    print(f'\n== HALAMAN == {cm(w)} x {cm(h)} cm')
    ok('H1 lebar halaman = 14,00 cm', cm(w) == 14.0, f'{cm(w)} cm (wajib 14,0)')
    ok('H2 tinggi halaman = 20,00 cm', cm(h) == 20.0, f'{cm(h)} cm (wajib 20,0)')

    # ── BATAS (sectPr pertama — kompat gerbang lama) ────────────────────
    pgmar = ambil(doc, r'<w:pgMar([^/]*)/>') or ''
    wajib = {'top': 1.6, 'bottom': 1.6, 'right': 1.6, 'left': 1.02, 'gutter': 0.89}
    print('\n== BATAS ==')
    for k, harus in wajib.items():
        v = ambil(pgmar, rf'w:{k}="(\d+)"')
        dapat = cm(v)
        print(f'  {k:7s} {dapat} cm (wajib {harus})')
        ok(f'M {k} = {harus} cm', dapat == harus, f'{dapat} cm')

    # ── G: SEMUA sectPr (v2) ────────────────────────────────────────────
    sects = re.findall(r'<w:sectPr.*?</w:sectPr>', doc, re.S)
    print(f'\n== SECTION == {len(sects)} sectPr')
    ok('G0 ada minimal 1 sectPr', bool(sects), 'tidak ada sectPr')
    if sects:
        buruk_sz, buruk_mar, buruk_hf = [], [], []
        for i, s in enumerate(sects):
            sz = ambil(s, r'<w:pgSz([^/]*)/>') or ''
            if (tw(ambil(sz, r'w:w="(\d+)"')), tw(ambil(sz, r'w:h="(\d+)"'))) != (7938, 11340):
                buruk_sz.append(i)
            mar = ambil(s, r'<w:pgMar([^/]*)/>') or ''
            for k, harus_twip in {'top': 907, 'bottom': 907, 'right': 907,
                                  'left': 578, 'gutter': 505}.items():
                if tw(ambil(mar, rf'w:{k}="(\d+)"')) != harus_twip:
                    buruk_mar.append((i, k))
            if (tw(ambil(mar, r'w:header="(\d+)"')) != 720
                    or tw(ambil(mar, r'w:footer="(\d+)"')) != 720):
                buruk_hf.append(i)
        ok('G1 SEMUA sectPr ukuran 14x20 cm', not buruk_sz,
           f'sectPr ke-{buruk_sz} ukurannya beda')
        ok('G2 SEMUA sectPr batas sama (1,6/1,6/1,6/1,02/gutter 0,89)',
           not buruk_mar, f'beda: {buruk_mar[:4]}')
        ok('G3 SEMUA sectPr margin header/footer = 720 twip (1,27 cm)',
           not buruk_hf, f'sectPr ke-{buruk_hf} header/footer beda')
        ok('G4 titlePg aktif (halaman pertama beda)', '<w:titlePg/>' in sects[-1],
           'titlePg hilang')
    ok('G5 settings: mirrorMargins + evenAndOddHeaders aktif',
       '<w:mirrorMargins/>' in settings and '<w:evenAndOddHeaders/>' in settings,
       'salah satu hilang dari settings.xml — margin cermin/footer genap-ganjil berubah')

    # ── K: FOOTER & NOMOR HALAMAN (v2) ──────────────────────────────────
    print('\n== FOOTER ==')
    ada_f1 = 'word/footer1.xml' in nama_berkas
    ada_f2 = 'word/footer2.xml' in nama_berkas
    ok('K1 footer1.xml + footer2.xml ada', ada_f1 and ada_f2,
       f'footer1={ada_f1} footer2={ada_f2}')
    if ada_f1 and ada_f2:
        f1 = z.read('word/footer1.xml').decode('utf-8')
        f2 = z.read('word/footer2.xml').decode('utf-8')
        ok('K2 kedua footer berisi field PAGE (nomor halaman otomatis)',
           'PAGE' in f1 and 'PAGE' in f2, 'field PAGE hilang dari footer')
    if sects:
        rujukan = sects[-1]
        ok('K3 sectPr merujuk footer default + even',
           'w:type="even"' in rujukan and 'w:type="default"' in rujukan,
           'rujukan footer default/even tidak lengkap')

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
        teks = teks_para(p)
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

    # ── F6/F7: SEMUA RUN isi zona konten (v2) ───────────────────────────
    # Zona konten = sesudah Heading1 pertama (KATA PENGANTAR). Paragraf
    # tanpa pStyle, tanpa field, teks >= 40 kar, bukan blok kutipan sz=32.
    # Dulu: paragraf 40-149 kar dan run ke-2 dst TIDAK diperiksa sama sekali.
    print('\n== RUN ISI (zona konten) ==')
    mulai = None
    for i, p in enumerate(paras):
        if ambil(p, r'<w:pStyle w:val="(Heading1)"'):
            mulai = i
            break
    run_font_salah, run_sz_salah, n_run = [], [], 0
    if mulai is not None:
        for p in paras[mulai:]:
            if 'w:fldChar' in p or 'w:instrText' in p:
                continue
            if ambil(p, r'<w:pStyle w:val="([^"]+)"'):
                continue
            if len(teks_para(p)) < 40:
                continue
            _sz = tw(ambil(p, r'<w:sz w:val="(\d+)"'))
            _jc = ambil(p, r'<w:jc w:val="([^"]+)"')
            if _sz == 32 or (_jc == 'center' and _sz and _sz > 20):
                continue              # blok kutipan/garis sz 32 — pengecualian terukur
            for run in re.findall(r'<w:r(?: [^>]*)?>.*?</w:r>', p, re.S):
                if '<w:t' not in run:
                    continue          # run gambar/pemutus — bukan teks
                n_run += 1
                f = ambil(run, r'w:ascii="([^"]+)"')
                s = tw(ambil(run, r'<w:sz w:val="(\d+)"'))
                if f != 'Palatino Linotype':
                    run_font_salah.append(f)
                if s != 20:
                    run_sz_salah.append(s)
    print(f'  {n_run} run teks diperiksa')
    ok('F6 SEMUA run isi font = Palatino Linotype', bool(n_run) and not run_font_salah,
       f'{len(run_font_salah)} run salah font: {run_font_salah[:3]}' if n_run else 'tidak ada run isi')
    ok('F7 SEMUA run isi ukuran = 10 pt', bool(n_run) and not run_sz_salah,
       f'{len(run_sz_salah)} run salah ukuran: {run_sz_salah[:3]}' if n_run else 'tidak ada run isi')

    # ── JUDUL (styles.xml) ──────────────────────────────────────────────
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

    # ── Y: GAYA LENGKAP (v2) ────────────────────────────────────────────
    normal = gaya.get('Normal') or ''
    toc1 = gaya.get('TOC1') or ''
    toc2 = gaya.get('TOC2') or ''
    print('\n== GAYA LENGKAP ==')
    ok('Y1 Normal = Times New Roman 12 pt',
       ambil(normal, r'w:ascii="([^"]+)"') == 'Times New Roman'
       and tw(ambil(normal, r'<w:sz w:val="(\d+)"')) == 24,
       f'font={ambil(normal, r"w:ascii=.([^\"]+).")} sz={ambil(normal, r"<w:sz w:val=.(\d+).")}')
    sp_h1 = ambil(h1, r'<w:spacing ([^/>]*)/?>') or ''
    ok('Y2 Heading1 spasi before=100 after=240',
       tw(ambil(sp_h1, r'w:before="(\d+)"')) == 100
       and tw(ambil(sp_h1, r'w:after="(\d+)"')) == 240,
       f'spacing H1: {sp_h1}')
    ok('Y3 Heading1 garis bawah single sz=4 warna 808080',
       bool(re.search(r'<w:bottom w:val="single" w:sz="4" w:space="1" w:color="808080"', h1)),
       'garis bawah Heading1 berubah')
    ok('Y4 Heading2 font = tema minorHAnsi',
       'minorHAnsi' in h2, 'font Heading2 berubah dari tema minorHAnsi')
    ok('Y5 Heading2 latar F2F2F2',
       'w:fill="F2F2F2"' in h2, 'latar Heading2 bukan F2F2F2')
    ok('Y6 Heading2 garis bawah 808080 + keepNext',
       bool(re.search(r'<w:bottom w:val="single" w:sz="4" w:space="1" w:color="808080"', h2))
       and '<w:keepNext/>' in h2, 'garis/keepNext Heading2 berubah')
    sp_h2 = ambil(h2, r'<w:spacing ([^/>]*)/?>') or ''
    ok('Y7 Heading2 spasi before=40', tw(ambil(sp_h2, r'w:before="(\d+)"')) == 40,
       f'spacing H2: {sp_h2}')
    ok('Y8 TOC1 + TOC2 tab kanan dot pos=5938',
       'w:pos="5938"' in toc1 and 'w:pos="5938"' in toc2
       and 'w:leader="dot"' in toc1 and 'w:leader="dot"' in toc2,
       'tab daftar isi berubah')

    # ── HIRARKI ────────────────────────────────────────────────────────
    judul = [(ambil(p, r'<w:pStyle w:val="([^"]+)"'), teks_para(p))
             for p in paras]
    judul = [(g, t) for g, t in judul if g in ('Heading1', 'Heading2') and t]
    print(f'\n== HIRARKI == {len(judul)} judul')
    for g, t in judul[:10]:
        print(f'  {g}: {t[:50]}')
    ok('J1 ada minimal 1 Heading1', any(g == 'Heading1' for g, _ in judul),
       'tidak ada judul bab')

    # ── T: STRUKTUR WAJIB + URUTAN (v2) ─────────────────────────────────
    print('\n== STRUKTUR ==')
    teks_h1 = [t.upper() for g, t in judul if g == 'Heading1']
    pos = {}
    for i, p in enumerate(paras):
        g = ambil(p, r'<w:pStyle w:val="([^"]+)"')
        t = teks_para(p).upper()
        if g == 'Heading1' and t.startswith('KATA PENGANTAR'):
            pos.setdefault('pengantar', i)
        if g in ('TOCHeading', 'Heading1') and t.startswith('DAFTAR ISI'):
            pos.setdefault('daftarisi', i)
        if g == 'Heading1' and t.startswith('BAB'):
            pos.setdefault('bab', i)
        if g == 'Heading1' and t.startswith('TENTANG PENULIS'):
            pos.setdefault('penulis', i)
    ok('T1 ada KATA PENGANTAR (Heading1)', 'pengantar' in pos,
       f'Heading1 yang ada: {teks_h1[:5]}')
    ok('T2 ada DAFTAR ISI + field TOC',
       'daftarisi' in pos and ' TOC ' in doc,
       'DAFTAR ISI / field TOC hilang')
    ok('T3 ada minimal 1 BAB (Heading1)', 'bab' in pos, 'tidak ada BAB')
    ok('T4 ada TENTANG PENULIS (Heading1)', 'penulis' in pos,
       'TENTANG PENULIS hilang')
    urut = [pos[k] for k in ('pengantar', 'daftarisi', 'bab', 'penulis') if k in pos]
    ok('T5 urutan: Pengantar < Daftar Isi < BAB < Tentang Penulis',
       len(urut) == 4 and urut == sorted(urut), f'posisi: {pos}')

    # ── P: MUKA BUKU (v2) ───────────────────────────────────────────────
    print('\n== MUKA BUKU ==')
    depan = paras[:50]
    ada_judul_sampul = any('<w:sz w:val="70"/>' in p for p in depan)
    ok('P1 ada judul sampul (run 35 pt di bagian depan)', ada_judul_sampul,
       'run sz=70 judul sampul tidak ditemukan')
    teks_semua = ' '.join(teks_para(p) for p in paras)
    ok('P2 ada data ISBN di halaman hak cipta', 'ISBN' in teks_semua,
       'teks ISBN hilang')
    ok('P3 ada keterangan Cetakan Pertama', 'Cetakan Pertama' in teks_semua,
       'teks Cetakan Pertama hilang')
    # Ukuran run teks zona depan TERUKUR dari template: {19, 22, 28, 30, 70}.
    # Mutasi audit D (sz 28 -> 60 di sampul) dulu lolos karena tak diperiksa.
    sz_depan_salah = []
    for p in depan:
        for run in re.findall(r'<w:r(?: [^>]*)?>.*?</w:r>', p, re.S):
            if '<w:t' not in run:
                continue
            s = tw(ambil(run, r'<w:sz w:val="(\d+)"'))
            if s not in (19, 22, 28, 30, 70):
                sz_depan_salah.append(s)
    ok('P4 ukuran run teks zona depan hanya yang terukur (19/22/28/30/70)',
       not sz_depan_salah, f'ukuran asing: {sorted(set(sz_depan_salah), key=str)[:4]}')

    # ── J2: JUDUL BAB DUA BARIS (putusan Bos 22 Okt 2026) ──────────────
    #  Template asli menulis "BAB I" <w:br/> "JUDUL BAB PERTAMA" dalam SATU
    #  paragraf Heading1. <w:br/> = pemutus baris ⇒ tampil DUA BARIS.
    #  Yang DILARANG: menyatu tanpa pemutus ("BAB IJUDUL" satu baris).
    # ⚠️ ROMAWI diuji ke BAGIAN AWAL saja (sebelum penanda «BR»).
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
        #  J2b: run PERTAMA pada tiap judul WAJIB angka Romawi yang SAH
        #  secara gramatika (v2: pola ketat — IIII / IC / IL ditolak).
        romawi_sah = re.compile(
            r'^BAB\s+M{0,3}(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$')
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
