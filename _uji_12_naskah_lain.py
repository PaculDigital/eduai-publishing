"""UJI 12 — NASKAH ASIH (tanpa nomor) + DISERTASI: apakah cara sekarang GENERAL?

Bos: "coba di bab lain yang belum pernah dipakai tuning (misal BAB II ke bawah),
      biar ketahuan apakah perbaikannya general atau cuma hafal potongan ini."

BAB II Tesis 78 sudah 9/9 ✅. Sekarang uji BENTUK YANG SANGAT BEDA:
  · Asih (fid=81) → skripsi, barisnya PANJANG (median 37 kar, p90 383!)
  · Disertasi S3 (fid=103) → barisnya PENDEK (median 16 kar)

CARA SEKARANG (kode beri ID + JEV 4 pilihan), 3 putaran, rentang awal naskah.
"""
import sys, json, time, html
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

PUTARAN = 3
KRITERIA = {
    'bab': 'Awal BAB (mis. BAB I, BAB II)',
    'subbab': 'Awal SUB-BAB (mis. 1.1, 2.1.3, atau judul bagian)',
    'paragraf': 'Awal PARAGRAF BARU (kalimat pertama paragraf)',
    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
}


def uji(fid, awal, akhir, judul):
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        akhir = min(akhir, len(baris))
        print('═' * 72)
        print(f'📄 UJI 12: fid={fid} {judul} · baris {awal}-{akhir} (total {len(baris)})')

        def _t(j):
            return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58] \
                if 0 <= j < len(baris) else '(tepi)'

        kand = [i for i in range(awal, akhir) if baris[i].strip()]
        paket, tanya = {}, {}
        for n, i in enumerate(kand):
            nm = f'c{n}'
            paket[nm] = {'sebelum': _t(i - 1), 'tengah': _t(i), 'sesudah': _t(i + 1)}
            tanya[nm] = {'type': 'choice',
                         'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah '
                                          f'akademik. Baris tengah ini perannya apa?'),
                         'criteria': dict(KRITERIA)}
        bahan = json.dumps(paket, ensure_ascii=False)
        print(f'   kandidat {len(kand)} · bahan {len(bahan):,} kar')

        putaran = []
        for k in range(PUTARAN):
            t0 = time.time()
            jw = satpam.tanya_bebas_mutu(bahan[:58000], tanya) or {}
            print(f'   ▶ putaran {k+1}: {time.time()-t0:.1f} dtk '
                  f'({len([v for v in jw.values() if v])}/{len(kand)})')
            putaran.append(jw)
            time.sleep(1.0)

        hasil = {}
        for n, i in enumerate(kand):
            vs = []
            for jw in putaran:
                v = (jw.get(f'c{n}') or {}).get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                vs.append(v)
            hasil[i] = vs
        goyang = [(i, v) for i, v in hasil.items() if len(set(v)) > 1]
        print(f'   🎯 GOYANG: {len(goyang)} dari {len(hasil)} '
              f'({100*len(goyang)/max(1,len(hasil)):.0f}%)')
        for i, v in goyang:
            print(f'      L{i:06d} {v} | {baris[i].strip()[:44]}')
        print('   🔎 label:')
        for i in sorted(hasil):
            v = hasil[i][0]
            if v in ('bab', 'subbab', 'paragraf'):
                emo = {'bab': '🅱️', 'subbab': '🔷', 'paragraf': '📄'}[v]
                print(f'      {emo} L{i:06d} {v:8s} | {baris[i].strip()[:44]}')

        # sajian
        BAR = {'bab': ('🅱️', '#c8e6c9', 'AWAL BAB'),
               'subbab': ('🔷', '#bbdefb', 'AWAL SUB-BAB'),
               'paragraf': ('📄', '#fff9c4', 'AWAL PARAGRAF'),
               'biasa': ('', '', '')}
        kiri, kanan = [], []
        for i in range(awal, akhir):
            s = baris[i].strip()
            no = f'L{i:06d}'
            if not s:
                kiri.append(f'<div class="b kosong"><span class="id">{no}</span>(kosong)</div>')
                kanan.append(f'<div class="b kosong"><span class="id">{no}</span>(kosong)</div>')
                continue
            kiri.append(f'<div class="b"><span class="id">{no}</span>'
                        f'<span class="tx">{html.escape(s)}</span></div>')
            vs = hasil.get(i, [None])
            emo, bg, ket = BAR.get(vs[0], ('', '', ''))
            st = f' style="background:{bg}"' if bg else ''
            gy = ' <span class="gy">⚠goyang</span>' if len(set(vs)) > 1 else ''
            kanan.append(f'<div class="b"{st}><span class="id">{no}</span>'
                         f'<span class="tg">{emo} {ket}</span>'
                         f'<span class="tx">{html.escape(s)}</span>{gy}</div>')
        dok = f'''<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>Uji 12 — {judul}</title><style>
body{{font-family:system-ui,sans-serif;margin:14px;color:#222}}
h1{{font-size:17px}} .kotak{{background:#f3e5f5;padding:9px;border-radius:8px;font-size:13px;margin-bottom:10px}}
.dua{{display:flex;gap:12px}} .kol{{flex:1;min-width:0;border:1px solid #ddd;border-radius:8px;overflow:hidden}}
.kepala{{background:#37474f;color:#fff;padding:6px 9px;font-size:12px;font-weight:600}}
.kepala.k2{{background:#6a1b9a}}
.b{{display:flex;gap:6px;padding:2px 7px;border-bottom:1px solid #f4f4f4;font-size:12px;line-height:1.4}}
.id{{color:#999;font-family:monospace;font-size:9.5px;flex:0 0 58px;padding-top:2px}}
.tx{{flex:1;word-wrap:break-word}} .tg{{flex:0 0 92px;font-size:9.5px}}
.kosong{{color:#ccc;font-size:9.5px}} .gy{{color:#d32f2f;font-size:9px;font-weight:700}}
</style></head><body>
<h1>🧪 Uji 12 — {judul} (bentuk berbeda, cara sekarang)</h1>
<div class="kotak">{len(kand)} kandidat · {len(goyang)} goyang · waktu {sum(1 for _ in putaran)} putaran</div>
<div class="dua">
<div class="kol"><div class="kepala">📄 NASKAH ASLI</div>{''.join(kiri)}</div>
<div class="kol"><div class="kepala k2">🔎 + TANDA JEV</div>{''.join(kanan)}</div>
</div></body></html>'''
        nama_saji = f'SAJI_UJI12_{judul.split()[0].replace("/","")}.html'
        open('/app/' + nama_saji, 'w').write(dok)
        print(f'   SAJI: /app/{nama_saji}')
    finally:
        db.close()


if __name__ == '__main__':
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 81
    awa = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    akh = int(sys.argv[3]) if len(sys.argv) > 3 else 90
    jdl = sys.argv[4] if len(sys.argv) > 4 else 'ASIH'
    uji(fid, awa, akh, jdl)
