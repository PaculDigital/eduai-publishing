"""UJI LAPIS 5 — PINTU LAYAR: `versi._deteksi_bagian()` pakai surveyor.

Diuji dengan TEKS NYATA (bukan fid), persis seperti editor memakainya.
  ① teks tanpa nomor (Asih) → surveyor jalan, bagian masuk akal
  ② teks kosong            → [] (tidak meledak)
  ③ teks hanya 'AAAA'      → tidak meledak
  ④ surveyor DIMATIKAN (suntikan) → fallback state.petakan() tetap jalan
Jalankan di DALAM container.
"""
import sys
sys.path.insert(0, '/app')

from app import versi

L = G = 0


def cek(n, s, cat=''):
    global L, G
    if s:
        L += 1
        print(f'  ✅ {n}' + (f' — {cat}' if cat else ''))
    else:
        G += 1
        print(f'  ❌ {n}' + (f' — {cat}' if cat else ''))


print('=' * 70)
print('UJI LAPIS 5 — PINTU LAYAR (_deteksi_bagian)')
print('=' * 70)

# ── teks uji: tiru naskah akademik (tanpa nomor, seperti Asih) ────────
TEKS = '\n'.join([
    'BAB I', 'PENDAHULUAN', '',
    'Latar Belakang', '',
    'Pendidikan adalah fondasi utama pembangunan bangsa. ' * 6, '',
    'Gap research', '',
    'Penelitian sebelumnya hanya membahas sebagian kecil. ' * 5, '',
    'Rumusan Masalah', '',
    'Bagaimana pengaruh kepemimpinan terhadap kinerja? ' * 5, '',
    'BAB II', 'TINJAUAN PUSTAKA', '',
    'Landasan Teori', '',
    'Teori kepemimpinan berkembang sejak lama. ' * 6, '',
])

# ── ① surveyor jalan pada teks nyata ─────────────────────────────────
try:
    h = versi._deteksi_bagian(TEKS)
    cek('① tidak meledak', isinstance(h, list), f'{len(h)} bagian')
    cek('①b ada bagian', bool(h))
    if h:
        print(f'     contoh: label={h[0].get("label")!r} '
              f'judul={h[0].get("judul")!r} isi={len(h[0].get("isi") or "")} kar')
    cek('①c kunci SAMA dgn pemakai lama',
        all(k in (h[0] if h else {}) for k in ('label', 'judul', 'isi', 'posisi')),
        repr(sorted((h[0] if h else {}).keys())))
except Exception as e:
    cek('① surveyor pada teks', False, f'{type(e).__name__}: {e}')

# ── ② teks kosong ────────────────────────────────────────────────────
try:
    cek('② teks kosong ⇒ []', versi._deteksi_bagian('') == [])
except Exception as e:
    cek('② teks kosong ⇒ []', False, f'{type(e).__name__}: {e}')

# ── ③ teks sampah ────────────────────────────────────────────────────
try:
    r = versi._deteksi_bagian('AAAA')
    cek('③ teks sampah tidak meledak', isinstance(r, list), f'{len(r)} bagian')
except Exception as e:
    cek('③ teks sampah tidak meledak', False, f'{type(e).__name__}: {e}')

# ── ④ surveyor DIMATIKAN ⇒ fallback tetap jalan ──────────────────────
print('── ④ surveyor dimatikan ⇒ fallback state.petakan ──')
try:
    import app.peta3_jev as P3
    asli = P3.petakan_teks
    P3.petakan_teks = lambda *a, **k: None            # tiru surveyor mati
    try:
        h2 = versi._deteksi_bagian(TEKS)
        cek('④ fallback tetap memberi bagian', isinstance(h2, list) and bool(h2),
            f'{len(h2)} bagian (cara lama)')
    finally:
        P3.petakan_teks = asli
    h3 = versi._deteksi_bagian(TEKS)
    cek('④b pulih (surveyor hidup lagi)', isinstance(h3, list) and bool(h3),
        f'{len(h3)} bagian')
except Exception as e:
    cek('④ fallback', False, f'{type(e).__name__}: {e}')

print('-' * 70)
print(f'HASIL UJI LAPIS 5: {L} LULUS / {G} GAGAL')
raise SystemExit(1 if G else 0)
