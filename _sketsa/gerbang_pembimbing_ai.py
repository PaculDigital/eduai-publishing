"""GERBANG PEMBIMBING AI — 03Okt26.

Membuktikan DUA arah:
  (A) FITUR BARU bekerja & pagarnya BERGIGI (bukan tampilan saja)
  (B) YANG LAMA MASIH JALAN (pagar 4 rencana: "yang lama masih 100% jalan")

Dijalankan DI DALAM container:
  docker exec -e PYTHONPATH=/app eduai-app python3 /app/_sketsa/gerbang_pembimbing_ai.py
"""
from __future__ import annotations

import inspect
import sys

sys.path.insert(0, '/app')

from app import pembimbing_ai as PAI
from app import rute_pembimbing_ai as RAI
from app import onlyoffice as OO

LULUS = GAGAL = 0
JEJAK = []


def _tanpa_komentar(src: str) -> str:
    """Buang komentar & docstring supaya asersi membaca KODE, bukan tulisan.

    ⚠️ KENAPA: asersi `'tulis_docx' not in sumber` GAGAL PALSU karena kata itu
    ada di komentar penjelasan. Uji yang membaca komentar = uji yang tidak
    menguji apa pun.
    """
    import io
    import tokenize
    hasil = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type in (tokenize.COMMENT, tokenize.STRING):
                continue
            hasil.append(tok.string)
    except Exception:                                          # noqa: BLE001
        return src                      # gagal urai → jangan menipu diri
    return ' '.join(hasil)


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}')
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama} {catatan}')


# ══════════════════════════════════════════════════════════════════════════
print('=== A. HAK AKSES: TULIS MATI, KOMENTAR HIDUP (inti fitur) ===')
# ══════════════════════════════════════════════════════════════════════════
cfg_baca = OO.konfigurasi_editor(
    kunci='uji-baca', nama='UJI.docx', url_unduh='http://x/unduh',
    url_simpan='http://x/simpan', user_id='pembimbing', user_nama='Pembimbing',
    extensi='.docx', mode_baca=True)
p = cfg_baca['document']['permissions']

cek('A1 tulis MATI (edit=False)', p['edit'] is False, f"edit={p['edit']}")
cek('A2 komentar HIDUP', p['comment'] is True, f"comment={p['comment']}")
cek('A3 sorot/usul HIDUP (review)', p['review'] is True)
cek('A4 unduh HIDUP', p['download'] is True)
cek('A5 isian form MATI', p['fillForms'] is False)
cek('A6 ubah filter MATI', p['modifyFilter'] is False)
cek('A7 control content MATI', p['modifyContentControl'] is False)
cek('A8 editor TETAP mode edit (bukan view)',
    cfg_baca['editorConfig']['mode'] == 'edit',
    f"mode={cfg_baca['editorConfig']['mode']}")
cek('A9 url_simpan TETAP dikirim (jangan kosong)',
    bool(cfg_baca['editorConfig'].get('callbackUrl')))

#  A10 — pemilik HARUS tetap bisa menulis (yang lama tidak rusak)
cfg_tulis = OO.konfigurasi_editor(
    kunci='uji-tulis', nama='UJI.docx', url_unduh='http://x/unduh',
    url_simpan='http://x/simpan', user_id='1', user_nama='Mahasiswa',
    extensi='.docx')
pt = cfg_tulis['document']['permissions']
cek('A10 pemilik tetap bisa MENULIS', pt['edit'] is True)
cek('A11 pemilik default tidak berubah (mode_baca opsional)',
    'mode_baca' in inspect.signature(OO.konfigurasi_editor).parameters
    and inspect.signature(OO.konfigurasi_editor).parameters['mode_baca'].default is False)
cek('A12 pemilik tetap bisa isian form', pt['fillForms'] is True)

# ══════════════════════════════════════════════════════════════════════════
print()
print('=== B. SAKLAR (titik henti darurat) ===')
# ══════════════════════════════════════════════════════════════════════════
from app import config as C
lama = C.PEMBIMBING_AI_AKTIF
C.PEMBIMBING_AI_AKTIF = False
cek('B1 saklar mati → aktif() False', PAI.aktif() is False)
cek('B2 saklar mati → boleh_pakai nolak (sebab saklar_mati)',
    PAI.boleh_pakai(None, None)[1] == 'saklar_mati')
C.PEMBIMBING_AI_AKTIF = True
cek('B3 saklar hidup → aktif() True', PAI.aktif() is True)
cek('B4 saklar dibaca ULANG (tanpa restart)',
    'PEMBIMBING_AI_AKTIF' in inspect.getsource(PAI.aktif))
C.PEMBIMBING_AI_AKTIF = lama

# ══════════════════════════════════════════════════════════════════════════
print()
print('=== C. GERBANG DOMPET — satu dompet, dua peran (D3) ===')
# ══════════════════════════════════════════════════════════════════════════
from app.models import SessionLocal, User   # noqa: E402
db = SessionLocal()
try:
    #  Paket gratis + saldo kosong → ditolak
    kelas = _u_kosong = None
    semua = db.query(User).limit(20).all()
    cek('C1 ada user untuk diuji', len(semua) > 0)
    if semua:
        u = semua[0]
        boleh, sebab = PAI.boleh_pakai(db, u)
        cek('C2 gerbang mengembalikan (boleh, sebab)',
            isinstance(boleh, bool) and isinstance(sebab, str),
            f'({boleh!r}, {sebab!r})')
        print(f'         contoh: paket={u.paket or "gratis"} role={u.role} '
              f'→ boleh={boleh} sebab={sebab}')
    cek('C3 pemakai None → belum_akun',
        PAI.boleh_pakai(db, None)[1] == 'belum_akun')

    #  Pemotongan & pengembalian memakai mesin yang SAMA (bukan jalur kedua)
    src = inspect.getsource(PAI.periksa)
    cek('C4 potong kuota lewat kuota.cek_dan_potong', 'cek_dan_potong' in src)
    cek('C5 gagal → kembalikan lewat saldo.kembalikan',
        'S.kembalikan' in src or 'kembalikan(' in src)
    cek('C6 TIDAK memakai jalur AI kedua (tetap _panggil_router)',
        '_panggil_router' in src)
finally:
    db.close()

# ══════════════════════════════════════════════════════════════════════════
print()
print('=== D. PAGAR DI SERVER (bukan tampilan) ===')
# ══════════════════════════════════════════════════════════════════════════
src_r = inspect.getsource(RAI)
cek('D1 token diperiksa (cari_dari_token)', 'cari_dari_token' in src_r)
cek('D2 berkas diperiksa milik bimbingan', '_berkas_sah' in src_r)

#  ⚠️ PELAJARAN 03Okt26: asersi `'tulis_docx' not in sumber` GAGAL PALSU —
#  kata itu cuma muncul di KOMENTAR penjelasan, bukan di kode. Uji WAJIB
#  membaca KODE, bukan komentar. Cara: buang komentar & docstring dulu.
_kode_r = _tanpa_komentar(src_r)
cek('D3 rute TIDAK menulis berkas (nol penulisan di KODE)',
    not any(x in _kode_r for x in ('shutil', 'open(', 'tulis_docx',
                                   '.write_text', '.write_bytes')))
cek('D4 halaman baca memakai mode_baca=True', 'mode_baca=True' in src_r)
cek('D5 url_unduh publik (mixed content 12Sep26)', 'PUBLIC_BASE_URL' in src_r)
cek('D6 url_simpan internal', '_base_internal' in src_r)

# ══════════════════════════════════════════════════════════════════════════
print()
print('=== E. YANG LAMA MASIH JALAN (pagar 4 → harus BERGIGI) ===')
# ══════════════════════════════════════════════════════════════════════════
from app import rute_pembimbing as RP
from app import ai as AI
from app import onlyoffice as OO2

#  E1 — halaman tinjau masih ada & masih merender
src_p = inspect.getsource(RP.halaman_tinjau)
cek('E1 halaman tinjau hidup', "TemplateResponse('tinjau.html'" in src_p)
cek('E2 halaman tinjau kirim ai_aktif', "'ai_aktif'" in src_p)

#  E3 — tiang T1: halaman tinjau HANYA-BACA.
#  ⚠️ KOREKSI UJI 03Okt26: asersi lama (`tidak impor ai.py`) SALAH UJI.
#     `rute_pembimbing.py` memang SUDAH mengimpor `ai` sejak 24Sep26 untuk
#     `_teks_dari_berkas` (MEMBACA berkas — bukan jalur AI kedua). Yang
#     penting bukan "ada impor", melainkan: (a) TIDAK memanggil model, dan
#     (b) TIDAK menulis naskah.
_kode_p = _tanpa_komentar(inspect.getsource(RP))
_panggil_model = any(x in _kode_p for x in (
    '_panggil_router', '_panggil_9router', '_panggil_openrouter',
    '_revisi_dengan_failover'))
cek('E3a halaman tinjau TIDAK memanggil model AI', not _panggil_model)
_tulis = any(x in _kode_p for x in ('shutil', '.write_text', '.write_bytes',
                                    'tulis_docx', 'simpan_versi'))
cek('E3b halaman tinjau TIDAK menulis naskah/versi', not _tulis)

#  E4 — pencatatan manual masih jalan
cek('E4 catat manual masih ada', hasattr(RP, 'tambah_catatan'))

#  E5 — jalur revisi AI mahasiswa TIDAK berubah tanda tangannya
cek('E5 /v1/revisi masih ada', hasattr(AI, 'ai_revisi'))

#  E6 — _panggil_router tanda tangannya TIDAK diubah (dipakai bersama)
sig = inspect.signature(AI._panggil_router)
cek('E6 _panggil_router tanda tangan sama',
    list(sig.parameters)[:3] == ['user_msg', 'timeout', 'system'],
    f'{list(sig.parameters)}')
cek('E7 _panggil_router punya parameter system', 'system' in sig.parameters)

#  E8 — editor mahasiswa TIDAK berubah perilakunya
cek('E8 editor mahasiswa = mode_baca default False',
    inspect.signature(OO2.konfigurasi_editor).parameters['mode_baca'].default is False)

#  E9 — tabel yang dipakai fitur ini SUDAH ADA (nol tabel baru)
from app.models import CatatanPembimbing
cek('E9 pakai tabel catatan_pembimbing yang ADA',
    CatatanPembimbing.__tablename__ == 'catatan_pembimbing')

# ══════════════════════════════════════════════════════════════════════════
print()
print('=== F. TIDAK ADA TABEL / DOMPET / JALUR BARU ===')
# ══════════════════════════════════════════════════════════════════════════
from app import models as M
nama_kelas = [c.__name__ for c in M.Base.__subclasses__()]
cek('F1 tidak ada kelas model baru (PembimbingAI dll)',
    not any('PembimbingAi' in n or 'PembimbingAI' in n for n in nama_kelas),
    f'{nama_kelas}')

print()
print(f'RINGKASAN GERBANG PEMBIMBING AI: {LULUS} LULUS / {GAGAL} GAGAL')
sys.exit(1 if GAGAL else 0)
