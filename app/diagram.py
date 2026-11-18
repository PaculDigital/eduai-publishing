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

# Peran sah: X bebas, M perantara (mediasi), Z penguat (moderasi),
# Y hasil. Istilah lazim (koreksi Boss 18 Nov 16:12 WIB): M untuk
# Mediasi, Z untuk Moderasi. Peta Bab IV sudah memakai M/Z ini.
PERAN_SAH = ('X', 'M', 'Z', 'Y')
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
# Garis tengah horizontal kanvas: pusat X dan Y selalu di sini,
# tumpukan X dan Y simetris terhadap garis ini (template default
# Boss 18 Nov 12:12 WIB); perantara M di atas garis ini,
# bukan di garisnya; penguat Z duduk di kolom X (tahap 0).
TENGAH_KANVAS = KANVAS_TINGGI // 2
# Jarak pusat X terluar ke garis tengah (2-4 X) / setengah
# bentang kolom X. 250 px; juga dipakai sebagai tinggi atap
# segitiga mediasi (pusat kolom perantara = garis - 250 px).
LANGKAH_X = 250
# Celah minimum antara bawah kolom perantara dan garis langsung
# X ke Y tertinggi yang lewat di kolom itu (px): supaya panah
# langsung lurus dan tidak terhalang perantara.
CELAH_PERANTARA = 40
LEBAR_KOTAK = 300
# Tinggi oval model (contoh skripsi Boss 18 Nov 2026): oval contoh
# besar dan bulat alami (rasio lebar:tinggi 1,2-1,8, teks di tengah
# dengan ruang lega), bukan pipih 300x90. Lebar 300, tinggi 180
# (nama 1 baris, rasio 1,67) / 216 (nama 2 baris, rasio 1,39).
# Boss 18 Nov 11:43 minta dikecilkan sedikit dari v3 (320x200/240):
# 180 = 200 kurang 10 persen, 216 = 240 kurang 10 persen (215 Boss
# dibulatkan ke 216 supaya tinggi genap dan pusat oval tepat di
# garis tengah).
TINGGI_OVAL_1 = 180
TINGGI_OVAL_2 = 216
# Kotak indikator gaya SmartPLS (Boss 18 Nov 16:24 WIB): kotak kecil
# di samping oval variabelnya, ada panah dari variabel ke tiap
# indikator; indikator di kiri untuk X/M/Z, di kanan untuk Y.
# Nama indikator SELALU dua baris (Boss 18 Nov 16:26 WIB) supaya
# kotaknya ramping dan seragam: kotak sempit (lebar 180) dan selalu
# setinggi 2 baris (56 px), nama panjang dibungkus jadi 2 baris yang
# seimbang, nama pendek tetap 1 baris di tengah kotak. Jarak mendatar
# oval ke kolom indikator 40 px, jarak tegak antar kotak 8 px.
LEBAR_IND = 180
TINGGI_IND = 56
CELAH_IND = 40
JARAK_IND = 8
# Maks indikator per variabel (sama seperti Bab IV).
BATAS_IND = 20


def _rapi(teks) -> str:
    return ' '.join(str(teks or '').split()).strip()


def _bersihkan_indikator(masuk) -> list:
    """Daftar indikator yang bersih: teks dirapikan, kosong dibuang,
    ganda dibuang (urutan dipertahankan), dibatasi BATAS_IND
    (seperti Bab IV). Boleh kosong, tidak menghalangi."""
    keluar: list[str] = []
    if not isinstance(masuk, (list, tuple)):
        return keluar
    for t in masuk:
        s = _rapi(t)
        if s and s not in keluar:
            keluar.append(s)
    return keluar[:BATAS_IND]


def _normalisasi_nama(nama: str) -> str:
    return re.sub(r'\s+', ' ', str(nama or '').strip()).lower()


def _mediator_lama(variabel_masuk, jalur_masuk) -> set:
    """Nama (ternormalisasi) variabel peran 'Z' yang sebenarnya
    perantara lama (sebelum istilah M/Z Boss 18 Nov 16:12 WIB).

    Z lama muncul sebagai Lewat, atau punya jalur masuk DAN keluar.
    Z penguat (baru) hanya punya jalur 'interaksi' keluar ke Y,
    tanpa jalur masuk, jadi tidak ikut. Referensi jalur bisa berupa
    nama atau kode: kode sementara dihitung dari peran masukan
    (X1.., Z/Z1.., M/M1.., Y), dan kode yang dikirim ikut dikenali.
    Dipakai normalisasi_model dan model_tampilan supaya model
    tersimpan lama (mis. Asih fid 81: Orientasi Kewirausahaan
    peran Z, H6 lewat Z) tetap terbaca sebagai perantara M tanpa
    mengubah berkas tersimpan itu.
    """
    if not variabel_masuk or not jalur_masuk:
        return set()
    jml = {}
    for v in variabel_masuk:
        if not isinstance(v, dict):
            continue
        p = str(v.get('peran') or '').strip().upper()
        jml[p] = jml.get(p, 0) + 1
    kenali = {}
    hitung = {}
    for v in variabel_masuk:
        if not isinstance(v, dict):
            continue
        nama = _normalisasi_nama(v.get('nama'))
        if not nama:
            continue
        kenali.setdefault(nama, v)
        kode_kirim = _rapi(v.get('kode'))
        if kode_kirim:
            kenali.setdefault(kode_kirim.lower(), v)
        peran = str(v.get('peran') or '').strip().upper()
        if peran not in ('X', 'Z', 'M', 'Y'):
            continue
        hitung[peran] = hitung.get(peran, 0) + 1
        n = hitung[peran]
        if peran == 'X':
            kenali.setdefault(f'x{n}', v)
        elif peran == 'Y':
            kenali.setdefault('y', v)
        elif jml.get(peran, 0) > 1:
            kenali.setdefault(f'{peran.lower()}{n}', v)
        else:
            kenali.setdefault(peran.lower(), v)
    masuk = set()
    keluar = set()
    for j in jalur_masuk or []:
        if not isinstance(j, dict):
            continue
        dari = kenali.get(_normalisasi_nama(j.get('dari')))
        ke = kenali.get(_normalisasi_nama(j.get('ke')))
        lewat = kenali.get(_normalisasi_nama(j.get('lewat')))
        if dari is not None:
            keluar.add(id(dari))
        if ke is not None:
            masuk.add(id(ke))
        if lewat is not None:
            masuk.add(id(lewat))
            keluar.add(id(lewat))
    lama = set()
    for v in variabel_masuk:
        if not isinstance(v, dict):
            continue
        if str(v.get('peran') or '').strip().upper() != 'Z':
            continue
        if id(v) in masuk and id(v) in keluar:
            lama.add(_normalisasi_nama(v.get('nama')))
    return lama


def normalisasi_model(data) -> tuple:
    """Periksa + rapikan data model. Kembalikan (model, masalah).

    Model: {'variabel': [{'nama', 'peran', 'kode'}],
            'jalur': [{'dari', 'ke', 'hipotesis', 'jenis', 'arah'}],
            'jenis': ..., 'desain': ...}.
    Istilah lazim (Boss 18 Nov 16:12 WIB): M perantara (mediasi),
    Z penguat (moderasi). Peran 'Z' lama (perantara, sebelum
    istilah ini) yang muncul sebagai Lewat atau punya jalur masuk
    DAN keluar dibaca jadi 'M' (migrasi di kode, berkas tersimpan
    tidak diubah). Jalur dari Z (penguat) otomatis 'interaksi' dan
    harus ke Y; Z tidak memakai Lewat. Kode: X1, X2, ...; M bila
    satu perantara, M1/M2/... bila lebih dari satu; Z bila satu
    penguat, Z1/Z2/... bila lebih dari satu; Y. Lebih dari 1 M/Z
    diizinkan (Boss 18 Nov 15:47 WIB) supaya mediasi + moderasi
    bisa digambar bersama. Kolom 'Jenis jalur' di formulir
    (Boss 18 Nov 16:12 WIB) dibaca dan divalidasi: 'langsung'
    maka Lewat kosong, 'tidak_langsung' maka Lewat harus M,
    'interaksi' maka Dari harus Z, Ke harus Y, Lewat kosong; bila
    jenis tidak dikirim, disimpulkan seperti dulu (cocok mundur:
    ada Lewat jadi tidak_langsung, Dari Z jadi interaksi, sisanya
    langsung). Referensi jalur boleh memakai kode lama ('Z' untuk
    perantara lama) atau nama; keduanya dikenali.
    Masalah berbahasa Indonesia polos; kosong berarti model sah.
    """
    masalah: list[str] = []
    if not isinstance(data, dict):
        return None, ['Data model tidak terbaca.']
    variabel_masuk = data.get('variabel') or []
    jalur_masuk = data.get('jalur') or []
    lama = _mediator_lama(variabel_masuk, jalur_masuk)
    variabel: list[dict] = []
    lihat: dict[str, str] = {}
    kode_lama: dict[str, str] = {}
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
        if peran == 'Z' and _normalisasi_nama(nama) in lama:
            peran = 'M'
        kunci = _normalisasi_nama(nama)
        if kunci in lihat and lihat[kunci] != peran:
            masalah.append(f'"{nama}" muncul dengan dua peran berbeda.')
            continue
        if kunci in lihat:
            continue
        lihat[kunci] = peran
        variabel.append({'nama': nama, 'peran': peran,
                         'indikator': _bersihkan_indikator(
                             v.get('indikator'))})
        kode_kirim = _rapi(v.get('kode'))
        if kode_kirim:
            kode_lama.setdefault(kode_kirim.lower(), kunci)
    peran_ada = {v['peran'] for v in variabel}
    if 'X' not in peran_ada:
        masalah.append('Belum ada variabel bebas (X).')
    if 'Y' not in peran_ada:
        masalah.append('Belum ada variabel hasil (Y).')
    if sum(1 for v in variabel if v['peran'] == 'Y') > 1:
        masalah.append('Variabel hasil (Y) hanya boleh satu.')
    # Kode lama (sebelum migrasi, untuk referensi jalur yang memakai
    # kode lama): X1, X2, ...; Z bila satu, Z1/Z2/... bila lebih
    # dari satu, dihitung dari peran masukan (M lama dan Z sama-sama
    # berkode Z); Y. Dipetakan ke nama supaya sesudah migrasi
    # referensi 'Z' tetap menunjuk perantara lama (kini M). Hanya
    # variabel yang diterima yang dihitung (nama ganda dilewat).
    peran_lama = {}
    for v in variabel_masuk:
        if not isinstance(v, dict):
            continue
        nama = _normalisasi_nama(v.get('nama'))
        if not nama or nama not in lihat or nama in peran_lama:
            continue
        peran_lama[nama] = str(v.get('peran') or '').strip().upper()
    jml_lama = {'X': 0, 'Z': 0}
    for p in peran_lama.values():
        if p == 'X':
            jml_lama['X'] += 1
        elif p in ('Z', 'M'):
            jml_lama['Z'] += 1
    hitung_lama = {'X': 0, 'Z': 0}
    for v in variabel:
        p = peran_lama.get(_normalisasi_nama(v['nama']), '')
        if p == 'X':
            hitung_lama['X'] += 1
            kode_lama.setdefault(f"x{hitung_lama['X']}",
                                 _normalisasi_nama(v['nama']))
        elif p in ('Z', 'M'):
            hitung_lama['Z'] += 1
            n = hitung_lama['Z']
            kode_lama.setdefault('z' if jml_lama['Z'] <= 1 else f'z{n}',
                                 _normalisasi_nama(v['nama']))
        elif p == 'Y':
            kode_lama.setdefault('y', _normalisasi_nama(v['nama']))
    # Kode baru (istilah M/Z): X1, X2, ...; M bila satu perantara,
    # M1/M2/... bila lebih dari satu (mediasi paralel, seperti
    # M1/M2 di Bab IV); Z bila satu penguat, Z1/Z2/... bila lebih
    # dari satu; Y.
    jml_m = sum(1 for v in variabel if v['peran'] == 'M')
    jml_z = sum(1 for v in variabel if v['peran'] == 'Z')
    hitung = {'X': 0, 'M': 0, 'Z': 0}
    for v in variabel:
        if v['peran'] == 'X':
            hitung['X'] += 1
            v['kode'] = f"X{hitung['X']}"
        elif v['peran'] == 'M':
            hitung['M'] += 1
            v['kode'] = f"M{hitung['M']}" if jml_m > 1 else 'M'
        elif v['peran'] == 'Z':
            hitung['Z'] += 1
            v['kode'] = f"Z{hitung['Z']}" if jml_z > 1 else 'Z'
        else:
            v['kode'] = 'Y'
    nama_ke_kode = {_normalisasi_nama(v['nama']): v['kode']
                    for v in variabel}
    kode_ke_kode = {v['kode'].lower(): v['kode'] for v in variabel}
    for k_lama, nama in kode_lama.items():
        if k_lama not in kode_ke_kode and nama in nama_ke_kode:
            kode_ke_kode[k_lama] = nama_ke_kode[nama]

    def _cari_kode(teks: str):
        """Cari kode variabel dari nama atau kode apa adanya.

        Formulir mengirim kode (X1, X2, M, Z, Y), naskah/peta
        mengirim nama; keduanya harus dikenali. Nama didahulukan
        supaya nama "X2" tetap menunjuk variabel bernama X2, bukan
        kode X2. Kode lama ('Z' untuk perantara lama, kini M) ikut
        dikenali lewat alias di kode_ke_kode.
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
        jenis_masuk = str(j.get('jenis') or '').strip().lower()
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
            if peran_lewat != 'M':
                masalah.append('Lewat harus perantara (M).')
                continue
        peran_dari = next((v['peran'] for v in variabel
                           if v['kode'] == kode_dari), '')
        if peran_dari == 'Z' and lewat:
            masalah.append('Penguat (Z) tidak memakai Lewat.')
            continue
        # Jenis jalur: bila dikirim eksplisit (kolom Jenis di
        # formulir), divalidasi; bila tidak dikirim, disimpulkan
        # seperti dulu (cocok mundur).
        if jenis_masuk in ('langsung', 'tidak_langsung', 'interaksi'):
            if jenis_masuk == 'langsung':
                if lewat:
                    masalah.append('Jalur langsung tidak memakai '
                                   'Lewat.')
                    continue
                jenis = 'langsung'
            elif jenis_masuk == 'tidak_langsung':
                if not lewat:
                    masalah.append('Jalur tidak langsung wajib lewat '
                                   'perantara (M).')
                    continue
                jenis = 'tidak_langsung'
            else:
                if peran_dari != 'Z':
                    masalah.append('Jalur interaksi (moderasi) harus '
                                   'dari penguat (Z).')
                    continue
                jenis = 'interaksi'
        elif lewat:
            jenis = 'tidak_langsung'
        elif peran_dari == 'Z':
            jenis = 'interaksi'
        else:
            jenis = 'langsung'
        if not label:
            masalah.append('Ada jalur yang belum berlabel hipotesis.')
            continue
        if label in label_pakai:
            masalah.append(f'Label {label} dipakai dua jalur.')
            continue
        label_pakai.add(label)
        if jenis == 'interaksi':
            peran_ke = next((v['peran'] for v in variabel
                             if v['kode'] == kode_ke), '')
            if peran_ke != 'Y':
                masalah.append('Jalur interaksi harus ke variabel '
                               'hasil (Y).')
                continue
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
    lama = _mediator_lama(data.get('variabel') or [],
                          data.get('jalur') or [])
    mentah: list[tuple] = []
    for v in data.get('variabel') or []:
        if not isinstance(v, dict):
            continue
        nama = _rapi(v.get('nama'))
        peran = str(v.get('peran') or 'X').strip().upper()
        if peran not in PERAN_SAH:
            peran = 'X'
        if peran == 'Z' and _normalisasi_nama(nama) in lama:
            peran = 'M'
        if not nama:
            continue
        mentah.append((nama, peran,
                       _bersihkan_indikator(v.get('indikator'))))
    jml_m = sum(1 for _, p, _ in mentah if p == 'M')
    jml_z = sum(1 for _, p, _ in mentah if p == 'Z')
    variabel: list[dict] = []
    hitung = {'X': 0, 'M': 0, 'Z': 0}
    for nama, peran, ind in mentah:
        if peran == 'X':
            hitung['X'] += 1
            kode = f"X{hitung['X']}"
        elif peran == 'M':
            hitung['M'] += 1
            kode = f"M{hitung['M']}" if jml_m > 1 else 'M'
        elif peran == 'Z':
            hitung['Z'] += 1
            kode = f"Z{hitung['Z']}" if jml_z > 1 else 'Z'
        else:
            kode = 'Y'
        variabel.append({'nama': nama, 'peran': peran, 'kode': kode,
                         'indikator': ind})
    kunci: dict[str, str] = {}
    for v in variabel:
        kunci[_normalisasi_nama(v['nama'])] = v['kode']
        kunci[v['kode'].lower()] = v['kode']
    # Alias kode lama ('Z' untuk perantara lama, kini M) + kode yang
    # dikirim, supaya referensi jalur lama tetap menunjuk variabel
    # yang sama saat validasi gagal dan formulir ditampilkan lagi.
    _peran_lama: dict[str, str] = {}
    _kode_kirim: dict[str, str] = {}
    for v in data.get('variabel') or []:
        if not isinstance(v, dict):
            continue
        _nm = _normalisasi_nama(v.get('nama'))
        if not _nm or _nm in _peran_lama:
            continue
        _peran_lama[_nm] = str(v.get('peran') or '').strip().upper()
        _kk = _rapi(v.get('kode')).lower()
        if _kk:
            _kode_kirim[_nm] = _kk
    _jml_lama = {'X': 0, 'Z': 0}
    for _p in _peran_lama.values():
        if _p == 'X':
            _jml_lama['X'] += 1
        elif _p in ('Z', 'M'):
            _jml_lama['Z'] += 1
    _hitung_lama = {'X': 0, 'Z': 0}
    for v in variabel:
        _nm = _normalisasi_nama(v['nama'])
        _p = _peran_lama.get(_nm, '')
        _kl = ''
        if _p == 'X':
            _hitung_lama['X'] += 1
            _kl = f"x{_hitung_lama['X']}"
        elif _p in ('Z', 'M'):
            _hitung_lama['Z'] += 1
            _n = _hitung_lama['Z']
            _kl = 'z' if _jml_lama['Z'] <= 1 else f'z{_n}'
        elif _p == 'Y':
            _kl = 'y'
        if _kl and _kl not in kunci:
            kunci[_kl] = v['kode']
        _kk = _kode_kirim.get(_nm, '')
        if _kk and _kk not in kunci:
            kunci[_kk] = v['kode']

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
    """'campuran' bila ada M dan Z, 'moderasi' bila ada Z tanpa M,
    'mediasi' bila ada M tanpa Z, 'banyak_x' bila X lebih dari
    satu, sisanya 'langsung'."""
    peran = [v['peran'] for v in model.get('variabel') or []]
    if 'M' in peran and 'Z' in peran:
        return 'campuran'
    if 'Z' in peran:
        return 'moderasi'
    if 'M' in peran:
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
    """Tinggi kotak langkah Desain (persegi, lebar 600): 1 baris = 90,
    2 baris = 110. Kotak model memakai tinggi_oval (oval besar).
    Aturan bungkus sama dengan editor (maks 18 karakter per baris
    untuk lebar 320, 30 untuk lebar 600).
    """
    return 110 if _jumlah_baris_nama(nama, lebar) >= 2 else 90


def tinggi_oval(nama: str, lebar: int = LEBAR_KOTAK) -> int:
    """Tinggi oval model: 180 (nama 1 baris) / 216 (nama 2 baris).

    Oval contoh besar dan bulat alami (rasio 1,2-1,8); oval mesin
    lama 300x90 pipih (rasio 3,33) dengan teks menempel tepi.
    Lebar 300 dengan tinggi ini memberi rasio 1,67 / 1,39 dan
    ruang teks lega (teks dipusatkan di dalam oval, lihat
    _teks_kotak di app/gambar.py).
    """
    return TINGGI_OVAL_2 if _jumlah_baris_nama(nama, lebar) >= 2 \
        else TINGGI_OVAL_1


def _tahap_variabel(variabel, jalur):
    """Tahap (kolom) tiap variabel dari graf jalur (longest-path).

    Tahap 0 bila tanpa jalur masuk, bila tidak 1 + maks tahap
    pendahulu. Jalur lewat diurai jadi dua sisi (Dari ke Lewat,
    Lewat ke Ke). Diulang sebanyak jumlah variabel supaya graf
    berputar (siklus) tetap berhenti dengan nilai deterministik.
    X/M/Y biasa kembali jadi X 0, M 1, Y 2; tanpa M jadi X 0, Y 1.
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


def _pusat_tumpukan(i, n, pusat_satu=400, tinggi_maks=216):
    """Pusat vertikal kotak ke-i dari n kotak yang simetris terhadap
    pusat_satu. 1 kotak di pusat_satu; 2-4 kotak berjarak sama
    dengan pusat terluar ±LANGKAH_X dari pusat_satu, direnggang
    bila perlu supaya oval (setinggi tinggi_maks) tidak tumpang
    tindih (jarak pusat paling sedikit tinggi_maks + 14 px)."""
    if n == 1:
        return pusat_satu
    langkah = max(2 * LANGKAH_X / (n - 1), tinggi_maks + 14)
    return pusat_satu + (i - (n - 1) / 2) * langkah


def _y_tumpukan_padat(nama_list, lebar=LEBAR_KOTAK, pusat=400,
                      batas=1560):
    """Daftar y untuk tumpukan padat (5+ kotak), terpusat simetris
    di garis tengah (pusat); celah 14 px, ditekan ke 6 px bila
    tumpukan lebih tinggi dari batas (kanvas lalu tumbuh, lihat
    tata_letak). Oval padat tetap setinggi oval biasa (180/216),
    bukan dirampingkan: oval kecil pipih adalah cacat yang
    diperbaiki putaran ini."""
    hs = [tinggi_oval(n, lebar) for n in nama_list]
    celah = 14
    total = sum(hs) + (len(hs) - 1) * celah
    if total > batas:
        celah = max(6, (batas - sum(hs)) // max(1, len(hs) - 1))
        total = sum(hs) + (len(hs) - 1) * celah
    # Tanpa jepit ke 20: tumpukan yang lebih tinggi dari kanvas
    # memang mulai di y negatif di sini, lalu digeser ke tengah
    # oleh tata_letak sesudah tinggi kanvas dihitung (menjepit
    # merusak simetri: pusat tumpukan bergeser dari garis tengah).
    y0 = pusat - total // 2
    out, yy = [], y0
    for h in hs:
        out.append(yy)
        yy += h + celah
    return out


def _indikator_dari_model(model: dict) -> dict:
    """{kode variabel: [teks indikator, ...]} dari model yang sudah
    dinormalisasi (kode = id kotak di tata draf)."""
    keluar: dict[str, list] = {}
    for v in (model or {}).get('variabel') or []:
        if not isinstance(v, dict):
            continue
        ind = _bersihkan_indikator(v.get('indikator'))
        if ind:
            keluar[str(v.get('kode') or v.get('nama') or '')] = ind
    return keluar


def posisi_indikator(induk: dict, i: int, n: int,
                     sisi: str = 'kiri') -> dict:
    """Kotak indikator ke-i dari n milik satu variabel (oval induk).

    Kotak ramping (lebar LEBAR_IND, tinggi TINGGI_IND = selalu
    setinggi 2 baris, Boss 18 Nov 16:26 WIB); tumpukan dipusatkan
    di tengah oval induk, celah JARAK_IND; kolom di kiri oval
    (jarak CELAH_IND) untuk X/M/Z, di kanan untuk Y (kolom
    terakhir). Kembalikan {'x', 'y', 'w', 'h'} (bilangan bulat)."""
    total = n * TINGGI_IND + (n - 1) * JARAK_IND
    atas = induk['y'] + induk['h'] / 2 - total / 2
    y = atas + i * (TINGGI_IND + JARAK_IND)
    if sisi == 'kanan':
        x = induk['x'] + induk['w'] + CELAH_IND
    else:
        x = induk['x'] - CELAH_IND - LEBAR_IND
    return {'x': round(x), 'y': round(y), 'w': LEBAR_IND,
            'h': TINGGI_IND}


def tambah_indikator(tata: dict, indikator: dict | None = None) -> dict:
    """Tambah kotak indikator ke tata (draf mesin / gambar akhir).

    `indikator` = {id kotak induk: [teks, ...]} (id = kode variabel
    di draf mesin, atau id kotak di tata manual editor). Tiap
    variabel yang punya indikator dapat satu kolom kotak kecil di
    samping ovalnya (kiri untuk X/M/Z, kanan untuk kolom terakhir
    = Y), dengan panah dari oval ke tiap kotak (lihat
    GB.panah_indikator). Kanvas melebar/meninggi seperlunya
    (memeluk isi); semua kotak digeser seperlunya supaya margin
    kiri 60 px dan atas 20 px tetap. Tanpa indikator, tata
    dikembalikan apa adanya (tidak ada perubahan, supaya skor dan
    uji lama tetap). Kembalikan tata yang sama (diubah di tempat),
    dengan 'indikator' = [{'id', 'induk', 'teks', 'sisi', 'x', 'y',
    'w', 'h'}].
    """
    if not tata or not indikator:
        return tata
    kotak = tata.get('kotak') or []
    if not kotak:
        return tata
    # Sisi: kolom terakhir (x terbesar) ke kanan, sisanya ke kiri.
    x_terakhir = max(k['x'] for k in kotak)
    daftar: list[dict] = []
    for k in kotak:
        teks_list = indikator.get(str(k.get('id') or '')) or []
        if not teks_list:
            continue
        sisi = 'kanan' if k['x'] == x_terakhir else 'kiri'
        n = len(teks_list)
        for i, teks in enumerate(teks_list):
            pos = posisi_indikator(k, i, n, sisi)
            daftar.append({'id': f"{k['id']}_i{i + 1}",
                           'induk': k['id'], 'teks': teks,
                           'sisi': sisi, **pos})
    if not daftar:
        return tata
    tata['indikator'] = daftar
    # Kanvas memeluk isi (termasuk kolom indikator): geser semua
    # kotak seperlunya supaya margin kiri 60 px dan atas 20 px
    # tetap, lalu lebar/tinggi mengikuti isi + margin.
    semua = list(kotak) + daftar
    min_x = min(b['x'] for b in semua)
    min_y = min(b['y'] for b in semua)
    geser_x = 60 - min_x if min_x < 60 else 0
    geser_y = 20 - min_y if min_y < 20 else 0
    if geser_x:
        for b in semua:
            b['x'] += geser_x
    if geser_y:
        for b in semua:
            b['y'] += geser_y
        if tata.get('tengah') is not None:
            tata['tengah'] = tata['tengah'] + geser_y
    # Kanvas hanya melebar/meninggi, tidak menyusut (lebar draf
    # minimal 1400, tinggi draf memeluk isi struktural).
    tata['lebar'] = max(tata.get('lebar') or 0,
                        max(b['x'] + b['w'] for b in semua) + 60)
    tata['tinggi'] = max(tata.get('tinggi') or 0,
                         max(b['y'] + b['h'] for b in semua) + 20)
    return tata


def tata_letak(model: dict, posisi_z: str | None = None) -> dict:
    """Tata letak deterministik: kotak + panah dalam kanvas 1400
    (dilebarkan bila kolom lebih dari 3); tinggi kanvas memeluk isi
    (mengikuti kotak teratas sampai terbawah + margin, tanpa ruang
    kosong besar di bawah diagram).

    Template default (Boss 18 Nov 12:12 WIB), menggantikan aturan
    18 Nov 10:09 (Z dan Y sejajar di garis tengah): posisi selalu
    variabel X berhadapan dengan variabel Y, defaultnya SEJAJAR
    (satu garis tengah yang sama), berapapun jumlah X dan Y;
    variabel lain seperti perantara M itu DI ATAS atau DI BAWAH garis X-Y
    itu, bukan di garisnya. Panah langsung diprioritaskan dulu
    (lurus, terpendek, jalurnya bersih); garis putus-putus mengalah,
    lewat perantara di atas/bawah, tidak pernah memotong jalur
    langsung. Posisi perantara TIDAK kaku (pilihan 1 Boss 18 Nov
    13:03 WIB): untuk mediasi 3 kolom (X|M|Y), mesin menghitung
    tiga kandidat (M di tengah garis seperti v4, M di atas garis
    seperti segitiga v5, M di bawah garis sebagai cerminnya),
    lengkap dengan panah dan labelnya, lalu memilih yang skornya
    terbaik (lihat skor_tata_letak di app/gambar.py: silangan
    paling sedikit, celah label paling lega, panjang panah
    seimbang, simetris, jarak ke kotak lega; seri memilih 'atas'
    dulu). Yang memutuskan adalah SKOR, bukan patokan jumlah X.
    Asih (1 X) menang di 'atas' (segitiga), Nura (2 X) menang di
    'tengah' (seperti v4). Rantai multi-kolom (Goal-Directed,
    contoh 5) tidak ikut pemilihan ini: perantaranya membentuk
    rantai utama, jadi kolomnya tetap simetris terhadap garis
    tengah seperti dulu.
    Tahap tiap variabel diturunkan dari graf jalur (longest-path):
    tanpa jalur masuk tahap 0, bila tidak 1 + maks tahap pendahulu;
    X/M/Y biasa kembali jadi 3 kolom (X 0, M 1, Y 2), tanpa M jadi
    2 kolom; model bertahap (mis. Goal-Directed) jadi N kolom.
    Kolom X dan Y simetris terhadap garis tengah (1 kotak di garis
    tengah, kecuali kolom X klasik 1 X di 'tengah' yang duduk di
    atas garis seperti v4; 2-4 kotak berjarak sama simetris; 5 kotak
    ke atas tumpukan terpusat simetris). Kolom perantara mediasi 3
    kolom ditempatkan menurut posisi_z yang dipilih skor ('tengah':
    di garis seperti v4; 'atas': di atas garis, pusat awal garis -
    250 px lalu dinaikkan sampai bawah kolom melewati garis langsung
    X ke Y tertinggi dengan celah 40 px; 'bawah': cermin 'atas').
    Jarak antar kolom 490 px (3 kolom ke bawah, sama seperti dulu:
    X 60, M 550, Y 1040) atau 440 px (4 kolom ke atas, kanvas
    dilebarkan supaya label panah muat di celah 120 px).
    Kotak model adalah oval besar (lebar 300, tinggi 180/216,
    rasio 1,67/1,39 seperti oval contoh); garis tengah (pusat X/Y)
    dicatat di 'tengah' karena kanvas yang memeluk isi tidak lagi
    berpusat di garis tengah.
    Panah langsung digambar LURUS seperti contoh 1 dan 3: titik
    tempel dipilih supaya garis lurus lewat di luar kotak
    perantara (di atas/bawah), bukan menembus lalu dibengkokkan
    (lihat _rute_lurus di app/gambar.py). Panah 'tidak_langsung'
    digambar putus-putus: dua segmen (Dari ke Lewat, Lewat ke Ke)
    bila ada Lewat, satu segmen (Dari ke Ke) bila tidak ada; label
    hipotesisnya muncul SATU kali saja (di segmen pertama, yang
    paling terbaca seperti label TL contoh 3), segmen kedua tanpa
    label, supaya tidak ada label yang sama dua kali.
    Kembalikan {'kotak', 'panah', 'bentuk', 'lebar', 'tinggi',
    'tengah', 'posisi_z'}; 'lebar' = lebar kanvas model ini (1400 bila 3 kolom
    ke bawah), 'tinggi' = tinggi kanvas model ini (memeluk isi),
    'tengah' = garis tengah (pusat X/Y) dalam koordinat akhir,
    'posisi_z' = posisi perantara yang dipakai ('tengah'/'atas'/
    'bawah') bila ada mediasi 3 kolom, bila tidak None.
    """
    variabel = model.get('variabel') or []
    tahap = _tahap_variabel(variabel, model.get('jalur') or [])
    kolom: dict[int, list] = {}
    for v in variabel:
        kolom.setdefault(tahap.get(v.get('kode') or v.get('nama'), 0),
                         []).append(v)
    n_kolom = (max(tahap.values()) + 1) if tahap else 1
    # Bila ada indikator, jarak antar kolom harus cukup untuk kotak
    # indikator (220 px di samping oval) supaya tidak menabrak kolom
    # sebelah (temuan pratinjau campuran 18 Nov 2026: kotak M_i1
    # menabrak oval X1 karena celah kolom 190 px < 220 px). Pitch
    # minimum = oval 300 + celah 40 + indikator 180 = 520 px.
    # Tanpa indikator pitch tetap seperti dulu (490/440), jadi skor
    # dan uji lama tidak berubah.
    ada_ind = any(isinstance(v, dict) and v.get('indikator')
                  for v in variabel)
    pitch_min = (LEBAR_KOTAK + CELAH_IND + LEBAR_IND) if ada_ind else 0
    if n_kolom <= 1:
        lebar_kanvas = KANVAS_LEBAR
        x_kolom = [550]
    elif n_kolom <= 3:
        pitch = max(980 / (n_kolom - 1), pitch_min)
        x_kolom = [60 + round(i * pitch) for i in range(n_kolom)]
        lebar_kanvas = max(KANVAS_LEBAR,
                           x_kolom[-1] + LEBAR_KOTAK + 60)
    else:
        pitch = max(440, pitch_min)
        lebar_kanvas = 420 + (n_kolom - 1) * pitch
        x_kolom = [60 + i * pitch for i in range(n_kolom)]
    # Template default (Boss 18 Nov 12:12 WIB): X berhadapan dengan Y
    # pada SATU garis tengah yang sama (tumpukan X dan Y simetris
    # terhadap garis itu, berapapun jumlahnya); perantara M TIDAK
    # di garis itu, melainkan DI ATAS atau DI BAWAH garis, supaya
    # panah langsung X ke Y lurus dan tidak terhalang perantara.
    # Penguat Z duduk di kolom X (tahap 0), jadi ikut garis tengah.
    garis = TENGAH_KANVAS
    # Kolom perantara mediasi 3 kolom: hanya bila 3 kolom, kolom
    # pertama hanya X/Z (penguat duduk di kolom X, tahap 0, entah
    # berkode Z atau Z2, jadi campuran mediasi + moderasi tetap
    # dapat segitiga/skor), kolom tengah hanya M, kolom terakhir
    # hanya Y. Rantai multi-kolom (Goal-Directed, contoh 5) TIDAK
    # memakai aturan ini: perantaranya membentuk rantai utama, jadi
    # kolomnya tetap simetris terhadap garis tengah seperti dulu.
    t_med = None
    if n_kolom == 3:
        peran_kolom = {t: {v.get('peran') for v in vs}
                       for t, vs in kolom.items()}
        kolom0 = peran_kolom.get(0) or set()
        if (kolom0 and kolom0 <= {'X', 'Z'} and 'X' in kolom0
                and peran_kolom.get(1) == {'M'}
                and peran_kolom.get(2) == {'Y'}):
            t_med = 1
    # Posisi perantara dipilih dari SKOR (pilihan 1 Boss 18 Nov
    # 13:03 WIB), bukan aturan kaku: bila posisi_z tidak disebut
    # dan ada mediasi 3 kolom, tiga kandidat dihitung lengkap lalu
    # yang skornya terbaik yang dipakai (seri: 'atas' dulu, urutan
    # evaluasi). Tanpa mediasi, posisi_z diabaikan.
    if t_med is not None and posisi_z is None:
        from .gambar import skor_tata_letak as _skor
        _terbaik = None
        for _pz in ('atas', 'tengah', 'bawah'):
            _t = tata_letak(model, posisi_z=_pz)
            _s = _skor(_t)
            if _terbaik is None or _s['banding'] < _terbaik[0]['banding']:
                _terbaik = (_s, _t)
        return _terbaik[1]

    def _pusat_kolom(vs, pusat):
        """Pusat vertikal tiap kotak di satu kolom, simetris
        terhadap pusat (pra-geser)."""
        n = len(vs)
        hs = [tinggi_oval(v['nama']) for v in vs]
        if n > 4:
            ys = _y_tumpukan_padat([v['nama'] for v in vs],
                                   pusat=pusat)
            return [y + h / 2 for y, h in zip(ys, hs)]
        return [_pusat_tumpukan(i, n, pusat, max(hs))
                for i in range(n)]

    def _pusat_untuk_kolom(t, vs):
        """Pusat acuan satu kolom (bukan perantara). Kolom X klasik
        1 X di 'tengah' duduk di atas garis (seperti v4, supaya X,
        Z, Y tidak segaris); di 'atas'/'bawah', 1 X di garis tengah
        (segitiga mediasi, v5). Kolom lain selalu di garis."""
        if (posisi_z == 'tengah' and t_med is not None
                and n_kolom <= 3 and t == 0 and len(vs) == 1
                and vs[0].get('peran') == 'X'):
            return garis - LANGKAH_X
        return garis

    def _pusat_mediasi(posisi):
        """Pusat vertikal kolom perantara mediasi 3 kolom.

        'tengah': di garis tengah seperti v4 (M sejajar Y, 1 X di
        atas garis); 'atas': di atas garis, pusat awal garis - 250
        px (atap segitiga mediasi), lalu dinaikkan sampai bawah
        kolom melewati garis langsung X ke Y tertinggi di kolom itu
        dengan celah CELAH_PERANTARA; 'bawah': cermin 'atas' (pusat
        awal garis + 250 px, diturunkan sampai atas kolom melewati
        garis langsung X ke Y terendah dengan celah yang sama). Bila
        tidak ada garis langsung X ke Y, pusatnya tetap pusat awal.
        """
        vs_med = kolom[t_med]
        hs_med = [tinggi_oval(v['nama']) for v in vs_med]
        if posisi == 'tengah':
            return _pusat_kolom(vs_med, garis)
        atas = posisi == 'atas'
        pusat_awal = garis - LANGKAH_X if atas else garis + LANGKAH_X
        pusat_xy = {}
        for t, vs in kolom.items():
            if t == t_med:
                continue
            for v, c in zip(vs, pusat_kolom[t]):
                pusat_xy[v.get('kode') or v.get('nama')] = (
                    x_kolom[t] + LEBAR_KOTAK / 2, c)
        peran_kode = {v.get('kode') or v.get('nama'): v.get('peran')
                      for v in variabel}
        x_med = x_kolom[t_med]
        y_ekstrem = None
        for j in model.get('jalur') or []:
            if str(j.get('jenis') or '').strip().lower() != 'langsung':
                continue
            dari, ke = j.get('dari'), j.get('ke')
            if (peran_kode.get(dari) != 'X'
                    or peran_kode.get(ke) != 'Y'):
                continue
            if dari not in pusat_xy or ke not in pusat_xy:
                continue
            (x1, y1), (x2, y2) = pusat_xy[dari], pusat_xy[ke]
            if x2 == x1:
                continue
            for x in (x_med, x_med + LEBAR_KOTAK):
                y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                y_ekstrem = (y if y_ekstrem is None else
                             (min(y_ekstrem, y) if atas
                              else max(y_ekstrem, y)))
        pusat_med = pusat_awal
        if y_ekstrem is not None:
            pusat_awal_list = _pusat_kolom(vs_med, pusat_awal)
            tepi_awal = (
                max(c + h / 2 for c, h in zip(pusat_awal_list, hs_med))
                if atas else
                min(c - h / 2 for c, h in zip(pusat_awal_list, hs_med)))
            batas = (y_ekstrem - CELAH_PERANTARA if atas
                     else y_ekstrem + CELAH_PERANTARA)
            if (tepi_awal > batas) if atas else (tepi_awal < batas):
                pusat_med = pusat_awal - (tepi_awal - batas)
        return _pusat_kolom(vs_med, pusat_med)

    # Pusat tiap kolom (pra-geser). Kolom ujung/rantai simetris
    # terhadap garis; kolom perantara dihitung sesudah garis
    # langsung diketahui (posisinya tergantung garis itu).
    pusat_kolom = {}
    for t, vs in kolom.items():
        if t != t_med:
            pusat_kolom[t] = _pusat_kolom(vs, _pusat_untuk_kolom(t, vs))
    if t_med is not None:
        pusat_kolom[t_med] = _pusat_mediasi(posisi_z or 'atas')
    kotak: list[dict] = []
    for t in sorted(kolom):
        vs = kolom[t]
        hs = [tinggi_oval(v['nama']) for v in vs]
        ys = [round(c - h / 2)
              for c, h in zip(pusat_kolom[t], hs)]
        for v, h, y in zip(vs, hs, ys):
            kotak.append({'id': v.get('kode') or v.get('nama'),
                          'nama': v['nama'],
                          'kode': v.get('kode') or v.get('nama'),
                          'peran': v.get('peran') or 'X',
                          'x': x_kolom[t], 'y': y,
                          'w': LEBAR_KOTAK, 'h': h})
    # Tinggi kanvas memeluk isi: dari kotak teratas sampai kotak
    # terbawah + margin 20 px di atas dan bawah. Kanvas tidak lagi
    # simetris terhadap garis tengah (model 1 X memang berat ke
    # atas, seperti contoh 1 Boss); garis tengah akhir dicatat di
    # 'tengah' supaya uji simetri tidak memakai tinggi // 2.
    if kotak:
        atas = min(k['y'] for k in kotak)
        bawah = max(k['y'] + k['h'] for k in kotak)
        tinggi_kanvas = (bawah - atas) + 2 * 20
        geser = 20 - atas
        if geser:
            for k in kotak:
                k['y'] += geser
        tengah = TENGAH_KANVAS + geser
    else:
        tinggi_kanvas = KANVAS_TINGGI
        tengah = TENGAH_KANVAS
    panah: list[dict] = []
    for j in model.get('jalur') or []:
        label = j['hipotesis']
        if j.get('arah'):
            label = f"{label} ({j['arah']})"
        if j.get('jenis') == 'tidak_langsung':
            if j.get('lewat'):
                # Label SATU kali saja (segmen pertama, Dari ke
                # Lewat); segmen kedua (Lewat ke Ke) tanpa label,
                # seperti contoh 3 yang tiap segmen berlabel beda
                # dan tidak ada label yang sama dua kali.
                panah.append({'dari': j['dari'], 'ke': j['lewat'],
                              'label': label, 'gaya': 'lewat'})
                panah.append({'dari': j['lewat'], 'ke': j['ke'],
                              'label': '', 'gaya': 'lewat'})
            else:
                panah.append({'dari': j['dari'], 'ke': j['ke'],
                              'label': label, 'gaya': 'lewat'})
            continue
        panah.append({'dari': j['dari'], 'ke': j['ke'], 'label': label,
                      'gaya': 'putus' if j.get('jenis') == 'interaksi'
                      else 'lurus'})
    hasil = {'kotak': kotak, 'panah': panah,
             'bentuk': bentuk_model(model), 'lebar': lebar_kanvas,
             'tinggi': tinggi_kanvas, 'tengah': tengah,
             'posisi_z': posisi_z if t_med is not None else None}
    # Indikator (bila ada): kolom kotak kecil di samping oval,
    # kanvas melebar seperlunya; tanpa indikator tidak ada perubahan.
    tambah_indikator(hasil, _indikator_dari_model(model))
    return hasil


def tata_dari_kotak(kotak, panah, jenis: str = 'model',
                   tinggi: int | None = None,
                   indikator=None) -> tuple:
    """Periksa tata letak buatan mahasiswa di editor.
    Kembalikan (tata, masalah). 'tinggi' = tinggi kanvas yang
    dikirim editor (bila tidak ada, pakai KANVAS_TINGGI).
    'indikator' = daftar {induk, teks} dari editor (kotak indikator
    menempel pada kotak induknya; posisinya dihitung ulang di
    sini dari posisi kotak akhir, supaya ikut bila kotak digeser)."""
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
        tinggi_kanvas = tinggi or KANVAS_TINGGI
        y = max(0, min(tinggi_kanvas - 60, y))
        kid = str(k.get('id') or f'k{len(bersih) + 1}')
        if kid in id_ada:
            kid = f'{kid}_{len(bersih) + 1}'
        id_ada.add(kid)
        # Tinggi mengikuti nama (oval model 2 baris = 240, kotak
        # Desain 2 baris = 110), supaya teks tidak terpotong sesudah
        # kotak digeser atau diubah tulisannya; tinggi yang dikirim
        # editor tidak boleh lebih pendek dari itu.
        try:
            h_kirim = int(k.get('h') or 90)
        except (TypeError, ValueError):
            h_kirim = 90
        h = h_kirim if jenis == 'desain' else max(
            h_kirim, tinggi_oval(nama, LEBAR_KOTAK))
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
    # Tinggi kanvas memeluk isi (kotak terbawah + 20 px, sama dengan
    # margin atas draf), bukan 800 tetap: PNG akhir ikut terpotong
    # seperti drafnya. Batas bawah 240 px supaya diagram yang sangat
    # kecil tetap punya ruang.
    tinggi_manual = max(
        240,
        max((b['y'] + b['h'] for b in bersih), default=0) + 20)
    hasil = {'kotak': bersih, 'panah': panah_bersih,
             'bentuk': 'manual', 'lebar': lebar_manual,
             'tinggi': tinggi_manual}
    # Indikator dari editor: {induk, teks} per kotak indikator;
    # induk harus id kotak yang ada, teks dibersihkan, maks
    # BATAS_IND per induk. Posisi dihitung ulang dari kotak akhir.
    ind_kirim: dict[str, list] = {}
    if isinstance(indikator, list):
        for it in indikator:
            if not isinstance(it, dict):
                continue
            induk = str(it.get('induk') or '')
            teks = _rapi(it.get('teks'))
            if induk not in id_ada or not teks:
                continue
            ind_kirim.setdefault(induk, [])
            if teks not in ind_kirim[induk]:
                ind_kirim[induk].append(teks)
        ind_kirim = {k: v[:BATAS_IND] for k, v in ind_kirim.items()}
    tambah_indikator(hasil, ind_kirim or None)
    return hasil, []


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
    jadi ini hanya alih bentuk, bukan baca ulang. Peta memakai
    istilah lazim yang sama (M perantara, Z penguat), jadi peran
    diteruskan apa adanya tanpa ubah."""
    if not isinstance(peta, dict) or not peta.get('variabel'):
        return None
    return {'variabel': [{'nama': v.get('nama', ''),
                          'peran': v.get('peran', 'X'),
                          'indikator': _bersihkan_indikator(
                              v.get('indikator'))}
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
