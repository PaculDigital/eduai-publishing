"""UJI dokumen resmi: prefix di X-Forwarded-Host, TANPA X-Forwarded-Prefix.

Membandingkan 3 kombinasi ke OO langsung, path BER-HASH:
  A. cara LAMA   : Host=host,      Prefix=/oo/aset   -> harap 302 LOOP
  B. cara BARU   : Host=host/oo/aset, tanpa Prefix   -> harap 200
  C. tanpa keduanya                                  -> harap 302 normal
"""
import urllib.request
import urllib.error

H = '9.4.0-884b8d735f24a691228ffc46e8d0719b'
SISA = H + '/web-apps/apps/documenteditor/main/index.html'


def uji(judul, hdr):
    r = urllib.request.Request('http://oo-converter/' + SISA, headers=hdr)
    try:
        with urllib.request.urlopen(r, timeout=25) as x:
            print('%-46s -> %s' % (judul, x.status))
    except urllib.error.HTTPError as e:
        loc = (e.headers.get('location') or '')[-52:]
        print('%-46s -> %s | loc=%s' % (judul, e.code, loc))


DASAR = {'X-Forwarded-Proto': 'https'}
uji('A. LAMA  : host + X-Forwarded-Prefix',
    dict(DASAR, **{'X-Forwarded-Host': 'eduai.bikinaja.id',
                   'X-Forwarded-Prefix': '/oo/aset'}))
uji('B. BARU  : host/oo/aset, tanpa Prefix',
    dict(DASAR, **{'X-Forwarded-Host': 'eduai.bikinaja.id/oo/aset'}))
uji('C. polos : host saja',
    dict(DASAR, **{'X-Forwarded-Host': 'eduai.bikinaja.id'}))
