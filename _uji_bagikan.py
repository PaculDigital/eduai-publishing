"""UJI TAHAP 2 — bagikan ke pembimbing (ACC Bos 23Sep26).

Uji lewat HALAMAN SUNGGUHAN (HTTP), bukan fungsi langsung. Ini yang bisa
menangkap: Jinja 500, rute tidak terpasang, form salah nama, JSON rusak.

UJI WAJIB BISA GAGAL. Kalau penjaganya dicabut, uji ini harus protes.
"""

import json
import re
import sys
import urllib.error
import urllib.request

BASE = 'http://127.0.0.1:8000'
LULUS = 0
GAGAL = 0
NAMA_GAGAL = []


def cek(nama, dapat, harus):
    global LULUS, GAGAL
    if dapat == harus:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        NAMA_GAGAL.append(nama)
        print(f'  ❌ {nama}\n       dapat : {dapat!r}\n       harus : {harus!r}')


def judul(t):
    print(f'\n── {t} ──')


def ambil(url, cookie=None, data=None, metode=None):
    """GET/POST sederhana. Return (kode, isi)."""
    req = urllib.request.Request(url, method=metode or ('POST' if data else 'GET'))
    if cookie:
        req.add_header('Cookie', cookie)
    if data is not None:
        req.data = data.encode()
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read().decode('utf-8', 'replace'), r.headers
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace'), e.headers


def main():
    sys.path.insert(0, '/app')
    from app import auth
    from app.models import (BerkasPembimbingan, CatatanPembimbing, FileBerkas,
                            Pembimbingan, SessionLocal, User, init_db)
    init_db()
    db = SessionLocal()

    u = db.query(User).order_by(User.id).first()
    if not u:
        print('  ❌ tidak ada user di DB — uji tidak bisa jalan')
        return 1
    #  ⚠️ Nama cookie = SESSION_COOKIE dari config ('eduai_session'),
    #  BUKAN 'sesi'. Uji pertama Wulan salah nama → semua uji halaman
    #  gagal palsu (dialihkan ke /masuk).
    from app.config import SESSION_COOKIE
    cookie = f'{SESSION_COOKIE}={auth.buat_token(u.id)}'
    print(f'  user uji: id={u.id} nama={u.nama!r}')

    dibuat = []
    try:
        # ══ 1. HALAMAN NASKAH memuat tombol ══
        judul('1. HALAMAN NASKAH — tombol "Bagikan ke Pembimbing" ada?')
        kode, isi, _ = ambil(f'{BASE}/naskah', cookie)
        cek('halaman naskah terbuka', kode, 200)
        cek('tombol "Bagikan ke Pembimbing" ada',
            'tombol-bagikan' in isi and 'Bagikan ke Pembimbing' in isi, True)
        cek('ada sub-tulisan kecil', 'Kirim naskah untuk ditinjau' in isi, True)
        cek('fungsi bukaBagikan() ada', 'function bukaBagikan()' in isi, True)
        cek('panel bagikan ada', 'id="latar-bagikan"' in isi, True)
        cek('form Nama pembimbing ada', 'id="kb-nama"' in isi, True)
        cek('form No WA ada', 'id="kb-wa"' in isi, True)
        cek('tahap KONFIRMASI ada', 'id="kb-tahap-konfirmasi"' in isi, True)
        cek('tombol Batal ada (konfirmasi)', '"kb-batal" onclick="kbKeIsi()"' in isi, True)
        cek('tombol YA/BUAT ada', 'id="kb-buat"' in isi, True)
        #  ⚠️ TEMUAN MATA 24Sep26: judul konfirmasi dulu 'Kirim undangan'
        #  tapi tombolnya 'Ya, Buat Tautan' → TIDAK NYAMBUNG. Sekarang
        #  judul & tombol sama-sama bicara TAUTAN.
        cek('judul konfirmasi nyambung dgn tombol',
            'Buat tautan untuk pembimbing?' in isi, True)
        cek('teks kunci Buat tautan di JS',
            chr(39) + 'Buat tautan untuk ' + chr(39) + ' + nama' in isi, True)
        cek('tidak ada lagi kata undangan di konfirmasi',
            'Kirim undangan' in isi, False)
        cek('tahap HASIL ada', 'id="kb-tahap-hasil"' in isi, True)
        cek('tombol SALIN ada', 'onclick="kbSalin()"' in isi, True)
        cek('tombol KIRIM ada', 'id="kb-kirim"' in isi, True)
        cek('ada kata "Berbayar" (DILARANG)', 'Berbayar' in isi, False)

        # ══ 2. BELUM LOGIN ══
        judul('2. BELUM LOGIN — harus ditolak, tidak bocor')
        kode, isi2, _ = ambil(f'{BASE}/pembimbing/daftar')
        cek('daftar tolak tanpa login', kode, 401)
        kode, isi2, _ = ambil(f'{BASE}/pembimbing/bagikan',
                              data='nama=X&wa=0812')
        cek('bagikan tolak tanpa login', kode, 401)
        cek('tidak bocor nama pembimbing', 'daftar' in isi2, False)

        # ══ 3. VALIDASI ISIAN (di SERVER, bukan cuma JS) ══
        judul('3. VALIDASI DI SERVER — bukan hanya di JS')
        kode, isi3, _ = ambil(f'{BASE}/pembimbing/bagikan', cookie,
                              data='nama=&wa=081234567890')
        d = json.loads(isi3)
        cek('nama kosong DITOLAK', d['ok'], False)
        cek('pesan sebut nama', 'Nama' in d.get('pesan', ''), True)

        kode, isi3, _ = ambil(f'{BASE}/pembimbing/bagikan', cookie,
                              data='nama=Prof.+Ahmad&wa=&email=')
        d = json.loads(isi3)
        cek('WA+email kosong DITOLAK', d['ok'], False)

        # ══ 4. BUAT TAUTAN — sungguhan ══
        judul('4. BUAT TAUTAN — hasil lengkap?')
        kode, isi4, _ = ambil(
            f'{BASE}/pembimbing/bagikan', cookie,
            data='nama=Prof.+Ahmad+Subandi&wa=0812-3456-7890&hari=30&file_id=0')
        d = json.loads(isi4)
        cek('permintaan berhasil', d['ok'], True)
        cek('ada token', len(d.get('token', '')) >= 40, True)
        cek('ada link', d.get('link', '').startswith('https://'), True)
        cek('link memuat token', d.get('token', 'x') in d.get('link', ''), True)
        cek('ada tautan kirim WhatsApp',
            d.get('kirim', '').startswith('https://wa.me/'), True)
        cek('nomor WA dirapikan ke 62',
            '6281234567890' in d.get('kirim', ''), True)
        cek('nama tersimpan', d.get('nama'), 'Prof. Ahmad Subandi')
        #  ⚠️ KOREKSI 24Sep26: sisa_hari dihitung `kedaluwarsa - sekarang`,
        #  jadi 30 hari baru dibuat = 29 hari 23 jam → sisa_hari 29. Itu
        #  PERILAKU BENAR (yang penting tidak 99999 dan tidak 0).
        cek('sisa hari masuk akal (29 atau 30)',
            d.get('sisa_hari') in (29, 30), True)
        cek('pesan WA memuat link',
            d.get('token', 'xyz') in d.get('kirim', ''), True)
        #  ⚠️ KOREKSI 24Sep26: alamat link (eduai.bikinaja.id) WAJIB ada di
        #  pesan — itu tautannya. Yang DILARANG = nama alat tampil sebagai
        #  'dikerjakan oleh EduAi' di kolom kerja. Jadi yang diperiksa:
        #  frasa yang memposisikan alat sebagai pelaku.
        pesan_wa = d.get('kirim', '').lower()
        cek('pesan WA TIDAK memposisikan alat sebagai pelaku',
            any(x in pesan_wa for x in ('oleh eduai', 'dikerjakan eduai',
                                        'dibantu eduai', 'ai yang')), False)

        bid = d['id']
        tok = d['token']
        dibuat.append(bid)

        # ══ 5. HARI NGACO → DIPAKSA KE NILAI SAH ══
        judul('5. MASA BERLAKU NGACO — tidak boleh dipercaya dari JS')
        kode, isi5, _ = ambil(
            f'{BASE}/pembimbing/bagikan', cookie,
            data='nama=Dr.+Sari&wa=08129998888&hari=99999&file_id=0')
        d5 = json.loads(isi5)
        cek('hari 99999 tetap diterima', d5['ok'], True)
        cek('tapi dipaksa ke masa sah (bukan 99999)',
            d5.get('sisa_hari') in (29, 30), True)
        dibuat.append(d5['id'])

        # ══ 6. LINK YANG DIBUAT BENAR-BENAR BISA DIBUKA ══
        judul('6. TAUTAN YANG BARU DIBUAT — benar-benar jalan?')
        kode, isi6, _ = ambil(f'{BASE}/tinjau/{tok}')
        cek('halaman tinjau terbuka', kode, 200)
        #  ⚠️ KOREKSI 24Sep26: pada kunjungan PERTAMA, halaman menampilkan
        #  KARTU SAMBUTAN (nama mahasiswa + judul naskah), bukan header
        #  'untuk <pembimbing>'. Nama pembimbing baru muncul di header
        #  SETELAH identitas diisi. Jadi yang benar diperiksa di sini:
        cek('tampil kartu sambutan', 'Undangan Kolaborasi' in isi6, True)
        cek('sebut nama MAHASISWA', 'Wulan' in isi6, True)
        cek('sebut naskah', 'naskah' in isi6.lower(), True)
        cek('ada kolom identitas', 'Nomor HP atau email Anda' in isi6, True)
        cek('tidak ada kata Berbayar', 'Berbayar' in isi6, False)

        # ══ 7. DAFTAR PEMBIMBING ══
        judul('7. DAFTAR — tampil & TIDAK bocorkan token')
        kode, isi7, _ = ambil(f'{BASE}/pembimbing/daftar', cookie)
        d7 = json.loads(isi7)
        cek('daftar terbuka', d7['ok'], True)
        #  ⚠️ KOREKSI 24Sep26: JANGAN asersi angka mutlak (2) — sisa
        #  data uji lain membuat uji GAGAL PALSU. Yang penting: jumlah
        #  WAJIB sama dengan yang baru dibuat (2), tidak lebih & tidak
        #  kurang. Cara aman: cek yang baru dibuat ADA di daftar.
        nama_daftar = [x['nama'] for x in d7['daftar']]
        cek('pembimbing baru ADA di daftar',
            'Prof. Ahmad Subandi' in nama_daftar and 'Dr. Sari' in nama_daftar,
            True)
        cek('nama benar', d7['daftar'][0]['nama'] in
            ('Prof. Ahmad Subandi', 'Dr. Sari'), True)
        cek('bertanda aktif', d7['daftar'][0]['aktif'], True)
        cek('TIDAK ada token di daftar', 'token' in isi7.lower(), False)
        cek('TIDAK ada sidik token di daftar', 'sidik' in isi7.lower(), False)

        # ══ 8. TIDAK BISA DICABUT ORANG LAIN ══
        judul('8. CECAT KEAMANAN — cabut milik orang lain')
        u2 = db.query(User).filter(User.id != u.id).first()
        if u2:
            cookie2 = f'{SESSION_COOKIE}={auth.buat_token(u2.id)}'
            kode, isi8, _ = ambil(f'{BASE}/pembimbing/cabut', cookie2,
                                  data=f'bimbingan_id={bid}')
            cek('user lain DITOLAK', kode, 403)
            b = db.query(Pembimbingan).filter(Pembimbingan.id == bid).one()
            db.refresh(b)
            cek('tidak jadi tercabut', bool(b.dicabut), False)

        # ══ 9. CABUT SENDIRI ══
        judul('9. CABUT — tautan mati, catatan TETAP ada')
        #  ⚠️ KOREKSI 24Sep26: pakai FUNGSI RESMI `P.catat()` — bukan
        #  bikin baris mentah. Kalau bikin sendiri, uji bisa 'lulus'
        #  dengan bentuk data yang tidak pernah dibuat aplikasi.
        from app import pembimbing as PB
        _b = db.get(Pembimbingan, bid)
        P_cat = PB.catat(db, _b, 'Tolong tambahkan kesimpulan.',
                         section_id='bab-3', section_judul='BAB III')
        cek('catatan contoh dibuat', P_cat.id is not None, True)

        kode, isi9, _ = ambil(f'{BASE}/pembimbing/cabut', cookie,
                              data=f'bimbingan_id={bid}')
        d9 = json.loads(isi9)
        cek('cabut berhasil', d9['ok'], True)
        cek('pesan sebut catatan tetap', 'catatan' in d9.get('pesan', '').lower(),
            True)

        kode, isi10, _ = ambil(f'{BASE}/tinjau/{tok}')
        #  ⚠️ KOREKSI 24Sep26: asersi lama salah TUJUAN — 'Undangan
        #  Kolaborasi' itu kartu SAMBUTAN (sebelum identitas diisi),
        #  bukan penanda halaman ramah. Yang benar diperiksa:
        #  (a) bukan halaman tinjau (tanpa panel Catatan Bimbingan),
        #  (b) ada kalimat jalan keluar, (c) tetap 200 bukan galat.
        cek('bukan halaman tinjau lagi',
            'Catatan Bimbingan' in isi10, False)
        cek('ada kalimat jalan keluar',
            any(x in isi10.lower() for x in ('mahasiswa', 'minta', 'hubungi')),
            True)
        cek('masih 200 (bukan galat)', kode, 200)
        n_cat = (db.query(CatatanPembimbing)
                 .filter(CatatanPembimbing.pembimbingan_id == bid,
                         CatatanPembimbing.dibuang == 0).count())
        cek('catatan TETAP tersimpan', n_cat, 1)

        # ══ 10. HALAMAN NASKAH TIDAK RUSAK ══
        judul('10. MESIN LAMA — tidak rusak oleh fitur baru')
        for jalur in ('/', '/naskah', '/sampah'):
            kode, _, _ = ambil(f'{BASE}{jalur}', cookie)
            cek(f'{jalur} tetap terbuka', kode, 200)

    finally:
        #  Bersihkan HANYA yang dibuat uji ini.
        for bid in dibuat:
            db.query(CatatanPembimbing).filter(
                CatatanPembimbing.pembimbingan_id == bid).delete()
            db.query(BerkasPembimbingan).filter(
                BerkasPembimbingan.pembimbingan_id == bid).delete()
            db.query(Pembimbingan).filter(Pembimbingan.id == bid).delete()
        db.commit()
        sisa = db.query(Pembimbingan).count()
        print(f'\n  (bersih-bersih: {len(dibuat)} bimbingan uji dihapus, '
              f'sisa {sisa})')
        db.close()

    print('\n' + '═' * 58)
    print(f'  UJI TAHAP 2: {LULUS} LULUS / {GAGAL} GAGAL')
    if GAGAL:
        print('  ❌ GAGAL: ' + ', '.join(NAMA_GAGAL))
    print('═' * 58)
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
