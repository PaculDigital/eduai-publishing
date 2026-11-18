"""DIAGRAM MODEL DAN DESAIN PENELITIAN, logika murni, tanpa AI.

Harga: 1 token per gambar (keputusan Boss 17 Nov 2026 09:24 WIB).
Gambar digambar mesin secara deterministik dari data model (bukan AI);
mahasiswa terima, tolak, atau lengkapi draf mesin (Boss 17 Nov 09:22 WIB).
Gambar yang sudah ada tidak pernah diganti diam-diam: ditawarkan dulu
(Boss 17 Nov 09:24 WIB).

Teks 3.1 untuk Desain ditulis dari template deterministik (bukan AI):
isinya hanya fakta standar (jenis, desain, langkah), jadi tidak butuh
AI; harganya tetap 1 token per gambar, tanpa tagihan kedua.
"""
from __future__ import annotations

import re
import zipfile
from pathlib import Path

HARGA_GAMBAR = 1

PERAN_SAH = ('X', 'Z', 'M', 'Y')
JENIS_SAH = ('kuantitatif', 'kualitatif', 'campuran')
DESAIN_PER_JENIS = {
    'kuantitatif': ('survei', 'eksperimen', 'pra-eksperimen', 'korelasional'),
    'kualitatif': ('eksploratif', 'fenomenologis', 'studi kasus'),
    'campuran': ('campuran',),
}
LABEL_JENIS = {
    'kuantitatif': 'kuantitatif',
    'kualitatif': 'kualitatif',
    'campuran': 'campuran',
}
LABEL_DESAIN = {
    'survei': 'survei',
    'eksperimen': 'eksperimen',
    'pra-eksperimen': 'pra-eksperimen',
    'korelasional': 'korelasional',
    'eksploratif': 'eksploratif',
    'fenomenologis': 'fenomenologis',
    'studi kasus': 'studi kasus',
    'campuran': 'campuran',
}

# Langkah alur per desain (dari pedoman, deterministik, tanpa AI).
LANGKAH_DESAIN = {
    'survei': ['Tentukan populasi dan sampel', 'Susun instrumen',
               'Sebar kuesioner', 'Olah data', 'Uji hipotesis',
               'Simpulkan hasil'],
    'eksperimen': ['Tentukan kelompok perlakuan dan kontrol',
                   'Beri perlakuan', 'Ukur sebelum dan sesudah',
                   'Bandingkan hasil', 'Simpulkan pengaruh'],
    'pra-eksperimen': ['Tentukan kelompok', 'Beri perlakuan',
                       'Ukur hasil', 'Simpulkan'],
    'korelasional': ['Tentukan variabel', 'Kumpulkan data',
                     'Hitung hubungan antar variabel', 'Simpulkan'],
    'eksploratif': ['Tentukan fokus', 'Kumpulkan data awal',
                    'Petakan temuan', 'Simpulkan'],
    'fenomenologis': ['Tentukan informan', 'Wawancara mendalam',
                      'Petakan pengalaman', 'Simpulkan makna'],
    'studi kasus': ['Tentukan kasus',
                    'Kumpulkan bukti dari banyak sumber',
                    'Analisis kasus', 'Simpulkan'],
    'campuran': ['Kumpulkan data kuantitatif',
                 'Kumpulkan data kualitatif', 'Gabungkan temuan',
                 'Simpulkan'],
}

KANVAS_LEBAR = 1400
KANVAS_TINGGI = 800
# Garis tengah horizontal kanvas: pusat Z dan Y selalu di sini, kolom X
# simetris terhadap garis ini (contoh skripsi Boss 18 Nov 2026).
TENGAH_KANVAS = KANVAS_TINGGI // 2
# Jarak pusat X terluar ke garis tengah (1 X) / setengah bentang
# kolom X (2-4 X). 250 px supaya panah langsung X ke Y lewat jelas
# di atas/bawah Z (dengan 210 px, panah itu hanya 3,7 px di atas Z
# bila Z 2 baris, sehingga ikut terbengkok).
LANGKAH_X = 250
LEBAR_KOTAK = 300


def _rapi(teks) -> str:
    return ' '.join(str(teks or '').split()).strip()


def _normalisasi_nama(nama: str) -> str:
    return re.sub(r'\s+', ' ', str(nama or '').strip()).lower()


def normalisasi_model(data) -> tuple:
    """Periksa + rapikan data model. Kembalikan (model, masalah).

    Model: {'variabel': [{'nama', 'peran', 'kode'}],
            'jalur': [{'dari', 'ke', 'hipotesis', 'jenis', 'arah'}],
            'jenis': ..., 'desain': ...}.
    Peran 'M' (peta Bab IV) dibaca sama dengan 'Z' (perantara).
    Masalah berbahasa Indonesia polos; kosong berarti model sah.
    """
    masalah: list[str] = []
    if not isinstance(data, dict):
        return None, ['Data model tidak terbaca.']
    variabel_masuk = data.get('variabel') or []
    jalur_masuk = data.get('jalur') or []
    variabel: list[dict] = []
    lihat: dict[str, str] = {}
    for v in variabel_masuk:
        if not isinstance(v, dict):
            continue
        nama = _rapi(v.get('nama'))
        peran = str(v.get('peran') or '').strip().upper()
        if not nama:
            continue
        if peran not in PERAN_SAH:
            masalah.append(f'Peran "{peran}" untuk "{nama}" tidak dikenal.')
            continue
        if peran == 'M':
            peran = 'Z'
        kunci = _normalisasi_nama(nama)
        if kunci in lihat and lihat[kunci] != peran:
            masalah.append(f'"{nama}" muncul dengan dua peran berbeda.')
            continue
        if kunci in lihat:
            continue
        lihat[kunci] = peran
        variabel.append({'nama': nama, 'peran': peran})
    peran_ada = {v['peran'] for v in variabel}
    if 'X' not in peran_ada:
        masalah.append('Belum ada variabel bebas (X).')
    if 'Y' not in peran_ada:
        masalah.append('Belum ada variabel hasil (Y).')
    if sum(1 for v in variabel if v['peran'] == 'Y') > 1:
        masalah.append('Variabel hasil (Y) hanya boleh satu.')
    # Kode: X1, X2, ...; Z; Y (urut masukan dipertahankan).
    hitung = {'X': 0}
    for v in variabel:
        if v['peran'] == 'X':
            hitung['X'] += 1
            v['kode'] = f"X{hitung['X']}"
        elif v['peran'] == 'Z':
            v['kode'] = 'Z'
        else:
            v['kode'] = 'Y'
    if len([v for v in variabel if v['peran'] == 'Z']) > 1:
        masalah.append('Perantara (Z) hanya boleh satu.')
    nama_ke_kode = {_normalisasi_nama(v['nama']): v['kode']
                    for v in variabel}
    kode_ke_kode = {v['kode'].lower(): v['kode'] for v in variabel}

    def _cari_kode(teks: str):
        """Cari kode variabel dari nama atau kode apa adanya.

        Formulir mengirim kode (X1, X2, Z, Y), naskah/peta mengirim
        nama; keduanya harus dikenali. Nama didahulukan supaya nama
        "X2" tetap menunjuk variabel bernama X2, bukan kode X2.
        """
        kunci = _normalisasi_nama(teks)
        if kunci in nama_ke_kode:
            return nama_ke_kode[kunci]
        return kode_ke_kode.get(kunci)

    jalur: list[dict] = []
    label_pakai: set[str] = set()
    for j in jalur_masuk:
        if not isinstance(j, dict):
            continue
        dari = _rapi(j.get('dari'))
        ke = _rapi(j.get('ke'))
        lewat = _rapi(j.get('lewat'))
        label = _rapi(j.get('hipotesis'))
        jenis = str(j.get('jenis') or 'langsung').strip().lower()
        arah = str(j.get('arah') or '').strip()
        if not dari or not ke:
            continue
        kode_dari = _cari_kode(dari)
        if kode_dari is None:
            masalah.append(f'Jalur menunjuk "{dari}" yang tidak ada '
                           'di daftar variabel.')
            continue
        kode_ke = _cari_kode(ke)
        if kode_ke is None:
            masalah.append(f'Jalur menunjuk "{ke}" yang tidak ada '
                           'di daftar variabel.')
            continue
        kode_lewat = ''
        if lewat:
            kode_lewat = _cari_kode(lewat)
            if kode_lewat is None:
                masalah.append(f'Jalur menunjuk "{lewat}" yang tidak '
                               'ada di daftar variabel.')
                continue
            if kode_lewat in (kode_dari, kode_ke):
                masalah.append('Lewat harus variabel lain, bukan Dari '
                               'atau Ke.')
                continue
            peran_lewat = next((v['peran'] for v in variabel
                                if v['kode'] == kode_lewat), '')
            if peran_lewat != 'Z':
                masalah.append('Lewat harus perantara (Z).')
                continue
            jenis = 'tidak_langsung'
        if not label:
            masalah.append('Ada jalur yang belum berlabel hipotesis.')
            continue
        if label in label_pakai:
            masalah.append(f'Label {label} dipakai dua jalur.')
            continue
        label_pakai.add(label)
        if jenis not in ('langsung', 'tidak_langsung', 'interaksi'):
            jenis = 'langsung'
        if arah not in ('+', '-', ''):
            arah = ''
        jalur.append({'dari': kode_dari, 'ke': kode_ke,
                      'lewat': kode_lewat, 'hipotesis': label,
                      'jenis': jenis, 'arah': arah})
    if masalah:
        return None, masalah
    return {'variabel': variabel, 'jalur': jalur,
            'jenis': data.get('jenis') or '',
            'desain': data.get('desain') or ''}, []


def model_tampilan(data) -> dict:
    """Bentuk model apa adanya untuk ditampilkan lagi di formulir.

    Dipakai saat validasi gagal: isian mahasiswa (nama, peran, Dari,
    Ke, Lewat, label, arah) ditampilkan lagi persis seperti diketik,
    tidak hilang. Tidak memeriksa apa pun; kode dihitung dari urutan
    peran seperti normalisasi_model, dan Dari/Ke/Lewat ditulis sebagai
    kode bila dikenali supaya cocok dengan pilihan formulir.
    """
    if not isinstance(data, dict):
        return {'variabel': [], 'jalur': [], 'jenis': '', 'desain': ''}
    variabel: list[dict] = []
    hitung = {'X': 0}
    for v in data.get('variabel') or []:
        if not isinstance(v, dict):
            continue
        nama = _rapi(v.get('nama'))
        peran = str(v.get('peran') or 'X').strip().upper()
        if peran not in PERAN_SAH:
            peran = 'X'
        if peran == 'M':
            peran = 'Z'
        if not nama:
            continue
        if peran == 'X':
            hitung['X'] += 1
            kode = f"X{hitung['X']}"
        elif peran == 'Z':
            kode = 'Z'
        else:
            kode = 'Y'
        variabel.append({'nama': nama, 'peran': peran, 'kode': kode})
    kunci: dict[str, str] = {}
    for v in variabel:
        kunci[_normalisasi_nama(v['nama'])] = v['kode']
        kunci[v['kode'].lower()] = v['kode']

    def _kode(teks: str) -> str:
        return kunci.get(_normalisasi_nama(teks), _rapi(teks))

    jalur: list[dict] = []
    for j in data.get('jalur') or []:
        if not isinstance(j, dict):
            continue
        lewat = _rapi(j.get('lewat'))
        jalur.append({'dari': _kode(j.get('dari')),
                      'ke': _kode(j.get('ke')),
                      'lewat': _kode(lewat) if lewat else '',
                      'hipotesis': _rapi(j.get('hipotesis')),
                      'jenis': str(j.get('jenis') or 'langsung'),
                      'arah': str(j.get('arah') or '').strip()})
    return {'variabel': variabel, 'jalur': jalur,
            'jenis': data.get('jenis') or '',
            'desain': data.get('desain') or ''}


def bentuk_model(model: dict) -> str:
    """'mediasi' bila ada Z, 'banyak_x' bila X lebih dari satu,
    sisanya 'langsung'."""
    peran = [v['peran'] for v in model.get('variabel') or []]
    if 'Z' in peran:
        return 'mediasi'
    if peran.count('X') > 1:
        return 'banyak_x'
    return 'langsung'


def _jumlah_baris_nama(nama: str, lebar: int = LEBAR_KOTAK) -> int:
    """Jumlah baris nama bila dibungkus (aturan sama dengan editor)."""
    maks = 30 if lebar > 400 else 18
    kata = str(nama or '').split()
    baris = 1
    kini = ''
    for k in kata:
        coba = (kini + ' ' + k).strip()
        if len(coba) <= maks or not kini:
            kini = coba
        else:
            baris += 1
            kini = k
    return baris


def tinggi_kotak(nama: str, lebar: int = LEBAR_KOTAK) -> int:
    """Tinggi kotak supaya nama muat di dalamnya (tidak terpotong).

    Aturan bungkus sama dengan editor (maks 18 karakter per baris
    untuk lebar 300, 30 untuk lebar 600): 1 baris = 90, 2 baris = 110
    (baris kedua berakhir di y+98 di PNG dan y+91 di editor).
    """
    return 110 if _jumlah_baris_nama(nama, lebar) >= 2 else 90


def _tinggi_muat(nama: str, lebar: int = LEBAR_KOTAK) -> int:
    """Tinggi minimal supaya nama muat di dalam kotak (tidak terpotong).

    Teks kotak di PNG: kode di y+10, nama mulai y+42, tiap baris 28 px
    (font 24, tinggi glif 23); nama 1 baris berakhir y+70, 2 baris
    y+98. Jadi 76 / 104 (margin 6 px). Dipakai kolom X yang padat
    (5 X ke atas), supaya kotak tetap ramping tapi teks tidak meluap.
    """
    return 104 if _jumlah_baris_nama(nama, lebar) >= 2 else 76


def _tahap_variabel(variabel, jalur):
    """Tahap (kolom) tiap variabel dari graf jalur (longest-path).

    Tahap 0 bila tanpa jalur masuk, bila tidak 1 + maks tahap
    pendahulu. Jalur lewat diurai jadi dua sisi (Dari ke Lewat,
    Lewat ke Ke). Diulang sebanyak jumlah variabel supaya graf
    berputar (siklus) tetap berhenti dengan nilai deterministik.
    X/Z/Y biasa kembali jadi X 0, Z 1, Y 2; tanpa Z jadi X 0, Y 1.
    """
    kode = [v.get('kode') or v.get('nama') for v in variabel]
    tahap = {k: 0 for k in kode if k}
    nama_ke_kode = {}
    for v in variabel:
        k = v.get('kode') or v.get('nama')
        if k:
            nama_ke_kode[_normalisasi_nama(v.get('nama') or '')] = k
            nama_ke_kode[str(k).lower()] = k

    def _kode(teks):
        if not teks:
            return None
        t = str(teks)
        if t in tahap:
            return t
        return nama_ke_kode.get(_normalisasi_nama(t))

    sisi = []
    for j in jalur or []:
        dari = _kode(j.get('dari'))
        ke = _kode(j.get('ke'))
        lewat = _kode(j.get('lewat'))
        if lewat and dari and ke:
            sisi.append((dari, lewat))
            sisi.append((lewat, ke))
        elif dari and ke:
            sisi.append((dari, ke))
    for _ in range(max(1, len(tahap))):
        berubah = False
        for u, v in sisi:
            if tahap[v] < tahap[u] + 1:
                tahap[v] = tahap[u] + 1
                berubah = True
        if not berubah:
            break
    return tahap


def _pusat_tumpukan(i, n, pusat_satu=400):
    """Pusat vertikal kotak ke-i dari n kotak yang simetris terhadap
    garis tengah. 1 kotak di pusat_satu; 2-4 kotak berjarak sama
    dengan pusat terluar ±LANGKAH_X dari garis tengah."""
    if n == 1:
        return pusat_satu
    langkah = 2 * LANGKAH_X / (n - 1)
    return TENGAH_KANVAS + (i - (n - 1) / 2) * langkah


def _y_tumpukan_padat(nama_list, lebar=LEBAR_KOTAK):
    """Daftar y untuk tumpukan padat (5+ kotak), terpusat simetris
    di garis tengah; celah 14 px, ditekan ke 6 px bila kolom lebih
    tinggi dari kanvas."""
    hs = [_tinggi_muat(n, lebar) for n in nama_list]
    celah = 14
    total = sum(hs) + (len(hs) - 1) * celah
    if total > 760:
        celah = max(6, (760 - sum(hs)) // max(1, len(hs) - 1))
        total = sum(hs) + (len(hs) - 1) * celah
    y0 = max(20, 400 - total // 2)
    out, yy = [], y0
    for h in hs:
        out.append(yy)
        yy += h + celah
    return out


def tata_letak(model: dict) -> dict:
    """Tata letak deterministik: kotak + panah dalam kanvas 1400x800
    (dilebarkan bila kolom lebih dari 3).

    Template per jumlah variabel (aturan umum, bukan per model):
    tahap tiap variabel diturunkan dari graf jalur (longest-path):
    tanpa jalur masuk tahap 0, bila tidak 1 + maks tahap pendahulu;
    X/Z/Y biasa kembali jadi 3 kolom (X 0, Z 1, Y 2), tanpa Z jadi
    2 kolom; model bertahap (mis. Goal-Directed) jadi N kolom.
    Tiap kolom simetris terhadap garis tengah: 1 kotak di garis
    tengah (kecuali kolom X klasik yang 1 X-nya di atas garis
    tengah, supaya X, Z, Y tidak segaris seperti contoh 1 Boss);
    2-4 kotak berjarak sama simetris; 5 kotak ke atas tumpukan
    terpusat simetris. Jarak antar kolom 490 px (3 kolom ke bawah,
    sama seperti dulu: X 60, Z 550, Y 1040) atau 420 px (4 kolom ke
    atas, kanvas dilebarkan supaya label panah muat di celah 120 px).
    Panah langsung yang menabrak kotak (mis. X di garis tengah ke Y
    lewat Z) TIDAK dihindari dengan menggeser kotak, melainkan
    dibengkokkan lewat atas kotak itu di penempatan_label
    (app/gambar.py) dan gambarUlang editor. Panah 'tidak_langsung'
    digambar putus-putus: dua segmen (Dari ke Lewat, Lewat ke Ke)
    bila ada Lewat, satu segmen (Dari ke Ke) bila tidak ada; tiap
    segmen berlabel hipotesisnya, supaya H6/H7 terlihat di draf.
    Kembalikan {'kotak', 'panah', 'bentuk', 'lebar'}; 'lebar' =
    lebar kanvas model ini (1400 bila 3 kolom ke bawah).
    """
    variabel = model.get('variabel') or []
    tahap = _tahap_variabel(variabel, model.get('jalur') or [])
    kolom: dict[int, list] = {}
    for v in variabel:
        kolom.setdefault(tahap.get(v.get('kode') or v.get('nama'), 0),
                         []).append(v)
    n_kolom = (max(tahap.values()) + 1) if tahap else 1
    if n_kolom <= 1:
        lebar_kanvas = KANVAS_LEBAR
        x_kolom = [550]
    elif n_kolom <= 3:
        lebar_kanvas = KANVAS_LEBAR
        pitch = 980 / (n_kolom - 1)
        x_kolom = [60 + round(i * pitch) for i in range(n_kolom)]
    else:
        pitch = 420
        lebar_kanvas = 420 + (n_kolom - 1) * pitch
        x_kolom = [60 + i * pitch for i in range(n_kolom)]
    kotak: list[dict] = []
    for t in sorted(kolom):
        vs = kolom[t]
        n = len(vs)
        # 1 kotak di kolom X klasik (3 kolom ke bawah) di atas garis
        # tengah; kolom lain 1 kotaknya di garis tengah.
        klasik_x = (n_kolom <= 3 and t == 0
                    and all(v.get('peran') == 'X' for v in vs))
        pusat_satu = (TENGAH_KANVAS - LANGKAH_X) if klasik_x \
            else TENGAH_KANVAS
        if n > 4:
            # Tumpukan padat: kotak setinggi nama (76/104) supaya
            # teks tidak meluap, kolom direnggang supaya kotak tidak
            # tumpang tindih (celah 14 px, tengah di y=400).
            ys = _y_tumpukan_padat([v['nama'] for v in vs])
            hs = [_tinggi_muat(v['nama']) for v in vs]
        else:
            hs = [tinggi_kotak(v['nama']) for v in vs]
            ys = [round(_pusat_tumpukan(i, n, pusat_satu) - h / 2)
                  for i, h in enumerate(hs)]
        for v, h, y in zip(vs, hs, ys):
            kotak.append({'id': v.get('kode') or v.get('nama'),
                          'nama': v['nama'],
                          'kode': v.get('kode') or v.get('nama'),
                          'peran': v.get('peran') or 'X',
                          'x': x_kolom[t], 'y': y,
                          'w': LEBAR_KOTAK, 'h': h})
    panah: list[dict] = []
    for j in model.get('jalur') or []:
        label = j['hipotesis']
        if j.get('arah'):
            label = f"{label} ({j['arah']})"
        if j.get('jenis') == 'tidak_langsung':
            if j.get('lewat'):
                panah.append({'dari': j['dari'], 'ke': j['lewat'],
                              'label': label, 'gaya': 'lewat'})
                panah.append({'dari': j['lewat'], 'ke': j['ke'],
                              'label': label, 'gaya': 'lewat'})
            else:
                panah.append({'dari': j['dari'], 'ke': j['ke'],
                              'label': label, 'gaya': 'lewat'})
            continue
        panah.append({'dari': j['dari'], 'ke': j['ke'], 'label': label,
                      'gaya': 'putus' if j.get('jenis') == 'interaksi'
                      else 'lurus'})
    return {'kotak': kotak, 'panah': panah,
            'bentuk': bentuk_model(model), 'lebar': lebar_kanvas}


def tata_dari_kotak(kotak, panah, jenis: str = 'model') -> tuple:
    """Periksa tata letak buatan mahasiswa di editor.
    Kembalikan (tata, masalah)."""
    masalah: list[str] = []
    if not isinstance(kotak, list) or not kotak:
        return None, ['Belum ada kotak di gambar.']
    bersih: list[dict] = []
    id_ada: set[str] = set()
    for k in kotak:
        if not isinstance(k, dict):
            continue
        nama = _rapi(k.get('nama'))
        peran = str(k.get('peran') or 'X').strip().upper()
        if not nama:
            continue
        if jenis == 'model' and peran not in PERAN_SAH:
            masalah.append(f'Peran "{peran}" tidak dikenal.')
            continue
        if jenis == 'desain':
            peran = 'langkah'
        try:
            x = int(k.get('x', 0))
            y = int(k.get('y', 0))
        except (TypeError, ValueError):
            x, y = 0, 0
        x = max(0, min(KANVAS_LEBAR - 120, x))
        y = max(0, min(KANVAS_TINGGI - 60, y))
        kid = str(k.get('id') or f'k{len(bersih) + 1}')
        if kid in id_ada:
            kid = f'{kid}_{len(bersih) + 1}'
        id_ada.add(kid)
        # Tinggi mengikuti nama (kotak 2 baris = 110), supaya teks
        # tidak terpotong sesudah kotak digeser atau diubah tulisannya;
        # tinggi yang dikirim editor tidak boleh lebih pendek dari itu.
        try:
            h_kirim = int(k.get('h') or 90)
        except (TypeError, ValueError):
            h_kirim = 90
        h = h_kirim if jenis == 'desain' else max(
            h_kirim, tinggi_kotak(nama, LEBAR_KOTAK))
        bersih.append({'id': kid, 'nama': nama, 'kode': kid,
                       'peran': peran, 'x': x, 'y': y,
                       'w': LEBAR_KOTAK, 'h': h})
    if not bersih:
        return None, ['Belum ada kotak di gambar.']
    if jenis == 'model':
        peran_ada = {b['peran'] for b in bersih}
        if 'X' not in peran_ada:
            masalah.append('Belum ada kotak bebas (X).')
        if 'Y' not in peran_ada:
            masalah.append('Belum ada kotak hasil (Y).')
    panah_bersih: list[dict] = []
    for p in (panah or []):
        if not isinstance(p, dict):
            continue
        dari = str(p.get('dari') or '')
        ke = str(p.get('ke') or '')
        if dari not in id_ada or ke not in id_ada or dari == ke:
            continue
        panah_bersih.append({'dari': dari, 'ke': ke,
                             'label': _rapi(p.get('label')),
                             'gaya': p.get('gaya') if p.get('gaya') in (
                                 'putus', 'lewat') else 'lurus'})
    if masalah:
        return None, masalah
    lebar_manual = max(
        KANVAS_LEBAR,
        max((b['x'] + b['w'] for b in bersih), default=0) + 60)
    return {'kotak': bersih, 'panah': panah_bersih,
            'bentuk': 'manual', 'lebar': lebar_manual}, []


def langkah_alur(desain: str) -> list[str]:
    """Langkah alur penelitian untuk satu desain (deterministik)."""
    return list(LANGKAH_DESAIN.get(str(desain or '').strip().lower(),
                                   LANGKAH_DESAIN['survei']))


def teks_desain_31(jenis: str, desain: str) -> list[str]:
    """Teks 3.1 dari template deterministik (bukan AI).

    Hanya fakta standar: jenis, desain, langkah. Gratis, bagian dari
    1 token gambar Desain. Hanya ditambahkan bila 3.1 masih kosong.
    """
    j = LABEL_JENIS.get(str(jenis or '').strip().lower(), 'kuantitatif')
    d = LABEL_DESAIN.get(str(desain or '').strip().lower(), 'survei')
    langkah = langkah_alur(d)
    baris = [f'Penelitian ini memakai jenis {j} dengan desain {d}.']
    nomor = '; '.join(f'{i + 1}) {s}' for i, s in enumerate(langkah))
    baris.append('Langkah penelitiannya: ' + nomor + '.')
    return baris


def model_dari_peta_bab4(peta: dict) -> dict | None:
    """Ubah peta Bab IV (variabel + jalur) jadi data model diagram.

    Peta Bab IV sudah dibaca dari naskah (beserta bukti kalimatnya),
    jadi ini hanya alih bentuk, bukan baca ulang. Peran 'M' dibaca
    sama dengan 'Z' (perantara)."""
    if not isinstance(peta, dict) or not peta.get('variabel'):
        return None
    return {'variabel': [{'nama': v.get('nama', ''),
                          'peran': v.get('peran', 'X')}
                         for v in peta.get('variabel') or []],
            'jalur': [{'dari': j.get('dari', ''), 'ke': j.get('ke', ''),
                       'hipotesis': j.get('hipotesis', ''),
                       'jenis': j.get('jenis', 'langsung'), 'arah': ''}
                      for j in peta.get('jalur') or []],
            'jenis': peta.get('jenis') or '',
            'desain': ''}


# ── Periksa gambar yang sudah ada (poin 2 rencana) ────────────────────
def _baca_dokumen(path):
    """(doc, cocok, teks_par, nomor_par, lain) dari docx; None bila
    tak terbaca. nomor_par = nomor efektif tiap paragraf dari
    penomoran otomatis (numPr); '' untuk paragraf tanpa penomoran.
    Daftar paragraf yang sama dipakai untuk teks dan nomor supaya
    sejajar; `lain` = isi zip selain document.xml (untuk tulis ulang).
    """
    from .gambar import _penomoran_dari_zip, nomor_untuk_paragraf
    from .pustaka_periksa import _RE_P, _teks_par_xml
    path = Path(path)
    if not path.exists():
        return None
    try:
        with zipfile.ZipFile(path) as z:
            nama = z.namelist()
            doc = z.read('word/document.xml').decode('utf-8')
            penomoran = _penomoran_dari_zip(z)
            lain = {n: z.read(n) for n in nama
                    if n != 'word/document.xml'}
    except Exception:                                      # noqa: BLE001
        return None
    cocok = list(_RE_P.finditer(doc))
    teks_par = [_teks_par_xml(m.group(0)) for m in cocok]
    nomor_par = nomor_untuk_paragraf([m.group(0) for m in cocok],
                                     penomoran)
    return doc, cocok, teks_par, nomor_par, lain


def periksa_gambar(path, bagian: str, judul_harapan: str) -> dict:
    """Periksa gambar di satu bagian naskah.

    Mesin tidak bisa membaca isi gambar (piksel). Yang diperiksa:
    gambar ada atau tidak, dan keterangannya benar atau tidak.
    Vonis: 'sesuai' (ada + keterangan cocok, dibiarkan),
    'meragukan' (ada tapi keterangan salah/tidak ada),
    'tidak_ada' (belum ada gambar).
    """
    from .gambar import rentang_bagian
    baca = _baca_dokumen(path)
    if baca is None:
        path = Path(path)
        if not path.exists():
            return {'ada': False, 'keterangan': [], 'vonis': 'tidak_ada',
                    'sebab': 'berkas tidak ada'}
        return {'ada': False, 'keterangan': [], 'vonis': 'tidak_ada',
                'sebab': 'berkas tidak bisa dibaca'}
    _doc, cocok, teks_par, nomor_par, _lain = baca
    awal, akhir = rentang_bagian(
        [m.group(0) for m in cocok], teks_par, nomor_par, bagian)
    if awal is None:
        return {'ada': False, 'keterangan': [], 'vonis': 'tidak_ada',
                'sebab': f'Bagian {bagian} tidak ditemukan di naskah.'}
    keterangan: list[str] = []
    ada_gambar = False
    pola_cap = re.compile(r'^\s*Gambar\s+\d+\.\s*\d+\b.*', re.IGNORECASE)
    for i in range(awal, akhir):
        xml = cocok[i].group(0)
        if '<w:drawing' in xml:
            ada_gambar = True
        if pola_cap.match(teks_par[i] or ''):
            keterangan.append(' '.join(teks_par[i].split()))
    if not ada_gambar:
        return {'ada': False, 'keterangan': keterangan,
                'vonis': 'tidak_ada', 'sebab': ''}
    harapan = _normalisasi_nama(judul_harapan)
    cocok_cap = any(harapan in _normalisasi_nama(k)
                    for k in keterangan)
    if cocok_cap:
        return {'ada': True, 'keterangan': keterangan,
                'vonis': 'sesuai', 'sebab': ''}
    return {'ada': True, 'keterangan': keterangan,
            'vonis': 'meragukan',
            'sebab': 'Gambar sudah ada, tapi keterangannya tidak cocok.'}


def buang_gambar_bagian(path, bagian: str, judul_harapan: str) -> dict:
    """Buang gambar + keterangan lama di satu bagian (untuk Perbarui).

    Hanya dipakai saat mahasiswa menekan Perbarui lalu Selesai (bukan
    diam-diam): gambar lama diganti gambar baru atas perintahnya.
    Yang dibuang: pasangan gambar + keterangan yang judulnya cocok;
    bila bagian ini hanya punya SATU gambar, gambar itu beserta
    keterangannya (gambar milik bagian ini apa pun keterangannya,
    supaya tidak ada duplikat; gambar milik mahasiswa yang
    keterangannya "Desain Penelitian" ikut terbuang saat diganti
    gambar "Alur Penelitian"). Baris "Sumber:" yang langsung mengikut
    keterangan gambar yang dibuang ikut dibuang (baris itu milik
    gambar lama; bila dibiarkan, ia duduk di atas gambar baru sebagai
    baris yatim). Berkas media lama dibiarkan di dalam zip (tidak
    terpakai, tidak merusak dokumen).
    """
    from .gambar import rentang_bagian
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'dibuang': 0, 'sebab': 'berkas tidak ada'}
    baca = _baca_dokumen(path)
    if baca is None:
        return {'ok': False, 'dibuang': 0,
                'sebab': 'berkas tidak bisa dibaca'}
    doc, cocok, teks_par, nomor_par, lain = baca
    awal, akhir = rentang_bagian(
        [m.group(0) for m in cocok], teks_par, nomor_par, bagian)
    if awal is None:
        return {'ok': False, 'dibuang': 0,
                'sebab': f'Bagian {bagian} tidak ditemukan di naskah.'}
    harapan = _normalisasi_nama(judul_harapan)
    pola_cap = re.compile(r'^\s*Gambar\s+\d+\.\s*\d+\b.*', re.IGNORECASE)
    # Pasangan gambar + keterangan sesudahnya di bagian ini.
    pasangan: list[tuple] = []
    for i in range(awal, akhir):
        if '<w:drawing' not in cocok[i].group(0):
            continue
        ket = None
        for j in range(i + 1, akhir):
            if '<w:drawing' in cocok[j].group(0):
                break
            if pola_cap.match(teks_par[j] or ''):
                ket = j
                break
        pasangan.append((i, ket))
    buang: set[int] = set()
    pola_sumber = re.compile(r'^\s*Sumber\s*:', re.IGNORECASE)
    for g, ket in pasangan:
        cocok_judul = ket is not None and \
            harapan in _normalisasi_nama(teks_par[ket])
        if cocok_judul or len(pasangan) == 1:
            buang.add(g)
            if ket is not None:
                buang.add(ket)
                # Baris Sumber tepat sesudah keterangan milik gambar
                # ini (hanya baris itu; Sumber lain tidak disentuh).
                if ket + 1 < akhir and pola_sumber.match(
                        teks_par[ket + 1] or ''):
                    buang.add(ket + 1)
    if not buang:
        return {'ok': True, 'dibuang': 0, 'sebab': ''}
    ganti = []
    for i in sorted(buang, reverse=True):
        ganti.append((cocok[i].start(), cocok[i].end(), ''))
    doc_baru = doc
    for a, b, isi in ganti:
        doc_baru = doc_baru[:a] + isi + doc_baru[b:]
    try:
        import shutil
        tmp = path.with_suffix('.tmp.docx')
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('word/document.xml', doc_baru)
            for n, isi_b in lain.items():
                if n == 'word/document.xml':
                    continue
                z.writestr(n, isi_b)
        shutil.move(str(tmp), str(path))
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'dibuang': 0,
                'sebab': f'gagal menulis berkas: {e}'}
    return {'ok': True, 'dibuang': len(buang), 'sebab': ''}


def bagian_punya_isi(path, bagian: str) -> bool:
    """True bila bagian ini sudah punya paragraf isi (bukan judul saja)."""
    from .gambar import rentang_bagian
    baca = _baca_dokumen(path)
    if baca is None:
        return False
    _doc, cocok, teks_par, nomor_par, _lain = baca
    awal, akhir = rentang_bagian(
        [m.group(0) for m in cocok], teks_par, nomor_par, bagian)
    if awal is None:
        return False
    for i in range(awal + 1, akhir):
        if teks_par[i].strip():
            return True
    return False


def sisip_teks_setelah_judul(path, bagian: str, baris: list[str]) -> dict:
    """Sisipkan paragraf teks tepat sesudah judul bagian."""
    from .gambar import rentang_bagian
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'sebab': 'berkas tidak ada'}
    if not baris:
        return {'ok': True, 'ditambah': 0}
    baca = _baca_dokumen(path)
    if baca is None:
        return {'ok': False, 'sebab': 'berkas tidak bisa dibaca'}
    doc, cocok, teks_par, nomor_par, lain = baca
    awal, _akhir = rentang_bagian(
        [m.group(0) for m in cocok], teks_par, nomor_par, bagian)
    if awal is None:
        return {'ok': False,
                'sebab': f'Bagian {bagian} tidak ditemukan di naskah.'}
    from . import bagian_awal as BA
    baru = ''.join(BA._xml_paragraf(str(b), '') for b in baris)
    akhir_judul = cocok[awal].end()
    doc_baru = doc[:akhir_judul] + baru + doc[akhir_judul:]
    try:
        import shutil
        tmp = path.with_suffix('.tmp.docx')
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('word/document.xml', doc_baru)
            for n, isi_b in lain.items():
                if n == 'word/document.xml':
                    continue
                z.writestr(n, isi_b)
        shutil.move(str(tmp), str(path))
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'sebab': f'gagal menulis berkas: {e}'}
    return {'ok': True, 'ditambah': len(baris)}


def _nomor_gambar(judul: str) -> tuple | None:
    """(bab, nomor) dari 'Gambar 2.1 ...' (terima 'Gambar 2. 1')."""
    m = re.search(r'Gambar\s+(\d+)\s*\.\s*(\d+)', str(judul or ''),
                  re.IGNORECASE)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


def _urutkan_entri_gambar(entri: list[dict]) -> list[dict]:
    """Urutkan entri Daftar Gambar menurut nomor gambar (2.1, 2.2, 3.1).

    Urutan dokumen biasanya sudah bernomor, tapi entri baru yang
    disisipkan belakangan harus terselip pada tempatnya, bukan di
    akhir daftar. Entri tanpa nomor tetap di akhir, urutan dokumen.
    """
    return sorted(entri, key=lambda e: _nomor_gambar(e.get('judul') or '')
                  or (10 ** 9, 10 ** 9))


def segarkan_daftar_gambar(path) -> dict:
    """Tulis ulang entri Daftar Gambar dari keterangan di naskah.

    Daftar Gambar adalah daftar turunan dari keterangan ("Gambar X.Y
    ..."): entri baru langsung masuk tanpa diketik. Nomor halaman
    diisi belakangan oleh perbarui_nomor_daftar (pekerja latar).
    Bila naskah belum punya bagian Daftar Gambar, gagal jujur:
    Perbarui Bagian Awal berikutnya yang membuatnya.
    """
    from . import bagian_awal as BA
    from .pustaka_periksa import _RE_P, _teks_par_xml
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'jumlah': 0, 'sebab': 'berkas tidak ada'}
    try:
        with zipfile.ZipFile(path) as z:
            nama = z.namelist()
            doc = z.read('word/document.xml').decode('utf-8')
            lain = {n: z.read(n) for n in nama if n != 'word/document.xml'}
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'jumlah': 0,
                'sebab': f'berkas tidak bisa dibaca: {e}'}
    cocok = list(_RE_P.finditer(doc))
    teks_par = [_teks_par_xml(m.group(0)) for m in cocok]
    baca = BA.baca_bagian_awal(teks_par)
    indeks = (baca.get('indeks', {}) or {}).get('daftar_gambar', []) or []
    if not indeks:
        return {'ok': False, 'jumlah': 0,
                'sebab': 'Daftar Gambar belum ada di naskah.'}
    entri = BA.entri_daftar_keterangan(
        # Hanya keterangan di BADAN, bukan dari daftar lama itu
        # sendiri: entri daftar lama (dengan nomor halaman menempel)
        # tidak terdedup dengan keterangan badan, sehingga daftar
        # jadi ganda dan entri baru menempel di akhir, di luar urutan
        # (cacat kosmetik 18 Nov 2026: Gambar 2.2 di akhir daftar).
        [teks_par[i] for i in range(len(teks_par))
         if i not in set(indeks)],
        gaya=[BA._gaya_dari_xml(cocok[i].group(0))
              for i in range(len(teks_par)) if i not in set(indeks)]
        ).get('daftar_gambar', [])
    entri = _urutkan_entri_gambar(entri)
    judul_entri = [e['judul'] for e in entri]
    # Paragraf entri lama: indeks[1:] (indeks[0] = judul seksi).
    lama = indeks[1:]
    if not lama:
        return {'ok': False, 'jumlah': 0,
                'sebab': 'Daftar Gambar belum ada di naskah.'}
    ppr = BA._ppr_dari_xml(cocok[lama[0]].group(0))
    baru_xml = [BA._xml_paragraf(j, ppr) for j in judul_entri]
    a = cocok[lama[0]].start()
    b = cocok[lama[-1]].end()
    doc_baru = doc[:a] + ''.join(baru_xml) + doc[b:]
    try:
        import shutil
        tmp = path.with_suffix('.tmp.docx')
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('word/document.xml', doc_baru)
            for n, isi_b in lain.items():
                if n == 'word/document.xml':
                    continue
                z.writestr(n, isi_b)
        shutil.move(str(tmp), str(path))
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'jumlah': 0,
                'sebab': f'gagal menulis berkas: {e}'}
    return {'ok': True, 'jumlah': len(judul_entri), 'sebab': ''}


# ── Penyimpanan (pola Bagian Awal: Setelan JSON) ─────────────────────
def simpan_model(db, fid: int, model: dict) -> None:
    from . import bagian_awal as BA
    BA.simpan_json(db, f'diagram_model_{int(fid)}', model,
                   oleh='diagram')


def muat_model(db, fid: int) -> dict | None:
    from . import bagian_awal as BA
    return BA.muat_json(db, f'diagram_model_{int(fid)}')


def simpan_hasil(db, fid: int, hasil: dict) -> None:
    from . import bagian_awal as BA
    BA.simpan_json(db, f'diagram_hasil_{int(fid)}', hasil, oleh='diagram')


def muat_hasil(db, fid: int) -> dict | None:
    from . import bagian_awal as BA
    return BA.muat_json(db, f'diagram_hasil_{int(fid)}')
