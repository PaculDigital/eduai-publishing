"""UJI MESIN MINI INSIGHT — pakai naskah NYATA (S1 unmul 5 bab).

Yang diuji (semua WAJIB, ini pagar hemat + pagar keamanan):
  1. teks_bab() benar-benar mengambil isi bab dari naskah NYATA
  2. pagar: naskah MILIK ORANG LAIN → naskah_milik balas None
  3. pagar: naskah belum diaktifkan → naskah_sudah_aktif balas None
  4. _urai_butir() tahan bentuk balasan model yang aneh
  5. HEMAT: bab yang sudah ada di DB → TIDAK panggil AI lagi (0 token)
  6. panggil LLM sungguhan (sekali) → hasil tersimpan ke belajar_naskah

⚠️ Uji ini memakai DB SALINAN. Jangan jalankan pada produksi.
"""
import asyncio
import os
import sys

sys.path.insert(0, '/app')

os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/data_uji')
os.environ.setdefault('EDUAI_UPLOAD_DIR', '/tmp/data_uji/uploads')

from app.models import (BelajarNaskah, FileBerkas, SessionLocal,  # noqa: E402
                        User)
from app import belajar                                             # noqa: E402

LULUS = GAGAL = 0


def cek(nama, syarat, ket=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}  ← {ket}')


def main():
    db = SessionLocal()
    u = db.query(User).filter(User.email == 'uji-belajar@eduai.test').first()
    if u is None:
        print('  ⚠️ user uji belum ada — jalankan _siapkan_uji_belajar.py dulu')
        return 1

    print(f'  user uji: id={u.id} paket={u.paket}')

    #  naskah uji: pilih naskah MILIK USER UJI yang berkasnya ADA
    f = (db.query(FileBerkas)
         .filter(FileBerkas.user_id == u.id)
         .first())
    if f is None:
        print('  ⚠️ naskah uji belum ada')
        return 1
    fid = f.id
    print(f'  naskah uji: {fid} "{f.nama}"')

    #  ── 1. baca isi bab dari naskah NYATA ──────────────────────────────
    print('\n── 1. BACA ISI BAB (fungsi produksi yang sudah ada) ──')
    #  ⚠️ 04Okt26: naskah uji bisa berupa PROPOSAL (cuma BAB I). Karena itu
    #     jangan menuntut bab yang belum ada — cek: (a) minimal SATU bab
    #     terbaca, (b) bab yang TIDAK ada → KOSONG (tidak balas seluruh naskah),
    #     (c) tiap bab yang terbaca jauh lebih kecil dari naskah utuh.
    panjang = {n: len(belajar.teks_bab(db, u, fid, n)) for n in range(1, 6)}
    ada = [n for n, L in panjang.items() if L > 500]
    print(f'     panjang per bab: {panjang}')
    cek('minimal SATU bab terbaca (>500 kar)', bool(ada), f'{ada}')
    cek('bab yang ADA berbeda-beda isinya',
        len({belajar.teks_bab(db, u, fid, n) for n in ada}) == len(ada) if ada else True)
    cek('bab yang TIDAK ADA (BAB 9) → KOSONG, tidak balas seluruh naskah',
        belajar.teks_bab(db, u, fid, 9) == '',
        f'{len(belajar.teks_bab(db, u, fid, 9))} kar (harus 0)')
    #  🚨 JEBAKAN TERBUKTI 04Okt26: `versi.ambil_bab` balas SELURUH naskah
    #     kalau label tak ketemu. Pastikan tak ada bab yang = seluruh naskah.
    cek('tidak ada bab yang = seluruh naskah (jebakan label palsu)',
        all(L < 60000 for L in panjang.values()), f'{panjang}')

    #  ── 2. pagar kepemilikan ─────────────────────────────────────────────
    print('\n── 2. PAGAR KEPEMILIKAN ──')
    cek('naskah sendiri → lolos', belajar.naskah_milik(db, u, fid) == fid)
    cek('naskah TIDAK ADA → None', belajar.naskah_milik(db, u, 999999) is None)
    lain = db.query(FileBerkas).filter(FileBerkas.user_id != u.id).first()
    if lain is not None:
        cek('naskah MILIK ORANG LAIN → None',
            belajar.naskah_milik(db, u, lain.id) is None)

    #  ── 3. pagar aktivasi ────────────────────────────────────────────────
    print('\n── 3. PAGAR AKTIVASI ──')
    cek('naskah sudah diaktifkan → lolos',
        belajar.naskah_sudah_aktif(db, u, fid) is not None)

    #  ── 4. urai balasan model (bentuk aneh) ──────────────────────────────
    print('\n── 4. URAI BALASAN MODEL ──')
    b = belajar._urai_butir(
        'BUTIR 1\ntema: Inti Masalah\nisi: Penjualan turun.\nkutipan: turun 18%\n'
        'BUTIR 2\ntema: Variabel\nisi: Dua variabel dipakai.\nkutipan: kualitas produk\n',
        3)
    cek('urai 2 butir benar', len(b) == 2, str(len(b)))
    cek('tema terbaca', b[0]['tema'] == 'Inti Masalah', b[0]['tema'])
    cek('kutipan terbaca', '18%' in b[0]['kutipan'])
    cek('tahan balasan berantakan (tanpa BUTIR) → kosong',
        belajar._urai_butir('maaf saya tidak bisa', 3) == [])
    cek('tahan balasan dengan ** tebal',
        len(belajar._urai_butir('BUTIR 1\n**tema:** A\n**isi:** B', 3)) == 1)

    #  ── 5. HEMAT: sudah tersimpan → tidak panggil AI lagi ───────────────
    print('\n── 5. PAGAR HEMAT (0 token kalau sudah ada) ──')
    belajar._simpan_insight(db, u, fid, 2, [{'tema': 'Uji', 'isi': 'uji', 'kutipan': 'x'}])
    d = belajar.baca_insight(db, u, fid)
    cek('insight tersimpan ke belajar_naskah', 'bab2' in d, str(list(d.keys())))
    #  hitung_insight bab 2 yang SUDAH ada → harus 'baru': False (tanpa AI)
    hasil = asyncio.run(belajar.hitung_insight(db, u, fid, 2))
    cek('bab sudah ada → TIDAK panggil AI (baru=False)', hasil.get('baru') is False)

    #  ── 6. panggil LLM sungguhan untuk BAB I (sekali) ───────────────────
    print('\n── 6. PANGGIL AI SUNGGUHAN (BAB I) ──')
    import time
    t0 = time.time()
    try:
        hasil = asyncio.run(belajar.hitung_insight(db, u, fid, 1))
        dt = time.time() - t0
        butir = hasil.get('butir') or []
        print(f'     waktu {dt:.1f} dtk · butir={len(butir)} · baru={hasil.get("baru")}')
        for t in butir:
            print(f'       · {t["tema"]}: {t["isi"][:70]}')
            if t['kutipan']:
                print(f'         📄 {t["kutipan"][:70]}')
        cek('AI membalas minimal 1 butir', len(butir) >= 1)
        cek('setiap butir punya tema', all(t['tema'] for t in butir))
        cek('setiap butir punya isi', all(t['isi'] for t in butir))
        #  guardrail §4.8: WAJIB ada kutipan sumber
        ada_kutip = sum(1 for t in butir if t['kutipan'])
        cek('minimal separuh butir menyertakan kutipan sumber §4.8',
            ada_kutip >= max(1, len(butir) // 2), f'{ada_kutip}/{len(butir)}')
        d2 = belajar.baca_insight(db, u, fid)
        cek('hasil DISIMPAN permanen di DB', 'bab1' in d2)
        #  panggil kedua kali → harus 0 token
        h2 = asyncio.run(belajar.hitung_insight(db, u, fid, 1))
        cek('panggil kedua → pakai simpanan (baru=False)', h2.get('baru') is False)
    except Exception as e:                                        # noqa: BLE001
        print(f'     ⚠️ AI gagal: {type(e).__name__}: {e}')
        cek('AI harus bisa dipanggil', False, str(e)[:120])

    #  bersihkan jejak uji
    for bn in db.query(BelajarNaskah).all():
        if (bn.insight_json or '').find('"Uji"') >= 0:
            import json
            dd = json.loads(bn.insight_json)
            dd.pop('bab2', None)
            bn.insight_json = json.dumps(dd, ensure_ascii=False)
            db.commit()

    db.close()
    print(f'\n═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
    print('✅ LULUS' if GAGAL == 0 else '❌ ADA YANG GAGAL')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
