"""PIPA REVISI — KONTRAK TUNGGAL antara jawaban AI dan naskah mahasiswa.

═══════════════════════════════════════════════════════════════════════════
🔴 MENGAPA BERKAS INI ADA (akar masalah, bukan tambalan)
═══════════════════════════════════════════════════════════════════════════
SEBELUM 25Sep26 ada 2 modul yang BERPIJAK PADA ASUMSI BERBEDA:

    prompts/revisi_produksi.txt (G7a):
        "JANGAN menyalin naskah. Tulis HANYA bagian yang kamu ubah."
        → AI balas POTONGAN KECIL

    app/tulis_docx.py::rakit():
        if bab_label == BAB_SELURUH:
            idx_awal, idx_akhir = 0, len(par) - 1
        → MENGGANTI SELURUH PARAGRAF dokumen dengan isi yang diterima

AKIBAT TERUKUR (uji 2 arah, naskah nyata 76.803 kar / 303 paragraf):
    masukan potongan 356 kar → hasil 3 paragraf, 356 kar
    📉 NASKAH SUSUT 99,5% (76.447 kar HILANG)

Gejala ini persis yang dulu membunuh `file_id=47` (naskah 5,1 MB → 4.522 kar).
Selama ini mahasiswa SELAMAT hanya karena pagar C9 kebetulan menolak
"hasil kosong" — BUKAN karena sistem tahu cara menempelkan.

═══════════════════════════════════════════════════════════════════════════
✅ OBATNYA — SATU KONTRAK, DIPATUHI KEDUA SISI
═══════════════════════════════════════════════════════════════════════════
    AI membalas PASTI (bentuk tetap):
        [PROFIL] Paradigma=…; Desain=…
        [K1-KUTIP-ASLI] <salin PERSIS kalimat naskah yang diganti>
        [K1-GANTI-JADI] <teks penggantinya>
        [K2-KUTIP-ASLI] …  (boleh berulang)

    Pemeriksa (berkas ini) memastikan SEBELUM naskah tersentuh:
        1. BENTUK   — penanda KUTIP/GANTI berpasangan, tidak ada sampah
        2. KUTIPAN  — kutipan BENAR-BENAR ada di naskah (toleran, bukan tebak)
        3. PANJANG  — hasil tidak lebih pendek dari ambang (pagar bencana)
        4. KEMBAR   — kalau kutipan muncul di >1 paragraf → TOLAK (jangan tebak)

    Penempel (tulis_docx) hanya mengganti paragraf yang KUTIP-nya TERBUKTI.
    Paragraf lain TIDAK DISENTUH.

Terverifikasi dengan AI NYATA (25Sep26, cbcn/glm-5.3-flash):
    permintaan tegas → AI PATUH (KUTIP-ASLI=1, GANTI-JADI=1)
    kutipan hasil cocok PERSIS dengan naskah (huruf demi huruf)

⚠️ DILARANG: menambal di hilir. Semua pagar di berkas INI (satu tempat).
⚠️ DILARANG: menebak paragraf saat tidak ketemu → WAJIB tolak + lapor jujur.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

log = logging.getLogger(__name__)

#  ── AMBANG (SATU SUMBER — jangan ditulis ulang di JS/template) ──────────
MIRIP_TOLERAN = 0.90      # kemiripan minimum kutipan vs paragraf (dice bigram)
PANJANG_MIN_RASIO = 0.60  # hasil tidak boleh < 60% panjang naskah asli
#  🔴 28Sep26 (OPSI 1, ACC Bos — "presisi tapi nyambung"): DASAR UKUR
#     PAGAR INI DIGANTI dari potongan KUTIP-ASLI → PANJANG PARAGRAF UTUH
#     yang memuat kutipan itu.
#     MENGAPA (terukur, bukan dugaan): `rakit_presisi()` MENGGANTI SELURUH
#     paragraf XML dengan GANTI-JADI (tulis_docx.py:498-501) — bukan hanya
#     kalimat yang dikutip. Kasus nyata C7 28Sep26: AI mengutip 1 kalimat
#     (163 kar) dari paragraf ratusan kar lalu menulis 7.201 kar → pagar
#     lama menghitung 44× dari KOTAKAN, padahal yang benar-benar diganti
#     adalah paragrafnya. Akibat: "perdalam" SELALU ditolak walau hasilnya
#     wajar, dan mahasiswa dapat pesan menyesatkan.
#  ⚠️ Sisi "terlalu sedikit" tetap dijaga pagar `cukup_panjang()`
#     (naskah utuh ≥ 60%) — lihat bagian 4 berkas ini.
PANJANG_MAKS_KALI = 3.0   # GANTI-JADI ≤ 3× panjang paragraf yang diganti
#  🔴 25Sep26 (ACC Bos "C"): permintaan BUAT_TABEL/BUAT_GRAFIK menghasilkan
#     TULISAN + STRUKTUR BARU (kalimat pengantar + data + penafsiran) —
#     itu memang yang diminta, jadi batas 3× terlalu ketat. Dinaikkan
#     menjadi 8× (tetap ADA batas, jangan sampai AI menulis naskah baru).
PANJANG_MAKS_KALI_KHUSUS = 8.0
MIN_KATA_KUTIP = 4        # kutipan < 4 kata → terlalu pendek untuk dicocokkan

#  Penanda bentuk balasan AI
_RE_PROFIL = re.compile(r'\[\s*PROFIL\s*\]([^\n]*)', re.I)
_RE_BLOK = re.compile(
    r'\[\s*K(\d+)\s*-\s*KUTIP-ASLI\s*\]\s*(.*?)'
    r'\[\s*K\1\s*-\s*GANTI-JADI\s*\]\s*(.*?)'
    r'(?=\[\s*K\d+\s*-\s*KUTIP-ASLI\s*\]|\[\s*PROFIL\s*\]|\Z)',
    re.S | re.I)
_RE_CAKUPAN = re.compile(r'\[\s*K(\d+)\s*-\s*CAKUPAN\s*:\s*([a-z]+)\s*\]', re.I)
_RE_TIDAK_ADA = re.compile(r'TIDAK\s+ADA\s+PERUBAHAN', re.I)
_RE_SISA_PENANDA = re.compile(r'\[\s*(PROFIL|K\d+\s*-\s*[A-Z-]+)\s*[:]?[^\]]*\]')


# ══════════════════════════════════════════════════════════════════════════
#  BENTUK DATA
# ══════════════════════════════════════════════════════════════════════════
@dataclass
class Editan:
    """Satu usulan penggantian dari AI."""
    nomor: int
    kutip: str
    ganti: str
    indeks: list[int] = field(default_factory=list)   # paragraf yang cocok
    keadaan: str = 'baru'      # baru | cocok | toleran | kembar | tak_ketemu


@dataclass
class Hasil:
    """Hasil pemeriksaan — siap dibaca pemanggil & dilaporkan ke mahasiswa."""
    ok: bool
    pesan: str = ''
    profil: str = ''
    editan: list[Editan] = field(default_factory=list)
    ditolak: list[dict] = field(default_factory=list)
    cakupan: dict = field(default_factory=dict)
    #  🎯 25Sep26 — penanda "AI JUJUR bilang tidak ada yang perlu diubah".
    #  Dipakai `ai.py._revisi_kerja` untuk memisahkan:
    #    bagian GAGAL kontrak pipa  → harus MENOLAK (503)
    #    bagian TANPA PERUBAHAN     → SAH, jangan menolak
    #  Dulu dibedakan lewat `cakupan` — SALAH, karena pada bentuk baru
    #  `cakupan` selalu {} → jawaban sah ikut tertolak.
    tanpa_perubahan: bool = False

    def ringkas(self) -> str:
        """Kalimat jujur untuk mahasiswa (dipakai tulis_docx/ai.py)."""
        if not self.ok:
            return self.pesan
        n = len(self.editan)
        bagian = [f'{n} bagian naskah diperbaiki.']
        if self.ditolak:
            bagian.append(f'{len(self.ditolak)} catatan belum bisa '
                          f'dikerjakan (bagiannya tidak ditemukan).')
        return ' '.join(bagian)


# ══════════════════════════════════════════════════════════════════════════
#  BANTU: pencocokan teks
# ══════════════════════════════════════════════════════════════════════════
def normal(teks: str) -> str:
    """Bentuk normal untuk pencocokan TOLERAN (bukan tebakan).

    Menyeragamkan: huruf besar/kecil, kutip pintar, tanda pisah, spasi.
    TIDAK membuang makna — hanya bentuk penulisan.
    """
    t = (teks or '').lower()
    t = re.sub(r'[\u2018\u2019\u201c\u201d]', '"', t)
    t = re.sub(r'[\u2013\u2014\u2212]', '-', t)
    t = re.sub(r'\s+', ' ', t)
    t = re.sub(r'[^\w\s\-.,;:()/%"]', '', t)
    return t.strip()


def _dice(a: str, b: str) -> float:
    """Kemiripan dice atas BIGRAM — tahan salah ketik ringan."""
    if not a or not b:
        return 0.0
    A = {a[i:i + 2] for i in range(len(a) - 1)}
    B = {b[i:i + 2] for i in range(len(b) - 1)}
    if not A or not B:
        return 0.0
    return 2 * len(A & B) / (len(A) + len(B))


def pisah_paragraf(naskah: str) -> list[str]:
    """Pecah naskah jadi paragraf — ATURAN TUNGGAL seluruh pipa.

    Mengapa di sini: dulu `tinjau.html:1013` memakai `\\n{2,}` sementara
    `app/ai.py::_teks_dari_docx` mengeluarkan `\\n` TUNGGAL → 478 paragraf
    jadi 1 blok 63.747 kar (BUG NYATA 25Sep26, sudah diperbaiki di hulu).
    Sekarang pemecahnya SATU tempat supaya tidak bisa berbeda lagi.
    """
    return [p.strip() for p in re.split(r'\n{2,}', naskah or '') if p.strip()]


# ══════════════════════════════════════════════════════════════════════════
#  1. BACA BENTUK BALASAN AI
# ══════════════════════════════════════════════════════════════════════════
def baca_bentukan(jawaban: str) -> tuple[str, list[Editan], dict, list[str]]:
    """Urai jawaban AI menurut kontrak.

    Kembalikan (profil, editan, cakupan, masalah).
    `masalah` = daftar pelanggaran bentuk (dipakai untuk menolak jujur).
    """
    jawaban = jawaban or ''
    masalah: list[str] = []

    m = _RE_PROFIL.search(jawaban)
    profil = (m.group(1).strip() if m else '')

    cakupan: dict = {}
    for no, jenis in _RE_CAKUPAN.findall(jawaban):
        cakupan[int(no)] = jenis.strip().lower()

    editan: list[Editan] = []
    for no, kutip, ganti in _RE_BLOK.findall(jawaban):
        kutip = _bersih(kutip)
        ganti = _bersih(ganti)
        if not kutip or not ganti:
            masalah.append(f'K{no}: penanda KUTIP-ASLI/GANTI-JADI kosong')
            continue
        editan.append(Editan(nomor=int(no), kutip=kutip, ganti=ganti))

    #  Kalau ada blok CAKUPAN: tolak → itu BUKAN kegagalan bentuk.
    for no, jenis in cakupan.items():
        if jenis == 'tolak':
            editan = [e for e in editan if e.nomor != no]

    #  ── SEMUA CAKUPAN = tolak → AI MENJAWAB JUJUR (bukan cacat bentuk) ──
    #  🐛 BUG NYATA (25Sep26, uji C8): jawaban `[K1-CAKUPAN: tolak]` yang
    #  SAH dulu jatuh ke "tidak ada blok KUTIP/GANTI" → ditolak sebagai
    #  cacat + mahasiswa TIDAK dapat penjelasan apa pun. Padahal AI hanya
    #  bilang "bagian itu tidak ada di potongan saya" — jawaban yang BENAR
    #  (terbukti dari AI nyata: ia menolak mengarang).
    #  Aturan: kalau SEMUA blok cakupan = tolak DAN tidak ada editan →
    #  anggap "tidak ada perubahan", sebutkan jumlahnya supaya mahasiswa
    #  tahu KENAPA hasilnya kosong.
    if cakupan and not editan and all(j == 'tolak' for j in cakupan.values()):
        masalah.append('__semua_tolak__')
        return profil, editan, cakupan, masalah

    if not editan and not masalah:
        if _RE_TIDAK_ADA.search(jawaban):
            masalah.append('__tanpa_perubahan__')       # sinyal khusus
        else:
            masalah.append('tidak ada blok KUTIP-ASLI/GANTI-JADI di jawaban')

    return profil, editan, cakupan, masalah


def _bersih(teks: str) -> str:
    """Buang penanda sisa + spasi berlebih dari satu potongan jawaban AI."""
    t = _RE_SISA_PENANDA.sub('', teks or '')
    t = re.sub(r'^\s*[-–•]\s*', '', t)
    return t.strip()


# ══════════════════════════════════════════════════════════════════════════
#  2. COCOKKAN KUTIPAN KE PARAGRAF (inti penjaga)
# ══════════════════════════════════════════════════════════════════════════
def cari_paragraf(paragraf: list[str], kutip: str) -> tuple[list[int], str, float]:
    """Cari paragraf yang memuat kutipan. TOLERAN tapi TIDAK menebak.

    Kembalikan (indeks, keadaan, skor):
        cocok      : kutipan ada utuh di satu paragraf
        toleran    : mirip ≥ MIRIP_TOLERAN (salah ketik ringan)
        kembar     : ketemu di >1 paragraf → PEMANGGIL WAJIB MENOLAK
        tak_ketemu : tidak ada → pemanggil WAJIB menolak
    """
    k = normal(kutip)
    if len(k.split()) < MIN_KATA_KUTIP:
        #  Terlalu pendek: masih boleh, tapi hanya cocok PERSIS (jangan toleran)
        kena = [i for i, p in enumerate(paragraf) if k and k in normal(p)]
        if not kena:
            return [], 'tak_ketemu', 0.0
        return (kena, 'cocok', 1.0) if len(kena) == 1 else (kena, 'kembar', 1.0)

    persis, mirip = [], []
    for i, p in enumerate(paragraf):
        pn = normal(p)
        if k in pn:
            persis.append(i)
            continue
        kata_k, kata_p = k.split(), pn.split()
        jendela = len(kata_k)
        if jendela < MIN_KATA_KUTIP or len(kata_p) < jendela:
            continue
        skor_terbaik = 0.0
        for j in range(len(kata_p) - jendela + 1):
            s = _dice(' '.join(kata_p[j:j + jendela]), k)
            if s > skor_terbaik:
                skor_terbaik = s
        if skor_terbaik >= MIRIP_TOLERAN:
            mirip.append((i, skor_terbaik))

    if persis:
        return (persis, 'cocok', 1.0) if len(persis) == 1 else (persis, 'kembar', 1.0)
    if mirip:
        idx = [i for i, _ in mirip]
        skor = max(s for _, s in mirip)
        return (idx, 'toleran', skor) if len(idx) == 1 else (idx, 'kembar', skor)

    #  ══ FIX 29Sep26 — PENCOCOKAN LINTAS POTONGAN ══════════════════════
    #  AKAR TERBUKTI (uji G1/G3/B2 29Sep26): naskah tertentu keluar dari
    #  `_teks_dari_berkas` sebagai potongan PER BARIS — pemisah `\n\n`
    #  tiap ~75 karakter (terukur pada TESIS uji: 1.621 pemisah `\n\n`,
    #  nol `\n` tunggal) — sehingga "paragraf" = 1 baris. Kutip AI 2+
    #  kalimat MELEWATI batas potongan → `tak_ketemu` walaupun teks ADA
    #  (terukur: `k in normal(naskah_penuh)` = True, tapi tak ada satu
    #  pun potongan tunggal yang memuatnya).
    #  Pagar TIDAK dilonggarkan: kata-katanya tetap harus persis utuh
    #  dalam potongan BERURUTAN — hanya BATAS BARIS yang tidak lagi
    #  menggagalkan. Kegagalan G1/G3 = inilah akarnya, BUKAN AI mengarang.
    #  (Downstream `rakit_presisi` mencocokkan per paragraf XML asli →
    #  penggantian tetap jatuh ke paragraf Word yang tepat & utuh.)
    from bisect import bisect_right
    norm_par = [normal(p) for p in paragraf]
    awal, posisi = [], 0
    for np_ in norm_par:
        awal.append(posisi)
        posisi += len(np_) + 1                     # +1 = spasi penghubung
    gabung = ' '.join(norm_par)
    lintas = []
    mulai = 0
    while len(lintas) < 3:                         # cukup utk deteksi kembar
        pos = gabung.find(k, mulai)
        if pos < 0:
            break
        i1 = max(0, bisect_right(awal, pos) - 1)
        i2 = max(0, bisect_right(awal, pos + len(k) - 1) - 1)
        lintas.append(list(range(i1, i2 + 1)))
        mulai = pos + 1
    if len(lintas) == 1:
        return lintas[0], 'cocok', 1.0
    if len(lintas) > 1:
        idx = lintas[0]
        return idx, 'kembar', 1.0
    return [], 'tak_ketemu', 0.0


# ══════════════════════════════════════════════════════════════════════════
#  3. PEMERIKSA — SELURUH PAGAR DI SINI (satu tempat)
# ══════════════════════════════════════════════════════════════════════════
def periksa(jawaban_ai: str, naskah: str, intent: str = '') -> Hasil:
    """Periksa jawaban AI SEBELUM naskah tersentuh.

    Pagar:
      1. BENTUK   — wajib ada blok KUTIP/GANTI (atau TIDAK ADA PERUBAHAN)
      2. KUTIPAN  — kutipan wajib TERBUKTI ada di naskah
      3. PANJANG  — hasil wajib wajar (tidak menghapus naskah)
      4. KEMBAR   — kutipan ambigu → TOLAK (jangan menebak)

    `intent` (BARU 25Sep26, ACC Bos "C" + sambung): jenis permintaan user,
    mis. 'BUAT_GRAFIK' / 'BUAT_TABEL'.

    🔴 MENGAPA PARAMETER INI ADA (bukti nyata dari uji E2E 25Sep26):
       Permintaan grafik MEMANG menghasilkan tulisan lebih panjang —
       itu memang yang diminta Bos ("grafik juga harus ada kata-kata yang
       menjelaskan + nyambung dengan tetangga"). Tanpa parameter ini,
       pipa menolaknya sebagai "balasan tidak wajar" (PAGAR 3) → revisi
       grafik SELALU 503 padahal jawabannya BENAR.
       ⇒ Terukur: PIPI menolak "ganti_terlalu_panjang" pada uji E2E.
    """
    profil, editan, cakupan, masalah = baca_bentukan(jawaban_ai)

    if masalah == ['__tanpa_perubahan__']:
        return Hasil(ok=True, pesan='AI menilai tidak ada yang perlu diubah.',
                     profil=profil, cakupan=cakupan, tanpa_perubahan=True)
    if masalah == ['__semua_tolak__']:
        #  AI JUJUR: bagian yang diminta tidak ada di potongan yang diterimanya.
        #  Ini BUKAN kegagalan — kuota TIDAK boleh dikembalikan begitu saja
        #  seolah-olah ada galat; mahasiswa diberi penjelasan yang bisa
        #  ditindaklanjuti (sebutkan sub-bab / kirim bagian itu).
        return Hasil(
            ok=True, profil=profil, cakupan=cakupan, tanpa_perubahan=True,
            pesan=('EduAi belum bisa merevisi catatan itu karena bagian '
                   'naskah yang dimaksud tidak ikut terbaca (naskah terlalu '
                   'besar sehingga diproses per bagian). Coba sebutkan '
                   'sub-babnya, lalu kirim ulang catatannya.'))
    if masalah:
        return Hasil(ok=False, profil=profil, cakupan=cakupan, pesan=(
            'Balasan AI tidak sesuai bentuk yang bisa dipakai. '
            'Token Revisi Anda sudah dikembalikan — silakan coba lagi. '
            f'({masalah[0]})'))

    paragraf = pisah_paragraf(naskah)
    if not paragraf:
        return Hasil(ok=False, pesan='Naskah kosong — tidak ada yang bisa '
                                      'diperbaiki.')

    lolos: list[Editan] = []
    ditolak: list[dict] = []

    for e in editan:
        idx, keadaan, skor = cari_paragraf(paragraf, e.kutip)
        e.indeks, e.keadaan = idx, keadaan

        if keadaan == 'tak_ketemu':
            ditolak.append({'nomor': e.nomor, 'sebab': 'tidak_ketemu',
                            'kutip': e.kutip[:120]})
            continue
        if keadaan == 'kembar':
            ditolak.append({'nomor': e.nomor, 'sebab': 'kembar',
                            'paragraf': idx, 'kutip': e.kutip[:120]})
            continue
        #  PAGAR 3 — panjang wajar (DASAR = PARAGRAF, 28Sep26 Opsi 1)
        #  🔴 Yang diukur: panjang PARAGRAF yang berisi kutipan — karena
        #     rakit_presisi mengganti paragraf itu UTUH dengan GANTI-JADI.
        #     Ukur dari potongan kutip = salah satuan (lihat catatan di atas).
        #  🔧 29Sep26 — rentang LINTAS POTONGAN (lihat `cari_paragraf`):
        #     kalau kutip memuat beberapa potongan, dasar = jumlah SEMUA
        #     potongan tercakup. Pakai idx[0] saja → dasar 1 baris (~75 kar)
        #     → batas 3× terlalu kecil → GANTI-JADI wajar (3 kalimat)
        #     ditolak "ganti_terlalu_panjang" padahal sah.
        dasar = (sum(len(paragraf[i]) for i in idx)
                 if idx else len(e.kutip))
        _maks = int(dasar * PANJANG_MAKS_KALI)
        #  🔴 PENGECUALIAN (25Sep26): permintaan BUAT_TABEL / BUAT_GRAFIK
        #     MEMANG menambah struktur + kalimat penjelas → batas 3×
        #     terlalu ketat. Batas untuk permintaan ini = 8× ATAU minimal
        #     1.200 kar (cukup untuk tabel/grafik + pengantar + penafsiran),
        #     TETAP ADA BATAS (jangan sampai AI menulis naskah baru).
        if intent in ('BUAT_TABEL', 'BUAT_GRAFIK'):
            _maks = max(1200, int(dasar * PANJANG_MAKS_KALI_KHUSUS))
        if len(e.ganti) > max(200, _maks):
            #  Semua angka DICATAT supaya kegagalan berikutnya bisa
            #  dijawab dengan angka (28Sep26: log lama hanya "tidak wajar"
            #  tanpa panjang → mustahil menuduh model mana).
            rasio = round(len(e.ganti) / max(1, dasar), 2)
            _batas_nyata = max(200, _maks)

            #  ══ PAGAR LAMA (05Okt26) — MURNI ARITMATIKA ═══════════════════
            #  🛑 JEV DICABUT DARI SINI (putusan Bos "A" 05Okt26).
            #  JEJAK 3 PERCOBAAN (semua GAGAL, terukur — JANGAN DIULANG):
            #    1) jev memutuskan → 5/6 permintaan SAH ditolak (0,98-1,00)
            #    2) pertanyaan `jawab_tugas` → SAH dijawab "tidak_nyambung"
            #       3/3 dengan keyakinan 0,97-1,00
            #    3) ukuran `menyisipkan` (choice) → SAH dijawab "ya" 4/4
            #       dengan keyakinan 0,93-1,00
            #  ⇒ SEBAB: jev-1.13 TIDAK BISA membedakan "memperdalam topik
            #    yang sama" dari "menambahkan hal yang tidak diminta". Ia
            #    melihat setiap PENAMBAHAN ISI sebagai "menyisipkan".
            #  ⇒ Karena itu jev TIDAK dipakai untuk menilai balasan. Perannya
            #    kembali ke yang TERBUKTI: **peta bab** (`satpam.periksa()`).
            #  Kalau kelak peran ini ingin dicoba lagi → PAKAI MODEL LAIN
            #  (mis. cb/gpt-5.6-luna), jangan jev-1.13.
            #  ⚠️ 21 Okt 2026: jev-1.14 SUDAH DIUJI, tapi HANYA pada BENTUK/ISI
            #     naskah (34 pertanyaan, 3 naskah) — BUKAN pada peran menilai
            #     balasan ini. Jadi catatan di atas BELUM gugur. Kalau ingin
            #     mencoba peran ini dengan 1.14, UKUR DULU; jangan anggap
            #     rilis baru otomatis memperbaiki kelemahan ini. SOT §16.
            #
            #  Pagar panjang di bawah tetap: ARITMATIKA MURNI (tak bisa mati,
            #  tak bisa salah paham tugas). Laporan jev DIHAPUS dari dict.
            ditolak.append({'nomor': e.nomor, 'sebab': 'ganti_terlalu_panjang',
                            'panjang_kutip': len(e.kutip),
                            'panjang_paragraf': dasar,
                            'rasio_paragraf': rasio,
                            'panjang_ganti': len(e.ganti),
                            'batas': _batas_nyata,
                            'intent': intent})
            continue
        lolos.append(e)

    if not lolos:
        sebab = ditolak[0]['sebab'] if ditolak else 'tidak ada'
        pesan = {
            'tidak_ketemu': ('Bagian naskah yang ditunjuk catatan tidak '
                             'ditemukan. Token Revisi Anda sudah dikembalikan '
                             '— silakan periksa catatannya atau kirim bagian '
                             'naskah yang dimaksud.'),
            'kembar': ('Kalimat yang ditunjuk catatan muncul di lebih dari satu '
                       'tempat, jadi EduAi tidak menebak mana yang dimaksud. '
                       'Token Revisi Anda sudah dikembalikan — sebutkan '
                       'sub-babnya agar bisa ditunjuk tepat.'),
            'ganti_terlalu_panjang': ('Balasan AI tidak wajar (jauh lebih '
                                      'panjang daripada bagian yang diganti). '
                                      'Token Revisi Anda sudah dikembalikan.'),
        }.get(sebab, 'Tidak ada bagian yang bisa diperbaiki dengan aman. '
                     'Token Revisi Anda sudah dikembalikan.')
        return Hasil(ok=False, pesan=pesan, profil=profil, editan=editan,
                     ditolak=ditolak, cakupan=cakupan)

    return Hasil(ok=True, profil=profil, editan=lolos, ditolak=ditolak,
                 cakupan=cakupan)


# ══════════════════════════════════════════════════════════════════════════
#  3b. OPSI D (29Sep26, ACC Bos "D1 + (a)") — SIMPAN BENTUK MENTAH
# ══════════════════════════════════════════════════════════════════════════
#
#  AKAR (terukur 29Sep26, cakupan 8/8 = 100%):
#      `bersihkan_jawaban_ai()` (ai.py:552) membuang kerangka
#      KUTIP-ASLI/GANTI-JADI → `versi_dokumen.isi` tersimpan sebagai teks
#      polos → `/api/ai/v1/terapkan` memeriksanya dengan `periksa()` →
#      jatuh ke jalur mundur `rakit(BAB_SELURUH)` mengganti
#      SELURUH naskah (Opsi A kini menolaknya 422, tapi user tetap harus
#      salin manual).
#
#  SOLUSI: simpan juga bentuk MENTAH pendamping tiap baris versi
#      (tabel baru `versi_pipa` — tabel lama TIDAK disentuh), supaya pintu
#      "Tulis hasil ke dokumen" bisa menulis PRESISI.

_POLA_CATATAN_AI = re.compile(
    #  ⚠️ SEMPIT & BERJANGKAR: hanya paragraf yang MEMULAI dengan frasa ini.
    #     Pola lebar pernah memakan kalimat revisi asli (pelajaran 16Sep26:
    #     "Tidak ada perubahan yang perlu dilakukan pada bagian ini." sempat
    #     ikut terbuang). Uji 2 arah WAJIB: catatan AI hilang, kalimat
    #     mahasiswa bertahan.
    r'^[ \t]*('
    r'catatan[ \t]+untuk[ \t]+anda\b'
    r'|catatan[ \t]+untuk[ \t]+komentar\b'
    r'|catatan[ \t]+dari[ \t]+(?:eduai|ai)\b'
    r'|catatan[ \t]+ai\b'
    r'|tidak[ \t]+ada[ \t]+perubahan\b'
    r'|hasil[ \t]+revisi[ \t]+di[ \t]+atas\b'
    r')[^\n]*$',
    re.I | re.M)


def buang_catatan_ai(teks: str) -> tuple[str, list[str]]:
    """Pisahkan CATATAN AI dari isi naskah (Opsi D, 29Sep26).

    Kembalikan `(teks_bersih, daftar_catatan)`.

    ═══ KENAPA ═══
    Pada kasus nyata file78 (29Sep26) dua paragraf catatan AI ikut
    tersimpan ke `versi_dokumen.isi`:
        "Catatan untuk Anda: data yang Anda kirim hanya memuat naskah
         hingga sub-bab 2.1.3 ..."
        "Catatan untuk komentar ini, meski bagiannya ada ..."
    Catatan itu bukan tulisan mahasiswa — kalau tersimpan sebagai versi,
    ia ikut terbaca sebagai isi dokumen (dan bisa ikut tertulis saat
    penerapan).

    Catatannya TIDAK dibuang diam-diam: ia dikembalikan sebagai daftar
    supaya pemanggil bisa menyampaikannya apa adanya (pesan jujur).
    """
    if not teks:
        return '', []
    potong = re.split(r'\n[ \t]*\n', teks)
    bersih: list[str] = []
    catatan: list[str] = []
    for p in potong:
        m = _POLA_CATATAN_AI.match(p.strip())
        if m:
            catatan.append(p.strip())
            continue
        bersih.append(p)
    keluar = '\n\n'.join(x for x in bersih if x.strip())
    return keluar.strip(), catatan


def gabung_mentah(daftar_mentah: list[str]) -> str:
    """Gabung jawaban MENTAH per bagian → satu teks pipa yang sah.

    ═══ ATURAN ═══
      · Ambil HANYA blok KUTIP-ASLI/GANTI-JADI (lewat `baca_bentukan`,
        sehingga CAKUPAN `tolak` tetap dihormati — blok yang AI tolak
        tidak ikut terbawa).
      · **Penomoran K diurutkan ulang** (K1..Kn) — tiap potongan naskah
        memakai nomor mulai dari K1, jadi kalau digabung mentah akan ada
        K1 kembar. Dampaknya nyata: `[K1-CAKUPAN: tolak]` di bagian 2
        MEMBUANG editan K1 milik bagian 1 (baca_bentukan, pipa.py:211).
      · Catatan AI di dalam GANTI-JADI ikut dibuang (lihat
        `buang_catatan_ai`) — jangan sampai tertulis ke naskah.
      · Jawaban BENTUK LAMA (tanpa penanda) → menyumbang 0 blok; hasilnya
        '' = "tidak ada pendamping" → pintu terapkan jujur menolak (422).

    Mengembalikan '' kalau tidak ada satu pun blok yang bisa dipakai.
    """
    potongan: list[str] = []
    nomor = 0
    for mentah in daftar_mentah or []:
        if not (mentah or '').strip():
            continue
        _, editan, _, _ = baca_bentukan(mentah)
        for e in editan:
            ganti_bersih, _cat = buang_catatan_ai(e.ganti or '')
            if not ganti_bersih:
                continue                      # isinya cuma catatan AI
            nomor += 1
            potongan.append(
                f'[K{nomor}-KUTIP-ASLI]\n{e.kutip}\n'
                f'[K{nomor}-GANTI-JADI]\n{ganti_bersih}\n')
    if not potongan:
        return ''
    return '\n'.join(potongan)


# ══════════════════════════════════════════════════════════════════════════
#  4. PAGAR BENCANA — dipakai SEBELUM menulis ke dokumen
# ══════════════════════════════════════════════════════════════════════════
def cukup_panjang(naskah_lama: str, naskah_baru: str) -> tuple[bool, str]:
    """Pagar terakhir: naskah hasil TIDAK BOLEH menyusut keterlaluan.

    Mengapa: bug 25Sep26 menyusutkan 76.803 → 356 kar (99,5%).
    Ambang dari data nyata: revisi sah paling banyak memangkas ~40%.
    """
    lama = len((naskah_lama or '').strip())
    baru = len((naskah_baru or '').strip())
    if lama == 0:
        return True, ''
    if baru == 0:
        return False, ('Hasil revisi kosong — naskah Anda tidak diubah dan '
                       'Token Revisi dikembalikan.')
    rasio = baru / lama
    if rasio < PANJANG_MIN_RASIO:
        return False, (f'Hasil revisi hanya {rasio*100:.0f}% panjang naskah asli. '
                       f'Demi keamanan naskah Anda, perubahan ini dibatalkan '
                       f'dan Token Revisi dikembalikan.')
    return True, ''
