"""GERBANG SETELAN PRODUKSI — alat uji WAJIB pakai setelan yang SAMA.

KENAPA GERBANG INI ADA (kejujuran, bukan pembelaan):
    15 Okt 2026 Wulan mengukur MUTU revisi lalu melapor "hasilnya jelek" —
    padahal ALAT UKURNYA yang rusak. `_hakim_mentah.py` ditulis 24 Sep,
    SEBELUM keputusan `enable_thinking: False` (29 Sep), dan tidak ikut
    diperbarui. Akibatnya AI BERPIKIR → jatah token habis → `content` KOSONG
    → hakim menilai `A=? B=? C=? D=?` → Wulan menyimpulkan "mutu POTONG buruk".

    Yang membuat berhenti bukan penjelasan, tapi GERBANG YANG BISA GAGAL.
    (Pelajaran yang sama dari ikon: aturan tertulis saja TIDAK cukup.)

CARA KERJA
    Cari setiap berkas yang MENYUSUN payload `chat/completions` SENDIRI
    (bukan lewat `app.ai`), lalu periksa:
      G1  ada `enable_thinking`?        (setelan 29Sep26: WAJIB ada)
      G2  berkas PRODUKSI (`app/*.py`) WAJIB `enable_thinking: False`
      G3  alat uji di ROOT wajib punya penanda setelan-produksi
      G4  pengecualian wajib DIDAFTARKAN di DAFTAR_KECUALI (jujur, bukan lolos)

PAKAI
    python3 _gerbang_setelan_produksi.py          # periksa semua
    python3 _gerbang_setelan_produksi.py --gigi   # uji gerbang BISA GAGAL

EXIT 0 = sehat · EXIT 1 = ada yang lupa setelan produksi
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

AKAR = Path(__file__).resolve().parent

#  ── BERKAS YANG MEMANG BOLEH TANPA `enable_thinking` ─────────────────────
#  Setiap pengecualian WAJIB punya ALASAN. Kalau tidak, dia cuma lubang.
#  ⚠️ Hanya untuk berkas di RUANG_PERIKSA (root + app). `_sketsa/` = arsip,
#     tidak diperiksa, jadi TIDAK perlu didaftarkan di sini.
DAFTAR_KECUALI: dict[str, str] = {
    '_gerbang_setelan_produksi.py':
        'gerbang ini sendiri (berkasnya memuat kata kuncinya)',
    #  ── JALUR JEV (bukan 9router/deepseek) ────────────────────────────────
    #  Diperiksa 15Okt26 dari kode, BUKAN ditebak:
    #    jev.py   BASE = jembatan 172.17.0.1:8130 (endpoint systemone)
    #             MODEL_DEFAULT = 'SATPAM/typesafe/jev-1.13'  ← model JEV
    #             body cuma {model, messages} — TIDAK ada max_tokens/temperature
    #  ⇒ Jev BUKAN model berpikir ⇒ `enable_thinking` memang TIDAK berlaku.
    #    Menambahkannya = menyentuh jalur produksi tanpa sebab (DILARANG).
    'app/jev.py':
        'jalur JEV (model jev-1.13 lewat jembatan 8130) — bukan model berpikir',
    'app/_gerbang_jev_jalantol.py':
        'gerbang jalur-tol JEV — menyentuh jalur JEV, bukan 9router',
    #  ⚠️ `_uji_3peran_jev_betul.py` DICABUT dari daftar 26 Okt 2026:
    #  berkasnya sudah DIARSIPKAN ke `_arsip/bersih-23okt26/` (bukan dihapus
    #  sembarangan). Mendaftar berkas yang tidak ada = daftar berisi nama hantu
    #  ⇒ gerbang G5/G7 MERAH dan deploy terhenti karena hal yang sudah beres.
}

#  Berkas produksi yang WAJIB `False` (bukan cuma "ada").
PRODUKSI_WAJIB_FALSE = ['app/ai.py']

#  Pengecualian karena JALUR BEDA (bukan karena lupa) — dikecualikan dari G6.
PENYEBAB_JALUR_JEV = (
    'app/jev.py', 'app/_gerbang_jev_jalantol.py',
)


#  ── RUANG LINGKUP: mana yang DIPERIKSA, mana yang dianggap ARSIP ────────
#  🚨 PELAJARAN 15Okt26 — JANGAN periksa `_sketsa/` & `_arsip/`:
#     `_sketsa/` = ARSIP berkas sekali-pakai (keputusan Bos 07Okt26, Opsi B:
#     "110 berkas .py sekali-pakai root → _sketsa/"). Arsip yang DIPAKSA patuh
#     = melawan keputusan itu + kerja tanpa manfaat.
#     Yang berbahaya = berkas yang MASIH BISA DIPAKAI ULANG dengan santai:
#     root (gampang dipanggil) + `app/` (produksi).
RUANG_PERIKSA = ('*.py', 'app/*.py')
RUANG_ARSIP = ('_sketsa', '_arsip', 'scripts')


def _kandidat() -> list[Path]:
    """Berkas .py yang menyusun payload chat/completions sendiri.

    ⚠️ HANYA di ruang yang bisa dipakai ulang (root + app) — `_sketsa/`
    dan `_arsip/` DILEWATI karena itu arsip (keputusan Bos 07Okt26).
    """
    hasil = []
    for pola in RUANG_PERIKSA:
        for f in sorted(AKAR.glob(pola)):
            try:
                if 'chat/completions' in f.read_text(errors='ignore'):
                    hasil.append(f)
            except Exception:
                continue
    return hasil


LULUS = GAGAL = 0


def cek(nama: str, syarat: bool, cat: str = '') -> None:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {cat}' if cat else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {cat}' if cat else ''))


def periksa() -> None:
    berkas = _kandidat()
    print('=' * 78)
    print('GERBANG SETELAN PRODUKSI — alat uji wajib sama dengan produksi')
    print('=' * 78)
    print(f'\n[i] {len(berkas)} berkas menyusun payload chat/completions sendiri\n')

    lupa = []
    for f in berkas:
        rel = str(f.relative_to(AKAR))
        if rel in DAFTAR_KECUALI:
            continue
        isi = f.read_text(errors='ignore')
        if 'enable_thinking' not in isi:
            lupa.append(rel)

    cek('G1 SEMUA berkas punya `enable_thinking`', not lupa,
        f'{len(lupa)} lupa' if lupa else f'{len(berkas)} berkas diperiksa')
    if lupa:
        for n in lupa[:20]:
            print(f'        ⚠️  {n}')
        if len(lupa) > 20:
            print(f'        … dan {len(lupa) - 20} lagi')

    #  G2: berkas PRODUKSI wajib False (bukan cuma "ada")
    for rel in PRODUKSI_WAJIB_FALSE:
        f = AKAR / rel
        if not f.exists():
            cek(f'G2 {rel} ada', False)
            continue
        isi = f.read_text(errors='ignore')
        jml_false = len(re.findall(r"'enable_thinking':\s*False", isi))
        jml_true = len(re.findall(r"'enable_thinking':\s*True", isi))
        cek(f'G2 {rel}: reasoning DIMATIKAN', jml_false >= 2 and jml_true == 0,
            f'{jml_false}× False, {jml_true}× True')

    #  G3: alat uji di ROOT wajib menandai asal setelan
    di_root = [f for f in berkas
               if f.parent == AKAR and str(f.relative_to(AKAR)) not in DAFTAR_KECUALI]
    tanpa_asal = []
    for f in di_root:
        isi = f.read_text(errors='ignore')
        #  penanda: impor setelan dari produksi ATAU konstanta dari config
        if not re.search(r'from app\.(ai|config) import|app\.config|ENABLE_THINKING|'
                         r'AI_MAX_TOKENS', isi):
            tanpa_asal.append(str(f.relative_to(AKAR)))
    cek('G3 alat uji di ROOT mengambil setelan dari produksi', not tanpa_asal,
        f'{len(tanpa_asal)} tanpa penanda' if tanpa_asal else
        f'{len(di_root)} berkas root diperiksa')
    if tanpa_asal:
        for n in tanpa_asal[:10]:
            print(f'        ⚠️  {n}')

    #  G4: pengecualian WAJIB beralasan
    kosong = [k for k, v in DAFTAR_KECUALI.items() if not (v or '').strip()]
    cek('G4 semua pengecualian punya alasan tertulis', not kosong,
        f'{len(DAFTAR_KECUALI)} pengecualian')

    #  G5: berkas pengecualian benar-benar ada (biar tidak jadi sampah)
    hilang = [k for k in DAFTAR_KECUALI if not (AKAR / k).exists()]
    cek('G5 berkas pengecualian benar-benar ada', not hilang,
        f'{len(hilang)} hilang' if hilang else 'semua ada')

    #  G6: PAGAR PENYALAHGUNAAN — jangan biarkan pengecualian jadi lubang.
    #  Pengecualian HANYA boleh karena JALUR BEDA (JEV). Kalau berkas
    #  menyentuh 9router tapi bukan jalur JEV ⇒ pengecualiannya janggal.
    janggal = []
    for k in DAFTAR_KECUALI:
        if k in PENYEBAB_JALUR_JEV or k.startswith('_gerbang_setelan'):
            continue
        f = AKAR / k
        if not f.exists():
            continue
        isi = f.read_text(errors='ignore')
        if '20128' in isi or 'ROUTER_BASE' in isi:
            janggal.append(k)
    cek('G6 pengecualian bukan kamuflase (kecuali jalur JEV)',
        not janggal, f'{len(janggal)} janggal: {janggal[:3]}' if janggal
        else f'{len(DAFTAR_KECUALI)} pengecualian wajar')

    #  G7: DAFTAR_KECUALI tidak boleh memuat nama berkas yang TIDAK ADA
    #  (Wulan menebak nama = pelanggaran yang sudah pernah terjadi).
    semua = {str(f.relative_to(AKAR)) for f in AKAR.rglob('*.py')}
    karangan = [k for k in DAFTAR_KECUALI if k not in semua]
    cek('G7 tidak ada nama berkas KARANGAN di daftar kecuali', not karangan,
        f'{len(karangan)} karangan: {karangan}' if karangan
        else f'{len(semua)} berkas .py dipetakan')

    #  G8: `_sketsa/` & `_arsip/` TIDAK diperiksa (mereka arsip).
    #  Gerbang yang memeriksa arsip = melawan keputusan Bos 07Okt26.
    diperiksa = {str(f.relative_to(AKAR)) for f in berkas}
    arsip_ikut = [b for b in diperiksa
                  if b.startswith(('_sketsa/', '_arsip/'))]
    cek('G8 arsip (_sketsa/_arsip) TIDAK ikut diperiksa', not arsip_ikut,
        f'{len(arsip_ikut)} arsip ikut' if arsip_ikut
        else f'ruang diperiksa: {RUANG_PERIKSA}')

    print('\n' + '=' * 78)
    print(f'  HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('=' * 78)
    if GAGAL:
        print('\n  OBAT: tambahkan `enable_thinking: False` + ambil angka dari')
        print('        app/config (AI_MAX_TOKENS) — JANGAN tulis angka sendiri.')
        print('        Kalau memang sengaja beda, daftarkan di DAFTAR_KECUALI.')


def uji_gigi() -> None:
    """Buktikan gerbang BISA GAGAL (kalau tidak, gerbang ini palsu)."""
    global LULUS, GAGAL
    print('=' * 78)
    print('UJI BERGIGI — gerbang HARUS menolak berkas yang lupa setelan')
    print('=' * 78)

    #  tiruan berkas rawan: panggil 9router tanpa enable_thinking.
    #  ⚠️ Ditaruh di ROOT (ruang yang diperiksa) — `_sketsa/` = arsip,
    #     tidak diperiksa, jadi candik di sana TIDAK akan terdeteksi.
    candik = AKAR / '_candik_gerbang_tanpa_setelan.py'
    candik.write_text(
        "import httpx\n"
        "r = httpx.post('http://9router:20128/v1/chat/completions', json={\n"
        "    'model': 'M', 'messages': [], 'max_tokens': 100})\n")

    LULUS = GAGAL = 0
    try:
        ditemukan = any(f.name == '_candik_gerbang_tanpa_setelan.py'
                        for f in _kandidat())
        cek('D1 tiruan TERDETEKSI oleh pemindai', ditemukan)

        waspada = '_candik_gerbang_tanpa_setelan.py' not in DAFTAR_KECUALI
        cek('D2 tiruan TIDAK ada di daftar kecuali (jadi diperiksa)', waspada)

        print('\n  ── jalankan pemeriksaan (harus GAGAL) ──')
        g_sebelum = GAGAL
        periksa()
        cek('D3 pemeriksaan BENAR-BENAR GAGAL karena tiruan', GAGAL > g_sebelum)

        #  D4: candik di ARSIP harus DIABAIKAN (bukti G8 bekerja)
        candik_arsip = AKAR / '_sketsa' / '_candik_arsip.py'
        candik_arsip.write_text(
            "import httpx\n"
            "r = httpx.post('http://9router:20128/v1/chat/completions', json={})\n")
        try:
            terdeteksi = any(f.name == '_candik_arsip.py' for f in _kandidat())
            cek('D4 candik di _sketsa/ DIABAIKAN (arsip tidak diperiksa)',
                not terdeteksi)
        finally:
            candik_arsip.unlink(missing_ok=True)
    finally:
        candik.unlink(missing_ok=True)
        sisa = (AKAR / '_candik_gerbang_tanpa_setelan.py').exists()
        print(f'\n  [i] tiruan dibersihkan: {"TIDAK ❌" if sisa else "YA"}')

    print(f'\n  UJI BERGIGI: {LULUS} LULUS / {GAGAL} GAGAL '
          f'(D3 GAGAL>0 = gerbang bergigi ✅)')


if __name__ == '__main__':
    if '--gigi' in sys.argv:
        uji_gigi()
    else:
        periksa()
    sys.exit(0 if GAGAL == 0 else 1)
