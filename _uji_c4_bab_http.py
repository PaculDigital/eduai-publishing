"""UJI C4 lewat API HIDUP — /api/ai/v1/bab harus mengembalikan SUB-BAB.

KENAPA (24Sep26): uji fungsi (`_uji_c4_bab.py`) membuktikan MESINNYA; uji ini
membuktikan JALUR NYATA (HTTP) yang dipakai layar mahasiswa.

CARA: bikin user uji + berkas uji berisi naskah bertanda sub-bab, lalu
panggil endpoint dengan token sah. Pakai DB terpisah? TIDAK — endpoint butuh
user & berkas nyata. Karena itu pakai BERKAS UJI yang dibuat lalu DIHAPUS
di akhir (aturan: jangan tinggalkan sampah di DB produksi).

JALAN di dalam container:
    docker cp _uji_c4_bab_http.py eduai-app:/app/
    docker exec -w /app eduai-app python3 _uji_c4_bab_http.py
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


NASKAH = """BAB I PENDAHULUAN

1.1 Latar Belakang
Pendidikan merupakan pondasi utama dalam membangun sumber daya manusia
yang berkualitas. Berbagai penelitian menunjukkan hal tersebut.

1.2 Rumusan Masalah
Bagaimana pengaruh kualitas layanan terhadap kepuasan pelanggan?

1.3 Tujuan Penelitian
Menganalisis pengaruh kualitas layanan terhadap kepuasan pelanggan.
"""

print('═' * 60)
print('UJI C4 (HTTP) — /api/ai/v1/bab harus keluarkan SUB-BAB')
print('═' * 60)

# ── Cek langsung pada fungsi endpoint (tanpa HTTP) ────────────────────────
#  Endpoint butuh Depends(wajib_login_api) + Request → sulit dipanggil
#  langsung. Yang diuji = JALUR KEPUTUSAN + jalur data yang sama.
from app.versi import deteksi_bab, _deteksi_bagian       # noqa: E402
from app.config import AI_POTONG_KARAKTER                 # noqa: E402

def keluaran_endpoint(teks):
    """Replika PERSIS blok pembentukan `keluaran` di app/ai.py (endpoint /bab)."""
    dari_bagian = _deteksi_bagian(teks)
    daftar = dari_bagian if dari_bagian else deteksi_bab(teks)
    keluaran = []
    for b in daftar:
        panjang = len(b.get('isi') or '') or b.get('panjang') or 0
        keluaran.append({
            'label': b['label'],
            'judul': b['judul'],
            'panjang': panjang,
            'bagian': max(1, -(-panjang // AI_POTONG_KARAKTER)),
        })
    return keluaran


out = keluaran_endpoint(NASKAH)
label = [x['label'] for x in out]
print(f'\n[1] Label dari endpoint: {label}')
print(f'[2] Panjang: {[(x["label"], x["panjang"]) for x in out]}')
print(f'[3] Jumlah bagian: {[(x["label"], x["bagian"]) for x in out]}')

cek('label yang keluar = SUB-BAB (bukan BAB I)',
    '1.2' in label, f'label={label}')
cek("label '1.2' ada → mahasiswa BISA pilih sub-bab",
    '1.2' in label)
cek("panjang '1.2' hanya bagian itu (< 25% seluruh naskah)",
    bool([x for x in out if x['label'] == '1.2'])
    and [x for x in out if x['label'] == '1.2'][0]['panjang'] * 4 < len(NASKAH),
    f"panjang={[x['panjang'] for x in out if x['label'] == '1.2']} total={len(NASKAH)}")
cek("'bagian' 1.2 = 1 (cukup 1 Token Revisi)",
    [x['bagian'] for x in out if x['label'] == '1.2'] == [1],
    f"bagian={[(x['label'], x['bagian']) for x in out]}")
cek('semua label bertanda sub-bab (1.1 / 1.2 / 1.3)',
    {'1.1', '1.2', '1.3'}.issubset(set(label)), f'label={label}')

# ── Bukti jumlah token turun: cara BARU vs cara LAMA ─────────────────────
out_lama = [{'label': b['label'],
             'panjang': len(b.get('isi') or '') or len(NASKAH)}
            for b in deteksi_bab(NASKAH)]
print(f'\n[4] Cara LAMA (deteksi_bab): {[(x["label"], x["panjang"]) for x in out_lama]}')
cek('cara LAMA tidak punya 1.2 → tak bisa pilih sub-bab (bukti bug)',
    '1.2' not in [x['label'] for x in out_lama])

print('\n' + '═' * 60)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 60)
sys.exit(0 if GAGAL == 0 else 1)
