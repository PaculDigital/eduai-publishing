"""SAJIAN 13 BUKTI — baris sub-bab yang MENCURIGAKAN (untuk Bos tandai).

Bos (08 Okt): "sajikan daftar 13 baris mencurigakan ke Bos dulu -> Bos tandai mana
yang salah -> baru Wulan pasang".

Tulis HTML rapi: nomor, ID baris, panjang, isi baris, dugaan Wulan (TABEL/PARAGRAF/
LAMPIRAN), dan KOLOM KOSONG "koreksi Bos" untuk ditandai.

TIDAK memanggil Jev — baca HASIL_PETA3_ASIH.json saja.
"""
import json, sys, html
sys.path.insert(0, '/app')
from app import state
from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas

FID = 81
d = json.load(open('/app/HASIL_PETA3_ASIH.json'))
lab = d['label']

db = SessionLocal()
fb = db.get(FileBerkas, FID)
p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
baris = state.buang_daftar_isi(_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
db.close()

sub = sorted(int(i) for i, v in lab.items() if v == 'subbab')
curiga = []
for i in sub:
    t = ' '.join(baris[i].split()) if i < len(baris) else ''
    pipa = t.count('|')
    panjang = len(t)
    dugaan, alasan = '', ''
    if pipa >= 2:
        dugaan = 'TABEL (bukan sub-bab)'
        alasan = 'ada %d tanda pipa "|"' % pipa
    elif panjang > 300:
        dugaan = 'PARAGRAF (bukan sub-bab)'
        alasan = 'panjang %d karakter' % panjang
    elif panjang > 100 and t.upper().startswith('KUESIONER'):
        dugaan = 'LAMPIRAN? (perlu putusan Bos)'
        alasan = 'judul kuesioner, %d kar' % panjang
    if dugaan:
        curiga.append((i, panjang, t, dugaan, alasan, pipa))

rows = []
for n, (i, panjang, t, dugaan, alasan, pipa) in enumerate(curiga, 1):
    rows.append(f"""
    <tr>
      <td class="no">{n}</td>
      <td class="id">L{i:06d}</td>
      <td class="isi">{html.escape(t[:300])}</td>
      <td class="num">{panjang}</td>
      <td class="dugaan">{dugaan}<div class="kecil">{html.escape(alasan)}</div></td>
      <td class="kosong">……………</td>
    </tr>""")

html_doc = """<!DOCTYPE html><html lang="id"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>13 Baris Mencurigakan — Asih</title>
<style>
 body{font-family:-apple-system,Segoe UI,Roboto,sans-serif;background:#0f1115;color:#e8e8e8;
      margin:0;padding:18px;line-height:1.5}
 h1{font-size:19px;margin:0 0 6px} .sub{color:#9aa0a6;font-size:13px;margin-bottom:16px}
 table{width:100%%;border-collapse:collapse;font-size:13px}
 th{background:#1b1f27;color:#c9cdd3;text-align:left;padding:9px 8px;font-weight:600;
    border-bottom:2px solid #2c313a;font-size:12px}
 td{padding:9px 8px;border-bottom:1px solid #23272f;vertical-align:top}
 tr:hover td{background:#171b22}
 .no{color:#6b7280;width:26px} .id{font-family:ui-monospace,monospace;color:#7dd3fc;width:74px}
 .isi{color:#e8e8e8;word-break:break-word;max-width:520px}
 .num{color:#9aa0a6;width:52px;text-align:right}
 .dugaan{color:#fbbf24;width:170px;font-size:12px}
 .kecil{color:#6b7280;font-size:11px;margin-top:3px}
 .kosong{width:110px;color:#374151;font-size:11px}
 .catatan{margin-top:20px;padding:14px;background:#161a21;border-left:3px solid #fbbf24;
          border-radius:5px;font-size:13px;color:#c9cdd3}
 .catatan b{color:#fbbf24}
</style></head><body>
<h1>🔍 13 Baris Mencurigakan — ditandai SUB-BAB oleh Jev</h1>
<div class="sub">Naskah: SKRIPSI-Asih (fid=81) · 151 sub-bab total · 13 mencurigakan (8,6%)</div>
<table>
 <tr><th>#</th><th>Baris</th><th>Isi</th><th>Panjang</th><th>Dugaan Wulan</th><th>Koreksi Bos</th></tr>
 %%ROWS%%
</table>
<div class="catatan">
<b>Yang diminta Bos:</b> tandai di kolom paling kanan, untuk tiap baris:<br>
· <b>"BUKAN"</b> = memang bukan sub-bab (harus dibuang)<br>
· <b>"YA"</b> = memang sub-bab asli (jangan dibuang)<br>
· <b>tulis lain</b> = kalau ada catatan khusus<br><br>
<b>Kalau Bos setuju semua dugaan Wulan</b> ⇒ cukup bilang "semua bukan" ⇒ Wulan pasang 2 saringan kode:
buang baris berpipa (&ge;2 tanda <code>|</code>) + buang baris &gt;300 karakter.
</div>
</body></html>"""
html_doc = html_doc.replace('%%ROWS%%', '\n'.join(rows))

open('/app/SAJI_13_CURIGA.html', 'w').write(html_doc)
print('SAJI: /app/SAJI_13_CURIGA.html')
print()
for n, (i, panjang, t, dugaan, alasan, pipa) in enumerate(curiga, 1):
    print('%2d. L%06d  %-5d kar  %-24s  %s' % (n, i, panjang, dugaan, t[:52]))
