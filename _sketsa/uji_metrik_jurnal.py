"""UJI DALAM: metrik jurnal apa saja yang terbaca dengan kunci kita?

Tujuan: apakah cukup untuk menandai "jurnal Scopus bereputasi"?
Uji dengan jurnal yang AKU KENAL reputasinya, bandingkan hasilnya.

Jurnal uji:
  • 0148-2963 Journal of Business Research (Elsevier, Scopus Q1)
  • 0022-3808 Journal of Political Economy (Chicago, Q1 top)
  • 0128-1234 ISSN karangan (HARUS gagal — uji pagar)
"""
import json
import os

import httpx

K = os.environ.get('KUNCI_UJI', '')
H = {'X-ELS-APIKey': K, 'Accept': 'application/json'}

JURNAL = [
    ('0148-2963', 'Journal of Business Research (Q1, Elsevier)'),
    ('0022-3808', 'Journal of Political Economy (Q1 top)'),
    ('0128-1234', 'ISSN KARANGAN — harus GAGAL'),
]


def tampil(nama, r):
    print('─' * 78)
    print('%s  →  HTTP %s' % (nama, r.status_code))
    if r.status_code != 200:
        try:
            e = r.json().get('service-error', {}).get('status', {})
            print('   %s | %s' % (e.get('statusCode', ''),
                                  (e.get('statusText', '') or '')[:70]))
        except Exception:
            print('  ', r.text[:100])
        return
    j = r.json()
    smr = j.get('serial-metadata-response', {})
    ent = smr.get('entry') or []
    print('   jumlah entri:', len(ent))
    for e in ent[:1]:
        print('   judul      :', (e.get('dc:title') or '')[:64])
        print('   ISSN       :', e.get('prism:issn') or e.get('prism:eIssn'))
        print('   penerbit   :', (e.get('dc:publisher') or '')[:44])
        print('   cakupan th :', e.get('coverageStartYear'), '-', e.get('coverageEndYear'))
        sno = e.get('SJRList', {}).get('SJR') or []
        if sno:
            for s in sno[:3]:
                print('   SJR        : %s (@%s) · kuartil %s' % (
                    s.get('$'), s.get('@year'), s.get('@quartile', '-')))
        else:
            print('   SJR        : (tidak ada di balasan)')
        snip = e.get('SNIPList', {}).get('SNIP') or []
        if snip:
            print('   SNIP       :', snip[0].get('$'), '(@%s)' % snip[0].get('@year'))
        cs = e.get('citeScoreYearInfoList', {}).get('citeScoreCurrentMetric')
        if cs:
            print('   CiteScore  :', cs)
        else:
            print('   CiteScore  : (tidak ada)')
        # semua kunci yg tersedia -> apa lagi yg bisa kita pakai?
        print('   KUNCI TERSEDIA:', sorted(e.keys())[:14])


for issn, nama in JURNAL:
    try:
        r = httpx.get('https://api.elsevier.com/content/serial/title/issn/' + issn,
                      headers=H, timeout=25, follow_redirects=True)
        tampil('%s [%s]' % (nama, issn), r)
    except Exception as e:
        print('%s → ERROR %s' % (nama, str(e)[:70]))

# apakah bisa cari jurnal berdasarkan JUDUL (bukan ISSN)?
print()
print('═' * 78)
print('UJI TAMBAHAN: cari jurnal berdasarkan JUDUL (tanpa ISSN)?')
try:
    r = httpx.get('https://api.elsevier.com/content/serial/title',
                  params={'title': 'journal of business research', 'count': 3},
                  headers=H, timeout=25, follow_redirects=True)
    print('  HTTP', r.status_code)
    if r.status_code == 200:
        ent = (r.json().get('serial-metadata-response', {}).get('entry') or [])
        print('  entri:', len(ent))
        for e in ent[:2]:
            print('   -', (e.get('dc:title') or '')[:60],
                  '| ISSN', e.get('prism:issn'))
    else:
        print('  ', r.text[:130])
except Exception as e:
    print('  ERROR', str(e)[:70])
