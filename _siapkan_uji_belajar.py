"""POTRET /belajar DI DB SALINAN — user uji berpaket PENERBIT.

⚠️ JANGAN ubah DB produksi. Skrip ini:
  1. menyalin /app/data/eduai.db → /tmp/eduai_uji.db
  2. menambah user uji berpaket penerbit + 1 naskah uji
  3. menjalankan server sementara :8002 memakai DB SALINAN
  4. mencetak URL untuk dipotret

Dipakai Wulan untuk MEMBUKTIKAN tampilan, bukan untuk produksi.
"""
import os
import shutil
import sqlite3
import sys

sys.path.insert(0, '/app')

ASAL = '/app/data/eduai.db'
SALIN = '/tmp/eduai_uji.db'


def main():
    if not os.path.exists(ASAL):
        print('❌ DB asal tidak ada:', ASAL)
        return 1
    shutil.copy2(ASAL, SALIN)
    print(f'✅ salinan DB: {SALIN} ({os.path.getsize(SALIN)} byte)')

    c = sqlite3.connect(SALIN)
    kol = [r[1] for r in c.execute('PRAGMA table_info(users)')]
    print('   kolom users:', kol)

    #  ── user uji berpaket penerbit ─────────────────────────────────────
    ada = c.execute("select id from users where email='uji-belajar@eduai.test'").fetchone()
    if ada:
        uid = ada[0]
        print(f'   user uji SUDAH ada id={uid}')
    else:
        #  nama kolom ASLI dibaca dari PRAGMA di atas; kuota_mb NOT NULL wajib diisi
        #  🚨 04Okt26: sandi WAJIB pakai fungsi PRODUKSI (PBKDF2) — Wulan
        #     sempat pakai sha256 → login selalu 401 (bug uji, bukan bug app).
        import sys as _s
        _s.path.insert(0, '/app')
        from app.auth import hash_password as _hp
        sandi = _hp('UjiBelajar123')
        c.execute("""insert into users (nama,email,paket,password_hash,aktif,dibuat,
                                        kuota_mb,role,folder_ekstra)
                     values (?,?,?,?,1,datetime('now'),1024,'client',0)""",
                  ('Siti N. (Uji Belajar)', 'uji-belajar@eduai.test',
                   'penerbit', sandi))
        uid = c.execute("select last_insert_rowid()").fetchone()[0]
        print(f'   ✅ user uji dibuat id={uid} paket=penerbit sandi=UjiBelajar123')

    #  ── naskah uji: pakai naskah terbaik yang ada (S1 unmul 5 bab) ────
    n = c.execute("""select id,nama,nama_simpan,user_id from files
                     where terhapus_pada is null
                     order by ukuran desc limit 1""").fetchone()
    if n:
        fid, nama, simpan, uid_lama = n
        c.execute('update files set user_id=? where id=?', (uid, fid))
        print(f'   ✅ naskah {fid} "{nama}" dipindah ke user uji (dari user {uid_lama})')
        #  ⚠️ WAJIB pindahkan berkas FISIKNYA juga — jalur berkas = /
        #     uploads/<user_id>/<nama_simpan>. Kalau tidak, halaman tidak bisa
        #     membaca naskah (BUG NYATA yang ditemukan dari potret 03Okt26).
        import glob
        for akar in ('/app/uploads', '/tmp/data_uji/uploads'):
            asal = os.path.join(akar, str(uid_lama), simpan)
            tuju_dir = os.path.join(akar, str(uid))
            tuju = os.path.join(tuju_dir, simpan)
            if os.path.exists(asal):
                os.makedirs(tuju_dir, exist_ok=True)
                shutil.copy2(asal, tuju)
                print(f'   ✅ berkas fisik disalin: {asal} → {tuju}')
            else:
                print(f'   ⚠️  berkas fisik tidak ada di {akar}')

    c.commit()
    c.close()
    print(f'\n👉 Jalankan server salinan:')
    print(f'   EDUAI_DB={SALIN} uvicorn app.main:app --port 8002')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
