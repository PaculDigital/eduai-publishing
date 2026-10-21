"""Daftarkan babak LoA di FLAG_LANJUT_DISINI.md (blok paling atas)."""
import pathlib, datetime

f = pathlib.Path('/opt/data/services/eduai-publishing/FLAG_LANJUT_DISINI.md')
s = f.read_text(encoding='utf-8')

BLOK = '''
### 📍 POSISI TERAKHIR (17 Okt 2026) — LoA OTOMATIS + VERIFIKASI QR ✅ LIVE

Image jalan: `eduai-app:20261017_*`  ← **LoA + QR VERIFIKASI**
Titik mundur: `eduai-app:cadangan-pra-sot`
SOT lengkap: **`SOT_LOA_QR_17OKT2026.md`** ← BACA INI DULU

**APA YANG JADI (semua TERUJI, 11 LULUS / 0 GAGAL di HP 390px):**
```
Editor "Terima" di Tridarma → user klik "Unduh LoA" di EduAi → PDF 1 halaman
   + QR ke https://qr.tridarma.id/verifikasi-loa?no=...
```

| Pintu | Isi |
|---|---|
| `app/loa.py` | mesin: cek syarat, 15 token, nomor urut, PDF, QR, `terbitkan()`, `cari_loa_nomor()` |
| `app/templates/loa/loa-jemt.html` | template LoA (kop, ttd, blok verifikasi+QR) |
| `app/templates/loa/verifikasi-loa.html` | halaman verifikasi publik (KOP SAMA dengan LoA) |
| `app/templates/loa/tanda-tangan.png` | ttd asli (ekstrak dari SVG Bayana) |
| `app/main.py` | `/verifikasi-loa` · `/api/loa/cek` · unduh LoA · **middleware domain** |
| `app/submit_jurnal.py` | `perbarui_status` simpan volume/nomor; `OJS_BRIDGE` dibetulkan |
| Cloudflare Tunnel | aturan **no.9** `qr.tridarma.id → localhost:8100` (wildcard no.10 UTUH) |

**3 JEBAKAN TERUKUR (JANGAN ULANG):**
1. **`async async function`** di verifikasi-loa.html ⇒ SELURUH JS mati ⇒ tombol diam.
   ⇒ WAJIB `node --check` isi `<script>` sebelum deploy.
2. **`@app.middleware` HARUS tepat setelah `app = FastAPI(...)`** — kalau di bawah,
   FastAPI menolak senyap ⇒ middleware tak terpasang ⇒ `qr.tridarma.id/` tampil beranda EduAi.
3. **Alat ukur menipu**: Chrome :9333 dipaksa `innerWidth=698` walau diminta 390.
   ⇒ UJI HP WAJIB **Playwright** + verifikasi MATA. JANGAN percaya Chrome 9333.

**JEMBATAN OJS — ALAMAT BENAR:** `https://tridarma.id/mcp`
(`ojs-ojs_web-1` = nama container internal ⇒ tak ketemu; `:9027` = SSH, BUKAN HTTP)

**SISA / BELUM:**
- Tridarma `issues = 0` ⇒ belum ada Volume/Nomor ⇒ LoA artikel NYATA belum bisa terbit.
- `app/config.py` `EDUAI_WA_ADMIN` masih nomor lama `6285720505555`.
- Tombol "Unduh LoA" belum diuji dengan akun user + artikel Diterima sungguhan.
- Data uji `1.001` SUDAH DIBERSIHKAN (cadangan `_arsip/pre-bersih-loa-20261017_035810/`).

**CARA UJI CEPAT:**
```bash
python3 _sketsa/uji_terbitkan30.py     # mesin (3 kasus, folder /tmp)
python3 _sketsa/uji_valid_hp.py        # halaman verifikasi HP (11 asersi)
curl -s "https://qr.tridarma.id/api/loa/cek?no=1.001"
```

'''

# sisipkan tepat setelah blok komentar riwayat
penanda = '<!-- Riwayat update: 16 Okt 2026 — UJI PLAGIARISME LIVE (tab ke-6, mode gratis) -->'
assert penanda in s
s = s.replace(penanda, penanda + '\n<!-- Riwayat update: 17 Okt 2026 — LoA OTOMATIS + QR VERIFIKASI LIVE -->', 1)

# sisipkan blok setelah "### 📍 POSISI TERAKHIR (16 Okt 2026)" ... cari judul pertama
idx = s.find('### 📍 POSISI TERAKHIR (16 Okt 2026)')
assert idx > 0, 'judul posisi terakhir tidak ketemu'
s = s[:idx] + BLOK.lstrip('\n') + '\n' + s[idx:]

f.write_text(s, encoding='utf-8')
print('✓ FLAG diperbarui')
for i, b in enumerate(s.split('\n')[:30], 1):
    if b.startswith('###') or b.startswith('Image jalan') or b.startswith('SOT lengkap'):
        print(f'  {i}: {b[:75]}')
