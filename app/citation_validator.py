"""Citation Validator — Fase 6 EduAi Publishing.

Sumber: penelitian-bot/telegram-bot/agents/citation-validator.js (READ-ONLY, 320 baris).
Adaptasi Python: fungsi utama diekspos untuk dipanggil dari konsistensi.py / ai.py.
TIDAK menggunakan AI (Rp 0).

Fungsi:
  extract_citations(text) → list[dict] — sitasi ditemukan di teks
  build_author_index(literature) → dict — indeks penulis dari daftar literatur
  is_citation_valid(citation, author_index) → dict — sitasi valid? cocok dengan literatur?
  validate_content(text, literature) → dict — validasi lengkap: sitasi + klaim tanpa sitasi
  format_report(validation) → str — laporan format teks

Aturan:
  - Sitasi format: (Author, Tahun) atau (Author et al., Tahun) atau (Author1 & Author2, Tahun)
  - Sitasi tunggal: (Author, Tahun) — minimal 2 huruf awal nama
  - Klaim panjang (>100 char) tanpa sitasi = unsupported claim
  - Kalimat pembuka standar (selain itu/oleh karena itu/dll) dikecualikan
  - Tabel/gambar/bab juga dikecualikan
  - Skor = 0.6 * citation_accuracy + 0.4 * claim_coverage
"""
import re
from typing import Any

# ════════════════════════════════════════════════════════════════
# 1. REGEX SITASI (adaptasi langsung dari JS)
# ════════════════════════════════════════════════════════════════
# Sitasi multi-penulis: (Author, 2024) atau (Author et al., 2024) atau (Author1 & Author2, 2024)
CITATION_REGEX = re.compile(
    r"\(([A-Z][a-zA-ZÀ-ÿ]+(?:\s*(?:et\s+al\.|&\s*[A-Z][a-zA-ZÀ-ÿ]+|,\s*[A-Z][a-zA-ZÀ-ÿ]+\s*[A-Z][a-zA-ZÀ-ÿ]+))?)(?:,\s*|\s+)(\d{4}[a-z]?)\)",
    re.UNICODE,
)

# Sitasi tunggal penulis: (Author, 2024) — minimal 2 huruf
SINGLE_AUTHOR_REGEX = re.compile(
    r"\(([A-Z][a-zA-ZÀ-ÿ]{2,}),?\s*(\d{4}[a-z]?)\)",
    re.UNICODE,
)

# ════════════════════════════════════════════════════════════════
# 2. EKSTRAKSI TEKS DARI STRUKTUR NESTED
# ════════════════════════════════════════════════════════════════

def _extract_all_text(obj: Any) -> list[str]:
    """Rekursif: ambil semua string dari dict/list/nested object.
    Adaptasi dari extractAllText() di JS (baris 9-28)."""
    if obj is None:
        return []
    texts: list[str] = []
    if isinstance(obj, str):
        texts.append(obj)
    elif isinstance(obj, list):
        for item in obj:
            texts.extend(_extract_all_text(item))
    elif isinstance(obj, dict):
        for value in obj.values():
            if isinstance(value, str):
                texts.append(value)
            elif isinstance(value, (list, dict)):
                texts.extend(_extract_all_text(value))
    return texts


# ════════════════════════════════════════════════════════════════
# 3. EKSTRAKSI SITASI
# ════════════════════════════════════════════════════════════════

def extract_citations(text: str) -> list[dict]:
    """Ekstrak semua sitasi dari teks.
    Adaptasi dari extractCitations() di JS (baris 30-57).

    Return: list of {author, year, raw, position}
    """
    if not text or not isinstance(text, str):
        return []

    citations: dict[str, dict] = {}

    for match in CITATION_REGEX.finditer(text):
        author = match.group(1).strip()
        year = match.group(2).strip()
        key = f"{author.lower()}_{year}"
        if key not in citations:
            citations[key] = {
                "author": author,
                "year": year,
                "raw": match.group(0),
                "position": match.start(),
            }

    for match in SINGLE_AUTHOR_REGEX.finditer(text):
        author = match.group(1).strip()
        year = match.group(2).strip()
        key = f"{author.lower()}_{year}"
        if key not in citations:
            citations[key] = {
                "author": author,
                "year": year,
                "raw": match.group(0),
                "position": match.start(),
            }

    return list(citations.values())


# ════════════════════════════════════════════════════════════════
# 4. INDEKS PENULIS
# ════════════════════════════════════════════════════════════════

def _normalize_author(author: str) -> str:
    """Normalisasi nama penulis.
    Adaptasi dari normalizeAuthor() di JS (baris 59-65).
    JS: toLowerCase → replace multiple spaces with 1 space → remove punctuation → trim.
    Python: ikut logika yang SAMA — spasi dirapikan jadi 1, bukan dihapus."""
    return re.sub(r"\s+", " ", author.lower().replace(".", "").replace(",", "")).strip()


def build_author_index(literature: list[dict]) -> dict:
    """Bangun indeks penulis dari daftar literatur.
    Adaptasi dari buildAuthorIndex() di JS (baris 67-104).

    Return: {byLastName: dict, byYear: dict}
    """
    if not literature:
        return {"byLastName": {}, "byYear": {}}

    by_last_name: dict[str, list[dict]] = {}
    by_year: dict[str, list[dict]] = {}

    for article in literature:
        year = str(article.get("year") or "").strip()
        if not year:
            continue

        authors_str = article.get("authors") or ""
        # Pisah penulis: koma/semicolon atau "and"
        author_list = re.split(r"[,;]\s*|\s+and\s+", authors_str, flags=re.IGNORECASE)
        author_list = [a.strip() for a in author_list if a.strip()]

        for author in author_list:
            clean = _normalize_author(author)
            parts = clean.split()
            last_name = parts[-1] if parts else clean
            first_initial = parts[0][0] if parts and parts[0] else ""

            key = f"{last_name}_{year}"
            if key not in by_last_name:
                by_last_name[key] = []
            by_last_name[key].append({
                "author": clean,
                "lastName": last_name,
                "firstInitial": first_initial,
                "year": year,
                "title": article.get("title") or "",
            })

        if year not in by_year:
            by_year[year] = []
        by_year[year].append(article)

    return {"byLastName": by_last_name, "byYear": by_year}


# ════════════════════════════════════════════════════════════════
# 5. VALIDASI SITASI
# ════════════════════════════════════════════════════════════════

def is_citation_valid(citation: dict, author_index: dict) -> dict:
    """Periksa apakah sitasi cocok dengan literatur.
    Adaptasi dari isCitationValid() di JS (baris 106-147).

    Return: {valid: bool, match?: dict, partial?: bool}
    """
    author = citation["author"]
    year = citation["year"]
    clean = _normalize_author(author)
    parts = clean.split()
    last_name = parts[-1] if parts else clean
    first_initial = parts[0][0] if parts and parts[0] else ""

    # Cari langsung: lastName + year
    direct_key = f"{last_name}_{year}"
    candidates = author_index.get("byLastName", {}).get(direct_key, [])
    for c in candidates:
        if c["year"] == year:
            if first_initial and c["firstInitial"] and c["firstInitial"] != first_initial:
                continue
            return {"valid": True, "match": c}

    # Cari tanpa initial (partial match)
    for c in candidates:
        if not first_initial or not c["firstInitial"]:
            return {"valid": True, "match": c, "partial": True}

    # Cari di byYear (pencarian lebih luas)
    year_candidates = author_index.get("byYear", {}).get(year, [])
    for c in year_candidates:
        c_authors = c.get("authors") or ""
        c_author_list = re.split(r"[,;]\s*|\s+and\s+", c_authors, flags=re.IGNORECASE)
        for c_author in c_author_list:
            c_clean = _normalize_author(c_author)
            c_parts = c_clean.split()
            c_last = c_parts[-1] if c_parts else c_clean
            if c_last == last_name:
                if first_initial and c_parts[0] and c_parts[0][0] != first_initial:
                    continue
                return {
                    "valid": True,
                    "match": {"author": c_clean, "year": year, "title": c.get("title", "")},
                    "partial": not bool(first_initial),
                }

    return {"valid": False}


# ════════════════════════════════════════════════════════════════
# 6. VALIDASI KONTEN LENGKAP
# ════════════════════════════════════════════════════════════════

def validate_content(text: str, literature: list[dict]) -> dict:
    """Validasi lengkap: sitasi valid + klaim tanpa sitasi.
    Adaptasi dari validateGeneratedContent() di JS (baris 149-206).

    Return: {ok, citations, validCitations, invalidCitations, unsupportedClaims, score, ...}
    """
    if not text:
        return {
            "ok": True,
            "citations": [],
            "validCitations": [],
            "invalidCitations": [],
            "unsupportedClaims": [],
            "totalTextLength": 0,
            "totalClaims": 0,
            "citationDensity": 0,
            "citationAccuracy": 1.0,
            "claimCoverage": 1.0,
            "score": 1.0,
            "literaturePoolSize": 0,
        }

    author_index = build_author_index(literature or [])
    all_texts = _extract_all_text(text)
    full_text = "\n".join(all_texts) if isinstance(text, str) else text

    citations = extract_citations(full_text)
    valid_citations: list[dict] = []
    invalid_citations: list[dict] = []

    for c in citations:
        result = is_citation_valid(c, author_index)
        if result["valid"]:
            valid_citations.append({**c, "matchedArticle": result.get("match")})
        else:
            invalid_citations.append(c)

    # Deteksi klaim tanpa sitasi
    sentences = re.split(r"[.!?]+", full_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 30]

    # Pola pengecualian
    PEMBAWA_STANDAR = re.compile(
        r"^(selain itu|oleh karena itu|berdasarkan data|hasil uji|dengan demikian|oleh sebab itu)",
        re.IGNORECASE,
    )
    PEMBAWA_NUMERIK = re.compile(r"\d+\.\d+")
    PEMBAWA_SITASI = re.compile(r"\([A-Z][a-z]+.*\d{4}\)")
    PEMBAWA_BAB = re.compile(r"\b(tabel|gambar|bab|chapter|table|figure)\s+\d", re.IGNORECASE)

    unsupported_claims: list[str] = []
    for sentence in sentences:
        if PEMBAWA_STANDAR.match(sentence):
            continue
        if PEMBAWA_NUMERIK.search(sentence):
            continue
        if PEMBAWA_SITASI.search(sentence):
            continue
        if PEMBAWA_BAB.match(sentence):
            continue

        if len(sentence) > 100:
            if not PEMBAWA_SITASI.search(sentence):
                unsupported_claims.append(sentence[:150])

    total_claims = len(sentences)
    claim_coverage = (total_claims - len(unsupported_claims)) / total_claims if total_claims > 0 else 1.0
    citation_accuracy = len(valid_citations) / len(citations) if citations else 1.0
    score = (citation_accuracy * 0.6) + (claim_coverage * 0.4)

    return {
        "ok": len(invalid_citations) == 0 and score >= 0.7,
        "citations": citations,
        "validCitations": valid_citations,
        "invalidCitations": invalid_citations,
        "unsupportedClaims": unsupported_claims,
        "totalTextLength": len(full_text),
        "totalClaims": total_claims,
        "citationDensity": len(citations) / total_claims if total_claims > 0 else 0,
        "citationAccuracy": citation_accuracy,
        "claimCoverage": claim_coverage,
        "score": score,
        "literaturePoolSize": len(literature or []),
    }


# ════════════════════════════════════════════════════════════════
# 7. FORMAT LAPORAN
# ════════════════════════════════════════════════════════════════

def format_report(validation: dict) -> str:
    """Format laporan validasi sitasi.
    Adaptasi dari formatValidationReport() di JS (baris 275-311)."""
    lines: list[str] = []

    if validation.get("ok"):
        lines.append("✅ Citation Validation: PASSED")
    else:
        lines.append("⚠️ Citation Validation: ISSUES FOUND")

    lines.append(f"📊 Score: {(validation.get('score', 0) * 100):.0f}%")
    lines.append(f"📚 Literature pool: {validation.get('literaturePoolSize', 0)} artikel")
    lines.append(
        f"📝 Total text: {validation.get('totalTextLength', 0)} chars, "
        f"{validation.get('totalClaims', 0)} klaim"
    )

    lines.append("\n🔗 Citations:")
    lines.append(f"  ✅ Valid: {len(validation.get('validCitations', []))}")
    lines.append(f"  ❌ Invalid: {len(validation.get('invalidCitations', []))}")

    if validation.get("invalidCitations"):
        lines.append("\n  Invalid citations detail:")
        for c in validation["invalidCitations"][:10]:
            lines.append(f"    - ({c['author']}, {c['year']}) at pos {c.get('position', '?')}")

    if validation.get("unsupportedClaims"):
        lines.append(
            f"\n⚠️ Unsupported claims (panjang tanpa sitasi): {len(validation['unsupportedClaims'])}"
        )
        for c in validation["unsupportedClaims"][:3]:
            lines.append(f"    - \"{c}...\"")

    if validation.get("citationDensity", 0) > 0:
        lines.append(
            f"\n📈 Citation density: {validation['citationDensity']:.2f} sitasi per kalimat"
        )

    return "\n".join(lines)
