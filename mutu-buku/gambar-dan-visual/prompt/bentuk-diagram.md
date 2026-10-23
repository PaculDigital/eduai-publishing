# Bentuk Diagram — DIAMBIL DARI KODE

> Sumber: `diagram_buku.py`. Diagram dibuat sebagai **SVG** (bukan AI gambar),
> jadi hasilnya presisi & gratis. 8 bentuk, dipilih menurut ISI (bukan template).

## Cara memilih bentuk — `pilih_bentuk(judul, ket, tahap)`

```python
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
```

## Daftar pembangun bentuk (`_PEMBANGUN`)

- **`alur`** → `_b_alur` — (tanpa keterangan)
- **`siklus`** → `_b_siklus` — Siklus melingkar TANPA PANAH — nomor besar + cincin gradasi.
- **`pohon`** → `_b_pohon` — (tanpa keterangan)
- **`piramida`** → `_b_piramida` — Piramida: SEGITIGA bertingkat, level terbawah paling LEBAR.
- **`lapisan`** → `_b_lapisan` — (tanpa keterangan)
- **`batang`** → `_b_batang` — (tanpa keterangan)
- **`pai`** → `_b_pai` — (tanpa keterangan)
- **`garis`** → `_b_garis` — (tanpa keterangan)

## Semua fungsi bentuk (kode lengkap)

### `_b_alur` — 10 baris

```python
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
```

### `_b_siklus` — 73 baris

```python
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
```

### `_b_pohon` — 10 baris

```python
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
```

### `_b_piramida` — 43 baris

```python
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
```

### `_b_lapisan` — 7 baris

```python
def _b_lapisan(judul, tahap):
    n = max(len(tahap or []), 3)
    labels = [_label(tahap, i, f'Lapisan {i+1}') for i in range(n)]
    baris = ''.join(
        f'<div class="simpul" style="background:{WARNA[min(i, len(WARNA)-1)]};'
        f'width:340px">{_esc(l)}</div>' for i, l in enumerate(labels))
    return f'<div class="tingkat" style="gap:3px">{baris}</div>'
```

### `_b_batang` — 12 baris

```python
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
```

### `_b_pai` — 18 baris

```python
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
```

### `_b_garis` — 26 baris

```python
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
```
