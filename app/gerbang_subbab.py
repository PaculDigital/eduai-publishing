"""Gerbang sitasi per subbab (Gas Boss 31 Okt 2026 12:03).

Latar: job 224 membuktikan daftar snapshot beku saja tidak cukup.
Daftar Bab 2 ada 8 baris di DB, prompt Bab 2 sama seperti Bab 3,
tetapi penulis Bab 2 menulis 11 sitasi, semuanya luar daftar, 0
snapshot. Tidak ada yang memeriksa saat menulis, jadi ketidakpatuhan
baru ketahuan di akhir, di gerbang final per bab.

Aturan baru di modul ini, murni deterministik, tanpa LLM:
  1. Satu-satunya daftar yang sah adalah snapshot bab itu dari DB
     (kunci sitasi atau alias, tahun sama). Bentuk sitasi yang
     dihitung adalah bentuk formal kurung atau naratif, sama dengan
     gerbang final di sitasi_anti_gagal. Sitasi inisial saja gagal,
     bukan dihitung.
  2. Syarat lolos subbab: minimal 1 sitasi snapshot formal, dan
     tidak ada sitasi luar daftar yang tersisa sesudah penghapusan
     deterministik sitasi luar, dan tidak ada sitasi inisial saja
     yang tersisa sesudah perbaikan deterministik inisial.
  3. Sitasi luar adalah sitasi formal yang TIDAK SATU PUN surnamenya
     cocok dengan baris snapshot untuk tahun itu. Sitasi dengan
     satu surname snapshot dan satu surname luar tetap dihitung
     snapshot, bukan luar, supaya sitasi sah tidak ikut terhapus
     bersama surname luarnya. Ini sama dengan logika per baris
     gerbang final, yang menghitung per baris, bukan per sitasi.
  4. Penghapusan deterministik hanya menghapus string sitasi luar
     itu sendiri, bukan kalimatnya, bukan klaimnya. Kalimat yang
     kehilangan sitasi tetap ada tanpa sitasi, lebih baik daripada
     sitasi palsu yang dipertahankan.
  5. Perbaikan inisial memakai repair_bab yang sudah ada, hanya
     bila kandidat tepat satu atau konteks menghasilkan tepat satu.
     Ambigu atau tanpa kandidat tidak ditebak, tetap gagal.

Modul ini tidak membaca DB dan tidak memanggil LLM. Pemanggil yang
menyediakan snapshot_rows (dari DB lewat pra_panen.ambil_snapshot,
atau diturunkan dari refs dict lewat rows_dari_refs_dicts).
"""

import re
import unicodedata

try:
    from . import sitasi_anti_gagal as _SG
except ImportError:  # dipakai sebagai modul atas dalam uji tertentu
    import sitasi_anti_gagal as _SG


class GagalSubbab(ValueError):
    """Gagal gerbang per subbab sesudah tulis ulang sekali.

    Subclass ValueError supaya jalur retry di penyusunan_buku.susun
    TIDAK mengulanginya (galat validasi, bukan galat teknis sesaat),
    dan supaya penyusun_buku bisa meneruskannya apa adanya ke
    jalur refund, bukan membungkusnya menjadi RuntimeError umum.
    Pesan memuat bab, subbab, cakupan per baris snapshot, jumlah
    sitasi snapshot, jumlah luar yang dihapus, jumlah inisial sisa,
    dan frasa Token sudah kembali, supaya galat DB dan log memuat
    rincian yang sama tanpa menebak bab mana yang gagal.
    """

    def __init__(self, bab=None, subbab=None, hasil=None):
        hasil = dict(hasil or {})
        self.bab = bab
        self.subbab = subbab
        self.hasil = hasil
        self.cakupan = {
            "total": hasil.get("cakupan_total", 0),
            "cocok_jumlah": hasil.get("cakupan_cocok", 0),
        }
        self.snapshot_ditemukan = hasil.get("snapshot_count", 0)
        self.luar_dihapus = list(hasil.get("luar_dihapus") or [])
        self.inisial_sisa = list(hasil.get("inisial_sisa") or [])
        detail = (
            "Bab %s, subbab %s, cakupan %s dari %s, "
            "sitasi snapshot %s, sitasi luar dihapus %s, "
            "inisial sisa %s"
            % (bab, subbab, self.cakupan["cocok_jumlah"],
               self.cakupan["total"], self.snapshot_ditemukan,
               len(self.luar_dihapus), len(self.inisial_sisa)))
        pesan = (
            "Maaf, buku belum berhasil dibuat. Token sudah kembali "
            "ke saldo. (%s)" % detail)
        super().__init__(pesan)
        self.detail = detail


def _lipat(tok):
    """Lipat diakritik dan huruf kecil untuk satu token nama.

    Sama dengan lipatan di sitasi_anti_gagal dan pra_panen, supaya
    Dabic dengan aksen cocok dengan dabic, dan LUHUR cocok dengan
    luhur, tanpa bergantung pada impor privat.
    """
    if not tok:
        return ""
    bentuk = unicodedata.normalize("NFKD", str(tok))
    tanpa_aksen = "".join(
        c for c in bentuk if not unicodedata.combining(c))
    return tanpa_aksen.strip().strip(".,").lower()


def _bersihkan_token(tok):
    return (tok or "").strip().strip(".,;:!?\"'()[]{}")


def _adalah_inisial_token(tok):
    """Token inisial saja, sama dengan pra_panen.

    Satu huruf, atau sampai 4 huruf besar, contoh M, T.S. menjadi TS,
    RPIR. Dipakai saat menurunkan baris snapshot dari refs dict,
    supaya Prasanna RPIR menghasilkan kunci prasanna, bukan rpir.
    """
    bersih = _bersihkan_token(tok).replace(".", "")
    if not bersih:
        return False
    if len(bersih) == 1:
        return True
    return len(bersih) <= 4 and bersih.isupper() and bersih.isalpha()


def rows_dari_refs_dicts(refs):
    """Turunkan baris snapshot dari list refs dict panen.

    Dipakai hanya bila pemanggil tidak mengoper snapshot_rows dari
    DB (pemanggil lama, mock, jalur non-DB). Logika kunci dan alias
    sama dengan pra_panen.parse_ref_ke_artikel: penulis pertama,
    bentuk koma berarti sebelum koma, bentuk lain berarti kata
    terakhir kecuali kata terakhir inisial, alias adalah semua
    token penulis kecuali kunci, dilipat. Referensi yang surname
    hanya inisial dilewati, sama seperti panen, karena tidak bisa
    dikutip dengan benar.
    Return list dict {kunci, alias, tahun, surname_tampil, authors}.
    """
    hasil = []
    for ref in (refs or []):
        if not isinstance(ref, dict):
            continue
        try:
            tahun = int(ref.get("year") or 0)
        except (TypeError, ValueError):
            tahun = 0
        if not tahun:
            continue
        authors = ref.get("authors") or []
        if isinstance(authors, str):
            authors = [x.strip() for x in authors.split(",") if x.strip()]
        authors = [str(a).strip() for a in authors if str(a).strip()]
        if not authors:
            continue
        pertama = authors[0]
        if "," in pertama:
            surname_raw = _bersihkan_token(pertama.split(",", 1)[0])
        else:
            kata = [_bersihkan_token(k) for k in pertama.split()
                    if _bersihkan_token(k)]
            if not kata:
                continue
            if _adalah_inisial_token(kata[-1]) and len(kata) >= 2:
                surname_raw = ""
                for k in kata:
                    if not _adalah_inisial_token(k):
                        surname_raw = k
                        break
                if not surname_raw:
                    continue
            else:
                surname_raw = kata[-1]
        if _adalah_inisial_token(surname_raw):
            continue
        kunci = _lipat(surname_raw)
        if not kunci:
            continue
        alias_set = set()
        for penulis in authors:
            for tok in re.split(r"[\s,]+", penulis):
                tok_lipat = _lipat(tok)
                if tok_lipat and tok_lipat != kunci:
                    alias_set.add(tok_lipat)
        hasil.append({
            "kunci": kunci,
            "alias": sorted(alias_set),
            "tahun": str(tahun),
            "surname_tampil": surname_raw,
            "authors": list(authors),
        })
    return hasil


def _refs_string_dari_rows(rows):
    """String referensi untuk repair_bab, dari baris snapshot.

    Bila baris membawa ref_dict, format_apa dipakai bila bisa
    diimpor, supaya inisial kandidat repair sama dengan gerbang
    final. Bila tidak, string dibangun dari authors dengan bentuk
    yang sama seperti format_apa (satu penulis apa adanya, dua
    penulis dipisah koma dan dan, lebih dari dua memakai et al.),
    supaya parser repair membaca surname dan inisial yang benar.
    """
    hasil = []
    for row in (rows or []):
        ref_dict = row.get("ref_dict") if isinstance(row, dict) else None
        teks_ref = None
        if ref_dict:
            try:
                from verifikasi_sitasi import format_apa as _format_apa
                teks_ref = _format_apa(ref_dict)
            except Exception:
                teks_ref = None
        if not teks_ref:
            authors = row.get("authors") if isinstance(row, dict) else None
            if authors:
                if len(authors) == 1:
                    nama = authors[0]
                elif len(authors) == 2:
                    nama = "%s, & %s" % (authors[0], authors[1])
                else:
                    nama = "%s, et al." % authors[0]
            else:
                nama = row.get("surname_tampil") or row.get("kunci") or ""
            teks_ref = "%s (%s)." % (nama, row.get("tahun") or "")
        if teks_ref and teks_ref.strip():
            hasil.append(teks_ref)
    return hasil


def _cocok_snapshot(surnames, tahun, rows):
    """True bila satu pun surname cocok dengan baris snapshot.

    Cocok berarti (surname dilipat, tahun) sama dengan (kunci,
    tahun) atau (alias, tahun) untuk satu baris. Tahun harus sama,
    nama saja tanpa tahun yang sama tidak dihitung.
    """
    tahun = str(tahun or "")
    for sur in (surnames or []):
        sur_lipat = _lipat(sur)
        for row in (rows or []):
            tahun_row = str(row.get("tahun") or "")
            if tahun_row != tahun:
                continue
            if sur_lipat and sur_lipat == _lipat(row.get("kunci") or ""):
                return True
            if sur_lipat in [_lipat(a) for a in (row.get("alias") or [])]:
                return True
    return False


def _baris_tercakup(teks, rows):
    """Himpunan indeks baris snapshot yang dikutip di teks.

    Sama dengan logika hitung_cakupan_kunci gerbang final: satu
    baris tercakup bila ada sitasi badan dengan (kunci atau alias,
    tahun sama). Dipakai untuk cakupan per baris subbab, bukan
    untuk syarat lolos subbab (syarat lolos adalah minimal 1
    sitasi snapshot, bukan cakupan 50 persen per subbab).
    """
    badan = set()
    for sit in _SG.ekstrak_sitasi_badan(teks or ""):
        tahun = str(sit.get("tahun") or "")
        for sur in (sit.get("surnames") or []):
            badan.add((_lipat(sur), tahun))
    tercakup = set()
    for idx, row in enumerate(rows or []):
        tahun = str(row.get("tahun") or "")
        kunci = _lipat(row.get("kunci") or "")
        if kunci and (kunci, tahun) in badan:
            tercakup.add(idx)
            continue
        for a in (row.get("alias") or []):
            if _lipat(a) and (_lipat(a), tahun) in badan:
                tercakup.add(idx)
                break
    return tercakup


def hapus_sitasi_luar(teks, rows):
    """Hapus sitasi luar daftar dari teks, deterministik.

    Return (teks_bersih, luar_dihapus) dengan luar_dihapus list
    string sitasi mentah yang dihapus, urut kemunculan pertama di
    teks awal. Hanya string sitasi luar yang dihapus, kalimat dan
    klaim tetap ada. Pembersihan spasi hanya di dalam baris, bukan
    menggabung paragraf, supaya pemecah paragraf tidak dibatalkan.
    """
    teks = teks or ""
    formal = _SG.ekstrak_sitasi_badan(teks)
    luar_raw = []
    for sit in formal:
        if not _cocok_snapshot(sit.get("surnames") or [],
                               sit.get("tahun") or "", rows):
            raw = sit.get("raw") or ""
            if raw and raw not in luar_raw:
                luar_raw.append(raw)
    bersih = teks
    for raw in luar_raw:
        bersih = bersih.replace(raw, "")
    # Rapikan spasi di dalam baris saja, paragraf tetap terpisah.
    baris_bersih = []
    for baris in bersih.split("\n"):
        baris = re.sub(r"[ \t]{2,}", " ", baris)
        baris = re.sub(r" \.([ \t]|$)", r".\1", baris)
        baris = re.sub(r" ,([ \t]|$)", r",\1", baris)
        baris_bersih.append(baris.strip(" \t"))
    bersih = "\n".join(baris_bersih)
    bersih = re.sub(r"\n{3,}", "\n\n", bersih)
    # Urut luar_dihapus menurut kemunculan di teks awal, untuk laporan.
    luar_urut = sorted(luar_raw, key=lambda r: teks.find(r))
    return bersih, luar_urut


def periksa_subbab(teks, rows, bab=None, subbab=None):
    """Periksa satu subbab terhadap snapshot bab itu.

    Langkah, urut: perbaikan inisial deterministik dulu (repair_bab
    tanpa LLM), lalu hapus sitasi luar deterministik, lalu cek
    ulang. Return dict dengan lolos, teks_bersih, jumlah sitasi
    snapshot, cakupan per baris, luar yang dihapus, inisial sisa,
    dan daftar masalah manusia. Tidak pernah raise untuk teks
    kosong atau baris kosong, lolos False dengan masalah jelas,
    supaya pemanggil yang memutuskan raise atau tidak.
    """
    teks_awal = teks or ""
    rows = list(rows or [])
    masalah = []
    if not rows:
        masalah.append(
            "BAB %s subbab %s: tidak ada baris snapshot referensi"
            % (bab, subbab))
        return {
            "lolos": False, "bab": bab, "subbab": subbab,
            "teks_bersih": teks_awal, "teks_awal": teks_awal,
            "diperbaiki": [], "luar_dihapus": [], "luar_sisa": [],
            "inisial_sisa": _SG.pindai_inisial(teks_awal),
            "snapshot_count": 0, "cakupan_total": 0,
            "cakupan_cocok": 0, "cakupan_rows": [],
            "masalah": masalah,
        }
    refs_string = _refs_string_dari_rows(rows)
    repair = _SG.repair_bab(teks_awal, refs_string, panggil_llm=None)
    teks_perbaiki = repair["teks_baru"]
    teks_bersih, luar_dihapus = hapus_sitasi_luar(teks_perbaiki, rows)
    formal_bersih = _SG.ekstrak_sitasi_badan(teks_bersih)
    snapshot_count = 0
    luar_sisa = []
    for sit in formal_bersih:
        if _cocok_snapshot(sit.get("surnames") or [],
                           sit.get("tahun") or "", rows):
            snapshot_count += 1
        else:
            luar_sisa.append(sit.get("raw") or "")
    inisial_sisa = _SG.pindai_inisial(teks_bersih)
    tercakup = _baris_tercakup(teks_bersih, rows)
    cakupan_rows = [rows[i].get("kunci") or "" for i in sorted(tercakup)]
    if snapshot_count < 1:
        masalah.append(
            "BAB %s subbab %s: 0 sitasi snapshot formal "
            "(minimal 1)" % (bab, subbab))
    if luar_sisa:
        masalah.append(
            "BAB %s subbab %s: %s sitasi luar daftar masih tersisa "
            "sesudah penghapusan deterministik"
            % (bab, subbab, len(luar_sisa)))
    if inisial_sisa:
        masalah.append(
            "BAB %s subbab %s: %s sitasi inisial saja masih tersisa"
            % (bab, subbab, len(inisial_sisa)))
    return {
        "lolos": not masalah,
        "bab": bab, "subbab": subbab,
        "teks_bersih": teks_bersih, "teks_awal": teks_awal,
        "diperbaiki": repair["diperbaiki"],
        "luar_dihapus": luar_dihapus, "luar_sisa": luar_sisa,
        "inisial_sisa": inisial_sisa,
        "snapshot_count": snapshot_count,
        "cakupan_total": len(rows),
        "cakupan_cocok": len(tercakup),
        "cakupan_rows": cakupan_rows,
        "masalah": masalah,
    }
