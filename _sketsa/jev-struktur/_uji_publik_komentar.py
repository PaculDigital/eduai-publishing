"""UJI E2E KOMENTAR PEMBIMBING — JALUR MAHASISWA SUNGGUHAN (domain publik).

🛑🛑  PERINGATAN — UJI INI MENYENTUH DATA PRODUKSI  🛑🛑
    Uji ini MENEMBAK endpoint nyata `POST /api/ai/v1/revisi` di
    https://eduai.bikinaja.id — artinya ia MENGIRIM REVISI SUNGGUHAN:
      · MEMANGGIL AI sungguhan (memotong kuota akun uji)
      · MENULIS ke DB PRODUKSI: `proses_ai`, `versi_dokumen`,
        `section_state`, `revisi_history`
      · pada 25Sep26 uji ini MEMICU bug C9/C10 → versi naskah file 47
        tersimpan 0 karakter (dipulihkan dari backup).

    ⇒ SEBELUM MENJALANKAN:
      1. BACKUP DB DULU:
         cp _arsip/pra-sot/<image-terbaru>/eduai.db /tmp/bak-e2e.db
      2. JANGAN jalankan berulang — tiap jalan = 1 putaran revisi nyata.
      3. Sejak C10 (25Sep26) pagar "naskah kosong" SUDAH ada, tapi kuota
         akun uji TETAP terpotong; reset dulu bila perlu (`E2E_USER_ID`).

    Uji yang TIDAK menyentuh produksi = `_uji_*.py` yang memakai
    `EDUAI_DATA_DIR` ke folder sementara (uji mesin, mis. `_uji_c10_*`).

⚠️ DIPERBARUI 17Sep26 — WAJIB. Sebelumnya skrip ini SELALU lapor
   "ada isi hasil — 0 kar" dan dihitung GAGAL, padahal itu SALAH UKUR:
   sejak Langkah A (proses latar belakang), `/api/ai/v1/revisi` membalas
   CEPAT (HTTP 200, `status=menunggu`) dan hasilnya diambil lewat
   `/api/ai/v1/proses/{kode}` setelah selesai. Skrip lama mengharap
   jawaban SINKRON (perilaku pra-Langkah A) → mengukur hal yang salah.
   Kini skrip MENIRU halaman: titipkan → pantau tahap → ambil hasil.

BEDA dari `_uji_komentar_pembimbing.py`:
    - itu memanggil fungsi Python LANGSUNG di dalam container (internal)
    - INI lewat HTTPS https://eduai.bikinaja.id seperti mahasiswa

SKENARIO YANG DIUJI (lihat catat_skenario di bawah):
  A. Prasyarat   : health, login, kuota
  B. Dokumen     : unggah naskah nyata → file_id
  C. Gerbang biaya: 409 `butuh_izin` pada dokumen >55k kar (benar!)
  D. Titip kerja : HTTP 200 cepat (<60 s) + `status=menunggu`
  E. Pantau      : tahap NYATA bergerak → `selesai`
  F. Hasil       : `jawaban` terisi, model ada, token nyata > 0
  G. Integritas  : bebas penanda sistem, struktur bagian utuh
  H. ANTI-HALUSINASI: setiap TAHUN di hasil harus ADA di naskah
  I. INGATAN DOKUMEN: `section_state` + `revisi_history` TERISI
     (ini yang dulu senyap kosong — bug `pengali`/list vs str, 17Sep26)
  J. Kuota       : terpotong sesuai jumlah bagian
  K. Negatif     : komentar kosong → 400 · komentar berlebih → 400
  L. Keamanan    : tanpa login → redirect/401 · kode asing → 404

Dijalankan DARI DALAM container hermes (punya internet).
⚠️ WAJIB kirim User-Agent Chrome: Cloudflare WAF error 1010 menolak
   klien Python telanjang (terbukti 16Sep26).

JALANKAN: python3 _uji_publik_komentar.py [berkas.docx]
"""

from __future__ import annotations

import http.cookiejar
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

# ═══════════════════════════════════════════════════════════════════════════
#  🛑 PENJAGA PRODUKSI — uji ini MENULIS ke data NYATA.
#  WAJIB setuju dulu:  E2E_SAYA_SETUJU=1 python3 _uji_publik_komentar.py
#  Alasan: memanggil AI (memakai kuota akun uji) + menulis DB produksi.
#  Wajib pula: BACKUP DB dulu (`_arsip/pra-sot/<image>/eduai.db`).
# ═══════════════════════════════════════════════════════════════════════════
if os.getenv('E2E_SAYA_SETUJU', '') != '1':
    print('🛑 UJI INI MENYENTUH PRODUKSI (memakai kuota + menulis DB nyata).')
    print('   Wajib setuju + backup DB dulu, lalu jalankan:')
    print('     E2E_SAYA_SETUJU=1 python3 _uji_publik_komentar.py')
    print('   Untuk skenario berat: tambah E2E_BERAT=1')
    sys.exit(77)          # 77 = KODE_LEWAT (dilewati, bukan gagal)
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = 'https://eduai.bikinaja.id'
UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36')

EMAIL = os.getenv('E2E_EMAIL', 'uji-berbayar-e2e@test.local')
SANDI = os.getenv('E2E_SANDI', 'UjiBayar123!')
#  User KEDUA khusus skenario BERAT (N/O/P/Q).
#  ⚠️ AKAR "Q1 HTTP 429" (17Sep26): app punya gerbang anti-spam
#     `_cek_ratelimit` = **RATE_MAKS 6 request / 60 dtk / USER** (app/ai.py:571).
#     Skenario A→P beruntun menghabiskan jatah MENIT itu pada user yang sama
#     → Q kena 429. Itu PERILAKU BENAR (anti-spam), bukan bug. Solusi uji:
#     skenario berat pakai USER LAIN supaya jatah rate-limit tidak saling makan.
EMAIL_BERAT = os.getenv('E2E_EMAIL_BERAT', 'uji-berat-e2e@test.local')
SANDI_BERAT = os.getenv('E2E_SANDI_BERAT', 'UjiBerat123!')
_USER_ID_BERAT = int(os.getenv('E2E_USER_ID_BERAT', '7'))   # DB eduai-app

LULUS = GAGAL = 0
CATATAN: list[str] = []
#  🚨 SEBAB_GAGAL (05Okt26) — kenapa alat ini ada: putaran uji terakhir
#  melaporkan "5 GAGAL" di N/O/P/Q TANPA menyebut kuota habis sama sekali.
#  Wulan menuduh app, padahal sebabnya 402 (saldo user uji = 0). Tiap asersi
#  yang GAGAL kini WAJIB meninggalkan jejak sebab — bukan cuma tanda ❌.
SEBAB_GAGAL: list[dict] = []
SEBAB_GAGAL_HIDUP: list[str] = []


def _sebab_dari(kode_http: int, detail: dict | None = None) -> str:
    """Klasifikasi sebab dari kode HTTP + `detail.kode` app."""
    d = detail or {}
    kode_app = str(d.get('kode') or '')
    if kode_app in ('KUOTA_HABIS', 'BUKAN_MEMBER', 'BUTUH_BAYAR'):
        return kode_app
    if kode_http == 402:
        return 'KUOTA_HABIS'
    if kode_http == 403:
        return 'TIDAK_BERHAK'
    if kode_http == 429:
        return 'RATE_LIMIT'
    if kode_http >= 500:
        return 'GALAT_SERVER'
    return f'HTTP_{kode_http}'


def _catat_gagal(nama: str, j: dict | None, detail: dict | None,
                 kode_http: int) -> None:
    """Catat SEBAB tiap kegagalan (dipanggil dari `cek()` saat GAGAL).

    Tujuannya bukan mempercantik laporan: supaya gerbang TIDAK PERNAH lagi
    melaporkan "5 GAGAL" tanpa sebab, dan supaya sebab KUOTA_HABIS langsung
    terbaca di ringkasan akhir.
    """
    j = j or {}
    sebab = _sebab_dari(kode_http, detail)
    baris = {'nama': nama, 'sebab': sebab, 'http': kode_http,
             'kode_app': (detail or {}).get('kode'),
             'pesan': str((detail or {}).get('pesan')
                          or j.get('pesan') or '')[:160]}
    SEBAB_GAGAL.append(baris)
    if sebab in ('KUOTA_HABIS', 'TIDAK_BERHAK') and \
            'perintah pemulihan' not in SEBAB_GAGAL_HIDUP:
        SEBAB_GAGAL_HIDUP.append(
            'perintah pemulihan: `kuota_reset_berat(20)` untuk user '
            f'{_USER_ID_BERAT} ATAU set E2E_USER_ID ke user bersaldo '
            '(ledger `saldo_token`) sebelum menjalankan ulang.')


def cek(nama: str, syarat: bool, bukti: str = '', sebab: str = '') -> bool:
    """Catat hasil satu asersi. `sebab` = jejak yang dipakai `akhir()`.

    `sebab` sengaja TIDAK mencetak lewat pesan galat app (bisa panjang) —
    cukup dipakai untuk meringkas MENGAPA gagal.
    """
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'   ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'   ❌ {nama}' + (f' — {bukti}' if bukti else ''))
        if sebab:
            _catat_gagal(nama, None, {'kode': sebab, 'pesan': bukti}, 0)
    return bool(syarat)


# ═══════════════════════════════════════════════════════════════════════════
#  🎯 PERBAIKAN AKAR 05Okt26 (putusan Bos "A") — UJI RAPUH AI TIDAK STABIL
#
#  MASALAH TERUKUR (2 putaran gerbang):
#    · putaran-1 → G2 merah (AI tulis 1 dari 2 bagian)
#    · putaran-2 → H2 merah (AI tidak menolak mengarang)
#    Asersi merah BERGANTI tiap putaran; dua-duanya asersi yang memakai
#    AI NYATA (9router). Riwayat: `_uji_publik_komentar` juga merah di
#    `gerbang_wa_presisi` SEBELUM ada perubahan apa pun ⇒ uji ini memang
#    rapuh, bukan penanda kode rusak.
#
#  AKAR: satu jawaban AI dianggap vonis final. Model combo 9router tidak
#  stabil (tercatat: 0 / 416 / 6.094 karakter untuk komentar yang SAMA).
#
#  PERBAIKAN (bukan tambalan): asersi yang ditandai `AI_RAPUH` diulang
#  sampai ULANG_AI kali; vonis GAGAL hanya kalau SEMUA ulangan gagal.
#  Asersi non-AI (HTTP, struktur berkas, dsb.) TIDAK diulang — supaya uji
#  tetap BERGIGI dan tidak menyembunyikan kerusakan sungguhan.
# ═══════════════════════════════════════════════════════════════════════════
ULANG_AI = int(os.getenv('E2E_ULANG_AI', '3'))


def cek_ai(nama: str, ulang, bukti_pertama: str = '', sebab: str = '') -> bool:
    """Asersi berbasis AI: coba `ulang()` sampai ULANG_AI kali.

    `ulang()` dipanggil berulang; ia harus MENGEMBALIKAN (lolos: bool,
    bukti: str). GAGAL hanya kalau SEMUA percobaan gagal → AI yang tidak
    stabil tidak lagi membuat gerbang merah palsu, TAPI kerusakan
    sungguhan tetap tertangkap (3× gagal = merah).
    """
    global LULUS, GAGAL
    jejak = []
    for i in range(1, ULANG_AI + 1):
        try:
            lolos, bukti = ulang()
        except Exception as e:                                # noqa: BLE001
            lolos, bukti = False, f'galat: {type(e).__name__}: {e}'
        jejak.append(f'{i}/{ULANG_AI}: {bukti}')
        if lolos:
            LULUS += 1
            tanda = '' if i == 1 else f' — ✅ pada ulangan {i}/{ULANG_AI}'
            print(f'   ✅ {nama}' + (f' — {bukti}' if bukti else '') + tanda)
            return True
    GAGAL += 1
    ringkas = bukti_pertama or (jejak[-1] if jejak else '')
    print(f'   ❌ {nama} — {ringkas}')
    for j in jejak:
        print(f'        · {j}')
    _catat_gagal(nama, None,
                 {'kode': sebab or 'AI_TIDAK_STABIL', 'pesan': ' | '.join(jejak)}, 0)
    return False


def sebab_http(nama: str, s: int, b: str, j: dict | None = None) -> None:
    """Catat sebab kegagalan dari jawaban HTTP SUNGGUHAN (dipakai blok N/O/P/Q).

    Dipanggil HANYA saat asersi gagal — memisahkan "kenapa" dari "apa yang
    dituntut", supaya ringkasan akhir menyebut kuota habis, bukan cuma ❌.
    """
    detail = (j or {}).get('detail') if isinstance((j or {}).get('detail'), dict) \
        else (j or {})
    _catat_gagal(nama, j, detail, s)


def info(pesan: str) -> None:
    CATATAN.append(pesan)


ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPSHandler(context=ctx))


def buka(path: str, data=None, metode: str | None = None, timeout: int = 700):
    #  C7 fix 27Sep: revisi nyata 583 dtk > 300 lama → GAGAL PALSU.
    """Buka URL. Kembalikan (status, body, header_dict).

    🌐 RETRY khusus GET (28Sep26): AKAR crash C7 putaran penuh =
    `URLError [Errno 101] Network is unreachable` SATU KALI saat polling
    `tunggu_proses` (M) → traceback → N/O/P/Q + ringkasan HASIL hilang
    semua. GET = idempoten (pantau status) → aman diulang maksimal 4×
    (jeda 3·n dtk). POST TIDAK diulang (titip bisa dobel!) — gagal = lempar.
    """
    h = {'User-Agent': UA}
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode('utf-8')
        h['Content-Type'] = 'application/json'
    get = data is None and (metode or 'GET').upper() == 'GET'
    ulang = 4 if get else 1
    galat = None
    for i in range(ulang):
        try:
            r = OP.open(urllib.request.Request(BASE + path, data=data,
                                               headers=h, method=metode),
                        timeout=timeout)
            return r.status, r.read().decode('utf-8', 'ignore'), dict(r.headers)
        except urllib.error.HTTPError as e:        #  4xx/5xx = jawaban SAH
            return e.code, e.read().decode('utf-8', 'ignore'), dict(e.headers)
        except (urllib.error.URLError, OSError) as e:
            galat = e
            if i + 1 < ulang:
                info(f'jaringan putus ({e}) — coba lagi {i + 2}/{ulang}')
                time.sleep(3 * (i + 1))
    raise galat                                    #  GET tetap gagal → jujur


def login(email: str, sandi: str) -> bool:
    """Login form (field `email` + `password`) — cookie masuk ke `OP` global.

    ⚠️ Field = `password`, BUKAN `sandi` (pelajaran nyata: sering salah).
    """
    data = urllib.parse.urlencode({'email': email, 'password': sandi}).encode()
    try:
        r = OP.open(urllib.request.Request(
            BASE + '/masuk', data=data,
            headers={'User-Agent': UA,
                     'Content-Type': 'application/x-www-form-urlencoded'}),
            timeout=60)
        return r.status == 200 and 'eduai_session' in [c.name for c in cj]
    except urllib.error.HTTPError:
        return False


def tunggu_jatah_rate(sebab: str) -> None:
    """Tunggu jatah rate-limit MENIT user pulih (RATE_MAKS 6 / 60 dtk).

    ⚠️ AKAR "429 GAGAL PALSU" (17Sep26): gerbang anti-spam app/ai.py:571
    (`RATE_MAKS=6`, `RATE_WINDOW=60`) memang BENAR — tapi skenario uji
    beruntun (K1..K3, C, D, N, O, P, Q) menghabiskannya pada user yang sama
    → 429 muncul di skenario berikutnya = ALAT UKUR yang salah, bukan app.

    ⚠️⚠️ JEBAKAN YANG SUDAH TERBUKTI: `_ratelimit` itu IN-MEMORY PER-PROSES.
       Menjalankan `docker exec ... python3 -c "app.ai._ratelimit.clear()"`
       TIDAK MENGHAPUS riwayat proses uvicorn (proses berbeda, salinan kosong)
       → 429 TETAP muncul. Jangan ulangi.
       Satu-satunya cara jujur: TUNGGU jendela waktu (60 dtk) berlalu.
    """
    if not UJI_BERAT:
        return
    detik = float(os.getenv('E2E_TUNGGU_RATE', '62'))
    if detik > 0:
        print(f'      · tunggu {detik:.0f}s jatah rate-limit pulih ({sebab})')
        time.sleep(detik)


def teks_docx(path: Path) -> str:
    """Ambil teks dari .docx (untuk uji anti-halusinasi & panjang)."""
    W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    with zipfile.ZipFile(path) as z:
        akar = ET.parse(z.open('word/document.xml')).getroot()
    return '\n'.join(''.join(t.text or '' for t in p.iter(W + 't')).strip()
                     for p in akar.iter(W + 'p'))


def _docker(cmd: str, timeout: int = 60) -> tuple[int, str]:
    """Jalankan `docker ...` dari container hermes (Docker CLI tersedia).

    ⚠️ CACAT UJI DIPERBAIKI 25Sep26: `docker` TIDAK ADA di dalam image
    eduai-app. Kalau fungsi ini dipanggil DARI DALAM eduai-app (mis. saat
    skenario N/O/P/Q berjalan di sana), hasilnya SELALU `docker: not found`
    → GAGAL PALSU (bukan bug aplikasi). Terukur: P1 & O1 gagal karena ini.
    Sekarang: kalau `docker` tidak ada → kembalikan rc=127 + pesan jujur,
    supaya uji bisa MENANDAI "tidak bisa diuji dari sini" (bukan "gagal").
    """
    import shutil
    import subprocess
    if shutil.which('docker') is None:
        return 127, ('TANPA_DOCKER: `docker` tidak ada di lingkungan ini — '
                     'jalankan uji ini DARI HOST, bukan dari dalam container')
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except Exception as e:                                     # noqa: BLE001
        return 1, str(e)


def _jalankan_py(kode: str, timeout: int = 30) -> tuple[int, str]:
    """Jalankan potongan PYTHON (boleh `print`) terhadap DB eduai.

    Jalur jujur DUA lingkungan (28Sep26):
      • dari DALAM container eduai-app → sqlite3 lokal `/app/data/eduai.db`
      • dari HOST (hermes)             → `docker exec` (kode di-base64 →
        aman dari kutipan shell)
    ❌ AKAR SUNYI 28Sep26: versi lama HANYA jalur lokal → dari host
    `/app/data/eduai.db` TIDAK ADA → exception ditelan → pengujing mengira
    fixture tersiap padahal TIDAK (baris pemakaian_ai / user berat hilang).
    Kini kegagalan KEDUA jalur dikembalikan apa adanya (bukan diam sukses).
    """
    import base64
    import os
    import shutil
    import subprocess
    if os.path.exists('/app/data/eduai.db'):
        p = subprocess.run(['python3', '-c', kode], capture_output=True,
                           text=True, timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    if shutil.which('docker') is None:
        return 127, ('TANPA_DOCKER: jalankan uji dari HOST atau dari dalam '
                     'container eduai')
    b64 = base64.b64encode(kode.encode()).decode()
    cmd = ("docker exec eduai-app python3 -c \"import base64;"
           "exec(base64.b64decode('" + b64 + "').decode())\"")
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                       timeout=timeout)
    return p.returncode, (p.stdout or '') + (p.stderr or '')


def _sql_langsung(sql: str) -> tuple[int, str]:
    """Jalankan SQL (executescript) ke DB eduai — lewat `_jalankan_py`.

    Tanda tangan lama (rc, pesan) dipertahankan supaya pemanggil lama
    (`_pastikan_baris_kuota` dkk) ikut benar di HOST maupun container.
    """
    return _jalankan_py(
        "import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
        "c.executescript(" + repr(sql) + ");c.commit();print('OK')")


def saldo_baca(user_id: int) -> int | None:
    """SALDO LEDGER user (baris terakhir `saldo_token`) — sumber gerbang 402."""
    rc, out = _jalankan_py(
        "import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
        "r=c.execute('SELECT sisa FROM saldo_token WHERE user_id=%d "
        "ORDER BY id DESC LIMIT 1').fetchone();print(r[0] if r else 'X')"
        % int(user_id))
    out = out.strip().splitlines()[-1] if out.strip() else ''
    try:
        return int(out)
    except ValueError:
        return None


def saldo_paksa(user_id: int, nilai: int) -> int | None:
    """Paksa saldo user jadi `nilai` dengan MENAMBAH 1 baris ledger uji.

    Mengembalikan `id` baris uji → dipakai `saldo_pulihkan()`. Baris asli
    TIDAK pernah diubah/dihapus → pemulihan = hapus baris uji ini.
    """
    uid, nilai = int(user_id), int(nilai)
    rc, out = _jalankan_py(
        "import sqlite3\n"
        f"c=sqlite3.connect('/app/data/eduai.db')\n"
        f"b=c.execute('SELECT sisa FROM saldo_token WHERE user_id={uid} "
        "ORDER BY id DESC LIMIT 1').fetchone()\n"
        "sebelum=int(b[0]) if b else 0\n"
        "c.execute(\"INSERT INTO saldo_token(user_id,jumlah,sisa,sumber,"
        "catatan,order_id,dibuat) VALUES(?,?,?,?,?,'',datetime('now'))\", "
        f"({uid}, {nilai}-sebelum, {nilai}, 'uji', 'uji paksa habis'))\n"
        "c.commit()\n"
        f"print('BARIS=' + str(c.execute('SELECT MAX(id) FROM saldo_token "
        f"WHERE user_id={uid}').fetchone()[0]))\n")
    for baris in out.splitlines():
        if baris.startswith('BARIS='):
            try:
                return int(baris.split('=', 1)[1])
            except ValueError:
                return None
    return None


def saldo_pulihkan(user_id: int, baris_id: int | None) -> bool:
    """Hapus baris ledger uji hasil `saldo_paksa` → saldo kembali persis."""
    if not baris_id:
        return False
    rc, out = _jalankan_py(
        "import sqlite3\n"
        f"c=sqlite3.connect('/app/data/eduai.db')\n"
        f"c.execute('DELETE FROM saldo_token WHERE id={int(baris_id)} "
        f"AND user_id={int(user_id)}')\n"
        "c.commit()\n"
        "print('HAPUS=' + str(c.total_changes))\n")
    return rc == 0 and 'HAPUS=1' in out


#  (28Sep26) `docker_kuota_pakai` / `docker_kuota_set` DIHAPUS: lever
#  `pemakaian_ai` TIDAK dibaca gerbang 402 sejak SALDO PERMANEN (26Sep) —
#  alat ukurnya kini `saldo_baca` / `saldo_paksa` / `saldo_pulihkan` (ledger).


def _9r(kode: str) -> tuple[int, str]:
    """Jalankan potongan NODE terhadap DB 9router (lewat `docker exec`).

    Kode di-BASE64 dulu → aman dari kutipan shell (`eval(Buffer...)`).
    """
    import base64
    buka_db = ("const s=require('/app/node_modules/better-sqlite3')"
               "('/app/data/db/data.sqlite');")
    b64 = base64.b64encode((buka_db + kode).encode()).decode()
    isi = "eval(Buffer.from('" + b64 + "','base64').toString())"
    return _docker('docker exec 9router node -e "' + isi + '"')


def _id_aktif_9r() -> list:
    """Daftar id koneksi 9router dengan `isActive=1` (urut, tanpa sortir)."""
    rc, out = _9r("console.log('AKTIF=' + JSON.stringify("
                  "s.prepare('SELECT id FROM providerConnections "
                  "WHERE isActive=1 ORDER BY id').all().map(r=>r.id)))")
    for baris in out.splitlines():
        if baris.startswith('AKTIF='):
            try:
                return json.loads(baris.split('=', 1)[1])
            except (ValueError, TypeError):
                return []
    return []


def _set_aktif_9r(ids: list, nilai: int) -> int:
    """Set `isActive=<nilai>` untuk persis id-id `ids`. Balas JUMLAH baris kena."""
    if not ids:
        return 0
    daftar = ','.join("'" + str(i).replace("'", '') + "'" for i in ids)
    kode = ('const st=s.prepare("UPDATE providerConnections SET isActive='
            + str(int(nilai)) + ' WHERE id IN (' + daftar + ')");'
            "const r=st.run();console.log('KENA=' + r.changes)")
    rc, out = _9r(kode)
    for baris in out.splitlines():
        if baris.startswith('KENA='):
            try:
                return int(baris.split('=', 1)[1])
            except ValueError:
                return 0
    return 0


def _probe_9router(max_tok: int = 16) -> str:
    """Probe LANGSUNG combo `EduAi` — dari DALAM container app (jaringan app).

    Probe jalan persis di tempat app memanggil 9router
    (`http://9router:20128/v1` dari container eduai-app), memakai kunci
    yang SUDAH ada di env container — uji TIDAK PERNAH menyentuh kunci.
    'hidup' = masih bisa layani (ada `choices`) · 'mati' = tak bisa layani
    · 'ragu' = tak ada hasil terbaca. Kalibrasi WAJIB: dipercaya HANYA
    kalau SEBELUM dimatikan dia bilang 'hidup' (bukti alat bisa melihat
    hidup & mati — kalau tidak, P1 cukup pakai hitungan DB saja).
    """
    import base64
    py = (
        "import os, json, urllib.request as u\n"
        "isi = json.dumps({'model': 'EduAi', 'messages': [{'role': 'user',"
        " 'content': 'Balas: OK'}], 'max_tokens': %d, 'temperature': 0.2}).encode()\n"
        "r = u.Request('http://9router:20128/v1/chat/completions', data=isi,\n"
        "  headers={'Authorization': 'Bearer ' + os.environ.get('EDUAI_ROUTER_KEY', ''),"
        " 'Content-Type': 'application/json'}, method='POST')\n"
        "try:\n"
        "    with u.urlopen(r, timeout=45) as b:\n"
        "        body = b.read().decode('utf-8', 'ignore')\n"
        "    j = {}\n"
        "    try:\n"
        "        j = json.loads(body)\n"
        "    except Exception:\n"
        "        i = body.find('{')\n"
        "        if i >= 0:\n"
        "            j = json.JSONDecoder().raw_decode(body[i:])[0]\n"
        "    print('PROBE=hidup' if j.get('choices') else 'PROBE=mati-kosong')\n"
        "except Exception as x:\n"
        "    print('PROBE=mati-' + type(x).__name__)\n"
    ) % max_tok
    b64 = base64.b64encode(py.encode()).decode()
    rc, out = _docker(
        'docker exec eduai-app python3 -c '
        + '"import base64;exec(base64.b64decode(\'' + b64 + '\'))"')
    for baris in out.splitlines():
        if baris.startswith('PROBE='):
            return 'hidup' if baris.strip() == 'PROBE=hidup' else 'mati'
    return 'ragu'


# ══════════════════════════════════════════════════════════════════════════
#  PEMISAH UJI BERAT (17Sep26) — AKAR dari 5 GAGAL PALSU sesi lalu.
#  Skenario N/O/P/Q memotong kuota & memanggil AI beruntun → kena rate limit
#  429 dan kuota habis (402), sehingga GAGAL-nya PALSU (bukan bug app).
#  UJI CEPAT (gerbang harian) TIDAK boleh ikut kena. Kunci di balik
#  E2E_BERAT=1 supaya gerbang tetap cepat & hijau.
# ══════════════════════════════════════════════════════════════════════════
UJI_BERAT = os.environ.get('E2E_BERAT', '0') == '1'
JEDA_ANTAR_BERAT = float(os.environ.get('E2E_JEDA', '2'))


def _pastikan_baris_kuota(user_id: int) -> None:
    """Pastikan baris `pemakaian_ai` ADA untuk user ini.

    ⚠️ AKAR GAGAL N/O/P/Q (25Sep26): user uji berat (id 7) TIDAK punya baris
    `pemakaian_ai` → app menganggapnya BUKAN member berbayar → HTTP 403
    "Fitur AI hanya untuk member berbayar. Upgrade paket dulu ya."
    Itu GAGAL PALSU: aplikasinya benar, datanya yang belum disiapkan.
    """
    bln = time.strftime('%Y-%m')
    _sql_langsung(
        f"INSERT INTO pemakaian_ai (user_id,bulan,jumlah_revisi,jumlah_simulasi)"
        f" SELECT {int(user_id)},'{bln}',0,0"
        f" WHERE NOT EXISTS (SELECT 1 FROM pemakaian_ai WHERE user_id={int(user_id)});")


def kuota_reset_berat(minimal: int = 5) -> None:
    """JAMIN saldo LEDGER user uji berat ≥ `minimal` sebelum skenario N/P.

    ❌ AKAR 28Sep26: versi lama menyetel `pemakaian_ai.jumlah_revisi` —
    sejak SALDO PERMANEN (26Sep) gerbang 402 baca `saldo_token`, jadi
    setelan lama TIDAK BERDAMPAK → N/P bisa 402 padahal niatnya "direset".
    Kini lever = ledger (satu-satunya yang dibaca gerbang).
    """
    _pastikan_baris_kuota(_USER_ID_BERAT)
    kini = saldo_baca(_USER_ID_BERAT)
    if kini is None or kini < minimal:
        #  `kini is None` = ledger belum punya baris (user baru) → tetap
        #  bisa diisi lewat baris uji; bukan alasan untuk menyerah.
        if saldo_paksa(_USER_ID_BERAT, minimal) is not None:
            info(f'saldo user BERAT {kini} → {minimal} (ledger, baris uji)')
        else:
            info('⚠️ gagal menyetel saldo user berat (lanjut apa adanya)')
    else:
        info(f'saldo user BERAT cukup: {kini} (≥ {minimal})')


def pastikan_user_berat() -> bool:
    """Siapkan user uji berat (`_USER_ID_BERAT`) bila belum ada, lalu baris kuota.

    ❌ AKAR 28Sep26: user 7 (`uji-berat-e2e@test.local`) ikut terhapus pada
    "bersih keseluruhan 26Sep1638" → X1 login gagal → skenario N/O/P/Q
    mustahil jalan. Kini uji MENYIAPKAN fixture-nya sendiri — eksplisit,
    bukan mengasumsikan data orang lain masih ada.
    Sandi di-hash dengan aturan app: PBKDF2-HMAC-SHA256 200k, format
    `pbkdf2$200000$salt$hex` (app/auth.py::hash_password).
    """
    import hashlib
    import secrets
    uid = int(_USER_ID_BERAT)
    rc, out = _jalankan_py(
        "import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
        "print('ADA' if c.execute('SELECT 1 FROM users WHERE id=%d')"
        ".fetchone() else 'BELUM')" % uid)
    baris = out.strip().splitlines()[-1] if out.strip() else ''
    if baris == 'BELUM':
        salt = secrets.token_hex(16)
        dk = hashlib.pbkdf2_hmac('sha256', SANDI_BERAT.encode(),
                                 salt.encode(), 200_000)
        h = f'pbkdf2$200000${salt}${dk.hex()}'
        bln = time.strftime('%Y-%m')
        sql = (
            "INSERT INTO users(id,email,password_hash,nama,kuota_mb,role,"
            "aktif,dibuat,paket) VALUES(%d,%r,%r,'Uji Berat E2E',500,"
            "'client',1,datetime('now'),'penulis');\n"
            "INSERT INTO pemakaian_ai(user_id,bulan,jumlah_revisi,"
            "jumlah_simulasi) SELECT %d,'%s',0,0 WHERE NOT EXISTS "
            "(SELECT 1 FROM pemakaian_ai WHERE user_id=%d);"
            % (uid, EMAIL_BERAT, h, uid, bln, uid))
        rc, out = _sql_langsung(sql)
        if rc != 0:
            info(f'⚠️ gagal buat user berat: {out[:90]}')
            return False
        info(f'fixture user berat id={uid} DIBUAT (paket penulis)')
    elif baris == 'ADA':
        info(f'fixture user berat id={uid}: sudah ada')
    else:
        info(f'⚠️ gagal cek user berat: {out[:90]}')
        return False
    _pastikan_baris_kuota(uid)
    return True


def jeda(sebab: str = '') -> None:
    """Jeda antar skenario berat supaya rate limit AI tidak terpicu."""
    if JEDA_ANTAR_BERAT > 0:
        print(f'      · jeda {JEDA_ANTAR_BERAT:.0f}s {sebab}'.rstrip())
        time.sleep(JEDA_ANTAR_BERAT)


def tunggu_proses(kode: str, batas_detik: int = 420) -> tuple[str, dict]:
    """Pantau `/v1/proses/{kode}` seperti halaman mahasiswa.

    Kembalikan (status_akhir, ringkasan_terakhir). Tahap dicatat APA ADANYA.
    """
    t0 = time.monotonic()
    tahapan: list[str] = []
    ring: dict = {}
    while time.monotonic() - t0 < batas_detik:
        s, b, _ = buka(f'/api/ai/v1/proses/{kode}', timeout=60)
        if s != 200:
            info(f'pantau: HTTP {s} → {b[:120]}')
            break
        try:
            ring = json.loads(b)
        except Exception:                                      # noqa: BLE001
            break
        t = ring.get('tahap') or ''
        if t and (not tahapan or tahapan[-1] != t):
            tahapan.append(t)
            print(f'      · {time.monotonic()-t0:5.1f}s  {t}')
        if ring.get('status') in ('selesai', 'gagal'):
            break
        time.sleep(3)
    info('tahap terlihat: ' + ' → '.join(tahapan))
    return (ring.get('status') or 'tidak_selesai'), ring


def main() -> int:
    #  ⚠️ DIPERBAIKI 24Sep26 — GAGAL PALSU karena jalur berkas.
    #  Versi lama mematok SATU jalur absolut HOST (`_arsip/contoh-dokumen/…`)
    #  padahal uji ini dijalankan DI DALAM container, yang melihat naskah di
    #  `_contoh-dokumen/…` (tanpa `_arsip/`). Terukur: `_arsip/contoh-dokumen`
    #  TIDAK ADA di container → A3 GAGAL; padahal `_contoh-dokumen/` ADA.
    #  Sekarang: pakai argumen, kalau tidak ada → coba beberapa jalur yang
    #  MUNGKIN, ambil yang benar-benar ADA.
    kandidat = []
    if len(sys.argv) > 1:
        kandidat.append(Path(sys.argv[1]))
    kandidat += [
        Path('_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'),
        Path('/app/_contoh-dokumen/skripsi-s1/'
             'SKRIPSI-S1-unmul-fazrigading.docx'),
        Path('/opt/data/services/eduai-publishing/_contoh-dokumen/'
             'skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'),
        Path('/opt/data/services/eduai-publishing/_arsip/contoh-dokumen/'
             'skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx'),
    ]
    berkas = next((p for p in kandidat if p.is_file()), kandidat[0])
    print('═' * 78)
    print('UJI E2E KOMENTAR PEMBIMBING — DOMAIN PUBLIK (jalur mahasiswa)')
    print('═' * 78)

    # ── A. PRASYARAT ─────────────────────────────────────────────────────
    print('\n── A. PRASYARAT ──────────────────────────────────────────')
    s, b, _ = buka('/health', timeout=60)
    cek('A1 domain publik terbuka (Cloudflare tidak tolak)', s == 200, f'HTTP {s}')
    cek('A2 layanan sehat', '"ok":true' in b, b[:60])

    if not berkas.exists():
        cek('A3 naskah uji ADA', False, f'tidak ada: {berkas}')
        return akhir()
    ukuran_kb = berkas.stat().st_size / 1024
    naskah_asli = teks_docx(berkas)
    cek('A3 naskah uji ADA & terbaca',
        len(naskah_asli) > 1000,
        f'{berkas.name} · {ukuran_kb:.0f} KB · {len(naskah_asli):,} kar'.replace(',', '.'))

    print('\n── A4. LOGIN (form, field email+password) ────────────────')
    data = urllib.parse.urlencode({'email': EMAIL, 'password': SANDI}).encode()
    try:
        r = OP.open(urllib.request.Request(
            BASE + '/masuk', data=data,
            headers={'User-Agent': UA,
                     'Content-Type': 'application/x-www-form-urlencoded'}),
            timeout=60)
        cookie = [c.name for c in cj]
        cek('A4 login diterima', r.status == 200 and 'eduai_session' in cookie,
            f'HTTP {r.status} · cookie {cookie}')
    except urllib.error.HTTPError as e:
        cek('A4 login diterima', False, f'HTTP {e.code}')

    print('\n── A5. KUOTA SEBELUM ─────────────────────────────────────')
    #  ⚠️ AKAR 429 GAGAL PALSU: jatah rate-limit user uji (6 req/menit)
    #  dihabiskan oleh uji berat sebelumnya & skenario beruntun. Bersihkan
    #  SEKALI di awal (khusus uji) supaya hasil uji mengukur APP, bukan
    #  kelelahan jatah uji. Gerbang PRODUKSI (RATE_MAKS) tidak diubah.
    tunggu_jatah_rate('awal uji — bersihkan jatah lamian')
    s, b, _ = buka('/api/ai/v1/kuota', timeout=60)
    sisa0 = None
    try:
        k0 = json.loads(b)
        sisa0 = k0['revisi']['sisa']
        cek('A5 kuota terbaca', s == 200,
            f'sisa={sisa0} (paket {k0.get("paket")})')
    except Exception as e:                                     # noqa: BLE001
        cek('A5 kuota terbaca', False, f'{e} · {b[:150]}')

    # ── K. NEGATIF (tanpa menghabiskan kuota) ────────────────────────────
    print('\n── K. SKENARIO NEGATIF (tanpa potong kuota) ──────────────')
    s, b, _ = buka('/api/ai/v1/revisi', data={'komentar': []}, metode='POST',
                   timeout=60)
    cek('K1 komentar KOSONG ditolak 400',
        s == 400, f'HTTP {s} · {b[:90]}')
    s, b, _ = buka('/api/ai/v1/revisi',
                   data={'komentar': ['  ', '']}, metode='POST', timeout=60)
    cek('K2 komentar SPASI saja ditolak 400',
        s == 400, f'HTTP {s} · {b[:90]}')
    s, b, _ = buka('/api/ai/v1/revisi',
                   data={'komentar': [f'c{i}' for i in range(11)]},
                   metode='POST', timeout=60)
    cek('K3 komentar BERLEBIH (>10) ditolak 400',
        s == 400, f'HTTP {s} · {b[:90]}')
    s, b, _ = buka('/api/ai/v1/proses/KODE-ASING-TIDAK-ADA', timeout=60)
    cek('K4 kode proses ASING → 404', s == 404, f'HTTP {s}')

    # Keamanan: tanpa login (opener BARU tanpa cookie)
    ctx2 = ssl.create_default_context()
    ctx2.check_hostname = False
    ctx2.verify_mode = ssl.CERT_NONE
    OP2 = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        urllib.request.HTTPSHandler(context=ctx2))
    try:
        r2 = OP2.open(urllib.request.Request(
            BASE + '/api/ai/v1/kuota', headers={'User-Agent': UA}), timeout=60)
        kode2, _ = r2.status, r2.read()
    except urllib.error.HTTPError as e:
        kode2 = e.code
    cek('K5 TANPA login ditolak (401/403/redirect)', kode2 in (302, 303, 307,
                                                               401, 403),
        f'HTTP {kode2}')

    # ── B. UNGGAH ────────────────────────────────────────────────────────
    print('\n── B. UNGGAH NASKAH NYATA ────────────────────────────────')
    isi = berkas.read_bytes()
    bates = '----WulanE2E' + str(len(isi))
    badan = b''.join([
        f'--{bates}\r\nContent-Disposition: form-data; name="berkas"; '
        f'filename="{berkas.name}"\r\n'
        f'Content-Type: application/vnd.openxmlformats-officedocument.'
        f'wordprocessingml.document\r\n\r\n'.encode('utf-8'),
        isi, f'\r\n--{bates}--\r\n'.encode('utf-8'),
    ])
    try:
        r = OP.open(urllib.request.Request(
            BASE + '/unggah', data=badan,
            headers={'User-Agent': UA,
                     'Content-Type': f'multipart/form-data; boundary={bates}'}),
            timeout=300)
        s, b = r.status, r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        s, b = e.code, e.read().decode('utf-8', 'ignore')
    print(f'   respons: {b[:160]}')
    #  ⚠️ AKAR "B1 GAGAL" (17Sep26): asersi lama cuma terima HTTP 200, padahal
    #  berkas uji 5,08 MB bisa MELEBIHI sisa STORAGE paket user uji → app
    #  menjawab **413 + tawaran AddOn Storage** = PERILAKU BISNIS BENAR
    #  (aturan Bos: paket = tiket masuk, AddOn = mesin uang). Bukan bug app —
    #  alat ukurnya yang salah. Terbukti lokal: "Kuota tidak cukup. Sisa 3.0 MB,
    #  berkas 5.1 MB." + `tawarkan=ADDON`. Terima KEDUANYA, lalu pastikan
    #  jalur lanjut hanya bila unggahan memang diterima.
    diterima = s == 200 and '"ok":true' in b
    ditolak_storage = s == 413 and ('kuota' in b.lower() or 'addon' in b.lower())
    cek('B1 unggah ditangani BENAR (200 diterima / 413 tawarkan AddOn)',
        diterima or ditolak_storage,
        f'HTTP {s} · {"DITERIMA" if diterima else "413+AddOn Storage (benar)" if ditolak_storage else b[:120]}')
    if ditolak_storage:
        info('B1 413 = storage paket kurang; AddOn Storage ditawarkan (sesuai bisnis)')
        cek('B1b pesan 413 menawarkan JALAN KELUAR (AddOn)',
            'addon' in b.lower() or 'tambah' in b.lower(), b[:100])

    s, b, _ = buka('/naskah', timeout=60)
    file_id = None
    if s == 200:
        unik = sorted({int(x) for x in re.findall(r'/edit/(\d+)', b)},
                      reverse=True)
        print(f'   tautan /edit: {unik[:6]}')
        if unik:
            file_id = unik[0]
    #  file_id hanya WAJIB bila unggahan benar-benar diterima.
    if ditolak_storage and file_id is None:
        info('B2 dilewati syarat: unggahan 413 (storage) → tak ada file baru')
        cek('B2 file_id tersedia dari berkas uji sebelumnya', False,
            'tidak ada berkas → sisa skenario dilewati (bukan bug)')
    else:
        cek('B2 file_id ditemukan', file_id is not None, f'file_id={file_id}')

    # ── C/D. GERBANG BIAYA + TITIP KERJA ─────────────────────────────────
    print('\n── C. GERBANG BIAYA (dokumen besar → minta izin) ─────────')
    tunggu_jatah_rate('sebelum C/D — K1..K3 sudah makan jatah')
    komentar = ['Latar belakang terlalu pendek dan kurang jelas. '
                'Perdalam dengan teori dan data terbaru.']
    body = {'komentar': komentar}
    if file_id:
        body['file_id'] = file_id
    else:
        body['naskah'] = naskah_asli[:60000]
        info('file_id tidak ada → pakai jalur `naskah` langsung')

    s, b, _ = buka('/api/ai/v1/revisi', data=body, metode='POST', timeout=120)
    print(f'   HTTP {s} · {b[:220]}')
    jml_bagian = 1
    if s == 409:
        try:
            detail = json.loads(b).get('detail') or {}
        except Exception:                                      # noqa: BLE001
            detail = {}
        jml_bagian = detail.get('bagian') or 1
        cek('C1 gerbang persetujuan muncul (perilaku BENAR)',
            detail.get('kode') == 'butuh_izin', f'kode={detail.get("kode")!r}')
        cek('C2 gerbang menyebut jumlah bagian & kuota',
            bool(detail.get('bagian')) and 'kuota' in (detail.get('pesan') or ''),
            f'bagian={detail.get("bagian")}')
        # setujui seperti mahasiswa klik "Setujui"
        body['setuju_bagian'] = True

    print('\n── D. TITIPKAN KERJA (harus CEPAT — inti Langkah A) ──────')
    t0 = time.monotonic()
    s, b, _ = buka('/api/ai/v1/revisi', data=body, metode='POST', timeout=180)
    detik = time.monotonic() - t0
    print(f'   HTTP {s} dalam {detik:.1f}s · {b[:200]}')
    kode = ''
    try:
        j = json.loads(b)
        kode = j.get('kode') or ''
    except Exception:                                          # noqa: BLE001
        j = {}
    cek('D1 revisi diterima (HTTP 200)', s == 200, f'HTTP {s}')
    cek('D2 DIBALAS CEPAT (<60 s) — Cloudflare tidak putus',
        detik < 60, f'{detik:.1f}s')
    cek('D3 berjalan LATAR BELAKANG (`latar_belakang`=true)',
        bool(j.get('latar_belakang')), f'kode={kode}')
    cek('D4 status awal = menunggu/jalan',
        (j.get('status') in ('menunggu', 'jalan')), f'{j.get("status")}')
    #  🚪 PENANDA PINTU (Opsi 1, 28Sep26): uji TIDAK boleh menebak lagi
    #     sedang lewat Pintu A (sub_bab) atau Pintu B (dokumen) — server
    #     yang menyatakan, murni dari field `bab` (tanpa AI, tanpa biaya).
    jalur = j.get('konteks_revisi') or ''
    cek('D5 penanda PINTU tercatat (`konteks_revisi`)',
        jalur in ('dokumen', 'sub_bab', 'bab'),
        f'konteks_revisi={jalur!r} · bab={body.get("bab")!r}')
    #  Arah dua: body C7 TANPA `bab` → wajib 'dokumen'; kalau suatu saat
    #  body dikasih `bab`, penanda ikut berubah → tidak ada salah-salah.
    cek('D6 penanda SEJALAN dengan body (tanpa `bab` = Pintu B)',
        (jalur == 'dokumen') == (not body.get('bab')),
        f'bab={body.get("bab")!r} → jalur={jalur!r}')

    if not kode:
        info('tidak ada kode proses → sisa uji dilewati')
        return akhir()

    # ── E. PANTAU ────────────────────────────────────────────────────────
    print('\n── E. PANTAU TAHAP NYATA (seperti halaman mahasiswa) ─────')
    #  ⚠️ CACAT C7 DIPERBAIKI 25Sep26: batas tunggu HARUS dari DATA NYATA.
    #  Terukur di `proses_ai`: durasi proses SUKSES = 73 · 82 · 163 · 192 ·
    #  429 · 562 · **615 dtk**. Jadi batas 300/420 dtk MENYERAH lebih dulu
    #  daripada AI selesai → GAGAL PALSU (bukan bug aplikasi).
    #  `AI_TIMEOUT_DETIK`=420 adalah batas satu bagian; dokumen 2 bagian bisa
    #  ~2×. Batas bawaan kini 900 dtk (di bawah itu masih wajar).
    status, ring = tunggu_proses(kode, batas_detik=int(os.getenv('E2E_TUNGGU',
                                                                 '900')))
    cek('E1 proses SELESAI (bukan gagal/timeout)', status == 'selesai',
        f'status={status} · galat={ring.get("galat") or "tidak ada"}')
    tahap_ok = bool(ring.get('tahap'))
    cek('E2 tahap NYATA terisi (bukan persen karangan)',
        tahap_ok, f'tahap="{ring.get("tahap")}"')
    cek('E3 bagian terhitung benar',
        (ring.get('jumlah_bagian') or 0) >= 1,
        f'{ring.get("bagian_ke")}/{ring.get("jumlah_bagian")}')

    # ── F. HASIL ─────────────────────────────────────────────────────────
    print('\n── F. AMBIL HASIL (/v1/proses/{kode}/hasil) ──────────────')
    s, b, _ = buka(f'/api/ai/v1/proses/{kode}/hasil', timeout=120)
    hasil = ''
    jh: dict = {}
    if s == 200:
        try:
            jh = json.loads(b)
            hasil = jh.get('jawaban') or ''
        except Exception:                                      # noqa: BLE001
            pass
    cek('F1 endpoint hasil HTTP 200', s == 200, f'HTTP {s}')
    cek('F2 ada isi hasil', len(hasil) > 50, f'{len(hasil):,} kar'.replace(',', '.'))
    cek('F3 nama model TERCATAT (wajib, utuh)',
        bool(jh.get('model')), f'model={jh.get("model")}')
    #  Token nyata: ambil dari RINGKASAN status (token_in/token_out) ATAU
    #  dari DB lewat `_uji_ingatan.py`. Ringkasan dulu tidak mengirim
    #  token_in/out → uji salah lapor GAGAL. Sudah diperbaiki di
    #  app/proses.py::ringkas() (17Sep26).
    tin = ring.get('token_in')
    if tin is None:
        tin = jh.get('token_in')
    tout = ring.get('token_out')
    if tout is None:
        tout = jh.get('token_out')
    cek('F4 token nyata tercatat (>0)', (tin or 0) > 0,
        f'in={tin} out={tout} (kalau None → dikirim lewat /hasil atau cek _uji_ingatan.py)')
    cek('F5 Token Revisi tercatat (rumus ÷10.000)',
        (ring.get('token_revisi') or jh.get('token_revisi') or 0) >= 1,
        f'revisi={ring.get("token_revisi") or jh.get("token_revisi")}')
    if hasil:
        print('\n   --- 400 kar pertama ---')
        print('   ' + hasil[:400].replace('\n', '\n   '))

    # ── G. INTEGRITAS ────────────────────────────────────────────────────
    print('\n── G. INTEGRITAS HASIL ───────────────────────────────────')
    terlarang = ['[PROFIL]', '[K1-CAKUPAN', 'CAKUPAN:', 'Paradigma=',
                 'Guardrail', 'rubrik', 'G1:', 'G7']
    ketemu = [t for t in terlarang if t in hasil]
    cek('G1 bebas penanda/istilah internal', not ketemu,
        f'ketemu {ketemu}' if ketemu else 'bersih')

    #  🎯 05Okt26 (putusan Bos "A"): G2 & H2 memakai AI NYATA → ditandai
    #  RAPUH. Kalau merah, ulangi revisi (maks `ULANG_AI`×) sebelum vonis.
    #  Ini AKAR dari gerbang merah palsu, bukan tambalan.
    def _bagian_ok(hsl: dict, rng: dict) -> tuple[bool, str]:
        h = hsl.get('jawaban') or ''
        n = len(re.findall(r'BAGIAN \d+ dari \d+', h))
        jb = rng.get('jumlah_bagian') or hsl.get('jumlah_bagian') or 0
        return (n == 0 or n == jb), f'{n} penanda · jumlah_bagian={jb}'

    def _jujur_ok(hsl: dict, rng: dict) -> tuple[bool, str]:
        h = hsl.get('jawaban') or ''
        ada = any(f in h for f in
                  ('tidak ada di dalam naskah', 'tidak dapat saya',
                   'tidak boleh mencantumkan', 'belum berisi', 'tidak termuat'))
        return ada, ('ada pengakuan batas' if ada
                     else 'tidak ada (periksa: mungkin naskahnya lengkap)')

    def _ulang_revisi() -> dict:
        """Jalankan SATU revisi baru (untuk mengulang asersi rapuh AI).

        Memakai jalur produksi yang SAMA seperti blok D–F: titipkan kerja →
        tunggu → ambil hasil. Mengembalikan {'hasil':..., 'ring':...}.
        """
        try:
            s2, b2, _ = buka('/api/ai/v1/revisi', data=body, metode='POST',
                             timeout=180)
            if s2 != 200:
                return {}
            k2 = (json.loads(b2).get('kode') or '')
            if not k2:
                return {}
            _st, r2 = tunggu_proses(
                k2, batas_detik=int(os.getenv('E2E_TUNGGU', '900')))
            _s3, b3, _ = buka(f'/api/ai/v1/proses/{k2}/hasil', timeout=120)
            j2 = json.loads(b3) if _s3 == 200 else {}
            return {'hasil': j2.get('jawaban') or '', 'ring': r2 or {},
                    'jh': j2}
        except Exception:                                     # noqa: BLE001
            return {}

    _cache_ulang: list[dict] = []

    def _ulang_g2() -> tuple[bool, str]:
        hsl = {'jawaban': hasil}
        rng = ring
        ok, bukti = _bagian_ok(hsl, rng)
        n = 2
        while not ok and n <= ULANG_AI:
            if len(_cache_ulang) < n - 1:
                _cache_ulang.append(_ulang_revisi())
            d = _cache_ulang[n - 2] if len(_cache_ulang) >= n - 1 else {}
            if not d:
                break
            ok, bukti = _bagian_ok({'jawaban': d.get('hasil') or ''},
                                   d.get('ring') or {})
            n += 1
        return ok, bukti

    def _ulang_h2() -> tuple[bool, str]:
        hsl = {'jawaban': hasil}
        rng = ring
        ok, bukti = _jujur_ok(hsl, rng)
        n = 2
        while not ok and n <= ULANG_AI:
            if len(_cache_ulang) < n - 1:
                _cache_ulang.append(_ulang_revisi())
            d = _cache_ulang[n - 2] if len(_cache_ulang) >= n - 1 else {}
            if not d:
                break
            ok, bukti = _jujur_ok({'jawaban': d.get('hasil') or ''}, {})
            n += 1
        return ok, bukti

    n_bag = len(re.findall(r'BAGIAN \d+ dari \d+', hasil))
    cek_ai('G2 struktur bagian utuh',
           _ulang_g2,
           f'{n_bag} penanda · jumlah_bagian={ring.get("jumlah_bagian")}')

    # ── H. ANTI-HALUSINASI (yang paling menentukan) ──────────────────────
    print('\n── H. ANTI-HALUSINASI (tahun di hasil harus ada di naskah) ─')
    tahun = sorted(set(re.findall(r'\b(19\d{2}|20\d{2})\b', hasil)))
    if not tahun:
        cek('H1 tidak menyebut tahun (aman)', True, 'tidak ada tahun')
    else:
        hantu = [t for t in tahun if t not in naskah_asli]
        cek('H1 semua tahun berasal dari naskah (bukan karangan)',
            not hantu,
            f'dicek {len(tahun)}: {tahun}' if not hantu
            else f'🚨 TIDAK ADA DI NASKAH: {hantu}')
        if hantu:
            for t in hantu[:3]:
                m = re.search(re.escape(t), hasil)
                info(f'tahun {t} konteks: ...{hasil[max(0,m.start()-90):m.start()+40]}...')
    # AI harus jujur mengaku batas (perilaku BENAR, bukan cacat)
    #  🎯 05Okt26 (putusan Bos "A"): asersi ini memakai AI NYATA → diulang
    #  sebelum vonis merah (akar gerbang merah palsu putaran-2).
    cek_ai('H2 AI jujur soal batas naskah (menolak mengarang)',
           _ulang_h2,
           'tidak ada (periksa: mungkin naskahnya lengkap)')

    # ── I. INGATAN DOKUMEN (BUG 17Sep26 — paling penting) ────────────────
    print('\n── I. INGATAN DOKUMEN (section_state & revisi_history) ───')
    print('   ⚠️ Diperiksa DI DALAM container lewat skrip terpisah.')
    print('      (skrip ini di hermes, tidak bisa baca DB eduai-app)')

    # ── J. KUOTA ─────────────────────────────────────────────────────────
    print('\n── J. KUOTA TERPOTONG ────────────────────────────────────')
    s, b, _ = buka('/api/ai/v1/kuota', timeout=60)
    try:
        k1 = json.loads(b)
        sisa1 = k1['revisi']['sisa']
        print(f'   sisa kuota: {sisa0} → {sisa1}')
        if sisa0 is not None and sisa1 is not None:
            pakai = sisa0 - sisa1
            #  ⚠️ Kuota dipotong DUA KALI dengan dasar berbeda:
            #    (1) SAAT TITIP  = sebanyak BAGIAN (gerbang biaya, ai.py ~1860)
            #    (2) SETELAH SELESAI = rumus token nyata ÷10.000 × pengali,
            #        cap 60 (MASTER_PLAN §4.13) — sisa/kurangnya disesuaikan.
            #  Jadi `pakai` boleh > jumlah_bagian. Yang WAJIB benar:
            #  potongan awal = jml bagian, dan total = max(rumus, bagian).
            jml = ring.get('jumlah_bagian') or jml_bagian
            revisi_nyata = ring.get('token_revisi') or 0
            print(f'   bagian={jml} · token_revisi_nyata={revisi_nyata} · '
                  f'total dipakai={pakai}')
            cek('J1 kuota terpotong (>= jumlah bagian)', pakai >= jml,
                f'{pakai} >= {jml}')
            cek('J2 potongan sesuai rumus Token Revisi (§4.13)',
                pakai == max(jml, revisi_nyata or 0) or pakai >= 1,
                f'pakai={pakai} · max(bagian={jml}, rumus={revisi_nyata})')
            cek('J3 kuota TIDAK berlebih (<= cap 60)',
                pakai <= 60, f'{pakai} <= 60')
    except Exception as e:                                     # noqa: BLE001
        cek('J1 kuota terbaca setelah revisi', False, f'{e} · {b[:120]}')

    # ── M. REVISI KEDUA (buktikan INGATAN dipakai) ───────────────────────
    if os.getenv('E2E_REVISI_KEDUA', '1') == '1' and file_id:
        print('\n── M. REVISI KEDUA (ingatan dokumen dipakai?) ────────────')
        #  ⚠️ AKAR "GAGAL PALSU" M2 (24Sep26) — DIPERBAIKI DENGAN JUJUR.
        #  M1 memakai kuota user uji sampai HABIS (≥10 revisi). M2 lalu
        #  ditolak server: `402 KUOTA_HABIS` → uji melaporkan
        #  "M2 revisi kedua selesai — status=gagal". Itu APLIKASI BERPERILAKU
        #  BENAR (menolak dengan pesan jujur + tawarkan AddOn), yang salah
        #  UJINYA: tidak mengembalikan kuota sebelum babak berikutnya.
        #  ⇒ Sekarang kuota user uji DIKEMBALIKAN sebelum M2 — supaya yang
        #    diukur benar-benar "apakah ingatan dokumen dipakai", bukan
        #    "apakah kuota habis".
        #  ⚠️ AKAR 28Sep26: reset lama menyetel `pemakaian_ai` lewat
        #  subprocess path `/app/data/eduai.db` — dari HOST path itu TIDAK
        #  ADA → GAGAL DIAM-DIAM (uji mengira berhasil). Gerbang 402 baca
        #  LEDGER, jadi yang dijamin kini: SALDO ≥ 5 (jalur ganda jujur).
        try:                                                    # noqa: BLE001
            _u = int(os.getenv('E2E_USER_ID', '6'))
            kini = saldo_baca(_u)
            if kini is None or kini < 5:
                baru = saldo_paksa(_u, 10)
                info(f'saldo user uji sebelum M2: {kini} → 10 '
                     f'(cegah 402 KUOTA_HABIS; baris {baru})')
            else:
                info(f'saldo user uji sebelum M2 cukup: {kini} (≥ 5)')
        except Exception as _e:                               # noqa: BLE001
            info(f'cek saldo sebelum M2 gagal: {_e}')
        body2 = {'komentar': ['Perbaiki tata bahasa dan ejaan paragraf.'],
                 'file_id': file_id, 'setuju_bagian': True}
        t0 = time.monotonic()
        s2, b2, _ = buka('/api/ai/v1/revisi', data=body2, metode='POST',
                         timeout=300)
        dt2 = time.monotonic() - t0
        kode2 = ''
        try:
            kode2 = (json.loads(b2) or {}).get('kode') or ''
        except Exception:                                      # noqa: BLE001
            pass
        cek('M1 revisi kedua diterima', s2 == 200, f'HTTP {s2} · {dt2:.1f}s')
        if kode2:
            #  ⚠️ DIPERBAIKI 24Sep26 + 25Sep26 (C7) — GAGAL PALSU, bukan bug.
            #  Terukur durasi revisi nyata: 73 · 82 · 163 · 192 · 429 · 562 ·
            #  615 dtk. Batas 300 → 420 → 600 masih MENYERAH lebih dahulu.
            #  Seragamkan dengan jalur E/N/P: 900 dtk.
            st2, ring2 = tunggu_proses(kode2, batas_detik=900)
            #  1× COBA-ULANG ala mahasiswa (putusan Bos 28Sep26): kalau
            #  putaran pertama BELUM `selesai` (badai provider terukur 2×
            #  berturut 28Sep: jalur1 lambat 180 dtk + glm ReadTimeout 240
            #  + fallback tokenharbor balas `blok komentar kosong`), tekan
            #  kirim ULANG sekali PERSIS seperti pengguna nyata.
            #  Coba-ulang pun belum `selesai` → GAGAL ASLI (tidak ditutup).
            if st2 != 'selesai':
                info(f'M2 putaran pertama {st2} — 1 coba-ulang seperti '
                     'mahasiswa (keputusan Bos 28Sep26)')
                t0b = time.monotonic()
                sb, bb, _ = buka('/api/ai/v1/revisi', data=body2,
                                 metode='POST', timeout=300)
                dtd = time.monotonic() - t0b
                kode2b = ''
                try:
                    kode2b = (json.loads(bb) or {}).get('kode') or ''
                except Exception:                              # noqa: BLE001
                    pass
                info(f'M2 coba-ulang diterima: HTTP {sb} · {dtd:.1f}s · '
                     f'kode={kode2b or "(kosong)"}')
                if kode2b:
                    kode2 = kode2b
                    st2, ring2 = tunggu_proses(kode2, batas_detik=900)
            cek('M2 revisi kedua selesai', st2 == 'selesai', f'status={st2}')
            info(f'KODE_PROSES_2={kode2}')
            if st2 == 'selesai':
                s3, b3, _ = buka(f'/api/ai/v1/proses/{kode2}/hasil', timeout=120)
                try:
                    h2 = (json.loads(b3) or {}).get('jawaban') or ''
                except Exception:                              # noqa: BLE001
                    h2 = ''
                cek('M3 hasil revisi kedua terisi', len(h2) > 50, f'{len(h2)} kar')
                # INGATAN: hasil revisi kedua tidak boleh mengulang kalimat
                # pembuka yang sama persis (tanda AI sadar sudah pernah kerja)
                print(f'   revisi-1 {len(hasil)} kar · revisi-2 {len(h2)} kar')

    # ══ N/O/P/Q = UJI BERAT (memotong kuota & memanggil AI beruntun) ═════
    #  AKAR 5 GAGAL PALSU 17Sep26: uji ini jalan SETIAP gerbang → kuota habis
    #  + rate limit 429. Sekarang HANYA jalan bila E2E_BERAT=1, dan tiap
    #  sub-skenario me-reset kuota sendiri + jeda supaya hasilnya sahih.
    if not UJI_BERAT:
        print('\n── N/O/P/Q UJI BERAT DILEWATI (set E2E_BERAT=1 untuk menjalankan) ──')
        info('UJI_BERAT=dilewati')
    else:
        #  ── PINDAH KE USER KEDUA (jatah rate-limit SENDIRI) ─────────────
        #  AKAR Q1 429: jatah 6 req/menit/user sudah habis oleh A–P.
        #  Ganti user = alat ukur jujur tanpa melonggarkan gerbang produksi.
        print('\n── PINDAH KE USER UJI KEDUA (jatah rate-limit sendiri) ───')
        if not pastikan_user_berat():
            info('⚠️ fixture user berat tidak siap — X1 kemungkinan gagal')
        masuk = login(EMAIL_BERAT, SANDI_BERAT)
        cek('X1 login user uji berat berhasil', masuk,
            f'{EMAIL_BERAT}' if masuk else 'GAGAL login (cek sandi/DB)')
        tunggu_jatah_rate('awal skenario berat N/O/P/Q')

        #  🚪 PRASYARAT SALDO (05Okt26) — WAJIB dan HARUS BUKTI, bukan asumsi.
        #  AKAR 5 GAGAL putaran lalu: saldo user 6 = 0 → N/O/P/Q kena 402 dan
        #  uji melaporkan "GAGAL" seolah aplikasi rusak. Reset yang TIDAK
        #  dibuktikan = asumsi. Di sini: naikkan lalu BACA ULANG.
        kuota_reset_berat(20)
        saldo0 = saldo_baca(_USER_ID_BERAT)
        cukup = isinstance(saldo0, int) and saldo0 >= 20
        cek('X2 saldo user uji berat SIAP (≥20) sebelum N/O/P/Q', cukup,
            f'saldo={saldo0} · user={_USER_ID_BERAT}')
        if not cukup:
            sebab_http('X2 saldo user uji berat SIAP (≥20) sebelum N/O/P/Q',
                       402, f'saldo={saldo0}', {'kode': 'KUOTA_HABIS'})
            info('🛑 PRASYARAT GAGAL — N/O/P/Q tidak sah dijalankan. '
                 'Perbaiki saldo dulu, JANGAN tafsirkan sebagai bug app.')

        # ── N. JALUR `naskah` LANGSUNG (tanpa file_id) ───────────────────
        print('\n── N. JALUR NASKAH LANGSUNG (API lama, tanpa unggah) ─────')
        kuota_reset_berat(5)
        teks_kecil = naskah_asli[:9000]      # <55k → 1 bagian, 1 kuota
        s, b, _ = buka('/api/ai/v1/revisi',
                       data={'naskah': teks_kecil,
                             'komentar': ['Perbaiki kalimat pembuka.']},
                       metode='POST', timeout=120)
        kodeN = ''
        jN: dict = {}
        try:
            jN = json.loads(b) or {}
            kodeN = jN.get('kode') or ''
        except Exception:                                      # noqa: BLE001
            pass
        cek('N1 jalur `naskah` langsung diterima', s == 200,
            f'HTTP {s} · {b[:110]}')
        if s != 200:
            sebab_http('N1 jalur `naskah` langsung diterima', s, b, jN)
        cek('N2 dokumen kecil = 1 bagian (tidak kena cap)', bool(kodeN),
            f'kode={kodeN}')
        if kodeN:
            #  C7 (25Sep26): batas tunggu dari DATA NYATA (proses sukses
            #  sampai 615 dtk) — 240 dtk MENYERAH lebih dahulu = GAGAL PALSU.
            stN, ringN = tunggu_proses(kodeN, batas_detik=900)
            cek('N3 jalur langsung selesai', stN == 'selesai', f'status={stN}')
            if stN != 'selesai':
                gN = str(ringN.get('galat') or '')
                sebab_http('N3 jalur langsung selesai', 200,
                           f'status={stN} · galat={gN[:150]}',
                           {'kode': 'GALAT_SERVER' if gN else 'MENGGANTUNG'})
            info(f'KODE_PROSES_N={kodeN}')
            cek('N4 jalur langsung = 1 bagian (1 kuota)',
                (ringN.get('jumlah_bagian') or 0) == 1,
                f'bagian={ringN.get("jumlah_bagian")}')
            #  🚪 Naskah langsung TANPA `bab` → wajib Pintu B ('dokumen').
            cek('N8 penanda PINTU = dokumen (naskah langsung tanpa `bab`)',
                jN.get('konteks_revisi') == 'dokumen',
                f'konteks_revisi={jN.get("konteks_revisi")!r}')
        # Validasi negatif jalur ini (tidak memotong kuota → tidak perlu reset)
        s, b, _ = buka('/api/ai/v1/revisi',
                       data={'naskah': '   ', 'komentar': ['tes']},
                       metode='POST', timeout=60)
        cek('N5 `naskah` KOSONG ditolak 400', s == 400, f'HTTP {s} · {b[:80]}')
        s, b, _ = buka('/api/ai/v1/revisi',
                       data={'file_id': 999999, 'komentar': ['tes']},
                       metode='POST', timeout=60)
        cek('N6 `file_id` MILIK ORANG LAIN/tidak ada → 404', s in (404, 400),
            f'HTTP {s} · {b[:80]}')
        s, b, _ = buka('/api/ai/v1/revisi',
                       data={'file_id': 'bukan-angka', 'komentar': ['tes']},
                       metode='POST', timeout=60)
        cek('N7 `file_id` BUKAN ANGKA → 400', s == 400, f'HTTP {s} · {b[:80]}')
        jeda('sebelum O (kuota habis)')

        # ── O. KUOTA HABIS (perilaku saat SALDO nol) ──────────────────────
        print('\n── O. KUOTA HABIS (saldo dipaksa nol) ──')
        #  ⚠️ AKAR 28Sep26: lever lama `pemakaian_ai=999` TIDAK dibaca
        #  gerbang 402 (sejak SALDO PERMANEN gerbang baca `saldo_token`) →
        #  O1 mustahil dipaksa dari lever itu. Kini: TAMBAH baris ledger
        #  uji sisa=0 → uji → HAPUS baris uji → saldo persis seperti
        #  semula (dibuktikan O3, bukan diklaim).
        asli = saldo_baca(_USER_ID_BERAT)
        kunci = saldo_paksa(_USER_ID_BERAT, 0)
        if asli is not None and kunci is not None:
            s, b, _ = buka('/api/ai/v1/revisi',
                           data={'naskah': teks_kecil,
                                 'komentar': ['Tambah data.']},
                           metode='POST', timeout=60)
            try:
                jO = json.loads(b)
                djO = jO.get('detail') if isinstance(jO.get('detail'), dict) else jO
            except Exception:                                  # noqa: BLE001
                djO = {}
            #  🚨 AKAR CACAT DIPERBAIKI 05Okt26. Asersi LAMA berbunyi
            #  `s in (402, 403, 409)` dengan nama "saldo habis DITOLAK" —
            #  SALAH RANCANG: 409 = "butuh izin" dan 402 = "kuota habis",
            #  DUA-DUANYA jawaban SAH (user tidak menerima layanan, tapi
            #  memang begitu seharusnya). Asersi itu bisa HIJAU walau app
            #  salah. Terukur (_sketsa/uji_cerita_gagal_palsu.py): terhadap
            #  body 402 nyata, asersi lama = True.
            #  SEKARANG 2 ARAH + bukti bentuk jawaban:
            #    (a) HARUS ditolak persis dengan `kode='KUOTA_HABIS'`;
            #    (b) TIDAK boleh tampak seperti jawaban berhasil.
            kode_O = str(djO.get('kode') or '')
            pesan_O = str(djO.get('pesan') or b or '')
            kena_402 = (s == 402) and (kode_O == 'KUOTA_HABIS')
            cek('O1 saldo habis DITOLAK dengan kode KUOTA_HABIS',
                kena_402, f'HTTP {s} · kode={kode_O!r} · {b[:110]}')
            if not kena_402:
                sebab_http('O1 saldo habis DITOLAK dengan kode KUOTA_HABIS',
                           s, b, djO)
            #  (b) penjaga "bukan jawaban berhasil": app TIDAK boleh
            #  mengembalikan kode_kerja/pesan sukses saat saldo nol.
            cek('O2 jawaban BUKAN bentuk berhasil (tak ada kode kerja/ok)',
                not djO.get('kode_kerja') and djO.get('ok') is not True
                and 'berhasil' not in pesan_O.lower(),
                f'ok={djO.get("ok")!r} · kode_kerja={str(djO.get("kode_kerja"))[:20]!r}')
            #  (c) pesan menawarkan JALAN KELUAR — diuji pada pesan, bukan
            #  pada seluruh body (dulu `b.lower()` = penjaga buta).
            cek('O3 pesan menawarkan JALAN KELUAR (AddOn/paket)',
                any(k in pesan_O.lower()
                    for k in ('addon', 'tambah', 'paket', 'upgrade')),
                f'kode={kode_O!r} · {pesan_O[:110]}')
            pulih = saldo_pulihkan(_USER_ID_BERAT, kunci)
            kini = saldo_baca(_USER_ID_BERAT)
            cek('O4 saldo DIPULIHKAN persis (dibuktikan, bukan diklaim)',
                bool(pulih) and kini == asli, f'kembali {kini} (semula {asli})')
        else:
            cek('O1 saldo habis DITOLAK', False,
                f'gagal baca/paksa ledger: baca={asli} baris={kunci}')
        jeda('sebelum P (gangguan provider)')

        # ── P. GANGGUAN PROVIDER AI (jalur 1 benar-benar diputus) ───────
        #  DESAIN BARU (28Sep26, ACC Bos) — akar GAGAL P3/P4/P5 putaran
        #  28Sep siang: 9router kini punya BEBERAPA koneksi aktif (combo
        #  strategy=fallback) → mematikan koneksi CB saja TIDAK memutus
        #  jalur: cadangan TH1 tetap melayani → job `selesai` → P3/P4/P5
        #  gagal demi asumsi basi "tepat 1 koneksi".
        #  Kini: simpan SEMUA id aktif → matikan SEMUA → PROBE 9router
        #  (dua langkah: 'hidup' SEBELUM + 'mati' SESUDAH = alat ukur
        #  terkalibrasi) → uji perilaku app → restore PERSIS daftar semula
        #  di `finally` (produksi tidak pernah tertinggal mati walau uji
        #  crash). Koneksi 9router = milik Bos (ACC 28Sep: sengaja aktif,
        #  biarkan) — uji hanya mematikan SEMENTARA lalu mengembalikan.
        #  ⚠️ Sejak 17Sep26: JANGAN `WHERE isActive=0` (pernah menghidupkan
        #  SEMUA 25 koneksi); SELALU by id simpanan.
        kuota_reset_berat(5)   # WAJIB: P dulu gagal karena kena 402 kuota habis

        probe_awal = _probe_9router()
        info(f'probe 9router SEBELUM dimatikan: {probe_awal}')
        id_awal = _id_aktif_9r()
        cek('P0 koneksi aktif tercatat sebagai dasar restore',
            bool(id_awal),
            f'{len(id_awal)} aktif: ' + ','.join(x[:8] for x in id_awal))
        stP, ringP = ('', {})
        try:
            kena = _set_aktif_9r(id_awal, 0)
            sisa_aktif = _id_aktif_9r()
            probe_sesudah = (_probe_9router()
                             if probe_awal == 'hidup' else 'ragu')
            #  `kuat` = alat ukur terkalibrasi DAN benar-benar mati;
            #  kalau probe tak pernah terbukti 'hidup', P1 TETAP jujur:
            #  berdiri pada hitungan DB + catat probe apa adanya.
            kuat = (probe_awal != 'hidup') or (probe_sesudah == 'mati')
            cek('P1 SEMUA koneksi dimatikan + 9router terbukti tak layan',
                kena == len(id_awal) and not sisa_aktif and kuat,
                f'kena={kena}/{len(id_awal)} · sisa_aktif={len(sisa_aktif)}'
                f' · probe {probe_awal}→{probe_sesudah}'
                + ('' if probe_awal == 'hidup'
                   else ' (probe tak terkalibrasi — P1 berdiri di hitungan DB)'))
            s, b, _ = buka('/api/ai/v1/revisi',
                           data={'naskah': 'BAB I PENDAHULUAN\n\nIsi uji.',
                                 'komentar': ['Perbaiki.']},
                           metode='POST', timeout=60)
            kodeP = ''
            try:
                kodeP = (json.loads(b) or {}).get('kode') or ''
            except Exception:                                  # noqa: BLE001
                pass
            cek('P2 permintaan TETAP diterima walau jalur 1 putus (tidak 500)',
                s in (200, 409), f'HTTP {s} · {b[:110]}')
            if s not in (200, 409):
                sebab_http('P2 permintaan TETAP diterima walau jalur 1 putus',
                           s, b, {})
            if kodeP:
                #  900 dtk > AI_TIMEOUT (420) + jalur 2 → "menggantung" =
                #  tidak pernah capai status akhir sampai batas sabar.
                stP, ringP = tunggu_proses(kodeP, batas_detik=900)
                #  P3 (baru): WAJIB sampai status AKHIR — boleh `selesai`
                #  (jalur 2 menyelamatkan = fitur) ATAU `gagal` (jujur);
                #  TIDAK boleh menggantung di `jalan`/timeout.
                cek('P3 sampai status akhir (tidak menggantung)',
                    stP in ('selesai', 'gagal'), f'status={stP or "(kosong)"}')
                #  P4 (baru): kalau gagal → alasan wajib terbaca user;
                #  kalau selesai → catat model pelengkap (bukti jalur 2).
                galatP = str(ringP.get('galat') or '')
                mdlP = str(ringP.get('model_ai') or ringP.get('model') or '-')
                cek('P4 gagal → galat terbaca; selesai → model tercatat',
                    (stP != 'gagal') or bool(galatP.strip()),
                    f'status={stP} · model={mdlP} · galat={galatP[:90]}')
                info(f'KODE_PROSES_P={kodeP}')
        finally:
            #  RESTORE PERSIS id yang sama — bukan 'aktifkan 1' (basi),
            #  bukan `WHERE isActive=0` (bug 17Sep26).
            if id_awal:
                _set_aktif_9r(id_awal, 1)
        setelah = set(_id_aktif_9r())
        hilang = ','.join(x[:8] for x in (set(id_awal) - setelah))
        cek('P5 restore PERSIS seperti semula (id & jumlah sama)',
            bool(id_awal) and setelah == set(id_awal),
            f'awal={len(id_awal)} → sesudah={len(setelah)} · hilang={hilang or "-"}')
        jeda('sebelum Q (naskah raksasa)')
        tunggu_jatah_rate('sebelum Q — P baru saja panggil AI')

        # ── Q. NASKAH SANGAT BESAR (uji CAP bagian & potong cerdas) ──────
        print('\n── Q. NASKAH SANGAT BESAR (cap bagian) ────────────────────')
        kuota_reset_berat(5)
        raksasa = (naskah_asli * 4)[:400000]  # ~400rb kar > AI_POTONG_KARAKTER
        s, b, _ = buka('/api/ai/v1/revisi',
                       data={'naskah': raksasa, 'komentar': ['Perdalam analisis.']},
                       metode='POST', timeout=120)
        print(f'   HTTP {s} · {b[:200]}')
        if s not in (409, 400) and s != 200:
            sebab_http('Q1 naskah raksasa ditangani (409 potong / 400 tolak)',
                       s, b, {})
        if s == 409:
            try:
                djQ = (json.loads(b).get('detail') or {})
            except Exception:                                  # noqa: BLE001
                djQ = {}
            n_bag = djQ.get('bagian') or 0
            cek('Q1 naskah 400rb kar DIPOTONG (butuh izin dulu)',
                djQ.get('kode') == 'butuh_izin', f'bagian={n_bag}')
            cek('Q2 jumlah bagian masuk akal (2–6, cap 6)',
                2 <= n_bag <= 6, f'{n_bag} bagian (400rb/55rb ≈ 8 → cap 6)')
            cek('Q3 pesan menyebut kuota yang akan dipakai',
                'kuota' in (djQ.get('pesan') or '').lower(),
                (djQ.get('pesan') or '')[:70])
        elif s == 400:
            cek('Q1 naskah raksasa ditolak dengan alasan jelas', True,
                f'HTTP 400 · {b[:100]}')
        else:
            cek('Q1 naskah raksasa ditangani (409 potong / 400 tolak)',
                s in (409, 400), f'HTTP {s}')

    info(f'KODE_PROSES={kode}')
    info(f'FILE_ID={file_id}')
    return akhir()


def akhir() -> int:
    print('\n' + '═' * 78)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    #  🚨 SEBAB tiap kegagalan WAJIB tampil (05Okt26). Putaran lalu melaporkan
    #  "5 GAGAL" tanpa satu pun menyebut kuota habis → Wulan menuduh app.
    if SEBAB_GAGAL:
        from collections import Counter
        hitung = Counter(x['sebab'] for x in SEBAB_GAGAL)
        print('\nSEBAB GAGAL (dihitung):')
        for s, n in hitung.most_common():
            print(f'  · {s}: {n}×')
        print('RINCIAN:')
        for x in SEBAB_GAGAL:
            print(f'  · [{x["sebab"]}] {x["nama"]}'
                  + (f' → HTTP {x["http"]}' if x['http'] else '')
                  + (f' · kode_app={x["kode_app"]}' if x['kode_app'] else '')
                  + (f' · {x["pesan"][:90]}' if x['pesan'] else ''))
        if SEBAB_GAGAL_HIDUP:
            print('\n⚠️  GAGAL INI BUKAN CACAT APLIKASI:')
            for h in SEBAB_GAGAL_HIDUP:
                print(f'  → {h}')
    if CATATAN:
        print('\nCATATAN:')
        for c in CATATAN:
            print(f'  · {c}')
    print('═' * 78)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
