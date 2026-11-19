"""Rute Cek Konsistensi: Setelan round-trip + endpoint + panel (19 Nov 2026).

Tidak memanggil LLM dan tidak menyentuh DB live. Setelan diuji lewat
SQLite sementara (pola test_pustaka_periksa.py). Panel diuji lewat
teks template naskah.html (tombol + wadah + fetch status/mulai-latar).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import rute_konsistensi as RK


def cek(nama, benar):
    print(("  LULUS  " if benar else "  GAGAL  ") + nama)
    return benar


def main():
    lulus = 0
    total = 0

    def t(nama, benar):
        nonlocal lulus, total
        total += 1
        if cek(nama, benar):
            lulus += 1

    # --- Router: dua endpoint ---
    rute = {(r.path, tuple(r.methods or [])) for r in RK.router.routes}
    t('rute: POST /v1/konsistensi/mulai-latar ada',
      ('/v1/konsistensi/mulai-latar', ('POST',)) in rute)
    t('rute: GET /v1/konsistensi/status ada',
      ('/v1/konsistensi/status', ('GET',)) in rute)

    # --- Setelan round-trip ---
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, Setelan
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    eng = create_engine(f'sqlite:///{tmp}/uji.db')
    Base.metadata.create_all(eng)
    db = sessionmaker(bind=eng)()
    hasil = {
        'peta_sidik': 'abc123',
        'diperiksa_pada': '2026-11-19T09:00:00+00:00',
        'vonis': [
            {'nama': 'masalah_tujuan', 'label': 'Masalah ke Tujuan',
             'vonis': 'nyambung', 'alasan': 'Tujuan menjawab pertanyaan.'},
            {'nama': 'tujuan_hipotesis', 'label': 'Tujuan ke Hipotesis',
             'vonis': 'ragu', 'alasan': 'Belum bisa diputuskan.'},
        ],
        'langkah_berikut': 'Cek sambungan yang belum bisa diputuskan ke pembimbing.',
    }
    RK.simpan_hasil(db, 81, hasil)
    muat = RK.muat_hasil(db, 81)
    t('setelan: simpan + muat hasil',
      muat is not None and muat['peta_sidik'] == 'abc123'
      and len(muat['vonis']) == 2)
    t('setelan: muat fid lain None', RK.muat_hasil(db, 999) is None)
    baris = db.get(Setelan, RK.KUNCI_HASIL.format(fid=81))
    baris.nilai = '{rusak'
    t('setelan: JSON rusak dibaca None', RK.muat_hasil(db, 81) is None)
    db.close()

    # --- Panel di naskah.html ---
    tpl = (ROOT / 'app' / 'templates' / 'naskah.html').read_text(
        encoding='utf-8')
    t('panel: tombol Cek Konsistensi ada',
      'data-konsistensi' in tpl and 'Cek Konsistensi' in tpl)
    t('panel: wadah panel-konsistensi ada',
      'panel-konsistensi-' in tpl and 'panel-konsistensi' in tpl)
    t('panel: fetch status + mulai-latar ada',
      '/v1/konsistensi/status' in tpl
      and '/v1/konsistensi/mulai-latar' in tpl)
    t('panel: tiga status (nyambung/putus/ragu) ada',
      'nyambung' in tpl and 'putus' in tpl and 'ragu' in tpl)
    # Cek yang ketat: blok JS konsistensi (kemunculan TERAKHIR marker,
    # yang pertama ada di komentar CSS) tidak memakai kata 'salah'
    # sebagai label tampil.
    bagian_js = tpl.split('Cek Konsistensi antar bab (19 Nov 2026)')[-1] \
        .split('</script>')[0]
    t('panel: JS konsistensi tidak menampilkan kata "salah"',
      'salah' not in bagian_js.lower())

    print(f'\n{lulus}/{total} lulus')
    return 0 if lulus == total else 1


if __name__ == '__main__':
    sys.exit(main())
