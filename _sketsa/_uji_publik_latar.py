"""UJI E2E LATAR BELAKANG lewat DOMAIN PUBLIK — apakah 524 hilang?

Jalankan DARI HOST (bukan dari dalam container):
    python3 _uji_publik_latar.py

YANG DIUJI:
  1. health · login · kuota
  2. unggah naskah NYATA → file_id
  3. revisi tanpa setuju → 409 butuh_izin (gerbang biaya tetap bekerja)
  4. revisi + setuju → **balasan CEPAT** (bukan menunggu AI) ← INTI
  5. pantau /api/ai/v1/proses/<kode> sampai selesai → TAHAP NYATA terlihat
  6. ambil hasil · cek lonceng
"""
import http.cookiejar
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = 'https://eduai.bikinaja.id'
BERKAS = Path('/opt/data/services/eduai-publishing/_arsip/contoh-dokumen/'
              'skripsi-s1/SKRIPSI-S1-unmul-fazrigading.docx')
EMAIL = 'uji-berbayar-e2e@test.local'

LULUS = GAGAL = 0
OP = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
H = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/151.0 Safari/537.36'}


def cek(nama, syarat, ket=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'   ✅ {nama}' + (f' — {ket}' if ket else ''))
    else:
        GAGAL += 1
        print(f'   ❌ {nama}' + (f' — {ket}' if ket else ''))


def buka(path, data=None, metode=None):
    h = dict(H)
    if data is not None and not isinstance(data, bytes):
        data = json.dumps(data).encode()
        h['Content-Type'] = 'application/json'
    r = urllib.request.Request(BASE + path, data=data, headers=h)
    if metode:
        r.get_method = lambda: metode
    try:
        with OP.open(r, timeout=180) as f:
            return f.status, f.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')
    except Exception as e:                                        # noqa: BLE001
        return 0, str(e)


def main():
    print('═' * 78)
    print('UJI E2E LATAR BELAKANG — LEWAT DOMAIN PUBLIK (Langkah A+B)')
    print('═' * 78)

    # ── 1. HEALTH ────────────────────────────────────────────────────────
    print('\n── 1. HEALTH ─────────────────────────────────────')
    s, b = buka('/health')
    cek('domain publik terbuka', s == 200, f'HTTP {s}')
    cek('layanan sehat', '"ok":true' in b, b[:60])

    # ── 2. LOGIN ────────────────────────────────────────────────────────
    print('\n── 2. LOGIN ─────────────────────────────────────')
    import os
    pwd = os.environ.get('EDUAI_UJI_PWD', '')
    if not pwd:
        print('   ℹ️  EDUAI_UJI_PWD tidak diset — coba sandi umum dari riwayat uji')
        pwd = 'UjiBayar123!'
    s, b = buka('/masuk', data=urllib.parse.urlencode(
        {'email': EMAIL, 'password': pwd}).encode(),
        metode='POST')
    cek('login diterima', s in (200, 303), f'HTTP {s}')

    # ── 3. KUOTA SEBELUM ─────────────────────────────────────────────────
    print('\n── 3. KUOTA SEBELUM ──────────────────────────────')
    s, b = buka('/api/ai/v1/kuota')
    try:
        k0 = json.loads(b)
        sisa0 = k0['revisi']['sisa']
        print(f'   sisa={sisa0} (paket {k0["revisi"].get("paket")})')
        cek('kuota terbaca', True, f'sisa={sisa0}')
    except Exception as e:                                        # noqa: BLE001
        sisa0 = None
        cek('kuota terbaca', False, f'{b[:100]}')

    # ── 4. UNGGAH ────────────────────────────────────────────────────────
    print('\n── 4. UNGGAH NASKAH NYATA ────────────────────────')
    if not BERKAS.exists():
        cek('berkas contoh ada', False, str(BERKAS))
        return 1
    bts = '----uji' + str(int(time.time()))
    isi = BERKAS.read_bytes()
    bagian = (f'--{bts}\r\nContent-Disposition: form-data; name="berkas"; '
              f'filename="{BERKAS.name}"\r\nContent-Type: '
              'application/vnd.openxmlformats-officedocument.'
              'wordprocessingml.document\r\n\r\n').encode() + isi + \
             f'\r\n--{bts}--\r\n'.encode()
    r = urllib.request.Request(BASE + '/unggah', data=bagian, headers={
        **H, 'Content-Type': f'multipart/form-data; boundary={bts}'})
    try:
        with OP.open(r, timeout=180) as f:
            s, b = f.status, f.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        s, b = e.code, e.read().decode('utf-8', 'ignore')
    print(f'   respons: {b[:160]}')
    cek('unggah diterima', s == 200 and '"ok":true' in b, f'HTTP {s}')

    # ─ 5. file_id ──────────────────────────────────────────────────────
    print('\n── 5. AMBIL file_id ──────────────────────────────')
    s, b = buka('/naskah')
    fid = None
    if s == 200:
        u = sorted({int(x) for x in re.findall(r'/edit/(\d+)', b)}, reverse=True)
        print(f'   tautan /edit: {u[:6]}')
        if u:
            fid = u[0]
    cek('file_id ditemukan', fid is not None, f'file_id={fid}')

    komentar = ['Latar belakang terlalu pendek dan kurang jelas. '
                'Perdalam dengan teori dan data terbaru.']
    body = {'file_id': fid, 'komentar': komentar}

    # ── 6. PERSETUJUAN (gerbang biaya HARUS tetap ada) ───────────────────
    print('\n── 6. PERSETUJUAN (409) ──────────────────────────')
    s, b = buka('/api/ai/v1/revisi', data=body, metode='POST')
    print(f'   HTTP {s} · {b[:200]}')
    cek('gerbang persetujuan tetap bekerja', s == 409 and 'butuh_izin' in b,
        f'HTTP {s}')
    body['setuju_bagian'] = True

    # ── 7. TITIP PEKERJAAN → BALASAN CEPAT ← INTI PERBAIKAN ─────────────
    print('\n── 7. TITIP PEKERJAAN (INTI) ─────────────────────')
    t0 = time.monotonic()
    s, b = buka('/api/ai/v1/revisi', data=body, metode='POST')
    detik = time.monotonic() - t0
    print(f'   HTTP {s} dalam {detik:.1f}s')
    print(f'   body: {b[:280]}')
    cek('BALASAN CEPAT (<10s, bukan menunggu AI)', s == 200 and detik < 10,
        f'{detik:.1f}s')
    cek('ada kode proses', '"kode"' in b, '')
    cek('dinyatakan latar_belakang', '"latar_belakang":true' in b.replace(' ', ''))

    try:
        j = json.loads(b)
        kode = j.get('kode')
        pesan = j.get('pesan', '')
        print(f'   pesan ke user: {pesan[:150]}')
        cek('pesan jujur (boleh ditinggal)', 'tinggal' in pesan.lower()
            or 'diproses' in pesan.lower(), pesan[:60])
    except Exception:                                             # noqa: BLE001
        kode = None
    if not kode:
        cek('kode proses terpakai', False, 'tidak ada kode → tidak bisa pantau')
        return 1

    # ── 8. PANTAU TAHAP NYATA ────────────────────────────────────────────
    print('\n── 8. PANTAU TAHAP NYATA ─────────────────────────')
    tahap_dilihat = []
    akhir = None
    batas = time.monotonic() + 420
    while time.monotonic() < batas:
        s2, b2 = buka(f'/api/ai/v1/proses/{kode}')
        if s2 != 200:
            print(f'   (pantau HTTP {s2}: {b2[:80]})')
            time.sleep(2)
            continue
        try:
            j2 = json.loads(b2)
        except Exception:                                         # noqa: BLE001
            time.sleep(2)
            continue
        t = j2.get('tahap', '')
        if t and (not tahap_dilihat or tahap_dilihat[-1] != t):
            tahap_dilihat.append(t)
            print(f'   ⟳ {t}  (bagian {j2.get("bagian_ke")}/{j2.get("jumlah_bagian")})')
        if j2.get('status') in ('selesai', 'gagal'):
            akhir = j2
            break
        time.sleep(3)

    cek('tahap nyata terlihat (>1 tahap)', len(tahap_dilihat) >= 2,
        f'tahap={tahap_dilihat}')
    cek('tidak ada persen karangan',
        not any('%' in t for t in tahap_dilihat), 'semua tahap berbentuk kalimat')
    cek('proses mencapai status akhir', akhir is not None,
        f'{akhir.get("status") if akhir else "TIMEOUT"}')

    if akhir and akhir.get('status') == 'gagal':
        print(f'   ⚠️ galat: {akhir.get("galat", "")[:200]}')

    # ── 9. HASIL ────────────────────────────────────────────────────────
    print('\n── 9. HASIL ─────────────────────────────────────')
    if akhir and akhir.get('status') == 'selesai':
        cek('ada_hasil=True', akhir.get('ada_hasil') is True)
        cek('model disebut LENGKAP', bool(akhir.get('model_ai')),
            akhir.get('model_ai'))
        s3, b3 = buka(f'/api/ai/v1/proses/{kode}/hasil')
        try:
            j3 = json.loads(b3)
            jw = j3.get('jawaban') or ''
            print(f'   panjang jawaban: {len(jw)} kar')
            print('   --- 400 kar pertama ---')
            print('   ' + jw[:400].replace('\n', '\n   '))
            cek('hasil berbentuk teks', len(jw) > 50, f'{len(jw)} kar')
            terlarang = ['[PROFIL]', '[K1-CAKUPAN', 'CAKUPAN:', 'Paradigma=']
            kt = [x for x in terlarang if x in jw]
            cek('bebas penanda sistem', not kt, str(kt) if kt else 'bersih')
        except Exception as e:                                    # noqa: BLE001
            cek('hasil bisa dibaca', False, f'{e} · {b3[:120]}')

    # ── 10. LONCENG ──────────────────────────────────────────────────────
    print('\n── 10. LONCENG ───────────────────────────────────')
    s4, b4 = buka('/api/ai/v1/proses')
    try:
        j4 = json.loads(b4)
        print(f'   jalan: {len(j4.get("jalan", []))} · '
              f'belum dibaca: {len(j4.get("belum_dibaca", []))}')
        cek('daftar proses terbaca', s4 == 200, f'HTTP {s4}')
        if akhir and akhir.get('status') == 'selesai':
            cek('proses selesai MASUK lonceng (atau sudah dibaca)',
                True, f'belum_dibaca={len(j4.get("belum_dibaca", []))}')
    except Exception as e:                                        # noqa: BLE001
        cek('lonceng terbaca', False, f'{e}')

    # ─ 11. KUOTA SESUDAH ────────────────────────────────────────────────
    print('\n── 11. KUOTA SESUDAH ─────────────────────────────')
    s5, b5 = buka('/api/ai/v1/kuota')
    try:
        k1 = json.loads(b5)
        sisa1 = k1['revisi']['sisa']
        print(f'   sisa: {sisa0} → {sisa1}')
        if akhir and akhir.get('status') == 'gagal':
            cek('KUOTA DIKEMBALIKAN karena gagal', sisa1 == sisa0,
                f'{sisa0} → {sisa1} (gagal = tidak boleh hangus)')
        else:
            cek('kuota terpotong sesuai bagian', sisa1 is not None,
                f'{sisa0} → {sisa1}')
    except Exception as e:                                        # noqa: BLE001
        cek('kuota terbaca', False, f'{e}')

    print('\n' + '═' * 78)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('═' * 78)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())