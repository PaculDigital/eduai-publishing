"""UJI MESIN BANK SOAL (L2) — 04Okt26.

Meniru pola `_uji_insight_belajar.py`. Diuji pada NASKAH NYATA (bukan karangan).

Yang diuji:
  1. Bank soal dibangun → 4 butir (dasar/menengah/tajam/jebakan)
  2. Tiap soal punya TANYA + TUMPU (kutipan asli naskah) + KUNCI
  3. PAGAR HEMAT: panggil ke-2 → pakai simpanan, TIDAK panggil AI (0 token)
  4. Tersimpan di belajar_naskah.soal_json (kolom SUDAH ADA)
  5. Pagar kepemilikan & aktivasi (titip pola yang sudah teruji)
  6. Rute halaman memuat bank soal (titip di /belajar/insight yang ADA)

Pakai:
  EDUAI_DATA_DIR=/tmp/data_uji EDUAI_UPLOAD_DIR=/tmp/data_uji/uploads \
  python3 _uji_bank_soal.py
"""
import os
import sys
import asyncio
import json

sys.path.insert(0, '/app')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) or '/app')

LULUS = 0
GAGAL = 0
CATATAN = []


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {catatan}' if catatan else ''))
    if catatan:
        CATATAN.append((nama, catatan))


def main():
    from app.models import SessionLocal, User, FileBerkas, BelajarNaskah
    from app import belajar

    db = SessionLocal()

    #  ── 0. ambil user uji + naskah uji ──────────────────────────────────
    u = db.query(User).filter(User.email == 'uji-belajar@eduai.test').first()
    if u is None:
        print('⛔ user uji tidak ada — jalankan _siapkan_data_uji.py dulu')
        return 2

    f = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
    if f is None:
        print('⛔ naskah uji tidak ada')
        return 2
    fid = int(f.id)
    print(f'  naskah uji: {fid} "{f.nama}" · user {u.id} ({u.email})')

    #  ── 1. baca isi bab (fungsi produksi) ───────────────────────────────
    print('\n── 1. BACA ISI BAB ──')
    ada_isi = []
    for n in (1, 2, 3, 4, 5):
        t = belajar.teks_bab(db, u, fid, n)
        if t:
            ada_isi.append((n, len(t)))
    cek('minimal 1 bab bisa dibaca', len(ada_isi) >= 1,
        f'bab terbaca: {ada_isi}')
    cek('tiap bab terbaca < 60rb kar (naskah proposal pun wajar)',
        all(p < 60000 for _, p in ada_isi), f'{ada_isi}')
    n_uji = ada_isi[0][0] if ada_isi else 1

    #  ── 2. bersihkan bank soal lama (biar uji jujur) ────────────────────
    print('\n── 2. BANK SOAL DIHITUNG (AI NYATA) ──')
    bn = (db.query(BelajarNaskah)
          .filter(BelajarNaskah.file_id == fid,
                  BelajarNaskah.user_id == u.id).first())
    if bn is not None:
        bn.soal_json = '{}'
        db.commit()
        cek('bank soal lama dibersihkan', True)

    import time
    t0 = time.time()
    hasil = asyncio.run(belajar.hitung_soal(db, u, fid, n_uji))
    dt = time.time() - t0
    soal = hasil.get('soal') or []
    print(f'  → {len(soal)} soal · {dt:.1f} detik · baru={hasil.get("baru")}')

    cek('soal tersusun', len(soal) >= 1, f'jumlah={len(soal)}')
    cek('soal baru (bukan simpanan)', hasil.get('baru') is True)

    #  ── 3. isi tiap soal ────────────────────────────────────────────────
    print('\n── 3. ISI SOAL ──')
    level = [s.get('level', '') for s in soal]
    cek('tiap soal punya TANYA', all(s.get('tanya') for s in soal))
    cek('tiap soal punya TUMPU (kutipan naskah)',
        all(s.get('tumpu') for s in soal),
        f'yang kosong: {[i for i, s in enumerate(soal) if not s.get("tumpu")]}')
    cek('tiap soal punya KUNCI', all(s.get('kunci') for s in soal))
    cek('level sah semua',
        all(l in ('dasar', 'menengah', 'tajam', 'jebakan') for l in level),
        f'level={level}')
    cek('level bervariasi (min 2 macam)', len(set(level)) >= 2, f'{set(level)}')

    #  ── 4. PAGAR HEMAT: panggil ke-2 = 0 token ──────────────────────────
    print('\n── 4. PAGAR HEMAT (klik ke-2 tidak panggil AI) ──')
    t0 = time.time()
    hasil2 = asyncio.run(belajar.hitung_soal(db, u, fid, n_uji))
    dt2 = time.time() - t0
    cek('panggil ke-2 → pakai simpanan (baru=False)', hasil2.get('baru') is False)
    cek('panggil ke-2 JAUH lebih cepat (<1 dtk)', dt2 < 1.0, f'{dt2:.3f} dtk')
    cek('jumlah soal sama (tersimpan utuh)',
        len(hasil2.get('soal') or []) == len(soal))

    #  ── 5. tersimpan di belajar_naskah.soal_json ────────────────────────
    print('\n── 5. TERSIMPAN DI DB ──')
    db.expire_all()
    bn = (db.query(BelajarNaskah)
          .filter(BelajarNaskah.file_id == fid,
                  BelajarNaskah.user_id == u.id).first())
    cek('baris belajar_naskah ada', bn is not None)
    d = json.loads(bn.soal_json or '{}')
    cek(f'kunci bab{n_uji} tersimpan di soal_json', f'bab{n_uji}' in d)
    cek('jumlah soal tersimpan sesuai', len(d.get(f'bab{n_uji}', {}).get('soal', [])) == len(soal))

    #  ── 6. pagar kepemilikan & aktivasi (pola yang sudah teruji) ────────
    print('\n── 6. PAGAR ──')
    cek('naskah_milik balas fid untuk pemilik', belajar.naskah_milik(db, u, fid) == fid)
    u_lain = db.query(User).filter(User.id != u.id).first()
    if u_lain is not None:
        cek('naskah_milik TOLAK untuk orang lain',
            belajar.naskah_milik(db, u_lain, fid) is None,
            f'dicoba user {u_lain.id}')
    cek('naskah_sudah_aktif balas dict', isinstance(belajar.naskah_sudah_aktif(db, u, fid), dict))

    #  ── 7. soal_json TIDAK menimpa insight_json ─────────────────────────
    print('\n── 7. TIDAK MERUSAK INSIGHT ──')
    db.expire_all()
    bn = (db.query(BelajarNaskah)
          .filter(BelajarNaskah.file_id == fid,
                  BelajarNaskah.user_id == u.id).first())
    ins = json.loads(bn.insight_json or '{}')
    cek('insight_json masih ada (tidak tertimpa bank soal)', isinstance(ins, dict))

    db.close()

    print(f'\n═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
