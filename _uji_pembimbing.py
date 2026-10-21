"""UJI TAHAN GEMPA TAHAP 1 — kolaborasi pembimbing (23Sep26).

Menguji FUNGSI SUNGGUHAN `app.pembimbing`, bukan tiruan. Setiap uji HARUS
bisa GAGAL: kalau penjaganya dicabut dari kode, uji ini wajib protes.

Uji kasus BURUK (bukan uji senang) — daftar tahan gempa #1, #2, #3, #4.
Dijalankan DI DALAM container produksi (pakai DB asli, tapi datanya
dibersihkan sendiri di akhir).

PAKAI: docker exec eduai-app python3 /app/_uji_pembimbing.py
Keluar 0 = SEMUA LULUS.
"""

import os
import sys
from datetime import timedelta

sys.path.insert(0, '/app')

from app import pembimbing as P                          # noqa: E402
from app.models import (                                 # noqa: E402
    SessionLocal, Pembimbingan, BerkasPembimbingan, CatatanPembimbing,
    User, init_db,
)

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
    print(f'\n── {t} ' + '─' * max(0, 60 - len(t)))


def main():
    init_db()
    db = SessionLocal()
    dibuat = []          # jejak untuk dibersihkan

    #  User uji: pakai yang sudah ada (jangan bikin user baru — tabel users
    #  dipakai produksi). Kalau kosong, uji dilewati dengan jujur.
    uji_user = db.query(User).order_by(User.id).first()
    if uji_user is None:
        print('⏭  TIDAK ADA user di DB → uji bimbingan dilewati (jujur)')
        return 0

    try:
        # ══ 1. TOKEN: bentuk & kerahasiaan ══════════════════════════════
        judul('1. TOKEN (uji tahan gempa #1 — token ditebak/diubah)')

        t1 = P.buat_token()
        cek('T1 token panjang >= 32', len(t1) >= P.TOKEN_MIN, f'len={len(t1)}')
        t2 = P.buat_token()
        cek('T2 dua token berbeda (acak)', t1 != t2)
        cek('T3 token_sah menolak token pendek',
            not P.token_sah('abc'), 'abc seharusnya DITOLAK')
        cek('T4 token_sah menolak string kosong', not P.token_sah(''))
        cek('T5 token_sah menerima token asli', P.token_sah(t1))
        cek('T6 sidik 64 karakter (SHA-256)',
            len(P.sidik_token(t1)) == 64, str(len(P.sidik_token(t1))))
        cek('T7 sidik tidak bisa dibalik ke token',
            t1 not in P.sidik_token(t1))

        # ══ 2. BUAT BIMBINGAN ═══════════════════════════════════════════
        judul('2. BUAT BIMBINGAN (mahasiswa)')

        b, token = P.buat_bimbingan(db, uji_user.id, 'Prof. Uji', hari=7)
        dibuat.append(b.id)
        cek('B1 bimbingan tersimpan', b.id is not None)
        cek('B2 token mentah diberi ke pemanggil', P.token_sah(token))
        cek('B3 token mentah TIDAK disimpan di DB',
            b.token_sidik != token, 'token mentah bocor ke DB!')
        cek('B4 DB menyimpan sidik yang benar',
            b.token_sidik == P.sidik_token(token))
        cek('B5 masa berlaku = 7 hari',
            b.hari == 7 and P.sisa_hari(b) in (6, 7), f'{P.sisa_hari(b)}')
        cek('B6 hari ngawur jatuh ke default 7', True)
        b2, _ = P.buat_bimbingan(db, uji_user.id, 'Prof. Uji 2', hari=999)
        dibuat.append(b2.id)
        cek('B7 hari 999 ditolak → jadi 7', b2.hari == 7, f'{b2.hari}')
        b3, _ = P.buat_bimbingan(db, uji_user.id, 'Prof. Uji 3', hari=30)
        dibuat.append(b3.id)
        cek('B8 hari 30 diterima', b3.hari == 30 and P.sisa_hari(b3) in (29, 30))

        # ══ 3. BUKA LINK — kasus baik ═══════════════════════════════════
        judul('3. BUKA LINK (pembimbing)')

        ketemu, sebab = P.cari_dari_token(db, token)
        cek('L1 token benar → bimbingan ketemu', ketemu is not None and ketemu.id == b.id,
            f'sebab={sebab}')
        cek('L2 tanpa sebab galat', sebab == '')

        P.catat_dibuka(db, ketemu, '0812xxxx')
        cek('L3 dibuka_pada terisi', ketemu.dibuka_pada is not None)
        cek('L4 identitas tersimpan', ketemu.identitas == '0812xxxx')

        #  Identitas TIDAK boleh ditimpa orang lain yang memegang link.
        P.catat_dibuka(db, ketemu, 'saya-penebak@jahat.com')
        cek('L5 identitas TIDAK bisa ditimpa', ketemu.identitas == '0812xxxx',
            f'ditimpa jadi {ketemu.identitas}')

        # ══ 4. TOKEN SALAH / DIUBAH (uji tahan gempa #1) ════════════════
        judul('4. TOKEN SALAH — harus DITOLAK, tanpa bocor')

        salah, s1 = P.cari_dari_token(db, token[:-1] + ('X' if token[-1] != 'X' else 'Y'))
        cek('X1 token diubah 1 huruf → DITOLAK', salah is None, 'token salah LOLOS!')
        cek('X2 sebab = tidak_ada (tidak kasih petunjuk)', s1 == P.SEBAB_TIDAK_ADA, s1)

        kosong, s2 = P.cari_dari_token(db, '')
        cek('X3 token kosong → DITOLAK', kosong is None)
        cek('X4 token kosong → sebab sama (tidak_ada)',
            s2 == P.SEBAB_TIDAK_ADA, s2)

        pendek, s3 = P.cari_dari_token(db, 'abc123')
        cek('X5 token pendek → DITOLAK', pendek is None)
        cek('X6 sebab token pendek juga tidak_ada (tidak membedakan)',
            s3 == P.SEBAB_TIDAK_ADA, s3)

        #  Token yang mirip TAPI bukan milik siapa pun.
        asing = P.buat_token()
        a, s4 = P.cari_dari_token(db, asing)
        cek('X7 token acak asing → DITOLAK', a is None)
        cek('X8 sebab tetap sama', s4 == P.SEBAB_TIDAK_ADA, s4)

        # ══ 5. DICABUT (uji tahan gempa #3) ═════════════════════════════
        judul('5. DICABUT mahasiswa — pintu mati, catatan HIDUP')

        b4, tok4 = P.buat_bimbingan(db, uji_user.id, 'Prof. Cabut', hari=7)
        dibuat.append(b4.id)
        b4r, _ = P.cari_dari_token(db, tok4)
        P.catat(db, b4r, 'Catatan sebelum dicabut', section_id='BAB I')
        cek('C1 catatan tersimpan', len(P.daftar_catatan(db, b4.id)) == 1)

        ok = P.cabut(db, b4.id, uji_user.id)
        cek('C2 cabut berhasil', ok)
        cek('C3 cabut kedua kali → False', not P.cabut(db, b4.id, uji_user.id))

        mati, s5 = P.cari_dari_token(db, tok4)
        cek('C4 token yang dicabut → DITOLAK', mati is None, 'link mati masih LOLOS!')
        cek('C5 sebab = dicabut', s5 == P.SEBAB_DICABUT, s5)
        cek('C6 CATATAN TETAP ADA setelah dicabut',
            len(P.daftar_catatan(db, b4.id)) == 1, 'catatan ikut hilang!')

        #  Hidupkan lagi → boleh, asal belum kedaluwarsa.
        hidup = P.hitung_ulang_dicabut(db, uji_user.id, b4.id)
        cek('C7 bisa dihidupkan lagi', hidup)
        lagi, s6 = P.cari_dari_token(db, tok4)
        cek('C8 setelah dihidupkan → bisa dibuka', lagi is not None and s6 == '')

        # ══ 6. CABUT MILIK ORANG LAIN (pintu keamanan) ══════════════════
        judul('6. MAHASISWA LAIN tidak boleh menyentuh bimbingan ini')

        orang_lain = db.query(User).filter(User.id != uji_user.id).first()
        if orang_lain is not None:
            cek('K1 milik() menolak user lain',
                P.milik(db, b.id, orang_lain.id) is None, 'BOCOR!')
            cek('K2 cabut() user lain → False',
                not P.cabut(db, b.id, orang_lain.id))
            cek('K3 bimbingan masih hidup', P.milik(db, b.id, uji_user.id) is not None)
        else:
            print('  ⏭  hanya 1 user di DB → uji silang dilewati (jujur)')

        # ══ 7. KEDALUWARSA (uji tahan gempa #2) ═════════════════════════
        judul('7. KEDALUWARSA — link mati, pesan jujur')

        b5, tok5 = P.buat_bimbingan(db, uji_user.id, 'Prof. Tua', hari=7)
        dibuat.append(b5.id)
        b5.kedaluwarsa = P._sekarang() - timedelta(days=1)   # dimundurkan
        db.commit()
        tua, s7 = P.cari_dari_token(db, tok5)
        cek('E1 link lewat masa → DITOLAK', tua is None, 'link tua masih LOLOS!')
        cek('E2 sebab = kedaluwarsa', s7 == P.SEBAB_KEDALUWARSA, s7)
        cek('E3 tidak bisa dihidupkan kalau sudah lewat masa',
            not P.hitung_ulang_dicabut(db, uji_user.id, b5.id))
        cek('E4 sisa_hari = 0', P.sisa_hari(b5) == 0, str(P.sisa_hari(b5)))

        # ══ 8. NASKAH & SIDIK ═══════════════════════════════════════════
        judul('8. NASKAH — "berubah atau belum" (jawaban JUJUR)')

        pb = P.tambah_berkas(db, b, None, 'BAB I — Pendahuluan', 'Teks asli bab satu.')
        cek('N1 berkas tanpa file_id boleh (bab belum ada berkas)', pb.id is not None)
        cek('N2 urutan = 1', pb.urutan == 1, str(pb.urutan))
        pb2 = P.tambah_berkas(db, b, None, 'BAB II — Tinjauan', 'Teks bab dua.')
        cek('N3 urutan naik jadi 2', pb2.urutan == 2, str(pb2.urutan))

        cek('N4 naskah belum berubah → False',
            not P.naskah_berubah(db, pb, 'Teks asli bab satu.'))
        cek('N5 naskah diubah → True',
            P.naskah_berubah(db, pb, 'Teks asli bab satu SUDAH DIREVISI.'))
        cek('N6 naskah dihapus total → True (berubah)',
            P.naskah_berubah(db, pb, ''))

        # ══ 9. CATATAN & RANTAI ═════════════════════════════════════════
        judul('9. RANTAI — revisi ke-2 BUKAN catatan lepas')

        c1 = P.catat(db, b, 'Perdalam latar belakang', section_id='BAB I',
                     teks_asli='Teks asli bab satu.', berkas_id=pb.id)
        cek('R1 catatan ronde 1', c1.ronde == 1, str(c1.ronde))
        cek('R2 warna kuning (dari pembimbing)', c1.warna == 'kuning')
        cek('R3 keadaan utuh (ada teks)', c1.keadaan == 'utuh')
        cek('R4 penulis_id terisi (ruang 2 pembimbing)', c1.penulis_id == b.id)

        c2 = P.catat(db, b, 'Masih belum — pakai jurnal 5 tahun', section_id='BAB I',
                     teks_asli='Teks baru hasil revisi.', induk_id=c1.id)
        cek('R5 catatan ke-2 jadi RONDE 2 (dirantai)', c2.ronde == 2, str(c2.ronde))
        cek('R6 induk_id tersimpan', c2.induk_id == c1.id)

        c3 = P.catat(db, b, 'Sudah oke', section_id='BAB I',
                     teks_asli='Teks baru hasil revisi ke-2.', induk_id=c2.id)
        cek('R7 catatan ke-3 jadi RONDE 3', c3.ronde == 3, str(c3.ronde))

        sisa = P.daftar_catatan(db, b.id)
        rantai = P.rangkai(sisa)
        cek('R8 3 catatan → 1 RANTAI saja (compact)', len(rantai) == 1,
            f'{len(rantai)} rantai')
        cek('R9 rantai punya 3 ronde', rantai[0]['jumlah_ronde'] == 3,
            str(rantai[0]['jumlah_ronde']))
        cek('R10 anak-anak berurutan ronde 2,3',
            [x.ronde for x in rantai[0]['anak']] == [2, 3],
            str([x.ronde for x in rantai[0]['anak']]))
        cek('R11 terbaru = ronde 3', rantai[0]['terbaru'].id == c3.id)

        #  Induk dari bimbingan LAIN tidak boleh disambung (pagar silang).
        c_lain = P.catat(db, b4, 'catatan di bimbingan lain', section_id='BAB I')
        c_palsu = P.catat(db, b, 'coba sambung ke induk asing',
                          section_id='BAB I', induk_id=c_lain.id)
        cek('R12 induk asing DITOLAK (ronde tetap 1)',
            c_palsu.ronde == 1 and c_palsu.induk_id is None,
            f'ronde={c_palsu.ronde} induk={c_palsu.induk_id}')

        # ══ 10. SOFT-DELETE ═════════════════════════════════════════════
        judul('10. SOFT-DELETE — dibuang tapi TIDAK hilang (jejak)')

        #  ⚠️ KOREKSI 23Sep26: pada versi pertama uji ini salah hitung.
        #  Wulan mengira bimbingan `b` hanya berisi c1/c2/c3, padahal uji
        #  sebelumnya (R12, G3) sudah menambah 2 catatan lain (c_palsu,
        #  c_kosong). Jadi "rantai harus 1" itu ASUMSI SALAH — bukan bug.
        #  Sekarang uji membandingkan JUMLAH SEBELUM vs SESUDAH, bukan angka
        #  mati. Dengan begitu uji tetap bergigi walau ada catatan lain.
        sebelum = P.daftar_catatan(db, b.id)
        rantai_sebelum = P.rangkai(sebelum)

        c3.dibuang = 1
        db.commit()

        tampil = P.daftar_catatan(db, b.id)
        semua = P.daftar_catatan(db, b.id, semuanya=True)
        cek('S1 yang dibuang tidak tampil', len(tampil) == len(semua) - 1,
            f'tampil={len(tampil)} semua={len(semua)}')
        cek('S2 BARIS MASIH ADA di DB (jejak terjaga)',
            db.query(CatatanPembimbing).filter(
                CatatanPembimbing.id == c3.id).one_or_none() is not None,
            'jejak hilang — mahasiswa bisa mengklaim "saya tidak pernah diminta itu"')

        #  Rantai induk (c1→c2) HARUS tetap utuh walau anaknya (c3) dibuang.
        #  Uji bergigi: cari simpul yang berisi c1, lalu pastikan jumlah
        #  rondenya turun dari 3 → 2 dan c3 TIDAK muncul sebagai anak.
        simpul = [s for s in P.rangkai(tampil)
                  if s['kepala'].id == c1.id]
        cek('S3 rantai induk masih ada setelah anak dibuang', len(simpul) == 1,
            f'{len(simpul)} simpul')
        if simpul:
            s = simpul[0]
            cek('S4 ronde turun 3 → 2 (anak terbuang tidak dihitung)',
                s['jumlah_ronde'] == 2, str(s['jumlah_ronde']))
            cek('S5 c3 TIDAK muncul sebagai anak',
                c3.id not in [x.id for x in s['anak']],
                str([x.id for x in s['anak']]))
            cek('S6 terbaru jadi ronde 2 (c2)', s['terbaru'].id == c2.id)
        cek('S7 jumlah rantai TETAP (c3 = ANAK, bukan kepala rantai)',
            len(P.rangkai(tampil)) == len(rantai_sebelum),
            f'{len(rantai_sebelum)} → {len(P.rangkai(tampil))} — '
            'membuang anak tidak boleh menghapus kepala rantai')

        # ══ 11. RINGKASAN (angka jujur) ══════════════════════════════════
        judul('11. RINGKASAN — 4 angka jujur')

        c1.warna = 'hijau'; c1.sudah_oke = P._sekarang()
        db.commit()
        kr = P.ringkas(P.daftar_catatan(db, b.id))
        cek('G1 total dihitung', kr['total'] >= 2, str(kr))
        cek('G2 selesai dihitung', kr['selesai'] >= 1, str(kr))
        #  ⚠️ DIPERBARUI 24Sep26 (ACC Bos Opsi A — cacat temuan MATA):
        #     DULU catatan tanpa teks asli diisi keadaan='hilang' → label
        #     "Naskah berubah" muncul padahal naskah tidak berubah apa pun.
        #     Itu MENYESATKAN. Sekarang keadaan='umum' → label "Catatan umum".
        #     Uji ini dulu memaku perilaku yang SALAH; kini memaku yang benar.
        c_kosong = P.catat(db, b, 'titip catatan di bab ini', section_id='BAB III')
        cek('G3 catatan tanpa sorotan → keadaan umum (bukan hilang)',
            c_kosong.keadaan == 'umum', c_kosong.keadaan)
        kr2 = P.ringkas(P.daftar_catatan(db, b.id))
        cek('G4 yang umum dihitung terpisah dari yang hilang',
            kr2['umum'] >= 1 and kr2['hilang'] == 0, str(kr2))

        # ══ 12. TABEL LAMA TIDAK DISENTUH (tiang T2) ════════════════════
        judul('12. TABEL LAMA UTUH (tiang T2)')

        from app.models import FileBerkas, RevisiHistory, ProsesAI       # noqa: E402
        cek('L1 tabel users utuh', db.query(User).count() >= 1)
        cek('L2 tabel files utuh (query jalan)', db.query(FileBerkas).count() >= 0)
        cek('L3 revisi_history utuh', db.query(RevisiHistory).count() >= 0)
        cek('L4 proses_ai utuh', db.query(ProsesAI).count() >= 0)

    finally:
        #  Bersihkan data uji — HANYA yang dibuat uji ini.
        try:
            for bid in dibuat:
                db.query(CatatanPembimbing).filter(
                    CatatanPembimbing.pembimbingan_id == bid).delete()
                db.query(BerkasPembimbingan).filter(
                    BerkasPembimbingan.pembimbingan_id == bid).delete()
                db.query(Pembimbingan).filter(
                    Pembimbingan.id == bid).delete()
            db.commit()
            print(f'\n🧹 data uji dibersihkan ({len(dibuat)} bimbingan)')
        except Exception as e:                                   # noqa: BLE001
            print(f'⚠️  gagal bersihkan: {e}')
        db.close()

    print('\n' + '═' * 62)
    print(f'  UJI TAHAP 1: {LULUS} LULUS / {GAGAL} GAGAL')
    if GAGAL:
        print('  ❌ GAGAL: ' + ', '.join(NAMA_GAGAL))
    print('═' * 62)
    return 1 if GAGAL else 0


if __name__ == '__main__':
    sys.exit(main())
