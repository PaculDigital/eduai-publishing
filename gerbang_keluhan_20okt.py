"""Verifikasi 4 keluhan Bos — cek pada PROMPT & GAYA nyata, bukan tebakan.

DIPECAH jadi fungsi `jalankan(modul, modul_brief)` supaya BISA DIUJI BERGIGI:
suntik kerusakan ke SALINAN, panggil `jalankan()` dengan salinan itu,
dan gerbang HARUS GAGAL. Gerbang yang tak bisa gagal = HIASAN.

Cara pakai normal:  python gerbang_keluhan_20okt.py
"""
import re
import sys


def jalankan(modul=None, modul_brief=None, cetak=True):
    """Jalankan semua asersi. Return (lulus, gagal, rincian_gagal)."""
    if modul is None:
        import diagram_buku as modul            # noqa: F811
    if modul_brief is None:
        import brief_visual as modul_brief      # noqa: F811

    lulus = 0
    gagal = []

    def cek(nama, syarat, pesan=''):
        nonlocal lulus
        if syarat:
            lulus += 1
            if cetak:
                print(f'  LULUS {nama}')
        else:
            gagal.append(f'{nama}: {pesan}')
            if cetak:
                print(f'  GAGAL {nama} — {pesan}')

    if cetak:
        print('=== KELUHAN 4: latar ilustrasi putih, ada outline, TANPA krem ===')
    for g in ('premium-konseptual', 'editorial-lineart', 'flat-editorial'):
        p = modul_brief.prompt_gambar('seorang anak mengamati bayangan tongkat',
                                      gaya=g)
        cek(f'{g}: latar PURE WHITE', 'PURE WHITE' in p and '#FFFFFF' in p,
            'latar putih tidak diminta')
        cek(f'{g}: TIDAK minta cream/beige', 'no cream' in p and 'no beige' in p,
            'larangan krem tidak ada')
        cek(f'{g}: ada outline', 'outline' in p.lower(), 'outline tidak diminta')
        cek(f'{g}: tidak menyuruh "on warm cream"',
            'on warm cream' not in p.lower(), 'MASIH menyuruh latar krem')

    if cetak:
        print()
        print('=== KELUHAN 2: variasi bentuk diagram dipilih dari ISI ===')
    kasus = [
        ('Daur Air', 'air laut menguap lalu turun kembali ke laut',
         ['menguap', 'mengembun', 'hujan', 'mengalir'], 'siklus'),
        ('Langkah Mencuci Tangan', 'proses pertama kedua ketiga',
         ['basahi', 'sabun', 'bilas'], 'alur'),
        ('Hierarki Kebutuhan', 'tingkatan dari dasar ke puncak',
         ['dasar', 'sosial', 'puncak'], 'piramida'),
        ('Proporsi Sampah', 'proporsi bagian terbesar',
         ['organik', 'plastik', 'kertas'], 'pai'),
        ('Perkembangan Panen', 'tren naik turun sepanjang waktu',
         ['2020', '2021', '2022'], 'garis'),
        ('Klasifikasi Awan', 'jenis-jenis dan penggolongan awan',
         ['sirus', 'kumulus', 'stratus'], 'pohon'),
        ('Lapisan Atmosfer', 'lapisan struktur dari permukaan',
         ['troposfer', 'stratosfer', 'mesosfer'], 'lapisan'),
    ]
    bentuk_dipakai = set()
    for j, k, t, harus in kasus:
        dapat = modul.pilih_bentuk(j, k, t)
        bentuk_dipakai.add(dapat)
        cek(f'{j} -> {harus}', dapat == harus, f'dapat {dapat}')

    cek(f'variasi >= 6 bentuk berbeda (dapat {len(bentuk_dipakai)})',
        len(bentuk_dipakai) >= 6, 'variasi kurang — masih monoton')

    if cetak:
        print()
        print('=== KELUHAN 2 & 3: teks rata tengah, TIDAK justify, '
              'TIDAK full width ===')
    gaya = modul.GAYA
    gaya_rendah = gaya.lower()

    #  🚨 GAGAL PALSU TERUKUR 20 Okt 2026: asersi lama mencari kata `justify`
    #  saja ⇒ tertangkap `justify-content:center` (flexbox, MEMUSATKAN elemen,
    #  justru YANG KITA INGINKAN). Obat: periksa PASANGAN properti+nilai
    #  yang sebenarnya dilarang — `text-align: justify` — bukan potongan kata.
    _justify_teks = re.findall(r'text-align\s*:\s*justify', gaya_rendah)
    cek('TIDAK ada text-align:justify (teks rata kiri-kanan)',
        not _justify_teks,
        f'MASIH ada text-align:justify ({len(_justify_teks)}×)')

    #  Lawannya: `justify-content` di flexbox HARUS tetap ada (memusatkan).
    cek('justify-content TETAP dipakai untuk memusatkan',
        'justify-content:center' in gaya_rendah,
        'justify-content:center hilang — elemen tidak lagi di tengah')

    cek('tidak ada width:100% pada kotak tahap', '.tahap' not in gaya,
        'kelas .tahap lama masih ada (kotak melebar)')
    cek('kartu TIDAK 720px full width', 'width:720px' not in gaya,
        'kartu masih full width 720px')
    cek('ada text-align:center', 'text-align:center' in gaya_rendah,
        'tidak ada center')

    #  ── KELUHAN 4 (BAGIAN GAYA): latar dokumen HARUS putih, bukan krem ──
    cek('latar body putih (#FFFFFF)', 'background:#ffffff' in gaya_rendah,
        'latar bukan putih bersih')

    #  🚨 GAGAL PALSU KEDUA TERUKUR 20 Okt 2026: regex `#f...` menangkap
    #  `#ffffff` (PUTIH! karena f-f-f-f-f-f cocok pola f[0-9a-f]{5}) dan
    #  `#edf1f4` (abu kebiruan). Obat: JANGAN menebak dari pola hex —
    #  HITUNG warnanya: krem/beige = merah > biru (hangat) DAN bukan putih.
    _krem = []
    for hexval in re.findall(r'background\s*:\s*#([0-9a-f]{6})', gaya_rendah):
        rr = int(hexval[0:2], 16)
        gg = int(hexval[2:4], 16)
        bb = int(hexval[4:6], 16)
        if (rr, gg, bb) == (255, 255, 255):
            continue                        # putih bersih — BOLEH
        #  hangat = merah jelas di atas biru; abu netral tidak hangat
        if rr - bb >= 12 and rr >= 200:
            _krem.append('#' + hexval)
    cek('TIDAK ada latar krem/beige (diukur dari nilai RGB)', not _krem,
        f'latar hangat/krem terdeteksi ({_krem[:3]})')

    return lulus, len(gagal), gagal


def main():
    lulus, gagal, rincian = jalankan()
    print()
    print('=' * 60)
    print({'lulus': lulus, 'gagal': gagal, 'rincian_gagal': rincian})
    sys.exit(0 if not gagal else 1)


if __name__ == '__main__':
    main()
