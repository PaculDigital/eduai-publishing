"""SAJIAN ASIH SELURUH NASKAH — peta3_jev.py + _subbab_palsu() (2 kolom).
Bos pilih A: sajikan supaya bisa dikoreksi.
TIDAK memanggil Jev lagi — pakai hasil yang sudah ada (simpan ke berkas dulu).
"""
import sys, json, html
sys.path.insert(0, '/app')
from peta3_jev import petakan

FID = int(sys.argv[1]) if len(sys.argv) > 1 else 81
JDL = sys.argv[2] if len(sys.argv) > 2 else 'ASIH'

r = petakan(FID, None, None)
# simpan hasil mentah supaya bisa diperiksa ulang tanpa panggil Jev lagi
with open('/app/HASIL_PETA3_%s.json' % JDL, 'w') as f:
    json.dump({'label': {str(k): v for k, v in r['label'].items()},
               'goyang': [[i, v] for i, v in r['goyang']],
               'gabung': {str(k): list(v) for k, v in r['gabung'].items()},
               'buang': r['buang'], 'waktu': r['waktu']}, f, ensure_ascii=False)

BAR = {'bab': ('B', '#c8e6c9', 'AWAL BAB'),
       'subbab': ('S', '#bbdefb', 'AWAL SUB-BAB'),
       'paragraf': ('P', '#fff9c4', 'AWAL PARAGRAF'),
       'biasa': ('', '', '')}
sis = set(r.get('sistematika') or [])       # D1: blok sistematika (ditandai)
goy = {i for i, _v in r['goyang']}
kiri, kanan = [], []
for i in range(r['awal'], r['akhir']):
    s = r['baris'][i].strip()
    no = 'L%06d' % i
    if not s:
        kiri.append('<div class="b kosong"><span class="id">%s</span></div>' % no)
        kanan.append('<div class="b kosong"><span class="id">%s</span></div>' % no)
        continue
    kiri.append('<div class="b"><span class="id">%s</span><span class="tx">%s</span></div>'
                % (no, html.escape(s)))
    if i in r['gabung']:
        kanan.append('<div class="b" style="background:#c8e6c9"><span class="id">%s</span>'
                     '<span class="tg">AWAL BAB</span><span class="tx">%s</span></div>'
                     % (no, html.escape(' '.join(r['gabung'][i]))))
        continue
    if i in r['buang']:
        kanan.append('<div class="b buang"><span class="id">%s</span>'
                     '<span class="tg">DIBUANG</span><span class="tx">%s</span></div>'
                     % (no, html.escape(s)))
        continue
    v = r['label'].get(i)
    _e, bg, ket = BAR.get(v, ('', '', ''))
    st = ' style="background:%s"' % bg if bg else ''
    gy = ' goy' if i in goy else ''
    # D1: blok SISTEMATIKA ditandai (TIDAK dibuang) — beri label khusus.
    if i in sis:
        ket = 'SISTEMATIKA (ditandai)'
        st = ' style="background:#eceff1;border-left:4px solid #607d8b"'
    kanan.append('<div class="b%s"%s><span class="id">%s</span>'
                 '<span class="tg">%s</span><span class="tx">%s</span></div>'
                 % (gy, st, no, ket, html.escape(s)))

hitung = {}
for i, v in r['label'].items():
    hitung[v] = hitung.get(v, 0) + 1
dok = ('<!doctype html><html lang="id"><head><meta charset="utf-8">'
       '<title>Asih seluruh - peta3</title><style>'
       'body{font-family:system-ui,sans-serif;margin:14px;color:#222;font-size:12px}'
       'h1{font-size:16px}'
       '.kotak{background:#e3f2fd;padding:8px;border-radius:8px;font-size:12px;margin-bottom:8px}'
       '.dua{display:flex;gap:10px}.kol{flex:1;min-width:0;border:1px solid #ddd;border-radius:8px;overflow:hidden}'
       '.kepala{background:#37474f;color:#fff;padding:5px 8px;font-size:11px;font-weight:600;position:sticky;top:0}'
       '.kepala.k2{background:#1565c0}'
       '.b{display:flex;gap:5px;padding:1px 6px;border-bottom:1px solid #f6f6f6;line-height:1.35}'
       '.b.goy{outline:2px solid #ff9800;outline-offset:-2px}'
       '.b.buang{opacity:.35}'
       '.id{color:#999;font-family:monospace;font-size:9px;flex:0 0 54px;padding-top:2px}'
       '.tx{flex:1;word-wrap:break-word}.tg{flex:0 0 78px;font-size:9px}'
       '.kosong{color:#eee;font-size:9px;height:3px}'
       '</style></head><body>'
       '<h1>Asih SELURUH NASKAH - peta 3 tingkat (kode + Jev)</h1>'
       '<div class="kotak"><b>hijau</b>=awal bab &nbsp;<b>biru</b>=awal sub-bab &nbsp;<b>kuning</b>=awal paragraf '
       '&nbsp;<b>jingga(garis)</b>=goyang antar-putaran &nbsp;<b>redup</b>=dibuang kode.<br>'
       'kandidat %d - gelombang %d - goyang %d - buang %d - gagal %d - waktu %s<br>'
       'HITUNG: %s<br>'
       'D1 SISTEMATIKA (ditandai, TIDAK dibuang): %s</div>'
       '<div class="dua">'
       '<div class="kol"><div class="kepala">NASKAH ASLI</div>%s</div>'
       '<div class="kol"><div class="kepala k2">+ PETA (kode+Jev)</div>%s</div>'
       '</div></body></html>') % (
    r['kand_jml'], r['gelombang'], len(r['goyang']), len(r['buang']), r.get('gagal', 0),
    ' '.join('%.1f' % w for w in r['waktu']), hitung,
    ['L%06d' % i for i in sorted(sis)],
    ''.join(kiri), ''.join(kanan))

open('/app/SAJI_ASIH_UTUH.html', 'w').write(dok)
print('SAJI: /app/SAJI_ASIH_UTUH.html (%d byte)' % len(dok))
print('kandidat %d · buang %d · goyang %d' % (r['kand_jml'], len(r['buang']), len(r['goyang'])))
print('HITUNG: %s' % hitung)
