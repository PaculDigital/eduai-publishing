"""PERBAIKI app/pustaka.py → RUMUS PICO: AND antar KONSEP, OR di dalam konsep.

🔴 AKAR MASALAH (ditemukan 26Sep26 dari uji naskah Bosch):
   Versi awal memecah tema jadi kata kunci lepas, lalu digabung dengan `OR`:
     TITLE-ABS-KEY("adolescent") OR TITLE-ABS-KEY("aktivitas") OR ...
   ⇒ presisi JATUH: kata 'adolescent'/'aktivitas' cocok di mana-mana
     → artikel COVID-19, Brain Imaging, lithium battery ikut masuk.

✅ CARA BENAR (dari skill Bos `penelitian-ilmiah` baris 73/216 — kerangka
   PICO/SPIDER + praktik ilmu perpustakaan):
   KONSEP (bukan kata) digabung dengan AND; sinonim di dalam konsep dengan OR:
     ( "physical activity" OR exercise OR training )
     AND ( "menstrual cycle" OR menstruation OR amenorrhea )
     AND ( athlete OR sportswoman )
   ⇒ Artikel harus memuat KETIGA konsep sekaligus → mustahil meleset jauh.

📌 PELAJARAN dari eduai-lab/tools/referensi.py (SUDAH TERUJI 50/50):
   · Kata kunci diberikan sebagai DAFTAR PILIHAN, bukan pecahan otomatis
   · Scopus WAJIB httpx/requests + params (jangan encode manual)
   · Garuda: query PER kata kunci
"""
import pathlib
import re

P = pathlib.Path('/opt/data/services/eduai-publishing/app/pustaka.py')
s = P.read_text()

# ══════════════════════════════════════════════════════════════════════════
#  1. KAMUS KONSEP  (ID → konsep + sinonim EN/ID)
# ══════════════════════════════════════════════════════════════════════════
KAMUS_LAMA_AWAL = s.index('# ── Kamus ID ↔ EN')
KAMUS_LAMA_AKHIR = s.index('_KATA_HENTI = {')
KAMUS_BARU = '''# ── KAMUS KONSEP (ID → sinonim EN & ID) ──────────────────────────────────
#  Dipakai untuk menyusun RUMUS PICO: tiap KONSEP jadi satu grup (OR di
#  dalamnya), lalu antar konsep digabung dengan AND.
KAMUS_KONSEP: dict[str, dict] = {
    'aktivitas fisik': {'en': ['physical activity', 'exercise', 'training'],
                        'id': ['aktivitas fisik', 'latihan fisik', 'olahraga']},
    'siklus menstruasi': {'en': ['menstrual cycle', 'menstruation',
                                 'menstrual'],
                          'id': ['siklus menstruasi', 'menstruasi']},
    'amenore': {'en': ['amenorrhea', 'amenorrhoea'],
                'id': ['amenore', 'amenorea']},
    'atlet': {'en': ['athlete', 'athletes', 'sportswoman', 'sports women'],
              'id': ['atlet', 'atlet wanita', 'olahragawan']},
    'remaja': {'en': ['adolescent', 'adolescents', 'teenager'],
               'id': ['remaja', 'remaja putri']},
    'keputusan pembelian': {'en': ['purchase decision', 'buying decision'],
                            'id': ['keputusan pembelian']},
    'kualitas produk': {'en': ['product quality'], 'id': ['kualitas produk']},
    'harga': {'en': ['price', 'pricing'], 'id': ['harga']},
    'promosi': {'en': ['promotion', 'advertising'],
                'id': ['promosi', 'iklan']},
    'kepuasan kerja': {'en': ['job satisfaction'], 'id': ['kepuasan kerja']},
    'kinerja karyawan': {'en': ['employee performance', 'job performance'],
                         'id': ['kinerja karyawan', 'kinerja pegawai']},
    'kepemimpinan': {'en': ['leadership'], 'id': ['kepemimpinan']},
    'motivasi': {'en': ['motivation'], 'id': ['motivasi']},
    'minat belajar': {'en': ['learning interest'], 'id': ['minat belajar']},
    'hasil belajar': {'en': ['learning outcome', 'learning achievement',
                             'academic achievement'],
                      'id': ['hasil belajar', 'prestasi belajar']},
    'literasi digital': {'en': ['digital literacy'], 'id': ['literasi digital']},
    'umkm': {'en': ['SME', 'small medium enterprise', 'MSME'],
             'id': ['umkm', 'usaha mikro kecil menengah']},
    'ekonomi digital': {'en': ['digital economy'], 'id': ['ekonomi digital']},
    'tata kelola': {'en': ['governance'], 'id': ['tata kelola']},
    'etika bisnis': {'en': ['business ethics'], 'id': ['etika bisnis']},
    'pendidikan tinggi': {'en': ['higher education'], 'id': ['pendidikan tinggi']},
    'kesehatan mental': {'en': ['mental health', 'psychological well-being'],
                         'id': ['kesehatan mental']},
    'kecemasan': {'en': ['anxiety', 'anxiety disorder'], 'id': ['kecemasan']},
    'cricket': {'en': ['cricket'], 'id': ['kriket', 'kricket']},
    'cedera': {'en': ['injury', 'injuries'], 'id': ['cedera', 'cidera']},
}

''' 
s = s[:KAMUS_LAMA_AWAL] + KAMUS_BARU + s[KAMUS_LAMA_AKHIR:]

# ══════════════════════════════════════════════════════════════════════════
#  2. FUNGSI BARU: konsep dari judul (PICO) + rumus AND/OR
# ══════════════════════════════════════════════════════════════════════════
FUNGSI_BARU = '''

# ══════════════════════════════════════════════════════════════════════════
#  RUMUS PICO — AND antar konsep, OR di dalam konsep  (26Sep26)
# ══════════════════════════════════════════════════════════════════════════
def konsep_dari_judul(judul: str) -> list[dict]:
    """Pecah judul penelitian → daftar KONSEP (bukan kata).

    Dasar: skill penelitian-ilmiah v2.2 (framework PICO/SPIDER) + pelajaran
    eduai-lab (kata kunci = DAFTAR PILIHAN, bukan pecahan otomatis).

    Contoh:
      "Pengaruh Aktivitas Fisik terhadap Siklus Menstruasi pada Atlet Remaja"
      → [ {konsep:'aktivitas fisik', en:[...], id:[...]},
          {konsep:'siklus menstruasi', ...},
          {konsep:'atlet', ...},
          {konsep:'remaja', ...} ]
    """
    t = (judul or '').lower()
    konsep: list[dict] = []
    lihat: set[str] = set()
    #  frasa panjang dulu (biar 'siklus menstruasi' menang atas 'menstruasi')
    for frasa in sorted(KAMUS_KONSEP, key=len, reverse=True):
        if frasa in t and frasa not in lihat:
            lihat.add(frasa)
            d = KAMUS_KONSEP[frasa]
            konsep.append({'konsep': frasa, 'en': list(d['en']),
                           'id': list(d['id'])})
    return konsep


def rumus_scopus(konsep: list[dict], maks_konsep: int = 3) -> str:
    """Susun query Scopus: AND antar konsep, OR di dalam konsep.

        TITLE-ABS-KEY("physical activity" OR exercise)
      AND TITLE-ABS-KEY("menstrual cycle" OR menstruation)

    ⚠️ Konsep dibatasi `maks_konsep` (default 3 = PICO inti) supaya hasil
       tidak habis oleh syarat yang terlalu ketat.
    """
    bagian = []
    for k in konsep[:maks_konsep]:
        sin = [x for x in (k.get('en') or []) if x.strip()]
        if not sin:
            continue
        bagian.append('TITLE-ABS-KEY(' + ' OR '.join(
            f'"{x}"' for x in sin) + ')')
    return ' AND '.join(bagian)


def rumus_openalex(konsep: list[dict], maks_konsep: int = 3) -> str:
    """OpenAlex: pakai SEARCH hanya untuk konsep PERTAMA (yang paling inti),
    lalu saring konsep lain di `_nyambung` — karena OpenAlex `search` tidak
    mendukung sintaks boolean AND yang andal.

    ⚠️ Pelajaran: `search` OpenAlex mencocokkan tiap kata → kalau semua
       konsep dimasukkan, presisi jatuh. Satu frasa inti = paling aman.
    """
    for k in konsep:
        en = [x for x in (k.get('en') or []) if x.strip()]
        if en:
            return en[0]
    return ''


def rumus_crossref(konsep: list[dict], maks_konsep: int = 2) -> str:
    """CrossRef: `query.bibliographic` dengan 2 frasa konsep teratas."""
    frasa = []
    for k in konsep[:maks_konsep]:
        en = [x for x in (k.get('en') or []) if x.strip()]
        if en:
            frasa.append(en[0])
    return ' '.join(frasa)


def konsep_id(konsep: list[dict]) -> list[str]:
    """Kata kunci untuk Garuda (Indonesia) — frasa ID utama tiap konsep."""
    keluar = []
    for k in konsep:
        for x in (k.get('id') or []):
            if x and x not in keluar:
                keluar.append(x)
                break
    return keluar


def kata_kunci(tema: str) -> dict:
    """Bentuk lama DIPERTAHANKAN (dipakai bagian lain) — isinya kini dari PICO.

    Menambah kunci baru:
       konsep : daftar konsep (buat audit manusia)
       q_scopus / q_openalex / q_crossref / kw_garuda : rumus siap pakai
    """
    k = konsep_dari_judul(tema)
    en_l, id_l = [], []
    for x in k:
        en_l += [w for w in x['en'] if w not in en_l]
        id_l += [w for w in x['id'] if w not in id_l]
    #  sisa = kata tema yang tak dikenali kamus (bukan konsep)
    dikenal = ' '.join(KAMUS_KONSEP.keys())
    sisa = [w.strip('.,;:!?()') for w in (tema or '').lower().split()
            if len(w) > 3 and w.strip('.,;:!?()') not in dikenal
            and w.strip('.,;:!?()') not in _KATA_HENTI]
    return {'en': en_l, 'id': id_l, 'sisa': sisa,
            'frasa': rumus_openalex(k),
            'konsep': k,
            'q_scopus': rumus_scopus(k),
            'q_openalex': rumus_openalex(k),
            'q_crossref': rumus_crossref(k),
            'kw_garuda': konsep_id(k)}

'''
#  sisipkan sebelum _nyambung
s = s.replace('def _nyambung(artikel: dict, kw: dict) -> bool:', FUNGSI_BARU.lstrip('\n') + '\ndef _nyambung(artikel: dict, kw: dict) -> bool:', 1)

P.write_text(s)
print('✅ KAMUS_KONSEP + fungsi PICO ditambahkan')
