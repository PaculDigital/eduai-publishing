"""Sitasi anti gagal (G4, 30 Okt 2026).

Latar: job 222 membuktikan tiga cacat yang lolos ke buku jadi.
Bab 5 memuat sitasi inisial saja, contoh (M., 2024), yang tidak bisa
ditelusur ke nama penulis. Bab 4 memuat 0 dari 8 surname referensi yang
cocok dengan sitasi badan. Daftar pustaka hanya 16 entri untuk 234
sitasi, karena konsolidasi lama mengambil refs panen saja, bukan
sitasi badan, sehingga 19 sitasi badan hilang dari pustaka, antara
lain Vial 2019, Teece 2018, Rogers 2003, dan Davis 1989.

Modul ini deterministik dan tanpa LLM secara bawaan. LLM hanya dipakai
bila pemanggil mengoper panggil_llm, dan hanya boleh memilih di antara
kandidat refs, tidak boleh mengarang surname baru. Jalur LLM yang
dipakai pemanggil adalah combo yang sudah ada (call_llm di
buku_umum_pipeline), dioper sebagai callable panggil_llm(prompt).

Isi:
  1. pindai_inisial(teks): sitasi inisial saja, pola (X., Tahun) dan (X.Y., Tahun).
  2. hitung_cakupan(teks, refs): persen surname refs yang muncul di
     sitasi badan. Ambang minimal 50 persen, fail-closed di bawahnya.
  3. cek_hulu_bab(nomor_bab, teks, refs): gagal hulu bila ada inisial
     saja ATAU cakupan di bawah ambang. Ini gagal, bukan peringatan.
  4. repair_bab(teks, refs, panggil_llm=None): ganti inisial yang
     kandidatnya tepat satu. Ambigu atau tanpa kandidat tidak diganti
     buta. Pendekatan kedua untuk ambigu dijelaskan di repair_bab.
  5. gabung_pustaka(teks_per_bab, refs_panen): pustaka dari gabungan
     sitasi badan dan refs panen (union, dedup, urutan terdokumentasi).
  6. periksa_dan_perbaiki_bab(...): cek, repair, verifikasi ulang.
     Bila sesudah repair masih gagal, sinyal gagal bersih lewat
     GagalSitasiBersih atau flag, bukan error mentah.

Pemakaian ulang, bukan duplikasi:
  - Surname refs disaring lewat referensi_indeks.kumpulkan_nama
    (logika R2 yang sudah ada). Parser modul ini mengambil surname
    yang benar (surname APA sebelum koma, atau kata terakhir nama
    lengkap), lalu hanya mempertahankan surname yang juga muncul di
    kumpulkan_nama. Dengan begitu kata pertama nama lengkap (misal
    Wan dari Wan Laura Hardilawati) tidak dihitung sebagai surname.
    Bila penyaringan kosong karena format tak terduga, parser dipakai
    apa adanya sebagai cadangan, supaya fungsi tidak buta total.
  - Sitasi normal badan dipindai dengan pola sendiri, karena
    citation_validator.extract_citations tidak menangkap bentuk
    "Culpepper dan Thelen, 2020" (kata hubung dan) dan tidak
    menangkap sitasi inisial saja. Validator lama tidak diubah.

Hook untuk koordinator (modul ini TIDAK memasang hook sendiri):
  Lihat HOOK_KOORDINATOR di bawah berkas ini.
"""

import json
import re

AMBANG_CAKUPAN = 0.50
PESAN_GAGAL_BERSIH = "Maaf, buku belum berhasil dibuat. Token sudah kembali ke saldo."

_INSTITUSI = {
    "universitas", "institut", "kementerian", "badan", "bank",
    "perusahaan", "pt", "cv", "yayasan", "sekolah", "fakultas",
    "jurusan", "program",
}

# Sitasi inisial saja dalam kurung: (M., 2024), (H., 2025).
# Bentuk multi inisial juga ditangkap: (B.E., 2019), (T.S., 2025).
# Titik sesudah inisial boleh ada atau tidak, tahun boleh bersufiks
# huruf, contoh 2019a. Surname normal minimal 2 huruf, jadi pola satu
# huruf ini tidak akan menangkap sitasi normal.
INISIAL_KURUNG = re.compile(r"\(((?:[A-Z]\.\s*)+),\s*(\d{4}[a-z]?)\)")
# Bentuk naratif: M. (2024) menyatakan. Bentuk ini juga inisial saja.
INISIAL_NARATIF = re.compile(r"\b((?:[A-Z]\.\s*)+)\((\d{4}[a-z]?)\)")
# Sitasi normal dalam kurung: (Vial, 2019), (Macharia dan Daoping, 2020),
# (Tjiptono dan Suryani, 2025), (Gawer dan Cusumano, 2014).
# Isi kurung dibatasi supaya tidak menelan kalimat panjang.
SITASI_KURUNG = re.compile(r"\(([^()]{1,90}?),\s*(\d{4}[a-z]?)\)")
# Sitasi naratif normal: Vial (2019) menyatakan. Nama sebelum kurung
# tahun, tanpa koma di antaranya, supaya tidak ganda dengan bentuk
# kurung di atas.
SITASI_NARATIF = re.compile(
    r"\b([A-Z][A-Za-z\xc0-\xff\-]+(?:\s+(?:&|dan)\s+[A-Z][A-Za-z\xc0-\xff\-]+)?(?:\s+et al\.?)?)"
    r"\s*\((\d{4}[a-z]?)\)"
)
_TAHUN_REF = re.compile(r"\((\d{4})[a-z]?\)")
_APA = re.compile(r"([A-Z][A-Za-z\xc0-\xff\-]+)\s*,\s*((?:[A-Z]\.\s*)+)")
_PEMISAH_PENULIS = re.compile(r"\s+&\s+|\s+dan\s+|\s+and\s+|;")


class GagalSitasiBersih(Exception):
    """Sinyal gagal bersih sesudah repair habis.

    str(exception) selalu PESAN_GAGAL_BERSIH, supaya pemanggil di
    penyusunan_buku.susun bisa mengandalkan jalur except yang sudah
    ada untuk refund, tanpa menampilkan error mentah ke user.
    Rincian teknis tetap tersedia sebagai atribut, bukan di pesan.
    """

    def __init__(self, nomor_bab=None, masalah=None, inisial_tersisa=None,
                 cakupan=None):
        super().__init__(PESAN_GAGAL_BERSIH)
        self.nomor_bab = nomor_bab
        self.masalah = list(masalah or [])
        self.inisial_tersisa = list(inisial_tersisa or [])
        self.cakupan = dict(cakupan or {})


def _norm(kata):
    return (kata or "").strip().lower().rstrip(".")


def _adalah_inisial(kata):
    w = (kata or "").replace(".", "")
    if not w:
        return True
    if len(w) == 1:
        return True
    if len(w) <= 4 and w.isupper():
        return True
    return False


def refs_dari_data(data):
    """Normalisasi data refs_babN.json menjadi list string.

    Menerima list string (format nyata refs_babN.json), atau dict
    dengan kunci refs atau referensi. Masukan lain menghasilkan list
    kosong, bukan crash, supaya pemanggil hook bisa fail-closed
    dengan alasan yang jelas di cek_hulu_bab.
    """
    if isinstance(data, list):
        return [str(x) for x in data if x and str(x).strip()]
    if isinstance(data, dict):
        refs = data.get("refs") or data.get("referensi") or []
        if isinstance(refs, list):
            return [str(x) for x in refs if x and str(x).strip()]
    return []


def _tahun_dan_segmen(entri):
    m = _TAHUN_REF.search(entri or "")
    if not m:
        return "", (entri or "").split("(")[0]
    return m.group(1), entri[:m.start()]


def _parse_kandidat_ref(entri):
    """Kandidat penulis dari satu string refs_babN.json.

    Return list dict {surname, inisial, tahun, entri}. Inisial adalah
    list huruf kapital, contoh ["H"] untuk Zhou, H. atau ["T", "S"]
    untuk Wulan, T. S. Entri institusi dikembalikan kosong.
    """
    entri = (entri or "").strip()
    if not entri:
        return []
    tahun, segmen = _tahun_dan_segmen(entri)
    if not tahun:
        return []
    segmen = segmen.strip().rstrip(",").strip()
    if not segmen:
        return []
    kata_pertama = segmen.split()[0].lower().rstrip(".")
    if kata_pertama in _INSTITUSI:
        return []
    # Bentuk APA: Surname, I. atau Surname, I. J., dan pasangan
    # berikutnya di entri yang sama.
    apa = []
    for m in _APA.finditer(segmen):
        surname = m.group(1)
        inisial = re.findall(r"([A-Z])\.", m.group(2))
        if surname and inisial and not _adalah_inisial(surname):
            apa.append({"surname": surname, "inisial": inisial,
                        "tahun": tahun, "entri": entri})
    if apa:
        return apa
    # Bentuk refs nyata tanpa koma: Surname I. atau Surname I. J.
    # (format refs_babN.json panen, contoh Alfarizi M. (2024) dan
    # Putra B.E. (2019)). Surname adalah kata pertama, inisial di
    # belakangnya, bukan kata terakhir seperti nama lengkap.
    tanpa_koma = re.match(
        r"([A-Z][A-Za-z\xc0-\xff\-]+)\s+((?:[A-Z]\.\s*)+)$",
        segmen)
    if tanpa_koma and not _adalah_inisial(tanpa_koma.group(1)):
        return [{"surname": tanpa_koma.group(1),
                 "inisial": re.findall(r"([A-Z])\.", tanpa_koma.group(2)),
                 "tahun": tahun, "entri": entri}]
    # Bentuk nama lengkap: "Bambang Arianto", "Wan Laura Hardilawati",
    # "Chege Samwel Macharia", atau beberapa penulis dipisah & atau dan.
    # Surname adalah kata terakhir tiap potongan, inisial adalah huruf
    # pertama kata pertama potongan itu.
    hasil = []
    for potong in _PEMISAH_PENULIS.split(segmen):
        potong = potong.strip().strip(",").strip()
        if not potong:
            continue
        potong = potong.replace(" et al.", "").replace(" et al", "").strip()
        if not potong:
            continue
        kata = [w.strip(".") for w in potong.split() if w.strip(".")]
        if not kata:
            continue
        if kata[0].lower() in _INSTITUSI:
            continue
        if len(kata) == 1:
            if _adalah_inisial(kata[0]):
                continue
            hasil.append({"surname": kata[0], "inisial": [kata[0][0]],
                          "tahun": tahun, "entri": entri})
            continue
        surname = kata[-1]
        if _adalah_inisial(surname):
            continue
        hasil.append({"surname": surname, "inisial": [kata[0][0]],
                      "tahun": tahun, "entri": entri})
    return hasil


def _kandidat_dari_refs(refs):
    """Semua kandidat penulis dari list refs, dedup urut kemunculan."""
    hasil, lihat = [], set()
    for entri in (refs or []):
        for kand in _parse_kandidat_ref(str(entri)):
            kunci = (kand["surname"].lower(), kand["tahun"],
                     tuple(kand["inisial"]))
            if kunci not in lihat:
                lihat.add(kunci)
                hasil.append(kand)
    return hasil


def _kumpulkan_nama_set(refs):
    """Token kumpulkan_nama (R2) sebagai set ternormalisasi.

    Gagal impor atau gagal panggil menghasilkan set kosong, dan
    pemanggil _surname_dari_refs lalu memakai parser apa adanya.
    """
    try:
        try:
            from . import referensi_indeks as _RI
        except ImportError:
            import referensi_indeks as _RI
        tokens = _RI.kumpulkan_nama([str(x) for x in (refs or [])])
        return {_norm(t) for t in tokens}
    except Exception:
        return set()


def _surname_dari_refs(refs):
    """Surname refs urut kemunculan, dedup, tanpa nama depan.

    Parser mengambil surname yang benar, lalu disaring dengan
    kumpulkan_nama. Bila saringan kosong karena format tak terduga,
    parser dipakai apa adanya sebagai cadangan.
    """
    parser, lihat = [], set()
    for kand in _kandidat_dari_refs(refs):
        kunci = kand["surname"].lower()
        if kunci not in lihat:
            lihat.add(kunci)
            parser.append(kand["surname"])
    if not parser:
        return []
    token_set = _kumpulkan_nama_set(refs)
    if not token_set:
        return parser
    saring = [s for s in parser if _norm(s) in token_set]
    return saring if saring else parser


def _huruf_inisial(grup):
    """Huruf inisial saja dari grup titik, contoh B.E. jadi BE, M. jadi M."""
    return "".join(c for c in (grup or "") if c.isalpha() and c.isupper())


def pindai_inisial(teks):
    """Semua kemunculan sitasi inisial saja, urut posisi.

    Tiap butir: {inisial, tahun, raw, posisi, bentuk}. Bentuk kurung
    untuk (M., 2024), naratif untuk M. (2024). Naratif yang posisinya
    tepat sesudah tanda kurung buka dilewati, supaya bentuk kurung
    tidak dihitung dua kali oleh pola naratif.
    """
    teks = teks or ""
    hasil = []
    for m in INISIAL_KURUNG.finditer(teks):
        hasil.append({"inisial": _huruf_inisial(m.group(1)), "tahun": m.group(2),
                      "raw": m.group(0), "posisi": m.start(),
                      "bentuk": "kurung"})
    for m in INISIAL_NARATIF.finditer(teks):
        if m.start() > 0 and teks[m.start() - 1] == "(":
            continue
        hasil.append({"inisial": _huruf_inisial(m.group(1)), "tahun": m.group(2),
                      "raw": m.group(0), "posisi": m.start(),
                      "bentuk": "naratif"})
    hasil.sort(key=lambda x: x["posisi"])
    return hasil


def ringkas_inisial(kemunculan):
    """Agregasi kemunculan inisial per (inisial, tahun).

    Tiap butir: {inisial, tahun, raw, jumlah}. Raw adalah bentuk
    pertama yang muncul, contoh (M., 2024).
    """
    agregat, urut = {}, []
    for item in (kemunculan or []):
        kunci = (item["inisial"], item["tahun"])
        if kunci not in agregat:
            agregat[kunci] = {"inisial": item["inisial"],
                              "tahun": item["tahun"],
                              "raw": item["raw"], "jumlah": 0}
            urut.append(kunci)
        agregat[kunci]["jumlah"] += 1
    return [agregat[k] for k in urut]


def _surname_dari_potongan_sitasi(potong):
    """Surname dari satu potongan penulis sitasi badan.

    Potongan sitasi badan memakai surname, jadi kata terakhir adalah
    surname. Potongan inisial saja atau kosong menghasilkan None.
    """
    potong = (potong or "").replace(" et al.", "").replace(" et al", "")
    potong = potong.strip().strip(",").strip()
    if not potong:
        return None
    kata = [w.strip(".") for w in potong.split() if w.strip(".")]
    if not kata:
        return None
    if len(kata) == 1 and _adalah_inisial(kata[0]):
        return None
    surname = kata[-1]
    if _adalah_inisial(surname):
        return None
    return surname


def ekstrak_sitasi_badan(teks):
    """Sitasi normal badan, tanpa sitasi inisial saja.

    Tiap butir: {surnames, tahun, raw}. Surnames adalah list surname
    urut kemunculan di sitasi itu. Bentuk kurung dan naratif normal
    dicakup, bentuk inisial saja dilewati karena tidak punya surname.
    """
    teks = teks or ""
    hasil = []
    for m in SITASI_KURUNG.finditer(teks):
        isi, tahun = m.group(1).strip(), m.group(2)
        # Inisial saja sudah ditangani pindai_inisial, bukan di sini.
        if re.fullmatch(r"[A-Z]\.?", isi):
            continue
        surnames = []
        for potong in re.split(r"\s+&\s+|\s+dan\s+|\s+and\s+|,", isi):
            sur = _surname_dari_potongan_sitasi(potong)
            if sur and sur not in surnames:
                surnames.append(sur)
        if surnames:
            hasil.append({"surnames": surnames, "tahun": tahun,
                          "raw": m.group(0)})
    for m in SITASI_NARATIF.finditer(teks):
        if m.start() > 0 and teks[m.start() - 1] == "(":
            continue
        isi, tahun = m.group(1).strip(), m.group(2)
        if re.fullmatch(r"[A-Z]\.?", isi):
            continue
        surnames = []
        for potong in re.split(r"\s+&\s+|\s+dan\s+|\s+and\s+|,", isi):
            sur = _surname_dari_potongan_sitasi(potong)
            if sur and sur not in surnames:
                surnames.append(sur)
        if surnames and not any(h["raw"] == m.group(0) for h in hasil):
            hasil.append({"surnames": surnames, "tahun": tahun,
                          "raw": m.group(0)})
    return hasil


def hitung_cakupan(teks, refs):
    """Persen surname refs yang muncul di sitasi badan.

    Return {total, cocok_jumlah, persen, cocok, hilang}. Persen 0.0
    bila refs kosong, supaya pemanggil fail-closed, bukan lolos diam.
    """
    surnames_ref = _surname_dari_refs(refs)
    badan = set()
    for sit in ekstrak_sitasi_badan(teks):
        for sur in sit["surnames"]:
            badan.add(sur.lower())
    cocok = [s for s in surnames_ref if s.lower() in badan]
    hilang = [s for s in surnames_ref if s.lower() not in badan]
    total = len(surnames_ref)
    persen = (len(cocok) / total) if total else 0.0
    return {"total": total, "cocok_jumlah": len(cocok),
            "persen": persen, "cocok": cocok, "hilang": hilang}


def cek_hulu_bab(nomor_bab, teks, refs):
    """Cek hulu per bab. Gagal hulu, bukan peringatan.

    Lolos hanya bila dua syarat terpenuhi sekaligus: tidak ada sitasi
    inisial saja, dan cakupan surname minimal 50 persen. Return
    {lolos, nomor_bab, jumlah_inisial, inisial, contoh_inisial,
    cakupan, masalah}. Contoh inisial dibatasi 5 butir pertama supaya
    laporan tidak penuh, jumlah penuh tetap ada di jumlah_inisial.
    """
    teks = teks or ""
    refs = [str(x) for x in (refs or []) if str(x).strip()]
    kemunculan = pindai_inisial(teks)
    ringkas = ringkas_inisial(kemunculan)
    cakupan = hitung_cakupan(teks, refs)
    masalah = []
    if kemunculan:
        contoh = ", ".join(
            "%s (%dx)" % (r["raw"], r["jumlah"]) for r in ringkas[:5])
        masalah.append(
            "BAB %s: %d sitasi inisial saja, contoh %s"
            % (nomor_bab, len(kemunculan), contoh))
    if not refs:
        masalah.append("BAB %s: tidak ada referensi bab" % nomor_bab)
    elif cakupan["persen"] < AMBANG_CAKUPAN:
        masalah.append(
            "BAB %s: cakupan surname hanya %.0f persen "
            "(%d dari %d, ambang 50 persen)"
            % (nomor_bab, cakupan["persen"] * 100,
               cakupan["cocok_jumlah"], cakupan["total"]))
    return {"lolos": not masalah, "nomor_bab": nomor_bab,
            "jumlah_inisial": len(kemunculan), "inisial": ringkas,
            "contoh_inisial": [r["raw"] for r in ringkas[:5]],
            "cakupan": cakupan, "masalah": masalah}


def _kalimat_memuat(teks, posisi):
    awal = max(teks.rfind(".", 0, posisi), teks.rfind("!", 0, posisi),
               teks.rfind("?", 0, posisi), teks.rfind("\n", 0, posisi)) + 1
    akhir = len(teks)
    for pemisah in (".", "!", "?", "\n"):
        idx = teks.find(pemisah, posisi)
        if idx >= 0:
            akhir = min(akhir, idx)
    return teks[awal:akhir]


def _paragraf_memuat(teks, posisi):
    awal = teks.rfind("\n\n", 0, posisi) + 2
    akhir = teks.find("\n\n", posisi)
    if akhir < 0:
        akhir = len(teks)
    return teks[awal:akhir]


def _pilih_dari_konteks(teks, kemunculan_grup, kandidat_surnames):
    """Pendekatan kedua untuk inisial ambigu, deterministik.

    Urutan bukti, berhenti di bukti pertama yang menghasilkan tepat
    satu kandidat:
      1. Kalimat yang memuat sitasi pertama menyebut tepat satu
         surname kandidat sebagai kata utuh.
      2. Paragraf yang memuat sitasi pertama menyebut tepat satu
         surname kandidat sebagai kata utuh.
      3. Sitasi normal lain di bab yang sama, dengan tahun yang sama,
         menyebut tepat satu surname kandidat.
    Bila tidak ada bukti yang menghasilkan tepat satu kandidat,
    kembalikan None dan sitasi tetap ambigu, tidak ditebak.
    """
    if not kemunculan_grup:
        return None, ""
    posisi = kemunculan_grup[0]["posisi"]
    tahun = kemunculan_grup[0]["tahun"]
    for label, konteks in (("kalimat_memuat_surname",
                            _kalimat_memuat(teks, posisi)),
                           ("paragraf_memuat_surname",
                            _paragraf_memuat(teks, posisi))):
        kena = [s for s in kandidat_surnames
                if re.search(r"\b" + re.escape(s) + r"\b", konteks,
                             re.IGNORECASE)]
        if len(kena) == 1:
            return kena[0], label
    badan_tahun = set()
    for sit in ekstrak_sitasi_badan(teks):
        if sit["tahun"] == tahun:
            for sur in sit["surnames"]:
                badan_tahun.add(sur.lower())
    kena = [s for s in kandidat_surnames if s.lower() in badan_tahun]
    if len(kena) == 1:
        return kena[0], "sitasi_normal_tahun_sama"
    return None, ""


def _parse_jawaban_llm(jawaban, grup_ambigu):
    """Parse jawaban LLM menjadi {kunci_raw: surname} yang sah saja.

    Kunci adalah raw agregat, contoh (N., 2025) tanpa tanda kurung
    luar di kunci JSON, atau bentuk "N., 2025". Surname yang
    dikembalikan hanya diterima bila ada di daftar kandidat grup
    itu. Surname di luar kandidat ditolak, supaya LLM tidak bisa
    mengarang nama baru atau memilih penulis yang tidak ada di refs.
    """
    if not jawaban or not isinstance(jawaban, str):
        return {}
    peta_kandidat = {}
    for grup in grup_ambigu:
        for raw_varian in (grup["raw"], grup["raw"].strip("()")):
            peta_kandidat[raw_varian] = grup
    hasil = {}
    teks_json = jawaban
    awal = jawaban.find("{")
    akhir = jawaban.rfind("}")
    if awal >= 0 and akhir > awal:
        teks_json = jawaban[awal:akhir + 1]
    try:
        data = json.loads(teks_json)
        if isinstance(data, dict):
            for kunci, nilai in data.items():
                grup = peta_kandidat.get(str(kunci).strip())
                if grup and isinstance(nilai, str):
                    if nilai.strip() in grup["kandidat"]:
                        hasil[grup["raw"]] = nilai.strip()
            return hasil
    except Exception:
        pass
    for m in re.finditer(
            r'"([A-Z]\.,\s*\d{4}[a-z]?)"\s*:\s*"([^"]+)"', jawaban):
        grup = peta_kandidat.get(m.group(1))
        if grup and m.group(2).strip() in grup["kandidat"]:
            hasil[grup["raw"]] = m.group(2).strip()
    return hasil


def repair_bab(teks, refs, panggil_llm=None):
    """Perbaiki sitasi inisial saja di satu bab, tanpa ganti buta.

    Langkah deterministik dulu: inisial dengan tepat satu kandidat
    (inisial dan tahun cocok di refs) diganti ke (Surname, Tahun)
    atau bentuk naratif Surname (Tahun). Langkah kedua untuk ambigu:
    pilih dari konteks, lihat _pilih_dari_konteks. Langkah ketiga,
    hanya bila panggil_llm dioper: LLM memilih di antara kandidat
    ambigu, jawaban di luar kandidat ditolak. Tanpa kandidat tetap
    tidak diganti. Return {teks_baru, diperbaiki, ambigu,
    tanpa_kandidat, jumlah_awal, jumlah_sisa}.
    """
    teks = teks or ""
    refs = [str(x) for x in (refs or []) if str(x).strip()]
    kandidat = _kandidat_dari_refs(refs)
    kemunculan = pindai_inisial(teks)
    grup = {}
    urut_grup = []
    for item in kemunculan:
        kunci = (item["inisial"], item["tahun"])
        if kunci not in grup:
            grup[kunci] = []
            urut_grup.append(kunci)
        grup[kunci].append(item)
    pengganti = []
    diperbaiki, ambigu, tanpa_kandidat = [], [], []
    for kunci in urut_grup:
        inisial, tahun = kunci
        items = grup[kunci]
        surnames = []
        for kand in kandidat:
            if kand["tahun"] == tahun and tuple(inisial) == tuple(kand["inisial"]):
                if kand["surname"] not in surnames:
                    surnames.append(kand["surname"])
        raw = items[0]["raw"]
        if not surnames:
            tanpa_kandidat.append({"inisial": inisial, "tahun": tahun,
                                   "raw": raw, "jumlah": len(items),
                                   "kandidat": []})
        elif len(surnames) == 1:
            surname = surnames[0]
            diperbaiki.append({"inisial": inisial, "tahun": tahun,
                               "raw": raw, "surname": surname,
                               "jumlah": len(items), "cara": "tunggal"})
            for item in items:
                if item["bentuk"] == "naratif":
                    baru = "%s (%s)" % (surname, tahun)
                else:
                    baru = "(%s, %s)" % (surname, tahun)
                pengganti.append((item["posisi"], len(item["raw"]), baru))
        else:
            dipilih, alasan = _pilih_dari_konteks(teks, items, surnames)
            if dipilih:
                diperbaiki.append({"inisial": inisial, "tahun": tahun,
                                   "raw": raw, "surname": dipilih,
                                   "jumlah": len(items),
                                   "cara": "konteks_" + alasan})
                for item in items:
                    if item["bentuk"] == "naratif":
                        baru = "%s (%s)" % (dipilih, tahun)
                    else:
                        baru = "(%s, %s)" % (dipilih, tahun)
                    pengganti.append((item["posisi"], len(item["raw"]), baru))
            else:
                ambigu.append({"inisial": inisial, "tahun": tahun,
                               "raw": raw, "jumlah": len(items),
                               "kandidat": surnames})
    if panggil_llm is not None and ambigu:
        try:
            prompt = (
                "Pilih surname yang benar untuk tiap sitasi inisial "
                "saja berikut, hanya dari daftar kandidat yang "
                "diberikan, tanpa mengarang nama baru. Jawab JSON "
                "saja, contoh {\"N., 2025\": \"Noerchoidah\"}. "
                "Sitasi ambigu: "
                + "; ".join(
                    "%s kandidat %s" % (g["raw"], ", ".join(g["kandidat"]))
                    for g in ambigu)
                + ". Konteks bab: " + teks[:2000])
            jawaban = panggil_llm(prompt)
        except Exception:
            jawaban = None
        pilihan = _parse_jawaban_llm(jawaban, ambigu)
        if pilihan:
            sisa_ambigu = []
            for grup_amb in ambigu:
                surname = pilihan.get(grup_amb["raw"])
                if surname:
                    diperbaiki.append(
                        {"inisial": grup_amb["inisial"],
                         "tahun": grup_amb["tahun"],
                         "raw": grup_amb["raw"], "surname": surname,
                         "jumlah": grup_amb["jumlah"], "cara": "llm_kandidat"})
                    for item in grup[grup_amb["inisial"], grup_amb["tahun"]]:
                        if item["bentuk"] == "naratif":
                            baru = "%s (%s)" % (surname, grup_amb["tahun"])
                        else:
                            baru = "(%s, %s)" % (surname, grup_amb["tahun"])
                        pengganti.append(
                            (item["posisi"], len(item["raw"]), baru))
                else:
                    sisa_ambigu.append(grup_amb)
            ambigu = sisa_ambigu
    teks_baru = teks
    for posisi, panjang, baru in sorted(pengganti, reverse=True):
        teks_baru = teks_baru[:posisi] + baru + teks_baru[posisi + panjang:]
    return {"teks_baru": teks_baru, "diperbaiki": diperbaiki,
            "ambigu": ambigu, "tanpa_kandidat": tanpa_kandidat,
            "jumlah_awal": len(kemunculan),
            "jumlah_sisa": len(pindai_inisial(teks_baru))}


def _teks_list(teks_per_bab):
    if isinstance(teks_per_bab, dict):
        kunci = []
        for k in teks_per_bab:
            try:
                kunci.append((int(k), teks_per_bab[k]))
            except (TypeError, ValueError):
                continue
        return [str(t or "") for _, t in sorted(kunci, key=lambda x: x[0])]
    if isinstance(teks_per_bab, str):
        return [teks_per_bab]
    if isinstance(teks_per_bab, (list, tuple)):
        return [str(t or "") for t in teks_per_bab]
    return []


def _refs_list(refs_panen):
    if isinstance(refs_panen, dict):
        kunci = []
        for k in refs_panen:
            try:
                kunci.append((int(k), refs_panen[k]))
            except (TypeError, ValueError):
                continue
        hasil = []
        for _, nilai in sorted(kunci, key=lambda x: x[0]):
            hasil.extend(refs_dari_data(nilai))
        return hasil
    return refs_dari_data(refs_panen)


def _kunci_ref(entri):
    """Kunci dedup satu entri panen, atau None bila tak terparse.

    Kunci adalah (frozenset surname, tahun). Entri yang tak terparse
    (misal institusi) dikembalikan None, supaya tidak hilang dari
    pustaka hanya karena surname tidak bisa diparse.
    """
    kand = _parse_kandidat_ref(entri)
    tahun, _segmen = _tahun_dan_segmen(entri)
    if not kand or not tahun:
        return None
    surnames = frozenset(k["surname"].lower() for k in kand)
    return (surnames, tahun)


def _entri_badan(surnames, tahun):
    """Entri pustaka minimal dari sitasi badan, tanpa judul karangan.

    Judul dan sumber tidak dikarang, karena sitasi badan saja tidak
    memuatnya. Entri ditandai jelas supaya gerbang atau editor tahu
    judul masih perlu dilengkapi dari sumber asli, bukan dianggap
    entri panen yang lengkap.
    """
    if len(surnames) == 1:
        nama = surnames[0]
    else:
        nama = " dan ".join(surnames)
    return ("%s (%s). Entri dari sitasi badan, judul dan sumber "
            "belum tersedia di panen." % (nama, tahun))


def gabung_pustaka(teks_per_bab, refs_panen):
    """Pustaka buku dari gabungan sitasi badan dan refs panen.

    Urutan yang didokumentasikan dan deterministik:
      1. Refs panen, urut kemunculan (bab 1 ke bab terakhir, dalam
         bab urut refs), dedup berdasarkan (surname, tahun).
      2. Sitasi badan yang belum ada di panen, urut kemunculan
         pertama di badan (bab 1 ke bab terakhir), dalam bentuk
         entri minimal _entri_badan, tanpa judul karangan.
    Panen yang tidak terparse tetap dipertahankan verbatim, supaya
    konsolidasi tidak pernah menghapus entri panen yang sah.
    """
    panen = _refs_list(refs_panen)
    hasil, kunci_lihat = [], set()
    for entri in panen:
        entri = str(entri).strip()
        if not entri:
            continue
        kunci = _kunci_ref(entri)
        if kunci is not None:
            if kunci in kunci_lihat:
                continue
            kunci_lihat.add(kunci)
        elif entri.lower() in kunci_lihat:
            continue
        else:
            kunci_lihat.add(entri.lower())
        hasil.append(entri)
    for teks in _teks_list(teks_per_bab):
        for sit in ekstrak_sitasi_badan(teks):
            kunci = (frozenset(s.lower() for s in sit["surnames"]),
                     sit["tahun"])
            if kunci in kunci_lihat:
                continue
            kunci_lihat.add(kunci)
            hasil.append(_entri_badan(sit["surnames"], sit["tahun"]))
    return hasil


def gabung_pustaka_dengan_info(teks_per_bab, refs_panen):
    """gabung_pustaka plus hitungan untuk laporan dan gerbang.

    Return (pustaka, info) dengan info {panen_masuk, panen_unik,
    badan_unik, ditambah_dari_badan, total, entri_badan_baru}.
    """
    panen = _refs_list(refs_panen)
    pustaka = gabung_pustaka(teks_per_bab, refs_panen)
    panen_unik = 0
    kunci_panen = set()
    for entri in panen:
        kunci = _kunci_ref(entri)
        kunci = kunci if kunci is not None else entri.lower()
        if kunci not in kunci_panen:
            kunci_panen.add(kunci)
            panen_unik += 1
    badan_unik = set()
    for teks in _teks_list(teks_per_bab):
        for sit in ekstrak_sitasi_badan(teks):
            badan_unik.add((frozenset(s.lower() for s in sit["surnames"]),
                            sit["tahun"]))
    ditambah = pustaka[panen_unik:] if len(pustaka) >= panen_unik else []
    return pustaka, {"panen_masuk": len(panen), "panen_unik": panen_unik,
                     "badan_unik": len(badan_unik),
                     "ditambah_dari_badan": len(ditambah),
                     "total": len(pustaka),
                     "entri_badan_baru": ditambah}


def periksa_dan_perbaiki_bab(nomor_bab, teks, refs, panggil_llm=None,
                              gagal_keras=True):
    """Orkestrasi per bab: cek, repair, verifikasi ulang.

    Return dict lolos True bila cek awal lolos, atau sesudah repair
    cek ulang lolos. Bila sesudah repair masih gagal dan gagal_keras
    True, raise GagalSitasiBersih (pesan manusia, atribut berisi
    rincian). Bila gagal_keras False, return dict lolos False dengan
    pesan manusia yang sama, tanpa raise, untuk pemanggil yang
    memakai flag. Teks yang dikembalikan ada di teks_baru.
    """
    cek_awal = cek_hulu_bab(nomor_bab, teks, refs)
    if cek_awal["lolos"]:
        return {"lolos": True, "nomor_bab": nomor_bab,
                "teks_baru": teks, "teks_asli": teks,
                "diperbaiki": [], "ambigu": [], "tanpa_kandidat": [],
                "cek_awal": cek_awal, "cek_ulang": cek_awal, "pesan": ""}
    repair = repair_bab(teks, refs, panggil_llm=panggil_llm)
    cek_ulang = cek_hulu_bab(nomor_bab, repair["teks_baru"], refs)
    if cek_ulang["lolos"]:
        return {"lolos": True, "nomor_bab": nomor_bab,
                "teks_baru": repair["teks_baru"], "teks_asli": teks,
                "diperbaiki": repair["diperbaiki"],
                "ambigu": repair["ambigu"],
                "tanpa_kandidat": repair["tanpa_kandidat"],
                "cek_awal": cek_awal, "cek_ulang": cek_ulang, "pesan": ""}
    if gagal_keras:
        raise GagalSitasiBersih(
            nomor_bab=nomor_bab, masalah=cek_ulang["masalah"],
            inisial_tersisa=cek_ulang["inisial"],
            cakupan=cek_ulang["cakupan"])
    return {"lolos": False, "nomor_bab": nomor_bab,
            "teks_baru": repair["teks_baru"], "teks_asli": teks,
            "diperbaiki": repair["diperbaiki"],
            "ambigu": repair["ambigu"],
            "tanpa_kandidat": repair["tanpa_kandidat"],
            "cek_awal": cek_awal, "cek_ulang": cek_ulang,
            "pesan": PESAN_GAGAL_BERSIH}


def _lipat_token(tok):
    """Lipat diakritik plus huruf kecil untuk satu token nama.

    Contoh: Dabic dengan aksen menjadi dabic. Sama dengan
    normalisasi_teks di pra_panen (didupikasi di sini supaya modul
    ini tetap mandiri, tanpa impor pra_panen).
    """
    import unicodedata
    if not tok:
        return ""
    bentuk = unicodedata.normalize("NFKD", str(tok))
    tanpa_aksen = "".join(
        c for c in bentuk if not unicodedata.combining(c))
    return tanpa_aksen.strip().strip(".,").lower()


def hitung_cakupan_kunci(teks, snapshot_rows):
    """Persen baris snapshot yang dikutip di badan, dari KUNCI DB.

    snapshot_rows: list dict {kunci, alias, tahun} dari
    pra_panen.ambil_snapshot (kunci dan alias sudah ternormalisasi).
    Satu baris cocok bila ada sitasi badan dengan (surname_key atau
    alias, tahun yang sama). Beda dengan hitung_cakupan lama yang
    mem-parse ulang string format APA (sumber salah hitung job 223:
    Marina lawan Dabic, Zhiqiang lawan Lu).

    Return {total, cocok_jumlah, persen, cocok, hilang}, bentuk sama
    dengan hitung_cakupan, supaya pemanggil bisa bertukar jalur.
    """
    teks = teks or ""
    badan = set()
    for sit in ekstrak_sitasi_badan(teks):
        tahun = str(sit.get("tahun") or "")
        for sur in (sit.get("surnames") or []):
            badan.add((_lipat_token(sur), tahun))
    total = len(snapshot_rows or [])
    cocok = []
    hilang = []
    for row in (snapshot_rows or []):
        kunci = _lipat_token(row.get("kunci") or "")
        tahun = str(row.get("tahun") or "")
        alias = [_lipat_token(a) for a in (row.get("alias") or [])]
        kena = (kunci, tahun) in badan if kunci else False
        if not kena:
            for a in alias:
                if a and (a, tahun) in badan:
                    kena = True
                    break
        if kena:
            cocok.append(kunci)
        else:
            hilang.append(kunci)
    persen = (len(cocok) / total) if total else 0.0
    return {"total": total, "cocok_jumlah": len(cocok),
            "persen": persen, "cocok": cocok, "hilang": hilang}


def cek_hulu_bab_snapshot(nomor_bab, teks, snapshot_rows):
    """Cek hulu per bab dari snapshot (bukan dari string refs).

    Lolos hanya bila dua syarat terpenuhi sekaligus: tidak ada sitasi
    inisial saja, dan cakupan kunci minimal 50 persen. Bentuk return
    dan wording masalah sama dengan cek_hulu_bab, supaya log bisa
    dibandingkan dengan jalur lama.
    """
    teks = teks or ""
    rows = list(snapshot_rows or [])
    kemunculan = pindai_inisial(teks)
    ringkas = ringkas_inisial(kemunculan)
    cakupan = hitung_cakupan_kunci(teks, rows)
    masalah = []
    if kemunculan:
        contoh = ", ".join(
            "%s (%dx)" % (r["raw"], r["jumlah"]) for r in ringkas[:5])
        masalah.append(
            "BAB %s: %d sitasi inisial saja, contoh %s"
            % (nomor_bab, len(kemunculan), contoh))
    if not rows:
        masalah.append("BAB %s: tidak ada referensi bab" % nomor_bab)
    elif cakupan["persen"] < AMBANG_CAKUPAN:
        masalah.append(
            "BAB %s: cakupan surname hanya %.0f persen "
            "(%d dari %d, ambang 50 persen)"
            % (nomor_bab, cakupan["persen"] * 100,
               cakupan["cocok_jumlah"], cakupan["total"]))
    return {"lolos": not masalah, "nomor_bab": nomor_bab,
            "jumlah_inisial": len(kemunculan), "inisial": ringkas,
            "contoh_inisial": [r["raw"] for r in ringkas],
            "cakupan": cakupan, "masalah": masalah}


def periksa_dan_perbaiki_bab_snapshot(nomor_bab, teks, snapshot_rows,
                                      gagal_keras=True):
    """Orkestrasi snapshot per bab: cek kunci, repair, verifikasi ulang.

    Bentuk return dan perilaku gagal sama dengan
    periksa_dan_perbaiki_bab (GagalSitasiBersih bila gagal keras),
    hanya sumber kebenarannya snapshot, bukan string refs_babN.json.
    Repair memakai string format APA yang dibangun dari ref_dict
    snapshot (untuk kandidat surname dan inisial), deterministik,
    panggil_llm=None. Pemanggil yang babnya tidak punya snapshot
    WAJIB memakai periksa_dan_perbaiki_bab lama (fallback JSON).
    """
    rows = list(snapshot_rows or [])
    cek_awal = cek_hulu_bab_snapshot(nomor_bab, teks, rows)
    if cek_awal["lolos"]:
        return {"lolos": True, "nomor_bab": nomor_bab,
                "teks_baru": teks, "teks_asli": teks,
                "diperbaiki": [], "ambigu": [], "tanpa_kandidat": [],
                "cek_awal": cek_awal, "cek_ulang": cek_awal, "pesan": ""}
    try:
        from verifikasi_sitasi import format_apa as _format_apa
    except Exception:
        _format_apa = None
    refs_string = []
    for row in rows:
        ref_dict = row.get("ref_dict") or {}
        teks_ref = None
        if _format_apa is not None and ref_dict:
            try:
                teks_ref = _format_apa(ref_dict)
            except Exception:
                teks_ref = None
        if not teks_ref:
            teks_ref = "%s (%s)." % (
                row.get("surname_tampil") or row.get("kunci") or "",
                row.get("tahun") or "")
        if teks_ref.strip():
            refs_string.append(teks_ref)
    repair = repair_bab(teks, refs_string, panggil_llm=None)
    cek_ulang = cek_hulu_bab_snapshot(
        nomor_bab, repair["teks_baru"], rows)
    if cek_ulang["lolos"]:
        return {"lolos": True, "nomor_bab": nomor_bab,
                "teks_baru": repair["teks_baru"], "teks_asli": teks,
                "diperbaiki": repair["diperbaiki"],
                "ambigu": repair["ambigu"],
                "tanpa_kandidat": repair["tanpa_kandidat"],
                "cek_awal": cek_awal, "cek_ulang": cek_ulang, "pesan": ""}
    if gagal_keras:
        raise GagalSitasiBersih(
            nomor_bab=nomor_bab, masalah=cek_ulang["masalah"],
            inisial_tersisa=cek_ulang["inisial"],
            cakupan=cek_ulang["cakupan"])
    return {"lolos": False, "nomor_bab": nomor_bab,
            "teks_baru": repair["teks_baru"], "teks_asli": teks,
            "diperbaiki": repair["diperbaiki"],
            "ambigu": repair["ambigu"],
            "tanpa_kandidat": repair["tanpa_kandidat"],
            "cek_awal": cek_awal, "cek_ulang": cek_ulang,
            "pesan": PESAN_GAGAL_BERSIH}


HOOK_KOORDINATOR = """
Cuplikan hook untuk koordinator, TIDAK diterapkan modul ini.
Nomor baris di bawah adalah kondisi saat cek 30 Okt 2026, agen lain
sedang mengubah penyusunan_buku.py, jadi koordinator wajib cek ulang
nomor baris sebelum menempel.

PERINGATAN PROPAGASI, WAJIB DIBACA KOORDINATOR:
  Menempel periksa_dan_perbaiki_bab di dalam _cek_bab SAJA tidak
  cukup untuk refund. Dua lapisan saat ini menelan exception:
  (a) _cek_bab sendiri (app/penyusunan_buku.py sekitar baris 371,
  except mengembalikan masalah kosong), dan (b) pemanggil callback
  di penyusun_buku.py (sekitar baris 347, 414, dan 524, except
  hanya melapor "Cek awal dilewati"). Supaya GagalSitasiBersih
  sampai ke except susun() dan memicu kembalikan_banyak, koordinator
  harus memilih satu dari dua jalur ini:
  Jalur A: _cek_bab me-raise ulang GagalSitasiBersih secara khusus
  (except GagalSitasiBersih: raise, sebelum except umum), DAN
  penyusun_buku.py me-raise ulang exception itu di ketiga situs
  callback, bukan menelannya.
  Jalur B (lebih aman, tidak mengubah pipeline): sesudah
  S.susun_buku kembali di susun(), sebelum rakit, jalankan satu
  pass sitasi atas berkas bab di disk (baca keluar/bab{n}/bab{n}.txt,
  periksa_dan_perbaiki_bab, tulis teks_baru kembali ke berkas yang
  sama bila berbeda, raise GagalSitasiBersih bila masih gagal).
  Pass ini berada di dalam try susun(), jadi raise langsung memicu
  refund lewat except yang sudah ada, tanpa bergantung callback.

(1) Hook per bab, di app/penyusunan_buku.py, di dalam susun(),
    fungsi _cek_bab yang sudah ada (sekitar baris 371, dipanggil
    lewat on_bab_selesai=_cek_bab di S.susun_buku sekitar baris 412):
      import json as _json
      from . import sitasi_anti_gagal as _SG
      _refs_path = os.path.join(folder_bab, "visual",
                                 "refs_bab%d.json" % n)
      try:
          with open(_refs_path, encoding="utf-8") as _f:
              _refs_bab_n = _SG.refs_dari_data(_json.load(_f))
      except Exception:
          _refs_bab_n = []
      hasil_sg = _SG.periksa_dan_perbaiki_bab(
          n, teks or "", _refs_bab_n, panggil_llm=None, gagal_keras=True)
      if hasil_sg["teks_baru"] != (teks or ""):
          with open(os.path.join(folder_bab, "bab%d.txt" % n),
                    "w", encoding="utf-8") as _f:
              _f.write(hasil_sg["teks_baru"])
    Parameter: n (int nomor bab), teks (str teks bab), folder_bab
    (str, sudah diterima _cek_bab). Bila lolos, kembalikan hasil
    cek_awal yang lama seperti sekarang, supaya Lapisan 3c tidak
    berubah. Bila koordinator memilih panggil_llm, oper callable
    lambda prompt: P.call_llm(prompt) dari buku_umum_pipeline, atau
    jalur combo yang setara, bukan model hardcode. Perhatian: jalur
    ini hanya efektif bila propagasi di atas sudah diperbaiki,
    atau bila koordinator memakai Jalur B.

(2) Hook konsolidasi pustaka, di app/penyusunan_buku.py, di dalam
    susun(), blok kartu buku-referensi sebelum rakit (sekitar baris
    486 sampai 495, refs_rakit dari kumpulkan_pustaka, rakit di
    sekitar baris 504):
      from . import sitasi_anti_gagal as _SG
      teks_per_bab = {}
      for _n in sorted(k for k in outline if isinstance(k, int)):
          _p = os.path.join(keluar, "bab%d" % _n, "bab%d.txt" % _n)
          if os.path.exists(_p):
              with open(_p, encoding="utf-8") as _f:
                  teks_per_bab[_n] = _f.read()
      refs_panen = _RI.kumpulkan_pustaka(keluar, outline)
      refs_rakit = _SG.gabung_pustaka(teks_per_bab, refs_panen)
    Parameter gabung_pustaka: teks_per_bab (dict nomor bab ke teks
    bab yang SUDAH diperbaiki sitasi, dibaca dari disk sesudah pass
    per bab), refs_panen (list string dari kumpulkan_pustaka yang
    sudah ada). Fallback lama (gagal kumpul lanjut dengan pustaka
    kosong) sebaiknya tidak lagi menelan gagal sitasi: bila
    gabung_pustaka raise, biarkan naik ke except susun() supaya
    tidak diam-diam jadi pustaka kosong.
"""
