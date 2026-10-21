"""PENJAGA MUTU ISI BUKU (Lapis 3c) — 19 Okt 2026.

KENAPA ADA (ACC Bos 19 Okt 2026):
  Sejak bab dikerjakan BERSAMAAN (Lapis 3), bab 2 TIDAK lagi menerima
  ringkasan bab 1 — penggantinya hanya jangkar dari outline. Akibatnya isi
  antarbab BISA BERULANG. Tanpa penjaga, hasilnya buku jelek tapi dilaporkan
  "selesai" — kerusakan SUNYI, paling berbahaya.

PRINSIP (aturan Bos: "jangan menuntut cepat kalau hasil salah"):
  Lebih baik MENGULANG satu bab daripada menyerahkan buku cacat. Tapi
  mengulang juga ada batasnya — setelah 1× perbaikan tetap tidak lolos,
  LAPOR JUJUR "TIDAK LOLOS", jangan pura-pura selesai.

NOL PANGGILAN AI — semua pemeriksaan berbasis teks (kemiripan, poin outline,
sitasi). Jadi Rp 0 dan cepat.
"""
import re

#  Ambang kemiripan antarbab.
#  🚨 DIKALIBRASI 19 Okt 2026 memakai BUKU NYATA (AI sungguhan, 3889 + 3642
#     kata): kemiripan kosakata mentah = **31,6%** padahal isinya BEDA TOTAL
#     (0 kalimat disalin). Penyebabnya kata wajar: 'adalah', 'akan', 'anda',
#     'angin', 'atmosfer' — kata domain yang memang harus sama di buku tentang
#     awan & hujan. ⇒ Jaccard MENTAH tidak layak jadi ambang.
#  ⇒ Ambang sekarang memakai ukuran yang lebih jujur:
#     `AMBANG_TUMPANG` untuk KALIMAT BERULANG (penanda isi disalin), dan
#     `AMBANG_MIRIP` dinaikkan ke 0,60 sebagai jaring pengaman kasar saja.
AMBANG_MIRIP = 0.60
AMBANG_TUMPANG = 0.15      # porsi kalimat bab yang muncul juga di bab lain

#  Kata wajar yang HARAM dihitung sebagai kemiripan isi (kalibrasi 19 Okt).
KATA_UMUM = set("""
adalah akan anda antara atau bahwa bagi banyak baru bawah begitu bekerja
belum benar bentuk berbeda besar bisa bukan bumi cara cukup dalam dapat
dari dengan demikian depan di dilakukan dua dunia harus hingga ibu ini
itu juga jadi jika kali karena kebih kehidupan kecil kemudian kepada
kembali kerja kita lagi lain lama lebih luas maka mampu masih mata
melalui melihat memiliki menjadi membuat memberikan seperti mereka
mengenai mengubah menjadi menurut dengan pada para pernah pertama
paling proses pula punya saat sangat satu secara sedang sebagai sebab
sedang setiap sering serta setelah selalu semua sendiri seperti sering
setiap sesuatu sejak seperti sini sudah sulit tahun tanpa tapi telah
tempat terhadap tetapi tidak tinggi terjadi untuk yaitu yang adanya
alam alat angka akhirnya arah atas awal bagian bahkan bawah berbeda
""".split())


def _kata(teks):
    """Ambil kata BERISI (>=5 huruf), huruf kecil, BUANG kata wajar.

    ⚠️ Versi pertama memakai >=4 huruf tanpa filter ⇒ kata seperti 'akan',
    'anda', 'atau' ikut dihitung dan buku sehat dituduh berulang 32%.
    """
    semua = re.findall(r'\b[a-zA-ZÀ-ÿ]{5,}\b', (teks or '').lower())
    return {k for k in semua if k not in KATA_UMUM}


def _kalimat(teks):
    """Pecah jadi kalimat yang cukup panjang (>=10 kata)."""
    bagian = re.split(r'(?<=[.!?])\s+', (teks or '').strip())
    return [b.strip() for b in bagian if len(b.split()) >= 10]


def kemiripan(a, b):
    """Kemiripan himpunan kata (Jaccard), 0..1."""
    ka, kb = _kata(a), _kata(b)
    if not ka or not kb:
        return 0.0
    return len(ka & kb) / len(ka | kb)


def kalimat_berulang(a, b, ambang=0.80):
    """Kalimat yang HAMPIR SAMA muncul di dua bab.

    Berbeda dari `kemiripan`: ini mencari KALIMAT YANG DISALIN, bukan
    sekadar kosakata yang kebetulan sama. Ambang 0,80 = hampir identik.
    """
    kunci = []
    for k in _kalimat(b):
        for k2 in _kalimat(a):
            if kemiripan(k, k2) >= ambang:
                kunci.append(k[:120])
                break
    return kunci


def poin_terpakai(teks, sub_bab):
    """Berapa judul sub-bab yang benar-benar disebut/dibahas di teks."""
    t = (teks or '').lower()
    ketemu = []
    for _nomor, judul, _poin in (sub_bab or []):
        kata_judul = [w for w in re.findall(r'\b[a-zA-ZÀ-ÿ]{4,}\b', judul.lower())]
        if not kata_judul:
            continue
        #  Sub-bab dianggap dibahas kalau >=60% kata judulnya muncul.
        cocok = sum(1 for w in kata_judul if w in t)
        if cocok / len(kata_judul) >= 0.60:
            ketemu.append(judul)
    return ketemu


def periksa_buku(isi_bab, outline, min_sitasi=2, min_kata=300):
    """Periksa SELURUH buku sebelum dirakit.

    `isi_bab`  : {nomor: teks bab}
    `outline`  : {nomor: {'title': ..., 'subs': [(nomor, judul, poin), ...]}}

    Return dict: {'lolos': bool, 'masalah': [...], 'curiga': [...]}
      - `masalah` = HARUS diperbaiki (buku tidak boleh dirakit apa adanya)
      - `curiga`  = dicatat, tidak memblokir
    """
    masalah, curiga = [], []
    nomor = sorted(k for k in isi_bab if isinstance(k, int))

    #  [1] Tiap bab cukup panjang
    for n in nomor:
        kata = len((isi_bab[n] or '').split())
        if kata < min_kata:
            masalah.append(f'BAB {n}: hanya {kata} kata (minimal {min_kata})')

    #  [2] Isi antarbab TIDAK berulang  ← ini alasan Lapis 3c dibuat
    #  ⚠️ KALIBRASI 19 Okt: yang menentukan buku BERULANG adalah KALIMAT yang
    #     muncul di dua bab (`AMBANG_TUMPANG`), BUKAN kosakata mirip. Kosakata
    #     mentah 31,6% pada buku sehat ⇒ jangan dipakai sebagai penentu utama.
    for i, a in enumerate(nomor):
        for b in nomor[i + 1:]:
            kal_a = _kalimat(isi_bab[a])
            kal_b = _kalimat(isi_bab[b])
            salinan = kalimat_berulang(isi_bab[a], isi_bab[b])
            #  Porsi kalimat bab A yang juga muncul di bab B.
            porsi = len(salinan) / max(1, len(kal_a))
            #  🚨 KALIBRASI 19 Okt: aturan "3 kalimat atau >=15%" TERLALU
            #     LONGGAR — satu kalimat panjang (bab 3000 kata punya ~30
            #     kalimat) = 3% saja, jadi LOLOS. Padahal menyalin SATU
            #     kalimat utuh sudah salah.
            #  ⇒ Ambang: 1 kalimat utuh (>=10 kata) yang hampir identik
            #     sudah cukup ditandai. Untuk kemiripan sedang, pakai porsi.
            ada_panjang = any(len(k.split()) >= 10 for k in salinan)
            if salinan and (ada_panjang or porsi >= AMBANG_TUMPANG
                            or len(salinan) >= 3):
                masalah.append(
                    f'BAB {a} & BAB {b}: {len(salinan)} kalimat DISALIN '
                    f'({porsi:.0%} kalimat bab {a}) — "{salinan[0][:70]}..."')
            elif kemiripan(isi_bab[a], isi_bab[b]) >= AMBANG_MIRIP:
                masalah.append(
                    f'BAB {a} & BAB {b} terlalu mirip '
                    f'({kemiripan(isi_bab[a], isi_bab[b]):.0%} kosakata) '
                    f'— periksa apakah isinya berulang')

    #  [3] Tiap bab membahas sub-babnya sendiri
    for n in nomor:
        subs = (outline.get(n) or {}).get('subs') or []
        if not subs:
            continue
        ketemu = poin_terpakai(isi_bab[n], subs)
        if len(ketemu) < len(subs):
            hilang = [s[1] for s in subs if s[1] not in ketemu]
            curiga.append(f'BAB {n}: sub-bab mungkin tidak dibahas: {hilang}')

    #  [4] Sitasi cukup (penjaga lama, jangan hilang saat paralel)
    for n in nomor:
        jum = len(re.findall(r'\([A-Z][^)]{2,60}\d{4}\)', isi_bab[n] or ''))
        if jum < min_sitasi:
            curiga.append(f'BAB {n}: hanya {jum} sitasi (disarankan '
                          f'≥{min_sitasi})')

    return {'lolos': not masalah, 'masalah': masalah, 'curiga': curiga}


def ringkas(hasil):
    """Kalimat siap-tampil untuk laporan ke user (tanpa istilah teknis)."""
    if hasil['lolos']:
        return 'Semua bab sudah diperiksa: isinya tidak berulang.'
    return 'Perlu diperbaiki: ' + '; '.join(hasil['masalah'][:3])


def bab_bermasalah(hasil):
    """Nomor bab yang disebut di `masalah` + `curiga` (keduanya TEKS).

    ⚠️ Bentuk `masalah`/`curiga` = LIST STRING ("BAB 2: ..."), BUKAN dict.
    Jangan menebak `m['bab']` — tidak ada kuncinya.
    """
    nomor = set()
    for pesan in list(hasil.get('masalah') or []) + list(hasil.get('curiga') or []):
        for n in re.findall(r'BAB\s+(\d+)', str(pesan)):
            nomor.add(int(n))
    return sorted(nomor)


def arahan_perbaikan(hasil, bab):
    """Arahan KONKRET untuk menulis ulang satu bab yang bermasalah.

    Dipakai `penyusun_buku` (Lapis 3c-2) sebagai tambahan jangkar bab.
    ⚠️ Harus menyebut MASALAHNYA, bukan "tolong lebih baik" — tanpa itu model
    akan menulis ulang dengan pola yang sama dan masalahnya berulang.
    """
    pola_bab = re.compile(r'BAB\s+' + str(bab) + r'\b')
    pesan = [str(m) for m in (hasil.get('masalah') or [])
             if pola_bab.search(str(m))]
    if not pesan:
        return ''
    lain = sorted({int(x) for m in pesan
                   for x in re.findall(r'BAB\s+(\d+)', m)} - {bab})
    baris = [
        "",
        "=== ARAHAN WAJIB (bab ini HARUS ditulis ULANG) ===",
        "Bab ini sebelumnya GAGAL diperiksa. Masalahnya:",
    ]
    for p_ in pesan[:4]:
        baris.append(f'- {p_}')
    if lain:
        daftar = ", ".join(str(x) for x in lain)
        baris.append(
            f'- JANGAN mengulang isi bab {daftar}. '
            'Ambil sudut pandang, contoh, dan urutan penjelasan yang BERBEDA. '
            'Pembaca sudah membaca bab itu.')
    baris.append(
        "Tulis ulang SELURUH bab: struktur sub-bab tetap sama, tetapi ISI tiap "
        "sub-bab HARUS baru — bukan kalimat lama yang dipindah urutannya.")
    return "\n".join(baris)
