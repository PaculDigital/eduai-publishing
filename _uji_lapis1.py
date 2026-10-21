"""UJI LAPIS 1 — DETEKSI JENIS DOKUMEN (app/jenis.py)

Uji dengan DOKUMEN NYATA (bukan karangan) + kasus sintetis untuk jenis yang
belum punya contoh (artikel jurnal, proposal, dokumen umum).

Dijalankan DI DALAM container produksi:
    docker cp _uji_lapis1.py eduai-app:/app/ && docker exec -w /app eduai-app \
        python3 _uji_lapis1.py
"""
import sys
sys.path.insert(0, '/app')

from pathlib import Path                       # noqa: E402
from app import ai as AI                       # noqa: E402
from app import jenis as J                     # noqa: E402

CONTOH = '/app/_contoh-dokumen'

# ── Dokumen NYATA (harapan: apa yang seharusnya terdeteksi) ────────────────
NYATA = [
    (f'{CONTOH}/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx',
     'skripsi', 'S1 UNMUL (template resmi)'),
    (f'{CONTOH}/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx',
     'skripsi', 'S1 Kedokteran UNHAS (dari PDF)'),
    (f'{CONTOH}/tesis-s2/TESIS-S2-unhas-sastra-novel.docx',
     'tesis', 'S2 Sastra UNHAS'),
    (f'{CONTOH}/tesis-s2/TESIS-S2-unhas-pendidikan-bahasa.docx',
     'tesis', 'S2 Pendidikan Bahasa UNHAS'),
    (f'{CONTOH}/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx',
     'tesis', 'S2 Manajemen UNHAS'),
    (f'{CONTOH}/disertasi-s3/DISERTASI-S3-unhas-kesehatan-stunting.docx',
     'disertasi', 'S3 Kesehatan UNHAS (323 hal)'),
    ('/app/uploads/5/acuan_tesis.docx', 'tesis', 'TESIS BOS (proposal 1.1-1.9)'),
]

# ── Sintetis: jenis yang belum punya contoh nyata ─────────────────────────
SINTETIS = [
    ('artikel_jurnal', 'artikel jurnal gaya polos', """
Judul: Pengaruh Kualitas Layanan terhadap Kepuasan Pelanggan UMKM
Keywords: kualitas layanan; kepuasan; UMKM

Pendahuluan
Penelitian ini bertujuan menganalisis pengaruh kualitas layanan terhadap
kepuasan pelanggan. Artikel ini disusun untuk disubmit ke Jurnal Manajemen
Indonesia Vol. 12. Data dikumpulkan dari 150 responden.

Metode
Penelitian ini menggunakan pendekatan kuantitatif dengan regresi berganda.

Hasil dan Pembahasan
Uji t menunjukkan koefisien determinasi sebesar 0,62. Hasil penelitian
menunjukkan bahwa kualitas layanan berpengaruh signifikan.

Simpulan
Kualitas layanan berpengaruh positif terhadap kepuasan pelanggan.
"""),
    ('proposal', 'proposal penelitian (bab I-III)', """
PROPOSAL PENELITIAN
Pengaruh Digital Marketing terhadap Kinerja UMKM di Kota Makassar

BAB I PENDAHULUAN
1.1 Latar Belakang
Usaha mikro kecil dan menengah menghadapi tantangan pemasaran digital.

BAB II TINJAUAN PUSTAKA
2.1 Landasan Teori
Technology Acceptance Model menjelaskan penerimaan teknologi.

BAB III METODE PENELITIAN
3.1 Jenis Penelitian
Penelitian ini akan menggunakan pendekatan kuantitatif.
3.2 Populasi dan Sampel
Populasi adalah pelaku UMKM.
"""),
    ('dokumen_umum', 'perjanjian kerja sama', """
SURAT PERJANJIAN KERJA SAMA
Nomor: 001/PKS/IX/2026

Pada hari ini, Senin tanggal satu bulan September tahun dua ribu dua puluh
enam, yang bertanda tangan di bawah ini:

1. Pihak Pertama: PT Maju Bersama, berkedudukan di Makassar.
2. Pihak Kedua: CV Karya Digital, berkedudukan di Gowa.

Pasal 1
Ruang lingkup kerja sama meliputi penyediaan layanan teknologi informasi.

Pasal 2
Jangka waktu perjanjian ini adalah 12 bulan sejak tanggal ditandatangani.
"""),
    ('dokumen_umum', 'nota dinas / invoice', """
NOTA DINAS
Kepada: Kepala Bagian Keuangan
Dari: Staf Administrasi
Perihal: Pengajuan Pembayaran

Sehubungan dengan pengadaan peralatan kantor, bersama ini diajukan
pembayaran sebagai berikut:

INVOICE No: INV/2026/0912
Jumlah: Rp 12.500.000
Terbilang: dua belas juta lima ratus ribu rupiah

Demikian nota dinas ini disampaikan.
"""),
    ('dokumen_umum', 'SOP prosedur', """
STANDAR OPERASIONAL PROSEDUR
PENGELOLAAN SURAT MASUK

1. Tujuan
Poin 1. Menjelaskan tata cara pengelolaan surat masuk.
2. Ruang Lingkup
Poin 2. Berlaku untuk seluruh unit kerja.
3. Prosedur
Poin 3. Surat diterima lalu dicatat dalam buku agenda.
"""),
]


def main() -> int:
    lulus = gagal = 0
    print('═' * 74)
    print('UJI LAPIS 1 — DETEKSI JENIS DOKUMEN')
    print('═' * 74)

    print('\n── A. DOKUMEN NYATA ─────────────────────────────────────────')
    for path, harap, ket in NYATA:
        p = Path(path)
        if not p.exists():
            print(f'  LEWAT  {ket} (berkas tidak ada)')
            continue
        teks = AI._teks_dari_berkas(p, p.name)
        h = J.deteksi(teks, p.name)
        ok = (h.jenis == harap)
        tanda = 'OK  ' if ok else 'GAGAL'
        print(f'  {tanda} {ket}')
        print(f'         jenis={h.jenis} (harap {harap}) | kategori={h.kategori} '
              f'| yakin={h.yakin} | {len(teks):,} kar')
        if not ok:
            print(f'         skor: {dict(sorted(h.skor.items(), key=lambda x: -x[1])[:4])}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    print('\n── B. SINTETIS (jenis tanpa contoh nyata) ───────────────────')
    for harap, ket, teks in SINTETIS:
        h = J.deteksi(teks, f'{harap}-uji.txt')
        ok = (h.jenis == harap)
        tanda = 'OK  ' if ok else 'GAGAL'
        print(f'  {tanda} {ket}')
        print(f'         jenis={h.jenis} (harap {harap}) | kategori={h.kategori} '
              f'| yakin={h.yakin}')
        if not ok:
            print(f'         skor: {dict(sorted(h.skor.items(), key=lambda x: -x[1])[:4])}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    print('\n── C. ATURAN KEYAKINAN (salah jenjang = naskah RUSAK) ───────')
    # Tanpa kata jenjang sama sekali → WAJIB ragu (supaya user ditanya 1x)
    netral = 'BAB I\nLatar Belakang\n' + ('Penelitian ini membahas sesuatu. ' * 30)
    h = J.deteksi(netral, 'naskah.docx')
    ok = (not h.yakin) and h.jenis in J.JENIS_AKADEMIK or h.jenis == J.JENIS_UMUM
    print(f'  {"OK  " if ok else "GAGAL"} naskah tanpa kata jenjang → '
          f'yakin={h.yakin} (harus False bila akademik)')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    # Catatan: deteksi jenjang dari cover yang jelas → WAJIB yakin
    jelas = ('DISERTASI\n\nDiajukan untuk Memenuhi Salah Satu Syarat Memperoleh\n'
             'Gelar Doktor\n\nBAB I PENDAHULUAN\n' + ('Isi bahasan. ' * 60))
    h = J.deteksi(jelas, 'x.docx')
    ok = h.jenis == 'disertasi' and h.yakin
    print(f'  {"OK  " if ok else "GAGAL"} cover "DISERTASI" tegas → '
          f'{h.jenis}, yakin={h.yakin}')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    # Tesis bos: kata TESIS 35x MAGISTER 14x → harus yakin
    p = Path('/app/uploads/5/acuan_tesis.docx')
    if p.exists():
        teks = AI._teks_dari_berkas(p, p.name)
        h = J.deteksi(teks, p.name)
        ok = h.jenis == 'tesis' and h.yakin
        print(f'  {"OK  " if ok else "GAGAL"} tesis Bos → {h.jenis}, yakin={h.yakin}')
        lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    print('\n── D. BLOK PROMPT (yang disisip ke prompt AI) ───────────────')
    h = J.deteksi(AI._teks_dari_berkas(
        Path(f'{CONTOH}/disertasi-s3/DISERTASI-S3-unhas-kesehatan-stunting.docx'),
        'd.docx'), 'd.docx')
    blok = J.blok_prompt(h)
    ok = ('DISERTASI' in blok.upper() or 'S3' in blok) and 'WAJIB' in blok
    print(f'  {"OK  " if ok else "GAGAL"} blok prompt memuat aturan S3 '
          f'({len(blok)} kar)')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)
    h_umum = J.deteksi(SINTETIS[2][2], 'pks.txt')
    blok_umum = J.blok_prompt(h_umum)
    ok = 'DILARANG' in blok_umum and 'BAB' in blok_umum
    print(f'  {"OK  " if ok else "GAGAL"} blok prompt dokumen umum memuat '
          f'larangan struktur BAB')
    lulus, gagal = (lulus + 1, gagal) if ok else (lulus, gagal + 1)

    print('\n' + '═' * 74)
    print(f'HASIL: {lulus} LULUS / {gagal} GAGAL')
    print('═' * 74)
    return 0 if gagal == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
