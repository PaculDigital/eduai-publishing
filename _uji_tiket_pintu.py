"""UJI 3c — TIKET DIBACA DI PINTU KONVERSI (periksa_sebelum_konversi).

Buktikan: elemen yang BERTIKET & maknanya tetap ⇒ TIDAK muncul di `kurang`.
"""
import os
import sys

os.makedirs("/tmp/uji3c", exist_ok=True)
sys.path.insert(0, "/app")

from app import main as M                      # noqa: E402
from app import konversi as K                  # noqa: E402
from app import tiket_lolos as T               # noqa: E402
from app import models                         # noqa: E402
from app.models import KonversiNaskah          # noqa: E402

lulus, gagal = [], []


def cek(nama, syarat, bukti=""):
    (lulus if syarat else gagal).append(nama)
    print(f"  {'✅' if syarat else '❌'} {nama}" + (f"  → {bukti}" if bukti else ""))


db = M.SessionLocal()
FID, EMAIL = 81, 'asih.susanti@eduai.test'
u = db.query(models.User).filter(models.User.email == EMAIL).first()

# ── 0. siapkan baris konversi uji ─────────────────────────────────────
db.query(KonversiNaskah).filter(KonversiNaskah.user_id == u.id,
                                KonversiNaskah.file_id == FID).delete()
db.commit()
db.add(KonversiNaskah(user_id=u.id, file_id=FID, status='beres',
                      hasil_json='{}'))
db.commit()

NASKAH = ('JUDUL: Uji Tiket\nPenulis: Asih Susanti\nEmail: asih@eduai.test\n\n'
          'BAB I PENDAHULUAN\n' + ('Kalimat pendahuluan penelitian. ' * 120) +
          '\n\nBAB II TINJAUAN PUSTAKA\n' + ('Teori dan kajian pustaka. ' * 120))

# ── 1. TANPA tiket: elemen kurang DITANYAKAN ──────────────────────────
print("\n══ 1. TANPA tiket → elemen tetap ditanyakan ══")
panggil_jev = {'n': 0}


def jev_sama(bahan, skema):
    panggil_jev['n'] += 1
    return {'masih_sama': {'choice': 'sama', 'confidence': 0.9}}


#  palsukan periksa_mutu supaya 'gap' pasti KURANG (tidak perlu Jev nyata)
asli_mutu = K.periksa_mutu
K.periksa_mutu = lambda db, fid, teks: {
    'ok': True, 'keputusan': 'kurang', 'ada': {}, 'skor': 0.4,
    'kurang': ['Gap (celah penelitian)'], 'ragu': [], 'alasan': '', 'detik': 0,
    'model': 'uji'}
asli_tanya = None
try:
    from app import jev
    asli_tanya = jev.tanya
    jev.tanya = jev_sama

    s1 = K.periksa_sebelum_konversi(db, u, FID, NASKAH, 'uji.docx')
    cek("1a 'gap' muncul di kurang (tanpa tiket)",
        'Gap (celah penelitian)' in (s1.get('mutu') or {}).get('kurang', []),
        str((s1.get('mutu') or {}).get('kurang')))

    # ── 2. TULIS tiket untuk 'gap' ────────────────────────────────────
    print("\n══ 2. tiket ditulis → bab makna tetap ══")
    T.tiket_tulis(db, u, FID, {}, ['gap'],
                  lambda k: NASKAH[:1500])
    tk = T.tiket_baca(db, u, FID)
    cek("2a tiket 'gap' tersimpan", 'gap' in tk, str(list(tk.keys())))

    # ── 3. tiket makna TETAP → elemen DILEWATI ────────────────────────
    print("\n══ 3. bab diubah TAPI makna tetap → dilewati ══")
    NASKAH2 = NASKAH + '\n\nKalimat tambahan pendukung di akhir bab.'
    s2 = K.periksa_sebelum_konversi(db, u, FID, NASKAH2, 'uji.docx')
    kurang2 = (s2.get('mutu') or {}).get('kurang', [])
    cek("3a 'gap' TIDAK lagi di kurang (sudah Done)", 
        'Gap (celah penelitian)' not in kurang2, str(kurang2))
    cek("3b laporan tiket mencatat 'lolos'",
        'Gap (celah penelitian)' in (s2.get('tiket') or {}).get('lolos', []),
        str((s2.get('tiket') or {}).get('lolos')))

    # ── 4. makna BERUBAH → tetap ditanyakan ───────────────────────────
    print("\n══ 4. makna BERUBAH → tetap ditanyakan ══")
    T.tiket_tulis(db, u, FID, {}, ['gap'], lambda k: NASKAH[:1500])

    def jev_beda(bahan, skema):
        return {'masih_sama': {'choice': 'beda', 'confidence': 0.9}}

    jev.tanya = jev_beda
    NASKAH3 = NASKAH.replace('BAB I PENDAHULUAN',
                             'BAB I PENDAHULUAN (fokus baru sama sekali)')
    s3 = K.periksa_sebelum_konversi(db, u, FID, NASKAH3, 'uji.docx')
    kurang3 = (s3.get('mutu') or {}).get('kurang', [])
    cek("4a makna berubah → 'gap' KEMBALI ditanyakan",
        'Gap (celah penelitian)' in kurang3, str(kurang3))
    cek("4b tiket 'gap' DIHAPUS", 'gap' not in T.tiket_baca(db, u, FID),
        str(list(T.tiket_baca(db, u, FID).keys())))

    # ── 5. GIGI: modul tiket dimatikan → tidak ada yang dilewati ──────
    print("\n══ 5. UJI GIGI: tiket dimatikan ══")
    T.tiket_tulis(db, u, FID, {}, ['gap'], lambda k: NASKAH[:1500])
    jev.tanya = jev_sama
    asli_periksa = T.tiket_periksa
    T.tiket_periksa = lambda *a, **k: {'kurang': a[3] if len(a) > 3 else [],
                                       'lolos': [], 'batal': [], 'diperiksa': 0}
    s4 = K.periksa_sebelum_konversi(db, u, FID, NASKAH2, 'uji.docx')
    T.tiket_periksa = asli_periksa
    kurang4 = (s4.get('mutu') or {}).get('kurang', [])
    cek("5a tiket mati → 'gap' tetap ditanyakan (bergigi)",
        'Gap (celah penelitian)' in kurang4, str(kurang4))

finally:
    K.periksa_mutu = asli_mutu
    if asli_tanya is not None:
        from app import jev
        jev.tanya = asli_tanya

# ── bersihkan ────────────────────────────────────────────────────────
db.query(KonversiNaskah).filter(KonversiNaskah.user_id == u.id,
                                KonversiNaskah.file_id == FID).delete()
db.commit()
db.close()

print()
print("═" * 62)
print(f"  HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL")
if gagal:
    print("  GAGAL: " + ", ".join(gagal))
print("═" * 62)
sys.exit(1 if gagal else 0)
