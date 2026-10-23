# ♻️ Perbaikan yang Lahir Lagi + Container Uji Bocor — review branch Meja Kerja (21 Okt 2026)

Dua kelas bug yang muncul saat me-review commit `eef25a9` (Meja Kerja kualitatif,
repo `statistik-lab`). Keduanya **lolos semua uji status** dan **lolos uji bawaan
agen**.

---

## 1. BUG YANG SUDAH DIBUNUH, LAHIR LAGI DI FUNGSI BARU

### Kejadian terukur

| Waktu | Kejadian |
|---|---|
| `4668116` | Wulan memperbaiki pesan galat di `saranAI()`: periksa `content-type` BALASAN, beri sebab jujur untuk 502/503/504 |
| `eef25a9` | Agen menulis ulang Meja Kerja. Tombol AI per-kartu memakai fungsi **BARU** `mintaTeksAI()` |
| review | `mintaTeksAI()` **menyalin pola LAMA** ⇒ keluhan Bos ("kok muncul HTTP 502") kembali |

Isi fungsi baru yang bermasalah:

```js
async function mintaTeksAI(prompt) {
  const r = await fetch('/api/kualitatif/saran', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({prompt: prompt})            // ← bentuk juga tidak dikirim
  });
  const d = await r.json().catch(() => ({}));         // ← r.json() buta
  if (!r.ok || !d.boleh) throw new Error(d.sebab || ('HTTP ' + r.status));  // ← pesan polos
  return d.saran || '';
}
```

⇒ Dua cacat sekaligus: (a) galat HTML dari Cloudflare → `d = {}` → **"HTTP 502"**
tanpa sebab; (b) `bentuk` tidak dikirim → AI bebas menulis Markdown.

### Kenapa ini kelas bug, bukan kejadian tunggal

Setiap kali satu layar **ditulis ulang**, penulis baru cenderung menulis ulang
pembungkus fetch — dan menulisnya dari pola yang dia ingat, bukan dari yang
sudah diperbaiki. Satu endpoint dengan **N pembungkus** = **N tempat bug yang
sama bisa hidup**.

### Cara mendeteksi (1 menit, sebelum baca logika)

```bash
# 1. berapa pembungkus memanggil endpoint yang sama?
grep -n "fetch('/api/<modul>" app/templates/*.html

# 2. apakah SEMUA pembungkus memeriksa jenis BALASAN?
grep -n "r.headers.get('content-type')" app/templates/*.html

# 3. apakah SEMUA pembungkus mengirim parameter wajib?
grep -n "bentuk: bentuk" app/templates/*.html
```

Hasil terukur: `content-type` hanya **1×** (di `saranAI`), padahal ada **2**
pembungkus. Itu bukti bug sebelum menulis satu baris uji.

### Aturan review

- Perbaikan di **satu** pembungkus **bukan** perbaikan fitur. Yang diuji = **N pembungkus**.
- Gerbang wajib mengunci **setiap** pembungkus dengan asersi bernama
  (mis. `C1 mintaTeksAI mengirim bentuk`, `C2 bantuKodeAI memakai bentuk kartu`).
- Obat yang benar: **panggil jalur yang sudah ada** (`return saranAI(...)`) atau
  satu fungsi inti bersama — **jangan menyalin polanya**.
- Kalau terpaksa ditulis ulang: salin dari **fungsi yang sudah diperbaiki**,
  jangan dari ingatan.

### 🔥 Jebakan alat ukur yang menyertai bug ini

Uji versi pertama mencari kata `"content-type"` → **LULUS PALSU**, karena kata
itu ADA di header **KIRIMAN**:

```js
headers: {'Content-Type': 'application/json'}   // ← bukan pemeriksaan balasan
```

Yang benar: `"r.headers.get('content-type')"` (header BALASAN).

Uji versi kedua **terbalik** — menuntut bug masih ADA:

```python
cek('B2 pakai r.json() tanpa cadangan (bug)',
    'await r.json().catch' in minta and 'r.text()' not in minta)
```

⇒ **Uji harus menyatakan keadaan SEHAT, bukan keadaan RUSAK.** Tanda kena:
setelah diperbaiki, uji GAGAL.

### Uji bergigi (wajib)

```python
# kembalikan fungsi ke bentuk LAMA (bug) lalu jalankan gerbang
# sehat   → 16 LULUS / 0 GAGAL
# bug balik → 5 GAGAL (B1–B4, C1)
# pulihkan → 0 GAGAL
```

Tanpa langkah "kembalikan bug", gerbang hijau belum membuktikan apa pun.

---

## 2. CONTAINER UJI BOCOR SETELAH MERGE YANG MEMBAWA BERKAS BARU

### Gejala

```
curl http://127.0.0.1:8120/health   → 000
docker logs simulasi-olah-data      → ModuleNotFoundError: No module named 'app.jembatan'
                                       (dari app/main.py:1252, baris `from app.jembatan import ...`)
```

### Sebab

Merge membawa **berkas baru** (`app/jembatan.py`, `uji_jembatan.py`) tapi container
uji diisi dengan `docker cp` **satu berkas per berkas** dari hafalan. Berkas baru
tidak ikut ⇒ import gagal ⇒ uvicorn mati saat startup.

**Ini bukan bug kode.** Kode benar; yang kurang prasyarat.

### Urutan pemulihan

```bash
git show --stat <commit_merge>        # daftar berkas BARU (bukan hafalan)
docker cp app/jembatan.py <ctr>:/app/app/jembatan.py
docker restart <ctr>
sleep 15
docker exec <ctr> python3 -c "import urllib.request as u; \
  print(u.urlopen('http://127.0.0.1:8000/health').status)"   # cek DARI DALAM
```

⚠️ **`curl` dari host SELALU 000** untuk service yang listen `0.0.0.0:8000` di
dalam container (loopback container berbeda). Jangan simpulkan "server mati"
dari `curl` host — cek lewat `docker exec` atau `docker logs`.

### Aturan

Kalau merge menambah **berkas**, salin berdasarkan `git show --stat <merge>`,
bukan berdasarkan "berkas apa yang saya ingat berubah".

---

## 3. Ringkasan bukti sesi ini

| Pemeriksaan | Hasil |
|---|---|
| Konflik merge `main` (`cf9a98e`) → branch meja kerja | **1 konflik**, di tombol koding global yang **sengaja dihapus** di branch ⇒ ambil sisi branch |
| Perbaikan Wulan selamat setelah merge | `bentuk: bentuk` 1×, `content-type` 1× |
| `_gerbang_meja_kerja.py` sehat | **16 LULUS / 0 GAGAL** |
| uji bergigi | bug dikembalikan → **5 GAGAL** |
| `gerbang_sintaks_js.py` | LULUS |
| `sot.py --periksa` | SELARAS |
| `uji_jembatan.py` | SEMUA LULUS |
| Gerbang penuh | 63 grup LULUS |
| Push branch | `eef25a9..812d69b` → `agen/wulan/meja-kerja-baru` |
