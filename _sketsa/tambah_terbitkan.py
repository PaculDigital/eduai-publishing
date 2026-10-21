import pathlib
f = pathlib.Path('/opt/data/services/eduai-publishing/app/loa.py')
s = f.read_text(encoding='utf-8')

TAMBAHAN = '''

def terbitkan(status: dict, artikel: dict, keluar: Path) -> dict:
    """TERBITKAN LoA: cek syarat -> ambil nomor -> isi template -> QR -> PDF.

    Mengembalikan {ok, nomor, nomor_surat, pdf, sebab}.
    Nomor HANYA naik kalau LoA benar-benar berhasil dicetak.
    """
    cek = periksa_syarat(status)
    if not cek.get('boleh'):
        return {'ok': False, 'sebab': cek.get('sebab') or 'Syarat belum terpenuhi.'}

    nomor = ambil_nomor()
    url = f'https://qr.tridarma.id/verifikasi-loa?no={nomor}'
    data = susun_data(status, artikel, setelan(), nomor, url)

    try:
        html = isi_template(data)
    except ValueError as e:
        return {'ok': False, 'sebab': f'Template LoA belum lengkap: {e}'}

    # QR ditulis SEJAJAR template (WeasyPrint mencari aset di DIR_TEMPLATE)
    bikin_qr(url, DIR_TEMPLATE / 'qr-verifikasi.png')
    cetak_pdf(html, keluar)

    # catat supaya bisa diverifikasi publik
    catat_terbit(nomor, data)
    return {'ok': True, 'nomor': nomor, 'nomor_surat': data['loa_number'],
            'pdf': str(keluar), 'url': url}


def unduh_untuk_user(status: dict, artikel: dict, folder: Path) -> dict:
    """Bungkus `terbitkan` untuk rute web: simpan PDF di folder data user."""
    folder = Path(folder)
    nomor_kira = nomor_berikut()
    keluar = folder / f'LoA-{nomor_kira.replace(".", "-")}.pdf'
    folder.mkdir(parents=True, exist_ok=True)
    return terbitkan(status, artikel, keluar)
'''

if 'def terbitkan' not in s:
    s = s.rstrip('\n') + '\n' + TAMBAHAN
    f.write_text(s, encoding='utf-8')
    print('✓ 2 fungsi baru: terbitkan, unduh_untuk_user')
else:
    print('sudah ada')

import re
print('fungsi:', re.findall(r'^def (\w+)', s, re.M))
