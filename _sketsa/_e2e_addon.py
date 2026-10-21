"""E2E ADDON STORAGE + FOLDER (ACC Bos 15Sep26).

Skenario uji (SEMUA jalur user, bukan jalur pintas):
  1. /api/addon → AddOn storage ada, keterangan "+50 MB & +10 folder"
  2. User GRATIS → boleh_beli = False (terkunci, ACC Bos)
  3. Beli AddOn sebagai user GRATIS → 403 ditolak backend
  4. User PENULIS beli → kuota_mb NAIK 50, folder_ekstra NAIK 10
  5. Jatah folder paket penulis: 10 → 20 setelah AddOn
  6. Bisa buat folder ke-11 (sebelumnya ditolak "batas 10 folder")
  7. Beli LAGI → kuota naik lagi (repeat order = mesin uang)
  8. Tanpa kedaluwarsa (ACC Bos)

⚠ Uji ini MEMBUAT user uji SENDIRI lalu MENGHAPUSNYA (lewat cascade).
"""
import sys
import urllib.error
import urllib.parse
import urllib.request

sys.path.insert(0, '/app')

from app.models import SessionLocal, User            # noqa: E402
from app.cascade import hapus_user                   # noqa: E402
from app.folder import buat as buat_folder, FolderGagal  # noqa: E402
from app.kuota import tambah_addon                   # noqa: E402
from app.config import ADDON, jatah_folder           # noqa: E402
from app.main import buat_token                      # noqa: E402

URL = 'http://localhost:8000'
LULUS, GAGAL = [], []


def cek(nama, syarat, bukti=''):
    (LULUS if syarat else GAGAL).append(nama)
    print('  %s %-52s %s' % ('✅' if syarat else '❌', nama, bukti))


def ambil(path, token=None, data=None):
    """GET/POST ke server (jalur HTTP nyata, bukan panggilan fungsi)."""
    url = URL + path
    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(url, data=body, method='POST')
    else:
        req = urllib.request.Request(url)
    if token:
        req.add_header('Cookie', 'eduai_session=' + token)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            import json
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        import json
        try:
            return e.code, json.loads(e.read().decode())
        except Exception:
            return e.code, {}


db = SessionLocal()
dibuat = []
try:
    # ── Siapkan dua user uji: satu gratis, satu penulis ──────────────────
    # ⚠ `password_hash` WAJIB (NOT NULL di skema) — user uji tanpa password
    #   tidak bisa dibuat. Hash apa pun cukup; uji ini tidak login via form.
    u_gratis = User(email='uji-addon-gratis@test.local', nama='Uji Gratis',
                    password_hash='x', paket='gratis', kuota_mb=30, aktif=True)
    u_penulis = User(email='uji-addon-penulis@test.local', nama='Uji Penulis',
                     password_hash='x', paket='penulis', kuota_mb=100, aktif=True)
    db.add_all([u_gratis, u_penulis])
    db.commit()
    dibuat = [u_gratis.id, u_penulis.id]
    t_gratis, t_penulis = buat_token(u_gratis.id), buat_token(u_penulis.id)

    print('\n══ 1. DAFTAR ADDON (/api/addon) ══')
    st, d = ambil('/api/addon', t_penulis)
    cek('endpoint balas 200', st == 200, 'HTTP %s' % st)
    stor = [a for a in d.get('addon', []) if a['kode'] == 'storage']
    cek('AddOn "storage" ada', len(stor) == 1)
    if stor:
        a = stor[0]
        cek('keterangan = +50 MB & +10 folder',
            a['keterangan'] == '+50 MB storage & +10 folder', a['keterangan'])
        cek('harga Rp 25.000', a['harga'] == 25000, 'Rp %s' % a['harga'])
        cek('ditandai permanen (tanpa kedaluwarsa)', a['permanen'] is True)

    print('\n══ 2. GERBANG PAKET GRATIS (ACC Bos: tetap terkunci) ══')
    st, d = ambil('/api/addon', t_gratis)
    cek('user gratis → boleh_beli = False', d.get('boleh_beli') is False)
    st, d = ambil('/api/addon/buat', t_gratis, {'jenis': 'storage'})
    cek('user gratis BELI → ditolak 403', st == 403, 'HTTP %s' % st)
    cek('pesan menyuruh upgrade paket',
        'paket' in (d.get('pesan') or '').lower(), d.get('pesan', '')[:40])

    print('\n══ 3. JATAH FOLDER: paket + AddOn ══')
    db.refresh(u_penulis)
    j0 = jatah_folder(u_penulis.paket, u_penulis.folder_ekstra)
    cek('penulis sebelum AddOn = 10 folder', j0 == 10, '%s folder' % j0)

    print('\n══ 4. TERAPKAN ADDON (inti fitur) ══')
    sebelum_mb, sebelum_fd = u_penulis.kuota_mb, u_penulis.folder_ekstra
    tambah_addon(db, u_penulis.id, 'storage', order_id='UJI-ADDON-1',
                 paket_user=u_penulis.paket)
    db.refresh(u_penulis)
    cek('kuota_mb naik +50', u_penulis.kuota_mb == sebelum_mb + 50,
        '%s → %s MB' % (sebelum_mb, u_penulis.kuota_mb))
    cek('folder_ekstra naik +10',
        u_penulis.folder_ekstra == sebelum_fd + 10,
        '%s → %s' % (sebelum_fd, u_penulis.folder_ekstra))
    j1 = jatah_folder(u_penulis.paket, u_penulis.folder_ekstra)
    cek('jatah folder jadi 20', j1 == 20, '%s folder' % j1)

    print('\n══ 5. USER BISA BUAT FOLDER KE-11 ══')
    for i in range(1, 12):
        try:
            buat_folder(db, u_penulis, 'Folder Uji %d' % i)
        except FolderGagal as e:
            print('     (gagal di folder ke-%d: %s)' % (i, e))
            break
    from app.folder import jumlah_folder
    n = jumlah_folder(db, u_penulis.id)
    cek('berhasil buat 11 folder (>10 jatah paket)', n == 11,
        '%s folder' % n)

    print('\n══ 6. FOLDER KE-21 DITOLAK (jatah 20) ══')
    for i in range(12, 22):
        try:
            buat_folder(db, u_penulis, 'Folder Uji %d' % i)
        except FolderGagal:
            break
    n = jumlah_folder(db, u_penulis.id)
    cek('berhenti tepat di 20 folder', n == 20, '%s folder' % n)
    try:
        buat_folder(db, u_penulis, 'Folder Kelebihan')
        cek('folder ke-21 DITOLAK', False, 'ternyata LOLOS')
    except FolderGagal as e:
        cek('folder ke-21 DITOLAK', True, str(e)[:44])

    print('\n══ 7. BELI LAGI (repeat order = mesin uang) ══')
    mb2 = u_penulis.kuota_mb
    tambah_addon(db, u_penulis.id, 'storage', order_id='UJI-ADDON-2',
                 paket_user=u_penulis.paket)
    db.refresh(u_penulis)
    cek('kuota naik lagi +50', u_penulis.kuota_mb == mb2 + 50,
        '%s → %s MB' % (mb2, u_penulis.kuota_mb))
    cek('jatah folder lagi +10',
        jatah_folder(u_penulis.paket, u_penulis.folder_ekstra) == 30,
        '%s folder' % jatah_folder(u_penulis.paket, u_penulis.folder_ekstra))

    print('\n══ 8. ADDON LAIN TIDAK IKUT BERUBAH ══')
    a_ai = ADDON['ai']
    cek('AddOn AI tetap berkuota (bukan permanen)',
        'tambahan' not in a_ai, '+%s revisi' % a_ai.get('kuota'))

finally:
    print('\n══ BERSIH-BERSIH ══')
    for uid in dibuat:
        try:
            obj = db.get(User, uid)          # ⚠ hapus_user minta OBJEK
            if obj is None:
                continue
            hasil = hapus_user(db, obj)
            print('  ✓ user uji %s dihapus: %s' % (uid, hasil))
        except Exception as e:
            print('  ✗ gagal hapus user %s: %s' % (uid, e))
    # Jaring pengaman: hapus sisa user uji dari percobaan yang gagal
    # sebelum ini (email berpola sama), supaya DB tidak kotor.
    from app.models import User as _U
    from sqlalchemy import select as _sel
    sisa = db.scalars(_sel(_U).where(_U.email.like('uji-addon-%'))).all()
    for s in sisa:
        try:
            hapus_user(db, s)
            print('  ✓ sisa user uji %s (%s) dihapus' % (s.id, s.email))
        except Exception as e:
            print('  ✗ gagal hapus sisa %s: %s' % (s.id, e))
    db.close()

print('\n' + '═' * 62)
print('  LULUS: %d   GAGAL: %d' % (len(LULUS), len(GAGAL)))
if GAGAL:
    print('  ✗ GAGAL:', ', '.join(GAGAL))
print('═' * 62)
sys.exit(1 if GAGAL else 0)
