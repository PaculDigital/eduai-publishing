import pathlib

P = pathlib.Path('/opt/data/services/eduai-publishing/app/tulis_docx.py')
s = P.read_text()

TAMBAHAN = '''

# ══════════════════════════════════════════════════════════════════════════
#  PENEMPEL PRESISI (25Sep26) — GANTI HANYA PARAGRAF YANG TERBUKTI
# ══════════════════════════════════════════════════════════════════════════
#  🔴 MENGAPA ADA (bug nyata, terukur):
#     `rakit()` di atas mengganti paragraf `idx_awal..idx_akhir`. Untuk
#     `bab_label = BAB_SELURUH` itu berarti **0 sampai paragraf terakhir**.
#     Sementara prompt (G7a) memerintahkan AI mengirim HANYA potongan kecil.
#
#     Uji 2 arah atas naskah nyata (76.803 kar / 303 paragraf):
#         masukan potongan 356 kar → hasil 3 paragraf (356 kar)
#         📉 naskah SUSUT 99,5% (76.447 kar hilang)
#
#     Itu persis yang membunuh `file_id=47`. Mahasiswa selama ini selamat
#     HANYA karena pagar C9 kebetulan menolak "hasil kosong" — bukan karena
#     sistem tahu cara menempelkan.
#
#  ✅ OBATNYA: pakai `app/pipa.py` — kutipan AI dicocokkan ke paragraf naskah,
#     lalu diganti SATU PER SATU. Paragraf lain TIDAK DISENTUH.
#
#  ⚠️ DILARANG: memakai Jalur B untuk bab (label selain BAB_SELURUH) tanpa
#     memeriksa ulang — lihat `terapkan_editan_ke_berkas()` di bawah.
# ══════════════════════════════════════════════════════════════════════════

def rakit_presisi(
    xml: str,
    editan: list,
    semua_paragraf: list[str],
) -> tuple[str, dict]:
    """Ganti HANYA paragraf yang ditunjuk `editan` (hasil `app/pipa.py`).

    Kembalikan (xml_baru, info). TIDAK menyentuh berkas sama sekali.

    Alasan tidak menyentuh berkas: pola yang SAMA seperti `rakit()` —
    uji harus bisa dijalankan atas teks tanpa risiko.
    """
    par = peta_paragraf(xml)
    if not par:
        return '', {'ok': False,
                    'pesan': 'Dokumen ini tidak punya paragraf teks yang bisa '
                             'diganti.'}

    #  Peta paragraf `tulis_docx` (XML) vs paragraf pipa (TEKS). Keduanya
    #  dihitung dari sumber yang sama, tapi pipa memecah dengan `\\n{2,}`
    #  atas TEKS, sementara `peta_paragraf` membaca `<w:p>` XML. Jumlahnya
    #  bisa berbeda (paragraf kosong, diagram, tabel). Karena itu pencocokan
    #  dilakukan lewat ISI TEKS, bukan lewat indeks — indeks pipa hanya
    #  pertanda; yang menentukan adalah teksnya.
    def normal(t: str) -> str:
        import re
        t = (t or '').lower()
        t = re.sub(r'[\\u2018\\u2019\\u201c\\u201d]', '"', t)
        t = re.sub(r'[\\u2013\\u2014\\u2212]', '-', t)
        t = re.sub(r'\\s+', ' ', t)
        t = re.sub(r'[^\\w\\s\\-.,;:()/%"]', '', t)
        return t.strip()

    #  Rentang ganti dikumpulkan dulu, lalu diterapkan DARI BELAKANG
    #  supaya posisi karakter tidak bergeser saat disisipkan.
    ganti_rencana: list[dict] = []
    tak_ketemu: list[int] = []

    for e in editan:
        k = normal(e.kutip)
        if not k:
            tak_ketemu.append(e.nomor)
            continue
        kena = None
        for i, p in enumerate(par):
            if k in normal(p['teks']):
                if kena is not None:            # lebih dari satu → TOLAK
                    kena = None
                    tak_ketemu.append(e.nomor)
                    break
                kena = i
        if kena is None:
            if e.nomor not in tak_ketemu:
                tak_ketemu.append(e.nomor)
            continue

        p_lama = par[kena]
        pPr = _pPr(xml[p_lama['awal']:p_lama['akhir']])
        rPr = _rPr_bersih(xml[p_lama['awal']:p_lama['akhir']])
        if not pPr and not rPr:
            #  Paragraf aneh (mis. tanpa format) — pakai paragraf isi terdekat
            for q in par:
                if _pPr(xml[q['awal']:q['akhir']]):
                    pPr = _pPr(xml[q['awal']:q['akhir']])
                    rPr = _rPr_bersih(xml[q['awal']:q['akhir']])
                    break

        #  GANTI-JADI bisa berisi BEBERAPA baris → beberapa paragraf Word.
        baris = [b for b in (e.ganti or '').split('\\n')]
        while baris and not baris[-1].strip():
            baris.pop()
        if not baris:
            tak_ketemu.append(e.nomor)
            continue
        isi_baru = ''.join(
            _par_baru(b.strip(), pPr, rPr) for b in baris if b.strip())
        if not isi_baru:
            tak_ketemu.append(e.nomor)
            continue

        ganti_rencana.append({
            'paragraf': kena, 'awal': p_lama['awal'],
            'akhir': p_lama['akhir'], 'isi': isi_baru,
            'nomor': e.nomor, 'teks_lama': p_lama['teks'][:80],
        })

    if not ganti_rencana:
        return '', {'ok': False,
                    'pesan': ('Tidak ada paragraf naskah yang cocok dengan '
                              'perubahan yang diminta. Naskah TIDAK diubah.'),
                    'tak_ketemu': tak_ketemu}

    #  Terapkan dari BELAKANG supaya offset karakter tetap sahih.
    xml_baru = xml
    for g in sorted(ganti_rencana, key=lambda d: d['awal'], reverse=True):
        xml_baru = _sisip(xml_baru, g['awal'], g['akhir'], g['isi'])

    return xml_baru, {
        'ok': True,
        'paragraf_diganti': len(ganti_rencana),
        'paragraf_baru': len(ganti_rencana),
        'karakter_baru': sum(len(g['isi']) for g in ganti_rencana),
        'bab': BAB_SELURUH,
        'presisi': True,
        'tak_ketemu': tak_ketemu,
        'rincian': [{'K': g['nomor'], 'paragraf': g['paragraf'] + 1,
                     'teks_lama': g['teks_lama']} for g in ganti_rencana],
    }


def terapkan_editan_ke_berkas(
    path: Path,
    editan: list,
    semua_paragraf: list[str],
    backup_dir: Path | None = None,
) -> dict:
    """Tulis hasil revisi PRESISI ke .docx — ATOMIK + BACKUP.

    Ini JALUR UTAMA untuk revisi berbasis catatan pembimbing (25Sep26).
    `terapkan_ke_berkas()` (jalur lama) tetap ada untuk penggantian per-bab.

    Urutan (SAMA seperti jalur lama — jangan diubah):
      1. baca isi .docx ke MEMORI
      2. rakit xml baru di MEMORI (presisi)
      3. PERIKSA xml sehat
      4. backup berkas asli
      5. tulis ke berkas SEMENTARA
      6. `os.replace()` → atomik
    """
    path = Path(path)
    if not path.exists():
        return {'ok': False, 'pesan': 'Berkas dokumen tidak ditemukan di server.'}
    if not editan:
        return {'ok': False, 'pesan': 'Tidak ada perubahan yang bisa diterapkan.'}

    try:
        with zipfile.ZipFile(path) as z:
            semua = {n: z.read(n) for n in z.namelist()}
        urutan = zipfile.ZipFile(path).namelist()
    except Exception as e:                                    # noqa: BLE001
        return {'ok': False, 'pesan': f'Dokumen tidak bisa dibaca: {e}'}

    if 'word/document.xml' not in semua:
        return {'ok': False, 'pesan': 'Bukan dokumen Word (.docx).'}

    xml_lama = semua['word/document.xml'].decode('utf-8', 'ignore')
    xml_baru, info = rakit_presisi(xml_lama, editan, semua_paragraf)
    if not info.get('ok'):
        return info

    #  ── PAGAR BENCANA (dari app/pipa.py — SATU SUMBER) ──
    try:
        from .pipa import cukup_panjang
        teks_lama = '\\n\\n'.join(p['teks'] for p in peta_paragraf(xml_lama))
        teks_br = '\\n\\n'.join(p['teks'] for p in peta_paragraf(xml_baru))
        aman, alasan = cukup_panjang(teks_lama, teks_br)
        if not aman:
            log.error('[tulis_docx] PAGAR PANJANG menolak: %s', alasan)
            return {'ok': False, 'pesan': alasan}
    except ImportError:
        pass                                  # pipa belum ada (mode lama)

    sehat, alasan = _cek_xml_sehat(xml_baru)
    if not sehat:
        log.error('[tulis_docx] XML cacat, dibatalkan: %s', alasan)
        return {'ok': False, 'pesan': f'Dibatalkan demi keamanan naskah: {alasan}'}

    # ── BACKUP ──
    jejak_backup = ''
    try:
        tempat = Path(backup_dir) if backup_dir else path.parent / '_cadangan_docx'
        tempat.mkdir(parents=True, exist_ok=True)
        cap = datetime.now().strftime('%Y%m%d_%H%M%S')
        tujuan = tempat / f'{path.stem}-SEBELUM-AI-{cap}{path.suffix}'
        shutil.copy2(path, tujuan)
        jejak_backup = str(tujuan)
    except Exception as e:                                    # noqa: BLE001
        log.warning('[tulis_docx] backup gagal (lanjut, tapi dicatat): %s', e)

    semua['word/document.xml'] = xml_baru.encode('utf-8')

    sementara = path.parent / f'.{path.name}.tmp-{os.getpid()}'
    try:
        with zipfile.ZipFile(sementara, 'w', zipfile.ZIP_DEFLATED) as z:
            for n in urutan:
                if n in semua:
                    z.writestr(n, semua[n])
            for n in semua:
                if n not in urutan:
                    z.writestr(n, semua[n])
        os.replace(sementara, path)
    except Exception as e:                                    # noqa: BLE001
        try:
            sementara.unlink(missing_ok=True)
        except Exception:                                     # noqa: BLE001
            pass
        return {'ok': False, 'pesan': f'Gagal menulis dokumen: {e}'}

    info['ukuran'] = path.stat().st_size
    info['cadangan'] = jejak_backup
    log.info('[tulis_docx] PRESISI %s: %s paragraf diganti (%s byte)',
             path.name, info['paragraf_diganti'], info['ukuran'])
    return info
'''

if 'def rakit_presisi' in s:
    print('SUDAH ADA — tidak ditulis ulang')
else:
    P.write_text(s.rstrip() + TAMBAHAN)
    print('✅ fungsi rakit_presisi + terapkan_editan_ke_berkas DITAMBAHKAN')
    print('   panjang berkas:', len(P.read_text()), 'byte')
