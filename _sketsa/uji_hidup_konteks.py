"""UJI SAMBUNGAN HIDUP — pakai AI NYATA lewat fungsi produksi.

Tujuan: membuktikan sambungan konteks BENAR-BENAR JALAN di jalur `ai.py`
(bukan hanya di uji terpisah). Dua jalan:
  A. sub-bab '1.2' (367 kar)  → harus PAKAI konteks tetangga
  B. 'BAB SELURUH'            → harus pakai jalur LAMA (naskah utuh)

Bukti diambil dari LOG server ([ai] konteks tetangga ...) + token NYATA.
"""
import asyncio, sys, os
sys.path.insert(0, '/app')

# muat env agar koneksi 9router & DB benar
from app.config import DATA_DIR, UPLOAD_DIR
from app.models import SessionLocal, User, FileBerkas
from app import ai as mod_ai
from fastapi import HTTPException


class LaporPalsu:
    def tahap(self, *a, **k): pass
    def menulis(self, *a, **k): pass


class BodyPalsu:
    def __init__(self, d): self._d = d
    async def json(self): return self._d


class ReqPalsu:
    def __init__(self, d): self._b = BodyPalsu(d)
    async def json(self): return await self._b.json()


async def jalankan(nama, payload):
    db = SessionLocal()
    try:
        u = db.query(User).filter(User.email == 'wulan@bikinaja.me').first()
        req = ReqPalsu(payload)
        print(f'\n══ {nama} ══')
        try:
            hasil = await mod_ai._revisi_kerja(req, u, db, _lapor=LaporPalsu())
            print(f'  ✅ selesai, kunci hasil: {sorted(hasil.keys())[:8]}')
            print(f'     token: {hasil.get("token_in",0):,} in / '
                  f'{hasil.get("token_out",0):,} out · '
                  f'{hasil.get("token_revisi","?")} Token Revisi')
            return hasil
        except HTTPException as e:
            print(f'  ⚠️ HTTPException {e.status_code}: {e.detail}')
        except Exception as e:
            print(f'  ❌ {type(e).__name__}: {e}')
    finally:
        db.close()


async def main():
    db = SessionLocal()
    fb = db.query(FileBerkas).filter(FileBerkas.user_id == 3).first()
    if not fb:
        print('tidak ada berkas milik admin — lewati uji hidup')
        db.close(); return
    naskah = mod_ai._teks_dari_berkas(
        UPLOAD_DIR / '3' / fb.nama_simpan, fb.nama).strip()
    print(f'berkas: {fb.nama} · {len(naskah):,} kar · file_id={fb.id}')
    fb_id = fb.id
    db.close()

    komentar = ['Perbaiki kalimat di bagian ini supaya lebih nyambung '
                'dengan latar belakang dan jelas maksudnya.']
    #  🚨 WAJIB pakai `file_id`, BUKAN `naskah` — ingatan (section_state)
    #     menempel pada BERKAS (`fb`). Kalau kirim `naskah` langsung, `fb=None`
    #     → pencatatan ingatan DILEWATI (terukur 24Sep26: revisi sukses tapi
    #     section_state tetap 0 baris).
    await jalankan('A. sub-bab + file_id (ingatan WAJIB tercatat)',
                   {'file_id': fb_id, 'bab': '1.2', 'komentar': komentar})


asyncio.run(main())
