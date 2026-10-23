# JEBAKAN PROBE HTTP/CDP YANG MENELAN GALAT — DAN BUG MIDDLEWARE-COOKIE (22 Okt 2026, sesi 2)

Lanjutan `references/jebakan-review-branch-dan-uji-cdp-22okt2026.md` (J1–J10).
Sesi ini menghabiskan **±10 putaran** memperbaiki probe Wulan sendiri, sementara
kode yang direview **sehat**. Dua kelas baru yang wajib dikenali.

---

## K1. 🚨 `exceptionDetails` ADA DI BALASAN, BUKAN DI `result` — probe jadi BUTA

Helper CDP yang "kelihatan benar" tapi **tidak pernah mendeteksi galat JS**:

```python
r = tunggu(kirim('Runtime.evaluate', expression=e, returnByValue=True, awaitPromise=True))
j = r.get('result') or {}
if 'exceptionDetails' in j:            # ❌ SELALU False — kunci ini di r, bukan di j
    return {'GALAT': ...}
return j.get('result', {}).get('value')  # → None saat galat
```

Bentuk balasan yang **sebenarnya**:

```json
{ "id": 5, "result": { "result": { "type": "boolean", "value": true } } }
{ "id": 6, "result": { "result": { "type": "object", "value": [...] } } }
{ "id": 7, "result": { "exceptionDetails": {...}, "result": {"type":"undefined"} } }
```

⇒ Galat JS muncul sebagai `exceptionDetails` **sejajar** `result` di dalam
`r['result']`. Akibat kalau salah tempat: galat apa pun (mis. `ReferenceError:
el is not defined`) **lenyap** dan probe menerjemahkannya jadi `None` → dibaca
"GAGAL" → **menuduh kode orang lain**.

**Helper yang benar (pakai ini, jangan tulis ulang):**

```python
def js(e, batas=180):
    r = tunggu(kirim('Runtime.evaluate', expression=e,
                     returnByValue=True, awaitPromise=True), batas)
    if r is None:
        return {'TIMEOUT': True}
    # exceptionDetails bisa di dua tingkat — periksa KEDUANYA
    if 'exceptionDetails' in r:
        ex = (r.get('exceptionDetails') or {}).get('exception') or {}
        return {'GALAT': (ex.get('description') or str(r['exceptionDetails']))[:500]}
    hasil = r.get('result') or {}
    if 'exceptionDetails' in hasil:
        ex = hasil['exceptionDetails'].get('exception') or {}
        return {'GALAT': (ex.get('description') or '')[:500]}
    return hasil.get('value')
```

**Aturan induk:** kalau sebuah probe mengembalikan `None` **berulang kali tanpa
galat**, JANGAN menyalahkan aplikasi. Sebelum apa pun: jalankan
`Runtime.evaluate` **MENTAH** (`1+1`, `typeof el`, `location.href`) dan **cetak
JSON balasannya utuh**. Probe yang tidak bisa membedakan `None` dari galat
adalah probe buta.

---

## K2. 🚨 SKRIP PROBE RUSAK OLEH PATCH STRING `%` — cek jumlah placeholder DULU

Gejala menyesatkan: SKENARIO tampak ada di berkas, sintaks Python sah, tapi
eksekusinya mengembalikan `null`/`None` untuk **semua** skenario.

Sebab nyata: `SKENARIO` sudah **tidak punya** `%s` (pola patch lama salah
sasaran), tapi pemanggilnya masih `SKENARIO % (a, b, c, d)`. Python
**mengabaikan argumen berlebih**, jadi yang dieksekusi potongan lain yang
kebetulan berakhir tanpa `return`.

**Pemeriksaan 3 detik sebelum menjalankan skrip probe yang di-patch:**

```bash
python3 - <<'EOF'
src = open('<probe>.py', encoding='utf-8').read()
i = src.index('SKENARIO = '); j = src.index('"""', i + 12); k = src.index('"""', j + 3)
blok = src[j+3:k]
print('jumlah %s :', blok.count('%s'))
print('mulai     :', blok[:40].replace('\n', ' '))
print('akhir     :', blok[-40:].replace('\n', ' '))
EOF
```

Harapan: `jumlah %s` = jumlah argumen di pemanggil, blok **mulai** dengan
`(async () => {` dan **berakhir** dengan `})()`. Kalau tidak → tulis ulang
probe dari nol, **jangan** tambal lagi.

⚠️ **Jebakan pencari batas:** `src.index('"""')` bisa menangkap docstring
**berikutnya**, bukan penutup `SKENARIO`. Verifikasi dengan `grep -n` pada
berkasnya (`SKENARIO = """` harus sebaris dengan `(async`), atau hitung dari
nomor baris yang dibaca `read_file`.

📌 **Aturan induk:** probe yang sudah di-patch **2×** dan masih gagal →
**tulis ulang dari nol**. Menambal probe adalah sumber utama "Wulan lambat".

---

## K3. 🚨 TUNGGU "SIAP" ≠ TUNGGU DETIK TETAP (dan jangan percaya klaim siap pertama)

Halaman produksi bisa butuh **1,5 dtk** atau **7 dtk** tergantung waktu.
`time.sleep(5)` memang kadang cukup, kadang tidak — dan kalau tidak cukup,
**semua** asersi jadi `None` (GAGAL palsu).

```python
def tunggu_siap(batas=60):
    t0 = time.time()
    while time.time() - t0 < batas:
        if js("typeof el === 'function' && typeof KUAL === 'object' && "
              "!!el('<elemen-khas-halaman>')") is True:
            return round(time.time() - t0, 1)
        time.sleep(1)
    return False
```

⚠️ **Jangan percaya `siap=True` sendirian.** Terukur: satu probe melaporkan
"halaman siap setelah 0.1 dtk" lalu `typeof el` = `'undefined'` — artinya
evaluasi pertama tembak ke **konteks JS tab lama**. Sesudah `tunggu_siap()`
mengembalikan True, buktikan sekali lagi dengan probe mentah (`typeof el`,
`location.href`) dan bandingkan URL dengan yang dituju. Kalau URL beda atau
`el` masih `undefined` → tutup SEMUA tab (`GET /json/close/<id>`), buka tab
baru via `PUT /json/new?<url>`, ulangi.

---

## K4. 🔴 BUG MIDDLEWARE-COOKIE: identitas dibuat SESUDAH handler → request pertama selalu salah

**Bukan jebakan probe — ini bug kode NYATA, ditemukan karena probe HTTP polos.**
Terukur pada `dbc496f` (statistik-lab, "sesi anonim untuk unduhan").

Gejala:

```
POST /api/buat-data   (#1)  -> 200   (Set-Cookie sl_sesi=... dikirim)
GET  /api/unduh       (#2)  -> 404   {"detail":"Belum ada data. Buat dulu."}
POST /api/buat-data   (#2)  -> 200
GET  /api/unduh       (#2)  -> 200   ✅
```

Bukti di disk container:

```
/app/data/terakhir.pkl                              <- data PERTAMA (slot bersama)
/app/data/terakhir_<sesi>.pkl                       <- data KEDUA (slot sesi)
```

Akar, di middleware `http`:

```python
sesi = request.cookies.get('sl_sesi', '')
disajikan = bool(re.fullmatch(r'[a-f0-9]{32}', sesi or ''))
request.state.sesi = sesi if disajikan else None   # request #1 -> None
response = await call_next(request)                # handler menulis pakai None
if not disajikan:
    response.set_cookie('sl_sesi', uuid4().hex, ...)  # cookie BARU sesudahnya
```

⇒ Pada request pertama handler membaca `request.state.sesi = None`, menulis ke
**slot bersama**; request berikutnya sudah membawa cookie dan mencari
**slot sesi** yang belum pernah dibuat.

**Dampak user:** kunjungan pertama → buat data → klik unduh → "Belum ada data.
Buat dulu." Harus membuat **dua kali**. Lebih buruk daripada tanpa sesi
(dulu selalu berhasil, walau bisa tertukar).

**Obat (akar, bukan tambalan):** buat kode sesi **SEBELUM** handler.

```python
sesi = request.cookies.get('sl_sesi', '')
sah = bool(re.fullmatch(r'[a-f0-9]{32}', sesi or ''))
if not sah:
    sesi = uuid.uuid4().hex          # <- dibuat di sini
request.state.sesi = sesi            # handler SELALU dapat identitas
response = await call_next(request)
if not sah:
    response.set_cookie('sl_sesi', sesi, max_age=30*24*3600, path='/',
                        httponly=True, samesite='lax',
                        secure=(request.headers.get('x-forwarded-proto', request.url.scheme) == 'https'))
```

**Probe HTTP yang menangkap kelas ini** (tanpa browser, murah, satu berkas):

```python
jar = cj.CookieJar(); op = u.build_opener(u.HTTPCookieProcessor(jar))
post('/api/buat-data', {...})                 # #1
assert unduh() == 200, 'BUG: request pertama tidak menemukan datanya sendiri'
post('/api/buat-data', {...})                 # #2
assert unduh() == 200
```

📌 **Kelas umum:** setiap fitur yang mengikat data ke **identitas yang baru
dibuat pada request itu** wajib diuji dengan **klien yang belum punya
identitas**. Uji dengan klien yang sudah login/kunjungan kedua **tidak akan
pernah** menangkapnya — dan itulah kenapa bug ini lolos review pertama.

📌 Sesi juga wajib diuji **dua klien berbeda** (`CookieJar` terpisah) →
A dapat data A, B dapat data B, tidak tertukar.

---

## K5. 🔴 VIF/DIAGNOSTIK DIHITUNG TAPI TIDAK MASUK `masalah` → laporan "layak" menipu

Terukur `30b012f`: data dengan **X kembar sempurna** menghasilkan

```json
"vif": [{"nama":"X1","vif":1000000.0},{"nama":"X2","vif":1.0001},{"nama":"X3","vif":1000000.0}]
"masalah": [{"kode":"normalitas", ...}]      <- X1/X3 TIDAK muncul
"status_laporan": "belum"
```

Statistiknya **dihitung benar**, tapi pelanggaran berat (VIF ≫ 10) **tidak
didaftarkan sebagai masalah**, sehingga fitur "tunjukkan akibatnya" tidak punya
alasan untuk ditawarkan dan user tidak pernah diberi tahu X-nya kembar.

**Probe kelas ini (berlaku untuk semua laporan diagnosis):**

```python
# bangun data yang MELANGGAR satu syarat secara sengaja, lalu:
assert len(masalah) > 0, 'pelanggaran tidak masuk daftar masalah'
assert any(b['kode'] == 'vif' for b in masalah), 'VIF tinggi tidak dilaporkan'
```

**Aturan induk:** setiap **angka** yang dihitung mesin untuk diagnosis wajib
punya **pembaca** yang menaikkannya ke daftar masalah / vonis. Angka yang
dihitung tapi tidak dibaca = fitur hiasan (sepupu §4r/§4u di SKILL.md).

---

## K6. POLA PROBE HTTP FINAL YANG BERSIH (dipakai ulang)

Ciri yang membuat probe sesi ini akhirnya 12 LULUS / 2 gagal-palsu:

1. **Satu berkas probe = satu kelas uji**, dijalankan `python3 <probe>.py [BASE]`.
2. **Bentuk payload dibaca dari kode dulu**, bukan ditebak —
   `grep -n "payload.get(" app/main.py | head -20`. Terukur: Wulan menebak
   `{'x': ['Harga'], 'y': [...]}` padahal aslinya
   `{'n':.., 'x': <jumlah>, 'beta': [..], 'nama_x': [..], 'cara':..}` → HTTP 400
   yang mudah disalahartikan sebagai bug.
3. **Unggah berkas pakai multipart tulisan tangan** (tanpa `requests`), lalu
   **cetak semua kunci balasan** sebelum menulis asersi:

```python
st, up = unggah_csv(csv_teks)
print('kunci balasan:', sorted(up.keys()))     # jangan tebak nama kunci
kunci = up.get('kunci') or up.get('id') or ''
```

4. **Bentuk hasil divergen** — cek tipe sebelum asersi. Terukur: `vif` adalah
   **list of dict** (`[{'nama','vif'}]`), bukan dict; kunci pengecualian baris
   adalah **`pengecualian.baris`**, bukan `dikeluarkan`. Dua "GAGAL" sesi ini
   keduanya berasal dari asumsi bentuk yang salah.
5. **Bandingkan dua pemisah/kondisi** untuk membuktikan efek (`,` vs `;`,
   data sama vs data beda untuk sidik jari).
6. **Pagar negatif wajib**: kunci palsu → 4xx, kolom tidak ada → 4xx dengan
   pesan jujur. Tanpa ini, probe tidak membuktikan pagar apa pun.

---

## Ringkasan satu layar

| # | Jebakan | Tanda | Obat |
|---|---|---|---|
| K1 | `exceptionDetails` salah tempat | semua asersi `None`, tak ada galat | baca dari `r` DAN `r['result']`; probe mentah dulu |
| K2 | probe di-patch rusak (`%s` hilang) | `null`/`None` untuk semua skenario | hitung `%s`, cek blok mulai `(async` & tutup `})()`; tulis ulang dari nol |
| K3 | tunggu detik tetap / percaya `siap=True` | siap 0,1 dtk tapi `el` undefined | `tunggu_siap()` + buktikan probe mentah + tab bersih |
| K4 | identitas dibuat sesudah handler | request #1 404, #2 200 | buat identitas SEBELUM `call_next`; uji klien tanpa cookie |
| K5 | statistik dihitung tapi tak masuk `masalah` | VIF 1.000.000, `masalah` kosong utk vif | probe data yang sengaja melanggar satu syarat |
| K6 | payload ditebak | HTTP 400 berulang | `grep payload.get` + cetak kunci balasan |
