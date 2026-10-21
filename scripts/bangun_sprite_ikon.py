"""Bangun SPRITE IKON Lucide untuk EduAi Publishing.

KENAPA SPRITE (bukan 38 file .svg terpisah):
  • 1 permintaan HTTP saja (bukan 38) → app lebih cepat
  • warna ikut `currentColor` → bisa diwarnai lewat CSS (emoji tidak bisa)
  • konsisten di SEMUA perangkat (emoji beda-beda bentuk per HP)

Cara pakai di template:
    {# macro ikon('nama', ukuran) #}
    <svg class="ik ik-sm"><use href="#ik-file-text"></use></svg>

Sumber: Lucide Static (ISC License — bebas dipakai, termasuk komersial).
Ikon diunduh SEKALI, lalu disimpan di app/static/ikon/lucide.svg
→ TIDAK butuh internet saat app jalan (penting untuk VPS produksi).
"""
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SUMBER = Path(sys.argv[1] if len(sys.argv) > 1 else '/tmp/lucide-x/package/icons')
KELUAR = Path(sys.argv[2] if len(sys.argv) > 2 else
              '/opt/data/services/eduai-publishing/app/static/ikon')

# ── SUMBER CADANGAN (16Sep26) ────────────────────────────────────────────
# Paket Lucide asli (/tmp/lucide-x) HILANG setelah VPS dibersihkan, sehingga
# skrip ini tidak bisa dijalankan ulang → ikon baru mustahil ditambah
# (lonceng Langkah E). Ikon yang ditambahkan SETELAH 16Sep26 disimpan di
# `_ikon-sumber/` (ikut repo) dan dicari di sini lebih dulu.
SUMBER_CADANGAN = Path(__file__).resolve().parent.parent / '_ikon-sumber'

# ── Daftar ikon yang DIPAKAI app (nama Lucide → keterangan) ──────────────
# Dipilih dengan gaya GARIS (outline) sesuai ACC Bos 15Sep26.
IKON = {
    # ── berkas / dokumen ──
    'file-text':        'dokumen teks (docx)',
    'file-spreadsheet': 'tabel (xlsx)',
    'presentation':     'presentasi (pptx)',
    'file-image':       'gambar',
    'file-type':        'berkas lain / pdf',
    'file':             'berkas umum',
    'file-plus':        'unggah berkas baru',
    'file-down':        'unduh berkas',
    # ── folder ──
    'folder':           'folder tertutup',
    'folder-open':      'folder terbuka',
    'folder-pen':       'ubah/ganti nama folder',
    'folder-plus':      'folder baru',
    # ──aksi berkas ──
    'pencil':           'sunting dokumen',
    'download':         'unduh',
    'upload':           'unggah',
    'trash-2':          'hapus (tong sampah)',
    'archive-restore':  'pulihkan dari sampah',
    'eraser':           'hapus permanen',
    'rotate-ccw':       'kembalikan ke titik riwayat',
    'history':          'riwayat',
    # ── AI ──
    'sparkles':         'revisi dengan AI',
    'brain':            'AI memahami dokumen',
    'zap':              'cepat / otomatis',
    # ── notifikasi (Langkah E, 16Sep26) ──
    # Sumber: lucide-react v0.577.0 (ISC) — disimpan di _ikon-sumber/
    # karena paket lucide asli sudah tidak ada di VPS ini.
    'bell':             'lonceng pemberitahuan',
    'bell-ring':        'lonceng berbunyi (ada yang baru)',
    # ── keamanan & pembayaran ──
    'shield-check':     'aman',
    'lock':             'terkunci',
    'credit-card':      'kartu / bayar',
    'landmark':         'transfer bank',
    'receipt':          'transaksi / kuitansi',
    'wallet':           'saldo / kuota',
    # ── lain-lain ──
    'cloud':            'penyimpanan cloud',
    'graduation-cap':   'akademik / mahasiswa',
    'users':            'banyak pengguna',
    'user-plus':        'undang orang',
    'handshake':        'kolaborasi',
    'rocket':           'mulai / cepat',
    'smartphone':       'mobile',
    'monitor':          'desktop',
    'bug':              'laporan masalah (dev)',
    'check':            'selesai / benar',
    'x':                'tutup / batal',
    'alert-triangle':   'peringatan',
    'info':             'keterangan',
    'chevron-right':    'panah buka',
    'chevron-down':     'panah tutup',
    'chevron-left':     'panah kiri',
    'arrow-left':       'kembali',
    'external-link':    'tautan luar',
    'search':           'cari',
    'settings':         'pengaturan',
    'log-out':          'keluar',
    'timer':            'waktu / sesi',
    'book-open':        'mode belajar',
    'clipboard-check':  'uji diri',
    'shield-alert':     'peringatan keamanan',
}

VIEWBOX = '0 0 24 24'
GAYA = ('fill="none" stroke="currentColor" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round"')

# ── Atribut Lucide yang TIDAK dikenal SVG murni (harus dibuang) ──────────
# ⚠ 15Sep26 BUG: 'width'/'height' sempat ada di sini → membuang ukuran
#   <rect> juga (bukan hanya <svg>), sehingga ikon `lock`, `monitor`,
#   `credit-card`, `smartphone`, `archive-restore`, `clipboard-check`
#   kehilangan kotaknya (gembok cuma kelihatan lengkungan atas).
#   → 'width'/'height' HANYA dibuang dari <svg> pembungkus, bukan dari anak.
BUANG_SVG = {'class', 'width', 'height', 'id', 'aria-hidden', 'role',
             'focusable', 'data-lucide', 'aria-label'}
# Atribut yang aman dibuang dari SEMUA elemen (nama presentasi saja)
BUANG_SEMUA = {'class', 'id', 'data-lucide', 'aria-hidden', 'role', 'focusable'}
# XML entities yang harus di-escape kembali saat menulis atribut
ESC = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}


def esc(t: str) -> str:
    return ''.join(ESC.get(c, c) for c in t)


def ambil_isi(path: Path) -> str:
    """Ambil isi <svg> (tanpa tag pembungkus) dari satu berkas Lucide.

    ⚠ JANGAN buang `width`/`height` dari elemen ANAK (`<rect>`, `<image>`)
      — itu UKURAN BENTUK, bukan ukuran kanvas. Hanya `<svg>` pembungkus
      yang ukurannya dibuang (diganti oleh atribut <use> di template).
    """
    txt = path.read_text(encoding='utf-8')
    # buang komentar lisensi
    txt = re.sub(r'<!--.*?-->', '', txt, flags=re.S)
    akar = ET.fromstring(txt)
    for t in akar.findall('{http://www.w3.org/2000/svg}title'):
        akar.remove(t)
    potong = []

    def tulis(el) -> str:
        """Tulis satu elemen (rekursif) tanpa atribut yang tidak perlu."""
        tag = el.tag.split('}')[-1]
        atr = []
        for k, v in el.attrib.items():
            if k.startswith('data-') or k in BUANG_SEMUA:
                continue
            if k == 'stroke-width':
                continue          # ikut stroke-width induk (<symbol>)
            atr.append('%s="%s"' % (k, esc(v)))
        anak = ''.join(tulis(a) for a in el)
        gab = (' ' + ' '.join(atr)) if atr else ''
        if anak:
            return '<%s%s>%s</%s>' % (tag, gab, anak, tag)
        return '<%s%s/>' % (tag, gab)

    for anak in akar:
        tag = anak.tag.split('}')[-1]
        if tag in ('title', 'defs', 'metadata'):
            continue
        potong.append(tulis(anak))
    return ''.join(potong)


def main() -> int:
    hilang, jadi = [], []
    for nama in IKON:
        p = SUMBER / (nama + '.svg')
        if not p.exists():
            p = SUMBER_CADANGAN / (nama + '.svg')     # ikon baru (16Sep26)
        if not p.exists():
            hilang.append(nama)
            continue
        jadi.append((nama, ambil_isi(p)))

    if hilang:
        print('  ✗ TIDAK ADA di Lucide:', ', '.join(hilang))
        print('  → hentikan supaya tidak ada <use> kosong di template')
        return 1

    KELUAR.mkdir(parents=True, exist_ok=True)
    bagian = ['<svg xmlns="http://www.w3.org/2000/svg" style="display:none" '
              'aria-hidden="true">']
    for nama, isi in jadi:
        bagian.append('<symbol id="ik-%s" viewBox="%s" %s>%s</symbol>'
                      % (nama, VIEWBOX, GAYA, isi))
    bagian.append('</svg>')

    keluar_file = KELUAR / 'lucide.svg'
    keluar_file.write_text('\n'.join(bagian), encoding='utf-8')
    print('  ✓ %d ikon ditulis ke %s (%s byte)'
          % (len(jadi), keluar_file, '{:,}'.format(keluar_file.stat().st_size)))

    # ── PEMERIKSA: bentuk WAJIB punya ukuran ────────────────────────────
    # 15Sep26: `lock` dkk sempat kehilangan width/height pada <rect> →
    # gembok cuma kelihatan lengkungan atas. Diperiksa otomatis di sini.
    isi_semua = keluar_file.read_text(encoding='utf-8')
    perlu = {'rect': ['width', 'height'], 'circle': ['r'],
             'ellipse': ['rx', 'ry'], 'image': ['width', 'height']}
    rusak = []
    for m in re.finditer(r'<symbol id="(ik-[a-z0-9-]+)"[^>]*>(.*?)</symbol>',
                         isi_semua, re.S):
        for t in re.finditer(r'<(\w+)([^>]*)/?>', m.group(2)):
            tag, atr = t.group(1), t.group(2)
            if tag not in perlu:
                continue
            kurang = [k for k in perlu[tag]
                      if not re.search(r'\b%s="' % k, atr)]
            if kurang:
                rusak.append((m.group(1), tag, kurang))
    if rusak:
        print('  ✗ IKON RUSAK (bentuk tanpa ukuran):')
        for n, t, k in rusak:
            print('      • %s <%s> kurang %s' % (n, t, ', '.join(k)))
        return 1
    print('  ✓ semua bentuk punya ukuran (rect/circle/ellipse lengkap)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
