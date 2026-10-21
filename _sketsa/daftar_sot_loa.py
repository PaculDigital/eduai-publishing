"""Perbarui SOT.md: blok SESI TERAKHIR -> LoA + QR (17 Okt 2026)."""
import pathlib

f = pathlib.Path('/opt/data/services/eduai-publishing/SOT.md')
s = f.read_text(encoding='utf-8')

BLOK = '''## 🟢 SESI TERAKHIR (17 Okt 2026) — BACA INI, LALU BERHENTI

```
1. SOT_LOA_QR_17OKT2026.md      ← ⭐ LoA OTOMATIS + VERIFIKASI QR (LIVE, teruji)
2. PAGAR_MUTU_PETA_DAN_HEMAT_JEV_14OKT2026.md
3. CATATAN_SAMBUNGAN_CATATAN_PEMBIMBING_14OKT2026.md
```

**Yang SELESAI (17 Okt) — LoA OTOMATIS + QR VERIFIKASI ✅ LIVE:**
- **LoA dicetak EduAi sendiri** (OJS tidak punya berkas LoA). Editor "Terima" di
  Tridarma → user klik **"Unduh LoA"** di EduAi → **PDF 1 halaman** + tanda tangan
  asli + **QR verifikasi**. `app/loa.py` · `templates/loa/loa-jemt.html`
- **Halaman verifikasi publik** https://qr.tridarma.id — **KOP SAMA dengan LoA**
  (logo 64px, brand 30px, "Tridarma Journal Publishing", E-ISSN•Terbit•Web•Email
  1 baris tengah, accent bar 4px). Nomor asli ⇒ VALID; palsu ⇒ TIDAK DITEMUKAN.
- **3 SYARAT TERBIT:** status = Diterima · Volume + Nomor ada · WA `0851-7813-8514`.
  Kosong ⇒ LoA TIDAK terbit (pesan jelas). Status = **TOMBOL MANUAL**, bukan otomatis.
- **Ingress:** aturan **no.9** `qr.tridarma.id → localhost:8100`; wildcard
  `*.tridarma.id` (no.10) **TETAP UTUH**. Middleware `HOST_VERIFIKASI` di
  `app/main.py` ⇒ `/` di domain itu = halaman verifikasi, BUKAN beranda EduAi.
- **UJI: 11 LULUS / 0 GAGAL** (HP 390px, `_sketsa/uji_valid_hp.py`) —
  valid/palsu/lebar/overflow/galat JS. Diverifikasi MATA juga.
- **3 JEBAKAN TERUKUR:** ① `async async function` ⇒ SELURUH JS mati (WAJIB
  `node --check` sebelum deploy) ② `@app.middleware` HARUS tepat setelah
  `app = FastAPI(...)` ③ Chrome :9333 dipaksa `innerWidth=698` ⇒ uji HP WAJIB
  **Playwright** + verifikasi mata.
- **Jembatan OJS BENAR:** `https://tridarma.id/mcp` (bukan `ojs-ojs_web-1`,
  bukan `:9027` yang ternyata SSH).
- **Data uji `1.001` DIBERSIHKAN** (`_arsip/pre-bersih-loa-20261017_035810/`);
  `nomor_artikel` = 0 ⇒ LoA asli pertama = `1.001`.
- **SISA:** Tridarma `issues = 0` (belum ada Volume/Nomor ⇒ LoA artikel nyata
  belum bisa terbit) · `config.py EDUAI_WA_ADMIN` masih nomor lama ·
  tombol "Unduh LoA" belum diuji dengan akun + artikel Diterima sungguhan.

'''

lama = '## 🟢 SESI TERAKHIR (14 Okt 2026) — BACA INI, LALU BERHENTI'
assert lama in s, 'blok SESI TERAKHIR tidak ketemu'
s = s.replace(lama, BLOK + lama.replace('SESI TERAKHIR', 'SESI SEBELUMNYA (arsip)'), 1)

# perbarui tanggal
s = s.replace('> 🚩 **Terakhir diperbarui: 10 Okt 2026** (oleh Wulan, atas perintah Bos).',
              '> 🚩 **Terakhir diperbarui: 17 Okt 2026** (oleh Wulan, atas perintah Bos).')

f.write_text(s, encoding='utf-8')
print('✓ SOT.md diperbarui')
for i, b in enumerate(s.split('\n')[:20], 1):
    if b.startswith('## 🟢') or 'Terakhir diperbarui' in b:
        print(f'  {i}: {b[:85]}')
