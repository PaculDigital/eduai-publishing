#!/usr/bin/env python3
"""
verifikasi_sitasi.py — Modul pencarian & lock-in referensi akademik nyata.

STRATEGI: Search-then-Lock (Opsi A + Web Search)
1. SEBELUM generate: cari referensi nyata di OpenAlex + Crossref + Google Books
2. Feed list referensi ke LLM: "HANYA kutip dari list ini"
3. SETELAH generate: verifikasi semua sitasi match dengan list

API gratis:
- OpenAlex: https://api.openalex.org (tanpa key, 100rb/hari) — jurnal + artikel
- Crossref: https://api.crossref.org (tanpa key) — jurnal + ebook ber-DOI
- Google Books: https://www.googleapis.com/books/v1 (tanpa key) — BUKU terbitan
"""
import re, json, time, urllib.request, urllib.parse

USER_AGENT = "BCP-Book-Pipeline/1.0 (mailto:syahrul@example.com)"
OPENALEX_BASE = "https://api.openalex.org/works"
CROSSREF_BASE = "https://api.crossref.org/works"
TIMEOUT = 15
_cache = {}


def _fetch_json(url):
    if url in _cache:
        return _cache[url]
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            _cache[url] = data
            return data
    except Exception as e:
        return None


def search_openalex(topic, n=5, year_min=2000):
    """Cari di OpenAlex (artikel jurnal + buku + book chapter)."""
    query = urllib.parse.quote(topic)
    url = (f"{OPENALEX_BASE}?search={query}"
           f"&filter=from_publication_date:{year_min}-01-01"
           f"&per-page={n}&sort=relevance_score:desc"
           f"&select=id,doi,title,publication_year,authorships,primary_location,type")
    data = _fetch_json(url)
    results = []
    if data and "results" in data:
        for item in data["results"]:
            authors = []
            for a in item.get("authorships", []):
                name = a.get("author", {}).get("display_name", "")
                if name:
                    parts = name.split()
                    if len(parts) >= 2:
                        authors.append(f"{parts[-1]}, {' '.join(p[0]+'.' for p in parts[:-1])}")
                    else:
                        authors.append(name)
            title = (item.get("title") or "").strip()
            year = item.get("publication_year")
            doi = (item.get("doi") or "").replace("https://doi.org/", "")
            journal = ((item.get("primary_location") or {}).get("source") or {}).get("display_name", "")
            item_type = item.get("type", "article")
            if title and year and authors:
                results.append({
                    "authors": authors, "year": year, "title": title,
                    "journal": journal, "doi": doi, "source": "OpenAlex",
                    "type": "book" if "book" in item_type else "article",
                })
    return results


def search_crossref(topic, n=5, year_min=2000):
    """Cari di Crossref (jurnal + ebook ber-DOI)."""
    query = urllib.parse.quote(topic)
    url = (f"{CROSSREF_BASE}?query={query}"
           f"&filter=from-pub-date:{year_min}-01-01"
           f"&rows={n}&select=author,title,published-print,published-online,DOI,container-title,type")
    data = _fetch_json(url)
    results = []
    if data and "message" in data and "items" in data["message"]:
        for item in data["message"]["items"]:
            authors = []
            for a in item.get("author", []):
                family = a.get("family", "")
                given = a.get("given", "")
                if family:
                    # "M. E. Porter"
                    initials = " ".join(g[0]+"." for g in given.split() if g) if given else ""
                    authors.append(f"{family}, {initials}" if initials else family)
            title_arr = item.get("title", [])
            title = title_arr[0].strip() if title_arr else ""
            pub = item.get("published-print") or item.get("published-online") or {}
            year = None
            if pub and pub.get("date-parts") and pub["date-parts"][0]:
                year = pub["date-parts"][0][0]
            doi = item.get("DOI", "")
            ct = item.get("container-title", [])
            journal = ct[0] if ct else ""
            item_type = item.get("type", "article")
            if title and year and authors:
                results.append({
                    "authors": authors, "year": year, "title": title,
                    "journal": journal, "doi": doi, "source": "Crossref",
                    "type": "book" if "book" in item_type else "article",
                })
    return results


# NOTE: search_google_books() DIHAPUS (18 Agu 2026) — dead code, tidak pernah dipanggil.
# Google Books API kena rate limit (~1000 req/hari). Pipeline hanya pakai:
#   - OpenAlex (100rb/hari, gratis, tanpa key) — jurnal + buku + book chapter
#   - Crossref (tanpa key) — jurnal + ebook ber-DOI
# Jika perlu cari buku non-DOI yang tidak ada di OpenAlex, bisa aktifkan ulang dengan
# menambahkan try/except rate-limit handling.


def search_real_references(topic, n=8, year_min=2000):
    """Cari referensi nyata dari 3 sumber: OpenAlex + Crossref + Google Books.
    
    Returns list of dict dengan format APA 7.
    """
    print(f"  [VERIF] Mencari referensi nyata: '{topic}'")
    all_results = []
    
    # 1. OpenAlex (artikel + buku)
    articles = search_openalex(topic, n=n, year_min=year_min)
    all_results.extend(articles)
    time.sleep(0.3)
    
    # 2. Crossref (tambahan jika kurang)
    if len(all_results) < n:
        cr = search_crossref(topic, n=n - len(all_results) + 2, year_min=year_min)
        all_results.extend(cr)
    
    # Dedupe by title
    seen = set()
    unique = []
    for r in all_results:
        key = r["title"].lower()[:80]
        if key not in seen and r["title"]:
            seen.add(key)
            unique.append(r)
    
    print(f"  [VERIF] {len(unique)} referensi nyata ditemukan (OpenAlex={len(articles)}, Crossref={len(all_results)-len(articles)})")
    return unique[:n]


def format_apa(ref):
    """Format referensi ke APA 7. Accept dict atau string."""
    if isinstance(ref, str):
        return ref  # Already APA formatted string
    authors = ref.get("authors", [])
    year = ref.get("year")
    title = ref.get("title", "")
    journal = ref.get("journal", "")
    doi = ref.get("doi", "")
    ref_type = ref.get("type", "article")
    
    # Format authors APA 7
    if len(authors) == 1:
        author_str = authors[0]
    elif len(authors) == 2:
        author_str = f"{authors[0]}, & {authors[1]}"
    elif len(authors) > 2:
        author_str = f"{authors[0]}, et al."
    else:
        author_str = "Anonim"
    
    entry = f"{author_str} ({year}). {title}."
    if ref_type == "book" or ref_type == "article":
        if journal:
            entry += f" {journal}."
    if doi and doi.startswith("10."):
        entry += f" https://doi.org/{doi}"
    return entry


def format_in_text(ref):
    """Format sitasi in-text APA 7: (Author, Year) atau (Author & Author, Year). Accept dict atau string."""
    if isinstance(ref, str):
        # Parse string "Porter, M. E. (1985). Competitive advantage..." → "(Porter, 1985)"
        import re
        # Match "Surname, ... (Year)" pattern
        m = re.match(r'^([A-Z][a-zA-Z\-]+)', ref)
        year_match = re.search(r'\((\d{4})\)', ref)
        if m and year_match:
            surname = m.group(1)
            year = year_match.group(1)
            # Check for "&" (2 authors) or "et al." (3+ authors)
            pre_year = ref[:ref.index(year_match.group(0))]
            # Count authors: split by comma, check for "&"
            # "Porter, M. E." → 1 author (1 comma before initials)
            # "Kotler, P., & Keller, K. L." → 2 authors (has "&")
            # "Osterwalder, A., Pigneur, Y., Bernarda, G., & Smith, A." → 4 authors (multiple commas + "&")
            ampersand_count = pre_year.count(' & ')
            # Count potential author entries: pattern "Surname, Initials."
            author_entries = re.findall(r'[A-Z][a-zA-Z\-]+,\s+[A-Z]\.', pre_year)
            if len(author_entries) >= 3:
                # 3+ authors → et al.
                return f"({surname} et al., {year})"
            elif ampersand_count == 1 and len(author_entries) == 2:
                # 2 authors — get second surname
                m2 = re.search(r'&\s+([A-Z][a-zA-Z\-]+)', pre_year)
                if m2:
                    return f"({surname} & {m2.group(1)}, {year})"
            return f"({surname}, {year})"
        return "(Anonim, n.d.)"
    authors = ref.get("authors", [])
    year = ref.get("year")
    
    if not authors:
        return f"(Anonim, {year})"
    
    # Extract surname dari "Porter, M. E." → "Porter"
    surnames = []
    for a in authors:
        if "," in a:
            surnames.append(a.split(",")[0].strip())
        else:
            surnames.append(a.split()[-1])
    
    if len(surnames) == 1:
        return f"({surnames[0]}, {year})"
    elif len(surnames) == 2:
        return f"({surnames[0]} & {surnames[1]}, {year})"
    else:
        return f"({surnames[0]} et al., {year})"


def build_citation_prompt(refs):
    """Buat string untuk disisipkan ke prompt LLM: list referensi yang BOLEH dikutip."""
    lines = ["REFERENSI YANG TERVERIFIKASI (HANYA kutip dari list ini):"]
    for i, ref in enumerate(refs, 1):
        apa = format_apa(ref)
        in_text = format_in_text(ref)
        lines.append(f"{i}. {apa}")
        lines.append(f"   Sitasi in-text: {in_text}")
    lines.append("DILARANG MENGARANG sitasi baru. HANYA gunakan sitasi dari list di atas.")
    return "\n".join(lines)


def verify_text_citations(text, allowed_refs, mode="hapus"):
    """Verifikasi: semua sitasi in-text harus ada di allowed_refs.

    mode hapus (default): clean_text adalah teks dengan sitasi tak
    terverifikasi dihapus (perilaku lama, dipakai semua pemanggil lama).
    mode lapor: clean_text adalah teks APA ADANYA (tidak diubah),
    pemanggil yang memutuskan (lapor, tulis ulang, atau hapus sebagai
    jalan terakhir). Dipakai jalur snapshot pra-panen.

    Returns:
        dict: {verified, unverified, clean_text}
    """
    # Build set of allowed in-text citations
    allowed_citations = set()
    for ref in allowed_refs:
        cite = format_in_text(ref)
        allowed_citations.add(cite)
        # Also add variants for flexible matching
        if isinstance(ref, str):
            # String ref — format_in_text already parsed it, add to allowed set
            # Also extract surname + year for variant matching
            import re as _re
            m = _re.match(r'^([A-Z][a-zA-Z\-]+)', ref)
            year_m = _re.search(r'\((\d{4})\)', ref)
            if m and year_m:
                surname = m.group(1)
                year = year_m.group(1)
                # Count authors for et al. variant
                pre_year = ref[:ref.index(year_m.group(0))]
                author_entries = _re.findall(r'[A-Z][a-zA-Z\-]+,\s+[A-Z]\.', pre_year)
                allowed_citations.add(f"({surname}, {year})")
                if len(author_entries) >= 3:
                    allowed_citations.add(f"({surname} et al., {year})")
                    allowed_citations.add(f"({surname} et al, {year})")
                elif len(author_entries) == 2:
                    m2 = _re.search(r'&\s+([A-Z][a-zA-Z\-]+)', pre_year)
                    if m2:
                        allowed_citations.add(f"({surname} & {m2.group(1)}, {year})")
        else:
            authors = ref.get("authors", [])
            year = ref.get("year")
            if authors:
                surname = authors[0].split(",")[0].strip() if "," in authors[0] else authors[0].split()[-1]
                allowed_citations.add(f"({surname}, {year})")
                # Add "et al." variant for refs with 2+ authors (LLM might abbreviate)
                if len(authors) >= 2:
                    allowed_citations.add(f"({surname} et al., {year})")
                    allowed_citations.add(f"({surname} et al, {year})")
    
    # Extract all in-text citations from text
    # Handle: (Porter, 1985), (Porter & Kramer, 2011), (Porter et al., 2019), (Wang et al, 2020)
    pattern = r'\(([A-Z][A-Za-z]+(?:\s+(?:&|et al\.?,?)\s+[A-Z][A-Za-z]+|\s+et al\.?,?)?,?\s+\d{4}[a-z]?)\)'
    found_citations = re.findall(pattern, text)
    
    verified = []
    unverified = []
    
    for cite_raw in found_citations:
        cite_clean = cite_raw.strip()
        # Normalize: remove extra spaces
        cite_normalized = re.sub(r'\s+', ' ', f"({cite_clean})")
        
        # Check if this citation matches any allowed
        matched = False
        for allowed in allowed_citations:
            if cite_clean.lower() in allowed.lower() or allowed.lower() in cite_normalized.lower():
                matched = True
                break
        
        if matched:
            verified.append(f"({cite_clean})")
        else:
            unverified.append(f"({cite_clean})")
    
    # Remove unverified citations from text (mode hapus saja).
    # Mode lapor: teks dikembalikan apa adanya, tanpa penghapusan.
    if mode == "lapor":
        clean_text = text
    else:
        clean_text = text
        for cite in unverified:
            clean_text = clean_text.replace(cite, "")
    #  🚨 BUG TERUKUR 20 Okt 2026 — AKAR "1 baris = 6.302 karakter":
    #  `\s{2,}` juga cocok dengan `\n\n` (baris kosong pemisah paragraf),
    #  sehingga SELURUH paragraf DIGABUNG jadi satu baris. Akibatnya
    #  perbaikan pemecah paragraf di `post_process` DIBATALKAN di sini,
    #  dan buku keluar sebagai satu blok raksasa.
    #  OBAT: rapikan spasi HANYA di dalam baris — baris baru TIDAK disentuh.
    if mode != "lapor":
        clean_text = re.sub(r'[ \t]{2,}', ' ', clean_text)     # spasi/tab dobel
        clean_text = re.sub(r'[ \t]+\n', '\n', clean_text)     # spasi sisa di ujung baris
        clean_text = re.sub(r'\n[ \t]+', '\n', clean_text)     # spasi sisa di awal baris
        clean_text = re.sub(r' \.([ \t]|$|\n)', r'.\1', clean_text)  # spasi sebelum titik
        clean_text = re.sub(r'\n{3,}', '\n\n', clean_text)     # baris kosong berlebih

    return {
        "verified": verified,
        "unverified": unverified,
        "clean_text": clean_text,
        "allowed_count": len(allowed_citations),
        "match_note": ("Fix 19 Agu 2026: allowed_citations juga add 'surname et al., year' "
                       "dan 'surname, year' (surname doang) agar bisa match format mixed. "
                       "Mis: ref 2 penulis -> allowed (Barney & Hesterly, 2019) + (Barney et al., 2019) + (Barney, 2019)")
    }


# === TEST ===
if __name__ == "__main__":
    print("=== TEST MODUL VERIFIKASI SITASI (Search-then-Lock) ===\n")
    
    # Test 1: search referensi
    print("Test 1: Search 'competitive advantage Porter'")
    refs = search_real_references("competitive advantage Porter strategic management", n=5)
    for r in refs:
        apa = format_apa(r)
        in_text = format_in_text(r)
        print(f"  {in_text}")
        print(f"    {apa[:100]}")
        print(f"    Source: {r['source']} | Type: {r['type']}")
        print()
    
    # Test 2: build prompt
    print("\nTest 2: Citation prompt for LLM")
    prompt = build_citation_prompt(refs[:3])
    print(prompt[:500])
    
    # Test 3: verify
    print("\n\nTest 3: Verify text citations")
    sample_text = """Menurut (Porter, 1985), competitive advantage adalah kemampuan perusahaan
    untuk memberikan nilai superior. Christensen (1997) memperkenalkan konsep disruptive
    innovation. Studi terbaru (Hidayat, 2021) menunjukkan dampak digitalisasi."""
    result = verify_text_citations(sample_text, refs[:3])
    print(f"  Allowed: {result['allowed_count']} citations")
    print(f"  Verified: {result['verified']}")
    print(f"  Unverified: {result['unverified']}")
