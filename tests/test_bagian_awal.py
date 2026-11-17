#!/usr/bin/env python3
"""Uji Lengkapi Bagian Awal skripsi (16 Nov 2026, GAS Bos 14:17 WIB).

Jalankan `python3 tests/test_bagian_awal.py`, keluar 0 bila semua lulus.
Memakai model asli + DB sqlite sementara (EDUAI_DATA_DIR), DB produksi
tidak tersentuh. TIDAK ada panggilan AI sungguhan dan TIDAK ada panggilan
jaringan sungguhan di uji ini (semua sumber dipalsukan dengan fungsi
suntik / penanya suntik); satu-satunya HTTP nyata adalah TIDAK ADA.

Aturan yang diuji (RENCANA_BAGIAN_AWAL.md):
  1. Keadaan tombol di tiap tahap (Bab I-III belum selesai / belum
     diperiksa / sudah diperiksa / sudah ditempel).
  2. Tooltip ada dan benar di tiap keadaan (aktif, nonaktif karena Bab
     belum selesai, nonaktif karena belum diperiksa, mode Perbarui):
     maksud tombol + kapan muncul + alasan saat nonaktif.
  3. Form boleh kosong dan tersimpan; NIP dicek format 18 angka saja.
  4. Daftar cek menandai yang kurang + judul bentrok; abstrak tidak
     ditagih di tahap proposal, muncul di tahap final.
  5. Harga 2 token buat dan update, 6 token abstrak, kembali bila AI gagal.
  6. ATURAN KUNCI: Kata Pengantar mahasiswa tetap utuh sesudah update
     (termasuk bila mahasiswa mengubahnya di naskah), halaman yang
     dihapus ditawarkan kembali, halaman baru tidak disentuh, daftar
     dibuat ulang dengan nomor halaman yang benar.
  7. Penomoran Romawi (bagian awal) lalu Arab mulai 1 (Bab I).
  8. Dua versi Persetujuan (proposal vs final); urutan 13 halaman.
  9. Ukur nomor pakai OnlyOffice ConvertService (17 Nov 2026, GAS Bos):
     render sama dengan editor (191 halaman, bukan WordCraft 247),
     XML jawaban diparse, host FileUrl ditulis ulang, FileUrl
     kedaluwarsa, paksa simpan bila disunting, gagal dengan jujur
     (nomor lama dipertahankan), jalan di pekerja latar.
"""
import os
import sys
import tempfile
import time
from pathlib import Path

TMP = tempfile.mkdtemp(prefix='eduai_bagian_awal_')
os.environ['EDUAI_DATA_DIR'] = TMP
os.environ['EDUAI_UPLOAD_DIR'] = os.path.join(TMP, 'uploads')
# Kunci palsu untuk uji saja (DB sementara, bukan produksi).
os.environ.setdefault('EDUAI_SECRET_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_ROUTER_KEY', 'uji-sementara-bukan-rahasia')
os.environ.setdefault('EDUAI_OO_JWT_SECRET', 'uji-jwt-sementara')

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LULUS = []
GAGAL = []


def cek(nama, benar, info=''):
    (LULUS if benar else GAGAL).append(nama)
    print(('  LULUS  ' if benar else '  GAGAL  ') + nama
          + (f'  [{info}]' if info and not benar else ''))


class _ReqPalsu:
    """Peniru Request: .json() + .cookies + .headers + .query_params."""

    def __init__(self, body=None, query=None):
        self._body = dict(body or {})
        self.cookies = {}
        self.headers = {}
        self.query_params = dict(query or {})

    async def json(self):
        return self._body


class _FormPalsu(dict):
    def getlist(self, kunci):
        nilai = self.get(kunci)
        if nilai is None:
            return []
        return nilai if isinstance(nilai, list) else [nilai]


class _ReqForm(_ReqPalsu):
    def __init__(self, form=None, query=None):
        super().__init__(None, query)
        self._form = _FormPalsu(form or {})

    async def form(self):
        return self._form


from app import bagian_awal as BA

TEKS_BAB123 = (
    'BAB I\nPENDAHULUAN\n1.1 Latar Belakang\nIsi latar belakang.\n\n'
    'BAB II\nTINJAUAN PUSTAKA\n2.1 Teori tentang Variabel Y\nIsi teori.\n\n'
    'BAB III\nMETODE PENELITIAN\n3.1 Jenis dan Desain Penelitian\nIsi metode.\n'
)

PETA_BAB123 = {
    'peta_surveyor': {
        'baris': ['BAB I', 'PENDAHULUAN', '1.1 Latar Belakang',
                  'BAB II', 'TINJAUAN PUSTAKA', '2.1 Teori tentang Variabel Y',
                  'BAB III', 'METODE PENELITIAN', '3.1 Jenis dan Desain Penelitian'],
        'label': {'0': 'bab', '1': 'bab', '2': 'subbab', '3': 'bab',
                  '4': 'bab', '5': 'subbab', '6': 'bab', '7': 'bab',
                  '8': 'subbab'},
    },
    'hakim': {'jumlah_ragu': 0, 'jumlah_curiga': 0},
}


def jalankan():
    # ── 1. Keadaan tombol ─────────────────────────────────────────────
    k = BA.keadaan_tombol(set(), False, False)
    cek('tombol: Bab belum selesai -> nonaktif + alasan',
        k['keadaan'] == 'nonaktif_belum_selesai' and not k['aktif']
        and k['alasan'] == 'Selesaikan Bab I sampai III dulu, bagian awal untuk ujian proposal.',
        str(k))
    k = BA.keadaan_tombol({1, 2, 3}, False, False)
    cek('tombol: Bab selesai belum diperiksa -> nonaktif + alasan',
        k['keadaan'] == 'nonaktif_belum_periksa' and not k['aktif']
        and k['alasan'] == 'Periksa Struktur dulu.', str(k))
    k = BA.keadaan_tombol({1, 2, 3}, True, False)
    cek('tombol: sudah diperiksa -> aktif, label Lengkapi',
        k['keadaan'] == 'aktif' and k['aktif']
        and k['label'] == 'Lengkapi Bagian Awal', str(k))
    k = BA.keadaan_tombol({1, 2, 3, 4, 5}, True, True)
    cek('tombol: sudah ditempel -> Perbarui',
        k['keadaan'] == 'perbarui' and k['aktif']
        and k['label'] == 'Perbarui Bagian Awal', str(k))
    k = BA.keadaan_tombol({1, 2}, True, False)
    cek('tombol: Bab III belum ada -> belum selesai (bukan belum diperiksa)',
        k['keadaan'] == 'nonaktif_belum_selesai', str(k))

    # ── 2. Tooltip tiap keadaan ───────────────────────────────────────
    for keadaan, wajib in (
            ('nonaktif_belum_selesai',
             ['bagian depan skripsi', 'Bab I sampai III', 'ujian proposal',
              'belum selesai']),
            ('nonaktif_belum_periksa',
             ['bagian depan skripsi', 'Bab I sampai III', 'ujian proposal',
              'Periksa Struktur']),
            ('aktif',
             ['bagian depan skripsi', 'Bab I sampai III', 'ujian proposal',
              '2 token']),
            ('perbarui',
             ['Memperbarui bagian depan', '2 token',
              'dipertahankan', 'tahap final'])):
        teks = BA.tooltip_tombol(keadaan)
        cek(f'tooltip: {keadaan} menjelaskan maksud + kapan + alasan',
            all(w in teks for w in wajib), teks[:120])
    cek('tooltip: umum menjelaskan maksud + kapan muncul',
        'bagian depan skripsi' in BA.TOOLTIP_TOMBOL_UMUM
        and 'Bab I sampai III' in BA.TOOLTIP_TOMBOL_UMUM
        and 'ujian proposal' in BA.TOOLTIP_TOMBOL_UMUM)
    cek('tooltip: daftar isi/tabel/gambar/lampiran disebut di tooltip aktif',
        'daftar isi' in BA.tooltip_tombol('aktif')
        and 'abstrak hanya di tahap final' in BA.tooltip_tombol('aktif').lower())

    # ── 3. Bab dari teks / peta + tahap ───────────────────────────────
    cek('bab teks: BAB I-III terdeteksi',
        BA.bab_dari_teks(TEKS_BAB123) == {1, 2, 3},
        str(BA.bab_dari_teks(TEKS_BAB123)))
    cek('bab teks: hanya BAB I',
        BA.bab_dari_teks('BAB I\nPENDAHULUAN\nIsi.') == {1})
    teks_toc = ('DAFTAR ISI\nBAB I PENDAHULUAN .... 1\nBAB II TINJAUAN PUSTAKA .... 5\n'
                'BAB I\nPENDAHULUAN\nIsi bab satu.')
    cek('bab teks: baris daftar isi tidak dihitung sebagai bab',
        BA.bab_dari_teks(teks_toc) == {1},
        str(BA.bab_dari_teks(teks_toc)))
    cek('bab peta: BAB I-III dari peta tersimpan',
        BA.bab_dari_peta(PETA_BAB123) == {1, 2, 3},
        str(BA.bab_dari_peta(PETA_BAB123)))
    cek('bab peta: peta rusak -> kosong, bukan galat',
        BA.bab_dari_peta('{rusak') == set())
    cek('tahap: Bab I-III -> proposal', BA.tahap_dari_bab({1, 2, 3}) == 'proposal')
    cek('tahap: Bab IV ada -> final', BA.tahap_dari_bab({1, 2, 3, 4}) == 'final')
    cek('tahap: Bab VI ada -> final', BA.tahap_dari_bab({1, 2, 3, 5, 6}) == 'final')

    # ── 4. Form: boleh kosong, NIP 18 angka ──────────────────────────
    cek('form: kosong semua tetap bersih (boleh kosong)',
        BA.bersihkan_data({})['nama'] == ''
        and len(BA.bersihkan_data({})) == len(BA.KUNCI_FORM) + 1)
    cek('form: spasi dirapikan',
        BA.bersihkan_data({'nama': '  Siti Aminah  '})['nama'] == 'Siti Aminah')
    cek('nip: kosong boleh', BA.cek_nip('') is True)
    cek('nip: 18 angka lulus', BA.cek_nip('198501012010011001') is True)
    cek('nip: 17 angka gagal', BA.cek_nip('19850101201001100') is False)
    cek('nip: titik/spasi diabaikan, 18 angka tetap lulus',
        BA.cek_nip('1985.0101.2010.011001') is True)
    per = BA.peringatan_form({'pembimbing_nip': '123'})
    cek('form: NIP salah format diperingatkan',
        len(per) == 1 and 'NIP pembimbing' in per[0] and '18 angka' in per[0],
        str(per))
    cek('form: NIP benar tanpa peringatan',
        BA.peringatan_form({'pembimbing_nip': '198501012010011001'}) == [])

    # ── 5. Daftar cek ─────────────────────────────────────────────────
    cek_proposal = BA.daftar_cek({}, {'tahap': 'proposal', 'bagian_ada': set(),
                                      'judul_naskah': '', 'abstrak_ada': False,
                                      'kata_pengantar_ada': False})
    abstrak_proposal = [c for c in cek_proposal
                        if c['kunci'] in ('abstract', 'abstrak')]
    cek('cek: abstrak TIDAK ditagih di tahap proposal',
        len(abstrak_proposal) == 2
        and all('tahap final' in c['catatan'] for c in abstrak_proposal),
        str(abstrak_proposal))
    cek_final = BA.daftar_cek({}, {'tahap': 'final', 'bagian_ada': set(),
                                   'judul_naskah': '', 'abstrak_ada': False,
                                   'kata_pengantar_ada': False})
    abstrak_final = [c for c in cek_final if c['kunci'] in ('abstract', 'abstrak')]
    cek('cek: abstrak ditagih di tahap final (dengan harga AI)',
        len(abstrak_final) == 2
        and all('6 token' in c['catatan'] for c in abstrak_final),
        str(abstrak_final))
    cek_bentrok = BA.daftar_cek(
        {'judul': 'Pengaruh A terhadap B'},
        {'tahap': 'proposal', 'bagian_ada': set(),
         'judul_naskah': 'Pengaruh X terhadap Y', 'abstrak_ada': False,
         'kata_pengantar_ada': False})
    bentrok = [c for c in cek_bentrok if c['kunci'] == 'judul_bentrok']
    cek('cek: judul bentrok ditandai, mahasiswa memilih yang benar',
        len(bentrok) == 1 and 'pilih yang benar' in bentrok[0]['catatan'],
        str(bentrok))
    cek_sama = BA.daftar_cek(
        {'judul': 'Pengaruh X terhadap Y'},
        {'tahap': 'proposal', 'bagian_ada': set(),
         'judul_naskah': 'Pengaruh X terhadap Y', 'abstrak_ada': False,
         'kata_pengantar_ada': False})
    cek('cek: judul sama tidak ditandai bentrok',
        not any(c['kunci'] == 'judul_bentrok' for c in cek_sama))
    cek_kurang = BA.daftar_cek({}, {'tahap': 'proposal', 'bagian_ada': set(),
                                    'judul_naskah': '', 'abstrak_ada': False,
                                    'kata_pengantar_ada': False})
    nama = [c for c in cek_kurang if c['kunci'] == 'nama'][0]
    cek('cek: data kosong ditandai belum lengkap (bukan ditolak)',
        nama['ada'] is False and 'Belum diisi' in nama['catatan'], str(nama))

    # ── 6. Harga ──────────────────────────────────────────────────────
    cek('harga: buat 2 token', BA.HARGA_BUAT == 2)
    cek('harga: update 2 token', BA.HARGA_UPDATE == 2)
    cek('harga: abstrak 6 token', BA.HARGA_ABSTRAK == 6)

    # ── 7. Sidik + baca bagian awal ───────────────────────────────────
    cek('sidik: sama -> sama, beda -> beda',
        BA.sidik_bagian(['a', 'b']) == BA.sidik_bagian(['a', 'b'])
        and BA.sidik_bagian(['a', 'b']) != BA.sidik_bagian(['a', 'c']))
    paragraf = ['KATA PENGANTAR', 'Puji syukur saya panjatkan.',
                'DAFTAR ISI', 'BAB I PENDAHULUAN',
                'BAB I', 'PENDAHULUAN', 'Isi bab satu.']
    baca = BA.baca_bagian_awal(paragraf)
    cek('baca: kata pengantar + daftar isi terbaca, berhenti di Bab I',
        baca['bagian'].get('kata_pengantar') == ['Puji syukur saya panjatkan.']
        and baca['bagian'].get('daftar_isi') == ['BAB I PENDAHULUAN']
        and baca['idx_bab1'] == 4, str(baca))
    paragraf_tambahan = ['Catatan pribadi saya.', 'KATA PENGANTAR', 'Isi.',
                         'BAB I', 'Isi bab.']
    baca2 = BA.baca_bagian_awal(paragraf_tambahan)
    cek('baca: blok tak bernama masuk tambahan (tidak disentuh)',
        len(baca2['tambahan']) == 1
        and baca2['tambahan'][0] == ['Catatan pribadi saya.'], str(baca2))
    cek('baca: baris daftar isi bukan Bab I',
        BA.cari_indeks_bab1(['DAFTAR ISI', 'BAB I PENDAHULUAN .... 1',
                             'BAB I', 'Isi']) == 2)
    # Regresi berkas 126 (uji live 16 Nov 2026): entri Daftar Isi
    # berjudul huruf campuran tidak terhitung _nomor_bab, jadi aturan
    # ulang tidak menyala; blok Daftar Isi terakhir langsung sebelum
    # judul badan 'BAB 1' telanjang. Baris telanjang adalah badan.
    cek('cari: entri Daftar Isi huruf campuran + BAB 1 telanjang sesudah blok daftar',
        BA.cari_indeks_bab1(['DAFTAR ISI',
                             'BAB 1. Lanskap Pemasaran Digital: Ruang Lingkup, Batasan, dan Fondasi Konseptual',
                             'BAB 2. Arsitektur Strategi Pemasaran Digital dan Dinamika Platform',
                             'BAB 1', 'PENDAHULUAN', 'Isi.']) == 3)
    cek('cari: dua blok Daftar Isi, yang terakhir langsung sebelum BAB 1 telanjang',
        BA.cari_indeks_bab1(['DAFTAR ISI', 'BAB 1. Pendahuluan',
                             'DAFTAR TABEL', 'Tabel 1.1 Jenis Data',
                             'DAFTAR ISI', 'BAB 1. Pendahuluan',
                             'BAB 2. Tinjauan Pustaka',
                             'BAB 1', 'PENDAHULUAN']) == 7)
    cek('cari: BAB 1 telanjang tetap badan walau tanpa blok daftar',
        BA.cari_indeks_bab1(['KATA PENGANTAR', 'Isi.', 'BAB 1',
                             'PENDAHULUAN']) == 2)
    cek('baca: tanpa Bab I -> idx None, seluruh jadi depan',
        BA.baca_bagian_awal(['KATA PENGANTAR', 'Isi.'])['idx_bab1'] is None)

    # ── 8. Rencana update (aturan kunci) ──────────────────────────────
    data_lama = {'nama': 'Siti Aminah', 'nim': '112310001', 'judul': 'Judul A'}
    data_baru = {'nama': 'Siti Aminah', 'nim': '112310001', 'judul': 'Judul A'}
    baca_r = {'bagian': {
        'kata_pengantar': ['Kata pengantar tulisan saya sendiri.'],
        'sampul': ['Fakultas Ekonomi dan Bisnis', 'Judul A'],
        'daftar_isi': ['BAB I PENDAHULUAN'],
    }, 'tambahan': [['Blok rahasia saya.']], 'tambahan_indeks': [[99]],
              'indeks': {}, 'idx_bab1': 9}
    sidik_lama = {
        'kata_pengantar': BA.sidik_bagian(['Kata pengantar AI lama.']),
        'sampul': BA.sidik_bagian(['Fakultas Ekonomi dan Bisnis', 'Judul A']),
        'daftar_isi': BA.sidik_bagian(['BAB I PENDAHULUAN']),
        'persembahan': BA.sidik_bagian(['']),
    }
    ren = BA.rencana_update(data_baru, data_lama, baca_r, sidik_lama, 'proposal')
    kp = [d for d in ren['dipertahankan'] if d['kunci'] == 'kata_pengantar']
    cek('rencana: kata pengantar yang diubah mahasiswa dipertahankan',
        len(kp) == 1 and 'tetap utuh' in kp[0]['catatan'], str(ren))
    cek('rencana: daftar isi selalu dibuat ulang',
        any(d['kunci'] == 'daftar_isi' for d in ren['dibuat_ulang']), str(ren))
    cek('rencana: sampul tak berubah + tak disentuh -> dipertahankan',
        any(d['kunci'] == 'sampul' for d in ren['dipertahankan']), str(ren))
    cek('rencana: halaman yang dihapus ditawarkan kembali',
        any(d['kunci'] == 'persembahan' for d in ren['kembalikan']), str(ren))
    cek('rencana: blok tambahan mahasiswa dipertahankan',
        any(d['kunci'] == 'tambahan_0' for d in ren['dipertahankan']), str(ren))
    data_ubah = dict(data_baru, nama='Siti Aminah Baru')
    ren2 = BA.rencana_update(data_ubah, data_lama, baca_r, sidik_lama, 'proposal')
    cek('rencana: data form berubah + sampul tak disentuh -> berubah',
        any(d['kunci'] == 'sampul' for d in ren2['berubah']), str(ren2))
    # Sampul yang disentuh tangan: data berubah pun tidak menimpa.
    baca_r3 = {'bagian': {
        'sampul': ['Fakultas Ekonomi dan Bisnis', 'Judul A (edit tangan)'],
    }, 'tambahan': [], 'tambahan_indeks': [], 'indeks': {}, 'idx_bab1': 5}
    ren3 = BA.rencana_update(data_ubah, data_lama, baca_r3, sidik_lama, 'proposal')
    cek('rencana: sampul edit tangan dipertahankan walau data berubah',
        any(d['kunci'] == 'sampul' and 'diubah tangan' in d['catatan']
            for d in ren3['dipertahankan']), str(ren3))

    # ── 9. Susun bagian ───────────────────────────────────────────────
    data_penuh = {'nama': 'Siti Aminah', 'nim': '112310001',
                  'prodi': 'Manajemen', 'fakultas': 'Ekonomi dan Bisnis',
                  'kota': 'Bekasi', 'tahun': '2026', 'judul': 'Judul Skripsi Saya',
                  'pembimbing_nama': 'Dr. Budi, M.M.',
                  'pembimbing_nip': '198501012010011001',
                  'kaprodi_nama': 'Dr. Yunita, M.Sc.', 'kaprodi_nip': '',
                  'penguji1_nama': '', 'penguji2_nama': '',
                  'dekan_nama': '', 'rektor_nama': '', 'tanggal_sidang': ''}
    susun_p = BA.susun_bagian(data_penuh, 'proposal', {})
    kunci_p = [k for k, _, _ in susun_p]
    cek('susun: proposal 11 halaman (tanpa abstract/abstrak)',
        len(susun_p) == 11 and 'abstract' not in kunci_p
        and 'abstrak' not in kunci_p, str(kunci_p))
    cek('susun: urutan ikut Pedoman (sampul dulu, daftar isi sesudah pengantar)',
        kunci_p.index('sampul') == 0
        and kunci_p.index('kata_pengantar') < kunci_p.index('daftar_isi')
        and kunci_p.index('daftar_isi') < kunci_p.index('daftar_tabel'),
        str(kunci_p))
    persetujuan_p = [b for k, _, b in susun_p if k == 'persetujuan'][0]
    cek('susun: proposal pakai Persetujuan Proposal',
        any('PROPOSAL' in b for b in persetujuan_p), str(persetujuan_p))
    susun_f = BA.susun_bagian(data_penuh, 'final', {}, abstrak={
        'id': ['Abstrak isi.'], 'en': ['Abstract text.'],
        'kunci_id': ['a', 'b'], 'kunci_en': ['a', 'b']})
    kunci_f = [k for k, _, _ in susun_f]
    cek('susun: final 13 halaman (dengan abstract/abstrak)',
        len(susun_f) == 13 and kunci_f[-2:] == ['abstract', 'abstrak'],
        str(kunci_f))
    persetujuan_f = [b for k, _, b in susun_f if k == 'persetujuan'][0]
    cek('susun: final pakai Persetujuan tanpa kata Proposal',
        all('PROPOSAL' not in b for b in persetujuan_f), str(persetujuan_f))
    pengesahan = [b for k, _, b in susun_p if k == 'pengesahan'][0]
    cek('susun: kolom kosong jadi garis kosong (bukan teks galat)',
        any(b == 'NIP : ' for b in pengesahan)
        and any(b == 'Telah diuji pada tanggal ' for b in pengesahan)
        and not any('None' in b or '...' in b
                    for _, _, bb in susun_p for b in bb),
        str(pengesahan))
    sampul = [b for k, _, b in susun_p if k == 'sampul'][0]
    cek('susun: sampul memuat judul, nama, kota tahun',
        'JUDUL SKRIPSI SAYA' in sampul and 'Siti Aminah' in sampul
        and 'Bekasi, 2026' in sampul, str(sampul))

    # ── 10. Entri daftar + nomor halaman render ───────────────────────
    entri = BA.entri_daftar_isi(PETA_BAB123)
    cek('entri: daftar isi dari peta (bab + subbab)',
        [e['judul'] for e in entri] == [
            'BAB I', 'PENDAHULUAN', '1.1 Latar Belakang', 'BAB II',
            'TINJAUAN PUSTAKA', '2.1 Teori tentang Variabel Y', 'BAB III',
            'METODE PENELITIAN', '3.1 Jenis dan Desain Penelitian']
        and all(e['halaman'] is None for e in entri), str(entri))
    render = ['Sampul halaman satu', 'BAB I PENDAHULUAN isi bab satu',
              'BAB II TINJAUAN PUSTAKA isi bab dua',
              'BAB III METODE PENELITIAN isi bab tiga']
    cek('render: nomor halaman nyata dari render',
        BA.nomor_halaman_dari_render(render, 'BAB II TINJAUAN PUSTAKA') == 3
        and BA.nomor_halaman_dari_render(render, 'BAB III METODE PENELITIAN') == 4)
    cek('render: judul tak ketemu -> None (tidak dikarang)',
        BA.nomor_halaman_dari_render(render, 'BAB IV HASIL') is None
        and BA.nomor_halaman_dari_render(None, 'BAB I') is None)
    ket = BA.entri_daftar_keterangan(
        ['Tabel 1.1 Jenis Data', 'Gambar 2.1 Model Penelitian',
         'Lampiran 1 Kuesioner', 'Kalimat biasa.'])
    cek('entri: tabel/gambar/lampiran dari keterangan naskah',
        len(ket['daftar_tabel']) == 1 and len(ket['daftar_gambar']) == 1
        and len(ket['daftar_lampiran']) == 1, str(ket))

    # ── 11. Draf AI (penanya suntik, tanpa jaringan) ──────────────────
    def _penanya_kp(prompt):
        assert 'Kata Pengantar' in prompt or 'KATA PENGANTAR' in prompt.upper()
        return 'Paragraf satu pengantar.\nParagraf dua pengantar.'
    kp = BA.draf_kata_pengantar(data_penuh, {'latar': 'Latar.'},
                                penanya=_penanya_kp)
    cek('ai: draf kata pengantar dari penanya',
        kp == ['Paragraf satu pengantar.', 'Paragraf dua pengantar.'], str(kp))
    cek('ai: penanya gagal -> None (pemanggil mengembalikan token)',
        BA.draf_kata_pengantar(data_penuh, {}, penanya=lambda p: 1 / 0) is None)

    def _penanya_abs(prompt):
        return ('ABSTRAK:\nPenelitian ini membahas X. Hasilnya Y.\n'
                'KATA KUNCI: X, Y, Z\n'
                'ABSTRACT:\nThis study discusses X. The result is Y.\n'
                'KEYWORDS: X, Y, Z')
    abs_draf = BA.draf_abstrak(data_penuh, {'latar': 'L', 'hasil': 'H'},
                               penanya=_penanya_abs)
    cek('ai: draf abstrak lengkap dua bahasa terurai',
        abs_draf is not None
        and abs_draf['id'] == ['Penelitian ini membahas X. Hasilnya Y.']
        and abs_draf['en'] == ['This study discusses X. The result is Y.']
        and abs_draf['kunci_id'] == ['X', 'Y', 'Z']
        and abs_draf['kunci_en'] == ['X', 'Y', 'Z'], str(abs_draf))
    cek('ai: balasan tanpa ABSTRACT -> None',
        BA.urai_draf_abstrak('ABSTRAK:\nHanya Indonesia.') is None)
    cek('ai: tanya_draf gagal semua -> None',
        BA.tanya_draf('halo', penanya=lambda p: (_ for _ in ()).throw(
            RuntimeError('putus'))) is None)
    cup = BA.cuplikan_naskah(TEKS_BAB123 + '\nBAB IV\nHASIL\nHasil uji.\n\n'
                             'BAB V\nPENUTUP\nSimpulan.')
    cek('ai: cuplikan mengambil Bab I, IV, V',
        'Latar Belakang' in cup['latar'] and 'Hasil uji' in cup['hasil']
        and 'Simpulan' in cup['penutup'], str(cup))

    # ── 12. Tulis .docx + penomoran Romawi/Arab ────────────────────────
    from docx import Document as _Docx

    def _buat_naskah(jalur, kp_teks='Kata pengantar AI lama.'):
        d = _Docx()
        d.add_paragraph('BAB I')
        d.add_paragraph('PENDAHULUAN')
        d.add_paragraph('1.1 Latar Belakang')
        d.add_paragraph('Isi latar belakang penelitian ini.')
        d.add_paragraph('BAB II')
        d.add_paragraph('TINJAUAN PUSTAKA')
        d.add_paragraph('2.1 Teori tentang Variabel Y')
        d.add_paragraph('Isi teori.')
        d.add_paragraph('BAB III')
        d.add_paragraph('METODE PENELITIAN')
        d.add_paragraph('3.1 Jenis dan Desain Penelitian')
        d.add_paragraph('Isi metode.')
        d.add_paragraph('Tabel 1.1 Jenis Data')
        d.add_paragraph('Gambar 2.1 Model Penelitian')
        d.save(str(jalur))
        return jalur

    def _teks_docx(jalur):
        from app.ai import _teks_dari_docx
        return _teks_dari_docx(Path(jalur))

    def _xml_docx(jalur):
        import zipfile
        with zipfile.ZipFile(jalur) as z:
            return z.read('word/document.xml').decode('utf-8')

    docx1 = Path(TMP) / 'naskah1.docx'
    _buat_naskah(docx1)
    bagian_awal = BA.susun_bagian(
        {'nama': 'Siti Aminah', 'nim': '112310001', 'prodi': 'Manajemen',
         'fakultas': 'Ekonomi dan Bisnis', 'kota': 'Bekasi', 'tahun': '2026',
         'judul': 'Judul Skripsi Saya', 'pembimbing_nama': 'Dr. Budi, M.M.',
         'pembimbing_nip': '198501012010011001', 'kaprodi_nama': '',
         'penguji1_nama': '', 'penguji2_nama': '', 'dekan_nama': '',
         'rektor_nama': '', 'tanggal_sidang': ''},
        'proposal', {'daftar_isi': BA.entri_daftar_isi(PETA_BAB123)},
        kata_pengantar=['Kata pengantar AI lama.'])
    tulis = BA.tulis_bagian_awal(docx1, [
        {'kunci': k, 'judul': j, 'baris': b, 'xml': None, 'ppr': ''}
        for k, j, b in bagian_awal])
    teks1 = _teks_docx(docx1)
    cek('docx: tempel berhasil, badan utuh sesudah tempel',
        tulis.get('ok') and 'Isi latar belakang penelitian ini.' in teks1
        and 'Isi metode.' in teks1, str(tulis))
    cek('docx: bagian depan di depan Bab I',
        teks1.index('Siti Aminah') < teks1.index('BAB I')
        and teks1.index('KATA PENGANTAR') < teks1.index('BAB I'), teks1[:200])
    xml1 = _xml_docx(docx1)
    cek('docx: pemutus bagian Romawi di akhir bagian depan',
        'lowerRoman' in xml1, xml1[-500:])
    cek('docx: badan Arab mulai 1',
        'w:fmt="decimal"' in xml1 and 'w:start="1"' in xml1)
    cek('docx: 11 halaman proposal tertulis',
        all(judul in teks1 for judul in
            ['KATA PENGANTAR', 'DAFTAR ISI', 'DAFTAR TABEL', 'DAFTAR GAMBAR'])
        and 'ABSTRAK' not in teks1, teks1[:300])

    # Update: Kata Pengantar diubah tangan di naskah, lalu update.
    d_edit = _Docx(str(docx1))
    for p in d_edit.paragraphs:
        if p.text == 'Kata pengantar AI lama.':
            p.text = 'Kata pengantar tulisan saya sendiri, jangan hilang.'
    d_edit.save(str(docx1))
    # Baca ulang + rencana + tulis dengan XML asli untuk yang dipertahankan.
    import zipfile as _zf
    from app.pustaka_periksa import _RE_P as _RP, _teks_par_xml as _TPX
    with _zf.ZipFile(docx1) as z:
        _doc_xml = z.read('word/document.xml').decode('utf-8')
    _cocok = list(_RP.finditer(_doc_xml))
    _teks_par = [_TPX(m.group(0)) for m in _cocok]
    baca_u = BA.baca_bagian_awal(_teks_par)
    sidik_lama_u = {'kata_pengantar': BA.sidik_bagian(['Kata pengantar AI lama.'])}
    ren_u = BA.rencana_update(
        {'nama': 'Siti Aminah'}, {'nama': 'Siti Aminah'}, baca_u,
        sidik_lama_u, 'proposal')
    cek('docx: kata pengantar edit tangan masuk dipertahankan',
        any(dd['kunci'] == 'kata_pengantar' for dd in ren_u['dipertahankan']),
        str(ren_u))
    # Tulis ulang dengan XML asli untuk kata pengantar (aturan kunci).
    idx_kp = baca_u.get('indeks', {}).get('kata_pengantar', [])
    xml_kp = [_cocok[i].group(0) for i in idx_kp if 0 <= i < len(_cocok)]
    bagian_update = []
    for k, j, b in BA.susun_bagian(
            {'nama': 'Siti Aminah', 'nim': '112310001', 'prodi': 'Manajemen',
             'fakultas': 'Ekonomi dan Bisnis', 'kota': 'Bekasi',
             'tahun': '2026', 'judul': 'Judul Skripsi Saya',
             'pembimbing_nama': 'Dr. Budi, M.M.',
             'pembimbing_nip': '198501012010011001'},
            'proposal', {'daftar_isi': BA.entri_daftar_isi(PETA_BAB123)}):
        if k == 'kata_pengantar':
            bagian_update.append({'kunci': k, 'judul': j, 'baris': [],
                                  'xml': xml_kp, 'ppr': ''})
        else:
            bagian_update.append({'kunci': k, 'judul': j, 'baris': b,
                                  'xml': None, 'ppr': ''})
    tulis2 = BA.tulis_bagian_awal(docx1, bagian_update)
    teks2 = _teks_docx(docx1)
    cek('docx ATURAN KUNCI: kata pengantar edit tangan tetap utuh sesudah update',
        tulis2.get('ok')
        and 'Kata pengantar tulisan saya sendiri, jangan hilang.' in teks2
        and 'Kata pengantar AI lama.' not in teks2, str(tulis2))

    # Halaman yang dihapus ditawarkan kembali; halaman baru tidak disentuh.
    d_hapus = _Docx(str(docx1))
    for p in d_hapus.paragraphs:
        if p.text.strip() == 'PERSEMBAHAN':
            p.text = ''
    d_hapus.save(str(docx1))
    _teks_h = _teks_docx(docx1)
    baca_h = BA.baca_bagian_awal(_teks_h.split('\n'))
    ren_h = BA.rencana_update(
        {}, {}, baca_h,
        {'persembahan': BA.sidik_bagian([''])}, 'proposal')
    cek('docx: halaman persembahan yang dihapus ditawarkan kembali',
        any(dd['kunci'] == 'persembahan' for dd in ren_h['kembalikan']),
        str(ren_h))

    # Blok tambahan mahasiswa di tengah seksi form tetap di tempatnya.
    docx3 = Path(TMP) / 'naskah3.docx'
    d3 = _Docx()
    for _t in ['Fakultas Ekonomi dan Bisnis', 'Program Studi Manajemen',
               'SKRIPSI', 'Judul Saya', 'Oleh', 'Siti Aminah',
               'LEMBAR PERSETUJUAN PEMBIMBING',
               'Skripsi ini diajukan oleh Siti Aminah.',
               'BLOK SAYA', 'Isi blok saya.',
               'KATA PENGANTAR', 'Puji syukur.',
               'BAB I', 'PENDAHULUAN', 'Isi bab.']:
        d3.add_paragraph(_t)
    d3.save(str(docx3))
    from app import rute_bagian_awal as _RBA
    _spans3 = _RBA._xml_spans(docx3)
    _teks3 = [t for t, _ in _spans3]
    _baca3 = BA.baca_bagian_awal(_teks3)
    cek('docx: blok caps di tengah seksi form jadi tambahan',
        len(_baca3['tambahan']) == 1
        and _baca3['tambahan'][0] == ['BLOK SAYA', 'Isi blok saya.'],
        str(_baca3))
    _ren3 = BA.rencana_update(
        {'nama': 'Siti Aminah'}, {'nama': 'Siti Aminah'}, _baca3, {}, 'proposal')
    _baru3 = _RBA._bangun_bagian_baru(
        _ren3, _baca3, _spans3, {'nama': 'Siti Aminah'}, 'proposal',
        PETA_BAB123, _teks3, None, None)
    _kunci3 = [b['kunci'] for b in _baru3]
    cek('docx: tambahan disisip sesudah persetujuan (tempat asal)',
        _kunci3.index('tambahan_0') > _kunci3.index('persetujuan')
        and _kunci3.index('tambahan_0') < _kunci3.index('kata_pengantar'),
        str(_kunci3))
    cek('docx: judul tidak ganda saat sampul dipertahankan',
        _kunci3.count('judul') == 0, str(_kunci3))
    _tulis3 = BA.tulis_bagian_awal(docx3, _baru3)
    _teks3b = _teks_docx(docx3)
    cek('docx ATURAN KUNCI: blok tambahan tetap utuh di tempatnya sesudah tulis',
        _tulis3.get('ok') and 'Isi blok saya.' in _teks3b
        and _teks3b.index('BLOK SAYA') < _teks3b.index('KATA PENGANTAR')
        and _teks3b.index('BLOK SAYA') > _teks3b.index('LEMBAR PERSETUJUAN'),
        _teks3b[:300])

    # Perbarui nomor daftar dari render.
    docx2 = Path(TMP) / 'naskah2.docx'
    _buat_naskah(docx2)
    BA.tulis_bagian_awal(docx2, [
        {'kunci': k, 'judul': j, 'baris': b, 'xml': None, 'ppr': ''}
        for k, j, b in BA.susun_bagian(
            {'nama': 'Siti Aminah', 'judul': 'Judul Saya'}, 'proposal',
            {'daftar_isi': BA.entri_daftar_isi(PETA_BAB123)})])
    render2 = ['Sampul', 'KATA PENGANTAR', 'DAFTAR ISI',
               'BAB I PENDAHULUAN latar', 'BAB II TINJAUAN PUSTAKA teori',
               'BAB III METODE PENELITIAN metode']
    r_per = BA.perbarui_nomor_daftar(docx2, halaman_render=render2)
    teks_per = _teks_docx(docx2)
    cek('docx: perbarui nomor daftar mengisi nomor nyata dari render',
        r_per.get('ok') and r_per.get('diperbarui', 0) >= 2
        and 'BAB I  1' in teks_per and 'BAB II  2' in teks_per,
        str(r_per) + ' | ' + teks_per[:400])
    import app.sidecar_buku as _sc
    _sc_asli = _sc.teks_halaman

    def _sc_mati(path):
        raise RuntimeError('sidecar mati')
    _sc.teks_halaman = _sc_mati
    try:
        r_gagal = BA.perbarui_nomor_daftar(
            docx2, halaman_render=None,
            ukur_fn=lambda p: (_ for _ in ()).throw(RuntimeError('sidecar mati')))
    finally:
        _sc.teks_halaman = _sc_asli
    cek('docx: tanpa render, nomor tidak dikarang (jujur gagal)',
        r_gagal.get('ok') is False and 'tidak tersedia' in r_gagal.get('sebab', ''),
        str(r_gagal))

    # ── 12b. Regresi 4 cacat uji live 16 Nov 2026 (file 126 = buku) ───
    import copy as _copy
    import re as _re
    import zipfile as _zf2
    from datetime import datetime as _dt, timedelta as _td
    from app.pustaka_periksa import _RE_P as _RP2, _teks_par_xml as _TPX2
    _tpl_ba = Path(ROOT, 'app', 'templates', 'bagian_awal.html').read_text()
    _naskah_tpl = Path(ROOT, 'app', 'templates', 'naskah.html').read_text()

    def _par_xml(jalur):
        """Daftar teks paragraf SESUNGGUHNYA dari XML (termasuk yang kosong).

        _teks_dari_docx membuang paragraf kosong dan menggabung dengan
        '\\n\\n', jadi tidak bisa dipakai untuk menghitung paragraf.
        """
        with _zf2.ZipFile(jalur) as z:
            _doc = z.read('word/document.xml').decode('utf-8')
        return [_TPX2(m.group(0)) for m in _RP2.finditer(_doc)]

    def _buat_buku(jalur):
        d = _Docx()
        for t in [
            'PEMASARAN DIGITAL',
            'Strategi, Perilaku Konsumen, dan Kinerja Bisnis di Era Ekonomi Digital',
            'Oleh: Uji Buku', '2026',
            'Hak cipta dilindungi undang-undang',
            'Diterbitkan oleh Penerbit Uji',
            'Cetakan pertama, 2026',
            'DAFTAR ISI',
            'BAB 1 Pendahuluan',
            'BAB 2 Tinjauan Pustaka',
            '1.1 Latar Belakang',
            'BAB 3 Metode Penelitian',
            'BAB 4 Hasil Penelitian dan Pembahasan',
            'BAB 5 Penutup',
            'KATA PENGANTAR',
            'Buku referensi ini disusun untuk menjawab satu pertanyaan sentral yang mendesak dalam diskursus manajemen.',
            'Penulis mengucapkan terima kasih kepada semua pihak.',
            'BAB 1', 'PENDAHULUAN', '1.1 Latar Belakang',
            'Isi latar belakang penelitian ini.',
            'Tabel 1.1 Jenis Data',
            'BAB 2', 'TINJAUAN PUSTAKA', '2.1 Teori tentang Variabel Y',
            'Isi teori.',
            'Gambar 2.1 Model Penelitian',
            'BAB 3', 'METODE PENELITIAN', '3.1 Jenis dan Desain Penelitian',
            'Isi metode.',
            'BAB 4', 'HASIL PENELITIAN DAN PEMBAHASAN', '4.1 Hasil Uji',
            'Hasil uji menunjukkan pengaruh positif.',
            'BAB 5', 'PENUTUP', '5.1 Simpulan', 'Simpulan penelitian ini.',
            'Lampiran 1 Kuesioner',
            'INDEKS SUBJEK', 'INDEKS NAMA', 'DAFTAR SINGKATAN',
            'TENTANG PENULIS',
        ]:
            d.add_paragraph(t)
        d.save(str(jalur))
        return jalur

    _BARIS_BUKU = ['BAB 1', 'PENDAHULUAN', '1.1 Latar Belakang',
                   'BAB 2', 'TINJAUAN PUSTAKA', '2.1 Teori tentang Variabel Y',
                   'BAB 3', 'METODE PENELITIAN', '3.1 Jenis dan Desain Penelitian',
                   'BAB 4', 'HASIL PENELITIAN DAN PEMBAHASAN', '4.1 Hasil Uji',
                   'BAB 5', 'PENUTUP', '5.1 Simpulan']
    _LABEL_BUKU = {str(i): ('subbab' if t[:1].isdigit() and '.' in t.split()[0]
                            else 'bab')
                   for i, t in enumerate(_BARIS_BUKU)}
    PETA_BUKU = {'peta_surveyor': {
        'baris': _BARIS_BUKU, 'label': _LABEL_BUKU,
        'hakim': {'jumlah_ragu': 0, 'jumlah_curiga': 0}}}
    _DATA_BUKU = {'nama': 'Mahasiswa Uji', 'nim': '0000000000',
                  'prodi': 'Manajemen', 'fakultas': 'Ekonomi dan Bisnis',
                  'kota': 'Bekasi', 'tahun': '2026', 'judul': 'Pemasaran Digital',
                  'pembimbing_nama': 'Dosen Uji', 'pembimbing_gelar': 'S.E., M.M.',
                  'pembimbing_nip': '', 'penguji1_nama': '', 'penguji2_nama': '',
                  'kaprodi_nama': 'Kaprodi Uji, S.E., M.M.', 'kaprodi_nip': '',
                  'dekan_nama': 'Dekan Uji, S.E., M.M.', 'dekan_nip': '',
                  'rektor_nama': '', 'rektor_nip': '',
                  'tanggal_sidang': '16 November 2026'}

    def _hitung_judul(teks, kata):
        return sum(1 for t in teks if t.strip().upper() == kata)

    docx_buku = Path(TMP) / 'buku.docx'
    _buat_buku(docx_buku)
    _spans_b = _RBA._xml_spans(docx_buku)
    _teks_b = [t for t, _ in _spans_b]
    cek('regresi buku: judul bab angka Arab dikenali dari teks',
        BA.bab_dari_teks('\n'.join(_teks_b)) == {1, 2, 3, 4, 5},
        str(BA.bab_dari_teks('\n'.join(_teks_b))))
    cek('regresi buku: teks dan peta sepakat soal bab (pesan kartu selaras)',
        BA.bab_dari_teks('\n'.join(_teks_b)) == BA.bab_dari_peta(PETA_BUKU))
    cek('regresi buku: indeks Bab I menunjuk badan, bukan daftar isi buku',
        BA.cari_indeks_bab1(_teks_b) == 17,
        str(BA.cari_indeks_bab1(_teks_b)))
    _baca_b = BA.baca_bagian_awal(_teks_b)
    _ren_b = BA.rencana_update(_DATA_BUKU, {}, _baca_b, {}, 'final')
    _baru_b = _RBA._bangun_bagian_baru(
        _ren_b, _baca_b, _spans_b, _DATA_BUKU, 'final', PETA_BUKU, _teks_b,
        ['Kata pengantar draf AI.'], None)
    _tulis_b = BA.tulis_bagian_awal(docx_buku, _baru_b)
    _teks_b1 = _teks_docx(docx_buku)
    _par_b1 = _par_xml(docx_buku)
    cek('regresi cacat 1: tempel berhasil, badan buku utuh',
        _tulis_b.get('ok') and 'Isi latar belakang penelitian ini.' in _teks_b1
        and 'Simpulan penelitian ini.' in _teks_b1, str(_tulis_b))
    cek('regresi cacat 1: sesudah tempel tiap seksi depan tepat satu',
        all(_hitung_judul(_par_b1, k) == 1 for k in
            ('KATA PENGANTAR', 'DAFTAR ISI', 'ABSTRACT', 'ABSTRAK')),
        str({k: _hitung_judul(_par_b1, k) for k in
             ('KATA PENGANTAR', 'DAFTAR ISI', 'ABSTRACT', 'ABSTRAK')}))
    _xml_b1 = _xml_docx(docx_buku)
    _sect_b1 = _re.findall(r'<w:sectPr.*?</w:sectPr>', _xml_b1, _re.S)
    cek('regresi cacat 2: tepat dua pemutus (Romawi depan, Arab badan, mulai 1)',
        len(_sect_b1) == 2
        and 'lowerRoman' in _sect_b1[0] and 'decimal' in _sect_b1[1]
        and 'w:start="1"' in _sect_b1[0] and 'w:start="1"' in _sect_b1[1],
        str(len(_sect_b1)))
    cek('regresi cacat 2: pemutus depan memakai footer yang sama dengan badan',
        len(_sect_b1) == 2
        and (lambda m: (m.group(1) if m else None))(
            _re.search(r'footerReference[^>]*r:id="([^"]+)"', _sect_b1[0]))
        == (lambda m: (m.group(1) if m else None))(
            _re.search(r'footerReference[^>]*r:id="([^"]+)"', _sect_b1[1])),
        # Fixture ini tanpa footer (python-docx), jadi keduanya None;
        # kasus footer nyata dibuktikan repro render (keduanya rIdFooter1).
        str(_sect_b1[0][:200] if _sect_b1 else ''))
    cek('regresi cacat 1: tiap seksi depan mulai di halaman baru (13 jeda)',
        _xml_b1.count('<w:br w:type="page"/>') == 13,
        str(_xml_b1.count('<w:br w:type="page"/>')))
    _idx_daftar = [_par_b1.index(k) for k in
                   ('DAFTAR ISI', 'DAFTAR TABEL', 'DAFTAR GAMBAR',
                    'DAFTAR LAMPIRAN')]
    cek('regresi cacat 3: urutan daftar ikut Pedoman (Isi, Tabel, Gambar, Lampiran)',
        _idx_daftar == sorted(_idx_daftar), str(_idx_daftar))
    _i_abs = _par_b1.index('ABSTRACT')
    _i_abr = _par_b1.index('ABSTRAK')
    cek('regresi cacat 4: halaman abstract berisi judul + kolom (bukan kosong)',
        _par_b1[_i_abs + 2] == 'Mahasiswa Uji'
        and _par_b1[_i_abs + 3] == 'Pemasaran Digital'
        and _par_b1[_i_abr + 2] == 'Mahasiswa Uji'
        and _par_b1[_i_abr + 3] == 'Pemasaran Digital',
        str(_par_b1[_i_abs:_i_abs + 5]) + ' | '
        + str(_par_b1[_i_abr:_i_abr + 5]))
    cek('regresi cacat 4: draf abstrak yang belum diterima tidak masuk naskah',
        'Buku referensi ini disusun' in _teks_b1
        and 'Kata pengantar draf AI.' not in _teks_b1
        and _par_b1[_i_abs + 4] == 'ABSTRAK'
        and _par_b1[_i_abr + 4] == 'BAB 1')
    cek('regresi (a): sampul terdeteksi sesudah tempel',
        'sampul' in BA.baca_bagian_awal(_par_b1).get('bagian', {}),
        str(sorted(BA.baca_bagian_awal(_par_b1).get('bagian', {}).keys())))
    cek('regresi: isi buku (sampul, copyright, indeks, Tentang Penulis) utuh',
        'Hak cipta dilindungi undang-undang' in _teks_b1
        and 'INDEKS SUBJEK' in _teks_b1 and 'TENTANG PENULIS' in _teks_b1,
        _teks_b1[:200])

    # Regresi berkas 126 (uji live 16 Nov 2026): tiruan setia strukturnya
    # (bagian depan mengganda + entri Daftar Isi berjudul huruf campuran
    # + blok Daftar Isi terakhir langsung sebelum judul badan 'BAB 1'
    # telanjang). Pencari harus menemukan Bab I dan tempel harus jalan.
    _par_126 = [
        'PEMASARAN DIGITAL',
        'Strategi, Perilaku Konsumen, dan Kinerja Bisnis di Era Ekonomi Digital',
        'Oleh: Uji Buku', '2026',
        'KATA PENGANTAR',
        'Buku referensi ini disusun untuk menjawab satu pertanyaan sentral.',
        'DAFTAR ISI',
        'BAB 1. Lanskap Pemasaran Digital: Ruang Lingkup, Batasan, dan Fondasi Konseptual',
        'BAB 2. Arsitektur Strategi Pemasaran Digital dan Dinamika Platform',
        'DAFTAR TABEL',
        'Tabel 1.1 Jenis Data',
        'LEMBAR PERSETUJUAN',
        'KATA PENGANTAR',
        'Buku referensi ini disusun untuk menjawab satu pertanyaan sentral.',
        'DAFTAR ISI',
        'BAB 1. Lanskap Pemasaran Digital: Ruang Lingkup, Batasan, dan Fondasi Konseptual',
        'BAB 2. Arsitektur Strategi Pemasaran Digital dan Dinamika Platform',
        'BAB 1', 'PENDAHULUAN',
        'Isi latar belakang penelitian ini.',
        'BAB 2', 'TINJAUAN PUSTAKA',
        'Isi teori.',
    ]
    docx_126 = Path(TMP) / 'tiruan126.docx'
    _d126 = _Docx()
    for _t in _par_126:
        _d126.add_paragraph(_t)
    _d126.save(str(docx_126))
    _spans_126 = _RBA._xml_spans(docx_126)
    _teks_126 = [t for t, _ in _spans_126]
    cek('regresi 126: pencari menemukan Bab I telanjang sesudah blok daftar',
        BA.cari_indeks_bab1(_teks_126) == _teks_126.index('BAB 1'),
        str(BA.cari_indeks_bab1(_teks_126)))
    _tulis_126 = BA.tulis_bagian_awal(docx_126, [
        {'kunci': 'kata_pengantar', 'judul': 'KATA PENGANTAR',
         'baris': ['KATA PENGANTAR', 'Isi pengantar uji.'],
         'xml': None, 'ppr': ''}])
    _teks_126b = _teks_docx(docx_126)
    _par_126b = _par_xml(docx_126)
    cek('regresi 126: tempel berhasil pada tiruan berkas 126, badan utuh',
        _tulis_126.get('ok')
        and 'Isi latar belakang penelitian ini.' in _teks_126b
        and 'Isi teori.' in _teks_126b, str(_tulis_126))
    cek('regresi 126: sesudah tempel bagian depan lama terganti (satu pengantar, tanpa daftar isi lama)',
        _hitung_judul(_par_126b, 'KATA PENGANTAR') == 1
        and _hitung_judul(_par_126b, 'DAFTAR ISI') == 0,
        str({k: _hitung_judul(_par_126b, k)
             for k in ('KATA PENGANTAR', 'DAFTAR ISI')}))

    # Perbarui: ubah NIP pembimbing, rencana dari sidik pasca-tempel.
    _DATA_B2 = dict(_DATA_BUKU, pembimbing_nip='198501012010011001')
    _spans_b2 = _RBA._xml_spans(docx_buku)
    _teks_b2 = [t for t, _ in _spans_b2]
    _baca_b2 = BA.baca_bagian_awal(_teks_b2)
    _ren_b2 = BA.rencana_update(_DATA_B2, _DATA_BUKU, _baca_b2, {}, 'final')
    _baru_b2 = _RBA._bangun_bagian_baru(
        _ren_b2, _baca_b2, _spans_b2, _DATA_B2, 'final', PETA_BUKU, _teks_b2,
        None, None)
    _tulis_b2 = BA.tulis_bagian_awal(docx_buku, _baru_b2)
    _teks_b3 = _teks_docx(docx_buku)
    _par_b3 = _par_xml(docx_buku)
    cek('regresi cacat 1: sesudah perbarui tiap seksi depan tetap satu',
        _tulis_b2.get('ok') and all(_hitung_judul(_par_b3, k) == 1 for k in
                                    ('KATA PENGANTAR', 'DAFTAR ISI',
                                     'ABSTRACT', 'ABSTRAK')),
        str(_tulis_b2) + ' | ' + str(
            {k: _hitung_judul(_par_b3, k) for k in
             ('KATA PENGANTAR', 'DAFTAR ISI', 'ABSTRACT', 'ABSTRAK')}))
    cek('regresi cacat 1: jumlah paragraf stabil sesudah perbarui (tidak membengkak)',
        len(_par_b3) == len(_par_b1), f'{len(_par_b1)} -> {len(_par_b3)}')
    _xml_b3 = _xml_docx(docx_buku)
    cek('regresi cacat 1: jeda halaman tetap 13 sesudah perbarui (idempotent)',
        _xml_b3.count('<w:br w:type="page"/>') == 13,
        str(_xml_b3.count('<w:br w:type="page"/>')))
    cek('regresi cacat 2: sesudah perbarui tetap dua pemutus',
        len(_re.findall(r'<w:sectPr.*?</w:sectPr>', _xml_b3, _re.S)) == 2)
    cek('regresi cacat 1: entri daftar tidak ganda sesudah perbarui',
        _par_b3.count('Tabel 1.1 Jenis Data') == 2
        and _par_b3.count('Gambar 2.1 Model Penelitian') == 2
        and _par_b3.count('Lampiran 1 Kuesioner') == 2,
        str({k: _par_b3.count(k) for k in
             ('Tabel 1.1 Jenis Data', 'Gambar 2.1 Model Penelitian',
              'Lampiran 1 Kuesioner')}))
    cek('regresi: NIP baru masuk Persetujuan sesudah perbarui',
        'NIP : 198501012010011001' in _teks_b3)
    cek('regresi cacat 3: entri daftar tabel/gambar dapat nomor dari render',
        BA.perbarui_nomor_daftar(
            docx_buku, halaman_render=[
                'Sampul', 'KATA PENGANTAR', 'DAFTAR ISI',
                'BAB 1\nPENDAHULUAN\nTabel 1.1 Jenis Data',
                'BAB 2\nTINJAUAN PUSTAKA\nGambar 2.1 Model Penelitian',
                'BAB 3\nMETODE PENELITIAN\nLampiran 1 Kuesioner']).get('ok')
        and 'Tabel 1.1 Jenis Data  1' in _teks_docx(docx_buku)
        and 'Gambar 2.1 Model Penelitian  2' in _teks_docx(docx_buku))

    # ── 12d. Regresi perbaikan Perbarui #3 (16 Nov 2026) ────────────
    # (a) Daftar Isi buatan: satu baris per bab. Penanda telanjang
    # ('BAB 1') + judul polos ('PENDAHULUAN') bergabung jadi satu
    # entri ('BAB 1. PENDAHULUAN'), bukan dua baris.
    _entri_buku = BA.entri_daftar_isi(
        PETA_BUKU, paragraf_badan=_BARIS_BUKU)
    _judul_entri = [e['judul'] for e in _entri_buku]
    cek('regresi 12d: Daftar Isi satu baris per bab (tanpa ganda)',
        _judul_entri.count('BAB 1. PENDAHULUAN') == 1
        and 'BAB 1' not in _judul_entri
        and 'PENDAHULUAN' not in _judul_entri
        and _judul_entri.count('BAB 5. PENUTUP') == 1,
        str(_judul_entri))
    # (b) Pencari Bab I menunjuk badan, bukan entri Daftar Isi.
    _idx_b3 = BA.cari_indeks_bab1(_par_b3)
    cek('regresi 12d: pencari Bab I menunjuk badan, bukan Daftar Isi',
        _idx_b3 is not None
        and _par_b3[_idx_b3] == 'BAB 1'
        and _par_b3[_idx_b3 + 1] == 'PENDAHULUAN'
        and _idx_b3 > _par_b3.index('ABSTRAK'),
        str(_idx_b3))
    # (c) Nomor daftar: judul seksi tidak tertimpa nomor, judul ganda
    # ('Ringkasan Bab' tiap bab) bernomor berurutan sesuai halamannya.
    _docx_dup = Path(TMP) / 'daftar_dup.docx'
    _d_dup = _Docx()
    for _t in ['KATA PENGANTAR', 'Isi pengantar.',
               'DAFTAR ISI', '', 'KATA PENGANTAR',
               'BAB 1. PENDAHULUAN', 'Ringkasan Bab',
               'BAB 2. TINJAUAN PUSTAKA', 'Ringkasan Bab',
               'DAFTAR TABEL', '', 'Tabel 1.1 Jenis Data',
               'BAB 1', 'PENDAHULUAN', 'Isi bab satu.', 'Ringkasan Bab',
               'BAB 2', 'TINJAUAN PUSTAKA', 'Isi teori.', 'Ringkasan Bab']:
        _d_dup.add_paragraph(_t)
    _d_dup.save(str(_docx_dup))
    _render_dup = ['Sampul', 'KATA PENGANTAR\nIsi pengantar.',
                   'DAFTAR ISI\nKATA PENGANTAR\nBAB 1. PENDAHULUAN',
                   'BAB 1\nPENDAHULUAN\nIsi bab satu.\nTabel 1.1 Jenis Data',
                   'Ringkasan Bab\nAkhir bab satu.',
                   'BAB 2\nTINJAUAN PUSTAKA\nIsi teori.',
                   'Ringkasan Bab\nAkhir bab dua.']
    _r_dup = BA.perbarui_nomor_daftar(
        _docx_dup, halaman_render=_render_dup)
    _par_dup = _par_xml(_docx_dup)
    cek('regresi 12d: nomor daftar tidak menimpa judul seksi',
        _r_dup.get('ok') and _par_dup[0] == 'KATA PENGANTAR'
        and _par_dup[3] == 'KATA PENGANTAR  ii',
        str(_r_dup) + ' | ' + str(_par_dup[:8]))
    cek('regresi 12d: judul ganda bernomor berurutan (bukan satu nomor)',
        _par_dup[5] == 'Ringkasan Bab  2'
        and _par_dup[7] == 'Ringkasan Bab  4'
        and _par_dup[4] == 'BAB 1. PENDAHULUAN  1'
        and _par_dup[6] == 'BAB 2. TINJAUAN PUSTAKA  3',
        str(_par_dup[3:9]))
    cek('regresi 12d: judul badan tidak ikut bernomor daftar',
        _par_dup[13] == 'Ringkasan Bab' and _par_dup[17] == 'Ringkasan Bab',
        str(_par_dup[10:]))
    # (d) Format paragraf yang dipakai ulang tidak membawa pemutus
    # bagian (sectPr): pemutus depan hanya dua, footer merata.
    _xml_sect = ('<w:p><w:pPr><w:rPr><w:b/></w:rPr>'
                 '<w:sectPr><w:pgSz w:w="12240"/></w:sectPr></w:pPr>'
                 '<w:r><w:t>Isi.</w:t></w:r></w:p>')
    cek('regresi 12d: ppr yang dipakai ulang tidak membawa pemutus bagian',
        'sectPr' not in BA._ppr_dari_xml(_xml_sect),
        BA._ppr_dari_xml(_xml_sect)[:200])
    # (e) Nama tercantum di kedua halaman abstrak (Inggris + Indonesia).
    _susun_abs = BA.susun_bagian(
        {'nama': 'Mahasiswa Uji', 'judul': 'Pemasaran Digital'}, 'final',
        {'daftar_isi': [], 'daftar_tabel': [], 'daftar_gambar': [],
         'daftar_lampiran': []})
    _abs_en = [b for k, _j, b in _susun_abs if k == 'abstract'][0]
    _abs_id = [b for k, _j, b in _susun_abs if k == 'abstrak'][0]
    cek('regresi 12d: nama tercantum di kedua halaman abstrak',
        'Mahasiswa Uji' in _abs_en and 'Mahasiswa Uji' in _abs_id
        and _abs_en[-1] != '' and _abs_id[-1] != '',
        str(_abs_en) + ' | ' + str(_abs_id))

    # Nomor footer dari render: Romawi depan, Arab badan dari 1, None bila tak ada.
    _render_nomor = ['Sampul\nFakultas Ekonomi',
                     'KATA PENGANTAR\nIsi pengantar.',
                     'DAFTAR ISI\nBAB 1\nPENDAHULUAN\n1.1 Latar Belakang',
                     'BAB 1\nPENDAHULUAN\nIsi bab satu.',
                     'BAB 2\nTINJAUAN PUSTAKA\nIsi teori.']
    cek('regresi cacat 3: nomor footer depan Romawi (pengantar ii, isi iii)',
        BA.nomor_footer_dari_render(_render_nomor, 'KATA PENGANTAR') == 'ii'
        and BA.nomor_footer_dari_render(_render_nomor, 'DAFTAR ISI') == 'iii',
        str(BA.nomor_footer_dari_render(_render_nomor, 'KATA PENGANTAR')))
    cek('regresi cacat 3: nomor footer badan Arab mulai 1 di Bab I',
        BA.nomor_footer_dari_render(_render_nomor, 'BAB 1') == 1
        and BA.nomor_footer_dari_render(_render_nomor, 'BAB 2') == 2
        and BA.nomor_footer_dari_render(_render_nomor, 'PENDAHULUAN') == 1)
    cek('regresi cacat 3: nomor footer tak ketemu -> None (tidak dikarang)',
        BA.nomor_footer_dari_render(_render_nomor, 'BAB IV HASIL') is None)

    # Peringatan usang: tidak menyala sesudah pembuatan ulang, menyala bila berubah.
    _waktu_tulis = _dt.fromtimestamp(Path(docx_buku).stat().st_mtime)
    _hasil_usang = {'ditempel': True,
                    'sidik_daftar': BA.sidik_daftar(PETA_BUKU, _par_b3),
                    'diubah_pada': _waktu_tulis}
    cek('regresi cacat 3: peringatan usang TIDAK muncul sesudah pembuatan ulang',
        BA.daftar_usang(_hasil_usang, PETA_BUKU, _par_b3, _waktu_tulis) is False)
    _peta_ubah = _copy.deepcopy(PETA_BUKU)
    _peta_ubah['peta_surveyor']['baris'] = list(_BARIS_BUKU) + ['BAB 6', 'SARAN']
    _peta_ubah['peta_surveyor']['label'] = dict(_LABEL_BUKU)
    _peta_ubah['peta_surveyor']['label'][str(len(_BARIS_BUKU))] = 'bab'
    _peta_ubah['peta_surveyor']['label'][str(len(_BARIS_BUKU) + 1)] = 'bab'
    cek('regresi cacat 3: peringatan usang menyala bila peta berubah',
        BA.daftar_usang(_hasil_usang, _peta_ubah, _par_b3, _waktu_tulis) is True)
    cek('regresi cacat 3: peringatan usang menyala bila berkas berubah sesudah tulis',
        BA.daftar_usang(_hasil_usang, PETA_BUKU, _par_b3,
                        _waktu_tulis + _td(hours=1)) is True)

    # Gagal tertutup: Bab I tidak ada -> tempel ditolak, berkas tidak berubah.
    docx_tanpa_bab = Path(TMP) / 'tanpa_bab.docx'
    d_tb = _Docx()
    for t in ['DAFTAR ISI', 'KATA PENGANTAR', 'Isi pengantar.']:
        d_tb.add_paragraph(t)
    d_tb.save(str(docx_tanpa_bab))
    _teks_tb_sebelum = _teks_docx(docx_tanpa_bab)
    _tulis_tb = BA.tulis_bagian_awal(docx_tanpa_bab, [
        {'kunci': k, 'judul': j, 'baris': b, 'xml': None, 'ppr': ''}
        for k, j, b in BA.susun_bagian(
            {'nama': 'Siti Aminah', 'judul': 'Judul Saya'}, 'proposal',
            {'daftar_isi': BA.entri_daftar_isi(PETA_BAB123)})])
    cek('regresi cacat 1: tanpa Bab I, tempel ditolak supaya tidak mengganda',
        _tulis_tb.get('ok') is False
        and _teks_docx(docx_tanpa_bab) == _teks_tb_sebelum,
        str(_tulis_tb))

    # Daftar lampiran kosong ditulis jujur, bukan halaman kosong.
    _susun_kosong = BA.susun_bagian(
        {'nama': 'Siti Aminah', 'judul': 'Judul Saya'}, 'proposal',
        {'daftar_isi': BA.entri_daftar_isi(PETA_BAB123),
         'daftar_tabel': [], 'daftar_gambar': [], 'daftar_lampiran': []})
    _baris_lamp = [b for k, _j, b in _susun_kosong if k == 'daftar_lampiran'][0]
    cek('regresi cacat 3: lampiran kosong ditandai "Belum ada lampiran."',
        BA.BARIS_BELUM_ADA_LAMPIRAN in _baris_lamp, str(_baris_lamp))

    # Catatan tambahan (a-e) dari uji yang sama.
    cek('regresi (d): nama pembimbing berupa email dikosongkan (bukan nama)',
        BA.bersihkan_data({'pembimbing_nama': 'uji-buku@bikinaja.id'}
                          ).get('pembimbing_nama') == '')
    cek('regresi (e): struk tempel dan perbarui menghitung baris yang sama',
        BA.hitung_baris_isi(['KATA PENGANTAR', '', 'Isi pengantar.',
                             '', 'Paragraf kedua.']) == 3
        and BA.hitung_baris_isi(['KATA PENGANTAR', '', 'Isi pengantar.',
                                 '', 'Paragraf kedua.'])
        == BA.hitung_baris_isi(['KATA PENGANTAR', '', 'Isi pengantar.',
                                '', 'Paragraf kedua.']))
    _aksi_awal = _naskah_tpl.index('.aksi{')
    _aksi_akhir = _naskah_tpl.index('}', _aksi_awal)
    cek('regresi (c): baris tombol kartu membungkus di layar sempit (flex-wrap)',
        'flex-wrap:wrap' in _naskah_tpl[_aksi_awal:_aksi_akhir],
        _naskah_tpl[_aksi_awal:_aksi_akhir])

    # ── 12c. Penyederhanaan layar (Boss 16 Nov 2026 16:07 WIB) ────────
    cek('sederhana: ringkasan layar pertama tepat 5 kelompok',
        [g['kelompok'] for g in BA.ringkas_kelompok({}, [], 'proposal')] ==
        ['tentang', 'pembimbing', 'penguji', 'pimpinan', 'daftar'])
    cek('sederhana: wajib sekarang 4 kolom, boleh nanti 18 kolom, semua 22 terjangkau',
        len(BA.WAJIB_SEKARANG) == 4 and len(BA.BOLEH_NANTI) == 18
        and set(BA.WAJIB_SEKARANG) | set(BA.BOLEH_NANTI) ==
        set(BA.KUNCI_FORM) | {'judul'})
    cek('sederhana: kolom boleh nanti di balik Tambah detail (tertutup dulu)',
        '  <details>\n  <summary>Tambah detail (boleh nanti)</summary>' in _tpl_ba
        and _tpl_ba.index('Wajib sekarang')
        < _tpl_ba.index('Tambah detail (boleh nanti)')
        < _tpl_ba.index('kunci not in wajib'))
    cek('sederhana: formulir tertutup dulu bila belum ada rencana',
        '<details class="kotak" {% if rencana %}open{% endif %}>' in _tpl_ba)
    cek('sederhana: ringkasan 5 kelompok tampil di layar pertama',
        '<h2>Ringkasan</h2>' in _tpl_ba and '{% for g in ringkasan %}' in _tpl_ba)
    cek('sederhana: semua kolom tetap dirender lewat loop kolom',
        'name="{{ kunci }}"' in _tpl_ba and 'name="judul"' in _tpl_ba)

    # ── 13. Setelan round-trip ────────────────────────────────────────
    from app.models import Base, Setelan, User, FileBerkas, ProfilDokumen
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    _eng = create_engine(f'sqlite:///{TMP}/uji.db')
    Base.metadata.create_all(_eng)
    _Sesi = sessionmaker(bind=_eng)
    db = _Sesi()
    BA.simpan_data(db, 81, {'nama': 'Siti Aminah', 'nim': ''})
    cek('setelan: data boleh kosong dan tersimpan',
        BA.muat_data(db, 81).get('nama') == 'Siti Aminah'
        and BA.muat_data(db, 81).get('nim') == '')
    BA.simpan_profil(db, 3, {'nama': 'Siti Aminah'})
    cek('setelan: profil tersimpan', BA.muat_profil(db, 3).get('nama') == 'Siti Aminah')
    BA.simpan_hasil(db, 81, {'ditempel': True, 'tahap': 'proposal'})
    cek('setelan: hasil tersimpan', (BA.muat_hasil(db, 81) or {}).get('ditempel') is True)
    BA.simpan_abstrak(db, 81, {'id': ['x'], 'diterima': False})
    cek('setelan: abstrak tersimpan', (BA.muat_abstrak(db, 81) or {}).get('id') == ['x'])
    baris = db.get(Setelan, BA._kunci_setelan('data', 81))
    baris.nilai = '{rusak'
    cek('setelan: JSON rusak dibaca None', BA.muat_data(db, 81) == {})

    # ── 14. Rute end-to-end (DB + docx sementara) ──────────────────────
    import asyncio as _asyncio
    import json as _json
    from app import rute_bagian_awal as RB
    from app import saldo as _saldo
    import app.models as _models
    _models.SessionLocal = _Sesi
    import app.proses as _proses
    _proses.SessionLocal = _Sesi
    import app.rute_bagian_awal as _RB
    _RB.UPLOAD_DIR = Path(TMP) / 'uploads'
    from fastapi.templating import Jinja2Templates
    RB.pasang(Jinja2Templates(directory=str(ROOT / 'app' / 'templates')))

    u = User(email='uji-ba@eduai.test', nama='Siti Aminah', password_hash='x')
    db.add(u)
    db.commit()
    _saldo.masuk(db, u, 20, sumber='uji')
    folder_u = Path(TMP) / 'uploads' / str(u.id)
    folder_u.mkdir(parents=True, exist_ok=True)
    _buat_naskah(folder_u / 'skripsi.docx')
    fb = FileBerkas(user_id=u.id, nama='skripsi.docx',
                    nama_simpan='skripsi.docx', ukuran=100)
    db.add(fb)
    db.commit()
    profil = ProfilDokumen(user_id=u.id, file_id=fb.id,
                           peta_json=_json.dumps(PETA_BAB123))
    db.add(profil)
    db.commit()

    def _tunggu_selesai(fid, maks=40):
        for _ in range(maks):
            time.sleep(0.5)
            db.expire_all()
            st = _asyncio.run(RB.bagian_awal_status(file_id=fid, u=u, db=db))
            if st.get('terakhir', {}).get('status') in ('selesai', 'gagal'):
                return st
        return None

    # Halaman: keadaan aktif (Bab I-III + peta) + tooltip benar.
    hal = _asyncio.run(RB.bagian_awal_halaman(
        fid=fb.id, request=_ReqPalsu(), u=u, db=db))
    badan = hal.body.decode('utf-8')
    cek('rute: halaman aktif sesudah Bab I-III terverifikasi',
        hal.status_code == 200 and 'Lengkapi Bagian Awal' in badan
        and 'Periksa Struktur dulu' not in badan, badan[:200])
    cek('rute: halaman memuat tooltip aktif (maksud + kapan + 2 token)',
        'bagian depan skripsi' in badan and 'ujian proposal' in badan
        and '2 token' in badan)
    cek('rute: halaman memuat daftar cek + form berkelompok',
        'Daftar cek' in badan and 'Tentang kamu' in badan
        and 'Pimpinan kampus' in badan and 'NIP pembimbing' in badan)
    cek('rute: halaman proposal tidak menagih abstrak',
        'Abstrak hanya di tahap final' in badan)

    # Simpan form (gratis, boleh kosong).
    hal_s = _asyncio.run(RB.bagian_awal_simpan(
        fid=fb.id, request=_ReqForm({'nama': 'Siti Aminah', 'nim': ''}),
        u=u, db=db))
    cek('rute: simpan form gratis (303) + tersimpan walau NIM kosong',
        hal_s.status_code == 303
        and BA.muat_data(db, fb.id).get('nama') == 'Siti Aminah'
        and BA.muat_data(db, fb.id).get('nim') == '')

    # Konfirmasi -> rencana tiga daftar tersimpan.
    hal_k = _asyncio.run(RB.bagian_awal_konfirmasi(
        fid=fb.id,
        request=_ReqForm({'nama': 'Siti Aminah', 'nim': '112310001',
                          'judul': 'Judul Skripsi Saya',
                          'tanpa_ai_pengantar': '1'}),
        u=u, db=db))
    ren_s = BA.muat_rencana(db, fb.id)
    cek('rute: konfirmasi 303 + rencana tersimpan',
        hal_k.status_code == 303 and ren_s is not None
        and ren_s.get('tanpa_ai_pengantar') is True, str(ren_s))
    cek('rute: rencana pertama: sampul/judul dari data baru masuk berubah, daftar dibuat ulang',
        any(d['kunci'] == 'sampul' for d in ren_s.get('berubah', []))
        and any(d['kunci'] == 'daftar_isi' for d in ren_s.get('dibuat_ulang', []))
        and ren_s.get('dipertahankan') == [], str(ren_s))

    # Tempel end-to-end (tanpa AI: tanpa_ai_pengantar dicentang).
    saldo_awal = _saldo.sisa(db, u, seed=False)
    hal_t = _asyncio.run(RB.bagian_awal_tempel(
        fid=fb.id, request=_ReqForm({'kembalikan': []}), u=u, db=db))
    st_akhir = _tunggu_selesai(fb.id)
    cek('rute: tempel 303 + pekerja selesai',
        hal_t.status_code == 303 and st_akhir is not None
        and st_akhir.get('terakhir', {}).get('status') == 'selesai',
        str(st_akhir))
    cek('rute: tempel memotong 2 token',
        _saldo.sisa(db, u, seed=False) == saldo_awal - 2,
        f"{saldo_awal} -> {_saldo.sisa(db, u, seed=False)}")
    hasil = BA.muat_hasil(db, fb.id) or {}
    cek('rute: hasil tersimpan (ditempel + sidik per bagian)',
        hasil.get('ditempel') is True
        and isinstance(hasil.get('sidik'), dict)
        and 'kata_pengantar' in hasil.get('sidik', {}), str(hasil)[:200])
    teks_akhir = _teks_docx(folder_u / 'skripsi.docx')
    cek('rute: docx sesudah tempel: depan ada, badan utuh',
        'Siti Aminah' in teks_akhir
        and 'Isi latar belakang penelitian ini.' in teks_akhir
        and teks_akhir.index('Siti Aminah') < teks_akhir.index('BAB I'))
    cek('rute: struk bukti tersimpan',
        bool((hasil.get('struk') or {}).get('dibuat_ulang')), str(hasil.get('struk')))

    # Update: ubah Kata Pengantar di naskah, tempel lagi -> tetap utuh.
    d_up = _Docx(str(folder_u / 'skripsi.docx'))
    # Isi paragraf kosong tepat sesudah judul KATA PENGANTAR
    # (pengantar pertama dibuat kosong karena tanpa AI).
    _pars = list(d_up.paragraphs)
    for _i, p in enumerate(_pars):
        if p.text.strip() == 'KATA PENGANTAR' and _i + 1 < len(_pars):
            _pars[_i + 1].text = 'Kata pengantar tulisan saya, versi dua.'
            break
    d_up.save(str(folder_u / 'skripsi.docx'))
    _asyncio.run(RB.bagian_awal_konfirmasi(
        fid=fb.id,
        request=_ReqForm({'nama': 'Siti Aminah', 'nim': '112310001',
                          'judul': 'Judul Skripsi Saya',
                          'tanpa_ai_pengantar': '1'}),
        u=u, db=db))
    ren_up = BA.muat_rencana(db, fb.id)
    cek('rute update: kata pengantar edit tangan masuk dipertahankan',
        any(d['kunci'] == 'kata_pengantar'
            for d in ren_up.get('dipertahankan', [])), str(ren_up))
    saldo_mid = _saldo.sisa(db, u, seed=False)
    _asyncio.run(RB.bagian_awal_tempel(
        fid=fb.id, request=_ReqForm({'kembalikan': []}), u=u, db=db))
    st_up = _tunggu_selesai(fb.id)
    teks_up = _teks_docx(folder_u / 'skripsi.docx')
    cek('rute update ATURAN KUNCI: tulisan mahasiswa tetap utuh',
        st_up is not None
        and st_up.get('terakhir', {}).get('status') == 'selesai'
        and 'Kata pengantar tulisan saya, versi dua.' in teks_up,
        str(st_up) + ' | ' + teks_up[:300])
    cek('rute update: memotong 2 token lagi',
        _saldo.sisa(db, u, seed=False) == saldo_mid - 2)

    # Abstrak AI gagal -> token kembali (penanya dipalsukan gagal).
    fb2 = FileBerkas(user_id=u.id, nama='skripsi2.docx',
                     nama_simpan='skripsi2.docx', ukuran=100)
    db.add(fb2)
    db.commit()
    _buat_naskah(folder_u / 'skripsi2.docx')
    # Tahap final untuk abstrak: tambah Bab IV-V ke naskah kedua.
    d_f = _Docx(str(folder_u / 'skripsi2.docx'))
    d_f.add_paragraph('BAB IV')
    d_f.add_paragraph('HASIL PENELITIAN DAN PEMBAHASAN')
    d_f.add_paragraph('Hasil uji menunjukkan pengaruh positif.')
    d_f.add_paragraph('BAB V')
    d_f.add_paragraph('PENUTUP')
    d_f.add_paragraph('Simpulan penelitian ini.')
    d_f.save(str(folder_u / 'skripsi2.docx'))
    saldo_abs = _saldo.sisa(db, u, seed=False)
    _asli_draf = BA.draf_abstrak
    BA.draf_abstrak = lambda *a, **k: None
    try:
        _asyncio.run(RB.bagian_awal_abstrak_ai(
            fid=fb2.id, request=_ReqPalsu(), u=u, db=db))
        st_abs = _tunggu_selesai(fb2.id)
    finally:
        BA.draf_abstrak = _asli_draf
    cek('rute abstrak: AI gagal -> pekerja gagal + 6 token kembali',
        st_abs is not None
        and st_abs.get('terakhir', {}).get('status') == 'gagal'
        and _saldo.sisa(db, u, seed=False) == saldo_abs,
        str(st_abs) + f" saldo {saldo_abs} -> {_saldo.sisa(db, u, seed=False)}")

    # Abstrak AI sukses (draf dipalsukan) -> tersimpan belum diterima.
    BA.draf_abstrak = lambda *a, **k: {
        'id': ['Abstrak isi.'], 'en': ['Abstract text.'],
        'kunci_id': ['a', 'b'], 'kunci_en': ['a', 'b']}
    try:
        _asyncio.run(RB.bagian_awal_abstrak_ai(
            fid=fb2.id, request=_ReqPalsu(), u=u, db=db))
        st_abs2 = _tunggu_selesai(fb2.id)
    finally:
        BA.draf_abstrak = _asli_draf
    cek('rute abstrak: AI sukses -> draf tersimpan, 6 token terpotong',
        st_abs2 is not None
        and st_abs2.get('terakhir', {}).get('status') == 'selesai'
        and (BA.muat_abstrak(db, fb2.id) or {}).get('diterima') is False
        and _saldo.sisa(db, u, seed=False) == saldo_abs - 6,
        str(st_abs2))
    hal_pakai = _asyncio.run(RB.bagian_awal_abstrak_pakai(
        fid=fb2.id, request=_ReqPalsu(), aksi='pakai', u=u, db=db))
    cek('rute abstrak: terima draf gratis (303)',
        hal_pakai.status_code == 303
        and (BA.muat_abstrak(db, fb2.id) or {}).get('diterima') is True)
    hal_manual = _asyncio.run(RB.bagian_awal_abstrak_manual(
        fid=fb2.id,
        request=_ReqForm({'abstrak_id': 'Tulisan sendiri.',
                          'abstrak_en': 'Own writing.',
                          'kunci_id': 'a, b', 'kunci_en': 'a, b'}),
        u=u, db=db))
    cek('rute abstrak: tulis sendiri gratis (303) + tersimpan diterima',
        hal_manual.status_code == 303
        and (BA.muat_abstrak(db, fb2.id) or {}).get('dari_ai') is False
        and (BA.muat_abstrak(db, fb2.id) or {}).get('diterima') is True)

    # Abstrak di tahap proposal ditolak.
    hal_abs_prop = _asyncio.run(RB.bagian_awal_abstrak_ai(
        fid=fb.id, request=_ReqPalsu(), u=u, db=db))
    cek('rute abstrak: tahap proposal ditolak (303 + pesan tahap final)',
        hal_abs_prop.status_code == 303
        and 'tahap%20final' in str(hal_abs_prop.headers.get('location', '')))

    # Status + template + wiring.
    st_s = _asyncio.run(RB.bagian_awal_status(file_id=fb.id, u=u, db=db))
    cek('rute: status melaporkan sudah ditempel',
        st_s.get('sudah_ditempel') is True, str(st_s))
    try:
        _asyncio.run(RB.bagian_awal_status(file_id=9999, u=u, db=db))
        cek('rute: status berkas orang lain 404', False, 'tidak 404')
    except Exception as e:
        cek('rute: status berkas orang lain 404',
            getattr(e, 'status_code', None) == 404, str(e))

    # Tempel gagal -> status + halaman menampilkan kegagalan (bukan
    # 'sedang ditempel' selamanya, uji live 16 Nov 2026).
    p_gagal = _proses.mulai(db, user_id=u.id, file_id=fb.id,
                            komentar=[BA.KOMENTAR_PROSES])
    _proses.tandai_gagal(
        p_gagal.kode,
        'Bab I tidak ditemukan di naskah, bagian awal tidak ditempel '
        'supaya tidak mengganda.')
    db.expire_all()
    st_g = _asyncio.run(RB.bagian_awal_status(file_id=fb.id, u=u, db=db))
    cek('rute gagal: status membawa pekerjaan gagal + galat + jenis tempel',
        st_g.get('terakhir', {}).get('status') == 'gagal'
        and 'Bab I tidak ditemukan' in st_g.get('terakhir', {}).get('galat', '')
        and st_g.get('terakhir', {}).get('jenis') == 'tempel', str(st_g))
    hal_g = _asyncio.run(RB.bagian_awal_halaman(
        fid=fb.id, request=_ReqPalsu(), u=u, db=db))
    badan_g = hal_g.body.decode('utf-8')
    cek('rute gagal: halaman menampilkan kegagalan + galat',
        hal_g.status_code == 200 and 'Tempel Bagian Awal gagal' in badan_g
        and 'Bab I tidak ditemukan' in badan_g, badan_g[:300])
    tpl = Path(ROOT, 'app', 'templates', 'bagian_awal.html').read_text()
    for frasa in ('Lengkapi Bagian Awal', 'Perbarui Bagian Awal',
                  'Periksa ulang', 'Saya sudah periksa',
                  'Tulis abstrak dengan AI (6 token)',
                  'Perbarui Daftar Isi (gratis)', 'Daftar cek',
                  'Tempel Bagian Awal gagal', "terakhir.status === 'gagal'",
                  "searchParams.delete('pesan')", 'id="gagal"',
                  'Yang dipertahankan'):
        cek(f'template: ada "{frasa}"', frasa in tpl)
    naskah_tpl = Path(ROOT, 'app', 'templates', 'naskah.html').read_text()
    cek('naskah: tombol Lengkapi Bagian Awal + tooltip ada',
        'Lengkapi Bagian Awal' in naskah_tpl
        and 'bagian depan skripsi' in naskah_tpl
        and 'ujian proposal' in naskah_tpl)
    main_src = Path(ROOT, 'app', 'main.py').read_text()
    cek('main: router bagian awal dipasang',
        'rute_bagian_awal.pasang(templates)' in main_src
        and 'rute_bagian_awal.router' in main_src)
    for berkas in ('app/bagian_awal.py', 'app/rute_bagian_awal.py',
                   'app/templates/bagian_awal.html'):
        isi = Path(ROOT, berkas).read_text()
        cek(f'0 em dash: {berkas}', '\u2014' not in isi)
    # naskah.html sudah punya em dash lama di <title> (bukan baris baru):
    # periksa hanya blok tombol yang ditambahkan.
    naskah_isi = Path(ROOT, 'app', 'templates', 'naskah.html').read_text()
    _awal = naskah_isi.find('Lengkapi Bagian Awal')
    cek('0 em dash: blok tombol naskah.html',
        '\u2014' not in naskah_isi[_awal - 400:_awal + 1200])

    # ── 15. Ukur nomor halaman pakai OnlyOffice (17 Nov 2026) ─────────
    import hashlib as _hl
    import hmac as _hm
    from app import ukur_onlyoffice as UO

    _XML_OK = ('<FileResult><FileUrl>http://docservice/cache/files/'
               'x/output.pdf</FileUrl><FileType>pdf</FileType>'
               '<Percent>100</Percent><EndConvert>True</EndConvert>'
               '</FileResult>')
    cek('ukur-oo: parse XML sukses -> FileUrl',
        UO.parse_jawaban_konversi(_XML_OK)
        == 'http://docservice/cache/files/x/output.pdf')
    try:
        UO.parse_jawaban_konversi('{"error": -8}')
        cek('ukur-oo: JSON error -8 -> UkurGagal', False, 'tidak melempar')
    except UO.UkurGagal as e:
        cek('ukur-oo: JSON error -8 -> UkurGagal', '-8' in str(e), str(e))
    try:
        UO.parse_jawaban_konversi('')
        cek('ukur-oo: jawaban kosong -> UkurGagal', False, 'tidak melempar')
    except UO.UkurGagal:
        cek('ukur-oo: jawaban kosong -> UkurGagal', True)
    try:
        UO.parse_jawaban_konversi('<FileResult></FileResult>')
        cek('ukur-oo: XML tanpa FileUrl -> UkurGagal', False,
            'tidak melempar')
    except UO.UkurGagal:
        cek('ukur-oo: XML tanpa FileUrl -> UkurGagal', True)

    cek('ukur-oo: host docservice ditulis ulang jadi oo-converter',
        UO.tulis_ulang_host_fileurl(
            'http://docservice/cache/files/x/output.pdf?token=a',
            'oo-converter')
        == 'http://oo-converter/cache/files/x/output.pdf?token=a')
    cek('ukur-oo: host oo-converter dibiarkan',
        UO.tulis_ulang_host_fileurl(
            'http://oo-converter/cache/files/x/output.pdf', 'oo-converter')
        == 'http://oo-converter/cache/files/x/output.pdf')
    cek('ukur-oo: host lain dibiarkan',
        UO.tulis_ulang_host_fileurl(
            'http://lain.invalid/x.pdf', 'oo-converter')
        == 'http://lain.invalid/x.pdf')

    _token_harap = _hm.new(
        b'uji-sementara-bukan-rahasia', b'126:12', _hl.sha256
    ).hexdigest()[:40]
    cek('ukur-oo: token unduh = HMAC SECRET_KEY atas fid:user_id',
        UO.token_unduh_berkas(126, 12) == _token_harap
        and len(_token_harap) == 40, _token_harap)
    _oo_env_lama = os.environ.get('EDUAI_OO_INTERNAL_URL')
    os.environ['EDUAI_OO_INTERNAL_URL'] = 'http://eduai-app:8000'
    try:
        _url_u = UO.url_unduh_berkas(126, 12)
    finally:
        if _oo_env_lama is None:
            os.environ.pop('EDUAI_OO_INTERNAL_URL', None)
        else:
            os.environ['EDUAI_OO_INTERNAL_URL'] = _oo_env_lama
    cek('ukur-oo: URL masukan = basis internal + /oo/unduh/{token}',
        _url_u == f'http://eduai-app:8000/oo/unduh/{_token_harap}', _url_u)

    cek('ukur-oo: rapikan hanya menyeragamkan akhir baris, '
        'footer di depan dipertahankan',
        UO._rapikan_teks_halaman('xi\r\nKATA PENGANTAR\r\nIsi')
        == 'xi\nKATA PENGANTAR\nIsi'
        and UO._rapikan_teks_halaman('24\r\n1.5 Judul\r\nIsi')
        == '24\n1.5 Judul\nIsi')
    cek('ukur-oo: rapikan tidak menyentuh baris isi',
        UO._rapikan_teks_halaman('BAB 1\r\nIsi') == 'BAB 1\nIsi'
        and UO._rapikan_teks_halaman('') == '')

    _pdf_bukti = (Path(ROOT, 'tests', 'fixtures', 'ukur_onlyoffice',
                      'f126_oo.pdf').read_bytes())
    _hal_oo = UO.teks_per_halaman_pdf(_pdf_bukti)
    cek('ukur-oo: PDF bukti dibaca = 191 halaman',
        len(_hal_oo) == 191, f'jumlah {len(_hal_oo)}')
    _baris11 = [b.strip() for b in _hal_oo[10].split('\n') if b.strip()]
    _awal11 = _baris11[1] if _baris11 and len(_baris11[0]) <= 3 \
        and _baris11[0] in ('xi', 'XI') else (_baris11[0] if _baris11
                                              else '')
    cek('ukur-oo: halaman 11 diawali KATA PENGANTAR (bukan nomor)',
        _awal11 == 'KATA PENGANTAR',
        _hal_oo[10][:60])
    cek('ukur-oo: halaman 53 memuat BAB 2',
        'BAB 2' in _hal_oo[52], _hal_oo[52][:80])
    _txt_bukti = (Path(ROOT, 'tests', 'fixtures', 'ukur_onlyoffice',
                       'f126_oo.txt').read_text(
                           encoding='utf-8', errors='ignore'))
    _hal_txt = _txt_bukti.split('\f')
    cek('ukur-oo: peta nomor dari teks bukti = footer editor (bukan WordCraft)',
        BA.nomor_footer_dari_render(
            _hal_txt, 'KATA PENGANTAR') == 'xi'
        and BA.nomor_footer_dari_render(
            _hal_txt,
            'BAB 1. Lanskap Pemasaran Digital: Ruang Lingkup, Batasan, '
            'dan Fondasi Konseptual') == 1
        and BA.nomor_footer_dari_render(
            _hal_txt,
            '1.5 Implikasi Struktural terhadap Pemetaan Bidang dan '
            'Sistematika Buku Referensi Ini') == 24
        and BA.nomor_footer_dari_render(
            _hal_txt,
            'BAB 2. Arsitektur Strategi Pemasaran Digital dan Dinamika '
            'Platform') == 32
        and BA.nomor_footer_dari_render(
            _hal_txt,
            '2.1 Definisi dan Konsep Kunci Strategi Pemasaran Digital '
            'Berbasis Platform') == 33)
    cek('ukur-oo: peta nomor dari PDF pypdfium2 = footer editor',
        BA.nomor_footer_dari_render(_hal_oo, 'KATA PENGANTAR') == 'xi'
        and BA.nomor_footer_dari_render(
            _hal_oo,
            'BAB 2. Arsitektur Strategi Pemasaran Digital dan Dinamika '
            'Platform') == 32)

    class _RespPalsu:
        def __init__(self, kode, teks='', konten=b''):
            self.status_code = kode
            self.text = teks
            self.content = konten

    class _PemanggilPalsu:
        """Peniru httpx sync: POST -> XML bukti, GET -> PDF bukti."""

        def __init__(self):
            self.panggilan = []

        def __call__(self, metode, url, **kw):
            self.panggilan.append((metode, url, kw))
            if metode == 'POST':
                return _RespPalsu(200, teks=_XML_OK)
            return _RespPalsu(200, konten=_pdf_bukti)

    _panggil = _PemanggilPalsu()
    _oo_url_asli = UO.OO_URL
    UO.OO_URL = 'http://oo-converter'
    try:
        _hal_ukur = UO.ukur_halaman(
            fid=126, user_id=12, nama_berkas='f126_v3.docx',
            pemanggil=_panggil)
    finally:
        UO.OO_URL = _oo_url_asli
    _post = [p for p in _panggil.panggilan if p[0] == 'POST']
    _get = [p for p in _panggil.panggilan if p[0] == 'GET']
    cek('ukur-oo: alur penuh (POST XML + GET PDF) -> 191 halaman',
        len(_hal_ukur) == 191 and 'BAB 2' in _hal_ukur[52],
        f'halaman {len(_hal_ukur)}')
    cek('ukur-oo: POST ke ConvertService.ashx + URL /oo/unduh + token',
        len(_post) == 1
        and _post[0][1] == 'http://oo-converter/ConvertService.ashx'
        and _post[0][2].get('json', {}).get('async') is False
        and _post[0][2].get('json', {}).get('outputtype') == 'pdf'
        and '/oo/unduh/' in _post[0][2].get('json', {}).get('url', '')
        and bool(_post[0][2].get('json', {}).get('token')),
        str(_post)[:300])
    cek('ukur-oo: GET PDF memakai host oo-converter (bukan docservice)',
        len(_get) == 1
        and _get[0][1].startswith('http://oo-converter/cache/files/'),
        str(_get)[:200])
    cek('ukur-oo: hasil hanya daftar halaman (URL tidak disimpan)',
        isinstance(_hal_ukur, list)
        and not any('FileUrl' in (h or '') or 'docservice' in (h or '')
                    for h in _hal_ukur))

    class _PemanggilGagal(_PemanggilPalsu):
        def __call__(self, metode, url, **kw):
            self.panggilan.append((metode, url, kw))
            if metode == 'POST':
                return _RespPalsu(200, teks='{"error": -8}')
            return _RespPalsu(404)
    UO.OO_URL = 'http://oo-converter'
    try:
        UO.ukur_halaman(fid=126, user_id=12, nama_berkas='x.docx',
                        pemanggil=_PemanggilGagal())
        cek('ukur-oo: ConvertService error -8 -> UkurGagal', False,
            'tidak melempar')
    except UO.UkurGagal as e:
        cek('ukur-oo: ConvertService error -8 -> UkurGagal', '-8' in str(e),
            str(e))
    finally:
        UO.OO_URL = _oo_url_asli

    class _Pemanggil404(_PemanggilPalsu):
        def __call__(self, metode, url, **kw):
            self.panggilan.append((metode, url, kw))
            if metode == 'POST':
                return _RespPalsu(200, teks=_XML_OK)
            return _RespPalsu(404)
    UO.OO_URL = 'http://oo-converter'
    try:
        UO.ukur_halaman(fid=126, user_id=12, nama_berkas='x.docx',
                        pemanggil=_Pemanggil404())
        cek('ukur-oo: unduh PDF 404 -> UkurGagal', False, 'tidak melempar')
    except UO.UkurGagal as e:
        cek('ukur-oo: unduh PDF 404 -> UkurGagal', '404' in str(e), str(e))
    finally:
        UO.OO_URL = _oo_url_asli
    _oo_url_kosong = UO.OO_URL
    UO.OO_URL = ''
    try:
        UO.ukur_halaman(fid=126, user_id=12, nama_berkas='x.docx',
                        pemanggil=_PemanggilPalsu())
        cek('ukur-oo: OO_URL kosong -> UkurGagal', False, 'tidak melempar')
    except UO.UkurGagal:
        cek('ukur-oo: OO_URL kosong -> UkurGagal', True)
    finally:
        UO.OO_URL = _oo_url_kosong

    # perbarui_nomor_daftar: jalur default baru butuh fid/user_id.
    _docx_u = Path(TMP) / 'naskah_u.docx'
    _buat_naskah(_docx_u)
    BA.tulis_bagian_awal(_docx_u, [
        {'kunci': k, 'judul': j, 'baris': b, 'xml': None, 'ppr': ''}
        for k, j, b in BA.susun_bagian(
            {'nama': 'Siti Aminah', 'judul': 'Judul Saya'}, 'proposal',
            {'daftar_isi': BA.entri_daftar_isi(PETA_BAB123)})])
    _r_tanpa = BA.perbarui_nomor_daftar(_docx_u)
    cek('ukur-oo: tanpa fid/user_id -> gagal jujur (bukan WordCraft)',
        _r_tanpa.get('ok') is False
        and 'file_id dan user_id' in _r_tanpa.get('sebab', ''),
        str(_r_tanpa))
    _uo_asli = UO.ukur_halaman

    def _uo_gagal(**k):
        raise UO.UkurGagal('ConvertService menolak: error -8.')
    UO.ukur_halaman = _uo_gagal
    try:
        _teks_sebelum = _teks_docx(_docx_u)
        _r_gagal_oo = BA.perbarui_nomor_daftar(
            _docx_u, fid=126, user_id=12)
        _teks_sesudah = _teks_docx(_docx_u)
    finally:
        UO.ukur_halaman = _uo_asli
    cek('ukur-oo: ConvertService gagal -> gagal jujur, docx tidak berubah',
        _r_gagal_oo.get('ok') is False
        and 'OnlyOffice' in _r_gagal_oo.get('sebab', '')
        and _teks_sebelum == _teks_sesudah, str(_r_gagal_oo))
    UO.ukur_halaman = lambda **k: render2
    try:
        _r_ukur = BA.perbarui_nomor_daftar(_docx_u, fid=126, user_id=12)
        _teks_ukur = _teks_docx(_docx_u)
    finally:
        UO.ukur_halaman = _uo_asli
    cek('ukur-oo: ukur stub -> nomor ditulis dari render OnlyOffice',
        _r_ukur.get('ok') and _r_ukur.get('diperbarui', 0) >= 2
        and 'BAB I  1' in _teks_ukur and 'BAB II  2' in _teks_ukur,
        str(_r_ukur))

    # Paksa simpan bila disunting (pembantu rute, async).
    import app.models as _mdl2
    _sesi_row = _mdl2.SesiEdit(user_id=u.id, file_id=fb.id,
                               kunci_oo='e9v9')
    db.add(_sesi_row)
    db.commit()
    _fs_asli = _RB.onlyoffice.forcesave

    async def _fs_ok(kunci, uid):
        return {'ok': True, 'pesan': 'perintah diterima', 'dicoba': True}

    async def _fs_gagal(kunci, uid):
        return {'ok': False, 'pesan': 'HTTP 500', 'dicoba': True}
    _RB.onlyoffice.forcesave = _fs_ok
    try:
        _ps_ok = _asyncio.run(_RB._paksa_simpan_bila_diedit(db, u.id, fb.id))
    finally:
        _RB.onlyoffice.forcesave = _fs_asli
    cek('ukur-oo: sesi aktif + forcesave ok -> perlu + ok',
        _ps_ok.get('perlu') is True and _ps_ok.get('ok') is True,
        str(_ps_ok))
    _RB.onlyoffice.forcesave = _fs_gagal
    try:
        _ps_gagal = _asyncio.run(
            _RB._paksa_simpan_bila_diedit(db, u.id, fb.id))
    finally:
        _RB.onlyoffice.forcesave = _fs_asli
    cek('ukur-oo: sesi aktif + forcesave gagal -> ok False + sebab',
        _ps_gagal.get('perlu') is True and _ps_gagal.get('ok') is False
        and 'paksa simpan' in _ps_gagal.get('sebab', '').lower(),
        str(_ps_gagal))
    db.delete(_sesi_row)
    db.commit()
    _ps_tidak = _asyncio.run(_RB._paksa_simpan_bila_diedit(db, u.id, fb.id))
    cek('ukur-oo: tanpa sesi edit -> tidak perlu dipaksa, ok',
        _ps_tidak.get('perlu') is False and _ps_tidak.get('ok') is True,
        str(_ps_tidak))

    # Rute Perbarui Daftar Isi: titip ke pekerja latar, bukan request web.
    # Render realistis untuk docx tempel: penanda bab telanjang di
    # baris sendiri (paragraf docx terpisah), entri daftar Arab
    # ("BAB 1. PENDAHULUAN") dicocokkan lewat penanda telanjang.
    render_fb = ['Sampul', 'KATA PENGANTAR', 'DAFTAR ISI',
                 'BAB I\nPENDAHULUAN\n1.1 Latar Belakang\nlatar',
                 'BAB II\nTINJAUAN PUSTAKA\n2.1 Teori tentang Variabel Y\nteori',
                 'BAB III\nMETODE PENELITIAN\n3.1 Jenis dan Desain Penelitian\nmetode']

    UO.ukur_halaman = lambda **k: render_fb
    try:
        _hal_pd = _asyncio.run(RB.bagian_awal_perbarui_daftar(
            fid=fb.id, request=_ReqPalsu(), u=u, db=db))
        _st_pd = _tunggu_selesai(fb.id)
    finally:
        UO.ukur_halaman = _uo_asli
    _teks_pd = _teks_docx(folder_u / 'skripsi.docx')
    cek('rute daftar: 303 + pekerja selesai + jenis daftar',
        _hal_pd.status_code == 303 and _st_pd is not None
        and _st_pd.get('terakhir', {}).get('status') == 'selesai'
        and _st_pd.get('terakhir', {}).get('jenis') == 'daftar',
        str(_st_pd))
    _idx_pd = _teks_pd.find('DAFTAR ISI')
    cek('rute daftar: nomor ditulis ke docx (BAB 1 = 1)',
        'BAB 1. PENDAHULUAN  1' in _teks_pd
        and '1.1 Latar Belakang  1' in _teks_pd,
        _teks_pd[_idx_pd:_idx_pd + 500])
    _p_jalan = _proses.mulai(db, user_id=u.id, file_id=fb.id,
                             komentar=[BA.KOMENTAR_PROSES_DAFTAR])
    _hal_dobel = _asyncio.run(RB.bagian_awal_perbarui_daftar(
        fid=fb.id, request=_ReqPalsu(), u=u, db=db))
    cek('rute daftar: tekan 2x saat jalan ditahan sopan',
        _hal_dobel.status_code == 303
        and 'Masih%20ada%20pekerjaan' in str(
            _hal_dobel.headers.get('location', '')),
        str(_hal_dobel.headers.get('location')))
    _proses.tandai_selesai(_p_jalan.kode, hasil='uji penahan')
    UO.ukur_halaman = _uo_gagal
    try:
        _asyncio.run(RB.bagian_awal_perbarui_daftar(
            fid=fb.id, request=_ReqPalsu(), u=u, db=db))
        _st_pd_gagal = _tunggu_selesai(fb.id)
    finally:
        UO.ukur_halaman = _uo_asli
    cek('rute daftar gagal: pekerja gagal + jenis daftar + galat jujur',
        _st_pd_gagal is not None
        and _st_pd_gagal.get('terakhir', {}).get('status') == 'gagal'
        and _st_pd_gagal.get('terakhir', {}).get('jenis') == 'daftar'
        and 'OnlyOffice' in _st_pd_gagal.get('terakhir', {}).get('galat', ''),
        str(_st_pd_gagal))
    _hal_pd_gagal = _asyncio.run(RB.bagian_awal_halaman(
        fid=fb.id, request=_ReqPalsu(), u=u, db=db))
    _badan_pd_gagal = _hal_pd_gagal.body.decode('utf-8')
    cek('rute daftar gagal: halaman menampilkan kegagalan + nomor lama',
        _hal_pd_gagal.status_code == 200
        and 'Perbarui Daftar gagal' in _badan_pd_gagal
        and 'Nomor lama dipertahankan' in _badan_pd_gagal,
        _badan_pd_gagal[:300])

    # Rute daftar gagal karena paksa simpan (berkas sedang disunting).
    _sesi_row2 = _mdl2.SesiEdit(user_id=u.id, file_id=fb.id,
                                kunci_oo='e9v9')
    db.add(_sesi_row2)
    db.commit()
    _RB.onlyoffice.forcesave = _fs_gagal
    try:
        _asyncio.run(RB.bagian_awal_perbarui_daftar(
            fid=fb.id, request=_ReqPalsu(), u=u, db=db))
        _st_pd_fs = _tunggu_selesai(fb.id)
    finally:
        _RB.onlyoffice.forcesave = _fs_asli
        db.delete(_sesi_row2)
        db.commit()
    cek('rute daftar gagal: paksa simpan gagal -> pekerja gagal jujur',
        _st_pd_fs is not None
        and _st_pd_fs.get('terakhir', {}).get('status') == 'gagal'
        and 'Paksa simpan' in _st_pd_fs.get('terakhir', {}).get('galat', ''),
        str(_st_pd_fs))
    _tpl_oo = Path(ROOT, 'app', 'templates', 'bagian_awal.html').read_text()
    for frasa in ('Perbarui Daftar gagal', 'Nomor lama dipertahankan',
                  "j.terakhir.jenis === 'daftar'"):
        cek(f'template: ada "{frasa}"', frasa in _tpl_oo)
    for berkas in ('app/ukur_onlyoffice.py', 'app/bagian_awal.py',
                   'app/rute_bagian_awal.py',
                   'app/templates/bagian_awal.html'):
        isi = Path(ROOT, berkas).read_text()
        cek(f'0 em dash: {berkas}', '\u2014' not in isi)

    # ── 16. Gema subbab di Daftar Isi (17 Nov 2026) ───────────────────
    # Uji live file 126: nomor sudah benar (OnlyOffice), tapi Daftar Isi
    # memuat dua baris ganda: di bawah '1.2 ...' muncul 'SUB-BAB ...'
    # (judul sama), dan '1.4 ...' tertulis dua kali (sekali bernomor,
    # sekali telanjang). Akar: badan menulis judul yang sama dua kali
    # berurutan (judul bernomor lalu gema), peta melabeli keduanya
    # 'subbab'. Judul 1.1 juga terpotong baris ('... Digital' lalu
    # 'dalam Ekosistem ...'). Data di bawah memakai judul ASLI file 126.
    _BARIS_GEMA = [
        'KATA PENGANTAR',
        'Lanskap Pemasaran Digital: Ruang Lingkup, Batasan, dan Fondasi Konseptual',
        '1.1 Definisi dan Konsep Kunci Pemasaran Digital',
        'dalam Ekosistem Ekonomi Digital',
        '1.2 Perkembangan Teori dan Kajian Transisi dari Pemasaran Tradisional ke Digital',
        'SUB-BAB Perkembangan Teori dan Kajian Transisi dari Pemasaran Tradisional ke Digital',
        '1.3 Perbandingan Kritis Paradigma Pemasaran Transaksional dan Relasional di Era Digital',
        '1.4 Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital',
        'Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital',
        '1.5 Implikasi Struktural terhadap Pemetaan Bidang dan Sistematika Buku Referensi Ini',
        'Ringkasan Bab',
        'Arsitektur Strategi Pemasaran Digital dan Dinamika Platform',
        '2.1 Definisi dan Konsep Kunci Strategi Pemasaran Digital Berbasis Platform',
        'Ringkasan Bab',
    ]
    _LABEL_GEMA = {str(i): 'subbab' for i in range(len(_BARIS_GEMA))}
    _LABEL_GEMA['0'] = 'bab'
    _BAB_GEMA = ['0', 'BAB 1', '1.1', 'BAB 1', '1.2', 'BAB 1', '1.3',
                 '1.4', 'BAB 1', '1.5', 'BAB 1', 'BAB 2', '2.1', 'BAB 2']
    _DAFTAR_GEMA = [
        {'id': f'g{i}', 'bab': _BAB_GEMA[i],
         'subbab': '', 'judul_bab': t, 'sub_judul': ''}
        for i, t in enumerate(_BARIS_GEMA)]
    _PETA_GEMA = {'peta_surveyor': {
        'baris': _BARIS_GEMA, 'label': _LABEL_GEMA,
        'hakim': {'jumlah_ragu': 0, 'jumlah_curiga': 0}},
        'daftar': _DAFTAR_GEMA}
    _BADAN_GEMA = [
        'BAB 1',
        'Lanskap Pemasaran Digital: Ruang Lingkup, Batasan, dan Fondasi Konseptual',
        '1.1 Definisi dan Konsep Kunci Pemasaran Digital dalam Ekosistem Ekonomi Digital',
        'Isi bab satu.',
        '1.2 Perkembangan Teori dan Kajian Transisi dari Pemasaran Tradisional ke Digital',
        'SUB-BAB Perkembangan Teori dan Kajian Transisi dari Pemasaran Tradisional ke Digital',
        'Isi subbab 1.2.',
        '1.4 Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital',
        'Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital',
        'Isi subbab 1.4.',
    ]
    _entri_gema = BA.entri_daftar_isi(_PETA_GEMA,
                                      paragraf_badan=_BADAN_GEMA)
    _judul_gema = [e['judul'] for e in _entri_gema]
    cek('regresi gema: 1.2 dan 1.4 masing-masing satu baris (tanpa ganda)',
        _judul_gema.count(
            '1.2 Perkembangan Teori dan Kajian Transisi dari Pemasaran Tradisional ke Digital') == 1
        and _judul_gema.count(
            '1.4 Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital') == 1,
        str(_judul_gema))
    cek('regresi gema: baris SUB-BAB dan judul telanjang tidak masuk Daftar Isi',
        not any(j.startswith('SUB-BAB') for j in _judul_gema)
        and 'Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital'
        not in _judul_gema,
        str(_judul_gema))
    cek('regresi gema: lanjutan judul terpotong baris tidak jadi baris sendiri',
        'dalam Ekosistem Ekonomi Digital' not in _judul_gema
        and _judul_gema.count('1.1 Definisi dan Konsep Kunci Pemasaran Digital') == 1,
        str(_judul_gema))
    cek('regresi gema: judul sah yang berulang tiap bab tetap ada (Ringkasan Bab x2)',
        _judul_gema.count('Ringkasan Bab') == 2
        and _judul_gema.count(
            'BAB 1. Lanskap Pemasaran Digital: Ruang Lingkup, Batasan, dan Fondasi Konseptual') == 1
        and _judul_gema.count(
            'BAB 2. Arsitektur Strategi Pemasaran Digital dan Dinamika Platform') == 1,
        str(_judul_gema))
    _entri_tanpa_badan = BA.entri_daftar_isi(_PETA_GEMA)
    _judul_tanpa_badan = [e['judul'] for e in _entri_tanpa_badan]
    cek('regresi gema: tanpa badan, gema tetap dibuang tapi lanjutan dibiarkan (tidak hilang diam-diam)',
        not any(j.startswith('SUB-BAB') for j in _judul_tanpa_badan)
        and 'Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital'
        not in _judul_tanpa_badan
        and 'dalam Ekosistem Ekonomi Digital' in _judul_tanpa_badan,
        str(_judul_tanpa_badan))
    cek('regresi gema: normalisasi judul menyamakan nomor dan SUB-BAB',
        BA._judul_subbab_normal(
            'SUB-BAB Perkembangan Teori dan Kajian Transisi dari Pemasaran Tradisional ke Digital')
        == BA._judul_subbab_normal(
            '1.2 Perkembangan Teori dan Kajian Transisi dari Pemasaran Tradisional ke Digital')
        and BA._judul_subbab_normal('1.4 Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital')
        == BA._judul_subbab_normal('Posisi dan Sintesis Penulis atas Ontologi Pemasaran Digital'))


if __name__ == '__main__':
    jalankan()
    print(f'\nHASIL: {len(LULUS)} lulus, {len(GAGAL)} gagal')
    if GAGAL:
        print('GAGAL: ' + ', '.join(GAGAL))
    sys.exit(1 if GAGAL else 0)
