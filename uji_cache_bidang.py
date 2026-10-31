"""Uji cache bidang pra-panen (Gas Bos 31 Okt 2026 12:03, butir 5).

HANYA dijalankan di dalam wadah live-image (punya sqlalchemy dan
dependensi app), bukan di venv hermes yang tidak punya sqlalchemy.
Pola: docker create dari image eduai-app, docker cp app/. ke wadah,
jalankan berkas ini, hapus wadah. DB uji hanya sqlite memori,
tidak pernah menyentuh DB produksi.

Jalankan: python3 /tmp/uji_cache_bidang.py (di dalam wadah, dengan
/app/app sudah berisi source terbaru).
Keluar 0 bila semua lulus, 1 bila ada yang gagal.
"""
import sys

sys.path.insert(0, '/app')

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama}   {bukti}')


def main():
    from app import pra_panen as PP
    from app import models as _models
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    _engine = create_engine('sqlite:///:memory:')
    _models.Base.metadata.create_all(_engine)
    _Session = sessionmaker(bind=_engine)
    _db = _Session()

    print('[CACHE] BIDANG TIDAK KOSONG BISA DIBACA DAN DITULIS')
    cek('cache kosong awal miss',
        PP.cari_cache(_db, 'ekonomi', 'judul bab uji') is None)
    PP.simpan_cache(_db, 'ekonomi', 'judul bab uji', [11, 22, 33])
    _db.commit()
    cek('cache ekonomi terbaca sesudah simpan',
        PP.cari_cache(_db, 'ekonomi', 'judul bab uji') == [11, 22, 33],
        str(PP.cari_cache(_db, 'ekonomi', 'judul bab uji')))
    cek('cache bidang lain miss (kunci bidang + judul)',
        PP.cari_cache(_db, 'hukum', 'judul bab uji') is None)
    cek('cache judul lain miss',
        PP.cari_cache(_db, 'ekonomi', 'judul lain') is None)

    print('\n[CACHE] BIDANG KOSONG TIDAK PERNAH DIBACA ATAU DITULIS')
    cek('cache bidang kosong selalu miss',
        PP.cari_cache(_db, '', 'judul bab uji') is None)
    PP.simpan_cache(_db, '', 'judul bab uji', [99])
    _db.commit()
    cek('simpan bidang kosong tidak menulis',
        _db.query(_models.CacheTopik).filter(
            _models.CacheTopik.bidang == '').first() is None)
    cek('cache ekonomi tetap utuh sesudah simpan kosong',
        PP.cari_cache(_db, 'ekonomi', 'judul bab uji') == [11, 22, 33])

    print('\n[CACHE] PANEN_SEMUA MENERIMA BIDANG (tanda tangan)')
    import inspect
    _params = list(inspect.signature(PP.panen_semua).parameters)
    cek('panen_semua punya parameter bidang',
        'bidang' in _params, str(_params))

    _db.close()
    print(f'\n{"=" * 64}\nCACHE BIDANG: {LULUS} LULUS / {GAGAL} GAGAL\n{"=" * 64}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
