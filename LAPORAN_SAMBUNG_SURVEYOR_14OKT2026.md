<!-- SOT: LAPORAN_SAMBUNG_SURVEYOR_14OKT2026 -->

# ✅ SAMBUNG SURVEYOR JEV — TUNTAS (14 Okt 2026)

> **Perintah Bos:** *"A"* — putusan 4 poin (14 Okt):
> 1. *"Peta3_jev mengganti peta halus, sesuai uji dan keputusan 08/09 okt"*
> 2. *"Tidak ... saya uji dan [Jev] lebih akurat dan presisi dalam memetakan"*
> 3. *"Ya hakim, setelah jev memetakan, maka hakim untuk memperjelas dan
>    fokus sebelum mesin dan Ai bekerja"*
> 4. *"Peta halus dan kasar yang sebelumnya jangan di buang dan jadikan
>    fallback jika jev dan hakim mati"*

## STATUS: TAYANG

```
Image jalan : eduai-app:20261014_033725-sot   (deploy #12)
Deploy #11  : eduai-app:20261014_032859-sot
Mundur      : eduai-app:cadangan-pra-surveyor
Backup      : _arsip/pre-sambung-surveyor-20261014_031322/
/health     : 200 OK (3 detik)
```

---

## 1. YANG DIPASANG

### ① K5 DIMATIKAN (`app/hakim_peta.py`)
```
K5_AKTIF = False            ← saklar eksplisit
_q_per_kandidat()           → `criteria` HANYA dipasang kalau K5_AKTIF
AMBANG 0,60/0,30            → tinggal CATATAN (bukan saklar produksi)
teks CRITERIA_K5            → DIPERTAHANKAN (arkeologi, bukan dibuang)
```
**Bukti perilaku:** pertanyaan TIDAK bawa `criteria` (`criteria=False`) ✅
**Alasan:** vonis Bos — K5 terlalu detail, tak bisa global (ribuan naskah).

### ② SURVEYOR JEV = jalur pertama (Lapis 1 + 2)
| Berkas | Peran |
|---|---|
| `app/peta3_jev.py` | **PEMBUNGKAS** — memuat `peta3_jev.py` root via importlib (NOL salinan logika) |
| `Dockerfile` | `COPY peta3_jev.py ./peta3_jev.py` ← **akar lapis-1** (root dulu tak ikut image) |
| `app/peta_jalur.py` | fungsi MURNI `putuskan_jalur()` → `('jev'\|'fallback', alasan)` |
| `app/ai.py` (`/v1/peta/mulai`) | surveyor → `peta_jembatan.dari_surveyor` → hasil |
| `peta_halus` / jalur lama | **TETAP ADA** — fallback apa adanya (putusan #4) |
| `peta_dari` + `peta_alasan` | **JEJAK** di dua jalur |

**Aturan penting:** MATI ≠ RAGU. Ragu sebagian tetap `jev`.

---

## 2. 🔴 BUG NYATA YANG KETEMU (semua dari UJI PERILAKU)

### ① `section_id` KOSONG semua (130/130)
```
gabung    : {0: ('BAB I','PENDAHULUAN'), 211: ('BAB II',...)}
label bab : jatuh di baris 191-207 = DAFTAR ISI
⇒ baris 0 TIDAK masuk `pos` ⇒ BAB I hilang, 130 subbab tanpa nomor
FIX: `gabung` masuk `pos` + subbab tanpa nomor ikut bab induk (_bab_kini)
     `section_id` ambil elemen[0] saja (supaya = state.petakan)
HASIL: id kosong 0 · 'BAB I' → 'Latar Belakang' 10.620 kar ✅
```

### ② GERBANG JEMBATAN PALSU sejak awal
```
data uji  : 'gabung': {0: 'BAB I'}       (STRING)
produksi  : ('BAB I', 'PENDAHULUAN')     (TUPLE)
⇒ menguji bentuk yang TAK PERNAH ADA
FIX: data uji = tuple, boleh_dipakai_fitur = DICT → 17/0 (naik dari 16)
```

### ③ `ambil_json` — AttributeError setiap jalur AI peta
```
ai.py   : _p.ambil_json(jawab)
ada     : peta_halus._ambil_json   (GARIS BAWAH)
⇒ jalur AI peta SELALU gagal → diam-diam jatuh ke "peta cepat"
FIX: getattr(_p,'ambil_json',None) or getattr(_p,'_ambil_json',None)
Ketemu lewat uji E2E /v1/peta/mulai (bukan dicari sengaja).
```

### ④ GERBANG PALSU WULAN ×3 (kelas lama)
```
a) 2 suntikan cuma ubah PESAN (cek redundan) → suntikan WAJIB ubah JALUR
b) asersi cek Dockerfile DI DALAM container (tak ada) → cek dari HOST
```

---

## 3. GOYANG JEV — TERUKUR, BUKAN CACAT

```
pembungkus dijalankan 3× naskah SAMA (fid=81):
run   bab  subbab  paragraf  biasa  goyang
1      5     132      157     197      26
2      5     131      158     197      21
3      5     131      160     195      17
⇒ BAB = 5 STABIL 3/3 (dari `gabung`/kode)
⇒ subbab/goyang goyang = SIFAT JEV (dokumen: 130–138 antar-panggilan)
```
**Peljaran:** gunakan `p` (confidence) untuk tahu mana yang ragu — jangan
vonis cacat dari angka yang memang goyang.

---

## 4. GERBANG (semua di dalam container)

```
_gerbang_modul_peta3   10/0  (pembungkas setia + pagar P2)
_gerbang_jalur_peta    11/0  BERGIGI (2 suntikan tertangkap)
_gerbang_lapis2_peta   17/0  (impor, urutan, jejak, kunci lama)
_gerbang_ambil_json     4/0  BERGIGI
_gerbang_jembatan      17/0  (data uji diperbaiki)
_uji_perilaku_lapis2   11/0  (Jev nyata → 131 bagian)
_uji_e2e_peta           9/0  ★ PENENTU: panggil fungsi rute sungguhan
verifikasi pasca #11    8/8  · periksa_kode.sh LULUS
```

**Uji E2E bercerita:**
```
E1 fid=81 (asih.susanti) → jalur = jev (bab=5 sub=130) · 135 bagian
   id='b0' bab='BAB I' judul='BAB I' · section_id TERISI ✅
E2 fid tidak ada         → jalur = fallback · peta_halus tetap jalan ✅
```

**Jebakan uji:** pertama GAGAL 404 karena pakai user 9 padahal fid=81 milik
user 8 ⇒ **pagar keamanan bekerja**, ujinya yang salah user.

---

## 5. ⏳ BELUM (jujur)

```
❌ LAPIS 3 — hakim sebagai penilai (putusan Bos #3). Menunggu prasyarat:
      stitch U9 (satu penggaris) + baseline X (kill-switch) — sesuai dokumen
❌ LAPIS 4 — simpan ke `section_state` + kolom `mulai` (masih 0)
❌ LAPIS 5 — tombol/pintu di layar
❌ Potret layar untuk Bos
```

## 6. ARSIP

```
_arsip/uji-lapis2-peta-14okt/  (8 skrip uji/gigi)
_arsip/pre-sambung-surveyor-20261014_031322/  (ai.py, hakim_peta.py, peta3_jev.py, Dockerfile)
Gerbang tetap: _gerbang_jalur_peta.py · _gerbang_lapis2_peta.py
               _gerbang_ambil_json.py · _uji_e2e_peta.py
```
