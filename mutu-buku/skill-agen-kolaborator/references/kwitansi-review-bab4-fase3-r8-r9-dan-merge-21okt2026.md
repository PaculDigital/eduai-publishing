# Kwitansi Review BAB IV — 21 Okt 2026 (ronde 8–9, VONIS LULUS, catat + merge)

Penutup rantai `kwitansi-review-bab4-21okt2026.md` → `kwitansi-review-bab4-fase3-21okt2026.md`.
Sesi berakhir dengan **Fase 3 LULUS** dan **merge ke `main` = `ef402e2`**.

## Peta commit akhir (eduai-publishing)

```
cb36678  Ronde 9: spasi dobel pada kalimat rentang kepercayaan + uji anti-spasi-dobel
fdde753  Ronde 8: 4 cacat prosa (CI bootstrap, label, separator, None)
af576d4  Ronde 7: endpoint layar dibetulkan + gerbang kontrak layar↔rute
440160b  Ronde 6: layar bab4.html + narasi + simulasi nyata (3 endpoint 404)
702ab37  Ronde 5: GET /hasil, olah tahap simulasi, GET /profil
...      (lihat reference sebelumnya untuk ronde 1–4)
8342ff1  commit VONIS (branch agen/wulan/review-lulus-fase3)  ← WAJIB di-cherry-pick
3ca2f2d  merge --no-ff ke main-merge3
ef402e2  main  (merge + vonis §15c/§15d)  ← ter-push
```

`statistik-lab`: pintu simulasi `06cf13d` di branch `agen/wulan/jembatan-bab4`,
**belum merge ke `master`** (`master` tetap `629c4ab`).

## Ronde 8 (`fdde753`) — 4 cacat PROSA, satu di antaranya salah ilmiah

Uji bawaan hijau karena hanya memeriksa `200` + `'signifikan' in teks`.
Teks nyata yang keluar sebelum perbaikan:

```
- H3: pengaruh Harga terhadap Keputusan sebesar 0.0065 dengan nilai
  signifikansi — — hipotesis ditolak.
- H1: H1: b=-0.043379, p=0.605672 → tidak signifikan
- H3: H3: b=0.006458, p=None → tidak signifikan
```

| # | Cacat | Akar | Obat yang dipakai agen |
|---|---|---|---|
| 1 | label dobel `H1: H1:` | `susun_draf` menambah label, `ringkas` mesin sudah memuat | label dari satu sumber saja |
| 2 | `— —` dobel | nilai kosong diformat dua lapis | satu formatter |
| 3 | 🚨 **vonis "ditolak" untuk `p` yang TIDAK ADA** | efek tidak langsung dihitung **bootstrap** ⇒ mesin tak mengirim `p`; `None` diperlakukan "tidak signifikan" | pakai **`lo`/`hi` CI bootstrap** dari mesin: *"rentang kepercayaan 95% [-0.0170, 0.0327] melewati nol — hipotesis ditolak (berdasarkan uji bootstrap)"* |
| 4 | `p=None` tercetak | `str(None)` ikut | hilangkan baris / "tidak dapat dihitung" |

Hasil sesudah perbaikan (diverifikasi Wulan, angka cocok mesin):

```
H3: pengaruh tidak langsung Harga terhadap Keputusan sebesar 0.0065;
    rentang kepercayaan 95% [-0.0170, 0.0327] melewati nol —
    hipotesis ditolak (berdasarkan uji bootstrap).
```

`peta_hipotesis` sekarang membawa `lo`/`hi` — jadi CI-nya **dari mesin**, bukan
karangan penyusun prosa. Uji bawaan naik **46 → 51 asersi**.

⚠️ **Kalau `p` DAN CI dua-duanya tidak ada**, vonis wajib *"belum dapat
diambil"* — **bukan** "ditolak". Itu asersi ke-51 yang ditambahkan.

## Ronde 9 (`cb36678`) — spasi dobel + jebakan uji yang tidak bergigi

```diff
- f"{'tidak' if e.get('signifikan') else ''} melewati nol"
+ f"{'tidak ' if e.get('signifikan') else ''}melewati nol"
```

Benar: spasi **masuk ke dalam** potongan bersyarat. Dua keadaan terpenuhi —
`] melewati nol` (tidak signifikan) dan `] tidak melewati nol` (signifikan).

🚨 **Yang WAJIB dicatat dari ronde ini:** agen menambahkan baris uji
pendamping, tapi ekspresinya **selalu True**:

```python
cek('tidak ada spasi dobel', '  ' not in _teks.replace('  ', '  ', 0) or all(...))
#                                                    ^ hitungan 0 = TANPA perubahan
```

Kesan di laporan: "ada uji anti-spasi-dobel". Kenyataannya: bug bisa kembali
tanpa tertangkap. **Probe Wulan sendiri** yang menutupnya
(`'] melewati nol' in teks and ']  melewati' not in teks`).

⇒ **Aturan baru:** setiap asersi baru dari agen, pada ronde perbaikan,
diperlakukan sebagai **klaim**. Baca ekspresinya; suntik balik bug-nya; kalau
asersi tetap hijau → laporkan *"uji tidak bergigi"*, dan tulis probe sendiri.

## Hasil uji bergigi yang Wulan jalankan (`_g11.py`)

| Mutasi yang disuntik balik | Hasil |
|---|---|
| label dobel `H1: H1:` | **tertangkap** |
| cetak `None` | **tertangkap** |
| vonis paksa (`belum diputuskan` → `ditolak`) | **tertangkap** |
| hapus filter `jenis` di `kunci_hasil` (ronde 6) | **tertangkap** (kunci simulasi → 200) |

## Vonis & eksekusi catat+merge

Isi vonis ditulis sebagai **§15c/§15d** di
`DOKUMENTASI_BAB4_RANCANGAN_FINAL_21OKT2026.md`:
9 ronde · 34 bug · tabel temuan per ronde · bagian **uji mutasi** · bagian
**"yang belum (bukan bug)"**.

### Konflik yang muncul (dan cara menyelesaikannya)

`cherry-pick 8342ff1` **bentrok**: `main` sudah punya **§15c = vonis Fase 2**,
commit baru juga menulis **§15c = vonis Fase 3**.

Penanganan: **dua-duanya disimpan** — Fase 2 tetap §15c, Fase 3 dinomori
**§15d**. Penanda `<<<<<<<`/`=======`/`>>>>>>>` dihapus dengan skrip, bukan
`--ours/--theirs` (yang akan membuang salah satu vonis). Verifikasi:
`grep -c` penanda = 0 dan `grep -n 'VONIS REVIEW'` = **2 baris**.

### Verifikasi pasca-push (clone baru, bukan repo kerja)

```
HEAD                     ef402e2  ✅
app/bab4.py              40235 B  ✅
app/bab4_narasi.py        7189 B  ✅
app/bab4_rute.py         22034 B  ✅
app/templates/bab4.html  10172 B  ✅
uji_bab4_fase3.py        24596 B  ✅
uji_bab4_fase3_sisa.py    9648 B  ✅
§15c / §15d              1 / 1    ✅
main.py:116-118          import + include_router(router) + include_router(router_layar)  ✅
uji inti & uji sisa      SEMUA LULUS (dijalankan dari berkas clone baru)
```

### ⚠️ Gerbang MERAH di clone baru — BUKAN kerusakan `main`

`periksa_kode.sh` LULUS di repo kerja, tapi **GAGAL** di `/tmp/_verif_fase3`.
Dua sebab, dua-duanya bukan kode fitur:

| Pesan gerbang | Sebab sebenarnya |
|---|---|
| `IMPORT-GAGAL app.ai RuntimeError EDUAI_SECRET_KEY belum diset` (5 modul) | clone baru **tanpa `.env`** — lingkungan, bukan kode |
| `GAGAL B2 ada alat potret BARU` → daftar **48 `potret_*.py`** | gerbang "anti-bikin-baru" memindai `_sketsa/`, menuduh **alat lama** sebagai baru |

⇒ Sebelum melapor "gerbang gagal, jangan deploy": **baca pesannya**, klasifikasikan
(i) kode · (ii) lingkungan (env/berkas absen) · (iii) gerbang salah saring.
Laporkan apa adanya; **jangan** menyimpulkan `main` rusak.

## Yang BELUM setelah merge (bukan bug — jangan dikira jadi)

1. **BELUM DEPLOY** (`bash jalankan.sh`) — keputusan Bos.
2. **`JEMBATAN_KUNCI_LAYANAN` produksi belum dipasang** → pintu **503**.
3. **`statistik-lab` `06cf13d` belum merge ke `master`.**
4. Dua pintu kualitatif (§12: koding + triangulasi/SWOT) belum ada.
5. Draf narasi **tanpa batas baris** (12 generate = 12 baris; pola
   `VersiDokumen` maks 2) — dicatat untuk fase berikutnya.
6. Layar **belum diuji di HP** (mobile-first).
7. §10.2 waktu bayar campuran & §11.3 timeout masih terbuka.

## Sisa cacat kosmetik yang sengaja tidak menahan merge

Saat melapor BUG 1–4 ronde 8, Wulan juga menyebut **spasi dobel** dan
menegaskan *"bukan alasan menolak merge"* — lalu tetap diminta diperbaiki
ronde 9. Pelajaran: **pisahkan tegas** "wajib" vs "kosmetik" di laporan,
supaya Bos bisa memutuskan cepat tanpa membaca ulang seluruh temuan.

## Salah ukur Wulan di sesi ini (dicatat supaya tidak terulang)

| Klaim Wulan | Kenyataan |
|---|---|
| "13 endpoint yatim" | `r.path` router **sudah** memuat prefix; probe menempelkan prefix lagi |
| "angka `0.0119` bukan dari mesin" | itu **R²** (`hasil['r2']`) |
| "fuzz → 213 fungsi meledak" | salah saring; fungsi berat-`db` tak pernah dipanggil dengan data user |
