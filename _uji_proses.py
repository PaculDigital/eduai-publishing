"""UJI MODUL PROSES LATAR BELAKANG (Langkah A) — app/proses.py.

Jalankan DI DALAM container produksi:
    docker cp _uji_proses.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _uji_proses.py
"""
import sys
import time

sys.path.insert(0, '/app')

from app import proses as P
from app.models import SessionLocal, User, init_db

LULUS = GAGAL = 0


def cek(nama, syarat, ket=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'   ✅ {nama}' + (f' — {ket}' if ket else ''))
    else:
        GAGAL += 1
        print(f'    {nama}' + (f' — {ket}' if ket else ''))


def main():
    print('═' * 72)
    print('UJI PROSES LATAR BELAKANG (Langkah A, ACC Bos 16Sep26)')
    print('═' * 72)
    init_db()
    db = SessionLocal()

    # ── 1. TABEL proses_ai ADA + kolom lengkap ───────────────────────────
    print('\n── 1. TABEL proses_ai ─────────────────────────────')
    try:
        kolom = {r[1] for r in db.execute(
            __import__('sqlalchemy').text('PRAGMA table_info(proses_ai)'))}
        perlu = {'id', 'kode', 'user_id', 'file_id', 'status', 'tahap',
                 'bagian_ke', 'jumlah_bagian', 'panjang', 'hasil',
                 'hasil_json', 'galat', 'komentar_json', 'jenis_dokumen',
                 'model_ai', 'token_in', 'token_out', 'token_revisi',
                 'dibaca', 'dibuat', 'diubah', 'selesai'}
        hilang = perlu - kolom
        cek('tabel proses_ai punya semua kolom', not hilang,
            f'kolom={len(kolom)} hilang={sorted(hilang) or "tidak ada"}')
    except Exception as e:                                        # noqa: BLE001
        cek('tabel proses_ai bisa dibaca', False, str(e))

    # ─ 2. Tabel LAMA tidak tersentuh ────────────────────────────────────
    print('\n── 2. TABEL LAMA TIDAK DIUBAH ─────────────────────')
    jml = db.execute(__import__('sqlalchemy').text(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'")).scalar()
    cek('jumlah tabel = 14 (13 lama + proses_ai)', jml == 14, f'tabel={jml}')

    # ── 3. mulai() membuat catatan ───────────────────────────────────────
    print('\n── 3. mulai() ────────────────────────────────────')
    u = db.execute(__import__('sqlalchemy').select(User).limit(1)).scalar_one()
    p = P.mulai(db, user_id=u.id, file_id=None,
                komentar=['perdalam latar belakang'], jumlah_bagian=2,
                panjang=65932, jenis_dokumen='skripsi')
    cek('kode dibuat', bool(p.kode) and len(p.kode) >= 16, f'kode={p.kode[:8]}…')
    cek('status awal menunggu', p.status == 'menunggu', p.status)
    cek('jumlah_bagian tercatat', p.jumlah_bagian == 2, str(p.jumlah_bagian))
    cek('panjang tercatat', p.panjang == 65932, str(p.panjang))
    cek('komentar tersimpan', 'latar belakang' in p.komentar_json, p.komentar_json[:40])

    # ── 4. KODE TIDAK BISA DITEBAK ───────────────────────────────────────
    print('\n── 4. KEAMANAN KODE ──────────────────────────────')
    kode2 = P.kode_baru()
    cek('kode acak (beda tiap panggil)', P.kode_baru() != P.kode_baru(),
        '2 pemanggilan berbeda')
    cek('kode panjang ≥16', len(kode2) >= 16, f'{len(kode2)} kar')

    # ── 5. ambil() + PEMILIK ─────────────────────────────────────────────
    print('\n── 5. ambil() & PEMERIKSAAN PEMILIK ──────────────')
    cek('ambil pakai kode', P.ambil(db, p.kode) is not None)
    cek('user LAIN tidak bisa ambil', P.ambil(db, p.kode, user_id=u.id + 9999) is None,
        'pemilik diperiksa')
    cek('pemilik benar bisa ambil', P.ambil(db, p.kode, user_id=u.id) is not None)

    # ─ 6. ubah_tahap() dari UTAS LAIN (sesi DB baru) ────────────────────
    print('\n── 6. ubah_tahap() dari utas ─────────────────────')
    P.ubah_tahap(p.kode, P.TAHAP_MEMBACA, status='jalan')
    db.expire_all()
    p2 = P.ambil(db, p.kode)
    cek('tahap jadi "Membaca naskah"', p2.tahap == P.TAHAP_MEMBACA, p2.tahap)
    cek('status jadi jalan', p2.status == 'jalan', p2.status)
    P.ubah_tahap(p.kode, P.tahap_menulis(2, 3), bagian_ke=2)
    db.expire_all()
    p3 = P.ambil(db, p.kode)
    cek('tahap bagian ke-2', p3.tahap == 'Menulis bagian ke-2 dari 3', p3.tahap)
    cek('bagian_ke tercatat', p3.bagian_ke == 2, str(p3.bagian_ke))
    P.ubah_tahap(p.kode, P.tahap_menulis(1, 1))
    db.expire_all()
    cek('1 bagian → teks tanpa nomor',
        P.ambil(db, p.kode).tahap == 'Menulis hasil revisi',
        P.ambil(db, p.kode).tahap)

    # ── 7. tandai_selesai() ──────────────────────────────────────────────
    print('\n── 7. tandai_selesai() ───────────────────────────')
    P.tandai_selesai(p.kode, hasil='HASIL PANJANG…', hasil_json='[{}]',
                     model_ai='ali/deepseek-v4.1-flash',
                     token_in=5000, token_out=2000, token_revisi=1)
    db.expire_all()
    p4 = P.ambil(db, p.kode)
    cek('status selesai', p4.status == 'selesai', p4.status)
    cek('tahap Selesai', p4.tahap == P.TAHAP_SELESAI, p4.tahap)
    cek('hasil tersimpan', p4.hasil == 'HASIL PANJANG…')
    cek('model nama LENGKAP', p4.model_ai == 'ali/deepseek-v4.1-flash', p4.model_ai)
    cek('token_revisi tersimpan', p4.token_revisi == 1, str(p4.token_revisi))
    cek('dibaca=0 (lonceng menyala)', p4.dibaca == 0, str(p4.dibaca))
    cek('selesai ada waktunya', p4.selesai is not None)

    # ── 8. LONCENG: belum_dibaca() ───────────────────────────────────────
    print('\n── 8. LONCENG (belum_dibaca) ─────────────────────')
    lc = P.belum_dibaca(db, u.id)
    cek('proses ini muncul di lonceng', any(x.kode == p.kode for x in lc),
        f'{len(lc)} item belum dibaca')

    # ── 9. tandai_dibaca() → lonceng padam ───────────────────────────────
    print('\n── 9. tandai_dibaca() ───────────────────────────')
    cek('tandai_dibaca berhasil', P.tandai_dibaca(db, p.kode, u.id) is True)
    db.expire_all()
    lc2 = P.belum_dibaca(db, u.id)
    cek('proses hilang dari lonceng', not any(x.kode == p.kode for x in lc2),
        f'{len(lc2)} item tersisa')

    # ── 10. yang_sedang_jalan() ─────────────────────────────────────────
    print('\n── 10. yang_sedang_jalan() ──────────────────────')
    p5 = P.mulai(db, user_id=u.id, file_id=None, komentar=['x'])
    jln = P.yang_sedang_jalan(db, u.id)
    cek('proses baru muncul di "sedang jalan"', any(x.kode == p5.kode for x in jln),
        f'{len(jln)} proses')
    cek('proses SELESAI tidak muncul', not any(x.kode == p.kode for x in jln))

    # ─ 11. tandai_gagal() + alasan ──────────────────────────────────────
    print('\n── 11. tandai_gagal() ───────────────────────────')
    P.tandai_gagal(p5.kode, 'ConnectError: koneksi ke 9router gagal')
    db.expire_all()
    p6 = P.ambil(db, p5.kode)
    cek('status gagal', p6.status == 'gagal', p6.status)
    cek('alasan tersimpan (bukan "terjadi kesalahan")',
        '9router' in p6.galat, p6.galat[:50])
    cek('proses gagal TIDAK masuk lonceng',
        not any(x.kode == p5.kode for x in P.belum_dibaca(db, u.id)))

    # ── 12. ringkas() TIDAK memuat hasil (hemat) ─────────────────────────
    print('\n── 12. ringkas() hemat ───────────────────────────')
    r = P.ringkas(P.ambil(db, p.kode))
    cek('ringkas TIDAK memuat naskah hasil', 'hasil' not in r,
        f'kunci={sorted(r.keys())[:6]}…')
    cek('ringkas ada "ada_hasil=True"', r['ada_hasil'] is True)
    cek('ringkas ada tahap & status', 'tahap' in r and 'status' in r)

    # ── 13. jalankan() BENAR-BENAR jalan di utas ─────────────────────────
    print('\n── 13. jalankan() di utas ────────────────────────')
    p7 = P.mulai(db, user_id=u.id, file_id=None, komentar=['uji'])
    urut = []

    async def kerja(lapor):
        urut.append('mulai')
        lapor.tahap('Membaca naskah')
        await __import__('asyncio').sleep(0.1)
        lapor.menulis(1, 2)
        await __import__('asyncio').sleep(0.1)
        urut.append('selesai')
        P.tandai_selesai(p7.kode, hasil='OK')

    t = P.jalankan(p7.kode, kerja)
    cek('utang berjalan (daemon)', t.daemon is True)
    t.join(timeout=5)
    cek('utas selesai < 5s', not t.is_alive())
    cek('urutan kerja lengkap', urut == ['mulai', 'selesai'], str(urut))
    db.expire_all()
    p8 = P.ambil(db, p7.kode)
    cek('status jadi selesai dari utas', p8.status == 'selesai', p8.status)
    cek('hasil dari utas tersimpan', p8.hasil == 'OK', p8.hasil)

    # ── 14. GAGAL DI UTAS → status gagal + alasan (bukan hilang diam) ────
    print('\n── 14. gagal di utas ditangkap ───────────────────')
    p9 = P.mulai(db, user_id=u.id, file_id=None, komentar=['uji gagal'])

    async def kerja_gagal(lapor):
        lapor.tahap('Membaca naskah')
        raise RuntimeError('provider 9router menolak (503)')

    t2 = P.jalankan(p9.kode, kerja_gagal)
    t2.join(timeout=5)
    time.sleep(0.2)
    db.expire_all()
    p10 = P.ambil(db, p9.kode)
    cek('status gagal (utas tidak mati diam)', p10.status == 'gagal', p10.status)
    cek('nama galat + pesan ada',
        'RuntimeError' in p10.galat and '503' in p10.galat, p10.galat[:60])

    # ── 15. SESI LAMA yang TERTINGGAL (simulasi restart) ─────────────────
    print('\n── 15. proses tertinggal saat app mati ───────────')
    p11 = P.mulai(db, user_id=u.id, file_id=None, komentar=['tertinggal'])
    P.ubah_tahap(p11.kode, P.TAHAP_MEMBACA, status='jalan')
    db.expire_all()
    cek('proses "jalan" bisa dilacak untuk dibersihkan',
        any(x.kode == p11.kode for x in P.yang_sedang_jalan(db, u.id)))

    # bersihkan data uji
    for kd in (p.kode, p5.kode, p7.kode, p9.kode, p11.kode):
        row = P.ambil(db, kd)
        if row:
            db.delete(row)
    db.commit()
    db.close()

    print('\n' + '═' * 72)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('═' * 72)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())