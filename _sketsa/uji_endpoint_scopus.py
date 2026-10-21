"""UJI NYATA: endpoint mana yang HIDUP dengan kunci Scopus kita?

Menjawab pertanyaan Bos: apakah repo scopus-mcp-extended akan membuat
pencarian kita lebih baik? Uji tiap endpoint yang repo itu tawarkan,
dengan KUNCI KITA SENDIRI (tanpa insttoken, tanpa langganan institusi).

Fokus: apa yang 200 (jalan) vs 403/400 (terkunci).
"""
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, '/app')
from app.pustaka import SCOPUS_KEY  # noqa

print('kunci Scopus terbaca:', bool(SCOPUS_KEY), '(panjang %d)' % len(SCOPUS_KEY or ''))
if not SCOPUS_KEY:
    print('TIDAK ADA KUNCI → berhenti')
    raise SystemExit(1)

H = {'X-ELS-APIKey': SCOPUS_KEY, 'Accept': 'application/json'}
DOI = '10.1177/002224299405800302'      # Morgan & Hunt 1994 (terbukti nyata)
ISSN = '0148-2963'                       # Journal of Business Research

UJI = [
    # (nama, url, params) — semua endpoint yg ditawarkan repo
    ('1. search_scopus (yg KITA pakai)', 'https://api.elsevier.com/content/search/scopus',
     {'query': 'TITLE-ABS-KEY("relationship marketing")', 'count': 3, 'sort': 'citedby'}),
    ('2. search_scopus + field RE FEID', 'https://api.elsevier.com/content/search/scopus',
     {'query': 'REFEID(2-s2.0-0028232193)', 'count': 3}),
    ('3. abstract by DOI', 'https://api.elsevier.com/content/abstract/doi/' + DOI, {}),
    ('4. citation count (batch)', 'https://api.elsevier.com/content/abstract/citation-count',
     {'doi': DOI, 'count': 5}),
    ('5. citation OVERVIEW (terkunci?)', 'https://api.elsevier.com/content/abstract/citation-overview',
     {'doi': DOI, 'date': '2015-2026'}),
    ('6. author search', 'https://api.elsevier.com/content/search/author',
     {'query': 'authlast(Morgan)', 'count': 3}),
    ('7. affiliation search', 'https://api.elsevier.com/content/search/affiliation',
     {'query': 'affil(universitas)', 'count': 3}),
    ('8. journal metrics by ISSN', 'https://api.elsevier.com/content/serial/title/issn/' + ISSN, {}),
    ('9. ScienceDirect search (butuh langganan)',
     'https://api.elsevier.com/content/search/sciencedirect', {'query': 'test', 'count': 3}),
    ('10. PlumX altmetrics', 'https://api.elsevier.com/analytics/plumx/doi/' + DOI, {}),
    ('11. quota status', 'https://api.elsevier.com/content/api-quota', {}),
]

print()
print('%-42s %-6s %s' % ('ENDPOINT', 'HTTP', 'KETERANGAN'))
print('-' * 92)
hasil = {}
for nama, url, par in UJI:
    try:
        r = httpx.get(url, params=par or None, headers=H, timeout=25,
                      follow_redirects=True)
        code = r.status_code
        ket = ''
        try:
            j = r.json()
            if code == 200:
                # bukti ada isi?
                sr = j.get('search-results', {})
                n = sr.get('opensearch:totalResults')
                ent = sr.get('entry') or []
                if n:
                    ket = 'totalResults=%s · contoh=%s' % (
                        n, (ent[0].get('dc:title', '')[:40] if ent else '-'))
                elif 'abstracts-retrieval-response' in j:
                    ket = 'ABSTRAK ADA ✅'
                elif 'citation-count' in str(j)[:200] or 'citationCount' in j:
                    ket = 'ada data sitasi'
                else:
                    kunci = list(j.keys())[:3]
                    ket = ('kunci: %s' % kunci)
            else:
                err = j.get('service-error', {}).get('status', {})
                ket = '%s | %s' % (err.get('statusCode', ''),
                                   (err.get('statusText', '') or '')[:52])
                if not ket.strip(' |'):
                    ket = str(j)[:70]
        except Exception:
            ket = (r.text or '')[:70].replace('\n', ' ')
        hasil[nama] = code
        print('%-42s %-6s %s' % (nama, code, ket))
    except Exception as e:
        hasil[nama] = 'ERR'
        print('%-42s %-6s %s' % (nama, 'ERR', str(e)[:60]))

print()
print('=== RINGKAS ===')
hidup = [k for k, v in hasil.items() if v == 200]
kunci = [k for k, v in hasil.items() if v != 200]
print('HIDUP  (%d): %s' % (len(hidup), ', '.join(x.split('.')[0] for x in hidup)))
print('MATI   (%d): %s' % (len(kunci), ', '.join(x.split('.')[0] for x in kunci)))
