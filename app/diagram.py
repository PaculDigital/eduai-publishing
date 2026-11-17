"""DIAGRAM MODEL DAN DESAIN PENELITIAN — logika murni, tanpa AI.

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

KANVAS_LEBAR = 1200
KANVAS_TINGGI = 700
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
    jalur: list[dict] = []
    label_pakai: set[str] = set()
    for j in jalur_masuk:
        if not isinstance(j, dict):
            continue
        dari = _rapi(j.get('dari'))
        ke = _rapi(j.get('ke'))
        label = _rapi(j.get('hipotesis'))
        jenis = str(j.get('jenis') or 'langsung').strip().lower()
        arah = str(j.get('arah') or '').strip()
        if not dari or not ke:
            continue
        if _normalisasi_nama(dari) not in nama_ke_kode:
            masalah.append(f'Jalur menunjuk "{dari}" yang tidak ada '
                           'di daftar variabel.')
            continue
        if _normalisasi_nama(ke) not in nama_ke_kode:
            masalah.append(f'Jalur menunjuk "{ke}" yang tidak ada '
                           'di daftar variabel.')
            continue
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
        jalur.append({'dari': nama_ke_kode[_normalisasi_nama(dari)],
                      'ke': nama_ke_kode[_normalisasi_nama(ke)],
                      'hipotesis': label, 'jenis': jenis, 'arah': arah})
    if masalah:
        return None, masalah
    return {'variabel': variabel, 'jalur': jalur,
            'jenis': data.get('jenis') or '',
            'desain': data.get('desain') or ''}, []


def bentuk_model(model: dict) -> str:
    """'mediasi' bila ada Z, 'banyak_x' bila X lebih dari satu,
    sisanya 'langsung'."""
    peran = [v['peran'] for v in model.get('variabel') or []]
    if 'Z' in peran:
        return 'mediasi'
    if peran.count('X') > 1:
        return 'banyak_x'
    return 'langsung'


def tata_letak(model: dict) -> dict:
    """Tata letak deterministik: kotak + panah dalam kanvas 1200x700.

    X di kiri, Y di kanan, Z di bawah tengah (supaya panah langsung
    X ke Y tidak menabrak kotak Z). Panah 'tidak_langsung' tidak
    digambar sendiri (jalurnya lewat Z, sudah terlihat di gambar).
    """
    variabel = model.get('variabel') or []
    xs = [v for v in variabel if v['peran'] == 'X']
    zs = [v for v in variabel if v['peran'] == 'Z']
    ys = [v for v in variabel if v['peran'] == 'Y']
    n_x = max(1, len(xs))
    tinggi = 90 if n_x <= 4 else 64
    kotak: list[dict] = []

    def _y_x(i: int) -> int:
        if n_x == 1:
            return 305
        return round(110 + i * (390 / (n_x - 1)))

    for i, v in enumerate(xs):
        kotak.append({'id': v['kode'], 'nama': v['nama'], 'kode': v['kode'],
                      'peran': 'X', 'x': 60, 'y': _y_x(i),
                      'w': LEBAR_KOTAK, 'h': tinggi})
    for v in zs:
        kotak.append({'id': v['kode'], 'nama': v['nama'], 'kode': v['kode'],
                      'peran': 'Z', 'x': 450, 'y': 520,
                      'w': LEBAR_KOTAK, 'h': tinggi})
    for v in ys:
        kotak.append({'id': v['kode'], 'nama': v['nama'], 'kode': v['kode'],
                      'peran': 'Y', 'x': 840, 'y': 305,
                      'w': LEBAR_KOTAK, 'h': tinggi})
    panah: list[dict] = []
    for j in model.get('jalur') or []:
        if j.get('jenis') == 'tidak_langsung':
            continue
        label = j['hipotesis']
        if j.get('arah'):
            label = f"{label} ({j['arah']})"
        panah.append({'dari': j['dari'], 'ke': j['ke'], 'label': label,
                      'gaya': 'putus' if j.get('jenis') == 'interaksi'
                      else 'lurus'})
    return {'kotak': kotak, 'panah': panah,
            'bentuk': bentuk_model(model)}


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
        bersih.append({'id': kid, 'nama': nama, 'kode': kid,
                       'peran': peran, 'x': x, 'y': y,
                       'w': LEBAR_KOTAK, 'h': 90})
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
                             'gaya': 'putus' if p.get('gaya') == 'putus'
                             else 'lurus'})
    if masalah:
        return None, masalah
    return {'kotak': bersih, 'panah': panah_bersih,
            'bentuk': 'manual'}, []


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
def periksa_gambar(path, bagian: str, judul_harapan: str) -> dict:
    """Periksa gambar di satu bagian naskah.

    Mesin tidak bisa membaca isi gambar (piksel). Yang diperiksa:
    gambar ada atau tidak, dan keterangannya benar atau tidak.
    Vonis: 'sesuai' (ada + keterangan cocok, dibiarkan),
    'meragukan' (ada tapi keterangan salah/tidak ada),
    'tidak_ada' (belum ada gambar).
    """
    from .gambar import _cocok_judul
    from .pustaka_periksa import _RE_P, _teks_par_xml
    path = Path(path)
    if not path.exists():
        return {'ada': False, 'keterangan': [], 'vonis': 'tidak_ada',
                'sebab': 'berkas tidak ada'}
    try:
        with zipfile.ZipFile(path) as z:
            doc = z.read('word/document.xml').decode('utf-8')
    except Exception as e:                                      # noqa: BLE001
        return {'ada': False, 'keterangan': [], 'vonis': 'tidak_ada',
                'sebab': f'berkas tidak bisa dibaca: {e}'}
    cocok = list(_RE_P.finditer(doc))
    teks_par = [_teks_par_xml(m.group(0)) for m in cocok]
    awal = None
    for i, t in enumerate(teks_par):
        if _cocok_judul(t, bagian):
            awal = i
            break
    if awal is None:
        return {'ada': False, 'keterangan': [], 'vonis': 'tidak_ada',
                'sebab': f'Bagian {bagian} tidak ditemukan di naskah.'}
    akhir = len(teks_par)
    for i in range(awal + 1, len(teks_par)):
        t = teks_par[i]
        if re.match(r'^\d+\.\d+\s+\S', t) and len(t) < 90:
            akhir = i
            break
        if re.match(r'^BAB\s+(?:[IVX]+|\d+)\b', t.strip(),
                    re.IGNORECASE):
            akhir = i
            break
    keterangan: list[str] = []
    ada_gambar = False
    pola_cap = re.compile(r'^\s*Gambar\s+\d+\.\d+\b.*', re.IGNORECASE)
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
    Yang dibuang hanya paragraf gambar + keterangan yang judulnya
    cocok; berkas media lama dibiarkan di dalam zip (tidak terpakai,
    tidak merusak dokumen).
    """
    from .gambar import _cocok_judul
    from .pustaka_periksa import _RE_P, _teks_par_xml
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'dibuang': 0, 'sebab': 'berkas tidak ada'}
    try:
        with zipfile.ZipFile(path) as z:
            nama = z.namelist()
            doc = z.read('word/document.xml').decode('utf-8')
            lain = {n: z.read(n) for n in nama if n != 'word/document.xml'}
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'dibuang': 0,
                'sebab': f'berkas tidak bisa dibaca: {e}'}
    cocok = list(_RE_P.finditer(doc))
    teks_par = [_teks_par_xml(m.group(0)) for m in cocok]
    awal = None
    for i, t in enumerate(teks_par):
        if _cocok_judul(t, bagian):
            awal = i
            break
    if awal is None:
        return {'ok': False, 'dibuang': 0,
                'sebab': f'Bagian {bagian} tidak ditemukan di naskah.'}
    akhir = len(teks_par)
    for i in range(awal + 1, len(teks_par)):
        t = teks_par[i]
        if re.match(r'^\d+\.\d+\s+\S', t) and len(t) < 90:
            akhir = i
            break
        if re.match(r'^BAB\s+(?:[IVX]+|\d+)\b', t.strip(),
                    re.IGNORECASE):
            akhir = i
            break
    harapan = _normalisasi_nama(judul_harapan)
    pola_cap = re.compile(r'^\s*Gambar\s+\d+\.\d+\b.*', re.IGNORECASE)
    buang: set[int] = set()
    for i in range(awal, akhir):
        if pola_cap.match(teks_par[i] or '') and \
                harapan in _normalisasi_nama(teks_par[i]):
            buang.add(i)
            # Paragraf gambar ada tepat sebelum keterangan.
            if i - 1 >= awal and '<w:drawing' in cocok[i - 1].group(0):
                buang.add(i - 1)
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
    from .gambar import _cocok_judul
    from .pustaka_periksa import _RE_P, _teks_par_xml
    path = Path(path)
    if not path.exists():
        return False
    try:
        with zipfile.ZipFile(path) as z:
            doc = z.read('word/document.xml').decode('utf-8')
    except Exception:                                          # noqa: BLE001
        return False
    cocok = list(_RE_P.finditer(doc))
    teks_par = [_teks_par_xml(m.group(0)) for m in cocok]
    awal = None
    for i, t in enumerate(teks_par):
        if _cocok_judul(t, bagian):
            awal = i
            break
    if awal is None:
        return False
    for i in range(awal + 1, len(teks_par)):
        t = teks_par[i]
        if re.match(r'^\d+\.\d+\s+\S', t) and len(t) < 90:
            break
        if re.match(r'^BAB\s+(?:[IVX]+|\d+)\b', t.strip(),
                    re.IGNORECASE):
            break
        if t.strip():
            return True
    return False


def sisip_teks_setelah_judul(path, bagian: str, baris: list[str]) -> dict:
    """Sisipkan paragraf teks tepat sesudah judul bagian."""
    from .gambar import _cocok_judul
    from .pustaka_periksa import _RE_P, _teks_par_xml
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'sebab': 'berkas tidak ada'}
    if not baris:
        return {'ok': True, 'ditambah': 0}
    try:
        with zipfile.ZipFile(path) as z:
            nama = z.namelist()
            doc = z.read('word/document.xml').decode('utf-8')
            lain = {n: z.read(n) for n in nama if n != 'word/document.xml'}
    except Exception as e:                                      # noqa: BLE001
        return {'ok': False, 'sebab': f'berkas tidak bisa dibaca: {e}'}
    cocok = list(_RE_P.finditer(doc))
    teks_par = [_teks_par_xml(m.group(0)) for m in cocok]
    awal = None
    for i, t in enumerate(teks_par):
        if _cocok_judul(t, bagian):
            awal = i
            break
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
    entri = BA.entri_daftar_keterangan(teks_par).get('daftar_gambar', [])
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
