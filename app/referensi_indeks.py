"""Bantu rakit buku referensi — glosarium, pustaka, dan indeks bernomor.

Dipakai HANYA jalur kartu buku-referensi di app/penyusunan_buku.susun().
Tidak mengimpor modul host (/opt/data) — stdlib + python-docx saja.

Alur (sesudah S.susun_buku, sebelum/sesudah isi_nomor):
  1. kumpulkan_istilah(): petik blok [ISTILAH BARU] dari berkas bab txt
     -> glosarium {istilah: definisi}; blok DIHAPUS dari txt supaya tidak
     tercetak mentah di buku (rakit membaca txt yang sama).
  2. kumpulkan_pustaka(): gabung refs_bab{n}.json dari folder visual PER
     BAB (keluar/bab{n}/visual/) — rakit HANYA mencari di satu folder
     visual, sehingga pustaka bab-bab awal hilang tanpa langkah ini
     (cacat lama jalur umum, tidak diubah di sini).
  3. kumpulkan_nama(): nama keluarga dari string APA pustaka (entri
     Indeks Nama v1: penulis pertama + rekan yang tercantum APA).
  4. isi_indeks(): sesudah isi_nomor, isi nomor halaman entri indeks di
     docx dari teks per halaman sidecar; halaman TOC dan halaman
     back-matter DIKECUALIKAN dari pencarian.
"""

import json
import os
import re

# Judul seksi yang dikenali sebagai pembatas saat mengganti entri indeks.
_SEKSI = ('GLOSARIUM', 'INDEKS SUBJEK', 'INDEKS NAMA', 'INDEKS',
          'DAFTAR PUSTAKA', 'DAFTAR SINGKATAN', 'TENTANG PENULIS')


def _path_bab(keluar, n):
    """Berkas txt satu bab (dua kemungkinan letak, seperti susun())."""
    utama = os.path.join(keluar, f'bab{n}', f'bab{n}.txt')
    if os.path.exists(utama):
        return utama
    return os.path.join(keluar, f'bab{n}.txt')


def kumpulkan_istilah(keluar, outline):
    """Petik [ISTILAH BARU] dari txt bab -> (glosarium, jumlah_diambil).

    Format blok (dari prompt architect): baris penanda '[ISTILAH BARU]'
    diikuti baris 'Istilah: definisi'. Blok berakhir di baris kosong,
    penanda '[' lain, atau judul sub '###'. Baris yang tidak berpola
    'Istilah: definisi' DIBIARKAN (tidak dihapus) — konservatif.
    """
    glos = {}
    diambil = 0
    for n in sorted(k for k in outline if isinstance(k, int)):
        path = _path_bab(keluar, n)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            baris = f.read().splitlines()
        keluar_baris = []
        i = 0
        while i < len(baris):
            b = baris[i].strip()
            if b.startswith('[ISTILAH BARU]'):
                # Sisa baris penanda setelah ']' diabaikan; kumpulkan
                # baris istilah berikutnya.
                i += 1
                while i < len(baris):
                    t = baris[i].strip()
                    if (not t or t.startswith('[')
                            or t.startswith('###')):
                        break
                    if ':' in t:
                        istilah, definisi = t.split(':', 1)
                        istilah, definisi = istilah.strip(), definisi.strip()
                        if istilah and definisi and istilah not in glos:
                            glos[istilah] = definisi
                            diambil += 1
                        i += 1
                    else:
                        break
                # Baris penanda + baris istilah TIDAK ditulis kembali
                # (= blok terhapus dari txt); baris pemutus (kosong/'###')
                # tetap diproses normal oleh loop.
                continue
            keluar_baris.append(baris[i])
            i += 1
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(keluar_baris) + ('\n' if keluar_baris else ''))
    return glos, diambil


def kumpulkan_pustaka(keluar, outline):
    """Gabung refs_bab{n}.json per bab (dedup, urut kemunculan)."""
    hasil, lihat = [], set()
    for n in sorted(k for k in outline if isinstance(k, int)):
        for cand in (os.path.join(keluar, f'bab{n}', 'visual',
                                  f'refs_bab{n}.json'),
                     os.path.join(keluar, 'visual', f'refs_bab{n}.json')):
            if not os.path.exists(cand):
                continue
            try:
                with open(cand, encoding='utf-8') as f:
                    data = json.load(f)
            except Exception:
                continue
            if not isinstance(data, list):
                continue
            for entri in data:
                if isinstance(entri, str) and entri.strip() \
                        and entri not in lihat:
                    lihat.add(entri)
                    hasil.append(entri)
            break
    return hasil


def kumpulkan_nama(daftar_pustaka):
    """Nama keluarga dari string APA ('Nama, I., & Rekan, J. (2024)...').

    Ambil segmen sebelum ' (Tahun)'; pecah koma/'&'; buang inisial
    ('J.', 'A. B.') dan 'et al'. Urut kemunculan, dedup.
    """
    nama, lihat = [], set()
    for entri in (daftar_pustaka or []):
        m = re.search(r'^(.*?)\s*\(\d{4}\)', entri)
        segmen = m.group(1) if m else entri.split('(')[0]
        for tok in re.split(r',|&', segmen):
            t = tok.strip().rstrip('.')
            if not t or t.lower().startswith('et al'):
                continue
            if re.fullmatch(r'[A-Z](?:\s+[A-Z])?', t):
                continue  # inisial, bukan nama
            if t not in lihat:
                lihat.add(t)
                nama.append(t)
    return nama


def _teks_halaman_normal(teks_per_halaman):
    """Normalisasi masukan sidecar -> {nomor_halaman: teks}.

    Sidecar mengirim list (indeks 0 = halaman 1); dict diterima juga
    (kunci string JSON dinormalisasi ke int).
    """
    if isinstance(teks_per_halaman, dict):
        return {int(k): (v or '') for k, v in teks_per_halaman.items()}
    return {i + 1: (t or '') for i, t in enumerate(teks_per_halaman or [])}


def _rentang_isi(halaman):
    """(halaman_isi_awal, halaman_back_matter_awal).

    Isi mulai dari halaman pertama yang memuat baris 'BAB N'; back-matter
    mulai dari halaman pertama sesudahnya yang memuat baris seksi
    (Glosarium/Indeks/Daftar Pustaka/dll). TOC (sebelum BAB pertama)
    otomatis di luar rentang.
    """
    awal, back = None, None
    for p in sorted(halaman):
        teks = halaman[p]
        if awal is None:
            if re.search(r'(?m)^BAB \d+\b', teks):
                awal = p
            continue
        if back is None:
            for b in teks.splitlines():
                if b.strip().upper() in _SEKSI:
                    back = p
                    break
    if awal is None:
        awal = min(halaman) if halaman else 1
    if back is None:
        back = (max(halaman) + 1) if halaman else awal
    return awal, back


def _halaman_cocok(halaman, isi, kunci):
    """Halaman isi tempat kunci muncul (batas kata, fallback substring)."""
    pola = re.compile(r'\b' + re.escape(kunci) + r'\b', re.IGNORECASE)
    cocok = [p for p in sorted(isi)
             if pola.search(halaman[p])]
    if not cocok:
        kl = kunci.lower()
        cocok = [p for p in sorted(isi)
                 if kl in halaman[p].lower()]
    return cocok


def _adalah_judul_seksi(teks):
    t = teks.strip().upper()
    return t in _SEKSI or re.match(r'^BAB \d+\b', t) is not None


def isi_indeks(path_docx, teks_per_halaman, glosarium, nama_list):
    """Isi nomor halaman entri Indeks Subjek + Indeks Nama di docx.

    Entri tanpa halaman DILEWATI (indeks hanya memuat istilah yang bisa
    dilacak — entri tanpa nomor adalah indeks rusak). Seksi yang belum
    ada DIBUAT (sebelum Daftar Pustaka bila ada, else akhir dokumen).
    Mengembalikan {'subjek': n, 'nama': n, 'isi_awal': p, 'back_awal': p}.
    """
    from docx import Document
    halaman = _teks_halaman_normal(teks_per_halaman)
    awal, back = _rentang_isi(halaman)
    isi = {p: halaman[p] for p in halaman if awal <= p < back}

    entri_subjek = {}
    for istilah in (glosarium or {}):
        cocok = _halaman_cocok(halaman, isi, istilah)
        if cocok:
            entri_subjek[istilah] = cocok
    entri_nama = {}
    for nm in (nama_list or []):
        cocok = _halaman_cocok(halaman, isi, nm)
        if cocok:
            entri_nama[nm] = cocok

    doc = Document(path_docx)

    def cari_judul(predikat):
        # WAJIB baca doc.paragraphs SEGAR tiap panggilan (temuan review
        # agen 28 Okt 2026 — bug mematikan): doc.paragraphs adalah daftar
        # yang dibuat ulang tiap diakses; snapshot lama (`paras = ...`)
        # TIDAK melihat judul yang baru dibuat buat_judul() sehingga
        # cari_judul mengembalikan None -> hapus_entri_lama(None) crash.
        # Di produksi, fallback add_indeks hanya menulis 'INDEKS' (tanpa
        # 'Indeks Nama') sehingga jalur buat_judul SELALU terpicu.
        for idx, pr in enumerate(doc.paragraphs):
            if predikat(pr.text.strip().upper()):
                return idx
        return None

    idx_subjek = cari_judul(lambda t: t in ('INDEKS SUBJEK', 'INDEKS'))
    idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
    idx_pustaka = cari_judul(lambda t: t == 'DAFTAR PUSTAKA')

    def hapus_entri_lama(idx_judul):
        """Hapus paragraf sesudah judul sampai seksi berikut/akhir."""
        if idx_judul is None:
            return  # tidak ada judul = tidak ada entri lama untuk dihapus
        j = idx_judul + 1
        while j < len(doc.paragraphs):
            if _adalah_judul_seksi(doc.paragraphs[j].text):
                break
            p_el = doc.paragraphs[j]._p
            p_el.getparent().remove(p_el)
            # Indeks bergeser: paragraf berikutnya menempati posisi j.
        # (loop tanpa j += 1 sengaja — penghapusan menggeser sisanya)

    def sisipkan_entri(idx_judul, entri):
        """Sisipkan baris 'Istilah .... 3, 7' sesudah judul, urut."""
        if idx_judul is None:
            # Jangan pernah crash TypeError samar: judul hilang = gagal
            # jelas, pemanggil (susun) menggagalkan buku + refund token.
            raise RuntimeError('judul seksi indeks tidak ditemukan')
        anchor = doc.paragraphs[idx_judul]._p
        for istilah in sorted(entri, key=str.lower):
            halaman_str = ', '.join(str(p) for p in entri[istilah])
            pr = doc.add_paragraph()
            pr.add_run(f'{istilah} .... {halaman_str}')
            anchor.addnext(pr._p)
            anchor = pr._p

    def buat_judul(judul, sebelum_idx=None):
        pr = doc.add_paragraph()
        run = pr.add_run(judul)
        run.bold = True
        if sebelum_idx is not None:
            target = doc.paragraphs[sebelum_idx]._p
            target.addprevious(pr._p)
            # Indeks paragraf bergeser; hitung ulang posisi judul baru.
            for idx, pp in enumerate(doc.paragraphs):
                if pp._p is pr._p:
                    return idx
        return len(doc.paragraphs) - 1

    if idx_subjek is None:
        idx_subjek = buat_judul('Indeks Subjek',
                                sebelum_idx=idx_pustaka)
        # Posisi lain bergeser setelah penyisipan — hitung ulang.
        idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
        idx_pustaka = cari_judul(lambda t: t == 'DAFTAR PUSTAKA')
    if idx_nama is None:
        # Indeks Nama sesudah Indeks Subjek (atau sebelum Pustaka).
        idx_nama = buat_judul(
            'Indeks Nama',
            sebelum_idx=idx_pustaka if idx_pustaka is not None
            and idx_pustaka > idx_subjek else None)
        idx_pustaka = cari_judul(lambda t: t == 'DAFTAR PUSTAKA')

    hapus_entri_lama(idx_subjek)
    # Indeks nama bergeser oleh penghapusan — hitung ulang.
    idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
    hapus_entri_lama(idx_nama)
    idx_subjek = cari_judul(lambda t: t in ('INDEKS SUBJEK', 'INDEKS'))
    idx_nama = cari_judul(lambda t: t == 'INDEKS NAMA')
    sisipkan_entri(idx_subjek, entri_subjek)
    sisipkan_entri(idx_nama, entri_nama)
    doc.save(path_docx)
    return {'subjek': len(entri_subjek), 'nama': len(entri_nama),
            'isi_awal': awal, 'back_awal': back}
