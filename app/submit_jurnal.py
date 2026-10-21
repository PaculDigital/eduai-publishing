"""Submit Artikel Jurnal ke Tridarma (OJS) — modul PEMANGGIL jembatan.

PETA LAPIS (8 — 5 sudah ada, lihat PUTUSAN_SUBMIT_ARTIKEL_JURNAL_16OKT2026.md):
  ③ daftar OJS      → jembatan `register_user.php`   (SUDAH ADA)
  ④ submit          → jembatan `submit_article.php`  (SUDAH ADA)
  ⑤ kirim kredensial→ WA EduAi + email               (SUDAH ADA)
  ⑥ reset sandi     → tautan resmi OJS               (SUDAH ADA di OJS)
  ⑦ baca status     → DB OJS `submissions`           (SUDAH ADA)

🔒 PUTUSAN BOS 16 Okt (lihat dokumen putusan):
  · username OJS = EMAIL user; sandi awal = Pass1EduAi.
  · Submit ke-2 dst TIDAK butuh sandi (jembatan cuma butuh username).
  · 1 AddOn Publish (Rp 500.000) = 1 artikel.
  · Jurnal tujuan SEMENTARA hanya JEMT (context_id=1).

⚠️ Yang TIDAK dilakukan modul ini: memotong token. Pemotongan AddOn tetap
   di jalur QRIS yang sudah ada (`/api/addon/buat`).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger(__name__)

# ── Alamat jembatan OJS (dari dalam VPS, TIDAK lewat Cloudflare) ──────────
#  Sumber tunggal: env `EDUAI_OJS_BRIDGE`. Default = alamat internal VPS.
#  ⚠️ 17 Okt 2026 (TERUKUR): default lama 'http://ojs-ojs_web-1/mcp' = nama
#  container INTERNAL VPS Tridarma => DNS tidak ketemu dari container EduAi
#  (Errno -3). Port 9027 di IP publik = SSH, BUKAN jembatan. Yang TERBUKTI
#  menjawab: lewat domain HTTPS `https://tridarma.id/mcp`.
OJS_BRIDGE = os.getenv(
    'EDUAI_OJS_BRIDGE',
    'https://tridarma.id/mcp',
).rstrip('/')

OJS_SITUS = os.getenv('EDUAI_OJS_SITUS', 'https://tridarma.id')

#  Jurnal tujuan. SEMENTARA hanya JEMT (putusan Bos: nanti bisa pilih bidang).
JURNAL_UTAMA = {
    'kode': 'jemt',
    'nama': 'JEMT (Journal of Economic and Management Technology)',
    'context_id': 1,
    'indeks': 'Google Scholar · Garuda · Ber-ISSN',
}

#  Peringkat Sinta untuk kartu 2 (negosiasi manual via WA admin).
SINTA = [2, 3, 4, 5, 6]

#  Sandi awal akun Tridarma (putusan Bos).
SANDI_AWAL = 'Pass1EduAi'

#  AddOn yang dipakai kartu 1 (SUDAH ADA di config.ADDON).
KODE_ADDON = 'publish'

#  Timeout panggilan jembatan (detik). Submit+daftar bisa lambat.
TIMEOUT_DETIK = 90


class JembatanError(Exception):
    """Gagal menghubungi/menjawab jembatan OJS. Pesannya untuk user."""


def _panggil(jalur: str, muatan: dict[str, Any]) -> dict[str, Any]:
    """POST JSON ke jembatan OJS. Mengembalikan dict balasan jembatan.

    Dipisah supaya mudah dipalsukan saat uji (jangan panggil jaringan nyata
    di gerbang uji).
    """
    import urllib.error                                           # noqa: PLC0415
    import urllib.request                                         # noqa: PLC0415

    url = f'{OJS_BRIDGE}/{jalur}'
    data = json.dumps(muatan).encode('utf-8')
    req = urllib.request.Request(
        url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_DETIK) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:                           # noqa: PERF203
        #  Jembatan SELALU balas JSON (walau galat) — coba baca isinya dulu.
        try:
            isi = json.loads(e.read().decode('utf-8'))
        except Exception:                                         # noqa: BLE001
            raise JembatanError(
                f'Jembatan OJS menolak permintaan (HTTP {e.code}).') from e
        isi.setdefault('ok', False)
        isi['http_status'] = e.code
        return isi
    except Exception as e:                                        # noqa: BLE001
        raise JembatanError(
            'Tidak bisa menghubungi sistem jurnal (Tridarma). '
            'Coba lagi sebentar lagi ya.') from e


# ══════════════════════════════════════════════════════════════════════════
#  ③ DAFTAR AKUN OJS
# ══════════════════════════════════════════════════════════════════════════
def daftarkan(u: Any, kata_sandi: str = SANDI_AWAL) -> dict[str, Any]:
    """Daftarkan user EduAi ke Tridarma. **Idempoten**: kalau sudah ada,
    jembatan sendiri yang menolak bikin dobel (pagar `getByUsername`).

    Username = EMAIL user (putusan Bos) supaya user ingat satu identitas.
    """
    bagian = (getattr(u, 'nama', '') or '').strip().split()
    depan = bagian[0] if bagian else 'Pengguna'
    belakang = ' '.join(bagian[1:]) if len(bagian) > 1 else 'EduAi'

    muatan = {
        'username': u.email,
        'email': u.email,
        'password': kata_sandi,
        'given_name': depan,
        'family_name': belakang,
        'affiliation': getattr(u, 'nama_kampus', '') or 'EduAi',
        'country': 'ID',
        'phone': _nomor_hp(u),
    }
    return _panggil('register_user.php', muatan)


def _nomor_hp(u: Any) -> str:
    """Nomor HP user dalam bentuk 628xxx. Kosong kalau tak ada.

    ⚠️ Nama kolom TIDAK ditebak: dibaca lewat getattr bertingkat supaya
    modul ini tidak pecah kalau kolomnya bernama lain.
    """
    for nama in ('phone', 'no_hp', 'wa', 'telepon', 'hp'):
        nilai = getattr(u, nama, None)
        if nilai:
            angka = ''.join(c for c in str(nilai) if c.isdigit())
            if angka.startswith('0'):
                angka = '62' + angka[1:]
            elif not angka.startswith('62'):
                angka = '62' + angka
            return angka
    return ''


# ══════════════════════════════════════════════════════════════════════════
#  ④ SUBMIT ARTIKEL
# ══════════════════════════════════════════════════════════════════════════
def kirim_artikel(email: str, judul: str, abstrak: str,
                  penulis: list[dict], kata_kunci: list[str] | None = None,
                  context_id: int = 1) -> dict[str, Any]:
    """Kirim artikel ke OJS lewat jembatan. **Tidak butuh sandi user.**

    Pagar jembatan (JANGAN diduplikasi): judul ≥10 huruf, abstrak ≥80 kata,
    anti-dobel 24 jam (judul + email penulis pertama).
    """
    muatan = {
        'username': email,
        'title': judul,
        'abstract': abstrak,
        'authors': penulis,
        'keywords': kata_kunci or [],
        'section_id': 1,
        'language': 'en',
        'context_id': context_id,
    }
    return _panggil('submit_article.php', muatan)


def periksa_siap(email: str, judul: str, abstrak: str,
                 penulis: list[dict]) -> list[str]:
    """Periksa SYARAT JEMBATAN lebih dulu (Rp 0) — supaya user tidak
    membayar AddOn lalu ditolak jembatan karena abstrak pendek.

    Mengembalikan daftar pesan masalah (kosong = siap).
    """
    masalah: list[str] = []
    if not email or '@' not in email:
        masalah.append('Email akunmu belum lengkap.')
    if len((judul or '').strip()) < 10:
        masalah.append('Judul artikel minimal 10 huruf.')
    jumlah_kata = len([k for k in (abstrak or '').split() if k.strip()])
    if jumlah_kata < 80:
        masalah.append(
            f'Abstrak minimal 80 kata (sekarang {jumlah_kata} kata). '
            'Abstrak ini yang dipakai sistem jurnal, ya.')
    if not penulis:
        masalah.append('Data penulis belum ada.')
    return masalah


# ══════════════════════════════════════════════════════════════════════════
#  ⑦ BACA STATUS ARTIKEL
# ══════════════════════════════════════════════════════════════════════════
#  Peta tahap OJS → kata yang DIMENGERTI USER (bukan istilah OJS).
TAHAP = {
    1: ('Antrean', 'kuning'),
    2: ('Diperiksa Editor', 'biru'),
    3: ('Sedang Review', 'biru'),
    4: ('Perlu Revisi', 'oranye'),
    5: ('Produksi', 'hijau'),
}

#  status kolom OJS: 1=queued/submitted, 3=published, 4=declined
STATUS = {
    1: ('Berjalan', 'biru'),
    3: ('Diterima', 'hijau'),
    4: ('Ditolak', 'merah'),
}


def terjemah_status(stage_id: int | None, status: int | None) -> dict:
    """Ubah angka OJS jadi kata + warna. Tidak menebak: nilai tak dikenal
    dikembalikan apa adanya dengan label 'Sedang Diproses'."""
    tahap, warna_t = TAHAP.get(int(stage_id or 0), ('Sedang Diproses', 'abu'))
    st, warna_s = STATUS.get(int(status or 0), ('Berjalan', 'biru'))
    if st in ('Diterima', 'Ditolak'):
        return {'label': st, 'warna': warna_s, 'tahap': tahap}
    return {'label': tahap, 'warna': warna_t, 'tahap': tahap}


def tautan_artikel(submission_id: int, jurnal: str = 'jemt') -> str:
    return f'{OJS_SITUS}/{jurnal}/en/submission/view/{submission_id}'


def tautan_lupa_sandi() -> str:
    """Tautan RESMI OJS untuk lupa sandi. EduAi TIDAK menyimpan sandi baru.

    ⚠️ Diketik dari rute nyata OJS 3.5 (`/login/lostPassword`). Kalau berubah,
    ubah DI SINI saja.
    """
    return f'{OJS_SITUS}/jemt/en/login/lostPassword'


def tautan_masuk() -> str:
    return f'{OJS_SITUS}/jemt/en/login'


def nomor_wa_admin() -> str:
    """Nomor WA admin untuk kartu 2. Sumber tunggal: `config.EDUAI_WA_ADMIN`.

    Format `wa.me` = angka tanpa tanda plus (62857…). JANGAN diketik ulang
    di template.
    """
    from .config import EDUAI_WA_ADMIN                            # noqa: PLC0415
    return ''.join(c for c in str(EDUAI_WA_ADMIN) if c.isdigit())


# ══════════════════════════════════════════════════════════════════════════
#  PENCATATAN ARTIKEL — menumpang kolom `profil_dokumen.jurnal_json` yang
#  SUDAH ADA (nol tabel baru, nol kolom baru). Putusan Bos 16 Okt.
# ══════════════════════════════════════════════════════════════════════════
KUNCI = 'submit_tridarma'


def catat(db, user_id: int, berkas_id: int, data: dict) -> bool:
    """Simpan penanda submit ke `jurnal_json` MILIK NASKAH itu.

    ⚠️ Kunci BEDA PER KONSUMEN: catatan ini hidup di dalam naskah
    (`ProfilDokumen` per file_id), bukan di tabel global.
    """
    from .models import ProfilDokumen                             # noqa: PLC0415
    p = db.query(ProfilDokumen).filter(
        ProfilDokumen.file_id == berkas_id,
        ProfilDokumen.user_id == user_id).first()
    if not p:
        p = ProfilDokumen(file_id=berkas_id, user_id=user_id)
        db.add(p)
        db.flush()
    isi = {}
    if p.jurnal_json:
        try:
            isi = json.loads(p.jurnal_json) or {}
        except Exception:                                         # noqa: BLE001
            isi = {}
    lama = isi.get(KUNCI) or {}
    riwayat = list(lama.get('riwayat') or [])
    riwayat.insert(0, data)
    isi[KUNCI] = {
        'username': data.get('username', ''),
        'terdaftar': True,
        'riwayat': riwayat[:20],
        'dikirim_pada': data.get('tanggal', ''),
    }
    p.jurnal_json = json.dumps(isi, ensure_ascii=False)
    db.commit()
    return True


def catatan(db, user_id: int, berkas_id: int) -> dict:
    """Baca penanda submit satu naskah (kosong kalau belum pernah)."""
    from .models import ProfilDokumen                             # noqa: PLC0415
    p = db.query(ProfilDokumen).filter(
        ProfilDokumen.file_id == berkas_id,
        ProfilDokumen.user_id == user_id).first()
    if not p or not p.jurnal_json:
        return {}
    try:
        return (json.loads(p.jurnal_json) or {}).get(KUNCI) or {}
    except Exception:                                             # noqa: BLE001
        return {}


def daftar_artikel(db, user_id: int) -> list[dict]:
    """Semua artikel user yang PERNAH dikirim ke Tridarma (untuk kartu 3).

    Hanya dari catatan EduAi — Rp 0, tidak memanggil jaringan. Status
    diperbarui oleh `perbarui_status()`.
    """
    from .models import ProfilDokumen                             # noqa: PLC0415
    keluar: list[dict] = []
    for p in db.query(ProfilDokumen).filter(
            ProfilDokumen.user_id == user_id).all():
        if not p.jurnal_json:
            continue
        try:
            cat = (json.loads(p.jurnal_json) or {}).get(KUNCI) or {}
        except Exception:                                         # noqa: BLE001
            continue
        for r in cat.get('riwayat') or []:
            keluar.append({
                'id': r.get('submission_id'),
                'berkas_id': p.file_id,
                'judul': r.get('judul') or (p.judul or 'Artikel'),
                'tanggal': (r.get('tanggal') or '')[:16].replace('T', ' '),
                'status': r.get('status') or 'Antrean',
                'warna': r.get('warna') or 'antre',
                'tautan': r.get('tautan') or '',
                'jurnal': r.get('jurnal') or 'JEMT',
                'volume': r.get('volume') or '',
                'nomor': r.get('nomor') or '',
                'tanggal_diterima': r.get('tanggal_diterima') or '',
            })
    keluar.sort(key=lambda a: str(a.get('tanggal') or ''), reverse=True)
    return keluar


# ══════════════════════════════════════════════════════════════════════════
#  🔗 DUA KABEL PENYAMBUNG (ACC Bos 16 Okt "A" — lanjut sampai sinkron)
# ══════════════════════════════════════════════════════════════════════════
def kirim_setelah_lunas(db, u, order_id: str = '') -> dict | None:
    """① KABEL 1 — dipanggil setelah QRIS LUNAS.

    Mengambil naskah yang dititipkan di `Transaksi.berkas_id` (diisi layar
    saat menekan "Kirim & Lanjut Bayar"), lalu:
      1. daftarkan akun Tridarma (kalau belum ada — jembatan idempoten),
      2. ambil JUDUL + ABSTRAK dari naskah,
      3. kirim ke `submit_article.php`,
      4. catat `submission_id` ke catatan naskah.

    Mengembalikan dict untuk layar, atau None kalau tidak ada naskah
    tertitip (AddOn publish dibeli tanpa lewat tombol kartu 1).
    """
    from .models import Transaksi                                 # noqa: PLC0415
    trx = db.query(Transaksi).filter(Transaksi.order_id == order_id).first()
    fid = getattr(trx, 'berkas_id', None) if trx else None
    if not fid:
        return None

    berkas = _berkas_user(db, u.id, fid)
    if not berkas:
        return {'ok': False, 'pesan': 'Naskah tidak ditemukan.'}

    judul, abstrak, penulis = _bahan_artikel(db, u, berkas)
    masalah = periksa_siap(u.email, judul, abstrak, penulis)
    if masalah:
        return {'ok': False, 'berkas_id': fid,
                'masalah': masalah,
                'pesan': 'Naskah belum lengkap untuk dikirim: '
                         + ' '.join(masalah)}

    #  1. daftarkan ke Tridarma (idempoten — jembatan yang menolak dobel)
    try:
        daftarkan(u, SANDI_AWAL)
    except JembatanError as e:
        return {'ok': False, 'berkas_id': fid,
                'pesan': f'Gagal menyiapkan akun Tridarma: {e}'}

    #  2. kirim artikel
    hasil = kirim_artikel(u.email, judul, abstrak, penulis,
                          context_id=JURNAL_UTAMA['context_id'])
    if not hasil.get('ok'):
        pesan = hasil.get('error') or hasil.get('pesan') or 'Jembatan menolak.'
        if hasil.get('duplicate'):
            pesan = 'Artikel ini sudah pernah dikirim ke Tridarma — jadi ' \
                    'tidak dikirim dua kali.'
        return {'ok': False, 'berkas_id': fid, 'pesan': str(pesan)[:300]}

    sid = hasil.get('submission_id')
    sekarang = _now_iso()
    tanya, warna = terjemah_status(None, None)
    data = {
        'submission_id': sid, 'judul': judul, 'username': u.email,
        'tanggal': sekarang, 'status': tanya, 'warna': warna,
        'jurnal': 'JEMT', 'tautan': tautan_artikel(sid) if sid else '',
        'order_id': order_id,
    }
    catat(db, u.id, fid, data)

    #  3. kirim kredensial ke user (WA EduAi — WA jembatan tidak jalan)
    _kabari_kredensial(db, u, judul)

    return {'ok': True, 'berkas_id': fid, 'submission_id': sid,
            'tautan': data['tautan'], 'judul': judul,
            'pesan': 'Artikel terkirim! Cek statusnya di bagian '
                     '"Artikel Saya di Tridarma".'}


def _kabari_kredensial(db, u, judul: str) -> None:
    """Beri tahu email + sandi awal Tridarma ke user (WA EduAi).

    ⚠️ WA jembatan Tridarma TIDAK jalan (`sent=false`) ⇒ EduAi kirim sendiri
    lewat WA EduAi yang sudah terbukti hidup. Gagal kirim TIDAK menghentikan
    proses (pesan tetap ada di layar).
    """
    try:
        from . import wa as _wa                                    # noqa: PLC0415
        pesan = (
            'Artikelmu sudah dikirim ke jurnal Tridarma 🎉\n\n'
            f'Judul: {judul[:70]}\n\n'
            'Untuk memantau status (review, revisi, dll), masuk ke:\n'
            f'{tautan_masuk()}\n\n'
            f'Email (username): {u.email}\n'
            f'Sandi awal: {SANDI_AWAL}\n\n'
            'Disarankan segera ganti sandi di halaman Tridarma ya. '
            'Kalau lupa, pakai tombol "Lupa sandi?" — tautannya dikirim '
            'ke emailmu.')
        _wa.kirim_user(db, u.id, 'jurnal', pesan)
    except Exception as e:                                        # noqa: BLE001
        log.warning('[submit-jurnal] kabari kredensial gagal: %s', e)


def _berkas_user(db, user_id: int, berkas_id: int):
    """Naskah milik user (1 gerbang). None kalau bukan miliknya/terhapus."""
    from .models import FileBerkas                                # noqa: PLC0415
    b = db.get(FileBerkas, berkas_id)
    if not b or b.user_id != user_id or b.terhapus_pada is not None:
        return None
    return b


def _bahan_artikel(db, u, berkas) -> tuple[str, str, list[dict]]:
    """Ambil judul + abstrak + penulis dari naskah.

    Sumber: dokumen `.docx` naskah (bagian awal = judul/abstrak). Kalau tidak
    terbaca, dipakai nama naskah sebagai judul. Abstrak WAJIB ada — kalau
    kosong, `periksa_siap()` yang menolak (bukan mesin ini).
    """
    judul = (berkas.nama or '').rsplit('.', 1)[0][:300]
    abstrak = ''
    try:
        from .plagiarisme import teks_naskah    # pola TUNGGAL baca naskah
        teks = teks_naskah(berkas) or ''
    except Exception:                                             # noqa: BLE001
        teks = ''
    if teks:
        baris = [b.strip() for b in teks.splitlines() if b.strip()]
        if baris:
            judul = baris[0][:300] or judul
        #  abstrak = paragraf panjang pertama (≥80 kata) di 60 baris awal
        for blok in baris[1:60]:
            if len(blok.split()) >= 80:
                abstrak = blok
                break

    bagian = (getattr(u, 'nama_lengkap', '') or u.nama or 'Pengguna').split()
    penulis = [{
        'given_name': bagian[0],
        'family_name': ' '.join(bagian[1:]) or 'EduAi',
        'email': u.email,
        'affiliation': getattr(u, 'nama_kampus', '') or 'EduAi',
    }]
    return judul, abstrak, penulis


def _now_iso() -> str:
    from datetime import datetime, timezone                          # noqa: PLC0415
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()


def perbarui_status(db, u, artikel: list[dict]) -> list[dict]:
    """② KABEL 2 — baca status TERKINI dari Tridarma.

    🔒 HANYA dipanggil saat user MENEKAN TOMBOL "Cek Status" — BUKAN otomatis
    tiap halaman dibuka (putusan Bos 16 Okt 2026: hemat resource VPS).

    Mengembalikan daftar artikel dengan status terbaru + menyimpannya ke
    catatan supaya kunjungan berikutnya tidak perlu menunggu.
    """
    for a in artikel:
        sid = a.get('id')
        if not sid:
            continue
        try:
            hasil = baca_status(int(sid))
        except JembatanError as e:
            a['catatan'] = f'Belum bisa diperiksa: {e}'
            continue
        if not hasil.get('ok'):
            a['catatan'] = hasil.get('error') or 'Status belum terbaca.'
            continue
        a['status'] = hasil.get('status') or a.get('status')
        a['warna'] = hasil.get('warna') or a.get('warna')
        a['diperbarui'] = (hasil.get('diperbarui') or '')[:16]
        if hasil.get('tautan'):
            a['tautan'] = hasil['tautan']
        #  ⚠️ 17 Okt 2026: LoA BUTUH Volume + Nomor terbitan dari Tridarma.
        #  Sebelumnya tidak diambil => tombol LoA selalu bilang "belum ada".
        for k in ('volume', 'nomor', 'tanggal_diterima', 'tanggal_terbit',
                  'penulis', 'afiliasi'):
            if hasil.get(k):
                a[k] = hasil[k]
        #  simpan supaya tak perlu tanya ulang tiap kali
        if a.get('berkas_id'):
            try:
                catat(db, u.id, a['berkas_id'], {
                    'submission_id': sid, 'judul': a.get('judul'),
                    'username': u.email, 'tanggal': _now_iso(),
                    'status': a.get('status'), 'warna': a.get('warna'),
                    'jurnal': a.get('jurnal') or 'JEMT',
                    'tautan': a.get('tautan') or '',
                    'volume': a.get('volume') or '',
                    'nomor': a.get('nomor') or '',
                    'tanggal_diterima': a.get('tanggal_diterima') or '',
                    'tanggal_terbit': a.get('tanggal_terbit') or '',
                    'penulis': a.get('penulis') or '',
                    'afiliasi': a.get('afiliasi') or '',
                    'sumber': 'cek-status'})
            except Exception as e:                                # noqa: BLE001
                log.warning('[submit-jurnal] simpan status gagal: %s', e)
    return artikel


def baca_status(submission_id: int) -> dict:
    """Tanya status SATU artikel ke jembatan OJS (`article_status.php`)."""
    return _panggil('article_status.php', {'submission_id': int(submission_id)})
