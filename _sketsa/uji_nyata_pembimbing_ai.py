"""UJI NYATA PEMBIMBING AI — panggil model SUNGGUHAN, ukur waktu.

⚠️ WAJIB: ukur waktu + catat NAMA MODEL ASLI (aturan Bos). Kalau nama model
tidak bisa ditunjuk dari jejak → tarik klaimnya.

Dijalankan DI DALAM container. Memakai naskah NYATA dari DB produksi.
"""
import asyncio
import sys
import time

sys.path.insert(0, '/app')

from app import pembimbing_ai as PAI
from app.models import (SessionLocal, BerkasPembimbingan, Pembimbingan,
                        CatatanPembimbing, User)

print('=== UJI NYATA: naskah → model → catatan ===')

db = SessionLocal()
try:
    bk = db.query(BerkasPembimbingan).first()
    if bk is None:
        print('TIDAK ADA data uji → batal (jangan mengarang)')
        raise SystemExit(2)
    b = db.query(Pembimbingan).filter(Pembimbingan.id == bk.pembimbingan_id).one()
    print(f'berkas id={bk.id} judul={bk.judul!r} file_id={bk.file_id}')

    #  1. Baca naskah (mesin yang sama dengan halaman tinjau)
    teks = PAI._teks_naskah(db, bk)
    print(f'NASKAH: {len(teks)} karakter')
    if len(teks) < 200:
        print('naskah terlalu pendek untuk uji → batal')
        raise SystemExit(2)
    print('kutipan awal:', repr(teks.strip()[:110]))

    #  2. Susun prompt
    prompt = PAI.bangun_prompt('Mahasiswa Uji', bk.judul or '', teks)
    print(f'PROMPT: {len(prompt)} karakter')

    #  3. Panggil model (SATU PINTU, lewat ai._panggil_router)
    from app import ai as AI
    t0 = time.monotonic()
    try:
        jawab, info = asyncio.run(AI._panggil_router(
            prompt, 240.0, system=PAI.SYSTEM_PEMBIMBING))
    except Exception as e:
        dt = time.monotonic() - t0
        print(f'GAGAL PANGGIL MODEL setelah {dt:.1f} detik: {type(e).__name__}: {e}')
        raise SystemExit(3)
    dt = time.monotonic() - t0

    model = (info or {}).get('model') or (info or {}).get('model_asli') or '?'
    print()
    print(f'>>> SELESAI dalam {dt:.1f} detik')
    print(f'>>> MODEL ASLI: {model}')
    print(f'>>> INFO kunci: {list((info or {}).keys())}')
    print(f'>>> PANJANG JAWABAN: {len(jawab or "")}')

    #  4. Urai
    cat = PAI.urai_catatan(jawab)
    print(f'>>> CATATAN TERURAI: {len(cat)}')
    for i, c in enumerate(cat, 1):
        print(f'   {i}. [{c["bagian"]}] {c["soal"][:90]}')

    if not cat:
        print('JAWABAN MENTAH (120 kar pertama):', repr((jawab or '')[:120]))

    #  5. Perapkan (tanpa menyimpan — uji ini TIDAK mengubah data produksi)
    print()
    print('BENTUK CATATAN YANG AKAN MASUK:')
    for c in cat[:2]:
        print('---')
        print(PAI.rapikan_isi(c))

    #  6. Pastikan TIDAK ada catatan baru tertulis (uji tidak mengubah apa pun)
    n = (db.query(CatatanPembimbing)
         .filter(CatatanPembimbing.berkas_id == bk.id).count())
    print()
    print(f'jumlah catatan berkas ini di DB: {n} (uji TIDAK menambah apa pun)')
finally:
    db.close()
