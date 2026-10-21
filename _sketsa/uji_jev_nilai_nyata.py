"""UJI NYATA: panggil JEJAK SUNGGUHAN (jev-1.13) untuk menilai balasan ngawur.

Kasus diambil dari KEJADIAN NYATA 05Okt26 (uji E1 gerbang):
  komentar: "Perbaiki tata bahasa dan ejaan paragraf"
  paragraf : 336 karakter
  balasan  : 6.094 karakter  → rasio 18×

Yang mau dibuktikan: jev MENILAI dengan benar (bukan sekadar menjawab).
"""
import json
import sys

sys.path.insert(0, '/app')
from app import satpam  # noqa: E402

# ── Kasus A: balasan NGAWUR (nyata dari kejadian) ────────────────────────
paragraf_a = (
    'Pendidikan memiliki peran yang sangat penting dalam membentuk karakter '
    'generasi muda. Proses pendidikan tidak hanya terjadi di dalam kelas, '
    'tetapi juga di lingkungan keluarga dan masyarakat. Oleh karena itu, '
    'diperlukan kerja sama yang baik antara semua pihak.'
)
ganti_ngawur = (
    'BAB I PENDAHULUAN\n\n'
    'Pendidikan merupakan fondasi utama dalam pembangunan sumber daya manusia '
    'yang berkualitas. Menurut Undang-Undang Nomor 20 Tahun 2003 tentang Sistem '
    'Pendidikan Nasional, pendidikan adalah usaha sadar dan terencana untuk '
    'mewujudkan suasana belajar dan proses pembelajaran agar peserta didik '
    'secara aktif mengembangkan potensi dirinya.\n\n'
    'Dalam konteks globalisasi yang semakin kompetitif, kualitas pendidikan '
    'menjadi faktor penentu daya saing suatu bangsa. Berbagai penelitian '
    'menunjukkan bahwa investasi di bidang pendidikan memiliki korelasi positif '
    'terhadap pertumbuhan ekonomi suatu negara.\n\n'
    'BAB II TINJAUAN PUSTAKA\n\n'
    'Teori konstruktivisme yang dikemukakan oleh Jean Piaget dan Lev Vygotsky '
    'menyatakan bahwa pengetahuan dibangun oleh individu melalui interaksi '
    'dengan lingkungannya. Vygotsky menekankan pentingnya zona perkembangan '
    'proksimal dalam proses pembelajaran.\n\n'
    'Selanjutnya, teori behaviorisme dari B.F. Skinner menjelaskan bahwa '
    'pembelajaran merupakan perubahan perilaku yang dapat diamati dan diukur '
    'secara objektif melalui stimulus dan respons yang diberikan secara repetitif.'
)

# ── Kasus B: balasan SAH (memang diminta "perdalam") ─────────────────────
paragraf_b = paragraf_a
ganti_sah = (
    'Pendidikan memiliki peran yang sangat penting dalam membentuk karakter '
    'generasi muda, terutama pada jenjang pendidikan dasar yang menjadi fondasi '
    'awal pembentukan nilai dan sikap. Proses pendidikan tidak hanya terjadi di '
    'dalam kelas, tetapi juga di lingkungan keluarga dan masyarakat, sehingga '
    'menciptakan ekosistem pembelajaran yang saling melengkapi. Berbagai kajian '
    'menunjukkan bahwa keterlibatan tiga lingkungan pendidikan tersebut secara '
    'bersama-sama berkontribusi terhadap perkembangan kognitif dan afektif anak. '
    'Oleh karena itu, diperlukan kerja sama yang baik antara semua pihak, termasuk '
    'sekolah, keluarga, dan komunitas, agar tujuan pendidikan dapat tercapai '
    'secara optimal dan berkelanjutan.'
)

print('═' * 100)
print('  UJI JEJAK SUNGGUHAN — jev-1.13 menilai dua balasan nyata')
print('═' * 100)

for nama, ganti, tugas, harapan in [
    ('A. balasan NGAWUR (BAB I & II baru, 18× paragraf)', ganti_ngawur,
     'Perbaiki tata bahasa dan ejaan paragraf', 'tolak'),
    ('B. balasan SAH (perdalam 1 paragraf, 4× paragraf)', ganti_sah,
     'Perdalam paragraf ini dengan penjelasan lebih rinci', 'lolos'),
]:
    rasio = round(len(ganti) / max(1, len(paragraf_a)), 2)
    batas = int(len(paragraf_a) * 3.0)
    print(f'── {nama}')
    print(f'   tugas    : {tugas}')
    print(f'   rasio    : {rasio}× (batas wajar: {batas} kar)')
    h = satpam.nilai_balasan(paragraf_a, paragraf_a, ganti, tugas, rasio, batas)
    cocok = '✅' if h.get('keputusan') == harapan else '❌'
    print(f'   {cocok} keputusan jev: {h.get("keputusan")} '
          f'(harus: {harapan}) · keyakinan {h.get("confidence")}')
    print(f'      alasan : {h.get("alasan")}')
    print()

print('CATATAN: keputusan ini HANYA berlaku untuk kasus rasio > batas wajar.')
print('         Balasan yang wajar (≤3×) tidak pernah sampai ke jev — pagar')
print('         aritmatika yang memutuskan (murah, tidak bisa mati).')
