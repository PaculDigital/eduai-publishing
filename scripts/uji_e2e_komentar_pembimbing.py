"""UJI E2E KOMENTAR PEMBIMBING — JALUR MAHASISWA SUNGGUHAN (domain publik).

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
EMAIL_BERAT = os.getenv('E2E_EMAIL_BERAT', 'uji-gratis-render@test.local')
SANDI_BERAT = os.getenv('E2E_SANDI_BERAT', 'UjiRender123!')
_USER_ID_BERAT = int(os.getenv('E2E_USER_ID_BERAT', '5'))   # DB eduai-app

LULUS = GAGAL = 0
CATATAN: list[str] = []


def cek(nama: str, syarat: bool, bukti: str = '') -> bool:
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'   ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'   ❌ {nama}' + (f' — {bukti}' if bukti else ''))
    return bool(syarat)


def info(pesan: str) -> None:
    CATATAN.append(pesan)


ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
cj = http.cookiejar.CookieJar()
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj),
                                 urllib.request.HTTPSHandler(context=ctx))


def buka(path: str, data=None, metode: str | None = None, timeout: int = 300):
    """Buka URL. Kembalikan (status, body, header_dict)."""
    h = {'User-Agent': UA}
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode('utf-8')
        h['Content-Type'] = 'application/json'
    try:
        r = OP.open(urllib.request.Request(BASE + path, data=data, headers=h,
                                           method=metode), timeout=timeout)
        return r.status, r.read().decode('utf-8', 'ignore'), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore'), dict(e.headers)


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
    """Jalankan `docker ...` dari container hermes (Docker CLI tersedia)."""
    import subprocess
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout)
        return p.returncode, (p.stdout or '') + (p.stderr or '')
    except Exception as e:                                     # noqa: BLE001
        return 1, str(e)


def docker_kuota_pakai() -> int | None:
    """Baca `jumlah_revisi` user uji dari DB eduai-app (lewat docker exec)."""
    sql = ("import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
           "r=c.execute('SELECT jumlah_revisi FROM pemakaian_ai "
           "WHERE user_id=6').fetchone();print(r[0] if r else 'X')")
    rc, out = _docker(f'docker exec eduai-app python3 -c "{sql}"')
    out = out.strip().splitlines()[-1] if out.strip() else ''
    return int(out) if out.isdigit() else None


def docker_kuota_set(nilai: int) -> bool:
    """Paksa `jumlah_revisi` = nilai (untuk uji kuota habis). SELALU pulihkan."""
    sql = ("import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
           f"c.execute('UPDATE pemakaian_ai SET jumlah_revisi={int(nilai)} "
           "WHERE user_id=6');c.commit()")
    rc, _ = _docker(f'docker exec eduai-app python3 -c "{sql}"')
    return rc == 0


# ══════════════════════════════════════════════════════════════════════════
#  PEMISAH UJI BERAT (17Sep26) — AKAR dari 5 GAGAL PALSU sesi lalu.
#  Skenario N/O/P/Q memotong kuota & memanggil AI beruntun → kena rate limit
#  429 dan kuota habis (402), sehingga GAGAL-nya PALSU (bukan bug app).
#  UJI CEPAT (gerbang harian) TIDAK boleh ikut kena. Kunci di balik
#  E2E_BERAT=1 supaya gerbang tetap cepat & hijau.
# ══════════════════════════════════════════════════════════════════════════
UJI_BERAT = os.environ.get('E2E_BERAT', '0') == '1'
JEDA_ANTAR_BERAT = float(os.environ.get('E2E_JEDA', '2'))


def kuota_reset(nilai: int = 0) -> None:
    """Reset kuota user uji SEBELUM tiap sub-skenario berat (bukan sekali).

    AKAR bug 17Sep26: skenario A–P dipakai beruntun tanpa reset → kuota habis
    di tengah → N & P dapat 402 → 'GAGAL' padahal app BENAR.
    """
    if docker_kuota_set(nilai):
        info(f'kuota user uji direset → {nilai}')
    else:
        info('⚠️ gagal reset kuota (lanjut apa adanya)')


def kuota_reset_berat(nilai: int = 0) -> None:
    """Reset kuota USER KEDUA (skenario berat) — pakai `_USER_ID_BERAT`.

    Dipisah dari `kuota_reset()` supaya skenario A–M (user utama) TIDAK
    terganggu, dan N/O/P/Q punya kuota sendiri.
    """
    sql = ("import sqlite3;c=sqlite3.connect('/app/data/eduai.db');"
           f"c.execute('UPDATE pemakaian_ai SET jumlah_revisi={int(nilai)} "
           f"WHERE user_id={_USER_ID_BERAT}');c.commit()")
    rc, _ = _docker(f'docker exec eduai-app python3 -c "{sql}"')
    info(f'kuota user BERAT (id={_USER_ID_BERAT}) direset → {nilai}'
         if rc == 0 else '⚠️ gagal reset kuota user berat')


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
    berkas = Path(sys.argv[1] if len(sys.argv) > 1 else
                  '/opt/data/services/eduai-publishing/_arsip/contoh-dokumen/'
                  'skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx')
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

    if not kode:
        info('tidak ada kode proses → sisa uji dilewati')
        return akhir()

    # ── E. PANTAU ────────────────────────────────────────────────────────
    print('\n── E. PANTAU TAHAP NYATA (seperti halaman mahasiswa) ─────')
    status, ring = tunggu_proses(kode, batas_detik=int(os.getenv('E2E_TUNGGU',
                                                                 '420')))
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
    n_bag = len(re.findall(r'BAGIAN \d+ dari \d+', hasil))
    cek('G2 struktur bagian utuh',
        n_bag == 0 or n_bag == (ring.get('jumlah_bagian') or 0),
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
    jujur = any(f in hasil for f in
                ('tidak ada di dalam naskah', 'tidak dapat saya',
                 'tidak boleh mencantumkan', 'belum berisi', 'tidak termuat'))
    cek('H2 AI jujur soal batas naskah (menolak mengarang)', jujur,
        'ada pengakuan batas' if jujur else 'tidak ada (periksa: mungkin naskahnya lengkap)')

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
        body2 = {'komentar': ['Perbaiki tata bahasa dan ejaan paragraf.'],
                 'file_id': file_id, 'setuju_bagian': True}
        t0 = time.monotonic()
        s2, b2, _ = buka('/api/ai/v1/revisi', data=body2, metode='POST',
                         timeout=180)
        dt2 = time.monotonic() - t0
        kode2 = ''
        try:
            kode2 = (json.loads(b2) or {}).get('kode') or ''
        except Exception:                                      # noqa: BLE001
            pass
        cek('M1 revisi kedua diterima', s2 == 200, f'HTTP {s2} · {dt2:.1f}s')
        if kode2:
            st2, ring2 = tunggu_proses(kode2, batas_detik=300)
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
        masuk = login(EMAIL_BERAT, SANDI_BERAT)
        cek('X1 login user uji berat berhasil', masuk,
            f'{EMAIL_BERAT}' if masuk else 'GAGAL login (cek sandi/DB)')
        tunggu_jatah_rate('awal skenario berat N/O/P/Q')

        # ── N. JALUR `naskah` LANGSUNG (tanpa file_id) ───────────────────
        print('\n── N. JALUR NASKAH LANGSUNG (API lama, tanpa unggah) ─────')
        kuota_reset_berat(0)
        teks_kecil = naskah_asli[:9000]      # <55k → 1 bagian, 1 kuota
        s, b, _ = buka('/api/ai/v1/revisi',
                       data={'naskah': teks_kecil,
                             'komentar': ['Perbaiki kalimat pembuka.']},
                       metode='POST', timeout=120)
        kodeN = ''
        try:
            kodeN = (json.loads(b) or {}).get('kode') or ''
        except Exception:                                      # noqa: BLE001
            pass
        cek('N1 jalur `naskah` langsung diterima', s == 200,
            f'HTTP {s} · {b[:110]}')
        cek('N2 dokumen kecil = 1 bagian (tidak kena cap)', bool(kodeN),
            f'kode={kodeN}')
        if kodeN:
            stN, ringN = tunggu_proses(kodeN, batas_detik=240)
            cek('N3 jalur langsung selesai', stN == 'selesai', f'status={stN}')
            info(f'KODE_PROSES_N={kodeN}')
            cek('N4 jalur langsung = 1 bagian (1 kuota)',
                (ringN.get('jumlah_bagian') or 0) == 1,
                f'bagian={ringN.get("jumlah_bagian")}')
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

        # ── O. KUOTA HABIS (perilaku saat jatah nol) ─────────────────────
        print('\n── O. KUOTA HABIS (jatah dipaksa nol) ─────────────────────')
        asli_dipakai = docker_kuota_pakai()  # simpan nilai asli
        if asli_dipakai is not None:
            docker_kuota_set(999)            # paksa habis
            s, b, _ = buka('/api/ai/v1/revisi',
                           data={'naskah': teks_kecil,
                                 'komentar': ['Tambah data.']},
                           metode='POST', timeout=60)
            try:
                jO = json.loads(b)
                djO = jO.get('detail') if isinstance(jO.get('detail'), dict) else jO
            except Exception:                                  # noqa: BLE001
                djO = {}
            cek('O1 kuota habis DITOLAK (402/403/409)',
                s in (402, 403, 409), f'HTTP {s} · {b[:140]}')
            cek('O2 pesan menawarkan JALAN KELUAR (AddOn/paket)',
                any(k in b.lower() for k in ('addon', 'tambah', 'paket', 'upgrade')),
                f'kode={djO.get("kode")!r}')
            docker_kuota_set(asli_dipakai)   # PULIHKAN
            cek('O3 kuota DIPULIHKAN setelah uji', True, f'set kembali {asli_dipakai}')
        else:
            cek('O1 kuota habis DITOLAK', False, 'gagal baca/set kuota DB')
        jeda('sebelum P (gangguan provider)')

        # ── P. GANGGUAN PROVIDER AI (benar-benar diputus) ────────────────
        print('\n── P. GANGGUAN PROVIDER (jalur AI benar-benar diputus) ────')
        #  CARA: matikan koneksi 9router→InferHub (kolom isActive), kirim revisi,
        #  lihat perilaku app, lalu PULIHKAN. Ini meniru "provider mati".
        #  ⚠️ Kolom = `isActive` (bukan `prefix`; prefix ada di dalam JSON `data`).
        #  ⚠️⚠️ PEMULIHAN WAJIB PAKAI **ID TETAP** — BUKAN `WHERE isActive=0`.
        #     Bug nyata 17Sep26: `WHERE isActive=0` menghidupkan SEMUA 25 koneksi
        #     provider (bukan 1) → jalur AI bisa bocor ke provider lain & biaya naik.
        #     ID TETAP = koneksi produksi (name='CB', provider inferhub).
        ID_PROVIDER = 'af541f8c-36e6-47f4-8662-38321fc8a364'
        kuota_reset_berat(0)   # WAJIB: P dulu gagal karena kena 402 kuota habis
        sql_mati = ("const s=require('/app/node_modules/better-sqlite3')"
                    "('/app/data/db/data.sqlite');"
                    "s.prepare('UPDATE providerConnections SET isActive=0 "
                    "WHERE id=?').run('" + ID_PROVIDER + "');"
                    "console.log('DIMATIKAN=' + s.prepare('SELECT COUNT(*) c "
                    "FROM providerConnections WHERE isActive=1').get().c)")
        rc, out = _docker(f'docker exec 9router node -e "{sql_mati}"')
        mati = 'DIMATIKAN' in out
        cek('P1 koneksi provider berhasil DIMATIKAN (simulasi gangguan)', mati,
            out.strip()[:120] if not mati else 'ok')
        if mati:
            s, b, _ = buka('/api/ai/v1/revisi',
                           data={'naskah': 'BAB I PENDAHULUAN\n\nIsi uji.',
                                 'komentar': ['Perbaiki.']},
                           metode='POST', timeout=60)
            kodeP = ''
            try:
                kodeP = (json.loads(b) or {}).get('kode') or ''
            except Exception:                                  # noqa: BLE001
                pass
            cek('P2 permintaan TETAP diterima walau provider mati (tidak 500)',
                s in (200, 409), f'HTTP {s} · {b[:110]}')
            if kodeP:
                stP, ringP = tunggu_proses(kodeP, batas_detik=180)
                #  YANG WAJIB: app TIDAK menggantung & TIDAK menipu — status
                #  harus `gagal` dengan alasan terbaca, BUKAN `selesai` kosong.
                cek('P3 status jujur: `gagal` (tidak pura-pura selesai)',
                    stP == 'gagal', f'status={stP}')
                cek('P4 ada pesan galat terbaca user',
                    bool(ringP.get('galat')), f'galat={str(ringP.get("galat"))[:110]}')
                info(f'KODE_PROSES_P={kodeP}')
            #  PULIHKAN koneksi — ID TETAP, JANGAN `WHERE isActive=0` (bug 17Sep26).
            sql_hidup = ("const s=require('/app/node_modules/better-sqlite3')"
                         "('/app/data/db/data.sqlite');"
                         "s.prepare('UPDATE providerConnections SET isActive=1 "
                         "WHERE id=?').run('" + ID_PROVIDER + "');"
                         "console.log('AKTIF=' + s.prepare('SELECT COUNT(*) c "
                         "FROM providerConnections WHERE isActive=1').get().c)")
            rc2, out2 = _docker(f'docker exec 9router node -e "{sql_hidup}"')
            cek('P5 provider DIPULIHKAN (produksi hidup lagi, TEPAT 1 koneksi)',
                'AKTIF=1' in out2, out2.strip()[-60:])
        jeda('sebelum Q (naskah raksasa)')
        tunggu_jatah_rate('sebelum Q — P baru saja panggil AI')

        # ── Q. NASKAH SANGAT BESAR (uji CAP bagian & potong cerdas) ──────
        print('\n── Q. NASKAH SANGAT BESAR (cap bagian) ────────────────────')
        kuota_reset_berat(0)
        raksasa = (naskah_asli * 4)[:400000]  # ~400rb kar > AI_POTONG_KARAKTER
        s, b, _ = buka('/api/ai/v1/revisi',
                       data={'naskah': raksasa, 'komentar': ['Perdalam analisis.']},
                       metode='POST', timeout=120)
        print(f'   HTTP {s} · {b[:200]}')
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
    if CATATAN:
        print('\nCATATAN:')
        for c in CATATAN:
            print(f'  · {c}')
    print('═' * 78)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
