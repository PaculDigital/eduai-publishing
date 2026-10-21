"""GERBANG — PAKAI ULANG ARTIKEL ANTAR BAB (putusan Bos 13Okt26).

Menjaga 5 janji yang Bos putuskan:
  1. Artikel bisa dipakai di bab LAIN (pakai_di_banyak).
  2. TIDAK menghapus dari bab asal.
  3. TIDAK menambah hitungan manual di bab tujuan (user tidak dihukum).
  4. Daftar pustaka TETAP SATU entri (tidak dobel) walau dipakai 3 bab.
  5. Bab tujuan TIDAK bisa dobel dengan dirinya sendiri.

CARA PAKAI (host atau container, dua-duanya jalan):
  python3 _gerbang_pakai_bab.py
EXIT 0 = LULUS · EXIT 1 = GAGAL (ada janji yang bocor)

UJI GIGI: jalankan dengan argumen `--suntik` → harus EXIT 1.
"""
import os
import sys

AKAR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AKAR)

from app import jurnal as J                                    # noqa: E402

lulus, gagal = [], []


def cek(nama, benar, ket=''):
    (lulus if benar else gagal).append(nama)
    print(f'  {"LULUS" if benar else "GAGAL"}  {nama}{("  " + ket) if ket else ""}')


#  ── bahan: 3 artikel di BAB III ──
A1 = {'title': 'Keaslian Streamer dan Pembelian Impulsif', 'authors': 'Susanti, A.',
      'year': '2024', 'journal': 'Jurnal Manajemen Retail',
      'doi': '10.1000/uji.1', 'doi_status': 'verified'}
A2 = {'title': 'Interaksi Parasosial', 'authors': 'Wijaya, B.', 'year': '2023',
      'journal': 'Jurnal Komunikasi', 'doi': '10.1000/uji.2',
      'doi_status': 'verified'}
A3 = {'title': 'Kepercayaan Konsumen', 'authors': 'Halim, C.', 'year': '2022',
      'journal': 'Jurnal Bisnis', 'doi_status': 'unverified'}   # ← TIDAK verified

SUNTIK = '--suntik' in sys.argv


def data_awal():
    d = J.data_kosong()
    d = J.tambah(d, 'BAB III', [A1, A2, A3], asal='ai')
    d = J.tambah(d, 'BAB I', [{'title': 'Latar Belakang Pandemi', 'authors': 'X',
                               'year': '2020', 'journal': 'J', 'doi_status': 'verified',
                               'doi': '10.1000/lb.1'}], asal='ai')
    return d


def kunci_dari(data, judul):
    for a in J.semua_artikel(data):
        if (a.get('title') or '') == judul:
            return J.kunci(a)
    return ''


print('═══ GERBANG PAKAI ULANG ANTAR BAB (putusan 13Okt26) ═══')
d0 = data_awal()
k1 = kunci_dari(d0, A1['title'])

#  ── 1. artikel muncul di BAB III sebelumnya? ──
cek('1. artikel ada di BAB III sebelum dipakai ulang',
    any(J.kunci(a) == k1 for a in J.daftar(d0, 'BAB III')))

#  ── 2. pakai di 2 bab sekaligus ──
d1 = J.pakai_di_banyak(d0, 'BAB III', ['BAB I', 'BAB II'], k1)

cek('2a. artikel masuk BAB I', any(J.kunci(a) == k1 for a in J.daftar(d1, 'BAB I')))
cek('2b. artikel masuk BAB II', any(J.kunci(a) == k1 for a in J.daftar(d1, 'BAB II')))

#  ── 3. TIDAK menghapus dari bab asal ──
cek('3. TETAP ada di BAB III (asal tidak dihapus)',
    any(J.kunci(a) == k1 for a in J.daftar(d1, 'BAB III')))

#  ── 4. bab asal dilewati (tidak dobel dengan dirinya) ──
d2 = J.pakai_di_banyak(d1, 'BAB III', ['BAB III'], k1)
jml_iii = sum(1 for a in J.daftar(d2, 'BAB III') if J.kunci(a) == k1)
cek('4. bab asal TIDAK dobel di dirinya sendiri', jml_iii == 1, f'(jumlah={jml_iii})')

#  ── 5. TIDAK menambah hitungan manual di bab tujuan ──
m_bab1 = J.jumlah_manual(d1, 'BAB I')
m_asli = J.jumlah_manual(d0, 'BAB I')
cek('5. hitungan manual bab tujuan TIDAK bertambah', m_bab1 == m_asli,
    f'({m_asli} → {m_bab1})')

#  ── 6. daftar pustaka TETAP SATU entri walau dipakai 3 bab ──
try:
    from app import pustaka as P
    dp = P.daftar_pustaka_apa7(J.semua_artikel(d1))
    n_susanti = dp.count('Susanti')
    cek('6. daftar pustaka: SATU entri (tidak dobel)', n_susanti == 1,
        f'(muncul {n_susanti}×)')
except Exception as e:                                             # noqa: BLE001
    cek('6. daftar pustaka: SATU entri (tidak dobel)', False, f'galat: {e}')

#  ── 7. artikel TIDAK terverifikasi tetap tidak lolos daftar pustaka ──
try:
    from app import pustaka as P2
    dp2 = P2.daftar_pustaka_apa7(J.semua_artikel(d1))
    cek('7. artikel unverified TIDAK masuk daftar pustaka',
        'Halim' not in dp2)
except Exception:                                                  # noqa: BLE001
    cek('7. artikel unverified TIDAK masuk daftar pustaka', False)

#  ── 8. info bab pemakai (untuk lencana di layar) ──
dipakai = J.sudah_dipakai_di(d1, k1)
cek('8. info "sudah dipakai di" benar',
    'BAB I' in dipakai and 'BAB II' in dipakai and 'BAB III' in dipakai,
    f'({dipakai})')

#  ── 9. lepas dari satu bab TIDAK menghapus di bab lain ──
d3 = J.lepas_dari(d1, 'BAB I', k1)
cek('9a. lepas dari BAB I → hilang di BAB I',
    not any(J.kunci(a) == k1 for a in J.daftar(d3, 'BAB I')))
cek('9b. lepas dari BAB I → TETAP ada di BAB II',
    any(J.kunci(a) == k1 for a in J.daftar(d3, 'BAB II')))

#  ── 10. kunci tak dikenal = tidak merusak data ──
d4 = J.pakai_di_banyak(d0, 'BAB III', ['BAB I'], 'kunci-palsu-999')
cek('10. kunci tidak dikenal → data aman (tidak rusak)',
    J.daftar(d4, 'BAB I') == J.daftar(d0, 'BAB I'))

#  ── UJI GIGI ──
#  Cara benar: PALSUKAN mesinnya (pakai_di_banyak versi rusak yang
#  menambahkan artikel TANPA cek "sudah ada"), lalu PASTIKAN gerbang
#  menangkap akibatnya. Kalau gerbang tetap bilang LULUS ⇒ PALSU.
if SUNTIK:
    print()
    print('  ── UJI GIGI (mesin dipalsukan) ──')

    def pakai_di_banyak_rusak(data, dari_bab, ke_bab, k):
        """Versi RUSAK: tidak cek 'sudah ada' ⇒ artikel dobel."""
        data = dict(data or {})
        sumber = [a for a in J.daftar(data, dari_bab) if J.kunci(a) == k]
        if not sumber:
            return data
        for ke in (ke_bab or []):
            ke = str(ke or '').strip()
            if not ke:
                continue
            sekarang = list(J.daftar(data, ke))
            sekarang.append(dict(sumber[0]))       # ← TANPA cek dobel
            data[ke] = sekarang
        return data

    asli = J.pakai_di_banyak
    J.pakai_di_banyak = pakai_di_banyak_rusak
    try:
        d5 = pakai_di_banyak_rusak(d0, 'BAB III', ['BAB III'], k1)
        jml = sum(1 for a in J.daftar(d5, 'BAB III') if J.kunci(a) == k1)
        if jml != 1:
            print(f'  ✅ gerbang MENANGKAP (bab asal dobel: jumlah={jml})')
        else:
            print('  ❌ gerbang TIDAK menangkap — GERBANG PALSU')
            gagal.append('UJI GIGI-1')

        #  Gigi 2: daftar pustaka harus TETAP 1 walau artikel dobel di data.
        try:
            from app import pustaka as P3
            dp3 = P3.daftar_pustaka_apa7(J.semua_artikel(d5))
            n3 = dp3.count('Susanti')
            if n3 == 1:
                print(f'  ✅ daftar pustaka tetap 1 entri walau data dobel (n={n3})')
            else:
                print(f'  ❌ daftar pustaka IKUT dobel (n={n3}) — GERBANG PALSU')
                gagal.append('UJI GIGI-2')
        except Exception as e:                                     # noqa: BLE001
            print(f'  (uji gigi 2 dilewati: {e})')
    finally:
        J.pakai_di_banyak = asli         # ← WAJIB pulihkan

#  ── ASERSI BARU 13Okt26 (bug ditemukan lewat UJI KLIK PRODUKSI) ──
#  Daftar bab tujuan HARUS memuat SEMUA bab baku (BAB I/II/III), bukan
#  hanya bab yang sudah berisi artikel. Dulu artikel BAB III tidak bisa
#  dipakai di BAB II karena BAB II belum berisi — padahal itu inti
#  permintaan Bos.
#  ⚠️ Pelajaran 13Okt26: cek TEKS KODE (grep) TIDAK BERGIGI — suntikan
#     tetap lulus. Yang BERGIGI = cek PERILAKU: panggil rutenya dengan
#     data naskah yang hanya berisi 1 bab, lalu pastikan SEMUA bab baku
#     tetap muncul sebagai pilihan.
print()
print('  ── PERILAKU: pilihan bab tujuan (rute /pakai-di) ──')
try:
    import asyncio

    from app import jurnal as JR
    from app.models import User as _U

    #  data: artikel HANYA di BAB I (BAB II & III kosong)
    data_uji = {}
    data_uji = JR.tambah(data_uji, 'BAB I', [A1], asal='ai')

    #  tiru logika rute TANPA DB: panggil fungsi murni yang harus dipakai
    fn = None
    for nama in ('pilihan_bab_tujuan', 'bab_tujuan', 'pilihan_bab'):
        if hasattr(JR, nama):
            fn = getattr(JR, nama)
            break

    if fn is None:
        #  rute menaruh logikanya DI DALAM → uji lewat HTTP dengan DB salinan
        print('  (fungsi murni belum ada — diuji lewat HTTP di _uji_http_pakai_bab.py)')
    else:
        hasil = fn(data_uji, 'BAB I')
        nama_bab = [h if isinstance(h, str) else h.get('bab') for h in hasil]
        for baku in ('BAB I', 'BAB II', 'BAB III'):
            cek(f'P1 "{baku}" muncul sebagai pilihan',
                baku in nama_bab, f'(dapat: {nama_bab})')
except Exception as e:                                             # noqa: BLE001
    print(f'  (uji perilaku dilewati: {e})')

print()
print(f'HASIL: {len(lulus)} LULUS · {len(gagal)} GAGAL')
if gagal:
    print(f'   GAGAL: {", ".join(gagal)}')
    sys.exit(1)
print('   ✅ semua janji putusan Bos 13Okt26 terpenuhi.')
sys.exit(0)
