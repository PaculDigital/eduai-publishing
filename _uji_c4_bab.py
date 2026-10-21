"""UJI C4 — dropdown /api/ai/v1/bab harus mengenal SUB-BAB ('1.1','1.2').

KENAPA ADA (24Sep26, ACC Bos "tahap 1, c4 bug /bab"):
    `app/ai.py` dulu `daftar = deteksi_bab(teks)` → hanya kenal 'BAB I'.
    UI mahasiswa memilih SUB-BAB → hemat Token 4→1 TIDAK terasa di layar.

CARA UJI: pakai fungsi SUNGGUHAN. Tidak mengarang — dokumen uji dibuat
bertanda 'BAB I' + sub-bab '1.1','1.2','1.3' seperti naskah nyata.

DUA ARAH (aturan Bos):
    SEHAT    → wajib LULUS (sub-bab muncul)
    BERGIGI  → kalau `ai.py` dikembalikan ke `deteksi_bab(teks)` saja,
               uji ini WAJIB GAGAL.

JALAN: docker cp _uji_c4_bab.py eduai-app:/app/ \
       && docker exec -w /app eduai-app python3 _uji_c4_bab.py
"""
import sys

sys.path.insert(0, '/app')

LULUS = 0
GAGAL = 0


def cek(nama, syarat, detail=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        print(f'  ❌ {nama} {detail}')


# ── DOKUMEN UJI (meniru naskah nyata: BAB I dengan 3 sub-bab) ──────────────
NASKAH = """BAB I PENDAHULUAN

1.1 Latar Belakang
Pendidikan merupakan pondasi utama dalam membangun sumber daya manusia
yang berkualitas. Berbagai penelitian menunjukkan bahwa kualitas pendidikan
berbanding lurus dengan kemajuan suatu bangsa.

1.2 Rumusan Masalah
Berdasarkan latar belakang di atas, maka rumusan masalah dalam penelitian
ini adalah bagaimana pengaruh kualitas layanan terhadap kepuasan.

1.3 Tujuan Penelitian
Penelitian ini bertujuan untuk menganalisis pengaruh kualitas layanan
terhadap kepuasan pelanggan pada usaha mikro di Kota Gorontalo.

BAB II TINJAUAN PUSTAKA

2.1 Kualitas Layanan
Kualitas layanan adalah tingkat keunggulan yang diharapkan dan pengendalian
atas tingkat keunggulan tersebut untuk memenuhi keinginan pelanggan.
"""

print('═' * 60)
print('UJI C4 — dropdown /bab harus mengenal SUB-BAB')
print('═' * 60)

# ── 1. Fungsi yang dipakai endpoint SEKARANG ──────────────────────────────
from app.versi import deteksi_bab, _deteksi_bagian   # noqa: E402

lama = deteksi_bab(NASKAH)
baru = _deteksi_bagian(NASKAH)

print(f'\n[1] Perbandingan dua fungsi')
print(f'    deteksi_bab()     → {[b["label"] for b in lama]}')
print(f'    _deteksi_bagian() → {[b["label"] for b in baru]}')

cek('deteksi_bab HANYA kenal bab besar (bukti bug lama nyata)',
    all(str(b['label']).startswith('BAB') for b in lama),
    f'label={[b["label"] for b in lama]}')

# ── 2. UJI SEBENARNYA: panggil ulang LOGIKA endpoint, bukan cek teks ──────
#  🚨 PELAJARAN 24Sep26: versi pertama uji ini hanya `grep` teks ai.py →
#  dirusak pun tetap LULUS (uji TIDAK BERGIGI). Yang benar: REPLIKA baris
#  keputusan endpoint, lalu pastikan label yang keluar adalah SUB-BAB.
def _logika_endpoint(teks):
    """Replika PERSIS baris keputusan di `app/ai.py` endpoint /bab."""
    dari_bagian = _deteksi_bagian(teks)
    daftar = dari_bagian if dari_bagian else deteksi_bab(teks)
    return [{'label': b['label'],
             'judul': b['judul'],
             'panjang': len(b.get('isi') or '') or b.get('panjang') or 0} for b in daftar]


hasil_endpoint = _logika_endpoint(NASKAH)
label_endpoint = [x['label'] for x in hasil_endpoint]
print(f'\n[2] Label yang KELUAR dari logika endpoint: {label_endpoint}')

cek('endpoint mengeluarkan SUB-BAB (bukan hanya BAB I)',
    any(str(l).startswith('1.') for l in label_endpoint),
    f'label={label_endpoint}')

cek('endpoint memuat 1.1 / 1.2 / 1.3',
    {'1.1', '1.2', '1.3'}.issubset({str(l) for l in label_endpoint}),
    f'label={label_endpoint}')

#  Ukur panjang: kalau endpoint balik ke deteksi_bab, '1.2' TIDAK ADA →
#  panjangnya len(NASKAH) = seluruh naskah (itulah bug 4 Token).
pjg_12 = [x['panjang'] for x in hasil_endpoint if str(x['label']) == '1.2']
cek("panjang '1.2' < seluruh naskah (bukti hemat Token nyata)",
    bool(pjg_12) and 0 < pjg_12[0] < len(NASKAH),
    f"panjang 1.2={pjg_12} · total naskah={len(NASKAH)}")

#  🚨 PAGAR BERGIGI (pelajaran 24Sep26): `_deteksi_bagian()` dipanggil
#  LANGSUNG dari sini, jadi kalau `ai.py` dikembalikan ke `deteksi_bab(teks)`
#  uji ini TETAP lulus. Karena itu WAJIB ada asersi yang membaca
#  KEPUTUSAN DI DALAM ai.py — inilah satu-satunya penangkap C4 kembali.
import re                                                    # noqa: E402
sumber = open('/app/app/ai.py', encoding='utf-8').read()
#  Buang komentar dulu — kalau tidak, kata `_deteksi_bagian` di KOMENTAR
#  ikut terbaca dan asersi jadi lulus palsu.
kode = re.sub(r'#[^\n]*', '', sumber)
cek('KODE ai.py (tanpa komentar) memakai _deteksi_bagian',
    '_deteksi_bagian(teks)' in kode,
    '→ GAGAL = endpoint /bab kembali hanya kenal BAB I (C4 kembali)')
cek('KODE ai.py punya baris keputusan fallback',
    re.search(r'daftar\s*=\s*dari_bagian\s+if\s+dari_bagian\s+else\s+deteksi_bab', kode) is not None,
    '→ baris keputusan hilang = pagar ke jalur lama tidak ada')
cek('ai.py mengimpor _deteksi_bagian dari versi',
    bool(re.search(r'from \.versi import[\s\S]{0,300}_deteksi_bagian', kode)))

# ── 3. Bentuk hasil IDENTIK dengan yang dibaca endpoint ──────────────────
if baru:
    b = baru[0]
    kunci_wajib = {'label', 'judul', 'posisi', 'akhir', 'isi'}
    cek('bentuk hasil punya kunci yang dibaca endpoint',
        kunci_wajib.issubset(set(b.keys())),
        f'kunci={sorted(b.keys())}')
    cek('`isi` tidak kosong (panjang bisa dihitung)',
        len(b.get('isi') or '') > 0)
    #  `panjang` di endpoint dihitung dari `len(isi)` — pastikan masuk akal.
    pjg12 = [len(x['isi']) for x in baru if str(x['label']) == '1.2']
    cek("bagian '1.2' punya isi > 0 (BUKAN seluruh naskah)",
        0 < (pjg12[0] if pjg12 else 0) < len(NASKAH),
        f'panjang 1.2={pjg12} dari total {len(NASKAH)}')

# ── 4. PAGAR: dokumen tanpa penomoran tetap jalan ────────────────────────
POLOS = 'Ini dokumen tanpa judul bab sama sekali.\nHanya berisi paragraf biasa.'
polos_baru = _deteksi_bagian(POLOS)
cek('dokumen polos → _deteksi_bagian kosong (pagar jatuh ke deteksi_bab)',
    polos_baru == [], f'hasil={polos_baru}')

# ── 5. HEMAT: bukti tujuan akhir (dropdown sub-bab = token turun) ────────
if baru:
    peta_pjg = {str(x['label']): len(x['isi']) for x in baru}
    print(f'\n[2] Panjang tiap bagian: {peta_pjg}')
    if '1.2' in peta_pjg and peta_pjg['1.2'] > 0:
        rasio = len(NASKAH) / max(1, peta_pjg['1.2'])
        cek('memilih 1.2 mengirim JAUH lebih sedikit dari seluruh naskah',
            rasio > 2,
            f'rasio={rasio:.1f}×')

print('\n' + '═' * 60)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 60)
sys.exit(0 if GAGAL == 0 else 1)
