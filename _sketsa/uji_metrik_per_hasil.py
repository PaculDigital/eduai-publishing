"""UJI: apakah metrik jurnal bisa diambil PER HASIL PENCARIAN?

Rencana: setiap hasil Scopus punya `journal` (nama) + DOI.
Uji: dari nama jurnal hasil pencarian Scopus asli → bisa ambil SJR/CiteScore?

Ini menentukan apakah penandaan mutu di hasil pencarian LAYAK dikerjakan.
"""
import os
import time

import httpx

K = os.environ.get('KUNCI_UJI', '')
H = {'X-ELS-APIKey': K, 'Accept': 'application/json'}

# ── 1. cari artikel Scopus asli (persis spt app kita) ──
print('=== 1. CARI ARTIKEL (persis rumus app kita) ===')
q = ('TITLE-ABS-KEY("relationship marketing" OR "customer relationship") '
     'AND TITLE-ABS-KEY("trust" OR "commitment")')
r = httpx.get('https://api.elsevier.com/content/search/scopus',
              params={'query': q, 'count': 5, 'sort': 'citedby',
                      'date': '2015-2026'},
              headers=H, timeout=30, follow_redirects=True)
print('  HTTP', r.status_code)
ent = r.json().get('search-results', {}).get('entry') or []
print('  hasil:', len(ent))
hasil = []
for it in ent:
    j = (it.get('prism:publicationName') or '').strip()
    doi = (it.get('prism:doi') or '').strip()
    print('   - %-52s | jurnal: %s | ISSN %s' % (
        (it.get('dc:title') or '')[:52], j[:34], it.get('prism:issn') or '-'))
    hasil.append({'judul': it.get('dc:title'), 'jurnal': j, 'doi': doi,
                  'issn': it.get('prism:issn') or ''})

# ── 2. ambil metrik per jurnal hasil ──
print()
print('=== 2. METRIK PER JURNAL (dari hasil di atas) ===')
for h in hasil:
    issn = (h['issn'] or '').split(',')[0].strip()
    if not issn:
        print('   %-34s → ISSN tidak ada di hasil Scopus' % h['jurnal'][:34])
        continue
    t0 = time.time()
    try:
        rr = httpx.get('https://api.elsevier.com/content/serial/title/issn/' + issn,
                       headers=H, timeout=25, follow_redirects=True)
        dt = time.time() - t0
        if rr.status_code != 200:
            print('   %-34s → HTTP %s (%.1f dtk)' % (h['jurnal'][:34], rr.status_code, dt))
            continue
        e = (rr.json().get('serial-metadata-response', {}).get('entry') or [{}])[0]
        sl = e.get('SJRList', {}).get('SJR') or []
        sjr = (sl[0] if isinstance(sl, list) and sl else sl) or {}
        cs = e.get('citeScoreYearInfoList', {}).get('citeScoreCurrentMetric')
        print('   %-34s → SJR %-8s CiteScore %-6s (%.1f dtk) ✅' % (
            h['jurnal'][:34], sjr.get('$', '-'), cs or '-', dt))
    except Exception as ex:
        print('   %-34s → ERR %s' % (h['jurnal'][:34], str(ex)[:40]))

print()
print('=== 3. KESIMPULAN ===')
print('  Jalur per-hasil: Scopus(search) -> ISSN/jurnal -> serial/title -> SJR/CiteScore')
print('  Kalau semua di atas ✅ => penandaan mutu di hasil pencarian LAYAK.')
