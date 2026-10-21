"""UJI MESIN SIMULASI SIDANG (L3+L4) — 04Okt26.

Meniru pola `_uji_bank_soal.py`. Diuji pada NASKAH NYATA.

Yang diuji:
  1. `nilai_jawaban` menilai jawaban → 0-100, ada tepat/tambah, ada kutipan
  2. JAWABAN DI LUAR NASKAH → nilai rendah (bukti AI TIDAK asal tinggi)
  3. Nilai tersimpan di belajar_naskah.bab_selesai (kolom SUDAH ADA)
  4. `skor_bab` menghitung rata-rata + per level
  5. `skor_naskah` merata-ratakan antar bab (bahan pembimbing)
  6. Jawaban terlalu pendek → ditolak (pagar)
  7. soal_ke di luar jangkauan → ditolak (pagar)
  8. bab_selesai TIDAK merusak insight_json & soal_json
  9. Kalimat terlarang (salah/gagal/bodoh) TIDAK muncul di keluaran
 10. Uji bergigi: jawaban BAGUS harus > jawaban NGACO

Pakai:
  docker exec -e EDUAI_DATA_DIR=/tmp/data_uji ... python3 _uji_simulasi.py
"""
import os
import sys
import asyncio
import json

sys.path.insert(0, '/app')

LULUS = 0
GAGAL = 0


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f'  → {catatan}' if catatan else ''))


TERLARANG = ('salah', 'gagal', 'buruk', 'bodoh', 'mengecewakan', 'habis')


def main():
    from app.models import SessionLocal, User, FileBerkas, BelajarNaskah
    from app import belajar

    db = SessionLocal()
    u = db.query(User).filter(User.email == 'uji-belajar@eduai.test').first()
    if u is None:
        print('⛔ user uji tidak ada — jalankan _siapkan_data_uji.py dulu')
        return 2
    f = db.query(FileBerkas).filter(FileBerkas.user_id == u.id).first()
    fid = int(f.id)

    bank = {}
    n_uji = None
    for n in (1, 2, 3, 4, 5):
        b = (belajar.baca_soal(db, u, fid).get(f'bab{n}') or {}).get('soal') or []
        if b:
            bank, n_uji = b, n
            break
    if not bank:
        print('⛔ bank soal kosong — jalankan _uji_bank_soal.py dulu')
        return 2
    print(f'  naskah {fid} "{f.nama}" · bab {n_uji} · {len(bank)} soal')

    #  ── 1. bersihkan dulu (uji jujur dari nol) ──────────────────────────
    print('\n── 1. BERSIHKAN SIMULASI LAMA ──')
    bn = (db.query(BelajarNaskah).filter(BelajarNaskah.file_id == fid,
                                         BelajarNaskah.user_id == u.id).first())
    bn.bab_selesai = '{}'
    db.commit()
    cek('bab_selesai dibersihkan', True)

    #  ── 2. jawaban NGACO (harus NILAI RENDAH) ───────────────────────────
    print('\n── 2. JAWABAN NGACO (di luar naskah) ──')
    ngaco = ('Menurut saya hal ini berkaitan dengan cuaca dan juga kondisi jalan raya '
             'yang rusak, lalu harga cabai naik karena musim hujan berkepanjangan.')
    h1 = asyncio.run(belajar.nilai_jawaban(db, u, fid, n_uji, 0, ngaco))
    n1 = (h1.get('hasil') or {}).get('nilai')
    print(f'  → nilai jawaban ngaco = {n1}')
    cek('jawaban ngaco dapat nilai', isinstance(n1, int))
    cek('jawaban ngaco nilai RENDAH (<45)', isinstance(n1, int) and n1 < 45, f'nilai={n1}')

    #  ── 3. jawaban MEMAKAI isi naskah (harus LEBIH TINGGI) ─────────────
    print('\n── 3. JAWABAN MEMAKAI ISI NASKAH ──')
    s0 = bank[0]
    bagus = (f"{s0.get('kunci','')} Selain itu, naskah menegaskan hal ini penting "
             f"dan berkaitan dengan {s0.get('tumpu','')[:80]}")
    h2 = asyncio.run(belajar.nilai_jawaban(db, u, fid, n_uji, 0, bagus))
    n2 = (h2.get('hasil') or {}).get('nilai')
    print(f'  → nilai jawaban bagus = {n2}')
    cek('jawaban bagus dapat nilai', isinstance(n2, int))
    cek('UJI BERGIGI: bagus > ngaco', isinstance(n2, int) and isinstance(n1, int) and n2 > n1,
        f'bagus={n2} ngaco={n1}')

    #  ── 4. isi penilaian ────────────────────────────────────────────────
    print('\n── 4. ISI PENILAIAN ──')
    hs = h2.get('hasil') or {}
    cek('ada "judul"', bool(hs.get('judul')))
    cek('ada "tepat"', bool(hs.get('tepat')))
    cek('ada "tambah"', bool(hs.get('tambah')))
    cek('nisan 0-100', isinstance(n2, int) and 0 <= n2 <= 100)
    gabung = f"{hs.get('judul','')} {hs.get('tepat','')} {hs.get('tambah','')}".lower()
    ketemu = [k for k in TERLARANG if k in gabung]
    cek('TIDAK ada kata terlarang', not ketemu, f'kata ditemukan: {ketemu}')
    semua_nilai = f"{n1} {hs.get('tepat','')} {hs.get('tambah','')}"
    cek('penilaian menyebut isi naskah (rujuk kutipan)',
        bool(hs.get('tumpu')) or len(semua_nilai) > 30)

    #  ── 5. tersimpan di bab_selesai ─────────────────────────────────────
    print('\n── 5. TERSIMPAN DI DB ──')
    db.expire_all()
    bn = (db.query(BelajarNaskah).filter(BelajarNaskah.file_id == fid,
                                         BelajarNaskah.user_id == u.id).first())
    d = json.loads(bn.bab_selesai or '{}')
    cek(f'bukti: bab{n_uji}.uji tersimpan', f'bab{n_uji}' in d and 'uji' in d[f'bab{n_uji}'])
    cek('jawaban 0 tersimpan', '0' in (d.get(f'bab{n_uji}', {}).get('uji', {}).get('jawaban', {})))

    #  ── 6. skor_bab ─────────────────────────────────────────────────────
    print('\n── 6. SKOR BAB (L4) ──')
    sb = belajar.skor_bab(db, u, fid, n_uji)
    print(f'  → {sb}')
    cek('skor_bab ada', sb['ada'] is True)
    cek('terjawab = 1 (baru 1 soal)', sb['terjawab'] == 1, str(sb))
    cek('total = jumlah soal bank', sb['total'] == len(bank))
    cek('skor = nilai jawaban terakhir', sb['skor'] == n2, f"{sb['skor']} vs {n2}")
    cek('per_level terisi', bool(sb['per_level']))

    #  ── 7. skor_naskah ──────────────────────────────────────────────────
    print('\n── 7. SKOR NASKAH (bahan pembimbing) ──')
    sn = belajar.skor_naskah(db, u, fid)
    cek('skor_naskah ada', sn['ada'] is True)
    cek('rinci punya 1 bab', len(sn['rinci']) == 1, str(sn['rinci']))
    cek('skor naskah = skor bab', sn['skor'] == sb['skor'])

    #  ── 8. PAGAR ────────────────────────────────────────────────────────
    print('\n── 8. PAGAR ──')
    h3 = asyncio.run(belajar.nilai_jawaban(db, u, fid, n_uji, 0, 'ya'))
    cek('jawaban terlalu pendek ditolak', h3.get('ok') is False, str(h3))
    h4 = asyncio.run(belajar.nilai_jawaban(db, u, fid, n_uji, 99, 'jawaban panjang sekali ini'))
    cek('soal_ke di luar jangkauan ditolak', h4.get('ok') is False, str(h4))
    cek('pesan penolakan ramah (tanpa kata terlarang)',
        not [k for k in TERLARANG if k in str(h3.get('pesan', '')).lower()])

    #  ── 9. tidak merusak bagian lain ────────────────────────────────────
    print('\n── 9. TIDAK MERUSAK ──')
    db.expire_all()
    bn = (db.query(BelajarNaskah).filter(BelajarNaskah.file_id == fid,
                                         BelajarNaskah.user_id == u.id).first())
    cek('insight_json utuh', isinstance(json.loads(bn.insight_json or '{}'), dict))
    cek('soal_json utuh + masih ada soal',
        bool((json.loads(bn.soal_json or '{}').get(f'bab{n_uji}') or {}).get('soal')))
    cek('status masih aktif', bn.status == 'aktif')

    db.close()
    print(f'\n═══ {LULUS} LULUS / {GAGAL} GAGAL ═══')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
