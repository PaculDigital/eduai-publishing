"""Rute Cek Format: Setelan round-trip + endpoint + panel (19 Nov 2026).

Tidak memanggil LLM dan tidak menyentuh DB live. Setelan diuji lewat
SQLite sementara (pola test_pustaka_periksa.py). Panel diuji lewat
teks template naskah.html (tombol + wadah + fetch status/mulai-latar).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import rute_format as RF


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
    rute = {(r.path, tuple(r.methods or [])) for r in RF.router.routes}
    t('rute: POST /v1/format/mulai-latar ada',
      ('/v1/format/mulai-latar', ('POST',)) in rute)
    t('rute: GET /v1/format/status ada',
      ('/v1/format/status', ('GET',)) in rute)

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
        'sidik_berkas': 'abc123',
        'diperiksa_pada': '2026-11-19T09:00:00+00:00',
        'ringkasan': {'lulus': 5, 'tidak': 2, 'ragu': 1},
        'temuan': [
            {'id': 'margin', 'label': 'Margin', 'vonis': 'ragu',
             'alasan': 'Margin seksi 1 tidak tertulis di berkas.', 'lokasi': 'Seksi 1'},
            {'id': 'tabel', 'label': 'Keterangan tabel', 'vonis': 'tidak',
             'alasan': '17 dari 17 keterangan tabel tidak rata kiri (contoh: Tabel 1.1).',
             'lokasi': 'Tabel 1.1'},
        ],
        'langkah_berikut': 'Perbaiki dulu: Keterangan tabel.',
    }
    RF.simpan_hasil(db, 81, hasil)
    muat = RF.muat_hasil(db, 81)
    t('setelan: simpan + muat hasil',
      muat is not None and muat['sidik_berkas'] == 'abc123'
      and len(muat['temuan']) == 2
      and muat['ringkasan'] == {'lulus': 5, 'tidak': 2, 'ragu': 1})
    t('setelan: muat fid lain None', RF.muat_hasil(db, 999) is None)
    baris = db.get(Setelan, RF.KUNCI_HASIL.format(fid=81))
    baris.nilai = '{rusak'
    t('setelan: JSON rusak dibaca None', RF.muat_hasil(db, 81) is None)
    db.close()

    # --- Panel di naskah.html ---
    tpl = (ROOT / 'app' / 'templates' / 'naskah.html').read_text(
        encoding='utf-8')
    t('panel: tombol Cek Format ada',
      'data-format' in tpl and 'Cek Format' in tpl)
    t('panel: wadah panel-format ada',
      'panel-format-' in tpl and 'panel-format' in tpl)
    t('panel: fetch status + mulai-latar ada',
      '/v1/format/status' in tpl
      and '/v1/format/mulai-latar' in tpl)
    t('panel: tiga status (lulus/tidak/ragu) ada',
      'lulus' in tpl and 'tidak' in tpl and 'ragu' in tpl)
    # Cek yang ketat: blok JS format tidak memakai kata 'salah' sebagai
    # label tampil.
    bagian_js = tpl.split('Cek Format Pedoman (19 Nov 2026)')[-1] \
        .split('</script>')[0]
    t('panel: JS format tidak menampilkan kata "salah"',
      'salah' not in bagian_js.lower())

    # --- Rute terdaftar di main.py ---
    main_py = (ROOT / 'app' / 'main.py').read_text(encoding='utf-8')
    t('main: rute_format didaftarkan',
      'rute_format' in main_py and 'rute_format.router' in main_py)

    print(f'\n{lulus}/{total} lulus')
    return 0 if lulus == total else 1


if __name__ == '__main__':
    sys.exit(main())
