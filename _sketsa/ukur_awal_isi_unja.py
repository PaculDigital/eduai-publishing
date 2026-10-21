"""UKUR: kenapa buang_daftar_isi UNJA membuang 40%? Mana jalur yang dipakai?"""
import sys, zipfile, re
sys.path.insert(0, '/opt/data/services/eduai-publishing')
from app.state import awal_isi_naskah, buang_daftar_isi

def baca(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    return re.sub(r'\n{3,}', '\n\n', re.sub(r'<[^>]+>', '', re.sub(r'</w:p>', '\n', xml)))

P = '_uji_web/Skripsi_Rizky_Hanif_FULL.docx'
asli = baca(P)
a = awal_isi_naskah(asli)
print('=' * 92)
print(f'awal_isi_naskah() = {a}  dari {len(asli):,} kar  ({a/len(asli)*100:.1f}%)')
print('=' * 92)
print('→ KALAU 0: aturan AKAR gagal (tidak menemukan "BAB I" judul bersih)')
print('           → jatuh ke jaring pengaman (pembuang per-baris)')
print()

# Cari semua "BAB I" di naskah + apakah judulnya bersih
print('--- semua baris "BAB ..." di naskah (+ baris berikutnya) ---')
baris = asli.split('\n')
for i, b in enumerate(baris):
    if re.match(r'^\s*BAB\b', b, re.I):
        bersih_b = b.strip()[:70]
        nxt = baris[i + 1].strip()[:60] if i + 1 < len(baris) else ''
        print(f'   baris {i:>4}: {bersih_b!r}')
        print(f'            +1: {nxt!r}')

# Di mana "DAFTAR" muncul?
print('\n--- baris yang mengandung "DAFTAR" ---')
for i, b in enumerate(baris):
    if 'DAFTAR' in b.upper() and len(b.strip()) < 60:
        print(f'   baris {i:>4} ({i/len(baris)*100:>5.1f}%): {b.strip()!r}')

# Jejak lengkap: mana yang hilang setelah pembersihan TANPA aturan akar?
print('\n--- SIMULASI: kalau aturan AKAR dimatikan, apa yang terjadi? ---')
import app.state as st
asli_awal = st.awal_isi_naskah
st.awal_isi_naskah = lambda t: 0     # matikan sementara
coba = buang_daftar_isi(asli)
st.awal_isi_naskah = asli_awal
print(f'   dengan aturan akar : {len(buang_daftar_isi(asli)):,} kar')
print(f'   TANPA aturan akar  : {len(coba):,} kar')
print(f'   → jadi aturan akar {"BEKERJA" if len(buang_daftar_isi(asli)) > len(coba) else "TIDAK menolong"}')
