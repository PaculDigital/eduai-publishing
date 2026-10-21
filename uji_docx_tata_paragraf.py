"""UJI DOCX — paragraf & variasi benar-benar berubah di berkas nyata?

Membuat DOCX dari naskah contoh yang SENGAJA punya:
  · paragraf sangat panjang (14 kalimat)  → harus DIPECAH
  · paragraf berisi hal setara (4 kalimat pendek) → harus jadi DAFTAR
  · 6 paragraf naratif beruntun → variasi harus muncul

Lalu DIPERIKSA dari DOCX-nya (bukan dari kode): indentasi, spasi,
jumlah kalimat per paragraf, jumlah daftar, list asli Word (numPr).
"""
import json
import os
import sys

sys.path.insert(0, '/app')

os.environ.setdefault('EDUAI_DATA_DIR', '/tmp/uji_tataparagraf')
KELUAR = '/tmp/uji_tataparagraf'
os.makedirs(KELUAR, exist_ok=True)

import buku_umum_assembly as A          # noqa: E402

#  Ukuran huruf isi diambil DARI kode (SOT 2.2: inden = 1 em = ukuran huruf).
#  🚨 JANGAN tulis 11 di sini — FONT_SIZE = Pt(12), dan menulis angka
#  karangan membuat uji GAGAL PALSU (terukur 20 Okt 2026).
UKURAN_HURUF = A.FONT_SIZE.pt if hasattr(A.FONT_SIZE, 'pt') else 12.0

#  ── Siapkan naskah contoh yang SAKIT (kaku) ───────────────────────────
sakit = []
sakit.append('1.1 Pengamatan Cuaca')
sakit.append('Cuaca adalah keadaan udara pada suatu tempat dan waktu tertentu. '
             'Cuaca dapat berubah setiap saat tanpa bisa kita duga sebelumnya. '
             'Pagi hari mungkin terasa sejuk dan segar bagi tubuh kita. '
             'Siang hari panas matahari mulai terasa menyengat di kulit. '
             'Sore hari angin bertiup lebih kencang dari arah laut. '
             'Malam hari udara kembali dingin dan lembap sekali. '
             'Setiap perubahan cuaca dipengaruhi oleh banyak hal di alam. '
             'Panas matahari adalah sumber utama dari seluruh perubahan itu. '
             'Angin membawa uap air dari laut menuju daratan yang lebih tinggi. '
             'Uap air itu kemudian berkumpul dan berubah menjadi awan tebal. '
             'Awan yang semakin berat akhirnya menurunkan hujan ke permukaan. '
             'Hujan membasahi tanah dan mengisi kembali cadangan air di dalamnya. '
             'Air di tanah mengalir menuju sungai lalu kembali lagi ke laut. '
             'Demikian seterusnya sehingga air di bumi tidak pernah habis.')
sakit.append('Air memiliki banyak manfaat bagi tubuh kita. '
             'Air menjaga suhu tubuh tetap stabil sepanjang hari. '
             'Air membantu proses pencernaan makanan di dalam tubuh. '
             'Air melancarkan peredaran darah ke seluruh bagian tubuh.')
sakit.append('Pengamatan dilakukan dengan cermat oleh seluruh peserta yang hadir. '
             'Mereka mencatat setiap perubahan cuaca yang terjadi hari itu. '
             'Catatan kemudian dibandingkan dengan data pengamatan sebelumnya. '
             'Hasilnya menunjukkan pola yang cukup jelas dan berulang. '
             'Pola itu lalu dicatat dalam tabel pengamatan harian. '
             'Tabel tersebut menjadi bahan diskusi pada pertemuan berikutnya.')
for i in range(1, 4):
    sakit.append(f'Paragraf naratif nomor {i} berisi penjelasan tambahan yang '
                 f'cukup panjang untuk menguji apakah variasi bentuk benar-benar '
                 f'muncul di tengah teks. Isinya sengaja dibuat mengalir seperti '
                 f'tulisan biasa tanpa daftar agar mesin harus menyisipkan bentuk '
                 f'lain supaya tidak menjadi dinding teks yang melelahkan mata. '
                 f'Kalimat kelima menutup paragraf ini dengan kesimpulan singkat.')
naskah = '\n'.join(sakit)

#  ── Rakit DOCX lewat fungsi ASLI ──────────────────────────────────────
A.OUT_DIR = KELUAR
A.VISUAL_DIR = os.path.join(KELUAR, 'visual')
os.makedirs(A.VISUAL_DIR, exist_ok=True)

doc = A.Document()
bab_data = {'title': 'Mengenal Cuaca', 'subs': []}
A.add_bab(doc, 1, bab_data, naskah)
path = os.path.join(KELUAR, 'UJI_TATA_PARAGRAF.docx')
doc.save(path)

#  ── PERIKSA dari DOCX ────────────────────────────────────────────────
from docx import Document
from docx.shared import Pt
d = Document(path)

par = [p for p in d.paragraphs if p.text.strip()]
isi = [p for p in par if len(p.text.split()) > 12]   # paragraf isi (bukan judul)

def inden_pt(p):
    """Indentasi baris pertama dalam pt (EMU / 12700).

    🚨 JEBAKAN TERUKUR (20 Okt 2026, 3× salah): nilai yang dibaca balik
    dari DOCX bisa berupa objek `Twips`, `Length`, atau int EMU — dan
    `.pt` pada `Twips` mengembalikan **number_format Twips**, bukan pt
    (terukur: 1935480000 → dilaporkan 152400.0). SATU-SATUNYA cara aman:
    konversi dari int EMU. 1 pt = 12700 EMU.
    """
    fi = p.paragraph_format.first_line_indent
    if fi is None:
        return 0.0
    try:
        return round(int(fi) / 12700.0, 2)
    except (TypeError, ValueError):
        return 0.0

def spasi_pt(p):
    pf = p.paragraph_format
    return (round(pf.space_before.pt, 1) if pf.space_before else 0.0,
            round(pf.space_after.pt, 1) if pf.space_after else 0.0)

berinden = [p for p in isi if abs(inden_pt(p) - UKURAN_HURUF) < 0.6]
tanpa_inden = [p for p in isi if inden_pt(p) == 0.0]
kalimat = lambda t: len([k for k in t.replace('!', '.').replace('?', '.').split('.') if k.strip()])

daftar_bullet = [p for p in par if p.style.name == 'List Bullet']
daftar_nomor = [p for p in par if p.style.name == 'List Number']

hasil = {
    'total_paragraf_isi': len(isi),
    'berinden_11pt': len(berinden),
    'tanpa_inden': len(tanpa_inden),
    'paragraf_terpanjang_kalimat': max((kalimat(p.text) for p in isi), default=0),
    'lebih_7_kalimat': sum(1 for p in isi if kalimat(p.text) > 7),
    'daftar_bullet': len(daftar_bullet),
    'daftar_nomor': len(daftar_nomor),
    'spasi_antar_paragraf': sorted({spasi_pt(p) for p in isi}),
    'berkas': path,
}
print(json.dumps(hasil, indent=1, ensure_ascii=False))

#  ── putusan ──────────────────────────────────────────────────────────
salah = []
if hasil['lebih_7_kalimat'] > 0:
    salah.append(f"masih ada {hasil['lebih_7_kalimat']} paragraf >7 kalimat")
if hasil['berinden_11pt'] < 2:
        salah.append(f"hanya {hasil['berinden_11pt']} paragraf berinden {UKURAN_HURUF}pt")
if hasil['spasi_antar_paragraf'] != [(0.0, 0.0)]:
    salah.append(f"spasi bukan 0: {hasil['spasi_antar_paragraf']}")
if len(tanpa_inden) < 1:
    salah.append('tidak ada paragraf pertama-setelah-judul yang rata kiri')
if hasil['daftar_bullet'] + hasil['daftar_nomor'] < 3:
    salah.append(f"daftar cuma {hasil['daftar_bullet'] + hasil['daftar_nomor']} butir")

print(json.dumps({'salah': salah}, ensure_ascii=False))
sys.exit(0 if not salah else 1)
