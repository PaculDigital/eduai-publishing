"""TAHAP 2 — pakai rumus PICO di 4 fungsi pencarian + saring 2 arah."""
import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/app/pustaka.py')
s = P.read_text()

# ══════════ SCOPUS — pakai q_scopus (AND antar konsep) ══════════
lama = """def cari_scopus(kw_en: list[str], maks: int = MAKS_PER_SUMBER) -> list[dict]:
    \"\"\"Cari di Scopus. Gagal → [] (failover, JANGAN hentikan pencarian).\"\"\"
    if not SCOPUS_KEY:
        log.warning('[pustaka] Scopus: kunci tidak ada → dilewati')
        return []
    try:
        #  ⚠️ WAJIB httpx + params (jangan encode manual — bisa 200 tapi 0).
        #  🔴 PERBAIKAN 26Sep26: JANGAN `OR` antar 8 kata kunci (hasil acak —
        #     "cycle" cocok di mana-mana). Gabung jadi SATU frasa.
        bagian = [f'TITLE-ABS-KEY("{k}")' for k in (kw_en or []) if k.strip()]
        if not bagian:
            return []
        if len(bagian) == 1:
            query = bagian[0]
        else:
            #  frasa utama + pembatas: (A) AND (B OR C)
            query = f'{bagian[0]} AND ({bagian[1]}' + ''.join(
                f' OR {b}' for b in bagian[2:]) + ')'
        params = {'query': query, 'count': maks,
                  'sort': 'citedby', 'date': f'{TAHUN_AWAL}-{TAHUN_AKHIR}'}"""
baru = """def cari_scopus(kw_en: list[str], maks: int = MAKS_PER_SUMBER,
                query_siap: str = '') -> list[dict]:
    \"\"\"Cari di Scopus. Gagal → [] (failover, JANGAN hentikan pencarian).

    🔴 RUMUS BENAR (26Sep26): AND antar KONSEP, OR di dalam konsep.
       `query_siap` = hasil `rumus_scopus(konsep)` — kalau kosong, jatuh ke
       cara lama (daftar kata kunci dalam satu frasa) supaya tetap jalan.
    \"\"\"
    if not SCOPUS_KEY:
        log.warning('[pustaka] Scopus: kunci tidak ada → dilewati')
        return []
    try:
        #  ⚠️ WAJIB httpx + params (jangan encode manual — bisa 200 tapi 0).
        if query_siap:
            query = query_siap
        else:
            bagian = [f'TITLE-ABS-KEY("{k}")' for k in (kw_en or []) if k.strip()]
            if not bagian:
                return []
            query = bagian[0] if len(bagian) == 1 else (
                f'{bagian[0]} AND ({bagian[1]}' + ''.join(
                    f' OR {b}' for b in bagian[2:]) + ')')
        params = {'query': query, 'count': maks,
                  'sort': 'citedby', 'date': f'{TAHUN_AWAL}-{TAHUN_AKHIR}'}"""
assert lama in s, 'scopus tak ketemu'
s = s.replace(lama, baru, 1)

# ══════════ OPENALEX — terima frasa dari PICO ══════════
lama_o = """def cari_openalex(kw_en: list[str], kw_id: list[str] | None = None,
                  maks: int = MAKS_PER_SUMBER) -> list[dict]:"""
baru_o = """def cari_openalex(kw_en: list[str], kw_id: list[str] | None = None,
                  maks: int = MAKS_PER_SUMBER, frasa: str = '') -> list[dict]:"""
assert lama_o in s
s = s.replace(lama_o, baru_o, 1)

lama_o2 = """        #  🔴 pakai frasa utuh (bukan 4 kata terpisah → hasil meleset)
        _frasa_en = ' '.join([k for k in kw_en if len(k) > 2][:2]) or \\
            ' '.join([k for k in (kw_id or []) if len(k) > 3][:2])"""
baru_o2 = """        #  🔴 pakai frasa KONSEP INTI (dari PICO) — bukan gabungan kata bebas
        _frasa_en = frasa or ' '.join(
            [k for k in kw_en if len(k) > 2][:1]) or \\
            ' '.join([k for k in (kw_id or []) if len(k) > 3][:1])"""
assert lama_o2 in s
s = s.replace(lama_o2, baru_o2, 1)

# ══════════ CROSSREF — terima frasa PICO ══════════
lama_c = """def cari_crossref(kw_en: list[str], maks: int = 10) -> list[dict]:"""
baru_c = """def cari_crossref(kw_en: list[str], maks: int = 10,
                  frasa: str = '') -> list[dict]:"""
assert lama_c in s
s = s.replace(lama_c, baru_c, 1)

lama_c2 = """        #  🔴 frasa utuh + bibliographic (lebih tepat daripada query bebas)
        par = {'query.bibliographic': ' '.join(
            [k for k in kw_en if len(k) > 2][:2]),"""
baru_c2 = """        #  🔴 2 FRASA KONSEP teratas (dari PICO) — bukan timbunan kata
        par = {'query.bibliographic': frasa or ' '.join(
            [k for k in kw_en if len(k) > 2][:2]),"""
assert lama_c2 in s
s = s.replace(lama_c2, baru_c2, 1)

# ══════════ SARINGAN: 2 ARAH (konsep AND) ══════════
lama_n = s[s.index('def _nyambung(artikel: dict, kw: dict) -> bool:'):
           s.index('def _kunci_dedup(r: dict) -> str:')]
baru_n = '''def _nyambung(artikel: dict, kw: dict) -> bool:
    """True kalau judul artikel memuat SEMUA konsep inti (rumus PICO).

    🔴 PERBAIKAN 26Sep26 (dari uji naskah Bosch):
       Versi awal hanya menuntut 1 kata inti → artikel COVID-19 & Brain
       Imaging lolos. Sekarang: artikel WAJIB menyentuh SETIAP konsep
       (diwakili minimal satu sinonimnya) → mustahil meleset jauh.
    """
    judul = (artikel.get('title') or '').lower()
    abstrak = (artikel.get('abstract') or '').lower()[:600]
    teks = judul + ' ' + abstrak
    if not judul:
        return False

    konsep = kw.get('konsep') or []
    if not konsep:
        #  tanpa konsep (tema bebas) → saring longgar seperti dulu
        inti = {w for frasa in (kw.get('en') or []) for w in frasa.lower().split()
                if len(w) > 4 and w not in _KATA_HENTI}
        return True if not inti else any(w in judul for w in inti)

    #  konsep inti = maksimal 3 pertama (sama seperti rumus pencarian)
    inti_konsep = konsep[:3]
    dikenai = 0
    for k in inti_konsep:
        sinonim = [x.lower() for x in (k.get('en') or [])] + \\
                  [x.lower() for x in (k.get('id') or [])]
        #  cek di JUDUL dulu (bukti kuat); abstrak sebagai cadangan
        if any(x in judul for x in sinonim):
            dikenai += 1
        elif any(x in teks for x in sinonim):
            dikenai += 0.5          # separuh bukti (cuma di abstrak)
    #  LULUS kalau semua konsep tersentuh (abstrak boleh menambal)
    return dikenai >= len(inti_konsep)


'''
s = s.replace(lama_n, baru_n, 1)

# ══════════ cari_semua: sambungkan rumus PICO ══════════
lama_g = """    semua: list[dict] = []
    jumlah: dict[str, int] = {}
    for nama, hasil in (
        ('Scopus', cari_scopus(kw['en'])),
        ('OpenAlex', cari_openalex(kw['en'], kw['id'])),
        ('Garuda', cari_garuda(kw['id'])),
        ('CrossRef', cari_crossref(kw['en'])),
    ):"""
baru_g = """    semua: list[dict] = []
    jumlah: dict[str, int] = {}
    #  ⭐ RUMUS PICO (26Sep26): AND antar konsep, OR di dalam konsep
    _garuda_kw = (kw.get('kw_garuda') or kw['id'])[:3]
    log.info('[pustaka] rumus Scopus   : %s', kw.get('q_scopus', '')[:200])
    log.info('[pustaka] rumus OpenAlex : %s', kw.get('q_openalex', ''))
    log.info('[pustaka] rumus CrossRef : %s', kw.get('q_crossref', ''))
    log.info('[pustaka] kata kunci Garuda: %s', _garuda_kw)
    for nama, hasil in (
        ('Scopus', cari_scopus(kw['en'], query_siap=kw.get('q_scopus', ''))),
        ('OpenAlex', cari_openalex(kw['en'], kw['id'],
                                   frasa=kw.get('q_openalex', ''))),
        ('Garuda', cari_garuda(_garuda_kw)),
        ('CrossRef', cari_crossref(kw['en'],
                                   frasa=kw.get('q_crossref', ''))),
    ):"""
assert lama_g in s, 'cari_semua tak ketemu'
s = s.replace(lama_g, baru_g, 1)

P.write_text(s)
print('✅ 4 fungsi pencarian pakai rumus PICO + saringan 2 arah (AND konsep)')
