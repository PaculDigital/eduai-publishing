"""GERBANG TATA PARAGRAF & VARIASI — SOT 20 Okt 2026.

Menguji `tata_paragraf.py` (murni fungsi) + pemeriksaan DOCX hasil rakit.

Cara kerja: sehat HARUS lulus, lalu DIBUAT SAKIT harus gagal.
Gerbang yang tidak bisa gagal = gerbang hiasan.
"""
import json
import os
import sys

sys.path.insert(0, '/app')
import tata_paragraf as T

LULUS, GAGAL = [], []


def cek(nama, syarat, ket=''):
    (LULUS if syarat else GAGAL).append(nama)
    print(('  LULUS ' if syarat else '  GAGAL ') + nama + (' | ' + ket if ket else ''))


# ═══ A. PEMECAH KALIMAT ══════════════════════════════════════════════════
print('\nA. PEMECAH KALIMAT')
kal = T.pecah_kalimat('Ini kalimat satu. Ini kalimat dua! Apakah tiga? Ya.')
cek('A1 empat kalimat terpecah', len(kal) == 4, f'dapat {len(kal)}')

kal = T.pecah_kalimat('Air mendidih pada suhu 100 derajat. Uapnya naik ke atas.')
cek('A2 angka tidak memecah kalimat', len(kal) == 2, f'dapat {len(kal)}')

kal = T.pecah_kalimat('Penelitian ini dilakukan oleh Prof. Dr. Wulan, M.Kom. Hasilnya baik.')
cek('A3 singkatan Prof./Dr. tidak memecah', len(kal) == 2, f'dapat {len(kal)}: {kal}')

kal = T.pecah_kalimat('Lihat hlm. 12 untuk detail. Lalu baca No. 5.')
cek('A4 hlm./No. tidak memecah', len(kal) == 2, f'dapat {len(kal)}: {kal}')

kal = T.pecah_kalimat('Nilai 3.14 dan 2.5 penting. Ini kalimat kedua.')
cek('A5 desimal tidak memecah', len(kal) == 2, f'dapat {len(kal)}: {kal}')

cek('A6 teks kosong → list kosong', T.pecah_kalimat('') == [])

# ═══ B. PEMECAH PARAGRAF ═════════════════════════════════════════════════
print('\nB. PEMECAH PARAGRAF (SOT 2.7: maks 7 kalimat / 200 kata)')
pendek = 'Satu. Dua. Tiga.'
cek('B1 paragraf pendek TIDAK dipecah', T.pecah_paragraf(pendek) == [pendek])

panjang = ' '.join([f'Ini kalimat nomor {i} yang cukup panjang isinya.' for i in range(1, 15)])
hasil = T.pecah_paragraf(panjang)
cek('B2 paragraf 14 kalimat DIPECAH', len(hasil) > 1, f'jadi {len(hasil)} paragraf')
cek('B3 tiap hasil ≤ 7 kalimat',
    all(len(T.pecah_kalimat(p)) <= 7 for p in hasil),
    f'maks {max(len(T.pecah_kalimat(p)) for p in hasil)}')
cek('B4 tidak ada kalimat hilang',
    len(' '.join(hasil).split('.')) == len(panjang.split('.')),
    'jumlah titik sama')
cek('B5 tidak ada paragraf 1 kalimat di ekor',
    len(T.pecah_kalimat(hasil[-1])) >= 2,
    f'ekor {len(T.pecah_kalimat(hasil[-1]))} kalimat')

cek('B6 perlu_dipecah: 14 kalimat = True', T.perlu_dipecah(panjang) is True)
cek('B7 perlu_dipecah: 3 kalimat = False', T.perlu_dipecah(pendek) is False)

# ═══ C. DETEKSI DAFTAR ═══════════════════════════════════════════════════
print('\nC. DETEKSI DAFTAR')
cek('C1 teks biasa bukan daftar', T.ada_daftar('Ini paragraf biasa saja.') is False)
cek('C2 "• " dikenali daftar', T.ada_daftar('• Satu\n• Dua') is True)
cek('C3 "1. " dikenali daftar', T.ada_daftar('1. Satu\n2. Dua') is True)
cek('C4 "a) " dikenali daftar', T.ada_daftar('a) Satu\nb) Dua') is True)

# ═══ D. UBAH JADI DAFTAR ═════════════════════════════════════════════════
print('\nD. VARIASI: PARAGRAF → DAFTAR')
sama = ('Air memiliki banyak manfaat. Air menjaga suhu tubuh tetap stabil. '
        'Air membantu pencernaan makanan. Air melancarkan peredaran darah.')
d = T.jadikan_daftar(sama, 'poin')
cek('D1 paragraf hal setara → daftar', d is not None, (d or '')[:60])
cek('D2 hasil 4 butir', d and len(d.split('\n')) == 4, f'{len(d.split(chr(10))) if d else 0} butir')
cek('D3 pakai penanda •', d and d.startswith('•'))
cek('D4 tanda baca SERAGAM (semua titik atau semua tanpa)',
    d and len({b.strip()[-1] for b in d.split('\n')}) == 1,
    f'akhir: {sorted({b.strip()[-1] for b in d.split(chr(10))}) if d else []}')

narasi = ('Kegiatan ini dilaksanakan pada hari Senin di aula sekolah dengan '
          'melibatkan seluruh siswa kelas empat yang antusias mengikuti '
          'seluruh rangkaian acara dari awal sampai akhir tanpa kendala.')
cek('D5 narasi panjang TIDAK dipaksa jadi daftar', T.jadikan_daftar(narasi) is None)
cek('D6 kurang dari 3 kalimat tidak jadi daftar',
    T.jadikan_daftar('Satu hal. Dua hal.') is None)

# ═══ E. VARIASI BERUNTUN ═════════════════════════════════════════════════
print('\nE. SISIP VARIASI (maks 4 paragraf beruntun tanpa variasi)')
#  Paragraf 10 kalimat > ambang 7 ⇒ WAJIB dipecah saat masuk buku.
narasi_panjang = ' '.join([f'Kalimat {i} menjelaskan bagian pengamatan ini.' for i in range(1, 11)])
blok = T.sisip_variasi([narasi_panjang] * 8)
jenis = [b[0] for b in blok]
cek('E1 paragraf 10 kalimat DIPECAH saat masuk buku', len(blok) > 8,
    f'{len(blok)} blok dari 8 paragraf')

#  Pagar penting: narasi 6 kalimat (di bawah ambang) TIDAK boleh dipecah
#  dan TIDAK boleh dipaksa jadi daftar — biar tetap paragraf utuh.
narasi_wajar = ('Pengamatan dilakukan dengan cermat oleh seluruh peserta. '
                'Mereka mencatat setiap perubahan cuaca hari itu. '
                'Catatan kemudian dibandingkan dengan data sebelumnya. '
                'Hasilnya menunjukkan pola yang cukup jelas dan berulang. '
                'Pola itu lalu dicatat dalam tabel pengamatan harian. '
                'Tabel tersebut menjadi bahan diskusi pertemuan berikutnya.')
blok_w = T.sisip_variasi([narasi_wajar] * 4)
cek('E1b narasi wajar 6 kalimat TIDAK dipecah/didaftarkan',
    all(j == 'paragraf' for j, _ in blok_w),
    f'jenis: {[j for j, _ in blok_w]}')

sama2 = ('Matahari menyinari bumi. Angin bertiup dari laut. Awan bergerak pelan. '
         'Hujan turun ke tanah.')
blok2 = T.sisip_variasi([sama2] * 5)
ada_daftar_blok = any(b[0] == 'daftar' for b in blok2)
cek('E2 paragraf hal setara → jadi daftar', ada_daftar_blok,
    f'jenis: {[b[0] for b in blok2]}')

beruntun_maks = 0
kini = 0
for j, _ in blok2:
    if j == 'paragraf':
        kini += 1
        beruntun_maks = max(beruntun_maks, kini)
    else:
        kini = 0
cek('E3 paragraf beruntun ≤ 4', beruntun_maks <= 4, f'maks {beruntun_maks}')

# ═══ F. TANPA KARANGAN ═══════════════════════════════════════════════════
print('\nF. PAGAR: TIDAK MENGARANG ISI')
asli = set(w.lower() for w in sama.replace('.', ' ').split())
hasil_d = T.jadikan_daftar(sama)
baru = set(w.lower() for w in hasil_d.replace('•', ' ').replace('.', ' ').split())
cek('F1 tidak ada kata baru', baru <= asli, f'kata tambahan: {baru - asli or "tidak ada"}')

teks_uji = ' '.join([f'Kalimat {i} berisi keterangan penting.' for i in range(1, 20)])
kata_asli = T.jumlah_kata(teks_uji)
kata_hasil = sum(T.jumlah_kata(p) for p in T.pecah_paragraf(teks_uji))
cek('F2 pecah paragraf tidak ubah jumlah kata', kata_asli == kata_hasil,
    f'{kata_asli} → {kata_hasil}')

# ═══ G. ANGKA SOT (yang dipakai DOCX) ════════════════════════════════════
print('\nG. ANGKA SOT')
cek('G1 inden = 1 em 11 pt (BUKAN 0)', T.INDEN_EM == 11.0, f'{T.INDEN_EM}')
cek('G2 maks kalimat = 7', T.PARA_MAKS_KALIMAT == 7, f'{T.PARA_MAKS_KALIMAT}')
cek('G3 maks kata = 200', T.PARA_MAKS_KATA == 200, f'{T.PARA_MAKS_KATA}')
cek('G4 maks paragraf beruntun = 4', T.MAKS_BERUNTUN_TANPA_VARIASI == 4,
    f'{T.MAKS_BERUNTUN_TANPA_VARIASI}')
cek('G5 maks butir poin = 7', T.MAKS_BUTIR_POIN == 7)
cek('G6 maks butir nomor = 10', T.MAKS_BUTIR_NOMOR == 10)

# ═══ H. TANDA BACA BUTIR SERAGAM ═════════════════════════════════════════
print('\nH. TANDA BACA BUTIR (SOT 4.3)')
kal_lengkap = ('Air menjaga suhu tubuh. Air membantu pencernaan. '
               'Air melancarkan darah.')
d2 = T.jadikan_daftar(kal_lengkap)
semua_titik = d2 and all(b.strip().endswith('.') for b in d2.split('\n'))
cek('H1 butir kalimat lengkap → SEMUA berakhir titik', semua_titik,
    repr(d2))
kapital = d2 and all(b.strip()[2].isupper() for b in d2.split('\n'))
cek('H2 butir kalimat lengkap → diawali kapital', kapital, repr(d2))

# ═══ HASIL ═══════════════════════════════════════════════════════════════
print('\n' + '=' * 60)
print(json.dumps({'lulus': len(LULUS), 'gagal': len(GAGAL),
                  'rincian_gagal': GAGAL}, ensure_ascii=False))
sys.exit(0 if not GAGAL else 1)
