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


TANGAN = {'/isi-nomor': isi_nomor, '/ukur': ukur, '/chapter': chapter}


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
