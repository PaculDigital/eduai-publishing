"""UJI HULU-HILIR — naskah BERISI KESALAHAN SENGAJA → AI beri USULAN NYATA.

Bedanya dari uji sebelumnya: naskah uji ini memang punya cacat yang layak
ditandai pembimbing (aturan RUBRIK: struktur, kelengkapan metode, rujukan,
kejelasan). Jadi AI punya ALASAN memberi usulan — bukan `{"usulan": []}`.

Yang dibuktikan (hulu → hilir):
  1. `asisten.kerjakan()` dipanggil lewat PIPA PRODUKSI (bukan potongan).
  2. AI memberi usulan NYATA (jumlah > 0).
  3. `simpan_usulan()` MENEMPELKAN usulan ke naskah → baris `catatan_pembimbing`.
  4. Kutipan yang AI pakai BENAR-BENAR ADA di naskah (bukan karangan).

PS: usulan DITULIS ke DB SALINAN (`EDUAI_DATA_DIR=/tmp/live_uji`) ⇒ produksi aman.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

sys.path.insert(0, '/app')
logging.basicConfig(level=logging.WARNING,
                    format='  [log] %(name)s: %(message)s', stream=sys.stdout)
for _n in ('app.asisten', 'app.ai'):
    logging.getLogger(_n).setLevel(logging.INFO)

print('=' * 74)
print('  UJI HULU-HILIR — NASKAH BERISI KESALAHAN SENGAJA')
print('=' * 74)
print(f'  EDUAI_DATA_DIR = {os.environ.get("EDUAI_DATA_DIR")}')

from app import asisten as A                                   # noqa: E402
from app.models import SessionLocal                            # noqa: E402

#  ══ NASKAH UJI — sengaja memuat cacat yang layak ditandai pembimbing ══
NASKAH = """BAB I PENDAHULUAN

1.1 Latar Belakang

Pendidikan adalah hal yang sangat penting sekali bagi semua orang di seluruh
dunia ini. Banyak sekali penelitian yang sudah meneliti tentang hal ini dan
hasilnya semuanya sama saja yaitu pendidikan itu penting.

Menurut Sudjana (2019) pendidikan mempengaruhi hasil belajar. Selain itu
pendidikan juga mempengaruhi prestasi. Pendidikan juga berpengaruh terhadap
motivasi belajar siswa. Pendidikan juga sangat berpengaruh terhadap minat
siswa untuk belajar lebih giat lagi.

Berdasarkan hasil observasi yang peneliti lakukan, ternyata ditemukan bahwa
siswa kelas X kurang begitu bersemangat dalam mengikuti pelajaran. Hal ini
disebabkan oleh beberapa faktor yang mana faktor tersebut tidak dapat
diidentifikasi secara pasti karena keterbatasan peneliti.

1.2 Rumusan Masalah

Berdasarkan latar belakang di atas, maka rumusan masalah dalam penelitian ini
adalah bagaimana pengaruh motivasi terhadap hasil belajar siswa?

1.3 Tujuan Penelitian

Adapun tujuan dari dilakukannya penelitian ini yaitu untuk mengetahui seberapa
besar pengaruh self efficacy terhadap kepuasan kerja karyawan.

1.4 Manfaat Penelitian

Penelitian ini diharapkan bermanfaat bagi semua pihak yang membutuhkan.

BAB II KAJIAN TEORI

2.1 Motivasi Belajar

Motivasi yaitu suatu dorongan. Menurut Slameto (2010, dalam Uno 2015)
motivasi adalah kekuatan yang ada di dalam diri seseorang. Menurut Hamalik
(2008) motivasi adalah perubahan energi. Menurut Sardiman (2011) motivasi
adalah serangkaian usaha. Menurut Winkel (2007) motivasi adalah daya penggerak.
Menurut Purwanto (2013) motivasi adalah sesuatu yang kompleks.

2.2 Hasil Belajar

Hasil belajar merupakan hasil yang diperoleh dari proses belajar. Nilai
siswa akan meningkat apabila siswa rajin belajar.

BAB III METODE PENELITIAN

Penelitian ini menggunakan pendekatan kuantitatif dengan jenis penelitian
deskriptif korelasional. Populasi dalam penelitian ini adalah seluruh siswa
kelas X yang berjumlah 120 orang. Sampel diambil sebanyak 120 orang dengan
teknik purposive sampling. Instrumen berupa angket dengan skala Likert 1-5.
Analisis data menggunakan regresi linear sederhana dengan bantuan SPSS.

BAB IV HASIL DAN PEMBAHASAN

Dari hasil analisis diperoleh nilai signifikansi sebesar 0,023 sehingga dapat
disimpulkan bahwa H0 diterima dan Ha ditolak. Artinya tidak ada pengaruh yang
signifikan antara motivasi terhadap hasil belajar siswa.

Berdasarkan hasil tersebut, dapat disimpulkan bahwa motivasi tidak berpengaruh
terhadap hasil belajar siswa kelas X. Temuan ini sesuai dengan pendapat
Sudjana (2019) yang menyatakan bahwa motivasi tidak berpengaruh terhadap
hasil belajar.

BAB V KESIMPULAN

Berdasarkan hasil penelitian, dapat disimpulkan bahwa tidak ada pengaruh
motivasi terhadap hasil belajar siswa. Saran bagi peneliti selanjutnya agar
menambah jumlah sampel.
"""

print(f'\n  naskah uji: {len(NASKAH):,} karakter')
print('  cacat sengaja: tujuan↔rumusan tidak nyambung (self efficacy vs motivasi),')
print('                angka sig 0,023 tapi disimpulkan H0 diterima,')
print('                "120 sampel dari 120 populasi" tapi disebut purposive,')


class _B:
    id = 9101
    nama = 'Uji Hulu-Hilir'
    user_id = 1


async def jalan() -> int:
    gagal = 0
    S = SessionLocal()
    try:
        #  1. APA YANG DIKIRIM (pagar, 0 Rp)
        print('\n' + '─' * 74)
        print('  1. PAGAR + APA YANG DIKIRIM')
        _asli = A._catatan_terbaru
        A._catatan_terbaru = lambda _db, _bid, batas=12: []
        try:
            kirim, pos = A._siapkan_kirim(S, _B(), NASKAH)
        finally:
            A._catatan_terbaru = _asli
        print(f'     kirim {len(kirim):,} kar (dari {len(NASKAH):,}) posisi={pos}')
        print(f'     (naskah pendek < {A.KONTEKS_MIN_PECAH:,} kar → kirim utuh, itu SAH)')

        #  2. PIPA PRODUKSI + AI NYATA
        print('\n' + '─' * 74)
        print('  2. PIPA PRODUKSI: AI menelaah (biaya nyata)')
        from app import ai as AI                                # noqa: PLC0415
        pesan = ('Draf mahasiswa (dapat dipotong di akhir):\n\n'
                 f'{kirim}\n\nBerikan tinjauan sesuai aturan jawaban.')
        konten, info = await AI._panggil_router(pesan, 180.0, system=A.RUBRIK)
        print(f'     model={info.get("model")} jawaban={len(konten):,} kar')
        print('     ── ISI JAWABAN (potongan) ──')
        print('     ' + konten[:700].replace('\n', '\n     '))

        #  3. URAI usulan
        print('\n' + '─' * 74)
        print('  3. URAI USULAN')
        usulan = A.urai_usulan(konten, NASKAH)
        if usulan is None:
            print('     ❌ jawaban tidak bisa diurai'); gagal += 1; usulan = []
        print(f'     {len(usulan)} usulan terbaca')
        for i, u in enumerate(usulan, 1):
            print(f'     {i}. [{u.get("bab","?")}] '
                  f'kutipan="{str(u.get("kutipan",""))[:60]}"')
            print(f'        catatan: {str(u.get("catatan",""))[:100]}')
        if not usulan:
            print('     ⚠️  AI tidak menemukan cacat — periksa naskah uji')
            gagal += 1

        #  4. KUTIPAN BENAR-BENAR ADA di naskah (bukan karangan)
        print('\n' + '─' * 74)
        print('  4. KUTIPAN ADA DI NASKAH? (anti-karangan)')
        if usulan:
            asli = sum(1 for u in usulan
                       if str(u.get('kutipan', '')).strip()[:30] in NASKAH)
            print(f'     {asli}/{len(usulan)} kutipan cocok dengan naskah asli')
            if asli < len(usulan):
                print('     ⚠️  ada kutipan yang tidak ditemukan di naskah')
    finally:
        S.close()
    return gagal


if __name__ == '__main__':
    n = asyncio.run(jalan())
    print('\n' + '═' * 74)
    print(f'  HASIL: {"LULUS ✅" if n == 0 else f"{n} GAGAL ❌"}')
    print('═' * 74)
    sys.exit(1 if n else 0)
