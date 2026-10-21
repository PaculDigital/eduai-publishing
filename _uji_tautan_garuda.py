"""UJI NYATA: seberapa banyak tautan Garuda yang BENAR-BENAR bisa diunduh.

Dipakai sebelum menyimpulkan 'selesai'. Jangan percaya tautan ada —
periksa berkasnya benar-benar PDF.
"""
import sys, re, httpx
sys.path.insert(0, '/app')
from app import pustaka as P

HDR = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}


def coba(u: str) -> str:
    """Kembalikan status singkat: PDF | html-login | html-lain | 403 | gagal."""
    try:
        r = httpx.get(u, headers=HDR, timeout=40, follow_redirects=True)
    except Exception as e:                                    # noqa: BLE001
        return f'GAGAL({type(e).__name__})'
    ct = (r.headers.get('content-type') or '').lower()
    awal = r.content[:8]
    akhir = str(r.url).lower()
    if 'pdf' in ct or awal.startswith(b'%PDF'):
        return f'PDF({len(r.content)}B)'
    if r.status_code == 403:
        return '403'
    if r.status_code >= 400:
        return f'HTTP{r.status_code}'
    if 'login' in akhir or 'masuk' in akhir:
        return 'html-LOGIN'
    return 'html-lain'


print('=== Tautan Garuda dari BEBERAPA artikel nyata — bisa diunduh? ===')
hasil = {}
for gid in ('1818743', '4200800', '2426413', '1818743'):
    t = P.tautan_garuda(gid)
    if t['pdf_url'] not in hasil:
        hasil[t['pdf_url']] = coba(t['pdf_url']) if t['pdf_url'] else 'kosong'
        print(f'  {gid}: {hasil[t["pdf_url"]]:22} {t["pdf_url"][:60]}')

print()
print('=== RINGKASAN ===')
tot = len(hasil)
pdf = sum(1 for v in hasil.values() if v.startswith('PDF'))
print(f'  {pdf}/{tot} tautan benar-benar PDF')

print()
print('=== Periksa: apakah tautan Garuda boleh dicoba juga kalau bukan OJS? ===')
#  Cek apakah ada pola tautan Garuda SENDIRI yang bisa jadi PDF
for gid in ('1818743', '4200800'):
    r = httpx.get(f'https://garuda.kemdiktisaintek.go.id/documents/detail/{gid}',
                  headers=HDR, timeout=30, follow_redirects=True)
    tautan = re.findall(r'href="([^"]*download\.garuda[^"]*)"', r.text, re.I)
    print(f'  {gid}: tautan garuda-sendiri = {len(tautan)}')
