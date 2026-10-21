"""MESIN KONVERSI — naskah akademik → artikel jurnal (07 Okt 2026).

═══════════════════════════════════════════════════════════════════════════
KENAPA MODUL INI ADA
Naskah skripsi/tesis/disertasi (BAB I–V, 60–150 halaman) harus jadi ARTIKEL
JURNAL (IMRAD, 5.000–7.000 kata) siap kirim ke editor. Ini RESTRUKTURISASI
STRUKTUR — bukan penilaian mutu, bukan penulisan baru.

ATURAN INDUK (SOT_KONVERSI_JURNAL.md):
  · NOL MESIN BARU — memakai ulang, bukan membangun:
      - kuota.potong_konversi / selesaikan_konversi / kembalikan_konversi
      - satpam.periksa()  → Jev sebagai MATA (peta bab), bukan hakim
      - state.petakan()   → peta bab GRATIS kalau section_state kosong
      - ai._brief_dan_peta() → brief + peta dari DB
      - dokumen_baru / folder → penyimpanan hasil
      - jenis.evaluasi()  → deteksi jenis dokumen
  · SATU modul, TIGA jalur (kuantitatif · kualitatif · review) — BUKAN 3 modul
  · Jev = MATA bukan HAKIM: ia MEMETAKAN bab lalu MELAPOR; USER yang memutuskan

URUTAN PAGAR (WAJIB — putusan Bos 07 Okt, SOT §N):
  ① cek template & makro (tolak .dotm/.docm/.doc + vbaProject.bin)
  ② cek nama + email ADA di naskah (kalau tidak → MESIN BERHENTI)
  ③ cek kelengkapan bagian (SEBELUM konversi — beri tahu, tidak memblokir)
  ④ konversi (POTONG KUOTA di sini)
  ⑤ periksa hasil (2 lapis: mesin gratis + Jev 11 elemen)
═══════════════════════════════════════════════════════════════════════════
"""
from __future__ import annotations

import json
import logging
import re
import time
import zipfile
from pathlib import Path

from . import satpam

log = logging.getLogger('eduai.konversi')

#  Batas naskah yang dikirim ke AI untuk konversi. Lebih besar dari batas
#  bimbingan (asisten.NASKAH_MAKS = 40.000) karena konversi WAJIB melihat
#  seluruh naskah sekaligus — artikel adalah SATU kesatuan, bukan per-bab.
#  Dinaikkan dari 40k → 100k (07 Okt) sejalan R4 di SOT: naskah 118 hlm
#  (±200k kar) tetap harus masuk; `potong_cerdas` memecah jadi bagian bila lewat.
NASKAH_MAKS_KONVERSI = 100_000

#  ── Batas & berkas ────────────────────────────────────────────────────────
PROMPTS_DIR = Path(__file__).resolve().parent.parent / 'prompts'
PROMPT_ARTIKEL = PROMPTS_DIR / 'artikel_jurnal.txt'

#  Ekstensi yang DILARANG (mengandung makro / bisa menjalankan script).
EKSTENSI_BAHAYA = {'.dotm', '.docm', '.dot', '.doc'}
EKSTENSI_SAH = {'.docx'}
#  Isi di dalam .docx/.dotm yang menandakan makro tersembunyi.
ISI_BAHAYA = {'word/vbaproject.bin', 'word/vbaData.xml'}

#  JENIS naskah (3 jalur fitur ini) — beda dari jenis.py (6 jenis dokumen).
JENIS_KUANTITATIF = 'kuantitatif'
JENIS_KUALITATIF = 'kualitatif'
JENIS_REVIEW = 'review'
SEMUA_JENIS = (JENIS_KUANTITATIF, JENIS_KUALITATIF, JENIS_REVIEW)

#  ── TOKEN ─────────────────────────────────────────────────────────────────
#  Putusan Bos 07 Okt (SOT §N no.9): 1× REVISI jurnal = 2 TOKEN.
#  Dihitung PER REVISI — bukan sekali untuk semua. Contoh Bos: revisi Abstrak
#  + revisi Novelty = 2× revisi = 4 token.
#  ⚠️ Konversi pertama TIDAK pakai token — ia pakai AddOn/jatah KONVERSI
#  (kuota.potong_konversi). Token hanya untuk REVISI sesudahnya.
TOKEN_PER_REVISI = 2

#  Bagian artikel yang BOLEH direvisi satu-satu (masing-masing = 2 token).
BAGIAN_REVISI = (
    ('judul', 'Judul'),
    ('abstrak_id', 'Abstrak (Indonesia)'),
    ('abstract_en', 'Abstract (English)'),
    ('pendahuluan', 'Pendahuluan'),
    ('metode', 'Metode'),
    ('hasil_pembahasan', 'Hasil dan Pembahasan'),
    ('kesimpulan', 'Kesimpulan'),
    ('daftar_pustaka', 'Daftar Pustaka'),
)
#  Elemen mutu (11) juga boleh direvisi satu-satu — kuncinya sama dengan
#  ELEMEN_11 di bawah, ditambah awalan 'elemen:' supaya tidak bentrok.
ELEMEN_REVISI = (
    ('hook', 'Hook (pembuka)'),
    ('state_of_art', 'State of Art'),
    ('gap', 'Gap (celah penelitian)'),
    ('novelty', 'Novelty (kebaruan)'),
    ('findings', 'Findings (temuan)'),
    ('critical_analysis', 'Critical Analysis'),
    ('diskusi_komparatif', 'Diskusi Komparatif'),
    ('kaitan_teori', 'Kaitan Teori'),
    ('limitasi', 'Limitasi'),
    ('rekomendasi', 'Rekomendasi Riset Lanjut'),
    ('implikasi', 'Implikasi Teoretis + Praktis'),
)

# ══════════════════════════════════════════════════════════════════════════
# HARGA MENAMBAH ELEMEN MUTU — BERTINGKAT (putusan Bos 15 Okt 2026)
# ══════════════════════════════════════════════════════════════════════════
#  Bos: "harga bisa saya variasi tidak seragam 2 token, karena beban kerja
#  ai juga lebih banyak" ⇒ 3 tingkat:
#     BERAT   = 5 token — AI harus baca banyak bahan + membandingkan
#     SEDANG  = 3 token — AI harus menyimpulkan dari seluruh naskah
#     STANDAR = 2 token — AI menyusun ringkas dari bahan yang sudah ada
#
#  ⚠️ HARGA INI HANYA UNTUK **ELEMEN MUTU** (yang ditambahkan ke naskah).
#     BAGIAN ARTIKEL (abstrak, pendahuluan, metode, …) tetap TOKEN_PER_REVISI.
#     Dasar: putusan Bos 15 Okt — pembicaraan harga = "tambah mutu".
TOKEN_ELEMEN = {
    #  BERAT — butuh bahan luas + pembanding penelitian lain
    'state_of_art': 5,
    'diskusi_komparatif': 5,
    #  SEDANG — butuh menyimpulkan dari naskah
    'gap': 3,
    'novelty': 3,
    'critical_analysis': 3,
    'kaitan_teori': 3,
    'findings': 3,
    #  STANDAR — menyusun ringkas dari bahan yang ada
    'hook': 2,
    'limitasi': 2,
    'rekomendasi': 2,
    'implikasi': 2,
}


def token_elemen(kunci: str) -> int:
    """Harga menambah SATU elemen mutu (token). Jatuh aman ke TOKEN_PER_REVISI."""
    return int(TOKEN_ELEMEN.get(str(kunci or ''), TOKEN_PER_REVISI))


def tingkat_elemen(kunci: str) -> str:
    """Tingkat beban sebuah elemen: 'berat' | 'sedang' | 'standar'."""
    t = token_elemen(kunci)
    if t >= 5:
        return 'berat'
    if t >= 3:
        return 'sedang'
    return 'standar'


LABEL_JENIS = {
    JENIS_KUANTITATIF: 'Kuantitatif',
    JENIS_KUALITATIF: 'Kualitatif',
    JENIS_REVIEW: 'Literatur Review',
}

#  Bagian artikel yang WAJIB ada (dipakai Langkah ③ cek kelengkapan).
BAGIAN_WAJIB = ('pendahuluan', 'metode', 'hasil_pembahasan', 'kesimpulan')

#  11 elemen mutu — SUMBER: jurnalkit/jemt_prompt.md:50-63 (dibaca, bukan karangan).
ELEMEN_11 = (
    ('hook',              'Hook',                   'Pendahuluan ¶1'),
    ('state_of_art',      'State of Art',           'Pendahuluan ¶2–3'),
    ('gap',               'Gap',                    'Pendahuluan ¶4'),
    ('novelty',           'Novelty',                'Pendahuluan ¶5'),
    ('findings',          'Findings',               'Hasil & Pembahasan'),
    ('critical_analysis', 'Critical Analysis',      'Hasil & Pembahasan'),
    ('diskusi_komparatif', 'Diskusi Komparatif',    'Hasil & Pembahasan'),
    ('kaitan_teori',      'Kaitan Teori',           'Hasil & Pembahasan'),
    ('limitasi',          'Limitasi',               'Kesimpulan ¶1'),
    ('rekomendasi',       'Rekomendasi Riset Lanjut', 'Kesimpulan ¶2'),
    ('implikasi',         'Implikasi Teoretis + Praktis', 'Kesimpulan ¶3'),
)


# ══════════════════════════════════════════════════════════════════════════
# PAGAR ① — TEMPLATE & MAKRO
# ══════════════════════════════════════════════════════════════════════════
def periksa_berkas_aman(nama: str, jalur: Path) -> tuple[bool, str]:
    """Periksa berkas .docx: BUKAN makro, BUKAN script berbahaya.

    Mengembalikan (aman: bool, pesan: str).
    Pesan sengaja jelas & menuduh barangnya, bukan usernya:
      "berkas ini bukan template yang sah / mengandung makro, silakan upload
       ulang berkas .docx biasa".

    KENAPA pakai zipfile: `.docx` itu ZIP. Kalau di dalamnya ada
    `word/vbaProject.bin` (atau vbaData.xml), itu MAKRO tersembunyi —
    walau namanya berakhiran .docx. Cek ISI, bukan cuma nama (pelajaran
    sama dengan "grep berkas, bukan percaya judul").
    """
    ekst = Path(nama or '').suffix.lower()
    if ekst in EKSTENSI_BAHAYA:
        return False, (f'Berkas berakhiran "{ekst}" — format ini bisa memuat '
                       'makro/script. Silakan upload ulang sebagai .docx biasa '
                       '(bukan .doc/.dotm/.docm).')
    if ekst not in EKSTENSI_SAH:
        return False, (f'Berkas "{ekst or "(tanpa akhiran)"}" bukan format yang '
                       'didukung. Yang sah hanya .docx.')

    if not jalur or not Path(jalur).is_file():
        return False, 'Berkas tidak ditemukan di server.'

    try:
        with zipfile.ZipFile(jalur) as z:
            isi = {n.lower() for n in z.namelist()}
    except zipfile.BadZipFile:
        return False, ('Berkas ini bukan .docx yang sah (rusak atau bukan '
                       'berkas Word). Silakan upload ulang.')
    except Exception as e:                                   # noqa: BLE001
        return False, f'Berkas tidak bisa dibaca: {e}'

    kena = isi & ISI_BAHAYA
    if kena:
        return False, ('Berkas ini MENGANDUNG MAKRO (script). Demi keamanan, '
                       'berkas ber-makro tidak diproses. Silakan upload versi '
                       '.docx yang bersih.')
    if 'word/document.xml' not in isi:
        return False, ('Isi berkas ini BUKAN dokumen Word (.docx). Pastikan '
                       'yang diupload benar-benar naskah/template Word.')
    return True, ''


# ══════════════════════════════════════════════════════════════════════════
# PAGAR ② — NAMA + EMAIL (putusan Bos: MESIN TIDAK JALAN kalau tidak ada)
# ══════════════════════════════════════════════════════════════════════════
_POLA_EMAIL = re.compile(r'[\w.+-]+@[\w-]+\.[\w.-]+')
#  Label yang biasa dipakai sebelum nama penulis di naskah Indonesia.
#  ⚠️ JEBAKAN 07Okt26: `\s` di DALAM char-class memakan BARIS BARU → regex
#  melebar ke baris berikutnya & gagal ("Nama: Budi Santoso" tak terbaca).
#  Solusi: pakai `[ \t]` (spasi/tab saja) di dalam kelas, jangan `\s`.
#  ⚠️ JEBAKAN 07Okt26 #2 (naskah NYATA Asih): regex lama cari `[A-Z][a-z]+`
#  → GAGAL karena skripsi Indonesia menulis nama HURUF KAPITAL SEMUA
#  ("OLEH : \n ASIH SUSANTI PUTRI"). Kini menerima dua bentuk:
#    · Huruf Kapital Awal ("Budi Santoso")  ·  KAPITAL SEMUA ("ASIH SUSANTI PUTRI")
_LABEL_NAMA = re.compile(
    r'(?:^|\n)[ \t]*(?:nama|oleh|penulis|disusun[ \t]+oleh|ditulis[ \t]+oleh)'
    r'[ \t]*[:\-]?[ \t]*\n?[ \t]*'
    r'([A-Z][A-Za-z\'., \t-]{2,80}?)(?=\n|NIM|NIP|$|  {2,})',
    re.MULTILINE | re.IGNORECASE)
#  Nama KAPITAL SEMUA (baris sendiri, 2–6 kata) — bentuk paling umum skripsi.
_POLA_NAMA_KAPITAL = re.compile(
    r'(?:^|\n)[ \t]*([A-Z][A-Z\'.,-]*(?:[ \t]+[A-Z][A-Z\'.,-]*){1,5})[ \t]*(?=\n)',
    re.MULTILINE)


def cari_identitas(naskah: str) -> dict:
    """Cari nama penulis + email DARI NASKAH.

    WAJIB — putusan Bos 07 Okt (SOT §N no.5): "diambil dari naskah nama dan
    email jika tidak ada user lengkapi dahulu. Mesin tidak akan jalan."

    Strategi (urut kepercayaan):
      1. EMAIL  → regex (paling andal, bentuknya pasti)
      2. NAMA   → cari setelah label (Nama/Oleh/Penulis/Disusun oleh)
      3. NAMA   → kalau tak ada label, coba baris setelah judul (baris pendek
                  berisi 2–5 kata, huruf besar di awal tiap kata)

    ⚠️ DILARANG mengarang: kalau tidak ketemu → kembalikan kosong & biarkan
    pemanggil MEMBLOKIR. Ini pagar bisnis — konversi tanpa nama = artikel cacat.
    """
    hasil = {'nama': '', 'email': ''}
    teks = naskah or ''

    #  EMAIL: ambil yang PERTAMA SAH — jangan berhenti di tangkapan pertama,
    #  karena tangkapan pertama bisa metrik penelitian (mis. "mAP@0.5").
    for m in _POLA_EMAIL.finditer(teks):
        kandidat = m.group(0).strip().rstrip('.,;')
        if _email_sah(kandidat):
            hasil['email'] = kandidat
            break

    #  ── NAMA, 3 percobaan berurutan (dari paling pasti) ──────────────
    #  ① setelah label (Nama/Oleh/Penulis) — bentuk "Nama: Budi Santoso"
    #     maupun "OLEH : \n ASIH SUSANTI PUTRI" (baris baru setelah label)
    for m2 in _LABEL_NAMA.finditer(teks):
        nama = _rapikan_nama(m2.group(1))
        if nama:
            hasil['nama'] = nama
            break

    #  ② nama KAPITAL SEMUA di barisnya sendiri (paling umum di skripsi).
    #     ⚠️ Dijalankan HANYA kalau ① gagal — jangan menebak dari baris acak
    #     kalau sudah ada bukti label (hindari salah ambil judul BAB).
    if not hasil['nama']:
        for m3 in _POLA_NAMA_KAPITAL.finditer(teks[:4000]):
            nama = _rapikan_nama(m3.group(1))
            if nama:
                hasil['nama'] = nama
                break
    return hasil


def _rapikan_nama(kotor: str) -> str:
    """Bersihkan calon nama + TOLAK kalau jelas bukan nama (judul/bab).

    Aturan tolak (terukur dari naskah nyata):
      · memuat kata struktur: SKRIPSI/TESIS/BAB/OLEH/NIM/JUDUL/PROPOSAL
      · terlalu panjang (>6 kata) atau terlalu pendek (<2 kata)
      · memuat angka (nama orang umumnya tidak)
    """
    if not kotor:
        return ''
    nama = re.sub(r'[ \t]{2,}', ' ', str(kotor).strip())
    nama = nama.strip(' :-,.;')
    if not nama:
        return ''
    kata = nama.split()
    if not (2 <= len(kata) <= 6):
        return ''
    if any(c.isdigit() for c in nama):
        return ''
    _tolak = {'SKRIPSI', 'TESIS', 'DISERTASI', 'PROPOSAL', 'BAB', 'OLEH', 'NIM',
              'NIP', 'JUDUL', 'PROGRAM', 'STUDI', 'FAKULTAS', 'UNIVERSITAS',
              'PENGARUH', 'ANALISIS', 'STUDI', 'DAN', 'PADA', 'UNTUK',
              #  ⚠️ 07Okt26 (naskah nyata UNMUL): pola kapital pernah menangkap
              #  "DAFTAR ISI" sebagai nama. Tambah kata struktur dokumen.
              'DAFTAR', 'ISI', 'TABEL', 'GAMBAR', 'LAMPIRAN', 'ABSTRAK',
              'ABSTRACT', 'KATA', 'PENGANTAR', 'HALAMAN', 'UCAPAN', 'TERIMA',
              'KASIH', 'MOTTO', 'PERSEMBAHAN', 'RIWAYAT', 'HIDUP', 'LEMBAR',
              'PENGESAHAN', 'PERSETUJUAN', 'ORISINALITAS', 'PERNYATAAN',
              'PEDOMAN', 'TRANSLITERASI', 'SINGKATAN', 'GLOSARIUM'}
    if any(k.upper().strip('.,:-') in _tolak for k in kata):
        return ''
    return nama


#  Email yang JELAS BUKAN email penulis (metrik/rumus/placeholder).
_EMAIL_PALSU = re.compile(
    r'^(?:map|ap|iou|precision|recall|f1|@|n|r)[\d.]*@|@[\d.]+$|@(?:x|y|z|\d)\.',
    re.IGNORECASE)


def _email_sah(email: str) -> bool:
    """Tolak email palsu hasil tangkapan metrik penelitian.

    ⚠️ 07Okt26 (naskah nyata UNMUL): regex email menangkap "mAP@0.5" —
    itu metrik Mean Average Precision, BUKAN email. Kalau lolos, pagar②
    mengira identitas lengkap → konversi jalan tanpa email penulis.
    """
    e = (email or '').strip().lower()
    if not e or '@' not in e:
        return False
    lokal, _, domain = e.partition('@')
    if '.' not in domain:              # domain harus punya titik (bukan "0.5")
        return False
    if not lokal:                      # lokal boleh 1 huruf (mis. a@b.co.id)
        return False
    if _EMAIL_PALSU.search(e):
        return False
    #  domain TLD wajib alfabet (menolak "mAP@0.5" → domain "0.5")
    tld = domain.rsplit('.', 1)[-1]
    if not tld.isalpha() or len(tld) < 2:
        return False
    return True


def lengkapi_identitas(hasil: dict) -> list[str]:
    """Daftar HAL YANG KURANG — dipakai memblokir konversi + pesan ke user."""
    kurang = []
    if not (hasil or {}).get('nama'):
        kurang.append('nama penulis')
    if not (hasil or {}).get('email'):
        kurang.append('email penulis')
    return kurang


# ══════════════════════════════════════════════════════════════════════════
# PAGAR ③ — CEK KELENGKAPAN BAGIAN (SEBELUM konversi, hanya memberi tahu)
# ══════════════════════════════════════════════════════════════════════════
#  🏷️ LABEL MANUSIA untuk kunci `bahan` di cek_kelengkapan() — dilihat USER.
#  Tanpa ini, layar menampilkan kata mesin ("hasil", "pustaka") yang jelek.
#  Gaya = daftar isi skripsi (putusan Bos 15 Okt 2026).
LABEL_KELENGKAPAN = {
    'latar_belakang':  'BAB I Pendahuluan',
    'tinjauan_pustaka': 'BAB II Tinjauan Pustaka',
    'metode':          'BAB III Metode Penelitian',
    'hasil':           'BAB IV Hasil',
    'pembahasan':      'BAB IV Pembahasan',
    'kesimpulan':      'BAB V Kesimpulan',
    'pustaka':         'Daftar Pustaka',
}


def label_kelengkapan(kunci: str) -> str:
    """Nama manusia sebuah kunci kelengkapan (jatuh aman ke kunci itu sendiri)."""
    return LABEL_KELENGKAPAN.get(str(kunci or ''), str(kunci or ''))


def bagian_kurang(kelengkapan: dict) -> list:
    """Daftar KURANG dalam bahasa manusia — siap ditampilkan ke layar.

    Dipakai layar konversi (jembatan bab kurang); tidak mengubah logika apa pun.
    """
    return [label_kelengkapan(k) for k in ((kelengkapan or {}).get('kurang') or [])]


def cek_kelengkapan(brief: dict, peta: list) -> dict:
    """Cek bahan konversi ADA TIDAK — GRATIS (aturan mesin, tanpa AI).

    Beda dengan PAGAR ②: yang ini TIDAK memblokir, hanya MEMBERI TAHU
    (putusan Bos no.7: cek bagian = A sebelum konversi, gratis).

    ⚠️ JEBAKAN 07Okt26 (terukur atas skripsi ASLI): `state.petakan()` mengembalikan
    daftar SUB-BAB (mis. 2.1, 2.2 …), dan untuk naskah nyata ia hanya memuat
    sebagian BAB (skripsi UNHAS: hanya sub-bab BAB II). Kalau kita menilai
    kelengkapan HANYA dari daftar itu → "metode/hasil/kesimpulan KURANG"
    padahal ADA di naskah. SALAH MENUDUH = user diarahkan keliru.
    ⇒ Bahan dinilai dari DUA sumber: (a) `kategori` di peta (bab1..bab5), DAN
    (b) TEKS NASKAH itu sendiri (`teks`). Yang menentukan = TEKS, karena
    daftar peta bisa tidak lengkap.
    """
    #  (a) dari peta: kumpulkan kategori + judul
    kategori = set()
    judul_bab = []
    for p in (peta or []):
        if not isinstance(p, dict):
            continue
        k = str(p.get('kategori') or '').strip().lower()
        if k:
            kategori.add(k)
        t = str(p.get('section_title') or p.get('section_id') or '')
        if t:
            judul_bab.append(t.upper())
    gabung = ' | '.join(judul_bab)

    #  (b) dari TEKS naskah (kalau ada) — inilah bukti terkuat
    teks = str((brief or {}).get('teks') or (brief or {}).get('naskah') or '')
    teks_besar = teks.upper()

    def ada(*kata):
        return any(k in gabung for k in kata)

    def ada_teks(*pola):
        return any(re.search(p, teks_besar) for p in pola)

    #  kategori bab1..bab5 = bukti langsung dari mesin peta
    bahan = {
        'latar_belakang': 'bab1' in kategori or ada('PENDAHULUAN', 'LATAR BELAKANG')
                          or ada_teks(r'BAB\s*I\b(?!\s*[IV])', r'PENDAHULUAN'),
        'tinjauan_pustaka': 'bab2' in kategori or ada('TINJAUAN', 'PUSTAKA', 'KAJIAN')
                            or ada_teks(r'BAB\s*II\b', r'TINJAUAN\s+PUSTAKA'),
        'metode': 'bab3' in kategori or ada('METODE', 'METODOLOGI')
                  or ada_teks(r'BAB\s*III\b', r'METODE\s+PENELITIAN'),
        'hasil': 'bab4' in kategori or ada('HASIL', 'TEMUAN')
                 or ada_teks(r'BAB\s*IV\b', r'HASIL\s+DAN\s+PEMBAHASAN'),
        'pembahasan': 'bab4' in kategori or ada('PEMBAHASAN', 'DISKUSI')
                      or ada_teks(r'PEMBAHASAN'),
        'kesimpulan': 'bab5' in kategori or ada('KESIMPULAN', 'SIMPULAN', 'PENUTUP')
                      or ada_teks(r'BAB\s*V\b', r'KESIMPULAN', r'SIMPULAN'),
        'pustaka': ada('DAFTAR PUSTAKA', 'REFERENSI')
                   or ada_teks(r'DAFTAR\s+PUSTAKA', r'DAFTAR\s+REFERENSI'),
    }
    kurang = [k for k, v in bahan.items() if not v]
    return {'bahan': bahan, 'kurang': kurang, 'ada_peta': bool(peta),
            'kategori': sorted(kategori)}


# ══════════════════════════════════════════════════════════════════════════
# DETEKSI JENIS — 3 jalur (kuantitatif · kualitatif · review)
# ══════════════════════════════════════════════════════════════════════════
_POLA_KUANT = re.compile(
    r'\b(?:koefisien|regresi|kuesioner|likert|spss|smartpls|sem|pls|uji\s+t|'
    r'uji\s+f|hipotesis|signifikan|signifikansi|p[\s-]*value|variabel\s+bebas|'
    r'variabel\s+terikat|populasi|sampel\s+acak|random\s+sampling|'
    r'validitas|reliabilitas|cronbach|r\s*square|r²|beta|β)\b',
    re.IGNORECASE)
_POLA_KUAL = re.compile(
    r'\b(?:wawancara|informan|narasumber|partisipan|fenomenologi|etnografi|'
    r'studi\s+kasus|grounded|purposive|triangulasi|koding|tema\s+analisis|'
    r'analisis\s+tematik|observasi\s+partisipatif|catatan\s+lapangan|'
    r'reduksi\s+data|member\s+check)\b', re.IGNORECASE)
_POLA_REVIEW = re.compile(
    r'\b(?:systematic\s+review|literature\s+review|tinjauan\s+sistematis|'
    r'tinjauan\s+literatur|prisma|meta[\s-]*analisis|state\s+of\s+the\s+art|'
    r'seleksi\s+artikel|kriteria\s+inklusi|kriteria\s+eksklusi)\b',
    re.IGNORECASE)


def deteksi_jenis(naskah: str, brief: dict | None = None) -> dict:
    """Deteksi JENIS penelitian dari ISI naskah — mesin, GRATIS, tanpa AI.

    Pola sama dengan deteksi jenis dokumen (jenis.py) dan Jev: MESIN mengusul,
    USER boleh menimpa (putusan Bos, SOT §C.1 no.2).

    Mengembalikan {'jenis': ..., 'yakin': 0..1, 'alasan': [...], 'skor': {...}}
    """
    t = (naskah or '')[:120000]
    n_kuant = len(_POLA_KUANT.findall(t))
    n_kual = len(_POLA_KUAL.findall(t))
    n_review = len(_POLA_REVIEW.findall(t))

    skor = {JENIS_KUANTITATIF: n_kuant,
            JENIS_KUALITATIF: n_kual,
            JENIS_REVIEW: n_review}
    total = n_kuant + n_kual + n_review

    if total == 0:
        #  tak ada bukti → default AMAN + keyakinan rendah → user ditanya
        return {'jenis': JENIS_KUANTITATIF, 'yakin': 0.30,
                'alasan': ['Tidak ada penanda metode yang jelas — dianggap '
                           'kuantitatif sampai kamu ubah.'],
                'skor': skor}

    jenis = max(skor, key=lambda k: skor[k])
    yakin = round(skor[jenis] / total, 2)
    #  rapikan keyakinan: kalau unggul mutlak, naikkan; kalau nyaris seri, turunkan
    urut = sorted(skor.values(), reverse=True)
    if len(urut) > 1 and urut[1] == 0:
        yakin = min(0.95, yakin + 0.25)
    elif len(urut) > 1 and (urut[0] - urut[1]) <= 1:
        yakin = min(yakin, 0.55)
    yakin = max(0.30, min(0.95, yakin))

    alasan = [f'{LABEL_JENIS[jenis]} — ditemukan {skor[jenis]} penanda metode '
              f'(kuantitatif {n_kuant} · kualitatif {n_kual} · review {n_review}).']
    return {'jenis': jenis, 'yakin': round(yakin, 2), 'alasan': alasan, 'skor': skor}


# ══════════════════════════════════════════════════════════════════════════
# PETA BAB — pakai Jev / state (MATA), bukan hakim
# ══════════════════════════════════════════════════════════════════════════
def peta_bab(db, file_id: int, naskah: str) -> dict:
    """Ambil peta bab+sub-bab sebagai BAHAN konversi.

    Memakai ULANG mesin yang ada (`ai._brief_dan_peta`), lalu dirapikan jadi
    kerangka ringkas untuk prompt: [{bab, judul, ringkas}].

    Jev di sini = MATA (memetakan), BUKAN HAKIM (menilai mutu). Larangan lama
    "Jev dilarang" hanya untuk 8 modul PENILAI MUTU — lihat SOT §C.
    """
    brief, peta = {}, []
    try:
        from .ai import _brief_dan_peta
        brief, peta = _brief_dan_peta(db, int(file_id), naskah)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konversi] peta bab gagal (file=%s): %s', file_id, e)

    kerangka = []
    for i, p in enumerate(peta or [], 1):
        isi = str(p.get('isi_teks') or '')
        kerangka.append({
            'no': i,
            'judul': str(p.get('section_title') or p.get('section_id') or f'Bagian {i}'),
            'panjang': len(isi),
            'ringkas': isi[:300],
        })
    return {'brief': brief or {}, 'peta': peta or [], 'kerangka': kerangka}


# ══════════════════════════════════════════════════════════════════════════
# JEV — MATA (bukan hakim) untuk KONVERSI (putusan Bos 07 Okt 2026)
# ══════════════════════════════════════════════════════════════════════════
#  Bos: "Perlu jev untuk mata". Jev DILIBATKAN, tapi perannya tetap SATU:
#  MEMBERI PETA bab + sub-bab + KEYAKINAN. USER yang memutuskan.
#
#  Kenapa Jev dipakai di sini: konversi = RESTRUKTURISASI STRUKTUR (bukan
#  menilai mutu tulisan) ⇒ tepat tugas Jev. Larangan lama "Jev dilarang" itu
#  untuk 8 modul PENILAI MUTU (konsistensi/etika/pustaka/gambar/citation)
#  yang Jev TERBUKTI gagal — bukan untuk konversi.
#
#  ✅ SKEMA JEV YANG BENAR (terukur ke `openrouter.ai/api/v1/systemone`
#  LANGSUNG, 07 Okt 2026 — sumber: skill `typesafe-jev` + dokumentasi resmi):
#      · NAMA pertanyaan = **BEBAS apa saja** (tidak dikirim ke model)
#      · TIPE = **3**: `noul` · `choice` · `score`
#      · `criteria` = **WAJIB PER-TIPE**:
#            noul   → ⛔ **TIDAK BOLEH ada `criteria`** (⇒ 400)
#            choice → **OBJEK** {'opsi': 'deskripsi'}
#            score  → **ARRAY** ['tingkat 0', 'tingkat 1', …]  (2–10 tingkat)
#
#  ❌ CARA LAMA (DIHAPUS — BAHAYA, JANGAN DIPAKAI LAGI):
#      a) menulis `criteria` pada `noul` (string/objek/array — semua 400)
#      b) menulis `criteria` ARRAY pada `choice`  ⇒ "expected record, received array"
#      c) menulis `criteria` OBJEK pada `score`   ⇒ "expected array"
#      d) memakai `options` sebagai ganti `criteria` pada `choice`
#      Semua itu ⇒ HTTP 400 Zod yang DISAMAR jadi **HTTP 503** oleh 9router,
#      sehingga tampak seolah "Jev/9router rusak".
#
#  🔴 KESALAHAN WULAN 07 Okt 2026 (JANGAN TERULANG):
#      – menyimpulkan "hanya 3 NAMA pertanyaan yang sah" ⇒ **KELIRU BERAT**;
#        yang terbatas hanya BENTUK `criteria`, nama bebas.
#      – menyimpulkan "Jev tidak stabil"                      ⇒ **KELIRU**;
#        penyebabnya `criteria` bentuk salah, konsisten 100%.
#      – menyimpulkan "Jev menolak jenis/choice/score"        ⇒ **KELIRU**;
#        ketiganya JALAN begitu `criteria` benar.
#      ⇒ ATURAN: Jev 503/400 → PERIKSA BENTUK `criteria` DULU, jangan tuduh Jev.
PERTANYAAN_PETA = {
    'jumlah_bab': {
        'instructions': ('Berapa bab akademik yang BENAR-BENAR ada di naskah '
                         'ini? Jangan hitung daftar isi, daftar tabel, daftar '
                         'pustaka, halaman judul, atau abstrak — hanya bab yang '
                         'punya isi.'),
        'type': 'choice',
        'criteria': {'0': 'tidak ada', '1': 'satu', '2': 'dua', '3': 'tiga',
                     '4': 'empat', '5': 'lima', '6': 'enam', '7': 'tujuh',
                     '8': 'lebih dari tujuh'},
    },
    'semua_romawi_sah': {
        'instructions': ('Apakah semua nomor bab memakai angka romawi yang SAH '
                         '(I, II, III, IV, V) — tidak ada yang salah tulis atau '
                         'melompat?'),
        'type': 'noul',
    },
    'berurutan': {
        'instructions': ('Apakah bagian-bagian naskah tersusun BERURUTAN tanpa '
                         'melompat atau kembali ke belakang?'),
        'type': 'noul',
    },
}


# ══════════════════════════════════════════════════════════════════════════
#  JEV — PERIKSA MUTU ARTIKEL (optimasi 07 Okt 2026, putusan Bos)
# ══════════════════════════════════════════════════════════════════════════
#  LATAR: Bos — "user bayar mahal, masa kita tidak kasih yang berbayar juga".
#  ⇒ Jev TIDAK cukup jadi mata peta bab. Ia jadi PEMERIKSA KEBERADAAN 11
#  ELEMEN MUTU artikel jurnal + bagian wajib IMRAD.
#
#  ⚠️ BATAS PERAN (putusan Bos 05–06 Okt): Jev GAGAL menilai MUTU TULISAN
#  ("bagus/tidak"). Yang dipakai di sini = KEBERADAAN bagian ("ada/tidak ada")
#  — itu STRUKTUR, bukan penilaian mutu. Nilai 'noul' = probabilitas "ya ada".
#  Ini SUDAH TERBUKTI (07 Okt): 12 pertanyaan dijawab 0,7 dtk, hasil masuk akal
#  (novelty 0,10 TIDAK ADA · daftar pustaka 0,34 TIDAK ADA — memang tak ada).
#
#  🔒 JEV HANYA MELAPOR. Ia TIDAK memblokir dan TIDAK memutuskan. Yang
#  memutuskan = USER. Kalimatnya harus "Poin X belum ada" — bukan "naskahmu
#  salah". Kalau Jev ragu → bilang "perlu diperiksa", JANGAN klaim.
#
#  💰 INI PINTU JUALAN (pola Bos): "Poin ini belum ada: XXX → apakah lanjut?
#  mau lengkapi pakai AI = KENA Token Revisi". Nol tabel baru, nol dompet baru.

#  11 ELEMEN MUTU — SUMBER ASLI: /opt/data/services/jurnalkit/jemt_prompt.md:50-63
#  (dibaca langsung, bukan karangan). Dipetakan jadi pertanyaan 'noul'.
ELEMEN_MUTU = {
    'ada_hook': {
        'instructions': ('Apakah ADA pembukaan yang MENARIK perhatian pembaca '
                         '(hook) — bukan kalimat klise seperti "Pendidikan '
                         'merupakan hal penting"?'),
        'type': 'noul',
    },
    'ada_state_of_art': {
        'instructions': ('Apakah ADA penjelasan perkembangan ilmu terkini pada '
                         'bidang ini (state of the art)?'),
        'type': 'noul',
    },
    'ada_gap': {
        'instructions': ('Apakah ADA pernyataan KESENJANGAN / celah penelitian '
                         '(gap) yang jelas — apa yang belum diteliti orang lain?'),
        'type': 'noul',
    },
    'ada_novelty': {
        'instructions': ('Apakah ADA pernyataan KEBARUAN (novelty) yang jelas — '
                         'apa yang baru dari penelitian ini?'),
        'type': 'noul',
    },
    'ada_findings': {
        'instructions': ('Apakah ADA penyampaian TEMUAN utama yang jelas?'),
        'type': 'noul',
    },
    'ada_critical_analysis': {
        'instructions': ('Apakah ADA analisis KRITIS — bukan hanya memaparkan, '
                         'tapi juga membahas mengapa hasilnya begitu?'),
        'type': 'noul',
    },
    'ada_diskusi_komparatif': {
        'instructions': ('Apakah ADA pembahasan yang MEMBANDINGKAN hasil dengan '
                         'penelitian sebelumnya?'),
        'type': 'noul',
    },
    'ada_kaitan_teori': {
        'instructions': ('Apakah ADA kaitan hasil penelitian dengan TEORI yang '
                         'dipakai?'),
        'type': 'noul',
    },
    'ada_limitasi': {
        'instructions': ('Apakah ADA pernyataan KETERBATASAN penelitian?'),
        'type': 'noul',
    },
    'ada_rekomendasi': {
        'instructions': ('Apakah ADA rekomendasi untuk penelitian selanjutnya?'),
        'type': 'noul',
    },
    'ada_implikasi': {
        'instructions': ('Apakah ADA implikasi teoretis dan/atau praktis?'),
        'type': 'noul',
    },
}

#  BAGIAN WAJIB IMRAD — untuk Jev periksa mutu.
#  ⚠️ JANGAN beri nama `BAGIAN_WAJIB` — nama itu SUDAH DIPAKAI mesin
#  `periksa_hasil()` (baris ~106) untuk pemeriksa hasil ARTIKEL. Wulan
#  sempat menimpanya 07Okt26 → periksa_hasil RUSAK (1 gerbang gagal).
#  ⇒ pakai nama berbeda: BAGIAN_WAJIB_JEV.
BAGIAN_WAJIB_JEV = {
    'ada_abstrak': {'instructions': 'Apakah ADA abstrak?', 'type': 'noul'},
    'ada_pendahuluan': {'instructions': 'Apakah ADA bagian pendahuluan?',
                        'type': 'noul'},
    'ada_metode': {'instructions': ('Apakah ADA bagian metode penelitian '
                                    '(cara penelitian dilakukan)?'),
                   'type': 'noul'},
    'ada_hasil': {'instructions': 'Apakah ADA bagian hasil?', 'type': 'noul'},
    'ada_pembahasan': {'instructions': 'Apakah ADA bagian pembahasan?',
                       'type': 'noul'},
    'ada_kesimpulan': {'instructions': 'Apakah ADA bagian kesimpulan?',
                       'type': 'noul'},
    'ada_pustaka': {'instructions': 'Apakah ADA daftar pustaka/referensi?',
                    'type': 'noul'},
}

#  Label manusia untuk laporan ke user (jangan tampilkan nama teknis).
LABEL_ELEMEN = {
    'ada_hook': 'pembukaan yang menarik (hook)',
    'ada_state_of_art': 'perkembangan ilmu terkini (state of the art)',
    'ada_gap': 'pernyataan celah penelitian (gap)',
    'ada_novelty': 'pernyataan kebaruan (novelty)',
    'ada_findings': 'penyampaian temuan utama',
    'ada_critical_analysis': 'analisis kritis',
    'ada_diskusi_komparatif': 'pembahasan pembanding dengan penelitian lain',
    'ada_kaitan_teori': 'kaitan hasil dengan teori',
    'ada_limitasi': 'pernyataan keterbatasan penelitian',
    'ada_rekomendasi': 'rekomendasi penelitian lanjutan',
    'ada_implikasi': 'implikasi teoretis & praktis',
    'ada_abstrak': 'abstrak',
    'ada_pendahuluan': 'pendahuluan',
    'ada_metode': 'metode penelitian',
    'ada_hasil': 'hasil',
    'ada_pembahasan': 'pembahasan',
    'ada_kesimpulan': 'kesimpulan',
    'ada_pustaka': 'daftar pustaka',
}

#  Ambang: di bawah ini JANGAN diklaim "ada" (bahaya: user senang padahal cacat).
AMBANG_ADA = 0.50
#  Di antara AMBANG_RAGU..AMBANG_ADA → jangan klaim, minta diperiksa manusia.
AMBANG_RAGU = 0.35


def _bahan_mutu(teks: str) -> str:
    """Bahan untuk Jev PERIKSA MUTU — beda dari bahan peta bab.

    ⚠️ AKAR 07 Okt 2026 (terbukti atas naskah Asih): bahan peta bab
    (`satpam._susun_state`) HANYA memuat daftar BAB + cuplikan 400 kar tiap bab
    ⇒ ABSTRAK & DAFTAR PUSTAKA (di depan/belakang naskah, di luar bab) TIDAK
    IKUT. Akibatnya Jev menjawab "tidak ada abstrak" (0,10) padahal naskah Asih
    PUNYA abstrak (2× kata ABSTRAK) ⇒ Jev SALAH, padahal yang salah = BAHAN.
    🔎 Pelajaran: Jev salah ⇒ PERIKSA DULU BAHANNYA sebelum menuduh Jev.

    ⚠️ AKAR KE-2 (07 Okt 2026, terbukti atas ARTIKEL hasil konversi):
    potongan `awal + [5000:9000] + akhir[-5000:]` BENAR untuk NASKAH (abstrak
    di depan, pustaka di belakang, tak ada lampiran). Untuk ARTIKEL hasil,
    urutannya ABSTRAK · PENDAHULUAN · METODE · HASIL · KESIMPULAN ·
    DAFTAR PUSTAKA · LAMPIRAN ⇒ potongan [-5000:] mendarat di **LAMPIRAN**
    (bukan pustaka), dan [5000:9000] mendarat di **sisa pendahuluan**
    (bukan metode/hasil). TERUKUR: dari 52.926 kar, METODE · HASIL ·
    KESIMPULAN · PUSTAKA **TIDAK PERNAH terkirim** ⇒ Jev bilang
    "kesimpulan 0,20" padahal ADA (5.163 kar) — Jev SALAH, BAHAN yang cacat.

    ⇒ Cara baru: KENALI bagian (baris judul HURUF BESAR seperti 'METODE',
      'KESIMPULAN', 'DAFTAR PUSTAKA'), lalu ambil cuplikan AWAL + AKHIR tiap
      bagian. Kalau penanda bagian tak ketemu (naskah mentah) → pakai cara
      LAMA (awal+tengah+akhir) supaya naskah tetap terlayani.
    """
    t = teks or ''
    if len(t) <= 14000:
        return t

    #  ── ① Coba jalur ARTIKEL: kenali penanda bagian (baris HURUF BESAR) ──
    bagian = _potong_per_bagian(t)
    if bagian:
        return bagian

    #  ── ② Jalur LAMA (naskah mentah tanpa penanda bagian) ──
    return (f'{t[:5000]}\n\n[...BAGIAN TENGAH NASKAH...]\n{t[5000:9000]}\n\n'
            f'[...AKHIR NASKAH...]\n{t[-5000:]}')


#  Penanda bagian ARTIKEL hasil konversi (judul HURUF BESAR dari
#  `artikel_ke_teks`). Sekali cari, dipakai bersama oleh `_bahan_mutu`.
_PENANDA_BAGIAN = (
    'ABSTRAK', 'ABSTRACT', 'PENDAHULUAN', 'METODE', 'HASIL DAN PEMBAHASAN',
    'KESIMPULAN', 'DAFTAR PUSTAKA', 'LAMPIRAN',
)

#  ⚠️ AKAR KE-4 (08 Okt 2026, terbukti atas NASKAH SKRIPSI Asih): penanda
#  artikel TIDAK ketemu di skripsi (skripsi pakai 'BAB I PENDAHULUAN',
#  'BAB V PENUTUP') ⇒ jatuh ke jalur LAMA ⇒ potongan `[-5000:]` mendarat di
#  LAMPIRAN, bagian GAP/NOVELTY/HOOK (BAB I) & LIMITASI/REKOMENDASI (BAB V)
#  TIDAK IKUT ⇒ Jev bilang novelty 0,17 · gap 0,38 · hook 0,30 · limitasi
#  0,23 · rekomendasi 0,19 padahal SEMUA ADA (terukur: 'celah', 'Gap
#  research', 'keterbatasan', 'rekomendasi', 'fenomena' ADA di naskah, TIDAK
#  ADA di bahan). ⇒ Kenali penanda SKRIPSI: baris yang mengandung 'BAB ' +
#  ANGKA ROMAWI (I, II, III, IV, V) — juga 'SARAN'/'PENUTUP'/'TINJAUAN
#  PUSTAKA'. Sehingga skripsi pun dipotong per-bagian, bukan potong buta.
_POLA_BAB = (
    r'^\s*BAB\s+([IVX]+)\b',
    r'^\s*BAB\s+(\d+)\b',
)



#  ──────────────────────────────────────────────────────────────────────
#  POLA RESMI "STRUCTURE RECOVERY" (cookbook TypeSafe) — 08 Okt 2026
#  ──────────────────────────────────────────────────────────────────────
#  Sumber: skill `typesafe-jev` → `references/cookbook-structure-recovery.md`.
#  Kutipan resmi:
#    *"the model never generates text: it answers NARROW QUESTIONS about the
#      document... and CODE does the rendering"*
#    *"the model gets only the questions code cannot answer from the text"*
#    *"Blank lines and explicit markers are read in code, never sent to the
#      model"*
#
#  ⚠️ CARA WULAN YANG GAGAL 6× (JANGAN DIULANG):
#    (a) tanya "berapa bab?" ⇒ kelemahan resmi #2 (Jev TIDAK menghitung)
#        ⇒ jawab "1" lalu "0" padahal 5.
#    (b) tanya "sebutkan judul bab" bertipe noul ⇒ kelemahan resmi #9
#        (Jev BUKAN penulis teks) + noul = ya/tidak.
#    (c) tanya "apakah baris ini awal bab BERISI?" ⇒ SEMUA jawaban mepet 0,5
#        (terukur asli 0,54 vs palsu 0,49) — TAK terpisah. Sebab: jawaban
#        pertanyaan itu ADA DI TEKS (kode bisa lihat panjang uraian) ⇒ bukan
#        pertanyaan untuk Jev.
#    (d) tanya "wilayah apa baris ini?" (choice) ⇒ mepet juga.
#    (e) kirim baris ber-ID + FAKTA panjang buatan kode ⇒ fakta cacat
#        (diukur ke "kandidat berikutnya", bukan panjang bagian) ⇒ Jev dihukum.
#    (f) kirim SELURUH naskah (2.224 baris / 69rb kar) ⇒ HTTP 503
#        (kelemahan #5 context rot: "saring di kode dulu").
#
#  ✅ POLA RESMI YANG TERBUKTI (naskah Asih fid=81, 11 dtk, 0 gagal):
#    PASS 1 — JEV MENYAMBUNG: satu `noul` per pasangan baris —
#      "Does line Lxxx pick up mid-sentence, continuing a sentence left
#       unfinished at the end of line Lyyy?"
#      ⇒ KODE gabung baris tersambung jadi BLOK.
#      (Blank line dibaca KODE sebagai batas — tak dikirim ke Jev.)
#    PASS 2 — JEV MENGKLASIFIKASI: satu `choice` per blok pendek —
#      "What kind of content is block Bxxx?" criteria: heading / paragraph /
#      table_caption / list_item / other ⇒ blok `heading` = JUDUL.
#
#    HASIL NYATA: Jev menemukan SEMUA judul dengan tepat —
#      · `BAB I` conf 1,00 + `PENDAHULUAN` conf 1,00   (bab I; judul di bawah)
#      · `Sistematika Penulisan` conf 1,00 ⇒ KODE tahu blok rangka mulai di
#        sini; heading 'BAB I PENDAHULUAN' … 'BAB V PENUTUP' di antaranya
#        DIBUANG KODE (itu rangka, bukan bab berisi).
#      · `BAB II` conf 1,00 + `TINJAUAN PUSTAKA` conf 1,00 = bab II
#      · 'Gap research' conf 1,00 · 'Rumusan Masalah' conf 1,00 ·
#        'Landasan Teori' conf 1,00 · 'Hipotesis' conf 1,00 · dst.
#
#  ⇒ PEMBAGIAN PERAN: Jev = MATA (sambung + klasifikasi); KODE = perakit
#     peta (gabung heading berurutan, buang rangka sistematika, potong ikut
#     peta). Jev TIDAK PERNAH menyalin/menulis teks.
#  ──────────────────────────────────────────────────────────────────────

#  Kriteria klasifikasi blok (persis cookbook, ditambah `table_caption`).
_KRITERIA_BLOK = {
    'heading': ('A short label or title naming the document or the section '
                'that follows it - not a full sentence of content'),
    'paragraph': ('Running prose: one or more complete sentences of '
                  'explanatory or narrative text'),
    'table_caption': 'A caption or label for a table or figure',
    'list_item': 'One entry in a list of parallel items',
    'other': 'Anything else',
}

#  Ambang sambung (persis cookbook): sesudah baris menggantung (tanpa tanda
#  akhir kalimat) → 0,2; sesudah tanda akhir kalimat (. ! ? : ;) → 0,5.
_SAMBUNG_GANTUNG, _SAMBUNG_AKHIR = 0.2, 0.5

#  Jatah per panggilan (kelemahan #5 context rot: "saring di kode dulu").
#  Terukur: state ~16rb kar + ~100 tanya = LULUS (0,6 dtk).
#           94rb kar / 567 tanya ⇒ HTTP 503.
#  ⚠️ TERUKUR 08 Okt 2026: yang menentukan 503 = PANJANG STATE, bukan jumlah
#     baris. Putus antara 80rb–120rb kar (120rb = 503 selama 11 dtk).
#     ⇒ jaga state ≤ ~60rb kar (aman), jangan pernah ≥ 100rb.
_GAL_BARIS = 100          # baris per panggilan PASS 1
_GAL_BLOK = 60            # blok per panggilan PASS 2
_GAL_KAND = 120           # KANDIDAT sambung per panggilan PASS 1 (baru 08 Okt)
_ULANG_JEV = 3            # 503 = MERAH PALSU → ulang maks 3× (pelajaran lama)
_JEDA_JEV = 0.8

#  ── OPTIMALISASI 08 Okt 2026 (Bos: "cari nilai optimal, jangan terlalu
#     ketat dan jangan terlalu longgar") ────────────────────────────────
#  AKAR TERUKUR: 20 detik itu = 32 panggilan × ~0,64 dtk (Jev SENDIRI cepat;
#  bukan jeda, bukan bahan besar). Yang bengkak = PASS 1 menanya SEMUA baris
#  (1.874 baris = 23 panggilan) & PASS 2 menanya 801 blok (14 panggilan).
#
#  ⛔ JANGAN saring pakai PANJANG JUDUL (mis. "hanya blok ≤60 kar"):
#     TERUKUR — judul bab kampus lain bisa 65/78/93 kar; ambang 60
#     MENGHILANGKAN bab-nya. Keselamatan > kecepatan.
#  ✅ SARING PAKAI BENTUK (kode tahu, tak menebak):
#     · "kandidat sambung" = pasangan baris PENDEK (kalimat terbelah selalu
#       baris pendek; paragraf panjang tak pernah terbelah).
#     · "bukan judul" = tabel (pipa `|`), laporan statistik (Coefficients/
#       Cronbach/Sig./ANOVA), kalimat berakhir titik yang panjang, deret angka.
#  HASIL TERUKUR (naskah Asih fid=81 · 1.874 baris · 159.909 kar):
#     32 panggilan/20,4 dtk  ⇒  ±10 panggilan/6,6 dtk  · peta bab TETAP 5/5.
_KANDIDAT_MAKS_KAR = 60   # pasangan baris <= ini = kandidat terbelah
_BLOK_PENDEK_MAKS = 110   # pagar luar blok "mungkin judul" (judul 93 kar aman)

#  Kata khas LAPORAN/TABEL — kode tahu ini bukan judul (bukan tebakan).
_BUKAN_JUDUL_KATA = re.compile(
    r'\b(Coefficients|Collinierity|Tolerance|Cronbach|Sum of Squares|'
    r'Mean Square|Sig\.|Std\. Error|Reliability Statistics|Model Summary|'
    r'ANOVA|Descriptive Statistics|Correlations)\b', re.IGNORECASE)

#  Penanda internal yang dibaca KODE, jangan dikirim ke Jev.
_PENANDA_INTERNAL = ('[[TABEL-', '[[GAMBAR-', '[[/', '[[TABEL:', '[[GAMBAR:')


def _tanya_jev_kuat(state: str, pertanyaan: dict):
    """Panggil Jev; HTTP 503 = MERAH PALSU → ulang maks `_ULANG_JEV` kali.

    ⚠️ Terukur 08 Okt 2026: 9router MEMOTONG pesan galat jadi 503. Sebagian
    503 itu gangguan sesaat (terbukti: panggilan yang sama LULUS saat
    diulang), sebagian karena state kelewat besar. Karena itu: ULANG dulu,
    baru menyerah — jangan vonis "skema salah" dari 1× gagal.
    """
    try:
        from . import satpam
    except Exception:                                          # noqa: BLE001
        return None
    for _ in range(_ULANG_JEV):
        try:
            jawab = satpam.tanya_bebas_mutu(state, pertanyaan)
        except Exception as e:                                 # noqa: BLE001
            log.warning('[konversi] tanya Jev gagal: %s', e)
            jawab = None
        if jawab:
            return jawab
        time.sleep(_JEDA_JEV)
    return None


def _kandidat_sambung(baris: list) -> list:
    """KODE pilih baris yang MUNGKIN terbelah — fakta, bukan tebakan.

    Kalimat yang terbelah SELALU jadi dua baris PENDEK (judul 2 baris,
    potongan kalimat). Paragraf panjang TIDAK MUNGKIN terbelah — tak ada
    editor memotong paragraf jadi dua baris judul.

    ⚠️ TERUKUR 08 Okt 2026: saring ini memotong PASS 1 dari 23 panggilan
    (semua 1.874 baris) jadi 5 panggilan (483 kandidat), TANPA mengubah peta
    bab sedikit pun. Yang menentukan 503 = panjang STATE, jadi kirim hanya
    baris yang perlu = lebih aman sekaligus lebih cepat.
    """
    kand: list = []
    for n in range(1, len(baris)):
        a, b = baris[n - 1], baris[n]
        if not a or not b:
            continue
        if len(a) <= _KANDIDAT_MAKS_KAR and len(b) <= _KANDIDAT_MAKS_KAR:
            kand.append(n)
    return kand


def _pecah_blok(teks: str) -> list:
    """PASS 1 — Jev MENYAMBUNG baris terbelah → daftar blok.

    KODE : pecah baris, normalisasi spasi, buang penanda internal, catat
           baris kosong (`kosong`) — semuanya dibaca KODE, tak dikirim ke Jev.
           KODE juga MENYARING kandidat (`_kandidat_sambung`) — sesuai
           kelemahan #5: "saring di kode dulu; kirim hanya yang perlu".
    JEV  : satu `noul` per pasangan kandidat baris — "does line Lxxx pick up
           mid-sentence?" Dikirim per jatah supaya tak kena context rot.
    KODE : gabung baris tersambung jadi blok (ambang dari cookbook).

    Balik: [{'text':…, 'lines':[…], 'kosong':bool}] — [] bila Jev mati.
    """
    baris: list = []
    for mentah in (teks or '').split('\n'):
        s = ' '.join(mentah.split())
        if s.startswith(_PENANDA_INTERNAL):
            continue                       # penanda internal: dibaca KODE
        baris.append(s)
    if len(baris) < 4:
        return []

    #  JEV pass 1 — sambung (HANYA baris kandidat + tetangga kirinya)
    sambung: dict = {}
    kandidat = _kandidat_sambung(baris)
    for mulai in range(0, len(kandidat), _GAL_KAND):
        sub = kandidat[mulai:mulai + _GAL_KAND]
        #  Jev butuh baris SEBELUMNYA untuk menilai "menyambung ke atas?" —
        #  itu SATU-SATUNYA tetangga yang perlu; sisanya tak dikirim.
        perlu = sorted({n - 1 for n in sub} | set(sub))
        state = '\n'.join(f'L{n:04d}| {baris[n][:200]}' for n in perlu)
        tanya = {f'L{n:04d}': {'instructions':
                 (f'Does line L{n:04d} pick up mid-sentence, '
                  f'continuing a sentence left unfinished at the end of '
                  f'line L{n - 1:04d}?'), 'type': 'noul'}
                 for n in sub}
        if not tanya:
            continue
        jawab = _tanya_jev_kuat(state, tanya)
        if jawab:
            sambung.update(jawab)

    #  KODE rakit blok
    def _akhir_kalimat(x: str) -> bool:
        return re.search(r'[.!?:;\u2026]["\')\]]*$', x) is not None

    blok: list = []
    for n, b in enumerate(baris):
        kosong = not b
        gabung = False
        if blok and not kosong:
            noul = (sambung.get(f'L{n:04d}') or {}).get('noul')
            if noul is not None:
                ambang = (_SAMBUNG_AKHIR if _akhir_kalimat(baris[n - 1])
                          else _SAMBUNG_GANTUNG)
                try:
                    gabung = float(noul) >= ambang
                except (TypeError, ValueError):
                    gabung = False
        if gabung:
            blok[-1]['text'] = (blok[-1]['text'] + ' ' + b).strip()
            blok[-1]['lines'].append(n)
        else:
            blok.append({'text': b, 'lines': [n], 'kosong': kosong})
    return blok


def _bukan_judul(t: str) -> bool:
    """KODE tahu blok ini BUKAN judul — dari BENTUK, bukan panjang.

    ⛔ JANGAN pakai panjang sebagai penentu: TERUKUR 08 Okt 2026, judul bab
    kampus lain bisa 65/78/93 kar (mis. "KAJIAN PUSTAKA, KERANGKA PEMIKIRAN
    DAN PENGEMBANGAN HIPOTESIS" = 56 kar) ⇒ ambang panjang MENGHILANGKAN bab.
    ✅ Pakai bentuk yang KODE bisa pastikan:
      ① tabel: ada pipa `|` pemisah kolom (≥2)
      ② laporan statistik: Coefficients/Cronbach/Sig./ANOVA/…
      ③ kalimat: panjang >55 kar DAN berakhir titik ⇒ itu paragraf pendek
      ④ deret angka dominan (>30% isi) ⇒ data, bukan judul
    """
    if t.count('|') >= 2:
        return True                                        # ① tabel
    if _BUKAN_JUDUL_KATA.search(t):
        return True                                        # ② laporan
    if len(t) > 55 and re.search(r'\.\s*$', t):
        return True                                        # ③ kalimat
    if len(t) > 20:
        angka = sum(1 for c in t if c.isdigit())
        if angka / len(t) > 0.30:
            return True                                    # ④ data
    return False


def _klasifikasi_blok(blok: list) -> dict:
    """PASS 2 — Jev MENGKLASIFIKASI tiap blok → {idx_blok: 'heading'|…}.

    Hanya blok yang MUNGKIN judul yang ditanya — blok panjang (paragraf) dan
    blok yang bentuknya jelas bukan judul (`_bukan_judul`) dilewati KODE.
    Hemat + sesuai kelemahan #5 "saring di kode dulu". Balik {} bila Jev mati.

    ⚠️ TERUKUR 08 Okt 2026 (naskah Asih): 819 blok → 296 setelah saring bentuk
    (PASS 2: 14 panggilan/9,0 dtk → 5 panggilan/3,0 dtk), peta bab TETAP 5/5,
    dan NOL blok judul hilang (semua judul bab di naskah 5–7 kar).
    """
    pendek = [n for n, b in enumerate(blok)
              if b.get('text') and len(b['text']) <= _BLOK_PENDEK_MAKS
              and not _bukan_judul(b['text'])]
    hasil: dict = {}
    for mulai in range(0, len(pendek), _GAL_BLOK):
        sub = pendek[mulai:mulai + _GAL_BLOK]
        state = '\n'.join(f'B{n:03d}| {blok[n]["text"][:170]}' for n in sub)
        tanya = {f't{n:03d}': {'instructions':
                 f'What kind of content is block B{n:03d}?',
                 'type': 'choice', 'criteria': _KRITERIA_BLOK} for n in sub}
        jawab = _tanya_jev_kuat(state, tanya)
        if jawab:
            hasil.update(jawab)
    return {n: (hasil.get(f't{n:03d}') or {}).get('choice') for n in pendek}


def _posisi_dari_jev(teks: str) -> list:
    """Minta JEV mengenali BENTUK naskah → balik [(idx_baris, nama_bab)].

    POLA RESMI "structure recovery" (cookbook TypeSafe) — 2 pass:
      ① KODE : pecah baris + beri ID (`L014| teks`). Penanda internal & baris
               kosong dibaca KODE, tak dikirim ke Jev.
      ② JEV  : PASS 1 sambung ("does line pick up mid-sentence?") → blok.
      ③ JEV  : PASS 2 klasifikasi blok ("what kind of content?") → heading.
      ④ KODE : RAKIT peta — heading berurutan digabung jadi satu bab; heading
               di dalam blok rangka `Sistematika Penulisan` DIBUANG.
               Jev TIDAK PERNAH menyalin/menulis teks.

    Kalau Jev mati → balik [] dan pemanggil jatuh ke cadangan
    `_cari_bab_skripsi` (regex). Jev bukan penghalang — dia PEMBUKA jalan.
    """
    try:
        from . import satpam
        from .state import buang_daftar_isi
    except Exception:                                          # noqa: BLE001
        return []
    if not getattr(satpam, 'AKTIF', False) or not teks:
        return []

    #  ⚠️ WAJIB: buang bagian pembuka (daftar isi/dafar tabel) DULUAN. Tanpa
    #  ini, baris daftar isi (`BAB I PENDAHULUAN1` — angka halaman nempel)
    #  ikut terklasifikasi `heading` oleh Jev lalu lolos jadi bab palsu
    #  (terukur 08 Okt: 5 bab palsu di baris 132–220).
    bersih = buang_daftar_isi(teks)
    if not bersih or len(bersih) < 0.3 * len(teks):
        bersih = teks                       # pembersih terlalu agresif → aman

    blok = _pecah_blok(bersih)
    if len(blok) < 4:
        return []
    jenis = _klasifikasi_blok(blok)
    if not jenis or not any(v == 'heading' for v in jenis.values()):
        return []

    #  ── KODE: rakit peta bab dari blok `heading` ──────────────────────────
    #  Aturan (semua TERUKUR di naskah Asih fid=81):
    #    · blok heading `SISTEMATIKA PENULISAN` ⇒ RANGKA mulai di sini.
    #      Semua blok heading sesudahnya DIBUANG sampai ketemu blok NON-heading
    #      yang panjang (uraian bab I pertama) — karena di rangka, judul bab
    #      ('BAB I PENDAHULUAN' … 'BAB V PENUTUP') datang BERUNTUN RAPAT tanpa
    #      uraian di antaranya, sedangkan bab ASLI selalu diikuti uraian.
    #      ⚠️ JANGAN cari 'sistematika' di dalam blok yang memuat 'BAB'
    #      (kesalahan 08 Okt): blok 'Sistematika Penulisan' TERPISAH dari blok
    #      'BAB I PENDAHULUAN' — Jev memang memberi keduanya tipe `heading`.
    #    · heading memuat 'BAB <romawi|angka>' = AWAL bab baru.
    #    · heading TANPA 'BAB' TEPAT sesudah awal bab = JUDUL bab itu
    #      (terukur: 'BAB II' + 'TINJAUAN PUSTAKA' = satu bab).
    #  ⚠️ CELAH TERUKUR 08 Okt 2026 (naskah SKRIPSI S1 unmul fid=107): template
    #  kampus menulis judul NEMPEL nomor — `BAB IPENDAHULUAN` (tanpa spasi).
    #  `_BAB_AWAL` lama gagal ⇒ 0 bab terdeteksi (padahal Jev SUDAH bilang blok
    #  itu `heading`). Ini BUKAN regex menebak bentuk — Jev tetap yang
    #  mengenali; kode hanya MEMISAH nomor & judul yang nempel.
    #  Dukur 08 Okt: 26 LULUS / 0 GAGAL (lihat _sketsa/jev-struktur/
    #  _uji_pemisah_bab.py) — termasuk MENOLAK daftar isi (`…PENDAHULUAN1`) &
    #  kalimat panduan (`Bab 4 dan Bab 5 dapat Anda tulis…`).
    _BAB_AWAL = re.compile(r'^\s*BAB\s+([IVXLC]+|\d+)\s*(.*)$', re.IGNORECASE)
    _RANGKA = re.compile(r'^\s*sistematika\s+penulisan\s*$', re.IGNORECASE)
    _BAB_NEMPEL = re.compile(
        r'^\s*BAB\s*([IVXLC]+|\d+)(?=[A-Za-z]{2,})(.*)$', re.IGNORECASE)
    _ROM = re.compile(r'^[IVXLC]+$', re.IGNORECASE)
    #  Kata yang HANYA muncul di kalimat, tak pernah di judul bab. Dipakai
    #  MENOLAK kalimat panduan template ('…yang dipakai', '…untuk peneliti').
    #  ⚠️ JANGAN tolak karena huruf kecil — judul gaya campuran
    #  ('BAB IV Hasil dan Pembahasan') UMUM di kampus & WAJIB lolos.
    _KATA_KALIMAT = re.compile(
        r'\b(yang|dapat|akan|untuk|adalah|telah|sudah|bisa|harus|oleh|pada|'
        r'dengan cara|seperti|misalnya|karena|agar|supaya|tetapi|namun|'
        r'silahkan|mohon|jangan|tulis|tuliskan|gunakan|lihat)\b', re.IGNORECASE)

    def _urai_bab(judul: str):
        """Pisah nomor & judul bab → (nomor, sisa_judul); None bila bukan bab.

        Dukung tiga gaya yang TERUKUR ada di naskah kampus:
          'BAB I PENDAHULUAN'      → ('I', 'PENDAHULUAN')   (spasi normal)
          'BAB IPENDAHULUAN'       → ('I', 'PENDAHULUAN')   (NEMPEL, selamat)
          'BAB IV Hasil dan Pembahasan' → ('IV', 'Hasil dan Pembahasan')
        """
        #  ⓵ angka halaman nempel di ujung = baris DAFTAR ISI, bukan bab
        #     ('BAB I PENDAHULUAN1') — dukur: dulu lolos jadi bab PALSU.
        if re.search(r'\d\s*$', judul) and not re.fullmatch(
                r'\s*BAB\s+\d+\s*$', judul, re.IGNORECASE):
            return None
        m0 = _BAB_AWAL.match(judul)
        if m0:
            nomor, sisa = m0.group(1), (m0.group(2) or '').strip()
            if sisa and (sisa[0].islower() or _KATA_KALIMAT.search(sisa)):
                return None                # kalimat, bukan judul
            return nomor, sisa
        mn = _BAB_NEMPEL.match(judul)
        if mn:
            nomor, sisa = mn.group(1) or '', (mn.group(2) or '').strip()
            if sisa and _KATA_KALIMAT.search(sisa):
                return None
            if not re.fullmatch(r'\d+', nomor):
                #  nomor romawi greedily menelan huruf judul
                #  ('IPENDAHULUAN' → 'IPENDA') ⇒ ambil potongan TERPANJANG
                #  yang masih sah sebagai romawi.
                for k in range(len(nomor), 0, -1):
                    if _ROM.match(nomor[:k]):
                        nomor = nomor[:k]
                        break
            return nomor, sisa
        return None

    posisi: list = []
    rangka = False
    for n, b in enumerate(blok):
        jenis_blok = jenis.get(n)
        judul = (b['text'] or '').strip()
        if jenis_blok != 'heading':
            #  blok non-heading PANJANG = uraian ⇒ rangka (kalau sedang aktif)
            #  hanya boleh berakhir di sini; lihat cabang 'BAB <n>' di bawah.
            continue
        if not judul:
            continue
        if _RANGKA.match(judul):
            rangka = True                  # mulai blok rangka sistematika
            continue
        urai = _urai_bab(judul)
        if urai:
            nomor, sisa = urai
            #  Judul dirapikan: 'BAB IPENDAHULUAN' → 'BAB I PENDAHULUAN'.
            rapi = f'BAB {nomor}' + (f' {sisa}' if sisa else '')
            #  Di dalam rangka, judul ringkas ('BAB I PENDAHULUAN', satu baris,
            #  pendek) datang rapat. Bab ASLI ditulis 'BAB <n>' SENDIRI
            #  (judulnya jadi blok heading terpisah di baris bawah).
            if rangka and not re.fullmatch(r'BAB\s+([IVXLC]+|\d+)',
                                           rapi, re.IGNORECASE):
                continue                   # baris rangka → BUANG
            rangka = False                 # 'BAB <n>' asli → rangka berakhir
            posisi.append((b['lines'][0], rapi[:80]))
        elif posisi and not rangka and len(posisi[-1][1]) <= 12 \
                and len(judul) <= 70:
            #  heading lanjutan: lengkapi judul bab terakhir yang masih pendek
            #  (mis. 'BAB II' → 'BAB II TINJAUAN PUSTAKA')
            i_akhir, judul_akhir = posisi[-1]
            posisi[-1] = (i_akhir, f'{judul_akhir} {judul}'[:80])
    return posisi if len(posisi) >= 2 else []


def _potong_per_bagian(teks: str) -> str:
    """Ambil cuplikan AWAL+TENGAH+AKHIR tiap bagian artikel — supaya Jev LIHAT.

    Balik '' kalau penanda bagian TIDAK ketemu (artinya bukan artikel jadi
    ⇒ biar pemanggil pakai cara lama).

    ⚠️ AKAR KE-3 (07 Okt 2026, terukur): cuplikan tetap 1.500 kar/bagian
    membuat bagian BESAR (HASIL DAN PEMBAHASAN 13.503 kar) hanya terkirim
    11% ⇒ paragraf TENGAH — tempat nama peneliti pembanding berada — TIDAK
    IKUT. Akibatnya Jev bilang "pembahasan pembanding 0,21" padahal ADA 9
    nama peneliti (Munawaroh, Vania, Hanaysha, …). Jev SALAH, BAHAN cacat.
    ⇒ Cuplikan sekarang MENYESUAIKAN UKURAN bagian dan mengambil TIGA ujung
      (awal + tengah + akhir) supaya isi tengah ikut terbawa.
    """
    baris = teks.split('\n')
    #  ── ① JALUR JEV (prinsip induk Bos: "Jev selalu terdepan sebelum mesin") ──
    #     Jev yang MENGENALI bentuk naskah; mesin hanya memotong ikut peta Jev.
    #     Terukur 08 Okt 2026: regex mesin (`_cari_bab_skripsi`) SALAH TERUS
    #     pada naskah Asih (daftar isi, blok SISTEMATIKA PENULISAN) — Bos:
    #     "Kenapa tidak pakai jev saja untuk melihat, kenapa mesin menebak?"
    posisi = _posisi_dari_jev(teks)
    if len(posisi) < 2:
        #  ── ② Jalur SKRIPSI (cadangan kalau Jev mati) ──
        posisi = _cari_bab_skripsi(baris)
    if len(posisi) < 3:
        #  ── ③ Jalur ARTIKEL: judul bagian HURUF BESAR ──
        posisi = []
        for i, b in enumerate(baris):
            bersih = b.strip()
            if bersih in _PENANDA_BAGIAN:
                posisi.append((i, bersih))
    if len(posisi) < 3:                           # bukan naskah berpenanda
        return ''

    hasil = []
    for n, (i, nama) in enumerate(posisi):
        akhir = posisi[n + 1][0] if n + 1 < len(posisi) else len(baris)
        isi = '\n'.join(baris[i + 1:akhir]).strip()
        if not isi:
            continue
        hasil.append(f'## {nama}\n{_cuplik_pandai(isi)}')
    return '\n\n'.join(hasil) if hasil else ''


def _cari_bab_skripsi(baris: list) -> list:
    """Cari penanda BAB pada NASKAH SKRIPSI (mis. 'BAB I PENDAHULUAN').

    Balik [(idx_baris, nama)] — penanda yang dipakai `_potong_per_bagian`.
    Penanda yang dicari:
      · 'BAB I' … 'BAB V' (romawi) atau 'BAB 1' … 'BAB 5' (angka)
      · 'DAFTAR PUSTAKA' (biar pustaka ikut — sering tak diawali 'BAB')
    Daftar isi DILEWATI: baris yang memuat '....' (titik-titik pemandu).
    """
    import re
    posisi = []
    sudah = set()          # kunci bab yang sudah diambil (anti penanda palsu)
    #  ⚠️ AKAR (terukur atas Asih): daftar isi BUKAN berbentuk '....' —
    #  bentuknya 'BAB I PENDAHULUAN1' (nomor halaman NEMPEL di ujung, tanpa
    #  titik). Karena itu daftar isi dikenali lewat ANGKA di ujung baris, dan
    #  ditambah pagar: penanda yang muncul SEBELUM 'ABSTRAK' (isi naskah
    #  selalu mulai setelah abstrak/prakata) DILEWATI.
    batas_isi = 0
    for i, b in enumerate(baris):
        if b.strip().upper().startswith('ABSTRAK'):
            if i > 10:                             # bukan di halaman mula-mula
                batas_isi = i
                break
    for i, b in enumerate(baris):
        if i <= batas_isi:
            continue
        bersih = b.strip()
        if not bersih or len(bersih) > 120:
            continue
        if re.search(r'\d\s*$', bersih) and len(bersih) < 60:
            continue                               # baris daftar isi (angka halaman)
        for pola in _POLA_BAB:
            m = re.match(pola, bersih, re.IGNORECASE)
            if not m:
                continue
            #  ⚠️ AKAR KE-5 (terukur atas Asih): blok 'SISTEMATIKA PENULISAN'
            #  memuat SEMUA judul bab BERURUTAN RAPAT (jarak < 20 baris, tiap
            #  bab hanya 1 paragraf 'Bab ini berisi…') ⇒ bab asli TERTUTUPI.
            #  Aturan: kalau penanda baru terlalu dekat (<20 baris) dengan
            #  penanda sebelumnya DAN bab sebelumnya pendek (<1.500 kar),
            #  penanda itu bagian dari rangka ⇒ DIBUANG.
            if posisi:
                jarak = i - posisi[-1][0]
                if jarak < 20:
                    break                      # rangka sistematika → buang
            kunci = m.group(1).upper() if m.lastindex else bersih.upper()
            if kunci in sudah:
                break
            sudah.add(kunci)
            posisi.append((i, bersih[:80]))
            break
        else:
            if bersih.upper().startswith('DAFTAR PUSTAKA'):
                posisi.append((i, 'DAFTAR PUSTAKA'))
    return posisi


#  Jatah cuplikan per bagian — menyesuaikan ukuran bagian (terukur: Jev kuat
#  membaca ±14.000 kar bahan; total di bawah tetap aman).
_CUPLIK_PENUH = 2000        # <= ini: kirim semua
_CUPLIK_AWAL = 1600         # bagian sedang: awal
_CUPLIK_TENGAH = 1400       # bagian sedang: tengah
_CUPLIK_AKHIR = 1000        # bagian sedang: akhir
_CUPLIK_BESAR = 4000        # bagian BESAR (>6000): tambahan jatah
_CUPLIK_BESAR_MIN = 6000    # ambang "bagian besar"


def _cuplik_pandai(isi: str) -> str:
    """Cuplikan 3 ujung: bagian kecil dikirim UTUH, bagian besar dipandai.

    Bagian besar (>6.000 kar) dapat jatah lebih (4.000 kar: awal+tengah+akhir)
    supaya paragraf TENGAH — kerap tempat pembanding/peneliti lain — ikut.
    """
    if len(isi) <= _CUPLIK_PENUH:
        return isi
    besar = len(isi) > _CUPLIK_BESAR_MIN
    awal = _CUPLIK_AWAL + (_CUPLIK_BESAR // 2 if besar else 0)
    tengah = _CUPLIK_TENGAH + (_CUPLIK_BESAR // 4 if besar else 0)
    akhir = _CUPLIK_AKHIR + (_CUPLIK_BESAR // 4 if besar else 0)
    tengah_mulai = max(awal, (len(isi) - tengah) // 2)
    if tengah_mulai + tengah > len(isi) - akhir:      # jangan bertumpuk
        tengah_mulai = max(awal, len(isi) - akhir - tengah)
    return (f'{isi[:awal]}\n\n[...BAGIAN TENGAH...]\n\n'
            f'{isi[tengah_mulai:tengah_mulai + tengah]}\n\n'
            f'[...AKHIR BAGIAN...]\n\n{isi[-akhir:]}')


def periksa_mutu(db, file_id: int, teks: str) -> dict:
    """JEV PERIKSA KEBERADAAN 11 ELEMEN MUTU + 7 BAGIAN WAJIB (MATA, bukan hakim).

    Balik:
      {'ok': bool, 'keputusan': 'bersih'|'kurang'|'ragu'|'mati',
       'ada': {label: nilai}, 'kurang': [label, ...], 'ragu': [label, ...],
       'skor': float, 'alasan': str, 'detik': float, 'model': str}

    🔒 JANGAN jadikan fungsi ini PENGHALANG. Jev hanya LAPOR. Konversi tetap
    jalan walau Jev mati/ragu (pola ai.py:2350 — Jev penjaga LAPORAN).
    """
    mulai = time.time()
    mati = {'ok': False, 'keputusan': 'mati', 'ada': {}, 'kurang': [],
            'ragu': [], 'skor': 0.0, 'alasan': 'Jev tidak menjawab',
            'detik': 0.0, 'model': ''}

    if not teks or not teks.strip():
        return {**mati, 'alasan': 'naskah kosong'}

    #  Bahan: JANGAN pakai `_susun_state()` — itu HANYA peta bab (1905 kar) +
    #  cuplikan 400 kar tiap bab ⇒ ABSTRAK / DAFTAR PUSTAKA / HOOK TIDAK IKUT,
    #  lalu Jev salah bilang "tidak ada abstrak" padahal ADA (terbukti 07 Okt:
    #  naskah Asih punya ABSTRAK tapi Jev bilang 0,10). ⇒ pagar LAMA salah bahan.
    #  ⇒ Untuk mutu, kirim: AWAL naskah (abstrak+hook) + AWAL tiap bab +
    #  AKHIR naskah (kesimpulan+pustaka). Dipotong supaya tetap ringan.
    bahan = _bahan_mutu(teks)
    #  peta tetap diambil untuk pemanggil lain (tidak dipakai Jev di sini)
    peta = {'peta': []}

    tanya = {**ELEMEN_MUTU, **BAGIAN_WAJIB_JEV}
    jawab = satpam.tanya_bebas_mutu(bahan, tanya)
    detik = time.time() - mulai
    if not jawab:
        return {**mati, 'detik': round(detik, 2),
                'alasan': 'Jev tidak menjawab (mati/lewat jaringan/DITOLAK skin)'}

    ada, kurang, ragu = {}, [], []
    for kunci in tanya:
        blok = jawab.get(kunci) or {}
        nilai = blok.get('noul')
        try:
            nilai = float(nilai) if nilai is not None else None
        except (TypeError, ValueError):
            nilai = None
        label = LABEL_ELEMEN.get(kunci, kunci)
        if nilai is None:
            ragu.append(label)
            continue
        ada[label] = round(nilai, 2)
        if nilai < AMBANG_RAGU:
            kurang.append(label)
        elif nilai < AMBANG_ADA:
            ragu.append(label)        # jangan klaim "ada", jangan klaim "tidak"
    #  urutkan sesuai urutan pertanyaan asli (stable)
    urut = {LABEL_ELEMEN.get(k, k): i for i, k in enumerate(tanya)}
    kurang.sort(key=lambda x: urut.get(x, 99))
    ragu.sort(key=lambda x: urut.get(x, 99))

    skor = round(sum(ada.values()) / len(ada), 2) if ada else 0.0
    keputusan = 'bersih' if not kurang else 'kurang'
    if ragu and not kurang:
        keputusan = 'ragu'
    return {'ok': True, 'keputusan': keputusan, 'ada': ada,
            'kurang': kurang, 'ragu': ragu, 'skor': skor,
            'detik': round(detik, 2), 'model': satpam.MODEL,
            'alasan': (f'Jev periksa {len(ada)} poin: {len(kurang)} kurang, '
                       f'{len(ragu)} perlu diperiksa')}


def rangkum_mutu(hasil: dict) -> str:
    """Kalimat LAPORAN ke user — 'Poin ini belum ada: XXX' (bukan vonis).

    🔒 JANGAN pakai kata vonis ('salah'/'buruk'/'tidak layak'). Yang benar:
    memberi tahu apa yang BELUM ADA, lalu USER yang putuskan.
    """
    if not hasil or not hasil.get('ok'):
        return ''
    kurang = hasil.get('kurang') or []
    ragu = hasil.get('ragu') or []
    if not kurang and not ragu:
        return ('Semua poin penting artikel sudah ada. Siap lanjut.')
    bagian = []
    if kurang:
        bagian.append('Poin ini BELUM ADA: ' + ' · '.join(kurang) + '.')
    if ragu:
        bagian.append('Perlu diperiksa (Jev kurang yakin): ' + ' · '.join(ragu) + '.')
    bagian.append('Silakan pilih: lanjut saja, atau lengkapi dulu '
                  '(lengkapi pakai AI memakai Token Revisi).')
    return ' '.join(bagian)


def mata_jev(db, file_id: int, naskah: str) -> dict:
    """JEV SEBAGAI MATA: beri peta bab+sub-bab + keyakinan. USER yang putuskan.

    Beda dengan `peta_bab()` (yang pakai mesin Python `_brief_dan_peta`), fungsi
    ini MENANYAKAN langsung ke Jev supaya kita punya MATA KEDUA — kalau mesin dan
    Jev BEDA PENDAPAT, itulah sinyal untuk bertanya ke user (pola Jev = pemeriksa
    yang LAPOR, user pemutus).

    SELALU mengembalikan dict. TIDAK PERNAH melempar galat (pola satpam P1/P2).
    Bentuk:
        {'ok': bool, 'keputusan': 'setuju'|'beda'|'ragu'|'mati',
         'bab_jev': [...], 'jumlah_jev': int|None, 'jumlah_mesin': int,
         'bagian_wajib': [...], 'subbab': {...},
         'confidence': float, 'alasan': str}

    Ambang: keyakinan >= AMBANG_JEK → 'setuju'; 0,5–AMBANG → 'beda' (mesin &
    Jev tak sepakat, user perlu lihat); < 0,5 → 'ragu'. Kalau Jev mati →
    'mati' dan konversi TETAP JALAN memakai peta mesin (Jev tak boleh jadi
    penghalang — pola yang sudah dipakai di ai.py:2350).
    """
    mati = {'ok': False, 'keputusan': 'mati', 'bab_jev': [], 'jumlah_jev': None,
            'jumlah_mesin': 0, 'bagian_wajib': [], 'subbab': {},
            'confidence': 0.0, 'alasan': 'Jev tidak aktif'}
    try:
        from . import satpam
    except Exception as e:                                    # noqa: BLE001
        return {**mati, 'alasan': f'satpam tak bisa dimuat: {e}'}

    if not getattr(satpam, 'AKTIF', False) or not naskah:
        return mati

    #  Peta mesin dulu — jadi pembanding + bahan untuk Jev.
    mesin = peta_bab(db, file_id, naskah)
    peta_mesin = mesin.get('peta') or []
    mati['jumlah_mesin'] = len(peta_mesin)

    try:
        jawab = satpam.tanya_bebas(naskah, peta_mesin, PERTANYAAN_PETA)
    except Exception as e:                                    # noqa: BLE001
        #  Jev pakai satpam.tanya_bebas kalau ADA; kalau belum, jangan gagal.
        return {**mati, 'alasan': f'Jev tak bisa ditanya: {type(e).__name__}'}
    if not jawab:
        return {**mati, 'alasan': 'Jev tidak menjawab'}

    #  baca jawaban — bentuk Jev: choice → {'choice': '2', 'probabilities': ...,
    #  'confidence': .95}; noul → {'noul': 0.91}. TIDAK ADA 'text'/'daftar_bab'!
    #  ⚠️ Terukur 07Okt26: Wulan pertama kali baca .get('text') → selalu kosong.
    bb = jawab.get('jumlah_bab') or {}
    jml = bb.get('choice')
    try:
        jml = int(jml) if jml is not None and str(jml).isdigit() else None
    except (TypeError, ValueError):
        jml = None
    conf = float(bb.get('confidence') or 0)

    romawi = (jawab.get('semua_romawi_sah') or {}).get('noul')
    urut = (jawab.get('berurutan') or {}).get('noul')

    #  BANDINGKAN dengan mesin → keputusan LAPOR (bukan putus sendiri)
    jumlah_mesin = len(peta_mesin)
    if conf >= satpam.AMBANG_LOLOS:
        keputusan = 'setuju' if (jml is None or jml == jumlah_mesin) else 'beda'
    elif conf >= satpam.AMBANG_TANYA:
        keputusan = 'beda'
    else:
        keputusan = 'ragu'

    alasan = (f'Jev hitung {jml} bab, mesin {jumlah_mesin} bab '
              f'(keyakinan {conf:.2f}) → {keputusan}')
    return {'ok': True, 'keputusan': keputusan, 'bab_jev': [],
            'jumlah_jev': jml, 'jumlah_mesin': jumlah_mesin,
            'bagian_wajib': [], 'subbab': {},
            'romawi_sah': romawi, 'berurutan': urut,
            'confidence': conf, 'alasan': alasan}


def rangkum_mata(mata: dict) -> str:
    """Ubah keluaran `mata_jev()` jadi 1 baris untuk DITAMPILKAN ke user.

    Jev = PEMERIKSA yang LAPOR; USER yang memutuskan. Jadi kalimatnya harus
    netral + menyebut ANGKA, bukan vonis 'benar/salah'.
    """
    if not mata or not mata.get('ok'):
        return ''
    k = mata.get('keputusan')
    n_j = mata.get('jumlah_jev')
    n_m = mata.get('jumlah_mesin')
    if k == 'setuju':
        return f'Jev memeriksa struktur: {n_j} bab — sama dengan hitungan mesin.'
    if k == 'beda':
        return (f'Jev melihat {n_j} bab, mesin menemukan {n_m} bab. '
                f'Silas periksa keduanya, lalu pilih yang sesuai naskahmu.')
    return (f'Jev kurang yakin soal jumlah bab (keyakinan '
            f'{float(mata.get("confidence") or 0):.2f}). Manusia yang putuskan.')



# ══════════════════════════════════════════════════════════════════════════
# PROMPT — susun pesan untuk AI
# ══════════════════════════════════════════════════════════════════════════
def muat_prompt() -> str:
    """Baca prompt artikel jurnal (single source of truth di prompts/)."""
    try:
        return PROMPT_ARTIKEL.read_text(encoding='utf-8')
    except Exception as e:                                    # noqa: BLE001
        log.error('[konversi] prompt tidak terbaca: %s', e)
        return ''


def _bersihkan_komentar_header(teks: str) -> str:
    """Buang baris komentar '#' di kepala berkas prompt (pola ai.py:368)."""
    baris = []
    for b in (teks or '').splitlines():
        if b.startswith('#') and not baris:
            continue
        baris.append(b)
    return '\n'.join(baris).strip()


def susun_pesan(naskah: str, jenis: str, identitas: dict, peta: dict,
                template: str = 'JPEM') -> str:
    """Susun pesan user untuk AI: identitas + peta bab + naskah (dipotong cerdas).

    ⚠️ Naskah panjang WAJIB dipotong cerdas, jangan asal potong: ambil kepala
    + ekor + bagian tengah per bab (pola ai.potong_cerdas).
    """
    template = (template or 'JPEM').upper()
    bagian = []
    bagian.append(f'[JENIS PENELITIAN] {LABEL_JENIS.get(jenis, jenis)}')
    bagian.append(f'[TEMPLATE JURNAL ACUAN] {template}')
    bagian.append(
        '[IDENTITAS PENULIS — DIAMBIL DARI NASKAH, JANGAN DIUBAH]' +
        f"\nNama : {identitas.get('nama') or '(tidak ada)'}" +
        f"\nEmail: {identitas.get('email') or '(tidak ada)'}")

    kerangka = (peta or {}).get('kerangka') or []
    if kerangka:
        baris = [f"  {k['no']}. {k['judul']} ({k['panjang']} kar)" for k in kerangka]
        bagian.append('[PETA NASKAH — urutan bagian yang ditemukan]\n' + '\n'.join(baris))

    brief = (peta or {}).get('brief') or {}
    if brief:
        try:
            ringkas = json.dumps(brief, ensure_ascii=False)[:2000]
            bagian.append(f'[BRIEF NASKAH]\n{ringkas}')
        except (TypeError, ValueError):
            pass

    naskah_kirim = naskah
    try:
        from .ai import potong_cerdas
        #  ⚠️ potong_cerdas() mengembalikan LIST bagian (bukan string) — ini
        #  untuk jaga-jaga naskah sangat panjang. Untuk konversi, bila terpecah,
        #  kita tetap kirim UTUH bila masih ≤ batas; kalau lebih, ambil bagian
        #  pertama + TERAKHIR (pembuka & kesimpulan = paling menentukan artikel).
        #  ⚠️ JEBAKAN 07Okt26: variabel ini JANGAN dinamai `bagian` — bentrok
        #  dengan daftar `bagian` pesan di atas → seluruh pesan ikut rusak.
        pecahan = potong_cerdas(naskah, NASKAH_MAKS_KONVERSI)
        if isinstance(pecahan, list) and pecahan:
            if len(pecahan) <= 1:
                naskah_kirim = pecahan[0]
            else:
                naskah_kirim = (pecahan[0] + '\n\n[...bagian tengah diringkas...]\n\n'
                                + pecahan[-1])
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konversi] potong_cerdas gagal, kirim apa adanya: %s', e)

    bagian.append('[NASKAH LENGKAP]\n' + (naskah_kirim or ''))
    bagian.append(
        'Susun ulang naskah di atas menjadi SATU artikel jurnal utuh sesuai '
        'aturan sistem. Balas HANYA JSON sah sesuai format keluaran.')
    return '\n\n'.join(bagian)


# ══════════════════════════════════════════════════════════════════════════
# PEMERIKSA HASIL — 2 lapis (mesin gratis + Jev 11 elemen)
# ══════════════════════════════════════════════════════════════════════════
def periksa_hasil(artikel: dict) -> dict:
    """LAPIS 1 — mesin, GRATIS: cek bagian wajib + keberadaan 11 elemen.

    Tidak memanggil AI. Yang dinilai: ADA/TIDAK ADA, bukan MUTU.
    """
    a = artikel or {}
    kurang_bagian = []
    for b in BAGIAN_WAJIB:
        isi = str(a.get(b) or '').strip()
        if len(isi) < 120:          # terlalu pendek = praktis kosong
            kurang_bagian.append(b)

    elemen = a.get('elemen') or {}
    elemen_hilang = []
    elemen_ada = []
    for kunci, label, _tempat in ELEMEN_11:
        nilai = elemen.get(kunci)
        if nilai and str(nilai).strip():
            elemen_ada.append({'kunci': kunci, 'label': label,
                               'kutipan': str(nilai)[:200]})
        else:
            elemen_hilang.append({'kunci': kunci, 'label': label})

    ident_ok = bool((a.get('penulis') or [{}])[0].get('nama'))
    abstrak_ok = len(str(a.get('abstrak_id') or '')) >= 300
    en_ok = len(str(a.get('abstract_en') or '')) >= 300

    temuan = []
    if kurang_bagian:
        temuan.append('Bagian belum terisi: ' + ', '.join(kurang_bagian))
    if elemen_hilang:
        temuan.append('Elemen mutu belum terlihat: ' +
                      ', '.join(e['label'] for e in elemen_hilang))
    if not abstrak_ok:
        temuan.append('Abstrak (ID) terlalu pendek / kosong')
    if not en_ok:
        temuan.append('Abstract (EN) terlalu pendek / kosong')
    if not ident_ok:
        temuan.append('Nama penulis tidak terbaca di hasil')

    return {
        'lolos': not temuan,
        'kurang_bagian': kurang_bagian,
        'elemen_ada': elemen_ada,
        'elemen_hilang': elemen_hilang,
        'jumlah_elemen': len(elemen_ada),
        'temuan': temuan,
    }


#  ── LAPIS 2 — JEV (MATA): periksa 18 poin MUTU pada ARTIKEL HASIL ──
def periksa_hasil_jev(db, file_id: int, artikel: dict) -> dict:
    """JEV PERIKSA HASIL konversi — MATA, bukan hakim (prinsip induk §④).

    Beda dari `periksa_mutu` (yang memeriksa NASKAH sebelum konversi):
    di sini yang diperiksa**ARTIKEL JADI** — apakah 18 poin mutu
    (11 elemen JEMT + 7 bagian IMBAD) BENAR-BENAR ADA di hasilnya.

    🔒 JANGAN jadikan penghalang. Gagal/mati → artikel TETAP diserahkan,
    hanya tanpa laporan Jev (pola ai.py:2350).
    """
    a = artikel or {}
    if not a:
        return {'ok': False, 'keputusan': 'mati', 'ada': {}, 'kurang': [],
                'ragu': [], 'skor': 0.0, 'alasan': 'artikel kosong',
                'detik': 0.0, 'model': '', 'pesan': ''}
    try:
        teks = artikel_ke_teks(a)
    except Exception as e:                                    # noqa: BLE001
        return {'ok': False, 'keputusan': 'mati', 'ada': {}, 'kurang': [],
                'ragu': [], 'skor': 0.0, 'alasan': f'rakit teks gagal: {e}',
                'detik': 0.0, 'model': '', 'pesan': ''}

    mutu = periksa_mutu(db, file_id, teks)
    mutu['pesan'] = rangkum_mutu(mutu)
    return mutu


# ══════════════════════════════════════════════════════════════════════════
# URUTAN LENGKAP — dipanggil dari rute
# ══════════════════════════════════════════════════════════════════════════
def periksa_sebelum_konversi(db, u, fid: int, naskah: str,
                             nama_berkas: str = '', jalur_berkas=None) -> dict:
    """PAGAR ① ② ③ — SEBELUM kuota dipotong (user tidak dirugikan).

    Mengembalikan dict:
      {'boleh': bool, 'henti': bool, 'pesan': str, 'identitas': {...},
       'kelengkapan': {...}, 'jenis': {...}}
    `henti=True` = MESIN TIDAK JALAN (pagar ② gagal) — putusan Bos §N no.5.
    """
    keluar = {'boleh': False, 'henti': False, 'pesan': '',
              'identitas': {}, 'kelengkapan': {}, 'jenis': {}, 'kerangka': []}

    #  ① berkas aman (kalau dari upload)
    if jalur_berkas is not None:
        aman, pesan = periksa_berkas_aman(nama_berkas, Path(jalur_berkas))
        if not aman:
            keluar.update(boleh=False, henti=True, pesan=pesan)
            return keluar

    #  ② nama + email  → BLOKIR
    ident = cari_identitas(naskah)
    keluar['identitas'] = ident
    kurang = lengkapi_identitas(ident)
    if kurang:
        keluar.update(
            boleh=False, henti=True,
            pesan=('Naskah ini belum memuat ' + ' dan '.join(kurang) +
                   '. Lengkapi dulu di naskah (di bagian judul/cover), '
                   'lalu jalankan konversi lagi. Konversi tidak dijalankan '
                   'sebelum ini lengkap.'))
        return keluar

    #  ③ kelengkapan bagian — memberi tahu, TIDAK memblokir
    #  ⚠️ TEKS naskah WAJIB ikut dikirim: daftar peta bisa tidak lengkap
    #  (skripsi ASLI: peta hanya memuat sub-bab BAB II) → tanpa teks, bahan
    #  dituduh "KURANG" padahal ada. Lihat catatan di cek_kelengkapan().
    peta = peta_bab(db, fid, naskah)
    keluar['kelengkapan'] = cek_kelengkapan(
        {'teks': naskah, **(peta.get('brief') or {})}, peta.get('peta'))
    #  ⚠️ 07 Okt 2026 — `kerangka` IKUT dibalikkan: pemanggil (rute POST)
    #     butuh untuk `susun_pesan()`. Dulu tidak disimpan → pemanggil harus
    #     memanggil `peta_bab()` ULANG (2× kerja PETA untuk 1 konversi).
    #     Menyimpan di sini = NOL hitungan baru, satu kali saja.
    keluar['kerangka'] = peta.get('kerangka') or []

    #  jenis (otomatis, bisa ditimpa user)
    keluar['jenis'] = deteksi_jenis(naskah, peta.get('brief'))

    #  ③b BENTUK NASKAH — DIBUANG 09 Okt 2026 (keputusan Bos).
    #  ⚠️ Pemanggil `bentuk_naskah(...)` di sini adalah SISA RENCANA 08 Okt yang
    #  TERPUTUS: fungsinya TIDAK PERNAH DIBUAT (dicek 3 backup: 1.247/1.915/2.205
    #  baris — nol hasil). Rencana lamanya (Jev kenali bentuk/jenis/desain dulu,
    #  lihat CATATAN_DISKUSI_BAB4_KONVERSI_08OKT2026.md §4.4) SUDAH TERGANTIKAN
    #  arah baru: peta3_jev (putusan Bos: "TUAS BERIKUTNYA = BERSIHKAN INPUT").
    #  ⇒ 1 baris mati ini dibuang; `bentuk`/`pesan_bentuk` tidak diisi lagi.
    keluar['bentuk'] = None
    keluar['pesan_bentuk'] = ''

    #  ④ JEV = MATA (putusan Bos 07 Okt 2026): peta bab+sub-bab + keyakinan.
    #     ⚠️ Jev TIDAK memblokir. Kalau Jev mati/ragu → konversi TETAP JALAN
    #     memakai peta mesin (pola ai.py:2350). Jev hanya LAPOR; USER memutuskan.
    #     Aman dipanggil di sini karena posisinya SETELAH pagar ①②③ (jadi
    #     naskah sudah pasti punya identitas & berkas aman).
    try:
        keluar['mata'] = mata_jev(db, fid, naskah)
        keluar['mata_pesan'] = rangkum_mata(keluar['mata'])
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konversi] mata_jev gagal (fid=%s): %s', fid, e)
        keluar['mata'] = {'ok': False, 'keputusan': 'mati',
                          'alasan': f'galat: {e}'}
        keluar['mata_pesan'] = ''

    #  ⑤ JEV = PERIKSA MUTU (optimasi 07 Okt — putusan Bos: "user bayar mahal,
    #     masa kita tidak kasih yang berbayar juga"). Periksa KEBERADAAN 11
    #     elemen mutu + 7 bagian wajib. 🔒 LAPOR saja, TIDAK memblokir —
    #     ini PINTU JUALAN (kurang → user boleh lengkapi pakai Token Revisi).
    try:
        keluar['mutu'] = periksa_mutu(db, fid, naskah)
        keluar['mutu_pesan'] = rangkum_mutu(keluar['mutu'])
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konversi] periksa_mutu gagal (fid=%s): %s', fid, e)
        keluar['mutu'] = {'ok': False, 'keputusan': 'mati', 'kurang': [],
                          'ragu': [], 'alasan': f'galat: {e}'}
        keluar['mutu_pesan'] = ''

    #  ⑤b TIKET LOLOS — LAPIS 3 (putusan Bos 16 Okt 2026).
    #     "User sudah bayar & dapat kebutuhannya di bab itu, lalu edit manual
    #      / menambah kalimat yang TIDAK merubah makna — lolos atau tidak?"
    #      ⇒ LOLOS. Yang dinilai MAKNA (Jev 1 pertanyaan choice), bukan huruf.
    #     Elemen yang PUNYA TIKET & maknanya tetap ⇒ DIBUANG dari `kurang`
    #     (tidak ditanyakan lagi = sudah "Done"). Jev mati ⇒ tiket BATAL
    #     (kegagalan teknis TIDAK boleh jadi pintu gratis).
    #     ⚠️ GRATIS (putusan Bos: biaya Jev ditanggung EduAi) — tidak memotong
    #        token user; hanya verifikasi.
    try:
        from . import tiket_lolos as _tiket
        hasil_tiket = _tiket.tiket_periksa(
            db, u, fid,
            (keluar.get('mutu') or {}).get('kurang') or [],
            lambda kunci: _teks_bab_untuk(kunci, naskah, peta),
        )
        keluar['tiket'] = hasil_tiket
        if hasil_tiket.get('lolos'):
            #  Elemen bertiket yang masih lolos → buang dari daftar kurang
            #  supaya layar TIDAK menanyakannya lagi (sudah lunas).
            mutu2 = dict(keluar.get('mutu') or {})
            mutu2['kurang'] = hasil_tiket.get('kurang') or []
            keluar['mutu'] = mutu2
            kurang_lagi = mutu2['kurang']
            if not kurang_lagi and (mutu2.get('ragu') or []):
                mutu2['ragu'] = []
            keluar['mutu_pesan'] = rangkum_mutu(mutu2)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[tiket] periksa tiket gagal (fid=%s): %s', fid, e)
        keluar['tiket'] = {'kurang': [], 'lolos': [], 'batal': [],
                           'diperiksa': 0}

    keluar.update(boleh=True, henti=False, pesan='Siap dikonversi.')
    return keluar


def _teks_bab_untuk(kunci: str, naskah: str, peta: dict,
                    maks: int = 1500) -> str:
    """Teks BAB tempat `kunci` (elemen) tinggal — untuk sidik tiket.

    NOL mesin baru: memakai `kerangka` dari `peta_bab()` yang SUDAH dihitung
    pemanggil (`periksa_sebelum_konversi`). Kalau bab tidak bisa ditemukan,
    kembalikan AWAL naskah (masih berguna untuk membandingkan makna).
    """
    teks = (naskah or '').strip()
    if not teks:
        return ''

    #  wilayah elemen dari ELEMEN_11, mis. 'Pendahuluan ¶4'
    wilayah = ''
    for baris in ELEMEN_11:
        if baris and baris[0] == kunci:
            wilayah = str(baris[2] if len(baris) > 2 else '')
            break

    #  Cari bab yang cocok di kerangka peta (judul bab mengandung wilayah).
    kerangka = (peta or {}).get('kerangka') or []
    kata = _kata_kunci_bab(wilayah)
    awal, akhir = 0, 0
    for b in kerangka:
        judul = str((b or {}).get('judul') or '')
        pos = (b or {}).get('mulai')
        if kata and judul and kata.lower() in judul.lower():
            awal = int(pos or 0)
            break
    if awal:
        akhir = min(len(teks), awal + maks)
        potong = teks[awal:akhir].strip()
        if potong:
            return potong
    #  Cadangan: awal naskah (selalu ada, tetap bisa dibandingkan)
    return teks[:maks].strip()


def _kata_kunci_bab(wilayah: str) -> str:
    """'Pendahuluan ¶4' → 'pendahuluan' (kata kunci pencari judul bab)."""
    w = (wilayah or '').split('¶')[0].strip().lower()
    return w


# ══════════════════════════════════════════════════════════════════════════
# TAHAP 3 — PENYIMPANAN HASIL (anti tekan-back) & PENGEMBALIAN TOKEN
# ══════════════════════════════════════════════════════════════════════════
def artikel_ke_teks(artikel: dict) -> str:
    """Rakit artikel (dict) menjadi teks siap simpan/tampil.

    Dipakai untuk: (a) menulis berkas hasil, (b) menyusun prompt revisi.
    """
    a = artikel or {}
    #  Daftar Pustaka bisa list atau string — satukan.
    pustaka = a.get('daftar_pustaka') or []
    if isinstance(pustaka, list):
        pustaka_txt = '\n'.join(f'{i+1}. {p}' for i, p in enumerate(pustaka))
    else:
        pustaka_txt = str(pustaka)

    bagian = [
        str(a.get('judul') or '').strip(),
        '',
    ]
    penulis = a.get('penulis') or []
    for p in penulis:
        if isinstance(p, dict):
            baris = p.get('nama') or ''
            if p.get('email'):
                baris += f" <{p['email']}>"
            if p.get('afiliasi'):
                baris += f" — {p['afiliasi']}"
            if baris.strip():
                bagian.append(baris.strip())
    bagian += [
        '',
        'ABSTRAK', str(a.get('abstrak_id') or '').strip(),
        'Kata kunci: ' + ', '.join(a.get('kata_kunci') or []) if a.get('kata_kunci') else '',
        '',
        'ABSTRACT', str(a.get('abstract_en') or '').strip(),
        'Keywords: ' + ', '.join(a.get('keywords') or []) if a.get('keywords') else '',
        '',
        'PENDAHULUAN', str(a.get('pendahuluan') or '').strip(),
        '',
        'METODE', str(a.get('metode') or '').strip(),
        '',
        'HASIL DAN PEMBAHASAN', str(a.get('hasil_pembahasan') or '').strip(),
        '',
        'KESIMPULAN', str(a.get('kesimpulan') or '').strip(),
        '',
        'DAFTAR PUSTAKA', pustaka_txt,
    ]
    lampiran = a.get('lampiran') or []
    if lampiran:
        bagian += ['', 'LAMPIRAN', '\n'.join(str(x) for x in lampiran)]
    return '\n'.join(bagian).strip()


def simpan_hasil(db, u, fid: int, artikel: dict, jenis: str = '',
                 token_dipotong: int = 0) -> dict:
    """TAHAP 3 — simpan hasil konversi: baris pelacak + BERKAS di workspace.

    KENAPA berkas disimpan OTOMATIS (bukan menunggu tombol unduh):
    putusan Bos 07 Okt — kalau user menekan back / HP mati / tab ketutup,
    hasil HARUS tetap ada. Ini lapis anti-rugi ke-1 (SOT §C.8).

    Rute yang membuat berkasnya ada di main.py; di sini kita hanya menandai
    baris konversi SELESAI + rakit teksnya. Rute memakai `artikel_ke_teks()`.
    """
    from . import kuota
    ok = kuota.selesaikan_konversi(db, int(getattr(u, 'id', 0)), int(fid),
                                   hasil=artikel, jenis=jenis,
                                   token_dipotong=token_dipotong)
    return {'tersimpan': bool(ok), 'teks': artikel_ke_teks(artikel)}


def gagalkan(db, u, fid: int, galat: str) -> dict:
    """TAHAP 3 — AI gagal TEKNIS → tandai gagal + KEMBALIKAN jatah konversi.

    Aturan Bos: user TIDAK boleh dirugikan oleh kegagalan teknis (SOT §C.8).
    """
    from . import kuota
    ok = kuota.kembalikan_konversi(db, int(getattr(u, 'id', 0)), int(fid),
                                   galat=galat)
    return {'dikembalikan': bool(ok), 'galat': galat}


# ══════════════════════════════════════════════════════════════════════════
# TAHAP 4 — REVISI PER-ITEM (2 token per revisi — SOT §N no.9)
# ══════════════════════════════════════════════════════════════════════════
def daftar_revisi(artikel: dict, tiket: dict | None = None) -> list:
    """Daftar item yang BOLEH direvisi pada artikel ini (untuk ditampilkan).

    Yang muncul = bagian + elemen mutu yang ADA isinya.
    Harga: BAGIAN = TOKEN_PER_REVISI (seragam 2); ELEMEN MUTU = BERTINGKAT
    2/3/5 sesuai beban kerja AI (putusan Bos 15 Okt 2026 — `TOKEN_ELEMEN`).

    `tiket` = hasil `tiket_lolos.tiket_baca()` — elemen yang PUNYA TIKET
    ditandai `done=True` (putusan Bos 16 Okt 2026: tetap MUNCUL di daftar
    dengan tanda ☑ Done, supaya user tahu sudah lunas).
    """
    a = artikel or {}
    tt = tiket or {}
    keluar = []
    for kunci, label in BAGIAN_REVISI:
        isi = a.get(kunci)
        ada = bool(isi) and (len(isi) > 0 if isinstance(isi, str) else bool(isi))
        keluar.append({'kunci': kunci, 'label': label, 'ada': ada,
                       'token': TOKEN_PER_REVISI, 'tingkat': '', 'done': False})
    elemen = a.get('elemen') or {}
    for kunci, label in ELEMEN_REVISI:
        isi = elemen.get(kunci)
        #  ⚠️ Label TANPA penanda teknis "[Elemen]" — layar punya kolom sendiri
        #     untuk memisahkan bagian artikel vs elemen mutu.
        keluar.append({'kunci': f'elemen:{kunci}', 'label': label,
                       'ada': bool(isi), 'token': token_elemen(kunci),
                       'tingkat': tingkat_elemen(kunci),
                       'done': bool(tt.get(kunci))})
    return keluar


def hitung_biaya_revisi(daftar_pilihan) -> dict:
    """Hitung token untuk sekumpulan item revisi (putusan Bos §N no.9).

    Dihitung PER ITEM — bukan sekali. Contoh Bos: revisi Abstrak + Novelty
    = 2 item = 2 + 3 = 5 token (dulu seragam 2+2=4, kini mengikuti beban).

    ⚠️ Menerima dua bentuk pilihan:
      (a) daftar teks kunci  → ['abstrak_id', 'elemen:novelty']
      (b) daftar dict item   → [{'kunci': ..., 'token': ...}, …]
    Bentuk (b) dipakai saat layar sudah punya daftar bertoken; bentuk (a)
    dipakai pemanggil lama (rute) yang hanya mengirim kunci.
    """
    pilihan = [p for p in (daftar_pilihan or []) if p]
    total = 0
    kunci_keluar = []
    for p in pilihan:
        if isinstance(p, dict):
            k = str(p.get('kunci') or '')
            t = p.get('token')
            t = int(t) if t is not None else _token_kunci(k)
        else:
            k = str(p)
            t = _token_kunci(k)
        total += t
        kunci_keluar.append(k)
    jumlah = len(pilihan)
    return {'jumlah': jumlah, 'token': total,
            'per_item': TOKEN_PER_REVISI,          # bagian (harga seragam)
            'pilihan': kunci_keluar}


def _token_kunci(kunci: str) -> int:
    """Harga satu item revisi dari KUNCI-nya (tanpa daftar item).

    'elemen:gap' → 3 (bertingkat) · 'abstrak_id' → TOKEN_PER_REVISI.
    """
    k = str(kunci or '')
    if k.startswith('elemen:'):
        return token_elemen(k.split(':', 1)[1])
    return TOKEN_PER_REVISI


def susun_pesan_revisi(artikel: dict, pilihan, catatan_pengguna: str = '') -> str:
    """Susun pesan untuk AI: revisi HANYA item yang dipilih.

    ⚠️ Aturan: AI TIDAK boleh menyentuh item di luar pilihan (biar adil —
    user bayar 2 token per item, bukan untuk rombak seluruh artikel).
    """
    pilihan = [p for p in (pilihan or []) if p]
    bagian_pilih = []
    for p in pilihan:
        if str(p).startswith('elemen:'):
            kunci = str(p).split(':', 1)[1]
            nilai = (artikel.get('elemen') or {}).get(kunci) or ''
            bagian_pilih.append(f'  · ELEMEN {kunci}: {str(nilai)[:400]}')
        else:
            nilai = artikel.get(p) or ''
            if isinstance(nilai, list):
                nilai = ' | '.join(str(x) for x in nilai)
            bagian_pilih.append(f'  · BAGIAN {p}: {str(nilai)[:1200]}')

    pesan = [
        'Ini artikel jurnal hasil konversi. Lakukan PERBAIKAN HANYA pada item '
        'yang diminta di bawah. JANGAN mengubah item lain.',
        '',
        '[ARTIKEL SEKARANG]',
        artikel_ke_teks(artikel)[:40000],
        '',
        '[ITEM YANG HARUS DIPERBAIKI]',
        '\n'.join(bagian_pilih),
    ]
    if catatan_pengguna:
        pesan += ['', f'[CATATAN PENULIS] {catatan_pengguna[:1000]}']
    pesan += [
        '',
        'Balas HANYA JSON sah berisi kunci item yang direvisi saja. '
        'Contoh: {"abstrak_id": "...", "elemen": {"novelty": "..."}}',
        'Jangan menambah data/angka/pustaka yang tidak ada di artikel.',
    ]
    return '\n'.join(pesan)


def terapkan_revisi(artikel: dict, jawaban: dict) -> dict:
    """Gabungkan hasil revisi ke artikel — HANYA kunci yang dikirim AI balik."""
    barang = dict(artikel or {})
    j = jawaban or {}
    for k, v in j.items():
        if k == 'elemen' and isinstance(v, dict):
            el = dict(barang.get('elemen') or {})
            el.update(v)
            barang['elemen'] = el
        elif k in dict(BAGIAN_REVISI) and v:
            barang[k] = v
        elif k in dict(ELEMEN_REVISI) and v:
            el = dict(barang.get('elemen') or {})
            el[k] = v
            barang['elemen'] = el
    return barang


# ══════════════════════════════════════════════════════════════════════════
# TAHAP 4b — JALANKAN REVISI (2 token/item — SOT §N no.9) — 08 Okt 2026
# ══════════════════════════════════════════════════════════════════════════
#  KENAPA DI SINI: `daftar_revisi()`, `hitung_biaya_revisi()`,
#  `susun_pesan_revisi()`, `terapkan_revisi()` SUDAH ADA sejak Tahap 4 —
#  yang belum cuma PEMANGGIL AI + POTONG TOKEN-nya. NOL mesin baru:
#    · biaya  : `kuota.potong_banyak()` (SATU dompet, sudah dipakai jalur AI)
#    · AI     : `ai._panggil_router()` (satu pintu 9router, pola sama
#               dengan `jalankan_konversi()` di atas — JANGAN bikin jalur baru)
#    · riwayat: ditulis ke `KonversiNaskah.hasil_json` yang SUDAH ADA
#               (TIDAK ada tabel baru, TIDAK ada dompet baru)
#  URUTAN PAGAR (konsisten dengan jalankan_konversi_artikel):
#    ① hitung biaya dari item yang dipilih → ② potong token (tolak bila kurang)
#    → ③ panggil AI → ④ terapkan → ⑤ simpan riwayat
#    Gagal TEKNIS ⇒ token DIKEMBALIKAN (user tidak dirugikan).

def biaya_revisi_valid(pilihan, saldo: int) -> dict:
    """Periksa pilihan revisi SEBELUM memotong token.

    Balik {'ok', 'pesan', 'token', 'jumlah', 'pilihan'} — pagar di SERVER,
    bukan tampilan (pola sama dengan pagar konversi).
    """
    sah = {k for k, _ in BAGIAN_REVISI} | {f'elemen:{k}' for k, _ in ELEMEN_REVISI}
    bersih, ditolak = [], []
    for p in (pilihan or []):
        s = str(p or '').strip()
        if not s:
            continue
        if s in sah:
            bersih.append(s)
        else:
            ditolak.append(s)
    if not bersih:
        return {'ok': False, 'token': 0, 'jumlah': 0, 'pilihan': [],
                'pesan': 'Belum ada bagian yang dipilih untuk diperbaiki.'}
    hitung = hitung_biaya_revisi(bersih)
    if hitung['token'] > int(saldo or 0):
        return {'ok': False, 'token': hitung['token'], 'jumlah': hitung['jumlah'],
                'pilihan': bersih, 'kurang': hitung['token'] - int(saldo or 0),
                'pesan': (f'Perlu {hitung["token"]} Token Revisi '
                          f'({hitung["jumlah"]} bagian), '
                          f'sedangkan saldomu kurang.')}
    keluar = {'ok': True, 'token': hitung['token'], 'jumlah': hitung['jumlah'],
              'pilihan': bersih,
              'pesan': (f'{hitung["jumlah"]} bagian = {hitung["token"]} Token '
                        f'Revisi.')}
    if ditolak:
        keluar['ditolak'] = ditolak
    return keluar


async def jalankan_revisi(db, u, fid: int, artikel: dict, pilihan,
                          catatan_pengguna: str = '') -> dict:
    """PANGGIL AI untuk merevisi item terpilih. TIDAK menyentuh kuota.

    Return {'ok', 'artikel', 'model', 'token_in', 'token_out', 'galat'}.
    Kuota dipotong & dikembalikan oleh PEMANGGIL (rute), seperti konversi.

    ⚠️ Aturan adil (SOT §N no.9): AI HANYA menyentuh item yang dipilih —
    user bayar 2 token per item, bukan untuk rombak seluruh artikel.
    """
    from . import ai as ai_mod
    keluar = {'ok': False, 'artikel': {}, 'model': '',
              'token_in': 0, 'token_out': 0, 'galat': ''}

    pesan = susun_pesan_revisi(artikel, pilihan, catatan_pengguna)
    sistem = _bersihkan_komentar_header(muat_prompt())
    if not sistem:
        keluar['galat'] = 'Prompt artikel jurnal tidak terbaca di server.'
        return keluar

    #  ⚠️ `_panggil_router` (BUKAN `_revisi_dengan_failover`) — alasan SAMA
    #  dengan jalankan_konversi(): jalur revisi lama menuntut baris [PROFIL]
    #  + blok komentar revisi, sedangkan di sini balasan harus JSON artikel.
    try:
        konten, info = await ai_mod._panggil_router(
            pesan, ai_mod.AI_TIMEOUT_DETIK, system=sistem)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konversi] panggil AI revisi gagal (fid=%s): %s', fid, e)
        keluar['galat'] = f'{type(e).__name__}: {e}'
        return keluar

    nama_model = str((info or {}).get('model') or '').strip() or 'EduAi'
    data = _urai_artikel(konten)
    if not data:
        keluar['galat'] = ('Balasan AI tidak bisa dibaca sebagai artikel. '
                           'Coba jalankan revisi lagi.')
        keluar['model'] = nama_model
        return keluar

    keluar.update(
        ok=True, artikel=terapkan_revisi(artikel, data), model=nama_model,
        token_in=int((info or {}).get('token_in') or 0),
        token_out=int((info or {}).get('token_out') or 0))
    return keluar


def catat_revisi(db, u, fid: int, artikel: dict, pilihan, token: int,
                 model: str = '') -> dict:
    """Simpan riwayat revisi ke `KonversiNaskah` yang SUDAH ADA + tulis berkas.

    TIDAK ada tabel baru: riwayat ditulis ke `hasil_json` (kunci 'revisi').
    TIDAK ada dompet baru: token sudah dipotong `kuota.potong_banyak()`.
    """
    import json as _json
    from .models import KonversiNaskah, _now
    from sqlalchemy import select as _select

    uid = int(getattr(u, 'id', 0))
    baris = db.execute(
        _select(KonversiNaskah).where(
            KonversiNaskah.user_id == uid,
            KonversiNaskah.file_id == int(fid),
            KonversiNaskah.status == 'beres',
        ).order_by(KonversiNaskah.id.desc())
    ).scalars().first()
    if baris is None:
        return {'tersimpan': False, 'pesan': 'Baris konversi tidak ditemukan.'}

    try:
        wadah = _json.loads(baris.hasil_json or '{}')
    except Exception:                                         # noqa: BLE001
        wadah = {}
    riwayat = list(wadah.get('revisi') or [])
    riwayat.append({
        'pilihan': list(pilihan or []),
        'token': int(token or 0),
        'model': str(model or ''),
        'waktu': _now().isoformat(timespec='seconds'),
    })
    wadah['revisi'] = riwayat[-50:]                 # jaga jangan membengkak
    wadah['artikel'] = artikel
    baris.hasil_json = _json.dumps(wadah, ensure_ascii=False)
    db.commit()

    #  Tulis ulang berkas .docx hasil (pola SAMA dengan konversi).
    nama_berkas = ''
    try:
        judul = str((artikel or {}).get('judul') or '').strip()[:80]
        if judul:
            nama_berkas = f'{judul}.docx'
        tulis_hasil(db, u, fid, artikel, nama_berkas)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konversi] tulis berkas hasil revisi gagal: %s', e)

    return {'tersimpan': True, 'jumlah_revisi': len(riwayat)}


# ══════════════════════════════════════════════════════════════════════════
# TAHAP 2b — SAMBUNGAN KE AI (07 Okt 2026)
# ══════════════════════════════════════════════════════════════════════════
#  KENAPA DI SINI: seluruh pagar + prompt + penyimpanan SUDAH ADA. Yang
#  belum cuma PEMANGGIL AI-nya. NOL MESIN BARU — memakai jalur AI yang
#  sudah dipakai revisi (`ai._revisi_dengan_failover`), jadi:
#    · gerbang biaya tetap SATU PINTU (9router)
#    · failover + validasi output ikut terbawa
#    · nama model ASLI ikut terlapor (aturan Bos)
#  DILARANG menyalin kode panggilan AI baru di sini (dua jalur = bahaya).

def _urai_artikel(mentah: str) -> dict | None:
    """Ambil OBJEK JSON artikel dari balasan AI (tahan pagar ```json)."""
    teks = (mentah or '').strip()
    if not teks:
        return None
    #  Buang pagar code-fence kalau ada.
    teks = re.sub(r'^```(?:json)?\s*', '', teks)
    teks = re.sub(r'\s*```$', '', teks).strip()
    #  Ambil dari '{' pertama sampai '}' terakhir (AI kadang beri kata pengantar).
    awal, akhir = teks.find('{'), teks.rfind('}')
    if awal < 0 or akhir <= awal:
        return None
    try:
        data = json.loads(teks[awal:akhir + 1])
    except (ValueError, TypeError):
        return None
    return data if isinstance(data, dict) else None


def normalisasi_artikel(data: dict) -> dict:
    """Rapikan balasan AI → bentuk baku artikel (kunci wajib selalu ada).

    Bentuk baku = yang SUDAH dipakai `artikel_ke_teks()`, `periksa_hasil()`,
    `daftar_revisi()`. Jadi JANGAN bikin bentuk kedua.
    """
    a = data or {}
    elemen = a.get('elemen') if isinstance(a.get('elemen'), dict) else {}
    penulis = a.get('penulis')
    if not isinstance(penulis, list):
        penulis = []
    kata = a.get('kata_kunci')
    if isinstance(kata, str):
        kata = [k.strip() for k in kata.split(',') if k.strip()]
    elif not isinstance(kata, list):
        kata = []
    pustaka = a.get('daftar_pustaka')
    if isinstance(pustaka, str):
        pustaka = [p.strip() for p in pustaka.splitlines() if p.strip()]
    elif not isinstance(pustaka, list):
        pustaka = []

    keluar = dict(a)
    for kunci in BAGIAN_WAJIB:
        if not isinstance(keluar.get(kunci), str):
            keluar[kunci] = str(keluar.get(kunci) or '')
    keluar.update({
        'judul': str(a.get('judul') or '').strip(),
        'penulis': [p for p in penulis if isinstance(p, dict)],
        'abstrak_id': str(a.get('abstrak_id') or ''),
        'abstract_en': str(a.get('abstract_en') or ''),
        'kata_kunci': [str(k) for k in kata],
        'daftar_pustaka': [str(p) for p in pustaka],
        'elemen': {str(k): str(v) for k, v in elemen.items() if v},
    })
    return keluar


async def jalankan_konversi(db, u, fid: int, naskah: str, identitas: dict,
                            peta: dict, jenis: str, template: str = 'JPEM'
                            ) -> dict:
    """PANGGIL AI → urai → normalisasi. TIDAK menyentuh kuota (pemanggil).

    Return {'ok', 'artikel', 'model', 'token_in', 'token_out', 'galat'}.
    Kuota dipotong & dikembalikan oleh PEMANGGIL (rute), sesuai urutan pagar:
      potong → panggil → simpan ; kalau gagal teknis → kembalikan.
    """
    from . import ai as ai_mod
    keluar = {'ok': False, 'artikel': {}, 'model': '',
              'token_in': 0, 'token_out': 0, 'galat': ''}

    pesan = susun_pesan(naskah, jenis, identitas, peta, template)
    sistem = _bersihkan_komentar_header(muat_prompt())
    if not sistem:
        keluar['galat'] = 'Prompt artikel jurnal tidak terbaca di server.'
        return keluar

    #  ⚠️ KENAPA `_panggil_router` (BUKAN `_revisi_dengan_failover`) —
    #  TERUKUR dari kode 07 Okt 2026 (Wulan hampir salah pakai):
    #   1. `_revisi_dengan_failover()` TIDAK punya parameter `system` → prompt
    #      artikel tak akan terkirim, AI memakai prompt REVISI (salah).
    #   2. `_revisi_dengan_failover()` memanggil `_valid(konten, n)` yang
    #      MENUNTUT baris `[PROFIL]` + blok komentar revisi → balasan artikel
    #      (JSON) PASTI ditolak → retry 2× → 503.
    #   `_panggil_router()` = LAPISAN YANG SAMA (satu pintu 9router + failover
    #   OpenRouter + urai usage), hanya TANPA gerbang format revisi. Jadi
    #   gerbang biaya TETAP SATU PINTU, bukan jalur AI kedua.
    try:
        konten, info = await ai_mod._panggil_router(
            pesan, ai_mod.AI_TIMEOUT_DETIK, system=sistem)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[konversi] panggil AI gagal (fid=%s): %s', fid, e)
        keluar['galat'] = f'{type(e).__name__}: {e}'
        return keluar

    #  NAMA MODEL ASLI wajib dilaporkan (aturan Bos 16Sep26) — 9router
    #  mengirim nama model yang BENAR-BENAR menjawab di field `model`.
    nama_model = str((info or {}).get('model') or '').strip() or 'EduAi'

    data = _urai_artikel(konten)
    if not data:
        keluar['galat'] = ('Balasan AI tidak bisa dibaca sebagai artikel. '
                           'Coba jalankan konversi lagi.')
        keluar['model'] = nama_model
        return keluar

    keluar.update(
        ok=True, artikel=normalisasi_artikel(data), model=nama_model,
        token_in=int((info or {}).get('token_in') or 0),
        token_out=int((info or {}).get('token_out') or 0))
    return keluar


# ══════════════════════════════════════════════════════════════════════════
# TAHAP 3b — BERKAS HASIL (.docx) — anti tekan-back (SOT §C.8)
# ══════════════════════════════════════════════════════════════════════════
#  KENAPA: hasil HARUS langsung jadi berkas di workspace (bukan menunggu
#  tombol unduh). Kalau user tekan back / HP mati, artikel tetap ada.
#  ⚠️ NOL MESIN BARU + NOL DEPENDENCY BARU: `python-docx` TIDAK terpasang
#  di container (terukur 07 Okt), jadi JANGAN pakai itu. Cara yang SUDAH
#  dipakai proyek ini = tulis `word/document.xml` ke dalam ZIP .docx
#  (pola `dokumen_baru.py` + `tulis_docx.py`).

def _xml_aman(s: str) -> str:
    """Escape teks untuk XML Word (wajib — kalau tidak, berkas rusak)."""
    t = str(s or '')
    t = (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
    t = (t.replace('"', '&quot;').replace("'", '&apos;'))
    #  Buang karakter kontrol yang tidak sah di XML.
    return ''.join(c for c in t if c >= ' ' or c in '\t\n')


def _par(teks: str, tebal: bool = False, tengah: bool = False,
         ukuran: int = 0, miring: bool = False) -> str:
    """Satu paragraf Word (XML) — pola `tulis_docx._par_baru`."""
    jc = '<w:jc w:val="center"/>' if tengah else ''
    sz = f'<w:sz w:val="{ukuran * 2}"/><w:szCs w:val="{ukuran * 2}"/>' if ukuran else ''
    b = '<w:b/><w:bCs/>' if tebal else ''
    i = '<w:i/><w:iCs/>' if miring else ''
    rpr = f'<w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/>{b}{i}{sz}</w:rPr>'
    return (f'<w:p><w:pPr>{jc}{rpr}</w:pPr>'
            f'<w:r>{rpr}<w:t xml:space="preserve">{_xml_aman(teks)}</w:t></w:r></w:p>')


def rakit_xml_artikel(artikel: dict) -> str:
    """Rakit isi dokument.xml artikel (bentuk baku → XML Word)."""
    a = normalisasi_artikel(artikel)
    par: list[str] = []

    par.append(_par(a.get('judul') or 'ARTIKEL JURNAL', tebal=True,
                    tengah=True, ukuran=14))
    for p in (a.get('penulis') or []):
        if not isinstance(p, dict):
            continue
        baris = str(p.get('nama') or '')
        if p.get('email'):
            baris += f" <{p['email']}>"
        if p.get('afiliasi'):
            baris += f" — {p['afiliasi']}"
        if baris.strip():
            par.append(_par(baris, tengah=True))
    if a.get('institusi'):
        par.append(_par(a['institusi'], miring=True, tengah=True))
    par.append(_par(''))

    if a.get('abstrak_id'):
        par.append(_par('ABSTRAK', tebal=True, tengah=True))
        par.append(_par(a['abstrak_id']))
        if a.get('kata_kunci'):
            par.append(_par('Kata kunci: ' + ', '.join(a['kata_kunci']),
                            miring=True))
        par.append(_par(''))
    if a.get('abstract_en'):
        par.append(_par('ABSTRACT', tebal=True, tengah=True))
        par.append(_par(a['abstract_en']))
        if a.get('keywords'):
            par.append(_par('Keywords: ' + ', '.join(a['keywords']),
                            miring=True))
        par.append(_par(''))

    #  Badan artikel — urutan IMRAD (kunci sama dengan BAGIAN_REVISI).
    for kunci, judul_bab in BAGIAN_REVISI:
        if kunci in ('judul', 'abstrak_id', 'abstract_en', 'daftar_pustaka'):
            continue
        isi = a.get(kunci)
        if not isi:
            continue
        par.append(_par(judul_bab, tebal=True))
        for baris in str(isi).split('\n'):
            if baris.strip():
                par.append(_par(baris.strip()))
        par.append(_par(''))

    #  Elemen mutu (11) yang ada isinya.
    ada_elemen = False
    for kunci, label, _tempat in ELEMEN_11:
        nilai = (a.get('elemen') or {}).get(kunci)
        if nilai:
            if not ada_elemen:
                ada_elemen = True
            par.append(_par(label, tebal=True))
            par.append(_par(nilai))
    if ada_elemen:
        par.append(_par(''))

    if a.get('daftar_pustaka'):
        par.append(_par('DAFTAR PUSTAKA', tebal=True))
        for i, p in enumerate(a['daftar_pustaka'], 1):
            par.append(_par(f'{i}. {p}'))

    return ''.join(par)


def tulis_artikel_docx(artikel: dict, jalur) -> dict:
    """Tulis artikel (dict baku) jadi .docx — SALIN templat, ganti document.xml.

    Cara SAMA dengan `dokumen_baru.py` (templat) + `tulis_docx.py` (zip).
    Return {'ok','galat'}.
    """
    from pathlib import Path as _P
    templat = _P(__file__).resolve().parent / 'templat' / 'naskah-baru.docx'
    try:
        if not templat.exists():
            return {'ok': False,
                    'galat': f'Templat .docx tidak ada di server ({templat}).'}
        tujuan = _P(jalur)
        tujuan.parent.mkdir(parents=True, exist_ok=True)

        isi_baru = rakit_xml_artikel(artikel)
        #  Baca isi templat, ganti `word/document.xml`, tulis ulang ZIP.
        with zipfile.ZipFile(templat, 'r') as zin:
            item = zin.infolist()
            with zipfile.ZipFile(tujuan, 'w', zipfile.ZIP_DEFLATED) as zout:
                for it in item:
                    data = zin.read(it.filename)
                    if it.filename == 'word/document.xml':
                        awal = data.find(b'<w:body>')
                        akhir = data.rfind(b'</w:body>')
                        if awal < 0 or akhir < 0:
                            return {'ok': False,
                                    'galat': 'Templat .docx tidak berwujud Word biasa.'}
                        #  ⚠️ AKAR (07 Okt 2026, ketahuan dari uji D5d):
                        #  `<w:sectPr>` (ukuran halaman + margin + header/footer)
                        #  letaknya DI DALAM <w:body>, SEBELUM `</w:body>` —
                        #  BUKAN sesudahnya. Kalau diambil `data[akhir:]`, sectPr
                        #  ikut terbuang → halaman kehilangan ukuran & margin.
                        #  Yang benar: potong tepat SEBELUM '<w:sectPr' terakhir.
                        sisa = data[awal + len(b'<w:body>'):akhir]
                        pos = sisa.rfind(b'<w:sectPr')
                        if pos < 0:
                            return {'ok': False,
                                    'galat': 'Templat .docx tidak punya <w:sectPr>.'}
                        kepala = data[:awal + len(b'<w:body>')].decode('utf-8')
                        ekor = sisa[pos:].decode('utf-8')       # sectPr utuh
                        tutup = data[akhir:].decode('utf-8')     # '</w:body>…'
                        data = (kepala + isi_baru + ekor + tutup).encode('utf-8')
                    zout.writestr(it, data)
        if not tujuan.exists() or tujuan.stat().st_size < 1000:
            return {'ok': False, 'galat': 'Berkas .docx hasil kosong/rusak.'}
        return {'ok': True, 'galat': ''}
    except Exception as e:                                    # noqa: BLE001
        log.error('[konversi] tulis docx gagal: %s', e)
        return {'ok': False, 'galat': f'{type(e).__name__}: {e}'}


def tulis_hasil(db, u, fid: int, artikel: dict, nama_berkas: str = '') -> dict:
    """TAHAP 3b — simpan hasil sebagai BERKAS BARU milik user (workspace).

    Return {'ok','file_id','nama','galat'}. Pola SAMA seperti unggahan /
    dokumen_baru: tulis disk DULU → baru catat di tabel `files`.
    """
    from .config import UPLOAD_DIR
    from .models import FileBerkas
    import secrets as _secrets

    a = normalisasi_artikel(artikel)
    judul = (a.get('judul') or 'Artikel').strip()[:80]
    judul = re.sub(r'[\\/:*?"<>|]+', ' ', judul).strip() or 'Artikel'
    nama_asli = (nama_berkas or f'{judul}.docx').strip()
    if not nama_asli.lower().endswith('.docx'):
        nama_asli += '.docx'
    nama_asli = nama_asli.replace('/', '-').replace('\\', '-')[:120]

    try:
        dir_unggah = UPLOAD_DIR / str(int(getattr(u, 'id', 0)))
        dir_unggah.mkdir(parents=True, exist_ok=True)
        nama_simpan = f'{_secrets.token_hex(8)}.docx'
        jalur = dir_unggah / nama_simpan

        tulis = tulis_artikel_docx(a, jalur)
        if not tulis['ok']:
            return {'ok': False, 'file_id': 0, 'nama': '', 'galat': tulis['galat']}

        ukuran = jalur.stat().st_size
        fb = FileBerkas(
            user_id=int(getattr(u, 'id', 0)), nama=nama_asli,
            nama_simpan=nama_simpan, ukuran=ukuran,
            tipe=('application/vnd.openxmlformats-officedocument'
                  '.wordprocessingml.document'),
            folder_id=None)
        db.add(fb)
        db.commit()
        db.refresh(fb)
        return {'ok': True, 'file_id': int(fb.id), 'nama': nama_asli,
                'galat': ''}
    except Exception as e:                                    # noqa: BLE001
        log.error('[konversi] tulis hasil gagal (fid=%s): %s', fid, e)
        try:
            db.rollback()
        except Exception:                                     # noqa: BLE001
            pass
        #  Jangan tinggalkan berkas yatim (pola dokumen_baru.py).
        try:
            (UPLOAD_DIR / str(int(getattr(u, 'id', 0))) /
             f'{_secrets.token_hex(8)}.docx').unlink(missing_ok=True)
        except Exception:                                     # noqa: BLE001
            pass
        return {'ok': False, 'file_id': 0, 'nama': '', 'galat':
                f'{type(e).__name__}: {e}'}
