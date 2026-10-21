"""JEV BUKU UMUM — membaca BENTUK naskah buku (bukan naskah akademik).

KENAPA BERKAS INI ADA (SOT 20 Okt 2026)
═══════════════════════════════════════════════════════════════════════════
Jev naskah akademik (`peta3_jev.py`) memakai pertanyaan:
    'bab' / 'subbab' / 'paragraf' / 'biasa'
Pertanyaan itu TERUKUR SALAH untuk buku:

    naskah akademik (Asih) : 2.224 baris / 159.909 kar / 1 baris ≈ 69 kar
    buku umum (bab1)       :    14 baris /  16.199 kar / 1 baris = 1 paragraf

⇒ Buku butuh pertanyaannya SENDIRI. Inilah Jev Buku Umum.

2 PEKERJAAN (batas peran: BENTUK saja, BUKAN mutu)
  B1  baris ini JUDUL atau ISI?          → choice 2 pilihan
  B3  paragraf ini RENTETAN SETARA?      → noul (pagar anti-daftar)

HASIL UKUR 20 Okt 2026 (bab1 buku "Ayo Mengenal Cuaca"):
  B1 : 13/14 benar (92,9%) · 0,91 dtk · 14 pertanyaan · 1 panggilan
  B3 : 10/11 TETAP PARAGRAF · 0,59 dtk · 1 panggilan
       ⇒ cerita anak TIDAK berubah jadi daftar (bandingkan regex: 170 butir)

ATURAN RESMI YANG DIPATUHI (skill `typesafe-jev` / `typesafe-pertanyaan`)
  · field nama = `instructions` (BUKAN `pertanyaan`)
  · noul ⛔ TANPA `criteria` · choice ✅ criteria OBJEK
  · 1 kandidat = 1 nama = 1 jawaban (`b7`, `d3`) — JANGAN ditumpuk
  · FAKTA POSITIF wajib (panjang, jumlah kalimat) — kalimat simpel = 0,224 ❌
  · JANGAN daftar larangan dalam instructions (0,844 → 0,32) ❌
  · BACA `p` LANGSUNG, jangan `abs(2p-1)`
  · jalan tol `app/jev.py` — satu-satunya pintu

HARAM (zona gagal, sudah terbukti):
  · menilai MUTU tulisan ("bagus/tidak")
  · menyuruh Jev MENGHITUNG ("berapa paragraf?") — kelemahan #2
  · menyuruh Jev MENULIS/MENYALIN teks atau POSISI karakter — kelemahan #9
  · membandingkan antar baris — tiap pertanyaan INDEPENDEN
"""
import hashlib
import json
import logging
import os
import re

import tata_paragraf as T

log = logging.getLogger(__name__)

# ── Ambang (SATU SUMBER supaya tak ditulis ulang di tempat lain) ─────────
#   B3 memakai `p` sebagai SAKLAR — keputusan SENGAJA: lebih baik tidak
#   mengubah apa pun daripada mengubah cerita jadi daftar.
AMBANG_RENTETAN = 0.50      # p >= ini ⇒ boleh jadi daftar
AMBANG_GOYANG = 0.50        # B1: p tertinggi < ini ⇒ ragu (perlakukan isi)
BARIS_MIN_KAR = 8           # lebih pendek dari ini bukan judul/isi berarti
PANJANG_JUDUL_MAKS = 90     # judul wajar; lebih panjang ⇒ hampir pasti isi
KALIMAT_JUDUL_MAKS = 2      # judul bukan kalimat panjang

_POLA_PENANDA = re.compile(
    r'^\s*(?:\[|Sumber\s*:|Tabel\s+\d|Gambar\s+\d'
    r'|Daftar\s+(?:Referensi|Pustaka|Isi|Tabel|Gambar)'
    r'|Kata\s+Pengantar|Prakata|Ucapan\s+Terima\s+Kasih'
    r'|Tentang\s+Penulis|Glosarium|Lampiran|Indeks)\b', re.I)

#  Cache sidik jari — pola `tahapan_diagram.py` (hemat 100% pada ronde ke-2).
_CACHE_NAMA = '_jev_buku.json'


def _berkas_cache():
    """Cache di samping data (BUKAN /app yang ephemeral)."""
    for d in ('/app/data', '/app/uploads', '/tmp'):
        if os.path.isdir(d):
            return os.path.join(d, _CACHE_NAMA)
    return os.path.join('/tmp', _CACHE_NAMA)


def _sidik(teks):
    return hashlib.sha256((teks or '').encode('utf-8')).hexdigest()


def _int_key(d):
    """Normalisasi kunci dict hasil JSON: '3' → 3.

    🚨 JEBAKAN TERUKUR 20 Okt 2026: JSON MEMAKSA semua kunci dict jadi
    STRING. Membaca `bentuk.get(0)` (int) pada cache yang kuncinya '0'
    (str) SELALU None ⇒ peta tampak kosong, `## BAB 1` jadi paragraf,
    dan seluruh perbaikan HILANG tanpa error. Wajib dinormalkan.
    """
    if not isinstance(d, dict):
        return {}
    return {int(k): v for k, v in d.items() if str(k).lstrip('-').isdigit()}


def _cache_baca(sidik):
    try:
        with open(_berkas_cache(), encoding='utf-8') as f:
            data = json.load(f).get(sidik)
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    #  Normalisasi kunci — cache lama & baru sama-sama terbaca.
    for k in ('bentuk', 'p_b1', 'p_b3', 'boleh_daftar'):
        if k in data:
            data[k] = _int_key(data[k])
    if not data.get('bentuk'):
        return None                     # cache rusak/kosong ⇒ jangan dipakai
    return data


def _cache_tulis(sidik, peta):
    """Tulis atomik. JANGAN simpan kalau Jev mati (balas None)."""
    f = _berkas_cache()
    try:
        isi = {}
        if os.path.exists(f):
            try:
                with open(f, encoding='utf-8') as g:
                    isi = json.load(g) or {}
            except ValueError:
                isi = {}
        isi[sidik] = peta
        tmp = f + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as g:
            json.dump(isi, g, ensure_ascii=False)
        os.replace(tmp, f)
    except OSError as e:
        log.warning('[jev_buku] cache tak tertulis (%s) — lanjut', e)


# ══════════════════════════════════════════════════════════════════════════
# 1. SIAPKAN BARIS + FAKTA POSITIF
# ══════════════════════════════════════════════════════════════════════════
def _baris_naskah(teks):
    return [b.strip() for b in (teks or '').split('\n') if b.strip()]


def _layak_jadi_kandidat(t):
    """Kandidat B1: baris bermakna, bukan penanda/caption (gratis, tanpa Jev)."""
    if not t or len(t) < BARIS_MIN_KAR:
        return False
    if _POLA_PENANDA.match(t):
        return False
    return True


def _paket_b1(baris, kand):
    """Bahan + pertanyaan B1 — FAKTA POSITIF per kandidat (1 nama = 1 jawaban)."""
    paket, tanya = {}, {}
    for i in kand:
        nm = f'b{i}'
        t = baris[i]
        sesudah = baris[i + 1] if i + 1 < len(baris) else ''
        paket[nm] = {
            'sebelum': baris[i - 1][:90] if i > 0 else '(awal naskah)',
            'tengah': t[:160],
            'sesudah': sesudah[:90],
            'panjang_tengah': len(t),
            'jumlah_kalimat_tengah': len(T.pecah_kalimat(t)),
            'jumlah_kalimat_sesudah': len(T.pecah_kalimat(sesudah)),
        }
        tanya[nm] = {
            'type': 'choice',
            'instructions': (
                f"Baris `{nm}.tengah` panjangnya `{nm}.panjang_tengah` "
                f"karakter dan memuat `{nm}.jumlah_kalimat_tengah` kalimat. "
                f"Baris `{nm}.sesudah` setelahnya memuat "
                f"`{nm}.jumlah_kalimat_sesudah` kalimat. "
                f"Baris tengah ini perannya apa?"),
            'criteria': {
                'judul': 'Judul bagian — nama singkat bagian, bukan kalimat',
                'isi': 'Isi/paragraf — kalimat yang menguraikan sesuatu',
            },
        }
    return paket, tanya


def _paket_b3(baris, isi_idx):
    """Bahan + pertanyaan B3 — pagar anti-daftar (noul, TANPA criteria)."""
    paket, tanya = {}, {}
    for i in isi_idx:
        nm = f'd{i}'
        paket[nm] = {
            'tengah': baris[i][:200],
            'jumlah_kalimat': len(T.pecah_kalimat(baris[i])),
            'panjang_karakter': len(baris[i]),
        }
        tanya[nm] = {
            'type': 'noul',
            'instructions': (
                f"Paragraf `{nm}.tengah` memuat `{nm}.jumlah_kalimat` kalimat "
                f"dengan panjang `{nm}.panjang_karakter` karakter. "
                f"Apakah paragraf ini merangkai BEBERAPA HAL YANG SETARA "
                f"sehingga lebih tepat disajikan sebagai daftar?"),
        }
    return paket, tanya


def _ambil_choice(j):
    v = (j or {}).get('choice')
    if isinstance(v, dict):
        v = v.get('id') or v.get('label')
    return v


# ══════════════════════════════════════════════════════════════════════════
# 2. INTI — petakan bentuk naskah buku
# ══════════════════════════════════════════════════════════════════════════
def petakan_buku(teks, pakai_cache=True):
    """Baca BENTUK naskah buku. Mengembalikan peta bentuk.

    Balikan dict:
      baris     : list baris asli
      bentuk    : {indeks: 'judul'|'isi'}
      p_b1      : {indeks: p}
      p_b3      : {indeks: p atau None}
      boleh_daftar : {indeks: bool}   ← hasil B3, dipakai tata_paragraf
      goyang    : [indeks]            ← B1 ragu, diperlakukan 'isi'
      jumlah    : {'baris','kandidat','judul','isi','gagal','gelombang'}
      waktu     : [detik per panggilan]
      dari_cache: bool
    """
    baris = _baris_naskah(teks)
    kand = [i for i in range(len(baris)) if _layak_jadi_kandidat(baris[i])]
    kosong = {
        'baris': baris, 'bentuk': {}, 'p_b1': {}, 'p_b3': {},
        'boleh_daftar': {}, 'goyang': [], 'waktu': [], 'gagal': 0,
        'gelombang': 0, 'dari_cache': False,
        'jumlah': {'baris': len(baris), 'kandidat': len(kand),
                   'judul': 0, 'isi': 0, 'gagal': 0},
    }
    if not kand:
        return kosong

    sidik = _sidik(teks)
    if pakai_cache:
        tersimpan = _cache_baca(sidik)
        if tersimpan:
            log.info('[jev_buku] dari SIMPANAN (sidik %s) — 0 panggilan',
                     sidik[:12])
            tersimpan['dari_cache'] = True
            return tersimpan

    import time
    from app import jev

    # ── B1 ──────────────────────────────────────────────────────────────
    paket, tanya = _paket_b1(baris, kand)
    t0 = time.time()
    jw = jev.tanya(json.dumps(paket, ensure_ascii=False), tanya) or {}
    waktu = [round(time.time() - t0, 2)]

    bentuk, p_b1, goyang = {}, {}, []
    gagal = 0
    for i in kand:
        nm = f'b{i}'
        j = jw.get(nm) or {}
        lab = _ambil_choice(j)
        p = j.get('confidence')
        p_b1[i] = p if isinstance(p, float) else None
        if lab in ('judul', 'isi'):
            bentuk[i] = lab
            #  p mepet = ragu. Perlakuan konservatif: anggap ISI
            #  (jangan mengangkat baris jadi judul kalau Jev ragu).
            if isinstance(p, float) and p < AMBANG_GOYANG:
                goyang.append(i)
                bentuk[i] = 'isi'
        else:
            gagal += 1
            bentuk[i] = 'isi'          # konservatif
    if not jw:
        gagal = len(kand)

    # ── B3 — hanya untuk baris yang Jev bilang ISI ──────────────────────
    isi_idx = [i for i in kand if bentuk.get(i) == 'isi']
    p_b3, boleh = {}, {}
    if isi_idx and jw:
        paket3, tanya3 = _paket_b3(baris, isi_idx)
        t1 = time.time()
        jw3 = jev.tanya(json.dumps(paket3, ensure_ascii=False), tanya3) or {}
        waktu.append(round(time.time() - t1, 2))
        for i in isi_idx:
            p = (jw3.get(f'd{i}') or {}).get('noul')
            p_b3[i] = p if isinstance(p, float) else None
            boleh[i] = bool(isinstance(p, float) and p >= AMBANG_RENTETAN)

    peta = {
        'baris': baris, 'bentuk': bentuk, 'p_b1': p_b1, 'p_b3': p_b3,
        'boleh_daftar': boleh, 'goyang': goyang, 'waktu': waktu,
        'gagal': gagal, 'gelombang': 2 if isi_idx else 1, 'dari_cache': False,
        'jumlah': {
            'baris': len(baris), 'kandidat': len(kand),
            'judul': sum(1 for v in bentuk.values() if v == 'judul'),
            'isi': sum(1 for v in bentuk.values() if v == 'isi'),
            'gagal': gagal,
        },
    }

    #  Simpan HANYA kalau Jev benar-benar menjawab — supaya gangguan
    #  sesaat tidak membeku jadi peta kosong selamanya.
    if gagal < len(kand):
        _cache_tulis(sidik, peta)
    return peta


def _ambil_boleh(peta, i):
    """Ambil putusan B3 untuk baris `i` — tahan kunci int MAUPUN str.

    🚨 JEBAKAN TERUKUR 20 Okt 2026: `boleh_daftar` disimpan ke cache JSON,
    dan JSON MEMAKSA kunci jadi STRING ('1', '2', …). Membacanya dengan
    `.get(1)` (int) TIDAK PERNAH cocok ⇒ pagar Jev diam-diam mati, dan
    narasi buku anak tetap diubah jadi 49 butir daftar. Wajib coba dua-duanya.
    """
    b = peta.get('boleh_daftar') or {}
    for k in (i, str(i)):
        if k in b:
            v = b[k]
            return bool(v) if v is not None else None
    return None


def _pecah_daftar_pustaka(baris):
    """Daftar pustaka: entri dipisah TAHUN `(2024).` / `(2011).` — bukan paragraf.

    Terukur 20 Okt 2026: 8 entri pustaka masuk sebagai SATU paragraf 13
    "kalimat" ⇒ gerbang menandainya paragraf kepanjangan, padahal bentuknya
    memang daftar. Ini pekerjaan KODE (pola pasti), bukan Jev.
    """
    t = (baris or '').strip()
    if len(t) < 200:
        return None
    #  Harus ada >=2 penanda tahun dalam kurung + URL/rujukan
    tahun = re.findall(r'\((?:19|20)\d{2}\)\.', t)
    if len(tahun) < 2:
        return None
    #  Pisah tepat SEBELUM pola tahun+entri berikutnya.
    bagian = re.split(r'(?<=\.)\s+(?=[A-Z][^()]{2,60}\((?:19|20)\d{2}\)\.)', t)
    bagian = [b.strip() for b in bagian if b.strip()]
    if len(bagian) < 2:
        return None
    return [('daftar_pustaka', '\n'.join(bagian))]


def blok_buku(teks, pakai_cache=True):
    """Ubah naskah buku jadi blok siap rakit: ('sub_heading'|'dll', isi, meta).

    ⚠️ BENTUK TRIPLE (20 Okt 2026): dulu blok = (jenis, isi) 2-elemen, dan
    pemanggil harus menebak indeks baris untuk memasangkan putusan Jev B3.
    TERUKUR SALAH: 1 baris bisa jadi >1 blok (penanda tabel/diagram dicabut)
    ⇒ 24 blok vs 14 baris ⇒ `boleh_daftar` TIDAK PERNAH terpasang, dan
    narasi buku anak tetap diubah jadi 42 butir daftar.
    Sekarang tiap blok membawa `meta = {'baris': indeks, 'boleh_daftar': bool|None}`
    sehingga pagar Jev SELALU ikut — tidak bisa hilang karena pergeseran indeks.

    Meta blok{'baris', 'boleh_daftar'}.
    """
    peta = petakan_buku(teks, pakai_cache=pakai_cache)
    boleh = peta.get('boleh_daftar') or {}
    blok = []
    for i, t in enumerate(peta['baris']):
        lab = peta['bentuk'].get(i)

        #  ⚠️ URUTAN WAJIB (terukur 20 Okt 2026 — 3 penanda HILANG):
        #  CABUT PENANDA DULU, baru pecah judul. Kalau dibalik, baris yang
        #  berisi `[TABEL 1.1: …]` dianggap "judul+isi" lalu penandanya
        #  ikut jadi paragraf ⇒ tabel/diagram HILANG dari .docx.
        potongan = _pecah_penanda(t)

        for jenis, isi in potongan:
            if jenis in ('tabel_marker', 'diagram_marker'):
                blok.append((jenis, isi, {'baris': i, 'boleh_daftar': None}))
                continue

            #  Teks biasa: cek apakah ini judul yang PASTI (##/###/label baku)
            potong = _pecah_judul_nempel(isi)
            if potong:
                for j2, isi2 in potong:
                    #  ⚠️ Setelah label dipotong, sisa isi BISA berupa daftar
                    #  pustaka (terukur 20 Okt 2026: "Daftar Referensi" menempel
                    #  dengan 8 entri pustaka ⇒ satu paragraf 8 entri).
                    if j2 == 'paragraf':
                        dp = _pecah_daftar_pustaka(isi2)
                        if dp:
                            for j3, isi3 in dp:
                                blok.append((j3, isi3, {'baris': i,
                                                        'boleh_daftar': None}))
                            continue
                    mb = _ambil_boleh(peta, i) if j2 == 'paragraf' else None
                    blok.append((j2, isi2, {'baris': i, 'boleh_daftar': mb}))
                continue

            #  Daftar pustaka = bentuk DAFTAR (pola pasti, pekerjaan kode).
            dp = _pecah_daftar_pustaka(isi)
            if dp:
                for j2, isi2 in dp:
                    blok.append((j2, isi2, {'baris': i, 'boleh_daftar': None}))
                continue

            if lab == 'judul':
                bersih = re.sub(r'^#{2,3}\s*', '', isi).strip()
                blok.append(('sub_heading', bersih,
                             {'baris': i, 'boleh_daftar': None}))
                continue

            mb = _ambil_boleh(peta, i)
            blok.append(('paragraf', isi, {'baris': i, 'boleh_daftar': mb}))
    return blok, peta


_POLA_TABEL = re.compile(r'\[\s*TABEL\s+\d+\.\d+[^\]]*\]', re.I)
_POLA_DIAGRAM = re.compile(r'\[\s*DIAGRAM\s+\d+\.\d+[^\]]*\]', re.I)

#  🚨 CACAT TERUKUR 20 Okt 2026 — PENANDA TERPOTONG JADI TEKS MENTAH.
#  Pola di atas MEWAJIBKAN `]` penutup. Kenyataannya penulis (LLM) sering
#  memotong tanda itu: baris `[DIAGRAM 1.1: Perjalanan Matahari dan
#  Bayanganmu - Gambar matahari bergerak…` panjangnya 135 karakter dan
#  TIDAK punya `]` sama sekali. Terukur: 1 dari 2 diagram (DIAGRAM 1.1)
#  lolos sebagai `paragraf` ⇒ tercetak MENTAH di .docx, gambarnya hilang.
#  `buku_umum_assembly._POLA_PENANDA_GADUH` sudah punya penangkal ini;
#  Jev belum — itulah sebabnya hanya jalur Jev yang kehilangan diagram.
#  Obat: pola cadangan yang mengambil sampai AKHIR BARIS bila `]` tak ada.
_POLA_TABEL_GADUH = re.compile(r'\[\s*TABEL\s+\d+\.\d+[^\]\n]*$', re.I)
_POLA_DIAGRAM_GADUH = re.compile(r'\[\s*DIAGRAM\s+\d+\.\d+[^\]\n]*$', re.I)


def _pecah_judul_nempel(baris):
    """Pisahkan JUDUL BAGIAN yang menempel di depan isi — HANYA yang PASTI.

    ⚠️ BATAS KERAS (20 Okt 2026): Jev TIDAK boleh menunjuk posisi karakter
    (kelemahan resmi #9 — Generation). Jadi kode TIDAK boleh menebak batas
    judul dari kalimat. Yang boleh dipotong HANYA yang penandanya PASTI:

      · `##` / `###` di awal        → penanda manual penulis
      · "Daftar Referensi"/"Pustaka" + titik → label baku buku
      · "Kata Pengantar"/"Prakata"/"Tentang Penulis" + titik

    Untuk judul yang menempel TANPA penanda (mis. "Bentuk-Bentuk Awan dan
    Pesannya bagi Kita Bagaimana orang dulu…"), kode DIAM — tidak memotong.
    Itu cacat PROMPT PENULIS (§6 SOT), bukan tugas perakit menebak.

    Mengembalikan [(jenis, isi)] atau None kalau tak ada yang pasti.
    """
    t = (baris or '').strip()
    if not t:
        return None
    #  ① Penanda manual ##/### — pasti judul, sisanya isi.
    m = re.match(r'^(#{2,3})\s*(\S.*)$', t)
    if m:
        sisa = m.group(2).strip()
        #  Kalau sisa masih memuat titik di tengah DAN panjang, itu judul+isi
        potong = _potong_label_baku(sisa)
        if potong:
            return potong
        return [('sub_heading', sisa)]
    #  ② Label baku buku yang menempel dengan isinya.
    return _potong_label_baku(t)


#  Label baku yang SELALU judul bagian, dan hampir selalu menempel dengan
#  isinya di naskah hasil pipeline (terukur 20 Okt 2026: "Sampai jumpa di
#  sana, ya! Daftar Referensi Badan Meteorologi…" masuk 1 baris).
_LABEL_BAKU = (
    'Daftar Referensi', 'Daftar Pustaka', 'Daftar Isi',
    'Daftar Tabel', 'Daftar Gambar', 'Kata Pengantar', 'Prakata',
    'Ucapan Terima Kasih', 'Tentang Penulis', 'Glosarium',
    'Lampiran', 'Indeks',
)


def _potong_label_baku(teks):
    """Potong 'Daftar Referensi <isi>' → (judul, isi). Hanya label PASTI."""
    for lab in _LABEL_BAKU:
        m = re.search(r'\b' + re.escape(lab) + r'\b', teks, re.I)
        if not m:
            continue
        sebelum = teks[:m.start()].strip()
        sesudah = teks[m.end():].strip()
        #  Harus ada isi sesudah label — kalau tidak, itu label berdiri sendiri
        if len(sesudah) < 30:
            continue
        hasil = []
        if sebelum:
            hasil.append(('paragraf', sebelum))
        hasil.append(('sub_heading', lab))
        hasil.append(('paragraf', sesudah))
        return hasil
    return None


def _pecah_penanda(baris):
    """Pisahkan penanda `[TABEL x.y: …]` / `[DIAGRAM x.y: …]` dari teksnya.

    Mengembalikan [(jenis, isi)] dengan jenis = 'tabel_marker' |
    'diagram_marker' | 'paragraf'. Teks di luar penanda tetap utuh sebagai
    paragraf — TIDAK ada kata yang dibuang.
    """
    hasil = []
    sisa = baris or ''
    #  Cari semua penanda berurutan menurut posisinya.
    temuan = []
    for pola, pola_gaduh, jenis in ((_POLA_TABEL, _POLA_TABEL_GADUH,
                                     'tabel_marker'),
                                    (_POLA_DIAGRAM, _POLA_DIAGRAM_GADUH,
                                     'diagram_marker')):
        #  Pola UTAMA dulu (penanda lengkap ber-`]`). Kalau tak ada satu pun
        #  di baris ini, coba pola CADANGAN yang mengambil sisa baris —
        #  menutup cacat penanda terpotong (lihat catatan _POLA_*_GADUH).
        ketemu = list(pola.finditer(sisa))
        if not ketemu:
            ketemu = list(pola_gaduh.finditer(sisa))
        for m in ketemu:
            temuan.append((m.start(), m.end(), jenis, m.group(0)))
    if not temuan:
        return [('paragraf', sisa)] if sisa.strip() else []
    temuan.sort()
    pos = 0
    for mulai, akhir, jenis, isi in temuan:
        if mulai > pos:
            teks = sisa[pos:mulai].strip()
            if teks:
                hasil.append(('paragraf', teks))
        hasil.append((jenis, isi.strip()))
        pos = akhir
    if pos < len(sisa):
        teks = sisa[pos:].strip()
        if teks:
            hasil.append(('paragraf', teks))
    return hasil
