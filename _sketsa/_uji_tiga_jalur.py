"""UJI 2 ARAH — TIGA JALUR REVISI PER-BAB (30Sep26). Salinan saja, produksi tak disentuh.

SEHAT (harus LULUS):
  S1 hitung jalur 3  → bab='BAB III' = 1 pembuka + 2 sub-bab = 3 Token (flat)
  S2 hitung jalur 1  → lingkup='pembuka' = 1 Token, panjang hanya pembuka
  S3 hitung jalur 2  → babs=['3.1','3.2'] = 2 Token
  S4 unit ambil_pembuka → isi berhenti SEBELUM 3.1; sebelum+isi+sesudah = utuh
  S5 revisi jalur 3  → kuota terpotong TEPAT 3 (rumus AI = 5, bukti FLAT menang)
  S6 revisi jalur 1  → 1 Token; pembuka berubah, sub-bab 3.1/3.2 TIDAK tersentuh
  S7 revisi jalur 2  → 2 Token; dua-duanya berubah; versi_dokumen +2 baris

DIRUSAK (harus GAGAL / tolak jujur):
  F1 hitung+revisi jalur 1 label palsu 'BAB IX' → 400, kuota TIDAK dipotong
  F2 babs dengan label hilang '9.9' → 400, kuota TIDAK dipotong
  F3 pengali > 1 (komentar 'ubah alur') → RUMUS menang, bukan flat 1

PAKAI:
  docker exec -e APP_ROOT=/tmp/rg -e EDUAI_DATA_DIR=/tmp/rg_data \
      -e EDUAI_UPLOAD_DIR=/tmp/rg_up eduai-app python3 /tmp/_uji_tiga_jalur.py
"""
import os
import re
import sys

APP_ROOT = os.environ.get('APP_ROOT', '/app')
sys.path.insert(0, APP_ROOT)

_DATA = os.environ.get('EDUAI_DATA_DIR', '')
if 'rg' not in _DATA and 'uji' not in _DATA and 'tj' not in _DATA:
    print(f'STOP: EDUAI_DATA_DIR={_DATA!r} bukan salinan uji.')
    sys.exit(2)

GAGAL = []


def cek(nama, ok, info=''):
    print(('  LULUS  ' if ok else '  GAGAL  ') + nama +
          (' → ' + str(info)[:260] if info != '' else ''))
    if not ok:
        GAGAL.append(nama)


# ── umum ─────────────────────────────────────────────────────────────────
from fastapi.testclient import TestClient                                # noqa: E402
from app.main import app as APP_UTAMA                                    # noqa: E402
from app.auth import buat_token                                          # noqa: E402
from app.config import SESSION_COOKIE                                    # noqa: E402
import app.ai as AI                                                      # noqa: E402
from app.ai import _teks_dari_body, ringkasan_kuota                       # noqa: E402
from app.versi import (ambil_bab, ambil_pembuka, deteksi_bab,             # noqa: E402
                       _deteksi_bagian, harga_flat)
from app.state import petakan, buang_daftar_isi                          # noqa: E402
from app.models import User                                              # noqa: E402
from sqlalchemy import create_engine                                     # noqa: E402
from sqlalchemy.orm import sessionmaker                                  # noqa: E402

_klien = TestClient(APP_UTAMA)
_cookie = {SESSION_COOKIE: buat_token(7)}
_URL = '/api/ai/v1'

#  🔎 SPY (diagnosa S7): cetak naskah yang benar-benar diterima pipa.
import app.pipa as _PIPA                                     # noqa: E402
_asli_periksa = _PIPA.periksa


def _spy_periksa(jawab, naskah, intent=''):
    import re as _re
    m = _re.search(r'\[K1-KUTIP-ASLI\]\n(.+?)\n\[K1-GANTI-JADI\]', jawab or '',
                   _re.S)
    k = (m.group(1) if m else '').strip()
    print(f'  [spy pipa] naskah={len(naskah)} kutip∈naskah={k in naskah} '
          f'awal={naskah[:70]!r}')
    return _asli_periksa(jawab, naskah, intent)


_PIPA.periksa = _spy_periksa
_db = sessionmaker(bind=create_engine('sqlite:///' + os.path.join(_DATA, 'eduai.db')))()
_u = _db.query(User).filter(User.id == 7).first()
NASKAH, _fb, _err = _teks_dari_body(_db, _u, {'file_id': 78})
if _err:
    print('berkas 78 tidak terbaca:', _err)
    sys.exit(3)
print(f'naskah asli: {len(NASKAH)} kar')
_UTUH = [NASKAH]          #  utk stub: tiru sumber naskah_dikirim produk


def sisa():
    _db.expire_all()
    return (ringkasan_kuota(_db, _u).get('revisi') or {}).get('sisa', 0)


def revisi(body):
    """POST /v1/revisi mode tunggu; bersihkan rate-limit in-process dulu
    (rate limit di memori PER PROSES — TestClient = proses yang sama)."""
    AI._ratelimit.clear()
    _KOM[0] = body.get('komentar') or []          #  LIST — utk _boleh_konteks
    return _klien.post(f'{_URL}/revisi', json={'tunggu': '1', **body},
                       cookies=_cookie)


# ── STUB AI (Rp 0): token DIBESARKAN supaya beda jelas dari harga flat ──
# rumus lama = ceil((40000+6000)/10000) = 5  →  flat 1/2/3 harus menang di
# jalur pengali=1, dan KALAH (rumus ×pengali menang) saat pengali > 1.
_TARGETS = []
_KOM = ['']            #  komentar siap pakai — ditiru dari pemakaian asli


def _komentar_siap(body):
    """`baris_komentar` persis pola ai.py:2084 — string bernomor."""
    k = body.get('komentar') or []
    return '\n'.join(f'{i + 1}. {x.strip()}'
                    for i, x in enumerate(k) if isinstance(x, str))


def _label_dari_target(target):
    """Label peta untuk suatu potongan (entri dgn isi == target persis)."""
    for e in (_deteksi_bagian(_UTUH[0]) + deteksi_bab(_UTUH[0])):
        if e.get('isi') == target:
            return str(e.get('label') or '')
    return ''


def _kutip_untuk(target, user_msg):
    """Pilih kutip K1 — TIRU alur produk menentukan `naskah_dikirim`
    (terbukti spy pipa 30Sep26):

    · sub-bab + komentar boleh-konteks → produk pakai `petakan().isi_teks`
      (S7: region versi 'Gambar 3.1' ≠ isi_teks '3.1.' → pipa tolak!)
    · sub-bab + konteks mati ('ubah alur') / bab besar / pembuka →
      produk pakai region `ambil_bab` / `ambil_pembuka` (= target).
    · peta paragraf aktif (komentar spesifik) → 1 paragraf terpilih.
    """
    label = _label_dari_target(target)
    sumber = target
    if '.' in label:
        try:
            if AI._boleh_konteks(_KOM[0]):
                from app.state import petakan, buang_daftar_isi
                entri = [e.get('isi_teks', '') for e in
                         petakan(buang_daftar_isi(_UTUH[0]))
                         if e.get('isi_teks')]
                if entri:
                    def _rasio(t):
                        b = [x.strip() for x in t.split('\n')
                             if len(x.strip()) > 30]
                        return (sum(1 for x in b if x in user_msg) / len(b)
                                if b else 0.0)
                    sumber = max(entri, key=_rasio)
        except Exception as _e:                              # noqa: BLE001
            print('  [dbg sumber]', _e)
    #  peta paragraf (ai.py:2386) — kalau aktif & ada di prompt
    try:
        from app.konteks import (petakan_paragraf, pilih_paragraf,
                                 isi_paragraf)
        par = petakan_paragraf(sumber)
        if len(par) >= 3:
            idx = pilih_paragraf(par, _komentar_siap(
                {'komentar': _KOM[0]}) or '')
            if idx is not None:
                p = (isi_paragraf(par, idx) or '').strip()
                if p and len(p) >= 40 and p in user_msg:
                    return p
    except Exception as _e:                                  # noqa: BLE001
        print('  [dbg peta-par gagal]', _e)
    #  baris prosa dari SUMBER yang benar-benar ada di prompt
    baris = [l.strip() for l in sumber.split('\n') if len(l.strip()) > 30]
    cocok = [l for l in baris if l in user_msg]
    if cocok:
        return max(cocok, key=len)
    print(f'  [dbg tak ada baris] label={label!r} sumber={len(sumber)} kar '
          f'baris={len(baris)} (fallback: baris terpanjang sumber)')
    return max(baris, key=len) if baris else sumber[:400]


def _target_aktif(user_msg):
    """Pilih blok target yang paling LENGKAP ada di prompt.

    Pipeline mengirim blok yang sedang direvisi UTUH + tetangga TERPOTONG →
    rasio (baris cocok / total baris prosa) blok aktif ≈ 1.0, tetangga < 1.
    Tanpa ini, kutip bisa salah blok (JALUR 2: 3.1 vs 3.2 → pipa menolak
    'bagian yang ditunjuk tidak ditemukan'). Tahan retry (tak bergantung
    urutan panggilan)."""
    terbaik, skor_t = '', -1.0
    for t in _TARGETS:
        baris = [l.strip() for l in t.split('\n') if len(l.strip()) > 30]
        if not baris:
            continue
        n = sum(1 for l in baris if l in user_msg)
        rasio = n / len(baris)
        print(f'  [dbg target] total={len(baris)} cocok={n} rasio={rasio:.2f} '
              f'awal={t[:40]!r}')
        if rasio > skor_t:
            skor_t, terbaik = rasio, t
    return terbaik or (_TARGETS[0] if _TARGETS else '')


def _kutip_untuk_lama_dihapus():       #  sudah digantikan def di atas
    raise NotImplementedError


async def _stubs_ai(user_msg, timeout, system=None, gambar=None):
    tgt = _target_aktif(user_msg)
    par = _kutip_untuk(tgt, user_msg)
    jawab = ('[PROFIL] Paradigma=kuantitatif; Desain=survei\n\n'
             '[K1-KUTIP-ASLI]\n' + par + '\n[K1-GANTI-JADI]\n' + par +
             ' (Paragraf ini sudah diperbarui.)\n')
    return jawab, {'model': 'uji-stub-tiga-jalur', 'token_in': 40000,
                   'token_out': 6000}


AI._panggil_router = _stubs_ai

_, isi3, _ = ambil_bab(NASKAH, 'BAB III')
_, isi_pem, _ = ambil_pembuka(NASKAH, 'BAB III')
_, isi31, _ = ambil_bab(NASKAH, '3.1')
_, isi32, _ = ambil_bab(NASKAH, '3.2')

# ═══ SEHAT ══════════════════════════════════════════════════════════════
print('=== S1–S3: /v1/hitung tiga jalur ===')
r = _klien.post(f'{_URL}/hitung', json={'file_id': 78, 'bab': 'BAB III'},
                cookies=_cookie)
d = r.json()
n_sub = sum(1 for b in _deteksi_bagian(NASKAH)
            if 'BAB III' in str(b.get('label')) or str(b.get('label')).startswith('3.'))
cek('S1 jalur 3: 1 pembuka + per sub-bab (flat)',
    r.status_code == 200 and d.get('revisi_dibutuhkan') == 1 + n_sub,
    f"revisi_dibutuhkan={d.get('revisi_dibutuhkan')} n_sub={n_sub} "
    f"bagian={d.get('bagian')} pesan={d.get('pesan')}")
cek('S1 pesan menyebut 1 pembuka + N sub-bab',
    '1 pembuka' in str(d.get('pesan')), d.get('pesan'))

r = _klien.post(f'{_URL}/hitung',
                json={'file_id': 78, 'bab': 'BAB III', 'lingkup': 'pembuka'},
                cookies=_cookie)
d1 = r.json()
cek('S2 jalur 1: pembuka = 1 Token, panjang hanya pembuka',
    r.status_code == 200 and d1.get('revisi_dibutuhkan') == 1
    and d1.get('panjang') == len(isi_pem) and d1.get('panjang') < len(isi3),
    f"tok={d1.get('revisi_dibutuhkan')} panjang={d1.get('panjang')} "
    f"(pem={len(isi_pem)} bab3={len(isi3)}) pesan={d1.get('pesan')}")

r = _klien.post(f'{_URL}/hitung',
                json={'file_id': 78, 'babs': ['3.1', '3.2']}, cookies=_cookie)
d2 = r.json()
cek('S3 jalur 2: 2 sub-bab = 2 Token',
    r.status_code == 200 and d2.get('revisi_dibutuhkan') == 2
    and d2.get('panjang') == len('\n\n'.join([isi31, isi32])),
    f"tok={d2.get('revisi_dibutuhkan')} panjang={d2.get('panjang')} "
    f"(harap {len(chr(10).join([isi31, isi32])) + 2} utk gabungan "
    f"+2 kar pemisah) pesan={d2.get('pesan')}")

print('=== S4: unit ambil_pembuka ===')
sblm, isi_p, sesudh = ambil_pembuka(NASKAH, 'BAB III')
_peta = petakan(buang_daftar_isi(NASKAH))
_isi31 = next((str(x.get('isi_teks') or '') for x in _peta
               if str(x.get('section_id') or '') == '3.1'), '')
_pos31_pet = NASKAH.find(_isi31) if _isi31 else -1
cek('S4 pembuka berhenti TEPAT di awal isi sub-bab 3.1 menurut PETAKAN '
    '(sumber kebenaran — deteksi versi menangkap "Gambar 3.1" = salah)',
    bool(isi_p) and _pos31_pet > 0 and len(sblm) + len(isi_p) == _pos31_pet,
    f'batas={len(sblm) + len(isi_p)} posisi_petakan={_pos31_pet} '
    f'panjang_pembuka={len(isi_p)}')
cek('S4 isi sub-bab 3.1 TIDAK ikut pembuka (jalur 1 tak menyentuh sub-bab)',
    bool(_isi31) and _isi31[:80] not in isi_p and '3.2' not in isi_p,
    f'isi={len(isi_p)} kar')
cek('S4 sebelum+isi+sesudah = naskah utuh (tak merusak dokumen)',
    (sblm + isi_p + sesudh) == NASKAH,
    f'sebelum={len(sblm)} isi={len(isi_p)} sesudah={len(sesudh)}')

# ═══ DIRUSAK (tolak jujur, kuota tak tersentuh) ══════════════════════════
print('=== F1: jalur 1 label palsu ===')
s0 = sisa()
r = _klien.post(f'{_URL}/hitung',
                json={'file_id': 78, 'bab': 'BAB IX', 'lingkup': 'pembuka'},
                cookies=_cookie)
cek('F1a hitung label palsu = 400 (bukan harga 1 utk seluruh dokumen)',
    r.status_code == 400, f"kode={r.status_code} {r.text[:180]}")
r = revisi({'file_id': 78, 'bab': 'BAB IX', 'lingkup': 'pembuka',
            'komentar': ['perbaiki paragraf pembuka']})
cek('F1b revisi label palsu = 400 + kuota TIDAK dipotong',
    r.status_code == 400 and sisa() == s0,
    f'kode={r.status_code} sisa {s0} → {sisa()}')

print('=== F2: jalur 2 label hilang ===')
r = _klien.post(f'{_URL}/hitung',
                json={'file_id': 78, 'babs': ['3.1', '9.9']}, cookies=_cookie)
cek('F2a hitung babs label hilang = 400', r.status_code == 400,
    f'kode={r.status_code} {r.text[:180]}')
s0 = sisa()
r = revisi({'file_id': 78, 'babs': ['3.1', '9.9'], 'setuju_bagian': True,
            'komentar': ['perbaiki paragraf']})
cek('F2b revisi babs label hilang = 400 + kuota TIDAK dipotong',
    r.status_code == 400 and sisa() == s0,
    f'kode={r.status_code} sisa {s0} → {sisa()}')

# ═══ SEHAT: revisi ujung-ke-ujung (stub AI, rumus = 5) ══════════════════
print('=== S5: revisi jalur 3 — FLAT menang atas rumus ===')
_TARGETS[:] = [isi3]
s0 = sisa()
r = revisi({'file_id': 78, 'bab': 'BAB III',
            'komentar': ['perbaiki paragraf pembuka dan metode']})
d = r.json() if r.status_code == 200 else {}
cek('S5 jalur 3 sukses', r.status_code == 200 and not d.get('gagal'),
    f"kode={r.status_code} {r.text[:200]}")
cek('S5 kuota terpotong TEPAT 3 (bukan rumus 5) → harga flat menang',
    sisa() == s0 - 3, f'sisa {s0} → {sisa()} (harap -3; rumus = 5)')

print('=== S6: revisi jalur 1 — hanya pembuka, sub-bab tak tersentuh ===')
_TARGETS[:] = [isi_pem]
s0 = sisa()
r = revisi({'file_id': 78, 'bab': 'BAB III', 'lingkup': 'pembuka',
            'komentar': ['perbaiki paragraf pembuka']})
d = r.json() if r.status_code == 200 else {}
cek('S6 jalur 1 sukses + kuota = 1 Token',
    r.status_code == 200 and not d.get('gagal') and sisa() == s0 - 1,
    f"kode={r.status_code} sisa {s0} → {sisa()} {r.text[:180]}")
from sqlalchemy import text as _sql                                    # noqa: E402
_row = _db.execute(_sql(
    "select isi from versi_dokumen where file_id=78 "
    "order by id desc limit 1")).fetchone()
isi_versi = _row[0] if _row else ''
_, _, ses_p = ambil_pembuka(NASKAH, 'BAB III')
cek('S6 sesudah pembuka (sub-bab 3.1/3.2) TIDAK berubah di versi',
    isi_versi.endswith(ses_p) if isi_versi else False,
    f'versi={len(isi_versi)} utuh={len(NASKAH)} sesudah={len(ses_p)}')
cek('S6 isi sub-bab 3.1 asli (petakan) TERSIMPAN UTUH di versi — '
    'bukti jalur 1 tak menyentuh sub-bab',
    bool(isi_versi) and bool(_isi31) and _isi31[:80] in isi_versi,
    f'isi3.1 ada={bool(_isi31) and _isi31[:80] in isi_versi}')
cek('S6 pembuka ikut terganti (hasil AI masuk)',
    isi_versi and isi_pem not in isi_versi and 'sudah diperbarui' in isi_versi,
    '' if isi_versi else 'versi_dokumen kosong')

print('=== S7: revisi jalur 2 — dua sub-bab, 2 Token ===')
_TARGETS[:] = [isi31, isi32]
s0 = sisa()
n_versi0 = _db.execute(_sql(
    "select count(*) from versi_dokumen where file_id=78")).scalar()
r = revisi({'file_id': 78, 'babs': ['3.1', '3.2'], 'setuju_bagian': True,
            'komentar': ['perbaiki paragraf di bagian ini']})
d = r.json() if r.status_code == 200 else {}
cek('S7 jalur 2 sukses + kuota TEPAT 2 Token',
    r.status_code == 200 and not d.get('gagal') and sisa() == s0 - 2,
    f"kode={r.status_code} sisa {s0} → {sisa()} {r.text[:200]}")
cek('S7 respons mengembalikan babs', d.get('babs') == ['3.1', '3.2'],
    d.get('babs'))
n_versi1 = _db.execute(_sql(
    "select count(*) from versi_dokumen where file_id=78")).scalar()
cek('S7 versi_dokumen bertambah 2 (satu per sub-bab)',
    n_versi1 == n_versi0 + 2, f'{n_versi0} → {n_versi1}')

# ═══ DIRUSAK: pengali > 1 → RUMUS menang, bukan flat ════════════════════
print('=== F3: pengali > 1 (komentar "ubah alur") ===')
_TARGETS[:] = [isi31]
s0 = sisa()
r = revisi({'file_id': 78, 'bab': '3.1',
            'komentar': ['ubah alur paragraf di bagian ini']})
d = r.json() if r.status_code == 200 else {}
terpotong = s0 - sisa()
cek('F3 revisi jalan tapi terpotong LEBIH dari harga flat 1 '
    '(rumus ÷10.000 × pengali menang)',
    r.status_code == 200 and not d.get('gagal') and terpotong > 1,
    f"kode={r.status_code} terpotong={terpotong} (flat=1, rumus=5, "
    f"pengali bisa ×4) {r.text[:160]}")

print(f'\nRINGKAS: {len(GAGAL)} GAGAL ' +
      (', '.join(GAGAL) if GAGAL else '(semua lulus)'))
sys.exit(1 if GAGAL else 0)
