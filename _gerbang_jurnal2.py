"""GERBANG JURNAL-2 (06Okt26) — uji app/jurnal.py (simpan/baca/hitung).

Uji SUNGGUHAN fungsi produksi, bukan pura-pura.
  J1. kunci() — DOI / Garuda / judul+tahun
  J2. sidik() — berubah kalau judul atau kk berubah
  J3. tambah() — dedup, tanpa dobel
  J4. PAGAR batas 8 manual per bab (inti putusan Bos)
  J5. hitungan manual PER BAB (bukan global)
  J6. hapus()
  J7. pakai ulang antar bab (tanpa hitung dobel)
  J8. layak_sitasi / tidak_layak (pagar P3 dipertahankan)
  J9. baca()/tulis() tahan JSON rusak & kolom kosong
  J10. jurnal.py TIDAK menyentuh pustaka.py (pemisahan tugas)

Cara pakai (di dalam container): cd /app && python3 _gerbang_jurnal2.py
"""
from __future__ import annotations

import sys

sys.path.insert(0, '/app')

from app import jurnal as J                                       # noqa: E402

lulus = 0
gagal = 0


def cek(nama: str, syarat: bool, bukti: str = '') -> None:
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  LULUS  {nama}')
    else:
        gagal += 1
        print(f'  GAGAL  {nama}  {bukti}')


def art(doi: str = '', gid: int | None = None, judul: str = 'J',
        tahun: int = 2020, status: str = 'verified') -> dict:
    return {'title': judul, 'authors': 'A', 'year': tahun, 'journal': 'Jr',
            'doi': doi, 'garuda_id': gid, 'doi_status': status}


# ── J1: kunci ──
def j1() -> None:
    cek('J1a DOI jadi kunci', J.kunci(art(doi='10.1/a')) == 'doi:10.1/a')
    cek('J1b DOI https://doi.org/ dinormalkan',
        J.kunci(art(doi='https://doi.org/10.1/a')) == 'doi:10.1/a')
    cek('J1c DOI huruf besar → kecil',
        J.kunci(art(doi='10.1/A')) == 'doi:10.1/a')
    cek('J1d tanpa DOI → pakai Garuda',
        J.kunci(art(gid=1662547)) == 'garuda:1662547')
    cek('J1e tanpa keduanya → judul+tahun',
        J.kunci(art(judul='Harga', tahun=2019)) == 'judul:harga|2019')
    cek('J1f DOI menang atas Garuda',
        J.kunci(art(doi='10.1/a', gid=99)) == 'doi:10.1/a')


# ── J2: sidik ──
def j2() -> None:
    a = J.sidik('Pengaruh Harga', 'harga, promosi')
    cek('J2a sama → sidik sama',
        a == J.sidik('Pengaruh Harga', 'harga, promosi'))
    cek('J2b spasi/huruf besar diabaikan',
        a == J.sidik('  pengaruh harga  ', 'HARGA, promosi'))
    cek('J2c kk beda → sidik beda', a != J.sidik('Pengaruh Harga', 'harga'))
    cek('J2d judul beda → sidik beda', a != J.sidik('Pengaruh Promosi', 'harga, promosi'))
    cek('J2e sidik 64 huruf', len(a) == 64)


# ── J3: dedup ──
def j3() -> None:
    d = {}
    d = J.tambah(d, 'BAB II', [art(doi='10.1/a'), art(doi='10.1/b')])
    cek('J3a 2 artikel masuk', len(J.daftar(d, 'BAB II')) == 2)
    d = J.tambah(d, 'BAB II', art(doi='10.1/a'))      # dobel
    cek('J3b artikel kembar TIDAK dobel', len(J.daftar(d, 'BAB II')) == 2)
    d = J.tambah(d, 'BAB II', art(doi='10.1/c'))
    cek('J3c artikel baru masuk', len(J.daftar(d, 'BAB II')) == 3)
    cek('J3d tiap artikel punya kunci',
        all('kunci' in a for a in J.daftar(d, 'BAB II')))


# ── J4: PAGAR BATAS 8 (inti) ──
def j4() -> None:
    d = {}
    for i in range(7):
        d = J.tambah(d, 'BAB II', art(doi=f'10.1/m{i}'), asal='manual')
    cek('J4a 7 manual terpasang', J.jumlah_manual(d, 'BAB II') == 7)
    cek('J4b masih boleh tambah (7<8)', J.boleh_tambah_manual(d, 'BAB II'))
    cek('J4c sisa slot = 1', J.sisa_slot_manual(d, 'BAB II') == 1)
    d = J.tambah(d, 'BAB II', art(doi='10.1/m7'), asal='manual')
    cek('J4d artikel ke-8 masuk', J.jumlah_manual(d, 'BAB II') == 8)
    cek('J4e setelah 8 → TIDAK boleh', not J.boleh_tambah_manual(d, 'BAB II'))
    d = J.tambah(d, 'BAB II', art(doi='10.1/m8'), asal='manual')
    cek('J4f artikel ke-9 DITOLAK (tetap 8)', J.jumlah_manual(d, 'BAB II') == 8)
    cek('J4g artikel ke-9 tidak ada di daftar',
        all(J.kunci(a) != 'doi:10.1/m8' for a in J.daftar(d, 'BAB II')))
    # artikel AI tidak dihitung ke batas
    d2 = {}
    d2 = J.tambah(d2, 'BAB II', [art(doi=f'10.1/ai{i}') for i in range(30)],
                  asal='ai')
    cek('J4h 30 artikel AI → manual tetap 0', J.jumlah_manual(d2, 'BAB II') == 0)
    cek('J4i AI tidak makan slot manual', J.sisa_slot_manual(d2, 'BAB II') == 8)
    cek('J4j BATAS_MANUAL_PER_BAB = 8', J.BATAS_MANUAL_PER_BAB == 8)


# ── J5: hitungan PER BAB ──
def j5() -> None:
    d = {}
    d = J.tambah(d, 'BAB II', [art(doi=f'10.1/x{i}') for i in range(8)], asal='manual')
    cek('J5a BAB II penuh (8)', J.jumlah_manual(d, 'BAB II') == 8)
    cek('J5b BAB IV masih kosong', J.jumlah_manual(d, 'BAB IV') == 0)
    cek('J5c BAB IV boleh tambah 8 lagi', J.boleh_tambah_manual(d, 'BAB IV'))
    d = J.tambah(d, 'BAB IV', art(doi='10.1/y0'), asal='manual')
    cek('J5d BAB IV punya 1 manual', J.jumlah_manual(d, 'BAB IV') == 1)
    cek('J5e BAB II tetap 8 (per bab, bukan global)',
        J.jumlah_manual(d, 'BAB II') == 8)


# ── J6: hapus ──
def j6() -> None:
    d = {}
    d = J.tambah(d, 'BAB II', [art(doi='10.1/a'), art(doi='10.1/b')], asal='manual')
    d = J.hapus(d, 'BAB II', 'doi:10.1/a')
    cek('J6a artikel terhapus', len(J.daftar(d, 'BAB II')) == 1)
    cek('J6b hitungan manual ikut turun', J.jumlah_manual(d, 'BAB II') == 1)
    cek('J6c yang tersisa benar',
        J.kunci(J.daftar(d, 'BAB II')[0]) == 'doi:10.1/b')


# ── J7: pakai ulang antar bab ──
def j7() -> None:
    d = {}
    d = J.tambah(d, 'BAB II', art(doi='10.1/a'), asal='manual')
    cek('J7a dipakai hanya di BAB II',
        J.sudah_dipakai_di(d, 'doi:10.1/a') == ['BAB II'])
    d = J.pakai_di(d, 'BAB II', 'BAB IV', 'doi:10.1/a')
    cek('J7b muncul juga di BAB IV',
        any(J.kunci(a) == 'doi:10.1/a' for a in J.daftar(d, 'BAB IV')))
    cek('J7c tercatat di 2 bab',
        sorted(J.sudah_dipakai_di(d, 'doi:10.1/a')) == ['BAB II', 'BAB IV'])
    cek('J7d pakai ulang TIDAK menambah hitungan manual',
        J.jumlah_manual(d, 'BAB IV') == 0)
    d = J.pakai_di(d, 'BAB II', 'BAB IV', 'doi:10.1/a')   # ulang lagi
    cek('J7e pakai ulang dua kali tidak dobel',
        len([a for a in J.daftar(d, 'BAB IV') if J.kunci(a) == 'doi:10.1/a']) == 1)
    d = J.pakai_di(d, 'BAB II', 'BAB III', 'doi:tidak-ada')
    cek('J7f artikel tak dikenal → tidak berubah',
        len(J.daftar(d, 'BAB III')) == 0)


# ── J8: pagar P3 (hanya terverifikasi) ──
def j8() -> None:
    d = {}
    d = J.tambah(d, 'BAB II', [
        art(doi='10.1/ok', status='verified'),
        art(doi='10.1/gr', gid=123, status='no_doi'),
        art(doi='10.1/bad', status='unverified'),
        art(doi='10.1/nd', status='no_doi'),          # no_doi tanpa garuda
    ])
    layak = J.layak_sitasi(d)
    cek('J8a yang layak = 2 (verified + garuda)', len(layak) == 2)
    cek('J8b unverified TIDAK layak',
        all(J.kunci(a) != 'doi:10.1/bad' for a in layak))
    cek('J8c no_doi tanpa garuda TIDAK layak',
        all(J.kunci(a) != 'doi:10.1/nd' for a in layak))
    cek('J8d tidak_layak menampung 2', len(J.tidak_layak(d)) == 2)
    cek('J8e semua_artikel = 4', len(J.semua_artikel(d)) == 4)
    cek('J8f terverifikasi() benar',
        J.terverifikasi({'doi_status': 'verified'})
        and not J.terverifikasi({'doi_status': 'unverified'}))


# ── J9: tahan data aneh ──
def j9() -> None:
    class P:
        jurnal_json = ''
        jurnal_sidik = ''
    cek('J9a kolom kosong → {}', J.baca(P()) == {})

    class P2:
        jurnal_json = '{rusak banget'
        jurnal_sidik = ''
    cek('J9b JSON rusak → {} (tidak lempar)', J.baca(P2()) == {})

    class P3:
        jurnal_json = '[1,2,3]'          # list, bukan dict
        jurnal_sidik = ''
    cek('J9c JSON list → {} (bukan dict)', J.baca(P3()) == {})
    cek('J9d prof None → {}', J.baca(None) == {})

    class P4:
        jurnal_json = ''
        jurnal_sidik = ''
    p = P4()
    J.tulis(p, {'BAB II': [art(doi='10.1/a')]}, sidik='abc')
    cek('J9e tulis() mengisi jurnal_json', 'BAB II' in p.jurnal_json)
    cek('J9f tulis() mengisi jurnal_sidik', p.jurnal_sidik == 'abc')
    cek('J9g round-trip tulis→baca', J.daftar(J.baca(p), 'BAB II')[0]['doi'] == '10.1/a')

    class P5:
        jurnal_json = ''
        jurnal_sidik = ''
    p5 = P5()
    J.tulis(p5, {}, sidik=J.sidik('J', 'k'))
    cek('J9h sidik_cocok True bila sama', J.sidik_cocok(p5, 'J', 'k'))
    cek('J9i sidik_cocok False bila judul beda', not J.sidik_cocok(p5, 'Lain', 'k'))
    cek('J9j sidik_cocok False bila kolom kosong',
        not J.sidik_cocok(P(), 'J', 'k'))


# ── J10: pemisahan tugas ──
def j10() -> None:
    """Diperbarui 06Okt26 (langkah 3): jurnal.py BOLEH memanggil mesin
    (`pustaka.cari_semua`) — itu memang tugas jembatannya. Yang tetap
    DILARANG: menyentuh mesin pencari secara langsung di dalam fungsinya
    sendiri lewat impor tingkat-atas yang berbahaya, atau menyentuh DB.

    Pemisahan tugas yang benar:
      · `pustaka.py` = MESIN (pencarian) — jurnal.py HANYA memanggil
      · `jurnal.py`  = INGATAN + JEMBATAN (tidak mengubah pustaka)
      · `models.py`  = TABEL + hitungan siklus
    """
    from pathlib import Path
    isi = Path('/app/app/jurnal.py').read_text(encoding='utf-8')
    cek('J10a jurnal.py memanggil mesin lewat impor DI DALAM fungsi '
        '(bukan tingkat-atas)', 'from . import pustaka' in isi)
    cek('J10b jurnal.py TIDAK mengimpor pustaka di tingkat-atas berkas',
        '\nfrom . import pustaka' not in isi.split('def ')[0])
    cek('J10c jurnal.py tidak menyentuh DB/sqlite langsung',
        'sqlite' not in isi and 'INSERT' not in isi)
    p = Path('/app/app/pustaka.py').read_text(encoding='utf-8')
    cek('J10d pustaka.py TIDAK memanggil modul jurnal (mesin tetap mandiri)',
        'import jurnal' not in p and 'from . import jurnal' not in p
        and 'PencarianManual' not in p)
    cek('J10e doktrin pemisahan tugas tertulis',
        'MESIN PENCARI' in isi and 'INGATAN' in isi)


def main() -> int:
    print('=== GERBANG JURNAL-2 — app/jurnal.py ===')
    for fn in (j1, j2, j3, j4, j5, j6, j7, j8, j9, j10):
        fn()
    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
