"""UJI TIKET LOLOS (Lapis 3) — 4 keadaan + bergigi.

Diuji TANPA jaringan: `panggil` (Jev) DIJADIKAN PARAMETER.
"""
import os
import sys

os.makedirs("/tmp/uji_tiket", exist_ok=True)
sys.path.insert(0, "/app")

from fastapi.testclient import TestClient      # noqa: E402
from app import main as M                      # noqa: E402
from app import konversi as K                  # noqa: E402
from app import tiket_lolos as T               # noqa: E402
from app import models                         # noqa: E402

lulus, gagal = [], []


def cek(nama, syarat, bukti=""):
    (lulus if syarat else gagal).append(nama)
    print(f"  {'✅' if syarat else '❌'} {nama}" + (f"  → {bukti}" if bukti else ""))


# ── 0. BENTUK MURNI ──────────────────────────────────────────────────
print("\n══ 0. fungsi murni (tanpa DB) ══")
cek("0a SIDIK_HURUF = 1500", T.SIDIK_HURUF == 1500, str(T.SIDIK_HURUF))
cek("0b _potong ambil 1500 huruf", len(T._potong("a" * 5000)) == 1500,
    str(len(T._potong("a" * 5000))))
cek("0c label_elemen('gap') = 'Gap (celah penelitian)'",
    T.label_elemen('gap') == 'Gap (celah penelitian)', T.label_elemen('gap'))
cek("0d bab_dari_kunci('gap') menyebut 'Pendahuluan'",
    'Pendahuluan' in T.bab_dari_kunci('gap'), T.bab_dari_kunci('gap'))
sk = T._skema_pertanyaan()
cek("0e skema choice punya criteria OBJEK (bukan list)",
    isinstance(sk['masih_sama']['criteria'], dict))
cek("0f skema punya instructions", bool(sk['masih_sama'].get('instructions')))
#  periksa_skema Jev harus menerima skema kita (bentuk sah!)
from app import jev                           # noqa: E402
cek("0g skema LULUS periksa_skema Jev (bentuk sah)",
    jev.periksa_skema(sk) == [], str(jev.periksa_skema(sk)))

# ── 1. BACA/TULIS/BATAL TIKET (DB SAMA dengan aplikasi) ───────────────
print("\n══ 1. baca/tulis/batal tiket ══")
#  ⚠️ `M.SessionLocal` = sesi DB aplikasi (BUKAN `db.SesiLocal` — tak ada).
#  ⚠️ Tabel KonversiNaskah bisa KOSONG di DB uji ⇒ Wulan WAJIB menyiapkan
#     barisnya sendiri (pola 'beres'), kalau tidak semua uji tiket GAGAL PALSU.
sesi_db = M.SessionLocal()
from app.models import KonversiNaskah          # noqa: E402

FID = 81
EMAIL = 'asih.susanti@eduai.test'

u = sesi_db.query(models.User).filter(models.User.email == EMAIL).first()
uid = int(getattr(u, 'id', 0))
print(f"     user uji: {getattr(u, 'email', None)} (id={uid})")

#  bersihkan sisa uji lama + siapkan SATU baris 'beres'
sesi_db.query(KonversiNaskah).filter(
    KonversiNaskah.user_id == uid, KonversiNaskah.file_id == FID).delete()
sesi_db.commit()
baris_uji = KonversiNaskah(user_id=uid, file_id=FID, status='beres',
                           hasil_json='{}')
sesi_db.add(baris_uji)
sesi_db.commit()
print(f"     baris konversi uji dibuat: id={baris_uji.id} status=beres")

db = sesi_db
awal = T.tiket_baca(db, u, FID)
print(f"     tiket awal: {list(awal.keys())}")

#  tulis tiket untuk 2 elemen
TEKS = {'gap': 'BAB I PENDAHULUAN ' + ('x' * 3000),
        'novelty': 'BAB II TINJAUAN ' + ('y' * 3000)}
ada = T.tiket_tulis(db, u, FID, {}, ['gap', 'novelty'], lambda k: TEKS.get(k, ''))
cek("1a tiket_tulis berhasil", ada.get('tersimpan') is True, str(ada))
baca = T.tiket_baca(db, u, FID)
cek("1b tiket 'gap' tersimpan", 'gap' in baca, str(list(baca.keys())))
cek("1c sidik dipotong 1500 huruf",
    len(baca.get('gap', {}).get('sidik', '')) == 1500,
    str(len(baca.get('gap', {}).get('sidik', ''))))
cek("1d tiket simpan wilayah bab", baca.get('gap', {}).get('bab') == 'Pendahuluan ¶4',
    str(baca.get('gap', {}).get('bab')))

# ── 2. JEV BILANG 'SAMA' → LOLOS ─────────────────────────────────────
print("\n══ 2. KEADAAN A: bab diubah TAPI makna tetap → LOLOS ══")
TEKS_BARU_SAMA = {'gap': 'BAB I PENDAHULUAN ' + ('x' * 3000) + ' Kalimat tambahan pendukung.'}


def jev_sama(bahan, skema):
    return {'masih_sama': {'choice': 'sama', 'confidence': 0.9}}


h = T.tiket_periksa(db, u, FID, ['Gap (celah penelitian)'],
                    lambda k: TEKS_BARU_SAMA.get(k, ''), panggil=jev_sama)
cek("2a elemen dilewati (masuk 'lolos')", h['lolos'] == ['Gap (celah penelitian)'],
    str(h['lolos']))
cek("2b elemen DIBUANG dari daftar kurang", h['kurang'] == [], str(h['kurang']))
cek("2c Jev diperiksa 1×", h['diperiksa'] == 1, str(h['diperiksa']))

# ── 3. JEV BILANG 'BEDA' → BATAL ─────────────────────────────────────
print("\n══ 3. KEADAAN B: makna BERUBAH → tiket BATAL ══")


def jev_beda(bahan, skema):
    return {'masih_sama': {'choice': 'beda', 'confidence': 0.9}}


TEKS_BARU_BEDA = {'gap': 'BAB I PENDAHULUAN Fokus baru: membahas hal lain sama sekali.'}
h2 = T.tiket_periksa(db, u, FID, ['Gap (celah penelitian)'],
                     lambda k: TEKS_BARU_BEDA.get(k, ''), panggil=jev_beda)
cek("3a elemen TETAP di daftar kurang", h2['kurang'] == ['Gap (celah penelitian)'],
    str(h2['kurang']))
cek("3b elemen masuk 'batal'", h2['batal'] == ['Gap (celah penelitian)'],
    str(h2['batal']))
cek("3c tiket 'gap' DIHAPUS dari simpanan", 'gap' not in T.tiket_baca(db, u, FID),
    str(list(T.tiket_baca(db, u, FID).keys())))

# ── 4. JEV MATI → BATAL (jangan jadi pintu gratis!) ──────────────────
print("\n══ 4. KEADAAN C: Jev MATI → BATAL (BUKAN lolos) ══")
T.tiket_tulis(db, u, FID, {}, ['gap'], lambda k: TEKS.get(k, ''))


def jev_mati(bahan, skema):
    return None


h3 = T.tiket_periksa(db, u, FID, ['Gap (celah penelitian)'],
                     lambda k: TEKS_BARU_BEDA.get(k, ''), panggil=jev_mati)
cek("4a Jev mati → elemen TETAP kurang", h3['kurang'] == ['Gap (celah penelitian)'],
    str(h3['kurang']))
cek("4b Jev mati → TIDAK masuk 'lolos'", h3['lolos'] == [], str(h3['lolos']))

# ── 5. BAB TIDAK BERUBAH → tiket tetap TANPA panggil Jev (hemat) ────
print("\n══ 5. KEADAAN D: bab TIDAK berubah → hemat, Jev tak dipanggil ══")
T.tiket_tulis(db, u, FID, {}, ['gap'], lambda k: TEKS.get(k, ''))
panggil_ke = {'n': 0}


def jev_hitung(bahan, skema):
    panggil_ke['n'] += 1
    return {'masih_sama': {'choice': 'sama', 'confidence': 0.9}}


h4 = T.tiket_periksa(db, u, FID, ['Gap (celah penelitian)'],
                     lambda k: TEKS.get(k, ''), panggil=jev_hitung)
cek("5a bab sama → lolos", h4['lolos'] == ['Gap (celah penelitian)'], str(h4['lolos']))
cek("5b Jev TIDAK dipanggil (hemat, Rp 0)", panggil_ke['n'] == 0, str(panggil_ke['n']))

# ── 6. GIGI: tiket dimatikan → HARUS GAGAL ───────────────────────────
print("\n══ 6. UJI GIGI: tiket dimatikan ══")
asli_baca = T.tiket_baca
T.tiket_baca = lambda db, u, fid: {}
h5 = T.tiket_periksa(db, u, FID, ['Gap (celah penelitian)'],
                     lambda k: TEKS_BARU_SAMA.get(k, ''), panggil=jev_sama)
T.tiket_baca = asli_baca
cek("6a tiket mati → elemen TETAP kurang (bergigi)",
    h5['kurang'] == ['Gap (celah penelitian)'], str(h5['kurang']))
cek("6b tiket mati → tidak ada yang lolos", h5['lolos'] == [], str(h5['lolos']))

# ── 7. elemen TANPA tiket → tetap ditanyakan ─────────────────────────
print("\n══ 7. elemen tanpa tiket → tetap ditanyakan ══")
#  ⚠️ Untuk membuktikan ini, tiket 'hook' SENGAJA TIDAK PERNAH dibuat
#     (bukan 'novelty' — novelty masih bertiket dari langkah 5).
h6 = T.tiket_periksa(db, u, FID, ['Hook (pembuka)'],
                     lambda k: TEKS.get(k, ''), panggil=jev_sama)
cek("7a elemen TANPA tiket tetap di daftar kurang",
    h6['kurang'] == ['Hook (pembuka)'], str(h6['kurang']))
cek("7b Jev tidak dipanggil untuk elemen tanpa tiket",
    h6['diperiksa'] == 0, str(h6['diperiksa']))
print(f"     tiket tersimpan: {list(T.tiket_baca(db, u, FID).keys())}")

db.close()

print()
print("═" * 62)
print(f"  HASIL: {len(lulus)} LULUS / {len(gagal)} GAGAL")
if gagal:
    print("  GAGAL: " + ", ".join(gagal))
print("═" * 62)
sys.exit(1 if gagal else 0)
