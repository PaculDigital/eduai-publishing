"""UJI JALUR PENUH — buktikan DOKUMEN FINAL bebas penanda & bebas salinan.

KENAPA UJI INI ADA (16Sep26):
    `_uji_pembersih.py` menguji FUNGSI `bersihkan_jawaban_ai()` langsung.
    `_uji_komentar_pembimbing.py` melihat JAWABAN MENTAH AI (sebelum pembersih).
    DUA-DUANYA **TIDAK** membuktikan dokumen yang diterima mahasiswa bersih.

    Uji ini meniru JALUR PRODUKSI (app/ai.py baris 1170-1225):
        potong_cerdas -> _revisi_dengan_failover -> _valid
        -> bersihkan_jawaban_ai(konten, potongan) -> gabung
    lalu memeriksa HASIL AKHIR yang akan ditulis ke .docx.

CARA JALAN: docker exec -w /app eduai-app python3 _uji_jalur_penuh.py
"""
import asyncio
import sys

sys.path.insert(0, '/app')

from app import ai as AI  # noqa: E402
from app.state import petakan  # noqa: E402

NASKAH_UJI = """BAB I
PENDAHULUAN

A. Latar Belakang

Stunting masih menjadi masalah gizi utama di Indonesia. Data Riset Kesehatan
Dasar menunjukkan prevalensi stunting nasional sebesar 30,8 persen pada 2018.
Pemerintah menargetkan penurunan hingga 14 persen pada 2024 melalui strategi
intervensi gizi spesifik dan sensitif bagi keluarga risiko stunting.

B. Rumusan Masalah

Berdasarkan latar belakang di atas, rumusan masalah penelitian ini adalah
bagaimana variasi spasial dan determinan stunting pada balita di Kabupaten XXX.

C. Tujuan Penelitian

Penelitian ini bertujuan menganalisis variasi spasial kejadian stunting dan
mengidentifikasi determinan yang paling berpengaruh terhadap kejadian tersebut.
"""

# Penanda SISTEM yang DILARANG muncul di dokumen mahasiswa.
# CATATAN (16Sep26): kata "Guardrail"/"cakupan"/"Profil" TIDAK dimasukkan ke sini
# — uji pembersih membuktikan kata-kata itu muncul di kalimat SAH ("Profil
# responden...", "Cakupan penelitian ini...") sehingga menandainya sebagai
# pelanggaran = uji palsu-GAGAL. Yang benar-benar dilarang = PENANDA BERKURUNG
# dan pasangan kunci=nilai milik sistem.
TERLARANG = ['[PROFIL]', '[K1', '[K2', 'K1-CAKUPAN', 'CAKUPAN:',
             'Paradigma=', 'Desain=', 'jenis_dokumen=', 'kategori=']

SKENARIO = [
    ('A. komentar biasa (perkaya paragraf)',
     'Tolong perdalam latar belakang dengan data terbaru.'),
    ('B. komentar pada bagian yang SUDAH benar',
     'Bagian ini sudah bagus, tidak perlu diubah.'),
    ('C. komentar minta data yang TIDAK ADA',
     'Tambahkan nilai R-square dan p-value dari hasil analisis.'),
]


async def jalankan_jalur_produksi(naskah: str, komentar: str, peta) -> str:
    """Tiru app/ai.py 1170-1225 — JALUR YANG SAMA dengan produksi."""
    potongan_list = AI.potong_cerdas(naskah)
    hasil_bagian = []
    for i, potongan in enumerate(potongan_list, start=1):
        user_msg = (
            f'[PETA DOKUMEN]\n'
            + '\n'.join(f"  {p['section_id']:10s} {p['section_title'][:32]:32s} "
                        f"{p['char_count']:,} kar" for p in peta)
            + f'\n\n[KOMENTAR MAHASISWA]\n{komentar}\n\n'
            + f'[NASKAH BAGIAN {i}/{len(potongan_list)}]\n{potongan}'
        )
        # ️ DIPERBARUI 16Sep26: _revisi_dengan_failover() kini mengembalikan
        # TIGA nilai (konten, nama_model, info_usage) — dipakai untuk rumus
        # Token Revisi ÷10.000 yang butuh token nyata. Uji lama masih unpack 2.
        konten, _model, _usage = await AI._revisi_dengan_failover(user_msg, 1)
        konten = AI.bersihkan_jawaban_ai(konten, potongan)
        hasil_bagian.append(konten)
    if len(hasil_bagian) == 1:
        return hasil_bagian[0]
    return '\n\n'.join(f'[K{i}]\n{h}' for i, h in enumerate(hasil_bagian, start=1))


async def main():
    print('=' * 76)
    print('UJI JALUR PENUH — DOKUMEN AKHIR BEBAS PENANDA & BEBAS SALINAN')
    print('=' * 76)
    peta = petakan(NASKAH_UJI)
    print(f'peta: {len(peta)} bagian | naskah {len(NASKAH_UJI):,} kar')
    print()

    lulus = gagal = 0
    for nama, komentar in SKENARIO:
        print('-' * 76)
        print(nama)
        try:
            dokumen = await jalankan_jalur_produksi(NASKAH_UJI, komentar, peta)
        except Exception as e:  # noqa: BLE001
            print(f'   ❌ GAGAL PANGGIL: {type(e).__name__}: {e}')
            gagal += 1
            continue

        ketemu = [t for t in TERLARANG if t in dokumen]
        if ketemu:
            print(f'   ❌ PENANDA MASUK DOKUMEN: {ketemu}')
            gagal += 1
        else:
            print('   ✅ bersih dari penanda sistem')
            lulus += 1

        kalimat = [k.strip() for k in NASKAH_UJI.split('.') if len(k.strip()) > 120]
        dobel = [k[:45] for k in kalimat if dokumen.count(k.strip()) > 1]
        if dobel:
            print(f'   ❌ NASKAH TERSALIN DOBEL: {dobel[:2]}')
            gagal += 1
        else:
            print('   ✅ tidak ada salinan naskah dobel')
            lulus += 1

        print(f'   panjang dokumen akhir: {len(dokumen):,} kar')
        print(f'   --- 200 kar pertama ---\n   {dokumen[:200]!r}')
        print()

    print('=' * 76)
    print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
    print('=' * 76)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
