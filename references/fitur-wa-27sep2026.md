# Fitur WA EduAi (GOWA) — 27Sep26, LIVE & TERBUKTI

## Konfigurasi PATEN (keputusan Bos)
- PENGIRIM: GOWA `gowa` port 3000, device `eduai-wa-8514`,
  nomor `6285178138516` — TERBUKTI kirim (WA Bos terima).
- Alarm fallback → `6285720505555` (WA pribadi Bos).
- DILARANG: `UPB_WA_BLAST` (port 3001) & slot `OJS Tridarma.id`.
- Konfigurasi `app/config.py` akhir: `EDUAI_GOWA_URL/_AUTH/_DEVICE`
  + `EDUAI_WA_ADMIN` (bisa dioverride .env).

## 3 pemicu (hanya yang penting)
1. Pembelian token — jangkar `notifikasi.catat()`: WA otomatis utk jenis
   `pembayaran_*` (+`pembimbing_diundang`), isi = judul+isi lonceng
   (sudah lembut). Switch `pembelian` per user (default ON).
2. Undangan pembimbing — `pembimbing.buat_bimbingan()`: nama mahasiswa +
   judul + link `{BASE_PUBLIK}/tinjau/{token}` (TANPA login, berlaku
   `hari` hari). Switch `undangan` per user (default ON).
3. Alarm fallback AI — `ai.py` setelah `_panggil_openrouter` sukses:
   model asli + durasi + sebab, TANPA switch, langsung `alarm_admin()`.
- Revisi mahasiswa/pembimbing: TIDAK per kejadian; switch `revisi`
  default OFF.

## Arsip kode
- `app/wa.py`: `kirim()` (parser di dalam, gagal ditelan+log),
  `kirim_user()` (switch + `setelan_wa.wa`), `alarm_admin()`,
  `setelan()/atur()`. Tabel `setelan_wa` (user_id, wa, pembelian,
  undangan, revisi) dibuat idempoten. Sumber nomor = `setelan_wa.wa`.
- Parser nomor SATU SUMBER = `pembimbing.bersihkan_wa()`:
  `+62/08/62/8...`, spasi/strip/titik/kurung, `wa.me/...`,
  buang `0` sisa kode area (`+62 (0) 812...` → `62812...`),
  <8 digit / tanpa digit → `''` = kirim BATAL (jangan menebak).

## Bukti (27Sep26)
- `scripts/uji_parsing_nomor.py` → 16 LULUS / 0 BEDA.
- `scripts/uji_wa_e2e.py` → 8 LULUS / 0 GAGAL (switch default, revisi
  on/off, pembelian via kirim_user, OFF memblok, undangan format-jelek,
  alarm fallback, nomor tak sah batal).
- WA nyata masuk HP Bos dari 3 format (+62 / 08 / 62 spasi-strip).
- `notifikasi.catat('pembayaran_masuk')` → WA otomatis terkirim.
- Deploy `jalankan.sh` ✅ health 200; backup DB `_arsip/pra-sot/`.

## Pelajaran pair GOWA (penting di lain waktu)
- Pair code expired ±60 dtk; 1 kode 1× per nomor — generate ulang
  SEBELUM sesi mati → `session deleted` + WhatsApp `missing element`.
- Device ID dgn slash (`.../log`) tak terjangkau API v9.2.2 → ID polos.
- Buat device di build ini: `POST /devices` (bukan /api/devices).

## BELUM (antrean)
- Halaman setelan WA (toggle + isi nomor) di dashboard mahasiswa.
- Alarm fallback via domain belum dipicu (jalur 1 sehat; jangkar kode
  masuk + `alarm_admin()` terbukti terkirim).
