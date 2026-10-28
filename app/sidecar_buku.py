"""Klien sidecar mesin buku (Opsi B2) — dipakai app per buku.

App TIDAK berisi WordCraft/pdftotext dan TIDAK memanggil docker, jadi
semua pekerjaan render + gerbang per buku dilempar ke layanan sidecar
(template-buku-resmi/scripts/sidecar_buku.py) lewat HTTP di jaringan yang
sama. Modul ini HANYA pustaka standar (urllib) — tanpa dependensi baru.

Konfigurasi (env):
    EDUAI_SIDECAR_URL    (default http://wordcraft-sidecar:8131)
    EDUAI_SIDECAR_KUNCI  (WAJIB — tanpa ini sidecar dianggap belum siap)

Kegagalan apa pun (tidak terjangkau, kunci salah, timeout, exit != 0 yang
ditandai gagal) dilempar sebagai SidecarGagal dengan pesan yang bisa
langsung ditampilkan ke log/lapor — pemanggil memutuskan: gagal teknis =
token kembali (pola yang sudah ada di penyusunan_buku.susun).
"""

import base64
import json
import os
import urllib.error
import urllib.request


class SidecarGagal(Exception):
    pass


def _url():
    return (os.environ.get('EDUAI_SIDECAR_URL') or
            'http://wordcraft-sidecar:8131').rstrip('/')


def _kunci():
    kunci = os.environ.get('EDUAI_SIDECAR_KUNCI', '')
    if not kunci:
        raise SidecarGagal('sidecar belum dikonfigurasi '
                           '(EDUAI_SIDECAR_KUNCI kosong)')
    return kunci


def _panggil(jalan, data, timeout):
    badan = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        _url() + jalan, data=badan,
        headers={'Content-Type': 'application/json',
                 'X-Kunci-Sidecar': _kunci()},
        method='POST')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            hasil = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        raise SidecarGagal(f'sidecar {jalan}: HTTP {e.code}')
    except Exception as e:
        raise SidecarGagal(f'sidecar {jalan} tidak terjangkau: '
                           f'{type(e).__name__}: {e}')
    if not hasil.get('ok', True):
        raise SidecarGagal(f'sidecar {jalan}: {hasil.get("galat", "?")}')
    return hasil


def siap():
    """True bila sidecar menjawab /sehat (dipakai cek kesiapan)."""
    try:
        with urllib.request.urlopen(_url() + '/sehat', timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8')).get('ok') is True
    except Exception:
        return False


def isi_nomor(path_docx):
    """Isi nomor TOC yang kosong. Kembalikan (path_baru, terisi, hilang).

    path_baru = berkas bernomor (ditulis di samping aslinya, akhiran
    .bernomor.docx); pemanggil yang mengganti aslinya bila mau.
    exit 2 (gagal total) -> SidecarGagal; exit 1 (sebagian hilang) ->
    tetap kembali + daftar hilang untuk dicatat, bukan digagalkan
    (filler adalah PERBAIKAN, bukan gerbang penolak).
    """
    with open(path_docx, 'rb') as f:
        data = {'docx_b64': base64.b64encode(f.read()).decode()}
    hasil = _panggil('/isi-nomor', data, timeout=300)
    if hasil.get('exit') == 2:
        raise SidecarGagal('isi nomor TOC gagal total: ' +
                           str(hasil.get('galat', ''))[:300])
    if 'docx_b64' not in hasil:
        raise SidecarGagal('isi nomor TOC: sidecar tidak mengembalikan berkas')
    baru = str(path_docx) + '.bernomor.docx'
    with open(baru, 'wb') as f:
        f.write(base64.b64decode(hasil['docx_b64']))
    return baru, hasil.get('terisi', []), hasil.get('hilang', [])


def ukur(path_docx, judul_bab):
    """Ukur halaman tiap judul bab dari render nyata.

    Kembalikan (peta, hilang, total). hilang tak kosong = buku cacat
    (judul babnya tidak tampil di rendernya sendiri) -> pemanggil WAJIB
    menggagalkan buku, bukan mengarang angka.
    """
    with open(path_docx, 'rb') as f:
        data = {'docx_b64': base64.b64encode(f.read()).decode(),
                'judul_bab': list(judul_bab)}
    hasil = _panggil('/ukur', data, timeout=300)
    if hasil.get('exit') != 0:
        raise SidecarGagal('ukur halaman gagal: ' +
                           str(hasil.get('galat', ''))[:300])
    return hasil.get('peta', {}), hasil.get('hilang', []), hasil.get('total')


def chapter(path_docx):
    """Gerbang book-chapter. Kembalikan True bila lolos, else SidecarGagal."""
    with open(path_docx, 'rb') as f:
        data = {'docx_b64': base64.b64encode(f.read()).decode()}
    hasil = _panggil('/chapter', data, timeout=300)
    if hasil.get('exit') != 0:
        raise SidecarGagal('gerbang book-chapter gagal:\n' +
                           str(hasil.get('keluar', ''))[-800:])
    return True


def teks_halaman(path_docx):
    """Teks per halaman dari render nyata (list; indeks 0 = halaman 1).

    Dipakai pengisi indeks referensi. Gagal render/pdftotext -> SidecarGagal
    (fail-closed: buku referensi tanpa teks halaman tidak bisa diindeks).
    """
    with open(path_docx, 'rb') as f:
        data = {'docx_b64': base64.b64encode(f.read()).decode()}
    hasil = _panggil('/teks-halaman', data, timeout=300)
    if hasil.get('exit') != 0:
        raise SidecarGagal('teks halaman gagal: ' +
                           str(hasil.get('galat', ''))[:300])
    return hasil.get('halaman', [])


def referensi(path_docx):
    """Gerbang buku-referensi (R1-R4 + struktur). True bila lolos."""
    with open(path_docx, 'rb') as f:
        data = {'docx_b64': base64.b64encode(f.read()).decode()}
    hasil = _panggil('/referensi', data, timeout=300)
    if hasil.get('exit') != 0:
        raise SidecarGagal(
            f"gerbang buku-referensi gagal "
            f"({hasil.get('lulus')} lulus / {hasil.get('gagal')} gagal):\n" +
            str(hasil.get('keluar', ''))[-800:])
    return True
