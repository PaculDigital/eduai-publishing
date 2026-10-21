"""PEMBUNGKUS JEV BUKU UMUM untuk produksi — bukan salinan.

Pola sama `app/peta3_jev.py` (14 Okt 2026): `jev_buku_umum.py` di root proyek
adalah modul kerja; berkas ini memuatnya lewat `importlib` supaya rute
produksi bisa memakainya tanpa putaran impor.

Cara pakai dari app:
    from app import jev_buku
    peta = jev_buku.petakan(teks_bab)
    blok = jev_buku.blok(teks_bab)
"""
import importlib.util
import logging
import os

log = logging.getLogger(__name__)

_MOD = None


def _muat():
    """Muat `jev_buku_umum.py` sekali, dari lokasi yang PASTI benar."""
    global _MOD
    if _MOD is not None:
        return _MOD
    calon = [
        '/app/jev_buku_umum.py',                                    # container
        os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     'jev_buku_umum.py'),                            # host
    ]
    for jalur in calon:
        if os.path.isfile(jalur):
            spec = importlib.util.spec_from_file_location('jev_buku_umum', jalur)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _MOD = mod
            log.info('[jev_buku] modul dimuat dari %s', jalur)
            return mod
    raise RuntimeError('jev_buku_umum.py tidak ditemukan')


def petakan(teks, pakai_cache=True):
    """Peta bentuk naskah buku. Lihat `jev_buku_umum.petakan_buku`."""
    return _muat().petakan_buku(teks, pakai_cache=pakai_cache)


def blok(teks, pakai_cache=True):
    """Blok siap rakit: [(jenis, isi)] + peta."""
    return _muat().blok_buku(teks, pakai_cache=pakai_cache)


def siap():
    """Jev hidup? — supaya pemanggil bisa lapor jelas, bukan misteri."""
    try:
        from app import jev
        return jev.cek_siap()
    except Exception as e:                      # noqa: BLE001
        return {'siap': False, 'sebab': str(e), 'kunci': '-'}
