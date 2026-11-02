"""Wiring cover dinamis, lapisan sambung (bukan modul desain).

Modul desain ada di root repo: susun_cover_dinamis.py. Modul ini hanya
menghubungkannya ke job buku yang sudah selesai, dengan aturan dari
keputusan Bos 2 Nov 2026 17:17 WIB:
- Bahan wide, 1 generasi, bukan portrait.
- Tombol Gambar Lain disembunyikan dulu, jadi tidak ada di sini.
- DOCX tidak diperbarui, cover final hanya PNG terpisah.
- File siap cetak UNESCO nanti saja, preview di sini digital saja.
- UI di halaman buku_selesai, bukan halaman baru.
- Foto dan bio per job dulu, bukan profil lintas buku.

Prinsip yang tidak boleh dilanggar di sini:
- Gagal cover tidak menggagalkan buku, tidak memicu refund, dan tidak
  mengubah DOCX yang sudah jadi.
- Status cover disimpan di hasil_json dengan MERGE kunci, bukan
  overwrite. Kunci lama (judul, bab, kata, docx, folder, file_id)
  harus tetap ada sesudah update cover.
- Bahan dan preview tidak boleh menimpa cover.png, karena cover.png
  dipakai rakitan DOCX sebagai halaman pertama.
- Nama berkas dari user tidak pernah dipakai mentah sebagai path.
  Semua path cover dibangun dari folder job dan nama yang dikunci di
  sini, untuk mencegah path traversal lewat parameter nama.
"""
import os
import shutil

KUNCI_COVER = (
    'cover_status', 'cover_bahan', 'cover_preview', 'cover_pilihan',
    'cover_depan', 'cover_belakang', 'cover_foto', 'cover_bio',
    'cover_gagal', 'cover_sinopsis',
)

NAMA_BAHAN = 'cover_bahan.png'
NAMA_DEPAN = 'cover_depan.png'
NAMA_BELAKANG = 'cover_belakang.png'
NAMA_FOTO = 'foto_penulis.png'
NAMA_STATUS = 'cover_status.json'

SINOPSIS_PLACEHOLDER = '[Sinopsis buku, diisi dari isi buku saat produksi]'
BIO_PLACEHOLDER = '[Bio penulis belum diisi]'


def _modul_cover():
    import sys
    akar = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if akar not in sys.path:
        sys.path.insert(0, akar)
    import susun_cover_dinamis as m
    return m


def perbarui_hasil_cover(hasil, kunci_baru):
    """Merge kunci cover ke hasil lama, tanpa menghapus kunci lama.

    Pure function, mudah diuji tanpa database. `hasil` boleh dict atau
    bukan dict, bila bukan dict mulai dari dict kosong. Hanya kunci di
    KUNCI_COVER yang diambil dari kunci_baru, kunci lain dari pemanggil
    tidak ikut masuk ke hasil, supaya hasil_json tidak tercemar.
    """
    lama = dict(hasil) if isinstance(hasil, dict) else {}
    for k in KUNCI_COVER:
        if k in kunci_baru:
            lama[k] = kunci_baru[k]
    return lama


def _judul_baris(judul):
    kata = (judul or '').strip().split()
    if len(kata) <= 2:
        return [judul or 'Buku']
    tengah = len(kata) // 2
    return [' '.join(kata[:tengah]), ' '.join(kata[tengah:])]


def _folder_aman(folder):
    if not folder or not os.path.isdir(folder):
        raise ValueError('Folder hasil buku tidak ditemukan')
    return folder


def buat_preview(folder, jenis, tema, judul, penulis, terbit,
                 bahan_path, sinopsis='', foto_path=None, bio=''):
    """Susun 3 preview depan dan 1 belakang dari bahan yang sudah ada.

    Tidak generate gambar di sini, bahan harus sudah ada. Return dict
    kunci cover yang siap di-merge ke hasil_json lewat
    perbarui_hasil_cover. Bila bahan tidak ada, raise ValueError dan
    pemanggil yang mencatat cover_gagal, bukan modul ini yang menelan
    galat diam-diam.
    """
    folder = _folder_aman(folder)
    if not bahan_path or not os.path.exists(bahan_path):
        raise ValueError('Bahan cover tidak ditemukan')
    m = _modul_cover()
    jenis_kunci = jenis if jenis in m.LABEL_JENIS else 'umum'
    konfig = m.pilih_cover(jenis_kunci, tema or '', judul or '', '')
    galat = m.cek_cover(konfig, judul or '', penulis or '', terbit or '')
    if galat:
        raise ValueError('Cover tidak lolos cek: ' + '; '.join(galat))
    previews = m.preview_depan(
        bahan_path, jenis_kunci, konfig['label'],
        _judul_baris(judul), penulis or 'Nama Penulis',
        terbit or 'PT Bayana Hasana Duna', konfig['keluarga'],
        folder, 'preview')
    belakang_path = os.path.join(folder, 'preview_belakang.png')
    m.susun_belakang(
        judul or 'Buku', (sinopsis or '').strip() or SINOPSIS_PLACEHOLDER,
        foto_path if (foto_path and os.path.exists(foto_path)) else None,
        (bio or '').strip() or '',
        konfig['aksen'], konfig['atas'], belakang_path)
    return {
        'cover_status': 'preview_siap',
        'cover_bahan': bahan_path,
        'cover_preview': previews,
        'cover_pilihan': '',
        'cover_depan': '',
        'cover_belakang': belakang_path,
        'cover_foto': foto_path if (foto_path and os.path.exists(foto_path)) else '',
        'cover_bio': (bio or '').strip(),
        'cover_gagal': '',
        'cover_sinopsis': (sinopsis or '').strip() or SINOPSIS_PLACEHOLDER,
    }


def pilih_preview(folder, hasil, pilihan):
    """Pilih 1 preview jadi final, idempotent, tanpa mengubah DOCX.

    `pilihan` harus nama varian yang ada di cover_preview job itu,
    misalnya klasik, minimal, atau foto_penuh_atas. Pilihan liar
    ditolak dengan ValueError, tanpa mengubah hasil. Final depan
    disalin dari preview yang dipilih, final belakang disalin dari
    preview_belakang yang sudah mengikuti palet keluarga yang sama,
    karena palet tidak berubah per varian. Bila user menutup tanpa
    memilih, pemanggil memakai pilihan klasik dengan catatan default,
    bukan fungsi ini yang menebak.
    """
    folder = _folder_aman(folder)
    previews = (hasil or {}).get('cover_preview') or []
    if not pilihan or pilihan not in ('klasik', 'minimal', 'editorial',
                                      'bold', 'ilustrasi_tematik',
                                      'foto_penuh_atas'):
        raise ValueError('Pilihan cover tidak dikenal')
    sumber = None
    for p in previews:
        if os.path.basename(p) == f'preview-{pilihan}.png' or \
                p.endswith(f'-{pilihan}.png'):
            sumber = p
            break
    if not sumber or not os.path.exists(sumber):
        raise ValueError('Preview yang dipilih tidak ditemukan')
    depan = os.path.join(folder, NAMA_DEPAN)
    belakang = os.path.join(folder, NAMA_BELAKANG)
    shutil.copyfile(sumber, depan)
    sumber_belakang = (hasil or {}).get('cover_belakang') or ''
    if sumber_belakang and os.path.exists(sumber_belakang):
        shutil.copyfile(sumber_belakang, belakang)
    else:
        belakang = ''
    return perbarui_hasil_cover(hasil, {
        'cover_status': 'dipilih',
        'cover_pilihan': pilihan,
        'cover_depan': depan,
        'cover_belakang': belakang,
        'cover_gagal': '',
    })


def lengkapi_belakang(folder, hasil, foto_path=None, bio=None):
    """Buat ulang sampul belakang saja dari foto dan bio baru.

    Dipakai tombol Lengkapi Sampul di halaman hasil. Tidak membuat
    ulang buku dan tidak membuat ulang sampul depan. Foto disimpan
    sebagai foto_penulis.png di folder job, bio disimpan sebagai teks
    di hasil_json. Bila foto None, foto lama dipakai bila ada, bila
    tidak ada pakai placeholder siluet di modul. Bila bio None, bio
    lama dipakai.
    """
    folder = _folder_aman(folder)
    m = _modul_cover()
    foto_final = (hasil or {}).get('cover_foto') or ''
    if foto_path and os.path.exists(foto_path):
        foto_final = os.path.join(folder, NAMA_FOTO)
        shutil.copyfile(foto_path, foto_final)
    bio_final = (hasil or {}).get('cover_bio') or ''
    if bio is not None:
        bio_final = (bio or '').strip()
    # Palet belakang diambil dari config terakhir bila bisa, bila tidak
    # pakai palet umum tosca, supaya belakang tetap jadi walau config
    # lama tidak tersimpan. Judul dan sinopsis diambil dari hasil bila
    # ada, bila tidak pakai placeholder yang jelas.
    judul = (hasil or {}).get('judul') or 'Buku'
    sinopsis = (hasil or {}).get('cover_sinopsis') or SINOPSIS_PLACEHOLDER
    # Keluarga tema tidak tersimpan di hasil lama, jadi pakai umum.
    # Ini hanya fallback untuk tombol lengkapi, preview awal tetap
    # memakai keluarga tema yang benar dari buat_preview.
    palet = m.PALET_KELUARGA['umum']
    belakang_path = os.path.join(folder, NAMA_BELAKANG)
    m.susun_belakang(
        judul, sinopsis,
        foto_final if (foto_final and os.path.exists(foto_final)) else None,
        bio_final, palet['aksen'], palet['atas'], belakang_path)
    return perbarui_hasil_cover(hasil, {
        'cover_belakang': belakang_path,
        'cover_foto': foto_final,
        'cover_bio': bio_final,
        'cover_gagal': '',
    })


def buat_bahan_wide(folder, brief):
    """Generate bahan wide lewat pipeline, 1 generasi, atau None.

    Fungsi ini sengaja mengimpor pipeline secara malas, supaya modul
    cover tetap bisa diuji tanpa kunci provider. Gagal generate
    mengembalikan None, bukan raise, karena pemanggil rute yang
    mencatat cover_gagal dan buku tetap bisa diunduh.
    """
    folder = _folder_aman(folder)
    try:
        import buku_umum_pipeline as _pipe
    except Exception:
        return None
    try:
        return _pipe.generate_gambar_cover_wide(
            brief, os.path.join(folder, NAMA_BAHAN))
    except Exception:
        return None
