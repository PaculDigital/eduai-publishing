"""UJI LOG REVISI 3 LAPIS (Tahap 2.3, ACC Bos 24Sep26).

Permintaan Bos: "Log Revisi compact (3 lapis lipatan)".
  LAPIS 1 — 4 angka ringkasan
  LAPIS 2 — 1 baris per MASALAH (bukan per ronde)
  LAPIS 3 — ronde-ronde masalah itu

⚠️ UJI INI WAJIB BISA GAGAL (bergigi). Kalau penjaganya dicabut → protes.
"""

import json
import sys
import urllib.error
import urllib.request

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


def main():
    sys.path.insert(0, '/app')
    from app import auth, pembimbing as P
    from app.config import SESSION_COOKIE
    from app.models import (CatatanPembimbing, FileBerkas, SessionLocal,
                            User, init_db)

    init_db()
    db = SessionLocal()
    #  ⚠️ PELAJARAN 24Sep26 (2× salah):
    #    `catatan_pembimbing.berkas_id` FK ke `pembimbingan_berkas`
    #    (BUKAN `file_berkas`) → JANGAN diisi dengan FileBerkas.id.
    #    `penulis_id` FK ke `pembimbingan.id` → BENAR pakai b.id.
    #  Karena berkas_id nullable, uji ini tidak mengisinya sama sekali.
    fb = db.query(FileBerkas).order_by(FileBerkas.id).first()
    u = db.get(User, fb.user_id)
    print(f'  (uji pakai user {u.id} "{u.nama}")')
    ck = SESSION_COOKIE + '=' + auth.buat_token(u.id)

    def get(path):
        r = urllib.request.Request('http://127.0.0.1:8000' + path,
                                   headers={'Cookie': ck})
        try:
            h = urllib.request.urlopen(r, timeout=20)
            return h.status, h.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode('utf-8', 'ignore')

    # ══ SIAPKAN: bimbingan + 1 MASALAH dengan 3 RONDE ══
    judul('0. Menyiapkan data uji (1 masalah, 3 ronde)')
    b, token = P.buat_bimbingan(db, u.id, 'Prof. Uji Log', hari=30,
                                wa='081200000001')
    bid = b.id
    fid = None

    #  Pakai fungsi RESMI P.catat() — bukan bikin baris mentah.
    #  (Pelajaran 24Sep26: baris mentah gagal karena `penulis_id` wajib.)
    r1 = P.catat(db, b, 'Rumusan masalah belum tajam.',
                 section_judul='BAB I')
    #  RONDE 2: menempel ke ronde 1 -> jadi ronde 2 di rantai yang sama
    r2 = P.catat(db, b, 'Sudah lebih baik, tapi variabelnya belum jelas.',
                 section_judul='BAB I', induk_id=r1.id)
    #  RONDE 3: tandai hijau (sudah oke) -- lewat warna
    r3 = P.catat(db, b, 'Sudah oke.', section_judul='BAB I', induk_id=r1.id)
    r3.warna = 'hijau'
    db.commit()
    #  MASALAH KEDUA (lepas, bukan anak) + tautan rujukan
    P.catat(db, b, 'Tinjauan pustaka kurang rujukan 5 tahun terakhir.',
            section_judul='BAB II',
            tautan='https://contoh.id/rujukan')
    cek('ronde 2 menempel ke ronde 1', r2.ronde, 2)
    cek('ronde 3 menempel ke ronde 1', r3.ronde, 3)
    #  ⚠️ BUG 24Sep26: dulu ronde 3 SELALU jadi 2. Uji ini penjaganya.
    r4b = P.catat(db, b, 'Ronde keempat.', section_judul='BAB I',
                  induk_id=r1.id)
    cek('ronde 4 = 4 (bug lama: selalu 2)', r4b.ronde, 4)
    db.delete(r4b)
    db.commit()

    cek('data siap: 4 catatan', db.query(CatatanPembimbing)
        .filter(CatatanPembimbing.pembimbingan_id == bid).count(), 4)

    try:
        # ══ 1. RUTE BUKA & HANYA MEMBACA ══
        judul('1. Rute log terbuka & memang hanya membaca')
        s, isi = get(f'/pembimbing/log/{bid}')
        cek('HTTP 200', s, 200)
        d = json.loads(isi)
        cek('ok=True', d.get('ok'), True)

        # ══ 2. LAPIS 1 — 4 ANGKA RINGKASAN ══
        judul('2. LAPIS 1 — angka ringkasan jujur')
        a = d.get('angka', {})
        cek('total = 4', a.get('total'), 4)
        cek('selesai = 1 (ronde ke-3 hijau)', a.get('selesai'), 1)
        #  ⚠️ KOREKSI UJI 24Sep26: 'hilang' di sini artinya catatan
        #  TIDAK MENEMPEL pada potongan teks tertentu (teks_asli kosong).
        #  Catatan uji ini memang catatan umum tanpa sorotan → 4.
        #  BUKAN 'naskah berubah' (itu urusan Tahap 3).
        #  ⚠️ PERBAIKAN 24Sep26 (cacat temuan MATA): catatan tanpa sorotan
        #  TIDAK lagi dihitung 'hilang' → masuk 'umum'. Label tampil
        #  'Catatan umum', BUKAN 'Naskah berubah'.
        cek('hilang = 0 (tdk ada sorotan yg hilang)', a.get('hilang'), 0)
        cek('umum = 4 (catatan tanpa sorotan)', a.get('umum'), 4)
        cek('belum = 3', a.get('belum'), 3)

        # ══ 3. LAPIS 2 — 1 BARIS PER MASALAH (bukan per ronde) ══
        judul('3. LAPIS 2 — 1 baris = 1 MASALAH (INILAH INTI "COMPACT")')
        cek('jumlah baris = 2 MASALAH (bukan 4 ronde)', d.get('jumlah_baris'), 2)
        baris = d.get('baris', [])
        cek('baris ada isinya', len(baris), 2)

        #  Baris untuk masalah 3-ronde harus punya jumlah_ronde = 3
        tiga = [x for x in baris if x['jumlah_ronde'] == 3]
        cek('ada 1 masalah dgn 3 ronde', len(tiga), 1)
        if tiga:
            t = tiga[0]
            cek('masalah 3-ronde: ronde tersimpan 3', len(t['ronde']), 3)
            cek('warna diambil dari RONDE TERBARU (hijau)',
                t['warna'], 'hijau')
            cek('isi masalah = isi KEPALA (bukan terbaru)',
                'Rumusan masalah' in t['masalah'], True)

        # ══ 4. LAPIS 3 — RONDE BERURUTAN ══
        judul('4. LAPIS 3 — ronde berurutan 1→2→3')
        if tiga:
            ronde = tiga[0]['ronde']
            cek('ronde 1 dulu', ronde[0]['ronde'], 1)
            cek('ronde 2', ronde[1]['ronde'], 2)
            cek('ronde 3 terakhir', ronde[2]['ronde'], 3)
            cek('ronde 1 masih kuning', ronde[0]['warna'], 'kuning')
            cek('ronde 3 sudah hijau', ronde[2]['warna'], 'hijau')

        #  Masalah kedua: tautan harus ikut (bukan hilang)
        dua = [x for x in baris if x['jumlah_ronde'] == 1]
        cek('ada 1 masalah 1 ronde', len(dua), 1)
        if dua:
            cek('tautan rujukan ikut dikirim',
                'contoh.id' in (dua[0]['ronde'][0].get('tautan') or ''), True)

        # ══ 5. BATAS DARI SERVER (bukan angka di JS) ══
        judul('5. Batas tampil datang dari SERVER')
        cek('batas_tampil ada', 'batas_tampil' in d, True)
        cek('batas_tampil = 5', d.get('batas_tampil'), 5)

        # ══ 6. JANGAN BOCORKAN DATA PEMBIMBING LAIN ══
        judul('6. Keamanan — tidak boleh lihat milik user lain')
        s2, _ = get('/pembimbing/log/999999')
        cek('bimbingan tak ada → 403/404', s2 in (403, 404), True)

        # ══ 6b. CACAT 1 — label tidak menyesatkan ══
        judul('6b. Cacat temuan MATA: label TIDAK menyesatkan')
        s5, isi5 = get('/naskah')
        cek('label "Catatan umum" ADA', 'Catatan umum' in isi5, True)
        cek('angka ringkasan pakai a.umum', 'a.umum' in isi5, True)
        #  'Naskah berubah' BOLEH ada di JS (untuk keadaan hilang sungguhan),
        #  tapi TIDAK boleh dipakai untuk keadaan 'umum'.
        cek('keadaan umum TIDAK dilabeli "Naskah berubah"',
            "b.keadaan === 'umum' ? 'Catatan umum'" in isi5, True)
        #  ⚠️ BUG CSS 24Sep26: selektor memakai `.kb-log-baris` (itu ID!)
        #  → ronde TIDAK PERNAH bisa dibuka. Uji ini penjaganya.
        #  (jangan cek kata di komentar — itu teks penjelasan, bukan kode)
        cek('CSS buka ronde: aturannya BENAR',
            '.masalah.buka .kb-log-ronde{display:block}' in isi5, True)
        cek('CSS buka ronde pakai .masalah.buka',
            '.masalah.buka .kb-log-ronde{display:block}' in isi5, True)

        # ══ 6c. CACAT 2 — nama kosong DITOLAK di akar ══
        judul('6c. Cacat temuan MATA: nama kosong ditolak di AKAR')
        try:
            P.buat_bimbingan(db, u.id, '   ', hari=30, wa='081200000002')
            cek('nama kosong DITOLAK', 'LOLOS', 'DITOLAK')
        except ValueError:
            cek('nama kosong DITOLAK', 'DITOLAK', 'DITOLAK')
        except Exception as e:
            cek('nama kosong DITOLAK', type(e).__name__, 'ValueError')

        # ══ 7. TIDAK MENGUBAH APA PUN ══
        judul('7. Hanya membaca — jumlah catatan tidak berubah')
        db.expire_all()
        cek('masih 4 catatan sesudah dibaca',
            db.query(CatatanPembimbing)
            .filter(CatatanPembimbing.pembimbingan_id == bid).count(), 4)

        # ══ 8. HALAMAN MAHASISWA TIDAK RUSAK ══
        judul('8. Halaman lain tetap hidup')
        s3, isi3 = get('/naskah')
        cek('/naskah HTTP 200', s3, 200)
        cek('kerangka Log Revisi ADA di halaman', 'kb-log-angka' in isi3, True)
        cek('judul Log Revisi ada', 'Log Revisi' in isi3, True)
        cek('fungsi kbMuatLog ada', 'function kbMuatLog' in isi3, True)
        cek('koma desimal CSS tidak ada (bug 13,5px)', '13,5px' in isi3, False)
        s4, _ = get('/pembimbing/daftar')
        cek('/pembimbing/daftar tetap 200', s4, 200)
    finally:
        # ══ BERSIH-BERSIH data uji ══
        db.rollback()
        #  ⚠️ URUTAN PENTING: `induk_id` FK ke catatan_pembimbing sendiri.
        #  Hapus ANAK dulu, induk belakangan — kalau terbalik → FK gagal.
        rows = (db.query(CatatanPembimbing)
                .filter(CatatanPembimbing.pembimbingan_id == bid)
                .order_by(CatatanPembimbing.ronde.desc()).all())
        for r in rows:
            db.delete(r)
            db.commit()
        bb = db.get(P.Pembimbingan, bid)
        if bb:
            db.delete(bb)
            db.commit()
        print(f'\n  (bersih-bersih: bimbingan uji {bid} dihapus)')

    print('\n' + '═' * 58)
    print(f'  UJI LOG REVISI 3 LAPIS: {LULUS} LULUS / {GAGAL} GAGAL')
    if GAGAL:
        print('  ❌ GAGAL: ' + ', '.join(NAMA_GAGAL))
    print('═' * 58)
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
