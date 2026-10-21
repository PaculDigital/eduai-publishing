#!/usr/bin/env python3
"""OPSI A (ACC Bos 29Sep26) — uji ON vs OFF langsung di PIPELINE app.

Cara: panggil `_revisi_kerja` ASLI dari dalam container — pagar ASLI
(`_valid` + `pipa.periksa`) ikut jalan — dengan satu-satunya perbedaan:
  · UJI_MODE=OFF → payload `enable_thinking: False` (SETINGAN PRODUKSI)
  · UJI_MODE=ON  → key `enable_thinking` DIHAPUS (perilaku LAMA pra-Opsi1)
Intercept di `httpx.AsyncClient.post` (kedua jalur app pakai itu).

⚠️ Pengembalian kuota di dalam `_revisi_kerja` SUDAH DIHAPUS (fix saldo
   dobel) & skrip ini memanggil TANPA penangkap pemanggil → kalau gagal,
   potongan dikompensasi manual di sini (user uji).

Jalankan DI DALAM container:
  docker exec -i -e UJI_MODE=OFF -e UJI_VAR=1 eduai-app python3 - < _sketsa/uji_on_off_pipeline.py
"""
import asyncio
import json
import os
import sys
import time

sys.path.insert(0, '/app')

MODE = os.getenv('UJI_MODE', 'OFF')          # OFF | ON
VAR = os.getenv('UJI_VAR', '1')              # varian komentar (anti-cache)
FID = int(os.getenv('UJI_FID', '70'))        # naskah T1 (skripsi 43rb kar)

import httpx                                     # noqa: E402
from app import ai as A                          # noqa: E402
from app.models import SessionLocal, User        # noqa: E402
from app import saldo as S                       # noqa: E402

# ── ambil kutip ASLI via PARSER APP yang sama (`_teks_dari_berkas`) ──
#  🔴 PELAJARAN (uji ini sendiri): kutip jangan dari regex kasar XML —
#     teks hasil re.sub MENYATUKAN paragraf ("jikadilakukan") padahal
#     naskah asli punya spasi → AI mengutip versi "normal" → pipa tolak
#     (kemungkinan besar akar 5/5 gagal komentar generik + kutip lama).
from app.models import FileBerkas                       # noqa: E402
from app.config import UPLOAD_DIR                       # noqa: E402

db0 = SessionLocal()
u = db0.get(User, 7)
fb = db0.get(FileBerkas, FID)
p = UPLOAD_DIR / str(u.id) / fb.nama_simpan
teks = A._teks_dari_berkas(p, fb.nama)
i = teks.find('Latar Belakang')
KUTIP = ' '.join(teks[i:i + 150].split())
#  bukti ke layar: kutip ini HARUS ada 100% di teks app
assert KUTIP in ' '.join(teks.split()), 'KUTIP tak cocok dgn naskah!'  # noqa: S101

VARIAN = {
    '1': [f'Catatan dosen untuk kalimat pembuka ini: "{KUTIP}" — terlalu umum '
          'dan tidak memuat data empiris terbaru; perdalam dengan angka '
          'prevalensi terkini serta referensi lima tahun terakhir.'],
    '2': [f'Rapikan kalimat ini: "{KUTIP}" — kalimatnya berbelit, subjeknya '
          'berulang, dan belum menyebut angka prevalensi terkini; sederhanakan '
          'tanpa mengubah makna dan tanpa mengurangi rujukan lima tahun '
          'terakhir.'],
    '3': [f'Perdalam bagian yang diawali kalimat "{KUTIP}" — terlalu normatif '
          'untuk skripsi; sisipkan data empiris lima tahun terakhir dan '
          'pastikan antarparagraf mengalir tanpa lompatan.'],
}
KOMENTAR = VARIAN.get(VAR, VARIAN['1'])

# ── INTERCEPT: satu-satunya perbedaan ON vs OFF ──────────────────────────
_asli_post = httpx.AsyncClient.post


async def post_timbun(self, url, *args, **kwargs):
    j = kwargs.get('json')
    if isinstance(j, dict) and 'enable_thinking' in j:
        if MODE == 'ON':
            j = dict(j)
            j.pop('enable_thinking', None)
            kwargs['json'] = j
        #  OFF: biarkan apa adanya (kode app sudah False)
    d = kwargs.get('data')
    if isinstance(d, (bytes, bytearray)) and b'enable_thinking' in d:
        if MODE == 'ON':
            t = d.decode('utf-8').replace('"enable_thinking": false', '')
            kwargs['data'] = t.encode('utf-8')
    return await _asli_post(self, url, *args, **kwargs)


httpx.AsyncClient.post = post_timbun


def saldo():
    try:
        with SessionLocal() as dbs:
            return S.sisa(dbs, u)
    except Exception:                                          # noqa: BLE001
        return None


async def jalankan():
    body = {'file_id': FID, 'komentar': KOMENTAR, 'setuju_bagian': True}
    sebelum = saldo()
    t0 = time.monotonic()
    hasil = {'mode': MODE, 'var': VAR, 'file_id': FID,
             'saldo_sebelum': sebelum}
    try:
        h = await A._revisi_kerja(A._RequestTiruan(body), u, db0)
        hasil['ok'] = True
        hasil['dt'] = round(time.monotonic() - t0, 1)
        hasil['token_in'] = h.get('token_in')
        hasil['token_out'] = h.get('token_out')
        hasil['token_revisi'] = h.get('token_revisi')
        hasil['model'] = h.get('model')
        hasil['kode'] = h.get('kode')
        hasil['jawaban_depan'] = (h.get('jawaban') or '')[:150]
    except Exception as e:                                      # noqa: BLE001
        hasil['ok'] = False
        hasil['dt'] = round(time.monotonic() - t0, 1)
        hasil['tipe'] = type(e).__name__
        pesan = getattr(getattr(e, 'detail', None), '__str__', lambda: '')()
        if not pesan:
            pesan = str(e)
        hasil['pesan'] = pesan[:400]
    time.sleep(1)
    sesudah = saldo()
    hasil['saldo_sesudah'] = sesudah
    #  kompensasi: skrip ini tanpa penangkap pemanggil (fix saldo dobel)
    #  → kalau gagal & potongan masih tersisa, kembalikan selisihnya.
    if not hasil['ok'] and sebelum is not None and sesudah is not None \
            and sesudah < sebelum:
        delta = sebelum - sesudah
        with SessionLocal() as dbk:
            uk = dbk.get(User, 7)
            S.masuk(dbk, uk, delta, 'uji',
                    f'kompensasi uji ON/OFF {MODE} var {VAR}')
            dbk.commit()
        hasil['dikompensasi'] = delta
        hasil['saldo_akhir'] = saldo()
    print(json.dumps(hasil, ensure_ascii=False, default=str))
    return 0 if hasil['ok'] else 1


sys.exit(asyncio.run(jalankan()))
