# Kwitansi review BAB IV Fase 4 — 21 Okt 2026 (petang)

Lanjutan dari `kwitansi-review-bab4-fase3-r8-r9-dan-merge-21okt2026.md`.
Sesi ini: **merge Fase 3 selesai**, lalu Bos menunjuk **Fase 4 sudah ada** di
kedua repo.

---

## 1. Posisi branch saat Fase 4 muncul

```
eduai-publishing
  cb36678  akhir Fase 3
     ├── 3ca2f2d  merge Fase 3 → main
     ├── ef402e2  catatan vonis Fase 3 (§15d) → main        ← main = ef402e2
     └── 0c71143  Fase 4 (bercabang dari cb36678, LEWAT dua commit di atas)

statistik-lab
  629c4ab  master (Fase 1)
     ├── 06cf13d  Fase 3 sisa: pintu simulasi BUAT DATA
     └── 59df57b  Fase 4: pintu kualitatif (koding + matriks)
```

⚠️ `statistik-lab` **tidak** ketinggalan `master` (aman). `eduai-publishing`
**ketinggalan** ⇒ bug §4t-3.

---

## 2. Eksekusi merge Fase 3 (dilakukan di sesi ini)

| Langkah | Hasil |
|---|---|
| Catatan vonis (`8342ff1`) | di branch `agen/wulan/review-lulus-fase3` |
| Merge dari `origin/main` (`3810854`) + branch kode | `3ca2f2d`, 10 berkas, +2077 −3 |
| Cherry-pick catatan | **konflik** — `main` sudah punya §15c (Fase 2), commit baru juga §15c (Fase 3) |
| Penyelesaian | Fase 2 tetap **§15c**, Fase 3 naik jadi **§15d**; penanda `<<<<<<<`/`=======`/`>>>>>>>` = 0 |
| HEAD akhir | **`ef402e2`**, ter-push ke `main` |
| Verifikasi | clone baru `/tmp/_verif_fase3`: `bab4.py` 40.235 B, `bab4_narasi.py`, `bab4_rute.py`, `bab4.html` 10.172 B, 2 berkas uji; §15c=1, §15d=1; `main.py:116-118` memasang `router` + `router_layar` |
| Uji di clone baru | `uji_bab4_fase3.py` + `uji_bab4_fase3_sisa.py` **SEMUA LULUS** |

⚠️ `periksa_kode.sh` **MERAH di clone baru** padahal HIJAU di repo kerja →
**lingkungan uji**, bukan kode (lihat jebakan #45). Jangan simpulkan "main rusak".

---

## 3. Fase 4 — apa yang dibangun (belum direview penuh)

### `statistik-lab` `59df57b` (+368 baris)
- `app/jembatan.py` +254 — 2 rute: `POST /api/jembatan/kualitatif/koding`,
  `POST /api/jembatan/kualitatif/matriks`
- `app/main.py` +50 — suntik `_panggil_ai_server` (pola saran yang sudah ada)
- `uji_jembatan_kualitatif.py` (baru, 66 baris)

**Hasil uji bawaan mereka:** SEMUA LULUS.
Temuan yang dikutip: `IFAS = 0.6*4+0.4*2 = 3.20`, `EFAS = 2.50`,
kuadran `x=+0.70 y=0.00 → I agresif`, angka rusak → 0 (bukan 500),
koding tanpa kunci → 401, catatan kosong → 400.
Regresi Fase 1 `uji_jembatan.py` **26/26 tetap LULUS**.

### `eduai-publishing` `0c71143` (+797 baris)
- `app/bab4_rute.py` +261 — 10 rute baru (total **27**)
- `app/bab4_narasi.py` +164 — narasi kualitatif + campuran
- `app/jembatan_statistik.py` +66 — 2 pintu baru
- `app/templates/bab4.html` +115 — layar kualitatif
- `uji_bab4_fase4.py` +167
- `app/bab4.py` +7 — `lo`/`hi` tambahan

**Rute baru:** `PUT/GET /kualitatif/catatan`, `POST /kualitatif/usulkan-koding`,
`PUT/GET /kualitatif/segmen`, `PUT/GET /kualitatif/faktor`,
`POST /kualitatif/matriks`, `POST /campuran/pendalaman`.

---

## 4. Hasil review Fase 4 `eduai-publishing`

### ✅ Terbukti BENAR (jangan diuji ulang)

| Kelompok | Hasil |
|---|---|
| Kebocoran antar-user **8 rute Fase 4** | **404 semua** (catatan, segmen, faktor, matriks, kunci, narasi, hasil, pendalaman) |
| Kunci kualitatif **tidak memakan** kunci kuantitatif | kuantitatif 409, kualitatif **tetap terkunci** |
| Kunci ganda kualitatif | **409** |
| Segmen kosong / bukan list / tema tanpa informan / informan angka | semuanya **bukan 5xx** |
| Kelompok SWOT aneh (`'X'`) | **422** |
| Matriks SWOT | IFAS 3.20, EFAS 2.50, kuadran I — angka mesin |
| GERBANG KERAS campuran: matriks tematik sebelum putaran 1 dikunci | **409** dengan pesan jelas; `pendalaman` juga 409 |
| AI hanya **mengusulkan**, tidak menyimpan | segmen tetap kosong sampai manusia sahkan |
| Narasi kualitatif 4.1–4.4 | lahir dari matriks terkunci, tanpa `None`, tanpa label dobel |
| Uji bawaan `uji_bab4_fase4.py` | SEMUA LULUS (9 kegagalan awal murni karena server lab masih versi Fase 3 → **404**) |

### 🐛 BUG sah — istilah tertukar (§4w)

Data uji: 3 informan, 1 teknik.
Mesin: `kuat: true, tertriangulasi: false, jumlah_teknik: 1`.
Narasi 4.3: *"…tergolong kuat; namun, tema tersebut baru didukung oleh **satu
jenis informan**."*

Dua salah: menyebut "satu" padahal 3 informan; memakai kata **informan** untuk
**teknik**. Wajib dibedakan: `jumlah_informan` → "informan",
`jumlah_teknik` → "teknik".

---

## 5. Gagal palsu Wulan sendiri (§4v) — 4 kejadian

| # | Gejala | Sebab |
|---|---|---|
| 1 | `peta/sahkan` 422 `fokus_kosong` | peta kualitatif pakai `fokus`/`informan` di akar, bukan `variabel` |
| 2 | `segmen` 422 "tidak punya teks" | bentuk wajib `teks/informan/teknik/jenis` per potongan, bukan `tema/kutipan` |
| 3 | narasi 500 `no attribute 'email'` | `SimpleNamespace(id=1)` di `dependency_overrides`; `kuota._saldo` baca `u.email`/`u.role` |
| 4 | narasi 403 BUTUH_UPGRADE | `u.token_saldo = 500` — kolom tak ada; isi lewat `kuota._saldo.masuk(db, u, 500, 'uji', ...)` |

📌 Suntingan `str.replace` pada probe **tidak selalu mendarat** — Wulan 2×
mengira sudah membetulkan probe padahal berkas di container masih versi lama.
Obat: **tulis ulang dari nol**, jangan tambal string.

---

## 6. Perintah lingkungan uji (terbukti jalan)

```bash
# server mesin (repo sebelah) — WAJIB --host 0.0.0.0
cd /tmp/_cek_statlab_remote
JEMBATAN_KUNCI_LAYANAN=kunci-e2e .venv/bin/python -m uvicorn app.main:app \
  --host 0.0.0.0 --port 8799
# container menjangkau lewat IP host di antarmuka docker
curl -s http://172.17.0.11:8799/api/jembatan/status
# {"layanan":"jembatan-eduai","ok":true,"kunci_terpasang":true}

# uji di container
docker exec -w /app \
  -e EDUAI_STATISTIK_URL=http://172.17.0.11:8799 \
  -e EDUAI_STATISTIK_KUNCI=kunci-e2e \
  -e EDUAI_SECRET_KEY=x -e EDUAI_ROUTER_KEY=x \
  eduai-app python3 uji_bab4_fase4.py
```

⚠️ Uji narasi memanggil AI nyata: 9router **401** (`API key required for remote
API access`) → fallback `tokenharbor/glm-5.3-flash` **120 dtk** per panggilan.
Bukan bug kode; catat sebagai lambat.

---

## 7. Yang masih terbuka saat sesi ditutup

1. **Fase 4 belum di-merge** di kedua repo.
2. **BUG istilah informan/teknik** belum diperbaiki agen.
3. **§15c/§15d diselamatkan** di branch `fase4-rapi` (`c71b780`, sudah di-push) —
   tapi **`main` belum menerimanya**; branch itu belum di-merge.
4. Langkah review yang belum jalan: **statistik-lab `59df57b`** penuh (baru uji
   bawaan + regresi), **campuran dua putaran ujung-ke-ujung** di EduAi.
5. Belum deploy; `JEMBATAN_KUNCI_LAYANAN` produksi belum dipasang (pintu 503).
6. `statistik-lab` `06cf13d` (pintu simulasi) belum masuk `master`.
