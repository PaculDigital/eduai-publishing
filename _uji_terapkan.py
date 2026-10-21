"""UJI ENDPOINT LANGKAH C+D+E — dijalankan DI DALAM container.

Bukan uji impor! Uji ini MENGGILANGG endpoint nyata lewat HTTP dan memeriksa
AKIBATNYA pada berkas .docx (isi berubah, cadangan ada, XML utuh).

Titik yang diuji:
  /api/ai/v1/kunci      → status kunci dokumen (Lapis 1 & 2)
  /api/ai/v1/terapkan   → tulis hasil ke .docx (Langkah D)
  /api/ai/v1/proses/<kode>/batalkan → batalkan proses
Penolakan yang WAJIB (jangan merusak naskah mahasiswa):
  • ekstensi bukan .docx  → tolak
  • hasil kosong          → tolak
  • bab tidak ada         → tolak
  • berkas bukan miliknya → tolak
"""
import http.cookiejar
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
import zipfile

BASE = 'http://127.0.0.1:8000'
DB = '/app/data/eduai.db'
CONTOH = '/app/_contoh-dokumen/skripsi-s1/SKRIPSI-S1-unhas-olahraga-menstruasi.docx'
UPLOAD = '/app/uploads'

LULUS = GAGAL = 0
# Pola TERBUKTI dari _uji_publik_lonceng.py (jangan bikin cara sendiri):
# cookie jar + User-Agent peramban. Tanpa UA, Cloudflare bisa menolak.
OP = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
H = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/151.0 Safari/537.36'}


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {catatan}' if catatan else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {catatan}' if catatan else ''))


def buka(jalur, data=None, metode='POST'):
    """Panggil endpoint; kembalikan (status, dict)."""
    h = dict(H)
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h['Content-Type'] = 'application/json'
    req = urllib.request.Request(BASE + jalur, data=body, headers=h)
    if metode:
        req.get_method = lambda: metode
    try:
        with OP.open(req, timeout=180) as r:
            teks = r.read().decode('utf-8', 'ignore')
            try:
                return r.status, json.loads(teks or '{}')
            except json.JSONDecodeError:
                return r.status, {'mentah': teks[:300]}
    except urllib.error.HTTPError as e:
        isi = e.read().decode('utf-8', 'ignore')
        try:
            return e.code, json.loads(isi or '{}')
        except json.JSONDecodeError:
            return e.code, {'mentah': isi[:300]}
    except Exception as e:                                    # noqa: BLE001
        return 0, {'galat': f'{type(e).__name__}: {e}'}


def masuk(email, sandi):
    """Login web — cookie disimpan di OP.

    ⚠️ Field WAJIB `password` (BUKAN `sandi`) — aturan yang sudah dicatat di
    memori Wulan; Wulan pernah salah beberapa kali di sini.
    """
    h = dict(H)
    h['Content-Type'] = 'application/x-www-form-urlencoded'
    data = urllib.parse.urlencode({'email': email, 'password': sandi}).encode()
    req = urllib.request.Request(BASE + '/masuk', data=data, headers=h)
    try:
        with OP.open(req, timeout=60) as r:
            return r.status in (200, 303)
    except urllib.error.HTTPError as e:
        return e.code in (200, 303)
    except Exception:
        return False


def teks_docx(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    import re
    return ' '.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml))


def main():
    print('=' * 62)
    print('UJI ENDPOINT LANGKAH C+D+E')
    print('=' * 62)

    # ── 0. Siapkan: user uji berbayar + berkas .docx di disk ─────────────
    print('\n[0] Siapkan user & berkas uji')
    c = sqlite3.connect(DB)
    baris = c.execute(
        "SELECT id, email FROM users WHERE email LIKE '%uji%' "
        "ORDER BY id DESC LIMIT 1").fetchone()
    if not baris:
        cek('user uji ada', False, 'jalankan _uji_publik_lonceng.py dulu')
        return 1
    uid, email = baris
    cek('user uji ada', True, f'id={uid} {email}')

    fb = c.execute(
        "SELECT id, nama, nama_simpan FROM files WHERE user_id=? AND "
        "nama LIKE '%.docx' ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    if not fb:
        cek('berkas .docx milik user uji ada', False, 'unggah dulu')
        return 1
    fid, nama, simpan = fb
    path = f'{UPLOAD}/{uid}/{simpan}'
    cek('berkas ada di disk', os.path.exists(path), path)
    if not os.path.exists(path):
        os.makedirs(f'{UPLOAD}/{uid}', exist_ok=True)
        import shutil
        shutil.copy2(CONTOH, path)
        cek('berkas disiapkan dari contoh', os.path.exists(path))
    c.close()

    sandi = os.getenv('E2E_SANDI', 'UjiBayar123!')
    if not masuk(email, sandi):
        cek('login web', False, 'cookie tidak didapat')
        return 1
    cek('login web', True, 'cookie tersimpan di jar')

    # ── 1. /v1/kunci — dokumen TIDAK terkunci saat tidak ada proses ─────
    print('\n[1] /v1/kunci — tidak terkunci saat tidak ada proses AI')
    s, d = buka('/api/ai/v1/kunci', {'file_id': fid})
    cek('HTTP 200', s == 200, f'HTTP {s}')
    cek('terkunci = False', d.get('terkunci') is False, str(d)[:80])

    # ── 2. /v1/terapkan — TOLAK ekstensi bukan .docx ────────────────────
    print('\n[2] /v1/terapkan — TOLAK berkas bukan .docx (jangan rusak)')
    c2 = sqlite3.connect(DB)
    c2.execute("INSERT INTO files (user_id,nama,nama_simpan,ukuran,tipe,dibuat,"
               "diubah,disunting_pada,terhapus_pada,folder_id) VALUES "
               "(?,?,?,?,?,datetime('now'),datetime('now'),NULL,NULL,NULL)",
               (uid, 'uji.pdf', 'uji-palsu.pdf', 100, 'application/pdf'))
    c2.commit()
    fid_pdf = c2.execute("SELECT id FROM files WHERE nama_simpan='uji-palsu.pdf'"
                         ).fetchone()[0]
    c2.close()
    s, d = buka('/api/ai/v1/terapkan',
                 {'file_id': fid_pdf, 'teks': 'BAB I\nisi', 'bab': '__seluruh__'})
    det = d.get('detail') or d
    cek('HTTP 400', s == 400, f'HTTP {s}')
    cek('pesan menyebut .docx', '.docx' in json.dumps(det), str(det)[:100])

    # ── 3. /v1/terapkan — TOLAK hasil kosong ────────────────────────────
    print('\n[3] /v1/terapkan — TOLAK hasil kosong')
    sebelum = open(path, 'rb').read()
    s, d = buka('/api/ai/v1/terapkan',
                 {'file_id': fid, 'teks': '   ', 'bab': '__seluruh__'})
    cek('HTTP >= 400', s >= 400, f'HTTP {s}')
    cek('berkas TIDAK berubah', open(path, 'rb').read() == sebelum)

    # ── 4. /v1/terapkan — TOLAK bab yang tidak ada ───────────────────────
    print('\n[4] /v1/terapkan — TOLAK bab tidak ada')
    s, d = buka('/api/ai/v1/terapkan',
                 {'file_id': fid, 'teks': 'isi baru', 'bab': 'BAB XCIX',
                  'judul_bab': 'TIDAK ADA'})
    cek('HTTP >= 400', s >= 400, f'HTTP {s}')
    cek('berkas TIDAK berubah', open(path, 'rb').read() == sebelum)

    # ── 5. /v1/terapkan — SUKSES ganti seluruh naskah ───────────────────
    print('\n[5] /v1/terapkan — SUKSES (ganti seluruh naskah)')
    teks_baru = ('BAB I PENDAHULUAN\n'
                 'Ini hasil revisi AI untuk uji endpoint Langkah D.\n'
                 'Paragraf kedua hasil revisi.\n')
    s, d = buka('/api/ai/v1/terapkan',
                 {'file_id': fid, 'teks': teks_baru, 'bab': '__seluruh__'})
    det = d.get('detail') or d
    cek('HTTP 200', s == 200, f'HTTP {s} {str(det)[:80]}')
    cek('ok = True', det.get('ok') is True)
    cek('paragraf diganti > 0', (det.get('paragraf_diganti') or 0) > 0,
        f"{det.get('paragraf_diganti')} → {det.get('paragraf_baru')}")
    cek('ada cadangan', det.get('ada_cadangan') is True)

    # ── 6. AKIBAT pada berkas: isi berubah, XML utuh ─────────────────────
    print('\n[6] AKIBAT nyata pada .docx')
    cek('ukuran berkas berubah', open(path, 'rb').read() != sebelum,
        f'{len(sebelum)} → {os.path.getsize(path)} byte')
    isi = teks_docx(path)
    cek('teks hasil revisi MASUK', 'hasil revisi AI untuk uji endpoint' in isi)
    cek('teks LAMA sudah hilang', 'MENSTRUASI' not in isi.upper())
    with zipfile.ZipFile(path) as z:
        cek('arsip .docx masih SAH', z.testzip() is None)
        cek('bagian penting masih ada',
            'word/document.xml' in z.namelist() and
            any(n.startswith('word/_rels/') for n in z.namelist()))

    # ── 7. sidik jari INGATAN diperbarui (kolom yang dulu mati) ──────────
    print('\n[7] Ingatan dokumen (kolom sidik_jari yang dulu MATI)')
    c3 = sqlite3.connect(DB)
    ada = c3.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
                     "AND name='profil_dokumen'").fetchone()[0]
    if not ada:
        cek('tabel profil_dokumen ada', False, 'belum dibangun (§4.11)')
    else:
        r = c3.execute("SELECT sidik_jari FROM profil_dokumen WHERE file_id=?",
                       (fid,)).fetchone()
        if r is None:
            cek('ingatan dokumen (belum ada baris — normal pra-onboarding)', True,
                'tidak diuji')
        else:
            cek('sidik_jari TERISI (dulu selalu kosong)', bool(r[0]),
                f'{(r[0] or "")[:16]}...')
    c3.close()

    # ── 8. berkas milik orang lain → TOLAK ──────────────────────────────
    print('\n[8] /v1/terapkan — TOLAK berkas bukan miliknya')
    c4 = sqlite3.connect(DB)
    lain = c4.execute("SELECT id FROM files WHERE user_id != ? LIMIT 1",
                      (uid,)).fetchone()
    c4.close()
    if lain:
        s, d = buka('/api/ai/v1/terapkan',
                     {'file_id': lain[0], 'teks': 'x', 'bab': '__seluruh__'})
        cek('HTTP 404', s == 404, f'HTTP {s}')
    else:
        cek('berkas user lain (tidak ada — dilewati)', True)

    # ── 9. /v1/kunci untuk berkas orang lain → tidak bocorkan ───────────
    print('\n[9] /v1/kunci — tidak membocorkan berkas orang lain')
    if lain:
        s, d = buka('/api/ai/v1/kunci', {'file_id': lain[0]})
        cek('terkunci = False (bukan 403 bocor)', d.get('terkunci') is False,
            str(d)[:60])

    # ── 10. batalkan proses yang tidak ada → 404 rapi ────────────────────
    print('\n[10] /v1/proses/<kode>/batalkan — kode tidak ada')
    s, d = buka('/api/ai/v1/proses/KODE-PALSU/batalkan', {})
    cek('HTTP 404', s == 404, f'HTTP {s}')

    print('\n' + '=' * 62)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('=' * 62)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    import urllib.parse
    sys.exit(main())
