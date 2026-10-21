"""BENTUK KELUARAN petakan() — dicetak DULU sebelum menyambung (aturan Bos:
'CETAK DULU bentuk kunci mesin sebelum menulis JS/kode sambungan')."""
import sys, zipfile, re, glob
sys.path.insert(0, '/app')
from app.state import petakan, buang_daftar_isi
from app.konteks import dari_peta, bangun_prompt


def teks_docx(p):
    with zipfile.ZipFile(p) as z:
        xml = z.read('word/document.xml').decode('utf-8', 'ignore')
    xml = re.sub(r'</w:p>', '\n', xml)
    xml = re.sub(r'<[^>]+>', '', xml)
    import html
    return html.unescape(xml)


for f in sorted(glob.glob('/app/_contoh-dokumen/**/*.docx', recursive=True)):
    teks = teks_docx(f)
    peta = petakan(buang_daftar_isi(teks))
    print(f'\n═══ {f.split("/")[-1][:45]} ═══')
    print(f'  panjang teks     : {len(teks):,}')
    print(f'  jumlah bagian    : {len(peta)}')
    print(f'  KUNCI tiap bagian: {sorted(peta[0].keys()) if peta else "(kosong)"}')
    for s in peta[:4]:
        print(f"    • {s.get('section_id','?'):<10} "
              f"{(s.get('section_title') or '')[:38]:<40} "
              f"{s.get('char_count',0):>8,} kar  [{s.get('kategori','?')}]")
    if peta:
        tgt = peta[min(2, len(peta) - 1)].get('section_id')
        st = dari_peta(peta, tgt)
        print(f'  --- dari_peta("{tgt}") kunci: {sorted(st.keys())}')
        for k, v in st.items():
            print(f'      {k:<12} = {len(v):>8,} kar')
        pr = bangun_prompt(bagian_target=tgt, struktur=peta,
                           brief_ringkas='JUDUL: Naiknya harga (contoh brief)',
                           isi_saat_ini=st.get('target', ''),
                           komentar='Perbaiki kalimat ini supaya nyambung.')
        print(f'  --- bangun_prompt: {len(pr):,} kar')
