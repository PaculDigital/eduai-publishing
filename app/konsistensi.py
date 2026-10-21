"""
app/konsistensi.py — Consistency Checker (FASE 5)

MENJAGA hasil revisi AI tetap NYAMBUNG dengan Research Brief.
Ini obat dari keluhan utama Bos: "kata tidak nyambung".

SUMBER ASAL (READ-ONLY, jangan diubah):
    penelitian-bot/telegram-bot/agents/consistency-checker.js
    (285 baris · normalize 6-9 · similarity 11-21 · levenshtein 23-40
     checkVariableConsistency 42-79 · checkJudulConsistency 81-113
     checkHipotesisConsistency 115-165 · checkOvConsistency 167-189
     checkConsistency 191-242 · formatConsistencyReport 244-278)

⚠️ ADAPTASI WAJIB (bukan copy-paste buta):
    - penelitian-bot  : Prisma + sectionStates dari DB, PF = problem-formulation
    - EduAi (di sini) : SQLAlchemy, data dari brief_json + section_state
    - Node => Python: optional chaining, regex \\w, Math.min => padanan Python
    - penelitian-bot MENULIS dari nol; EduAi MEREVISI => issue dipakai
      sebagai "catatan konsistensi" untuk AI, bukan untuk memblokir user.

Harga: Rp 0. Semua fungsi di sini MURNI string/angka — TIDAK memanggil AI.
"""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from typing import Any, Dict, Iterable, List, Optional

# ────────────────────────────────────────────────────────────────
# Tingkat masalah (sumber: baris 226-228 & 266)
# ────────────────────────────────────────────────────────────────
LEVEL_ERROR = "error"
LEVEL_WARNING = "warning"
LEVEL_INFO = "info"

_IKON = {LEVEL_ERROR: "🔴", LEVEL_WARNING: "🟡", LEVEL_INFO: "💡"}

# Section yang WAJIB menyebut variabel (sumber: baris 63)
_SECTION_WAJIB_VARIABEL = ("4.1", "4.4", "4.5", "3.1", "2.1", "2.4")

# Section pembanding hipotesis (sumber: baris 124-126)
_SECTION_HIPOTESIS = "2.4"
_SECTION_UJI_HIPOTESIS = "4.4"
_SECTION_KESIMPULAN = "5.1"

# Section definisi operasional (sumber: baris 169)
_SECTION_OV = "3.1"

# Ambang judul mirip-tapi-tak-persis (sumber: baris 95, 99)
_AMBANG_JUDUL_MIRIP = 0.6


# ════════════════════════════════════════════════════════════════
# 1. ALAT DASAR — normalize, similarity, levenshtein
#    (sumber: baris 6-40)
# ════════════════════════════════════════════════════════════════
def normalize(s: Any) -> str:
    """Rapikan teks sebelum dibandingkan.

    JS: s.toString().toLowerCase().replace(/\\s+/g,' ').replace(/[^\\w\\s]/g,'').trim()
    Python: \\w sudah unicode-aware; tanda baca dibuang, spasi dirapikan.
    """
    if s is None:
        return ""
    teks = str(s).lower()
    teks = re.sub(r"\s+", " ", teks)
    teks = re.sub(r"[^\w\s]", "", teks, flags=re.UNICODE)
    return teks.strip()


def similarity(a: Any, b: Any) -> float:
    """Kemiripan Jaccard antar kata (0..1). Sumber: baris 11-21.

    ⚠️ BATAS PEMAKAIAN (audit Bos 16Sep26 — JANGAN SALAH TEMPAT):
    Jaccard mengabaikan URUTAN dan MAKNA. Terbukti:
      • "…KINERJA KARYAWAN…" vs "…KINERJA PEGAWAI…" → Jaccard 0,833 (TINGGI)
        padahal JUDUL WAJIB PERSIS → Jaccard MELOLOSKAN cacat akademik.
      • paragraf yang MAKNANYA sama tapi katanya berbeda → Jaccard 0,455
        (RENDAH) padahal makna terjaga → Jaccard MENUDUH salah.

    ATURAN (kaidah akademik):
      • Judul / rumusan masalah / hipotesis / istilah variabel → pakai
        `sama_persis()` atau `sama_teks_akademik()`. JANGAN pakai Jaccard
        sebagai penentu.
      • Paragraf naskah (yang memang direvisi) → pakai `kata_kunci_akademik()`
        untuk menilai MAKNA.

    Fungsi ini tetap dipertahankan untuk kemiripan KASAR (mis. mengelompokkan
    bagian yang mirip), TAPI BUKAN untuk memutuskan sah/tidak.
    """
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    kata_a = set(na.split(" "))
    kata_b = set(nb.split(" "))
    irisan = len(kata_a & kata_b)
    gabungan = len(kata_a | kata_b)
    return irisan / gabungan if gabungan else 0.0


# Batas panjang untuk levenshtein. Teks naskah bisa ratusan ribu karakter —
# tabel O(n*m) bikin pemanggil MENGGANTUNG (terbukti 16Sep26: 16.000 kar >120s).
# Levenshtein memang hanya untuk membandingkan JUDUL/frasa pendek, jadi
# di atas batas ini cukup pakai rasio SequenceMatcher (O(n) praktis).
_BATAS_LEVENSHTEIN = 3000


def levenshtein(a: Any, b: Any) -> int:
    """Jarak edit dengan batas panjang (mitigasi O(n*m)).

    Sumber: baris 23-40 (JS memakai tabel penuh m+1 x n+1).
    Python: hanya 2 baris (rolling) + BATAS PANJANG. Kalau teks terlalu
    panjang, kembalikan PERKIRAAN dari rasio kecocokan (bukan angka palsu —
    nilainya tetap wajar: 0 = identik, makin beda makin besar).
    """
    na, nb = normalize(a), normalize(b)
    if not na:
        return len(nb)
    if not nb:
        return len(na)
    if len(na) > _BATAS_LEVENSHTEIN or len(nb) > _BATAS_LEVENSHTEIN:
        rasio = SequenceMatcher(None, na, nb).ratio()
        return int(round(len(na) * (1.0 - rasio)))
    if len(na) < len(nb):
        na, nb = nb, na
    baris_lalu = list(range(len(nb) + 1))
    for i, ca in enumerate(na, start=1):
        baris_kini = [i]
        for j, cb in enumerate(nb, start=1):
            biaya = 0 if ca == cb else 1
            baris_kini.append(
                min(
                    baris_lalu[j] + 1,        # hapus
                    baris_kini[j - 1] + 1,    # sisip
                    baris_lalu[j - 1] + biaya,  # ganti
                )
            )
        baris_lalu = baris_kini
    return baris_lalu[-1]


def mirip_teks(a: Any, b: Any, ambang: float = 0.85) -> bool:
    """Teks hampir sama TAPI tidak persis (typo ringan).

    ⚠️ Dipakai HANYA untuk membandingkan FRASA PENDEK (judul, istilah).
    JANGAN dipakai untuk paragraf panjang.
    """
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return False  # persis = bukan "mirip"
    rasio = SequenceMatcher(None, na, nb).ratio()
    return rasio >= ambang


# ════════════════════════════════════════════════════════════════
# 1b. ALAT UKUR AKADEMIK (TAMBAHAN audit Bos 16Sep26)
#
# KAIDAH: tiap elemen punya alat ukurnya sendiri. Memakai alat yang salah
# = laporan palsu (meloloskan yang cacat, atau menuduh yang benar).
#   • WAJIB PERSIS → sama_persis() / sama_teks_akademik()
#   • BOLEH MIRIP  → kata_kunci_akademik() (nilai MAKNA)
# ════════════════════════════════════════════════════════════════

# Ambang MAKNA — arah Bos 16Sep26: "kalau masih semantik tidak masalah,
# semantiknya 80% lebih artinya mirip".
AMBANG_MAKNA = 0.80

# Penanda akademik yang WAJIB dipertahankan saat naskah direvisi.
# Kalau salah satu HILANG setelah revisi, maknanya bergeser → catatan.
_POLA_AKADEMIK = (
    (r"\b\d+(?:[.,]\d+)?\s*%", "angka persen"),
    (r"\b(?:19|20)\d{2}\b", "tahun"),
    (r"\b[bBrR][²2]\b|\b(?:p|sig)\s*[<>=]\s*0[.,]\d+", "statistik"),
    (r"\b[Hh]\d{1,2}\b", "kode hipotesis"),
    (r"\bβ\s*=\s*[-\d.,]+|\bbeta\s*=\s*[-\d.,]+", "koefisien"),
)

# Istilah metodologis yang mengubah MAKNA kalau hilang/bertukar.
_ISTILAH_PENTING = (
    "kuantitatif", "kualitatif", "deduktif", "induktif", "hipotesis",
    "mediasi", "moderasi", "regresi", "korelasi", "signifikan",
    "purposive", "random", "validitas", "reliabilitas", "triangulasi",
    "eksperimen", "survei", "wawancara", "observasi",
)


def sama_persis(teks: Any, acuan: Any) -> bool:
    """Apakah `acuan` muncul PERSIS di dalam `teks` (setelah normalisasi)?

    INI ALAT YANG BENAR untuk judul / rumusan masalah / hipotesis.
    Bukan `similarity()`. Bukti audit 16Sep26: judul "KINERJA KARYAWAN" vs
    "KINERJA PEGAWAI" punya Jaccard 0,833 → dinyatakan "hampir sama" padahal
    itu CACAT AKADEMIK.
    """
    na, nb = normalize(teks), normalize(acuan)
    if not na or not nb:
        return False
    return nb in na


def sama_teks_akademik(a: Any, b: Any, toleransi: float = 0.97) -> bool:
    """Bandingkan dua FRASA yang WAJIB sama, izinkan typo/spasi ringan.

    `toleransi` dinaikkan ke 0,97 (bukan 0,85) SENGAJA: untuk judul, beda satu
    kata penting ("karyawan"→"pegawai") TIDAK boleh dianggap sama. Bukti audit:
    pasangan itu punya rasio 0,9+ sehingga ambang 0,85 MELOLOSKANNYA.
    """
    na, nb = normalize(a), normalize(b)
    if not na or not nb:
        return False
    if na == nb:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= toleransi


def kata_kunci_akademik(teks: Any) -> set:
    """Ambil penanda akademik dari teks (angka/tahun/statistik/hipotesis/istilah).

    Dipakai untuk mengukur MAKNA dua versi naskah. Terbukti (audit 16Sep26):
    dua versi paragraf yang maknanya sama mendapat Jaccard hanya 0,455, tapi
    kata kunci akademiknya 16/17 = 94% sama. Jadi INI alat ukur yang benar
    untuk paragraf.
    """
    t = normalize(teks)
    if not t:
        return set()
    keluar = set()
    for pola, _nama in _POLA_AKADEMIK:
        for m in re.findall(pola, t):
            keluar.add(str(m).replace(" ", ""))
    for ist in _ISTILAH_PENTING:
        if ist in t:
            keluar.add(ist)
    return keluar


def _potongan_mirip_judul(teks: Any, judul: Any,
                          ambang: float = 0.60) -> str:
    """Cari POTONGAN di `teks` yang paling menyerupai `judul`, lalu kembalikan.

    KENAPA FUNGSI INI ADA (temuan audit Bos 16Sep26):
    Membandingkan SELURUH paragraf (mis. 705 karakter) dengan judul (96
    karakter) memakai rasio kemiripan = 0,227 → selalu rendah, sehingga cacat
    judul LOLOS. Yang benar: cari dulu potongan sepanjang judul, baru
    dibandingkan.

    ⚠️ JEBAKAN KINERJA (terukur 16Sep26): percobaan pertama memakai jendela
    bergeser + SequenceMatcher penuh → **142 detik** untuk paragraf 2.105
    karakter. Tidak bisa dipakai produksi (naskah bisa puluhan ribu karakter).
    DIPERBAIKI dengan **pencocokan kata** (O(n)) — jauh lebih cepat dan justru
    lebih tepat untuk judul, karena judul peka pada KATA, bukan huruf.

    ️ AMBANG = 0,60 (BUKAN 0,80) — ini KEPUTUSAN PENTING, jangan dinaikkan
    tanpa alasan. Terukur 16Sep26: "Kualitas Produk" vs "Kualitas Barang"
    (beda 1 kata, judul WAJIB PERSIS) hanya mendapat rasio **0,70**. Bila
    ambang 0,80, kasus cacat itu LOLOS tanpa catatan — persis bahaya yang
    harus dicegah. Ambang ini HANYA untuk MENEMUKAN frasa sejenis; keputusan
    sah/tidak dilakukan oleh `sama_teks_akademik()` (toleransi 0,97).
    """
    nt, nj = normalize(teks), normalize(judul)
    if not nt or not nj:
        return ""
    kata_t = nt.split()
    kata_j = nj.split()
    n_j = len(kata_j)
    if not n_j or not kata_t:
        return ""

    # Kalau teks lebih pendek dari judul → bandingkan langsung (frasa pendek).
    if len(kata_t) < n_j:
        rasio = len(set(kata_t) & set(kata_j)) / max(len(set(kata_t) | set(kata_j)), 1)
        return teks if rasio >= ambang else ""

    set_j = set(kata_j)
    terbaik_rasio, terbaik_idx, terbaik_len = 0.0, 0, n_j
    for n_win in range(max(1, n_j - 3), n_j + 4):        # toleran ±3 kata
        for mulai in range(0, len(kata_t) - n_win + 1):
            jendela = kata_t[mulai:mulai + n_win]
            set_w = set(jendela)
            # rasio kata yang sama (jaccard) — O(n) karena set
            rasio = len(set_w & set_j) / max(len(set_w | set_j), 1)
            if rasio > terbaik_rasio:
                terbaik_rasio, terbaik_idx, terbaik_len = rasio, mulai, n_win

    if terbaik_rasio >= ambang:
        return " ".join(kata_t[terbaik_idx:terbaik_idx + terbaik_len])
    return ""


def kemiripan_makna(a: Any, b: Any) -> float:
    """Ukur kemiripan MAKNA (0..1) lewat penanda akademik bersama.

    Hanya untuk NASKAH/PARAGRAF — bukan untuk judul (judul pakai `sama_persis`).
    """
    ka, kb = kata_kunci_akademik(a), kata_kunci_akademik(b)
    if not ka and not kb:
        return 1.0
    if not ka or not kb:
        return 0.0
    return len(ka & kb) / len(ka | kb)


def makna_terjaga(lama: Any, baru: Any,
                  ambang: float = AMBANG_MAKNA) -> dict:
    """Apakah revisi MENJAGA makna? (arah Bos: 80% lebih = mirip)

    Kembalikan rincian supaya bisa dilaporkan jujur ke user.
    """
    ka, kb = kata_kunci_akademik(lama), kata_kunci_akademik(baru)
    sim = kemiripan_makna(lama, baru)
    hilang = sorted(ka - kb)
    baru_ada = sorted(kb - ka)
    return {
        "kemiripan": round(sim, 3),
        "terjaga": sim >= ambang or not ka,
        "penanda_hilang": hilang,
        "penanda_baru": baru_ada,
    }


# ════════════════════════════════════════════════════════════════
# 2. PEMBACA DATA — adaptasi dari penarikan Prisma (baris 191-211)
# ════════════════════════════════════════════════════════════════
def _ambil(sec: Any, *kunci: str) -> str:
    """Ambil teks section dari dict / objek SQLAlchemy. Sumber: baris 54-55."""
    if sec is None:
        return ""
    for k in kunci:
        nilai = sec.get(k) if isinstance(sec, dict) else getattr(sec, k, None)
        if nilai:
            return nilai if isinstance(nilai, str) else json.dumps(nilai, ensure_ascii=False)
    return ""


def _sid(sec: Any) -> str:
    return (sec.get("section_id") or sec.get("sectionId") or "") if isinstance(sec, dict) else (
        getattr(sec, "section_id", None) or getattr(sec, "sectionId", "") or ""
    )


def _stitle(sec: Any) -> str:
    if isinstance(sec, dict):
        return sec.get("section_title") or sec.get("sectionTitle") or sec.get("title") or ""
    return getattr(sec, "title", "") or ""


def _isi(sec: Any) -> str:
    """Isi teks section. Sumber: `sec.content || sec.text` (baris 55)."""
    return _ambil(sec, "content", "isi_teks", "text")


def _daftar(nilai: Any) -> List[Any]:
    """Selalu balikkan list. Sumber: baris 117-118 (jaga tipe hipotesis)."""
    if nilai is None:
        return []
    if isinstance(nilai, list):
        return nilai
    if isinstance(nilai, str):
        return [nilai] if nilai.strip() else []
    return [nilai]


def _cari_section(section_states: Iterable[Any], section_id: str) -> Optional[Any]:
    """Sumber: `sectionStates.find(s => s.sectionId === '2.4')` (baris 124-126)."""
    for sec in section_states or []:
        if _sid(sec) == section_id:
            return sec
    return None


# ════════════════════════════════════════════════════════════════
# 3. EMPAT PEMERIKSAAN (sumber: baris 42-189)
# ════════════════════════════════════════════════════════════════
def check_variable_consistency(brief: Dict[str, Any], section_states: Iterable[Any]) -> Dict[str, Any]:
    """Semua variabel di Brief WAJIB disebut di bab kunci. Sumber: baris 42-79.

    Kalau variabel hilang dari bab, AI sudah menyimpang dari Brief —
    inilah akar "kata tidak nyambung".

    ⚠️ PERBAIKAN ATAS SUMBER (temuan 16Sep26, uji nyata):
    Sumber hanya memeriksa section ber-ID tetap (4.1/4.4/4.5/3.1/2.1/2.4).
    Pada dokumen yang BELUM punya section itu — misalnya PROPOSAL yang baru
    berisi 1.1–1.9 seperti tesis Bos, atau dokumen dengan penomoran lain —
    pemeriksaan itu LEWAT TOTAL dan sistem melaporkan "konsisten" padahal
    variabelnya tidak ada di mana pun. Itu laporan palsu.

    Perbaikan: variabel diperiksa ke SELURUH bagian dokumen. Kalau sebuah
    bagian (yang panjangnya memadai) sama sekali tidak menyebut salah satu
    variabel, itu catatan. Section kunci tetap diprioritaskan secara pesan.
    """
    issues: List[Dict[str, Any]] = []
    variabel = []
    for v in _daftar((brief or {}).get("variabel")):
        nama = v if isinstance(v, str) else (v.get("nama") or v.get("name") or "" if isinstance(v, dict) else getattr(v, "nama", "") or "")
        if nama:
            variabel.append(str(nama))

    if not variabel:
        return {"issues": [], "summary": "Tidak ada variabel terdefinisi di Research Brief"}

    # Bagian yang panjangnya < ambang ini cenderung cuma judul/transisi,
    # bukan pembahasan — jangan diadili.
    ambang_bahas = 400

    for sec in section_states or []:
        content = _isi(sec)
        if not content or len(content) < ambang_bahas:
            continue
        sid = _sid(sec)
        teks = content.lower()
        # Prioritas pesan: section kunci disebut lengkap, sisanya ringkas
        kunci = sid in _SECTION_WAJIB_VARIABEL
        for v in variabel:
            vl = v.lower().strip()
            if vl in teks:
                continue
            # ⚠️ BUG YANG DIPERBAIKI (audit Bos 16Sep26):
            # Dulu: kalau KATA PERTAMA variabel ada di teks, variabel
            # dianggap "masih ada jejaknya" → catatan TIDAK keluar.
            # TERBUKTI SALAH: Brief minta "motivasi intrinsik" +
            # "motivasi ekstrinsik", naskah cuma menulis "motivasi" → DUA
            # variabel hilang tapi 0 catatan keluar. Akibatnya AI tidak
            # pernah diberi tahu variabelnya tidak dibahas. Laporan PALSU.
            #
            # Sekarang: variabel dianggap "ada" hanya bila FRASA UTUHnya
            # muncul, ATAU minimal 2 kata intinya muncul berdekatan.
            # Untuk variabel satu kata, perilaku lama tetap dipakai.
            kata_v = [k for k in vl.split() if len(k) > 3]
            if len(kata_v) >= 2:
                # semua kata inti harus ada di teks
                if all(re.search(rf"\b{re.escape(k)}\w*", teks) for k in kata_v):
                    continue
            elif len(kata_v) == 1:
                if re.search(rf"\b{re.escape(kata_v[0])}\w*", teks):
                    continue
            issues.append({
                "level": LEVEL_WARNING if kunci else LEVEL_INFO,
                "type": "missing_variable_in_section",
                "section": sid,
                "message": (
                    f'Variabel "{v}" terdefinisi di Research Brief tapi TIDAK disebut '
                    f'di section {sid} ({_stitle(sec)}).'
                ),
                "suggestion": (
                    f'Sebutkan variabel "{v}" di section {sid}, minimal pada kalimat '
                    f'pembuka, supaya alur naskah tetap menyambung dengan bagian lain.'
                ),
                "jenis": "variabel",
            })

    return {"issues": issues, "summary": f"{len(variabel)} variabel dicek"}


def check_judul_consistency(brief: Dict[str, Any], section_states: Iterable[Any]) -> Dict[str, Any]:
    """Judul di Brief WAJIB persis sama bila disebut di naskah. Sumber: baris 81-113.

    ⚠️ ATURAN BOS (§4.17): judul acuan = COVER. Beda judul ID↔EN itu SAH
    (abstrak dua bahasa, disengaja) — fungsi ini hanya menandai kalimat yang
    MIRIP TAPI TIDAK PERSIS, dan itu pun level warning (bukan error),
    supaya tidak "memperbaiki" yang sebenarnya benar.
    """
    issues: List[Dict[str, Any]] = []
    judul = (brief or {}).get("judul")
    if not judul:
        return {"issues": [], "summary": "Judul belum terdefinisi di Research Brief"}

    for sec in section_states or []:
        content = _isi(sec)
        if not content:
            continue
        paragraf_pertama = content.split("\n")[0] if content.split("\n") else ""
        if not paragraf_pertama:
            continue

        #  BUG YANG DIPERBAIKI (audit Bos 16Sep26):
        # Dulu penentu = similarity()/Jaccard ambang 0,6 → TERBUKTI SALAH:
        # mengabaikan URUTAN kata, dan membandingkan SELURUH paragraf (bisa
        # ratusan karakter) dengan judul → rasionya selalu rendah, sehingga
        # cacat judul bisa LOLOS atau justru memunculkan catatan palsu.
        #
        # Sekarang (kaidah akademik — judul WAJIB PERSIS):
        #   1. Cari FRASA JUDUL di dalam paragraf (toleran typo ringan).
        #      → pakai SequenceMatcher, cari potongan sepanjang judul.
        #   2. Kalau ketemu PERSIS            → AMAN, tidak ada catatan.
        #   3. Kalau ketemu HAMPIR persis     → WARNING (beda penulisan).
        #   4. Kalau tidak ada frasa sejenis  → AMAN (section ini memang
        #      tidak menulis judul; jangan ganggu user).
        if sama_persis(content, judul):
            continue
        potongan = _potongan_mirip_judul(paragraf_pertama, judul)
        if potongan and not sama_teks_akademik(potongan, judul):
            issues.append({
                "level": LEVEL_WARNING,
                "type": "judul_hampir_persis",
                "section": _sid(sec),
                "message": (
                    f'Section {_sid(sec)} ({_stitle(sec)}) menulis judul yang '
                    f'HAMPIR persis, tapi ada beda penulisan: "{potongan[:100]}"'
                ),
                "suggestion": (
                    f'Judul akademik WAJIB sama huruf per huruf. Samakan '
                    f'dengan judul di COVER: "{judul}".'
                ),
                "jenis": "judul",
            })

    return {"issues": issues, "summary": f'Judul: "{judul}" dicek (wajib persis)'}


def check_hipotesis_consistency(brief: Dict[str, Any], section_states: Iterable[Any]) -> Dict[str, Any]:
    """Hipotesis di bab kunci WAJIB sinkron. Sumber: baris 115-165.

    Sumber hanya membandingkan string daftar H (persis sama atau tidak).

    ⚠️ PERBAIKAN ATAS SUMBER (temuan 16Sep24, uji nyata): kalau section 2.4/4.4
    TIDAK ADA (proposal baru 1.1–1.9, atau penomoran berbeda), sumber diam saja
    dan melaporkan "konsisten". Di EduAi itu berbahaya: pengguna proposal tidak
    pernah tahu hipotesis di Brief-nya tidak muncul di naskah. Jadi bila section
    pembanding tidak ada, permainan tetap jalan lewat PENCARIAN SELURUH TEKS:
    hipotesis yang tercantum di Brief tapi tidak ada di naskah = catatan.
    """
    issues: List[Dict[str, Any]] = []
    hipotesis = _daftar((brief or {}).get("hipotesis") or (brief or {}).get("hipotesis_penelitian"))

    if not hipotesis:
        return {"issues": [], "summary": "Tidak ada hipotesis di Research Brief"}

    def kode(isi: Any) -> List[str]:
        """Ambil kode hipotesis dari teks, SERAGAMKAN penulisannya.

        ACC Bos 16Sep26: naskah nyata menulis hipotesis dengan banyak gaya —
        "H1", "H 1", "Hipotesis 1", "hipotesis ke-1", "H.1", "Hipotesis 1 dan 2".
        Semua itu HARUS dianggap sama supaya:
          (a) tidak ada catatan palsu hanya karena beda gaya tulis;
          (b) AI bisa memperbaiki yang memang tidak seragam.
        Semua bentuk dinormalkan ke bentuk baku "H<n>".

        ⚠️ JEBAKAN YANG SUDAH TERBUKTI (uji 16Sep26): "Hipotesis 1 dan 2"
        menghasilkan HANYA H1, sebab angka "2" berdiri sendiri tanpa kata
        "Hipotesis". Padahal mahasiswa SANGAT sering menulis begitu. Karena itu
        setelah kata kunci, angka lanjutan yang dipisah "dan"/","/"s.d."/"-"
        juga ikut diambil.
        """
        if not isi:
            return []
        teks = str(isi)

        # 1) "Hipotesis 1", "hipotesis ke-1", + lanjutan "dan 2"/", 3"/"dan ke-2"
        #    ⚠️ JEBAKAN TERBUKTI ke-2 (uji 16Sep26): "Hipotesis ke-1 dan ke-2"
        #    hanya menghasilkan H1 — angka lanjutan "ke-2" tidak ikut karena
        #    setelah "dan" ada kata "ke". Karena itu kata "ke" opsional di
        #    SETIAP angka lanjutan, bukan hanya di angka pertama.
        _lanjut = (r"(?:\s*(?:dan|s\.?d\.?|sampai|hingga|,|&|\-)\s*"
                   r"(?:ke[\s\-]*)?\s*\d{1,2})")
        _pola_hipo = re.compile(
            r"hipotesis\s*(?:ke[\s\-]*)?\s*(\d{1,2})"
            rf"((?:{_lanjut})*)",
            re.IGNORECASE)
        _pola_angka = re.compile(r"(\d{1,2})", re.IGNORECASE)

        def _ganti(m: "re.Match[str]") -> str:
            nomor = [m.group(1)] + _pola_angka.findall(m.group(2) or "")
            return " ".join(f"H{n}" for n in nomor)

        teks = _pola_hipo.sub(_ganti, teks)

        # 2) "H.1", "H-1", "H 1" → "H1"
        teks = re.sub(r"\bH\s*[.\-]?\s*(\d{1,2})\b", r"H\1", teks, flags=re.IGNORECASE)

        # 3) kumpulkan bentuk baku
        kode_mentah = re.findall(r"\bH(\d{1,2})\b", teks, flags=re.IGNORECASE)
        return sorted({f"H{int(n)}" for n in kode_mentah}, key=lambda k: int(k[1:]))

    sec_24 = _cari_section(section_states, _SECTION_HIPOTESIS)
    sec_44 = _cari_section(section_states, _SECTION_UJI_HIPOTESIS)
    sec_51 = _cari_section(section_states, _SECTION_KESIMPULAN)

    h24 = kode(_isi(sec_24))
    h44 = kode(_isi(sec_44))
    h51 = kode(_isi(sec_51))

    if h24 and h44 and h24 != h44:
        issues.append({
            "level": LEVEL_ERROR,
            "type": "hipotesis_mismatch_2.4_4.4",
            "section": _SECTION_HIPOTESIS,
            "message": f"Hipotesis di 2.4 ({', '.join(h24)}) TIDAK COCOK dengan yang diuji di 4.4 ({', '.join(h44)}).",
            "suggestion": "Pastikan hipotesis di 2.4 SAMA dengan yang diuji di 4.4. Update salah satunya agar konsisten.",
            "jenis": "hipotesis",
        })

    if h24 and h51 and h24 != h51:
        issues.append({
            "level": LEVEL_ERROR,
            "type": "hipotesis_mismatch_2.4_5.1",
            "section": _SECTION_KESIMPULAN,
            "message": f"Hipotesis di 2.4 ({', '.join(h24)}) TIDAK COCOK dengan kesimpulan di 5.1 ({', '.join(h51)}).",
            "suggestion": "Kesimpulan di 5.1 harus sesuai dengan hipotesis yang diuji. Update salah satunya.",
            "jenis": "hipotesis",
        })

    # ── Jaring pengaman (adaptasi EduAi): Brief sebagai ACUAN ──
    # ⚠️ BUG NYATA yang ditemukan uji 16Sep26: sumber penelitian-bot HANYA
    # membandingkan 2.4 ↔ 4.4 dan 2.4 ↔ 5.1. Akibatnya bila Brief bilang
    # "H9" tapi naskah cuma punya H1, ketiganya SAMA-SAMA menulis H1 →
    # dianggap "sinkron" dan laporan bilang LULUS. Itu laporan palsu:
    # yang benar hipotesisnya tidak nyambung dengan Research Brief.
    # Perbaikan: setelah antar-section cocok, bandingkan juga dengan Brief.
    kode_di_brief = set(kode(" ".join(str(h) for h in hipotesis)))
    kode_di_naskah: set = set()
    for _sec in (section_states or []):
        kode_di_naskah |= set(kode(_isi(_sec)))

    if kode_di_brief and kode_di_naskah:
        if not (kode_di_brief & kode_di_naskah):
            # Tidak ada SATU pun hipotesis Brief yang muncul di naskah.
            issues.append({
                "level": LEVEL_ERROR,
                "type": "hipotesis_brief_tidak_dipakai",
                "section": "-",
                "message": (
                    f"Hipotesis di naskah ({', '.join(sorted(kode_di_naskah, key=lambda k: int(k[1:])))}"
                    f") SAMA SEKALI TIDAK ADA yang cocok dengan Research Brief "
                    f"({', '.join(sorted(kode_di_brief, key=lambda k: int(k[1:])))})."
                ),
                "suggestion": (
                    "Hipotesis di naskah wajib mengikuti Research Brief. Samakan "
                    "penandanya (H1, H2, …) tanpa mengubah jumlah hipotesisnya."
                ),
                "jenis": "hipotesis",
            })
        else:
            hanya_di_brief = kode_di_brief - kode_di_naskah
            hanya_di_naskah = kode_di_naskah - kode_di_brief
            if hanya_di_brief or hanya_di_naskah:
                bagian = []
                if hanya_di_brief:
                    bagian.append("belum muncul di naskah: "
                                  + ", ".join(sorted(hanya_di_brief, key=lambda k: int(k[1:]))))
                if hanya_di_naskah:
                    bagian.append("ada di naskah tapi tidak di Brief: "
                                  + ", ".join(sorted(hanya_di_naskah, key=lambda k: int(k[1:]))))
                issues.append({
                    "level": LEVEL_WARNING,
                    "type": "hipotesis_tidak_lengkap",
                    "section": "-",
                    "message": "Hipotesis naskah dan Research Brief tidak sepenuhnya sama (" + "; ".join(bagian) + ").",
                    "suggestion": "Samakan daftar hipotesis naskah dengan Research Brief, tanpa menambah atau menghapus hipotesis.",
                    "jenis": "hipotesis",
                })

    return {"issues": issues, "summary": f"{len(hipotesis)} hipotesis dicek"}


def check_ov_consistency(brief: Dict[str, Any], section_states: Iterable[Any]) -> Dict[str, Any]:
    """Pastikan tabel Definisi Operasional benar-benar ada di 3.1. Sumber: baris 167-189."""
    issues: List[Dict[str, Any]] = []
    sec_31 = _cari_section(section_states, _SECTION_OV)
    content = _isi(sec_31)
    if not content:
        return {"issues": [], "summary": "OV belum terdefinisi di 3.1"}

    # Sumber: /X\d+|"[^"]+"|Y\s*\(/g — tanda tabel OV hidup
    cocok = re.findall(r'X\d+|"[^"]+"|Y\s*\(', content)
    if not cocok:
        issues.append({
            "level": LEVEL_INFO,
            "type": "no_ov_detected",
            "section": _SECTION_OV,
            "message": "Definisi Operasional tidak terdeteksi otomatis di section 3.1.",
            "suggestion": "Pastikan tabel Definisi Operasional ada dengan kolom: Variabel, Dimensi, Indikator, Skala Ukur, Skala Pengukuran, Sumber Acuan.",
            "jenis": "ov",
        })

    return {"issues": issues, "summary": f"{len(cocok)} variabel di OV dicek"}


# ════════════════════════════════════════════════════════════════
# 4. PENGUMPUL — check_consistency (sumber: baris 191-242)
# ════════════════════════════════════════════════════════════════
def check_consistency(brief: Optional[Dict[str, Any]], section_states: Optional[Iterable[Any]]) -> Dict[str, Any]:
    """Jalankan 4 pemeriksaan. Rp 0 — murni string, tanpa AI.

    Adaptasi penting: sumber mengembalikan ok:false bila PF belum selesai.
    EduAi TIDAK memblokir — kalau Brief kosong, tetap balikkan hasil kosong
    dengan keterangan (sesuai prinsip §4.17: jangan halangi kerja user).
    """
    # Brief dari DB bisa berbentuk teks JSON (SQLite Text) → parse aman
    if isinstance(brief, str):
        try:
            brief = json.loads(brief)
        except (ValueError, TypeError):
            brief = None
    if not isinstance(brief, dict):
        brief = {}

    states = list(section_states or [])
    semua: List[Dict[str, Any]] = []

    cek_judul = check_judul_consistency(brief, states)
    cek_var = check_variable_consistency(brief, states)
    cek_hipo = check_hipotesis_consistency(brief, states)
    cek_ov = check_ov_consistency(brief, states)

    for hasil in (cek_judul, cek_var, cek_hipo, cek_ov):
        semua.extend(hasil["issues"])

    jumlah = {
        LEVEL_ERROR: sum(1 for i in semua if i["level"] == LEVEL_ERROR),
        LEVEL_WARNING: sum(1 for i in semua if i["level"] == LEVEL_WARNING),
        LEVEL_INFO: sum(1 for i in semua if i["level"] == LEVEL_INFO),
    }

    return {
        "ok": jumlah[LEVEL_ERROR] == 0,
        "issues": semua,
        "summary": {
            "judul": cek_judul["summary"],
            "variabel": cek_var["summary"],
            "hipotesis": cek_hipo["summary"],
            "ov": cek_ov["summary"],
            "counts": jumlah,
        },
    }


# ════════════════════════════════════════════════════════════════
# 5. PELAPOR UNTUK USER (sumber: baris 244-278)
# ════════════════════════════════════════════════════════════════
def format_laporan(result: Optional[Dict[str, Any]], maks_detail: int = 20) -> str:
    """Laporan siap tayang. Sumber: formatConsistencyReport (baris 244-278).

    ⚠️ DISESUAIKAN KE BAHASA EDUAI: DILARANG memunculkan kata terlarang
    ("kuota"/"token AI"/"rupiah"). Ini murni catatan mutu naskah.
    """
    if not result:
        return "⚠️ Pemeriksaan konsistensi gagal dijalankan."

    baris: List[str] = []
    c = (result.get("summary") or {}).get("counts") or {LEVEL_ERROR: 0, LEVEL_WARNING: 0, LEVEL_INFO: 0}

    if result.get("ok") and c.get(LEVEL_ERROR, 0) == 0:
        baris.append("✅ Pemeriksaan Konsistensi: LULUS")
    else:
        judul = "DITEMUKAN MASALAH" if c.get(LEVEL_ERROR, 0) > 0 else "ADA CATATAN"
        baris.append(f"❌ Pemeriksaan Konsistensi: {judul}")

    baris.append(
        f"📊 Temuan: {c.get(LEVEL_ERROR, 0)} masalah, "
        f"{c.get(LEVEL_WARNING, 0)} catatan, {c.get(LEVEL_INFO, 0)} keterangan\n"
    )

    ringkas = result.get("summary") or {}
    for kunci in ("judul", "variabel", "hipotesis", "ov"):
        if ringkas.get(kunci):
            baris.append(f"• {ringkas[kunci]}")

    issues = result.get("issues") or []
    if issues:
        baris.append("\nRincian:\n")
        for iss in issues[:maks_detail]:
            ikon = _IKON.get(iss.get("level"), "📌")
            baris.append(f"{ikon} {iss.get('section') or 'umum'}: {iss.get('message')}")
            if iss.get("suggestion"):
                baris.append(f"   💡 {iss['suggestion']}")
        if len(issues) > maks_detail:
            baris.append(f"\n…dan {len(issues) - maks_detail} temuan lainnya.")

    return "\n".join(baris)


def catatan_untuk_ai(result: Optional[Dict[str, Any]]) -> str:
    """Versi ringkas untuk DISISIPKAN KE PROMPT AI (adaptasi EduAi).

    Bedanya dengan penelitian-bot (yang menampilkan ke user lewat Telegram):
    EduAi memakai hasil ini sebagai PERINGATAN SEBELUM revisi dijalankan,
    supaya AI memperbaiki penyimpangan dalam revisi yang sama — bukan
    menagih user sekali lagi.

    ⚠️ PELAJARAN UJI 16Sep26: pembanding `result.get("issues")` saja MENIPU —
    daftar `issues` bisa KOSONG padahal ringkasan justru melaporkan temuan
    (mis. temuan hanya muncul di summary). Jadi: pakai `issues` kalau ada,
    kalau tidak, jatuh ke ringkasan supaya AI tetap dapat peringatan.
    """
    if not result:
        return ""
    issues = result.get("issues") or []
    ringkas = result.get("summary") or {}
    jumlah = ringkas.get("counts") or {}
    total = sum(v for v in jumlah.values() if isinstance(v, int))
    if not issues and not total:
        return ""
    if not issues:
        # Tidak ada rincian, tapi ringkasan bilang ada temuan → sampaikan
        # ringkasannya supaya AI tetap waspada, bukan diam.
        issues = [{
            "level": LEVEL_WARNING,
            "section": "-",
            "message": "; ".join(
                str(ringkas.get(k)) for k in ("judul", "variabel", "hipotesis", "ov")
                if ringkas.get(k)
            ) or "pemeriksaan konsistensi melaporkan temuan",
        }]
    potong = issues[:10]
    isi = "\n".join(f"- [{i['level']}] {i.get('section')}: {i.get('message')}" for i in potong)
    return (
        "CATATAN KONSISTENSI (JANGAN dijelaskan ke user, pakai untuk menjaga "
        "naskah tetap nyambung):\n"
        f"{isi}\n"
        "CARA MEMPERBAIKI (ACC Bos 16Sep26):\n"
        "- Hipotesis: PERBAIKI penulisan yang tidak seragam di naskah hasilmu. "
        "Bentuk baku = H1, H2, H3. Kalau naskah asli menulis 'Hipotesis 1', "
        "'H 1', atau 'H.1', SERAGAMKAN menjadi H1 — tapi JANGAN mengubah jumlah "
        "atau isi hipotesisnya, dan JANGAN menambah/menghapus hipotesis.\n"
        "- Variabel: pakai nama variabel PERSIS seperti di Research Brief. Kalau "
        "naskah menyebut variasi nama yang berbeda, samakan ke nama Brief.\n"
        "- Judul: tulis judul PERSIS seperti di Research Brief bila kamu menyebutnya.\n"
        "- Jangan menyebut catatan ini ke user."
    )
