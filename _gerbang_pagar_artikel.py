"""GERBANG PAGAR ARTIKEL (06Okt26) — jawaban "tanpa halusinasi" untuk Bos.

Yang diuji:
  P1  HANYA YANG ADA      — artikel berabstrak boleh jadi dasar temuan
  P2  TANDA ISI TERBATAS  — abstrak kosong → ditandai
  P3  TAMPILKAN SUMBER    — abstrak ikut bahan + aturan disisipkan
  P4  BAHAN NYATA         — tidak ada angka/penulis yang bukan dari artikel
  P5  KATA-KATA           — DILARANG menyuruh user "unduh sendiri"

MODE:
  python3 _gerbang_pagar_artikel.py            → normal
  python3 _gerbang_pagar_artikel.py --rusak N   → suntik kerusakan (uji bergigi)

Uji bergigi WAJIB (aturan Bos): kalau dirusak → HARUS ada GAGAL.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

AKAR = Path('/app') if Path('/app/app').exists() else Path(__file__).resolve().parent
sys.path.insert(0, str(AKAR))

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--rusak', type=int, default=0,
                    help='1..N — suntik kerusakan (uji bergigi)')
    arg = ap.parse_args()

    print('=== GERBANG PAGAR ARTIKEL ===')
    from app import pagar_artikel as P

    #  ── bahan uji ──────────────────────────────────────────────────────
    ART_PENUH = {
        'title': 'Pengaruh Kualitas Produk terhadap Keputusan Pembelian',
        'authors': 'Siti, A.; Budi, B.', 'year': 2021,
        'journal': 'Jurnal Manajemen', 'doi': 'https://doi.org/10.1/a',
        'doi_status': 'verified',
        'abstract': ('Penelitian ini menguji pengaruh kualitas produk terhadap '
                     'keputusan pembelian pada 200 responden. Hasil menunjukkan '
                     'kualitas produk berpengaruh positif signifikan (b=0,42; '
                     'p<0,01). Koefisien determinasi sebesar 0,31.'),
    }
    ART_KOSONG = {
        'title': 'Strategi Pemasaran Digital', 'authors': 'Ani, C.', 'year': 2020,
        'journal': 'Jurnal Bisnis', 'doi': '', 'doi_status': 'no_doi',
        'abstract': '',
    }
    ART_PENDEK = {
        'title': 'Catatan Singkat', 'authors': 'X', 'year': 2019,
        'journal': '', 'abstract': 'Singkat saja.',
    }

    #  ── kerusakan (uji bergigi) ────────────────────────────────────────
    if arg.rusak == 1:                    # pagar 1 dimatikan (semua dianggap layak)
        P.abstrak_ada = lambda a: True
    elif arg.rusak == 2:                  # penanda isi_terbatas dihapus
        P.isi_terbatas = lambda a: False
    elif arg.rusak == 3:                  # artikel tanpa abstrak IKUT jadi bahan
        P.bagi = lambda art: {'layak': [dict(a, isi_terbatas=False)
                                        for a in art if isinstance(a, dict)],
                              'terbatas': [],
                              'jumlah': {'layak': len(art), 'terbatas': 0,
                                         'total': len(art)}}

    #  ── P1: HANYA YANG ADA ─────────────────────────────────────────────
    cek('P1a artikel berabstrak → BOLEH jadi dasar',
        P.abstrak_ada(ART_PENUH) is True)
    cek('P1b abstrak KOSONG → TIDAK boleh jadi dasar',
        P.abstrak_ada(ART_KOSONG) is False)
    cek('P1c abstrak TERLALU PENDEK (<80) → TIDAK boleh',
        P.abstrak_ada(ART_PENDEK) is False)
    cek('P1d layak_sitasi() sejalan dgn abstrak_ada()',
        P.layak_sitasi(ART_PENUH) is True
        and P.layak_sitasi(ART_KOSONG) is False)

    #  ── P2: TANDA ISI TERBATAS ─────────────────────────────────────────
    ter = P.tandai([ART_PENUH, ART_KOSONG])
    cek('P2a artikel tanpa abstrak DITANDAI isi_terbatas',
        ter[1].get('isi_terbatas') is True)
    cek('P2b artikel berabstrak TIDAK ditandai',
        ter[0].get('isi_terbatas') is False)
    cek('P2c tandai() TIDAK mengubah masukan (murni)',
        'isi_terbatas' not in ART_PENUH)

    #  ── P3/P4: BAHAN NYATA + TAMPILKAN SUMBER ──────────────────────────
    bahan = P.teks_untuk_ai([ART_PENUH, ART_KOSONG], maks=8)
    cek('P3a judul artikel berabstrak ADA di bahan', 'Pengaruh Kualitas' in bahan)
    cek('P3b ABSTRAK ikut disertakan (tampilkan sumber)', 'ABSTRAK:' in bahan)
    cek('P3c artikel TANPA abstrak diberi bagian terpisah + larangan',
        'TANPA ABSTRAK' in bahan and 'JANGAN' in bahan)
    cek('P4a bahan memuat data NYATA (tahun + jurnal asli)',
        '2021' in bahan and 'Jurnal Manajemen' in bahan)
    #  ⚠️ TIDAK ada angka karangan di bahan
    angka_bahan = set(re.findall(r'\d+[.,]\d+', bahan))
    angka_asli = set(re.findall(r'\d+[.,]\d+', ART_PENUH['abstract']))
    cek('P4b TIDAK ada angka di bahan yang bukan dari abstrak',
        angka_bahan <= angka_asli, f'(asing: {angka_bahan - angka_asli})')

    #  ── aturan prompt ──────────────────────────────────────────────────
    atr = P.aturan_prompt()
    cek('P5a aturan prompt memuat "HANYA berdasarkan JUDUL dan ABSTRAK"',
        'HANYA berdasarkan JUDUL dan ABSTRAK' in atr)
    cek('P5b aturan prompt melarang menambah temuan/angka',
        'JANGAN menambah temuan' in atr)
    cek('P5c aturan prompt menyebut bagian TANPA ABSTRAK',
        'TANPA ABSTRAK' in atr)

    #  ── bagi() ─────────────────────────────────────────────────────────
    b = P.bagi([ART_PENUH, ART_KOSONG, ART_PENDEK])
    cek('P6a bagi(): 1 layak, 2 isi terbatas',
        b['jumlah'] == {'layak': 1, 'terbatas': 2, 'total': 3},
        f'({b["jumlah"]})')

    #  ── P7: KATA-KATA (dilarang menyuruh unduh sendiri) ───────────────
    rute = (AKAR / 'app/rute_jurnal.py').read_text(encoding='utf-8')
    cek('P7a rute /unduh TIDAK menyuruh user "unduh sendiri"',
        'sendiri ya' not in rute and 'membukanya sendiri' not in rute)
    cek('P7b rute memakai frase "Tautannya kami sertakan"',
        'Tautannya kami sertakan' in rute)
    cek('P7c ada pesan utk abstrak kosong (isi terbatas)',
        'Abstrak artikel ini tidak dicantumkan' in rute)
    cek('P7d ada pesan utk artikel tersedia di penerbit',
        'tersedia di penerbit' in rute)

    #  ── P8: is_oa tidak lagi diTEBAK di jalur Garuda ──────────────────
    pst = (AKAR / 'app/pustaka.py').read_text(encoding='utf-8')
    i = pst.find('def tautan_garuda')
    j = pst.find('def lengkapi_tautan')
    blok = pst[i:j]
    cek('P8a tautan_garuda TIDAK menyetel is_oa=True (dulu TEBAKAN)',
        'is_oa\': True' not in blok and "'is_oa': True" not in blok)
    blok2 = pst[j:pst.find('def ', j + 10)]
    cek('P8b lengkapi_tautan TIDAK menyetel is_oa=True',
        "a['is_oa'] = True" not in blok2)

    #  ── P9: kerangka menyambungkan pagar ───────────────────────────────
    kk = (AKAR / 'app/kerangka.py').read_text(encoding='utf-8')
    cek('P9a kerangka memakai pagar_artikel',
        'pagar_artikel' in kk and '_pa.tandai' in kk)
    cek('P9b kerangka mengirim bahan_ai + aturan_ai',
        "'bahan_ai'" in kk and "'aturan_ai'" in kk)
    cek('P9c info pagar melaporkan artikel layak & terbatas',
        'artikel_layak' in kk and 'artikel_isi_terbatas' in kk)

    #  ── P10: TANDA ISI TERBATAS SAMPAI KE HALAMAN (06Okt26, permintaan Bos) ──
    rj = (AKAR / 'app/rute_jurnal.py').read_text(encoding='utf-8')
    cek('P10a rute /lihat menandai artikel (pagar_artikel.tandai)',
        '_pa.tandai(artikel)' in rj)
    html = (AKAR / 'app/templates/referensi.html').read_text(encoding='utf-8')
    cek('P10b halaman menampilkan lencana "isi terbatas"',
        'isi terbatas' in html and 'lencana batas' in html)
    cek('P10c halaman menampilkan ABSTRAK (pagar 3: user bisa membuktikan)',
        'Lihat abstrak' in html and 'details class="abs"' in html)
    cek('P10d CSS lencana.batas ada', '.lencana.batas' in html)
    cek('P10e CSS blok abstrak ada', 'details.abs' in html)
    #  ikon yang dipakai HARUS ada di sprite (pelajaran 'spark' — jangan mengarang)
    sprite = (AKAR / 'app/static/ikon/lucide.svg').read_text(encoding='utf-8')
    for ic in ('alert-triangle', 'book-open'):
        cek(f'P10f ikon "{ic}" ADA di sprite', f'id="ik-{ic}"' in sprite)

    print(f'\nTOTAL: {lulus} LULUS / {gagal} GAGAL')
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
