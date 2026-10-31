"""Perbaikan mesin buku, Gas Boss 31 Okt 2026 17:05.

Tiga cacat job 227 yang diperbaiki di mesin, bukan di naskah:
  1. Kalimat ganda antarbab hanya dicatat, tidak diperbaiki, lalu
     buku tetap dirakit. Di sini kalimat ganda ditulis ulang hanya
     kalimat itu saja, lalu dicek lagi.
  2. Daftar pustaka memakai placeholder "belum tersedia di panen"
     untuk sitasi badan yang tidak ada di panen. Di sini sitasi luar
     panen dihapus dari badan, dan pustaka hanya dari baris snapshot
     job itu, satu artikel satu entri, lengkap dengan judul.
  3. Ambang cakupan hanya 50 persen, jadi 7 dari 8 lolos. Di sini
     tiap bab dituntut 8 dari 8: baris yang hilang disisipkan satu
     kalimat sitasi dari data panen itu saja, bila tidak bisa
     disisipkan buku gagal bersih, bukan dirakit cacat.

Urutan wajib di pemanggil: hapus luar, lalu sisip cakupan, lalu
tulis ulang ganda, lalu cek ulang, baru rakit. Sisipan bisa
menimbulkan kalimat ganda baru, jadi cek ganda harus sesudah
sisipan, bukan sebelumnya.

Modul ini deterministik kecuali tulis ulang ganda, yang memakai
callable panggil_llm dari pemanggil (combo EduAi yang sudah ada,
bukan model hardcode). Tanpa panggil_llm, tulis ulang ganda hanya
memakai jalan terakhir hapus kalimat, bila aman.
"""

import re

try:
    from . import sitasi_anti_gagal as SG
    from . import gerbang_subbab as GB
except ImportError:
    try:
        from app import sitasi_anti_gagal as SG
        from app import gerbang_subbab as GB
    except ImportError:
        import sitasi_anti_gagal as SG
        import gerbang_subbab as GB

try:
    import mutu_isi_buku as MI
except ImportError:
    MI = None


def _kalimat(teks):
    """Pecah teks jadi kalimat cukup panjang, sama seperti penjaga mutu."""
    if MI is not None:
        try:
            return MI._kalimat(teks)
        except Exception:
            pass
    bagian = re.split(r'(?<=[.!?])\s+', (teks or '').strip())
    return [b.strip() for b in bagian if len(b.split()) >= 10]


def _kemiripan(a, b):
    """Kemiripan kata dua kalimat, sama seperti penjaga mutu."""
    if MI is not None:
        try:
            return MI.kemiripan(a, b)
        except Exception:
            pass
    ka = set(re.findall(r'\b[a-zA-Z]{5,}\b', (a or '').lower()))
    kb = set(re.findall(r'\b[a-zA-Z]{5,}\b', (b or '').lower()))
    if not ka or not kb:
        return 0.0
    return len(ka & kb) / len(ka | kb)


def _token_kata(teks):
    """Token kata bermakna untuk pencocokan subbab, huruf kecil."""
    henti = {'dan', 'yang', 'untuk', 'dengan', 'dalam', 'dari', 'pada',
             'oleh', 'ini', 'itu', 'sebagai', 'tentang', 'kajian',
             'adalah', 'atau', 'juga', 'serta', 'bagi', 'para'}
    return [w for w in re.findall(r'[a-zA-Z]{4,}', (teks or '').lower())
            if w not in henti]


def _ganti_kalimat(teks, lama, baru):
    """Ganti kemunculan pertama satu kalimat, toleran terhadap spasi."""
    if lama and lama in teks:
        return teks.replace(lama, baru, 1), True
    pola = re.compile(re.escape(lama).replace(r'\ ', r'\s+'))
    teks_baru, n = pola.subn(lambda m: baru, teks, count=1)
    return teks_baru, n > 0


def _hapus_kalimat(teks, kalimat):
    """Hapus satu kalimat utuh dari teks, rapikan spasi di barisnya."""
    teks_baru, ketemu = _ganti_kalimat(teks, kalimat, '')
    if not ketemu:
        return teks, False
    baris = []
    for b in teks_baru.split('\n'):
        b = re.sub(r'[ \t]{2,}', ' ', b).strip(' \t')
        baris.append(b)
    return '\n'.join(baris), True


# ---------------------------------------------------------------------------
# Langkah 2: hapus sitasi luar panen
# ---------------------------------------------------------------------------

def hapus_luar_per_bab(teks_per_bab, rows_per_bab):
    """Hapus sitasi luar snapshot per bab, deterministik.

    Memakai hapus_sitasi_luar yang sudah ada di gerbang subbab, supaya
    definisi luar sama persis: sitasi yang tidak satu pun surnamenya
    cocok dengan baris snapshot untuk tahun itu. Sitasi campuran
    (satu surname snapshot, satu surname luar) TIDAK dihapus.

    Return (teks_baru, laporan) dengan laporan per bab {dihapus: list
    sitasi mentah unik, kemunculan: jumlah kemunculan di teks awal}.
    """
    teks_baru = {}
    laporan = {}
    for n in sorted(teks_per_bab):
        teks = teks_per_bab[n] or ''
        rows = (rows_per_bab or {}).get(n) or []
        bersih, dihapus = GB.hapus_sitasi_luar(teks, rows)
        kemunculan = sum(teks.count(raw) for raw in dihapus)
        teks_baru[n] = bersih
        laporan[n] = {'dihapus': list(dihapus),
                      'kemunculan': kemunculan}
    return teks_baru, laporan


# ---------------------------------------------------------------------------
# Langkah 3: sisip cakupan sampai 8 dari 8
# ---------------------------------------------------------------------------

def _baris_hilang(teks, rows):
    """Baris snapshot yang belum dikutip di teks, urut snapshot."""
    if not rows:
        return []
    cak = SG.hitung_cakupan_kunci(teks, rows)
    hilang_kunci = set(cak.get('hilang') or [])
    hasil = []
    for row in rows:
        kunci = SG._lipat_token(row.get('kunci') or '')
        if kunci and kunci in hilang_kunci:
            hasil.append(row)
    return hasil


def _nama_naratif(row):
    """Surname untuk sitasi naratif, kata terakhir nama tampil."""
    tampil = (row.get('surname_tampil') or '').strip()
    if tampil:
        nama = tampil.split()[-1].strip('.,;:!?')
        if nama:
            return nama
    kunci = (row.get('kunci') or '').strip()
    if kunci:
        return kunci[0].upper() + kunci[1:]
    return ''


def _judul_row(row):
    """Judul artikel dari data panen, kosong bila tidak ada."""
    ref = row.get('ref_dict') or {}
    return (ref.get('title') or '').strip()


def _kalimat_sisipan(row, varian):
    """Satu kalimat sitasi dari data panen saja, tanpa klaim temuan.

    Tiga template diputar menurut varian, supaya artikel yang sama
    yang disisipkan di beberapa bab tidak langsung menjadi kalimat
    yang sama persis di semua bab. Isi kalimat hanya menyebut
    penulis, tahun, dan judul dari database, tidak mengarang hasil
    penelitian artikel itu.
    """
    nama = _nama_naratif(row)
    tahun = row.get('tahun') or ''
    judul = _judul_row(row).replace('"', "'")
    template = [
        '%s (%s) membahas "%s" dan menjadi salah satu rujukan bab ini.',
        'Sebagai rujukan bab ini, %s (%s) menulis "%s".',
        'Rujukan bab ini juga mencakup karya %s (%s) yang berjudul "%s".',
    ]
    return template[varian % len(template)] % (nama, tahun, judul)


def _sisip_di_akhir_subbab(teks, nomor_subbab, kalimat):
    """Sisipkan kalimat di akhir bagian subbab, sebelum judul ### berikut.

    nomor_subbab adalah string 'N.M' seperti di outline referensi,
    contoh '3.1'. Bila judul subbab tidak ditemukan, tempel di akhir
    bab, supaya sisipan tidak hilang diam-diam.
    """
    pola_judul = re.compile(
        r'^###\s*' + re.escape(str(nomor_subbab)) + r'\b',
        re.MULTILINE)
    cocok = pola_judul.search(teks)
    if not cocok:
        return teks.rstrip() + '\n\n' + kalimat + '\n', False
    pola_berikut = re.compile(r'^###\s+', re.MULTILINE)
    berikut = pola_berikut.search(teks, cocok.end())
    if berikut:
        return (teks[:berikut.start()].rstrip() + '\n\n' + kalimat + '\n\n'
                + teks[berikut.start():]), True
    return teks.rstrip() + '\n\n' + kalimat + '\n', True


def _sisip_sebelum_ringkasan(teks, kalimat):
    """Sisipkan kalimat sebelum bagian Ringkasan, atau di akhir bab."""
    pola = re.compile(r'^#{1,3}\s+.*Ringkasan.*$', re.MULTILINE)
    cocok = pola.search(teks)
    if cocok:
        return teks[:cocok.start()].rstrip() + '\n\n' + kalimat + '\n\n' + teks[cocok.start():]
    return teks.rstrip() + '\n\n' + kalimat + '\n'


def _pilih_subbab(judul, subs):
    """Nomor subbab yang kata kuncinya paling cocok dengan judul artikel.

    Return None bila tidak ada kata kunci yang cocok sama sekali.
    """
    kata_judul = set(_token_kata(judul))
    if not kata_judul or not subs:
        return None
    terbaik, skor_terbaik = None, 0
    for sub in subs:
        try:
            nomor_sub = sub[0]
            teks_sub = ' '.join(str(x) for x in sub[1:])
        except Exception:
            continue
        skor = len(kata_judul & set(_token_kata(teks_sub)))
        if skor > skor_terbaik:
            terbaik, skor_terbaik = nomor_sub, skor
    return terbaik


def sisip_cakupan_per_bab(teks, nomor_bab, rows, subs=None):
    """Sisipkan kalimat sitasi untuk tiap baris snapshot yang hilang.

    Return (teks_baru, sisipan) dengan sisipan list {kunci, tahun,
    subbab, kalimat}. Bila baris hilang tanpa judul, raise
    GagalSitasiBersih dengan galat yang menyebut bab, cakupan, dan
    baris hilang, supaya pemanggil gagal bersih dan token kembali,
    bukan merakit buku cacat. Bila kalimat sisipan pertama tidak
    terbaca sebagai sitasi oleh ekstraktor, dicoba bentuk kurung
    sebagai kalimat kedua di tempat yang sama.
    """
    teks_baru = teks or ''
    sisipan = []
    hilang = _baris_hilang(teks_baru, rows)
    for idx, row in enumerate(hilang):
        kunci = row.get('kunci') or ''
        tahun = row.get('tahun') or ''
        judul = _judul_row(row)
        if not judul:
            cak = SG.hitung_cakupan_kunci(teks_baru, rows)
            detail = (SG.detail_galat_sitasi(nomor_bab, cak)
                      + ', baris hilang tanpa judul: %s %s'
                      % (kunci, tahun))
            raise SG.GagalSitasiBersih(
                nomor_bab=nomor_bab,
                masalah=['baris snapshot %s %s tanpa judul, tidak bisa disisipkan'
                         % (kunci, tahun)],
                cakupan=cak, detail_text=detail)
        nomor_sub = _pilih_subbab(judul, subs)
        kalimat = _kalimat_sisipan(row, nomor_bab + idx)
        if nomor_sub is not None:
            teks_baru, _ = _sisip_di_akhir_subbab(
                teks_baru, nomor_sub, kalimat)
            lokasi = nomor_sub
        else:
            teks_baru = _sisip_sebelum_ringkasan(teks_baru, kalimat)
            lokasi = 'akhir'
        # Pastikan sisipan terbaca sebagai sitasi baris itu.
        masih_hilang = [r for r in _baris_hilang(teks_baru, rows)
                        if SG._lipat_token(r.get('kunci') or '')
                        == SG._lipat_token(kunci)]
        if masih_hilang:
            nama = _nama_naratif(row)
            kalimat_kurung = ('Rujukan ini dicatat sebagai '
                              '(%s, %s).' % (nama, tahun))
            if nomor_sub is not None:
                teks_baru, _ = _sisip_di_akhir_subbab(
                    teks_baru, nomor_sub, kalimat_kurung)
            else:
                teks_baru = _sisip_sebelum_ringkasan(
                    teks_baru, kalimat_kurung)
            kalimat = kalimat + ' ' + kalimat_kurung
        sisipan.append({'kunci': kunci, 'tahun': tahun,
                        'subbab': lokasi, 'kalimat': kalimat})
    return teks_baru, sisipan


# ---------------------------------------------------------------------------
# Pustaka kanonik, tanpa placeholder
# ---------------------------------------------------------------------------

def pustaka_kanonik(teks_per_bab, rows_per_bab):
    """Daftar pustaka dari baris snapshot yang dikutip, satu artikel satu entri.

    Entri memakai format APA dari ref_dict baris itu, jadi tag
    [Sumber: X] yang sudah ada di pemanggil tetap cocok dengan
    entri ini. Satu artikel yang dikutip di beberapa bab, atau
    dikutip dengan bentuk penulis berbeda, hanya satu entri.
    Return (pustaka, laporan) dengan laporan {total, tanpa_judul:
    list kunci-tahun yang dikutip tapi judulnya kosong di database}.
    """
    try:
        from verifikasi_sitasi import format_apa as _format_apa
    except ImportError:
        try:
            from app.verifikasi_sitasi import format_apa as _format_apa
        except ImportError:
            _format_apa = None

    pustaka = []
    lihat = set()
    tanpa_judul = []
    for n in sorted(teks_per_bab):
        teks = teks_per_bab[n] or ''
        rows = (rows_per_bab or {}).get(n) or []
        if not rows:
            continue
        cak = SG.hitung_cakupan_kunci(teks, rows)
        cocok = set(cak.get('cocok') or [])
        for row in rows:
            kunci = SG._lipat_token(row.get('kunci') or '')
            if kunci not in cocok:
                continue
            artikel_id = row.get('artikel_id')
            kunci_dedup = ('id', artikel_id) if artikel_id else (
                'kunci', kunci, row.get('tahun') or '')
            if kunci_dedup in lihat:
                continue
            lihat.add(kunci_dedup)
            ref = row.get('ref_dict') or {}
            entri = None
            if _format_apa is not None and ref:
                try:
                    entri = _format_apa(ref)
                except Exception:
                    entri = None
            if not entri:
                tampil = row.get('surname_tampil') or row.get('kunci') or ''
                judul = _judul_row(row)
                jurnal = (ref.get('journal') or '').strip()
                entri = '%s (%s). %s.' % (tampil, row.get('tahun') or '', judul)
                if jurnal:
                    entri += ' %s.' % jurnal
            if not _judul_row(row):
                tanpa_judul.append('%s %s' % (
                    row.get('kunci') or '', row.get('tahun') or ''))
            pustaka.append(entri.strip())
    return pustaka, {'total': len(pustaka), 'tanpa_judul': tanpa_judul}


# ---------------------------------------------------------------------------
# Langkah 1: tulis ulang kalimat ganda
# ---------------------------------------------------------------------------

def _ganda(teks_per_bab):
    """Pasangan kalimat ganda antarbab, dari penjaga mutu yang sama."""
    nomor = sorted(teks_per_bab)
    hasil = {}
    for i, a in enumerate(nomor):
        for b in nomor[i + 1:]:
            if MI is not None:
                kunci = MI.kalimat_berulang(teks_per_bab[a], teks_per_bab[b])
            else:
                kunci = []
                for k in _kalimat(teks_per_bab[b]):
                    for k2 in _kalimat(teks_per_bab[a]):
                        if _kemiripan(k, k2) >= 0.80:
                            kunci.append(k[:120])
                            break
            if kunci:
                kalimat_b = _kalimat(teks_per_bab[b])
                penuh = []
                for pref in kunci:
                    for kal in kalimat_b:
                        if kal.startswith(pref) or pref.startswith(kal[:120]):
                            if kal not in penuh:
                                penuh.append(kal)
                            break
                if penuh:
                    hasil[(a, b)] = penuh
    return hasil


def _sitasi_kalimat(kalimat):
    """Himpunan sitasi formal satu kalimat, untuk validasi tulis ulang."""
    hasil = set()
    for sit in SG.ekstrak_sitasi_badan(kalimat):
        hasil.add((tuple(sit.get('surnames') or []), sit.get('tahun') or ''))
    return hasil


def _tulis_ulang_satu(kalimat, panggil_llm):
    """Minta tulis ulang satu kalimat, validasi ketat, atau None."""
    if panggil_llm is None:
        return None
    sitasi_asli = _sitasi_kalimat(kalimat)
    kata_asli = len(kalimat.split())
    prompt = (
        'Tulis ulang kalimat berikut dengan kata berbeda, makna sama, '
        'panjang mirip, pertahankan sitasi (Nama, Tahun) yang ada '
        'persis bila ada, jangan tambah sitasi baru, jangan tambah '
        'klaim baru, jangan tambah nama penulis baru, jangan tambah '
        'kalimat lain. Kembalikan HANYA kalimat itu, tanpa penjelasan, '
        'tanpa tanda kutip pembungkus. Kalimat: ' + kalimat)
    for _percobaan in range(2):
        try:
            jawaban = panggil_llm(prompt)
        except Exception:
            jawaban = None
        if not jawaban or not str(jawaban).strip():
            continue
        baru = str(jawaban).strip()
        baru = baru.strip('"').strip()
        if '\n' in baru:
            baru = baru.split('\n')[0].strip()
        if len(baru.split()) < 10:
            continue
        if not (0.5 * kata_asli <= len(baru.split()) <= 1.5 * kata_asli):
            continue
        if _sitasi_kalimat(baru) != sitasi_asli:
            continue
        if SG.pindai_inisial(baru):
            continue
        if _kemiripan(baru, kalimat) >= 0.80:
            continue
        return baru
    return None


def tulis_ulang_ganda(teks_per_bab, panggil_llm, rows_per_bab=None):
    """Tulis ulang kalimat ganda di bab belakangan, lalu cek lagi.

    Return (teks_baru, laporan) dengan laporan {ditulis_ulang, dihapus,
    tidak_teratasi, ganda_sisa}. Jalan terakhir hapus kalimat hanya
    dipakai bila kalimat itu tidak memuat satu-satunya sitasi sebuah
    baris snapshot di bab itu; bila tidak bisa ditulis ulang dan
    tidak bisa dihapus dengan aman, kalimat itu dilaporkan tidak
    teratasi dan pemanggil wajib gagal bersih, bukan merakit cacat.
    """
    teks_baru = dict(teks_per_bab or {})
    laporan = {'ditulis_ulang': [], 'dihapus': [],
               'tidak_teratasi': [], 'ganda_sisa': []}
    nomor = sorted(teks_baru)
    for i, a in enumerate(nomor):
        for b in nomor[i + 1:]:
            ganda = _ganda({a: teks_baru[a], b: teks_baru[b]}).get((a, b), [])
            for kalimat in ganda:
                if kalimat not in _kalimat(teks_baru[b]):
                    continue
                baru = _tulis_ulang_satu(kalimat, panggil_llm)
                if baru is not None:
                    teks_ganti, ketemu = _ganti_kalimat(
                        teks_baru[b], kalimat, baru)
                    if ketemu and _kemiripan(baru, kalimat) < 0.80:
                        teks_baru[b] = teks_ganti
                        laporan['ditulis_ulang'].append(
                            {'bab': b, 'lama': kalimat, 'baru': baru})
                        continue
                # Jalan terakhir: hapus, bila aman untuk cakupan.
                aman_hapus = True
                if rows_per_bab and rows_per_bab.get(b):
                    teks_tanpa = _hapus_kalimat(teks_baru[b], kalimat)[0]
                    hilang_sesudah = _baris_hilang(
                        teks_tanpa, rows_per_bab[b])
                    hilang_sebelum = _baris_hilang(
                        teks_baru[b], rows_per_bab[b])
                    if len(hilang_sesudah) > len(hilang_sebelum):
                        aman_hapus = False
                if aman_hapus:
                    teks_hapus, ketemu = _hapus_kalimat(teks_baru[b], kalimat)
                    if ketemu:
                        teks_baru[b] = teks_hapus
                        laporan['dihapus'].append({'bab': b, 'kalimat': kalimat})
                        continue
                laporan['tidak_teratasi'].append({'bab': b, 'kalimat': kalimat})
    sisa = _ganda(teks_baru)
    for (a, b), daftar in sisa.items():
        for kalimat in daftar:
            laporan['ganda_sisa'].append(
                {'bab_awal': a, 'bab': b, 'kalimat': kalimat})
    return teks_baru, laporan


# ---------------------------------------------------------------------------
# Orkestrasi, urutan wajib
# ---------------------------------------------------------------------------

def perbaiki_buku(teks_per_bab, rows_per_bab, subs_per_bab=None,
                  panggil_llm=None):
    """Jalankan 3 langkah dalam urutan wajib, return (teks, laporan).

    Urutan: hapus luar, lalu sisip cakupan, lalu tulis ulang ganda.
    Gagal bersih dari sisip cakupan (baris tanpa judul) diteruskan
    apa adanya, supaya pemanggil memicu refund, bukan merakit cacat.
    """
    teks1, lap_hapus = hapus_luar_per_bab(teks_per_bab, rows_per_bab)
    teks2 = dict(teks1)
    lap_sisip = {}
    for n in sorted(teks2):
        rows = (rows_per_bab or {}).get(n) or []
        subs = (subs_per_bab or {}).get(n) if subs_per_bab else None
        teks2[n], sisipan = sisip_cakupan_per_bab(teks2[n], n, rows, subs)
        lap_sisip[n] = sisipan
    teks3, lap_ganda = tulis_ulang_ganda(teks2, panggil_llm, rows_per_bab)
    laporan = {'hapus_luar': lap_hapus, 'sisip_cakupan': lap_sisip,
               'ganda': lap_ganda}
    return teks3, laporan
