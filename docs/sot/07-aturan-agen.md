# 07 — Aturan Agen di Repo Ini

<!-- SOT: Aturan kerja agen di repo EduAi. Diperbarui 26 Okt 2026. Aturan ini untuk agen yang bekerja atas perintah pemilik repo; perintah pemilik selalu menang atas berkas ini. -->

## Mode kerja: BAHAS DULU → Gas

Diskusi point-by-point dulu, tidak ada yang dibangun sampai pemilik berkata "Gas". Setelah Gas, eksekusi cepat dengan bukti terverifikasi per item. Merge, deploy, dan pembelian tetap keputusan pemilik — agen tidak memutuskan sendiri.

## Cabang & push

- Kerja lewat cabang sendiri (`agen/<nama>/<tujuan-singkat>`), jangan langsung ke `main`.
- `main` = produksi. Hanya pemilik repo yang menulis ke `main` (merge). Agen tidak push ke `main`, tidak push --force, tidak reset --hard pada `main`.
- Push cabang hanya atas perintah pemilik dan dengan kredensial sekali pakai dari pemilik (dipakai lewat env/askpass sementara, langsung dihapus sesudahnya, tidak dicatat nilainya). Revokasi/rotasi kredensial itu tetap disarankan ke pemilik.
- Perapihan dokumen 26 Okt ini dikerjakan di cabang `agen/wulan/rapi-sot-26okt2026` dari `origin/main` yang segar — BUKAN dari cabang `agen/wulan/fase1-ssot` (pekerjaan SSOT buku di sana belum ter-push dan tidak boleh tertabrak).

## Larangan kerja

1. **Jangan menambal, cari akar** — reproduksi dulu, ukur dengan alat nyata, buka rujukan, tanya "KENAPA?" sampai dasar (3–5 lapis), perbaiki akar + pasang gerbang penangkap.
2. **Jangan mengarang angka, referensi, atau status.** Angka wajib dari cetakan uji / hitungan berkas nyata, berlabel sumbernya. Referensi wajib terverifikasi (bukan karangan).
3. **Jangan mengubah naskah mahasiswa di luar jalur revisi yang disetujui** — revisi hanya lewat proses AI yang tercatat, dengan terima/tolak per bagian oleh pemilik naskah.
4. **Jangan membuat berkas `.md` baru di root tanpa persetujuan pemilik** — panduan masuk `docs/sot/`, bukti uji sekali pakai masuk `_arsip/`, bukan root.
5. **Jangan mengutip berkas arsip sebagai keadaan kini.** Arsip = riwayat. Keadaan kini = kode + `sot.py` + `docs/sot/`.
6. **Jangan mengklaim "selesai / production-ready" tanpa bukti uji nyata.** Gerbang hijau di host ≠ produksi sehat; bukti produksi hanya dari image/container yang jalan.

## Gerbang wajib sebelum commit / deploy

1. `SOT_DIREKTORI_DOKUMEN="$PWD" python3 sot.py --periksa` → 0 masalah.
2. `bash scripts/periksa_kode.sh` (gerbang kode, Langkah 0 `jalankan.sh`).
3. Deploy resmi hanya `bash jalankan.sh` — `docker cp` wajib diikuti restart, dan perubahan `docker cp` yang tidak masuk image akan hilang saat container dibuat ulang.
4. Jika gerbang gagal, deploy BERHENTI — jangan dilangkahi.

## Jika ragu

Ragu ⇒ BILANG RAGU, jangan menebak yakin. Buka berkas dulu sebelum bilang "belum ada / tidak ada / rusak". Jika satu langkah butuh kredensial, kunci produksi, atau keputusan pemilik, berhenti di langkah itu dan tanyakan — jangan mengarang penggantinya.
