"""Pra-panen referensi Fase 1 (31 Okt 2026, Gas Boss 31 Okt 00:01).

Tujuan: sebelum bab 1 ditulis, semua bab sudah punya daftar referensi
BEKU di database, dari SATU sumber yang sama untuk penulis, Skeptic,
Editor, pemeriksa sitasi, dan pustaka. Ini menutup cacat job 223: daftar
yang dipakai menulis berbeda dengan daftar yang dipakai memeriksa
(15 surname saat cek, 5 surname di berkas akhir), karena panen lama
menempel di tiap sub-bab, menumpuk per sub-bab, dan tidak pernah
dibekukan.

Prinsip:
  1. Panen dulu, tulis belakangan. Panen berjalan di dalam job latar,
     sesudah token dipotong (lewat on_mulai di susun(), supaya refund
     tetap jujur), sebelum bab 1 ditulis.
  2. Parse deterministik, tanpa LLM. Nama penulis diparse dari JSON API
     menjadi surname_key plus alias, SEKALI saat panen, bukan diparse
     ulang dari string format APA saat memeriksa. LLM hanya dipakai
     untuk kata kunci Inggris oleh helper panen yang sudah ada, bukan
     untuk parsing atau identifikasi.
  3. Satu sumber beku. Penulis membaca snapshot_job (bukan cache hidup,
     bukan panen on demand). Sesudah snapshot ditulis, tidak ada tulis
     lagi selama job berjalan. Job baru menyalin cache ke snapshot baru
     lalu membekukan, tidak membaca cache hidup selama menulis.
  4. Gagal cepat. Bab di bawah minimum 8 referensi menghentikan job
     sebelum bab 1, lewat jalur refund yang sudah ada, dengan pesan
     manusia yang menyebut semua bab yang gagal.

KEBIJAKAN RETENSI (putusan Boss 30 Okt 2026, DB tidak dihapus):
  Artikel dedup disimpan selamanya sebagai pustaka EduAi. Snapshot job
  dipertahankan 90 hari untuk audit dan rakit ulang, lalu hapus baris
  join-nya saja (artikel tetap). Penghapusan itu adalah KEBIJAKAN,
  bukan kode hapus otomatis di Fase 1. Pekerjaan lanjutan: skrip prune
  snapshot 90 hari, dijalankan terpisah, bukan di jalur produksi.

Batas Fase 1:
  Hanya buku-referensi. Tier, Gate 1, struktur DOCX, dan mekanisme
  token atau refund yang sudah ada tidak diubah, kecuali penambahan
  gerbang pra-panen yang memakai jalur refund yang sudah ada.
  Tidak ada Jev untuk identifikasi sitasi (deterministik saja).
  Timeout per sumber 30 detik sudah dipenuhi fungsi pustaka yang
  dipakai (cari_scopus, cari_openalex, cari_garuda, cari_crossref
  semuanya memakai timeout=30), jadi tidak ada kode timeout baru.
"""

import json
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone

try:
    from .models import Artikel, CacheTopik, SnapshotJob
except ImportError:  # dipakai sebagai modul atas, bukan paket app
    from models import Artikel, CacheTopik, SnapshotJob

try:
    from .prioritas_sumber import pilih_seimbang as _pilih_seimbang
except ImportError:  # jalur cache tetap jalan urutan lama bila gagal
    try:
        from prioritas_sumber import pilih_seimbang as _pilih_seimbang
    except ImportError:
        _pilih_seimbang = None

MIN_REFERENSI_PER_BAB = 8
CACHE_SEGAR_HARI = 365  # 12 bulan
PARALEL_MAKS = 4
TIMEOUT_PER_SUMBER_DETIK = 30  # sudah dipakai pustaka.py, lihat atas


def _now():
    return datetime.now(timezone.utc)


class GagalPraPanen(ValueError):
    """Gagal gerbang pra-panen. Subclass ValueError supaya loop retry
    di susun() TIDAK mengulanginya (galat validasi, bukan galat
    teknis). Pesan manusia menyebut semua bab yang gagal dan memuat
    frasa Token sudah kembali, supaya cabang gagal di template dan JS
    menampilkan pesan bersih (perbaikan tampilan gagal 163908-sot).
    """

    def __init__(self, gagal):
        # gagal: list (bab, judul_bab, jumlah)
        self.gagal = list(gagal or [])
        bagian = []
        for bab, judul_bab, jumlah in self.gagal:
            bagian.append(
                "Bab %s (%s) hanya menemukan %s referensi (minimal %s)"
                % (bab, judul_bab or "", jumlah, MIN_REFERENSI_PER_BAB))
        pesan = (
            "Maaf, buku belum berhasil dibuat. "
            + "; ".join(bagian)
            + ". Coba ubah judul bab atau bidang, lalu pesan lagi. "
            "Token sudah kembali ke saldo.")
        super().__init__(pesan)


def normalisasi_teks(teks):
    """Lipat diakritik, huruf kecil, rapikan spasi.

    Contoh: Dabic dengan aksen menjadi dabic, LUHUR menjadi luhur.
    Dipakai untuk kunci cache, judul_normal, surname_key, dan alias,
    supaya pencocokan tidak gagal hanya karena aksen atau huruf besar.
    """
    if not teks:
        return ""
    bentuk = unicodedata.normalize("NFKD", str(teks))
    tanpa_aksen = "".join(
        c for c in bentuk if not unicodedata.combining(c))
    tanpa_aksen = tanpa_aksen.strip().strip(".,;:!?\"'()[]{}")
    return re.sub(r"\s+", " ", tanpa_aksen.lower()).strip()


def _bersihkan_token(tok):
    return (tok or "").strip().strip(".,;:!?\"'()[]{}")


def _adalah_inisial_token(tok):
    """Token inisial saja: satu huruf, atau sampai 4 huruf besar.

    Contoh: M, T.S. (menjadi TS), RPIR. Dipakai untuk memilih surname
    yang benar dari nama seperti Prasanna RPIR (surname Prasanna,
    bukan RPIR) dan untuk melewati referensi yang surname-nya hanya
    inisial (tidak bisa dikutip dengan benar, jadi tidak dihitung).
    """
    bersih = _bersihkan_token(tok).replace(".", "")
    if not bersih:
        return False
    if len(bersih) == 1:
        return True
    return len(bersih) <= 4 and bersih.isupper() and bersih.isalpha()


def parse_ref_ke_artikel(ref):
    """Parse SATU dict referensi API menjadi baris artikel terstruktur.

    Return dict artikel (siap simpan) atau None bila tidak layak
    dikutip (tanpa judul, tanpa tahun, atau surname hanya inisial).
    Deterministik, tanpa LLM. Bentuk ref yang diterima: dict panen
    (authors list, year int) dan dict fallback verifikasi (authors
    string atau list, year int atau string).
    """
    if not isinstance(ref, dict):
        return None
    judul = (ref.get("title") or "").strip()
    if not judul:
        return None
    try:
        tahun = int(ref.get("year") or 0)
    except (TypeError, ValueError):
        tahun = 0
    if not tahun:
        return None
    authors = ref.get("authors") or []
    if isinstance(authors, str):
        authors = [x.strip() for x in authors.split(",") if x.strip()]
    authors = [str(a).strip() for a in authors if str(a).strip()]
    if not authors:
        return None
    pertama = authors[0]
    if "," in pertama:
        # Bentuk Marga, Nama (satu entri mengandung koma).
        surname_raw = _bersihkan_token(pertama.split(",", 1)[0])
    else:
        kata = [_bersihkan_token(k) for k in pertama.split() if _bersihkan_token(k)]
        if not kata:
            return None
        if _adalah_inisial_token(kata[-1]) and len(kata) >= 2:
            # Nama terbalik dengan inisial di akhir, contoh Prasanna
            # RPIR: surname adalah kata pertama yang bukan inisial.
            surname_raw = ""
            for k in kata:
                if not _adalah_inisial_token(k):
                    surname_raw = k
                    break
            if not surname_raw:
                return None
        else:
            surname_raw = kata[-1]
    if _adalah_inisial_token(surname_raw):
        return None
    surname_key = normalisasi_teks(surname_raw)
    if not surname_key:
        return None
    alias_set = set()
    for penulis in authors:
        for tok in re.split(r"[\s,]+", penulis):
            tok_bersih = normalisasi_teks(tok)
            if tok_bersih and tok_bersih != surname_key:
                alias_set.add(tok_bersih)
    doi = (ref.get("doi") or "").strip().lower()
    penulis_json = {
        "authors": authors,
        "surname_key": surname_key,
        "surname_tampil": surname_raw,
        "alias": sorted(alias_set),
    }
    return {
        "doi": doi,
        "judul": judul,
        "judul_normal": normalisasi_teks(judul),
        "tahun": tahun,
        "jurnal": (ref.get("journal") or "").strip(),
        # Sumber kosong dibiarkan kosong (jujur), bukan dilabel
        # "harvest" (bukan nama sumber nyata). Produksi: 4 sumber
        # pustaka selalu mengisi source, jadi kosong hanya untuk
        # ref degeneratif yang seharusnya tidak lolos parse.
        "sumber": (ref.get("source") or "").strip(),
        "penulis_json": penulis_json,
        "surname_key": surname_key,
        "surname_tampil": surname_raw,
        "alias": sorted(alias_set),
    }


def _pastikan_jalur_modul():
    """Tambah /opt/data dan /app ke sys.path supaya modul akar
    (buku_umum_pipeline, verifikasi_sitasi) bisa diimpor dari app.
    Pola yang sama dengan _pastikan_modul di penyusunan_buku.py.
    """
    import os
    import sys
    for p in ("/opt/data", "/app"):
        if os.path.isdir(p) and p not in sys.path:
            sys.path.insert(0, p)


def panen_satu_bab(judul_bab):
    """Panen SATU bab dari API, tanpa DB, tanpa tulis. Fail-soft.

    Leg 1: _refs_dari_harvest yang sudah ada (4 sumber Scopus,
    OpenAlex, Garuda, CrossRef, kata kunci EN lewat helper yang sudah
    ada). Leg 2 bila leg 1 kosong: search_real_references (n=5),
    sumber asli dipertahankan (OpenAlex/Crossref), label fallback
    hanya bila source kosong, bukan diam-diam. Gagal total: [].
    Kata kunci EN memakai LLM lewat helper yang sudah ada (seperti
    panen hari ini). Parse ke artikel tetap deterministik, tanpa LLM.
    """
    judul_bab = (judul_bab or "").strip()
    if not judul_bab:
        return []
    _pastikan_jalur_modul()
    try:
        import buku_umum_pipeline as _P
        hasil = _P._refs_dari_harvest(judul_bab)
    except Exception:
        hasil = None
    if hasil:
        return list(hasil)
    try:
        from verifikasi_sitasi import search_real_references as _cari
        topik = "%s teori konsep jurnal penelitian" % judul_bab
        hasil2 = _cari(topik, n=5)
    except Exception:
        hasil2 = []
    keluar = []
    for r in (hasil2 or []):
        if isinstance(r, dict):
            salin = dict(r)
            # Pertahankan sumber asli (OpenAlex/Crossref dari
            # search_real_references). Label fallback hanya bila
            # source kosong, supaya sumber nyata tidak hilang.
            salin["source"] = salin.get("source") or "fallback"
            keluar.append(salin)
    return keluar


def _panen_dan_parse(judul_bab):
    """Panen plus parse untuk satu bab. Murni (tanpa DB), aman
    dipanggil dari utas worker. Gagal apa pun: [] (gerbang nanti
    gagal jujur dengan jumlah 0, bukan crash).
    """
    try:
        mentah = panen_satu_bab(judul_bab)
    except Exception:
        return []
    hasil = []
    for r in mentah:
        try:
            parsed = parse_ref_ke_artikel(r)
        except Exception:
            parsed = None
        if parsed:
            hasil.append(parsed)
    return hasil


def cari_cache(db, bidang_norm, judul_norm):
    """Cache topik: list id artikel, atau None bila miss.

    Hit hanya bila cocok persis (bidang plus judul_bab_normal,
    sesudah normalisasi) DAN dipanen kurang dari 12 bulan yang lalu
    DAN daftarnya tidak kosong. Kosong tidak pernah di-cache, supaya
    topik yang dulu kosong selalu dapat kesempatan panen baru.
    """
    if not bidang_norm or not judul_norm:
        return None
    baris = db.query(CacheTopik).filter(
        CacheTopik.bidang == bidang_norm,
        CacheTopik.judul_bab_normal == judul_norm).first()
    if baris is None:
        return None
    if baris.dipanen is None:
        return None
    dipanen = baris.dipanen
    if dipanen.tzinfo is None:
        dipanen = dipanen.replace(tzinfo=timezone.utc)
    if (_now() - dipanen) > timedelta(days=CACHE_SEGAR_HARI):
        return None
    try:
        ids = json.loads(baris.artikel_ids or "[]")
    except Exception:
        return None
    ids = [int(i) for i in ids if isinstance(i, int) or str(i).isdigit()]
    return ids or None


def simpan_cache(db, bidang_norm, judul_norm, artikel_ids):
    """Simpan atau perbarui cache topik. Kosong tidak disimpan.
    Tanpa commit (pemanggil yang commit per bab).
    """
    if not bidang_norm or not judul_norm or not artikel_ids:
        return
    baris = db.query(CacheTopik).filter(
        CacheTopik.bidang == bidang_norm,
        CacheTopik.judul_bab_normal == judul_norm).first()
    isi = json.dumps([int(i) for i in artikel_ids], ensure_ascii=False)
    if baris is None:
        baris = CacheTopik(
            bidang=bidang_norm, judul_bab_normal=judul_norm,
            artikel_ids=isi, dipanen=_now())
        db.add(baris)
    else:
        baris.artikel_ids = isi
        baris.dipanen = _now()


def cari_atau_buat_artikel(db, parsed):
    """Dedup artikel, lalu kembalikan barisnya (tanpa commit).

    Kunci 1: DOI (bila ada, huruf kecil). Kunci 2 (tanpa DOI):
    judul_normal plus tahun plus surname_key (tiga-tiganya harus
    cocok, supaya dua artikel beda yang judulnya sama tidak digabung).
    Baris lama tidak ditimpa (first wins).
    """
    art = None
    doi = (parsed.get("doi") or "").strip()
    if doi:
        art = db.query(Artikel).filter(Artikel.doi == doi).first()
    if art is None:
        art = db.query(Artikel).filter(
            Artikel.judul_normal == parsed["judul_normal"],
            Artikel.tahun == parsed["tahun"],
            Artikel.surname_key == parsed["surname_key"]).first()
    if art is not None:
        return art
    art = Artikel(
        doi=doi or None,
        judul=parsed["judul"],
        judul_normal=parsed["judul_normal"],
        tahun=parsed["tahun"],
        jurnal=parsed.get("jurnal") or "",
        sumber=parsed.get("sumber") or "",
        penulis_json=json.dumps(parsed["penulis_json"], ensure_ascii=False),
        surname_key=parsed["surname_key"],
        dibuat=_now())
    db.add(art)
    db.flush()
    return art


def tulis_snapshot(db, job_kode, bab, items):
    """Tulis snapshot beku satu bab (tanpa commit).

    items: list dict {artikel_id, kunci, surname_tampil, tahun,
    alias, sumber}, urut sesuai urutan snapshot. Idempoten: baris lama
    untuk (job_kode, bab) dihapus dulu, lalu ditulis ulang. Sesudah
    ditulis, tidak ada tulis lagi selama job berjalan.
    """
    db.query(SnapshotJob).filter(
        SnapshotJob.job_kode == job_kode,
        SnapshotJob.bab == bab).delete()
    for urutan, it in enumerate(items, 1):
        baris = SnapshotJob(
            job_kode=job_kode, bab=bab, urutan=urutan,
            artikel_id=int(it["artikel_id"]),
            kunci_sitasi="%s-%s" % (it["kunci"], it["tahun"]),
            surname_tampil=it.get("surname_tampil") or it["kunci"],
            tahun=int(it["tahun"]) if it.get("tahun") else None,
            alias_json=json.dumps(list(it.get("alias") or []),
                                  ensure_ascii=False),
            sumber=it.get("sumber") or "")
        db.add(baris)


def ambil_snapshot(db, job_kode, bab):
    """Baca snapshot beku satu bab, urut. Return list dict.

    Tiap dict: {kunci, alias, tahun, surname_tampil, artikel_id,
    urutan, sumber, ref_dict}. ref_dict adalah dict referensi lengkap
    untuk format_apa dan repair (authors, year, title, journal, doi).
    Bila artikel induk hilang (seharusnya tidak terjadi di Fase 1,
    karena tidak ada hapus otomatis), ref_dict dibuat minimal dari
    kolom snapshot, supaya cakupan tetap bisa dihitung.
    """
    baris_list = db.query(SnapshotJob).filter(
        SnapshotJob.job_kode == job_kode,
        SnapshotJob.bab == bab).order_by(SnapshotJob.urutan).all()
    hasil = []
    for b in baris_list:
        try:
            alias = json.loads(b.alias_json or "[]")
        except Exception:
            alias = []
        kunci = (b.kunci_sitasi or "").rsplit("-", 1)[0] if b.kunci_sitasi else ""
        art = None
        try:
            art = db.get(Artikel, b.artikel_id)
        except Exception:
            art = None
        if art is not None:
            try:
                pj = json.loads(art.penulis_json or "{}")
            except Exception:
                pj = {}
            ref_dict = {
                "authors": pj.get("authors") or [b.surname_tampil or ""],
                "year": art.tahun,
                "title": art.judul,
                "journal": art.jurnal or "",
                "doi": art.doi or "",
                "type": "article",
                "source": b.sumber or art.sumber or "",
            }
        else:
            ref_dict = {
                "authors": [b.surname_tampil or ""],
                "year": b.tahun,
                "title": "",
                "journal": "",
                "doi": "",
                "type": "article",
                "source": b.sumber or "",
            }
        hasil.append({
            "kunci": kunci or normalisasi_teks(b.surname_tampil or ""),
            "alias": [normalisasi_teks(a) for a in alias if a],
            "tahun": str(b.tahun) if b.tahun else "",
            "surname_tampil": b.surname_tampil or "",
            "artikel_id": b.artikel_id,
            "urutan": b.urutan,
            "sumber": b.sumber or "",
            "ref_dict": ref_dict,
        })
    return hasil


def panen_semua(db, job_kode, bidang, outline, lapor=None):
    """Fase pra-panen: panen semua bab, simpan, bekukan, gerbang.

    Dipanggil dari on_mulai di susun() (sesudah token dipotong,
    sebelum bab 1 ditulis). Pekerja API berjalan paralel maks 4 bab
    bersamaan (tanpa DB di worker, supaya sesi SQLAlchemy tidak dipakai
    lintas utas). Tulis DB (artikel, cache, snapshot) hanya di utas
    utama, commit per bab. Lapor tahap jujur: Bab X dari N adalah
    jumlah bab yang sudah selesai dipanen, bukan persen.

    Return dict bab ke list dict referensi (urut snapshot), untuk
    penulisan. Raise GagalPraPanen bila ada bab di bawah minimum 8
    (snapshot sudah ditulis dan di-commit sebelum raise, sebagai
    audit, dan pemanggil mengembalikan token lewat jalur refund).
    """
    babs = sorted(k for k in (outline or {}) if isinstance(k, int))
    if not babs:
        raise ValueError("outline tidak punya bab")
    total = len(babs)
    bidang_norm = normalisasi_teks(bidang or "")
    refs_per_bab = {}
    hitung = {}
    selesai = 0

    def _lapor(teks):
        if lapor:
            try:
                lapor(teks)
            except Exception:
                pass

    _lapor("Menyiapkan referensi (Bab 0 dari %s)" % total)
    perlu_panen = []
    for bab in babs:
        judul_bab = ((outline.get(bab) or {}).get("title") or "")
        judul_norm = normalisasi_teks(judul_bab)
        ids = cari_cache(db, bidang_norm, judul_norm)
        if ids:
            rows = []
            refs = []
            for aid in ids:
                art = db.get(Artikel, aid)
                if art is None:
                    continue
                try:
                    pj = json.loads(art.penulis_json or "{}")
                except Exception:
                    pj = {}
                rows.append({
                    "artikel_id": art.id,
                    "kunci": art.surname_key,
                    "surname_tampil": pj.get("surname_tampil") or art.surname_key,
                    "tahun": art.tahun,
                    "alias": pj.get("alias") or [],
                    "sumber": art.sumber or "",
                })
                refs.append({
                    "authors": pj.get("authors") or [],
                    "year": art.tahun,
                    "title": art.judul,
                    "journal": art.jurnal or "",
                    "doi": art.doi or "",
                    "type": "article",
                    "source": art.sumber or "",
                })
            if rows:
                # Keputusan Bos 31 Okt 2026 19:36, seimbang 2-2-2-2:
                # baris cache diurutkan ulang dengan aturan seimbang
                # yang sama sebelum snapshot ditulis, supaya judul
                # berulang tidak lolos dari seimbang. Pasangan baris
                # dan ref diurutkan bersama, jadi ref yang dikembalikan
                # ke penulisan mengikuti urutan snapshot baru, bukan
                # urutan cache lama. Cache_topik sendiri tidak ditulis
                # ulang, hanya snapshot job baru yang seimbang. Bila
                # helper tidak tersedia, urutan lama dipertahankan
                # (fail-soft, gerbang minimum 8 tetap berlaku).
                if _pilih_seimbang is not None:
                    try:
                        _pasangan = _pilih_seimbang(
                            list(zip(rows, refs)),
                            kunci=lambda _p: _p[0].get('sumber') or '')
                        if _pasangan:
                            rows = [_p[0] for _p in _pasangan]
                            refs = [_p[1] for _p in _pasangan]
                    except Exception:
                        pass
                tulis_snapshot(db, job_kode, bab, rows)
                db.commit()
                refs_per_bab[bab] = refs
                hitung[bab] = len(rows)
                selesai += 1
                _lapor("Menyiapkan referensi (Bab %s dari %s)"
                       % (selesai, total))
                continue
        perlu_panen.append((bab, judul_bab))
    if perlu_panen:
        with ThreadPoolExecutor(max_workers=PARALEL_MAKS) as ex:
            futs = {}
            for bab, judul_bab in perlu_panen:
                futs[ex.submit(_panen_dan_parse, judul_bab)] = (bab, judul_bab)
            for fut in as_completed(futs):
                bab, judul_bab = futs[fut]
                try:
                    parsed_list = fut.result() or []
                except Exception:
                    parsed_list = []
                unik = []
                lihat = set()
                for p in parsed_list:
                    if p.get("doi"):
                        k = "doi:" + p["doi"]
                    else:
                        k = "judul:%s|%s|%s" % (
                            p["judul_normal"], p["tahun"], p["surname_key"])
                    if k in lihat:
                        continue
                    lihat.add(k)
                    unik.append(p)
                rows = []
                refs = []
                for p in unik:
                    art = cari_atau_buat_artikel(db, p)
                    rows.append({
                        "artikel_id": art.id,
                        "kunci": p["surname_key"],
                        "surname_tampil": p["surname_tampil"],
                        "tahun": p["tahun"],
                        "alias": p["alias"],
                        "sumber": p["sumber"],
                    })
                    refs.append({
                        "authors": p["penulis_json"]["authors"],
                        "year": p["tahun"],
                        "title": p["judul"],
                        "journal": p["jurnal"],
                        "doi": p["doi"],
                        "type": "article",
                        "source": p["sumber"],
                    })
                if rows:
                    simpan_cache(db, bidang_norm,
                                 normalisasi_teks(judul_bab),
                                 [r["artikel_id"] for r in rows])
                tulis_snapshot(db, job_kode, bab, rows)
                db.commit()
                refs_per_bab[bab] = refs
                hitung[bab] = len(rows)
                selesai += 1
                _lapor("Menyiapkan referensi (Bab %s dari %s)"
                       % (selesai, total))
    gagal = []
    for bab in babs:
        judul_bab = ((outline.get(bab) or {}).get("title") or "")
        jumlah = hitung.get(bab, 0)
        if jumlah < MIN_REFERENSI_PER_BAB:
            gagal.append((bab, judul_bab, jumlah))
    if gagal:
        raise GagalPraPanen(gagal)
    return refs_per_bab
