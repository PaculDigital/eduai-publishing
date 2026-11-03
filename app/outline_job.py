"""Pekerjaan kerangka server-side (Gate 1) — tahan back, navigasi, tutup tab.

Dulu generasi kerangka jalan di dalam request POST, jadi back atau
navigasi = hasil hilang. Sekarang POST hanya membuat pekerjaan + utas,
lalu redirect ke halaman menunggu GET. Pekerjaan jalan di server sampai
selesai, walau user back, pindah halaman, atau tutup tab; kembali ke
alamat pekerjaan menampilkan status yang sama.

Kenapa berkas, bukan tabel baru? Gate 1 sudah memakai berkas pending di
pohon yang sama (referensi_pesanan), jadi tidak perlu migrasi DB. Satu
pekerjaan = satu JSON di folder outline_job di bawah BUKU_DIR (default
/opt/data/buku_hasil, volume persisten, jadi pekerjaan selamat dari
restart container; utasnya tidak lanjut otomatis, tapi timeout malas di
bawah menandai pekerjaan jalan yang menggantung menjadi gagal saat
berikutnya dibaca).

Status: 'jalan' | 'selesai' | 'gagal'. TIDAK ADA status batal manual:
pembatalan dari frontend dilarang (putusan Bos 3 Nov 2026). Pekerjaan
hanya berakhir lewat selesai, gagal server, atau timeout 10 menit.
"""

import json
import os
import secrets
import threading
import time

_DIR = None
_KUNCI = threading.Lock()
BATAS_MENIT = 10
UMUR_PRUNE_HARI = 7
_HEX = set('0123456789abcdef')


def _dir_job():
    """Folder berkas pekerjaan kerangka (satu pohon dengan pending)."""
    global _DIR
    if _DIR is None:
        dasar = os.environ.get('BUKU_DIR', '/opt/data/buku_hasil')
        _DIR = os.path.join(dasar, 'outline_job')
        os.makedirs(_DIR, exist_ok=True)
    return _DIR


def _jalan_file(token):
    return os.path.join(_dir_job(), 'job_' + token + '.json')


def _tulis_atom(path, data):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def buat_job(user_id, judul, tier, tier_form, bidang, penulis, penelaah,
             jumlah_bab):
    """Buat pekerjaan jalan baru + kembalikan record-nya."""
    token = secrets.token_hex(16)
    kini = time.time()
    rec = {
        'token': token, 'user_id': user_id, 'judul': judul, 'tier': tier,
        'tier_form': tier_form, 'bidang': bidang, 'penulis': penulis,
        'penelaah': penelaah, 'jumlah_bab': jumlah_bab, 'status': 'jalan',
        'galat': '', 'pending_token': '', 'outline': None,
        'dibuat': kini, 'diubah': kini,
    }
    with _KUNCI:
        _tulis_atom(_jalan_file(token), rec)
    prune_lama(user_id)
    return rec


def muat_job(token):
    """Muat pekerjaan apa adanya (None bila tidak ada, rusak, atau token
    bukan hex — token hex mencegah traversal path dari query)."""
    token = (token or '').strip()
    if not token or any(c not in _HEX for c in token):
        return None
    try:
        with open(_jalan_file(token), encoding='utf-8') as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _simpan(rec):
    rec['diubah'] = time.time()
    with _KUNCI:
        _tulis_atom(_jalan_file(rec['token']), rec)


def _baca_dir():
    try:
        return os.listdir(_dir_job())
    except OSError:
        return []


def cari_jalan(user_id, judul, tier):
    """Pekerjaan jalan milik user dengan judul+tier sama (baru dulu).

    Judul dibandingkan sesudah strip + casefold, tier sesudah normalisasi
    (keduanya dilakukan pemanggil). Hanya status jalan yang dihitung:
    selesai/gagal tidak menghalangi submit baru.
    """
    kunci_judul = (judul or '').strip().casefold()
    hasil = []
    for n in _baca_dir():
        if not (n.startswith('job_') and n.endswith('.json')):
            continue
        try:
            with open(os.path.join(_dir_job(), n), encoding='utf-8') as f:
                rec = json.load(f)
        except (OSError, ValueError):
            continue
        if (rec.get('user_id') == user_id and rec.get('status') == 'jalan'
                and (rec.get('judul') or '').strip().casefold() == kunci_judul
                and rec.get('tier') == tier):
            hasil.append(rec)
    if not hasil:
        return None
    hasil.sort(key=lambda r: r.get('dibuat', 0), reverse=True)
    return hasil[0]


def tandai_selesai(token, outline_json, pending_token):
    """Jalan -> selesai + simpan hasil. False bila status sudah berubah
    (misal timeout menandai gagal duluan): hasil harus dibuang pemanggil."""
    rec = muat_job(token)
    if rec is None or rec.get('status') != 'jalan':
        return False
    rec['status'] = 'selesai'
    rec['outline'] = outline_json
    rec['pending_token'] = pending_token
    _simpan(rec)
    return True


def tandai_gagal(token, galat):
    """Jalan -> gagal + pesan. False bila status sudah berubah."""
    rec = muat_job(token)
    if rec is None or rec.get('status') != 'jalan':
        return False
    rec['status'] = 'gagal'
    rec['galat'] = galat
    _simpan(rec)
    return True


def terapkan_timeout(rec, batas_menit=BATAS_MENIT):
    """Jalan yang lebih tua dari batas -> gagal (timeout malas).

    Dipanggil tiap baca status, jadi pekerjaan menggantung (restart
    container, provider menggantung) tidak pernah tampil jalan selamanya.
    """
    if rec is None or rec.get('status') != 'jalan':
        return False
    umur = time.time() - float(rec.get('dibuat', 0) or 0)
    if umur <= batas_menit * 60:
        return False
    return tandai_gagal(rec['token'], 'Waktu penyusunan habis, coba lagi')


def prune_lama(user_id, hari=UMUR_PRUNE_HARI):
    """Hapus pekerjaan selesai/gagal milik user yang lebih tua dari hari.

    Aman untuk persetujuan: tombol Setuju memakai token pending (berkas
    terpisah), bukan berkas job, jadi prune tidak merusak pesanan yang
    sedang disetujui.
    """
    batas = time.time() - hari * 86400
    for n in _baca_dir():
        if not (n.startswith('job_') and n.endswith('.json')):
            continue
        path = os.path.join(_dir_job(), n)
        try:
            with open(path, encoding='utf-8') as f:
                rec = json.load(f)
        except (OSError, ValueError):
            continue
        if (rec.get('user_id') == user_id
                and rec.get('status') in ('selesai', 'gagal')
                and float(rec.get('diubah', 0) or 0) < batas):
            try:
                os.remove(path)
            except OSError:
                pass


def jalankan_job(token):
    """Utas pekerja: susun outline -> periksa -> pending -> selesai/gagal.

    Langkahnya PERSIS handler lama (susun_outline dengan tier form mentah,
    periksa bentuk, simpan pending dengan tier normalisasi). Impor malas
    supaya modul ini bisa diuji tanpa menarik seluruh pipeline.
    """
    rec = muat_job(token)
    if rec is None or rec.get('status') != 'jalan':
        return
    judul, tier_form = rec['judul'], rec.get('tier_form', '')
    tier_nama, jml = rec['tier'], rec['jumlah_bab']
    try:
        from . import referensi_outline as _RO
        outline = _RO.susun_outline(judul, '', jml, tier=tier_form)
    except Exception as e:
        print(f'[outline_job] gagal susun judul={judul!r} tier={tier_nama!r}: '
              f'{e!r}', flush=True)
        tandai_gagal(token, 'Kerangka gagal disusun, coba lagi')
        return
    try:
        import outline_buku as _OB
        masalah = _OB.periksa(outline)
    except Exception:
        masalah = []
    if masalah:
        print(f'[outline_job] kerangka tidak lolos periksa judul={judul!r}: '
              f'{masalah!r}', flush=True)
        tandai_gagal(token, 'Kerangka gagal disusun, coba lagi')
        return
    try:
        from . import referensi_pesanan as _RP
        pending = _RP.simpan_outline_pending(outline, tier=tier_nama)
        outline_json = _RP.outline_ke_json(outline)
    except Exception as e:
        print(f'[outline_job] gagal simpan pending judul={judul!r}: {e!r}',
              flush=True)
        tandai_gagal(token, 'Kerangka gagal disusun, coba lagi')
        return
    if not tandai_selesai(token, outline_json, pending):
        # Status sudah bukan jalan (timeout menandai gagal duluan):
        # buang hasil + pending, jangan timpa status gagal.
        try:
            _RP.hapus_outline_pending(pending)
        except Exception:
            pass


def mulai_utas(token):
    """Jalankan pekerjaan di utas daemon (tidak menahan shutdown)."""
    t = threading.Thread(target=jalankan_job, args=(token,),
                         name='outline-job-' + token, daemon=True)
    t.start()
    return t
