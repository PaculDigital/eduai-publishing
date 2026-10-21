#!/usr/bin/env python3
"""
Assembly Buku Umum — Ekonomi Digital (Uji Coba 3 Bab)
Struktur: Cover → ISBN → Kata Pengantar → Daftar Isi → Bab 1-3 → Glosarium → Indeks → Daftar Pustaka → Bio
B5, TNR 12pt, footer PAGE, page break per bab
"""

import json, os, re, random, time
import logging
import tata_paragraf
from docx import Document
from docx.shared import Pt, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

log = logging.getLogger(__name__)

OUT_DIR = "/opt/data/buku_umum_test"
VISUAL_DIR = os.path.join(OUT_DIR, "visual")
DOCX_OUT = os.path.join(OUT_DIR, "EKONOMI_DIGITAL_BUKU_UMUM_FINAL.docx")

# ═══════════════════════════════════════════════════════════════════════════
#  SETELAN PER BUKU (ACC Bos 19 Okt 2026 — assembly disambung ke rute /buku)
#
#  AKAR MASALAH SEBELUM INI: berkas ini DITULIS UNTUK SATU BUKU. Judul,
#  penulis, institusi, tahun, folder hasil, dan nama berkas DOCX semuanya
#  HARDCODE ("EKONOMI_DIGITAL_..."). Akibatnya buku milik user lain akan
#  dirakit dengan sampul dan identitas buku Ekonomi Digital.
#
#  OBAT: `siapkan(judul, ...)` menyetel global untuk buku yang sedang
#  dirakit, mengikuti pola `penyusun_buku.py` (setel global, pulihkan di
#  finally). TIDAK ada fungsi assembly baru — fungsi lama dipakai apa adanya.
# ═══════════════════════════════════════════════════════════════════════════
#  ⚠️ `_ASLI` diisi SETELAH `BUKU` didefinisikan (lihat bawah, setelah KONFIGURASI).
_ASLI = {}


def siapkan(judul, keluar_dir, penulis='', institusi='', tahun=None,
            subjudul='', nama_berkas=None):
    """Setel global assembly untuk SATU buku. Return (docx_out, pemulih).

    Pemanggil WAJIB memanggil `pemulih()` di blok finally — kalau tidak,
    buku berikutnya mewarisi judul buku sebelumnya (pencemaran lintas buku,
    jebakan yang sama dengan `architect_prompt` di penyusun_buku.py).
    """
    global OUT_DIR, VISUAL_DIR, DOCX_OUT, BUKU
    import time as _t
    OUT_DIR = keluar_dir
    VISUAL_DIR = os.path.join(keluar_dir, 'visual')
    os.makedirs(VISUAL_DIR, exist_ok=True)
    if not nama_berkas:
        #  Nama berkas dari JUDUL, bukan dari judul buku lama.
        aman = re.sub(r'[^A-Za-z0-9]+', '_', (judul or 'BUKU')).strip('_').upper()
        nama_berkas = (aman or 'BUKU') + '_FINAL.docx'
    DOCX_OUT = os.path.join(keluar_dir, nama_berkas)
    BUKU = {
        'judul': (judul or '').strip(),
        'subjudul': subjudul or '',
        'penulis': penulis or '',
        'institusi': institusi or '',
        'tahun': str(tahun or _t.strftime('%Y')),
        'ukuran': 'B5',
    }

    def _pulih():
        global OUT_DIR, VISUAL_DIR, DOCX_OUT, BUKU
        OUT_DIR = _ASLI['OUT_DIR']
        VISUAL_DIR = _ASLI['VISUAL_DIR']
        DOCX_OUT = _ASLI['DOCX_OUT']
        BUKU = dict(_ASLI['BUKU'])

    return DOCX_OUT, _pulih

# === DATA TABEL (dari pipeline JSON, fallback ke hardcoded) ===
def load_tabel_data():
    """Load tabel data dari JSON yang di-generate pipeline (one-pass).

    🚨 CACAT TERUKUR 20 Okt 2026 — BOCOR TOPIK.
    Versi lama SELALU memulai dari `dict(TABEL_DATA_FALLBACK)` yang berisi
    **12 tabel contoh tentang EKONOMI DIGITAL** (Gojek, Tokopedia, Google,
    Meta). Akibat nyata: buku anak "Mengamati Langit" keluar dengan 2 tabel
    berisi "Aset Utama / Ekonomi Tradisional / Data & algoritma" — penandanya
    `[TABEL 1.1: Bayangan Tongkat…]` tapi ISINYA ekonomi. Pembaca melihat
    tabel yang tidak nyambung sama sekali dengan bukunya.

    Obat (bukan tambalan): fallback HANYA dipakai kalau pipeline TIDAK
    menghasilkan tabel sama sekali. Kalau pipeline punya data, data pipeline
    yang menang PENUH — jangan dicampur contoh.
    """
    #  Kumpulkan SEMUA tabel dari pipeline lebih dulu.
    ada_pipeline = {}
    for bab_num in range(1, 13):
        json_path = os.path.join(VISUAL_DIR, f"tabel_bab{bab_num}.json")
        if os.path.exists(json_path):
            try:
                with open(json_path) as f:
                    pipeline_tables = json.load(f)
            except Exception as e:                # noqa: BLE001
                log.warning('[tabel] gagal baca %s (%s)', json_path, e)
                continue
            for tid, tdata in (pipeline_tables or {}).items():
                if tdata.get("rows"):
                    ada_pipeline[tid] = tdata

    if ada_pipeline:
        #  Ada data nyata ⇒ JANGAN campur dengan contoh tertulis mati.
        #  ⚠️ TAPI: pipeline bisa menulis tabel dengan `rows: []` (judul &
        #  headers benar, isi KOSONG). Ini TERUKUR 20 Okt 2026: AI hanya
        #  menulis penanda `[TABEL 1.1: Bayangan Tongkat - Waktu, Posisi
        #  Matahari, Bayangan]` tanpa data baris. Kalau entri kosong tetap
        #  dikembalikan, perakit akan mencari id yang sama di fallback dan
        #  memakai tabel EKONOMI DIGITAL ⇒ bocor topik.
        #  Obat: buang entri tanpa baris. Tidak ada tabel lebih baik
        #  daripada tabel yang isinya bohong.
        berisi = {k: v for k, v in ada_pipeline.items() if v.get('rows')}
        kosong = sorted(set(ada_pipeline) - set(berisi))
        if kosong:
            log.warning('[tabel] %s tabel KOSONG (rows=[]) dibuang, bukan '
                        'diisi contoh: %s', len(kosong), kosong)
        if berisi:
            log.info('[tabel] %s tabel berisi dari pipeline (fallback TIDAK '
                     'dipakai)', len(berisi))
            return berisi
        log.warning('[tabel] SEMUA tabel pipeline kosong — tidak ada tabel '
                    'yang dirakit (lebih baik kosong daripada salah topik)')
        return {}

    log.warning('[tabel] pipeline tidak menghasilkan tabel — fallback contoh '
                'dipakai (%s entri). Isinya CONTOH, bukan dari naskah buku!',
                len(TABEL_DATA_FALLBACK))
    return dict(TABEL_DATA_FALLBACK)

TABEL_DATA_FALLBACK = {
    "1.1": {
        "title": "Perbandingan Ekonomi Tradisional dan Digital",
        "headers": ["Aspek", "Ekonomi Tradisional", "Ekonomi Digital"],
        "rows": [
            ["Aset Utama", "Properti fisik & modal mesin", "Data & algoritma"],
            ["Batasan Geografis", "Terbatas radius lokal", "Pasar global tanpa batas"],
            ["Model Interaksi", "Tatap muka & fisik", "Digital & tanpa batas"],
        ]
    },
    "1.2": {
        "title": "Perbandingan Aset Tradisional dengan Aset Digital",
        "headers": ["Pilar Ekonomi", "Pendekatan Tradisional", "Pendekatan Digital"],
        "rows": [
            ["Platform Interaksi", "Pasar fisik & tatap muka", "Aplikasi & pasar dua sisi"],
            ["Sumber Data", "Buku catatan & ingatan", "Riwayat perilaku digital"],
            ["Jaringan Akses", "Jalan & transportasi", "Sinyal seluler & internet"],
        ]
    },
    "1.3": {
        "title": "Aktor Utama Ekonomi Digital dan Perannya",
        "headers": ["Aktor", "Peran", "Contoh"],
        "rows": [
            ["Startup", "Pengembang inovasi cepat", "Gojek, Tokopedia"],
            ["Tech Giant", "Penyedia platform & skalabilitas", "Google, Meta, Amazon"],
            ["Pemerintah", "Regulasi & infrastruktur", "Kemkominfo, Bank Indonesia"],
        ]
    },
    "2.3": {
        "title": "Perbandingan Karakteristik Bisnis Tradisional dan Digital",
        "headers": ["Aspek", "Bisnis Tradisional", "Bisnis Digital"],
        "rows": [
            ["Aset Fisik", "Gudang, mesin, karyawan", "Server, kode, data"],
            ["Skalabilitas", "Linear dengan modal", "Eksponensial"],
            ["Biaya Marjinal", "Tinggi", "Hampir nol"],
        ]
    },
    "3.1": {
        "title": "Evolusi Preferensi Pembayaran Konsumen",
        "headers": ["Era", "Karakteristik Utama", "Contoh"],
        "rows": [
            ["1990-an", "Tunai & cek", "ATM, transfer bank"],
            ["2010-an", "Kartu debit & kredit", "VISA, Mastercard"],
            ["2020-an", "Digital wallet & QR", "GoPay, OVO, QRIS"],
        ]
    },
    "2.2": {
        "title": "Evolusi Model Pendapatan Ekonomi Digital",
        "headers": ["Model", "Karakteristik", "Contoh"],
        "rows": [
            ["Freemium", "Gratis dasar, bayar premium", "Spotify, Canva"],
            ["Subscription", "Bayar periodik", "Netflix, SaaS"],
            ["Transaction", "Per transaksi", "Marketplace, e-commerce"],
        ]
    },
    "3.3": {
        "title": "Perbandingan Cryptocurrency dan CBDC",
        "headers": ["Aspek", "Cryptocurrency", "CBDC"],
        "rows": [
            ["Penerbit", "Desentralisasi", "Bank Sentral"],
            ["Kontrol", "Blockchain publik", "Bank Sentral"],
            ["Stabilitas", "Volatil", "Stabil"],
        ]
    },
    "1.4": {
        "title": "Sinergi Tiga Pilar Ekonomi Digital",
        "headers": ["Pilar", "Fungsi", "Dampak"],
        "rows": [
            ["Platform", "Mempertemukan penjual dan pembeli", "Network effect"],
            ["Data", "Bahan baku algoritma", "Personalisasi & prediksi"],
            ["Konektivitas", "Infrastruktur akses internet", "Jangkauan global"],
        ]
    },
    "2.1": {
        "title": "Perbandingan Network Effect di Platform Digital",
        "headers": ["Platform", "Jenis Network Effect", "Skala"],
        "rows": [
            ["Gojek", "Two-sided (driver & rider)", "Nasional"],
            ["Tokopedia", "Two-sided (seller & buyer)", "Nasional"],
            ["WhatsApp", "Direct (user & user)", "Global"],
        ]
    },
    "2.4": {
        "title": "Strategi Kompetitif Raksasa Digital",
        "headers": ["Perusahaan", "Strategi Utama", "Benteng Pertahanan"],
        "rows": [
            ["Google", "Search dominance", "Data index terbesar"],
            ["Amazon", "E-commerce ecosystem", "Logistik + Prime"],
            ["Meta", "Social graph", "Network effect 3B+ users"],
        ]
    },
    "3.2": {
        "title": "Perbandingan Layanan Keuangan Tradisional dan Digital",
        "headers": ["Kriteria", "Perbankan Konvensional", "Fintech"],
        "rows": [
            ["Proses", "1-4 minggu", "24 jam"],
            ["Agunan", "Wajib fisik", "Tidak wajib"],
            ["Jangkauan", "Kota besar", "Nasional via app"],
        ]
    },
    "3.4": {
        "title": "Evolusi Teknologi dan Implikasi Ekonomi",
        "headers": ["Fase", "Teknologi Inti", "Implikasi Pasar"],
        "rows": [
            ["Web 1.0", "Halaman statis", "Konsumsi informasi"],
            ["Web 2.0", "Media sosial", "Partisipasi & interaksi"],
            ["Web 3.0", "Blockchain & AI", "Kepemilikan desentralisasi"],
        ]
    },
}

# === KONFIGURASI BUKU ===
BUKU = {
    "judul": "EKONOMI DIGITAL",
    "subjudul": "Transformasi Bisnis di Era Teknologi",
    "penulis": "Syahrul Alim, S.TP., M.M., DBA",
    "institusi": "Universitas Pelita Bangsa",
    "tahun": "2026",
    "ukuran": "B5",
}

FONT_NAMA = "Times New Roman"
FONT_SIZE = Pt(12)

#  Isi `_ASLI` SEKARANG — `BUKU` sudah ada. Dipakai `siapkan()` untuk memulihkan
#  global setelah satu buku dirakit (anti pencemaran lintas buku).
_ASLI.update({'OUT_DIR': OUT_DIR, 'VISUAL_DIR': VISUAL_DIR,
              'DOCX_OUT': DOCX_OUT, 'BUKU': dict(BUKU)})

def set_font(run, size=FONT_SIZE, bold=False, italic=False):
    run.font.name = FONT_NAMA
    run.font.size = size
    run.bold = bold
    run.italic = italic
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), FONT_NAMA)
    rFonts.set(qn('w:hAnsi'), FONT_NAMA)
    rFonts.set(qn('w:cs'), FONT_NAMA)

def _tata_blok_paragraf(teks, setelah_judul=False, boleh_daftar=None):
    """Terapkan SOT paragraf: pecah paragraf panjang + ubah jadi daftar.

    SOT 2.7: ideal 3-5 kalimat, MAKS 7 kalimat / 200 kata ⇒ lebih dipecah.
    SOT 3.1: maks 4 paragraf beruntun tanpa variasi ⇒ dijadikan daftar.
    SOT 2.4: paragraf pertama setelah judul TIDAK diinden (ditangani pemanggil).

    ⚠️ `boleh_daftar` = PUTUSAN JEV BUKU (SOT_JEV_BUKU_UMUM_20OKT2026 §3).
       Jev menilai apakah paragraf ini benar-benar merangkai hal SETARA.
       Terukur 20 Okt 2026: regex saja mengubah narasi buku anak jadi
       **170 butir daftar** (cerita rusak). Dengan pagar Jev: 10 dari 11
       paragraf TETAP paragraf.
       · True  → boleh jadi daftar
       · False → WAJIB tetap paragraf (Jev bilang bukan rentetan)
       · None  → Jev tak tersedia ⇒ pakai jalur lama (jangan memblokir terbit)

    Mengembalikan list (jenis, teks): ('paragraf'|'daftar', isi).
    TIDAK mengarang kata — hanya memindahkan batas & mengubah bentuk.
    """
    if not teks or not teks.strip():
        return []

    #  Teks yang SUDAH berbentuk daftar (dari penulis) → jangan diutak-atik.
    if tata_paragraf.ada_daftar(teks):
        return [('paragraf_asli', teks)]

    hasil = []
    #  ⚠️ URUTAN WAJIB: PECAH dulu, baru pertimbangkan daftar.
    #  Terukur 20 Okt 2026: kalau `jadikan_daftar` jalan lebih dulu, paragraf
    #  8 kalimat langsung jadi daftar (karena Jev bilang boleh) dan TIDAK
    #  PERNAH dipecah ⇒ gerbang menemukan paragraf >7 kalimat. Dengan urutan
    #  ini, tiap potongan diuji sendiri: yang 8 kalimat dipecah dulu, lalu
    #  potongannya masing-masing dinilai layak-daftar atau tidak.
    for p in tata_paragraf.pecah_paragraf(teks):
        daftar = tata_paragraf.jadikan_daftar(p)
        if daftar and tata_paragraf.jumlah_kata(p) < 160:
            #  PAGAR JEV: daftar HANYA kalau Jev bilang boleh (True).
            #  False = Jev bilang bukan rentetan ⇒ tetap paragraf.
            #  None  = Jev tak tersedia ⇒ JANGAN jadi daftar (aman): narasi
            #          yang salah jadi daftar merusak cerita, sedangkan
            #          paragraf yang seharusnya daftar cuma kurang menarik.
            if boleh_daftar is True:
                hasil.append(('daftar', daftar))
            else:
                hasil.append(('paragraf', p))
        else:
            hasil.append(('paragraf', p))
    return hasil


def _tulis_daftar(doc, teks_daftar):
    """Tulis daftar sebagai LIST ASLI Word (SOT 4.4), bukan ketik manual."""
    baris = [b for b in teks_daftar.split('\n') if b.strip()]
    for i, b in enumerate(baris):
        isi = b.strip()
        bernomor = bool(re.match(r'^\d{1,2}[.)]\s', isi))
        #  Buang penanda mentah dari teks — Word yang menggambar nomornya
        isi = re.sub(r'^(?:[-•*–—]|\d{1,2}[.)]|[a-z][.)])\s+', '', isi)
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = Pt(0)
        pf.space_after = Pt(2)
        pf.line_spacing = 1.15
        pf.left_indent = Pt(tata_paragraf.INDEN_EM * 2)      # gantung
        pf.first_line_indent = Pt(-tata_paragraf.INDEN_EM)   # hanging
        gaya = 'List Number' if bernomor else 'List Bullet'
        try:
            p.style = doc.styles[gaya]
        except KeyError:
            pass
        r = p.add_run(isi)
        set_font(r)


def add_para(doc, text="", size=FONT_SIZE, bold=False, italic=False,
             align=None, space_before=0, space_after=6, indent=None,
             first_line_indent=None, line_spacing=1.15, page_break_before=False,
             inden_otomatis=False):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line_spacing
    #  SOT 2.6 (S3 PLOS Rule 3): jangan tinggalkan 1 baris menggantung
    pf.widow_control = True
    if align == 'center':
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == 'justify':
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == 'right':
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if indent is not None:
        pf.left_indent = Cm(indent)
    if first_line_indent is not None:
        pf.first_line_indent = Cm(first_line_indent)
    elif inden_otomatis:
        #  SOT 2.2: inden buku = 1 em (11 pt), BUKAN 0,5 inci.
        #  🚨 JEBAKAN TERUKUR (20 Okt 2026): `size` di sini SUDAH berupa
        #  objek `Pt` (FONT_SIZE = Pt(11) = 152400 EMU). Membungkusnya lagi
        #  dengan Pt(size) MENGALIKAN 12700 lagi → 1.935.480.000 EMU
        #  (152.400 pt) sehingga inden jadi tak bermakna.
        #  Ambil nilai pt-nya dulu, baru bungkus.
        _pt = size.pt if hasattr(size, 'pt') else float(size)
        pf.first_line_indent = Pt(_pt)
    if page_break_before:
        pf.page_break_before = True
    if text:
        r = p.add_run(text)
        set_font(r, size=size, bold=bold, italic=italic)
    return p

def add_page_number_footer(section):
    """Footer dengan field PAGE di tengah."""
    footer = section.footer
    footer.is_linked_to_previous = False
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    # Hapus isi default
    for r in list(p.runs):
        r._element.getparent().remove(r._element)
    # Field PAGE
    run = p.add_run()
    set_font(run, size=Pt(10))
    fldChar1 = OxmlElement('w:fldChar'); fldChar1.set(qn('w:fldCharType'), 'begin')
    instrText = OxmlElement('w:instrText'); instrText.set(qn('xml:space'), 'preserve'); instrText.text = ' PAGE '
    fldChar2 = OxmlElement('w:fldChar'); fldChar2.set(qn('w:fldCharType'), 'end')
    run._element.append(fldChar1)
    run._element.append(instrText)
    run._element.append(fldChar2)

def set_cell_border(cell, **kwargs):
    """Set border pada cell (none = hapus border)."""
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcBorders = OxmlElement('w:tcBorders')
    for edge in ('start', 'top', 'end', 'bottom', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            element = OxmlElement(f'w:{edge}')
            for k, v in edge_data.items():
                element.set(qn(f'w:{k}'), str(v))
            tcBorders.append(element)
    tcPr.append(tcBorders)

def set_cell_width(cell, width_twips):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcW = OxmlElement('w:tcW')
    tcW.set(qn('w:w'), str(width_twips))
    tcW.set(qn('w:type'), 'dxa')
    tcPr.append(tcW)

def set_table_fixed_layout(tbl, widths):
    """Set tabel fixed layout + lebar kolom."""
    tblPr = tbl._tbl.tblPr
    # tblLayout fixed
    layout = OxmlElement('w:tblLayout')
    layout.set(qn('w:type'), 'fixed')
    tblPr.append(layout)
    # tblW
    tblW = OxmlElement('w:tblW')
    tblW.set(qn('w:w'), str(sum(widths)))
    tblW.set(qn('w:type'), 'dxa')
    tblPr.append(tblW)
    # Grid
    grid = tbl._tbl.find(qn('w:tblGrid'))
    if grid is not None:
        tbl._tbl.remove(grid)
    grid = OxmlElement('w:tblGrid')
    for w in widths:
        gc = OxmlElement('w:gridCol')
        gc.set(qn('w:w'), str(w))
        grid.append(gc)
    tbl._tbl.insert(list(tbl._tbl).index(tblPr) + 1, grid)

def no_border_table(tbl):
    """Hapus border tabel."""
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement(f'w:{edge}')
        el.set(qn('w:val'), 'none')
        el.set(qn('w:sz'), '0')
        el.set(qn('w:space'), '0')
        borders.append(el)
    tblPr.append(borders)

def add_isbn_page(doc):
    """Halaman 2: Lembar hak cipta/ISBN — 1 halaman kosong minimalis."""
    add_para(doc, "", space_after=300)
    add_para(doc, f"© {BUKU['tahun']} {BUKU['penulis']}", align='center', space_before=200, space_after=12)
    add_para(doc, "", space_after=6)
    add_para(doc, "Hak cipta dilindungi undang-undang.", align='center', space_after=6)
    add_para(doc, "Dilarang memperbanyak atau mengutip sebagian atau seluruh isi buku ini", align='center', space_after=6)
    add_para(doc, "tanpa izin tertulis dari penerbit.", align='center', space_after=6)
    add_para(doc, "", space_after=150)
    add_para(doc, "ISBN: ____________________", align='center', space_after=6)
    add_para(doc, "", space_after=100)
    add_para(doc, "Penerbit: ____________________", align='center', space_after=6)
    add_para(doc, "", space_after=6)
    add_para(doc, "Dicetak di Indonesia", align='center', space_after=6)
    doc.add_page_break()

def add_kata_pengantar(doc, judul, penulis, institusi):
    """Kata Pengantar — MENGIKUTI JUDUL BUKU, bukan buku contoh.

    🚨 JEBAKAN TERUKUR 19 Okt 2026: versi lama menulis pengantar mati tentang
       "ekonomi digital". Buku berjudul "Petualangan di Laut" keluar dengan
       pengantar ekonomi digital ⇒ gerbang assembly menangkapnya (1 GAGAL).
    """
    add_para(doc, "KATA PENGANTAR", size=Pt(16), bold=True, align='center', space_before=12, space_after=12)

    judul_bersih = (judul or 'buku ini').strip() or 'buku ini'
    pengantar = f"""Buku ini disusun untuk memberi pembaca pemahaman yang utuh tentang {judul_bersih}. Banyak pembaca mengenal topiknya sekilas, tetapi belum sempat memahaminya secara berurutan — dari dasar, ke penerapan, sampai ke hal yang sering ditanyakan.

Karena itu, setiap bab disusun mengalir dan saling menyambung. Penjelasan dimulai dari hal yang paling dekat dengan pengalaman pembaca, lalu bertahap menuju gagasan yang lebih dalam. Setiap istilah penting dijelaskan saat pertama kali muncul, sehingga pembaca tidak perlu berhenti untuk membuka kamus.

Buku ini ditujukan bagi siapa pun yang ingin memahami {judul_bersih} tanpa merasa sedang membaca pelajaran yang berat. Semoga buku ini bermanfaat dan menemani pembaca memahami topiknya dengan lebih percaya diri. Selamat membaca."""

    for para in pengantar.split('\n\n'):
        add_para(doc, para.strip(), align='justify', space_after=10)

    add_para(doc, "", space_after=20)
    add_para(doc, f"{penulis}", align='right', space_after=6)
    add_para(doc, f"{institusi}", align='right', space_after=6)
    doc.add_page_break()

def add_daftar_isi(doc, outline):
    """Daftar isi dengan dot leader."""
    add_para(doc, "DAFTAR ISI", size=Pt(16), bold=True, align='center', space_before=12, space_after=12)

    # Kata Pengantar
    p = add_para(doc, "", space_after=6)
    r = p.add_run("Kata Pengantar")
    set_font(r)
    p.paragraph_format.tab_stops.add_tab_stop(Cm(15.5), WD_ALIGN_PARAGRAPH.RIGHT, leader=1)  # leader=1 = dot
    r2 = p.add_run("\t")
    set_font(r2)
    r3 = p.add_run("iii")
    set_font(r3)

    for bab_num, bab_data in outline.items():
        # Judul bab
        p = add_para(doc, "", space_before=6, space_after=3)
        r = p.add_run(f"BAB {bab_num}. {bab_data['title']}")
        set_font(r, bold=True)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.5), WD_ALIGN_PARAGRAPH.RIGHT, leader=1)
        r2 = p.add_run("\t")
        set_font(r2)

        # Sub-bab
        for sub_num, sub_title, _ in bab_data['subs']:
            p = add_para(doc, "", space_after=3, indent=0.8)
            r = p.add_run(f"{sub_num} {sub_title}")
            set_font(r, size=Pt(11))
            p.paragraph_format.tab_stops.add_tab_stop(Cm(15.5), WD_ALIGN_PARAGRAPH.RIGHT, leader=1)
            r2 = p.add_run("\t")
            set_font(r2, size=Pt(11))

    # Back matter
    for section in ["Glosarium", "Indeks", "Daftar Pustaka", "Tentang Penulis"]:
        p = add_para(doc, "", space_before=3, space_after=3)
        r = p.add_run(section)
        set_font(r)
        p.paragraph_format.tab_stops.add_tab_stop(Cm(15.5), WD_ALIGN_PARAGRAPH.RIGHT, leader=1)
        r2 = p.add_run("\t")
        set_font(r2)

    doc.add_page_break()

# Penanda di UJUNG baris panjang (kejadian nyata): penulis menaruh
# "### 1.1 Judul <seluruh isi> [TABEL 1.1: ...] <isi lagi> [DIAGRAM 1.1: ...]"
_POLA_PENANDA = re.compile(r'\[(TABEL|DIAGRAM)\s+\d+\.\d+[^\]]*\]', re.IGNORECASE)
# Penanda di TENGAH baris yang terpotong `[TABEL 1.1: Judul` tanpa `]`
# (kalimat judul memuat `]` seperti "[Tabel 3.1 ...]"). Ditangkap sampai
# akhir baris supaya gambar/tabel tidak hilang hanya karena kurung tutup.
_POLA_PENANDA_GADUH = re.compile(r'\[(TABEL|DIAGRAM)\s+\d+\.\d+[^\n]*$',
                                 re.IGNORECASE)


def _pecah_penanda(line):
    """Pecah satu baris jadi potongan teks + penanda UTUH.

    JEJAK AKAR (20 Okt 2026): penulis (LLM) menaruh `[TABEL 1.1: ...]` dan
    `[DIAGRAM 1.2: ...]` di TENGAH baris panjang — sub-bab + seluruh isi
    menyatu jadi satu baris. Pembaca lama hanya mengenali penanda yang ada
    di AWAL baris (`.startswith('[TABEL')`), sehingga penanda itu tenggelam
    sebagai "paragraf" biasa. TERUKUR: `parse_diagram_marker()` menemukan
    12 diagram di naskah, tetapi blok diagram di perakit = 0 di keenam bab.
    ⇒ Diagram (dan tabel) hilang walau datanya ADA.

    TIDAK memakai `.startswith()` lagi — penanda diburu di posisi mana pun.
    """
    potongan, sisa = [], line
    while True:
        m = _POLA_PENANDA.search(sisa) or _POLA_PENANDA_GADUH.search(sisa)
        if not m:
            if sisa.strip():
                potongan.append(('teks', sisa.strip()))
            return potongan
        sebelum = sisa[:m.start()].strip()
        if sebelum:
            potongan.append(('teks', sebelum))
        potongan.append(('penanda', m.group(0).strip()))
        sisa = sisa[m.end():]


def _baris_judul_bernomor(isi):
    """Baris ini judul sub-bab bernomor? ("1.1 Judul", "2.3.1 Judul")

    PAGAR (jangan terlalu rakus — terukur 20 Okt 2026):
      · pola: angka.angka[.angka] + spasi + teks
      · teks judul MAKS 12 kata
      · TIDAK diakhiri titik (kalimat diakhiri titik)
      · tidak memuat titik dua di akhir
    """
    if not isi or len(isi) > 200:
        return False
    m = re.match(r'^\d{1,2}\.\d{1,2}(?:\.\d{1,2}){0,2}\s+(\S.*)$', isi)
    if not m:
        return False
    judul = m.group(1).strip()
    if judul.endswith('.') or judul.endswith(':'):
        return False
    return len(judul.split()) <= 12


#  Pola judul sub-bab TANPA nomor yang MENEMPEL dengan isinya
#  ("Matahari, Suhu, dan Bayangan di Sepanjang Hari Pagi tadi, Dinda…").
#  Terukur 20 Okt 2026: naskah hasil pipeline menempelkan judul sub-bab
#  langsung ke kalimat pertama TANPA pemisah apa pun ⇒ 5 blok @2.800
#  karakter masuk sebagai satu "paragraf" 67 kalimat.
_POLA_JUDUL_TEMPEL = re.compile(
    r'^(?P<judul>[A-Z][^.!?]{8,70}?)\s+'
    r'(?P<awal>(?:Pagi|Siang|Sore|Malam|Pernahkah|Bayangkan|Coba|Ayo|Mari|Sekarang|'
    r'Ketika|Saat|Setelah|Sebelum|Pada|Di|Dulu|Kini|Namun|Tetapi|Selain|Jika|Bila|'
    r'Kalau|Bagaimana|Mengapa|Apa|Siapa|Kamu|Kita|Mereka|Ia|Dinda|Banyak|Ada|Setiap|'
    r'Angka|Gambar|Trik|Bentuk|Awan|Air|Angin|Matahari|Hujan|Langit|Suhu|Udara)\b)')


def _pecah_judul_tempel(isi):
    """Pisahkan judul sub-bab yang MENEMPEL di depan isi paragraf.

    Mengembalikan (judul, sisa_isi) atau (None, isi) bila tidak menempel.

    PAGAR (jangan menebak — terukur 20 Okt 2026):
      · judul 8–70 karakter, diawali huruf kapital
      · TIDAK berakhir titik, TIDAK memuat titik sama sekali
        (judul = frasa, bukan kalimat)
      · sisa isi diawali kata umum pembuka kalimat (lihat pola di atas)
      · sisa isi minimal 120 karakter (kalau pendek, itu bukan judul)
    """
    if not isi or len(isi) < 180:
        return None, isi
    m = _POLA_JUDUL_TEMPEL.match(isi)
    if not m:
        return None, isi
    judul = m.group('judul').strip()
    sisa = isi[m.end('judul'):].strip()
    #  Judul tidak boleh memuat titik/koma berlebih — itu kalimat.
    if '.' in judul or ',' in judul and len(judul.split()) > 12:
        return None, isi
    if len(judul.split()) > 10:
        return None, isi
    if len(sisa) < 120:
        return None, isi
    return judul, sisa


def parse_bab_file(content):
    """Parse bab txt content jadi struktur: headings + paragraphs + markers.

    20 Okt 2026 — penanda `[TABEL ...]`/`[DIAGRAM ...]` dikenali di POSISI
    MANA PUN di dalam baris (lihat `_pecah_penanda`), bukan hanya di awal.

    ⚠️ JEBAKAN YANG SUDAH TERBUKTI (jangan diulang): `startswith('### ')`
    lalu `continue` membuat SELURUH sisa baris — termasuk penanda di
    belakangnya — dibuang sebagai judul. Karena LLM menulis
    "### 1.2 Judul <isi> [DIAGRAM 1.2: ...]", akibatnya sub_heading MENELAN
    diagram + isi sub-bab. Yang benar: penanda DICABUT DULU, baru sisa teks
    diuji sebagai judul.
    """
    blocks = []
    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        potongan = _pecah_penanda(line)
        #  ① Penanda dikeluarkan lebih dulu — jangan sampai tertelan judul.
        for jenis, isi in potongan:
            if jenis == 'penanda':
                blok = _blok_penanda(isi)
                if blok:
                    blocks.append(('__penanda__', blok))
        #  ② Teks sisa: judul HANYA kalau barisnya memang murni judul.
        for jenis, isi in potongan:
            if jenis != 'teks':
                continue
            if isi.startswith('## '):
                blocks.append(('bab_heading', isi[3:].strip()))
            elif isi.startswith('### '):
                sisa = isi[4:].strip()
                if sisa:
                    blocks.append(('sub_heading', sisa))
            elif _baris_judul_bernomor(isi):
                #  SOT 2.4: judul sub-bab bernomor ("1.1 Pengamatan Cuaca")
                #  WAJIB dikenali sebagai sub_heading. Tanpa ini, judul
                #  dianggap paragraf ⇒ paragraf sesudahnya ikut berinden
                #  padahal seharusnya rata kiri (terukur 20 Okt 2026).
                blocks.append(('sub_heading', isi))
            elif isi:
                #  Judul sub-bab yang MENEMPEL dengan isinya → dipisah dulu,
                #  supaya (a) judul dikenali, (b) isinya bisa dipecah jadi
                #  paragraf wajar. Terukur 20 Okt 2026: tanpa ini, satu
                #  "paragraf" bisa 67 kalimat / 2.800 karakter.
                _judul, _sisa = _pecah_judul_tempel(isi)
                if _judul:
                    blocks.append(('sub_heading', _judul))
                    blocks.append(('paragraf', _sisa))
                else:
                    blocks.append(('paragraf', isi))
    #  ③ Penanda dipindahkan ke urutan aslinya: setelah blok teks di depannya
    #     dan sebelum blok teks di belakangnya. Dikerjakan per baris supaya
    #     urutan naskah tidak berubah.
    hasil, tunggu = [], []
    for tipe, isi in blocks:
        if tipe == '__penanda__':
            tunggu.append(isi)
        else:
            for p in tunggu:
                hasil.append(p)
            tunggu = []
            hasil.append((tipe, isi))
    hasil.extend(tunggu)
    return hasil


def _blok_penanda(penanda):
    """Ubah penanda UTUH jadi blok tabel/diagram — atau None kalau tak dipakai."""
    if re.match(r'(?i)^\[TABEL\s', penanda):
        m = re.search(r'(\d+\.\d+)', penanda)
        if not m:
            return None
        tid = m.group(1)
        data = load_tabel_data().get(tid, {})
        # Tanpa data → jangan tampilkan placeholder kosong (perilaku lama).
        return ('tabel_marker', penanda) if data and data.get('rows') else None
    if re.match(r'(?i)^\[DIAGRAM\s', penanda):
        return ('diagram_marker', penanda)
    return None

def add_bab(doc, bab_num, bab_data, bab_text):
    """Tambah bab ke docx."""
    # Bab heading dengan page break
    add_para(doc, f"BAB {bab_num}", size=Pt(16), bold=True, align='center',
             space_before=0, space_after=6, page_break_before=True)
    add_para(doc, bab_data['title'], size=Pt(16), bold=True, align='center', space_after=12)

    #  ── JEV BUKU UMUM = JEV DI DEPAN (SOT 20 Okt 2026) ──────────────────
    #  Prinsip induk Bos (08 Okt): "selalu nomor satukan jev dulu".
    #  Jev membaca BENTUK naskah lebih dulu; mesin merakit ikut jawaban Jev.
    #  Regex tetap ada sebagai CADANGAN kalau Jev mati — jangan sampai buku
    #  gagal terbit gara-gara Jev gangguan sesaat.
    blocks = None
    _peta_jev = None
    try:
        import jev_buku_umum as _JB
        blocks, _peta_jev = _JB.blok_buku(bab_text)
        _j = (_peta_jev or {}).get('jumlah') or {}
        log.info('[buku] Jev bentuk bab %s: %s judul · %s isi · ragu %s · '
                 'gagal %s · cache %s · waktu %s',
                 bab_num, _j.get('judul'), _j.get('isi'),
                 len((_peta_jev or {}).get('goyang') or []),
                 _j.get('gagal'), (_peta_jev or {}).get('dari_cache'),
                 (_peta_jev or {}).get('waktu'))
        if not blocks:
            blocks = None
    except Exception as e:                      # noqa: BLE001
        log.warning('[buku] Jev bentuk GAGAL (%s) — pakai jalur regex', e)
        blocks = None
    if blocks is None:
        blocks = parse_bab_file(bab_text)
        log.info('[buku] bab %s dirakit lewat CADANGAN regex (%s blok)',
                 bab_num, len(blocks))
    total_blocks = len(blocks)

    #  🚨 CACAT TERUKUR 20 Okt 2026 — JUDUL BAB DITULIS TIGA KALI.
    #  `add_bab` sudah menulis "BAB 1" + judul bab di atas (2 baris), lalu
    #  blok PERTAMA naskah (`## BAB 1. Judul …`) ikut dirakit sebagai
    #  heading ⇒ .docx berisi:
    #      BAB 1
    #      Mengamati Langit: Dari Matahari Hingga Awan
    #      BAB 1. Mengamati Langit: Dari Matahari Hingga Awan   ← DOBEL
    #  Obat: blok pertama yang MASIH mengulang judul bab DIBUANG. Cek pakai
    #  kunci tanpa nomor & tanpa "BAB n", sebab teksnya tidak persis sama.
    def _kunci(t):
        t = re.sub(r'^#+\s*', '', str(t)).strip()
        t = re.sub(r'^BAB\s+\d+[.:]?\s*', '', t, flags=re.I)
        t = re.sub(r'^\d+(?:\.\d+)*[.)]?\s*', '', t)
        return t.lower().strip().rstrip('.:')

    _judul_bab = _kunci(bab_data.get('title', ''))
    _dibuang = 0
    while blocks and _judul_bab and _kunci(blocks[0][1] if isinstance(blocks[0], (tuple, list)) else blocks[0]) == _judul_bab:
        _jenis = blocks[0][0] if isinstance(blocks[0], (tuple, list)) else '?'
        #  Hanya heading yang dibuang — paragraf isi TIDAK, walau teksnya
        #  kebetulan sama dengan judul.
        if _jenis not in ('heading', 'judul', 'sub_heading', 'bab'):
            break
        blocks.pop(0)
        _dibuang += 1
    if _dibuang:
        log.info('[buku] bab %s: %s blok judul dobel dibuang', bab_num, _dibuang)

    #  🚨 CACAT TERUKUR 20 Okt 2026 — SUB-JUDUL DOBEL.
    #  Jev mengenali `1.1 Matahari…` sebagai `sub_heading` — DAN baris polos
    #  sesudahnya `Matahari…` JUGA sebagai `sub_heading` (Jev benar: teksnya
    #  memang judul). Perakit lalu menulis DUA heading berturut-turut.
    #  ⚠️ JEBAKAN: versi pertama hanya memeriksa jenis `paragraf` ⇒ tidak
    #  pernah menangkap, sebab blok keduanya `sub_heading`. Jadi yang harus
    #  diperiksa = SESAMA heading yang teksnya sama.
    def _kunci2(t):
        t = re.sub(r'^#+\s*', '', str(t)).strip()
        t = re.sub(r'^BAB\s+\d+[.:]?\s*', '', t, flags=re.I)
        t = re.sub(r'^\d+(?:\.\d+)*[.)]?\s*', '', t)
        return t.lower().strip().rstrip('.:')

    _JUDUL = ('sub_heading', 'heading', 'judul', 'bab_heading', 'bab')
    _bersih = []
    for _blk in blocks:
        _jns = _blk[0] if isinstance(_blk, (tuple, list)) else '?'
        _isi = _blk[1] if isinstance(_blk, (tuple, list)) else _blk
        if _jns in _JUDUL and _bersih:
            _sblm = _bersih[-1]
            _sjns = _sblm[0] if isinstance(_sblm, (tuple, list)) else '?'
            _sisi = _sblm[1] if isinstance(_sblm, (tuple, list)) else _sblm
            #  Heading berurutan dengan teks SAMA ⇒ yang kedua dibuang.
            #  Jangan sentuh heading nomor berbeda (1.1 vs 1.2).
            if _sjns in _JUDUL and _kunci2(_isi) == _kunci2(_sisi):
                log.info('[buku] sub-judul dobel dibuang: %s', str(_isi)[:50])
                continue
        _bersih.append(_blk)
    _dibuang2 = len(blocks) - len(_bersih)
    if _dibuang2:
        log.info('[buku] bab %s: %s heading pengulang dibuang',
                 bab_num, _dibuang2)
        blocks = _bersih

    #  SOT 2.4: paragraf pertama setelah judul bab = rata kiri (tanpa inden).
    baru_setelah_judul = True

    # === Posisi ilustrasi: RANDOM di tengah bab (40-60% paragraf) ===
    ilustrasi_path = os.path.join(VISUAL_DIR, f"ilustrasi_bab{bab_num}.png")
    ilustrasi_inserted = False
    if os.path.exists(ilustrasi_path):
        # Target posisi: antara 40-60% dari total blocks
        target_pos = random.randint(int(total_blocks * 0.4), int(total_blocks * 0.6))
        # Auto-crop whitespace
        try:
            from PIL import Image as PILImage, ImageChops
            img = PILImage.open(ilustrasi_path)
            bg = PILImage.new(img.mode, img.size, (255, 255, 255))
            diff = ImageChops.difference(img, bg)
            bbox = diff.getbbox()
            if bbox:
                cropped = img.crop(bbox)
                cropped.save(ilustrasi_path)
        except:
            pass

    for idx, blk in enumerate(blocks):
        #  Blok jalur JEV = 3-elemen (jenis, isi, meta) — meta membawa
        #  putusan Jev B3 ('boleh_daftar'). Jalur regex = 2-elemen.
        if len(blk) == 3:
            block_type, content, _meta = blk
        else:
            block_type, content = blk
            _meta = {}
        _boleh_meta = (_meta or {}).get('boleh_daftar')
        #  Indeks baris ASAL (untuk jejak/log saja) — pagar Jev diambil
        #  dari META, bukan dari indeks, supaya tak bisa meleset saat satu
        #  baris jadi beberapa blok (penanda tabel/diagram dicabut).
        # Insert ilustrasi di posisi target
        if ilustrasi_inserted is False and ilustrasi_path and os.path.exists(ilustrasi_path) and idx >= target_pos:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run()
            run.add_picture(ilustrasi_path, width=Cm(12))
            add_para(doc, f"Gambar {bab_num}.0 Ilustrasi: {bab_data['title']}",
                     size=Pt(10), italic=True, align='center', space_after=12)
            ilustrasi_inserted = True

        if block_type == 'bab_heading':
            continue  # sudah di-add manual
        elif block_type == 'sub_heading':
            add_para(doc, content, size=Pt(14), bold=True, space_before=12, space_after=8)
            #  SOT 2.4 (S1 CMOS faq0223): paragraf pertama SETELAH judul
            #  dimulai rata kiri — inden tidak diperlukan karena batas
            #  paragraf sudah jelas dari judulnya.
            baru_setelah_judul = True
        elif block_type == 'paragraf':
            #  PAGAR JEV BUKU: boleh tidaknya paragraf ini jadi daftar
            #  DIPUTUSKAN JEV (B3) — dibawa lewat META blok, bukan indeks.
            bloks = _tata_blok_paragraf(content, baru_setelah_judul,
                                        boleh_daftar=_boleh_meta)
            for idx_blok, (blok, isi_blok) in enumerate(bloks):
                #  SOT 2.4: HANYA paragraf PERTAMA setelah judul yang rata kiri.
                #  Kalau blok pertama ternyata jadi daftar, paragraf
                #  berikutnya WAJIB berinden.
                inden = not (baru_setelah_judul and idx_blok == 0)
                if blok == 'daftar':
                    _tulis_daftar(doc, isi_blok)
                elif blok == 'paragraf_asli':
                    baris = [b for b in isi_blok.split('\n') if b.strip()]
                    if len(baris) > 1:
                        _tulis_daftar(doc, isi_blok)
                    else:
                        add_para(doc, isi_blok, align='justify',
                                 space_before=0, space_after=0,
                                 inden_otomatis=inden)
                else:
                    add_para(doc, isi_blok, align='justify',
                             space_before=0, space_after=0,
                             inden_otomatis=inden)
            baru_setelah_judul = False
        elif block_type == 'daftar_pustaka':
            #  Entri pustaka: inden gantung (SOT §3) — baris ke-2 dst menjorok.
            entri = [b.strip() for b in content.split('\n') if b.strip()]
            for i_e, e in enumerate(entri):
                p = doc.add_paragraph()
                pf = p.paragraph_format
                pf.left_indent = Pt(11)
                pf.first_line_indent = Pt(-11)
                pf.space_before = Pt(0)
                #  Jarak antarentri 3 pt, bukan 0 — supaya terbaca terpisah.
                pf.space_after = Pt(3 if i_e < len(entri) - 1 else 0)
                run = p.add_run(e)
                run.font.name = FONT_NAMA
                run.font.size = FONT_SIZE
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif block_type == 'tabel_marker':
            # Parse berbagai format: [TABEL 1.1: ...] atau TABEL 1.1 ... atau [Tabel 3.1 ...]
            m = re.match(r'(?:\[)?(?:TABEL|Tabel)\s+(\d+\.\d+)[:\s]*(.+?)(?:\s*-\s*(.+?))?(?:\])?$', content)
            fallback = False
            if not m:
                m = re.match(r'(?:\[)?(?:TABEL|Tabel)\s+(\d+\.\d+)\s+(.+)', content)
                fallback = True
            if m:
                tid = m.group(1)
                if fallback:
                    ttitle = m.group(2).strip()
                    cols = ['Aspek', 'Penjelasan']
                else:
                    ttitle = m.group(2).strip()
                    cols = [c.strip() for c in m.group(3).split(',')] if m.group(3) else ['Aspek', 'Penjelasan']
                # Cek data tabel dari TABEL_DATA (pipeline JSON + fallback)
                data = load_tabel_data().get(tid, {})
                rows_data = data.get("rows", data.get("data", []))
                headers = data.get("headers", cols)
                #  🚨 CACAT TERUKUR 20 Okt 2026 — TABEL BOHONG.
                #  Versi lama SELALU membuat tabel, walau `rows_data` kosong
                #  (diisi "..." placeholder). Lebih buruk: `load_tabel_data()`
                #  membawa 12 tabel CONTOH ekonomi digital, dan id `1.1`/`1.2`
                #  nyata dipakai buku anak "Mengamati Langit" ⇒ buku langit
                #  berisi tabel "Aset Utama / Ekonomi Tradisional / Gojek".
                #  Obat: TANPA baris data ⇒ tabel TIDAK dirakit sama sekali,
                #  dan alasannya DICATAT. Lebih baik tidak ada tabel
                #  daripada tabel yang isinya tidak nyambung dengan bukunya.
                if not rows_data:
                    log.warning('[buku] tabel %s DILEWATI — pipeline tidak '
                                'memberi baris data (judul: %s). Tabel contoh '
                                'TIDAK dipakai.', tid, ttitle[:50])
                    print(f"       ⚠️ Tabel {tid} dilewati: tidak ada data baris "
                          f"(bukan diisi contoh)")
                    add_para(doc, "", space_after=6)
                    continue
                #  Judul tabel: pakai judul dari PIPELINE kalau ada (sesuai
                #  naskah), bukan judul contoh.
                judul_tabel = data.get('title') or ttitle
                # Caption
                add_para(doc, f"Tabel {tid} {judul_tabel}", bold=True, align='center', space_before=10, space_after=6)
                # Tabel dengan border (comot dari buku ajar: table.style = 'Table Grid')
                n_rows = len(rows_data) + 1
                n_cols = len(headers)
                table = doc.add_table(rows=n_rows, cols=n_cols)
                table.style = 'Table Grid'
                table.alignment = WD_TABLE_ALIGNMENT.CENTER
                # Header
                for ci, h in enumerate(headers):
                    cell = table.rows[0].cells[ci]
                    cell.text = h
                    for pp in cell.paragraphs:
                        pp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        for rr in pp.runs:
                            rr.bold = True; rr.font.size = Pt(10)
                # Data rows
                if rows_data:
                    for ri, row in enumerate(rows_data):
                        for ci in range(n_cols):
                            cell = table.rows[ri+1].cells[ci]
                            cell.text = row[ci] if ci < len(row) else ""
                            for pp in cell.paragraphs:
                                pp.alignment = WD_ALIGN_PARAGRAPH.LEFT
                                for rr in pp.runs:
                                    rr.font.size = Pt(10)
                #  ⚠️ Cabang `else` (isi "..." placeholder) SUDAH DIHAPUS
                #  20 Okt 2026. Sejak `if not rows_data: continue` di atas,
                #  tabel tanpa baris tidak pernah dibuat — jadi cabang ini
                #  kode mati yang menyesatkan. Placeholder "..." itulah yang
                #  membuat pembaca melihat "tabel bohong" tanpa data.
                add_para(doc, "", space_after=6)
        elif block_type == 'diagram_marker':
            # Parse: [DIAGRAM 1.3: Judul - deskripsi] atau DIAGRAM 1.3 Judul
            m = re.match(r'(?:\[)?DIAGRAM\s+(\d+\.\d+)[:\s]*', content)
            if m:
                did = m.group(1)
                img_path = os.path.join(VISUAL_DIR, f"diagram_{did}.png")
                # Caption
                add_para(doc, f"Diagram {did}", bold=True, align='center', space_before=10, space_after=6)
                # Insert image jika PNG ada
                if os.path.exists(img_path):
                    p = doc.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    run = p.add_run()
                    run.add_picture(img_path, width=Cm(14))  # sama dengan buku ajar
                    add_para(doc, "", space_after=6)
                # JANGAN tampilkan "[Diagram akan di-render]" — skip saja
                else:
                    add_para(doc, "", space_after=6)  # skip placeholder

def add_glosarium(doc, glosarium, kosong=False):
    """Glosarium dalam bentuk tabel 2 kolom (Istilah | Definisi).

    `kosong=True` dipakai kalau tidak ada satu pun istilah: halaman tetap
    dibuat (daftar isi menyebutnya), TAPI tabel kosong TIDAK dirakit.
    🚨 TERUKUR 20 Okt 2026: versi lama selalu membuat tabel walau
    `glosarium={}` ⇒ .docx memuat tabel 1x2 berisi header saja.
    """
    from docx.enum.table import WD_TABLE_ALIGNMENT
    add_para(doc, "GLOSARIUM", size=Pt(16), bold=True, align='center',
             space_before=12, space_after=12, page_break_before=True)

    if not glosarium:
        add_para(doc, "Glosarium belum tersedia untuk buku ini.",
                 align='center', italic=True)
        return

    glos_sorted = sorted(glosarium.items(), key=lambda x: x[0].lower())
    table = doc.add_table(rows=len(glos_sorted)+1, cols=2)
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    # Header row
    hdr = table.rows[0].cells
    for ci, header_text in enumerate(['Istilah', 'Definisi']):
        cell = hdr[ci]
        cell.text = ''
        p = cell.paragraphs[0]
        r = p.add_run(header_text); r.bold = True; r.font.size = Pt(12); r.font.name = 'Cambria'
    
    # Data rows
    for ri, (istilah, definisi) in enumerate(glos_sorted):
        row = table.rows[ri+1].cells
        row[0].text = ''
        p = row[0].paragraphs[0]
        r = p.add_run(istilah); r.bold = True; r.font.size = Pt(11); r.font.name = 'Cambria'
        row[1].text = ''
        p = row[1].paragraphs[0]
        r = p.add_run(definisi); r.font.size = Pt(11); r.font.name = 'Cambria'

def add_indeks(doc, glosarium, teks_per_halaman=None):
    """INDEKS SUBJEK + INDEKS NAMA ber-nomor halaman.

    Diperbarui 17 Okt 2026 untuk skill `buku-referensi`:
    dulu fungsi ini hanya menulis DAFTAR ISTILAH tanpa nomor halaman —
    belum layak disebut indeks. Sekarang memakai mesin `indeks_referensi.py`
    (diuji 27 LULUS / 0 GAGAL).

    `teks_per_halaman` = {nomor_halaman: teks}. Kalau None → indeks nama
    kosong & halaman subjek kosong (jujur, bukan dikarang).
    """
    import sys
    if '/opt/data' not in sys.path:
        sys.path.insert(0, '/opt/data')
    try:
        from indeks_referensi import kumpulkan_entri, \
            tulis_indeks_subjek, tulis_indeks_nama
    except ImportError:
        #  titik mundur: perilaku lama (tanpa nomor halaman) — jangan crash
        add_para(doc, "INDEKS", size=Pt(16), bold=True, align='center',
                 space_before=12, space_after=12, page_break_before=True)
        for term in sorted(glosarium.keys()):
            add_para(doc, term, space_after=4)
        return

    subjek, nama = kumpulkan_entri(teks_per_halaman or {}, glosarium=glosarium)
    tulis_indeks_subjek(doc, subjek)
    tulis_indeks_nama(doc, nama)

def add_daftar_pustaka(doc, references):
    add_para(doc, "DAFTAR PUSTAKA", size=Pt(16), bold=True, align='center',
             space_before=12, space_after=12, page_break_before=True)
    for ref in references:
        p = add_para(doc, "", space_after=8)
        pf = p.paragraph_format
        pf.left_indent = Cm(1.0)
        pf.first_line_indent = Cm(-1.0)
        r = p.add_run(ref)
        set_font(r, size=Pt(11))

def add_bio(doc):
    """Tentang Penulis — MENGIKUTI data buku, bukan penulis buku contoh.

    🚨 JEBAKAN TERUKUR 19 Okt 2026: versi lama menulis biografi mati
       ("Syahrul Alim ... ekonomi digital"). Buku milik user lain akan keluar
       dengan biografi orang lain ⇒ harus dari BUKU['penulis']/['institusi'].
    """
    add_para(doc, "TENTANG PENULIS", size=Pt(16), bold=True, align='center',
             space_before=12, space_after=12, page_break_before=True)
    penulis = (BUKU.get('penulis') or '').strip()
    institusi = (BUKU.get('institusi') or '').strip()
    judul = (BUKU.get('judul') or 'buku ini').strip() or 'buku ini'

    if penulis:
        awal = f"{penulis} adalah penulis {judul}."
        if institusi:
            awal += f" Saat ini berafiliasi dengan {institusi}."
        bio = (awal + "\n\n"
               "Penulis menekuni bidang yang dibahas dalam buku ini dan "
               "menyusunnya agar mudah diikuti pembaca dari berbagai latar "
               "belakang.")
    else:
        #  Nama penulis belum diisi user — JANGAN karang nama orang.
        bio = ("Nama penulis belum diisi. Isi lewat menu buku agar halaman ini "
               "menampilkan biodata yang benar.")

    for para in bio.split('\n\n'):
        add_para(doc, para.strip(), align='justify', space_after=10)

def rakit(judul, keluar_dir, outline, glosarium=None, references=None,
          penulis='', institusi='', tahun=None, subjudul='',
          nama_berkas=None, judul_kartu=None):
    """Rakit SEMUA bab jadi SATU .docx. Return dict hasil (bukan cuma print).

    Dipakai rute `/buku/susun` supaya user dapat 1 dokumen utuh — bukan
    6 berkas `babN.txt` terpisah yang tidak bisa dibuka di OnlyOffice.

    TIDAK ada logika assembly baru: fungsi-fungsi di bawah (`add_isbn_page`,
    `add_bab`, `add_glosarium`, ...) dipakai APA ADANYA. Yang ditambah hanya
    (a) setelan per buku lewat `siapkan()`, (b) baca bab yang benar-benar ADA
    (bukan asumsi 1..n), (c) kembalian terukur + pemulihan global di finally.
    """
    global VISUAL_DIR
    #  Folder visual AKAR = tempat pipeline menaruh semua PNG/Tabel
    #  (`OUT/visual/`). Disimpan SEBELUM loop menimpanya per bab, supaya
    #  bisa jadi cadangan saat bab tidak punya folder visual sendiri.
    _VISUAL_AKAR = VISUAL_DIR
    if not os.path.isdir(keluar_dir):
        raise ValueError(f'folder hasil tidak ada: {keluar_dir}')
    nomor = sorted(k for k in (outline or {}) if isinstance(k, int))
    if not nomor:
        raise ValueError('outline tidak punya bab — tidak ada yang dirakit')

    #  Bab yang berkasnya BENAR-BENAR ada di disk. Bab hilang = dilaporkan,
    #  bukan dilewati diam-diam (kalau dilewati, buku tampak "lengkap").
    ada, hilang = {}, []
    for n in nomor:
        #  ┌─ 20 Okt 2026 — AKAR, BUKAN TAMBALAN ────────────────────────────
        #  🔴 TERUKUR: buku pendidikan anak 6 bab (20.806 kata, 35,6 menit)
        #     GAGAL dirakit → "tidak satu pun berkas bab ada".
        #     Sebabnya BUKAN berkasnya hilang: `susun_buku` menaruh bab di
        #     folder PER BAB (`keluar_dir/bab{n}/bab{n}.txt`, Lapis 3a),
        #     sedangkan fungsi ini hanya mencari SATU bentuk
        #     (`keluar_dir/bab{n}.txt`). Dua susunan, satu pembaca ⇒ buku
        #     user tidak pernah jadi .docx padahal naskahnya lengkap.
        #  YANG BENAR: cari kedua susunan yang SAH. Jangan menyalin berkas
        #     (boros 2× ruang); cukup tunjuk yang ada. Gambar pun ikut:
        #     `visual/` ada di folder per bab, bukan di akar.
        #  └─────────────────────────────────────────────────────────────────
        #  ⚠️ Ambang 200 byte itu penjaga berkas KOSONG, bukan syarat bab sah.
        #     20 Okt 2026: uji gerbang pakai bab PENDEK (di bawah 200 byte) dan
        #     langsung dituduh "tidak ada" ⇒ gerbangnya sendiri yang gagal
        #     karena isi uji, bukan karena kode. Ambang diturunkan ke 1 byte
        #     (berkas benar-benar kosong = tidak sah; isi pendek = sah).
        kandidat = [
            os.path.join(keluar_dir, f'bab{n}.txt'),                    # lama
            os.path.join(keluar_dir, f'bab{n}', f'bab{n}.txt'),         # Lapis 3a
        ]
        p = next((k for k in kandidat
                  if os.path.exists(k) and os.path.getsize(k) > 0), None)
        if p:
            ada[n] = p
        else:
            hilang.append(n)
    if not ada:
        raise ValueError('tidak satu pun berkas bab ada — tidak ada yang dirakit')

    docx_out, pulih = siapkan(judul, keluar_dir, penulis=penulis,
                              institusi=institusi, tahun=tahun,
                              subjudul=subjudul, nama_berkas=nama_berkas)
    t0 = time.time()
    try:
        doc = Document()

        # === PAGE SETUP B5 ===
        sec = doc.sections[0]
        sec.page_width = Cm(17.6)
        sec.page_height = Cm(25.0)
        sec.left_margin = Cm(2.0)
        sec.right_margin = Cm(2.0)
        sec.top_margin = Cm(2.0)
        sec.bottom_margin = Cm(2.0)

        style = doc.styles['Normal']
        style.font.name = FONT_NAMA
        style.font.size = FONT_SIZE
        add_page_number_footer(sec)

        # === COVER ===
        cover_png = os.path.join(VISUAL_DIR, 'cover.png')
        if os.path.exists(cover_png):
            add_para(doc, '', space_after=0)
            p = doc.paragraphs[-1]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(cover_png, width=Cm(13.6))
            doc.add_page_break()
        else:
            add_para(doc, '', space_after=200)
            add_para(doc, BUKU['judul'], size=Pt(28), bold=True,
                     align='center', space_after=10)
            if BUKU['subjudul']:
                add_para(doc, BUKU['subjudul'], size=Pt(18),
                         align='center', space_after=30)
            add_para(doc, '', space_after=100)
            if BUKU['penulis']:
                add_para(doc, BUKU['penulis'], size=Pt(14), align='center',
                         space_after=6)
            if BUKU['institusi']:
                add_para(doc, BUKU['institusi'], size=Pt(12), align='center',
                         space_after=6)
            add_para(doc, BUKU['tahun'], size=Pt(12), align='center',
                     space_after=6)
            doc.add_page_break()

        add_isbn_page(doc)
        add_kata_pengantar(doc, BUKU['judul'], BUKU['penulis'],
                           BUKU['institusi'])
        #  Daftar isi HANYA bab yang benar-benar dirakit — supaya nomor bab
        #  di daftar isi tidak menunjuk bab yang tidak ada.
        add_daftar_isi(doc, {n: outline[n] for n in sorted(ada)})

        # === BAB (hanya yang ada) ===
        visual_hilang = []          #  pagar: cacat gambar HARUS kelihatan
        for n in sorted(ada):
            #  Gambar tiap bab tinggal di `visual/` MILIK BAB ITU
            #  (`keluar_dir/bab{n}/visual/`, Lapis 3a), bukan di akar.
            #  Tanpa penunjukan ini, buku jadi TANPA gambar padahal
            #  gambarnya ADA di disk — cacat senyap yang paling mahal
            #  (user bayar token, dapat buku kosong gambar).
            #  🚨 CACAT TERUKUR 20 Okt 2026 — GAMBAR HILANG DARI .docx.
            #  Versi lama HANYA menunjuk `bab{n}/visual/` kalau folder itu
            #  ada, dan kalau TIDAK ada ia membiarkan VISUAL_DIR warisan
            #  (bisa menunjuk bab sebelumnya / folder lain). TERUKUR:
            #  diagram 1.1 & 1.2 ADA di `OUT/visual/` (34 + 42 KB), tetapi
            #  .docx hanya memuat 2 gambar (1 ilustrasi + 1 diagram) —
            #  diagram 1.1 HILANG tanpa sepatah kata.
            #  Obat: pakai folder bab kalau ada, JATUH ke folder visual akar
            #  kalau tidak. Satu berkas dicari di DUA tempat, bukan satu.
            dari_bab = os.path.join(os.path.dirname(ada[n]), 'visual')
            if os.path.isdir(dari_bab):
                VISUAL_DIR = dari_bab
            elif os.path.isdir(_VISUAL_AKAR):
                VISUAL_DIR = _VISUAL_AKAR
            with open(ada[n], encoding='utf-8') as f:
                isi_bab = f.read()
            #  PAGAR ANTI-SENYAP (20 Okt 2026): naskah minta diagram, tapi PNG
            #  tidak ada ⇒ DULU dilewati tanpa sepatah kata. Sekarang DICATAT
            #  dan dibawa ke hasil rakit. Filename WAJIB dicocokkan dengan
            #  nama yang dicari `add_bab()` (diagram_{id}.png).
            for did in re.findall(r'\[DIAGRAM\s+(\d+\.\d+)', isi_bab, re.IGNORECASE):
                if not os.path.exists(os.path.join(VISUAL_DIR, f'diagram_{did}.png')):
                    visual_hilang.append(f'b{n}-diagram-{did}')
            if not os.path.exists(os.path.join(VISUAL_DIR, f'ilustrasi_bab{n}.png')):
                visual_hilang.append(f'b{n}-ilustrasi')
            add_bab(doc, n, outline[n], isi_bab)

        # === BACK MATTER ===
        glos = glosarium or {}
        if glos:
            add_glosarium(doc, glos)
            add_indeks(doc, glos)
        else:
            #  ⚠️ TERUKUR 20 Okt 2026: versi lama tetap memanggil
            #  `add_glosarium(doc, {})` ⇒ .docx berisi tabel 1 baris x 2 kolom
            #  ("Istilah | Definisi") TANPA satu pun istilah. Pembaca melihat
            #  tabel rusak, bukan glosarium.
            #  Obat: tanpa istilah ⇒ tabel TIDAK dibuat. Halaman GLOSARIUM
            #  tetap ada (daftar isi sudah menyebutnya) dengan keterangan
            #  jujur, bukan tabel kosong.
            add_glosarium(doc, {}, kosong=True)
            log.warning('[buku] glosarium kosong — tabel tidak dibuat, '
                        'halaman diberi keterangan')

        # === DAFTAR PUSTAKA — dari refs_babN.json (hasil verifikasi sitasi) ===
        all_refs = set(references or [])
        for n in sorted(ada):
            rp = os.path.join(VISUAL_DIR, f'refs_bab{n}.json')
            if os.path.exists(rp):
                try:
                    with open(rp, encoding='utf-8') as f:
                        all_refs.update(json.load(f))
                except Exception:
                    pass
        if all_refs:
            add_daftar_pustaka(doc, sorted(all_refs))

        add_bio(doc)
        doc.save(docx_out)

        # === VERIFIKASI NYATA — baca ulang berkasnya ===
        ukuran = os.path.getsize(docx_out)
        doc2 = Document(docx_out)
        sec2 = doc2.sections[0]
        bab_heading = [p.text.strip() for p in doc2.paragraphs
                       if re.match(r'^BAB \d+', p.text.strip())]
        hasil = {
            'ok': True,
            'docx': docx_out,
            'ukuran_byte': ukuran,
            'bab_dirakit': sorted(ada),
            'bab_hilang': hilang,
            'paragraf': len(doc2.paragraphs),
            'tabel': len(doc2.tables),
            'gambar': len(doc2.inline_shapes),
            'visual_hilang': visual_hilang,
            'heading_bab_terbaca': bab_heading,
            'halaman_b5': (round(sec2.page_width.cm, 1),
                           round(sec2.page_height.cm, 1)),
            'footer_nomor_halaman': 'PAGE' in sec2.footer._element.xml,
            'detik': round(time.time() - t0, 1),
        }
        return hasil
    finally:
        #  GLOBAL WAJIB dipulihkan — kalau tidak, buku berikutnya dirakit
        #  dengan judul/penulis buku sebelumnya (pencemaran lintas buku).
        pulih()


def main():
    # Load outline dari pipeline
    import sys
    sys.path.insert(0, '/opt/data')
    from buku_umum_pipeline import OUTLINE, REFERENCES, GLOSARIUM

    doc = Document()

    # === PAGE SETUP B5 ===
    sec = doc.sections[0]
    sec.page_width = Cm(17.6)
    sec.page_height = Cm(25.0)
    sec.left_margin = Cm(2.0)
    sec.right_margin = Cm(2.0)
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)

    # Style default
    style = doc.styles['Normal']
    style.font.name = FONT_NAMA
    style.font.size = FONT_SIZE

    # Footer nomor halaman
    add_page_number_footer(sec)

    # === HALAMAN 1: COVER (PNG dari HTML+CSS, auto-crop whitespace) ===
    cover_png = os.path.join(VISUAL_DIR, "cover.png")
    if os.path.exists(cover_png):
        add_para(doc, "", space_after=0)
        p = doc.paragraphs[-1]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        # B5 text width = 17.6 - 4 = 13.6cm
        run.add_picture(cover_png, width=Cm(13.6))
        doc.add_page_break()
    else:
        # Fallback: teks cover
        add_para(doc, "", space_after=200)
        add_para(doc, BUKU['judul'], size=Pt(28), bold=True, align='center', space_after=10)
        add_para(doc, BUKU['subjudul'], size=Pt(18), align='center', space_after=30)
        add_para(doc, "", space_after=100)
        add_para(doc, BUKU['penulis'], size=Pt(14), align='center', space_after=6)
        add_para(doc, BUKU['institusi'], size=Pt(12), align='center', space_after=6)
        add_para(doc, BUKU['tahun'], size=Pt(12), align='center', space_after=6)
        doc.add_page_break()

    # === HALAMAN 2: ISBN / HAK CIPTA ===
    add_isbn_page(doc)

    # === HALAMAN 3: KATA PENGANTAR ===
    add_kata_pengantar(doc, BUKU['judul'], BUKU['penulis'], BUKU['institusi'])

    # === HALAMAN 4: DAFTAR ISI ===
    add_daftar_isi(doc, OUTLINE)

    # === BAB 1-3 ===
    for bab_num in sorted(OUTLINE.keys()):
        bab_data = OUTLINE[bab_num]
        bab_file = os.path.join(OUT_DIR, f"bab{bab_num}.txt")
        if not os.path.exists(bab_file):
            print(f"❌ Bab file missing: {bab_file}")
            continue
        with open(bab_file) as f:
            bab_text = f.read()
        add_bab(doc, bab_num, bab_data, bab_text)

    # === GLOSARIUM ===
    add_glosarium(doc, GLOSARIUM)

    # === INDEKS ===
    add_indeks(doc, GLOSARIUM)

    # === DAFTAR PUSTAKA — load dari refs_babN.json (verifikasi sitasi) ===
    all_refs = set()
    visual_dir = os.path.join(OUT_DIR, "visual")
    for bab_num in sorted(OUTLINE.keys()):
        refs_path = os.path.join(visual_dir, f"refs_bab{bab_num}.json")
        if os.path.exists(refs_path):
            import json
            with open(refs_path) as f:
                bab_refs = json.load(f)
            for r in bab_refs:
                all_refs.add(r)
    
    # Fallback: jika tidak ada refs JSON, gunakan REFERENCES hardcoded
    if not all_refs:
        all_refs = REFERENCES
    
    add_daftar_pustaka(doc, sorted(all_refs))

    # === BIO ===
    add_bio(doc)

    # === SAVE ===
    doc.save(DOCX_OUT)
    size = os.path.getsize(DOCX_OUT)
    print(f"✅ {DOCX_OUT}")
    print(f"   Size: {size/1024:.0f} KB")

    # === VERIFIKASI ===
    doc2 = Document(DOCX_OUT)
    sec2 = doc2.sections[0]
    print(f"   Ukuran: {sec2.page_width.cm:.1f} x {sec2.page_height.cm:.1f} cm")
    print(f"   Paragraf: {len(doc2.paragraphs)}")
    print(f"   Tabel: {len(doc2.tables)}")
    footer_xml = sec2.footer._element.xml
    print(f"   Footer PAGE: {'ADA' if 'PAGE' in footer_xml else 'TIDAK'}")
    print(f"   Bab headings:")
    for i, p in enumerate(doc2.paragraphs):
        t = p.text.strip()
        if re.match(r'^BAB \d+$', t):
            pbb = p.paragraph_format.page_break_before
            print(f"     [{i}] \"{t}\" | page_break={pbb}")

if __name__ == "__main__":
    main()
