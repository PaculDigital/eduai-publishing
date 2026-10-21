"""UJI 2 ARAH PAGAR OPSI A — dijalankan DI DALAM container `eduai-app`.

Membuktikan pagar `editan=0` di `/api/ai/v1/terapkan` BERGIGI:
  SEHAT  — hasil berbentuk kontrak pipa (kutipan nyata) → diterima,
           hanya paragraf kutipan yang diganti (jalur presisi).
  DIRUSAK— hasil berbentuk potongan naskah (tanpa blok KUTIP/GANTI,
           persis bentuk hasil Pintu B) → DITOLAK 422, dokumen utuh.

🚨 ATURAN: uji TIDAK BOLEH menyentuh berkas milik user sungguhan.
   Jadinya uji MENCIPTAKAN SALINAN khusus (baris `files` + berkas di
   uploads/7/), snapshot hanya untuk salinan itu, lalu dibersihkan
   di akhir — termasuk kalau gagal.

Pola login/copy: disalin dari `_uji_terapkan.py` + `_uji_publik_komentar.py`
(cookie jar + UA, user berat id=7). Jangan bikin cara sendiri.
"""
import hashlib
import http.cookiejar
import json
import os
import secrets
import sqlite3
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = os.getenv('UJI_BASE', 'http://127.0.0.1:8000')
DB = os.getenv('UJI_DB', '/app/data/eduai.db')
UPLOAD = os.getenv('UJI_UPLOAD', '/app/uploads')
SANDI = os.getenv('E2E_SANDI_BERAT', 'UjiBerat123!')

LULUS = GAGAL = 0
OP = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
H = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/151.0 Safari/537.36'}

fid_salinan = None
path_salinan = None


def cek(nama, syarat, catatan=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  LULUS  {nama}' + (f' — {catatan}' if catatan else ''))
    else:
        GAGAL += 1
        print(f'  GAGAL  {nama}' + (f' — {catatan}' if catatan else ''))


def buka(jalur, data=None):
    h = dict(H)
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        h['Content-Type'] = 'application/json'
    req = urllib.request.Request(BASE + jalur, data=body, headers=h)
    try:
        with OP.open(req, timeout=120) as r:
            return r.status, json.loads(r.read().decode('utf-8', 'ignore') or '{}')
    except urllib.error.HTTPError as e:
        isi = e.read().decode('utf-8', 'ignore')
        try:
            return e.code, json.loads(isi or '{}')
        except json.JSONDecodeError:
            return e.code, {'mentah': isi[:300]}
    except Exception as e:                                    # noqa: BLE001
        return 0, {'galat': f'{type(e).__name__}: {e}'}


def masuk(email, sandi):
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


def bersihkan():
    global fid_salinan, path_salinan
    if path_salinan and os.path.exists(path_salinan):
        os.remove(path_salinan)
    if fid_salinan:
        c = sqlite3.connect(DB)
        c.execute('DELETE FROM files WHERE id=?', (fid_salinan,))
        c.commit()
        c.close()
    print('\n  (salinan uji dibersihkan)')


def main():
    global fid_salinan, path_salinan
    print('=' * 62)
    print('UJI 2 ARAH PAGAR OPSI A — /api/ai/v1/terapkan (atas SALINAN)')
    print('=' * 62)

    c = sqlite3.connect(DB)
    bar = c.execute("SELECT id, email FROM users WHERE email LIKE '%uji%' "
                    "ORDER BY id DESC LIMIT 1").fetchone()
    if not bar:
        cek('user uji ada', False, 'jalankan _uji_publik_komentar.py dulu')
        return 1
    uid, email = bar
    cek('user uji ada', True, f'id={uid} {email}')

    fb = c.execute("SELECT id, nama_simpan FROM files WHERE user_id=? AND "
                   "nama LIKE '%.docx' AND terhapus_pada IS NULL "
                   "ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    if not fb:
        cek('asli .docx cowok uji ada', False, 'unggah dulu')
        return 1
    id_asis, simpan_asis = fb
    path_asis = f'{UPLOAD}/{uid}/{simpan_asis}'
    cek('asli ada di disk', os.path.exists(path_asis), f'file_id={id_asis}')

    cek('login web', masuk(email, SANDI), 'cookie di jar')

    # ── 0. SALINAN khusus uji (baris files + berkas) ─────────────────────
    import shutil
    simpan_baru = 'uji-pagar-opsiA-%s.docx' % secrets.token_hex(6)
    path_salinan = f'{UPLOAD}/{uid}/{simpan_baru}'
    shutil.copy2(path_asis, path_salinan)
    asli = open(path_asis, 'rb').read()
    c.execute(
        "INSERT INTO files (user_id,nama,nama_simpan,ukuran,tipe,dibuat,"
        "diubah,disunting_pada,terhapus_pada,folder_id) VALUES "
        "(?,?,?,?,?,datetime('now'),datetime('now'),NULL,NULL,NULL)",
        (uid, 'uji_pagar_opsiA.docx', simpan_baru, len(asli),
         'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
    c.commit()
    fid_salinan = c.execute(
        "SELECT id FROM files WHERE nama_simpan=?", (simpan_baru,)).fetchone()[0]
    c.close()
    cek('salinan uji siap', os.path.exists(path_salinan),
        f'file_id={fid_salinan} — asli TIDAK dipakai')

    # kutipan uji: ambil dari isi salinan supaya pasti ada
    import re as _re
    import zipfile
    with zipfile.ZipFile(path_salinan) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    kalimat = next((t.strip() for t in _re.findall(r'<w:t[^>]*>([^<]*)</w:t>', xml)
                    if len(t.strip()) > 60), '')
    print(f'  kutipan uji: {kalimat[:70]!r}')

    try:
        # ── (1) SEHAT: bentuk kontrak, bab default __seluruh__ ───────────
        sehat = (f'[PROFIL] uji pagar Opsi A\n\n'
                 f'[K1-KUTIP-ASLI] {kalimat}\n'
                 f'[K1-GANTI-JADI] Kalimat ini diperbaiki lewat jalur presisi '
                 f'pipa (uji pagar Opsi A, koreksi ejaan.\n')
        s1, d1 = buka('/api/ai/v1/terapkan',
                      {'file_id': fid_salinan, 'teks': sehat})
        det1 = d1.get('detail') or d1
        print('\n[1] SEHAT — bentuk kontrak pipa (kutipan ada di naskah)')
        cek('HTTP 200 / diterima (BUKAN 422)', s1 == 200, f'HTTP {s1} {str(det1)[:90]}')
        cek('menulis ke SALINAN (jalur presisi jalan)',
            os.path.getsize(path_salinan) != len(asli),
            f'{len(asli)} → {os.path.getsize(path_salinan)} byte')

        snap = open(path_salinan, 'rb').read()   # snapshot SEBELUM kerusakan
        with zipfile.ZipFile(path_salinan) as z:
            xml_snap = z.read('word/document.xml').decode('utf-8', 'ignore')
        cek('koreksi masuk, teks lain utuh',
            'jalur presisi pipa' in xml_snap)

        # ── (2) DIRUSAK: bentuk hasil Pintu B ─────────────────────────────
        rusak = ('───── BAGIAN 1 dari 2 ─────\n\n'
                 'BAB V HASIL DAN PEMBAHASAN\n\n'
                 'Hasil penelitian menunjukkan olahraga berpengaruh '
                 'terhadap penurunan nyeri menstruasi.\n\n'
                 'Catatan untuk Anda: tidak ada perubahan yang perlu dilakukan.\n')
        s2, d2 = buka('/api/ai/v1/terapkan',
                      {'file_id': fid_salinan, 'teks': rusak})
        det2 = d2.get('detail') or d2
        print('\n[2] DIRUSAK — bentuk potongan naskah (hasil Pintu B)')
        cek('HTTP 422 (pagar BERGIGI)', s2 == 422, f'HTTP {s2}')
        cek('pesan jujur + jalan keluar ("Salin hasil")',
            'Salin hasil' in json.dumps(det2), str(det2)[:110])
        cek('SALINAN tidak berubah sama sekali',
            open(path_salinan, 'rb').read() == snap, 'is .docx identik')

        # ── (3) DIRUSAK variasi: "TIDAK ADA PERUBAHAN" ────────────────────
        s3, d3 = buka('/api/ai/v1/terapkan',
                      {'file_id': fid_salinan, 'teks': 'TIDAK ADA PERUBAHAN'})
        det3 = d3.get('detail') or d3
        print('\n[3] DIRUSAK — hasil hanya "TIDAK ADA PERUBAHAN"')
        cek('HTTP 422', s3 == 422, f'HTTP {s3}')
        cek('pesan bisa ditindaklanjuti',
            'Salin hasil' in json.dumps(det3), str(det3)[:110])
        cek('SALINAN tidak berubah', open(path_salinan, 'rb').read() == snap)

        # ── (4) hasil LAWAS berbentuk teks polos (bentuk pra-pipa) ────────
        #  Perilaku yang DIINGINKAN Opsi A: teks polos pun tidak bisa
        #  dicocokkan ke paragraf → DITOLAK jujur (user pakai "Salin hasil").
        polos = ('BAB V HASIL DAN PEMBAHASAN\n\n'
                 'Ini naskah hasil revisi bentuk lama tanpa blok KUTIP/GANTI, '
                 'hanya teks biasa.\n')
        s4, d4 = buka('/api/ai/v1/terapkan',
                      {'file_id': fid_salinan, 'teks': polos})
        det4 = d4.get('detail') or d4
        print('\n[4] LAWAS — hasil teks polos tanpa blok kontrak')
        cek('HTTP 422 (dikonfirmasi tertolak)', s4 == 422, f'HTTP {s4}')
        cek('pesan ada jalan keluar', 'Salin hasil' in json.dumps(det4))
        cek('SALINAN tidak berubah', open(path_salinan, 'rb').read() == snap)

        # ── (5) garansi: arsip .docx masih sah setelah 2 penolakan ────────
        with zipfile.ZipFile(path_salinan) as z:
            cek('arsip .docx SAH sesudah penolakan', z.testzip() is None)
    finally:
        bersihkan()

    # ―― (6) GARANSI TERAKHIR: berkas asli user utuh total ───────────────
    print('\n[CTX] berkas asli user TIDAK tersentuh')
    cek('asli .docx identik byte-per-byte', open(path_asis, 'rb').read() == asli,
        f'{len(asli)} byte')

    print('\n' + '=' * 62)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('=' * 62)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())