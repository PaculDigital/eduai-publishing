"""Rute Cek Abstrak: Setelan round-trip + endpoint + panel (20 Nov 2026).

Tidak memanggil LLM dan tidak menyentuh DB live. Setelan diuji lewat
SQLite sementara (pola test_bahasa_rute.py). Panel diuji lewat teks
template naskah.html (tombol + wadah + fetch status/mulai-latar).
Rute cek abstrak tinggal di app/rute_bagian_awal.py (bukan berkas baru).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import rute_bagian_awal as RBA


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

    # --- Router: dua endpoint cek abstrak ---
    rute = {(r.path, tuple(r.methods or [])) for r in RBA.router.routes}
    t('rute: POST /v1/abstrak/mulai-latar ada',
      ('/v1/abstrak/mulai-latar', ('POST',)) in rute)
    t('rute: GET /v1/abstrak/status ada',
      ('/v1/abstrak/status', ('GET',)) in rute)
    t('rute: POST /v1/bagian-awal/mulai-latar tetap ada',
      ('/v1/bagian-awal/mulai-latar', ('POST',)) in rute)
    t('rute: GET /v1/bagian-awal/status tetap ada',
      ('/v1/bagian-awal/status', ('GET',)) in rute)

    # --- Setelan round-trip (SQLite sementara) ---
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.models import Base, Setelan
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    hasil = {'sidik_abstrak': 'abc123', 'peta_sidik': 'peta9',
             'diperiksa_pada': '2026-11-20T00:00:00+00:00',
             'ringkasan': {'cocok': 2, 'lulus': 2, 'tidak': 1, 'ragu': 0},
             'temuan': [{'nama': 'cocok_id', 'label': 'Abstrak cocok '
                         'dengan isi', 'vonis': 'cocok', 'alasan': 'x'}],
             'langkah_berikut': 'Perbaiki Panjang abstrak sesuai.'}
    RBA.simpan_hasil_abstrak(db, 81, hasil)
    muat = RBA.muat_hasil_abstrak(db, 81)
    t('setelan: simpan lalu muat sama',
      muat is not None and muat.get('sidik_abstrak') == 'abc123'
      and muat.get('ringkasan', {}).get('tidak') == 1)
    t('setelan: kunci hasil beda dari kunci draf abstrak',
      RBA.KUNCI_HASIL_ABSTRAK.format(fid=81)
      != 'bagian_awal_abstrak_81')
    t('setelan: fid lain -> None',
      RBA.muat_hasil_abstrak(db, 82) is None)
    # Menimpa hasil lama.
    hasil2 = dict(hasil, sidik_abstrak='zzz')
    RBA.simpan_hasil_abstrak(db, 81, hasil2)
    t('setelan: simpan kedua menimpa',
      RBA.muat_hasil_abstrak(db, 81).get('sidik_abstrak') == 'zzz')
    # Nilai rusak -> None.
    baris = db.get(Setelan, RBA.KUNCI_HASIL_ABSTRAK.format(fid=81))
    baris.nilai = 'bukan json {'
    db.commit()
    t('setelan: nilai rusak -> None',
      RBA.muat_hasil_abstrak(db, 81) is None)
    db.close()

    # --- Penanda proses ---
    t('proses: komentar Cek Abstrak dikenali',
      RBA._adalah_proses_cek_abstrak('["Cek Abstrak"]') is True)
    t('proses: komentar Abstrak AI bukan cek abstrak',
      RBA._adalah_proses_cek_abstrak('["Abstrak AI Bagian Awal"]')
      is False)
    t('proses: komentar Bagian Awal bukan cek abstrak',
      RBA._adalah_proses_cek_abstrak('["Lengkapi Bagian Awal"]')
      is False)

    # --- Panel naskah.html ---
    teks = (ROOT / 'app' / 'templates' / 'naskah.html').read_text()
    t('panel: tombol Cek Abstrak ada',
      'data-abstrak' in teks and 'Cek Abstrak' in teks)
    t('panel: wadah panel-abstrak ada',
      'panel-abstrak-' in teks and 'panel-abstrak' in teks)
    t('panel: fetch status + mulai-latar abstrak',
      "/v1/abstrak/status" in teks
      and "/v1/abstrak/mulai-latar" in teks)
    t('panel: CSS status cocok/lulus/tidak/ragu',
      '.panel-abstrak .baris-abstrak.cocok' in teks
      and '.panel-abstrak .baris-abstrak.ragu' in teks)
    t('panel: pesan belum ada abstrak',
      'Belum ada abstrak' in teks)
    t('panel: tanpa kata "salah" di JS abstrak',
      'salah' not in teks.split('Cek Abstrak (20 Nov 2026)')[1]
      .split('</script>')[0])

    print(f'\n{lulus}/{total} lulus')
    return 0 if lulus == total else 1


if __name__ == '__main__':
    raise SystemExit(main())
