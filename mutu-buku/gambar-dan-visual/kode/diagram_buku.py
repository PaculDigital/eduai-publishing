"""DIAGRAM BUKU — VARIASI BENTUK DIPILIH DARI ISI (bukan kotak-panah-bawah).

🚨 KELUHAN BOS 20 Okt 2026 (verbatim):
  "Masih gunakan diagram lama, kotak garis, panah ke bawah. = Jelek!
   Dan rata kanan kiri flat sangat jelek untuk diagram.
   Tidak variasi, lebih aman kalo data ditengah/ justify/ rata tengah,
   lebih aman. Atau bisa pakai variasi, diagram kan banyak: grafik, pie,
   siklus dll."

AKAR (terukur, bukan tebakan):
  ① `generate_diagram_html()` hanya punya SATU bentuk: kotak → ▼ → kotak.
     Tidak ada pemilihan bentuk dari ISI.
  ② `.tahap { width:100% }` di dalam `.kartu { width:720px }` ⇒ kotak
     selebar halaman dan teks melebar rata kiri-kanan (flat, jelek).
  ③ Tidak ada variasi: siklus, pohon, piramida, batang, pai, garis.

OBAT:
  · Bentuk dipilih dari ISI (kata kunci + jumlah tahap), BUKAN acak.
  · Teks SELALU rata tengah. Tidak ada justify, tidak ada width:100%.
  · Lebar diagram 72% (di tengah), bukan full width.
  · 8 bentuk: alur, siklus, pohon, piramida, lapisan, batang, pai, garis.
"""
import re

#  ── Palet: tenang, cetak aman (B/W tetap terbaca) ──────────────────────
WARNA = ['#0D2C5A', '#1B5E8C', '#2E86AB', '#5BA3C7', '#8FC0D8',
         '#B8D4E3', '#D6E6EF', '#EAF2F7']
ABU = '#6B7280'

GAYA = """
* { margin:0; padding:0; box-sizing:border-box;
    font-family:'DejaVu Sans','Liberation Sans',Segoe UI,Roboto,Arial,sans-serif; }
body { background:#FFFFFF; padding:14px; display:flex; justify-content:center; }
.kartu { width:520px; }                      /* 72% dari 720px — TIDAK full width */
.judul { text-align:center; font-size:14px; font-weight:700; color:#0D2C5A;
         margin-bottom:4px; line-height:1.3; }
.keterangan { text-align:center; font-size:11px; color:#6B7280;
              font-style:italic; margin-bottom:16px; line-height:1.4; }
.sumber { text-align:center; font-size:10px; color:#9CA3AF; margin-top:14px; }
.panggung { display:flex; justify-content:center; align-items:center;
            flex-direction:column; gap:0; }

/* ── ALUR: kartu bersambung, teks tengah, TIDAK melebar ── */
.alur { display:flex; flex-direction:column; align-items:center; gap:0; }
.alur .kotak { background:#fff; border:1.5px solid #0D2C5A;
               border-radius:7px; padding:9px 16px; max-width:340px;
               min-width:200px; text-align:center; font-size:12px;
               color:#123; line-height:1.35; }
.alur .kotak b { color:#0D2C5A; }
.alur .sambung { color:#0D2C5A; font-size:15px; line-height:1; padding:4px 0; }

/* ── SIKLUS: melingkar, label di luar lingkaran ── */
/*  🚨 CACAT TERUKUR 20 Okt 2026 (dilihat mata dari PNG): label kiri &
    kanan TERPOTONG ("mengalr") karena `.simpul` berpusat di 10%/90% dan
    keluar dari kanvas 340px. Obat: panggung siklus diberi ruang
    horizontal (lebar 520px penuh) dan simpul dipersempit + posisi
    digeser ke dalam (radius 32% bukan 40%). */
.siklus { position:relative; width:100%; height:330px; margin:0 auto; }
.siklus .pusat { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%);
                 text-align:center; font-size:11.5px; font-weight:700;
                 color:#0D2C5A; width:120px; line-height:1.3;
                 background:#fff; padding:6px; border-radius:6px; z-index:2; }
.siklus .simpul { position:absolute; transform:translate(-50%,-50%);
                  width:104px; text-align:center; font-size:10.5px;
                  color:#123; line-height:1.25; z-index:3; }
.siklus .nomer { display:inline-block; width:20px; height:20px; line-height:20px;
                 border-radius:50%; background:#0D2C5A; color:#fff;
                 font-size:10.5px; font-weight:700; margin-bottom:3px; }
.siklus .kanvas { position:absolute; left:50%; top:50%;
                  transform:translate(-50%,-50%); }

/* ── KUNCI SIKLUS: daftar HTML di bawah gambar (tidak bisa terpotong) ── */
.kunci-siklus { display:grid; grid-template-columns:1fr 1fr; gap:5px 16px;
                margin-top:12px; width:100%; max-width:430px; }
.kunci-baris { display:flex; align-items:flex-start; gap:7px; font-size:10.5px;
               color:#111827; line-height:1.3; text-align:left; }
.kunci-no { flex:0 0 17px; width:17px; height:17px; line-height:17px;
            border-radius:50%; background:#0D2C5A; color:#fff;
            font-size:10px; font-weight:700; text-align:center; }

/* ── POHON / PIRAMIDA / LAPISAN: batang bertingkat, teks tengah ── */
.tingkat { display:flex; flex-direction:column; align-items:center; gap:5px; }
.tingkat .baris { display:flex; justify-content:center; gap:8px; }
.tingkat .simpul { border-radius:6px; padding:8px 12px; text-align:center;
                   font-size:11.5px; color:#fff; line-height:1.3;
                   display:flex; align-items:center; justify-content:center; }
.tingkat .sambung { color:#9CA3AF; font-size:13px; line-height:1; }

/* ── BATANG (bar chart): sumbu + batang ── */
.batang { width:400px; }
.batang .item { display:flex; align-items:center; gap:8px; margin-bottom:7px; }
.batang .label { width:112px; text-align:right; font-size:11px; color:#374151;
                 line-height:1.25; }
.batang .trek { flex:1; background:#EDF1F4; border-radius:3px; height:20px;
                overflow:hidden; }
.batang .isi { height:100%; border-radius:3px;
               display:flex; align-items:center; justify-content:flex-end;
               padding-right:6px; color:#fff; font-size:10px; font-weight:700; }

/* ── PAI (donut + legenda) ── */
.pai { display:flex; align-items:center; justify-content:center; gap:20px; }
.pai svg { flex:0 0 auto; }
.pai .legenda { font-size:11px; color:#374151; line-height:1.7; text-align:left; }
.pai .kunci { display:inline-block; width:11px; height:11px; border-radius:2px;
              margin-right:6px; vertical-align:middle; }

/* ── GARIS (line chart) ── */
.garis { width:400px; }
.garis .catatan { font-size:10.5px; color:#6B7280; text-align:center;
                  margin-top:6px; }
"""


def _esc(t):
    """Escape teks supaya tidak merusak HTML."""
    return (str(t if t is not None else '')
            .replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


#  ── PEMILIH BENTUK: dibaca dari ISI, bukan acak ──────────────────────
POLA_SIKLUS = re.compile(
    r'\b(siklus|daur|berulang|kembali|putaran|melingkar|rotasi|peredaran)\b',
    re.IGNORECASE)
POLA_POHON = re.compile(
    r'\b(pohon|klasifikasi|penggolongan|jenis-jenis|cabang|turunan|'
    r'sebab-akibat|penyebab|mengapa|faktor)\b', re.IGNORECASE)
POLA_PIRAMIDA = re.compile(
    r'\b(piramida|hierarki|tingkatan|bertingkat|peringkat|dari umum|'
    r'dasar ke|fondasi|lapisan masyarakat)\b', re.IGNORECASE)
POLA_LAPISAN = re.compile(
    r'\b(lapisan|struktur|susunan|berlapis|irisan|potongan|anatomi|'
    r'dari dalam|permukaan)\b', re.IGNORECASE)
POLA_BATANG = re.compile(
    r'\b(perbandingan|dibandingkan|lebih besar|lebih kecil|tertinggi|'
    r'terendah|jumlah|persentase|data|ukuran|tingkat\s+\w+\s+di)\b',
    re.IGNORECASE)
POLA_PAI = re.compile(
    r'\b(proporsi|bagian|porsi|sebagian besar|mayoritas|persen|'
    r'komposisi|sebaran|distribusi)\b', re.IGNORECASE)
POLA_GARIS = re.compile(
    r'\b(perkembangan|pertumbuhan|tren|tahun ke tahun|naik turun|'
    r'sepanjang waktu|grafik|kurva|meningkat|menurun)\b', re.IGNORECASE)
POLA_ALUR = re.compile(
    r'\b(langkah|tahap|proses|alur|urutan|cara|pertama|kedua|'
    r'prosedur|tahapan)\b', re.IGNORECASE)


def pilih_bentuk(judul, ket, tahap=None):
    """Pilih bentuk diagram DARI ISI. Bukan acak.

    Urutan penilaian: pola paling KHAS menang. "Siklus" mengalahkan "alur"
    karena siklus lebih spesifik. Jumlah tahap ikut menentukan: tepat 3-4
    tahap dengan kata siklus ⇒ siklus; banyak tahap ⇒ tetap alur.

    Mengembalikan salah satu dari:
      'siklus' | 'pohon' | 'piramida' | 'lapisan' | 'batang' | 'pai' |
      'garis' | 'alur'
    """
    teks = f'{judul or ""} {ket or ""}'.strip()
    n = len(tahap or [])

    #  Pola khas dulu — bukan yang paling umum.
    if POLA_SIKLUS.search(teks) and 2 <= n <= 6:
        return 'siklus'
    if POLA_PIRAMIDA.search(teks) and 2 <= n <= 6:
        return 'piramida'
    if POLA_LAPISAN.search(teks) and 2 <= n <= 6:
        return 'lapisan'
    if POLA_POHON.search(teks) and 2 <= n <= 7:
        return 'pohon'
    if POLA_PAI.search(teks) and 2 <= n <= 6:
        return 'pai'
    if POLA_GARIS.search(teks) and 2 <= n <= 8:
        return 'garis'
    if POLA_BATANG.search(teks) and 2 <= n <= 8:
        return 'batang'
    if POLA_ALUR.search(teks) or n >= 3:
        return 'alur'
    return 'alur'


def _label(tahap, i, default):
    """Ambil label tahap ke-i, kalau tak ada pakai default."""
    if tahap and i < len(tahap):
        s = str(tahap[i]).strip()
        if s:
            return s
    return default


#  ── Pembangun tiap bentuk ────────────────────────────────────────────
def _b_alur(judul, tahap):
    isi = []
    n = len(tahap) or 3
    for i in range(n):
        lbl = _label(tahap, i, ('KONSEP', 'POKOK BAHASAN', 'PENERAPAN')[i]
                     if i < 3 else f'Tahap {i+1}')
        isi.append(f'<div class="kotak"><b>{i+1}.</b> {_esc(lbl)}</div>')
        if i < n - 1:
            isi.append('<div class="sambung">▼</div>')
    return f'<div class="alur">{"".join(isi)}</div>'


def _b_siklus(judul, tahap):
    """Siklus melingkar TANPA PANAH — nomor besar + cincin gradasi.

    🚨 KOREKSI BOS 20 Okt 2026 (verbatim):
      "Kurang pas panah nya" → lalu "Lebih aman kalo tidak pakai panah,
       cukup besarkan lingkaran angka dan buat lebih menarik saja".
    Jadi: BUANG semua panah & mata panah. Arah putaran dibaca dari URUTAN
    NOMOR (1→2→3→4) yang tentu lebih aman daripada mata panah kecil yang
    tidak terbaca saat dicetak hitam-putih. Nomor diperbesar (r=20) dan
    diberi cincin warna bergradasi supaya menarik tanpa panah.
    Label tahap tetap sebagai daftar HTML di bawah gambar (tidak bisa
    terpotong — pelajaran dari 4× gagal sebelumnya).
    """
    n = max(len(tahap or []), 3)
    labels = [_label(tahap, i, f'Tahap {i+1}') for i in range(n)]
    import math

    W = H = 300
    cx, cy = W / 2, H / 2
    r = 104

    #  Cincin: SATU lingkaran penuh, gradasi warna, tanpa panah & tanpa dash.
    cincin = (
        '<defs>'
        '<linearGradient id="cincin" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#0D2C5A"/>'
        '<stop offset="55%" stop-color="#2E86AB"/>'
        '<stop offset="100%" stop-color="#8FC0D8"/>'
        '</linearGradient>'
        '<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
        '<stop offset="60%" stop-color="#F3F8FB"/>'
        '<stop offset="100%" stop-color="#FFFFFF"/>'
        '</radialGradient>'
        '</defs>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#glow)"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
        f'stroke="url(#cincin)" stroke-width="7" opacity="0.28"/>')

    #  Nomor BESAR (r=21) di atas cincin. Tidak ada panah sama sekali.
    simpul = []
    for i in range(n):
        rad = math.radians(-90 + (360 / n) * i)
        x = cx + r * math.cos(rad)
        y = cy + r * math.sin(rad)
        warna = WARNA[min(i + 1, len(WARNA) - 1)]
        simpul.append(
            #  cincin putih pemisah supaya nomor "duduk" di atas garis
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="23" fill="#fff"/>'
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="20" fill="{warna}"/>'
            f'<text x="{x:.1f}" y="{y+7:.1f}" text-anchor="middle" '
            f'font-size="19" font-weight="700" fill="#fff" '
            f'font-family="DejaVu Sans">{i + 1}</text>')

    svg = (
        f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'{cincin}'
        #  Pusat: judul dengan latar putih supaya tidak tertabrak cincin
        f'<rect x="{cx-82}" y="{cy-20}" width="164" height="40" rx="8" '
        f'fill="#fff"/>'
        f'<text x="{cx}" y="{cy+6}" text-anchor="middle" font-size="13" '
        f'font-weight="700" fill="#0D2C5A" font-family="DejaVu Sans">'
        f'{_esc(str(judul)[:26])}</text>'
        f'{"".join(simpul)}</svg>')

    #  Kunci label: <div> HTML — dijamin tidak terpotong.
    kunci = ''.join(
        f'<div class="kunci-baris"><span class="kunci-no" '
        f'style="background:{WARNA[min(i + 1, len(WARNA) - 1)]}">{i + 1}</span>'
        f'<span class="kunci-teks">{_esc(l)}</span></div>'
        for i, l in enumerate(labels))

    return (f'<div class="panggung">{svg}'
            f'<div class="kunci-siklus">{kunci}</div></div>')


def _b_pohon(judul, tahap):
    n = max(len(tahap or []), 3)
    labels = [_label(tahap, i, f'Cabang {i+1}') for i in range(n)]
    akar = f'<div class="simpul" style="background:#0D2C5A;min-width:220px">{_esc(judul)}</div>'
    cabang = ''.join(
        f'<div class="simpul" style="background:{WARNA[min(i+1, len(WARNA)-1)]};'
        f'max-width:150px">{_esc(l)}</div>' for i, l in enumerate(labels))
    return ('<div class="tingkat">'
            f'{akar}<div class="sambung">│</div>'
            f'<div class="baris">{cabang}</div></div>')


def _b_piramida(judul, tahap):
    """Piramida: SEGITIGA bertingkat, level terbawah paling LEBAR.

    🚨 CACAT TERUKUR 20 Okt 2026 (dilihat mata dari PNG):
      versi-1 memakai kotak bertumpuk yang makin LEBAR ke bawah tapi
      gelap di atas → terbaca sebagai "hierarki terbalik", dan BUKAN
      bentuk piramida sama sekali.
    OBAT: gambar trapesium sungguhan lewat SVG (bukan div). Level 0
    (dasar) di BAWAH dan paling lebar; puncak sempit di atas.
    """
    n = max(len(tahap or []), 3)
    labels = [_label(tahap, i, f'Tingkat {i+1}') for i in range(n)]

    W = 420
    tinggi_baris = 46
    H = tinggi_baris * n + 16
    puncak_w = 96                      # lebar puncak
    dasar_w = W - 40                   # lebar dasar

    lapis = []
    for i in range(n):
        #  i=0 = PUNCAK (sempit, di atas). Label tetap urut 1..n dari atas.
        lebar_atas = puncak_w + (dasar_w - puncak_w) * (i / n)
        lebar_bawah = puncak_w + (dasar_w - puncak_w) * ((i + 1) / n)
        y = 8 + i * tinggi_baris
        cx = W / 2
        x1 = cx - lebar_atas / 2
        x2 = cx + lebar_atas / 2
        x3 = cx + lebar_bawah / 2
        x4 = cx - lebar_bawah / 2
        warna = WARNA[min(i + 1, len(WARNA) - 1)]
        lapis.append(
            f'<polygon points="{x1:.1f},{y} {x2:.1f},{y} {x3:.1f},{y+tinggi_baris} '
            f'{x4:.1f},{y+tinggi_baris}" fill="{warna}" stroke="#fff" '
            f'stroke-width="2"/>'
            f'<text x="{cx}" y="{y + tinggi_baris/2 + 4:.1f}" text-anchor="middle" '
            f'font-size="11" font-weight="600" '
            f'fill="{"#fff" if i < 3 else "#1F2937"}" '
            f'font-family="DejaVu Sans">{_esc(str(labels[i])[:34])}</text>')

    svg = (f'<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
           f'{"".join(lapis)}</svg>')
    return f'<div class="panggung">{svg}</div>'


def _b_lapisan(judul, tahap):
    n = max(len(tahap or []), 3)
    labels = [_label(tahap, i, f'Lapisan {i+1}') for i in range(n)]
    baris = ''.join(
        f'<div class="simpul" style="background:{WARNA[min(i, len(WARNA)-1)]};'
        f'width:340px">{_esc(l)}</div>' for i, l in enumerate(labels))
    return f'<div class="tingkat" style="gap:3px">{baris}</div>'


def _b_batang(judul, tahap):
    n = max(len(tahap or []), 3)
    labels = [_label(tahap, i, f'Butir {i+1}') for i in range(n)]
    #  Nilai batang: turun bertahap (bukan data palsu — hanya panjang visual).
    item = []
    for i, lbl in enumerate(labels):
        pct = max(18, 100 - i * int(78 / max(n, 1)))
        item.append(
            f'<div class="item"><div class="label">{_esc(lbl)}</div>'
            f'<div class="trek"><div class="isi" style="width:{pct}%;'
            f'background:{WARNA[min(i, len(WARNA)-1)]}">{i+1}</div></div></div>')
    return f'<div class="batang">{"".join(item)}</div>'


def _b_pai(judul, tahap):
    n = max(min(len(tahap or []), 6), 3)
    labels = [_label(tahap, i, f'Bagian {i+1}') for i in range(n)]
    total, acc, busur = 100, 0, []
    for i in range(n):
        porsi = round(total / n)
        warna = WARNA[min(i, len(WARNA)-1)]
        busur.append(f'<circle cx="70" cy="70" r="52" fill="none" '
                     f'stroke="{warna}" stroke-width="26" '
                     f'stroke-dasharray="{porsi*3.27:.1f} 327" '
                     f'stroke-dashoffset="{-acc*3.27:.1f}" '
                     f'transform="rotate(-90 70 70)"/>')
        acc += porsi
    legenda = ''.join(
        f'<div><span class="kunci" style="background:{WARNA[min(i, len(WARNA)-1)]}">'
        f'</span>{i+1}. {_esc(l)}</div>' for i, l in enumerate(labels))
    return (f'<div class="pai"><svg width="140" height="140">{"".join(busur)}</svg>'
            f'<div class="legenda">{legenda}</div></div>')


def _b_garis(judul, tahap):
    n = max(min(len(tahap or []), 8), 3)
    labels = [_label(tahap, i, f'T{i+1}') for i in range(n)]
    #  Naik bertahap: titik + garis, bukan data palsu berlabel angka.
    w, h, pad = 380, 150, 26
    langkah = (w - 2 * pad) / max(n - 1, 1)
    titik = []
    for i in range(n):
        x = pad + i * langkah
        y = h - pad - (h - 2 * pad) * (i / max(n - 1, 1))
        titik.append((x, y))
    path = ' '.join(f'{"M" if i == 0 else "L"}{x:.0f},{y:.0f}'
                    for i, (x, y) in enumerate(titik))
    bulatan = ''.join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4" fill="#0D2C5A"/>'
                      for x, y in titik)
    nomor = ''.join(
        f'<text x="{x:.0f}" y="{h-6}" font-size="9" fill="#6B7280" '
        f'text-anchor="middle">{i+1}</text>' for i, (x, y) in enumerate(titik))
    svg = (f'<svg width="{w}" height="{h}">'
           f'<line x1="{pad}" y1="{h-pad}" x2="{w-pad}" y2="{h-pad}" '
           f'stroke="#D1D5DB" stroke-width="1"/>'
           f'<path d="{path}" fill="none" stroke="#0D2C5A" stroke-width="2.5"/>'
           f'{bulatan}{nomor}</svg>')
    ket = '<div class="catatan">' + ' · '.join(
        f'{i+1}. {_esc(l)}' for i, l in enumerate(labels)) + '</div>'
    return f'<div class="garis">{svg}{ket}</div>'


_PEMBANGUN = {
    'alur': _b_alur, 'siklus': _b_siklus, 'pohon': _b_pohon,
    'piramida': _b_piramida, 'lapisan': _b_lapisan, 'batang': _b_batang,
    'pai': _b_pai, 'garis': _b_garis,
}


def html_diagram(diagram_id, judul, ket, tahap=None):
    """Rakit HTML diagram: bentuk dipilih dari ISI, teks rata tengah."""
    bentuk = pilih_bentuk(judul, ket, tahap)
    bangun = _PEMBANGUN.get(bentuk, _b_alur)
    #  Bentuk alur butuh label; bentuk lain juga. Kalau tahap kosong,
    #  alur memakai default KONSEP/POKOK/PENERAPAN, bentuk lain 3 simpul.
    if not tahap:
        tahap = ['', '', '']
    badan = bangun(judul, tahap)
    return f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="UTF-8"><style>{GAYA}</style></head>
<body><div class="kartu">
  <div class="judul">Diagram {_esc(diagram_id)} · {_esc(judul)}</div>
  <div class="keterangan">{_esc(ket)}</div>
  <div class="panggung">{badan}</div>
  <div class="sumber">Sumber: analisis konsep {_esc(judul)}</div>
</div></body></html>"""


if __name__ == '__main__':
    import sys
    for j, k, t in [
        ('Daur Air', 'air laut menguap lalu turun kembali ke laut', ['menguap', 'mengembun', 'hujan', 'mengalir']),
        ('Langkah Mencuci Tangan', 'proses pertama kedua ketiga', ['basahi', 'sabun', 'bilas']),
        ('Hierarki Kebutuhan', 'tingkatan dari dasar ke atas', ['dasar', 'menengah', 'puncak']),
        ('Proporsi Sampah', 'proporsi bagian terbesar', ['organik', 'plastik', 'kertas']),
    ]:
        print(f'{j:28s} -> {pilih_bentuk(j, k, t)}')
    sys.exit(0)
