"""BAB IV — orkestrasi Hasil & Pembahasan (Fase 2, 21 Okt 2026).

Dua isi modul ini (fondasi — alur UI menyusul di fase berikutnya):

1. LAYANAN HASIL: menyimpan hasil hitung dari jembatan Statistik Lab
   sebagai versi-versi (`HasilBab4`), tombol Kunci Hasil, dan tarif
   generate mengikuti keputusan Bos:
     · Paket Olah Data (30 token, dibayar sekali di depan lewat layanan
       kerangka yang sudah ada) mencakup generate pertama.
     · Revisi data pada penelitian & data yang sama: generate ke-2
       s.d. ke-4 GRATIS (itu "gratis 3 kali" — tiga kali generate ULANG),
       generate ke-5 dan seterusnya 5 token per kali (dipotong pemanggil
       lewat kuota; modul ini hanya menghitung tarifnya).
   Narasi hanya boleh lahir dari hasil berstatus 'terkunci'.

2. MESIN ATURAN PETA: pemeriksa konsistensi peta penelitian + penentu
   label desain dari SIDIK JARI FAKTA (prinsip Bos: tanya fakta, bukan
   label). Fungsi-fungsi ini MURNI (tanpa AI, tanpa basis data) supaya
   bisa diuji sendiri dan tidak bisa "mengarang": unsur peta tanpa
   bukti kalimat ditandai sebagai masalah, bukan diteruskan.

Rancangan induk: DOKUMENTASI_BAB4_RANCANGAN_FINAL_21OKT2026.md (§5, §10).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from .models import HasilBab4, PetaBab4

TARIF_GENERATE_LANJUT = 5        # token, per generate sesudah jatah gratis
JATAH_GENERATE_GRATIS = 4        # 1 generate paket + 3 generate ulang gratis


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ══════════════════════════════════════════════════════════════════════════
# LAYANAN HASIL
# ══════════════════════════════════════════════════════════════════════════
def simpan_hasil(db: Session, user_id: int, file_id: int, jenis: str,
                 mode: str, hasil: dict) -> HasilBab4:
    """Simpan hasil hitung sebagai VERSI BARU berstatus 'draf'."""
    terakhir = (db.query(HasilBab4)
                .filter_by(user_id=user_id, file_id=file_id, jenis=jenis)
                .order_by(HasilBab4.nomor.desc()).first())
    baris = HasilBab4(
        user_id=user_id, file_id=file_id, jenis=jenis, mode=mode,
        nomor=(terakhir.nomor + 1) if terakhir else 1,
        status='draf', hasil=json.dumps(hasil, ensure_ascii=False))
    db.add(baris)
    db.commit()
    db.refresh(baris)
    return baris


def jumlah_generate(db: Session, user_id: int, file_id: int,
                    jenis: str = 'olah_data') -> int:
    return (db.query(HasilBab4)
            .filter_by(user_id=user_id, file_id=file_id, jenis=jenis)
            .count())


def tarif_generate_berikutnya(db: Session, user_id: int, file_id: int,
                              jenis: str = 'olah_data') -> int:
    """Token untuk generate berikutnya: 0 selama dalam jatah gratis
    (1 paket + 3 ulang), 5 token sesudahnya. Keputusan Bos 21 Okt 2026."""
    return 0 if jumlah_generate(db, user_id, file_id, jenis) < JATAH_GENERATE_GRATIS \
        else TARIF_GENERATE_LANJUT


def kunci_hasil(db: Session, user_id: int, file_id: int,
                jenis: str = 'olah_data') -> HasilBab4 | None:
    """Bekukan draf TERBARU menjadi 'terkunci' (Kunci Hasil).

    ATURAN (BUG kritis, temuan review 21 Okt): yang boleh dikunci
    hanyalah draf yang nomornya LEBIH BARU dari versi terkunci yang
    sedang berlaku. Tanpa aturan ini, panggilan kedua tanpa data baru
    menurunkan kunci ke draf lama — narasi akan lahir dari angka yang
    BUKAN terakhir dihitung. Tidak ada draf lebih baru → kembalikan
    None, kunci lama tidak diganggu sama sekali.
    Hanya satu versi terkunci yang berlaku pada satu waktu."""
    berlaku = (db.query(HasilBab4)
               .filter_by(user_id=user_id, file_id=file_id, jenis=jenis,
                          status='terkunci')
               .order_by(HasilBab4.nomor.desc()).first())
    batas = berlaku.nomor if berlaku else 0
    draf = (db.query(HasilBab4)
            .filter(HasilBab4.user_id == user_id,
                    HasilBab4.file_id == file_id,
                    HasilBab4.jenis == jenis,
                    HasilBab4.status == 'draf',
                    HasilBab4.nomor > batas)
            .order_by(HasilBab4.nomor.desc()).first())
    if draf is None:
        return None
    for lama in (db.query(HasilBab4)
                 .filter_by(user_id=user_id, file_id=file_id, jenis=jenis,
                            status='terkunci').all()):
        lama.status = 'draf'
        lama.dikunci_pada = None
    draf.status = 'terkunci'
    draf.dikunci_pada = _now()
    db.commit()
    db.refresh(draf)
    return draf


def hasil_terkunci(db: Session, user_id: int, file_id: int,
                   jenis: str = 'olah_data') -> HasilBab4 | None:
    return (db.query(HasilBab4)
            .filter_by(user_id=user_id, file_id=file_id, jenis=jenis,
                       status='terkunci')
            .order_by(HasilBab4.nomor.desc()).first())


def baca_hasil(baris: HasilBab4) -> dict:
    try:
        return json.loads(baris.hasil or '{}')
    except (TypeError, ValueError):
        return {}


# ══════════════════════════════════════════════════════════════════════════
# PETA — simpan & sahkan
# ══════════════════════════════════════════════════════════════════════════
def simpan_peta(db: Session, user_id: int, file_id: int, isi: dict) -> PetaBab4:
    terakhir = (db.query(PetaBab4)
                .filter_by(user_id=user_id, file_id=file_id)
                .order_by(PetaBab4.nomor.desc()).first())
    baris = PetaBab4(
        user_id=user_id, file_id=file_id,
        nomor=(terakhir.nomor + 1) if terakhir else 1,
        status='usulan', isi=json.dumps(isi, ensure_ascii=False))
    db.add(baris)
    db.commit()
    db.refresh(baris)
    return baris


def sahkan_peta(db: Session, peta_id: int) -> PetaBab4 | None:
    baris = db.get(PetaBab4, peta_id)
    if baris is None:
        return None
    baris.status = 'disahkan'
    baris.disahkan_pada = _now()
    db.commit()
    db.refresh(baris)
    return baris


def baca_peta(baris: PetaBab4) -> dict:
    try:
        return json.loads(baris.isi or '{}')
    except (TypeError, ValueError):
        return {}


# ══════════════════════════════════════════════════════════════════════════
# MESIN ATURAN PETA — murni, tanpa AI/DB
# ══════════════════════════════════════════════════════════════════════════
# Bentuk peta kuantitatif:
#   {jenis:'kuantitatif',
#    variabel:[{nama, peran:'X'|'M'|'Z'|'Y', bukti:'kalimat…'|None,
#               indikator:[…]}],
#    jalur:[{dari, ke, hipotesis:'H1', jenis:'langsung'|'tidak_langsung'|
#            'interaksi'}],
#    jumlah_hipotesis:int, target_sampel:int|None}
# Bentuk peta kualitatif:
#   {jenis:'kualitatif', fokus:[{nama, bukti}], informan:[{jenis, bukti}],
#    teknik:[…]}
def periksa_peta(peta: dict) -> list[dict]:
    """Periksa konsistensi peta. Kembalikan daftar masalah
    [{kode, pesan}] — kosong berarti peta konsisten & siap disahkan.

    Aturan kerasnya (keputusan Bos): unsur tanpa bukti = masalah;
    jumlah jalur (berlabel) harus sama dengan jumlah hipotesis;
    ada perantara ⇒ ada jalur masuk DAN keluar; ada penguat ⇒ ada
    jalur interaksi ke hasil."""
    masalah: list[dict] = []

    def tambah(kode: str, pesan: str) -> None:
        masalah.append({'kode': kode, 'pesan': pesan})

    # Pagar bentuk (temuan review 21 Okt): masukan bukan dict / daftar
    # berisi bukan-dict TIDAK BOLEH meledakkan fungsi — pemeriksa yang
    # meledak tidak bisa melaporkan apa-apa. Kembalikan masalah bentuk.
    if not isinstance(peta, dict):
        return [{'kode': 'bentuk_salah',
                 'pesan': 'Peta harus berupa objek (dict), bukan '
                          f'{type(peta).__name__}.'}]
    for kunci_daftar in ('variabel', 'jalur', 'fokus', 'informan'):
        nilai = peta.get(kunci_daftar)
        if nilai is not None and (not isinstance(nilai, list) or
                                  any(not isinstance(x, dict) for x in nilai)):
            tambah('bentuk_salah',
                   f'Bagian "{kunci_daftar}" harus berupa daftar objek.')
            peta = {**peta, kunci_daftar: []}

    if peta.get('jenis') == 'kualitatif':
        if not peta.get('fokus'):
            tambah('fokus_kosong', 'Fokus penelitian belum terisi.')
        if not peta.get('informan'):
            tambah('informan_kosong', 'Informan belum terdaftar.')
        for f in peta.get('fokus') or []:
            if not f.get('bukti'):
                tambah('tanpa_bukti',
                       f'Fokus "{f.get("nama", "?")}" tidak punya bukti '
                       'kalimat dari naskah — tidak boleh dikarang.')
        for i in peta.get('informan') or []:
            if not i.get('bukti'):
                tambah('tanpa_bukti',
                       f'Informan "{i.get("jenis", "?")}" tidak punya '
                       'bukti kalimat dari naskah.')
        return masalah

    variabel = peta.get('variabel') or []
    jalur = peta.get('jalur') or []
    nama_peran: dict[str, str] = {}
    for v in variabel:
        nama = str(v.get('nama') or '')
        if v.get('peran') not in ('X', 'M', 'Z', 'Y'):
            tambah('peran_tak_dikenal',
                   f'Peran "{v.get("peran")}" untuk "{nama}" tidak '
                   'dikenal — peran yang sah hanya X, M, Z, atau Y.')
        if nama in nama_peran and nama_peran[nama] != v.get('peran'):
            tambah('peran_ganda',
                   f'"{nama}" muncul dengan dua peran berbeda '
                   f'({nama_peran[nama]} dan {v.get("peran")}).')
        nama_peran[nama] = v.get('peran')
        if not v.get('bukti'):
            tambah('tanpa_bukti',
                   f'Variabel "{nama}" tidak punya bukti kalimat dari '
                   'naskah — statusnya harus "tidak ditemukan", bukan '
                   'diteruskan.')
    peran_ada = set(nama_peran.values())
    if 'Y' not in peran_ada:
        tambah('tanpa_y', 'Belum ada variabel hasil (Y).')
    if 'X' not in peran_ada:
        tambah('tanpa_x', 'Belum ada variabel bebas (X).')
    if len([1 for r in peran_ada if r == 'Y']) and \
            sum(1 for v in variabel if v.get('peran') == 'Y') > 1:
        tambah('y_ganda', 'Variabel hasil (Y) lebih dari satu — model '
                          'BAB IV ini mendukung satu Y.')

    label = [str(j.get('hipotesis') or '') for j in jalur]
    if any(not h for h in label):
        tambah('jalur_tanpa_label', 'Ada jalur yang belum berlabel '
                                    'hipotesis (H1, H2, …).')
    if len(set(label)) != len(label):
        tambah('label_kembar', 'Ada label hipotesis yang dipakai dua '
                               'jalur sekaligus.')
    jml_hip = peta.get('jumlah_hipotesis')
    # jumlah_hipotesis datang dari AI/pembacaan naskah — bisa bukan
    # angka ('tiga'). int() mentah meledak → 500 di rute (temuan
    # review ronde 5). Parse aman: bukan angka = masalah peta (422).
    try:
        jml_hip_int = int(jml_hip) if jml_hip is not None else None
    except (TypeError, ValueError):
        jml_hip_int = None
        tambah('jumlah_hipotesis_salah',
               f'Jumlah hipotesis harus berupa angka, diterima: '
               f'{jml_hip!r}.')
    if jml_hip_int is not None and len(jalur) != jml_hip_int:
        tambah('jumlah_tak_sama',
               f'Jumlah jalur ({len(jalur)}) tidak sama dengan jumlah '
               f'hipotesis di naskah ({jml_hip_int}).')

    # Tabrakan nama kolom (temuan review Fase 3): dua nama variabel
    # berbeda bisa menyatu jadi dasar kolom yang sama sesudah
    # dibersihkan ('Kualitas Produk' dan 'Kualitas_Produk' → sama) —
    # data dua variabel akan tertukar diam-diam. Tolak sejak peta.
    dasar_kolom: dict[str, str] = {}
    for v in variabel:
        nama_v = str(v.get('nama') or '')
        dasar = _nama_kolom(nama_v)
        if dasar in dasar_kolom and dasar_kolom[dasar] != nama_v:
            tambah('kolom_tabrakan',
                   f'Variabel "{nama_v}" dan "{dasar_kolom[dasar]}" '
                   f'menghasilkan nama kolom yang sama ("{dasar}") — '
                   'samakan ejaannya atau bedakan namanya supaya data '
                   'tidak tertukar.')
        dasar_kolom.setdefault(dasar, nama_v)
    # Bentrok awalan (temuan review ronde 5): dasar yang satu menjadi
    # awalan dasar lain pada batas garis bawah ('Harga' vs 'Harga_1')
    # membuat butir 'Harga_1' ambigu — bisa berarti butir 1 dari
    # 'Harga' atau butir dari variabel 'Harga 1'. Mesin membaca awalan
    # dan akan menggabungkan dua variabel diam-diam. Tolak juga.
    dasars = sorted(dasar_kolom)
    for i, a in enumerate(dasars):
        for b in dasars[i + 1:]:
            if b.startswith(a + '_') or a.startswith(b + '_'):
                tambah('kolom_tabrakan',
                       f'Nama kolom "{a}" dan "{b}" saling mengawali — '
                       'butirnya akan terbaca sebagai satu variabel '
                       'oleh mesin. Bedakan nama variabelnya.')

    # Jalur hantu (temuan review 21 Okt): ujung jalur harus variabel
    # yang BENAR-BENAR ada di daftar — jalur ke variabel tak dikenal
    # adalah persis yang wajib ditolak pemeriksa konsistensi.
    for j in jalur:
        for ujung in ('dari', 'ke'):
            if str(j.get(ujung) or '') not in nama_peran:
                tambah('jalur_hantu',
                       f'Jalur {j.get("hipotesis", "?")} menunjuk '
                       f'variabel "{j.get(ujung)}" yang tidak ada di '
                       'daftar variabel.')

    masuk = {str(j.get('ke')) for j in jalur}
    keluar = {str(j.get('dari')) for j in jalur}
    for v in variabel:
        if v.get('peran') == 'M':
            if v['nama'] not in masuk or v['nama'] not in keluar:
                tambah('perantara_terputus',
                       f'Perantara "{v["nama"]}" harus punya jalur masuk '
                       'DAN jalur keluar.')
        if v.get('peran') == 'Z':
            ada_interaksi = any(
                j.get('jenis') == 'interaksi' and str(j.get('ke')) in
                {n for n, r in nama_peran.items() if r == 'Y'}
                for j in jalur)
            if not ada_interaksi:
                tambah('penguat_tanpa_interaksi',
                       f'Penguat "{v["nama"]}" belum punya jalur '
                       'interaksi ke variabel hasil.')
    return masalah


def label_desain(fakta: dict) -> dict:
    """Tentukan label desain dari SIDIK JARI FAKTA (bukan tebakan label).

    fakta: {perlakuan: bool, kelompok_kontrol: bool,
            ukur_sebelum_sesudah: bool, sekali_sebar: bool}
    Kembalikan {desain, alasan[]} — desain salah satu dari:
    'eksperimen', 'pra-eksperimen', 'survei', 'korelasional',
    'belum_jelas' (fakta belum cukup — yang ditanyakan ke user adalah
    pertanyaan fakta, lihat DOKUMENTASI §5.3)."""
    if not isinstance(fakta, dict):
        fakta = {}
    perlakuan = bool(fakta.get('perlakuan'))
    kontrol = bool(fakta.get('kelompok_kontrol'))
    sebelum = bool(fakta.get('ukur_sebelum_sesudah'))
    sekali = bool(fakta.get('sekali_sebar'))
    if perlakuan and kontrol:
        return {'desain': 'eksperimen',
                'alasan': ['Ada perlakuan dan ada kelompok kontrol.']}
    if perlakuan and not kontrol:
        return {'desain': 'pra-eksperimen',
                'alasan': ['Ada perlakuan tapi tidak ada kelompok '
                           'kontrol.']}
    if sekali and not perlakuan:
        return {'desain': 'survei',
                'alasan': ['Data diambil sekali sebar (kuesioner) tanpa '
                           'perlakuan.']}
    if sebelum and not perlakuan:
        return {'desain': 'korelasional',
                'alasan': ['Ada pengukuran berulang tanpa perlakuan.']}
    return {'desain': 'belum_jelas',
            'alasan': ['Fakta lapangan belum cukup untuk menentukan '
                       'desain — tanyakan fakta kegiatannya, bukan '
                       'labelnya.']}


# ============================================================
#  Instrumen (lahir dari peta yang sama → data pasti cocok mesin)
# ============================================================

def _nama_kolom(nama_variabel: str) -> str:
    """'Keaslian Streamer' → 'Keaslian' tidak aman; pakai SELURUH nama
    dibersihkan: spasi→garis bawah, buang selain huruf/angka/_. Pola
    ini yang dikenali mesin Statistik Lab (Nama_Variabel_Nomor)."""
    bersih = ''.join(ch if (ch.isalnum() or ch == ' ') else ' '
                     for ch in nama_variabel).split()
    return '_'.join(bersih) or 'Variabel'


def buat_instrumen(peta: dict) -> dict:
    """Susun paket instrumen dari peta yang DISAHKAN:

    - kuesioner: butir per variabel. Teks butir diambil dari
      'indikator' variabel bila ada; bila belum ada, dibuat kerangka
      'Pernyataan ke-i tentang <variabel>' bertanda contoh — TIDAK
      mengarang isi pernyataan (itu pekerjaan peneliti/AI perancang).
    - kolom_template: nama kolom persis pola mesin, urut per variabel.
    - petunjuk: kartu ringkas cara mengisi & menyebar."""
    bagian, kolom = [], []
    for v in peta.get('variabel') or []:
        if not isinstance(v, dict):
            continue
        nama = str(v.get('nama') or '')
        dasar = _nama_kolom(nama)
        indikator = [str(x) for x in (v.get('indikator') or [])]
        # jumlah_butir dari peta TIDAK dipercaya mentah (temuan review
        # Fase 3): teks 'abc' meledakkan int() → 500; negatif membuat
        # kuesioner kosong diam-diam. Nilai aneh → jatuh ke jumlah
        # indikator / bawaan 4; dibatasi wajar 1–20.
        try:
            jumlah = int(v.get('jumlah_butir'))
        except (TypeError, ValueError):
            jumlah = 0
        if jumlah < 1:
            jumlah = len(indikator) or 4
        jumlah = min(jumlah, 20)
        butir = []
        for i in range(1, jumlah + 1):
            kode = f'{dasar}_{i}'
            kolom.append(kode)
            if i <= len(indikator):
                butir.append({'kode': kode, 'teks': indikator[i - 1],
                              'dari_indikator': True})
            else:
                butir.append({'kode': kode,
                              'teks': f'Pernyataan ke-{i} tentang {nama.lower()} '
                                      '(tulis pernyataanmu di sini).',
                              'dari_indikator': False})
        bagian.append({'variabel': nama, 'peran': v.get('peran'),
                       'butir': butir})
    return {
        'kuesioner': bagian,
        'kolom_template': kolom,
        'skala': 'Likert 1–5 (1 = sangat tidak setuju, 5 = sangat setuju)',
        'petunjuk': [
            'Satu baris = satu responden. Satu kolom = satu pernyataan.',
            'Isi hanya angka 1–5. Jawaban kosong biarkan KOSONG '
            '(jangan diisi 0).',
            'Jangan mengubah nama kolom — mesin membacanya dari nama.',
            'Paket yang sama dipakai untuk uji coba (10–30 responden) '
            'dan penyebaran utama.',
        ],
    }


def teks_template_csv(instrumen: dict) -> str:
    """CSV satu baris kepala — template unduhan resmi."""
    return ','.join(instrumen.get('kolom_template') or []) + '\n'


def teks_kuesioner_md(instrumen: dict, judul: str = 'Kuesioner Penelitian') -> str:
    baris = [f'# {judul}', '', f"Skala: {instrumen.get('skala', '')}", '']
    for b in instrumen.get('kuesioner') or []:
        baris.append(f"## {b['variabel']}")
        for bt in b['butir']:
            baris.append(f"- [{bt['kode']}] {bt['teks']}")
        baris.append('')
    return '\n'.join(baris)


# ============================================================
#  Kartu kesehatan (terjemahan manusiawi hasil pra-survei)
# ============================================================

def kartu_kesehatan(hasil_pra: dict) -> dict:
    """Ubah hasil hitung pra-survei (bentuk pintu jembatan Fase 1:
    {variabel: [{nama, butir: [{butir, r, r_kritis, lolos}], alpha,
    lolos_alpha}]}) menjadi kartu sederhana: per variabel
    sehat/perlu-perhatian + daftar butir lemah dengan nasihat
    memperbaiki KATA-KATA butir (bukan menyalahkan responden).
    Mesin yang menghitung; fungsi ini hanya menerjemahkan."""
    kartu, lemah_semua = [], []
    if not isinstance(hasil_pra, dict):
        hasil_pra = {}
    for g in hasil_pra.get('variabel') or []:
        if not isinstance(g, dict):
            continue
        butir = g.get('butir')
        if not isinstance(butir, list):
            butir = []
        lemah = [{'butir': b.get('butir'), 'r': b.get('r'),
                  'r_kritis': b.get('r_kritis')}
                 for b in butir
                 if isinstance(b, dict) and not b.get('lolos')]
        lemah_semua += lemah
        alpha_ok = bool(g.get('lolos_alpha', True))
        sehat = not lemah and alpha_ok
        kartu.append({
            'variabel': g.get('nama'),
            'alpha': g.get('alpha'),
            'sehat': sehat,
            'pesan': ('Semua butir sehat dan kelompoknya konsisten.'
                      if sehat else
                      (f"{len(lemah)} butir lemah — periksa kata-katanya."
                       if lemah else
                       'Butir lolos, tetapi konsistensi kelompoknya '
                       'rendah — periksa lagi pertanyaannya.')),
        })
    return {
        'semua_sehat': not lemah_semua and
                       all(k['sehat'] for k in kartu),
        'butir_lemah': lemah_semua,
        'nasihat': ('Butir lemah biasanya kalimatnya membingungkan atau '
                    'berisi dua pertanyaan sekaligus — perjelas '
                    'kata-katanya, lalu uji lagi ke responden baru.'
                    if lemah_semua else
                    'Kuesioner siap dipakai untuk penyebaran utama.'),
        'per_variabel': kartu,
    }


# ============================================================
#  Deskriptif ringan untuk 4.1/4.2 (dihitung di EduAi sendiri)
# ============================================================

def frekuensi_kolom(baris: list, kolom: list, nama: str) -> dict:
    """Hitung frekuensi nilai satu kolom (profil responden 4.1)."""
    if nama not in kolom:
        return {}
    i = kolom.index(nama)
    hitung: dict[str, int] = {}
    for b in baris:
        if i < len(b) and b[i] not in (None, ''):
            kunci = str(b[i])
            hitung[kunci] = hitung.get(kunci, 0) + 1
    return hitung


def tingkat_pengembalian(masuk: int, target: int | None) -> float | None:
    if not target:
        return None
    return round(masuk / target * 100, 1)


# ============================================================
#  Susun kiriman hitung utama dari peta + data lapangan
# ============================================================

def susun_payload_hitung(peta: dict, kolom: list, tahap: str = 'utama') -> dict:
    """Petakan peran peta ke kontrak jembatan Statistik Lab.

    mode: 'pls' bila peta menyebut metode PLS/SEM, selain itu 'spss'.
    peran dibangun dari daftar variabel peta; kolom butir diambil dari
    awalan nama kolom variabel (pola buat_instrumen)."""
    mode = 'pls' if 'pls' in str(peta.get('metode') or '').lower() \
        or 'sem' in str(peta.get('metode') or '').lower() else 'spss'
    # CATATAN KONTRAK (terbukti di uji Fase 3): pintu jembatan menolak
    # kiriman yang mencampur 'peran' dengan kolom eksplisit — kirim
    # SATU bentuk saja (kolom eksplisit / konstruk).
    import re as _re
    peran, konstruk = {}, {}
    for v in peta.get('variabel') or []:
        if not isinstance(v, dict):
            continue
        dasar = _nama_kolom(str(v.get('nama') or ''))
        # Pola TEGAS (temuan review Fase 3): hanya '<Dasar>_<angka>'
        # yang milik variabel ini. startswith biasa membuat variabel
        # 'Harga' menelan butir 'Harga_Diskon_1' milik variabel lain.
        pola = _re.compile(rf'{_re.escape(dasar)}_\d+$')
        milik = [k for k in kolom if pola.match(k)]
        peran[str(v.get('nama'))] = v.get('peran')
        konstruk[str(v.get('nama'))] = milik
    payload: dict = {'tahap': tahap, 'mode': mode}
    if mode == 'pls':
        y = next((n for n, r in peran.items() if r == 'Y'), None)
        payload['konstruk'] = konstruk
        payload['kolom_y_konstruk'] = y
    else:
        # BUG PALING BERAT (temuan review Fase 3): kontrak mesin SPSS
        # meminta kolom_y SATU nama kolom gabungan — mengirim daftar
        # butir Y membuat SEMUA olah data SPSS ditolak 400. Bentuk
        # yang benar = 'peran' per butir (X1, X2, M1, Z1, Y1 per
        # variabel): mesin menggabungkan butir per variabel jadi skor
        # konstruk dengan aturannya sendiri (skor_konstruk), persis
        # jalur yang dipakai halaman Diagnosis selama ini.
        label = label_peran(peta)
        peran_kolom = {k: label[nama] for nama in peran
                       if nama in label
                       for k in konstruk.get(nama, [])}
        payload['peran'] = peran_kolom
        payload['bentuk_mediasi'] = _bentuk_mediasi(peta)
    return payload


def _bentuk_mediasi(peta: dict) -> str:
    peran = {str(v.get('nama')): v.get('peran')
             for v in (peta.get('variabel') or []) if isinstance(v, dict)}
    if 'M' not in peran.values():
        return 'regresi_biasa'
    langsung_xy = any(
        j.get('jenis') == 'langsung' and
        peran.get(str(j.get('dari'))) == 'X' and
        peran.get(str(j.get('ke'))) == 'Y'
        for j in (peta.get('jalur') or []) if isinstance(j, dict))
    return 'lengkap' if langsung_xy else 'tidak_langsung_saja'


# ============================================================
#  Simulasi placeholder (sebelum bayar): contoh TETAP berlabel
# ============================================================

SIMULASI_CONTOH: dict = {
    'tanda': 'CONTOH TAMPILAN — bukan hasil penelitianmu',
    'model': {'X': ['Kualitas Produk', 'Harga'], 'M': 'Kepuasan',
              'Y': 'Loyalitas'},
    'hasil_ringkasan': {'r2': 0.42,
                        'catatan': 'Ini contoh tampilan. Simulasi dari '
                                   'model penelitianmu sendiri terbuka '
                                   'setelah Paket Olah Data aktif.'},
}


def baris_ke_objek(kolom: list, baris: list) -> list[dict]:
    """Ubah grid (daftar-daftar) menjadi bentuk kontrak jembatan:
    satu OBJEK per responden {nama_kolom: nilai}. Sel kosong/None
    dibuang dari objek (di mesin terbaca sebagai kosong betulan)."""
    objek = []
    for b in baris:
        if isinstance(b, dict):
            # Baris sudah berbentuk objek {kolom: nilai} (bentuk yang
            # wajar dari layar) — saring ke kolom yang dikenal saja.
            objek.append({str(k): v for k, v in b.items()
                          if v not in (None, '')})
            continue
        o = {}
        for i, k in enumerate(kolom):
            if i < len(b) and b[i] not in (None, ''):
                o[str(k)] = b[i]
        objek.append(o)
    return objek


# ============================================================
#  Pemeta hasil → hipotesis (BUG BARU 1 review Fase 3)
# ============================================================

def label_peran(peta: dict) -> dict[str, str]:
    """Label mesin per variabel: {nama: 'X1'|'X2'|'M1'|'Z1'|'Y1'}.

    Urutan mengikuti daftar variabel di peta. Label inilah yang
    dikirim ke mesin (bentuk peran SPSS) dan yang muncul di hasil
    mesin ('koef', 'kaitan') — pemeta hipotesis memakainya untuk
    menyambungkan hasil kembali ke H1..Hn milik peneliti."""
    label: dict[str, str] = {}
    nomor: dict[str, int] = {}
    for v in peta.get('variabel') or []:
        if not isinstance(v, dict):
            continue
        r = v.get('peran')
        if r not in ('X', 'M', 'Z', 'Y'):
            continue
        nomor[r] = nomor.get(r, 0) + 1
        label[str(v.get('nama'))] = f'{r}{nomor[r]}'
    return label


def _sig(p) -> bool | None:
    try:
        return float(p) < 0.05
    except (TypeError, ValueError):
        return None


def petakan_hasil_ke_hipotesis(peta: dict, hasil: dict) -> list[dict]:
    """Sambungkan hasil mentah mesin ke hipotesis peta (H1..Hn).

    TANPA fungsi ini hasil mesin tidak bisa dipakai narasi: mesin
    melaporkan jalur per label (X1→Y1 dst), peneliti berpikir per
    hipotesis. Keluaran per jalur peta: {hipotesis, dari, ke, jenis,
    ketemu, b, p, signifikan, ringkas}. Jalur yang tidak ditemukan di
    hasil ditandai ketemu=False — JANGAN ditebak angkanya."""
    label = label_peran(peta)
    mode = str((hasil or {}).get('mode') or '')
    koef: dict[str, dict] = {}
    mediasi: dict[tuple, dict] = {}
    moderasi: dict[tuple, dict] = {}
    jalur_pls: dict[tuple, dict] = {}
    mediasi_pls: dict[tuple, dict] = {}
    if mode == 'pls':
        for j in hasil.get('jalur') or []:
            jalur_pls[(str(j.get('dari')), str(j.get('ke')))] = j
        for m in hasil.get('mediasi') or []:
            mediasi_pls[(str(m.get('dari')), str(m.get('lewat')),
                         str(m.get('ke')))] = m
    else:
        for k in hasil.get('koef') or []:
            koef[str(k.get('nama'))] = k
        for m in (hasil.get('kaitan') or {}).get('mediasi') or []:
            mediasi[(str(m.get('x')), str(m.get('m')), str(m.get('y')))] = m
        for m in (hasil.get('kaitan') or {}).get('moderasi') or []:
            moderasi[(str(m.get('x')), str(m.get('z')), str(m.get('y')))] = m

    keluar: list[dict] = []
    for j in peta.get('jalur') or []:
        if not isinstance(j, dict):
            continue
        dari, ke = str(j.get('dari')), str(j.get('ke'))
        entri: dict = {'hipotesis': j.get('hipotesis'), 'dari': dari,
                       'ke': ke, 'jenis': j.get('jenis'),
                       'ketemu': False, 'b': None, 'p': None,
                       'signifikan': None, 'ringkas': ''}
        if mode == 'pls':
            if j.get('jenis') == 'tidak_langsung':
                m = mediasi_pls.get((dari, str(j.get('lewat')), ke))
                if m:
                    entri.update(ketemu=True, b=m.get('efek'), p=m.get('p'),
                                 signifikan=_sig(m.get('p')))
            else:
                jj = jalur_pls.get((dari, ke))
                if jj:
                    entri.update(ketemu=True, b=jj.get('koef'),
                                 p=jj.get('p'), signifikan=_sig(jj.get('p')))
        elif j.get('jenis') == 'tidak_langsung':
            m = mediasi.get((label.get(dari, ''), label.get(str(j.get('lewat')), ''),
                             label.get(ke, '')))
            if m and isinstance(m.get('tidak_langsung'), dict):
                tl = m['tidak_langsung']
                sig = _sig(tl.get('p'))
                if sig is None and tl.get('lo') is not None and tl.get('hi') is not None:
                    sig = not (float(tl['lo']) <= 0 <= float(tl['hi']))
                entri.update(ketemu=True, b=tl.get('b'), p=tl.get('p'),
                             signifikan=sig)
        elif j.get('jenis') == 'interaksi':
            cocok = [m for (x, z, y), m in moderasi.items()
                     if z == label.get(dari, '') and y == label.get(ke, '')]
            if cocok:
                m = cocok[0]
                di = (m.get('dengan_interaksi') or {})
                inter = di.get('interaksi') or {}
                # Mesin SUDAH menyediakan angka interaksi lengkap
                # (b, t, p), delta_r2, jenis, arah, dan kalimat —
                # ambil semuanya (temuan review: versi lama hanya
                # mengambil r2, menyisakan hipotesis moderasi kosong).
                entri.update(
                    ketemu=True, b=inter.get('b'), p=inter.get('p'),
                    signifikan=_sig(inter.get('p')),
                    delta_r2=m.get('delta_r2'),
                    jenis_moderasi=m.get('jenis'), arah=m.get('arah'),
                    kalimat_mesin=m.get('kalimat'),
                    ringkas=m.get('kalimat') or '')
        else:  # langsung
            # Presisi (temuan review): 'koef' mesin dibulatkan 4
            # desimal, 'kaitan' presisi penuh. Untuk model ber-mediasi
            # ambil angka jalur langsung dari kaitan (c' untuk X→Y,
            # b untuk M→Y) supaya SATU laporan tidak mencampur dua
            # presisi. Tanpa mediasi, koef adalah satu-satunya sumber.
            sumber, asal = None, None
            ld, lk = label.get(dari, ''), label.get(ke, '')
            if lk.startswith('Y'):
                if ld.startswith('M'):
                    m = next((mm for (x, mm_, y), mm in mediasi.items()
                              if mm_ == ld and y == lk), None)
                    if m:
                        sumber, asal = m.get('b'), 'kaitan'
                if sumber is None:
                    m = next((mm for (x, mm_, y), mm in mediasi.items()
                              if x == ld and y == lk), None)
                    if m:
                        sumber, asal = m.get('cp'), 'kaitan'
                if sumber is None:
                    sumber, asal = koef.get(ld), 'koef'
            elif lk.startswith('M'):
                m = mediasi.get((ld, lk,
                                 next((lb for nm, lb in label.items()
                                       if lb.startswith('Y')), '')))
                sumber, asal = (m or {}).get('a'), 'kaitan'
            if sumber:
                entri.update(ketemu=True, b=sumber.get('b'),
                             p=sumber.get('p'),
                             signifikan=_sig(sumber.get('p')),
                             sumber=asal)
        if entri['ketemu'] and not entri['ringkas']:
            entri['ringkas'] = (f"{entri['hipotesis']}: b={entri['b']}, "
                                f"p={entri['p']} → "
                                f"{'signifikan' if entri['signifikan'] else 'tidak signifikan'}")
        keluar.append(entri)
    return keluar
