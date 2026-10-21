"""BUKTI AKAR: apakah cookie sesi sampai ke browser lewat produksi?

Kalau set_cookie memakai secure=True, browser HANYA menyimpan di HTTPS.
Kalau secure=False di domain HTTPS tetap disimpan, TAPI header Set-Cookie
yang benar akan tampak 'Secure'. Yang kita cek:
  1. apakah Set-Cookie muncul saat login lewat domain
  2. apakah atributnya Secure / SameSite
"""
import urllib.request
import urllib.error

DOMAIN = 'eduai.bikinaja.id'
URL = 'https://%s/masuk' % DOMAIN

# Coba login pakai kredensial uji TIDAK mungkin berhasil (kita hanya lihat
# header Set-Cookie / perilaku). Pakai GET ke /masuk dulu: apakah halaman hidup.
r = urllib.request.Request('https://%s/masuk' % DOMAIN,
                           headers={'Cache-Control': 'no-cache'})
try:
    with urllib.request.urlopen(r, timeout=25) as x:
        print('GET /masuk →', x.status)
        sc = x.headers.get_all('Set-Cookie') or []
        print('  Set-Cookie:', sc if sc else '(tidak ada — wajar utk GET)')
except urllib.error.HTTPError as e:
    print('GET /masuk →', e.code)

print()
print('=== cek header X-Forwarded-Proto sampai ke app? (via /health) ===')
r2 = urllib.request.Request('https://%s/health' % DOMAIN,
                            headers={'Cache-Control': 'no-cache'})
with urllib.request.urlopen(r2, timeout=25) as x:
    for k in ('Server', 'Cf-Cache-Status'):
        v = x.headers.get(k)
        if v:
            print('  %s: %s' % (k, v))
