"""SAJI — 1.1 Latar Belakang APA ADANYA + tanda paragraf temuan Jev.

Bos minta: "cetak 1 sub-bab penuh (1.1 Latar Belakang) apa adanya + tanda
paragraf temuan Jev → Bos lihat sendiri apakah paragrafnya tepat atau kurang"

TANPA mengubah teks. Tanda hanya di tepi (kiri) supaya Bos bisa menilai:
   🅱️/🔷 = Jev bilang awal BAB / awal SUB-BAB
   📄     = Jev bilang awal PARAGRAF BARU
   (kosong) = Jev bilang lanjutan/biasa
"""
import sys, json, time, html
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

RENTANG = (354, 665)          # BAB I


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        teks = _teks_dari_berkas(p, fb.nama or '') or ''
        baris = teks.split('\n')
        awal, akhir = RENTANG
        akhir = min(akhir, len(baris))

        def _b(j):
            if j < 0 or j >= len(baris):
                return '(tepi)'
            return f'L{j:06d}| ' + ' '.join(baris[j].split())[:60]

        kand = [i for i in range(awal, akhir) if baris[i].strip()]
        paket, tanya = {}, {}
        for n, i in enumerate(kand):
            nm = f'c{n}'
            paket[nm] = {'sebelum': _b(i - 1), 'tengah': _b(i), 'sesudah': _b(i + 1)}
            tanya[nm] = {
                'type': 'choice',
                'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah akademik. '
                                 f'Baris tengah ini perannya apa?'),
                'criteria': {
                    'bab': 'Awal BAB (mis. BAB I, BAB II)',
                    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
                    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
                    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
                },
            }
        bahan = json.dumps(paket, ensure_ascii=False)[:58000]
        t0 = time.time()
        jw = satpam.tanya_bebas_mutu(bahan, tanya) or {}
        dtk = time.time() - t0

        hasil = {}
        for n, i in enumerate(kand):
            v = (jw.get(f'c{n}') or {}).get('choice')
            if isinstance(v, dict):
                v = v.get('id') or v.get('label')
            hasil[i] = v

        BAR = {'bab': ('🅱️', '#c8e6c9', 'AWAL BAB'),
               'subbab': ('🔷', '#bbdefb', 'AWAL SUB-BAB'),
               'paragraf': ('📄', '#fff9c4', 'AWAL PARAGRAF BARU'),
               'biasa': ('', '', 'lanjutan')}
        brt = []
        for i in range(awal, akhir):
            s = baris[i].strip()
            if not s:
                brt.append('<div class="kosong">(baris kosong)</div>')
                continue
            v = hasil.get(i)
            emo, bg, ket = BAR.get(v, ('', '', ''))
            st = f' style="background:{bg}"' if bg else ''
            brt.append(f'<div class="br"{st}><span class="id">L{i:06d}</span>'
                       f'<span class="tg">{emo} {ket}</span>'
                       f'<span class="tx">{html.escape(s)}</span></div>')
        n_par = sum(1 for v in hasil.values() if v == 'paragraf')
        n_sub = sum(1 for v in hasil.values() if v == 'subbab')
        n_bab = sum(1 for v in hasil.values() if v == 'bab')

        dok = f'''<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>Uji 5 — 1.1 Latar Belakang + tanda Jev</title>
<style>
body{{font-family:system-ui,sans-serif;max-width:1100px;margin:20px auto;padding:0 14px;color:#222}}
h1{{font-size:20px}} .kotak{{background:#eef6ee;padding:10px;border-radius:8px;font-size:13px;margin-bottom:14px}}
table.ket{{border-collapse:collapse;font-size:13px;margin:10px 0}}
table.ket th,table.ket td{{border:1px solid #ddd;padding:4px 9px}}
.br{{display:flex;gap:10px;padding:2px 4px;border-bottom:1px solid #f4f4f4;font-size:13.5px;line-height:1.5}}
.id{{color:#999;font-family:monospace;font-size:11px;min-width:74px;flex:0 0 74px;padding-top:2px}}
.tg{{min-width:132px;flex:0 0 132px;font-size:11px;color:#555}}
.tx{{flex:1}}
.kosong{{color:#ccc;font-size:11px;padding:1px 0 1px 84px}}
</style></head><body>
<h1>🔎 Uji 5 — BAB I Tesis 78 APA ADANYA + tanda temuan Jev</h1>
<div class="kotak">
<b>Bagian:</b> baris {awal}–{akhir} · <b>1 panggilan Jev</b> · {dtk:.1f} detik ·
{n_bab} bab · {n_sub} sub-bab · {n_par} paragraf.<br>
Tanda di kiri = jawaban Jev. <b>Teks TIDAK diubah sama sekali.</b><br>
Bos lihat: apakah tanda 📄 (awal paragraf) <b>tepat</b> atau <b>kurang</b>?
</div>
<table class="ket"><tr><th>Tanda</th><th>Arti</th></tr>
<tr><td>🅱️ AWAL BAB</td><td>Jev bilang ini awal bab</td></tr>
<tr><td>🔷 AWAL SUB-BAB</td><td>Jev bilang ini awal sub-bab (judul bagian)</td></tr>
<tr><td>📄 AWAL PARAGRAF BARU</td><td>Jev bilang ini kalimat pertama paragraf</td></tr>
<tr><td>(kosong) lanjutan</td><td>Jev bilang bukan awal apa pun</td></tr></table>
{''.join(brt)}
</body></html>'''
        keluar = '/app/SAJI_UJI5_PARAGRAF.html'
        open(keluar, 'w').write(dok)
        print(f'SAJI: {keluar} {len(dok):,} byte · {dtk:.1f} dtk')
        print(f'   bab={n_bab} subbab={n_sub} paragraf={n_par} biasa={sum(1 for v in hasil.values() if v=="biasa")}')
    finally:
        db.close()


if __name__ == '__main__':
    main()
