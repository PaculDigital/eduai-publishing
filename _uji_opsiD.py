"""UJI 2 ARAH OPSI D — di dalam container `eduai-app`, atas SALINAN.

D1 + (a) ACC Bos 29Sep26: simpan bentuk mentah pendamping (`versi_pipa`),
buang penanda `BAGIAN x dari y`, pisahkan catatan AI dari isi versi.

BUKTI YANG DICARI
─────────────────
A  UNIT (tanpa server): pipa.buang_catatan_ai / pipa.gabung_mentah
   A1 data NYATA `_arsip/vd_file78.txt` → 2 catatan AI hilang, kalimat
      mahasiswa TETAP ADA (uji 2 arah).
   A2 pola sempit → teks mahasiswa yang memuat kata "catatan" TIDAK ikut
      terbuang; paragraf "Tidak ada perubahan..." buatan AI hilang.
   A3 gabung_mentah: penomoran K diurutkan ulang (bukti kasus tabrakan
      nomor kembar) + CAKUPAN tolak tetap dihormati.
   A4 gabung_mentah hasilnya DAPAT diperiksa pipa → ok + editan=2.
   A5 jawaban bentuk lama (tanpa penanda) → '' (tak ada pendamping).
   A6 catatan AI di dalam GANTI-JADI ikut dibuang dari pendamping.
   A7 penulis penanda `───── BAGIAN x dari y` sudah TIDAK ADA di sumber.

B  HTTP `/api/ai/v1/terapkan` (server vitiasi :8001, DB+berkas SALINAN)
   B1 SEHAT : versi punya pendamping, tanpa `teks` di body → 200,
      paragraf kutip diganti, paragraf LAIN utuh (presisi).
   B2 SUNTIK : pendamping DIHAPUS → 422 + berkas identik.
      (Ini yang membuktikan B1 sukses KARENA pendamping, bukan kebetulan.)
   B3 SUNTIK : kutipan pendamping TIDAK ADA di naskah → 422, tak menulis.
   B4 SUNTIK : GANTI-JADI terlalu panjang → 422, tak menulis.
   B5 PAGAR A masih bekerja: versi polos tanpa pendamping → 422.
   B6 arsip .docx tetap sah.

ENV (diisi skrip pelontar): UJI_BASE · UJI_DB · UJI_UPLOAD · UJI_SRC
Exit code 0 = semua LULUS.
"""
import json
import os
import sqlite3
import sys
import urllib.error
import urllib.request
import http.cookiejar
import zipfile
import re

BASE = os.getenv('UJI_BASE', 'http://127.0.0.1:8001')
DB = os.getenv('UJI_DB', '/tmp/ujiD_data/eduai.db')
UPLOAD = os.getenv('UJI_UPLOAD', '/tmp/ujiD_up')
SRC = os.getenv('UJI_SRC', '/tmp/ujiD_root')
LOG = os.getenv('UJI_LOG', '/tmp/ujiD_root/server.log')
VD78 = os.getenv('UJI_VD78', '/tmp/ujiD_root/vd_file78.txt')
SANDI = os.getenv('E2E_SANDI_BERAT', 'UjiBerat123!')

LULUS = GAGAL = 0
OP = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
H = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                   '(KHTML, like Gecko) Chrome/151.0 Safari/537.36'}

fid = None
path_uji = None
uid = None


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
        with OP.open(req, timeout=180) as r:
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
    import urllib.parse
    data = urllib.parse.urlencode({'email': email, 'password': sandi}).encode()
    req = urllib.request.Request(BASE + '/masuk', data=data, headers=h)
    try:
        with OP.open(req, timeout=60) as r:
            return r.status in (200, 303)
    except urllib.error.HTTPError as e:
        return e.code in (200, 303)
    except Exception:
        return False


def isi_docx(path):
    """Teks paragraf dari .docx — pakai FUNGSI APLIKASI yang sama
    (`app.ai._teks_dari_docx`) supaya kutipan uji persis yang dilihat
    server saat `pipa.periksa()`."""
    from app.ai import _teks_dari_docx
    from pathlib import Path as _P
    return [t for t in _teks_dari_docx(_P(path)).split('\n\n') if t.strip()]


def xml_docx(path):
    with zipfile.ZipFile(path) as z:
        return z.read('word/document.xml').decode('utf-8', 'ignore')


# ═══════════════════════════════════════════════════════════════════════
# BAGIAN A — UNIT (langsung dari sumber, tanpa server)
# ═══════════════════════════════════════════════════════════════════════
def bagian_a():
    sys.path.insert(0, SRC)
    from app.pipa import buang_catatan_ai, gabung_mentah, periksa  # noqa: E402

    print('\n── A. UNIT (pipa.buang_catatan_ai / gabung_mentah) ──')

    # A1 — data NYATA file78
    if os.path.exists(VD78):
        vd = open(VD78, encoding='utf-8').read()
        bersih, catatan = buang_catatan_ai(vd)
        ada_dua = ('Catatan untuk Anda' in ' '.join(catatan)
                   and 'Catatan untuk komentar' in ' '.join(catatan))
        cek('A1 2 catatan AI panjang file78 terangkat', ada_dua,
            f'{len(catatan)} blok: {[c[:38] for c in catatan]}')
        cek('A1 "Catatan untuk Anda" hilang dari isi',
            'Catatan untuk Anda' not in bersih)
        cek('A1 "Catatan untuk komentar" hilang dari isi',
            'Catatan untuk komentar' not in bersih)
        cek('A1 sinyal "TIDAK ADA PERUBAHAN" buatan AI hilang',
            'TIDAK ADA PERUBAHAN' not in bersih)
        cek('A1 kalimat mahasiswa PERTAMA tetap ada',
            'Pesatnya perkembangan teknologi' in bersih)
        cek('A1 isi file78 tidak berkurang drastis',
            len(bersih) > len(vd) * 0.9,
            f'{len(vd)} → {len(bersih)} kar (buang '
            f'{len(vd) - len(bersih)} kar catatan AI)')
    else:
        cek('A1 berkas vd_file78 tersedia', False, f'tidak ada: {VD78}')

    # A2 — pola sempit, 2 arah
    contoh = ('Catatan untuk Anda: bagian ini tidak bisa saya kerjakan.\n\n'
              'Mahasiswa mencatat bahwa data catatan survei dipilih teliti '
              'dan diverifikasi dosen pembimbing.\n\n'
              'Tidak ada perubahan yang perlu dilakukan pada bagian ini.')
    b2, c2 = buang_catatan_ai(contoh)
    cek('A2 catatan AI (2 paragraf) hilang', len(c2) == 2, f'{len(c2)}')
    cek('A2 kalimat mahasiswa memuat kata "catatan" TETAP ADA',
        'data catatan survei dipilih teliti' in b2)
    cek('A2 isi yang bersih tidak kosong', len(b2) > 60, f'{len(b2)} kar')

    # A3 — penomoran ulang + cakupan tolak
    raw1 = ('[PROFIL] uji\n\n[K1-KUTIP-ASLI]\nkalimat satu unik\n'
            '[K1-GANTI-JADI]\nganti satu')
    raw2 = ('[K1-CAKUPAN: tolak]\n[K1-KUTIP-ASLI]\nkalimat dua unik\n'
            '[K1-GANTI-JADI]\nganti dua')
    raw3 = ('[K1-KUTIP-ASLI]\nkalimat tiga unik\n'
            '[K1-GANTI-JADI]\nganti tiga')
    gabung = gabung_mentah([raw1, raw2])
    cek('A3 nomor K diurutkan ulang (K1 ada, K2 tidak bocor)',
        gabung.count('KUTIP-ASLI]') == 1 and '[K1-KUTIP-ASLI]' in gabung,
        repr(gabung[:80]))
    g23 = gabung_mentah([raw1, raw3])
    nomor = re.findall(r'\[K(\d+)-KUTIP-ASLI\]', g23)
    cek('A3 dua bagian bernomor urut K1,K2 (tabrakan nomor kembar tertangani)',
        nomor == ['1', '2'], f'nomor={nomor}')

    # A4 — hasil gabung DAPAT dipakai pipa (editan nyata)
    naskah = ('Pembuka. kalimat satu unik.\n\n'
              'Isi. kalimat tiga unik.\n\n'
              'Penutup.')
    h = periksa(g23, naskah)
    cek('A4 pipa menerima gabungan (ok + 2 editan)',
        h.ok and len(h.editan) == 2, f'ok={h.ok} editan={len(h.editan)} '
        f'ditolak={h.ditolak}')

    # A5 — bentuk lama tanpa penanda → '' (tak ada pendamping)
    cek('A5 jawaban bentuk lama → "" (pendamping kosong = pagar A aktif)',
        gabung_mentah(['jawaban bentuk lama tanpa penanda KUTIP',
                       'isi naskah biasa']) == '')

    # A6 — catatan AI di dalam GANTI-JADI ikut dibuang
    raw6 = ('[K1-KUTIP-ASLI]\nkalimat target\n[K1-GANTI-JADI]\n'
            'Catatan untuk Anda: abaikan ini.\n\n'
            'Isi revisi yang sebenarnya tetap dipakai.')
    g6 = gabung_mentah([raw6])
    cek('A6 catatan AI di GANTI-JADI hilang',
        'Catatan untuk Anda' not in g6 and g6 != '')
    cek('A6 isi revisi GANTI-JADI tetap ada',
        'Isi revisi yang sebenarnya' in g6)

    # A7 — penulis penanda BAGIAN sudah tidak ada di sumber
    src_ai = open(os.path.join(SRC, 'app', 'ai.py'), encoding='utf-8').read()
    cek('A7 penulis penanda BAGIAN (f-string "BAGIAN {i} dari") DIHAPUS',
        'BAGIAN {i} dari' not in src_ai)
    cek('A7 gabung tanpa penanda (pakai "\\n\\n".join polos)',
        "'\\n\\n'.join(h for h in hasil_bagian" in src_ai)


# ═══════════════════════════════════════════════════════════════════════
# BAGIAN B — HTTP terapkan (atas SALINAN)
# ═══════════════════════════════════════════════════════════════════════
def pasang_versi(c, uid_b, fid_b, isi, teks_pipa=None):
    """Buat baris versi terpakai + (opsi) pendamping pipa. Kembalikan id."""
    from datetime import datetime, timezone
    kol = [r[1] for r in c.execute('PRAGMA table_info(versi_dokumen)')]
    waktu = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    isi_row = {'user_id': uid_b, 'file_id': fid_b, 'bab': '__seluruh__',
               'nomor': 991, 'isi': isi, 'komentar': 'uji opsi D',
               'model': 'uji', 'terpakai': 1, 'dibuat': waktu,
               'sumber': 'ai', 'ukuran': len(isi), 'diarsipkan': 0}
    isi_row = {k: v for k, v in isi_row.items() if k in kol}
    kunci = ','.join(isi_row)
    nilai = ','.join('?' * len(isi_row))
    c.execute(f'INSERT INTO versi_dokumen ({kunci}) VALUES ({nilai})',
              list(isi_row.values()))
    vid = c.execute('SELECT id FROM versi_dokumen WHERE file_id=? '
                    'AND nomor=991', (fid_b,)).fetchone()[0]
    if teks_pipa:
        c.execute('INSERT INTO versi_pipa (versi_id, file_id, teks, dibuat) '
                  "VALUES (?,?,?,datetime('now'))",
                  (vid, fid_b, teks_pipa))
    c.commit()
    return vid


def bagian_b():
    global fid, path_uji, uid
    print('\n── B. HTTP /api/ai/v1/terapkan (SALINAN DB + berkas) ──')

    c = sqlite3.connect(DB)
    # buktikan tabel pendamping dibuat sendiri oleh init_db (create_all)
    ada_tabel = c.execute("SELECT name FROM sqlite_master WHERE type='table' "
                          "AND name='versi_pipa'").fetchone()
    cek('B0 tabel versi_pipa DIBUAT OTOMATIS (create_all saat start)',
        ada_tabel is not None)

    bar = c.execute("SELECT id, email FROM users WHERE email LIKE '%uji%' "
                    "ORDER BY id DESC LIMIT 1").fetchone()
    if not bar:
        cek('B user uji ada', False, 'salinan DB tak memuat user uji')
        return
    uid, email = bar
    cek('B user uji siap', True, f'id={uid} {email}')

    fb = c.execute("SELECT id, nama_simpan FROM files WHERE user_id=? AND "
                   "nama LIKE '%.docx' AND terhapus_pada IS NULL "
                   "ORDER BY id DESC LIMIT 1", (uid,)).fetchone()
    if not fb:
        cek('B berkas .docx uji ada', False, 'tidak ada di salinan')
        return
    id_asli, simpan_asli = fb
    path_asli = f'{UPLOAD}/{uid}/{simpan_asli}'
    cek('B berkas uji ada di salinan', os.path.exists(path_asli),
        f'file_id={id_asli}')

    cek('B login', masuk(email, SANDI), 'cookie di jar')

    # ── salinan khusus uji (asli tidak dipakai) ─────────────────────────
    import secrets
    import shutil
    simpan_baru = 'uji-opsiD-%s.docx' % secrets.token_hex(6)
    path_uji = f'{UPLOAD}/{uid}/{simpan_baru}'
    shutil.copy2(path_asli, path_uji)
    asli = open(path_asli, 'rb').read()
    c.execute(
        "INSERT INTO files (user_id,nama,nama_simpan,ukuran,tipe,dibuat,"
        "diubah,disunting_pada,terhapus_pada,folder_id) VALUES "
        "(?,?,?,?,?,datetime('now'),datetime('now'),NULL,NULL,NULL)",
        (uid, 'uji_opsiD.docx', simpan_baru, os.path.getsize(path_uji),
         'application/vnd.openxmlformats-officedocument.wordprocessingml.document'))
    c.commit()
    fid = c.execute("SELECT id FROM files WHERE nama_simpan=?",
                    (simpan_baru,)).fetchone()[0]
    c.close()
    cek('B salinan uji siap', os.path.exists(path_uji),
        f'file_id={fid} — berkas asli TIDAK dipakai')

    par = isi_docx(path_uji)
    kutip = next((p for p in par if len(p) > 120), '')
    lain = next((p for p in par if len(p) > 60 and p != kutip), '')
    cek('B kutipan uji ditemukan', len(kutip) > 120, repr(kutip[:60]))
    cek('B paragraf pembanding ditemukan', lain != '', repr(lain[:60]))

    ganti = ('Hasil tulis presisi lewat pendamping pipa (uji Opsi D). '
             'Paragraf lain tidak boleh tersentuh.')

    teks_pipa = (f'[PROFIL] uji opsi D\n\n'
                 f'[K1-KUTIP-ASLI]\n{kutip}\n'
                 f'[K1-GANTI-JADI]\n{ganti}\n')
    teks_versi = ('───── BAGIAN 1 dari 2 ─────\n\n'
                  + kutip[:80] + ' …\n\n'
                  'Catatan untuk Anda: ini catatan AI yang tidak boleh '
                  'tersimpan sebagai isi versi.\n')

    c = sqlite3.connect(DB)
    vid = pasang_versi(c, uid, fid, teks_versi, teks_pipa)
    c.close()
    cek('B versi + pendamping terpasang (isi = bentuk LAMA, ada penanda '
        'BAGIAN & catatan AI)', vid is not None, f'versi_id={vid}')

    snap_awal = open(path_uji, 'rb').read()

    # ── B1 SEHAT ────────────────────────────────────────────────────────
    s1, d1 = buka('/api/ai/v1/terapkan', {'file_id': fid})
    det1 = d1.get('detail') or d1
    print('\n[B1] SEHAT — versi punya pendamping, tanpa `teks` di body')
    cek('B1 HTTP 200 (bukan 422)', s1 == 200, f'HTTP {s1} {str(det1)[:100]}')
    xml1 = xml_docx(path_uji)
    cek('B1 paragraf kutip DIGANTI (jalur presisi lewat pendamping)',
        ganti in xml1)
    cek('B1 paragraf LAIN tetap utuh', lain[:60] in xml1)
    cek('B1 penanda BAGIAN tidak ikut tertulis',
        'BAGIAN 1 dari 2' not in xml1)
    cek('B1 berkas berubah', open(path_uji, 'rb').read() != snap_awal,
        f'{len(snap_awal)} → {os.path.getsize(path_uji)} byte')
    try:
        logisi = open(LOG, encoding='utf-8', errors='ignore').read()
    except Exception:                                          # noqa: BLE001
        logisi = ''
    cek('B1 log server: pendamping benar-benar DIPAKAI',
        'pendamping pipa DIPAKAI' in logisi)

    snap1 = open(path_uji, 'rb').read()

    # ── B2 SUNTIK: pendamping dihapus → gagal ───────────────────────────
    c = sqlite3.connect(DB)
    c.execute('DELETE FROM versi_pipa WHERE versi_id=?', (vid,))
    c.commit()
    c.close()
    s2, d2 = buka('/api/ai/v1/terapkan', {'file_id': fid})
    det2 = d2.get('detail') or d2
    print('\n[B2] SUNTIK — pendamping DIHAPUS dari DB')
    cek('B2 HTTP 422 (tanpa pendamping = tertolak)', s2 == 422,
        f'HTTP {s2} {str(det2)[:90]}')
    cek('B2 pesan jujur + jalan keluar ("Salin hasil")',
        'Salin hasil' in json.dumps(det2), str(det2)[:110])
    cek('B2 berkas TIDAK berubah', open(path_uji, 'rb').read() == snap1)

    # ── B3 SUNTIK: kutipan tidak ada di naskah ──────────────────────────
    c = sqlite3.connect(DB)
    c.execute('UPDATE versi_pipa SET teks=? WHERE versi_id=?',
              ('[K1-KUTIP-ASLI]\nKalimat hantu yang tidak pernah ada di '
               'naskah manapun.\n[K1-GANTI-JADI]\nHasil hantu.\n', vid))
    c.commit()
    c.close()
    s3, d3 = buka('/api/ai/v1/terapkan', {'file_id': fid})
    print('\n[B3] SUNTIK — kutipan pendamping TIDAK ADA di naskah')
    cek('B3 HTTP 422', s3 == 422, f'HTTP {s3}')
    cek('B3 berkas TIDAK berubah', open(path_uji, 'rb').read() == snap1)
    cek('B3 tidak ada "Hasil hantu" tertulis',
        'Hasil hantu' not in xml_docx(path_uji))

    # ── B4 SUNTIK: GANTI-JADI jauh lebih panjang ────────────────────────
    panjang = max(400, int(len(kutip) * 4) + 200)
    c = sqlite3.connect(DB)
    c.execute('UPDATE versi_pipa SET teks=? WHERE versi_id=?',
              ('[K1-KUTIP-ASLI]\n' + kutip + '\n[K1-GANTI-JADI]\n'
               + ('Naskah dibuat baru oleh AI. ' * (panjang // 27 + 1))
               + '\n', vid))
    c.commit()
    c.close()
    s4, d4 = buka('/api/ai/v1/terapkan', {'file_id': fid})
    print('\n[B4] SUNTIK — GANTI-JADI terlalu panjang')
    cek('B4 HTTP 422', s4 == 422, f'HTTP {s4}')
    cek('B4 berkas TIDAK berubah', open(path_uji, 'rb').read() == snap1)

    # ── B5 PAGAR A: versi polos tanpa pendamping ────────────────────────
    c = sqlite3.connect(DB)
    c.execute('DELETE FROM versi_pipa WHERE versi_id=?', (vid,))
    c.execute('UPDATE versi_dokumen SET isi=? WHERE id=?',
              ('BAB V HASIL DAN PEMBAHASAN\n\nHasil penelitian menunjukkan '
               'hal penting tanpa blok KUTIP/GANTI apa pun.\n', vid))
    c.commit()
    c.close()
    s5, d5 = buka('/api/ai/v1/terapkan', {'file_id': fid})
    print('\n[B5] PAGAR OPSI A — versi polos tanpa pendamping')
    cek('B5 HTTP 422 (pagar tetap bergigi)', s5 == 422, f'HTTP {s5}')
    cek('B5 berkas TIDAK berubah', open(path_uji, 'rb').read() == snap1)

    # ── B6 arsip sah ────────────────────────────────────────────────────
    with zipfile.ZipFile(path_uji) as z:
        cek('B6 arsip .docx sah', z.testzip() is None)


def bersihkan():
    global fid, path_uji
    try:
        if path_uji and os.path.exists(path_uji):
            os.remove(path_uji)
        if fid:
            c = sqlite3.connect(DB)
            c.execute('DELETE FROM versi_pipa WHERE file_id=?', (fid,))
            c.execute('DELETE FROM versi_dokumen WHERE file_id=?', (fid,))
            c.execute('DELETE FROM files WHERE id=?', (fid,))
            c.commit()
            c.close()
        print('\n  (salinan uji dibersihkan)')
    except Exception as e:                                     # noqa: BLE001
        print(f'  (bersih-bersih gagal: {e})')


def main():
    print('=' * 62)
    print('UJI 2 ARAH OPSI D — pendamping pipa + bersih-bersih')
    print(f'BASE={BASE}\nDB={DB}\nUPLOAD={UPLOAD}\nSRC={SRC}')
    print('=' * 62)
    try:
        bagian_a()
        bagian_b()
    finally:
        bersihkan()
    # ── berkas asli user TIDAK tersentuh ─────────────────────────────────
    print('\n[CTX] berkas asli user')
    if fid and path_uji:
        c = sqlite3.connect(DB)
        bar = c.execute('SELECT nama_simpan FROM files WHERE id=?',
                        (fid,)).fetchone()
        c.close()
        cek('salinan uji benar-benar dihapus dari DB', bar is None)
    print('\n' + '=' * 62)
    print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
    print('=' * 62)
    return 0 if GAGAL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
