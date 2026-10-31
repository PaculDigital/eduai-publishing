"""Prioritas sumber artikel, Gas Bos 31 Okt 2026 19:03, diubah
menjadi seimbang 2-2-2-2 atas keputusan Bos 31 Okt 2026 19:36,
yang menggantikan prioritas Scopus penuh.

Urutan kelompok yang sama dipakai di tiga tempat:
1. Tampilan artikel pendukung di halaman proses, lewat
   urutkan_prioritas_sumber (Scopus dulu, stabil, bukan seimbang,
   karena tampilan hanya mengurutkan snapshot yang sudah seimbang).
2. Pemilihan snapshot panen di _refs_dari_harvest, lewat
   pilih_seimbang, sebelum potong 8.
3. Jalur cache hit di panen_semua, lewat pilih_seimbang, sebelum
   tulis_snapshot, supaya judul berulang tidak lolos dari seimbang.

Aturan seimbang, tepatnya: dari kandidat yang SUDAH lolos saring
relevansi dan filter tahun, sesudah dedup, ambil kuota 2 per sumber
(2 Scopus, 2 OpenAlex, 2 CrossRef, 2 Garuda), total 8, urutan
kelompok Scopus dulu, lalu OpenAlex, lalu CrossRef, lalu Garuda,
dan di dalam tiap sumber pertahankan urutan asli (stabil).
Bila satu sumber kurang dari 2, slot yang kurang diisi dari sumber
lain menurut prioritas Scopus, OpenAlex, CrossRef, Garuda, lain,
tetap dalam urutan asli di dalam sumber, sampai total 8 atau sampai
kandidat habis. Tidak pernah mengarang artikel, dan gerbang minimum
8 yang sudah ada tidak diubah di sini.

Sumber dinormalisasi huruf kecil dan dicocokkan mengandung nama,
supaya variasi ejaan seperti CrossRef dan Crossref diperlakukan sama.
Modul ini murni, tanpa impor aplikasi, supaya bisa dipakai dari
app/proses.py, app/pra_panen.py, maupun dari buku_umum_pipeline.py
tanpa impor melingkar.
"""

PRIORITAS_SUMBER = {
    'scopus': 0,
    'openalex': 1,
    'crossref': 2,
    'garuda': 3,
}

KUOTA_SEIMBANG_PER_SUMBER = 2
TOTAL_SEIMBANG = 8


def prioritas_sumber(nama):
    """Angka prioritas satu nama sumber, lain = 4."""
    if not nama:
        return 4
    kunci = str(nama).strip().lower()
    for nama_prioritas, angka in PRIORITAS_SUMBER.items():
        if nama_prioritas in kunci:
            return angka
    return 4


def sumber_dari_item(item):
    """Ambil nama sumber dari satu item artikel, dalam bentuk apa pun."""
    if isinstance(item, dict):
        return item.get('sumber') or item.get('source') or ''
    sumber = getattr(item, 'sumber', None)
    if sumber:
        return sumber
    return getattr(item, 'source', '') or ''


def urutkan_prioritas_sumber(daftar):
    """Urutkan daftar artikel dengan prioritas sumber, stabil.

    Masukan bukan list atau tuple dikembalikan apa adanya sebagai
    list kosong, supaya pemanggil display-only tidak error.
    Daftar asli tidak diubah, hasil adalah list baru.
    Dipakai tampilan saja, bukan pemilihan snapshot.
    """
    if not isinstance(daftar, (list, tuple)):
        return []
    return sorted(list(daftar),
                  key=lambda item: prioritas_sumber(sumber_dari_item(item)))


_KATA_HENTI_TEMA = {
    'dan', 'atau', 'dengan', 'dari', 'untuk', 'dalam', 'yang', 'ini',
    'ke', 'oleh', 'sebagai', 'antara', 'serta', 'tentang', 'pada',
    'di', 'the', 'of', 'on', 'and', 'for', 'in', 'to', 'a', 'an',
}

# Kata yang ada di hampir semua judul bab buku ini: bukan pembeda tema,
# jadi tidak dipakai sebagai kata tema (dipakai tetap di saringan inti
# pustaka, bukan di sini).
_KATA_GENERIK_BUKU = {
    'umkm', 'usaha', 'mikro', 'kecil', 'menengah', 'sme', 'msme',
    'digital', 'transformasi', 'transformation', 'ekonomi', 'economy',
    'bisnis', 'business', 'skala', 'scale', 'lintas', 'dimensi',
    'dimension', 'dimensions',
}

# Frasa inti buku: artikel yang memuat salah satunya dianggap cocok
# untuk bab mana pun (literatur inti transformasi digital), tanpa
# memandang kata tema bab.
_FRASA_INTI = (
    'digital transformation', 'transformasi digital',
    'technology adoption', 'adopsi teknologi', 'digital adoption',
    'adopsi digital', 'digital economy', 'ekonomi digital',
    'digital maturity', 'digitalization', 'digitalisasi',
)

# Sinonim Inggris untuk kata tema Indonesia yang umum di judul bab.
_SINONIM_TEMA = {
    'strategi': {'strategy', 'strategic'},
    'adopsi': {'adoption', 'adopt', 'adopting'},
    'kinerja': {'performance'},
    'dampak': {'impact', 'effect', 'effects', 'influence'},
    'sintesis': {'synthesis', 'synthesizing'},
    'integrasi': {'integration', 'integrated'},
    'ekosistem': {'ecosystem'},
    'kerangka': {'framework'},
    'konseptual': {'conceptual'},
    'lanskap': {'landscape'},
    'batasan': {'limitation', 'limitations', 'boundary', 'boundaries'},
    'teknologi': {'technology', 'technological'},
    'informasi': {'information'},
    'komunikasi': {'communication'},
    'agenda': {'agenda'},
    'riset': {'research'},
    'mendatang': {'future'},
    'global': {'global'},
    'lokal': {'local'},
    'berkembang': {'developing'},
    'empiris': {'empirical'},
    'keuangan': {'financial', 'finance'},
    'metrik': {'metric', 'metrics'},
    'nilai': {'value'},
    'kematangan': {'maturity'},
    'keselarasan': {'alignment'},
    'determinan': {'determinant', 'determinants'},
    'institusional': {'institutional'},
    'individu': {'individual'},
    'pemilik': {'owner', 'owners'},
    'tekanan': {'pressure', 'pressures'},
    'model': {'model'},
    'penerimaan': {'acceptance'},
    'keunggulan': {'advantage', 'competitive'},
    'kompetitif': {'competitive'},
    'operasional': {'operational', 'operations'},
    'keberlanjutan': {'sustainability', 'sustainable'},
    'kebijakan': {'policy', 'policies'},
    'fasilitasi': {'facilitation'},
    'pemerintah': {'government'},
    'konvergensi': {'convergence'},
    'manajemen': {'management'},
    'sistem': {'system', 'systems'},
    'pembangunan': {'development'},
    'metodologis': {'methodological'},
    'implikasi': {'implication', 'implications'},
    'penelitian': {'research', 'study', 'studies'},
    'kajian': {'study', 'studies', 'review'},
    'teori': {'theory', 'theoretical'},
    'pendekatan': {'approach', 'approaches'},
    'perbandingan': {'comparison', 'comparative'},
    'kritis': {'critical'},
    'kontribusi': {'contribution'},
    'teoretis': {'theoretical'},
    'praktis': {'practical'},
    'lingkup': {'scope'},
    'ruang': {'scope'},
}

# Pola platform: artikel UMKM + platform digital (mis. e-commerce)
# tetap cocok meski tanpa kata tema bab, karena itu bukti penerapan.
_KATA_SME = ('umkm', 'sme', 'msme', 'usaha kecil', 'small medium')
_KATA_PLATFORM = ('e-commerce', 'ecommerce', 'platform', 'online',
                  'payment', 'pembayaran', 'system', 'sistem')


def kata_tema(judul_bab):
    """Kata tema dari judul bab: token isi minus kata henti dan kata
    generik buku, plus sinonim Inggrisnya. Kosong bila judul hanya
    berisi kata generik (saat itu saringan tema tidak dipakai)."""
    import re as _re
    teks = (judul_bab or '').lower()
    # Frasa multi-kata dulu: 'ruang lingkup' -> 'scope', 'masa depan'
    # -> 'future', 'negara berkembang' -> 'developing'.
    tema = set()
    if 'ruang lingkup' in teks:
        tema.add('scope')
    if 'masa depan' in teks:
        tema.add('future')
    if 'negara berkembang' in teks:
        tema.add('developing')
    for tok in _re.split(r'[^a-z]+', teks):
        if len(tok) < 4:
            continue
        if tok in _KATA_HENTI_TEMA or tok in _KATA_GENERIK_BUKU:
            continue
        tema.add(tok)
        tema.update(_SINONIM_TEMA.get(tok, ()))
    return tema


def cocok_tema(judul_artikel, judul_bab):
    """True bila artikel cocok dengan tema bab ATAU literatur inti.

    Cocok bila judul artikel memuat frasa inti, kata tema bab (atau
    sinonimnya), atau pola SME + platform. Judul bab tanpa kata tema
    (hanya kata generik) selalu cocok (fail-soft, saringan tidak
    dipakai). Dipakai sebagai PREFERENSI urutan di pilih_seimbang,
    bukan penghapus: artikel tidak cocok hanya turun urutan dan tetap
    dipakai mengisi bila kandidat cocok tidak cukup mencapai total.
    """
    teks = (judul_artikel or '').lower()
    if not teks.strip():
        return False
    for frasa in _FRASA_INTI:
        if frasa in teks:
            return True
    tema = kata_tema(judul_bab)
    if not tema:
        return True
    if any(k in teks for k in tema):
        return True
    if any(k in teks for k in _KATA_SME) \
            and any(k in teks for k in _KATA_PLATFORM):
        return True
    return False


def _identitas_default(item):
    """Identitas satu artikel untuk aturan artikel-berbeda-antar-bab.

    Pasangan (baris_snapshot, ref) di jalur cache: artikel_id baris.
    Dict artikel biasa: DOI bila ada, kalau tidak judul + tahun.
    Selain itu: DOI/title dari atribut, kalau tidak ada pakai id()
    objek (tidak pernah dianggap sama dengan artikel lain).
    """
    if isinstance(item, (list, tuple)) and len(item) == 2 \
            and isinstance(item[0], dict):
        aid = item[0].get('artikel_id')
        if aid is not None:
            return ('id', aid)
        item = item[1]
    if isinstance(item, dict):
        doi = (item.get('doi') or '').strip().lower()
        if doi:
            return ('doi', doi)
        judul = (item.get('title') or item.get('judul') or '').strip().lower()
        tahun = str(item.get('year') or item.get('tahun') or '')
        if judul:
            return ('judul', judul, tahun)
        return ('obj', id(item))
    doi = str(getattr(item, 'doi', '') or '').strip().lower()
    if doi:
        return ('doi', doi)
    judul = str(getattr(item, 'title', '') or getattr(item, 'judul', '')
                or '').strip().lower()
    tahun = str(getattr(item, 'year', '') or getattr(item, 'tahun', '') or '')
    if judul:
        return ('judul', judul, tahun)
    return ('obj', id(item))


def _pilih_dari_kelompok(kelompok, kuota, total, sudah, ambil_id):
    """Jalankan aturan kuota + isi kekurangan di atas satu kelompok.

    sudah: hasil sejauh ini (dipakai sebagai awal, supaya pengisian
    dari daftar kedua tidak mengulang kuota dari awal). Item yang
    identitasnya sudah ada di hasil dilewati, jadi hasil tidak pernah
    memuat artikel yang sama dua kali.
    """
    terpilih = list(sudah)
    sudah_id = set()
    for item in terpilih:
        try:
            sudah_id.add(ambil_id(item))
        except Exception:
            pass
    for angka in (0, 1, 2, 3):
        for item in kelompok[angka][:kuota]:
            if len(terpilih) >= total:
                return terpilih[:total]
            try:
                iid = ambil_id(item)
            except Exception:
                iid = ('obj', id(item))
            if iid in sudah_id:
                continue
            sudah_id.add(iid)
            terpilih.append(item)
    for angka in (0, 1, 2, 3, 4):
        for item in kelompok[angka][kuota:]:
            if len(terpilih) >= total:
                return terpilih[:total]
            try:
                iid = ambil_id(item)
            except Exception:
                iid = ('obj', id(item))
            if iid in sudah_id:
                continue
            sudah_id.add(iid)
            terpilih.append(item)
    return terpilih


def pilih_seimbang(daftar, kuota=KUOTA_SEIMBANG_PER_SUMBER,
                   total=TOTAL_SEIMBANG, kunci=None, terpakai=None,
                   identitas=None, cocok=None):
    """Pilih artikel seimbang dari daftar kandidat, stabil.

    daftar: list atau tuple item, dalam urutan asli. Bukan list atau
    tuple menghasilkan list kosong. kunci: fungsi opsional yang
    menerima satu item dan mengembalikan nama sumbernya, dipakai
    bila item bukan dict artikel biasa, misalnya pasangan
    (baris_snapshot, ref) di jalur cache hit, di mana sumber ada
    di elemen pertama pasangan. Tanpa kunci, sumber diambil dengan
    sumber_dari_item.

    terpakai: himpunan identitas artikel yang SUDAH terpilih untuk
    bab-bab sebelumnya dalam job yang sama (paket sempurna, Gas Bos
    31 Okt 2026 malam: artikel berbeda per bab). Bila diisi, kandidat
    yang belum terpakai dipilih dulu dengan aturan kuota yang sama,
    dan kekurangan HANYA diisi dari artikel terpakai bila kandidat
    belum terpakai tidak cukup mencapai total, supaya gerbang
    minimum 8 tidak berubah dan tidak ada artikel yang dikarang.
    Tanpa terpakai, perilaku sama persis seperti sebelumnya.
    cocok: fungsi opsional item -> bool (cocok tema bab). Bila diisi,
    di dalam tiap kelompok sumber, artikel yang cocok diurutkan dulu
    (stabil), jadi kuota per sumber diambil dari artikel yang cocok
    dulu dan artikel tidak cocok hanya mengisi kekurangan. Ini
    PREFERENSI urutan, bukan penghapus: artikel tidak cocok tetap
    dipakai bila kandidat cocok tidak cukup.
    identitas: fungsi opsional item -> identitas; tanpa itu dipakai
    _identitas_default (artikel_id untuk pasangan, DOI, lalu
    judul + tahun).

    Langkah: kelompokkan menurut prioritas (Scopus, OpenAlex,
    CrossRef, Garuda, lain), pertahankan urutan asli di dalam tiap
    kelompok, ambil sampai kuota dari tiap kelompok bernama dalam
    urutan prioritas, lalu isi kekurangan dari sisa kelompok dalam
    urutan prioritas yang sama (termasuk kelompok lain di akhir),
    sampai total atau sampai kandidat habis. Daftar asli tidak
    diubah, hasil adalah list baru, tanpa duplikat, tanpa artikel
    yang tidak ada di masukan.
    """
    if not isinstance(daftar, (list, tuple)):
        return []
    if total is None or total <= 0:
        return []
    if kuota is None or kuota < 0:
        kuota = 0
    ambil_sumber = kunci if kunci is not None else sumber_dari_item
    ambil_id = identitas if identitas is not None else _identitas_default
    terpakai_set = set(terpakai) if terpakai else set()

    def _kelompokkan(items):
        kelompok = {0: [], 1: [], 2: [], 3: [], 4: []}
        for item in items:
            try:
                nama = ambil_sumber(item)
            except Exception:
                nama = ''
            kelompok[prioritas_sumber(nama)].append(item)
        if cocok is not None:
            for angka in kelompok:
                grp = kelompok[angka]
                ya = []
                tidak = []
                for item in grp:
                    try:
                        ok = bool(cocok(item))
                    except Exception:
                        ok = True
                    (ya if ok else tidak).append(item)
                kelompok[angka] = ya + tidak
        return kelompok

    if not terpakai_set:
        return _pilih_dari_kelompok(_kelompokkan(daftar), kuota, total,
                                    [], ambil_id)
    belum = []
    sudah_pakai = []
    for item in daftar:
        try:
            iid = ambil_id(item)
        except Exception:
            iid = ('obj', id(item))
        if iid in terpakai_set:
            sudah_pakai.append(item)
        else:
            belum.append(item)
    terpilih = _pilih_dari_kelompok(_kelompokkan(belum), kuota, total,
                                    [], ambil_id)
    if len(terpilih) < total and sudah_pakai:
        terpilih = _pilih_dari_kelompok(_kelompokkan(sudah_pakai), kuota,
                                        total, terpilih, ambil_id)
    return terpilih
