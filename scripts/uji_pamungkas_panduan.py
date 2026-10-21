#!/usr/bin/env python3
"""Uji pamungkas: unggah panduan user → revisi AI → blok harus bawa aturan USER.

Bandarkan token_in aturan_baku vs panduan_user (bukti blok masuk prompt).
"""
import json
import os
import sys
import urllib.request

BASE = 'https://eduai.bikinaja.id'
UA = ('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36')
TOK = os.environ['TOKEN_UJI']
PDF = os.environ.get(
    'PDF', '/opt/data/cache/documents/doc_0e40131213cc_PEDOMAN PENULISAN '
           'SKRIPSI PRODI MANAJEMEN EDISI REVISI 2025.pdf')

NASKAH = (
    "BAB I PENDAHULUAN\n\n"
    "1.1 Latar Belakang\n"
    "Penjualan merupakan kegiatan utama perusahaan untuk mempertahankan "
    "kelangsungan bisnisnya. Kinerja pemasaran yang baik sangat menentukan "
    "peningkatan penjualan produk. Penelitian ini dilakukan untuk "
    "menganalisis pengaruh promosi dan kualitas layanan terhadap "
    "peningkatan penjualan pada perusahaan daerah.\n"
)


def req(jalur, data=None, tipe='application/json', method=None):
    h = {'Cookie': f'eduai_session={TOK}', 'User-Agent': UA}
    if data is not None:
        h['Content-Type'] = tipe
    r = urllib.request.Request(BASE + jalur, data=data, headers=h,
                               method=method)
    try:
        with urllib.request.urlopen(r, timeout=180) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


def multipart(bagian):
    b = '----batas123'
    out = []
    for k, v, fn, ct in bagian:
        if fn:
            out.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"; '
                       f'filename="{fn}"\r\nContent-Type: {ct}\r\n\r\n'
                       .encode() + v + b'\r\n')
        else:
            out.append(f'--{b}\r\nContent-Disposition: form-data; '
                       f'name="{k}"\r\n\r\n{v}\r\n'.encode())
    out.append(f'--{b}--\r\n'.encode())
    return b''.join(out), f'multipart/form-data; boundary={b}'


if __name__ == '__main__':
    # 1. UNGGAH panduan (PDF pedoman asli)
    isi = open(PDF, 'rb').read()
    badan, ct = multipart([
        ('file_id', '58', None, None),
        ('berkas', isi, PDF.split('/')[-1], 'application/pdf'),
    ])
    st, d = req('/api/ai/v1/profil-naskah/panduan', badan, ct, 'POST')
    kartu = d.get('kartu') or {}
    print('unggah:', st, 'ok=', d.get('ok'),
          '| margin:', kartu.get('margin'),
          '| spasi isi:', (kartu.get('spasi') or {}).get('isi_paragraf'))

    # 2. REVISI AI (sumber = panduan_user)
    st, d2 = req('/api/ai/v1/revisi', json.dumps({
        'file_id': 58, 'naskah': NASKAH,
        'komentar': ['Rapikan sesuai aturan pedoman.'],
        'setuju_bagian': True,
    }).encode(), method='POST')
    kode = d2.get('kode')
    print('revisi:', st, 'kode=', kode)

    # 3. pantau
    import time
    token_in = None
    for _ in range(40):
        time.sleep(5)
        s, p = req(f'/api/ai/v1/proses/{kode}')
        if p.get('status') == 'selesai':
            token_in = p.get('token_in')
            print('SELESAI | token_in =', token_in,
                  '| token_out =', p.get('token_out'),
                  '| model =', p.get('model_ai'))
            break
    else:
        print('batas pantau habis')
        sys.exit(2)

    # 4. bandingkan (aturan_baku terakhir = 8720)
    if token_in:
        selisih = token_in - 8720
        print(f'PERBANDINGAN: token_in sekarang {token_in} vs baku 8720 '
              f'→ selisih {selisih:+d} (positif = blok panduan user masuk)')
