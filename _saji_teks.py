#!/usr/bin/env python3
"""SAJI NASKAH DARI TEKS (bukan DB) — untuk naskah luar (PDF/GDrive Bos).

Cara pakai (DI DALAM container eduai-app):
    docker cp _saji_teks.py eduai-app:/app/
    docker cp naskah.txt eduai-app:/app/_naskah.txt
    docker exec -w /app eduai-app python3 _saji_teks.py _naskah.txt WULANDARI

Alasan dibuat: peta3_jev.susun() mengambil teks dari DB (FileBerkas). Naskah
dari luar (PDF kiriman Bos) belum ada di DB, jadi perlu jalur teks langsung.
ATURAN: JANGAN menyentuh peta3_jev.py — ini alat BANTU, bukan mengubah mesin.
"""
import sys
import html
import json

import peta3_jev as P
from app import state

NAMA = sys.argv[1] if len(sys.argv) > 1 else '_naskah.txt'
JDL = sys.argv[2] if len(sys.argv) > 2 else 'NASKAH'

teks = open('/app/' + NAMA, encoding='utf-8', errors='ignore').read()
bersih = state.buang_daftar_isi(teks or '')
baris = bersih.split('\n')
awal, akhir = 0, len(baris)


def _t(j):
    if 0 <= j < len(baris):
        return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58]
    return '(tepi)'


# ── RAKIT kandidat: PAKAI ATURAN YANG SAMA dengan peta3_jev.susun() ──
kand, gabung, buang = [], {}, []
i = awal
while i < akhir:
    s = baris[i].strip()
    if not s:
        i += 1
        continue
    if P.dibuang(s):
        buang.append(i)
        i += 1
        continue
    m = P.POLA_BAB.match(s)
    if m:
        j = i + 1
        while j < akhir and not baris[j].strip():
            j += 1
        if j < akhir:
            s2 = baris[j].strip()
            if s2 and s2 == s2.upper() and 4 < len(s2) < 70:
                gabung[i] = (s, s2)
                i = j + 1
                continue
        gabung[i] = (s, '')
        i += 1
        continue
    kand.append((i, s))
    i += 1

d = {'baris': baris, 'kand': kand, 'gabung': gabung, 'buang': buang,
     'awal': awal, 'akhir': akhir, 'nama': JDL, 't': _t}

# ── jalankan Jev langsung (bukan lewat susun/DB) ──
r = P.petakan_dari(d)

BAR = {'bab': ('B', '#c8e6c9', 'AWAL BAB'),
       'subbab': ('S', '#bbdefb', 'AWAL SUB-BAB'),
       'paragraf': ('P', '#fff9c4', 'AWAL PARAGRAF'),
       'biasa': ('', '', '')}
sis = set(r.get('sistematika') or [])
goy = {i for i, _v in r['goyang']}
kiri, kanan = [], []
for i in range(r['awal'], r['akhir']):
    s = baris[i].strip()
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
       '<title>%s - peta3</title><style>'
       'body{font-family:system-ui,sans-serif;margin:14px;color:#222;font-size:12px}'
       '.kotak{background:#f5f5f5;padding:10px;border-radius:8px;margin-bottom:12px;line-height:1.7}'
       '.dua{display:flex;gap:12px}.kol{flex:1;min-width:0}'
       '.kepala{font-weight:700;padding:6px;background:#e0e0e0;border-radius:6px;margin-bottom:6px}'
       '.k2{background:#fff3e0}.b{padding:2px 6px;border-radius:4px;margin-bottom:2px;'
       'display:flex;gap:6px;align-items:baseline}'
       '.b .id{color:#888;font-family:monospace;font-size:10px;flex:0 0 62px}'
       '.b .tg{font-size:9px;font-weight:700;color:#555;flex:0 0 108px}'
       '.b .tx{word-break:break-word}'
       '.kosong{background:#fafafa;height:6px;padding:0}'
       '.buang{background:#eeeeee;color:#9e9e9e;text-decoration:line-through}'
       '.goy{border-left:4px solid #ff9800}'
       '</style></head><body>'
       '<div class="kotak"><b>hijau</b>=awal bab &nbsp;<b>biru</b>=awal sub-bab '
       '&nbsp;<b>kuning</b>=awal paragraf &nbsp;<b>jingga(garis)</b>=goyang '
       'antar-putaran &nbsp;<b>redup</b>=dibuang kode. &nbsp;<b>abu-abu(tanda)</b>=sistematika.<br>'
       'kandidat %d - gelombang %d - goyang %d - buang %d - gagal %d - waktu %s<br>'
       'HITUNG: %s<br>'
       'D1 SISTEMATIKA (ditandai, TIDAK dibuang): %s</div>'
       '<div class="dua">'
       '<div class="kol"><div class="kepala">NASKAH ASLI</div>%s</div>'
       '<div class="kol"><div class="kepala k2">+ PETA (kode+Jev)</div>%s</div>'
       '</div></body></html>') % (
    JDL,
    r['kand_jml'], r['gelombang'], len(r['goyang']), len(r['buang']), r.get('gagal', 0),
    ' '.join('%.1f' % w for w in r['waktu']), hitung,
    ['L%06d' % i for i in sorted(sis)],
    ''.join(kiri), ''.join(kanan))

out = '/app/SAJI_%s.html' % JDL
open(out, 'w').write(dok)
print('SAJI: %s (%d byte)' % (out, len(dok)))
print('kandidat %d · gelombang %d · goyang %d · gabung %d · buang %d'
      % (r['kand_jml'], r['gelombang'], len(r['goyang']), len(r['gabung']), len(r['buang'])))
print('HITUNG: %s' % hitung)
print('D1 SISTEMATIKA: %s' % sorted(sis))
