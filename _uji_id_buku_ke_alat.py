"""UJI BERGIGI — ID buku diterjemahkan & alat dijaga di rute /buku/susun.

ACC Bos 19 Okt 2026: "harus punya id sendiri ... agar menggunakan jev dan
hakim tepat dan tidak salah alat".

Yang diuji (Rp 0, tanpa AI, tanpa sentuh produksi):
  [1] Terjemahan kartu → ID: 'buku-umum' → 'buku_umum' (BUKAN 'buku-umum')
  [2] SEMUA kartu siap di app/buku.py punya ID yang dikenal app/jenis.py
  [3] ID karangan / kosong → '' (pemanggil menolak, tidak menebak)
  [4] Untuk setiap ID buku: jev & hakim MATI, mutu_buku HIDUP
  [5] Jaring pengaman rute: kalau tabel PORSI_ALAT dirusak (buku→jev),
      rute /buku/susun HARUS menolak SEBELUM memotong kuota
  [6] Sumber kode: rute benar-benar memanggil _buku.id_dokumen + _porsi
      (bukan cuma niat di komentar)

Jalankan:
  cd /opt/data/services/eduai-publishing
  /opt/data/.venv/bin/python _uji_id_buku_ke_alat.py
"""
import os
import re
import sys

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
    akar = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, akar)
    from app import buku as B
    from app import jenis as J

    print('\n[1] TERJEMAHAN KARTU → ID DOKUMEN')
    cek("'buku-umum' → 'buku_umum'", B.id_dokumen('buku-umum') == 'buku_umum',
        B.id_dokumen('buku-umum'))
    cek("'buku-umum' BUKAN 'buku-umum' (strip tidak bocor ke identitas)",
        B.id_dokumen('buku-umum') != 'buku-umum')
    cek("'book-chapter' → 'book_chapter'",
        B.id_dokumen('book-chapter') == 'book_chapter', B.id_dokumen('book-chapter'))

    print('\n[2] SEMUA KARTU SIAP PUNYA ID YANG DIKENAL')
    for k in B.JENIS_BUKU:
        kode = k['kode']
        if not k.get('siap'):
            print(f'  ⏭️  {kode}: siap=False (dilewati — belum bisa dijalankan)')
            continue
        id_dok = B.id_dokumen(kode)
        cek(f'{kode}: punya ID', bool(id_dok), 'id_dokumen() mengembalikan kosong')
        cek(f'{kode}: ID ada di jenis.JENIS_BUKU', id_dok in J.JENIS_BUKU, id_dok)
        cek(f'{kode}: ID ada di jenis.PORSI_ALAT', id_dok in J.PORSI_ALAT, id_dok)
        cek(f'{kode}: ID ada di jenis.STANDAR', id_dok in J.STANDAR, id_dok)

    # Kartu yang siap JANGAN ada yang tertinggal tanpa ID
    siap = [k['kode'] for k in B.JENIS_BUKU if k.get('siap')]
    cek(f'semua kartu siap ({len(siap)}) punya ID', all(B.id_dokumen(k) for k in siap),
        [k for k in siap if not B.id_dokumen(k)])

    print('\n[3] ID KARANGAN / KOSONG → KOSONG (tidak menebak)')
    for aneh in ('', None, 'buku', 'buku-barang', 'novel', 'BUKU-UMUM', '  '):
        cek(f'id_dokumen({aneh!r}) == ""', B.id_dokumen(aneh) == '',
            repr(B.id_dokumen(aneh)))
    cek("id_dokumen('BUKU-UMUM') == '' (huruf besar tidak diterima diam-diam)",
        B.id_dokumen('BUKU-UMUM') == '')

    print('\n[4] PORSI ALAT UNTUK SETIAP ID BUKU')
    for k in B.JENIS_BUKU:
        id_dok = B.id_dokumen(k['kode'])
        if not id_dok:
            continue
        p = J.porsi_alat(id_dok)
        cek(f'{id_dok}: jev MATI', p['jev'] is False, f"jev={p['jev']}")
        cek(f'{id_dok}: hakim MATI', p['hakim'] is False, f"hakim={p['hakim']}")
        cek(f'{id_dok}: mutu_buku HIDUP', p['mutu_buku'] is True, f"mutu={p['mutu_buku']}")

    print('\n[5] JARING PENGAMAN RUTE — tabel dirusak, rute WAJIB menolak')
    # Tiru logika penjaga di rute tanpa menjalankan FastAPI/DB:
    # kalau porsi bilang jev/hakim HIDUP untuk sebuah ID buku → tolak.
    for k in B.JENIS_BUKU:
        id_dok = B.id_dokumen(k['kode'])
        if not id_dok:
            continue
        p = J.porsi_alat(id_dok)
        ditolak = bool(p['jev'] or p['hakim'])
        cek(f'{id_dok}: penjaga TIDAK menolak (tabel sehat)', ditolak is False)
    # Sekarang suntik: tiru tabel rusak
    rusak = dict(J.PORSI_ALAT[J.JENIS_BUKU_UMUM])
    rusak['jev'] = True
    cek('kalau buku_umum diberi jev=True, penjaga HARUS menolak',
        bool(rusak['jev'] or rusak['hakim']) is True)

    print('\n[6] SUMBER KODE — rute benar-benar memanggil penjaga')
    main_py = os.path.join(akar, 'app', 'main.py')
    src = open(main_py, encoding='utf-8').read()
    # Ambil badan fungsi buku_susun saja (dari def sampai route berikutnya).
    # ⚠️ JANGAN pakai pola `def buku_susun\((.*?)\n@_router` — badan fungsi
    #    TIDAK memuat "\n@_router", jadi regex gagal dan `badan` jadi ''.
    #    Uji versi pertama lolos 54/0 walau penjaga DICABUT = gerbang palsu
    #    (terbukti lewat suntikan 19 Okt 2026).
    m = re.search(r"def buku_susun\(.*?(?=\n@_router|\Z)", src, re.S)
    badan = m.group(0) if m else ''
    # 🚨 JEBAKAN TERUKUR 19 Okt 2026 (gerbang PALSU): nama fungsi di KOMENTAR
    #    ikut terhitung ⇒ suntikan "penjaga dicabut" LOLOS 55/0. Uji wajib
    #    memeriksa KODE saja, bukan komentar. Buang komentar + docstring dulu.
    kode_saja = re.sub(r"#.*", "", badan)
    kode_saja = re.sub(r'""".*?"""', "", kode_saja, flags=re.S)
    cek('badan fungsi buku_susun berhasil dibaca (bukan kosong)',
        len(kode_saja) > 300,
        f'panjang={len(kode_saja)} — regex gagal, uji di bawah tidak bermakna')
    cek('rute buku_susun memanggil _buku.id_dokumen(',
        '_buku.id_dokumen(' in kode_saja)
    cek('rute buku_susun memanggil porsi_alat(', 'porsi_alat' in kode_saja)
    cek('rute MENOLAK kalau id_dok kosong', "if not id_dok:" in kode_saja)
    cek('rute MENOLAK kalau jev/hakim hidup untuk buku',
        "porsi['jev'] or porsi['hakim']" in kode_saja)
    # Penjaga harus SEBELUM pemotongan kuota (kuota ada di penyusunan_buku.susun)
    if 'porsi_alat' in kode_saja and '_susun.susun(' in kode_saja:
        cek('penjaga dipasang SEBELUM _susun.susun(',
            kode_saja.index('porsi_alat') < kode_saja.index('_susun.susun('),
            'penjaga setelah potong kuota = user bisa dirugikan')
    else:
        cek('penjaga dipasang SEBELUM _susun.susun(', False,
            'penjaga atau pemanggil kuota tidak ada di rute')

    print(f'\n{"="*62}\nID BUKU → ALAT: {LULUS} LULUS / {GAGAL} GAGAL\n{"="*62}')
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
