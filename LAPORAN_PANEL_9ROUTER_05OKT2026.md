# 🚨 LAPORAN PANEL 9ROUTER — MODEL MATI DI COMBO "EduAi"
**Tanggal ukur:** 05 Okt 2026 · **Sumber:** `docker logs 9router --since 24h`
**Untuk:** Bos (membersihkan di panel 9router)

---

## AKAR NOTIF WA PALSU

Notif *"jalur 1 AI sedang bermasalah… cek saldo jalur cadangan"* muncul karena
**setiap permintaan GAGAL DULU di model #1**, lalu berpindah ke model #2.

```
[COMBO] Trying model 1/12: ds/deepseek-flash
⚠️  [AUTH] No credentials for deepseek
⚠️  [COMBO] Model ds/deepseek-flash failed, trying next {"status":404}
[COMBO] Trying model 2/12: inferhub/cb/deepseek-v4.1-flash
✅  [COMBO] Model inferhub/cb/deepseek-v4.1-flash succeeded
```

---

## HASIL UKUR 24 JAM

### ❌ MODEL MATI — urutan 1 (paling sering, WAJIB dibersihkan)
| Model | Gagal | Sebab |
|---|---|---|
| **`ds/deepseek-flash`** | **1.509×** | `[AUTH] No credentials for deepseek` (404) |

### ⚠️ MODEL MATI SESEKALI (2× masing-masing — koneksi putus-nyambung)
| Model |
|---|
| `inferhub/cp/cline-pass/deepseek-v4.1-flash` |
| `inferhub/cbcn/glm-5.3-flash` |
| `inferhub/cb/deepseek-v4.1-flash` |
| `inferhub/ali/deepseek-v4.1-flash` |
| `inferhub/ag/gemini-3.6-flash-high` |

### ✅ MODEL YANG BEKERJA
| Model | Sukses |
|---|---|
| `inferhub/cb/deepseek-v4.1-flash` | **1.556×** (100% dari yang berhasil) |

---

## 🎯 YANG DIMINTA KE BOS (di panel 9router)

1. **HAPUS / matikan `ds/deepseek-flash`** dari combo `EduAi` — dia model **#1**,
   jadi SEMUA permintaan mampir ke sana dulu dan gagal (1.509× / 24 jam).
   Setiap kegagalan = **2 round-trip terbuang** + waktu tambah.
2. Kalau bisa, **jadikan `inferhub/cb/deepseek-v4.1-flash` urutan #1** —
   dia 1.556× sukses, tidak pernah gagal.

**Catatan:** 9router SENDIRI **SEHAT** (1,3–2,2 dtk). Yang mati cuma **koneksi
kredensial `deepseek`** di dalam combo.

## 📌 SEBAB NOTIF WA (dua lapis — lapis 2 diperbaiki di app)
- **Lapis 1 (panel):** model #1 mati → selalu buang waktu (di atas)
- **Lapis 2 (app):** app vonis "jalur 1 mati" padahal hanya **1 model dari 12**
  yang gagal, dan 9router sudah otomatis pindah → lihat
  `DOKUMENTASI_NOTIF_WA_PRESISI_05OKT2026.md`
