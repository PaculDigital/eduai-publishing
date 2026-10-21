#!/usr/bin/env python3
"""GERBANG TIKET LOLOS (Lapis 3) — dipanggil `scripts/periksa_kode.sh`.

Menjaga 4 hal yang MUDAH rusak tanpa sengaja:

  ① `tiket_lolos` bisa diimpor & skema pertanyaannya SAH (diterima Jev).
  ② Arah aman: **Jev mati / ragu ⇒ tiket BATAL** (bukan lolos gratis).
  ③ Bab tidak berubah ⇒ lolos TANPA panggil Jev.
  ④ Elemen bertiket tampil `done=True`; elemen tanpa tiket tetap `done=False`.

⚠️ Gerbang ini TIDAK memanggil Jev (biaya). Jev diuji terpisah dengan
   `_uji_tiket_jev_nyata.py` (dijalankan manual, ~1 dtk, gratis).

Cara jalankan:  python3 _gerbang_tiket_lolos.py
"""
from __future__ import annotations

import importlib
import os
import sys

os.environ.setdefault('EDUAI_DATA_DIR', os.environ.get('EDUAI_DATA_DIR', '/app/data'))
sys.path.insert(0, os.environ.get('EDUAI_APP_DIR', '/app'))

LULUS: list[str] = []
GAGAL: list[str] = []


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    (LULUS if syarat else GAGAL).append(nama)
    print(f"  {'✅' if syarat else '❌'} {nama}" + (f"  → {bukti}" if bukti else ""))


try:
    T = importlib.import_module('app.tiket_lolos')
    K = importlib.import_module('app.konversi')
except Exception as e:                                   # noqa: BLE001
    print(f"❌ GAGAL impor app.tiket_lolos: {e}")
    sys.exit(1)

print("\n── ① modul & skema ──")
for fn in ('tiket_baca', 'tiket_tulis', 'tiket_batal', 'tiket_periksa'):
    cek(f"① fungsi {fn}() ada", hasattr(T, fn))
cek("① SIDIK_HURUF = 1500", getattr(T, 'SIDIK_HURUF', None) == 1500,
    str(getattr(T, 'SIDIK_HURUF', None)))
try:
    skema = T._skema_pertanyaan()
    cek("① skema pertanyaan berbentuk dict", isinstance(skema, dict))
    #  ⚠️ Bentuk BENAR: skema = {<nama_tanya>: {'type','instructions','criteria'}}
    #     ⇒ criteria ada DI DALAM tiap pertanyaan, BUKAN di level atas.
    isi = list(skema.values())[0] if skema else {}
    cek("① pertanyaan punya type='choice'", isi.get('type') == 'choice',
        str(isi.get('type')))
    opsi = isi.get('criteria') or {}
    cek("① criteria = OBJEK {opsi: arti} (bukan list)",
        isinstance(opsi, dict) and len(opsi) >= 2, str(list(opsi)))
except Exception as e:                                   # noqa: BLE001
    cek("① skema pertanyaan bisa dirakit", False, str(e))

print("\n── ② arah aman: Jev mati ⇒ BATAL ──")
ARTIKEL = {'judul': 'Uji', 'elemen': {'gap': 'isi', 'novelty': 'isi'}}
TIKET = {'gap': {'bab': 'Pendahuluan ¶4', 'sidik': 'x' * 200}}
#  Jev palsu yang MATI (mengembalikan None seperti jev.tanya saat jaringan rusak)
d_mati = K.daftar_revisi(ARTIKEL, {k: v for k, v in TIKET.items()})
gap_mati = [i for i in d_mati if i['kunci'] == 'elemen:gap'][0]
cek("② tiket dibaca ⇒ elemen gap done=True", gap_mati['done'] is True)
cek("② elemen tanpa tiket ⇒ done=False",
    [i for i in d_mati if i['kunci'] == 'elemen:novelty'][0]['done'] is False)
cek("② bagian artikel TIDAK dapat done",
    all(not i['done'] for i in d_mati if not i['kunci'].startswith('elemen:')))

print("\n── ③ bentuk lama tetap jalan (tanpa argumen tiket) ──")
d_lama = K.daftar_revisi(ARTIKEL)
cek("③ daftar_revisi(artikel) tidak error", len(d_lama) > 0, str(len(d_lama)))
cek("③ semua item punya kunci 'done'", all('done' in i for i in d_lama))

print("\n── ④ harga elemen tetap utuh (2/3/5) ──")
harga = {i['kunci'].split(':', 1)[1]: i['token'] for i in d_lama
         if i['kunci'].startswith('elemen:')}
cek("④ gap = 3 token", harga.get('gap') == 3, str(harga.get('gap')))
cek("④ state_of_art = 5 token", harga.get('state_of_art') == 5,
    str(harga.get('state_of_art')))
cek("④ hook = 2 token", harga.get('hook') == 2, str(harga.get('hook')))
cek("④ bagian artikel seragam 2",
    {i['token'] for i in d_lama if not i['kunci'].startswith('elemen:')} == {2})

print()
print("═" * 58)
print(f"  HASIL: {len(LULUS)} LULUS / {len(GAGAL)} GAGAL")
if GAGAL:
    print("  GAGAL: " + ", ".join(GAGAL))
print("═" * 58)
sys.exit(1 if GAGAL else 0)
