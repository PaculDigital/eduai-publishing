#!/usr/bin/env python3
"""UJI KATA NOTIFIKASI EDUAI — penjaga aturan Bos 17Sep26.

MEMERIKSA SEMUA kalimat di app/notifikasi.py:
  1. TIDAK memuat kata pantangan (PERINGATAN, BAHAYA, GAGAL!, HABIS!, dst)
  2. TIDAK menyebut "AI", "Wulan", "asisten", "agen" → harus "EduAi"
  3. Selalu punya judul + isi, dan isi memberi JALAN KELUAR untuk kabar buruk
  4. Tidak memakai tanda seru berlebihan

KENAPA DIPISAH JADI SKRIP: aturan gaya bahasa mudah rusak diam-diam ketika
seseorang (termasuk Wulan) menambah notifikasi baru. Skrip ini jadi GERBANG.
"""
import re
import sys

sys.path.insert(0, '/app')
from app import notifikasi as N                                    # noqa: E402

lulus = gagal = 0


def cek(nama, syarat, bukti=''):
    global lulus, gagal
    if syarat:
        lulus += 1
        print(f'  ✅ {nama} {bukti}')
    else:
        gagal += 1
        print(f'  ❌ {nama} {bukti}')


#  Kalimat yang DILARANG muncul di teks user-facing.
TERLARANG_SEBUTAN = (
    r'\bAI\b', r'\bWulan\b', r'\basisten\b', r'\bagen\b', r'\bmodel\b',
    r'\bLLM\b', r'\bgemini\b', r'\bqwen\b', r'\bgpt\b', r'\bdeepseek\b',
)

#  Contoh data uji per jenis
CONTOH = {
    'revisi_selesai': {'bagian': 'BAB II'},
    'revisi_belum_berhasil': {'alasan': 'provider tidak merespons'},
    'kuota_hampir_habis': {'sisa': 2},
    'addon_hampir_habis': {'sisa': 3, 'jenis': 'revisi'},
    'pembayaran_masuk': {'amount': 'Rp 50.000', 'item': 'AddOn AI'},
    'pembayaran_menunggu': {},
    'pembayaran_belum_masuk': {},
    'naskah_kena_batas': {'jumlah_bagian': 2, 'panjang': 65932},
}

print('=== 1. SEMUA JENIS PUNYA KALIMAT LENGKAP ===')
jenis_all = N.semua_jenis()
print(f'   jenis tersedia: {len(jenis_all)} → {", ".join(jenis_all)}')
for j in jenis_all:
    t = N.pesan(j, **CONTOH.get(j, {}))
    cek(f'{j}: judul & isi terisi',
        bool(t.get('judul')) and bool(t.get('isi')),
        f"→ \"{t.get('judul','')}\"")

print('\n=== 2. TIDAK ADA KATA PANTANGAN (aturan Bos: jangan menakutkan) ===')
for j in jenis_all:
    t = N.pesan(j, **CONTOH.get(j, {}))
    teks = f"{t.get('judul','')} {t.get('isi','')}"
    kena = [p for p in N.PANTANGAN if p.lower() in teks.lower()]
    cek(f'{j}: bebas kata pantangan', not kena, f'→ kena: {kena}' if kena else '')

print('\n=== 3. PENYEBUTAN HARUS "EduAi" (BUKAN AI/Wulan/agen) ===')
for j in jenis_all:
    t = N.pesan(j, **CONTOH.get(j, {}))
    teks = f"{t.get('judul','')} {t.get('isi','')}"
    kena = [p for p in TERLARANG_SEBUTAN if re.search(p, teks)]
    cek(f'{j}: sebutan bersih', not kena, f'→ kena: {kena}' if kena else '')

print('\n=== 4. TANDA SERU BERLEBIHAN ===')
for j in jenis_all:
    t = N.pesan(j, **CONTOH.get(j, {}))
    teks = f"{t.get('judul','')} {t.get('isi','')}"
    cek(f'{j}: maksimal 1 tanda seru', teks.count('!') <= 1,
        f"(ada {teks.count('!')})")

print('\n=== 5. KABAR BURUK / PENGINGAT WAJIB PUNYA JALAN KELUAR ===')
#  Kunci yang HARUS muncul di jenis tertentu — inti kepercayaan user.
WAJIB = {
    'revisi_belum_berhasil': ['kuota', 'kembalikan'],
    'kuota_hampir_habis': ['tambah', 'kapan'],
    'addon_hampir_habis': ['isi ulang', 'kapan'],
    'pembayaran_menunggu': ['bantu', 'cek'],
    'pembayaran_belum_masuk': ['bantu', 'kabari'],
}
for j, harus in WAJIB.items():
    t = N.pesan(j, **CONTOH.get(j, {}))
    teks = f"{t.get('judul','')} {t.get('isi','')}".lower()
    kurang = [k for k in harus if k not in teks]
    cek(f'{j}: menyebut jalan keluar', not kurang,
        f'→ kurang: {kurang}' if kurang else f'(cari: {harus})')

print('\n=== 6. TOMBOL TERSEDIA UNTUK YANG BUTUH AKSI ===')
for j in jenis_all:
    t = N.pesan(j, **CONTOH.get(j, {}))
    cek(f'{j}: punya label tombol', bool(t.get('tombol')),
        f"→ \"{t.get('tombol')}\"")

print('\n=== 2b. KEJUJURAN ANGKA (akar 17Sep26: sisa=0 bilang "masih cukup") ===')
#  🐛 Ketemu lewat uji E2E: saat sisa=0 kalimatnya berbunyi "Masih cukup untuk
#  sekali revisi lagi" — BOHONG. Notifikasi harus JUJUR: jangan menjanjikan
#  revisi yang sudah tidak ada.
for sisa_uji in (0, 1, 2, 5):
    t = N.pesan('kuota_hampir_habis', sisa=sisa_uji)
    isi = t['isi'].lower()
    if sisa_uji == 0:
        cek('sisa=0 TIDAK menjanjikan sisa',
            'masih cukup' not in isi and 'tinggal sekali' not in isi,
            f'→ "{t["judul"]}"')
    elif sisa_uji == 1:
        cek('sisa=1 jujur ("tinggal sekali")',
            'tinggal sekali' in isi, f'→ "{t["judul"]}"')
    else:
        cek(f'sisa={sisa_uji} menyebut angka yang benar',
            f'{sisa_uji} kali' in isi, f'→ "{t["judul"]}"')
    #  Semua tetap menawarkan JALAN KELUAR (tambah kuota), bukan menakutkan.
    cek(f'  sisa={sisa_uji} tetap memberi jalan keluar',
        'tambah kuota' in isi)

print('\n=== 7. JENIS TAK DIKENAL → TIDAK MELEMPAR GALAT ===')
try:
    t = N.pesan('jenis_yang_tidak_ada_sama_sekali')
    cek('jenis asing ditangani aman', bool(t.get('judul')),
        f"→ \"{t.get('judul')}\"")
except Exception as e:
    cek('jenis asing ditangani aman', False, f'→ {type(e).__name__}: {e}')

print('\n=== 8. GALAT TEKNIS TIDAK BOLEH BOCOR KE MAHASISWA ===')
#  🐛 17Sep26: terbukti galat mentah ("RuntimeError: provider AI tidak
#  merespons") dulu ditempel ke pesan. Menyebut 'AI' juga = melanggar aturan.
GALAT_MENTAH = [
    'RuntimeError: provider AI tidak merespons',
    'Traceback (most recent call last): File "/app/ai.py"',
    'HTTP 500 Internal Server Error',
    'sqlite3.OperationalError: database is locked',
    'KeyError: token_in',
]
for g in GALAT_MENTAH:
    t = N.pesan('revisi_belum_berhasil', alasan=g)
    teks = f"{t.get('judul','')} {t.get('isi','')}"
    bocor = [k for k in ('RuntimeError', 'Traceback', 'HTTP 500',
                         'OperationalError', 'KeyError', 'File "/app')
             if k.lower() in teks.lower()]
    cek(f'galat "{g[:32]}..." tidak bocor', not bocor,
        f'→ BOCOR: {bocor}' if bocor else '')
    # pesan tetap harus menyebut kuota dikembalikan (inti kepercayaan)
    cek('  ...tapi tetap menyebut kuota kembali',
        'kembalikan' in teks.lower() or 'kembali' in teks.lower())

print(f'\nHASIL: {lulus} LULUS / {gagal} GAGAL')
sys.exit(0 if gagal == 0 else 1)
