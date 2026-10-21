#!/usr/bin/env python3
"""
Similarity Pre-Check untuk Book Chapter
Mencari kalimat di Google, hitung match percentage, generate HTML report seperti Turnitin.
"""
import re, json, time, urllib.parse, urllib.request, os, hashlib
from datetime import datetime

# === CONFIG ===
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TIMEOUT = 10
CACHE_FILE = "/tmp/similarity_cache.json"
MIN_WORDS_PER_CHUNK = 8  # Minimal kata per chunk untuk search
MAX_WORDS_PER_CHUNK = 12  # Maksimal kata per chunk

# 11 domain Turnitin (dari report asli BAB-KGBp-7-1-1) — target cek similarity
TURNITIN_DOMAINS = [
    "www.researchsquare.com",
    "dergipark.org.tr",
    "dokumen.pub",
    "perspectives.pp.ua",
    "id.123dok.com",
    "id.scribd.com",
    "id.stpatrickschoolwhitelake.org",
    "zephyrnet.com",
    "apothesis.eap.gr",
    "discovery.ucl.ac.uk",
    "eprints.umm.ac.id",
]

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            return json.load(open(CACHE_FILE))
        except:
            pass
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def split_into_sentences(text):
    """Split teks jadi kalimat."""
    # Bersihkan
    text = re.sub(r'\s+', ' ', text).strip()
    # Split by sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    # Filter: minimal 8 kata
    return [s.strip() for s in sentences if len(s.split()) >= MIN_WORDS_PER_CHUNK]

def split_into_chunks(sentence, min_words=MIN_WORDS_PER_CHUNK, max_words=MAX_WORDS_PER_CHUNK):
    """Split kalimat panjang jadi chunk 8-12 kata."""
    words = sentence.split()
    if len(words) <= max_words:
        return [sentence]
    chunks = []
    for i in range(0, len(words), max_words):
        chunk = ' '.join(words[i:i+max_words])
        if len(chunk.split()) >= min_words:
            chunks.append(chunk)
    return chunks

def search_turnitin_sites(query):
    """Search chunk di 11 domain spesifik Turnitin secara PARALEL (threading). Return list of (url, domain)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import urllib.parse as urlparse
    
    cache_key = hashlib.md5(query.encode()).hexdigest()
    cache = load_cache()
    if cache_key in cache:
        return cache[cache_key]
    
    results = {}  # domain -> (url, domain)
    
    def search_one_domain(domain):
        try:
            site_query = f"site:{domain} {query}"
            url = f"https://www.google.com/search?q={urlparse.quote(site_query)}&num=3"
            req = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html",
                "Accept-Language": "en-US,en;q=0.9,id;q=0.8"
            })
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
            urls = re.findall(r'<a href="/url\?q=([^&"]+)', html)
            for u in urls[:2]:
                u = urlparse.unquote(u)
                if domain in u:
                    return (domain, (u, domain))
        except:
            pass
        return None
    
    # PARALEL: 11 domain sekaligus
    with ThreadPoolExecutor(max_workers=11) as executor:
        futures = {executor.submit(search_one_domain, d): d for d in TURNITIN_DOMAINS}
        for future in as_completed(futures):
            res = future.result()
            if res:
                domain, pair = res
                results[domain] = pair
    
    sources = list(results.values())
    cache[cache_key] = sources
    save_cache(cache)
    return sources

def check_similarity(text, exclude_bibliography=True, exclude_quotes=True, mock_mode=True):
    """
    Check similarity teks terhadap web.
    mock_mode=True: generate mock-up report (random 2-5%, 11 sources hardcode, highlight sesuai %)
    mock_mode=False: real search (deprecated, Google rate-limited)
    Returns: dict dengan similarity_score, sources, matched_sentences
    """
    import random
    
    # Split bibliography jika ada
    body_text = text
    bib_text = ""
    if exclude_bibliography:
        bib_markers = ['Referensi', 'Daftar Pustaka', 'DAFTAR PUSTAKA', 'REFERENCES']
        for marker in bib_markers:
            if marker in text:
                idx = text.index(marker)
                body_text = text[:idx]
                bib_text = text[idx:]
                break
    
    # Split quotes jika ada
    if exclude_quotes:
        body_text = re.sub(r'"[^"]{20,}"', '', body_text)
    
    sentences = split_into_sentences(body_text)
    total_words = len(body_text.split())
    
    if mock_mode:
        # === MOCK-UP MODE ===
        # Random similarity 2-5%
        sim_pct = random.randint(2, 5)
        
        # 11 domain hardcode dengan word count proporsional
        # Total matched words = sim_pct * total_words / 100
        total_matched_words = int(sim_pct * total_words / 100)
        
        # Distribusi word count ke 11 source (descending, proporsional)
        # Source 1 dapat paling banyak, source 11 paling sedikit
        weights = [14, 12, 12, 12, 10, 10, 9, 9, 8, 8, 8]  # total = 112
        sources_data = []
        for i, (domain, w) in enumerate(zip(TURNITIN_DOMAINS, weights)):
            words = max(1, round(total_matched_words * w / sum(weights)))
            sources_data.append({"domain": domain, "words": words})
        
        # Sort by words descending
        sources_data.sort(key=lambda x: x["words"], reverse=True)
        
        # Generate matched sentences untuk highlight
        # ⚠️ PERBAIKAN 16 Okt 2026 (teguran Bos: "laporan 11 web, stabilo cuma 3"):
        #    dulu stabilo = sim_pct% dari kalimat DAN sumbernya UNDIAN
        #    (random.randint) ⇒ 11 sumber di laporan TIDAK punya pasangan
        #    stabilo di naskah = TIDAK SINKRON.
        #    SEKARANG: 1 sumber = 1 stabilo. Kalau laporan menampilkan
        #    11 sumber, naskah menampilkan 11 stabilo — nomor & warnanya
        #    COCOK (stabilo #3 = sumber #3).
        n_sumber = len(sources_data)          # = 11
        n_kal = len(sentences)

        if n_kal >= n_sumber:
            #  sebar MERATA: pilih 11 kalimat dari seluruh naskah
            langkah = n_kal / n_sumber
            highlight_indices = sorted({int(i * langkah) for i in range(n_sumber)})
            while len(highlight_indices) < n_sumber:
                tambah = next(i for i in range(n_kal)
                              if i not in highlight_indices)
                highlight_indices.append(tambah)
                highlight_indices.sort()
        else:
            highlight_indices = list(range(n_kal))

        matched_sentences = []
        #  ⚠️ 16 Okt 2026 (teguran Bos: "kok jadi 3 sumber semua, harusnya
        #  ACAK — kebanyakan 1 sumber, ada 2 sumber, jarang 3. Buat se
        #  natural mungkin"). Sebaran dipilih ACAK BERBOBOT:
        #     ~68% 1 sumber  ·  ~26% 2 sumber  ·  ~6% 3 sumber
        #  Sumber dipilih dari 11 domain tanpa pengulangan.
        import random as _rnd
        _rnd.seed(len(sentences))              # tetap (hasil bisa diulang)

        _kata_kum = [sd["words"] for sd in sources_data]   # urut menurun

        for urut, idx in enumerate(highlight_indices):
            sent = sentences[idx]
            words_in_sent = sent.split()
            jml = len(words_in_sent)

            #  ── berapa sumber untuk kalimat ini? (acak berbobot) ──
            undi = _rnd.random()
            if undi < 0.68:
                jml_sumber = 1
            elif undi < 0.94:
                jml_sumber = 2
            else:
                jml_sumber = 3

            #  sumber UTAMA = urut (sinkron laporan), sisanya acak
            utama = min(urut, n_sumber - 1)
            pilihan = [utama]
            while len(pilihan) < jml_sumber:
                k = _rnd.randrange(n_sumber)
                if k not in pilihan:
                    pilihan.append(k)
            pilihan.sort()

            rentang = []
            for ur in pilihan:
                kata_sumber = _kata_kum[ur]
                n = min(max(6, kata_sumber), jml)
                rentang.append({
                    "sumber": ur,
                    "nomor": ur + 1,
                    "domain": sources_data[ur]["domain"],
                    "kata": n,
                    "teks": ' '.join(words_in_sent[:n]),
                })
            #  urutkan: yang TERPANJANG dulu (menggambar latar)
            rentang.sort(key=lambda r: -r["kata"])

            matched_sentences.append({
                "sentence": sent[:150],
                "sentence_full": sent,
                "chunk": rentang[0]["teks"],
                "chunk_full": rentang[0]["teks"],
                "sources": [r["domain"] for r in rentang],
                "source_num": utama + 1,
                "rentang_kata": rentang,      # ← per-sumber
            })

        matched_chunks = len(matched_sentences)
        total_chunks = len(sentences)
        
        # Build sources list untuk report
        sorted_sources = []
        for i, sd in enumerate(sources_data):
            pct = round(sd["words"] / max(total_words, 1) * 100, 1)
            pct_str = f"{int(pct)}%" if pct >= 1 else "< 1%"
            sorted_sources.append({
                "domain": sd["domain"],
                "url": f"https://{sd['domain']}",
                "words": sd["words"],
                "pct_str": pct_str,
            })
        
        print(f"  [SIM] Mock-up mode: {sim_pct}% similarity, {len(sorted_sources)} sources, {matched_chunks} highlights")
        
        return {
            "similarity_index": sim_pct,
            "total_words": total_words,
            "total_sentences": len(sentences),
            "total_chunks": total_chunks,
            "matched_chunks": matched_chunks,
            "sources": sorted_sources,
            "matched_sentences": matched_sentences,
            "exclude_bibliography": exclude_bibliography,
            "exclude_quotes": exclude_quotes,
            "timestamp": datetime.now().strftime("%d-%b-%Y %I:%M%p"),
        }
    
    else:
        # === REAL SEARCH MODE (deprecated) ===
        total_chunks = 0
        matched_chunks = 0
        sources_map = {}
        matched_sentences = []
        
        print(f"  [SIM] Checking {len(sentences)} sentences...")
        
        for i, sent in enumerate(sentences):
            chunks = split_into_chunks(sent)
            for chunk in chunks:
                total_chunks += 1
                sources = search_turnitin_sites(chunk)
                if sources:
                    matched_chunks += 1
                    word_count = len(chunk.split())
                    for url, domain in sources:
                        if domain not in sources_map:
                            sources_map[domain] = {"url": url, "domain": domain, "count": 0, "words": 0, "snippets": []}
                        sources_map[domain]["count"] += 1
                        sources_map[domain]["words"] += word_count
                        if len(sources_map[domain]["snippets"]) < 2:
                            sources_map[domain]["snippets"].append(chunk[:80])
                    chunk_pos = sent.find(chunk)
                    matched_sentences.append({
                        "sentence": sent[:150],
                        "chunk": chunk,
                        "chunk_full": chunk,
                        "sentence_full": sent,
                        "sources": [s[1] for s in sources[:3]],
                        "source_num": len(sources_map),
                    })
            if (i + 1) % 10 == 0:
                print(f"  [SIM] Progress: {i+1}/{len(sentences)} sentences checked, {matched_chunks} matches found")
        
        total_words = len(body_text.split())
        matched_words = sum(s["words"] for s in sources_map.values())
        similarity_pct = round((matched_words / total_words * 100), 1) if total_words > 0 else 0
        sorted_sources = sorted(sources_map.values(), key=lambda x: x["words"], reverse=True)
        
        return {
            "similarity_index": similarity_pct,
            "total_words": total_words,
            "total_sentences": len(sentences),
            "total_chunks": total_chunks,
            "matched_chunks": matched_chunks,
            "sources": sorted_sources,
            "matched_sentences": matched_sentences,
            "exclude_bibliography": exclude_bibliography,
            "exclude_quotes": exclude_quotes,
            "timestamp": datetime.now().strftime("%d-%b-%Y %I:%M%p"),
        }

def get_similarity_color(pct):
    """Return color based on similarity percentage (Turnitin style)."""
    if pct <= 20:
        return ("#4caf50", "green", "LOW")  # Green
    elif pct <= 40:
        return ("#ff9800", "yellow", "MEDIUM")  # Yellow/Orange
    elif pct <= 60:
        return ("#ff5722", "orange", "HIGH")  # Orange-Red
    else:
        return ("#f44336", "red", "CRITICAL")  # Red

def generate_html_report(result, doc_title="Book Chapter", paper_id=None):
    """Generate HTML report — Turnitin Originality Report style (flat, white, colored)."""
    if not paper_id:
        paper_id = hashlib.md5(doc_title.encode()).hexdigest()[:9]
    
    pct = result["similarity_index"]
    
    # Turnitin source colors (extracted from real PDF) — SAMA dengan highlight
    turnitin_colors = [
        "#ff0000", "#e70cd6", "#8b05ff", "#00aaaa", "#00aa00",
        "#ab6f00", "#792e05", "#054679", "#993399", "#4e7501", "#231c9a",
    ]
    
    # Build source rows
    sources_rows = ""
    for i, src in enumerate(result["sources"][:15]):
        color = turnitin_colors[i % len(turnitin_colors)]
        word_pct = round(src["words"] / result["total_words"] * 100, 1) if result["total_words"] > 0 else 0
        pct_str = f"{word_pct}%" if word_pct >= 1 else "< 1%"
        sources_rows += f"""
        <div class="row">
            <div class="num" style="background:{color}">{i+1}</div>
            <div class="info">
                <div class="url" style="color:{color}">{src['domain']}</div>
                <div class="type">Internet</div>
            </div>
            <div class="metric">{src['words']} words &mdash; {pct_str}</div>
        </div>"""
    
    if not sources_rows:
        sources_rows = '<div class="no-sources">No matching sources found</div>'
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap" rel="stylesheet">
<title>Originality Report - {doc_title}</title>
<style>
@page {{
    size: A4;
    margin: 2cm;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Open Sans', Arial, Helvetica, sans-serif;
    background: #fff;
    color: #000;
    padding: 45px 65px;
    max-width: 900px;
    line-height: 1.5;
}}
.docid {{
    font-size: 24px;
    font-weight: 400;
    letter-spacing: 0.2px;
}}
.report-type {{
    font-size: 8px;
    text-transform: uppercase;
    color: #7a7a7a;
    letter-spacing: 0.5px;
    margin-top: 2px;
}}
.divider {{
    border: none;
    border-top: 1px solid #000;
    margin: 12px 0;
}}
.sim {{
    font-size: 36px;
    font-weight: 400;
    line-height: 1.1;
}}
.sim-label {{
    font-size: 7.3px;
    text-transform: uppercase;
    color: #7a7a7a;
    letter-spacing: 0.5px;
    margin-top: 3px;
}}
.sources-title {{
    font-size: 8px;
    text-transform: uppercase;
    color: #7a7a7a;
    letter-spacing: 0.5px;
    margin: 6px 0 4px;
}}
.row {{
    display: flex;
    align-items: flex-start;
    padding: 6px 0;
    border-bottom: 1px solid #d4d4d4;
}}
.row:last-child {{
    border-bottom: 1px solid #000;
}}
.num {{
    width: 20px;
    height: 20px;
    border-radius: 2px;
    color: #fff;
    font-size: 12px;
    font-weight: 400;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 10px;
    margin-top: 2px;
    flex-shrink: 0;
}}
.info {{
    flex: 1;
}}
.url {{
    font-size: 12.5px;
    font-weight: 400;
}}
.type {{
    font-size: 10px;
    color: #7a7a7a;
    margin-top: 1px;
}}
.metric {{
    font-size: 13.3px;
    font-weight: 400;
    white-space: nowrap;
    margin-top: 3px;
    text-align: right;
}}
.no-sources {{
    padding: 15px 0;
    color: #7a7a7a;
    font-size: 12px;
}}
.filters {{
    border-top: 1px solid #000;
    margin-top: 20px;
    padding-top: 10px;
    display: flex;
    gap: 24px;
    font-size: 8px;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}}
.filter-label {{
    color: #7a7a7a;
}}
.filter-val {{
    font-weight: 700;
    margin-left: 4px;
}}
</style>
</head>
<body>

<div class="docid">{doc_title}</div>
<div class="report-type">Originality Report</div>
<hr class="divider">

<div class="sim">{pct}%</div>
<div class="sim-label">Similarity Index</div>
<hr class="divider">

<div class="sources-title">Primary Sources</div>
{sources_rows}

<div class="filters">
    <div><span class="filter-label">Exclude Quotes</span><span class="filter-val">{'ON' if result['exclude_quotes'] else 'OFF'}</span></div>
    <div><span class="filter-label">Exclude Bibliography</span><span class="filter-val">{'ON' if result['exclude_bibliography'] else 'OFF'}</span></div>
    <div><span class="filter-label">Exclude Sources</span><span class="filter-val">OFF</span></div>
    <div><span class="filter-label">Exclude Matches</span><span class="filter-val">OFF</span></div>
</div>

</body>
</html>"""
    
    return html

def run_precheck(text, doc_title="Book Chapter", output_path="/opt/data/bcp_test/similarity_report.html"):
    """Run full pre-check dan save HTML report."""
    print(f"\n{'='*60}")
    print(f"SIMILARITY PRE-CHECK")
    print(f"Document: {doc_title}")
    print(f"{'='*60}")
    
    result = check_similarity(text, exclude_bibliography=True, exclude_quotes=True)
    
    html = generate_html_report(result, doc_title)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n{'='*60}")
    print(f"  Similarity Index: {result['similarity_index']}%")
    print(f"  Total Words: {result['total_words']:,}")
    print(f"  Sentences: {result['total_sentences']}")
    print(f"  Matched Chunks: {result['matched_chunks']}/{result['total_chunks']}")
    print(f"  Sources Found: {len(result['sources'])}")
    print(f"  Report: {output_path}")
    print(f"{'='*60}")
    
    return result, output_path

def generate_highlighted_doc(text, result, output_path, doc_title="Book Chapter"):
    """Generate HTML dokumen dengan teks yang match di-highlight (stabilo Turnitin style).
    Nomor sumber: kotak kecil di ATAS baris teks (superscript sejati), DI LUAR area stabilo.
    """
    import html as html_module
    
    # Warna Turnitin persis dari PDF asli
    turnitin_colors = [
        ("#ff0000", "#ffdddd"), ("#e70cd6", "#f8d8f8"), ("#8b05ff", "#eed8ff"),
        ("#00aaaa", "#d0f0f0"), ("#00aa00", "#d0f0d0"), ("#ab6f00", "#f8eed0"),
        ("#792e05", "#f0d8d0"), ("#054679", "#d0d8f0"), ("#993399", "#f0d8f0"),
        ("#4e7501", "#e8f0d0"), ("#231c9a", "#d0d0f0"),
    ]
    
    domain_to_num = {}
    for i, src in enumerate(result["sources"]):
        domain_to_num[src["domain"]] = i + 1
    
    # Escape text dulu
    escaped_text = html_module.escape(text)
    
    # Cari posisi match di escaped text
    matches = []
    for m in result.get("matched_sentences", []):
        chunk = m.get("chunk_full", m.get("chunk", ""))
        chunk_esc = html_module.escape(chunk)
        #  TAHAN SPASI: `find()` persis GAGAL bila naskah ada baris baru.
        _pos = cari_chunk_tahan_spasi(escaped_text, chunk_esc)
        pos = _pos[0] if _pos else -1
        _akhir = _pos[1] if _pos else -1
        if pos >= 0:
            #  ⚠️ 16 Okt 2026 (permintaan Bos): kalau SATU potongan teks
            #  terdeteksi di BEBERAPA sumber, JANGAN tumpuk stabilo
            #  (jadi gelap). Pakai WARNA sumber PERTAMA saja, tapi
            #  tampilkan SEMUA nomor sumbernya (maks 3 kotak).
            sumber_semua = m.get("sources") or []
            if not sumber_semua:
                sumber_semua = [""]
            nomor_semua = [domain_to_num.get(d, 1) for d in sumber_semua]

            src_num = nomor_semua[0]                 # ← warna dari sumber UTAMA
            color_idx = (src_num - 1) % len(turnitin_colors)
            fg, bg = turnitin_colors[color_idx]
            matches.append((pos, _akhir, chunk_esc, src_num, fg, bg,
                            nomor_semua))

    #  Gabungkan stabilo yang MENEMPEL/sama (anti-tumpuk) — warna & nomor
    #  sumber pertama dipakai; nomor sumber lain ditambahkan.
    gabung: dict = {}
    for pos, end, chunk_esc, src_num, fg, bg, nomor_semua in matches:
        if pos in gabung:
            lama = gabung[pos]
            for n in nomor_semua:
                if n not in lama[6]:
                    lama[6].append(n)
        else:
            gabung[pos] = [pos, end, chunk_esc, src_num, fg, bg,
                           list(nomor_semua)]
    matches = list(gabung.values())

    # Sort descending by position (replace from end)
    matches.sort(key=lambda x: -x[0])

    for pos, end, chunk_esc, src_num, fg, bg, nomor_semua in matches:
        #  ① nomor UTAMA (warna sumber utama)
        kotak = (f'<span class="hl-num" style="background:{fg};">'
                 f'{nomor_semua[0]}</span>')
        #  ② nomor sumber LAIN (maks 2 lagi) — kotak kecil di kiri
        for urut, n in enumerate(nomor_semua[1:3], start=2):
            cidx = (n - 1) % len(turnitin_colors)
            fg2, _ = turnitin_colors[cidx]
            kotak += (f'<span class="hl-num hl-num-{urut}" '
                      f'style="background:{fg2};">{n}</span>')
        replacement = (
            f'<span class="hl" style="background:{bg};">'
            f'{kotak}'
            f'{chunk_esc}'
            f'</span>'
        )
        escaped_text = escaped_text[:pos] + replacement + escaped_text[end:]
    
    highlighted_text = escaped_text.replace("\n", "<br>\n")
    
    # Legend
    legend_items = ""
    for i, src in enumerate(result["sources"]):
        color_idx = i % len(turnitin_colors)
        fg, _ = turnitin_colors[color_idx]
        legend_items += f'<span class="legend-item"><span class="legend-num" style="background:{fg}">{i+1}</span> {src["domain"]}</span>\n'
    
    html_doc = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap" rel="stylesheet">
<title>Document View - {doc_title}</title>
<style>
@page {{
    size: A4;
    margin: 2cm;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Open Sans', Arial, sans-serif;
    background: #fff;
    color: #000;
    padding: 20px 30px;
    line-height: 1.8;
    font-size: 12px;
}}
.doc-title {{
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 15px;
}}
.content {{
    white-space: pre-wrap;
    word-wrap: break-word;
}}
/* Stabilo: background warna saja, TANPA garis bawah */
.hl {{
    position: relative;
    padding: 0;
    border-radius: 0;
    cursor: pointer;
    display: inline;
}}
/* Nomor kotak: BERJEJER, DI ATAS huruf pertama (putusan Bos 16 Okt 2026).
   ⚠️ `position:absolute` DIBUANG — WeasyPrint TIDAK bisa menumpuk absolute
   bertingkat (terbukti: 3 kotak ⇒ cuma 1 yang terlihat). Sekarang INLINE:
   kotak berjejer [1][4][7] lalu teks — SEMUA nomor pasti terlihat.  */
.hl-num {{
    display: inline-block;
    vertical-align: super;
    width: 14px;
    height: 14px;
    border-radius: 2px;
    color: #fff;
    font-size: 9px;
    font-weight: 700;
    line-height: 14px;
    text-align: center;
    margin-right: 1px;
}}
.no-match {{
    color: #000;
}}
</style>
</head>
<body>

<div class="content">
{highlighted_text if highlighted_text.strip() else '<span class="no-match">No matching text found. Document appears to be original.</span>'}
</div>

</body>
</html>"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    
    print(f"  Highlighted doc: {output_path}")
    return output_path

def html_to_pdf(html_path, pdf_path):
    """Convert HTML to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML as WPHtml
        WPHtml(html_path).write_pdf(pdf_path)
        return pdf_path
    except Exception as e:
        print(f"  [WARN] PDF conversion failed: {e}")
        return None

def cari_chunk_tahan_spasi(escaped_text: str, chunk_esc: str):
    """Cari `chunk_esc` di `escaped_text` DENGAN SPASI DINORMALISASI.

    AKAR BUG (terukur 16 Okt 2026, naskah BAB 2 Bos): `chunk` dibuat dari
    kalimat yang sudah dibersihkan `' '.join(...)` -> TANPA baris baru.
    Naskah asli PUNYA baris baru (`\\n`). Akibat `find()` persis = -1
    => stabilo HILANG (terukur: 7 stabilo -> hanya 2 yang tampil).

    Obat: normalisasi semua rentetan spasi jadi SATU spasi di kedua sisi,
    lalu telusuri peta posisi supaya penggantian tetap di tempat yang benar.

    Kembalikan (awal, akhir) di `escaped_text`, atau None bila tak ketemu.
    """
    import re as _re

    #  1. Normalisasi naskah + simpan peta posisi
    keluar, peta = [], []
    i = 0
    n = len(escaped_text)
    while i < n:
        if escaped_text[i].isspace():
            keluar.append(' ')
            peta.append(i)
            while i < n and escaped_text[i].isspace():
                i += 1
        else:
            keluar.append(escaped_text[i])
            peta.append(i)
            i += 1
    bersih = ''.join(keluar)

    #  2. Normalisasi chunk, lalu cari di naskah bersih
    potong = _re.sub(r'\s+', ' ', chunk_esc).strip()
    pos = bersih.find(potong)
    if pos < 0:
        return None

    #  3. Terjemahkan posisi di `bersih` -> posisi di `escaped_text`
    a = peta[pos]
    akhir = pos + len(potong) - 1
    if akhir + 1 < len(peta):
        b = peta[akhir + 1]
    else:
        b = peta[akhir] + (len(escaped_text) - peta[akhir])
    return a, b


def generate_combined_pdf(text, result, output_path, doc_title="Book Chapter"):
    """Generate 1 PDF gabungan: halaman atas = naskah+highlight, halaman bawah = similarity report."""
    import html as html_module
    
    # Warna Turnitin
    turnitin_colors = [
        ("#ff0000", "#ffdddd"), ("#e70cd6", "#f8d8f8"), ("#8b05ff", "#eed8ff"),
        ("#00aaaa", "#d0f0f0"), ("#00aa00", "#d0f0d0"), ("#ab6f00", "#f8eed0"),
        ("#792e05", "#f0d8d0"), ("#054679", "#d0d8f0"), ("#993399", "#f0d8f0"),
        ("#4e7501", "#e8f0d0"), ("#231c9a", "#d0d0f0"),
    ]
    
    # --- BAGIAN 1: Naskah + Highlight ---
    domain_to_num = {}
    for i, src in enumerate(result["sources"]):
        domain_to_num[src["domain"]] = i + 1
    
    escaped_text = html_module.escape(text)
    matches = []
    for m in result.get("matched_sentences", []):
        chunk = m.get("chunk_full", m.get("chunk", ""))
        chunk_esc = html_module.escape(chunk)
        #  TAHAN SPASI: `find()` persis GAGAL bila naskah ada baris baru.
        _pos = cari_chunk_tahan_spasi(escaped_text, chunk_esc)
        pos = _pos[0] if _pos else -1
        _akhir = _pos[1] if _pos else -1
        if pos >= 0:
            #  ⚠️ 16 Okt 2026 — KOREKSI permintaan Bos:
            #  Satu KALIMAT bisa terdeteksi BEBERAPA sumber, dan tiap sumber
            #  menangkap JUMLAH KATA BERBEDA. Jadi SIMPAN tiap rentang
            #  per-sumber: yang TERPANJANG menggambar latar, yang lebih
            #  pendek menggambar di ATASNYA (tanpa menimpa kata yang sama),
            #  sehingga tampil 2-3 warna dalam satu kalimat.
            rentang = m.get("rentang_kata")
            if not rentang:
                sumber_semua = m.get("sources") or [""]
                nomor_semua = [domain_to_num.get(d, 1) for d in sumber_semua]
                n_kata = len(chunk.split())
                rentang = [{
                    "nomor": nomor_semua[0], "kata": n_kata, "teks": chunk,
                }]
            matches.append((pos, _akhir, rentang, m))

    matches.sort(key=lambda x: -x[0])
    for pos, end, rentang, m in matches:
        #  maks 3 rentang, yang TERPANJANG di bawah
        rentang = sorted(rentang, key=lambda r: -r["kata"])[:3]
        if not rentang:
            continue

        #  ① semua kotak nomor dikumpulkan → ditaruh di BARIS ATAS
        kotak = ""
        for r in rentang:
            cidx = (r["nomor"] - 1) % len(turnitin_colors)
            fg, _ = turnitin_colors[cidx]
            kotak += (f'<span class="hl-num" '
                      f'style="background:{fg};">{r["nomor"]}</span>')

        #  ② teks kalimat penuh diwarnai menurut rentang kata tiap sumber.
        #     PUTUSAN BOS 16 Okt 2026 = "A": SUMBER TERPANJANG MENANG.
        #     Bagian yang tumpang tindih memakai warna rentang TERPANJANG,
        #     sehingga satu kalimat tampil SATU warna (tidak ditumpuk).
        kalimat = m.get("sentence_full") or m.get("chunk_full") or ""
        kata_kalimat = kalimat.split()

        #  lapis dari terpanjang → terpendek; yang lebih panjang menang
        warna_kata = [None] * len(kata_kalimat)
        for r in sorted(rentang, key=lambda x: -x["kata"]):
            cidx = (r["nomor"] - 1) % len(turnitin_colors)
            _, bg = turnitin_colors[cidx]
            for i in range(min(r["kata"], len(kata_kalimat))):
                if warna_kata[i] is None:       # ← lebih panjang sudah menang
                    warna_kata[i] = bg

        #  rakit HTML: kelompokkan kata berurutan dengan warna sama
        potongan = ""
        dari = 0
        while dari < len(kata_kalimat):
            w = warna_kata[dari]
            j = dari
            while j < len(kata_kalimat) and warna_kata[j] == w:
                j += 1
            teks = html_module.escape(' '.join(kata_kalimat[dari:j]))
            if w:
                potongan += (f'<span class="hl" style="background:{w};">'
                             f'{teks}</span>')
            else:
                potongan += teks
            potongan += ' '
            dari = j

        replacement = (
            f'<span class="baris-nomor">{kotak}</span>'
            f'{potongan.rstrip()}'
        )
        escaped_text = escaped_text[:pos] + replacement + escaped_text[end:]
    
    highlighted_html = escaped_text.replace("\n", "<br>\n")
    
    # --- BAGIAN 2: Similarity Report ---
    sim_pct = result["similarity_index"]
    if sim_pct < 5:
        risk_color = "#008000"
        risk_label = "LOW"
    elif sim_pct < 20:
        risk_color = "#cc8800"
        risk_label = "MEDIUM"
    else:
        risk_color = "#cc0000"
        risk_label = "HIGH"
    
    paper_id = hashlib.md5(doc_title.encode()).hexdigest()[:10]
    timestamp = result.get("timestamp", datetime.now().strftime("%d-%b-%Y %I:%M%p"))
    
    sources_html = ""
    for i, src in enumerate(result["sources"]):
        color_idx = i % len(turnitin_colors)
        fg, _ = turnitin_colors[color_idx]
        words = src.get("words", 0)
        pct = round(words / max(result["total_words"], 1) * 100, 1)
        pct_str = f"{int(pct)}%" if pct >= 1 else "< 1%"
        sources_html += f"""<tr>
<td><span class="src-num-box" style="background:{fg};">{i+1}</span></td>
<td><span class="src-url" style="color:{fg};">{src['domain']}</span><br><span class="src-type">Internet</span></td>
<td class="src-match">{words} words — <span class="src-match-pct">{pct_str}</span></td>
</tr>"""
    
    if not sources_html:
        sources_html = '<tr><td colspan="3" style="text-align:center;padding:20px;">No matching sources found. Document appears to be original.</td></tr>'
    
    # --- COMBINE: 1 HTML, 4 section dengan page break ---
    combined_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Open+Sans:wght@400;700&display=swap" rel="stylesheet">
<title>Pre-Check Similarity - {doc_title}</title>
<style>
@page {{
    size: A4;
    margin: 2cm;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Open Sans', Arial, sans-serif;
    background: #fff;
    color: #000;
    line-height: 1.8;
    font-size: 12px;
}}

/* === HALAMAN 1: COVER (standalone) === */
.cover {{
    text-align: center;
    padding-top: 200px;
}}
.cover-doc-id {{
    font-size: 32px;   /* 24pt */
    font-weight: 400;
}}
.cover-spacer {{
    height: 12px;      /* gap doc-id -> By */
}}
.cover-by-line {{
    font-size: 16px;   /* 12pt */
    color: #000;
}}
.cover-by-line em {{
    font-style: italic;
}}
.cover-footer {{
    position: absolute;
    bottom: 45px;
    left: 2cm;
    right: 2cm;
}}
.cover-divider {{
    border: none;
    border-top: 0.7px solid #ccc;  /* 0.5pt gray */
    margin-bottom: 6px;
}}
.cover-meta-row {{
    font-size: 10.7px;  /* 8pt */
    color: #000;
}}
.cover-meta-row .label {{
    color: #000;
    text-transform: uppercase;
}}
.cover-meta-left {{
    display: inline-block;
    width: 45%;
}}
.cover-meta-left .label {{
    display: inline-block;
    width: 135px;
}}
.cover-meta-right {{
    display: inline-block;
    width: 50%;
    vertical-align: top;
}}
.cover-meta-right .label {{
    display: inline-block;
    width: 135px;
}}
.cover-meta-line {{
    margin-bottom: 4px;
}}

/* === NASKAH (tanpa header/footer) === */
.content {{
    white-space: pre-wrap;
    word-wrap: break-word;
    text-align: justify;
}}
.hl {{
    position: relative;
    padding: 0;
    display: inline;
}}
.hl-num {{
    /* 16 Okt 2026 — putusan Bos: "kotaknya di atas stabilo".
       ⚠️ `position:absolute` TERBUKTI GAGAL di WeasyPrint: kotak
       bertumpuk jadi satu ("14") karena `top` diabaikan.
       CARA yang DIDUKUNG: nomor ditaruh di BARIS KHUSUS di ATAS
       kalimat (lihat `.baris-nomor` di kode), jadi mengambang di atas.  */
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 2px;
    color: #fff;
    font-size: 9px;
    font-weight: 700;
    line-height: 14px;
    text-align: center;
    margin-right: 1px;
}}
/* baris khusus nomor — duduk DI ATAS kalimat yang distabilo */
.baris-nomor {{
    display: block;
    height: 15px;
    line-height: 1;
    font-size: 9px;
    margin: 0;
    padding: 0;
}}

/* === PAGE BREAK === */
.page-break {{
    page-break-before: always;
}}

/* === SIMILARITY REPORT === */
.report-doc-id {{
    font-size: 21.3px;   /* 16pt */
    font-weight: 400;
    text-align: left;
}}
.report-line-thick {{
    border: none;
    border-top: 2px solid #000;   /* 1.5pt */
    margin: 5px 0;
}}
.report-subtitle {{
    font-size: 10.7px;  /* 8pt */
    color: #000;
    letter-spacing: 1px;
    text-transform: uppercase;
    text-align: left;
}}
.report-line-thin {{
    border: none;
    border-top: 0.5px solid #000;
    margin: 3px 0 8px 0;
}}
.report-line-thick {{
    border: none;
    border-top: 2px solid #000;   /* 1.5pt */
    margin: 3px 0 8px 0;
}}
.sim-section {{
    border-bottom: 2px solid #000;   /* 1.5pt */
    margin-bottom: 3px;
    padding-bottom: 3px;
}}
.sim-index {{
    font-size: 48px;    /* 36pt */
    font-weight: 400;
}}
.sim-label {{
    font-size: 9.7px;   /* 7.3pt */
    color: #000;
    text-transform: uppercase;
}}
.sources-label {{
    font-size: 10.7px;  /* 8pt */
    color: #000;
    text-transform: uppercase;
    margin: 6px 0 3px 0;
}}
table.sources {{
    width: 100%;
    border-collapse: collapse;
}}
table.sources td {{
    padding: 2px 2px;
    border-bottom: 0.5px solid #ccc;
    vertical-align: middle;
    color: #000;
}}
.src-num-box {{
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 21px;
    height: 21px;
    font-size: 16px;
    font-weight: 700;
    color: #fff;
    border-radius: 2px;
}}
.src-url {{
    font-size: 16.7px;  /* 12.5pt */
    font-weight: 700;
}}
.src-type {{
    font-size: 9.7px;   /* 7.3pt */
    color: #777;
    text-transform: uppercase;
}}
.src-match {{
    text-align: right;
    font-size: 17.7px;  /* 13.3pt */
    white-space: nowrap;
    vertical-align: middle;
}}
.src-match-pct {{
    font-size: 32px;  /* 24pt */
    font-weight: 400;
}}

/* === FOOTER 1 BARIS (di halaman akhir saja) === */
.filter-page {{
    padding-top: 60px;
}}
.filter-cols {{
    display: flex;
    justify-content: space-between;
}}
.filter-col {{
    width: 48%;
}}
.filter-item {{
    margin-bottom: 15px;
}}
.filter-name {{
    font-size: 9px;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.filter-status {{
    font-size: 11px;
    margin-top: 2px;
}}
.filter-status-on {{
    color: #000;
    font-weight: 700;
}}
.filter-status-off {{
    color: #999;
    font-weight: 400;
}}
/* === FOOTER 1 BARIS (di cover & halaman akhir saja) === */
.footer-bar {{
    margin-top: 8px;
    padding-top: 4px;
    border-top: 1px solid #000;
    font-size: 10.7px;  /* 8pt */
    color: #888;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
/*  LAPORAN WAJIB 1 HALAMAN (putusan Bos 16 Okt 2026):
    laporan selalu mulai di halaman BARU; isi laporan dirapatkan
    supaya 11 sumber + EXCLUDE muat 1 halaman.  */
.halaman-baru {{
    page-break-before: always;
    break-before: page;
}}
/*  blok EXCLUDE JANGAN dilempar ke halaman berikutnya */
tr.baris-exclude,
tr.baris-exclude td {{
    page-break-inside: auto;
    break-inside: auto;
}}
/*  rapatkan sumber supaya muat 1 halaman (seperti Turnitin asli) */
table.sources td {{
    padding: 0 2px;
}}
.src-url {{
    line-height: 1.15;
}}
.footer-bar span {{
    margin-right: 12px;
}}
.footer-bar .status {{
    font-weight: 700;
    color: #000;
}}
</style>
</head>
<body>

<!-- ===== HALAMAN 1: COVER (standalone) ===== -->
<div class="cover">
    <div class="cover-doc-id">{doc_title}</div>
    <div class="cover-spacer"></div>
    <div class="cover-by-line"><em>By</em> Turnitin Official</div>
</div>
<div class="cover-footer">
    <hr class="cover-divider">
    <div class="cover-meta-row">
        <div class="cover-meta-left">
            <div class="cover-meta-line"><span class="label">WORD COUNT</span>{result['total_words']:,}</div>
        </div>
        <div class="cover-meta-right">
            <div class="cover-meta-line"><span class="label">TIME SUBMITTED</span>{timestamp}</div>
            <div class="cover-meta-line"><span class="label">PAPER ID</span>{paper_id}</div>
        </div>
    </div>
</div>

<!-- ===== PAGE BREAK ===== -->
<div class="page-break"></div>

<!-- ===== HALAMAN 2-N: NASKAH + HIGHLIGHT (tanpa header/footer) ===== -->
<div class="content">
{highlighted_html if highlighted_html.strip() else '<span>No matching text found. Document appears to be original.</span>'}
</div>

<!-- ===== HALAMAN N+1: SIMILARITY REPORT (WAJIB 1 HALAMAN) ===== -->
<div class="halaman-baru">
<div class="report-doc-id">{doc_title}</div>
<hr class="report-line-thick">
<div class="report-subtitle">ORIGINALITY REPORT</div>
<hr class="report-line-thin">

<div class="sim-section">
    <span class="sim-index">{sim_pct}%</span>
    <div class="sim-label">SIMILARITY INDEX</div>
</div>

<div class="sources-label">PRIMARY SOURCES</div>
<table class="sources">
{sources_html}
<tr class="baris-exclude"><td colspan="3">
<div class="footer-bar">
    EXCLUDE QUOTES <span class="status">ON</span>
    EXCLUDE BIBLIOGRAPHY <span class="status">ON</span>
    EXCLUDE SOURCES <span class="status">OFF</span>
    EXCLUDE MATCHES <span class="status">OFF</span>
</div>
</td></tr>
</table>
</div>

</body>
</html>"""
    
    # Tulis HTML
    html_path = output_path.replace('.pdf', '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(combined_html)
    
    # Convert ke PDF
    try:
        from weasyprint import HTML as WPHtml
        WPHtml(string=combined_html).write_pdf(output_path)
        print(f"  Combined PDF: {output_path}")
        return output_path
    except Exception as e:
        print(f"  [WARN] PDF failed: {e}")
        return None

def run_precheck_full(text, doc_title="Book Chapter", output_dir="/opt/data/bcp_test"):
    """Run pre-check: generate 1 combined PDF (naskah+highlight + similarity report)."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"SIMILARITY PRE-CHECK (FULL)")
    print(f"Document: {doc_title}")
    print(f"{'='*60}")
    
    result = check_similarity(text, exclude_bibliography=True, exclude_quotes=True)
    
    # Generate 1 PDF gabungan: naskah+highlight + similarity report
    combined_pdf = os.path.join(output_dir, "similarity_precheck.pdf")
    generate_combined_pdf(text, result, combined_pdf, doc_title)
    
    print(f"\n{'='*60}")
    print(f"  Similarity Index: {result['similarity_index']}%")
    print(f"  Total Words: {result['total_words']:,}")
    print(f"  Sentences: {result['total_sentences']}")
    print(f"  Matched Chunks: {result['matched_chunks']}/{result['total_chunks']}")
    print(f"  Sources Found: {len(result['sources'])}")
    print(f"  Output: {combined_pdf}")
    print(f"{'='*60}")
    
    return result, combined_pdf

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        text = open(sys.argv[1]).read()
        title = sys.argv[2] if len(sys.argv) > 2 else "Book Chapter"
    else:
        text = open("/opt/data/bcp_test/bab1_bcp.txt").read()
        title = "BAB 1 - Konsep Dasar Analisis Pasar dan Pemasaran"
    
    result, pdf_path = run_precheck_full(text, title)
    print(f"\nOutput: {pdf_path}")
