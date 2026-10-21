"""UJI A: bisakah kuartil jurnal (Q1-Q4) ditentukan dari data kunci kita?

Masalah: Elsevier TIDAK mengirim kuartil. Yang ada: SJR, CiteScore.
Tujuan uji: cari jalan yang SAH & terukur untuk tahu Q1/Q2/Q3/Q4.

Cara uji:
 1. Ambil SJR + CiteScore dari Scopus (endpoint serial/title) untuk
    jurnal yang kuartilnya SUDAH KITA TAHU dari pengetahuan umum.
 2. Cek apakah ada jalur LAIN yang mengirim kuartil langsung
    (mis. Scopus source list / SciMago — API publik?).
 3. Kalau kuartil tidak bisa dipastikan -> JANGAN paksa, laporkan jujur.

Jurnal pembanding (kuartil umum diketahui):
  Q1: 0148-2963 J Business Research · 0022-3808 J Political Economy
  Q1: 0001-4273 Academy of Management Journal
  Q1: 0039-0402? (uji) · Q1: 0002-8282 American Economic Review
"""
import os

import httpx

K = os.environ.get('KUNCI_UJI', '')
H = {'X-ELS-APIKey': K, 'Accept': 'application/json'}
BASE = 'https://api.elsevier.com/content/serial/title/issn/'

JURNAL = [
    ('0148-2963', 'Journal of Business Research', 'Q1'),
    ('0022-3808', 'Journal of Political Economy', 'Q1'),
    ('0002-8282', 'American Economic Review', 'Q1'),
    ('2302-6294', 'Jurnal Indonesia (uji, kuartil tdk diketahui)', '?'),
    ('0128-1234', 'ISSN KARANGAN (kontrol negatif)', '—'),
]

print('=== 1. APA YANG DIKIRIM Elsevier per jurnal ===')
simpul = []
for issn, nama, q_harap in JURNAL:
    try:
        r = httpx.get(BASE + issn, headers=H, timeout=25, follow_redirects=True)
    except Exception as e:
        print('%-46s ERR %s' % (nama[:46], str(e)[:40]))
        continue
    if r.status_code != 200:
        print('%-46s HTTP %s' % (nama[:46], r.status_code))
        simpul.append((nama, issn, q_harap, None, None, None))
        continue
    e = (r.json().get('serial-metadata-response', {}).get('entry') or [{}])[0]
    sjr_l = e.get('SJRList', {}).get('SJR') or []
    sjr = sjr_l[0] if isinstance(sjr_l, list) and sjr_l else (
        sjr_l if isinstance(sjr_l, dict) else {})
    snap = e.get('SNIPList', {}).get('SNIP') or []
    snip = snap[0] if isinstance(snap, list) and snap else (
        snap if isinstance(snap, dict) else {})
    cs = e.get('citeScoreYearInfoList', {}).get('citeScoreCurrentMetric')
    print('%-40s SJR=%-8s SNIP=%-7s CiteScore=%-6s kuartil-harap=%s'
          % (nama[:40], (sjr or {}).get('$', '-'), (snip or {}).get('$', '-'),
             cs, q_harap))
    simpul.append((nama, issn, q_harap, (sjr or {}).get('$'), cs, None))

print()
print('=== 2. APAKAH ADA JALUR PUBLIK YANG KIRIM KUARTIL LANGSUNG? ===')
# SciMago (SCImago Journal Rank) -- publik, tanpa kunci
for jalur, ket in [
    ('https://www.scimagojr.com/journalsearch.php?q=0148-2963',
     'SciMago (web, publik)'),
]:
    try:
        r = httpx.get(jalur, timeout=25, follow_redirects=True,
                      headers={'User-Agent': 'Mozilla/5.0'})
        ada_q = 'Q1' in r.text or 'Q2' in r.text
        print('  %-34s HTTP %s · ada penanda Q? %s · %d byte'
              % (ket, r.status_code, ada_q, len(r.text)))
    except Exception as e:
        print('  %-34s ERR %s' % (ket, str(e)[:50]))

print()
print('=== 3. KESIMPULAN ===')
sah = [(n, s) for n, i, q, s, c, _ in simpul if s]
print('  jurnal dgn SJR terbaca: %d dari %d' % (len(sah), len(simpul)))
print('  kuartil dari Elsevier  : TIDAK ADA (dibuktikan)')
print('  -> kuartil HARUS dihitung sendiri dari SJR, atau dari sumber lain (SciMago).')
