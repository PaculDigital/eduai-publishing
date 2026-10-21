# 🏛️ LAPORAN SIMULASI SIDANG (L3+L4) — 04 Okt 2026

## HASIL DEPLOY

```text
Image LIVE   : eduai-app:20261004_143446-sot
Titik mundur : eduai-app:cadangan-pra-sot
Backup DB    : _arsip/pra-simulasi-deploy/20261004_143440/eduai.db
               (ab2e7449981afcdc6743940cea29700f · 24 tabel · 5 user · 27 berkas)
Backup berkas: _arsip/pre-simulasi-20261004/ (belajar.py · main.py · 2 template + MD5)
```

## APA YANG DIBANGUN — bentuk C (ACC Bos)

```text
/belajar/insight/{fid}?bab=N   ← halaman yang SUDAH ADA (tidak ada halaman baru)
  ├─ panel "Kesiapan Sidang kamu"     ← L4: skor + bar + per level
  ├─ PEMAHAMAN (L1)
  └─ 🏛️ BANK SOAL (L2)
       └─ tiap soal: tanya + kutipan + arah jawaban
            └─ L3: textarea "Tulis jawabanmu dengan kata sendiri"
                 → POST /belajar/uji/{fid}
                 → AI jadi PENGUJI → nilai 0-100
                 → kartu nilai: angka + "Yang sudah tepat" + "Yang bisa ditambah"
                 → tersimpan → panel skor naik · bisa "Jawab ulang"
```

## TITIP DI YANG SUDAH ADA (aturan Bos "jangan bikin baru")

| Kebutuhan | Yang dipakai (SUDAH ADA) |
|---|---|
| simpan jawaban + nilai | kolom `belajar_naskah.bab_selesai` (ada sejak awal, belum terpakai) |
| halaman | `/belajar/insight/{fid}` |
| bank soal | kolom `belajar_naskah.soal_json` (L2) |
| pola prompt/urai | `PROMPT_SOAL`/`_urai_soal` → `PROMPT_NILAI`/`_urai_nilai` |
| pagar hemat | cek simpanan dulu, AI hanya kalau belum ada |

**TIDAK ada tabel / kolom / halaman / dompet / jalur baru.**

## BERKAS

```text
app/belajar.py     : +PROMPT_NILAI · +_urai_nilai · +nilai_jawaban · +baca_uji ·
                     +skor_bab · +skor_naskah · +_isi_bab_selesai · +_tulis_bab_selesai
app/main.py        : +rute POST /belajar/uji/{fid} · +_hasil_uji() · kirim
                     `uji`+`skor`+`hasil` ke halaman
app/templates/belajar_insight.html : +panel Kesiapan Sidang · +form jawab ·
                     +kartu nilai · 14 kelas CSS BARU (nama baru, tidak bentrok)
_uji_simulasi.py   : 27 uji (root proyek, TIDAK ikut image)
_uji_klik_alur.py  : uji alur sungguhan DARI DALAM container
```

## UJI (SEMUA TERBUKTI)

```text
_uji_simulasi.py (AI nyata)          : 27 LULUS / 0 GAGAL
   · jawaban NGACO (cuaca/cabai)     → nilai 20
   · jawaban pakai isi naskah        → nilai 55
   · UJI BERGIGI: bagus > ngaco      ✅ TERBUKTI AI benar-benar menilai
   · skor_bab {terjawab:1,total:4,skor:55,per_level:{dasar:55}} ✅
   · skor_naskah (bahan pembimbing)  ✅
   · pagar: jawaban <5 huruf ditolak · soal_ke ngawur ditolak ✅
   · nada hangat: TIDAK ada kata salah/gagal/bodoh ✅
   · tidak merusak insight_json/soal_json ✅

_uji_klik_alur.py (alur sungguhan)   : BERHASIL
   · login form → /naskah 200
   · halaman belajar: 4 form jawab · panel Kesiapan ADA
   · kirim jawaban → 200 dalam 8,0 detik
   · BACA LAYAR: kartu nilai 1 · bulat 45 · lencana 45/100 · panel 45/100 ✅
   · AI menangkap jawaban yang MELESET ("yang ditanyakan kapabilitas adaptif,
     bukan digital readiness — keduanya berbeda") → nilai 45, JUJUR

Gerbang visual   : BERSIH (produksi / & /belajar)
periksa_kode.sh  : LULUS
Produksi         : / 200 · /masuk 200 · /belajar 303 · /kolaborasi 303
Data produksi    : 24 tabel · 5 user · 27 berkas UTUH
Berkas uji di image : 0 ✅
```

## 🚨 JEBAKAN BESAR (2× gagal, akar terukur) — CATATAN PENTING

```text
Browser CDP (host)  → port container (:8002/:8001/:8100) = ERR_CONNECTION_REFUSED
Container           → browser :9333                      = port tertutup (111)
⇒ DUA DUNIA TERPISAH. Tidak ada jalan silang.

Browser HANYA bisa : 127.0.0.1:8899 (http.server host /tmp/saji) + domain publik
Host TIDAK punya   : fastapi / uvicorn (server uji WAJIB di container)

✅ CARA BENAR uji alur interaktif: jalankan DARI DALAM container lewat
   form HTTP + cookie jar (`_uji_klik_alur.py`) — meniru persis browser:
   GET /masuk → POST /masuk → POST /belajar/uji/{fid} → ikut 303 → baca HTML.
✅ Potret MATA: sajikan HTML ke /tmp/saji/ → potret via http://127.0.0.1:8899/
```

**Jebakan kecil lain:**
```text
· `tab_baru(url)` TIDAK menavigasi → wajib Page.navigate
· `Tab.cmd(metode, params)` — bukan `expression=`
· `bersihkan_tab()` tidak menerima argumen
· DB uji /tmp/data_uji KOSONG (4096 B) sesudah `bash jalankan.sh`
  → jalankan ulang `_siapkan_data_uji.py`; cek ukuran >1 MB sebelum uji
```

## 🧭 STATUS 4 LAYER MODE BELAJAR

```text
L1 INSIGHT per BAB    ✅ LIVE
L2 BANK SOAL 4 level  ✅ LIVE
L3 SIMULASI SIDANG    ✅ LIVE (mahasiswa jawab → AI nilai → skor)
L4 SKOR PENGUASAAN    ✅ LIVE (panel "Kesiapan Sidang" + skor_naskah utk pembimbing)
```
