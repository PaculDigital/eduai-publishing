"""Penangkap C7 (28Sep26) — MODEL + ANGKA saat PIPA menolak revisi.

Masalah: saat PIPA menolak, app hanya mencatat "balasan tidak wajar" TANPA
nama model, tanpa panjang jawaban, tanpa rasio → mustahil menuduh model X.
Skrip ini memanggil jalur revisi ASLI (_revisi_kerja) dengan dua jaring:

  · ai._panggil_router  → model asli + jalur + durasi + token
  · pipa.periksa        → panjang jawaban/naskah + rasio tiap KUTIP/GANTI

Tanpa menyalin logika uji — hanya MENGINTIP. Backup DB sudah ada
(`scripts/backup_db.sh` 04:24 UTC).
"""
import asyncio
import time

import app.ai as ai
import app.pipa as pipa
from app.ai import _revisi_kerja, _RequestTiruan
from app.models import SessionLocal, User

FILE_ID = 65
KOMENTAR = ['Latar belakang terlalu pendek dan kurang jelas. '
            'Perdalam dengan teori dan data terbaru.']

CATAT: dict = {}
_router_asli = ai._panggil_router
_periksa_asli = pipa.periksa


async def router_tangkap(user_msg, timeout, system=None, gambar=None):
    t0 = time.monotonic()
    teks, info = await _router_asli(user_msg, timeout, system=system,
                                    gambar=gambar)
    dt = time.monotonic() - t0
    CATAT.update(model=info.get('model'), jalur=info.get('jalur'),
                 detik=dt, keluar=len(teks), masuk=len(user_msg),
                 token_in=info.get('token_in'), token_out=info.get('token_out'))
    print(f"  [AI ] model={info.get('model')} · jalur={info.get('jalur')} · "
          f"{dt:.1f} dtk · prompt={len(user_msg)} kar · "
          f"keluar={len(teks)} kar · in={info.get('token_in')} "
          f"out={info.get('token_out')}", flush=True)
    return teks, info


def periksa_tangkap(jawaban_ai, naskah, intent=''):
    print(f"  [PIP] jawaban={len(jawaban_ai)} kar · naskah={len(naskah)} kar · "
          f"intent={intent!r}", flush=True)
    try:
        _prof, editan, _cak, masalah = pipa.baca_bentukan(jawaban_ai)
        print(f"  [PIP] blok terbaca: {len(editan)} editan · "
              f"masalah bentuk: {masalah or '-'}", flush=True)
        for e in editan:
            rasio = len(e.ganti) / max(1, len(e.kutip))
            #  28Sep26 (Opsi 1): ukur juga terhadap PARAGRAF UTUH —
            #  itulah yang sebenarnya diganti rakit_presisi.
            _par = pipa.pisah_paragraf(naskah)
            _idx, _keadaan, _ = pipa.cari_paragraf(_par, e.kutip)
            dasar = len(_par[_idx[0]]) if _idx else 0
            rp = len(e.ganti) / max(1, dasar)
            print(f"        K{e.nomor}: kutip {len(e.kutip)} kar → "
                  f"ganti {len(e.ganti)} kar = {rasio:.2f}× (dasar KUTIP) · "
                  f"paragraf {dasar} kar = {rp:.2f}× "
                  f"(batas {pipa.PANJANG_MAKS_KALI}×) · cari={_keadaan}",
                  flush=True)
    except Exception as ex:                                    # noqa: BLE001
        print(f"  [PIP] gagal bedah bentuk: {type(ex).__name__}: {ex}",
              flush=True)
    hasil = _periksa_asli(jawaban_ai, naskah, intent)
    CATAT['pipa_ok'] = hasil.ok
    print(f"  [PIP] ok={hasil.ok} · pesan={hasil.pesan[:180]!r}", flush=True)
    return hasil


ai._panggil_router = router_tangkap
pipa.periksa = periksa_tangkap

db = SessionLocal()
u = db.query(User).filter(User.email == 'uji-berbayar-e2e@test.local').first()
assert u, 'user uji tidak ada'

print(f'== TANGKAP C7 · file {FILE_ID} · user {u.id} ==', flush=True)
t0 = time.monotonic()
try:
    hasil = asyncio.run(_revisi_kerja(
        _RequestTiruan({'file_id': FILE_ID, 'komentar': KOMENTAR}), u, db))
    print(f'== SELESAI {time.monotonic() - t0:.1f} dtk · ok={hasil.get("ok")} · '
          f'kode={hasil.get("kode")} ==', flush=True)
except Exception as e:                                         # noqa: BLE001
    print(f'== DITOLAK {time.monotonic() - t0:.1f} dtk · '
          f'{type(e).__name__}: {str(e)[:300]} ==', flush=True)

print('RINGKAS:', CATAT, flush=True)
