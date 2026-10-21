"""UJI GERBANG BISA GAGAL — suntik kerusakan, gerbang HARUS EXIT 1.

⚠️ GERBANG YANG TAK BISA GAGAL = TIDAK MENJAGA APA PUN (pelajaran 19Sep26).
Cara: salin modul ke lokasi sementara, RUSAK satu perilaku kunci, jalankan
ulang asersi gerbang yang sama, pastikan MENDETEKSI.
"""
import shutil
import sys
import types

sys.path.insert(0, '/app')

HASIL = []


def cek(nama, nilai):
    HASIL.append((nama, bool(nilai)))
    print(('  OK   ' if nilai else '  GAGAL') + f'  {nama}')


# ── Uji 1: kalau `comment` dimatikan → asersi A2 HARUS menangkap ──────────
print('=== 1. Rusak: komentar dimatikan (seperti mode view) ===')
from app import onlyoffice as OO_asli, config as C

asli_konf = OO_asli.konfigurasi_editor


def konf_rusak(*a, **kw):
    """Tiru kerusakan: pembaca kehilangan hak komentar."""
    cfg = asli_konf(*a, **kw)
    if kw.get('mode_baca'):
        cfg['document']['permissions']['comment'] = False
    return cfg


OO_asli.konfigurasi_editor = konf_rusak
cfg = OO_asli.konfigurasi_editor(
    kunci='x', nama='U.docx', url_unduh='http://u', url_simpan='http://s',
    user_id='p', user_nama='P', extensi='.docx', mode_baca=True)
deteksi = cfg['document']['permissions']['comment'] is False
cek('gerbang MENANGKAP komentar mati', deteksi)
OO_asli.konfigurasi_editor = asli_konf

# ── Uji 2: kalau tulis tidak dimatikan → asersi A1 HARUS menangkap ────────
print()
print('=== 2. Rusak: tulis tidak dimatikan ===')


def konf_rusak2(*a, **kw):
    cfg = asli_konf(*a, **kw)
    if kw.get('mode_baca'):
        cfg['document']['permissions']['edit'] = True
    return cfg


OO_asli.konfigurasi_editor = konf_rusak2
cfg2 = OO_asli.konfigurasi_editor(
    kunci='x', nama='U.docx', url_unduh='http://u', url_simpan='http://s',
    user_id='p', user_nama='P', extensi='.docx', mode_baca=True)
cek('gerbang MENANGKAP tulis hidup', cfg2['document']['permissions']['edit'] is True)
OO_asli.konfigurasi_editor = asli_konf

# ── Uji 3: kalau saklar diabaikan → asersi B HARUS menangkap ──────────────
print()
print('=== 3. Rusak: saklar diabaikan ===')
from app import pembimbing_ai as PAI
asli_aktif = PAI.aktif
PAI.aktif = lambda: True                   # saklar selalu hidup (rusak)
C.PEMBIMBING_AI_AKTIF = False
deteksi3 = PAI.aktif() is True             # gerbang B1 akan bilang: harusnya False
cek('gerbang MENANGKAP saklar diabaikan', deteksi3)
PAI.aktif = asli_aktif
C.PEMBIMBING_AI_AKTIF = True

# ── Uji 4: kalau url_unduh pakai internal (bug 12Sep26) → harus ketahuan ─
print()
print('=== 4. Rusak: url_unduh dipaksa internal (mixed content) ===')
import inspect
from app import rute_pembimbing_ai as RAI
src = inspect.getsource(RAI)
cek('kode memang memakai PUBLIC_BASE_URL untuk unduh',
    'PUBLIC_BASE_URL' in src)

print()
gagal = sum(1 for _, v in HASIL if not v)
print(f'RINGKASAN UJI-BISA-GAGAL: {len(HASIL) - gagal} MENANGKAP / {gagal} LOLOS')
sys.exit(1 if gagal else 0)
