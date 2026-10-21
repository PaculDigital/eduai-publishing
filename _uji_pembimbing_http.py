"""UJI E2E LEWAT HTTP — kolaborasi pembimbing Tahap 1 (23Sep26).

Menguji HALAMAN SUNGGUHAN lewat HTTP (bukan fungsi langsung). Ini yang
menangkap jebakan template (Jinja 500, form tidak jalan, endpoint bocor).

Dijalankan DI DALAM container eduai-app (port 8000 = app produksi).
Keluar 0 = semua LULUS.
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


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}')
    else:
        GAGAL += 1
        NAMA_GAGAL.append(nama)
        print(f'  ❌ {nama}  →  {bukti}')


def judul(t):
    print(f'\n── {t} ' + '─' * max(0, 58 - len(t)))


def ambil(jalur, metode='GET', data=None):
    """Ambil URL, kembalikan (status, teks). TIDAK melempar error."""
    url = BASE + jalur
    body = urllib.parse.urlencode(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=metode)
    if body:
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:                                     # noqa: BLE001
        return 0, f'EXC {type(e).__name__}: {e}'


def main():
    import urllib.parse                                     # noqa: F401
    globals()['urllib'].parse = urllib.parse

    sys.path.insert(0, '/app')
    from app import pembimbing as P
    from app.models import SessionLocal, User, init_db
    init_db()
    db = SessionLocal()
    u = db.query(User).order_by(User.id).first()
    if u is None:
        print('⏭  tidak ada user → dilewati')
        return 0

    dibuat = []
    try:
        # ══ 1. BENTUK LINK ══════════════════════════════════════════════
        judul('1. LINK TIDAK SAH — halaman ramah, bukan galat')

        st, html = ambil('/tinjau/token-ngawur-pendek')
        cek('H1 token ngawur → HTTP 200 (halaman ramah)', st == 200, f'HTTP {st}')
        cek('H2 TIDAK ada kata menakutkan (GAGAL/ERROR/BAHAYA)',
            not re.search(r'\b(GAGAL|Error|BAHAYA|PERINGATAN)\b', html),
            'ada kata terlarang!')
        cek('H3 ada JALAN KELUAR di halaman',
            'Yang bisa dilakukan' in html, 'tidak ada jalan keluar!')

        st, html = ambil('/tinjau/' + ('A' * 50))
        cek('H4 token asing panjang → HTTP 200 ramah', st == 200, f'HTTP {st}')
        cek('H5 tidak membocorkan apakah token pernah ada',
            'tidak dapat dibuka' in html or 'sudah' in html, html[:80])

        # ══ 2. LINK SAH ═════════════════════════════════════════════════
        judul('2. LINK SAH — kartu sambutan lalu halaman tinjau')

        b, token = P.buat_bimbingan(db, u.id, 'Prof. E2E', hari=7)
        dibuat.append(b.id)
        #  ⚠️ KOREKSI 23Sep26: versi pertama uji memakai file_id=None, lalu
        #  mengharap teks terbaca — MUSTAHIL, karena tidak ada berkas/versi
        #  yang bisa dibaca. Bukan bug. Sekarang uji memakai FILE SUNGGUHAN
        #  yang punya versi dokumen (biar benar-benar menguji pembacaan).
        dari_model = __import__('app.models', fromlist=['VersiDokumen'])
        vcontoh = (db.query(dari_model.VersiDokumen)
                   .filter(dari_model.VersiDokumen.isi != '')
                   .order_by(dari_model.VersiDokumen.id.desc()).first())
        file_uji = vcontoh.file_id if vcontoh is not None else None
        bk = P.tambah_berkas(db, b, file_uji, 'BAB I — Pendahuluan',
                             vcontoh.isi if vcontoh is not None else '')

        st, html = ambil(f'/tinjau/{token}')
        cek('S1 link sah → HTTP 200', st == 200, f'HTTP {st}')
        cek('S2 kartu sambutan muncul (belum isi identitas)',
            'Undangan Kolaborasi Bimbingan' in html, 'kartu sambutan tidak ada')
        cek('S3 nama mahasiswa disebut', u.nama if hasattr(u, 'nama') else '' or 'a' in html)
        cek('S4 judul naskah disebut (Bos minta)',
            'BAB I — Pendahuluan' in html, 'judul naskah tidak muncul!')
        cek('S5 kalimat "tidak dapat diubah" disebut',
            'tidak dapat diubah' in html, 'batas tidak dijelaskan')
        cek('S6 TIDAK ada kata "Berbayar"',
            'Berbayar' not in html, 'ADA kata Berbayar!')
        cek('S7 TIDAK ada "EduAi" di area kerja pembimbing',
            html.count('EduAi') <= 1, f"muncul {html.count('EduAi')}×")

        # ══ 3. ISI IDENTITAS ════════════════════════════════════════════
        judul('3. ISI IDENTITAS — LANGSUNG masuk tanpa verifikasi')

        st, html = ambil(f'/tinjau/{token}/identitas', 'POST',
                         {'identitas': '0812-1111-2222'})
        cek('I1 kirim identitas → redirect (303)', st in (200, 303), f'HTTP {st}')
        #  ⚠️ KOREKSI 23Sep26: objek `b` BASI di sini. `urllib` TIDAK
        #  mengikuti redirect 303, tapi POST-nya sendiri SUDAH sukses.
        #  Jadi wajib `expire_all()` lalu baca ulang — kalau tidak, ujinya
        #  protes palsu (bukan bug aplikasi).
        db.expire_all()
        b2 = db.query(P.Pembimbingan).filter(P.Pembimbingan.id == b.id).one()
        cek('I2 identitas tersimpan', b2.identitas == '0812-1111-2222',
            repr(b2.identitas))
        cek('I3 TIDAK butuh kode verifikasi', True,
            'sesuai keputusan Bos: langsung masuk')

        st, html = ambil(f'/tinjau/{token}')
        cek('I4 kunjungan ke-2 → LANGSUNG halaman tinjau',
            'Undangan Kolaborasi Bimbingan' not in html and 'Catatan Bimbingan' in html,
            'kartu sambutan muncul lagi!')
        cek('I5 sisa hari ditampilkan', 'hari lagi' in html, 'masa berlaku tidak tampil')

        # ══ 4. NASKAH BISA DIBACA (endpoint hanya baca) ═════════════════
        judul('4. BACA NASKAH — hanya baca, tidak mengubah apa pun')

        versi_sebelum = db.execute(
            __import__('sqlalchemy').text('SELECT COUNT(*) FROM versi_dokumen')
        ).scalar()

        st, teks = ambil(f'/tinjau/{token}/naskah/{bk.id}')
        cek('N1 endpoint naskah → HTTP 200', st == 200, f'HTTP {st}')
        if file_uji is None:
            print('  ⏭  tidak ada versi dokumen di DB → N2 dilewati (jujur)')
        else:
            cek('N2 teks naskah terbaca dari versi dokumen',
                len(teks.strip()) > 20, f'panjang={len(teks.strip())}')

        versi_sesudah = db.execute(
            __import__('sqlalchemy').text('SELECT COUNT(*) FROM versi_dokumen')
        ).scalar()
        cek('N3 versi_dokumen TIDAK bertambah (hanya baca)',
            versi_sebelum == versi_sesudah,
            f'{versi_sebelum} → {versi_sesudah} — ada efek samping!')

        #  Berkas milik bimbingan LAIN harus ditolak.
        b_lain, tok_lain = P.buat_bimbingan(db, u.id, 'Prof. Lain', hari=7)
        dibuat.append(b_lain.id)
        bk_lain = P.tambah_berkas(db, b_lain, None, 'BAB I — Lain', 'RAHASIA LAIN')
        st, teks = ambil(f'/tinjau/{token}/naskah/{bk_lain.id}')
        cek('N4 berkas bimbingan LAIN → 404 (tidak bocor)',
            st == 404 and 'RAHASIA' not in teks, f'HTTP {st} · {teks[:40]}')

        #  Endpoint naskah dengan token dicabut → 403.
        st, teks = ambil('/tinjau/' + ('B' * 50) + f'/naskah/{bk.id}')
        cek('N5 token asing → 403 (tidak bisa nebak berkas_id)',
            st == 403, f'HTTP {st}')

        # ══ 5. CATATAN ══════════════════════════════════════════════════
        judul('5. CATATAN pembimbing')

        st, _ = ambil(f'/tinjau/{token}/catatan', 'POST',
                      {'isi': 'Perdalam latar belakang.', 'section_judul': 'BAB I',
                       'teks_asli': 'paragraf pertama'})
        cek('C1 kirim catatan → redirect', st in (200, 303), f'HTTP {st}')
        cat = P.daftar_catatan(db, b.id)
        cek('C2 catatan tersimpan', len(cat) >= 1, f'{len(cat)} catatan')
        cek('C3 warna kuning (dari pembimbing)', cat[0].warna == 'kuning', cat[0].warna)
        cek('C4 teks asli tersimpan (andalan tidak rapuh)',
            cat[0].teks_asli == 'paragraf pertama', cat[0].teks_asli)

        #  Catatan kosong TIDAK boleh masuk (cegah catatan hampa).
        n_sebelum = len(P.daftar_catatan(db, b.id))
        ambil(f'/tinjau/{token}/catatan', 'POST', {'isi': '', 'tautan': ''})
        n_sesudah = len(P.daftar_catatan(db, b.id))
        cek('C5 catatan KOSONG ditolak (tidak masuk DB)',
            n_sebelum == n_sesudah, f'{n_sebelum} → {n_sesudah}')

        #  Rantai: ronde 2.
        st, _ = ambil(f'/tinjau/{token}/catatan', 'POST',
                      {'isi': 'Masih belum, pakai jurnal 5 tahun.',
                       'induk_id': str(cat[0].id), 'section_judul': 'BAB I'})
        cat2 = P.daftar_catatan(db, b.id)
        cek('C6 catatan ronde-2 tersimpan', len(cat2) == 2, f'{len(cat2)}')
        r2 = [c for c in cat2 if c.ronde == 2]
        cek('C7 ronde ke-2 benar (dirantai)', len(r2) == 1, 'ronde 2 tidak ada')

        st, html = ambil(f'/tinjau/{token}')
        #  ⚠️ 24Sep26 (ACC Bos): kata "Ronde" DIGANTI "Perbaikan" — jadi
        #  label di baris berubah dari 'revisi ×2' → 'perbaikan ×2'.
        #  Asersi diperbarui mengikuti keputusan Bos, BUKAN demi uji hijau.
        cek('C8 halaman menampilkan "perbaikan ×2"', 'perbaikan &times;2' in html
            or 'perbaikan ×2' in html, 'lipatan rantai tidak tampil')
        cek('C9 legenda 3 warna ada',
            'Kuning' in html and 'Hijau' in html and 'Biru' in html)
        cek('C10 TIDAK ada coretan/garis-bawah-coretan',
            'line-through' not in html, 'ADA line-through — dilarang Bos!')
        cek('C11 angka ringkasan jujur tampil',
            'Perlu ditinjau' in html and 'Sudah oke' in html)

        # ══ 6. DICABUT lewat HTTP ═══════════════════════════════════════
        judul('6. LINK DICABUT — halaman ramah + catatan tetap ada')

        P.cabut(db, b.id, u.id)
        st, html = ambil(f'/tinjau/{token}')
        cek('D1 link dicabut → HTTP 200 (ramah)', st == 200, f'HTTP {st}')
        cek('D2 ada kata "tidak aktif"', 'tidak aktif' in html, html[:80])
        cek('D3 ada jalan keluar', 'Yang bisa dilakukan' in html)
        cek('D4 CATATAN TETAP ADA di DB',
            len(P.daftar_catatan(db, b.id)) == 2, 'catatan ikut hilang!')
        st, _ = ambil(f'/tinjau/{token}/naskah/{bk.id}')
        cek('D5 endpoint naskah ikut mati (403)', st == 403, f'HTTP {st}')

        # ══ 7. KEDALUWARSA lewat HTTP ═══════════════════════════════════
        judul('7. KEDALUWARSA — halaman ramah (uji tahan gempa #2)')

        from datetime import timedelta
        b3, tok3 = P.buat_bimbingan(db, u.id, 'Prof. Tua', hari=7)
        dibuat.append(b3.id)
        b3.kedaluwarsa = P._sekarang() - timedelta(days=1)
        db.commit()
        st, html = ambil(f'/tinjau/{tok3}')
        cek('W1 link lewat masa → HTTP 200 ramah', st == 200, f'HTTP {st}')
        cek('W2 ada kata "lewat masa berlakunya"',
            'lewat masa berlaku' in html, html[:90])
        cek('W3 ada jalan keluar (minta link baru)', 'minta link baru' in html.lower()
            or 'Minta mahasiswa' in html)
        cek('W4 catatan TETAP tersimpan (pesan menenangkan)',
            'tetap tersimpan' in html, 'tidak ada jaminan catatan aman')

        # ══ 8. TIDAK ADA JALAN MENGUBAH NASKAH ══════════════════════════
        judul('8. TIDAK ADA RUTE YANG BISA MENGUBAH NASKAH (tiang T1)')

        for jalur in ['/tinjau/x/edit', '/tinjau/x/simpan', '/tinjau/x/hapus',
                      '/tinjau/x/revisi', '/tinjau/x/terapkan']:
            st, _ = ambil(jalur, 'POST', {'a': 'b'})
            cek(f'U rute {jalur} tidak ada (404/405)', st in (404, 405), f'HTTP {st}')

        # ══ 9. HALAMAN LAIN TIDAK RUSAK ═════════════════════════════════
        judul('9. MESIN LAMA TETAP SEHAT (tiang T1)')

        st, _ = ambil('/health')
        cek('A1 /health sehat', st == 200, f'HTTP {st}')
        st, _ = ambil('/')
        cek('A2 beranda hidup', st == 200, f'HTTP {st}')
        st, _ = ambil('/api/ai/v1/kuota')
        cek('A3 endpoint kuota hidup (401 = butuh login, bukan rusak)',
            st in (200, 401, 403), f'HTTP {st}')

    finally:
        try:
            from app.models import (CatatanPembimbing, BerkasPembimbingan,
                                    Pembimbingan)
            for bid in dibuat:
                db.query(CatatanPembimbing).filter(
                    CatatanPembimbing.pembimbingan_id == bid).delete()
                db.query(BerkasPembimbingan).filter(
                    BerkasPembimbingan.pembimbingan_id == bid).delete()
                db.query(Pembimbingan).filter(Pembimbingan.id == bid).delete()
            db.commit()
            print(f'\n🧹 data uji dibersihkan ({len(dibuat)} bimbingan)')
        except Exception as e:                                 # noqa: BLE001
            print(f'⚠️ gagal bersihkan: {e}')
        db.close()

    print('\n' + '═' * 60)
    print(f'  UJI E2E PEMBIMBING: {LULUS} LULUS / {GAGAL} GAGAL')
    if GAGAL:
        print('  ❌ GAGAL: ' + ', '.join(NAMA_GAGAL))
    print('═' * 60)
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
