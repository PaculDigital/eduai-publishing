<!-- LAPORAN (RIWAYAT) — bukan SOT status -->
# 🌉 LAPORAN #1 — SURVEYOR MASUK APP (OPSI A: JEMBATAN)

> **Perintah Bos:** pilih **A** (09 Okt 2026) — *"Lakulan hati hati, karena ini paling pondasi."*
> **Putusan:** surveyor (`peta3_jev`) = **SUMBER** · jembatan = **PENERJEMAH**.
> **Berkas BARU:** `app/peta_jembatan.py` + `app/_gerbang_jembatan.py`.
> **Berkas LAMA disentuh: NOL** (✅ aturan Bos & pagar P1).

---

## 1. ⚠️ WULAN PERIKSA DULU — 4 TEMUAN SEBELUM SENTUH

Wulan **tidak langsung koding** (pondasi!). Hasil pemeriksaan:

### T1. Peta pemakai (terverifikasi `grep`)
```
state.petakan()  ← mesin REGEX, dipakai PRODUKSI di 5+ tempat:
    ai.py:1379,1411   (peta nol-AI Rp 0)
    ai.py:2348,2382   (bersama satpam)
    catatan_ai.py:69,71 · peta_halus.py:245 · versi.py:307,445 · konversi.py
peta3_jev.petakan() ← surveyor BARU ⇒ NOL pemakai
```

### T2. Bentuk keluaran BEDA (tak bisa tukar-emblek)
```
state.petakan   : teks → list[dict] {section_id, section_title, kategori, char_count, isi_teks}
peta3_jev       : fid  → dict       {baris, kand, label, gabung, p, sistematika, ...}
```
⇒ Kalau ditimpa ⇒ 5 pemakai rusak.

### T3. Pola jembatan SUDAH ADA di proyek
`app/konteks.py:134` — *"JEMBATAN: terjemahkan keluaran state.petakan() → bentuk konteks.py"*.
Catatan di berkas itu: **"KENAPA di sini (bukan di ai.py): aturan Bos — `app/ai.py`
DILARANG disentuh tanpa ACC."** ⇒ Wulan ikuti pola yang sama: jembatan di berkas TERPISAH.

### T4. 🚨 Harga kuota — WULAN HAMPIR SALAH SIMPUL
`state.petakan` docstring bilang: *"Ini yang dipakai jalur biaya kuota: 1 unit =
1 sub-bab ATAU 1 bab."* Uji nyata: LAMA 5 bagian → BARU **135 bagian** (27×).
Wulan **hampir** melaporkan "harga naik 27×".

**DICEK KE SUMBER — ternyata TIDAK. Harga TIDAK pakai peta:**
```python
def hitung_bagian(teks):                     # ai.py:168 — TITIK HARGA
    bagian = -(-len(teks) // AI_POTONG_KARAKTER)   # hitung KARAKTER!
```
⇒ Docstring `state.petakan` **USANG**. Risiko harga = **TIDAK NYATA**.
**Pelajaran:** Wulan hampir menyimpulkan dari DOCSTRING, bukan dari kode. Dicek → aman.

---

## 2. APA YANG DIBUAT

```
app/peta_jembatan.py   (BARU) — dari_surveyor(peta_surveyor, teks) → list[dict]
```

| Pagar | Isi |
|---|---|
| **P1** | Tidak mengubah `state.py` / `ai.py` / `peta3_jev.py` |
| **P2** | Surveyor gagal/mati ⇒ **`None`** ⇒ pemanggil KEMBALI KE CARA LAMA |
| **P3** | Keluaran bentuk **SAMA PERSIS** `state.petakan` |
| **P4** | Nomor dinormalkan lewat `state.title_for` / `get_category_for` (**impor**, bukan salin) |

**Pembuangan bagian curiga** (jangan menebak): pakai `boleh_dipakai_fitur` +
`sistematika` yang **sudah ada** di keluaran surveyor.

---

## 3. HASIL UJI NYATA (`fid=81` ASIH, jalur resmi, `<w:tab>`=0 ✅)

```
KUNCI lama : ['char_count','isi_teks','kategori','section_id','section_title']
KUNCI baru : ['char_count','isi_teks','kategori','section_id','section_title']
KUNCI IDENTIK: True ✅

LAMA (state.petakan) : 5 bagian  → BAB I..V   (21rb–57rb kar)
BARU (jembatan)      : 135 bagian → sub-bab   (294 kar–10rb kar)
```
⇒ Beda **memang disengaja**: lama 0 sub-bab (Asih tak bernomor `1.1`) ⇒ jatuh ke BAB.
Baru = **135 sub-bab dari Jev** — justru **tujuan Bos** (*"revisi jangan satu bab,
tapi bagian tertentu"*). Harga TIDAK terpengaruh (lihat T4).

---

## 4. ✅ VERIFIKASI

```
GERBANG JEMBATAN : 16 LULUS / 0 GAGAL · EXIT 0
UJI BERGIGI      : 15/1 · EXIT 1 ✅ TERTANGKAP (lepas pagar sistematika)
periksa_kode.sh  : ✅ LULUS
sot.py --periksa : ✅ SELARAS
md5 host==container ✅ (peta_jembatan b145954c · gerbang c739d919)
```

---

## 5. 🔻 YANG **BELUM** (jujur)

1. **Jembatan BELUM dipasang ke pemakai mana pun.** Uji dulu ⇒ sengaja.
2. **Putaran >1 belum diuji** (uji ini putaran=1).
3. **Naskah lain belum diuji** (Wulandari fid=115, Disertasi fid=104).
4. **`peta3_jev.py` masih di root `/app/`**, belum di `app/`.
5. **Keputusan pemasangan belum diambil:** siapa yang duluan pakai jembatan ini
   (versi.py / konteks.py / catatan_ai.py / peta_halus.py) — **wajib satu per satu**,
   karena 5 pemakai = 5 risiko terpisah. **JANGAN serentak.**

---

## 6. BERKAS

- `app/peta_jembatan.py` (BARU, md5 `b145954c…`) · `app/_gerbang_jembatan.py` (BARU, `c739d919…`)
- Pola acuan: `app/konteks.py:134` · Titik harga: `app/ai.py:168` `hitung_bagian()`
- Rancangan: `RANCANGAN_HAKIM_JEV_NAIK_KELAS_09OKT2026.md` §6
- Laporan terkait: `LAPORAN_S1_SURVEYOR_P_LABEL_09OKT2026.md`
