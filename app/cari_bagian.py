"""PENCARI BAGIAN NASKAH — untuk mengarahkan pembimbing ke bagian yang dimaksud.

TUJUAN (perintah Bos 24Sep26):
    "kalau bisa saat klik revisi juga langsung menuju halaman revisi yang
     dimaksud, jadi Pembimbing menjadi di mudahkan untuk cek revisian naskah."

Jadi: pembimbing klik satu CATATAN → naskah di kiri meluncur ke bagian yang
dibahas catatan itu. Pembimbing tidak perlu scroll-scroll mencari.

═══════════════════════════════════════════════════════════════════════
CARA KERJA (2 lapis, dari yang paling pasti ke yang paling longgar)
═══════════════════════════════════════════════════════════════════════
Lapis 1 — TEKS ASLI (pasti)
    Kalau catatan punya `teks_asli` (catatan dari Tahap 3, sorotan), pakai
    itu. Paling tepat karena memang teks itu yang ditandai pembimbing.

Lapis 2 — KATA KUNCI (tebakan cerdas)
    Catatan sekarang belum punya sorotan, isinya kalimat bebas seperti
    "Tabel 3.1 belum ada sumbernya". Kita cari potongan yang KHAS di dalam
    catatan (nama tabel, angka bab, istilah panjang) lalu cari di naskah.

═══════════════════════════════════════════════════════════════════════
⚠️ ATURAN YANG DIPEGANG
═══════════════════════════════════════════════════════════════════════
1. JUJUR: kalau tidak ketemu, kembalikan None — template WAJIB bilang
   apa adanya ("belum ketemu di naskah"), JANGAN diam-diam tidak bergerak.
   Pembimbing yang menunggu sesuatu yang tidak terjadi = lebih buruk
   daripada diberi tahu.
2. HEMAT: saringan dilakukan di SERVER (Python), bukan di browser. Naskah
   bisa 400rb karakter — mengirim seluruh naskah ke JS untuk dicari itu
   pemborosan.
3. TIDAK MENGUBAH APA PUN: modul ini murni membaca. Tidak menyentuh
   naskah, tidak menyimpan.
"""

from __future__ import annotations

import re

#  ── Kata yang TERLALU UMUM: kalau dipakai sebagai kata kunci, hasilnya
#  nyasar ke mana-mana. Dibuang dari bahan pencarian. (Daftar sengaja
#  pendek & jelas — bukan kamus.) ─────────────────────────────────────────
_KATA_UMUM = {
    'yang', 'dan', 'atau', 'untuk', 'pada', 'dengan', 'dari', 'ke', 'di',
    'ini', 'itu', 'ada', 'tidak', 'belum', 'sudah', 'akan', 'bisa', 'dapat',
    'harus', 'perlu', 'tolong', 'mohon', 'agar', 'supaya', 'kalau', 'jika',
    'saja', 'juga', 'lebih', 'kurang', 'sangat', 'masih', 'buat', 'buatkan',
    'perbaiki', 'diperbaiki', 'revisi', 'catatan', 'bagian', 'paragraf',
    'kalimat', 'kata', 'halaman', 'lihat', 'cek', 'coba', 'pakai', 'gunakan',
    'jelaskan', 'dijelaskan', 'tambahkan', 'ditambahkan', 'kurang jelas',
    #  ⚠️ Kata berikut TERLALU UMUM kalau berdiri sendiri — "Metode",
    #  "Hasil", "Data" ada di hampir setiap naskah akademik. Kalau dipakai
    #  sebagai kandidat tunggal, naskah akan meluncur ke TEMPAT YANG SALAH
    #  (bukti nyata 24Sep26: "Metode sampling belum dijelaskan" → nyasar ke
    #  kepala "BAB III METODE PENELITIAN"). Boleh dipakai sebagai BAGIAN
    #  frasa ("Metode penelitian"), tapi tidak sebagai kata tunggal.
    'metode', 'metodologi', 'hasil', 'data', 'teori', 'analisis', 'sis',
    'tabel', 'gambar', 'hipotesis', 'penelitian', 'bahasan', 'pembahasan',
    'kesimpulan', 'saran', 'referensi', 'sumber', 'sampel', 'populasi',
}

#  ── Pola yang KHAS dan mudah ditemukan di naskah ──────────────────────
#  Contoh yang tertangkap: "Tabel 3.1", "Gambar 2.4", "Tabel 4.2",
#  "hipotesis H3", "Bab III", "BAB 2", "3.1.2", "2020", "n = 187"
_POLA_KHAS = (
    re.compile(r'\b(Tabel|Gambar|Grafik|Diagram|Lampiran)\s*\.?\s*\d+(?:\.\d+)*',
               re.IGNORECASE),
    re.compile(r'\b([Hh]\d{1,2})\b'),                       # H1, H12
    #  🔴 BUG FIX 03Okt26 (temuan skripsi S1 nyata): pola lama
    #    r'\b(BAB|Bab|bab)\s*([IVXLC]{1,5}|\d{1,2})\b'
    #  punya DUA cacat:
    #    (1) `\s*` = spasi OPSIONAL + nomor WAJIB HURUF BESAR setelahnya →
    #        "Tabel bab 3" ikut COCOK (bab huruf kecil + angka) = SALAH TANGKAP
    #    (2) `\b` di ujung → kebalikan dari masalah versi.py: judul MENEMPEL
    #        ("BAB IPENDAHULUAN") justru GAGAL, padahal itu yang paling sering
    #        di naskah nyata.
    #  POLA BARU = sepola app/state.py:203 (terbukti pada 6 naskah nyata):
    #    'BAB'/'Bab' + spasi WAJIB + romawi HURUF BESAR 1–5 huruf.
    #    → "Tabel bab 3" DITOLAK (bab huruf kecil) · "BAB IPENDAHULUAN" COCOK
    #  ⭐ 05Okt26 (putusan Bos "A"): + BENTUK NYATA dari naskah Bos —
    #    (a) BAB angka Arab ("BAB 1 PENDAHULUAN") — 290465463.pdf nyata;
    #    (b) romawi titik tanpa kata BAB ("IV. HASIL DAN PEMBAHASAN") —
    #        290462754.pdf nyata, dan `$` WAJIB tahan '\r'.
    #    Disamakan dengan app/state.py (pelajaran 03Okt26: pola kembar!).
    re.compile(r'(?i:BAB)[ \t]+([IVXLC]{1,5}|\d{1,2})[ \t]*(?=[A-Z\d])'),
    re.compile(r'^[ \t]*([IVXLC]{1,5})\.[ \t]+[A-Z][A-Z0-9 ,\-]{3,70}[ \t\r]*$',
               re.MULTILINE),
    re.compile(r'\b\d+\.\d+(?:\.\d+)*\b'),                  # 3.1 / 3.1.2
    re.compile(r'\b(19|20)\d{2}\b'),                        # tahun
    re.compile(r'\b[A-Z][a-zA-Z]{4,}\b'),                   # istilah panjang
)


def _potongan_khas(isi: str) -> list[str]:
    """Ambil potongan yang KHAS dari isi catatan (untuk dicari di naskah).

    Urutan penting: yang lebih khas diletakkan LEBIH DULU, supaya pencarian
    memakai yang paling tepat duluan. Contoh nyata:
        "Tabel 3.1 belum ada sumbernya"
        → ['Tabel 3.1']  ← ini yang dipakai (paling khas)
    """
    t = ' '.join((isi or '').split())
    if not t:
        return []
    kandidat: list[str] = []
    #  ── (i) PILIHAN TERBAIK: frasa beberapa kata dari catatan sendiri ──
    #  Catatan pembimbing sering mengutip naskahnya sendiri
    #  ("Teknik sampling yang digunakan belum dijelaskan" ↔ naskah
    #  "Teknik sampling yang digunakan"). Frasa 3 kata jauh lebih tepat
    #  daripada kata tunggal ("Metode" bisa nyasar ke mana-mana).
    kata = re.findall(r"[A-Za-zÀ-ÿ0-9.,]+", t)
    for i in range(len(kata) - 2):
        frasa = ' '.join(kata[i:i + 3])
        if all(k.lower() not in _KATA_UMUM for k in kata[i:i + 3]):
            kandidat.append(frasa)
    #  ── (ii) frasa 2 kata (kalau 3 kata tidak ada yang lolos) ──
    for i in range(len(kata) - 1):
        frasa = ' '.join(kata[i:i + 2])
        if all(k.lower() not in _KATA_UMUM for k in kata[i:i + 2]):
            kandidat.append(frasa)
    #  ── (iii) pola khas (Tabel 3.1 / H3 / 3.1.2 / tahun) ──
    for pola in _POLA_KHAS:
        for m in pola.finditer(t):
            s = ' '.join(m.group(0).split()).strip(' .,;:')
            if len(s) >= 3 and s.lower() not in _KATA_UMUM:
                kandidat.append(s)
    #  ── (iv) terakhir: kata panjang, JANGAN kata biasa ──
    for kata_t in re.findall(r'\b[A-Za-zÀ-ÿ]{7,}\b', t):
        if kata_t.lower() not in _KATA_UMUM:
            kandidat.append(kata_t)
    #  buang duplikat, pertahankan urutan (yang khas dipertahankan duluan)
    hasil, sudah = [], set()
    for k in kandidat:
        u = k.lower()
        if u not in sudah:
            sudah.add(u)
            hasil.append(k)
    return hasil[:16]


def cari_bagian(naskah: str, isi_catatan: str, teks_asli: str = '',
                maks_tampil: int = 260) -> dict | None:
    """Cari bagian naskah yang dimaksud sebuah catatan.

    Return None kalau TIDAK ketemu (template wajib memberi tahu pembimbing).
    Return dict kalau ketemu:
        {'kutipan': '…teks naskah yang ketemu…',
         'dasar':   'teks asli' | 'Tabel 3.1',
         'ketemu':  True}
    """
    naskah = naskah or ''
    if not naskah.strip():
        return None

    #  ── LAPIS 1: teks asli (paling pasti, dari sorotan Tahap 3) ─────────
    ta = ' '.join((teks_asli or '').split())
    if len(ta) >= 12:
        pos = _cari_lentur(naskah, ta)
        if pos is not None:
            return _bungkus(naskah, pos, len(ta), 'teks asli', maks_tampil)

    #  ── LAPIS 2: potongan khas dari isi catatan ────────────────────────
    for kunci in _potongan_khas(isi_catatan):
        pos = _cari_lentur(naskah, kunci)
        if pos is not None:
            return _bungkus(naskah, pos, len(kunci), kunci, maks_tampil)

    return None


def _cari_lentur(naskah: str, kunci: str) -> int | None:
    """Cari `kunci` di naskah dengan TOLERANSI spasi.

    KENAPA tidak pakai `str.find` biasa: naskah hasil ekstraksi .docx sering
    punya spasi/baris baru yang berbeda dari yang diketik pembimbing
    ("Tabel 3.1" vs "Tabel\n3.1"). Pencarian biasa akan GAGAL padahal
    teksnya ada — itu membuat fitur ini terasa rusak padahal bukan.
    """
    k = ' '.join(kunci.split())
    if not k:
        return None
    #  coba persis dulu (paling cepat & paling aman)
    pos = naskah.lower().find(k.lower())
    if pos >= 0:
        return pos
    #  lalu toleran: setiap jeda di kunci boleh jadi apa pun spasi/newline
    try:
        pola = re.compile(r'\s+'.join(re.escape(b) for b in k.split()),
                          re.IGNORECASE)
    except re.error:
        return None
    m = pola.search(naskah)
    return m.start() if m else None


def _bungkus(naskah: str, pos: int, panjang: int, dasar: str,
             maks: int) -> dict:
    """Ambil kutipan secukupnya di sekitar posisi yang ketemu."""
    a = max(0, pos - 60)
    b = min(len(naskah), pos + panjang + 160)
    kutipan = ' '.join(naskah[a:b].split())
    if len(kutipan) > maks:
        kutipan = kutipan[:maks].rstrip() + '…'
    return {'kutipan': kutipan, 'dasar': dasar, 'ketemu': True}


def cari_di_banyak(naskah_daftar: list[str], isi_catatan: str,
                   teks_asli: str = '') -> dict | None:
    """Cari di beberapa naskah (kalau mahasiswa membagikan >1 berkas).

    Return dict + 'berkas_ke' = indeks naskah tempat teks itu ditemukan,
    supaya template bisa MEMINDAH ke berkas yang benar dulu.
    """
    for i, naskah in enumerate(naskah_daftar or []):
        r = cari_bagian(naskah, isi_catatan, teks_asli)
        if r:
            r['berkas_ke'] = i
            return r
    return None
