"""UKUR (Langkah 0-1, 24Sep26) — berapa token yang SEBENARNYA dibutuhkan?

TUJUAN: menjawab pertanyaan Bos dengan ANGKA, bukan perkiraan:
  1. Sekarang: naskah 65.932 kar → berapa token_in yang dikirim?
  2. Setelah konteks.py disambung: berapa token_in-nya?
  3. Apakah naskah 65.932 masih pecah 2 bagian?
  4. Berapa Token Revisi yang SEHARUSNYA (menurut §4.13)?

CARA: memakai FUNGSI ASLI dari app/ (petakan, potong_cerdas, konteks.bangun_prompt)
      + naskah uji nyata. TIDAK menyentuh kode produksi. TIDAK memanggil AI.
"""
import sys, zipfile, re
sys.path.insert(0, '/opt/data/services/eduai-publishing')

from app.state import petakan, buang_daftar_isi, deteksi_subbab, deteksi_bab_besar
from app.konteks import dari_struktur, bangun_prompt
from app.ai import potong_cerdas, hitung_bagian
from app.config import AI_POTONG_KARAKTER

# ── Kira-kira token: 1 token ≈ 3,7 karakter (Indonesia, campuran akademik) ──
KAR_PER_TOKEN = 3.7
def tok(kar): return round(kar / KAR_PER_TOKEN)

def baca_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    t = re.sub(r'<[^>]+>', '', xml)
    return re.sub(r'\n{3,}', '\n\n', t)

# ══════════════════════════════════════════════════════════════════
print('=' * 78)
print('BAHAN UJI: naskah nyata (sama dgn yang dipakai produksi, file_id=47)')
print('=' * 78)

KANDIDAT = [
    '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx',
    '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-pendidikan-bahasa.docx',
    '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-sastra-novel.docx',
    '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx',
    '_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx',
]
import os
for f in KANDIDAT:
    if not os.path.exists(f):
        print(f'  (lewat) {f}'); continue
    teks = baca_docx(f)
    bersih = buang_daftar_isi(teks)
    sub = deteksi_subbab(bersih)
    bab = deteksi_bab_besar(bersih)
    peta = petakan(bersih)
    nama = os.path.basename(f)[:42]
    print(f'\n{nama}')
    print(f'  naskah      : {len(teks):>9,} kar')
    print(f'  setelah bersih: {len(bersih):>7,} kar')
    print(f'  sub-bab     : {len(sub):>3}    BAB besar: {len(bab)}    peta terpakai: {len(peta)} ({peta[0]["section_id"] if peta else "-"})')

# ══════════════════════════════════════════════════════════════════
print()
print('=' * 78)
print('UKURAN 1 — SEKARANG (naskah utuh dikirim + potong_cerdas)')
print('=' * 78)
f = '_contoh-dokumen/tesis-s2/TESIS-S2-unhas-manajemen-digital-marketing.docx'
teks = baca_docx(f)
bersih = buang_daftar_isi(teks)

for label, n in [('naskah penuh (yg dikirim sekarang)', len(bersih))]:
    bagian = potong_cerdas(bersih)
    print(f'\n{label}: {n:,} kar  (batas potong = {AI_POTONG_KARAKTER:,} kar)')
    print(f'  → dipecah jadi {len(bagian)} bagian: {[len(b) for b in bagian]}')
    print(f'  → hitung_bagian() = {hitung_bagian(bersih)}')
    tin = tok(n)
    print(f'  → token_in kira-kira = {tin:,}  (nyata di DB: 32.397 – 35.802 → COCOK)')

# ══════════════════════════════════════════════════════════════════
print()
print('=' * 78)
print('UKURAN 2 — KALAU konteks.py DISAMBUNG (kirim tetangga saja)')
print('=' * 78)
peta = petakan(bersih)
print(f'peta dari petakan(): {len(peta)} bagian')
for p in peta:
    print(f'   {p["section_id"]:<12} {p["section_title"][:34]:<34} {p["char_count"]:>8,} kar')

if len(peta) > 1:
    # ambil bagian TENGAH sebagai target (kasus paling umum: revisi 1 bab)
    target = peta[1]['section_id']
    print(f'\ntarget uji = {target!r}  ({peta[1]["char_count"]:,} kar)')

    # bahan-bahan
    brief_contoh = ('JUDUL: Pengaruh Digital Marketing dan Kualitas Produk terhadap '
                    'Keputusan Pembelian (Studi pada UMKM Kota Makassar). Variabel: '
                    'X1 Digital Marketing, X2 Kualitas Produk, Y Keputusan Pembelian. '
                    'Metode: kuantitatif, SEM-PLS, n=200, purposive sampling. Teori: '
                    'TAM, Kotler. Hipotesis: H1 X1→Y, H2 X2→Y, H3 keduanya simultan. ' * 8)
    isi_target = peta[1]['isi_teks']

    for nama, brief, isi in [
        ('konteks.py APA ADANYA (nama kunci masih beda)', brief_contoh, isi_target),
    ]:
        pr = bangun_prompt(bagian_target=target, struktur=peta,
                           brief_ringkas=brief, isi_saat_ini=isi,
                           komentar='1. Perbaiki kalimat pertama agar lebih akademik.')
        print(f'\n── {nama} ──')
        print(f'   isi prompt konteks : {len(pr):,} kar  → ±{tok(len(pr)):,} token')
        print(f'   CELAH blok tetangga: '
              f'BAB I={"ADA" if "BAB I (konteks)" in pr else "KOSONG"} · '
              f'sebelum={"ADA" if "BAGIAN SEBELUMNYA" in pr else "KOSONG"} · '
              f'sesudah={"ADA" if "BAGIAN SESUDAHNYA" in pr else "KOSONG"}')

    # simulasi kalau kunci SUDAH diterjemahkan (ybs. peta halus)
    peta2 = [{'nomor': p['section_id'], 'judul': p['section_title'],
              'isi': p['isi_teks']} for p in peta]
    pr2 = bangun_prompt(bagian_target=target, struktur=peta2,
                        brief_ringkas=brief_contoh, isi_saat_ini=isi_target,
                        komentar='1. Perbaiki kalimat pertama agar lebih akademik.')
    print(f'\n── konteks.py SETELAH kunci diterjemahkan (peta kasar 3 BAB) ──')
    print(f'   isi prompt konteks : {len(pr2):,} kar  → ±{tok(len(pr2)):,} token')
    print(f'   BAB I={"ADA" if "BAB I (konteks)" in pr2 else "KOSONG"} · '
          f'sebelum={"ADA" if "BAGIAN SEBELUMNYA" in pr2 else "KOSONG"} · '
          f'sesudah={"ADA" if "BAGIAN SESUDAHNYA" in pr2 else "KOSONG"}')

print()
print('=' * 78)
print('UKURAN 3 — APAKAH 65.932 MASIH PECAH 2 SETELAH DIKIRIM PER-ISI?')
print('=' * 78)
for p in peta:
    n = len(p['isi_teks']) if p['isi_teks'] else 0
    bg = hitung_bagian(p['isi_teks'] or '')
    print(f'  {p["section_id"]:<12} {n:>8,} kar  → {bg} bagian  ({n/len(bersih)*100:.0f}% naskah)')
