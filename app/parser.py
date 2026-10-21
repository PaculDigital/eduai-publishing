"""Section Parser — tentukan APA & DI MANA user minta direvisi.

=== SALINAN POLA DARI PENELITIAN-BOT (SUMBER READ-ONLY) ===
Asal: /opt/data/services/penelitian-bot/telegram-bot/agents/section-parser.js
      baris 3-46   -> SECTIONS_CATALOG (katalog section + keywords)
      baris 58-65  -> INTENT_KEYWORDS (6 intent)
      baris 67-125 -> parseSectionIntent()  (versi AI)
      baris 147-193 -> fallbackParse()      (versi aturan kata kunci)

KENAPA ADA DI EDUAI: intent MENENTUKAN PENGALI Token Revisi (§4.13):
  REVISI/perbaiki       x1
  GANTI_METODE          x3
  ubah alur             x4
  ubah alur + semua bab x5
Salah baca intent = salah tagih user. Karena itu parser WAJIB punya jalur
ATURAN (gratis, tanpa AI) supaya (a) tidak menambah biaya per pesan, dan
(b) tetap jalan kalau AI sedang tidak tersedia/mengantre.

URUTAN: pakai aturan dulu (cepat, Rp 0). Kalau confidence rendah (<0.5)
baru tawarkan ke AI — sesuai prinsip Bos §4.17 "AI = pemandu".
"""

from __future__ import annotations

import logging
import re
from typing import Any

log = logging.getLogger(__name__)

# ── SECTIONS_CATALOG — section-parser.js baris 3-46 ─────────────────────
SECTIONS_CATALOG: dict[str, list[dict[str, Any]]] = {
    'meta': [
        {'id': 'judul', 'title': 'Judul Penelitian', 'keywords': ['judul', 'title']},
        {'id': 'abstrak', 'title': 'Abstrak', 'keywords': ['abstrak', 'abstract', 'ringkasan']},
        {'id': 'kata_pengantar', 'title': 'Kata Pengantar', 'keywords': ['kata pengantar', 'preface']},
        {'id': 'daftar_pustaka', 'title': 'Daftar Pustaka', 'keywords': ['daftar pustaka', 'referensi', 'bibliography']},
    ],
    'bab1': [
        {'id': '1.1', 'title': 'Latar Belakang', 'keywords': ['latar belakang', '1.1', 'pendahuluan', 'konteks']},
        {'id': '1.2', 'title': 'Rumusan Masalah', 'keywords': ['rumusan masalah', '1.2', 'masalah penelitian']},
        {'id': '1.3', 'title': 'Tujuan Penelitian', 'keywords': ['tujuan', '1.3']},
        {'id': '1.4', 'title': 'Manfaat Penelitian', 'keywords': ['manfaat', '1.4', 'kontribusi']},
        {'id': '1.5', 'title': 'Sistematika Penulisan', 'keywords': ['sistematika', '1.5']},
    ],
    'bab2': [
        {'id': '2.1', 'title': 'Landasan Teori', 'keywords': ['landasan teori', '2.1', 'teori']},
        {'id': '2.2', 'title': 'Penelitian Terdahulu', 'keywords': ['penelitian terdahulu', '2.2', 'riset sebelumnya']},
        {'id': '2.3', 'title': 'Kerangka Berpikir', 'keywords': ['kerangka berpikir', 'kerangka konseptual', '2.3']},
        {'id': '2.4', 'title': 'Hipotesis', 'keywords': ['hipotesis', '2.4', 'h1', 'h2']},
    ],
    'bab3': [
        {'id': '3.1', 'title': 'Metode Penelitian', 'keywords': ['metode', '3.1', 'pendekatan']},
        {'id': '3.2', 'title': 'Populasi dan Sampel', 'keywords': ['populasi', 'sampel', '3.2', 'informan']},
        {'id': '3.3', 'title': 'Instrumen Penelitian', 'keywords': ['instrumen', '3.3', 'kuesioner', 'pedoman']},
        {'id': '3.4', 'title': 'Teknik Analisis Data', 'keywords': ['analisis data', '3.4', 'teknik analisis']},
    ],
    'bab4': [
        {'id': '4.1', 'title': 'Deskripsi Responden', 'keywords': ['deskripsi responden', '4.1', 'karakteristik responden', 'profil responden']},
        {'id': '4.2', 'title': 'Uji Instrumen', 'keywords': ['uji instrumen', '4.2', 'validitas', 'reliabilitas']},
        {'id': '4.3', 'title': 'Uji Asumsi Klasik', 'keywords': ['uji asumsi', '4.3', 'normalitas', 'multikolinearitas', 'heteroskedastisitas']},
        {'id': '4.4', 'title': 'Uji Hipotesis', 'keywords': ['uji hipotesis', '4.4', 'regresi', 'koefisien determinasi', 'uji f', 'uji t']},
        {'id': '4.5', 'title': 'Pembahasan', 'keywords': ['pembahasan', '4.5', 'diskusi', 'interpretasi hasil',
                                                          # 🔴 tambahan 05Okt26 (cacat C-3, terukur):
                                                          # "hasil penelitian belum dibahas" dulu → UNKNOWN
                                                          # padahal 4.5 Pembahasan ADA. Kata "hasil" & "dibahas"
                                                          # tak ada di kamus. Mahasiswa sangat sering menyebut
                                                          # pembahasan sebagai "hasil yang dibahas".
                                                          'hasil', 'dibahas', 'membahas', 'hasil penelitian',
                                                          'temuan']},
    ],
    'bab5': [
        {'id': '5.1', 'title': 'Kesimpulan', 'keywords': ['kesimpulan', '5.1', 'simpulan']},
        {'id': '5.2', 'title': 'Saran', 'keywords': ['saran', '5.2', 'rekomendasi']},
        {'id': '5.3', 'title': 'Keterbatasan Penelitian', 'keywords': ['keterbatasan', '5.3', 'limitasi']},
    ],
    'lampiran': [
        {'id': 'lampiran_kuesioner', 'title': 'Lampiran Kuesioner', 'keywords': ['lampiran kuesioner']},
        {'id': 'lampiran_pedoman', 'title': 'Lampiran Pedoman Wawancara', 'keywords': ['pedoman wawancara', 'lampiran pedoman']},
        {'id': 'lampiran_transkrip', 'title': 'Lampiran Transkrip', 'keywords': ['transkrip', 'lampiran transkrip']},
    ],
}

ALL_SECTIONS: list[dict[str, Any]] = [
    s for kat in ('meta', 'bab1', 'bab2', 'bab3', 'bab4', 'bab5', 'lampiran')
    for s in SECTIONS_CATALOG[kat]
]

# ── INTENT_KEYWORDS — section-parser.js baris 58-65 ─────────────────────
INTENT_KEYWORDS: dict[str, list[str]] = {
    #  ══ BUAT_TABEL / BUAT_GRAFIK (25Sep26, ACC Bos "C") ═══════════════════
    #  MENGAPA DI ATAS: user yang bilang "tambahkan tabel…" harus masuk
    #  BUAT_TABEL, BUKAN TAMBAH_DATA biasa — sebab pekerjaannya BEDA
    #  (menyusun struktur baru) dan harganya BEDA (×2, bukan ×1).
    #  ⚠️ Urutan kamus PENTING: `_cocok_intent` memakai skor kata terpanjang.
    'BUAT_TABEL': ['buatkan tabel', 'buat tabel', 'tambahkan tabel',
                   'bikin tabel', 'sajikan dalam bentuk tabel', 'tabel baru',
                   'tabel distribusi', 'tabel frekuensi', 'tabel silang',
                   'tabel perbandingan', 'tabel ringkasan', 'tabulasikan',
                   'sajikan tabel', 'buatkan tabulasi'],
    'BUAT_GRAFIK': ['buatkan grafik', 'buat grafik', 'bikin grafik',
                    'tambahkan grafik', 'buatkan histogram', 'buat histogram',
                    'buatkan diagram', 'buat diagram', 'buatkan bagan',
                    'grafik baru', 'gambar grafik', 'visualisasikan',
                    'buatkan chart', 'sajikan dalam bentuk grafik',
                    'grafik pertumbuhan', 'grafik tren', 'diagram alur'],
    'TAMBAH_DATA': ['tambah', 'tambahkan', 'tambahin', 'isi', 'masukin', 'append',
                    'insert', 'kasih tau', 'lengkapi data', 'tambahan'],
    'PERKAYA_NARASI': ['perkaya', 'perluas', 'elaborasi', 'panjang', 'dalam',
                       'mendalam', 'rinci', 'detail', 'lengkap', 'lebih jelas',
                       'kembangkan', 'perjelas', 'urai',
                       # tambahan 15Sep26 (uji nyata): mahasiswa bilang "kurang"
                       'pendek', 'sedikit', 'minim', 'kurang panjang',
                       'belum lengkap', 'belum dalam', 'terlalu singkat'],
    'REVISI': ['revisi', 'ubah', 'ganti', 'koreksi', 'betulin', 'fix', 'salah',
               'kurang tepat', 'sebaiknya', 'mending', 'perbaiki', 'benahi'],
    'GANTI_METODE': ['ganti metode', 'pakai uji', 'coba analisis lain',
                     'ganti pendekatan', 'ubah metode', 'metode lain',
                     'ganti analisis', 'metode berbeda'],
    'HAPUS': ['hapus', 'buang', 'ilangin', 'remove', 'jangan ada'],
    'PERTANYAAN': ['apa itu', 'kenapa', 'bagaimana', 'kapan', 'dimana', 'siapa',
                   'jelasin', 'terangkan', 'apa yang dimaksud'],
}

# ── PENGALI Token Revisi per intent (MASTER_PLAN §4.13) ─────────────────
PENGALI_INTENT: dict[str, int] = {
    #  ══ ×2 (25Sep26, ACC Bos "C") — MENYUSUN STRUKTUR BARU ═══════════════
    #  ALASAN ×2 (bukan ×1): membuat tabel/grafik = pekerjaan MENULIS
    #  STRUKTUR BARU (menyusun baris/kolom, memilih data, menata), bukan
    #  sekadar memperbaiki kalimat. Lebih berat dari revisi biasa (×1),
    #  lebih ringan dari ganti metode (×3).
    #  ⚠️ GRAFIK: AI menyiapkan DATA-nya, app MENGGAMBAR (app/gambar.py).
    #     Kalau data tidak ada di naskah → AI WAJIB TANYA, jangan mengarang.
    'BUAT_TABEL': 2,
    'BUAT_GRAFIK': 2,
    'TAMBAH_DATA': 1,
    'PERKAYA_NARASI': 1,
    'REVISI': 1,
    'PERTANYAAN': 1,
    'HAPUS': 1,
    'GANTI_METODE': 3,          # ganti metode = 3 kuota
    'UBAH_ALUR': 4,             # ubah alur/paradigma = 4
    'UBAH_ALUR_SEMUA': 5,       # ubah alur + semua bab = 5
    'UNKNOWN': 1,
}

# ══════════════════════════════════════════════════════════════════════════
#  TANGGA CAKUPAN (25Sep26, ACC Bos "1. A") — pengali dari LUAS pekerjaan
#
#  MASALAH TERUKUR: "perbaiki seluruh bagian ini" DULU dihitung ×1 — padahal
#  mesin mengerjakan 11 paragraf sekaligus. Mahasiswa RUGI (kerja 11, bayar 1)
#  dan Bos juga rugi (AI memakan token lebih banyak).
#
#  KINI: pengali ditentukan CAKUPAN yang disebut, bukan cuma niat.
#     ×2 = satu BAGIAN penuh (sub-bab 1.1 dsb) / "seluruh bagian ini"
#     ×3 = satu BAB penuh / "seluruh bab ini"
#     ×5 = SELURUH DOKUMEN
#  ATURAN: cakupan hanya MENGUBAH ke atas bila pekerjaannya memang lebih
#  besar (perbaikan/penambahan isi). "PERTANYAAN" tidak dihitung — bertanya
#  tidak mengubah naskah.
# ══════════════════════════════════════════════════════════════════════════

#  kata pemicu CAKUPAN "1 bagian penuh"
_KATA_BAGIAN = ('seluruh bagian', 'semua bagian', 'bagian ini seluruhnya',
                'seluruh sub-bab', 'seluruh subbab', 'semua paragraf',
                'seluruh paragraf', 'seluruh isi bagian')

#  kata pemicu CAKUPAN "1 bab penuh"
_KATA_BAB = ('seluruh bab', 'semua bab ini', 'bab ini seluruhnya',
             'seluruh isi bab', 'sepanjang bab ini')

#  🔴 BUG WULAN 25Sep26 (ketemu dari uji): "perbaiki seluruh bab ini" dapat ×5
#     padahal harus ×3 — sebab `_KATA_SEMUA` (untuk UBAH_ALUR) memuat
#     'seluruh bab'. Dua hal BERBEDA: ALUR seluruh dokumen vs CAKUPAN 1 bab.
#     PERBAIKAN: cakupan punya daftar SENDIRI yang khusus DOKUMEN penuh.
_KATA_DOKUMEN = ('seluruh dokumen', 'seluruh naskah', 'semua naskah',
                 'satu dokumen', 'dari bab 1 sampai', 'bab 1 sampai bab 5',
                 'semua bab sekaligus', 'seluruh dokumen ini',
                 'seluruh isi dokumen', 'semua bab dan sub-bab')


def pengali_cakupan(pesan: str) -> int:
    """Hitung pengali dari CAKUPAN yang disebut user (1/2/3/5).

    Return 1 kalau tidak ada kata cakupan (biar `pilih_pengali` memakai
    niat/intent seperti biasa).

    Urutan: DOKUMEN (5) > BAB (3) > BAGIAN (2).
    ⚠️ 'seluruh bab' = 1 BAB = ×3 (BUKAN dokumen penuh).
    """
    teks = (pesan or '').lower()
    #  dokumen penuh — daftar KHUSUS (jangan pakai _KATA_SEMUA: itu untuk alur)
    if any(k in teks for k in _KATA_DOKUMEN):
        return 5
    #  "seluruhnya" tanpa sebut bab → dokumen penuh
    if 'seluruhnya' in teks and not any(k in teks for k in _KATA_BAB):
        return 5
    if any(k in teks for k in _KATA_BAB):
        return 3
    if any(k in teks for k in _KATA_BAGIAN):
        return 2
    return 1


# Intent yang MENGUBAH isi dokumen (PERTANYAAN tidak mengubah apa pun)
INTENT_MENGUBAH = frozenset({'TAMBAH_DATA', 'PERKAYA_NARASI', 'REVISI',
                             'BUAT_TABEL', 'BUAT_GRAFIK',
                             'GANTI_METODE', 'HAPUS', 'UBAH_ALUR', 'UBAH_ALUR_SEMUA'})

# Kata pemicu "ubah alur" — ini yang menaikkan pengali ke 4/5
_KATA_ALUR = ('ubah alur', 'ganti alur', 'ubah paradigma', 'ganti paradigma',
              'deduktif jadi induktif', 'induktif jadi deduktif', 'ubah kerangka',
              'rombak alur', 'ganti alur berpikir')
_KATA_SEMUA = ('semua bab', 'seluruh bab', 'seluruh dokumen', 'semua bab sekaligus',
               'dari bab 1 sampai', 'bab 1 sampai bab 5', 'satu dokumen',
               'seluruh naskah', 'semua naskah', 'seluruh dokumen ini')


def pilih_pengali(intent: str, pesan: str = '') -> int:
    """Hitung PENGALI Token Revisi dari intent + isi pesan (MASTER_PLAN §4.13).

    Urutan menang: ubah alur + semua bab (5) > ubah alur (4) > ganti metode (3)
    > TANGGA CAKUPAN (2/3/5) > lainnya (1).

    ⚠️ PERTANYAAN: bertanya TIDAK mengubah naskah → selalu ×1 (cakupan
       tidak menaikkan, karena tidak ada pekerjaan tulis).
    """
    teks = (pesan or '').lower()
    intent = intent or 'UNKNOWN'

    #  bertanya = tidak ada pekerjaan mengubah → ×1 apa pun cakupannya
    if intent == 'PERTANYAAN':
        return 1

    if any(k in teks for k in _KATA_ALUR):
        if any(k in teks for k in _KATA_SEMUA):
            return 5
        return 4

    #  ── TANGGA CAKUPAN (25Sep26) — ambil yang TERBESAR dari niat vs cakupan
    dasar = PENGALI_INTENT.get(intent, 1)
    cakup = pengali_cakupan(pesan)
    if cakup > 1:
        return max(dasar, cakup)
    return dasar


def _cocok_section(pesan: str) -> tuple[str, str, float]:
    """Cocokkan pesan dengan katalog section. Mengembalikan (id, judul, skor).

    Skor: 0 = tidak ketemu. Makin panjang keyword yang cocok, makin yakin.
    Nomor sub-bab (1.1) = bukti TERKUAT (skor 1.0).

    🔴 PERBAIKAN C-2/C-3 (05Okt26) — "revisi tempatnya tidak salah yang direvisi".
    CACAT LAMA (terukur: uji 16 kasus → 56% benar):
      (1) "perbaiki bab 4" → dijawab `SECTIONS_CATALOG['bab4'][0]` = SELALU 4.1,
          padahal yang dimaksud bisa 4.2/4.3/4.5.  SEBAB: baris 266 memakai
          indeks [0] = sub-bab PERTAMA bab itu.  ⇒ TERBUKTI salah tempat.
      (2) "perbaiki kerangka berpikir di bab 2" → juga 2.1 (bukan 2.3 Kerangka
          Berpikir) sebab kata kunci sub-bab TIDAK pernah dicoba setelah BAB.
      (3) conf dihitung dari PANJANG KATA KUNCI (len(kw)/40) — panjang kata
          TIDAK sama dengan keyakinan. "perbaiki bab 4" dapat conf 0,78
          (butuh_ai=False) padahal 4.1 vs 4.5 bisa beda jauh.

    PERBAIKAN (aturan baru):
      (a) _subbab_dari_bab() — bila user menyebut BAB saja, JANGAN ambil [0].
          Kembalikan section BER-KONFIDENSI RENDAH (butuh_ai=True) supaya
          pemanggil boleh meminta JEV/urutan pemeriksa memutuskan, atau AI
          memilih sub-bab dari ISI NASKAH. Isi naskah = sumber kebenaran.
      (b) Setelah BAB, TETAP coba kata kunci sub-bab — tapi hanya sub-bab
          DALAM bab itu (mis. "kerangka berpikir di bab 2" → 2.3).
      (c) Kata kunci "hasil" untuk pembahasan (kasus "hasil penelitian belum
          dibahas" dulu UNKNOWN padahal 4.5 Pembahasan ada).
    """
    teks = (pesan or '').lower()
    terbaik = ('unknown', '', 0.0)

    # 1) nomor sub-bab eksplisit — paling kuat
    m = re.search(r'\b(\d\.\d)\b', teks)
    if m:
        nomor = m.group(1)
        for s in ALL_SECTIONS:
            if s['id'] == nomor:
                return s['id'], s['title'], 1.0

    # 2) sebut BAB saja
    mb = re.search(r'\bbab\s*([1-5]|i{1,3}|iv|v)\b', teks)
    if mb:
        peta_romawi = {'1': 'bab1', 'i': 'bab1', '2': 'bab2', 'ii': 'bab2',
                       '3': 'bab3', 'iii': 'bab3', '4': 'bab4', 'iv': 'bab4',
                       '5': 'bab5', 'v': 'bab5'}
        kat = peta_romawi.get(mb.group(1).lower())
        kandidat_bab = SECTIONS_CATALOG.get(kat) or []

        # 2a) PERBAIKAN (b): coba kata kunci sub-bab DI DALAM bab itu dulu.
        #     "perbaiki kerangka berpikir di bab 2" → 2.3 (bukan 2.1).
        # ⚠️ Kata kunci berupa nomor ('2.1') dilewati — user menyebut bab,
        #    bukan nomor; '2.1' takkan cocok di teks "bab 2" tapi 'teori' bisa.
        for s in kandidat_bab:
            for kw in s['keywords']:
                if re.fullmatch(r'\d\.\d', kw):
                    continue
                if kw in teks:
                    return s['id'], s['title'], 0.75

        # 2b) PERBAIKAN (a): tak ada kata kunci sub-bab → JANGAN ambil [0].
        #     Jawab bab-nya, TAPI conf rendah → butuh_ai=True.
        #     Alasan: memilih 4.1 untuk "perbaiki bab 4" = MENEBAK tempat.
        if kandidat_bab:
            return kandidat_bab[0]['id'], kandidat_bab[0]['title'], 0.45

    # 3) keyword judul (mis. "pembahasan", "kesimpulan")
    for s in ALL_SECTIONS:
        for kw in s['keywords']:
            if kw in teks:
                skor = min(0.9, 0.5 + len(kw) / 40)     # keyword panjang = yakin
                if skor > terbaik[2]:
                    terbaik = (s['id'], s['title'], skor)
    return terbaik


def _cocok_intent(pesan: str) -> tuple[str, float]:
    """Cocokkan pesan dengan 6 intent. Mengembalikan (intent, skor)."""
    teks = (pesan or '').lower()
    if not teks.strip():
        return 'UNKNOWN', 0.0

    # tanda tanya = PERTANYAAN (paling jelas)
    if teks.strip().endswith('?') or teks.strip().endswith(' ya'):
        for kw in INTENT_KEYWORDS['PERTANYAAN']:
            if kw in teks:
                return 'PERTANYAAN', 0.9

    terbaik, skor = 'UNKNOWN', 0.0
    for nama, kws in INTENT_KEYWORDS.items():
        for kw in kws:
            if kw in teks:
                s = min(0.95, 0.5 + len(kw) / 30)
                if s > skor:
                    terbaik, skor = nama, s
    return terbaik, skor


def urai(pesan: str) -> dict[str, Any]:
    """Urai pesan user -> section + intent + pengali. TANPA AI (Rp 0).

    Mengembalikan dict siap pakai:
      section, section_title, intent, pengali, confidence, butuh_ai,
      mengubah_dokumen, pesan_asli
    `butuh_ai=True` bila confidence < 0.5 → pemanggil boleh tawarkan AI (§4.17).
    """
    pesan = (pesan or '').strip()
    sec_id, sec_title, s_skor = _cocok_section(pesan)
    intent, i_skor = _cocok_intent(pesan)

    # "lebih dalam", "kurang" tanpa konteks lain -> PERKAYA (aturan section-parser.js:99)
    if intent == 'UNKNOWN' and re.search(r'\b(lebih|kurang|agak)\b', pesan.lower()):
        intent, i_skor = 'PERKAYA_NARASI', 0.5

    # "tambah/isi/kasih/lengkapi" -> TAMBAH_DATA (jalur pengaman, baris 160)
    if intent == 'UNKNOWN' and re.search(r'tambah|isi|kasih|lengkapi', pesan.lower()):
        intent, i_skor = 'TAMBAH_DATA', 0.45

    pengali = pilih_pengali(intent, pesan)

    # ── 🔴 PERBAIKAN C-lanjut (05Okt26) — INTENT JANGAN MENUTUPI RAGU BAGIAN ──
    #  CACAT TERUKUR: confidence lama = rata-rata (s_skor + i_skor)/2.
    #  "tolong perbaiki bab 4" → bagian menebak (s_skor 0.45), tapi intent
    #  sangat yakin (i_skor 0.95 "perbaiki") → rata-rata naik jadi 0.61 →
    #  butuh_ai=False → aplikasi MEREVISI 4.1 TANPA memeriksa.  Padahal yang
    #  salah bisa 4.2/4.3/4.5. Ini akar keluhan "revisi tempatnya tidak salah
    #  yang direvisi": keyakinan NIAT dipakai untuk membenarkan TEBAKAN TEMPAT.
    #
    #  ATURAN BARU: niat & tempat = DUA HAL BERBEDA, jangan dirata-rata.
    #    · i_skor = keyakinan NIAT (mau diapakan) — boleh tinggi.
    #    · s_skor = keyakinan TEMPAT (bagian mana) — inilah yang menentukan
    #      apakah aman merevisi tanpa diperiksa.
    #  Niat jelas TIDAK BOLEH menaikkan keyakinan TEMPAT.
    #
    #  Ambang 0,5 = ambang `butuh_ai` yang sudah dipakai file ini (baris 350),
    #  JANGAN bikin ambang baru. Skor 0,45 = penanda "menyebut BAB tapi tak
    #  menyebut sub-bab" (lihat _cocok_section bagian 2b) → WAJIB butuh_ai.
    _RAGU_TEMPAT = 0.5
    if s_skor >= _RAGU_TEMPAT:
        # tempat cukup yakin → aman pakai rata-rata lama (perilaku lama utuh)
        confidence = (round((s_skor + i_skor) / 2, 2) if i_skor
                      else round(s_skor * 0.6, 2))
    else:
        # tempat RAGU → keyakinan dibatasi oleh keraguan TERSEBUT.
        # Niat yang kuat TIDAK menaikkannya.
        confidence = round(s_skor * 0.6, 2) if s_skor else round(i_skor * 0.6, 2)

    hasil = {
        'section': sec_id,
        'section_title': sec_title or None,
        'intent': intent,
        'pengali': pengali,
        'confidence': confidence,
        'butuh_ai': confidence < 0.5,
        'mengubah_dokumen': intent in INTENT_MENGUBAH,
        'preserve_data': intent in ('PERKAYA_NARASI', 'TAMBAH_DATA'),
        'preserve_structure': intent not in ('REVISI', 'GANTI_METODE'),
        'pesan_asli': pesan[:200],
    }
    log.debug('[parser] %r -> %s/%s pengali=%d conf=%.2f',
              pesan[:60], sec_id, intent, pengali, confidence)
    return hasil


def label_pengguna(intent: str, pengali: int) -> str:
    """Teks ramah user (BOS: DILARANG tampilkan 'kuota'/angka token mentah).

    Dipakai untuk pop-up konfirmasi (§4.12) — sebutan resmi = "Token Revisi".
    """
    peta = {
        'PERKAYA_NARASI': 'memperkaya isi',
        'TAMBAH_DATA': 'menambah data/isi',
        'BUAT_TABEL': 'membuat tabel',
        'BUAT_GRAFIK': 'membuat grafik/gambar',
        'REVISI': 'memperbaiki',
        'GANTI_METODE': 'mengganti metode',
        'HAPUS': 'menghapus bagian',
        'PERTANYAAN': 'menjawab pertanyaan',
        'UBAH_ALUR': 'mengubah alur berpikir',
        'UBAH_ALUR_SEMUA': 'mengubah alur seluruh dokumen',
        'UNKNOWN': 'merevisi',
    }
    aksi = peta.get(intent, 'merevisi')
    if pengali > 1:
        return f'{aksi} (setara {pengali}× revisi biasa)'
    return aksi


def daftar_section() -> list[dict[str, Any]]:
    return list(ALL_SECTIONS)


def section_per_kategori(kategori: str) -> list[dict[str, Any]]:
    return list(SECTIONS_CATALOG.get(kategori, []))


# ── BUKTI, BUKAN TEBAPAN (putusan Bos 29Sep26) ─────────────────────────────
#  Mesin DILARANG menebak bagian. Yang dibolehkan HANYA membaca bukti
#  HARIPIAH yang tertulis user lalu mencocokkannya dengan LABEL BAB
#  DOKUMEN INI. Tanpa skor, tanpa `confidence`, tanpa AI:
#    · ada bukti → balas beserta katanya (layar MENAMPILKAN bukti, bukan
#      menyimpulkan); boleh lebih dari satu — TIDAK boleh memilihkan.
#    · tidak ada → balas kosong (layar mendampingi user memilih sendiri).

PANJANG_JUDUL_MIN = 6   # 'saran'(5) sengaja TIDAK jadi bukti — terlalu umum

_ROMAWI_KE_ANGKA = {
    'i': '1', 'ii': '2', 'iii': '3', 'iv': '4', 'v': '5', 'vi': '6',
    'vii': '7', 'viii': '8', 'ix': '9', 'x': '10', 'xi': '11', 'xii': '12',
    'xiii': '13', 'xiv': '14', 'xv': '15', 'xvi': '16', 'xvii': '17',
    'xviii': '18', 'xix': '19', 'xx': '20',
}


def _norm_bukti(pesan: str) -> str:
    """Rapikan untuk pencocokan HARFIAH: huruf kecil, spasi rapat, '3,1'→'3.1'."""
    t = re.sub(r'\s+', ' ', (pesan or '').casefold()).strip()
    return re.sub(r'(?<=\d),(?=\d)', '.', t)


def _nomor_label(label: str) -> tuple[str, list[str]]:
    """Pecah label bagian → (kunci_nomor, daftar variasi ejaan yang setara).

    '3.1 Metode Penelitian' → ('3.1', ['3.1'])
    'BAB III METODE'         → ('bab iii', ['bab iii', 'bab 3'])
    'Lampiran Kuesioner'     → ('', [])
    Variasi hanya EJAAN (romawi↔angka), bukan makna — itu bukan tebakan.
    """
    lab = re.sub(r'\s+', ' ', (label or '').strip()).casefold()
    m = re.match(r'^(\d+(?:[.,]\d+)+|\d+|bab\s+[ivxlcdm]+|bab\s+\d+)\b\s*(.*)$',
                 lab)
    if not m:
        return '', []
    kunci, sisa = m.group(1), m.group(2)
    variasi = [kunci]
    m2 = re.match(r'^bab\s+([ivxlcdm]+|\d+)$', kunci)
    if m2:
        isi = m2.group(1)
        angka = _ROMAWI_KE_ANGKA.get(isi, isi)
        variasi = [f'bab {isi}', f'bab {angka}']
    elif re.match(r'^\d+(?:[.,]\d+)+$', kunci):
        #  ⚠️ JANGAN tambah induknya ('3.1' → jangan ikut '3'): user menulis
        #     "bab 3" berarti bab induk, BUKTI untuk 3.1 = menipu.
        variasi = [kunci, kunci.replace('.', ',')]
    return kunci, list(dict.fromkeys(variasi))


def cocok_bukti(pesan: str, labels: list[str]) -> list[dict[str, Any]]:
    """Cocokkan komentar dengan label bagian dokumen. Tanpa skor/tebakan.

    Mengembalikan SEMUA yang terbukti (boleh >1): [{'label', 'bukti': [...]}].
    Tidak ada satu pun → daftar kosong; pemanggil TIDAK boleh mengisi sendiri.
    """
    teks = _norm_bukti(pesan)
    if not teks or not labels:
        return []
    hasil: list[dict[str, Any]] = []
    for label in labels:
        kunci, variasi = _nomor_label(str(label))
        sisa = re.sub(r'^\d+(?:[.,]\d+)*\s*|^bab\s+[ivxlcdm\d]+\s*', '',
                      _norm_bukti(str(label)))
        bukti: list[str] = []
        for v in variasi:
            if re.search(r'(?<![\w])' + re.escape(v) + r'(?![\w])', teks):
                bukti.append(v)
                break
        if len(sisa) >= PANJANG_JUDUL_MIN and sisa in teks:
            bukti.append(sisa)
        if bukti:
            hasil.append({'label': str(label), 'bukti': bukti})
    return hasil

