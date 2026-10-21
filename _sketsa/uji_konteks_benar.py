"""Uji dari_peta() vs bangun_prompt() — pakai JALUR YANG BENAR.
Dan cetak ISI prompt supaya bisa diperiksa MATA (aturan Bos: 'cetak dulu')."""
import sys, zipfile, re, glob, html
sys.path.insert(0, '/app')
from app.state import petakan, buang_daftar_isi
from app.konteks import dari_peta, bangun_prompt, BATAS_BAB1, BATAS_SEBELUM, BATAS_SESUDAH


def teks_docx(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    return html.unescape(re.sub(r'<[^>]+>', '', xml))


f = glob.glob('/app/_contoh-dokumen/**/TESIS-S2-unhas-manajemen*.docx')[0]
teks = teks_docx(f)
peta = petakan(buang_daftar_isi(teks))

print('══ 1. dari_peta() LANGSUNG ══')
for tgt in ('1.3', 'BAB III'):
    st = dari_peta(peta, tgt)
    print(f'  target={tgt:<10} ' + ' '.join(f'{k}={len(v):,}' for k, v in st.items()))
    st2 = dari_peta(peta, tgt)
    st2['target'] = ''

print('\n══ 2. bangun_prompt dengan peta= (JALUR BENAR) ══')
for tgt in ('1.3', '2.1'):
    pr = bangun_prompt(
        bagian_target=tgt,
        peta=peta,                    # ← jalur BENAR
        brief_ringkas='JUDUL: Pengaruh Digital Marketing terhadap Keputusan Pembelian',
        isi_saat_ini=next((s['isi_teks'] for s in peta if s['section_id'] == tgt), ''),
        komentar='Perbaiki supaya nyambung dengan latar belakang.')
    print(f'\n  target {tgt} → prompt {len(pr):,} karakter')
    # blok apa saja yang masuk?
    for blok in pr.split('\n\n'):
        if blok.startswith('==='):
            print(f'    • {blok.splitlines()[0][:60]}')
    print(f'  batas: BAB1={BATAS_BAB1} SEBELUM={BATAS_SEBELUM} SESUDAH={BATAS_SESUDAH}')
