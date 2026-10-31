"""PENYUSUN BUKU — menjalankan `buku_umum_pipeline` untuk SATU buku nyata.

KENAPA PEMBUNGKUS, BUKAN MESIN BARU (aturan Bos: jangan bikin yang sudah ada):
  `buku_umum_pipeline.py` sudah punya seluruh mesin (penulis→kritikus→editor,
  ilustrasi, infografis, assembly) + gerbang 39/0. Yang KURANG cuma satu hal:
  mesin itu memakai GLOBAL (`OUTLINE`, `OUT_DIR`) yang di-hardcode buku Ekonomi
  Digital. Jadi modul ini hanya MENYETEL global itu per buku, lalu memanggil
  fungsinya apa adanya. NOL logika tulis-menulis disalin.

API:
    apakah_bisa() -> (bool, alasan)
    susun_buku(judul, outline, jenis, keluar_dir, batas_bab=None,
               lapor=None, ulang=0, on_mulai=None) -> dict hasil
    info_antrian() -> (sedang_jalan?, jumlah_menunggu) [non-blokir]
"""
import os
import re
import threading
import time

SUMBER = "penyusun_buku.py"

# ══════════════════════════════════════════════════════════════════════════
#  LAPIS 3a — STATE PER BAB (ACC Bos 19 Okt 2026, batas 4 bab sejak 29 Okt 2026)
# ══════════════════════════════════════════════════════════════════════════
#  MASALAH: `buku_umum_pipeline` memakai variabel GLOBAL (`OUT_DIR`,
#  `CKPT_FILE`, `VISUAL_DIR`, `OUTLINE`) di 20 titik. Kalau 2 bab jalan
#  bersamaan, keduanya menulis ke folder & checkpoint yang SAMA ⇒ isi
#  tercampur, bab saling menimpa. Itu kerusakan SUNYI (tidak error, tapi
#  hasilnya salah) — paling berbahaya.
#
#  OBAT: KUNCI (threading.Lock). Sebelum satu bab bekerja, ia mengunci,
#  MENYETEL global ke foldernya sendiri, bekerja, lalu MENGEMBALIKAN global.
#  ⇒ Hanya SATU bab yang menyentuh global pada satu waktu.
#
#  ⚠️ KONSEKUENSI YANG HARUS JUJUR: karena global dikunci, bab yang sedang
#  menulis TIDAK benar-benar paralel di bagian Python-nya. Yang benar-benar
#  paralel adalah MENUNGGU AI (99% waktu, terukur). Jadi:
#    - 2 bab bersamaan TETAP memotong waktu besar (AI-nya jalan bersamaan),
#    - tapi bukan 2× penuh, karena bagian globalnya bergantian.
#  Ini pilihan sadar: BENAR dulu, cepat kemudian.
# ══════════════════════════════════════════════════════════════════════════
_KUNCI_GLOBAL = None
# 29 Okt 2026 (perintah 'perbaiki menjadi sempurna'): batas paralel bab
# bisa diubah lewat env tanpa ubah kode (default 4 = perilaku teruji;
# 6 belum teruji lintas kuota Scopus — naikkan hanya untuk uji ukur).
# Dijepit 1..8 (0 = macet, >8 = di luar bukti 9router); env rusak = 4.
try:
    _BATAS_BAB = min(8, max(1, int(os.environ.get('EDUAI_BAB_PARALEL', '4') or 4)))
except (TypeError, ValueError):
    _BATAS_BAB = 4
#  Perbaikan bedah struktural (Gas Bos 31 Okt 2026 12:03, butir 2).
#  Lapis 3c-2 lama (tulis ulang penuh satu bab, ACC Bos 19 Okt 2026)
#  DIHAPUS di Gas ini: bukti job 224, 5 dari 5 tulis ulang dibuang,
#  40 sampai 50 menit terbuang, isi bab tidak berubah. Penggantinya
#  adalah sisipan kecil SEKALI per celah struktural (tabel R3 atau
#  posisi R4), dicek deterministik, gagal cek berarti sisipan
#  dibuang dan bab lama dipertahankan, tanpa putaran kedua.
#  MAKSIMAL 1 sisipan per jenis celah per bab.
_BEDAH_MAKS = 1

#  Frasa posisi penulis, SAMA dengan app/cek_awal._FRASA_POSISI.
#  Diduplikasi di modul root ini supaya modul ini tidak bergantung
#  pada paket app, yang bisa tidak ada di sys.path saat gerbang
#  uji berjalan. Bila cek_awal mengubah daftarnya, daftar ini wajib
#  disamakan lagi.
_FRASA_POSISI = (
    'posisi penulis',
    'sintesis penulis',
    'penulis berpendapat',
    'penulis menilai',
    'penulis menyimpulkan',
    'penulis menegaskan',
    'menurut penulis',
    'pandangan penulis',
)


def _cek_sisipan_tabel(sisipan):
    """Cek deterministik sisipan tabel komparasi.

    Format tabel bab yang sudah ada: [TABEL N.1: Judul - Kolom
    A, Kolom B | Baris1: ... | Baris2: ... | Baris3: ...].
    Lolos bila memuat penanda [TABEL, pemisah pipa, dan minimal
    3 kemunculan Baris. Tanpa ketiganya, sisipan dibuang.
    """
    if not isinstance(sisipan, str) or not sisipan.strip():
        return False
    return ('[TABEL' in sisipan and '|' in sisipan
            and sisipan.count('Baris') >= 3)


def _cek_sisipan_posisi(sisipan):
    """Cek deterministik sisipan kalimat posisi penulis.

    Lolos bila memuat satu frasa posisi dari daftar cek_awal dan
    minimal 10 kata, sama dengan syarat R4 gerbang final. Tanpa
    keduanya, sisipan dibuang.
    """
    if not isinstance(sisipan, str) or not sisipan.strip():
        return False
    rendah = sisipan.lower()
    if not any(frasa in rendah for frasa in _FRASA_POSISI):
        return False
    return len(sisipan.split()) >= 10


def _sisip_ke_subbab(teks, nomor_bab, nomor_sub, sisipan):
    """Sisipkan teks kecil ke dalam subbab N.S yang tepat.

    Cari judul ### N.S, sisipkan sebelum judul ### berikutnya,
    bila tidak ada judul berikutnya, tempel di akhir bab. Bila
    judul subbab tidak ditemukan sama sekali, tempel di akhir
    bab, supaya sisipan tidak hilang diam-diam.
    """
    teks = teks or ''
    sisipan = (sisipan or '').strip()
    if not sisipan:
        return teks
    pola_judul = re.compile(
        r'^###\s*' + str(nomor_bab) + r'\.' + str(nomor_sub) + r'\b',
        re.MULTILINE)
    cocok = pola_judul.search(teks)
    if not cocok:
        return teks.rstrip() + '\n\n' + sisipan + '\n'
    pola_berikut = re.compile(r'^###\s+', re.MULTILINE)
    berikut = pola_berikut.search(teks, cocok.end())
    if berikut:
        return teks[:berikut.start()].rstrip() + '\n\n' + sisipan + '\n\n' + teks[berikut.start():]
    return teks.rstrip() + '\n\n' + sisipan + '\n'


def _celah_struktural(masalah, curiga):
    """Celah struktural dari hasil cek per bab.

    Return {'tabel': bool, 'posisi': bool}. Tabel bila masalah
    memuat tidak ada tabel (R3). Posisi bila masalah memuat tidak
    ada kalimat posisi, atau curiga memuat kalimat posisi terlalu
    pendek (R4). Masalah lain (duplikasi, sitasi, kata) BUKAN
    celah struktural dan tidak memicu bedah, supaya bedah tidak
    mencoba memperbaiki hal yang bukan tugasnya.
    """
    masalah = list(masalah or [])
    curiga = list(curiga or [])
    tabel = any('tidak ada tabel' in str(m) for m in masalah)
    posisi = (any('tidak ada kalimat posisi' in str(m) for m in masalah)
              or any('kalimat posisi penulis terlalu pendek' in str(c)
                     for c in curiga))
    return {'tabel': tabel, 'posisi': posisi}


def _sisipan_aman_sitasi(sisipan, rows):
    """True bila sisipan boleh dipakai, dari sisi sitasi.

    Aman bila sisipan tidak memuat sitasi formal sama sekali,
    atau setiap sitasi formalnya cocok dengan satu baris snapshot
    (kunci atau alias, tahun sama), memakai ekstraktor gerbang
    final. Bila rows None, sitasi formal apa pun dianggap tidak
    aman (fail-closed), karena tidak bisa diverifikasi. Bila
    ekstraktor tidak bisa diimpor, fallback ke pola tahun: ada
    tahun berarti tidak aman, tanpa tahun berarti aman.
    """
    if not isinstance(sisipan, str) or not sisipan.strip():
        return False
    try:
        from app.sitasi_anti_gagal import ekstrak_sitasi_badan as _ekstrak
        from app.gerbang_subbab import _cocok_snapshot as _cocok
        formal = _ekstrak(sisipan)
        if not formal:
            return True
        if rows is None:
            return False
        for sit in formal:
            if not _cocok(sit.get("surnames") or [],
                          sit.get("tahun") or "", rows):
                return False
        return True
    except Exception:
        if re.search(r"\b(19|20)\d{2}[a-z]?\b", sisipan):
            return False
        return True


# ══════════════════════════════════════════════════════════════════════════
#  ANTREAN BUKU GLOBAL (29 Okt 2026): SATU buku diproduksi dalam satu
#  waktu; di dalamnya bab dikerjakan bersamaan (maks `_BATAS_BAB`).
# ══════════════════════════════════════════════════════════════════════════
#  KENAPA FIFO PER BUKU (bukan berbagi slot antarbuku): `susun_buku`
#  menyetel GLOBAL pipeline per buku (P.OUT_DIR, P.OUTLINE, dan tambalan
#  P.architect_prompt). Dua pemanggilan bersamaan akan saling menimpa
#  global itu ⇒ isi buku tercampur (pencemaran lintas buku — terbukti
#  dari cara `generate_sub_bab` memanggil `architect_prompt` global).
#  Jadi antrean ini JUGA perbaikan kebenaran, bukan cuma keadilan.
#  Catatan: kunci ini berlaku dalam SATU proses aplikasi (uvicorn
#  1 worker). Jalur operator di proses lain tetap wajib eksklusif manual.
#  Pesan antrean dikirim berkala lewat `lapor` selama menunggu (halaman
#  proses memantau tiap 4 detik) — user melihat posisi + perkiraan, bukan
#  layar diam.
_ANTRIAN_KONDISI = threading.Condition()
_ANTRIAN_DEPAN = []        # token pesanan yang MENUNGGU giliran (FIFO)
_ANTRIAN_JALAN = None      # token pesanan yang SEDANG diproduksi
_ASLI_ARSITEK_TERSIMPAN = None  # original P.architect_prompt (slot pemulihan)


def _pesan_antrian(depan):
    """Pesan antrean yang lembut untuk user (tanpa jargon)."""
    return (
        "Buku sudah diterima dan masuk antrian produksi. "
        f"Ada {depan} buku lain di depan. "
        f"Perkiraan mulai ditulis sekitar {30 * depan}–{30 * (depan + 1)} menit lagi. "
        "Tidak perlu menunggu di halaman ini — lonceng akan menyala saat buku selesai."
    )


def _antrian_masuk():
    """Daftarkan pesanan ke antrean. Return token pesanan (objek unik)."""
    token = object()
    with _ANTRIAN_KONDISI:
        _ANTRIAN_DEPAN.append(token)
    return token


def _antrian_tunggu_giliran(token, lapor=None, jeda_pesan=30):
    """Blokir sampai giliran token tiba (FIFO + tidak ada buku berjalan).

    Selama menunggu, kirim pesan antrean berkala lewat `lapor` (tiap
    `jeda_pesan` detik) supaya tahap di halaman proses tetap hidup.
    `lapor` TIDAK pernah dipanggil sambil memegang kunci (hindari
    antrean macet karena tulis DB yang lambat).
    """
    global _ANTRIAN_JALAN
    while True:
        with _ANTRIAN_KONDISI:
            if _ANTRIAN_JALAN is None and _ANTRIAN_DEPAN and _ANTRIAN_DEPAN[0] is token:
                _ANTRIAN_DEPAN.pop(0)
                _ANTRIAN_JALAN = token
                return
            depan = (1 if _ANTRIAN_JALAN is not None else 0) + _ANTRIAN_DEPAN.index(token)
        if lapor is not None:
            try:
                lapor(_pesan_antrian(depan))
            except Exception:
                pass
        with _ANTRIAN_KONDISI:
            #  Cek ulang sebelum tidur (hindari kehilangan notify).
            if _ANTRIAN_JALAN is None and _ANTRIAN_DEPAN and _ANTRIAN_DEPAN[0] is token:
                _ANTRIAN_DEPAN.pop(0)
                _ANTRIAN_JALAN = token
                return
            _ANTRIAN_KONDISI.wait(timeout=jeda_pesan)


def _antrian_selesai(token):
    """Lepaskan giliran + bangunkan antrean (aman dipanggil berkali-kali)."""
    global _ANTRIAN_JALAN
    with _ANTRIAN_KONDISI:
        if token in _ANTRIAN_DEPAN:
            _ANTRIAN_DEPAN.remove(token)
        if _ANTRIAN_JALAN is token:
            _ANTRIAN_JALAN = None
        _ANTRIAN_KONDISI.notify_all()


def info_antrian():
    """NON-BLOKIR: (sedang_jalan?, jumlah_menunggu) — untuk pemantauan."""
    with _ANTRIAN_KONDISI:
        return (_ANTRIAN_JALAN is not None, len(_ANTRIAN_DEPAN))

def _ambil_kunci():
    """Buat/lambda kunci global sekali saja (aman dipanggil banyak utas)."""
    global _KUNCI_GLOBAL
    if _KUNCI_GLOBAL is None:
        import threading
        _KUNCI_GLOBAL = threading.Lock()
    return _KUNCI_GLOBAL


def apakah_bisa():
    """Cek mesin tersedia. Jangan janjikan proses kalau mesinnya tak ada."""
    try:
        import buku_umum_pipeline as P  # noqa: F401
    except Exception as e:
        return False, f"mesin pipeline tidak bisa dimuat: {type(e).__name__}: {e}"
    for fn in ("generate_bab", "post_process"):
        if not hasattr(P, fn):
            return False, f"fungsi {fn} tidak ada di pipeline"
    return True, ""


def susun_buku(judul, outline, jenis="umum", keluar_dir=None,
               batas_bab=None, lapor=None, ulang=0, on_mulai=None, tier=None, on_bab_selesai=None,
               refs_holder=None, dari_snapshot=False):
    """Susun buku dari outline yang SUDAH dibuat. Return dict hasil.

    Satu buku diproduksi dalam satu waktu (antrean FIFO global — lihat
    blok ANTREAN di atas): pemanggilan kedua menunggu sampai yang pertama
    selesai penuh. Di dalamnya, bab dikerjakan bersamaan (maks `_BATAS_BAB`).

    batas_bab : kalau diisi, hanya bab 1..batas_bab yang dikerjakan
                (dipakai untuk uji murah — jangan bakar token 6 bab).
    lapor     : fungsi(teks) untuk memberi kabar ke pemanggil (progress).
    ulang     : 0 = mulai dari awal; >0 = lanjutkan bab yang belum selesai.
    on_mulai  : dipanggil TEPAT saat giliran produksi tiba (sebelum satu
                kata ditulis). Pemanggil memotong kuota di sini — jadi
                buku yang masih mengantre BELUM dipotong.
    tier      : paket Hemat/Normal/Full (None = perilaku lama); diteruskan ke visuals.
    refs_holder: dict yang diisi on_mulai dengan refs snapshot
                 (dipakai bila dari_snapshot True, dibaca sesudah on_mulai).
    dari_snapshot: True bila penulisan memakai snapshot pra-panen
                 beku (bukan panen on demand), False bila jalur lama.

    TIDAK memotong kuota sendiri. Pemotongan kuota = tugas pemanggil
    lewat `on_mulai`, supaya modul ini bisa diuji tanpa menyentuh saldo
    siapa pun.
    """
    global _ASLI_ARSITEK_TERSIMPAN
    token = _antrian_masuk()
    try:
        _antrian_tunggu_giliran(token, lapor=lapor)
        return _susun_buku_dalam(judul, outline, jenis, keluar_dir,
                                 batas_bab, lapor, ulang, on_mulai, tier=tier,
                                 on_bab_selesai=on_bab_selesai,
                                 refs_holder=refs_holder,
                                 dari_snapshot=dari_snapshot)
    finally:
        _antrian_selesai(token)
        #  Pulihkan tambalan prompt — SEKALIGUS untuk semua jalan keluar
        #  (normal, gagal, dibatalkan). Sebelumnya pemulihan ada di
        #  `finally` loop utama, sehingga putaran PERBAIKAN (yang jalan
        #  sesudahnya) memakai prompt ASLI tanpa outline buku ⇒ jangkar
        #  [MASTER OUTLINE] jatuh ke outline Ekonomi Digital sementara.
        if _ASLI_ARSITEK_TERSIMPAN is not None:
            try:
                import buku_umum_pipeline as _P
                _P.architect_prompt = _ASLI_ARSITEK_TERSIMPAN
            except Exception:
                pass
            _ASLI_ARSITEK_TERSIMPAN = None


def _susun_buku_dalam(judul, outline, jenis="umum", keluar_dir=None,
                      batas_bab=None, lapor=None, ulang=0, on_mulai=None, tier=None, on_bab_selesai=None,
                      refs_holder=None, dari_snapshot=False):
    """Isi susun_buku (lihat docstring-nya). Dipanggil HANYA dari wrapper
    antrean di atas — jangan dipanggil langsung, supaya antrean tidak
    bisa dilewati diam-diam."""
    global _ASLI_ARSITEK_TERSIMPAN

    bisa, alasan = apakah_bisa()
    if not bisa:
        raise RuntimeError(alasan)

    import outline_buku as OB
    import buku_umum_pipeline as P

    masalah = OB.periksa(outline)
    if masalah:
        raise ValueError(f"outline tidak sehat ({len(masalah)} masalah): {masalah[:3]}")

    nomor = sorted(k for k in outline if isinstance(k, int))
    if not nomor:
        raise ValueError("outline tidak punya bab")

    #  GILIRAN TIBA = PRODUKSI DIMULAI: baru di sini pemanggil memotong
    #  kuota (lewat `on_mulai`). Validasi di atas sudah lolos, jadi gagal
    #  di titik ini bukan soal outline — dan buku yang masih mengantre
    #  di wrapper TIDAK PERNAH sampai ke sini (belum dipotong).
    if on_mulai is not None:
        on_mulai()

    # Pra-panen (31 Okt 2026): bila dari_snapshot, refs bab WAJIB
    # sudah diisi on_mulai ke refs_holder (pemotong plus panen).
    # Kosong = gagal cepat, tanpa fallback, supaya buku tidak
    # ditulis dengan referensi campur aduk.
    refs_per_bab = None
    if dari_snapshot:
        if isinstance(refs_holder, dict) and refs_holder.get("refs"):
            refs_per_bab = refs_holder["refs"]
        else:
            raise ValueError(
                "Snapshot referensi hilang, gagal cepat tanpa fallback")

    if keluar_dir is None:
        raise ValueError("keluar_dir wajib — hasil harus jadi BERKAS, "
                         "bukan cuma di memori (anti-rugi: tekan Back "
                         "tidak menghilangkan hasil)")
    os.makedirs(keluar_dir, exist_ok=True)
    os.makedirs(os.path.join(keluar_dir, "visual"), exist_ok=True)

    # ── SETEL GLOBAL PIPELINE untuk buku INI (bukan mesin baru) ──────────
    P.OUT_DIR = keluar_dir
    P.CKPT_FILE = os.path.join(keluar_dir, "checkpoint.json")
    P.OUTLINE = {k: outline[k] for k in nomor}
    teks_outline = OB.ke_teks(outline)

    #  Outline disuntik ke prompt lewat parameter, bukan variabel global:
    #  `architect_prompt(outline=...)` sudah menerima ini (18 Okt 2026).
    def _architect(*a, **kw):
        kw.setdefault("outline", teks_outline)
        kw.setdefault("jenis", jenis)
        return _architect_asli(*a, **kw)

    _architect_asli = P.architect_prompt
    P.architect_prompt = _architect
    _ASLI_ARSITEK_TERSIMPAN = _architect_asli

    ckpt = {"judul": judul, "jenis": jenis, "babs": {}}
    if ulang and os.path.exists(P.CKPT_FILE):
        try:
            import json
            ckpt = json.load(open(P.CKPT_FILE))
            ckpt.setdefault("babs", {})
        except Exception:
            pass

    t0 = time.time()
    hasil_bab = {}
    ringkasan = ""
    total_kata = total_sitasi = 0
    target = nomor[:batas_bab] if batas_bab else nomor

    # ── LAPIS 3a+3b: BAB DIKERJAKAN BERSAMAAN (maks `_BATAS_BAB`) ────────
    def _kerjakan_satu_bab(n, ckpt_bab, ringkasan_awal):
        """Kerjakan SATU bab dengan global miliknya sendiri.

        Dipanggil dari utas terpisah. Kunci global dipakai supaya hanya satu
        bab yang menyetel `P.OUT_DIR`/`P.CKPT_FILE`/`P.VISUAL_DIR` pada satu
        waktu. Hasilnya dikembalikan sebagai dict — TIDAK menulis ke `ckpt`
        bersama, supaya tidak ada balapan penulisan.

        PENTING: `prev_summary` (ringkasan bab sebelumnya) TIDAK tersedia saat
        bersamaan. Penggantinya = judul bab + poin kunci outline, yang SUDAH
        ada di `outline[n]`. Ini penurunan mutu yang HARUS diuji, bukan
        diabaikan (lihat RANCANGAN_LAPIS3 §3b).
        """
        lama = ckpt_bab.get(str(n)) or {}
        if lama.get("status") == "done" and lama.get("words", 0) > 0:
            return {"n": n, "dilewati": True, "kata": lama.get("words", 0),
                    "sitasi": lama.get("citations", 0),
                    "file": lama.get("file"), "summary": lama.get("summary", ""),
                    "judul": outline[n]["title"]}

        #  Folder kerja per bab (Lapis 3a) — TIDAK bertabrakan karena
        #  `P.OUT_DIR`/`P.VISUAL_DIR`/`P.CKPT_FILE` sudah sadar-utas.
        dir_bab = os.path.join(keluar_dir, f"bab{n}")
        os.makedirs(os.path.join(dir_bab, "visual"), exist_ok=True)

        #  Daftarkan folder MILIK UTAS INI. Semua pemakaian OUT_DIR di dalam
        #  `generate_bab` otomatis mengarah ke sini. NOL kunci ⇒ bab lain
        #  tetap berjalan bersamaan.
        P.folder_bab(dir_bab)
        try:
            if lapor:
                lapor(f"BAB {n} mulai: {outline[n]['title']}")
            # Snapshot hanya bila dari_snapshot True. Bila False,
            # panggil dengan argumen lama persis, supaya mock dan
            # pemanggil lama yang signature-nya lama tidak gagal
            # TypeError karena kwargs baru (gerbang perbaikan bab).
            if dari_snapshot:
                # Gas 31 Okt 2026 12:03, butir 1: baris snapshot
                # bab ini dioper ke pipeline, supaya gerbang per
                # subbab memakai baris DB yang sama dengan gerbang
                # final, bukan turunan refs yang bisa berbeda arah
                # kunci dan alias. Fallback TypeError untuk mock
                # lama yang signature-nya belum mengenal
                # snapshot_rows, pipeline menurunkan baris dari
                # refs bila kwarg tidak sampai.
                _rows_bab = None
                if isinstance(refs_holder, dict):
                    _rows_bab = (refs_holder.get("snapshot_rows") or {}).get(n)
                try:
                    teks, summ, wc, cit = P.generate_bab(
                        n, outline[n], ringkasan_awal, jenis=jenis, tier=tier,
                        refs_bab=(refs_per_bab.get(n) if isinstance(refs_per_bab, dict) else None),
                        dari_snapshot=True, snapshot_rows=_rows_bab)
                except TypeError:
                    teks, summ, wc, cit = P.generate_bab(
                        n, outline[n], ringkasan_awal, jenis=jenis, tier=tier,
                        refs_bab=(refs_per_bab.get(n) if isinstance(refs_per_bab, dict) else None),
                        dari_snapshot=True)
            else:
                teks, summ, wc, cit = P.generate_bab(
                    n, outline[n], ringkasan_awal, jenis=jenis, tier=tier)
        finally:
            P.lepas_folder()
        #  ⚠️ PENJAGA: bab kosong TIDAK boleh dicatat "done".
        if not teks or wc < 50:
            raise RuntimeError(
                f"BAB {n} menghasilkan {wc} kata — terlalu sedikit, "
                "dianggap GAGAL (bukan selesai)")
        #  ┌─ 19 Okt 2026 (TEMUAN BESAR) ─────────────────────────────────────
        #  🔴 `bab{n}.txt` TIDAK PERNAH DITULIS di sini. Akibatnya:
        #     • `isi_bab` di pemeriksa mutu KOSONG ⇒ pemeriksaan mutu
        #       DILEWATI DIAM-DIAM dan buku berulang dilaporkan "lolos"
        #     • laporan "hasil ada di disk" tidak benar untuk bab
        #  Sekarang ditulis SEBELUM bab dinyatakan selesai.
        #  └──────────────────────────────────────────────────────────────────
        berkas = os.path.join(dir_bab, f"bab{n}.txt")
        with open(berkas, "w", encoding="utf-8") as fh:
            fh.write(teks)
        return {"n": n, "kata": wc, "sitasi": cit, "summary": summ,
                "judul": outline[n]["title"], "folder": dir_bab,
                "berkas": berkas}

    gagal = {}
    _galat_gerbang = None  # GagalSubbab pertama, diteruskan apa adanya
    cek_bab = {}  # point 3: hasil cek awal per bab (R3/R4/surname)
    try:
        pekerjaan = []
        for n in target:
            lama = ckpt["babs"].get(str(n)) or {}
            if lama.get("status") == "done" and lama.get("words", 0) > 0:
                if lapor:
                    lapor(f"BAB {n} sudah ada — dilewati")
                hasil_bab[n] = {"kata": lama.get("words", 0),
                                "sitasi": lama.get("citations", 0),
                                "file": lama.get("file"), "dilewati": True}
                total_kata += lama.get("words", 0)
                total_sitasi += lama.get("citations", 0)

                if on_bab_selesai is not None:
                    _f_lewat = os.path.join(keluar_dir, f"bab{n}", f"bab{n}.txt")
                    if os.path.exists(_f_lewat):
                        try:
                            _cek_bab_hasil = on_bab_selesai(
                                n, open(_f_lewat, encoding="utf-8").read(),
                                os.path.join(keluar_dir, f"bab{n}"))
                            cek_bab[n] = {
                                "masalah": list(_cek_bab_hasil.get("masalah") or []),
                                "curiga": list(_cek_bab_hasil.get("curiga") or []),
                            }
                        except Exception as _e_cek:  # noqa: BLE001
                            if lapor:
                                lapor(f"Cek awal BAB {n} dilewati: {_e_cek}")
                continue
            #  Ganti `prev_summary` dengan JANGKAR dari outline.
            #  ⚠️ JEBAKAN 19 Okt: outline TIDAK punya kunci `points`.
            #     Bentuknya: {1: {'title': ..., 'subs': [(nomor, judul,
            #     key_points), ...]}} — lihat `outline_buku.py:39,147`.
            #     Kalau salah kunci, jangkarnya jadi string kosong ⇒ bab 2
            #     tidak tahu apa pun tentang bab 1 (mutu rusak diam-diam).
            subs = outline[n].get("subs") or []
            poin = '; '.join(f'{s[1]}' for s in subs[:5])
            jangkar = (f"Ini buku berbab-bab. Bab ini: {outline[n]['title']}. "
                       f"Sub-bab yang dibahas: {poin}.")
            pekerjaan.append((n, jangkar))

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=_BATAS_BAB) as ex:
            futs = {ex.submit(_kerjakan_satu_bab, n, ckpt["babs"], jangkar): n
                    for n, jangkar in pekerjaan}
            for f in futs:
                n = futs[f]
                try:
                    r = f.result()
                except Exception as e:                     # noqa: BLE001
                    # Gas 31 Okt 2026 12:03, butir 1 dan 3: gagal
                    # gerbang subbab TIDAK boleh dibungkus menjadi
                    # RuntimeError umum yang di-retry A1. Simpan
                    # apa adanya, laporkan, bab lain tetap ditunggu
                    # sampai selesai, lalu raise di bawah sebelum
                    # cek gagal umum, supaya susun() melihat
                    # ValueError dan langsung refund tanpa retry.
                    if type(e).__name__ == "GagalSubbab":
                        if _galat_gerbang is None:
                            _galat_gerbang = e
                        if lapor:
                            lapor(f"BAB {n} GAGAL gerbang subbab: {e}")
                        continue
                    gagal[n] = f"{type(e).__name__}: {e}"
                    if lapor:
                        lapor(f"BAB {n} GAGAL — {gagal[n]}")
                    continue
                if r.get("dilewati"):
                    continue
                #  ⚠️ `ckpt` ditulis dari UTAS UTAMA saat bab LAIN masih
                #  berjalan. Tanpa kunci, dua bab bisa menulis checkpoint
                #  bersamaan ⇒ berkas rusak / bab hilang dari catatan.
                with _ambil_kunci():
                    ckpt["babs"][str(n)] = {
                        "status": "done", "title": r["judul"],
                        "words": r["kata"], "citations": r["sitasi"],
                        "summary": r["summary"],
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "file": f"bab{n}.txt",
                    }
                    import json
                    #  Checkpoint buku ditulis di folder INDUK (bukan folder
                    #  bab) supaya semua bab tercatat di satu tempat.
                    berkas_ckpt = os.path.join(keluar_dir, "checkpoint.json")
                    json.dump(ckpt, open(berkas_ckpt, "w"),
                              ensure_ascii=False, indent=1)
                hasil_bab[n] = {"kata": r["kata"], "sitasi": r["sitasi"],
                                "file": f"bab{n}.txt"}
                total_kata += r["kata"]
                total_sitasi += r["sitasi"]
                if lapor:
                    lapor(f"BAB {n} selesai: {r['kata']} kata, "
                          f"{r['sitasi']} sitasi")

                if on_bab_selesai is not None:
                    try:
                        _teks_bab = open(os.path.join(
                            keluar_dir, f"bab{n}", f"bab{n}.txt"),
                            encoding="utf-8").read()
                        _cek_bab_hasil = on_bab_selesai(
                            n, _teks_bab,
                            os.path.join(keluar_dir, f"bab{n}"))
                        cek_bab[n] = {
                            "masalah": list(_cek_bab_hasil.get("masalah") or []),
                            "curiga": list(_cek_bab_hasil.get("curiga") or []),
                        }
                    except Exception as _e_cek:  # noqa: BLE001
                        if lapor:
                            lapor(f"Cek awal BAB {n} dilewati: {_e_cek}")
    finally:
        #  Pemulihan tambalan prompt TIDAK di sini lagi: bedah
        #  struktural (di bawah) masih butuh wrapper outline.
        #  Pemulihan dilakukan wrapper antrean di `finally`-nya
        #  (mencakup SEMUA jalan keluar), supaya bab bedah tidak
        #  jatuh ke outline Ekonomi Digital sementara.
        pass

    if _galat_gerbang is not None:
        # Gagal gerbang subbab diteruskan apa adanya (ValueError),
        # supaya susun() tidak me-retry dan langsung refund dengan
        # galat detail bab dan subbab. Bab lain yang sudah jadi
        # tetap tersimpan di disk sebagai audit, token kembali.
        raise _galat_gerbang

    if gagal:
        #  JANGAN pura-pura selesai. Bab yang gagal dilaporkan apa adanya.
        ringkas_gagal = ", ".join(f"BAB {k}" for k in sorted(gagal))
        raise RuntimeError(
            f"{ringkas_gagal} TIDAK LOLOS: {gagal}. "
            f"Bab yang jadi: {sorted(hasil_bab)}")

    # ── LAPIS 3c: PERIKSA MUTU ISI sebelum dinyatakan selesai ─────────────
    #  Sejak bab dikerjakan bersamaan, isi antarbab BISA berulang. Tanpa
    #  pemeriksaan ini, buku berulang dilaporkan "selesai" — kerusakan SUNYI.
    import mutu_isi_buku as MI
    isi_bab = {}
    for n in sorted(hasil_bab):
        f = os.path.join(keluar_dir, f"bab{n}", f"bab{n}.txt")
        if os.path.exists(f):
            isi_bab[n] = open(f, encoding='utf-8').read()
    periksa = {'lolos': True, 'masalah': [], 'curiga': []}
    if isi_bab:
        periksa = MI.periksa_buku(isi_bab, outline)

        #  Cek awal point 3: gabungkan masalah/curiga per bab (R3/R4/
        #  surname) SEBELUM putaran perbaikan, supaya bab-bab itu ikut
        #  diperbaiki (bab_bermasalah membaca teks 'BAB N: ...').
        for _n in sorted(cek_bab):
            for _m in cek_bab[_n].get('masalah') or []:
                if _m not in periksa['masalah']:
                    periksa['masalah'].append(_m)
            for _c in cek_bab[_n].get('curiga') or []:
                if _c not in periksa['curiga']:
                    periksa['curiga'].append(_c)
        periksa['lolos'] = not periksa['masalah']
        if lapor:
            lapor(MI.ringkas(periksa))
        for c in periksa['curiga'][:3]:
            if lapor:
                lapor(f'Catatan: {c}')

        # -- BEDAH STRUKTURAL SEKALI (Gas Bos 31 Okt 2026 12:03, butir 2) --
        #  Pengganti Lapis 3c-2 yang dihapus: tidak ada lagi tulis
        #  ulang penuh satu bab. Hanya celah struktural (tabel R3
        #  hilang atau kalimat posisi R4 hilang atau terlalu pendek)
        #  yang diperbaiki, dengan SATU sisipan kecil per celah,
        #  dicek deterministik. Sisipan gagal cek, LLM tidak menjawab,
        #  atau sitasi sisipan tidak cocok snapshot, maka sisipan
        #  dibuang saja dan bab lama dipertahankan, tanpa putaran
        #  kedua dan tanpa tulis ulang penuh. Bila tidak ada celah,
        #  tidak ada perbaikan sama sekali. Hanya buku-referensi.
        #  Batas: tabel disisipkan ke subbab N.3, posisi ke N.4.
        #  Proksi R3 di cek_awal membaca berkas visual, bukan teks
        #  bab, jadi sesudah tabel masuk ke teks bab, masalah R3
        #  dihapus eksplisit di sini dengan catatan bahwa tabel
        #  kini ada di teks bab dan akan dirakit ke DOCX. Proksi
        #  R4 membaca teks bab, jadi posisi baru akan lolos bila
        #  cek diulang, tetapi masalahnya tetap dihapus eksplisit
        #  di sini supaya laporan akhir konsisten.
        #  Baris snapshot per bab untuk cek sitasi sisipan: dari
        #  holder bila ada (otoritatif dari DB), bila tidak ada
        #  diturunkan dari refs, bila keduanya tidak ada maka
        #  sitasi formal apa pun di sisipan dianggap tidak aman
        #  dan sisipan dibuang (fail-closed).
        if jenis == "referensi":
            _rows_bedah_per_bab = {}
            if isinstance(refs_holder, dict) and refs_holder.get("snapshot_rows"):
                _rows_bedah_per_bab = refs_holder.get("snapshot_rows") or {}
            elif dari_snapshot and isinstance(refs_per_bab, dict):
                try:
                    from app.gerbang_subbab import rows_dari_refs_dicts as _rows_dari
                    for _nb in refs_per_bab:
                        _rows_bedah_per_bab[_nb] = _rows_dari(
                            refs_per_bab.get(_nb) or [])
                except Exception:
                    _rows_bedah_per_bab = {}
            for _n_bedah in sorted(isi_bab):
                _celah = _celah_struktural(
                    (cek_bab.get(_n_bedah) or {}).get("masalah") or [],
                    (cek_bab.get(_n_bedah) or {}).get("curiga") or [])
                if not (_celah["tabel"] or _celah["posisi"]):
                    continue
                _teks_lama = isi_bab[_n_bedah]
                if not isinstance(_teks_lama, str):
                    # Penjaga None job 221: teks bab bukan string
                    # diperlakukan sebagai celah yang tidak bisa
                    # dibedah, bukan crash AttributeError.
                    if lapor:
                        lapor(f"Bedah struktural BAB {_n_bedah} dilewati: "
                              f"teks bab bukan string")
                    continue
                _teks_bedah = _teks_lama
                _diterima = []
                _dibuang = []
                for _jenis_celah, _nomor_sub in (
                        ("tabel", 3), ("posisi", 4)):
                    if not _celah[_jenis_celah]:
                        continue
                    _sisipan = None
                    _alasan_buang = None
                    for _percobaan_bedah in range(1, _BEDAH_MAKS + 1):
                        try:
                            _judul_bedah = (outline[_n_bedah].get("title") or "")
                            if _jenis_celah == "tabel":
                                _prompt_bedah = (
                                    f"Buat SATU blok tabel komparasi untuk "
                                    f"Bab {_n_bedah} buku ini, judul bab: "
                                    f"{_judul_bedah}. Format persis: "
                                    f"[TABEL {_n_bedah}.1: Judul Tabel - Kolom A, "
                                    f"Kolom B, Kolom C | Baris1: ..., ..., ... | "
                                    f"Baris2: ..., ..., ... | Baris3: ..., ..., ...]. "
                                    f"Isi dengan perbandingan teori yang SUDAH "
                                    f"dibahas di bab ini, jangan menambah sitasi "
                                    f"baru, jangan menambah klaim baru, hanya "
                                    f"rangkum perbandingan yang ada. Keluarkan "
                                    f"HANYA blok tabel, tanpa kalimat lain.")
                            else:
                                _prompt_bedah = (
                                    f"Buat SATU kalimat posisi penulis untuk "
                                    f"Bab {_n_bedah} buku ini, judul bab: "
                                    f"{_judul_bedah}, minimal 10 kata, diawali "
                                    f"dengan frasa 'Penulis berpendapat' atau "
                                    f"'Menurut penulis', yang merangkum posisi "
                                    f"penulis atas perbandingan di bab ini, "
                                    f"tanpa sitasi baru, tanpa klaim baru. "
                                    f"Keluarkan HANYA kalimat itu.")
                            _sisipan = P.call_llm(_prompt_bedah, max_tokens=800)
                        except Exception as _e_bedah:
                            _sisipan = None
                            _alasan_buang = (
                                f"LLM gagal: {type(_e_bedah).__name__}")
                        break
                    if _sisipan is None or not str(_sisipan).strip():
                        _alasan_buang = _alasan_buang or "LLM tidak menjawab"
                    elif _jenis_celah == "tabel" and not _cek_sisipan_tabel(_sisipan):
                        _alasan_buang = "gagal cek tabel"
                    elif _jenis_celah == "posisi" and not _cek_sisipan_posisi(_sisipan):
                        _alasan_buang = "gagal cek posisi"
                    elif not _sisipan_aman_sitasi(
                            _sisipan,
                            _rows_bedah_per_bab.get(_n_bedah)):
                        _alasan_buang = "sitasi tidak cocok snapshot"
                    if _alasan_buang:
                        _dibuang.append((_jenis_celah, _alasan_buang))
                        continue
                    _teks_bedah = _sisip_ke_subbab(
                        _teks_bedah, _n_bedah, _nomor_sub, _sisipan)
                    _diterima.append(_jenis_celah)
                if _diterima:
                    _berkas_bedah = os.path.join(
                        keluar_dir, f"bab{_n_bedah}", f"bab{_n_bedah}.txt")
                    with open(_berkas_bedah, "w", encoding="utf-8") as _fh:
                        _fh.write(_teks_bedah)
                    isi_bab[_n_bedah] = _teks_bedah
                    if _n_bedah in hasil_bab:
                        hasil_bab[_n_bedah]["kata"] = len(_teks_bedah.split())
                    if "tabel" in _diterima:
                        periksa["masalah"] = [
                            m for m in periksa["masalah"]
                            if not (str(m).startswith(f"BAB {_n_bedah}:")
                                    and "tidak ada tabel" in str(m))]
                        if _n_bedah in cek_bab:
                            cek_bab[_n_bedah]["masalah"] = [
                                m for m in cek_bab[_n_bedah]["masalah"]
                                if "tidak ada tabel" not in str(m)]
                    if "posisi" in _diterima:
                        periksa["masalah"] = [
                            m for m in periksa["masalah"]
                            if not (str(m).startswith(f"BAB {_n_bedah}:")
                                    and "tidak ada kalimat posisi" in str(m))]
                        periksa["curiga"] = [
                            c for c in periksa["curiga"]
                            if not (str(c).startswith(f"BAB {_n_bedah}:")
                                    and "kalimat posisi penulis terlalu pendek" in str(c))]
                        if _n_bedah in cek_bab:
                            cek_bab[_n_bedah]["masalah"] = [
                                m for m in cek_bab[_n_bedah]["masalah"]
                                if "tidak ada kalimat posisi" not in str(m)]
                            cek_bab[_n_bedah]["curiga"] = [
                                c for c in cek_bab[_n_bedah]["curiga"]
                                if "kalimat posisi penulis terlalu pendek" not in str(c)]
                    periksa["lolos"] = not periksa["masalah"]
                    if lapor:
                        lapor(f"Bedah struktural BAB {_n_bedah}: sisipan "
                              f"{' dan '.join(_diterima)} diterima")
                for _jenis_buang, _alasan_buang in _dibuang:
                    if lapor:
                        lapor(f"Bedah struktural BAB {_n_bedah}: sisipan "
                              f"{_jenis_buang} dibuang, {_alasan_buang}")

    #  Total kata dihitung ULANG dari isi final (bisa berubah karena bedah).
    #  Penjaga None job 221: nilai bukan string dilewati, bukan crash.
    if isi_bab:
        total_kata = sum(len(t.split()) for t in isi_bab.values()
                         if isinstance(t, str))
        for n, t in isi_bab.items():
            if n in hasil_bab and isinstance(t, str):
                hasil_bab[n]["kata"] = len(t.split())

    return {
        "ok": True,
        "judul": judul,
        "jenis": jenis,
        "bab": hasil_bab,
        "bab_selesai": len(hasil_bab),
        "mutu_lolos": periksa['lolos'],
        "mutu_masalah": periksa['masalah'],
        "mutu_curiga": periksa['curiga'],
        "total_kata": total_kata,
        "total_sitasi": total_sitasi,
        "detik": round(time.time() - t0, 1),
        "folder": keluar_dir,
        "sumber": SUMBER,
    }
