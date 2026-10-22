#!/usr/bin/env python3
"""UJI UJUNG-KE-UJUNG GENERATOR: contoh_buku.json -> buku -> bukti setia.

Yang dibuktikan (bukan diklaim):
  1. Generator jalan & buku lolos gerbang (semua asersi).
  2. Semua bagian zip SELAIN document.xml, footer1, footer2, settings.xml,
     document.xml.rels BYTE-PER-BYTE identik dengan template — artinya
     styles, theme, numbering, gambar bawaan, sectPr TIDAK berubah.
     (v2: rels hanya bertambah relasi gambar baru; media gambar baru
     byte-identik dengan berkas sumbernya.)
  3. Isi baru benar-benar masuk: judul sampul, ISBN baru, judul bab dua
     baris, sub-sub bab; dan 'Lorem ipsum' template sudah tidak tersisa.
  4. Footer memuat judul & penulis baru; settings memuat updateFields.
  5. Template asli TIDAK berubah sesudah generator jalan (MD5 tetap).
"""
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
TEMPLATE = SKILL / 'templates' / 'template-buku-resmi.docx'
GENERATOR = HERE / 'buat_buku.py'
GERBANG = HERE / 'periksa_buku_template.py'
CONTOH = HERE / 'contoh_buku.json'
MD5_WAJIB = '0bb7bc5cdae9a99f489feb87387b64b6'
BOLEH_BEDA = {'word/document.xml', 'word/footer1.xml', 'word/footer2.xml',
              'word/settings.xml',
              # v2: rels berubah HANYA karena relasi gambar baru ditambahkan
              'word/_rels/document.xml.rels'}
MEDIA_BARU = {'word/media/buku1.png'}   # gambar dari contoh_buku.json (v2)

LULUS = GAGAL = 0


def cek(nama, syarat, info=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama} -> {info}')


md5_awal = hashlib.md5(TEMPLATE.read_bytes()).hexdigest()
cek('MD5 template sebelum generate', md5_awal == MD5_WAJIB, md5_awal)

with tempfile.TemporaryDirectory() as td:
    hasil = Path(td) / 'buku-hasil.docx'
    r = subprocess.run([sys.executable, str(GENERATOR), str(CONTOH), str(hasil),
                        '--tanpa-gerbang'], capture_output=True, text=True)
    cek('generator jalan (exit 0)', r.returncode == 0, r.stderr[-300:])
    if r.returncode != 0:
        print(r.stdout[-500:], r.stderr[-500:])
        sys.exit(1)

    g = subprocess.run([sys.executable, str(GERBANG), str(hasil)],
                       capture_output=True, text=True)
    cek('buku hasil lolos gerbang v2', g.returncode == 0,
        [ln for ln in g.stdout.splitlines() if 'GAGAL' in ln][:3])

    with zipfile.ZipFile(TEMPLATE) as z:
        asli = {n: z.read(n) for n in z.namelist()}
    with zipfile.ZipFile(hasil) as z:
        baru = {n: z.read(n) for n in z.namelist()}
    cek('daftar berkas zip = template + media gambar baru',
        set(baru) == set(asli) | MEDIA_BARU,
        f'beda: {set(asli) ^ set(baru)}')
    beda = [n for n in asli if n not in BOLEH_BEDA and asli[n] != baru[n]]
    cek('semua berkas selain yang diizinkan byte-identik', not beda, str(beda))
    contoh_png = (HERE / 'contoh_gambar.png').read_bytes()
    cek('media gambar baru byte-identik dengan berkas sumber',
        baru.get('word/media/buku1.png') == contoh_png)
    rels_baru = baru['word/_rels/document.xml.rels'].decode('utf-8')
    rels_asli = asli['word/_rels/document.xml.rels'].decode('utf-8')
    cek('rels lama utuh + 1 relasi gambar baru',
        rels_baru.replace('</Relationships>', '').startswith(
            rels_asli.replace('</Relationships>', '')[:200])
        and 'media/buku1.png' in rels_baru and rels_baru.count('<Relationship') ==
        rels_asli.count('<Relationship') + 1)

    doc = baru['word/document.xml'].decode('utf-8')
    cek('judul sampul masuk (huruf besar)', 'BELAJAR MENULIS BUKU PERTAMA' in doc)
    cek('ISBN baru masuk', '978-602-000-000-0' in doc)
    cek('judul bab I masuk', 'MEMULAI DENGAN PETA YANG JELAS' in doc)
    cek('sub-sub bab masuk', 'Menyiapkan Ruang Kerja' in doc)
    cek('tidak ada Lorem ipsum tersisa', 'Lorem ipsum' not in doc)
    cek('tidak ada placeholder tersisa',
        'TULIS JUDUL' not in doc and 'Tulis Nama Kamu' not in doc
        and '12345' not in doc)
    f2 = baru['word/footer2.xml'].decode('utf-8')
    cek('footer2 memuat judul baru', 'Belajar Menulis Buku Pertama' in f2)
    f1 = baru['word/footer1.xml'].decode('utf-8')
    cek('footer1 memuat penulis baru', 'Nama Penulis Contoh' in f1)
    st = baru['word/settings.xml'].decode('utf-8')
    cek('settings updateFields aktif', '<w:updateFields w:val="true"/>' in st)
    cek('teks cache daftar isi diperbarui',
        'BAB I MEMULAI DENGAN PETA YANG JELAS' in doc
        and 'JUDUL BAB PERTAMA' not in doc)
    # ── v2: tabel & gambar ──
    cek('tabel masuk (w:tbl + kepala F2F2F2)',
        '<w:tbl>' in doc and 'w:fill="F2F2F2"' in doc)
    cek('isi sel tabel masuk', 'Menentukan gagasan inti dan pembaca sasaran' in doc)
    cek('judul tabel masuk', 'Tabel 1.1 Contoh Tabel Tahapan Menulis' in doc)
    cek('gambar inline masuk (wp:inline + r:embed baru)',
        '<wp:inline' in doc and 'buku1.png' in rels_baru)
    cek('keterangan gambar masuk',
        'Gambar: Contoh diagram batang' in doc)

    # ── v2.1: mode gagal TIDAK meninggalkan berkas (cacat review) ──
    # Cacat 1: bab=[] -> exit 1 TETAPI berkas rusak tetap tertulis.
    # Cacat 2: romawi '1' -> generator menulis 'BAB 1', gerbang menolak
    # sesudahnya. Keduanya ditutup validasi awal + tulis-sementara.
    spec_asli = json.loads(CONTOH.read_text(encoding='utf-8'))

    def jalan(spec_mod, nama_keluar):
        sp = Path(td) / f'spec-{nama_keluar}.json'
        sp.write_text(json.dumps(spec_mod), encoding='utf-8')
        out = Path(td) / f'{nama_keluar}.docx'
        r = subprocess.run([sys.executable, str(GENERATOR), str(sp), str(out)],
                           capture_output=True, text=True)
        sisa_tmp = list(Path(td).glob('*.tmp.docx'))
        return r, out, sisa_tmp

    s_bab_kosong = json.loads(json.dumps(spec_asli))
    s_bab_kosong['bab'] = []
    r, out, sisa = jalan(s_bab_kosong, 'tanpa-bab')
    cek('bab kosong: generator menolak (exit != 0)', r.returncode != 0)
    cek('bab kosong: TIDAK ada berkas keluaran', not out.exists())
    cek('bab kosong: TIDAK ada berkas sementara tersisa', not sisa)

    s_romawi = json.loads(json.dumps(spec_asli))
    s_romawi['bab'][0]['romawi'] = '1'
    r, out, sisa = jalan(s_romawi, 'romawi-angka')
    cek("romawi '1': generator menolak SEBELUM menulis (exit != 0)",
        r.returncode != 0)
    cek("romawi '1': TIDAK ada berkas keluaran", not out.exists())

    # berkas baik yang sudah ada TIDAK tertimpa percobaan gagal
    out_baik = Path(td) / 'sudah-baik.docx'
    out_baik.write_bytes(b'ISI LAMA YANG BAIK')
    sp = Path(td) / 'spec-gagal.json'
    sp.write_text(json.dumps(s_bab_kosong), encoding='utf-8')
    r = subprocess.run([sys.executable, str(GENERATOR), str(sp), str(out_baik)],
                       capture_output=True, text=True)
    cek('percobaan gagal tidak menimpa berkas baik yang ada',
        r.returncode != 0 and out_baik.read_bytes() == b'ISI LAMA YANG BAIK')

md5_akhir = hashlib.md5(TEMPLATE.read_bytes()).hexdigest()
cek('MD5 template sesudah generate tetap', md5_akhir == MD5_WAJIB, md5_akhir)

print('\n' + '=' * 66)
print(f'RINGKAS UJI GENERATOR: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
