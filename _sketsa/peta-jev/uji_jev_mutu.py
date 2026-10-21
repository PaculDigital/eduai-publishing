"""UJI: JEV memeriksa MUTU naskah (rusak atau tidak) — berapa biaya & akurat?

Cara: kirim CONTOH baris (bukan naskah utuh — naskah utuh >64rb token = 502).
Tanya Jev tipe noul: "apakah baris ini potongan/terbelah?"

Ukur: waktu, token, dan apakah Jev BENAR memisah sehat vs rusak.
"""
from __future__ import annotations

import sys
import time

sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR   # noqa: E402
from app.models import FileBerkas                                 # noqa: E402
import app.state as S                                             # noqa: E402
from app import satpam                                            # noqa: E402


def contoh_baris(bersih: str, n: int = 24) -> list:
    """Ambil CONTOH baris menyebar (bukan semua) — hemat token."""
    baris = [x.strip() for x in bersih.split('\n') if x.strip()]
    if len(baris) <= n:
        return baris
    langkah = len(baris) / n
    return [baris[int(i * langkah)] for i in range(n)]


def tanya(teks_contoh: list) -> tuple:
    #  State: baris ber-ID (pola resmi — kode beri ID, Jev menilai)
    state = '\n'.join(f'L{i:04d}| {x[:160]}' for i, x in enumerate(teks_contoh))
    tanya = {}
    for i in range(len(teks_contoh)):
        tanya[f'L{i:04d}'] = {
            'instructions': ('Apakah baris ini POTONGAN teks — misalnya hanya '
                             'satu dua huruf, potongan kata, atau lanjutan '
                             'kalimat yang terbelah — sehingga BUKAN baris '
                             'naskah yang utuh?'),
            'type': 'noul',
        }
    t0 = time.time()
    try:
        hasil = satpam.tanya_bebas(state, [], tanya)
    except Exception as e:                                        # noqa: BLE001
        return None, time.time() - t0, str(e)[:140]
    return hasil, time.time() - t0, None


for fid, nama in ((81, 'Asih (SEHAT)'), (115, 'PDF (RUSAK)'),
                  (104, 'Disertasi (BEDA MASALAH)')):
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        bersih = S.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '')
    finally:
        db.close()

    c = contoh_baris(bersih, 24)
    hasil, dtk, err = tanya(c)
    print(f'── fid={fid} ({nama}) ──')
    if err:
        print(f'   GAGAL: {err}')
        continue
    nilai = []
    for k, v in (hasil or {}).items():
        try:
            nilai.append(float(v.get('noul') if isinstance(v, dict) else v))
        except (TypeError, ValueError):
            pass
    if not nilai:
        print('   hasil kosong:', hasil)
        continue
    tinggi = sum(1 for x in nilai if x >= 0.5)
    print(f'   waktu {dtk:.1f} dtk · {len(nilai)} baris dinilai')
    print(f'   rata-rata noul : {sum(nilai)/len(nilai):.2f}')
    print(f'   dianggap POTONGAN (>=0,5): {tinggi}/{len(nilai)} '
          f'({100*tinggi/len(nilai):.0f}%)')
    print()
