# ✅ TAHAP 1 LANGKAH 3 — JEMBATAN KE MESIN + `bangun_isi()` TERIMA KIRIMAN (06 Okt 2026)

> Lanjutan izin Bos. Langkah 1 = kolom. Langkah 2 = modul `jurnal.py`.
> Langkah 3 = **sambung ke mesin pencari + `bangun_isi()` terima artikel kiriman**.

---

## ✅ SELESAI & TERUJI

### 1. `app/kerangka.py` — `bangun_isi()` sekarang TERIMA kiriman
**Perbaikan kecil yang sudah direncanakan** (parameter baru, default `None`):
```python
def bangun_isi(judul, bab='1', ..., maks_artikel=20,
               artikel_dipakai: list[dict] | None = None) -> dict:
```
```python
if artikel_dipakai:
    artikel = artikel_dipakai          # ← pakai kiriman, JANGAN cari ulang
    info = {..., 'dari_kiriman': True, 'per_sumber': {'AI + tambahan user': n}}
else:
    h = _pustaka.cari_semua(tema_kerja)   # ← perilaku LAMA persis
```
⇒ **Artikel manual user + artikel AI = SATU daftar** yang dipakai menulis bab.
⇒ Kalau **tidak ada kiriman → perilaku lama PERSIS** (tidak ada yang rusak).

### 2. Fungsi bantu baru `info_terverifikasi()` (`kerangka.py`)
Menghitung artikel yang lolos audit **saat datang dari kiriman** (karena
`pustaka.cari_semua()` tidak dijalankan) → **pagar P3 tetap jujur**.

### 3. `app/jurnal.py` — 5 fungsi jembatan ditambahkan
| Fungsi | Guna |
|---|---|
| `_bersihkan(a, asal)` | Ambil hanya kunci yang dikenal + tandai asal |
| `cari_untuk_bab(judul, bab, kk, maks)` | Panggil `pustaka.cari_semua()` + rapikan |
| `cari_dan_simpan(prof, bab, judul, kk)` | **Cek sidik → cari → simpan** (hemat) |
| `tambah_manual(prof, bab, artikel)` | Tambah manual + **pagar batas 8** + pesan hangat |
| `untuk_bangun_isi(data, bab)` | Bersihkan kunci internal → siap kirim ke `bangun_isi()` |

---

## 📊 BUKTI (bukan klaim)

| Bukti | Hasil |
|---|---|
| Gerbang `_gerbang_jurnal3.py` | ✅ **53 LULUS / 0 GAGAL** (EXIT 0) |
| Gerbang **BERGIGI** | ✅ kode dirusak → **8 GAGAL** |
| `/health` | ✅ 200 |

### ⭐ Bukti paling penting — artikel manual BENAR-BENAR terpakai
```
LULUS  K6b info menandai dari kiriman (pagar utama)
LULUS  K6c DOI kiriman ADA di artikel keluaran
LULUS  K6d jumlah artikel = 2 (kiriman saja, tidak tambah hasil mesin)
LULUS  K6e artikel HASIL MESIN tidak ikut masuk
LULUS  K6h daftar pustaka memuat manual
LULUS  K8a kiriman → mesin TIDAK dipanggil (0 kali)
LULUS  K8b tanpa kiriman → mesin DIPANGGIL
LULUS  K7b TIDAK ditandai dari_kiriman   ← perilaku lama utuh
LULUS  K7d balikan lama tetap utuh (kerangka ada)
```

### Bukti pagar batas 8 + pesan hangat
```
LULUS  K4e ke-9 DITOLAK
LULUS  K4f kode = batas_manual
LULUS  K4g pesan HANGAT (bukan "GAGAL/PERINGATAN")
LULUS  K4h pesan menyebut jumlah 8
LULUS  K4j bab lain masih boleh
```
Pesan yang keluar (ramah, tanpa kata keras):
> *"Kamu sudah menambahkan 8 artikel untuk bab ini. Bagian ini sudah cukup ya —
> sisanya dari pilihan EduAi supaya pembahasan tetap fokus."*

### Bukti hemat (tidak cari ulang)
```
LULUS  K3a sidik cocok → dari_simpanan
LULUS  K3b TIDAK cari ulang (0 panggilan mesin)
LULUS  K3d paksa=True → cari ulang
```

---

## 🚨 PELAJARAN PENTING (Wulan temukan & perbaiki sendiri)

**Uji Wulan GENERASI PERTAMA LEMAH — hampir meloloskan bug.**

Kejadian: Wulan rusak `bangun_isi` (abaikan kiriman) → gerbang **tetap 51 LULUS**.
Padahal seharusnya GAGAL. Wulan bedah sebabnya:

**Sebab:** asersi awal cuma memeriksa *"judul ada di daftar artikel"*. Saat
rusak, `bangun_isi` mencari sendiri lewat mesin → hasilnya artikel internet,
**dan salah satunya kebetulan relevan** → asersi lolos **palsu**.

**Perbaikan:** asersi diganti jadi **bergigi**:
- `info_cari['dari_kiriman'] is True` ← pagar utama
- DOI kiriman **harus ada** di keluaran
- jumlah artikel **= 2** (tidak ada tambahan dari mesin)
- `total_unik == 2`

**Bukti perbaikan berhasil:** kode rusak → **8 GAGAL** (bukan lagi 51 LULUS).

⇒ **ATURAN yang Wulan simpan:** *asersi "judul ada di daftar" TIDAK CUKUP —
harus periksa **sumbernya** (dari kiriman atau dari mesin).*

---

## ⚠️ CATATAN JUJUR

1. **Belum tersambung ke rute/UI** — fungsi tersedia, tapi belum ada halaman
   yang memanggilnya. Tab Referensi = langkah berikutnya.
2. **Belum deploy ke image produksi** — masih `docker cp`. Deploy menunggu izin Bos.
3. **Uji bergigi HARUS dijalankan di dalam container** (bukan host) — di host
   tidak ada `httpx` → ImportError. Wulan sempat gagal 2× karena ini.
4. **Scopus masih dilewati** (`kunci tidak ada`) — perilaku lama, bukan baru.

---

## 📋 STATUS
- [x] Langkah 1: kolom + migrasi ✅ (21/0)
- [x] Langkah 2: `app/jurnal.py` ✅ (59/0)
- [x] **Langkah 3: jembatan mesin + `bangun_isi` terima kiriman ✅ (53/0, bergigi 8 GAGAL)**
- [ ] Belum deploy ke image produksi (menunggu izin Bos)
- [ ] Langkah 4: pencarian manual + token + UI
