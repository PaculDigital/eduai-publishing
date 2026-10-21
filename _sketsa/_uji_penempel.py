"""UJI PENEMPEL PRESISI — 2 ARAH atas NASKAH BOS NYATA (bukan contoh).

  A. SEHAT  : ganti 1 paragraf → naskah 99,8% utuh, paragraf lain TIDAK berubah
  B. DIRUSAK: potongan kecil (bug 25Sep26) → pagar panjang HARUS menolak
"""
import pathlib
import sys
import zipfile

sys.path.insert(0, '/app')
from app.pipa import Editan, periksa                       # noqa: E402
from app.tulis_docx import (peta_paragraf, rakit_presisi,  # noqa: E402
                            terapkan_editan_ke_berkas)

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))


DOCX = pathlib.Path('/app/_naskah_bos_uji.docx')
with zipfile.ZipFile(DOCX) as z:
    xml = z.read('word/document.xml').decode('utf-8')

par = peta_paragraf(xml)
teks_lama = '\n\n'.join(p['teks'] for p in par)
print('═' * 74)
print(f'NASKAH NYATA: {len(par)} paragraf · {len(teks_lama):,} kar')
print('═' * 74)

#  Ambil paragraf isi yang panjang (bukan judul) sebagai sasaran
sasaran = None
for i, p in enumerate(par):
    if 200 < len(p['teks']) < 800:
        sasaran = (i, p['teks'])
        break
assert sasaran, 'tidak ada paragraf sasaran'
i_sas, t_sas = sasaran
print(f'\nsasaran: paragraf #{i_sas + 1} ({len(t_sas)} kar)')
print(f'   {t_sas[:150]}…')

#  ── A. SEHAT ────────────────────────────────────────────────────────────
print()
print('A. SEHAT — ganti 1 paragraf, sisanya TIDAK boleh berubah')
#  ⚠️ JEBAKAN UJI (ketemu 25Sep26): `split('. ')[0] + '.'` menambah titik
#     PADAHAL kalimatnya sudah berakhir titik → kutipan jadi "...Bangsa.."
#     (2 titik) → tidak cocok. ATURAN: bangun kutipan dari teks APA ADANYA.
bagian = t_sas.split('. ')
kalimat = bagian[0] + ('.' if not bagian[0].rstrip().endswith('.') else '')
if len(kalimat) < 40 and len(bagian) > 1:          # kalimat terlalu pendek
    kalimat = '. '.join(bagian[:2]) + '.'
ganti = (kalimat.rstrip('.') + '. Perubahan ini menyisipkan penekanan pada '
         'tujuan penelitian sesuai catatan pembimbing.')
e = Editan(nomor=1, kutip=kalimat, ganti=ganti, indeks=[i_sas], keadaan='cocok')

xml_baru, info = rakit_presisi(xml, [e], [p['teks'] for p in par])
if not info.get('ok'):
    cek('A1 rakit_presisi jalan', False, info.get('pesan', '')[:90])
else:
    cek('A1 rakit_presisi jalan', True, f"{info['paragraf_diganti']} paragraf")
    par_baru = peta_paragraf(xml_baru)
    teks_baru = '\n\n'.join(p['teks'] for p in par_baru)
    susut = 100 - (len(teks_baru) / len(teks_lama) * 100)
    print(f'   paragraf: {len(par)} → {len(par_baru)}')
    print(f'   panjang : {len(teks_lama):,} → {len(teks_baru):,} kar ({susut:+.2f}%)')
    cek('A2 jumlah paragraf TIDAK berubah', len(par_baru) == len(par),
        f'{len(par)} → {len(par_baru)}')
    cek('A3 naskah nyaris utuh (susut < 2%)', susut < 2, f'{susut:+.2f}%')
    #  Paragraf lain wajib SAMA
    beda = [j for j in range(min(len(par), len(par_baru)))
            if par[j]['teks'] != par_baru[j]['teks']]
    cek('A4 HANYA 1 paragraf berubah', beda == [i_sas],
        f'paragraf berubah: {[j + 1 for j in beda]}')
    #  Isi barunya benar
    cek('A5 paragraf sasaran memuat teks baru',
        'menyisipkan penekanan' in par_baru[i_sas]['teks'])
    cek('A6 judul naskah TIDAK rusak',
        'PENGARUH KUALITAS' in par_baru[0]['teks'].upper(),
        par_baru[0]['teks'][:60])

#  ── B. DIRUSAK — jalur LAMA (rakit) masih mengganti seluruh dokumen ─────
print()
print('B. JALUR LAMA (rakit) — penggantian seluruh naskah masih bisa bencana')
print('   (bukti kenapa jalur PRESISI wajib jadi jalur utama)')
from app.tulis_docx import rakit                          # noqa: E402
xml_lama_hasil, info_lama = rakit(xml, 'Ringkasan singkat saja.',
                                  bab_label='__seluruh__')
if info_lama.get('ok'):
    par_lama = peta_paragraf(xml_lama_hasil)
    teks_lama_hasil = '\n'.join(p['teks'] for p in par_lama)
    susut_lama = 100 - (len(teks_lama_hasil) / len(teks_lama) * 100)
    print(f'   jalur LAMA: {len(par)} → {len(par_lama)} paragraf · '
          f'{susut_lama:.1f}% hilang')
    cek('B1 jalur LAMA memang BERBAHAYA (susut > 90%) — alasan jalur presisi ada',
        susut_lama > 90, f'{susut_lama:.1f}%')
else:
    cek('B1 jalur LAMA menolak', False, info_lama.get('pesan', '')[:80])

#  Pagar panjang dipanggil LANGSUNG (yang benar menguji pagar = panggil perilakunya)
from app.pipa import cukup_panjang                          # noqa: E402
aman, alasan = cukup_panjang(teks_lama, teks_lama[:int(len(teks_lama) * 0.05)])
cek('B2 pagar panjang MENOLAK susut 95%', not aman, alasan[:80])

#  ── C. SEHAT lewat berkas (bukan cuma memori) ───────────────────────────
print()
print('C. SEHAT lewat BERKAS — tulis sungguhan ke salinan')
tmp2 = pathlib.Path('/app/_uji_tmp_naskah2.docx')
tmp2.write_bytes(DOCX.read_bytes())
h2 = terapkan_editan_ke_berkas(tmp2, [e], [p['teks'] for p in par])
cek('C1 penulisan BERKAS berhasil', h2.get('ok'), str(h2.get('pesan', ''))[:80])
if h2.get('ok'):
    with zipfile.ZipFile(tmp2) as z:
        par2 = peta_paragraf(z.read('word/document.xml').decode('utf-8'))
    cek('C2 berkas hasil masih 303 paragraf (Word bisa buka)',
        len(par2) == len(par), f'{len(par2)} paragraf')
    cek('C3 ada cadangan dibuat', bool(h2.get('cadangan')),
        str(h2.get('cadangan'))[-50:])
    cek('C4 ukuran wajar', 100_000 < h2.get('ukuran', 0) < 1_000_000,
        f"{h2.get('ukuran'):,} byte")
for f in (tmp2,):
    f.unlink(missing_ok=True)

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
