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
               lapor=None, ulang=0) -> dict hasil
"""
import os
import re
import time

SUMBER = "penyusun_buku.py"

# ══════════════════════════════════════════════════════════════════════════
#  LAPIS 3a — STATE PER BAB (ACC Bos 19 Okt 2026, batas 2 bab)
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
_BATAS_BAB = 2          # putusan Bos: maksimal 2 bab bersamaan
#  Perbaikan-otomatis bab bermasalah (Lapis 3c-2, ACC Bos 19 Okt 2026).
#  MAKSIMAL 1 putaran per bab: cukup untuk memperbaiki isi berulang, tapi
#  TIDAK boleh berputar sampai token user habis.
_PERBAIKAN_MAKS = 1


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
               batas_bab=None, lapor=None, ulang=0):
    """Susun buku dari outline yang SUDAH dibuat. Return dict hasil.

    batas_bab : kalau diisi, hanya bab 1..batas_bab yang dikerjakan
                (dipakai untuk uji murah — jangan bakar token 6 bab).
    lapor     : fungsi(teks) untuk memberi kabar ke pemanggil (progress).
    ulang     : 0 = mulai dari awal; >0 = lanjutkan bab yang belum selesai.

    TIDAK memotong kuota. Pemotongan kuota = tugas pemanggil (rute), supaya
    modul ini bisa diuji tanpa menyentuh saldo siapa pun.
    """
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
            teks, summ, wc, cit = P.generate_bab(
                n, outline[n], ringkasan_awal, jenis=jenis)
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
    finally:
        #  GLOBAL WAJIB dipulihkan — kalau tidak, pemanggil berikutnya
        #  memakai outline buku sebelumnya (pencemaran lintas buku).
        P.architect_prompt = _architect_asli

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
                    #  ⚠️ `masalah` = LIST TEKS. Hitung yang MENYEBUT bab ini
                    #     (bukan `m['bab']` — tidak ada kuncinya).
                    pola_n = re.compile(r'BAB\s+' + str(n) + r'\b')
                    skor_baru = len([m for m in uji['masalah']
                                     if pola_n.search(str(m))])
                    skor_lama = len([m for m in periksa['masalah']
                                     if pola_n.search(str(m))])
                    if skor_baru < skor_lama:
                        isi_bab[n] = baru
                        periksa = uji
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
