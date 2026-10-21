"""SIAPKAN DATA UJI Mode Belajar — URUTAN BENAR (04Okt26).

🚨 JEBAKAN YANG SUDAH DIMAKAN (jangan ulangi):
   `_siapkan_uji_belajar.py` menyalin DB PRODUKSI → salinan. Kalau dipanggil
   SETELAH kita menambah user uji, user uji HILANG (tertimpa salinan baru) →
   login 401 dan Wulan menuduh "bug app" padahal bug urutan uji.

URUTAN WAJIB:
   1. salin DB produksi  → /tmp/data_uji/eduai.db      (fresh)
   2. TAMBAH user uji (sandi PBKDF2 via app.auth.hash_password)
   3. sinyal naskah uji ke user uji + salin BERKAS FISIKNYA
   4. aktifkan Mode Belajar untuk naskah itu

Jalankan DI DALAM container:
   EDUAI_DATA_DIR=/tmp/data_uji EDUAI_UPLOAD_DIR=/tmp/data_uji/uploads \
     python3 /app/app/_siapkan_data_uji.py
"""
import os
import shutil
import sqlite3
import sys

sys.path.insert(0, '/app')

SRC = '/app/data/eduai.db'
DST_DIR = os.environ.get('EDUAI_DATA_DIR', '/tmp/data_uji')
DST = os.path.join(DST_DIR, 'eduai.db')
UPL = os.environ.get('EDUAI_UPLOAD_DIR', os.path.join(DST_DIR, 'uploads'))
EMAIL = 'uji-belajar@eduai.test'
SANDI = 'UjiBelajar123'


def main():
    from app.auth import hash_password

    os.makedirs(DST_DIR, exist_ok=True)
    os.makedirs(UPL, exist_ok=True)

    #  ── 1. salin DB produksi (selalu fresh) ────────────────────────────
    shutil.copy(SRC, DST)
    print(f'  1. salinan DB: {DST} ({os.path.getsize(DST)} byte)')

    c = sqlite3.connect(DST)
    c.row_factory = None

    #  ── 2. user uji (PBKDF2 — fungsi PRODUKSI) ─────────────────────────
    kolom = [r[1] for r in c.execute('PRAGMA table_info(users)')]
    ada = c.execute('select id from users where email=?', (EMAIL,)).fetchone()
    hash_sandi = hash_password(SANDI)
    if ada:
        uid = ada[0]
        c.execute('update users set password_hash=?, paket=?, aktif=1 where id=?',
                  (hash_sandi, 'penerbit', uid))
        print(f'  2. user uji DIPERBARUI id={uid} (sandi PBKDF2, paket penerbit)')
    else:
        isian = {'nama': 'Siti N. (Uji Belajar)', 'email': EMAIL,
                 'paket': 'penerbit', 'password_hash': hash_sandi,
                 'aktif': 1, 'kuota_mb': 1024, 'role': 'client',
                 'folder_ekstra': 0,
                 'dibuat': __import__('datetime').datetime.utcnow()
                 .strftime('%Y-%m-%d %H:%M:%S')}
        isian = {k: v for k, v in isian.items() if k in kolom}
        kol = ', '.join(isian)
        tanya = ', '.join('?' for _ in isian)
        cur = c.execute(f'insert into users ({kol}) values ({tanya})',
                        tuple(isian.values()))
        uid = cur.lastrowid
        print(f'  2. user uji DIBUAT id={uid} (sandi PBKDF2, paket penerbit)')

    #  ── 3. naskah uji: pilih yang BERKAS FISIKNYA ADA + babnya terbanyak ──
    #     ⚠️ 04Okt26: Wulan sempat hanya lihat section_state → pilih naskah
    #     yang berkasnya TIDAK ADA di container ⇒ teks_bab() balas '' dan
    #     uji jadi menuduh "mesin rusak". SEKARANG berkasnya diperiksa dulu.
    kandidat = c.execute("""select id, nama, nama_simpan, user_id from files
                            where terhapus_pada is null and nama_simpan is not null
                            order by id""").fetchall()

    def _berkas_ada(k):
        """Cari berkas fisik: di folder user DB, atau folder lain yang sama."""
        _fid, _nama, _simpan, _uid = k
        for uid_coba in (_uid, 3, 6, 7, 8, 1):
            j = f'/app/uploads/{uid_coba}/{_simpan}'
            if os.path.exists(j):
                return j, _uid, uid_coba
        return None, _uid, None

    def _bobot(k):
        jalur, _u, _u2 = _berkas_ada(k)
        if not jalur:
            return -1                      # berkas tidak ada → JANGAN dipilih
        jml = c.execute("""select count(distinct kategori) from section_state
                           where file_id=? and kategori like 'bab%'""",
                        (k[0],)).fetchone()[0]
        return (1, jml, os.path.getsize(jalur))

    f = None
    terbaik = (-1, -1, -1)
    for k in kandidat:
        b = _bobot(k)
        if b[0] == -1:
            continue
        if b > terbaik:
            terbaik, f = b, k
    if not f:
        print('  ⚠️ tidak ada naskah yang berkas fisiknya ada')
        c.close()
        return 1
    fid, nama, simpan, uid_lama = f
    _jalur, _u, uid_punya = _berkas_ada(f)
    print(f'  3. naskah {fid} "{nama}" ({terbaik[1]} bab, '
          f'{terbaik[2] // 1024} KB) → user uji {uid}')
    c.execute('update files set user_id=? where id=?', (uid, fid))

    src_berkas = _jalur
    dst_berkas = os.path.join(UPL, str(uid), simpan)
    os.makedirs(os.path.dirname(dst_berkas), exist_ok=True)
    if os.path.exists(src_berkas):
        shutil.copy(src_berkas, dst_berkas)
        print(f'     berkas fisik disalin: {src_berkas} → {dst_berkas}')
    else:
        print(f'     ⚠️ berkas fisik TIDAK ADA: {src_berkas}')

    #  ── 4. PINDAHKAN catatan revisi (section_state) ke user uji ─────────
    #     ⚠️ 04Okt26: kalau tidak dipindah, `bab_sudah_direvisi()` KOSONG →
    #     rute /belajar/insight/{fid} menolak (dialihkan balik ke /belajar).
    #     Ini penting: SYARAT TERBUKA = bab SUDAH DIREVISI (bukan ada bab).
    pindah = c.execute('update section_state set user_id=? where file_id=?',
                       (uid, fid)).rowcount
    print(f'  4. section_state dipindah ke user {uid}: {pindah} baris')

    #  ── 5. aktifkan Mode Belajar (pakai fungsi PRODUKSI) ───────────────
    catat_bab = c.execute("""select distinct kategori from section_state
                             where file_id=? and user_id=?
                               and kategori like 'bab%'""",
                          (fid, uid)).fetchall()
    #  bersihkan baris lama (UNIQUE file_id → jangan dobel)
    c.execute('delete from belajar_naskah where file_id=?', (fid,))
    c.execute("""insert into belajar_naskah
                   (file_id, user_id, status, insight_json, soal_json,
                    bab_selesai, dibuat, diubah)
                 values (?,?,?,?,?,?, datetime('now'), datetime('now'))""",
              (fid, uid, 'aktif', '{}', '{}', '{}'))
    c.commit()
    c.close()
    print(f'     belajar_naskah: 1 baris status=aktif (bab direvisi: '
          f'{[x[0] for x in catat_bab]})')

    print()
    print('👉 Jalankan server uji:')
    print(f'   EDUAI_DATA_DIR={DST_DIR} EDUAI_UPLOAD_DIR={UPL} '
          f'uvicorn app.main:app --port 8002')
    return 0


if __name__ == '__main__':
    sys.exit(main())
