"""Rute Cek Bahasa: Setelan round-trip + endpoint + panel (20 Nov 2026).

Tidak memanggil LLM dan tidak menyentuh DB live. Setelan diuji lewat
SQLite sementara (pola test_format_rute.py). Panel diuji lewat
teks template naskah.html (tombol + wadah + fetch status/mulai-latar).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import rute_bahasa as RB


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
    rute = {(r.path, tuple(r.methods or [])) for r in RB.router.routes}
    t('rute: POST /v1/bahasa/mulai-latar ada',
      ('/v1/bahasa/mulai-latar', ('POST',)) in rute)
    t('rute: GET /v1/bahasa/status ada',
      ('/v1/bahasa/status', ('GET',)) in rute)

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
        'diperiksa_pada': '2026-11-20T09:00:00+00:00',
        'ringkasan': {'lulus': 2, 'tidak': 3, 'ragu': 1},
        'temuan': [
            {'id': 'saya', 'label': 'Kata saya/aku/kita', 'vonis': 'tidak',
             'alasan': 'Ditemukan 1 kali di paragraf isi (contoh: Kita).',
             'lokasi': ''},
            {'id': 'aktif', 'label': 'Kalimat aktif', 'vonis': 'ragu',
             'alasan': '82 dari 455 kalimat tampak aktif (contoh: penulis '
                       'melakukan). Perlu diperiksa, mesin tidak bisa '
                       'memastikan kalimat pasif.',
             'lokasi': ''},
        ],
        'langkah_berikut': 'Perbaiki dulu: Kata saya/aku/kita, Kata '
                           '"dimana", Awalan di-/ke- menempel.',
    }
    RB.simpan_hasil(db, 81, hasil)
    muat = RB.muat_hasil(db, 81)
    t('setelan: simpan + muat hasil',
      muat is not None and muat['sidik_berkas'] == 'abc123'
      and len(muat['temuan']) == 2
      and muat['ringkasan'] == {'lulus': 2, 'tidak': 3, 'ragu': 1})
    t('setelan: muat fid lain None', RB.muat_hasil(db, 999) is None)
    baris = db.get(Setelan, RB.KUNCI_HASIL.format(fid=81))
    baris.nilai = '{rusak'
    t('setelan: JSON rusak dibaca None', RB.muat_hasil(db, 81) is None)
    db.close()

    # --- Panel di naskah.html ---
    tpl = (ROOT / 'app' / 'templates' / 'naskah.html').read_text(
        encoding='utf-8')
    t('panel: tombol Cek Bahasa ada',
      'data-bahasa' in tpl and 'Cek Bahasa' in tpl)
    t('panel: wadah panel-bahasa ada',
      'panel-bahasa-' in tpl and 'panel-bahasa' in tpl)
    t('panel: fetch status + mulai-latar ada',
      '/v1/bahasa/status' in tpl
      and '/v1/bahasa/mulai-latar' in tpl)
    t('panel: tiga status (lulus/tidak/ragu) ada',
      'lulus' in tpl and 'tidak' in tpl and 'ragu' in tpl)
    # Cek yang ketat: blok JS bahasa tidak memakai kata 'salah' sebagai
    # label tampil.
    bagian_js = tpl.split('Cek Bahasa Pedoman (20 Nov 2026)')[-1] \
        .split('</script>')[0]
    t('panel: JS bahasa tidak menampilkan kata "salah"',
      'salah' not in bagian_js.lower())

    # --- Rute terdaftar di main.py ---
    main_py = (ROOT / 'app' / 'main.py').read_text(encoding='utf-8')
    t('main: rute_bahasa didaftarkan',
      'rute_bahasa' in main_py and 'rute_bahasa.router' in main_py)

    print(f'\n{lulus}/{total} lulus')
    return 0 if lulus == total else 1


if __name__ == '__main__':
    sys.exit(main())
