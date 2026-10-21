#!/usr/bin/env python3
"""
Pipeline Buku Umum — Ekonomi Digital (Uji Coba 3 Bab)
Chunking per sub-bab: 1 sub-bab = 1 LLM call (800-1200 kata)
4-agen: Architect → Skeptic → Pragmatist → Editor
Rolling summary: 200 kata per sub-bab → context sub-bab berikutnya
"""

import json, os, re, time, sys, logging
log = logging.getLogger(__name__)
import tata_paragraf
from datetime import datetime
from verifikasi_sitasi import search_real_references, format_apa, format_in_text, build_citation_prompt, verify_text_citations

OUT_DIR = "/opt/data/buku_umum_test"
os.makedirs(OUT_DIR, exist_ok=True)
CKPT_FILE = os.path.join(OUT_DIR, "checkpoint.json")
STATE_FILE = os.path.join(OUT_DIR, "state.json")

# ══════════════════════════════════════════════════════════════════════════
#  FOLDER PER-UTAS (ACC Bos 19 Okt 2026 — "OUT_DIR per-utas")
# ══════════════════════════════════════════════════════════════════════════
#  MASALAH: `OUT_DIR`/`VISUAL_DIR`/`CKPT_FILE` dipakai di 20 titik sebagai
#  variabel GLOBAL. Dua bab bersamaan ⇒ menulis ke folder yang SAMA.
#
#  OBAT — JANGAN sentuh 20 titik, cukup 3 FUNGSI di bawah:
#  Modul ini punya `class _DirUtas(str)`. Variabel global di atas DIGANTI
#  jadi objek jenis itu. Setiap kali dipakai (`os.path.join(OUT_DIR, ...)`,
#  `open(CKPT_FILE)`, `os.makedirs(VISUAL_DIR)`), Python memanggil
#  `__fspath__()`/`__str__()` — di situ kita kembalikan folder MILIK UTAS
#  yang sedang bekerja, bukan folder bersama.
#
#  ⇒ Tiap bab dapat foldernya sendiri TANPA mengubah 20 titik pemakaian.
#  ⇒ Nol kunci, nol saling menunggu ⇒ bab BENAR-BENAR bersamaan.
#
#  Kalau utas tidak mendaftar (pemakaian biasa / CLI), jatuh ke folder asal
#  ⇒ perilaku lama TIDAK berubah sama sekali.
_FOLDER_UTAS = {}


def folder_bab(nama):
    """Daftarkan folder kerja untuk UTAS YANG SEDANG BERJALAN."""
    import threading
    _FOLDER_UTAS[threading.get_ident()] = str(nama)
    return nama


def lepas_folder():
    """Lupakan folder utas ini (wajib dipanggil di `finally`)."""
    import threading
    _FOLDER_UTAS.pop(threading.get_ident(), None)


class _DirUtas(str):
    """String folder yang MENYESUAIKAN DIRI dengan utas yang memakainya.

    ⚠️ JEBAKAN 19 Okt (TERBUKTI): `os.path.join(OUT_DIR, "x")` TIDAK memanggil
    `__fspath__` kalau `OUT_DIR` adalah turunan `str` — hasilnya memakai nilai
    string ASLI. Jadi kelas ini HANYA berguna untuk pemakaian yang memanggil
    `str()`/`__fspath__` langsung. Untuk `os.path.join`, WAJIB pakai
    `folder_ini()` (fungsi di bawah) — jangan andalkan kelas ini.
    """

    def __new__(cls, nilai_asli):
        obj = super().__new__(cls, nilai_asli)
        obj._asli = nilai_asli
        obj._jenis = 'dir'
        return obj

    def _nilai(self):
        import threading
        return _FOLDER_UTAS.get(threading.get_ident(), self._asli)

    def __str__(self):
        return self._nilai()

    def __fspath__(self):
        return self._nilai()


class _BerkasUtas(_DirUtas):
    """Sama seperti `_DirUtas`, tapi untuk BERKAS di dalam folder utas."""

    def __new__(cls, nilai_asli, nama_berkas):
        obj = super().__new__(cls, nilai_asli)
        obj._nama_berkas = nama_berkas
        return obj

    def _nilai(self):
        import threading
        folder = _FOLDER_UTAS.get(threading.get_ident())
        if folder:
            return os.path.join(folder, self._nama_berkas)
        return self._asli


def folder_ini(bawaan=None):
    """Folder kerja UTAS INI. Kalau tak terdaftar → `bawaan` (perilaku lama)."""
    import threading
    return _FOLDER_UTAS.get(threading.get_ident(), bawaan)


def visual_ini():
    """Folder visual UTAS INI (dicari saat dipanggil, bukan saat impor)."""
    import threading
    folder = _FOLDER_UTAS.get(threading.get_ident())
    if folder:
        return os.path.join(folder, "visual")
    #  ⚠️ `VISUAL_DIR` baru dibuat di bawah (butuh OUT_DIR) ⇒ cari lewat globals().
    return str(globals().get('VISUAL_DIR', os.path.join(str(OUT_DIR), "visual")))


OUT_DIR = _DirUtas(OUT_DIR)
CKPT_FILE = _BerkasUtas(CKPT_FILE, "checkpoint.json")
STATE_FILE = _BerkasUtas(STATE_FILE, "state.json")

# === ENOWX API ===
#  ⚠️ KUNCI TIDAK DITULIS DI SINI (dipindah 17 Okt 2026).
#  Alasan: kunci tertanam di berkas = bocor ke mana-mana (terbukti tersebar di
#  11 skill + 5 pipeline). Sumber tunggal sekarang: /opt/data/.env (ENOWX_KEY).
def _baca_env(nama='ENOWX_KEY', berkas=('/opt/data/.env',
                                       '/opt/data/services/eduai-publishing/.env')):
    """Ambil kunci dari environment dulu, lalu dari .env. Tanpa kunci = gagal jelas."""
    nilai = os.environ.get(nama)
    if nilai:
        return nilai
    for p in berkas:
        try:
            with open(p, encoding='utf-8') as f:
                for baris in f:
                    baris = baris.strip()
                    if baris.startswith(nama + '='):
                        return baris.split('=', 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    raise RuntimeError(
        f'{nama} tidak ditemukan. Set environment variable atau isi di /opt/data/.env')


#  ══════════════════════════════════════════════════════════════════════════
#  DUA PINTU (putusan Bos 17 Okt 2026) — TEKS lewat 9router, GAMBAR lewat enowx
#  ══════════════════════════════════════════════════════════════════════════
#  Kenapa dipisah, bukan satu pintu:
#    TEKS    → 9router (satu pintu AI Bos). TERUJI: HTTP 200, stream jalan.
#    GAMBAR  → enowx. TERUJI 17 Okt: 9router MENOLAK semua model gambar
#              (`provider does not support image generation`, 3 model dicoba).
#              Jadi enowx DIPERTAHANKAN KHUSUS GAMBAR sampai 9router punya
#              jalur gambar. Begitu ada, hapus enowx dari sini.
#  ⚠️ Kunci TIDAK ditulis di berkas ini — sumber tunggal: .env
ENOWX_KEY = _baca_env("ENOWX_KEY")        # khusus gambar
ROUTER_KEY = _baca_env("EDUAI_ROUTER_KEY")  # khusus teks (kunci 9router)

#  ── SETELAN PRODUKSI (gerbang G3 menolak deploy tanpa ini) ────────────────
#  Jangan hardcode batas token di berkas ini. Ambil dari SATU sumber:
#  `app/config.py` (yang membaca .env). Kalau dijalankan di luar container
#  (skrip uji root), pakai nilai cadangan yang SAMA dengan produksi.
try:  # pragma: no cover
    from app.config import AI_MAX_TOKENS          # noqa: F401
except Exception:                                 # pragma: no cover
    AI_MAX_TOKENS = int(os.getenv('EDUAI_AI_MAX_TOKENS', '32000'))

#  ── `requests` TIDAK ADA DI IMAGE PRODUKSI (terukur 19 Okt 2026) ────────────
#  `requirements.txt` tidak memuat `requests`; aplikasi memakai `httpx`.
#  Dulu berkas ini `import requests` di tingkat atas ⇒ di container gagal
#  dimuat ⇒ `siap()` False ⇒ tombol "Susun sekarang" tidak bisa dipakai.
#  JANGAN tambah dependency baru: sediakan pengganti kecil di atas httpx
#  yang punya bentuk SAMA dengan yang dipakai di bawah (`resp.iter_lines()`,
#  `resp.status_code`, `resp.text`, `.json()`).
try:  # pragma: no cover
    import requests                                # noqa: F401
except ModuleNotFoundError:                        # pragma: no cover
    import httpx as _httpx

    class _Resp:
        """Pembungkus httpx supaya bentuknya mirip `requests.Response`."""

        def __init__(self, r):
            self._r = r
            self.status_code = r.status_code

        @property
        def text(self):
            return self._r.text

        def json(self):
            return self._r.json()

        def iter_lines(self):
            #  httpx memberi bytes per baris; samakan dengan requests.
            for baris in self._r.iter_lines():
                yield baris.encode('utf-8') if isinstance(baris, str) else baris

        def raise_for_status(self):
            self._r.raise_for_status()

    class _RequestsShim:
        """Hanya bagian `requests` yang benar-benar dipakai berkas ini."""

        Response = _Resp

        @staticmethod
        def post(url, headers=None, json=None, stream=False, timeout=None,
                 **kw):
            return _Resp(_httpx.post(url, headers=headers, json=json,
                                     timeout=timeout or 120.0))

        @staticmethod
        def get(url, headers=None, timeout=None, **kw):
            return _Resp(_httpx.get(url, headers=headers,
                                    timeout=timeout or 120.0))

    requests = _RequestsShim()

BASE_URL = "http://172.17.0.1:20128/v1"          # 9router — TEKS
#  ── GAMBAR: InferHub LANGSUNG (putusan Bos 18 Okt 2026) ────────────────────
#  enowx ditinggalkan: `cbc/*` akun KOSONG, `infer/*` provider TOLAK gambar.
#  9router juga tidak bisa: `inferhub/*` rusak, `JEV/nano-banana` kolam bersama.
#  TERUJI 18 Okt: cb/gemini-2.5-flash-image = SATU-SATUNYA model gambar hidup
#  di InferHub (45 penjual) · 6,9–9,2 s · $0,00043/gambar (~Rp 7).
GAMBAR_BASE = "https://api.inferhub.dev/v1"
#  🚨 CACAT TERUKUR 20 Okt 2026 — SALAH PREFIX.
#  Dulu `cb/gemini-2.5-flash-image` = model melalui **CodeBuddy**, dan
#  kredit CodeBuddy HABIS (galat 14018 "Credits exhausted", 429).
#  Padahal saldo InferHub sendiri masih $7,57.
#  TERUJI 20 Okt 2026 langsung ke API (9 kandidat, 1 hidup):
#    ✅ `gemini-2.5-flash-image`  (TANPA `cb/`) → HTTP 200, b64 782 KB
#    ❌ `cb/...`  → 429/14018 kredit habis
#    ❌ gpt-image-1.5, gpt-image-2, flux-schnell, flux-dev,
#       nano-banana-2-lite, seedream-4.0, recraft-v4 → 404 unknown model
#  Jadi prefix `cb/` DILARANG untuk gambar: beda prefix = beda tagihan.
GAMBAR_MODEL = "gemini-2.5-flash-image"
GAMBAR_KEY = _baca_env("INFERHUB_KEY")
#  ⚠️ JANGAN pakai glm-5.2 — model BERPIKIR: max_tokens habis untuk reasoning,
#     jawaban jadi 2 karakter (terukur 18 Okt: content=2 kar, reasoning=1156 kar).
MODEL = "inferhub/cb/glm-5.3"
# Fallback: semua TERUJI menghasilkan 170-200 kata pada max_tokens=3000 (18 Okt)
MODEL_FALLBACK = ["inferhub/cb/glm-5.3", "inferhub/cb/deepseek-v4.1-flash",
                  "inferhub/cb/glm-5.3-flash", "inferhub/cb/kimi-k2.7"]

#  ══════════════════════════════════════════════════════════════════════════
#  AKAR "EMPTY RESPONSE" (terukur 18 Okt 2026) — model GLM BERPIKIR dulu.
#  Kalau max_tokens kecil, jatah habis untuk reasoning → content = 0-2 karakter.
#  Terbukti: glm-5.2 max_tokens=300 → content 2 kar, reasoning 1156 kar.
#  OBAT: setiap tahap WAJIB punya jatah cukup. Skeptic/Pragmatist 800 → 3000.
#  Jangan turunkan angka ini tanpa menguji ulang hasilnya.
#  ══════════════════════════════════════════════════════════════════════════

def _jalankan_bersamaan(pekerjaan, tenggat=300):
    """Jalankan beberapa pekerjaan BERSAMAAN. Return list hasil (urutan tetap).

    KENAPA ADA (ACC Bos 19 Okt 2026 — Lapis 2):
      Per sub-bab, `generate_sub_bab` memanggil 4 AI BERURUTAN:
      Architect → Skeptic → Pragmatist → Editor. Padahal **Skeptic dan
      Pragmatist sama-sama hanya MEMBACA `draft`** — keduanya tidak saling
      butuh dan hasilnya tidak saling memengaruhi. Menjalankannya berurutan
      = membuang waktu ±30% per sub-bab.

      Terukur 19 Okt: 9router melayani 8 permintaan bersamaan hampir sama
      cepat dengan 1 (5,1 dtk vs 9,9 dtk) ⇒ jalur ini NYATA, bukan teori.

    ATURAN (JANGAN diubah tanpa alasan):
      - TIDAK mengubah prompt, TIDAK mengubah urutan logika sesudahnya.
      - Kalau SALAH SATU gagal (None), hasilnya tetap dikembalikan apa
        adanya — pemanggil yang memutuskan (jangan menyembunyikan kegagalan).
      - Maks 2 utas (cukup untuk Skeptic+Pragmatist). Lebih dari itu =
        risiko kuota/tabrakan tanpa manfaat terukur.
    """
    from concurrent.futures import ThreadPoolExecutor

    if not pekerjaan:
        return []
    if len(pekerjaan) == 1:
        return [pekerjaan[0]()]

    hasil = [None] * len(pekerjaan)
    with ThreadPoolExecutor(max_workers=min(2, len(pekerjaan))) as ex:
        futs = [ex.submit(fn) for fn in pekerjaan]
        for i, f in enumerate(futs):
            try:
                hasil[i] = f.result(timeout=tenggat)
            except Exception as e:                                # noqa: BLE001
                print(f'       [PARALEL] pekerjaan ke-{i} gagal: {type(e).__name__}: {e}')
                hasil[i] = None
    return hasil


def call_llm(prompt, max_tokens=3000, timeout=120, retries=5):
    """Call LLM dengan retry 5x, exponential backoff, dan model fallback.
    Returns: str (response) atau None kalau semua model gagal total."""
    for model in MODEL_FALLBACK:
        for attempt in range(retries):
            try:
                resp = requests.post(f"{BASE_URL}/chat/completions",
                    headers={"Content-Type": "application/json",
                             "Authorization": f"Bearer {ROUTER_KEY}"},
                    json={"model": model, "stream": True,
                          "messages": [{"role": "user", "content": prompt}],
                          #  ⚠️ WAJIB False: tanpa ini model reasoning bisa
                          #  "berpikir" panjang ⇒ lambat + boros token.
                          #  Setelan produksi (gerbang G1/G2 menolak deploy).
                          "enable_thinking": False,
                          #  Batas token WAJIB ikut setelan produksi — dulu
                          #  hardcode 3000/4000 di sini, jauh di bawah 32.000
                          #  yang sudah disetujui Bos (16 Sep 2026).
                          "max_tokens": AI_MAX_TOKENS},
                    stream=True, timeout=timeout)
                full = ""
                for line in resp.iter_lines():
                    if line:
                        line = line.decode("utf-8", "ignore")
                        if line.startswith("data: "):
                            data = line[6:]
                            if data.strip() == "[DONE]": break
                            try:
                                chunk = json.loads(data)
                                #  ⚠️ JANGAN pakai chunk.get("choices",[{}])[0] —
                                #  stream 9router mengirim chunk `choices: []` di akhir
                                #  (berisi usage) → IndexError → ditelan except →
                                #  tampak "empty response" padahal cuma crash parsing.
                                #  Terukur 18 Okt 2026: content 1473 kar hilang karena ini.
                                _chs = chunk.get("choices") or []
                                if not _chs: continue
                                delta = _chs[0].get("delta") or {}
                                if delta.get("content"): full += delta["content"]
                            except Exception: continue
                if full.strip():
                    if model != MODEL:
                        print(f"       [fallback] Using {model} instead of {MODEL}")
                    return full
                print(f"       [retry {attempt+1}/{retries}] empty response from {model}...")
                time.sleep(3 * (2 ** attempt))
            except requests.exceptions.Timeout:
                print(f"       [retry {attempt+1}/{retries}] timeout from {model}...")
                time.sleep(3 * (2 ** attempt))
            except Exception as e:
                err_msg = str(e)
                if "no usable account" in err_msg or "insufficient" in err_msg:
                    print(f"       [model-switch] {model} → no usable account, trying next model...")
                    break
                print(f"       [retry {attempt+1}/{retries}] {type(e).__name__}: {err_msg[:80]}")
                time.sleep(3 * (2 ** attempt))
    print(f"       [FATAL] All models exhausted. Returning None.")
    return None

# === MASTER OUTLINE ===
MASTER_OUTLINE_SEMENTARA = """
[MASTER OUTLINE — JANGKAR]
Buku: Ekonomi Digital — Transformasi Bisnis di Era Teknologi
Penulis: Syahrul Alim, S.TP., M.M., DBA
Tone: DITENTUKAN OLEH JENIS BUKU (lihat bagian TONE di prompt — jangan pakai tone lain)

Bab 1: Revolusi Digital dan Lanskap Ekonomi Baru
  1.1 Dari Ekonomi Tradisional ke Digital: Sebuah Perjalanan
    → key points: definisi ekonomi digital, perbedaan ekonomi tradisional vs digital, revolusi industri 4.0
  1.2 Pilar Ekonomi Digital: Platform, Data, dan Konektivitas
    → key points: platform economy, data sebagai aset, konektivitas internet/mobile
  1.3 Aktor Utama: Startup, Tech Giant, dan Pemerintah
    → key points: peran startup, dominasi tech giant (GAFAM), regulasi pemerintah
  1.4 Tantangan dan Peluang Ekonomi Digital di Indonesia
    → key points: roadmap digital nasional, gap infrastruktur, demografi bonus

Bab 2: Model Bisnis Digital dan Strategi Persaingan
  2.1 Model Bisnis Berbasis Platform: Network Effect dan Skalabilitas
    → key points: network effect, two-sided market, skalabilitas digital
  2.2 Freemium, Subscription, dan Ekonomi Langganan
    → key points: model freemium, SaaS, subscription economy, recurring revenue
  2.3 Disrupsi dan Inovasi: Bagaimana Digital Mengubah Industri Tradisional
    → key points: disrupsi (Uber, Netflix, Tokopedia), creative destruction Schumpeter
  2.4 Strategi Kompetitif di Ekonomi Digital
    → key points: lock-in effect, data moat, first-mover advantage, Porter dalam konteks digital

Bab 3: Ekosistem Pembayaran Digital dan Masa Depan
  3.1 Evolusi Pembayaran: Tunai ke Digital
    → key points: cashless society, e-wallet, QRIS, open banking
  3.2 Fintech dan Demokratisasi Layanan Keuangan
    → key points: fintech lending, P2P, robo-advisor, financial inclusion
  3.3 KRIPTO, CBDC, dan Tantangan Regulasi
    → key points: cryptocurrency, blockchain, CBDC (Rupiah digital), regulasi BI
  3.4 Masa Depan Ekonomi Digital: AI, IoT, dan Web3
    → key points: AI dalam ekonomi, IoT, Web3, metaverse, sustainability
"""

# === PROMPTS ===

def architect_prompt(bab_num, bab_title, sub_num, sub_title, key_points, rolling_summary, is_intro=False, is_closing=False, refs=None, jenis="umum", outline=None):
    """Prompt penulis. `jenis` menentukan TONE (Bos 18 Okt 2026).

    ⚠️ TONE TIDAK BOLEH ditulis langsung di sini — ambil dari tone_menulis.py.
    Buku anak dengan tone buku bisnis = lebih aneh daripada tanpa pilihan.

    ⚠️ `outline` WAJIB berisi outline buku yang SEDANG dikerjakan. Kalau tidak
    diisi, dipakai MASTER_OUTLINE_SEMENTARA (buku Ekonomi Digital) — itu HANYA
    jangkar sementara. TERUKUR 18 Okt 2026: memakai outline sementara untuk
    topik lain memasukkan 11x kata "ekonomi" + 17x "digital" ke prompt topik
    "Siklus Hujan" ⇒ LLM menulis ekonomi padahal topiknya hujan.
    """
    import tone_menulis as TM
    _t = TM.tone(jenis)
    MASTER_OUTLINE = outline or MASTER_OUTLINE_SEMENTARA
    # Build verified references section
    refs_section = ""
    if refs:
        refs_lines = ["\nREFERENSI TERVERIFIKASI (WAJIB gunakan, HANYA dari list ini):"]
        for i, ref in enumerate(refs, 1):
            refs_lines.append(f"{i}. {format_apa(ref)}")
            refs_lines.append(f"   Sitasi: {format_in_text(ref)}")
        refs_lines.append("DILARANG mengarang sitasi baru.")
        refs_lines.append("PERATURAN SITASI KETAT — PELANGGARAN = GAGAL TOTAL:")
        refs_lines.append("  - HANYA gunakan sitasi yang ADA di daftar referensi di atas")
        refs_lines.append("  - DILARANG menulis sitasi di luar daftar: (Nama, Tahun) yang tidak ada di list = HALLUSINASI")
        refs_lines.append("  - Jika tidak ada referensi yang cocok, TIDAK perlu sitasi di bagian itu")
        refs_lines.append("  - Verifikasi sebelum menulis: cek apakah (Nama, Tahun) ada di daftar referensi")
        refs_section = "\n".join(refs_lines)
    
    if is_intro:
        return f"""[MASTER OUTLINE]
{MASTER_OUTLINE}

[RINGKASAN BAB SEBELUMNYA]
{rolling_summary or "Ini bab pertama."}

Kamu adalah Architect (penulis buku {jenis}). Tulis INTRO BAB {bab_num}: "{bab_title}".

TONE: {_t['tone']}
SAPAAAN WAJIB: sapa pembaca dengan "{_t['sapaan']}" — pakai kata "{_t['sapaan']}" untuk menyapa, dan DILARANG memakai sapaan lain ("Anda"/"kamu"/"siswa") di luar itu.

ATURAN:
- Hook KUAT: {_t['hook']}
- Paragraf {_t['paragraf']}
- Bahasa Indonesia EYD, 0 markdown (tidak ada * _ `)
- {_t['sitasi']}
- Cross-bab: "Pada bab sebelumnya..." jika bab > 1
- Transisi: maksimal 2 frasa transisi
{_t['personal']}
{_t['larangan']}
- {_t['intro_kata']}

Tulis INTRO BAB {bab_num} sekarang. Output: teks langsung."""

    if is_closing:
        return f"""[MASTER OUTLINE]
{MASTER_OUTLINE}

[RINGKASAN BAB INI]
{rolling_summary}

Kamu adalah Architect. Tulis PENUTUP BAB {bab_num}: "{bab_title}".

TONE: {_t['tone']}
SAPAAAN WAJIB: sapa pembaca dengan "{_t['sapaan']}" — pakai kata "{_t['sapaan']}" untuk menyapa, dan DILARANG memakai sapaan lain ("Anda"/"kamu"/"siswa") di luar itu.
Penutup bab yang mengikat ide + transisi ke bab berikutnya.

ATURAN:
- {_t['penutup_kata']}, 2-3 paragraf naratif
- JANGAN buat section "Ringkasan" formal — tulis paragraf penutup yang natural
- Transisi: "Bab selanjutnya akan membahas..." (natural, tidak dipaksakan)
- 0 markdown, EYD
- {_t['sitasi']}
{_t['personal']}
{_t['larangan']}

Tulis PENUTUP BAB {bab_num} sekarang. Output: teks langsung."""

    return f"""[MASTER OUTLINE]
{MASTER_OUTLINE}

[RINGKASAN SUB-BAB SEBELUMNYA]
{rolling_summary or "Ini sub-bab pertama."}

Kamu adalah Architect (penulis buku {jenis}). Tulis SUB-BAB {sub_num}: "{sub_title}" dari BAB {bab_num}: "{bab_title}".

Key points yang WAJIB dibahas:
{key_points}

TONE: {_t['tone']}
SAPAAAN WAJIB: sapa pembaca dengan "{_t['sapaan']}" — pakai kata "{_t['sapaan']}" untuk menyapa, dan DILARANG memakai sapaan lain ("Anda"/"kamu"/"siswa") di luar itu.

{refs_section}

ATURAN:
- Paragraf {_t['paragraf']} PADAT
- BENTUK WAJIB: SATU PARAGRAF = SATU BARIS. Pisahkan tiap paragraf dengan
  SATU BARIS KOSONG. JANGAN menulis seluruh sub-bab jadi satu baris panjang.
- Judul sub-bab TIDAK perlu ditulis (sudah ditangani perakit).
- Buka sub-bab dengan {_t['hook']}
- {_t['sitasi']}
- 0 markdown (tidak ada * _ `)
- EYD
{_t['personal']}
- Transisi: maksimal 2 frasa per sub-bab
- Cross-bab: rujuk bab/sub-bab sebelumnya jika relevan
{_t['larangan']}
{_t['istilah']}
- [TABEL {sub_num}: Judul - kolom1, kolom2, kolom3] jika relevan.
  WAJIB: data tabel ditulis dalam KURUNG KURAWAL yang SAMA, dipisah "|".
  BENTUK WAJIB (perhatikan: SEMUA di dalam kurung siku!):
  [TABEL 1.1: Judul Tabel - Kolom A, Kolom B, Kolom C | Baris1: x, y, z | Baris2: x, y, z | Baris3: x, y, z]
  Minimal 3 baris data. Isi tabel HARUS tentang topik sub-bab ini —
  JANGAN pakai contoh dari buku lain. Contoh bentuk untuk sub-bab tentang
  pengamatan cuaca:
  [TABEL 1.1: Cuaca Pagi dan Sore - Waktu, Suhu, Kelembapan | Baris1: Pagi, Sejuk, Tinggi | Baris2: Siang, Panas, Rendah | Baris3: Sore, Hangat, Sedang]
  JANGAN cuma header tanpa data baris. JANGAN menaruh "Baris1" di luar
  kurung siku.
- [DIAGRAM {sub_num}: Judul - deskripsi singkat visual] jika relevan

Target: 800-1200 kata. Output: teks langsung. JANGAN POTONG sebelum selesai."""

def skeptic_prompt(sub_title, draft):
    return f"""Kamu Skeptic. KRITIK SUB-BAB "{sub_title}":
{draft[:3000]}
Kritik: gap konten, inkonsistensi, panjang paragraf (<60 atau >100 kata), transisi berlebihan, hook lemah, tone terlalu akademik/kaku, sitasi kurang. Max 300 kata. JANGAN rewrite."""

def pragmatist_prompt(draft, kritik):
    return f"""Kamu Pragmatist. SARAN KONKRET:
DRAFT: {draft[:2000]}
KRITIK: {kritik}
Saran: paragraf perlu dipisah/digabung, hook diperkuat, konten ditambah/dihapus, tone diperbaiki. Max 300 kata. JANGAN rewrite."""

def editor_prompt(sub_title, draft, kritik, saran, jenis="umum"):
    """Prompt Editor. `jenis` WAJIB — kalau tidak, aturan buku dewasa bocor ke anak.

    ⚠️ TERUKUR 18 Okt 2026: tanpa `jenis`, editor menulis aturan
       "Personal >= 20% (Anda, kita, pembaca)" dan "0 pertanyaan" untuk buku
       ANAK ⇒ hasilnya 4x "Anda" padahal sapaan buku anak "kamu", dan tidak
       ada pertanyaan padahal buku anak butuh pertanyaan.
    """
    import tone_menulis as TM
    _t = TM.tone(jenis)
    #  ┌─ 20 Okt 2026 — AKAR, BUKAN TAMBALAN ────────────────────────────────
    #  🔴 `anak = jenis == "anak"` ⇒ HANYA dua cabang. `pendidikan` jatuh ke
    #     cabang BUKU DEWASA dan menerima "Personal >= 20% (Anda, kita,
    #     pembaca)" + "0 pertanyaan". TERUKUR: buku pendidikan anak 3 bab →
    #     bab 1 memuat 14× "Anda", bab 2 & 3 nol (model kadang menuruti
    #     `personal` dari tone, kadang menuruti editor — tidak konsisten).
    #  YANG BENAR: sapaan diambil dari SATU sumber (`_t['sapaan']`), dan
    #     larangan sapaan lain SELALU ditulis — tidak bergantung jenis.
    #  └─────────────────────────────────────────────────────────────────────
    sapaan = _t['sapaan']
    anak = jenis == 'anak'
    bukan_dewasa = sapaan != 'Anda'

    #  Aturan yang BERGANTI mengikuti jenis buku.
    if bukan_dewasa:
        lain = '"Anda", "pembaca", atau "para pembaca"' if anak else '"Anda"'
        aturan_personal = (
            f'4. Sapaan WAJIB "{sapaan}"/"kita". DILARANG memakai {lain} — '
            f'buku ini menyapa "{sapaan}".')
    else:
        aturan_personal = f'4. Personal >= 20% ({sapaan}, kita, pembaca)'

    if anak:
        aturan_tanya = (
            '5. Pertanyaan PEMBUKA DIIZINKAN (maksimal 2 per sub-bab) — '
            'buku anak butuh mengajak anak berpikir. Pertanyaan retoris di '
            'tengah narasi tetap DILARANG.')
        aturan_paragraf = '1. Paragraf 30-60 kata, 2-4 kalimat. Kalimat maksimal 12 kata.'
    elif bukan_dewasa:
        #  Buku pendidikan: memandu berpikir, jadi pertanyaan pemandu WAJAR.
        aturan_tanya = (
            '5. Pertanyaan pemandu DIIZINKAN (maksimal 2 per sub-bab) untuk '
            'mengajak siswa mengamati. Pertanyaan retoris berderet tetap DILARANG.')
        aturan_paragraf = '1. Paragraf 40-70 kata, 3-4 kalimat.'
    else:
        aturan_tanya = '5. 0 pertanyaan di body narasi'
        aturan_paragraf = '1. Paragraf 60-100 kata, 3-5 kalimat. <50 kata = GAGAL'

    return f"""Kamu Editor. Tulis SUB-BAB "{sub_title}" FINAL:
DRAFT: {draft}
KRITIK: {kritik}
SARAN: {saran}

ATURAN FINAL (WAJIB SEMUA):
{aturan_paragraf}
2. Hook: cerita/kasus di awal, BUKAN teori
3. Transisi: maksimal 2 frasa per sub-bab
{aturan_personal}
{aturan_tanya}
6. Sitasi APA 7: WAJIB 2+ — KURANG dari 2 = GAGAL
6a. ANTI-HALLUSINASI SITASI — WAJIB: HANYA gunakan sitasi dari daftar referensi yang diberikan. DILARANG MENULIS SITASI yang tidak ada di daftar referensi. Setiap (Nama, Tahun) di teks WAJIB match dengan entri di daftar referensi. Sitasi palsu = HALLUSINASI = GAGAL TOTAL. Jika ragu, HAPUS sitasi tersebut — lebih baik kurang daripada mengarang.
7. DILARANG KERAS MENGURANGI NARASI. Jika draft 800 kata, output WAJIB minimal 800 kata. Jika draft 1000 kata, output WAJIB minimal 1000 kata. Mengurangi narasi = GAGAL TOTAL. JANGAN ringkas, JANGAN potong, JANGAN hapus paragraf.
8. Tone: {_t['tone']}
8a. SAPAAN: sapa pembaca dengan "{sapaan}" — pakai kata "{sapaan}" untuk menyapa. DILARANG memakai sapaan lain.
9. 0 markdown (tidak ada * _ `). EYD.
10. Pertahankan [TABEL/DIAGRAM] markers
11. DILARANG: "Penting untuk dicatat", "Secara komprehensif", "Di era digital ini"
Output: teks langsung. JANGAN POTONG sebelum selesai."""

def summarize_prompt(text):
    """Ringkasan bab untuk DUA keperluan: konteks bab berikutnya + bahan brief
    ilustrasi.

    ⚠️ JANGAN balik ke bentuk lama (18 Okt 2026). Prompt lama meminta "Contoh/
    kasus yang disebut" sebagai DAFTAR → hasilnya tumpukan contoh (Airbnb,
    Netflix, Tokopedia) tanpa penanda mana yang INTI. Akibat terukur di bab 2
    "Model Bisnis Digital": brief ilustrasinya jatuh ke adegan KURIR OJOL yang
    bisa dipasang di bab mana pun, dan pemeriksa "khas" pun jadi longgar karena
    ringkasannya sendiri tidak menyatakan apa yang khas. Bab 3 lolos justru
    karena ringkasannya menyebut SATU tokoh kuat (Ibu Ratna).
    ⇒ Ringkasan WAJIB menyebut 1 TOKOH/KASUS UTAMA dan 1 KONSEP INTI.
    """
    return f"""Buat ringkasan 200 kata dari teks bab berikut. Ringkasan dipakai
untuk dua hal: (a) bahan bab berikutnya, (b) bahan ilustrasi bab ini.

WAJIB dimulai dengan tiga baris ini, lalu paragraf ringkasan:
TOKOH UTAMA: satu tokoh/kasus/perusahaan yang paling banyak dibahas di bab ini
  (sebut namanya + apa yang dilakukannya). Kalau bab ini murni konsep tanpa
  tokoh, tulis konsep paling konkret yang dibahas, bukan nama orang.
KONSEP INTI: satu gagasan utama bab ini dalam satu kalimat.
KHAS BAB INI: satu hal yang HANYA ada di bab ini dan tidak ada di bab lain
  buku ini (tokoh, kasus, angka, atau peristiwa tertentu).

Lalu paragraf ringkasan 150 kata yang menjelaskan: konsep inti tadi,
tokoh/kasus utama tadi, istilah kunci, dan nada penulisan.

ATURAN: jangan menumpuk daftar contoh. Contoh lain boleh disebut maksimal
SATU, dan hanya sebagai pendukung tokoh/kasus utama.

Teks:
{text[:3000]}

Output: 3 baris wajib di atas + paragraf ringkasan. Teks langsung."""

# === POST-PROCESSING ===

def strip_markdown(text):
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text

def fix_narrative_citations(text):
    skip = {'Pada', 'Sejak', 'Menurut', 'Berdasarkan', 'Teori', 'Konsep', 'Model', 'Kerangka', 'Bab', 'Studi', 'Riset', 'Penelitian', 'Dalam', 'Sebuah'}
    def replace(m):
        word = m.group(1)
        if word in skip: return m.group(0)
        return f"({m.group(1)}, {m.group(2)})"
    text = re.sub(r'\b([A-Z][a-z]+)\s*\((\d{4})\)', replace, text)
    return text

def normalize_headings(text):
    lines = text.split('\n')
    fixed = []
    for line in lines:
        s = line.strip()
        if re.match(r'^BAB\s+\d+', s, re.IGNORECASE) and not s.startswith('#'):
            fixed.append(f"## {s}")
        elif re.match(r'^\d+\.\d+\s', s) and not s.startswith('#'):
            fixed.append(f"### {s}")
        else:
            fixed.append(line)
    return '\n'.join(fixed)

def merge_short_paragraphs(text, ambang_kata=None, jenis="umum"):
    """Gabung paragraf yang KEPENDEKAN — dengan ambang yang ikut setelan tone.

    🚨 BUG TERUKUR 20 Okt 2026 (AKAR "satu baris = 8.251 karakter"):
       ambang ditulis MATI `wc < 50` dan `>= 60`, padahal setelan tone buku
       anak (`tone_menulis.py:43`) meminta **25-40 kata per paragraf**.
       ⇒ SETIAP paragraf buku anak dianggap "pendek" lalu DIGABUNG sampai
       ≥60 kata. Terukur: bab 1 buku 6.196 kata menjadi **SATU baris 8.251
       karakter** (bukan paragraf). Akibat berantai: Jev hanya melihat 14
       "blok" raksasa, dan perakit tak bisa mengatur inden per paragraf.

    OBAT (bukan tambalan): ambang diambil DARI setelan tone, dan penggabungan
    HANYA terjadi kalau hasilnya masih di bawah batas atas tone. Paragraf
    yang sudah sesuai setelan TIDAK disentuh.
    """
    #  Ambang dari setelan tone (satu sumber), bukan angka mati.
    if ambang_kata is None:
        ambang_kata = _ambang_paragraf_min(jenis)
    batas_atas = max(ambang_kata * 2, 60)

    lines = text.split('\n')
    merged = []
    buffer = ""

    def _siram(akhir=False):
        """Keluarkan isi buffer ke hasil. `akhir` = paksa keluar walau pendek."""
        nonlocal buffer
        if buffer:
            merged.append(buffer)
            buffer = ""
        if akhir:
            merged.append("")

    for line in lines:
        s = line.strip()
        if not s:
            #  🚨 BUG TERUKUR 20 Okt 2026: dulu baris kosong LANGSUNG
            #  mengeluarkan buffer, sehingga paragraf pendek TIDAK PERNAH
            #  bisa digabung (buffer direset tiap baris kosong) ⇒ fungsi
            #  penggabung praktis MATI. Sekarang buffer DITAHAN melewati
            #  baris kosong, baru dikeluarkan saat sudah memenuhi ambang.
            continue
        if s.startswith('#') or s.startswith('[') or s.startswith('-') or s.startswith('|'):
            _siram()
            merged.append(s)
            continue
        wc = len(s.split())
        #  Sudah memenuhi ambang tone ⇒ JANGAN digabung. Ini inti perbaikan.
        if wc >= ambang_kata:
            _siram()
            merged.append(s)
        else:
            buffer = (buffer + " " + s).strip() if buffer else s
            if len(buffer.split()) >= ambang_kata:
                _siram()
    _siram()
    #  Rapikan: buang baris kosong berlebih di ujung.
    while merged and not merged[-1].strip():
        merged.pop()
    return '\n\n'.join(m for m in merged if m.strip())


def _ambang_paragraf_min(jenis=None):
    """Ambil batas BAWAH jumlah kata paragraf dari setelan tone.

    `tone_menulis` menyimpan paragraf sebagai teks, mis. "25-40 kata,
    2-3 kalimat pendek" ⇒ ambil angka PERTAMA (25). Kalau tak terbaca,
    pakai 40 (tengah-tengah buku umum) — JANGAN 50 seperti bug lama.
    """
    try:
        import tone_menulis
        t = tone_menulis.tone(jenis or 'umum')
        m = re.search(r'(\d+)\s*(?:-|–|sampai)?\s*\d*\s*kata', t.get('paragraf', ''))
        if m:
            return int(m.group(1))
    except Exception as e:                      # noqa: BLE001
        log.warning('[pipeline] ambang paragraf tak terbaca (%s) — pakai 40', e)
    return 40


def pecah_paragraf_panjang(text, ambang_kata=None, jenis="umum"):
    """PECAH paragraf kepanjangan jadi beberapa paragraf wajar.

    🚨 AKAR TERUKUR 20 Okt 2026: `merge_short_paragraphs` hanya MENGGABUNG,
    tak pernah MEMECAH. Terukur pada buku baru dari awal: AI menulis satu
    paragraf **945 kata / 6.565 karakter** untuk satu sub-bab, dan TIDAK ADA
    satu pun fungsi di jalur penulisan yang memecahnya. Akibatnya:
      · naskah tersimpan sebagai 9 "baris" raksasa, bukan paragraf
      · Jev hanya melihat blok raksasa
      · perakit tak bisa mengatur inden per paragraf
      · aturan SOT 2.7 (maks 7 kalimat / 200 kata) DILANGGAR SENYAP

    Obat (bukan tambalan): pakai `tata_paragraf.pecah_paragraf()` yang SUDAH
    ADA (dipakai perakit) — jangan tulis pemecah baru. Dipanggil di jalur
    PENULIS supaya naskah yang tersimpan sudah berparagraf wajar.
    """
    if ambang_kata is None:
        ambang_kata = _ambang_paragraf_min(jenis)

    hasil = []
    #  Toleransi 2× tone: tone = TARGET penulis, 2× = BATAS pecah.
    #  Pecah tepat di angka tone akan memotong paragraf yang sebenarnya sah.
    boleh_kata = max(ambang_kata * 2, 40)
    #  🚨 CACAT TERUKUR 20 Okt 2026: AI menulis JUDUL DUA KALI —
    #  `### 1.1 Matahari, Suhu, dan Bayangan…` lalu baris berikutnya
    #  `Matahari, Suhu, dan Bayangan…` (polos, tanpa ###). Perakit menulis
    #  keduanya sebagai heading ⇒ judul sub-bab muncul DOBEL di .docx.
    #  ⚠️ JEBAKAN: heading berisi NOMOR ("1.1 Matahari…"), baris ulangnya
    #  TIDAK ("Matahari…"). Perbandingan pertama GAGAL karena nomor ikut
    #  dibandingkan ⇒ judul dobel lolos. Nomor WAJIB dibuang dulu.
    def _kunci_judul(t):
        t = re.sub(r'^#+\s*', '', t).strip()
        t = re.sub(r'^\d+(?:\.\d+)*[.)]?\s*', '', t)      # buang "1.1 " / "2. "
        t = re.sub(r'^BAB\s+\d+[.:]?\s*', '', t, flags=re.I)  # buang "BAB 1. "
        return t.lower().strip().rstrip('.:')

    judul_sebelum = ''
    for baris in text.split('\n'):
        s = baris.strip()
        #  Catat heading terakhir (## / ###).
        if s.startswith('#'):
            judul_sebelum = _kunci_judul(s)
            hasil.append(baris)
            continue
        #  Baris polos yang mengulang heading sebelumnya ⇒ BUANG.
        if s and judul_sebelum and _kunci_judul(s) == judul_sebelum:
            log.info('[pipeline] judul dobel dibuang: %s', s[:60])
            continue
        #  Baris isi memutus rantai judul — jangan sampai paragraf yang
        #  kebetulan sama teksnya dengan judul 20 baris lalu ikut dibuang.
        if s:
            judul_sebelum = ''
        s = baris.strip()
        #  Judul/penanda/tabel JANGAN dipecah — hanya paragraf isi.
        if (not s or s.startswith('#') or s.startswith('[')
                or s.startswith('-') or s.startswith('|')):
            hasil.append(baris)
            continue
        if len(s.split()) <= ambang_kata:
            hasil.append(s)
            continue
        #  Paragraf panjang ⇒ pecah pakai modul tata_paragraf (SUDAH ADA).
        #  ⚠️ TERUKUR 20 Okt 2026 (2 kali gagal menetapkan ambang):
        #  ① `maks_kata=200` bawaan = batas MUTU, bukan target tone ⇒ buku
        #     anak tetap keluar 60-94 kata;
        #  ② `maks_kata=50` juga TIDAK cukup — karena pemecah menghitung
        #     "kalimat BERIKUTNYA akan lewat" (kata_kini + n > maks_kata),
        #     dan satu kalimat buku anak ±9 kata ⇒ praktis 4-5 kalimat.
        #  Yang mengikat sebenarnya BATAS KALIMAT. Tone buku anak (25-40
        #  kata @ ±9 kata/kalimat) = 3-4 kalimat. Jadi pakai batas kalimat
        #  dari tone, DAN batas kata 2× tone sebagai jaring kedua.
        kal_per_para = max(3, round(boleh_kata / 9))
        batas_kalimat = min(tata_paragraf.PARA_MAKS_KALIMAT, kal_per_para)
        potong = tata_paragraf.pecah_paragraf(
            s, maks_kalimat=batas_kalimat, maks_kata=boleh_kata)
        for p in potong:
            hasil.append(p)
        log.info('[pipeline] paragraf %s kata dipecah jadi %s bagian '
                 '(batas %s kalimat / %s kata)',
                 len(s.split()), len(potong), batas_kalimat, boleh_kata)
    return '\n\n'.join(b.strip() for b in hasil if b.strip())


def post_process(text, jenis="umum"):
    text = strip_markdown(text)
    text = fix_narrative_citations(text)
    text = normalize_headings(text)
    #  ⚠️ URUTAN WAJIB (terukur 20 Okt 2026): PECAH dulu, baru gabung.
    #  Kalau dibalik, satu paragraf 945 kata tetap utuh karena penggabung
    #  memang tak punya tugas memecah.
    #  🚨 JEBAKAN TERUKUR: `jenis` HARUS diteruskan ke KEDUA fungsi. Versi
    #  pertama lupa meneruskan ⇒ keduanya memakai bawaan `umum` (ambang 60)
    #  walau bukunya `anak` (ambang 25) ⇒ paragraf 43 kata yang sudah
    #  dipecah DIGABUNG BALIK jadi 85 kata. Hasil akhir terlihat "tak
    #  berubah" padahal pemecahnya bekerja.
    text = pecah_paragraf_panjang(text, jenis=jenis)
    text = merge_short_paragraphs(text, jenis=jenis)
    
    # 5. Bersihkan narasi tabel bocor (Baris/Kolom/pipe-separated)
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        s = line.strip()
        # Skip narasi "Baris1: ..." atau "Kolom1: ..."
        if re.match(r'^(Baris\d+:|Kolom\d+:)', s, re.IGNORECASE):
            continue
        # Skip "Industri | Model Lama | ..." (pipe-separated narrative)
        if s.count('|') >= 2 and not s.startswith('[') and not s.startswith('#'):
            # Convert pipe ke comma (jadikan teks biasa, bukan tabel)
            parts = [p.strip() for p in s.split('|')]
            if 2 <= len(parts) <= 5:
                new_lines.append(', '.join(parts))
                continue
        new_lines.append(line)
    text = '\n'.join(new_lines)
    
    return text

def word_count(text):
    return len(text.split())

def count_citations(text):
    """Hitung sitasi APA 7 bentuk (Nama, Tahun) di dalam tanda kurung.

    ⚠️ POLA LAMA `\\([A-Z][a-z]+.*?\\d{4}\\)` SALAH (terukur 18 Okt 2026):
       - `(A, 2019)` TIDAK terhitung (butuh huruf kecil sesudah huruf besar)
       - beberapa sitasi dalam satu baris hanya terhitung 1 (regex rakus)
       Akibatnya penjaga sitasi bisa minta perbaikan padahal sudah cukup.

    Pola baru: ambil TIAP isi kurung yang memuat tahun 4 angka.
    """
    if not text:
        return 0
    n = 0
    for isi in re.findall(r'\(([^()]{3,200})\)', text):
        #  tahun 4 angka (1900-2099) menandakan sitasi, bukan sekadar "(lihat bab 2)"
        if re.search(r'\b(19|20)\d{2}\b', isi):
            n += 1
    return n

# === VISUAL GENERATION (ONE-PASS) ===

VISUAL_DIR = _BerkasUtas(os.path.join(OUT_DIR, "visual"), "visual")
os.makedirs(VISUAL_DIR, exist_ok=True)

def parse_tabel_marker(text):
    """Parse penanda tabel dari teks naskah.

    Bentuk yang didukung (KEDUANYA wajib jalan):
      A) AI menaruh data DI DALAM kurung siku (bentuk yang diminta prompt):
         [TABEL 1.1: Judul - Kol A, Kol B | Baris1: x, y | Baris2: x, y]
      B) AI menaruh data SETELAH penanda (bentuk lama, kompatibilitas):
         [TABEL 1.1: Judul - Kol A, Kol B]
         Baris1: x, y | Baris2: x, y

    🚨 CACAT TERUKUR 20 Okt 2026 — "TABEL BOCOR TOPIK".
    Versi lama SELALU menghasilkan `rows: []` untuk bentuk (A). Rantainya:
      ① regex Phase 1 memotong `full_content` di `]` ⇒ `Baris1:` (yang ada
         DI DALAM kurung siku) ikut terbuang sebelum dibaca;
      ② Phase 2 hanya memindai teks DI LUAR penanda ⇒ tidak ketemu apa pun;
      ③ `tables[tid] = {..., 'rows': []}` MENIMPA hasil apa pun dari atasnya;
      ④ assembly melihat rows kosong, lalu diam-diam memakai
         `TABEL_DATA_FALLBACK` = 12 tabel CONTOH tentang EKONOMI DIGITAL.
    Akibat nyata: buku anak "Mengamati Langit" terbit dengan tabel
    "Aset Utama / Ekonomi Tradisional / Gojek-Tokopedia".

    Obat AKAR (bukan tambalan): SATU fase, SATU penulis. `tables[tid]`
    dibuat SEKALI, dan baris data dari kedua bentuk dikumpulkan ke situ —
    tidak ada penimpaan. Tidak ada jalur yang bisa menghasilkan `rows: []`
    saat naskah sebenarnya memuat baris data.
    """
    tables = {}
    positions = []          # (posisi_mulai, tid)

    # ── FASE 1: temukan penanda + baca SEMUA baris di dalam kurung siku ──
    #    Regex TIDAK memotong di `]` supaya `Baris1:` ikut terbaca.
    pola = re.compile(
        r'\[?TABEL\s+(\d+\.\d+):\s*(.*?)'
        r'(?=\[?TABEL\s+\d+\.\d+|\n\n|\n##|\n###|$)',
        re.IGNORECASE | re.DOTALL)

    for m in pola.finditer(text):
        tid = m.group(1).strip()
        isi = m.group(2).strip()
        #  Buang penutup `]` yang menggantung di ujung.
        isi = isi.rstrip(']').strip()

        #  ── Pisahkan bagian judul/header dari bagian "Baris…" ──
        #  Ambil SEMUA "Baris<n>: …" lebih dulu, lalu sisanya = judul+header.
        baris_mentah = []
        for bm in re.finditer(r'[Bb]aris\s*\d+\s*:\s*([^|]+?)\s*(?=\||$|\[)',
                              isi):
            nilai = [v.strip() for v in bm.group(1).split(',') if v.strip()]
            if nilai:
                baris_mentah.append(nilai)

        kepala = re.split(r'[Bb]aris\s*\d+\s*:', isi)[0].strip()
        kepala = kepala.rstrip('|').strip()

        #  Judul vs kolom: pisah pada " - " pertama.
        parts = re.split(r'\s+[-–]\s+', kepala, maxsplit=1)
        title = parts[0].strip()[:100].split('\n')[0].strip()
        headers = ["Aspek", "Penjelasan"]

        if len(parts) > 1:
            kolom = parts[1].strip()
            kolom = re.sub(r'^[Kk]olom\s*:\s*', '', kolom)
            kolom = kolom.replace('\n', ' ').strip().rstrip('|').strip()
            kandidat = [c.strip() for c in kolom.split(',') if c.strip()]
            if kandidat:
                headers = kandidat

        #  ✅ DIBUAT SEKALI — tidak ada penimpaan sesudahnya.
        tables[tid] = {"title": title, "headers": headers,
                       "rows": list(baris_mentah)}
        positions.append((m.start(), tid))

    # ── FASE 2: baris data yang ditulis SETELAH penanda (bentuk lama) ──
    #     Hanya MENAMBAH ke tabel yang sudah ada; tidak pernah menimpa.
    for seg in re.split(r'[|\n]', text):
        bm = re.match(r'\s*[Bb]aris\s*\d+\s*:\s*(.+)', seg)
        if not bm:
            continue
        nilai = [v.strip().rstrip(']').strip()
                 for v in bm.group(1).split(',') if v.strip()]
        if not nilai:
            continue
        seg_pos = text.find(seg)
        best_tid, best_pos = None, -1
        for pos, tid in positions:
            if pos < seg_pos and pos > best_pos:
                best_pos, best_tid = pos, tid
        if best_tid and best_tid in tables:
            if nilai not in tables[best_tid]["rows"]:
                tables[best_tid]["rows"].append(nilai)

    return tables

def parse_diagram_marker(text):
    """Parse semua format DIAGRAM marker — FLEXIBLE (tanpa colon/dash juga OK)."""
    diagrams = {}
    for m in re.finditer(r'(?:\[)?DIAGRAM\s+(\d+\.\d+)[:\s]+([^\n\]]+)', text, re.IGNORECASE):
        tid = m.group(1).strip()
        rest = m.group(2).strip()
        # Split title dan desc: cari " - " atau "Visualisasi" atau "Garis" atau "Visual"
        parts = re.split(r'\s+[-–]\s+|(Visualisasi|Garis|Visual|Gambar|Skema|Bagan)', rest, maxsplit=1)
        title = parts[0].strip()
        desc = rest[len(title):].strip(' -–')
        if not desc and len(parts) > 2:
            desc = (parts[1] + parts[2]).strip() if len(parts) > 2 else rest
        if tid not in diagrams:
            diagrams[tid] = {"title": title[:80], "desc": desc[:200] if desc else title[:80]}
    return diagrams

_GAYA_DIAGRAM = """
* { margin:0; padding:0; box-sizing:border-box;
    font-family:'DejaVu Sans','Liberation Sans',Segoe UI,Roboto,Arial,sans-serif; }
body { background:#fff; padding:18px; }
.kartu { width:720px; }
.kepala { background:#0D2C5A; color:#fff; padding:11px 18px;
          border-radius:8px 8px 0 0; font-size:15px; font-weight:700; }
.badan { border:2px solid #e0e0e0; border-top:none; border-radius:0 0 8px 8px;
         padding:20px 22px 24px; background:#fafafa; }
.keterangan { font-size:12px; color:#555; font-style:italic;
              margin-bottom:18px; line-height:1.45; }
.susun { display:flex; flex-direction:column; gap:0; align-items:center; }
.tahap { display:flex; align-items:center; gap:12px; background:#fff;
         border:2px solid #2196f3; border-left:9px solid #0D2C5A;
         border-radius:8px; padding:11px 15px; width:100%; }
.no { background:#0D2C5A; color:#fff; border-radius:50%; width:34px;
      height:34px; line-height:34px; text-align:center; font-weight:700;
      font-size:15px; flex:0 0 34px; }
.isi { font-size:13.5px; color:#123; line-height:1.4; }
.panah { color:#0D2C5A; font-size:19px; line-height:1; padding:5px 0; }
.sumber { text-align:center; font-size:10.5px; color:#999; margin-top:14px; }
"""


_KATA_HUBUNG = ('lalu', 'dan', 'kemudian', 'selanjutnya', 'setelah itu',
                'akhirnya', 'berikutnya', 'serta', 'lalu,', 'dan,')


def _rapikan_label(teks, batas=96):
    """Rapikan satu label tahap jadi frasa yang BERDIRI SENDIRI.

    CACAT YANG DITANGKAP MATA (20 Okt 2026, diagram 3.1):
      · label 1 masih meta: "Gambar panah melingkar yang menunjukkan air
        laut menguap ke atas" ⇒ yang berguna cuma "air laut menguap ke atas"
      · label 2-4 kehilangan subjek dan diawali kata hubung: "berubah menjadi
        awan", "lalu turun sebagai hujan", "dan mengalir kembali ke laut"
        ⇒ dibaca sebagai kalimat tanggung.
    OBAT: (a) buang klausa meta "gambar … yang menunjukkan/menampilkan";
          (b) buang kata hubung di depan;
          (c) kata kerja tanpa subjek diberi subjek dari tahap sebelumnya
              (mis. "Air laut berubah menjadi awan").
    """
    t = re.sub(r'^\s*[\(\[]?\d+[\.\)\]]\s*', '', str(teks)).strip(' -–:,')

    #  (a) buang klausa meta di depan: "Gambar … yang menunjukkan X" → "X"
    m = re.match(r'^(?:gambar|skema|bagan|ilustrasi|visualisasi)\b[^,]*?'
                 r'\b(?:yang\s+)?(?:menunjukkan|menampilkan|memperlihatkan|'
                 r'berupa|menggambarkan)\s+(.+)$', t, re.IGNORECASE)
    if m:
        t = m.group(1)

    #  (b) buang kata hubung pembuka
    for _ in range(3):
        t2 = re.sub(r'^(?:%s)\b[,\s]*' % '|'.join(_KATA_HUBUNG), '', t,
                    flags=re.IGNORECASE).strip(' -–:,')
        if t2 == t:
            break
        t = t2

    t = re.sub(r'\s+', ' ', t).strip(' -–:,.')
    return t[:batas]


def _subjek_dari(teks):
    """Tebak SUBJEK (kata benda) dari awal frasa, berhenti di kata kerja.

    "air laut menguap ke atas"       → "air laut"
    "cahaya matahari putih masuk…"   → "cahaya matahari putih"
    "ragi ditaburkan ke adonan"      → "ragi"
    """
    kata = str(teks or '').split()
    if not kata:
        return ''
    for i, w in enumerate(kata):
        if i and _kata_kerja(w):
            return ' '.join(kata[:i])
    return ' '.join(kata[:3])


def _kata_kerja(kata):
    """Kata kerja bahasa Indonesia yang lazim muncul setelah subjek."""
    k = kata.lower().strip('.,;:')
    awalan = ('meng', 'meny', 'mem', 'men', 'me', 'ber', 'ter', 'di', 'ke',
              'pe', 'per')
    khusus = ('turun', 'naik', 'keluar', 'masuk', 'tumbuh', 'pecah', 'hilang',
              'muncul', 'terbentuk', 'jadi', 'ada', 'bisa', 'dapat', 'dibuang',
              'kembali', 'lagi')
    if k in khusus:
        return True
    #  "memakan", "menguap", "berubah", "terbentuk", "dipantulkan", "keluar"
    return any(k.startswith(a) and len(k) > len(a) + 2 for a in awalan)


#  Pasangan subjek → subjek baru setelah TAHAP PERTAMA. Mata manusia membaca
#  "air laut turun sebagai hujan" sebagai SALAH (yang jadi hujan itu awan),
#  dan "air laut mengalir kembali ke laut" sebagai TAUTOLOGI. Jadi subjek
#  WAJIB berganti mengikuti proses, bukan ditempel buta.
_GANTI_SUBJEK = {
    'air laut': ['uap air', 'awan', 'air hujan', 'air'],
    'air': ['uap air', 'awan', 'air hujan', 'air'],
    'uap air': ['awan', 'air hujan', 'air'],
    'cahaya': ['cahaya', 'cahaya', 'cahaya'],
    'ragi': ['ragi', 'ragi', 'ragi'],
}


def _rapikan_daftar(label, petunjuk):
    """Rapikan daftar label: subjek berganti mengikuti proses, tanpa tautologi.

    CACAT YANG DITANGKAP MATA (20 Okt 2026, dari .docx hasil rakit):
      menempel subjek yang SAMA di semua tahap menghasilkan kalimat salah:
        · "air laut turun sebagai hujan ke daratan"  ← yang turun itu awan
        · "air laut mengalir kembali ke laut"        ← tautologi
    OBAT: tahap pertama memakai subjek asli; tahap berikutnya memakai subjek
    dari rantai `_GANTI_SUBJEK` (uap air → awan → air hujan). Kalau rantai
    tidak dikenal, subjek TIDAK ditempel (lebih baik label pendek & benar
    daripada label panjang & salah).
    """
    hasil = [x for x in label if x]
    if not hasil:
        return hasil
    asli = _subjek_dari(hasil[0])
    rantai = _GANTI_SUBJEK.get(asli.lower()) if asli else None

    for i in range(1, len(hasil)):
        awal = hasil[i].split()[0].lower() if hasil[i].split() else ''
        #  Sudah punya subjek sendiri? jangan sentuh.
        if not _kata_kerja(awal) and not awal.startswith(('meng', 'ber')):
            continue
        if not rantai:
            continue                      #  tak dikenal ⇒ jangan menebak
        subjek = rantai[min(i, len(rantai)) - 1] if i - 1 < len(rantai) \
            else rantai[-1]
        #  Jangan sampai jadi tautologi: subjek == kata benda di belakangnya.
        if subjek.lower() in hasil[i].lower():
            continue
        hasil[i] = f'{subjek} {hasil[i]}'
    return hasil


def pecah_tahapan(desc, jumlah):
    """Bagi keterangan diagram jadi `jumlah` label tahap.

    Yang dicoba berurutan (yang PERTAMA cocok dipakai):
      ① penanda eksplisit "(1)…", "1)…", "1.…"  — bentuk paling lazim
      ② daftar berkoma/titik-koma
      ②b daftar yang masih disambung " dan "
      ③ potong rata jadi `jumlah` bagian (usaha terakhir)

    ⚠️ PAGAR MUTU (20 Okt 2026, dari UKURAN + MATA — bukan selera):
    Pemotongan yang benar secara JUMLAH belum tentu benar secara ISI.
    Terukur: "gambar penampang mata … kornea, pupil, lensa, retina …" dipecah
    7 label menghasilkan "gambar penampang mata" / "dengan panah menunjukkan"
    / "arah cahaya dari" — jumlahnya 7, isinya SAMPAH. Sebaliknya daftar
    berkoma asli ("mulut ke kerongkongan, lambung, usus halus, usus besar")
    menghasilkan label utuh yang benar.
    ⇒ Hanya cara ①②②b (yang menghormati batas yang DITULIS penulis) yang
      boleh lolos. Cara ③ (potong rata per kata) DIBUANG: kalau tidak ada
      daftar asli, lebih baik template daripada diagram berisi potongan
      kalimat tanggung.

    Balasan: daftar label (panjang HARUS sama dengan `jumlah`, selain itu
    pemanggil jatuh ke template).
    """
    teks = str(desc or '')
    if not jumlah or jumlah < 2:
        return []

    #  ① penanda nomor eksplisit
    bertanda = re.findall(r'[\(\[]?(\d{1,2})[\.\)\]]\s*([^\d][^\)\]]{2,180})',
                          teks)
    if len(bertanda) >= jumlah:
        label = [_rapikan_label(b) for _, b in bertanda[:jumlah]]
        if all(len(x) > 2 for x in label):
            return _rapikan_daftar(label, teks)

    #  ② daftar berkoma — buang dulu kalimat pengantar sebelum titik dua
    badan = teks.split(':', 1)[1] if ':' in teks else teks
    potong = [p for p in re.split(r'[,;]\s*', badan) if len(p.strip()) > 3]
    if len(potong) == jumlah:
        return _rapikan_daftar([_rapikan_label(p) for p in potong], teks)
    if len(potong) > jumlah:
        #  Gabungkan sisa ke potongan terakhir supaya jumlahnya tepat.
        kepala = [_rapikan_label(p) for p in potong[:jumlah - 1]]
        kepala.append(_rapikan_label(', '.join(potong[jumlah - 1:])))
        return _rapikan_daftar(kepala, teks)

    #  ②b daftar yang masih disambung " dan " ("cacing DAN pengurai memecah")
    if len(potong) < jumlah:
        pecah_lagi = []
        for p in potong:
            pecah_lagi.extend(re.split(r'\s+dan\s+', p))
        pecah_lagi = [x for x in pecah_lagi if len(x.strip()) > 3]
        if len(pecah_lagi) == jumlah:
            return _rapikan_daftar([_rapikan_label(p) for p in pecah_lagi], teks)

    #  ✗ Cara ③ (potong rata per kata) SENGAJA TIDAK ADA — lihat pagar mutu.
    return []


def generate_diagram_html(diagram_id, title, desc, tahap=None):
    """Diagram buku: bentuk DIPILIH DARI ISI (delegasi ke `diagram_buku`).

    🚨 KELUHAN BOS 20 Okt 2026: "Masih gunakan diagram lama, kotak garis,
    panah ke bawah. = Jelek! ... Tidak variasi".
    ✅ Sekarang: 8 bentuk (alur/siklus/pohon/piramida/lapisan/batang/pai/
    garis), dipilih dari kata kunci ISI + jumlah tahap. Teks rata tengah,
    lebar 72% (bukan full width).
    Cadangan: kalau `diagram_buku` gagal dimuat, pakai template lama supaya
    buku tetap terbit.
    """
    try:
        import diagram_buku
        return diagram_buku.html_diagram(diagram_id, title, desc, tahap)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[diagram] diagram_buku gagal (%s) — pakai template lama',
                    e)
    if tahap:
        baris = []
        for i, isi in enumerate(tahap, 1):
            baris.append(
                f'<div class="tahap"><div class="no">{i}</div>'
                f'<div class="isi">{_aman_html(isi)}</div></div>')
            if i < len(tahap):
                baris.append('<div class="panah">▼</div>')
        isi_badan = (f'<div class="keterangan">{_aman_html(desc)}</div>'
                     f'<div class="susun">{"".join(baris)}</div>')
    else:
        isi_badan = f"""
    <div class="keterangan">{_aman_html(desc)}</div>
    <div class="susun">
      <div class="tahap"><div class="no">1</div>
        <div class="isi"><b>KONSEP</b> — ide &amp; inovasi utama</div></div>
      <div class="panah">▼</div>
      <div class="tahap"><div class="no">2</div>
        <div class="isi"><b>{_aman_html(title)}</b> — pokok bahasan</div></div>
      <div class="panah">▼</div>
      <div class="tahap"><div class="no">3</div>
        <div class="isi"><b>IMPLEMENTASI</b> — penerapan &amp; praktik</div></div>
    </div>"""
    return f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8"><style>{_GAYA_DIAGRAM}</style>
</head><body>
<div class="kartu">
  <div class="kepala">Diagram {_aman_html(diagram_id)} {_aman_html(title)}</div>
  <div class="badan">{isi_badan}
    <div class="sumber">Sumber: analisis konsep {_aman_html(title)}</div>
  </div>
</div></body></html>"""


def _aman_html(teks):
    """Escape supaya teks naskah tidak merusak HTML (dan tidak jadi tag)."""
    return (str(teks if teks is not None else '')
            .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))

def render_html_to_png(html_content, output_path):
    """Render HTML diagram → PNG, TANPA browser.

    JEJAK AKAR (20 Okt 2026): fungsi ini dulu STUB — hanya menulis HTML lalu
    `return html_file`, dengan komentar "render manual nanti". Akibatnya
    `diagram_*.png` TIDAK PERNAH ada, dan perakit melewati diagram DIAM-DIAM
    ⇒ dari 12 diagram di naskah, 0 masuk .docx. Cacat senyap: laporan bilang
    "visuals complete".

    JALUR OBAT (semua SUDAH terpasang di image eduai-app — tidak tambah paket):
        HTML --WeasyPrint--> PDF --PyMuPDF(150dpi)--> PNG --PIL--> potong margin
    Playwright/selenium/imgkit TIDAK ADA di image ⇒ jangan dipakai.

    Balasan: path PNG (atau None kalau gagal — pemanggil WAJIB melaporkan).
    """
    try:
        import io

        import fitz
        import weasyprint
        from PIL import Image
    except Exception as e:                                        # noqa: BLE001
        print(f"       ⚠️ Diagram TIDAK dirender: pustaka tidak ada ({e})")
        return None

    try:
        pdf = weasyprint.HTML(string=html_content).write_pdf()
        dok = fitz.open(stream=pdf, filetype='pdf')
        pix = dok[0].get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB')
        #  Halaman A4 selalu berisi ruang kosong besar; potong supaya gambar
        #  tidak menempati seperempat halaman di .docx.
        kotak = img.convert('L').point(lambda x: 0 if x > 250 else 255).getbbox()
        if kotak:
            img = img.crop(kotak)
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        img.save(output_path)
        return output_path
    except Exception as e:                                        # noqa: BLE001
        print(f"       ⚠️ Diagram GAGAL dirender: {type(e).__name__}: {e}")
        return None

#  ══════════════════════════════════════════════════════════════════════════
#  ILUSTRASI = 2 TAHAP (putusan Bos 18 Okt 2026) — DARI ISI BAB, BUKAN LABEL
#  ══════════════════════════════════════════════════════════════════════════
#  Dulu (SALAH): prompt = label topik bab ("ilustrasi smartphone wallet") +
#    template 3D "photorealistic, rich lighting" ⇒ hasil wallpaper fintech
#    generik, tak ada hubungan dengan isi bab, dan jadi abu-abu kotor saat
#    dicetak hitam-putih (interior buku umum biasanya B/W demi ongkos cetak).
#  Sekarang: (1) LLM (call_llm di bawah) menulis BRIEF dari ringkasan bab +
#    sub-bab di tengah bab → (2) prompt = STYLE_BUKU (editorial line art navy +
#    terracotta di kertas krem) + brief. Gaya SATU untuk seluruh bab.
#  Modul: /opt/data/brief_visual.py (brief_visual, prompt_gambar, apa_brief_generik)
#  QC: brief tanpa TOKOH+AKSI+LATAR konkret = terlalu generik → brief diulang,
#      BUKAN ganti seed gambar. Posisi gambar tetap 40-60% paragraf (assembly).
#  ══════════════════════════════════════════════════════════════════════════

def _sub_bab_tengah(bab_text):
    """Ambil 2-3 sub-bab di sekitar posisi gambar (40-60% bab) untuk konteks brief."""
    if not bab_text:
        return ""
    bagian = re.split(r'(?m)^###\s+', bab_text)
    subs = [b.strip() for b in bagian[1:] if b.strip()]
    if not subs:
        return ""
    n = len(subs)
    tengah = int(n * 0.5)
    pilih = [subs[i] for i in range(max(0, tengah - 1), min(n, tengah + 2))]
    return "\n\n".join(s[:900] for s in pilih)


def _gambar_inferhub(prompt, simpan=None, ukuran="1024x1024", seed=1000,
                     timeout=280):
    """Panggil InferHub → simpan PNG. Return path atau None.

    PINTU TUNGGAL ke InferHub. Dipakai DUA jalur:
      ① `generate_ilustrasi_api()` (produksi buku, varian 3-pilih-1)
      ② `brief_visual.buat_ilustrasi()` (uji/alat, satu gambar)

    🚨 CACAT TERUKUR 20 Okt 2026: `brief_visual.buat_ilustrasi` mengimpor
    `_gambar_inferhub` DAN `gambar_dari_prompt` — DUA-DUANYA tidak ada ⇒
    ilustrasi tidak pernah dibuat lewat jalur itu. Fungsi ini menutupnya
    dengan MEMINDAHKAN inti kode InferHub yang sudah teruji, bukan
    menulis pemanggil baru.

    Model TERUJI 18 Okt 2026: cb/gemini-2.5-flash-image satu-satunya yang
    hidup (45 penjual); 29 nama lain 0 penjual. 6,9–9,2 s · ~Rp 7/gambar.
    """
    if not prompt:
        return None
    if not simpan:
        os.makedirs(VISUAL_DIR, exist_ok=True)
        simpan = os.path.join(visual_ini(), "ilustrasi.png")
    folder = os.path.dirname(simpan) or VISUAL_DIR
    os.makedirs(folder, exist_ok=True)

    try:
        resp = requests.post(
            f"{GAMBAR_BASE}/images/generations",
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {GAMBAR_KEY}"},
            json={"model": GAMBAR_MODEL, "prompt": prompt, "n": 1,
                  "size": ukuran, "response_format": "b64_json",
                  "seed": seed},
            timeout=timeout)
        data = resp.json()
    except Exception as e:                                    # noqa: BLE001
        print(f"       ⚠️ InferHub error: {type(e).__name__}: {e}")
        return None

    if not data.get("data"):
        print(f"       ⚠️ InferHub kosong: {str(data)[:120]}")
        return None

    item = data["data"][0]
    raw = None
    if item.get("b64_json"):
        import base64 as _b64
        raw = _b64.b64decode(item["b64_json"])
    elif item.get("url"):
        raw = requests.get(item["url"], timeout=90).content
    if not raw:
        return None

    with open(simpan, 'wb') as f:
        f.write(raw)
    print(f"       ✅ Gambar: {simpan} ({round(len(raw)/1024)} KB)")
    return simpan


def generate_ilustrasi_api(bab_num, bab_title, ringkasan_bab="", bab_text="",
                           varian=3):
    """Generate ilustrasi (2 tahap + kurasi): brief dari isi bab → gambar.

    varian > 1 → simpan SEMUA varian (ilustrasi_babN_varK.png) dan pakai
    varian pertama sebagai default; pemilihan terbaik dilakukan lewat
    brief_visual.pilih_varian() dengan deskripsi hasil periksa mata
    (LANGKAH 3 kurasi 3-pilih-1 — tidak memilih buta).
    """
    from brief_visual import prompt_dari_bab, GAYA_DEFAULT, MODE_BRIEF

    if not ringkasan_bab:
        print("       ⚠️ Ilustrasi dilewati: ringkasan bab kosong "
              "(brief WAJIB dari isi bab, bukan dari judul)")
        return None

    hasil = prompt_dari_bab(bab_num, ringkasan_bab,
                            sub_bab=_sub_bab_tengah(bab_text),
                            gaya=GAYA_DEFAULT, panggil_llm=call_llm,
                            mode=MODE_BRIEF)
    if not hasil["prompt"]:
        print(f"       ⚠️ Ilustrasi dilewati: {hasil['galat']}")
        return None
    prompt = hasil["prompt"]
    print(f"       📝 Brief {MODE_BRIEF} ({hasil['brief_meta']['percobaan']}x): "
          f"{hasil['brief'][:110]}...")

    #  ── InferHub LANGSUNG (putusan Bos 18 Okt 2026) ──────────────────────
    #  Diganti dari enowx (cbc/hunyuan-image-v3.0) karena akun enowx KOSONG.
    #  TERUJI 18 Okt: cb/gemini-2.5-flash-image = satu-satunya model gambar
    #  yang HIDUP di InferHub (45 penjual). 29 nama lain 0 penjual = mati.
    #  Kecepatan 6,9–9,2 s · biaya $0,00043/gambar (~Rp 7) · hasil b64 inline.
    berhasil = []
    for k in range(1, max(1, varian) + 1):
        try:
            resp = requests.post(f"{GAMBAR_BASE}/images/generations",
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {GAMBAR_KEY}"},
                json={"model": GAMBAR_MODEL,
                      "prompt": prompt, "n": 1, "size": "1024x1024",
                      "response_format": "b64_json",
                      # seed beda per varian = komposisi berbeda, GAYA tetap sama
                      "seed": 1000 + k},
                timeout=280)
            data = resp.json()
            if "data" not in data or not data["data"]:
                print(f"       ⚠️ Varian {k} kosong: {str(data)[:100]}")
                continue
            item = data["data"][0]
            raw = None
            if item.get("b64_json"):                 # InferHub: inline base64
                import base64 as _b64
                raw = _b64.b64decode(item["b64_json"])
            elif item.get("url"):                    # cadangan: kalau ada URL
                raw = requests.get(item["url"], timeout=60).content
            if not raw:
                continue
            os.makedirs(VISUAL_DIR, exist_ok=True)
            if varian > 1:
                p = os.path.join(visual_ini(), f"ilustrasi_bab{bab_num}_var{k}.png")
            else:
                p = os.path.join(visual_ini(), f"ilustrasi_bab{bab_num}.png")
            with open(p, 'wb') as f:
                f.write(raw)
            berhasil.append(p)
            print(f"       ✅ Varian {k}: {round(len(raw)/1024)} KB")
        except Exception as e:
            print(f"       ⚠️ Varian {k} error: {type(e).__name__}: {e}")
    if not berhasil:
        return None

    # Simpan catatan brief+varian agar kurasi (pilih 1) bisa dilakukan sesudahnya
    try:
        import json as _json
        catatan = {"bab": bab_num, "judul": bab_title, "mode": MODE_BRIEF,
                   "brief": hasil["brief"], "prompt": prompt, "varian": berhasil}
        with open(os.path.join(visual_ini(), f"brief_bab{bab_num}.json"), 'w') as f:
            _json.dump(catatan, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    # Default = varian pertama; ganti dengan pilihan kurasi bila ada
    default = berhasil[0]
    if berhasil and os.path.basename(default).endswith("_var1.png"):
        pilih = os.path.join(visual_ini(), f"ilustrasi_bab{bab_num}.png")
        import shutil
        shutil.copyfile(default, pilih)
        if len(berhasil) > 1:
            print(f"       ℹ️ {len(berhasil)} varian siap dikurasi "
                  f"(brief_bab{bab_num}.json). Default = varian 1.")
        return pilih
    return default

def generate_bab_visuals(bab_num, bab_title, bab_text, ringkasan_bab=""):
    """ONE-PASS: Generate semua visual untuk 1 bab setelah teks selesai."""
    print(f"\n  🎨 Generating visuals for BAB {bab_num}...")

    # 1. Parse tabel & diagram markers dari teks
    tables = parse_tabel_marker(bab_text)
    diagrams = parse_diagram_marker(bab_text)
    print(f"     Found: {len(tables)} tabel, {len(diagrams)} diagram markers")

    # 2. Simpan tabel data ke JSON (untuk assembly)
    tabel_data_path = os.path.join(visual_ini(), f"tabel_bab{bab_num}.json")
    with open(tabel_data_path, 'w') as f:
        json.dump(tables, f, indent=2, ensure_ascii=False)

    # 3. Generate diagram HTML **dan PNG-nya**
    #    JEJAK AKAR (20 Okt 2026): dulu HANYA .html yang ditulis, sedangkan
    #    perakit mencari `diagram_{id}.png` ⇒ dilewati tanpa sepatah kata.
    #    Sekarang: render → PNG, dan yang gagal DICATAT ke laporan_visual
    #    supaya tidak ada lagi "complete" yang bohong.
    #
    #  🧭 JEV DI DEPAN (putusan Bos 20 Okt 2026, pilih A): tahapan diagram
    #     dibaca Jev — bukan ditebak template. Bukti terukur: Jev membaca
    #     "empat tahap air mendidih" dengan yakin 0,98 (0,69 dtk, 4 pertanyaan).
    #     Kalau Jev mati/ragu ⇒ template lama, buku TETAP jadi.
    laporan_visual = {'diagram_png': [], 'diagram_gagal': [],
                      'diagram_ber_tahap': [], 'diagram_template': []}
    for did, dinfo in diagrams.items():
        tahap, asal = [], 'template'
        try:
            import tahapan_diagram as TD
            tahap, asal = TD.tahapan_diagram(did, dinfo["title"],
                                             dinfo["desc"], pecah_tahapan)
        except Exception as e:                                 # noqa: BLE001
            print(f"       ⚠️ Jev tahapan {did} dilewati: {type(e).__name__}: {e}")
        (laporan_visual['diagram_ber_tahap'] if asal == 'jev'
         else laporan_visual['diagram_template']).append(did)
        html = generate_diagram_html(did, dinfo["title"], dinfo["desc"],
                                     tahap=tahap)
        html_path = os.path.join(visual_ini(), f"diagram_{did}.html")
        with open(html_path, 'w') as f:
            f.write(html)
        png_path = os.path.join(visual_ini(), f"diagram_{did}.png")
        hasil_png = render_html_to_png(html, png_path)
        if hasil_png and os.path.exists(hasil_png):
            laporan_visual['diagram_png'].append(did)
            print(f"     📐 Diagram {did}: PNG ✅ "
                  f"({os.path.getsize(hasil_png)//1024}KB, "
                  f"{len(tahap)} tahap dari {asal})")
        else:
            laporan_visual['diagram_gagal'].append(did)
            print(f"     ❌ Diagram {did}: PNG GAGAL — akan hilang dari buku")

    # 4. Generate ilustrasi (2 tahap: brief dari ISI bab → line art buku)
    ilust_path = generate_ilustrasi_api(bab_num, bab_title,
                                        ringkasan_bab=ringkasan_bab,
                                        bab_text=bab_text)
    if ilust_path:
        print(f"     🖼️ Ilustrasi: {os.path.getsize(ilust_path)//1024}KB ✅")
    else:
        print(f"     🖼️ Ilustrasi: skipped (API error)")

    print(f"  ✅ Visuals BAB {bab_num} complete: {len(tables)} tabel + "
          f"{len(diagrams)} diagram "
          f"({len(laporan_visual['diagram_png'])} PNG ok, "
          f"{len(laporan_visual['diagram_ber_tahap'])} ber-tahap dari Jev, "
          f"{len(laporan_visual['diagram_gagal'])} GAGAL)")
    return laporan_visual

# === CHECKPOINT ===

def load_checkpoint():
    if os.path.exists(CKPT_FILE):
        with open(CKPT_FILE) as f:
            return json.load(f)
    return {"babs": {}}

def save_checkpoint(ckpt):
    with open(CKPT_FILE, 'w') as f:
        json.dump(ckpt, f, indent=2, ensure_ascii=False)

def is_sub_done(ckpt, bab, sub):
    b = ckpt["babs"].get(str(bab), {})
    return sub in b.get("subs_done", [])

# === PIPELINE ===

OUTLINE = {
    1: {
        "title": "Revolusi Digital dan Lanskap Ekonomi Baru",
        "subs": [
            ("1.1", "Dari Ekonomi Tradisional ke Digital: Sebuah Perjalanan",
             "definisi ekonomi digital, perbedaan ekonomi tradisional vs digital, revolusi industri 4.0, contoh transformasi nyata"),
            ("1.2", "Pilar Ekonomi Digital: Platform, Data, dan Konektivitas",
             "platform economy, data sebagai aset strategis, konektivitas internet/mobile, infrastruktur digital"),
            ("1.3", "Aktor Utama: Startup, Tech Giant, dan Pemerintah",
             "peran startup digital, dominasi tech giant (GAFAM), regulasi pemerintah, ekosistem digital"),
            ("1.4", "Tantangan dan Peluang Ekonomi Digital di Indonesia",
             "roadmap digital nasional, gap infrastruktur, demografi bonus, ekonomi digital Indonesia"),
        ]
    },
    2: {
        "title": "Model Bisnis Digital dan Strategi Persaingan",
        "subs": [
            ("2.1", "Model Bisnis Berbasis Platform: Network Effect dan Skalabilitas",
             "network effect, two-sided market, skalabilitas digital, contoh Gojek/Tokopedia"),
            ("2.2", "Freemium, Subscription, dan Ekonomi Langganan",
             "model freemium, SaaS, subscription economy, recurring revenue, contoh Netflix/Spotify"),
            ("2.3", "Disrupsi dan Inovasi: Bagaimana Digital Mengubah Industri Tradisional",
             "disrupsi digital, creative destruction Schumpeter, contoh Uber/Netflix/Tokopedia"),
            ("2.4", "Strategi Kompetitif di Ekonomi Digital",
             "lock-in effect, data moat, first-mover advantage, Porter dalam konteks digital"),
        ]
    },
    3: {
        "title": "Ekosistem Pembayaran Digital dan Masa Depan",
        "subs": [
            ("3.1", "Evolusi Pembayaran: Tunai ke Digital",
             "cashless society, e-wallet, QRIS, open banking, transformasi pembayaran Indonesia"),
            ("3.2", "Fintech dan Demokratisasi Layanan Keuangan",
             "fintech lending, P2P lending, robo-advisor, financial inclusion, contoh Akulaku/Kredivo"),
            ("3.3", "Kripto, CBDC, dan Tantangan Regulasi",
             "cryptocurrency, blockchain, CBDC (Rupiah digital), regulasi BI, tantangan regulasi kripto"),
            ("3.4", "Masa Depan Ekonomi Digital: AI, IoT, dan Web3",
             "AI dalam ekonomi, IoT, Web3, metaverse, sustainability, masa depan ekonomi digital"),
        ]
    }
}

REFERENCES = [
    "Brynjolfsson, E., & McAfee, A. (2014). The second machine age: Work, progress, and prosperity in a time of brilliant technologies. W. W. Norton.",
    "Porter, M. E. (1985). Competitive advantage: Creating and sustaining superior performance. Free Press.",
    "Tapscott, D. (1996). The digital economy: Promise and peril in the age of networked intelligence. McGraw-Hill.",
    "Schumpeter, J. A. (1942). Capitalism, socialism and democracy. Harper & Brothers.",
    "Kotler, P., & Keller, K. L. (2016). Marketing management (15th ed.). Pearson.",
    "Parker, G. G., Van Alstyne, M. W., & Choudary, S. P. (2016). Platform revolution: How networked markets are transforming the economy. W. W. Norton.",
    "Christensen, C. M. (1997). The innovator's dilemma: When new technologies cause great firms to fail. Harvard Business Review Press.",
    "Kenny, C. (2021). The economics of digital transformation. World Bank Group.",
    "Bank Indonesia. (2023). Laporan ekonomi dan keuangan digital Indonesia. Bank Indonesia.",
    "Rifkin, J. (2014). The zero marginal cost society: The internet of things, the collaborative commons, and the eclipse of capitalism. Palgrave Macmillan.",
    "O'Reilly, T. (2017). WTF?: What's the future and why it's up to us. Harper Business.",
    "Narasimhan, C., & Turut, O. (2019). Freemium and digital goods. Marketing Science, 38(2), 281-296.",
    "Nakamoto, S. (2008). Bitcoin: A peer-to-peer electronic cash system. https://bitcoin.org/bitcoin.pdf",
    "Mougayar, W. (2016). The business blockchain: Promise, practice, and application of the next internet technology. Wiley.",
    "Galloway, S. (2017). The four: The hidden DNA of Amazon, Apple, Facebook, and Google. Portfolio.",
    "Manyika, J., et al. (2016). Digital globalization: The new era of global flows. McKinsey Global Institute.",
    "OECD. (2021). The digital economy report 2021. United Nations Conference on Trade and Development.",
    "World Bank. (2021). World development report 2021: Data for better lives. World Bank.",
    "Bloomberg. (2022). The digital economy: Trends and forecasts. Bloomberg Finance L.P.",
    "Deloitte. (2023). Southeast Asia's digital economy report 2023. Deloitte Southeast Asia.",
]

GLOSARIUM = {
    "Ekonomi Digital": "Aktivitas ekonomi yang berbasis teknologi digital, mencakup e-commerce, fintech, dan layanan digital.",
    "Platform Economy": "Model ekonomi yang menciptakan nilai melalui interaksi antara dua atau lebih kelompok pengguna via platform digital.",
    "Network Effect": "Fenomena di mana nilai suatu produk atau layanan meningkat seiring bertambahnya pengguna.",
    "Freemium": "Model bisnis yang menawarkan layanan dasar gratis dan layanan premium berbayar.",
    "Disrupsi Digital": "Transformasi yang mengubah model bisnis tradisional melalui teknologi digital.",
    "Fintech": "Teknologi keuangan yang menyediakan layanan keuangan secara digital.",
    "CBDC": "Central Bank Digital Currency, mata uang digital yang diterbitkan bank sentral.",
    "Blockchain": "Teknologi buku besar terdistribusi yang mencatat transaksi secara aman dan transparan.",
    "SaaS": "Software as a Service, model layanan perangkat lunak berbasis langganan cloud.",
    "Two-Sided Market": "Pasar dengan dua kelompok pengguna yang saling membutuhkan (misal: pembeli dan penjual di marketplace).",
    "Data Moat": "Keunggulan kompetitif yang diperoleh dari kepemilikan data dalam jumlah besar.",
    "QRIS": "Quick Response Code Indonesian Standard, standar pembayaran QR nasional Indonesia.",
    "Open Banking": "Sistem yang membuka akses data keuangan nasabah kepada pihak ketiga melalui API.",
    "Web3": "Generasi internet berbasis blockchain yang menekankan desentralisasi.",
    "IoT": "Internet of Things, jaringan perangkat fisik yang terhubung ke internet untuk bertukar data.",
    "Metaverse": "Ruang virtual 3D di mana pengguna dapat berinteraksi secara imersif.",
    "Robo-Advisor": "Platform advisory keuangan otomatis yang menggunakan algoritma AI.",
}

def generate_sub_bab(bab_num, bab_title, sub_num, sub_title, key_points, rolling_summary, refs=None, jenis="umum"):
    """Generate 1 sub-bab via 4-agen council."""
    print(f"  [{sub_num}] {sub_title}")
    
    # Cari referensi nyata jika belum ada
    if refs is None:
        # FIX: Jangan masukkan key_points yang mengandung nama author+tahun
        # Gunakan bab_title + sub_title saja sebagai query
        topic = f"{bab_title} {sub_title} teori konsep jurnal penelitian"
        refs = search_real_references(topic, n=5)
        print(f"       Refs: {len(refs)} terverifikasi")
    
    print(f"       Architect...", end="", flush=True)
    t0 = time.time()
    draft = call_llm(architect_prompt(bab_num, bab_title, sub_num, sub_title, key_points, rolling_summary, refs=refs, jenis=jenis))
    t1 = time.time()
    print(f" {t1-t0:.1f}s ({word_count(draft)} kata)")

    #  ── SKEPTIC → PRAGMATIST → EDITOR (TETAP BERURUTAN) ─────────────────
    #  🚨 DIBATALKAN 19 Okt 2026 (Lapis 2 versi awal): Wulan hampir
    #     menjalankan Skeptic + Pragmatist BERSAMAAN. TIDAK BISA:
    #     `pragmatist_prompt(draft, kritik)` MEMAKAI kritik sebagai BAHAN.
    #     Mengirim kritik kosong = menurunkan mutu diam-diam.
    #     Cek bukti: `sed -n '391,394p' buku_umum_pipeline.py`.
    #  Lihat catatan "YANG MASIH BISA DIPARALELKAN" di bawah.
    print(f"       Skeptic...", end="", flush=True)
    t2 = time.time()
    kritik = call_llm(skeptic_prompt(sub_title, draft), max_tokens=3000, timeout=90)
    t3 = time.time()
    print(f" {t3-t2:.1f}s")

    print(f"       Pragmatist...", end="", flush=True)
    t4 = time.time()
    saran = call_llm(pragmatist_prompt(draft, kritik), max_tokens=3000, timeout=90)
    t5 = time.time()
    print(f" {t5-t4:.1f}s")

    print(f"       Editor...", end="", flush=True)
    t6 = time.time()
    final = call_llm(editor_prompt(sub_title, draft, kritik, saran, jenis=jenis))
    t7 = time.time()
    print(f" {t7-t6:.1f}s ({word_count(final)} kata)")

    # Post-process
    final = post_process(final, jenis=jenis)
    
    # VERIFIKASI SITASI: hapus sitasi yang tidak ada di list referensi
    if refs:
        verif = verify_text_citations(final, refs)
        final = verif["clean_text"]
        if verif["unverified"]:
            print(f"       [VERIF] Hapus {len(verif['unverified'])} sitasi tidak terverifikasi: {verif['unverified'][:3]}")
        # Simpan referensi terverifikasi untuk daftar pustaka
        refs_path = os.path.join(visual_ini(), f"refs_bab{bab_num}.json")
        existing_refs = []
        if os.path.exists(refs_path):
            try:
                with open(refs_path) as f:
                    existing_refs = json.load(f)
            except:
                existing_refs = []
        for r in refs:
            apa = format_apa(r)
            if apa not in existing_refs:
                existing_refs.append(apa)
        with open(refs_path, 'w') as f:
            json.dump(existing_refs, f, indent=2, ensure_ascii=False)

    #  ── PENJAGA SITASI (18 Okt 2026) ────────────────────────────────────
    #  ⚠️ SEBELUM INI: "KURANG dari 2 = GAGAL" hanya TULISAN di prompt.
    #  Kode tidak pernah memeriksa. Terukur: buku anak keluar 1 sitasi
    #  padahal 8 referensi tersedia — dan lolos tanpa keluhan.
    #  Sekarang: 1 kesempatan perbaikan dengan referensi yang PASTI ada.
    #  Kalau masih kurang, dicatat TERANG — bukan didiamkan.
    MIN_SITASI = 2
    cit = count_citations(final)
    kalau = refs or []
    if cit < MIN_SITASI and kalau:
        daftar = "\n".join(f"- {format_apa(r)}" for r in kalau[:8])
        print(f"       [SITASI] hanya {cit} — minta perbaikan", flush=True)
        perbaikan = call_llm(
            f"""Teks di bawah hanya punya {cit} sitasi, padahal WAJIB minimal
{MIN_SITASI}. Tambahkan sitasi dari DAFTAR REFERENSI saja.

DAFTAR REFERENSI (HANYA ini yang boleh dikutip):
{daftar}

TEKS:
{final[:6000]}

ATURAN:
- Sisipkan sitasi APA 7 bentuk (Nama, Tahun) pada pernyataan yang memang
  didukung referensi itu. JANGAN mengarang nama/tahun di luar daftar.
- Sisipkan di tempat yang WAJAR — bukan menumpuk di akhir paragraf.
- JANGAN mengubah isi, JANGAN memotong narasi, JANGAN menambah markdown.
- Kalau tidak ada referensi yang cocok untuk suatu bagian, biarkan bagian
  itu tanpa sitasi — lebih baik daripada sitasi palsu.

Output: teks lengkap hasil perbaikan saja.""",
            max_tokens=4000, timeout=120)
        if perbaikan and len(perbaikan) > len(final) * 0.7:
            perbaikan = post_process(perbaikan, jenis=jenis)
            if refs:
                verif2 = verify_text_citations(perbaikan, refs)
                perbaikan = verif2["clean_text"]
            cit2 = count_citations(perbaikan)
            if cit2 > cit:
                print(f"       [SITASI] {cit} -> {cit2} setelah perbaikan",
                      flush=True)
                final, cit = perbaikan, cit2
            else:
                print(f"       [SITASI] perbaikan tidak menambah "
                      f"({cit2}) — teks asli dipakai", flush=True)
        else:
            print("       [SITASI] perbaikan ditolak (terlalu pendek)",
                  flush=True)

    if cit < MIN_SITASI:
        print(f"       [SITASI] ⚠️ AKHIR: hanya {cit} sitasi "
              f"(minimum {MIN_SITASI}) — TIDAK dipalsukan", flush=True)
    
    # Rolling summary
    print(f"       Summary...", end="", flush=True)
    t8 = time.time()
    summary = call_llm(summarize_prompt(final), max_tokens=2500, timeout=90)
    t9 = time.time()
    print(f" {t9-t8:.1f}s")

    wc = word_count(final)
    cit = count_citations(final)
    md = len(re.findall(r'[*_`]', final))
    print(f"       ✅ {wc} kata, {cit} sitasi, markdown={md}")

    return final, summary, wc, cit

def generate_intro(bab_num, bab_title, rolling_summary, jenis="umum"):
    """Generate intro bab (hook)."""
    print(f"  [INTRO] {bab_title}")
    print(f"       Architect...", end="", flush=True)
    t0 = time.time()
    intro = call_llm(architect_prompt(bab_num, bab_title, None, None, None, rolling_summary, is_intro=True, jenis=jenis), max_tokens=2500, timeout=90)
    t1 = time.time()
    print(f" {t1-t0:.1f}s ({word_count(intro)} kata)")
    intro = post_process(intro, jenis=jenis)
    return intro

def generate_closing(bab_num, bab_title, rolling_summary, jenis="umum"):
    """Generate penutup bab (naratif, bukan ringkasan formal)."""
    print(f"  [PENUTUP] {bab_title}")
    print(f"       Architect...", end="", flush=True)
    t0 = time.time()
    closing = call_llm(architect_prompt(bab_num, bab_title, None, None, None, rolling_summary, is_closing=True, jenis=jenis), max_tokens=2000, timeout=90)
    t1 = time.time()
    print(f" {t1-t0:.1f}s ({word_count(closing)} kata)")
    closing = post_process(closing, jenis=jenis)
    return closing

def generate_bab(bab_num, bab_data, prev_summary, jenis="umum"):
    """Generate 1 bab lengkap: intro + sub-bab + penutup."""
    bab_title = bab_data["title"]
    subs = bab_data["subs"]
    print(f"\n{'='*60}")
    print(f"BAB {bab_num}: {bab_title}")
    print(f"{'='*60}")

    # Intro
    intro = generate_intro(bab_num, bab_title, prev_summary, jenis=jenis)

    # Rolling summary untuk sub-bab
    rolling = intro[:500]  # start with intro as context
    bab_parts = [f"## BAB {bab_num}. {bab_title}\n\n{intro}\n"]
    #  📌 Ringkasan tiap sub-bab DIKUMPULKAN di sini. Dipakai untuk menyusun
    #  ringkasan bab TANPA memanggil AI lagi (ACC Bos 19 Okt 2026).
    ringkasan_subs = []

    for sub_num, sub_title, key_points in subs:
        final, summary, wc, cit = generate_sub_bab(
            bab_num, bab_title, sub_num, sub_title, key_points, rolling,
            jenis=jenis
        )
        bab_parts.append(f"\n### {sub_num} {sub_title}\n\n{final}\n")
        rolling = summary  # next sub gets this summary
        if summary:
            ringkasan_subs.append((sub_num, sub_title, summary.strip()))

    # Penutup
    closing = generate_closing(bab_num, bab_title, rolling, jenis=jenis)
    bab_parts.append(f"\n{closing}\n")

    # Gabung bab
    bab_text = '\n'.join(bab_parts)

    # Simpan ke file
    bab_file = os.path.join(folder_ini(str(OUT_DIR)), f"bab{bab_num}.txt")
    with open(bab_file, 'w') as f:
        f.write(bab_text)

    # === ONE-PASS: Auto-generate semua visual untuk bab ini ===
    #  ⚠️ URUTAN PENTING: ringkasan bab dihitung DULU. Ilustrasi memakai ringkasan
    #  itu sebagai bahan brief (putusan Bos 18 Okt 2026) — kalau visual dibuat
    #  lebih dulu, brief jatuh kembali ke label topik (wallpaper generik).
    #
    #  🚨 DIPERBAIKI 19 Okt 2026 (ACC Bos, Langkah 1 "optimalisasi"):
    #  DULU: `bab_summary = call_llm(summarize_prompt(bab_text[:5000]))`
    #        = panggilan AI KELIMA yang MERINGKAS ULANG dari teks mentah,
    #        padahal tiap sub-bab SUDAH punya ringkasan sendiri (`summary`).
    #        Akibatnya: (a) ±8 detik terbuang per bab, (b) DUA ringkasan
    #        BAB yang BERBEDA beredar — ringkasan sub-bab dipakai penulis
    #        sebagai `rolling`, ringkasan bab dipakai pembuat brief gambar.
    #        Kalau keduanya tidak sinkron, ilustrasi bisa bercerita lain
    #        dari alur bab.
    #  SEKARANG: ringkasan bab DISUSUN dari ringkasan sub-bab yang sudah ada
    #        ⇒ NOL panggilan AI, dan PASTI konsisten dengan alur penulisan.
    #        Kalau ringkasan sub-bab tidak ada (mesin gagal), JANGAN mengarang:
    #        turun ke ringkasan lama (satu panggilan AI) sebagai cadangan.
    if ringkasan_subs:
        bab_summary = '\n'.join(
            f'{sub}: {ringkas}' for sub, _judul, ringkas in ringkasan_subs)
        print(f"       [RINGKASAN] disusun dari {len(ringkasan_subs)} ringkasan "
              f"sub-bab — 0 panggilan AI")
    else:
        print("       [RINGKASAN] ringkasan sub-bab kosong → cadangan 1 panggilan AI")
        bab_summary = call_llm(summarize_prompt(bab_text[:5000]),
                               max_tokens=2500, timeout=90)

    generate_bab_visuals(bab_num, bab_title, bab_text, ringkasan_bab=bab_summary or "")

    # Simpan referensi bab ini (dari semua sub-bab) untuk daftar pustaka
    bab_refs_path = os.path.join(visual_ini(), f"refs_bab{bab_num}.json")
    # refs sudah disimpan per sub-bab di generate_sub_bab, tapi simpan juga di level bab
    # untuk assembly

    wc_total = word_count(bab_text)
    cit_total = count_citations(bab_text)
    print(f"\n✅ BAB {bab_num} selesai: {wc_total} kata, {cit_total} sitasi")
    print(f"   File: {bab_file}")

    return bab_text, bab_summary, wc_total, cit_total

def main():
    mode = "--resume" if "--resume" in sys.argv else "--fresh"

    if mode == "--fresh" and os.path.exists(CKPT_FILE):
        os.remove(CKPT_FILE)
        print("🗑️ Checkpoint lama dihapus (--fresh)")

    ckpt = load_checkpoint()
    if "babs" not in ckpt:
        ckpt["babs"] = {}

    all_summary = ""
    total_wc = 0
    total_cit = 0
    total_t0 = time.time()

    for bab_num in sorted(OUTLINE.keys()):
        bab_key = str(bab_num)

        if bab_key in ckpt["babs"] and ckpt["babs"][bab_key].get("status") == "done":
            print(f"\n⏭️ BAB {bab_num} sudah selesai, skip")
            all_summary = ckpt["babs"][bab_key].get("summary", "")
            total_wc += ckpt["babs"][bab_key].get("words", 0)
            total_cit += ckpt["babs"][bab_key].get("citations", 0)
            continue

        bab_data = OUTLINE[bab_num]
        bab_text, bab_summary, wc, cit = generate_bab(bab_num, bab_data, all_summary)

        ckpt["babs"][bab_key] = {
            "status": "done",
            "title": bab_data["title"],
            "words": wc,
            "citations": cit,
            "summary": bab_summary,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file": f"bab{bab_num}.txt"
        }
        save_checkpoint(ckpt)

        all_summary = bab_summary
        total_wc += wc
        total_cit += cit

    total_t1 = time.time()
    elapsed = total_t1 - total_t0

    print(f"\n{'='*60}")
    print(f"PIPELINE SELESAI")
    print(f"{'='*60}")
    print(f"Total bab: {len(OUTLINE)}")
    print(f"Total kata: {total_wc:,}")
    print(f"Total sitasi: {total_cit}")
    print(f"Waktu: {elapsed:.0f}s ({elapsed/60:.1f} menit)")
    print(f"Rata-rata: {elapsed/len(OUTLINE):.0f}s/bab")

    # Simpan referensi & glosarium
    with open(os.path.join(folder_ini(str(OUT_DIR)), "references.txt"), 'w') as f:
        for ref in REFERENCES:
            f.write(ref + "\n")
    with open(os.path.join(folder_ini(str(OUT_DIR)), "glosarium.json"), 'w') as f:
        json.dump(GLOSARIUM, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
