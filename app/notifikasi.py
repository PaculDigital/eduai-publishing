"""KATA-KATA NOTIFIKASI EDUAI — satu sumber, mudah diubah.

═══ KENAPA MODUL TERPISAH ═══

ACC Bos 17Sep26:
  1. Semua notifikasi WAJIB bertutur HANGAT & MENGINGATKAN — bukan
     menakutkan. Notifikasi akan SERING muncul, jadi tidak boleh terasa
     mengganggu. Lihat `PANTANGAN` di bawah.
  2. Penyebutan pelaku = **"EduAi"** saja. JANGAN "AI", "Wulan", "asisten",
     atau "agen". User harus mengenal SATU identitas produk.

KENAPA DI SATU BERKAS: teks notifikasi dulu tersebar di dalam kode. Begitu
Bos ingin mengganti pilihan kata, harus berburu ke banyak tempat dan ada yang
terlewat (pelajaran 15Sep26: pesan yang diubah bos mematikan logika yang
mencocokkan kata). Sekarang SEMUA kalimat ada di sini — halaman/pemanggil
hanya memanggil fungsi, tidak menulis kalimat sendiri.

CARA PAKAI:
    from .notifikasi import pesan
    teks = pesan('kuota_hampir_habis', sisa=2)
    teks['judul'], teks['isi'], teks['tombol'], teks['nada']
"""
from __future__ import annotations

import logging

#  ⛔ PANTANGAN KATA (aturan Bos 17Sep26). Ada UJI yang menjaga daftar ini
#  (scripts/uji_notifikasi_kata.py) supaya tidak ada yang menyelinap masuk.
PANTANGAN = (
    'PERINGATAN', 'BAHAYA', 'AWAS', 'HABIS!', 'GAGAL!', 'SEGERA',
    'DARURAT', 'TERAKHIR', 'DIBLOKIR', 'DITOLAK!', 'ERROR', 'TERJADI KESALAHAN',
    'Anda harus', 'Wajib', 'JANGAN SAMPAI',
)

#  Yang JADI patokan: hangat, mengingatkan, selalu ada jalan keluar.
#  Nada = dipakai UI untuk memilih warna/ikon (bukan untuk menakut-nakuti).
#    'kabar'  → kabar baik       (hijau)
#    'ingat'  → pengingat lembut (kuning)
#    'bantu'  → menemani         (biru)
#    'semangat' → penyemangat    (ungu lembut)


def pesan(nama_jenis: str, **data) -> dict:
    """Ambil teks notifikasi. Selalu mengembalikan dict lengkap.

    Kunci: judul, isi, tombol (bisa None), nada.
    Kalau `jenis` tidak dikenal → dipakai teks netral (TIDAK melempar galat),
    karena notifikasi yang rusak lebih buruk daripada notifikasi biasa.

    ⚠️ JEBAKAN TERBUKTI (17Sep26): dulu parameter pertama bernama `jenis`
    juga, jadi `pesan('addon_hampir_habis', jenis='revisi')` → TypeError
    "got multiple values for argument 'jenis'". Namanya diganti jadi
    `nama_jenis` supaya kunci data bernama `jenis` (yang dipakai AddOn)
    tidak bentrok.
    """
    pembuat = _DAFTAR.get(nama_jenis)
    if pembuat is None:
        return {'judul': 'Ada kabar dari EduAi', 'isi': '', 'tombol': None,
                'nada': 'bantu'}
    return pembuat(**data)


# ── FASE 1: uang & kepercayaan ────────────────────────────────────────────
def _revisi_selesai(bagian: str = '', file_id=None) -> dict:
    bagian = (bagian or '').strip()
    sebut = f'"{bagian}"' if bagian else 'Naskahmu'
    return {
        'judul': 'Revisi naskahmu sudah siap',
        'isi': (f'{sebut} baru saja dirapikan EduAi. '
                'Yuk lihat hasilnya — santai saja, kapan pun kamu siap.'),
        'tombol': 'Buka',
        'nada': 'kabar',
    }


def _revisi_belum_berhasil(alasan: str = '', file_id=None) -> dict:
    """Revisi gagal. WAJIB menyebut kuota dikembalikan — itu inti kepercayaan.

    ⚠️ JANGAN pakai kata 'gagal' di judul (pantangan Bos). Pakai
    'belum berhasil' — jujur, tapi tidak menghakimi.

    ⚠️ JEBAKAN TERBUKTI (17Sep26): dulu `alasan` (galat teknis server)
    ditempel APA ADANYA ke kalimat ini. Akibatnya mahasiswa membaca
    "RuntimeError: provider AI tidak merespons" — membingungkan DAN
    menyebut 'AI' (melanggar aturan penyebutan: harus 'EduAi').
    Sekarang galat teknis TIDAK PERNAH ditampilkan ke user; hanya
    dijelaskan sebagai 'kendala teknis'. Galat asli tetap tersimpan di
    DB (`proses_ai.galat`) untuk diperiksa Wulan/teknisi.
    """
    return {
        'judul': 'Revisimu belum berhasil kali ini',
        'isi': ('Ada kendala teknis kecil saat menyusun naskahmu. '
                'Tenang, kuotamu sudah EduAi kembalikan penuh. '
                'Coba lagi kapan pun kamu siap — biasanya langsung lancar.'),
        'tombol': 'Coba lagi',
        'nada': 'bantu',
    }


def _buku_selesai(judul_buku: str = '', **_kw) -> dict:
    """Buku selesai disusun — lonceng + WA (keputusan Bos 30 Okt 2026).

    Beda dari revisi_selesai: jenis ini KHUSUS buku, supaya WA buku
    tidak ikut terkirim untuk semua revisi yang memakai revisi_selesai.
    Judul buku dari hasil pekerjaan (tandai_selesai: hasil=judul).
    """
    sebut = f'Buku "{(judul_buku or "").strip()}"' if (judul_buku or '').strip() else 'Bukumu'
    return {
        'judul': 'Buku kamu sudah jadi',
        'isi': (f'{sebut} sudah selesai disusun EduAi. '
                'Yuk lihat dan unduh di Naskah Saya, kapan pun kamu siap.'),
        'tombol': 'Lihat buku',
        'nada': 'kabar',
    }


def _kuota_hampir_habis(sisa: int = 0, file_id=None) -> dict:
    """Sisa kuota menipis.

    🐛 AKAR YANG DITUTUP (17Sep26, ketemu lewat uji E2E): versi lama memakai
    satu pola kalimat untuk semua sisa, sehingga saat sisa=0 notifikasinya
    berbunyi *"Masih cukup untuk sekali revisi lagi"* — BOHONG, dan langsung
    terpatahkan begitu mahasiswa klik revisi. Sekarang tiap sisa punya
    kalimatnya sendiri: 0 → ajakan mengisi; 1 → jujur tinggal sekali;
    >=2 → masih lega.
    """
    sisa = max(0, int(sisa or 0))
    if sisa == 0:
        return {
            'judul': 'Kuota revisimu sudah terpakai semua',
            'isi': ('Semua jatah bulan ini sudah dipakai untuk naskahmu. '
                    'Kalau masih ada yang mau dirapikan, kamu bisa tambah '
                    'kuota kapan saja kok — tanpa menunggu bulan depan.'),
            'tombol': 'Lihat paket',
            'nada': 'ingat',
        }
    if sisa == 1:
        return {
            'judul': 'Kuota revisimu tersisa 1',
            'isi': ('Tinggal sekali lagi untuk bulan ini. Kalau naskahmu masih '
                    'panjang, kamu bisa tambah kuota kapan saja kok — tanpa '
                    'menunggu bulan depan.'),
            'tombol': 'Lihat paket',
            'nada': 'ingat',
        }
    return {
        'judul': f'Kuota revisimu tersisa {sisa}',
        'isi': (f'Masih cukup untuk {sisa} kali revisi lagi. '
                'Kalau naskahmu masih panjang, kamu bisa tambah kuota '
                'kapan saja kok — tanpa menunggu bulan depan.'),
        'tombol': 'Lihat paket',
        'nada': 'ingat',
    }


def _addon_hampir_habis(sisa: int = 0, jenis: str = 'revisi') -> dict:
    sisa = max(0, int(sisa or 0))
    if jenis == 'storage':
        return {
            'judul': 'Ruang penyimpananmu mulai penuh',
            'isi': ('Naskahmu masih aman tersimpan semua. Kalau mau menambah '
                    'berkas lagi, ruangnya bisa ditambah kapan saja ya.'),
            'tombol': 'Tambah ruang',
            'nada': 'ingat',
        }
    return {
        'judul': f'Paket revisi tambahanmu tersisa {sisa}',
        'isi': (f'Masih ada {sisa} jatah. Biar tidak terputus di tengah jalan, '
                'bisa diisi ulang kapan saja — tidak hangus di akhir bulan.'),
        'tombol': 'Isi ulang',
        'nada': 'ingat',
    }


def _pembayaran_masuk(amount: str = '', item: str = '') -> dict:
    return {
        'judul': 'Pembayaranmu sudah masuk',
        'isi': ('Tambahan revisimu sudah aktif dan siap dipakai. '
                'Selamat mengerjakan naskahnya — EduAi siap membantu!'),
        'tombol': 'Mulai revisi',
        'nada': 'kabar',
    }


def _pembayaran_menunggu(amount: str = '', item: str = '') -> dict:
    return {
        'judul': 'Pembayaranmu masih menunggu',
        'isi': ('Kalau sudah transfer, biasanya masuk dalam beberapa menit. '
                'Kalau dirasa kelamaan, balas pesan ini ya — EduAi bantu cek.'),
        'tombol': 'Cek status',
        'nada': 'bantu',
    }


def _pembayaran_belum_masuk(amount: str = '', item: str = '') -> dict:
    return {
        'judul': 'Pembayaranmu belum terdeteksi',
        'isi': ('Belum ada pembayaran yang tercatat untuk pesanan ini. '
                'Kalau kamu merasa sudah membayar, kabari EduAi ya — '
                'nanti dibantu dicek sama-sama.'),
        'tombol': 'Bantuan',
        'nada': 'bantu',
    }


def _naskah_kena_batas(jumlah_bagian: int = 1, panjang: int = 0) -> dict:
    bagian = max(1, int(jumlah_bagian or 1))
    return {
        'judul': 'Naskahmu cukup besar',
        'isi': (f'Agar hasilnya tetap rapi, naskahmu dikerjakan bertahap '
                f'({bagian} bagian). Kamu bisa pantau perkembangannya di sini — '
                'tidak perlu ditunggui.'),
        'tombol': 'Lihat progres',
        'nada': 'bantu',
    }


def _naskah_kembali_kuota_terpakai(file_id=None) -> dict:
    """Rollback naskah — kuota TIDAK dibalikkan.

    ⚠️ KALIMAT INI DIKTE BOS VERBATIM (17Sep26) — JANGAN diubah tanpa ACC:
      "Kuota revisi sudah terpakai. Naskah kamu telah kembali dan bisa
       dirapikan kapan saja."

    Kenapa begitu: Bos MENOLAK versi awal yang berbunyi "karena hasilnya
    sudah pernah kamu lihat" — terasa menuduh/menyalahkan user. Kalimat baru
    menyatakan FAKTA (kuota terpakai) lalu langsung memberi jalan keluar
    (naskah bisa dirapikan kapan saja).
    """
    return {
        'judul': 'Naskah kamu telah kembali',
        'isi': ('Kuota revisi sudah terpakai. Naskah kamu telah kembali dan '
                'bisa dirapikan kapan saja.'),
        'tombol': 'Buka naskah',
        'nada': 'bantu',
    }


def _naskah_kembali_kuota_balik(jumlah: int = 1, file_id=None) -> dict:
    """Rollback naskah — kuota DIBALIKKAN (3 syarat Opsi C terpenuhi).

    Nada: kabar baik + jujur menyebut jumlah Token Revisi yang kembali.
    """
    jumlah = max(1, int(jumlah or 1))
    satuan = 'Token Revisi' if jumlah == 1 else 'Token Revisi'
    return {
        'judul': 'Kuotamu sudah EduAi kembalikan',
        'isi': (f'Karena hasil revisi tadi belum sempat kamu pakai, '
                f'{jumlah} {satuan} sudah masuk kembali. '
                'Naskah kamu sudah kembali ke versi sebelumnya — '
                'silakan coba lagi kapan pun kamu siap.'),
        'tombol': 'Buka naskah',
        'nada': 'kabar',
    }


def _pembimbing_catatan_baru(jumlah: int = 1, bab: str = '',
                             file_id=None) -> dict:
    """Pembimbing menulis catatan baru di naskah mahasiswa (26Sep26).

    Sumber: rute_pembimbing.tambah_catatan (halaman /tinjau). Penerima =
    pemilik naskah. Sebut 'pembimbing' (aturan 21Sep26), jangan 'dosen'.
   """
    jumlah = max(1, int(jumlah or 1))
    sebut = f'"{bab}"' if (bab or '').strip() else 'naskahmu'
    return {
        'judul': 'Pembimbing menambah catatan baru',
        'isi': (f'Pembimbingmu menandai {jumlah} catatan di {sebut}. '
                'Yuk lihat — santai saja, nanti kamu balas kapan siap.'),
        'tombol': 'Buka',
        'nada': 'kabar',
    }


def _pembimbing_membuka(file_id=None) -> dict:
    """Pembimbing PERTAMA kali membuka naskah (26Sep26).

    HANYA sekali (dibuka_pada tadinya kosong) — bukan tiap kunjungan,
    supaya tidak jadi spam. Penerima = pemilik naskah.
   """
    return {
        'judul': 'Pembimbingmu sudah membuka naskah',
        'isi': ('Kabar baik: naskahmu sudah diperhatikan. '
                'Tenang, kamu tak perlu buru-buru membalas catatannya.'),
        'tombol': 'Buka',
        'nada': 'kabar',
    }


def _pembimbing_diundang(nama: str = '', file_id=None) -> dict:
    """Mahasiswa baru MEMBUAT link bimbingan (27Sep26, gelombang 2 #3).

    Sumber: pembimbing.buat_bimbingan (dipanggil rute bagikan).
    Penerima = pemilik naskah. Nada: tenang — ini kabar proses, bukan
    tuntutan. Jangan tampilkan kontak pembimbing.
    """
    sebut = f'untuk "{nama}"' if (nama or '').strip() else 'buat pembimbingmu'
    return {
        'judul': 'Link bimbingan sudah siap',
        'isi': (f'Link tinjau {sebut} sudah dibuat. Tinggal kirimkan ke '
                'beliau — naskahmu bisa dilihat begitu linknya dibuka.'),
        'tombol': 'Lihat link',
        'nada': 'kabar',
    }


def _hasil_ai_siap(jumlah: int = 1, file_id=None) -> dict:
    """Rekomendasi Peta Halus selesai dikerjakan AI (27Sep26, gelombang 2 #5).

    Sumber: peta_kerjakan jalur latar belakang (27Sep26 anti-524).
    Penerima = pemilik naskah. Kalimat hasil revisi lama dipakai ulang
    polanya: jujur + santai.
    """
    return {
        'judul': 'Perbaikan pilihanmu sudah selesai',
        'isi': ('EduAi sudah menyelesaikan perbaikan yang kamu pilih di '
                'Peta Halus. Cek hasilnya — bisa langsung dipakai atau '
                'disunting dulu sesuai gayamu.'),
        'tombol': 'Lihat hasil',
        'nada': 'kabar',
    }


_DAFTAR = {
    'revisi_selesai': _revisi_selesai,
    'revisi_belum_berhasil': _revisi_belum_berhasil,
    'buku_selesai': _buku_selesai,
    'kuota_hampir_habis': _kuota_hampir_habis,
    'addon_hampir_habis': _addon_hampir_habis,
    'pembayaran_masuk': _pembayaran_masuk,
    'pembayaran_menunggu': _pembayaran_menunggu,
    'pembayaran_belum_masuk': _pembayaran_belum_masuk,
    'naskah_kena_batas': _naskah_kena_batas,
    'naskah_kembali_kuota_terpakai': _naskah_kembali_kuota_terpakai,
    'naskah_kembali_kuota_balik': _naskah_kembali_kuota_balik,
    'pembimbing_catatan_baru': _pembimbing_catatan_baru,
    'pembimbing_membuka': _pembimbing_membuka,
    'pembimbing_diundang': _pembimbing_diundang,
    'hasil_ai_siap': _hasil_ai_siap,
}


def semua_jenis() -> list[str]:
    """Daftar jenis yang tersedia — dipakai skrip uji."""
    return sorted(_DAFTAR.keys())


# ══════════════════════════════════════════════════════════════════════════
#  PEMICU OTOMATIS — menyimpan notifikasi ke DB supaya MUNCUL ke mahasiswa
# ══════════════════════════════════════════════════════════════════════════
#
#  KENAPA DI SINI: ACC Bos 17Sep26 — notifikasi harus benar-benar muncul,
#  bukan sekadar kalimat yang tersimpan. Dulu `app/notifikasi.py` hanya
#  menyimpan KALIMAT; pemicunya belum ada, jadi mahasiswa tidak pernah
#  melihatnya.
#
#  PEMIKIRAN PENTING (jangan diubah tanpa pikir panjang):
#  - Notifikasi TIDAK BOLEH menggagalkan pekerjaan utama. Kalau pencatatan
#    gagal (DB sibuk, kolom belum ada), revisi tetap harus jalan. Karena itu
#    SEMUA galat di sini ditelan + dicatat ke log, bukan dilempar.
#  - Notifikasi DIAM kalau tidak ada sesuatu yang layak disampaikan
#    (contoh: sisa kuota masih banyak → jangan ganggu).
#  - ANTI-SPAM: satu jenis notifikasi yang sama untuk konteks yang sama
#    hanya dikirim SEKALI dalam `JEDA_SPAM_JAM`. Tanpa ini, mahasiswa yang
#    memakai 10 kali revisi akan menerima 10 notifikasi "sisa 1" — persis
#    yang Bos tidak inginkan ("agar tidak merasa terganggu").

JEDA_SPAM_JAM = 24

#  Ambang pemberitahuan — DI SINI angka bisnisnya, jangan disebar ke UI.
AMBANG_KUOTA = 2      # sisa <= 2 → beri tahu (ajakan menambah)
AMBANG_ADDON = 2      # sisa addon <= 2 → beri tahu


def catat(db, user_id: int, nama_jenis: str, jeda_jam: int | None = None,
          **data):
    """Simpan satu notifikasi ke DB. SELALU aman dipanggil.

    Kembalikan True kalau benar-benar tersimpan, False kalau dilewati
    (kena jeda anti-spam, atau ada galat). TIDAK PERNAH melempar.

    ⚠️ `db` sengaja TIDAK di-commit di sini; pemanggil yang memutuskan
    kapan commit supaya tidak ada commit di tengah transaksi penting.

    🐛 AKAR YANG DITUTUP (17Sep26, terbukti lewat uji):
    `db.add()` yang gagal (mis. user_id tidak sah → FOREIGN KEY gagal) TIDAK
    cukup ditangkap `except`. Sesinya jadi "teracuni" → setiap perintah
    berikutnya di sesi yang SAMA melempar `PendingRollbackError`. Kalau ini
    terjadi di jalur produksi (kuota.py/proses.py memakai sesi yang sama),
    transaksi UTAMA ikut rusak — bukan sekadar notifikasi yang hilang.
    Karena itu `db.rollback()` WAJIB dipanggil di blok `except`.
    """
    try:
        from .models import Notifikasi
        from sqlalchemy import select
        from datetime import datetime, timedelta

        t = pesan(nama_jenis, **data)
        #  Kunci anti-spam: jenis + konteks (file_id kalau ada).
        kunci = f'{nama_jenis}:{data.get("file_id") or data.get("sisa") or data.get("kode") or ""}'

        #  Sudah pernah dikirim dalam JEDA_SPAM_JAM terakhir?
        batas = datetime.utcnow() - timedelta(
            hours=(jeda_jam if jeda_jam is not None else JEDA_SPAM_JAM))
        sudah = db.execute(
            select(Notifikasi.id).where(
                Notifikasi.user_id == user_id,
                Notifikasi.kunci == kunci,
                Notifikasi.dibuat >= batas,
            ).limit(1)
        ).first()
        if sudah:
            return False

        db.add(Notifikasi(
            user_id=user_id,
            kunci=kunci,
            jenis=nama_jenis,
            judul=t['judul'],
            isi=t['isi'],
            tombol=t['tombol'],
            nada=t['nada'],
            file_id=data.get('file_id'),
        ))
        #  Paksa tulis SEKARANG supaya galat (mis. user tidak ada) muncul di
        #  sini — bukan menyusup ke commit pemanggil dan merusak transaksinya.
        db.flush()
        #  ── PENGANTAR WA (keputusan Bos 27Sep26) ─────────────────────────
        #  WA = pengantar KEDUA dari notifikasi penting. Fire-and-forget:
        #  WA tidak sampai TIDAK boleh menggagalkan transaksi utama.
        #  Hanya jenis yang Bos izinkan (pembelian lembut + undangan);
        #  revisi/kejadian harian TIDAK dikirim (switch per user di app.wa).
        if nama_jenis in ('pembayaran_masuk', 'pembayaran_menunggu',
                          'pembayaran_belum_masuk', 'pembimbing_diundang', 'buku_selesai'):
            try:
                from . import wa as _wa_mod
                _wa_mod.kirim_user(
                    db, user_id, ('pembelian' if nama_jenis.startswith(
                        'pembayaran') else 'undangan' if nama_jenis == 'pembimbing_diundang' else 'revisi'),
                    f"EduAi\n\n{t['judul']}\n\n{t['isi']}")
            except Exception as e_wa:                             # noqa: BLE001
                logging.getLogger(__name__).warning(
                    '[notifikasi] WA tidak terkirim: %s', e_wa)
        return True
    except Exception as e:                                        # noqa: BLE001
        #  JANGAN pernah menggagalkan pekerjaan utama hanya karena notifikasi.
        import logging
        logging.getLogger(__name__).warning(
            '[notifikasi] catat gagal (%s): %s', nama_jenis, e)
        try:
            #  WAJIB: bersihkan sesi yang teracuni supaya transaksi pemanggil
            #  tetap sehat. Tanpa ini, satu notifikasi gagal = seluruh
            #  pekerjaan revisi user ikut error.
            db.rollback()
        except Exception:                                         # noqa: BLE001
            pass
        return False


def periksa_dan_catat(db, user_id: int, sisa_kuota: int | None = None,
                      sisa_addon: int | None = None, **data) -> list[str]:
    """Periksa kondisi user → catat notifikasi yang LAYAK dikirim.

    Dipanggil SETELAH kuota dipotong (satu tempat, langsung saat kejadian).
    Kembalikan daftar jenis yang tercatat — berguna untuk uji.
    """
    tercatat: list[str] = []
    try:
        if sisa_kuota is not None and 0 <= sisa_kuota <= AMBANG_KUOTA:
            if catat(db, user_id, 'kuota_hampir_habis',
                     sisa=sisa_kuota, **data):
                tercatat.append('kuota_hampir_habis')
        if sisa_addon is not None and 0 < sisa_addon <= AMBANG_ADDON:
            if catat(db, user_id, 'addon_hampir_habis',
                     sisa=sisa_addon, **data):
                tercatat.append('addon_hampir_habis')
    except Exception as e:                                        # noqa: BLE001
        import logging
        logging.getLogger(__name__).warning(
            '[notifikasi] periksa_dan_catat gagal: %s', e)
    return tercatat
