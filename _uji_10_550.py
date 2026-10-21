"""UJI 10 + SAJI — RENTANG 550-670 (baris yang BOS sorot), DENGAN perbaikan ①+②.

Bos sorot: L000570 ("Pada"), L000602 ("antara"), L000608 (butir 1.2), L000662 (TINJAUAN PUSTAKA).

Perbaikan yang dipakai:
  ① SAMBUNG BARIS yang berakhir kata menggantung (patahan ekstraksi) — FAKTA.
  ② DEFINISI TAJAM di criteria (judul bab / butir bernomor / lanjutan).

Keluaran: sajian BERDAMPINGAN (asli vs bertanda) + ringkas goyang 3 putaran.
"""
import sys, json, time, html
sys.path.insert(0, '/app')

from app.ai import SessionLocal, _teks_dari_berkas, UPLOAD_DIR
from app.models import FileBerkas
from app import satpam

AWAL, AKHIR = 550, 672
PUTARAN = 3
GANTUNG = {'pada', 'antara', 'dan', 'yang', 'dengan', 'di', 'ke', 'untuk', 'dari',
           'atau', 'karena', 'sedangkan', 'yaitu', 'adalah', 'oleh', 'ini', 'itu',
           'juga', 'serta', 'agar', 'supaya', 'bila', 'jika', 'seperti', 'dalam',
           'terhadap', 'pengaruh', 'hubungan', 'melalui'}
KRITERIA = {
    'bab': ('Awal BAB (BAB I, BAB II) ATAU JUDUL BAB di baris terpisah '
            '(PENDAHULUAN, TINJAUAN PUSTAKA, METODE PENELITIAN)'),
    'subbab': ('Awal SUB-BAB = bagian BERNOMOR di dalam bab (1.1, 2.1.3) atau '
               'judul bagian yang berdiri sendiri. BUKAN butir bernomor '
               '(1. 2. 3.) di bawah Rumusan Masalah/Tujuan/Hipotesis'),
    'paragraf': ('Awal PARAGRAF BARU = kalimat pertama paragraf. Baris LANJUTAN '
                 'dari kalimat sebelumnya BUKAN awal paragraf'),
    'biasa': 'Lanjutan/biasa (bukan awal apa pun)',
}
SOROT = {570: 'lanjutan? (baris sebelum berakhir "Pada")',
         602: 'lanjutan? (baris sebelum berakhir "antara")',
         608: 'butir no.1 di bawah 1.2',
         662: 'judul bab (pasangan BAB II)'}


def bersihkan(baris, awal, akhir):
    out, nyambung = [], []
    i = awal
    while i < akhir:
        s = baris[i].strip()
        if not s:
            out.append((i, '', [i]))
            i += 1
            continue
        gab, asal = s, [i]
        while True:
            kata = gab.rstrip().rstrip('.,;:').split()[-1].lower() if gab.strip() else ''
            if kata in GANTUNG and i + 1 < akhir:
                j = i + 1
                while j < akhir and not baris[j].strip():
                    j += 1
                if j < akhir:
                    gab = gab.rstrip() + ' ' + baris[j].strip()
                    asal.append(j)
                    nyambung.append(i)
                    i = j
                    continue
            break
        out.append((asal[0], gab, asal))
        i += 1
    return out, nyambung


def main():
    fid = int(sys.argv[1]) if len(sys.argv) > 1 else 78
    db = SessionLocal()
    try:
        fb = db.get(FileBerkas, fid)
        p = UPLOAD_DIR / str(fb.user_id) / (fb.nama_simpan or '')
        baris = (_teks_dari_berkas(p, fb.nama or '') or '').split('\n')
        akhir = min(AKHIR, len(baris))
        print('═' * 72)
        print(f'📄 fid={fid} · UJI 10: rentang {AWAL}-{akhir} + perbaikan ①+②')

        bersih, nyambung = bersihkan(baris, AWAL, akhir)
        print(f'   ① disambung {len(nyambung)} kali · bahan {len(bersih)}')

        def _t(j):
            return ('L%06d| ' % j) + ' '.join(baris[j].split())[:58] \
                if 0 <= j < len(baris) else '(tepi)'

        alamat, paket, tanya = [], {}, {}
        for n, (i, t, asal) in enumerate(bersih):
            if not t:
                continue
            nm = f'c{n}'
            alamat.append((nm, i, asal))
            sebelum = _t(asal[0] - 1)
            sesudah = _t(max(asal) + 1)
            paket[nm] = {'sebelum': sebelum, 'tengah': ('L%06d| ' % i) + t[:70],
                         'sesudah': sesudah}
            tanya[nm] = {'type': 'choice',
                         'instructions': (f'Baris `{nm}.tengah` ada di dalam naskah '
                                          f'akademik. Baris tengah ini perannya apa?'),
                         'criteria': dict(KRITERIA)}
        bahan = json.dumps(paket, ensure_ascii=False)
        print(f'   kandidat {len(alamat)} · bahan {len(bahan):,} kar')

        putaran = []
        for k in range(PUTARAN):
            t0 = time.time()
            jw = satpam.tanya_bebas_mutu(bahan[:58000], tanya) or {}
            print(f'   ▶ putaran {k+1}: {time.time()-t0:.1f} dtk '
                  f'({len([v for v in jw.values() if v])}/{len(alamat)})')
            putaran.append(jw)
            time.sleep(1.0)

        hasil = {}
        for nm, i, _asal in alamat:
            vs = []
            for jw in putaran:
                v = (jw.get(nm) or {}).get('choice')
                if isinstance(v, dict):
                    v = v.get('id') or v.get('label')
                vs.append(v)
            hasil[i] = vs

        goyang = [(i, v) for i, v in hasil.items() if len(set(v)) > 1]
        print(f'\n   🎯 GOYANG: {len(goyang)} dari {len(hasil)} baris')
        for i, v in goyang:
            print(f'      L{i:06d} {v} | {baris[i].strip()[:44]}')
        print(f'\n   🔍 BARIS YANG BOS SOROT:')
        for t, ket in SOROT.items():
            v = hasil.get(t)
            if v:
                tanda = '⚠️GOYANG' if len(set(v)) > 1 else 'stabil'
                print(f'      L{t:06d} [{tanda}] {v} → {ket}')
            else:
                print(f'      L{t:06d} (tidak jadi kandidat: kosong/sudah disambung)')

        BAR = {'bab': ('🅱️', '#c8e6c9', 'AWAL BAB'),
               'subbab': ('🔷', '#bbdefb', 'AWAL SUB-BAB'),
               'paragraf': ('📄', '#fff9c4', 'AWAL PARAGRAF'),
               'biasa': ('', '', '')}
        kiri, kanan = [], []
        for i in range(AWAL, akhir):
            s = baris[i].strip()
            no = f'L{i:06d}'
            if not s:
                kiri.append(f'<div class="b kosong"><span class="id">{no}</span>(kosong)</div>')
                kanan.append(f'<div class="b kosong"><span class="id">{no}</span>(kosong)</div>')
                continue
            tag = ' <span class="ny">↩nyambung</span>' if i in nyambung else ''
            kiri.append(f'<div class="b"><span class="id">{no}</span>'
                        f'<span class="tx">{html.escape(s)}</span></div>')
            v = (hasil.get(i) or [None])[0]
            emo, bg, ket = BAR.get(v, ('', '', ''))
            st = f' style="background:{bg}"' if bg else ''
            sorot = ' sorot' if i in SOROT else ''
            kanan.append(f'<div class="b{sorot}"{st}><span class="id">{no}</span>'
                         f'<span class="tg">{emo} {ket}</span>'
                         f'<span class="tx">{html.escape(s)}</span>{tag}</div>')
        dok = f'''<!doctype html><html lang="id"><head><meta charset="utf-8">
<title>Uji 10 — 550-{akhir} sesudah perbaikan</title><style>
body{{font-family:system-ui,sans-serif;margin:14px;color:#222}}
h1{{font-size:18px}} .kotak{{background:#eef6ee;padding:9px;border-radius:8px;font-size:13px;margin-bottom:10px}}
.dua{{display:flex;gap:14px}} .kol{{flex:1;min-width:0;border:1px solid #ddd;border-radius:8px;overflow:hidden}}
.kepala{{background:#37474f;color:#fff;padding:6px 9px;font-size:12.5px;font-weight:600}}
.kepala.k2{{background:#1565c0}}
.b{{display:flex;gap:7px;padding:2px 8px;border-bottom:1px solid #f4f4f4;font-size:12.5px;line-height:1.42}}
.b.sorot{{outline:2px solid #e91e63;outline-offset:-2px}}
.id{{color:#999;font-family:monospace;font-size:10px;flex:0 0 60px;padding-top:2px}}
.tx{{flex:1;word-wrap:break-word}} .tg{{flex:0 0 96px;font-size:10px}}
.kosong{{color:#ccc;font-size:10px}} .ny{{color:#e65100;font-size:9.5px}}
</style></head><body>
<h1>⚖️ Uji 10 — baris {AWAL}–{akhir} SESUDAH perbaikan ①+②</h1>
<div class="kotak">Kotak <b style="color:#e91e63">MERAH</b> = 4 baris yang Bos sorot ·
TANDA_JML · tanda ↩nyambung = baris patahan yang disambung kode.</div>
<div class="dua">
<div class="kol"><div class="kepala">📄 NASKAH ASLI</div>{''.join(kiri)}</div>
<div class="kol"><div class="kepala k2">🔎 + TANDA JEV (perbaikan)</div>{''.join(kanan)}</div>
</div></body></html>'''
        dok = dok.replace('TANDA_JML', f'{len(nyambung)} baris disambung · goyang {len(goyang)} baris')
        open('/app/SAJI_UJI10_550.html', 'w').write(dok)
        print(f'\n   SAJI: /app/SAJI_UJI10_550.html {len(dok):,} byte')
    finally:
        db.close()


if __name__ == '__main__':
    main()
