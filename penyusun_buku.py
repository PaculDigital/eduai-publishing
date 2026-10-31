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
#  Perbaikan-otomatis bab bermasalah (Lapis 3c-2, ACC Bos 19 Okt 2026).
#  MAKSIMAL 1 putaran per bab: cukup untuk memperbaiki isi berulang, tapi
#  TIDAK boleh berputar sampai token user habis.
_PERBAIKAN_MAKS = 1


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
        #  Pemulihan tambalan prompt TIDAK di sini lagi: putaran PERBAIKAN
        #  (Lapis 3c-2, di bawah) masih butuh wrapper outline. Pemulihan
        #  dilakukan wrapper antrean di `finally`-nya (mencakup SEMUA
        #  jalan keluar) — supaya bab perbaikan tidak jatuh ke outline
        #  Ekonomi Digital sementara.
        pass

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

        # ── LAPIS 3c-2: PERBAIKI SEKALI bab BERMASALAH (ACC Bos 19 Okt) ────
        #  Dulu `mutu_lolos=False` hanya DILAPORKAN. Sekarang bab yang bermasalah
        #  dikerjakan ULANG SEKALI dengan arahan konkret soal apa yang salah,
        #  lalu diperiksa lagi.
        #  Pagar:
        #   • MAKSIMAL 1 putaran per bab (`_PERBAIKAN_MAKS`) — tidak boleh
        #     berputar sampai token habis.
        #   • Hanya bab yang disebut MASALAH; bab yang lolos TIDAK disentuh.
        #   • Kalau hasil perbaikan TIDAK lebih baik, PAKAI VERSI LAMA dan
        #     laporkan jujur — jangan menukar yang lebih baik dengan yang buruk.
        #   • Kuota TIDAK dipotong lagi (perbaikan = tanggung jawab mesin).
        if not periksa['lolos']:
            #  ⚠️ `periksa['masalah']` = LIST TEKS ("BAB 2: ..."), bukan dict.
            #  `bab_bermasalah()` yang membaca nomornya.
            bab_rusak = [n for n in MI.bab_bermasalah(periksa) if n in isi_bab]
            if lapor:
                lapor(f"🔧 Memperbaiki {len(bab_rusak)} bab bermasalah "
                      f"(maksimal {_PERBAIKAN_MAKS} putaran): {bab_rusak}")
            for n in bab_rusak:
                #  Jangkar sama bentuknya dengan loop utama (judul bab +
                #  sub-bab dari outline) — JANGAN mengarang string lain,
                #  nanti bab perbaikan tidak tahu strukturnya.
                subs_n = (outline[n].get("subs") or [])
                poin_n = '; '.join(f'{x[1]}' for x in subs_n[:5])
                jangkar_n = (f"Ini buku berbab-bab. Bab ini: "
                             f"{outline[n]['title']}. Sub-bab yang dibahas: "
                             f"{poin_n}.")
                for putaran in range(1, _PERBAIKAN_MAKS + 1):
                    arahan = MI.arahan_perbaikan(periksa, n)
                    lama = isi_bab[n]
                    try:
                        with ThreadPoolExecutor(max_workers=1) as ex:
                            f = ex.submit(_kerjakan_satu_bab, n, {},
                                          jangkar_n + "\n\n" + arahan)
                            r = f.result()
                    except Exception as e:               # noqa: BLE001
                        if lapor:
                            lapor(f"   BAB {n} perbaikan gagal: "
                                  f"{type(e).__name__}: {e}")
                        break
                    f_baru = os.path.join(keluar_dir, f"bab{n}", f"bab{n}.txt")
                    if not os.path.exists(f_baru):
                        break
                    baru = open(f_baru, encoding='utf-8').read()
                    uji = MI.periksa_buku({**isi_bab, n: baru}, outline)

                    #  Cek awal point 3: nilai ulang cek per bab pada teks
                    #  perbaikan (R3/R4/surname), supaya skor perbaikan
                    #  tidak buta terhadap cek baru.
                    _cek_baru = {'masalah': [], 'curiga': []}
                    if on_bab_selesai is not None:
                        try:
                            _cek_baru = on_bab_selesai(
                                n, baru, os.path.join(keluar_dir, f"bab{n}")) or _cek_baru
                        except Exception as _e_cek2:  # noqa: BLE001
                            if lapor:
                                lapor(f"Cek awal BAB {n} (perbaikan) dilewati: {_e_cek2}")
                    #  ⚠️ `masalah` = LIST TEKS. Hitung yang MENYEBUT bab ini
                    #     (bukan `m['bab']` — tidak ada kuncinya).
                    pola_n = re.compile(r'BAB\s+' + str(n) + r'\b')
                    skor_baru = len([m for m in uji['masalah']
                                     if pola_n.search(str(m))])
                    skor_lama = len([m for m in periksa['masalah']
                                     if pola_n.search(str(m))])
                    skor_baru = skor_baru + len(_cek_baru.get('masalah') or [])
                    if skor_baru < skor_lama:
                        isi_bab[n] = baru
                        periksa = uji

                        #  Periksa diganti uji (MI saja), gabungkan lagi
                        #  cek per bab terbaru supaya sinyal R3/R4/surname
                        #  tidak hilang sesudah perbaikan diterima.
                        cek_bab[n] = {
                            'masalah': list(_cek_baru.get('masalah') or []),
                            'curiga': list(_cek_baru.get('curiga') or []),
                        }
                        for _n2 in sorted(cek_bab):
                            for _m2 in cek_bab[_n2].get('masalah') or []:
                                if _m2 not in periksa['masalah']:
                                    periksa['masalah'].append(_m2)
                            for _c2 in cek_bab[_n2].get('curiga') or []:
                                if _c2 not in periksa['curiga']:
                                    periksa['curiga'].append(_c2)
                        periksa['lolos'] = not periksa['masalah']
                        hasil_bab[n] = {"kata": r["kata"], "sitasi": r["sitasi"],
                                        "file": f"bab{n}.txt",
                                        "diperbaiki": True}
                        if lapor:
                            lapor(f"   ✅ BAB {n} diperbaiki: "
                                  f"{skor_lama} → {skor_baru} masalah")
                    else:
                        #  Perbaikan TIDAK lebih baik → kembalikan versi lama.
                        with open(f_baru, "w", encoding='utf-8') as fh:
                            fh.write(lama)
                        if lapor:
                            lapor(f"   ⚠️ BAB {n} perbaikan TIDAK lebih baik "
                                  f"({skor_lama} → {skor_baru}) — versi LAMA "
                                  f"dipertahankan")
                    break

    #  Total kata dihitung ULANG dari isi final (bisa berubah karena perbaikan).
    if isi_bab:
        total_kata = sum(len(t.split()) for t in isi_bab.values())
        for n, t in isi_bab.items():
            if n in hasil_bab:
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
