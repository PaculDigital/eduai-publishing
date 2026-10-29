#!/usr/bin/env python3
"""Layanan sidecar mesin buku (Opsi B2) — WordCraft + gerbang per buku.

KENAPA ADA: image app TIDAK berisi WordCraft/pdftotext dan TIDAK boleh
memanggil docker (aturan desain akar 26 Okt 2026: WordCraft = satu-satunya
perender gerbang). Mesin render + gerbang per buku tinggal di layanan ini,
di samping app, di jaringan yang sama (eduai-net). App hanya kirim docx
lewat HTTP dan terima hasil — app TIDAK pernah menyentuh WordCraft.

CARA JALAN (operator, sekali — scripts/jalankan_sidecar.sh):
    bash template-buku-resmi/scripts/jalankan_sidecar.sh <KUNCI_YANG_SAMA_DENGAN_APP>
    (Skrip itu build image wordcraft-sidecar:1 sekali, lalu menjalankan
    container di eduai-net dengan mount read-only: kode mesin, WordCraft,
    pdftotext. Port TIDAK dipublish ke host.)
Tanpa EDUAI_SIDECAR_KUNCI layanan MENOLAK start (gagal keras di awal,
bukan diam-diam terbuka). Port TIDAK dipublish ke host — hanya eduai-net.

ENDPOINT (JSON; docx dikirim base64 agar tanpa multipart):
    GET  /sehat                     -> {ok, layanan, versi} (tanpa kunci)
    POST /isi-nomor  {docx_b64}     -> {exit, terisi[], hilang[], docx_b64}
           exit 0 = semua terisi, 1 = sebagian hilang (berkas tetap ditulis),
           2 = gagal total. Mengikuti kontrak scripts/isi_nomor_toc.py.
    POST /ukur  {docx_b64, judul_bab[]} -> {peta{judul: halaman}, hilang[], total}
           Render WordCraft -> pdftotext -layout per halaman -> cari judul
           DI LUAR bentang DAFTAR ISI (aturan yang sama dengan cari() di
           buat_buku.py: halaman TOC + halaman lanjutan yang tiap halamannya
           punya >=3 baris bertitik-panjang >=10 ikut dilewati).
    POST /chapter  {docx_b64}       -> {exit, keluar}
           Gerbang book-chapter (scripts/periksa_book_chapter.py); exit 0 lolos.
    POST /referensi {docx_b64}      -> {exit, lulus, gagal, keluar}
           Gerbang buku-referensi: docx diekstrak jadi spec (gaya keluaran
           assembly: 'BAB N' + judul, sub 'N.M ...', tabel + caption
           'Tabel ...', seksi Glosarium/Indeks/Daftar Pustaka), lalu
           periksa_jenis_buku.jalankan(spec, 'buku-referensi'). exit 0 =
           semua cek lolos (gagal == 0). Satu tabel komparasi per bab/sub
           sudah cukup untuk R3; tabel tambahan di bab/sub yang sama tidak
           masuk spec (keterbatasan jujur ekstraktor, bukan gerbang).

KEAMANAN: semua POST wajib header X-Kunci-Sidecar == EDUAI_SIDECAR_KUNCI.
Berkas sementara SELALU di direktori mktemp per request + dibersihkan
(pelajaran merge 14ceabe: tidak ada nama /tmp tetap).
Hanya pustaka standar — tidak ada dependensi baru.
"""

import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSI = 'b2-1'
MESIN = Path(__file__).resolve().parent
BATAS_BADAN = 64 * 1024 * 1024  # docx buku < 5 MB; 64 MB sudah longgar


def _kunci():
    kunci = os.environ.get('EDUAI_SIDECAR_KUNCI', '')
    if not kunci:
        print('sidecar_buku: EDUAI_SIDECAR_KUNCI belum diset — menolak start',
              file=sys.stderr)
        sys.exit(2)
    return kunci


KUNCI = _kunci()
PORT = int(os.environ.get('SIDECAR_PORT', '8131'))


def _baca_json(handler):
    panjang = int(handler.headers.get('Content-Length', '0') or '0')
    if panjang <= 0 or panjang > BATAS_BADAN:
        raise ValueError('badan kosong atau melebihi batas 64 MB')
    return json.loads(handler.rfile.read(panjang).decode('utf-8'))


def _tulis(handler, kode, obj):
    badan = json.dumps(obj, ensure_ascii=False).encode('utf-8')
    handler.send_response(kode)
    handler.send_header('Content-Type', 'application/json')
    handler.send_header('Content-Length', str(len(badan)))
    handler.end_headers()
    handler.wfile.write(badan)


def _docx_dari(data):
    try:
        return base64.b64decode(data['docx_b64'], validate=True)
    except Exception:
        raise ValueError('docx_b64 bukan base64 yang sah')


def _jalan(cmd, timeout=300):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          env={**os.environ})


def _normal(teks):
    return re.sub(r'\s+', ' ', (teks or '')).strip().upper()


def _halaman_teks(pdf):
    """Per halaman -> teks -layout; pisah halaman pakai form feed."""
    out = subprocess.run(['pdftotext', '-layout', str(pdf), '-'],
                         capture_output=True, text=True, timeout=120)
    if out.returncode != 0:
        raise RuntimeError('pdftotext gagal: ' + out.stderr[:200])
    return out.stdout.split('\f')


def _bentang_toc(halaman):
    """Halaman TOC + lanjutannya (aturan sama dengan cari() buat_buku.py)."""
    toc = set()
    for i, teks in enumerate(halaman):
        if 'DAFTAR ISI' in _normal(teks):
            toc.add(i)
            j = i + 1
            while j < len(halaman):
                baris_titik = sum(
                    1 for b in halaman[j].splitlines()
                    if len(re.findall(r'\.{10,}', b)) >= 1)
                if baris_titik >= 3:
                    toc.add(j)
                    j += 1
                else:
                    break
            break
    return toc


def isi_nomor(data, td):
    masuk = Path(td) / 'masuk.docx'
    keluar = Path(td) / 'keluar.docx'
    masuk.write_bytes(_docx_dari(data))
    r = _jalan([sys.executable, str(MESIN / 'isi_nomor_toc.py'),
                str(masuk), str(keluar)], timeout=300)
    terisi, hilang = [], []
    mode_hilang = False
    for baris in r.stdout.splitlines():
        if baris.startswith('  TERISI: '):
            terisi.append(baris[len('  TERISI: '):])
        elif baris.startswith('HILANG'):
            mode_hilang = True
        elif mode_hilang and baris.startswith('  - '):
            hilang.append(baris[4:])
    hasil = {'exit': r.returncode, 'terisi': terisi, 'hilang': hilang}
    if keluar.exists():
        hasil['docx_b64'] = base64.b64encode(keluar.read_bytes()).decode()
    else:
        hasil['galat'] = (r.stdout + r.stderr)[-500:]
    return hasil


def ukur(data, td):
    from perender_halaman import hitung_halaman, render_pdf
    masuk = Path(td) / 'masuk.docx'
    pdf = Path(td) / 'masuk.pdf'
    masuk.write_bytes(_docx_dari(data))
    if not render_pdf(str(masuk), str(pdf)):
        return {'exit': 2, 'galat': 'WordCraft gagal merender ke PDF'}
    total = hitung_halaman(str(masuk))
    if total is None:
        return {'exit': 2, 'galat': 'WordCraft gagal menghitung halaman'}
    halaman = _halaman_teks(pdf)
    toc = _bentang_toc(halaman)
    peta, hilang = {}, []
    for judul in data.get('judul_bab') or []:
        kunci = _normal(judul)
        ketemu = None
        for i, teks in enumerate(halaman):
            if i in toc:
                continue
            normal = _normal(teks)
            if kunci and (kunci in normal or kunci[:30] in normal):
                ketemu = i + 1  # halaman dihitung dari 1
                break
        if ketemu:
            peta[judul] = ketemu
        else:
            hilang.append(judul)
    return {'exit': 0, 'peta': peta, 'hilang': hilang, 'total': total}


def chapter(data, td):
    masuk = Path(td) / 'masuk.docx'
    masuk.write_bytes(_docx_dari(data))
    r = _jalan([sys.executable, str(MESIN / 'periksa_book_chapter.py'),
                str(masuk)], timeout=300)
    return {'exit': r.returncode, 'keluar': (r.stdout + r.stderr)[-2000:]}


def teks_halaman(data, td):
    """Teks per halaman dari render nyata (untuk pengisi indeks).

    Mengembalikan list: indeks 0 = halaman 1 (pisah form feed dari
    pdftotext). Pemanggil (app/referensi_indeks) yang menentukan halaman
    isi vs TOC/back-matter dari isinya.
    """
    from perender_halaman import render_pdf
    masuk = Path(td) / 'masuk.docx'
    pdf = Path(td) / 'masuk.pdf'
    masuk.write_bytes(_docx_dari(data))
    if not render_pdf(str(masuk), str(pdf)):
        return {'exit': 2, 'galat': 'WordCraft gagal merender ke PDF'}
    try:
        halaman = _halaman_teks(pdf)
    except Exception as e:
        return {'exit': 2, 'galat': f'pdftotext gagal: {e}'}
    return {'exit': 0, 'halaman': halaman}


def _pasangan_indeks(baris):
    """'Istilah ..... 12' -> ['Istilah', '12']; tanpa angka -> [baris, ''].

    Bentuk pasangan WAJIB karena entri_indeks_bermakna di gerbang hanya
    menerima [istilah, acuan] (string polos = gagal). Acuan kosong =
    gagal jujur: indeks tanpa nomor halaman tidak lolos R1/R2.
    """
    m = re.match(r'^(.*?)[\.\s]+(\d+(?:,\s*\d+)*)\s*$', baris.strip())
    if m and m.group(1).strip():
        return [m.group(1).strip(), m.group(2)]
    return [baris.strip(), '']


def ekstrak_spec_referensi(path_docx):
    """Docx gaya assembly -> spec untuk periksa_jenis_buku.

    Mengerti: 'BAB N' (paragraf angka saja, judul di paragraf berikut),
    sub 'N.M ...', Heading 1/2, caption 'Tabel ...', seksi Glosarium /
    Indeks Subjek / Indeks Nama / Daftar Singkatan / Daftar Pustaka.
    Entri DAFTAR ISI dilewati (berhenti di page break sesudahnya).
    """
    from docx import Document
    from docx.document import Document as _Doc
    from docx.table import Table as _Tabel
    from docx.text.paragraph import Paragraph as _Para
    doc = Document(str(path_docx))
    babs, idx_subjek, idx_nama, glos, singk = [], [], [], [], []
    pengantar, tentang, pustaka = [], [], []
    judul = ''
    bab = sub = None
    seksi = None
    caption = ''
    lewati_toc = False
    for anak in doc.element.body.iterchildren():
        if anak.tag.endswith('}p'):
            p = _Para(anak, doc)
            teks = p.text.strip()
            xml = p._p.xml
            # Cek page break DULU, sebelum buang paragraf kosong: paragraf
            # page break memang kosong (hanya run <w:br type=page/>).
            # Kalau cek ini sesudah 'if not teks', lewati_toc tidak pernah
            # mati dan seluruh isi sesudah TOC terbuang (bug tangkapan uji).
            if lewati_toc:
                # Akhir TOC: jeda halaman eksplisit (w:br) ATAU judul
                # bab/seksi yang memakai pageBreakBefore. Gaya assembly
                # buku: 'BAB N' + pageBreakBefore, TANPA elemen br —
                # tanpa klausul kedua ini, lewati_toc tidak pernah mati
                # dan seluruh isi sesudah TOC terbuang (6 gagal gerbang
                # pada uji 29 Okt 2026). Paragraf pemutus HARUS diproses
                # (bukan di-continue) karena ia adalah isi.
                if 'w:type="page"' in xml or 'pageBreakBefore' in xml:
                    lewati_toc = False
                else:
                    continue
            if not teks:
                continue
            if teks.upper() == 'DAFTAR ISI':
                lewati_toc = True
                continue
            atas = teks.upper()
            if atas == 'KATA PENGANTAR':
                seksi = 'pengantar'
                continue
            if atas in ('GLOSARIUM', 'INDEKS', 'INDEKS SUBJEK'):
                seksi = 'glosarium' if atas == 'GLOSARIUM' else 'subjek'
                continue
            if atas == 'INDEKS NAMA':
                seksi = 'nama'
                continue
            if atas == 'DAFTAR SINGKATAN':
                seksi = 'singkatan'
                singk.append('Daftar Singkatan')
                continue
            if atas == 'DAFTAR PUSTAKA':
                seksi = 'pustaka'
                continue
            if atas == 'TENTANG PENULIS':
                seksi = 'penulis'
                continue
            if re.fullmatch(r'BAB\s+\d+', atas):
                bab = {'judul': teks, 'paragraf_pembuka': [], 'sub': []}
                babs.append(bab)
                sub, seksi = None, None
                continue
            if re.match(r'^\d+\.\d+\s+\S+', teks):
                if bab is not None:
                    sub = {'judul': teks, 'paragraf': []}
                    bab['sub'].append(sub)
                continue
            gaya = (p.style.name or '')
            if gaya.startswith('Heading 1'):
                bab = {'judul': teks, 'paragraf_pembuka': [], 'sub': []}
                babs.append(bab)
                sub, seksi = None, None
                continue
            if gaya.startswith('Heading 2'):
                if bab is not None:
                    sub = {'judul': teks, 'paragraf': []}
                    bab['sub'].append(sub)
                continue
            if teks.startswith('Tabel ') and re.match(r'Tabel\s+\d', teks):
                caption = teks
                continue
            if seksi == 'subjek':
                idx_subjek.append(_pasangan_indeks(teks))
            elif seksi == 'nama':
                idx_nama.append(_pasangan_indeks(teks))
            elif seksi == 'glosarium':
                glos.append(teks)
            elif seksi == 'singkatan':
                singk.append(teks)
            elif seksi == 'pengantar':
                pengantar.append(teks)
            elif seksi == 'penulis':
                tentang.append(teks)
            elif seksi == 'pustaka':
                pustaka.append(teks)
            elif sub is not None:
                sub['paragraf'].append(teks)
            elif bab is not None:
                bab['paragraf_pembuka'].append(teks)
            elif not judul:
                # Paragraf pertama sebelum bab/seksi = judul sampul
                # (urutan assembly: Cover -> Kata Pengantar -> Daftar Isi).
                judul = teks
        elif anak.tag.endswith('}tbl'):
            t = _Tabel(anak, doc)
            baris = [[c.text.strip() for c in r.cells] for r in t.rows]
            baris = [r for r in baris if any(r)]
            if len(baris) < 2:
                continue
            tabel = {'judul': caption, 'kolom': baris[0], 'baris': baris[1:]}
            caption = ''
            if sub is not None and 'tabel' not in sub:
                sub['tabel'] = tabel
            elif bab is not None and 'tabel' not in bab:
                bab['tabel'] = tabel
    try:
        penulis = (doc.core_properties.author or '').strip()
    except Exception:
        penulis = ''
    if not penulis and tentang:
        penulis = tentang[0]
    return {'bab': babs, 'judul': judul, 'penulis': penulis,
            'kata_pengantar': ' '.join(pengantar),
            'tentang_penulis': ' '.join(tentang),
            'daftar_pustaka': pustaka,
            'indeks_subjek': idx_subjek,
            'indeks_nama': idx_nama, 'glosarium': glos,
            'daftar_singkatan': singk}


_KUNCI_JALANKAN = __import__('threading').Lock()


def referensi(data, td):
    import contextlib
    import io
    import periksa_jenis_buku as _gj
    masuk = Path(td) / 'masuk.docx'
    masuk.write_bytes(_docx_dari(data))
    spec = ekstrak_spec_referensi(masuk)
    # jalankan() memakai global LULUS/GAGAL — panggilan bersamaan dari
    # dua buku web akan merusak hitungan; kunci ini menyerikannya.
    # Endpoint lain memakai subprocess (proses terpisah) jadi aman.
    buf = io.StringIO()
    with _KUNCI_JALANKAN, contextlib.redirect_stdout(buf):
        lulus, gagal = _gj.jalankan(spec, 'buku-referensi', diam=False)
    return {'exit': 0 if gagal == 0 else 1, 'lulus': lulus, 'gagal': gagal,
            'keluar': buf.getvalue()[-2000:]}


TANGAN = {'/isi-nomor': isi_nomor, '/ukur': ukur, '/chapter': chapter,
          '/referensi': referensi, '/teks-halaman': teks_halaman}


class Tangan(BaseHTTPRequestHandler):
    def log_message(self, *a):  # log standar dimatikan; cukup stdout kita
        pass

    def do_GET(self):
        if self.path == '/sehat':
            _tulis(self, 200, {'ok': True, 'layanan': 'sidecar-buku',
                               'versi': VERSI})
        else:
            _tulis(self, 404, {'ok': False, 'galat': 'tidak dikenal'})

    def do_POST(self):
        fn = TANGAN.get(self.path)
        if not fn:
            _tulis(self, 404, {'ok': False, 'galat': 'tidak dikenal'})
            return
        if self.headers.get('X-Kunci-Sidecar', '') != KUNCI:
            _tulis(self, 403, {'ok': False, 'galat': 'kunci salah'})
            return
        try:
            data = _baca_json(self)
            with tempfile.TemporaryDirectory(prefix='sidecar-buku-') as td:
                hasil = fn(data, td)
            hasil.setdefault('ok', True)
            _tulis(self, 200, hasil)
        except Exception as e:
            _tulis(self, 500, {'ok': False, 'galat': f'{type(e).__name__}: {e}'})


if __name__ == '__main__':
    sys.path.insert(0, str(MESIN))  # perender_halaman tinggal sefolder
    print(f'sidecar-buku {VERSI} jalan di port {PORT} (kunci: diset)',
          flush=True)
    ThreadingHTTPServer(('0.0.0.0', PORT), Tangan).serve_forever()
