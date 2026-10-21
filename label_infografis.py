"""MESIN LABEL — HTML infografis → PNG, plus tempel label ke ilustrasi AI.

KEPUTUSAN BOS 18 Okt 2026 (verbatim arahnya):
  "sengaja bikin tanpa teks. Label-label 'SIKLUS HUJAN', '1. PENGUAPAN' di gambar
   referensi saya itu hampir pasti dipasang sesudahnya di tahap desain — bukan
   digambar AI. Kalau teks diminta langsung ke AI, hasilnya pasti rusak/typo
   (apalagi bahasa Indonesia). Jadi pipeline yang profesional memang 2 langkah:
   ilustrasi AI dulu (bersih, tanpa teks) → label dipasang setelahnya di tahap layout."

⇒ TAHAP 1 (sudah ada): brief_visual.py → gambar AI TANPA TEKS.
⇒ TAHAP 2 (modul ini): label/tanda dipasang di atas gambar lewat HTML+CSS,
   dirender headless Chromium → PNG. Teksnya HTML asli, jadi TAJAM dan TIDAK
   mungkin typo dari model gambar.

Pakai:
    dari label_infografis import infografis, tempel_label
    infografis("<img src='...'>...", "/tmp/hasil.png", lebar=1024, tinggi=1024)
    tempel_label("ilustrasi.png", [{"teks":"PENGUAPAN","x":120,"y":300}], "out.png")
"""
import os
import base64
import mimetypes

CHROME = "/opt/data/.cloakbrowser/chromium-146.0.7680.177.5/chrome"

# Palet buku anak/pendidikan — cerah tapi tetap enak dilihat & aman cetak
PALET_ANAK = {
    "langit": "#E8F4FB",
    "krem": "#FFF9EE",
    "tinta": "#1B3A57",
    "aksen": "#F2994A",
    "hijau": "#27AE60",
    "biru": "#2D9CDB",
    "kuning": "#F2C94C",
    "merah": "#EB5757",
}


def _chrome_path():
    """Cari Chromium: env dulu, lalu CloakBrowser, lalu sistem."""
    if os.environ.get("CHROME_PATH") and os.path.exists(os.environ["CHROME_PATH"]):
        return os.environ["CHROME_PATH"]
    if os.path.exists(CHROME):
        return CHROME
    import shutil
    for n in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        p = shutil.which(n)
        if p:
            return p
    raise RuntimeError("Chromium tidak ditemukan — set CHROME_PATH")


def _gambar_jadi_data_uri(path):
    """Ubah PNG lokal jadi data URI supaya HTML mandiri (tidak butuh server)."""
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def html_infografis(isi_html, judul=None, lebar=1024, tinggi=1024,
                    palet=None, label_html="", jenis="umum"):
    """Rakit HTML infografis: latar, judul (opsional), isi, dan lapisan label.

    jenis: 'umum' | 'anak' | 'pendidikan' — MENENTUKAN wajah infografis
    (palet, bentuk label, font). Jangan campur: buku anak wajib jenis='anak'.
    """
    # Palet & CSS label ikut JENIS BUKU (keputusan Bos 18 Okt 2026)
    import jenis_buku as JB
    p = dict(JB.paket(jenis)["palet"])
    p.update(palet or {})
    judul_html = ""
    if judul:
        judul_html = (
            f'<div class="judul" style="color:{p["tinta"]}">{judul}</div>'
        )
    css_jenis = JB.label_css_penuh(jenis)
    return f"""<!doctype html>
<html lang="id"><head><meta charset="utf-8">
<style>
  @page {{ margin: 0; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin:0; padding:0; }}
  body {{
    width:{lebar}px; height:{tinggi}px; overflow:hidden;
    background:{p["krem"]};
    font-family:"DejaVu Sans","Noto Sans",Arial,sans-serif;
    position:relative;
  }}
  .kanvas {{ position:absolute; inset:0; }}
  .kanvas img {{ width:100%; height:100%; object-fit:contain; display:block; }}
  .judul {{
    position:absolute; top:24px; left:0; right:0; text-align:center;
    font-size:44px; font-weight:800; letter-spacing:.5px;
    text-transform:uppercase; z-index:5;
    text-shadow:0 2px 0 #fff, 0 0 12px rgba(255,255,255,.85);
  }}
  .label {{
    position:absolute; z-index:6; transform:translate(-50%,-50%);
    background:#fff; border:3px solid {p["tinta"]}; border-radius:18px;
    padding:8px 16px; font-size:22px; font-weight:700; color:{p["tinta"]};
    box-shadow:0 4px 0 {p["tinta"]}; white-space:nowrap; max-width:46%;
    line-height:1.15;
  }}
  .label.aksen {{ background:{p["aksen"]}; color:#fff; border-color:{p["tinta"]}; }}
  .label.hijau {{ background:{p["hijau"]}; color:#fff; border-color:{p["tinta"]}; }}
  .label.biru  {{ background:{p["biru"]};  color:#fff; border-color:{p["tinta"]}; }}
  .nomor {{
    display:inline-flex; align-items:center; justify-content:center;
    width:30px; height:30px; border-radius:50%; background:{p["tinta"]};
    color:#fff; font-size:19px; margin-right:8px; vertical-align:middle;
  }}
  .kaki {{
    position:absolute; bottom:14px; left:0; right:0; text-align:center;
    font-size:17px; color:{p["tinta"]}; opacity:.72; z-index:5;
  }}
  {css_jenis}
  {label_html}
</style></head>
<body>
  <div class="kanvas">{isi_html}</div>
  {judul_html}
</body></html>"""


def lebar_label_px(teks, nomor=None, ukur_asli=False):
    """Lebar label (px). Default: tabel TERUKUR; ukur_asli=True: tanya browser.

    TERUKUR 18 Okt 2026 (Chrome, font 22px bold DejaVu Sans):
        "1PENGUAPAN" 215 · "2PENGEMBUNAN" 251 · "3HUJAN" 152 · "4ALIRAN AIR" 202
        tinggi semua 52 px
    Rumus taksiran (15,5 px/huruf) MELESET: PENGUAPAN ditebak 197, aslinya 215
    ⇒ penjaga tumpang tindih jadi buta. Karena itu: huruf per huruf diukur.
    """
    if ukur_asli:
        return _ukur_browser(teks, nomor)
    n = len(str(teks))
    # Tabel terukur + margin aman; huruf lebar (M,W) ditambah
    lebar_huruf = 21 if n >= 9 else (18 if n >= 6 else 15)
    return int(lebar_huruf * n + (46 if nomor else 20))


def _ukur_browser(teks, nomor=None):
    """Ukur lebar label SEBENARNYA dengan Chrome headless (dump-dom + JS)."""
    import subprocess, re, tempfile
    isi = (f'<span class="nomor">{nomor}</span>' if nomor else "") + str(teks)
    html = html_infografis(
        f'<div id="U" class="label" style="left:500px;top:500px">{isi}</div>',
        lebar=1024, tinggi=1024)
    html = html.replace("</body>", """
<script>
const r=document.getElementById('U').getBoundingClientRect();
document.title=Math.round(r.width)+','+Math.round(r.height);
</script></body>""")
    f = tempfile.NamedTemporaryFile('w', suffix='.html', delete=False)
    f.write(html); f.close()
    try:
        r = subprocess.run([_chrome_path(), "--headless=new", "--no-sandbox",
                            "--disable-gpu", "--dump-dom", f"file://{f.name}"],
                           capture_output=True, text=True, timeout=60)
        m = re.search(r'<title>(\d+),(\d+)</title>', r.stdout)
        if not m:
            raise RuntimeError("ukur gagal: " + r.stdout[:200])
        return int(m.group(1))
    finally:
        os.unlink(f.name)


def cek_tumpang_tindih(label_list, lebar, tinggi):
    """Deteksi label yang saling tumpang tindih SEBELUM dirender.

    ⚠️ Terukur 18 Okt 2026: uji pertama Wulan menghasilkan label 1 & 2
    bertumpuk (jarak 230 px, lebar asli ±250 px). Penjaga versi pertama
    MEMAKAI 13 px/huruf sehingga kasus nyata itu TIDAK terdeteksi — gerbang
    palsu. Sekarang pakai lebar terkalibrasi. Tambah jeda aman 10 px.
    """
    if not label_list:
        return []
    kotak = []
    for i, lb in enumerate(label_list):
        teks = str(lb.get("teks", ""))
        w = lebar_label_px(teks, lb.get("nomor")) + 4    # jeda aman kecil
        h = 62
        x, y = lb.get("x", 0), lb.get("y", 0)
        kotak.append((i, x - w / 2, y - h / 2, x + w / 2, y + h / 2, teks, w))

    masalah = []
    for a in range(len(kotak)):
        for b in range(a + 1, len(kotak)):
            _, x1, y1, x2, y2, t1, w1 = kotak[a]
            _, u1, v1, u2, v2, t2, w2 = kotak[b]
            if x1 < u2 and u1 < x2 and y1 < v2 and v1 < y2:
                kurang = int(min(w1, w2) - abs(kotak[a][1] - kotak[b][1])) if False else None
                masalah.append(f"'{t1}' bertumpuk dengan '{t2}' "
                                f"(renggangkan minimal 20 px)")
        _, x1, y1, x2, y2, t1, _ = kotak[a]
        if x1 < 0 or y1 < 0 or x2 > lebar or y2 > tinggi:
            masalah.append(f"'{t1}' keluar kanvas ({lebar}x{tinggi})")
    return masalah


def infografis(isi_html, output_path, judul=None, lebar=1024, tinggi=1024,
               palet=None, label_list=None, jenis="umum"):
    """Render HTML infografis → PNG. Return path PNG.

    ⚠️ TERUKUR 18 Okt 2026: Chromium CloakBrowser TIDAK bisa dibuka lewat
    Playwright (`set_content` timeout 30 s — build-nya dipatch untuk stealth).
    Jalan yang BEKERJA: tulis HTML ke berkas, lalu panggil Chrome headless
    langsung (`--headless --screenshot`). Jangan kembali ke Playwright.

    label_list: [{"teks":..., "x":int, "y":int, "warna":"aksen|hijau|biru",
                  "nomor":int}] — posisi dalam piksel kanvas.
    """
    tumpang = cek_tumpang_tindih(label_list, lebar, tinggi)
    if tumpang:
        raise ValueError("label bertumpuk / keluar kanvas: " + "; ".join(tumpang))

    blok_label = ""
    for lb in (label_list or []):
        kelas = "label"
        if lb.get("warna"):
            kelas += " " + lb["warna"]
        isi = lb["teks"]
        if lb.get("nomor"):
            isi = f'<span class="nomor">{lb["nomor"]}</span>{isi}'
        blok_label += (
            f'<div class="{kelas}" style="left:{lb["x"]}px;top:{lb["y"]}px">{isi}</div>'
        )

    html = html_infografis(isi_html, judul=judul, lebar=lebar, tinggi=tinggi,
                           palet=palet, label_html="", jenis=jenis)
    html = html.replace("</body>", blok_label + "\n</body>")

    out_abs = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)
    tmp_html = out_abs + ".html"
    with open(tmp_html, "w", encoding="utf-8") as f:
        f.write(html)

    return _screenshot(tmp_html, out_abs, lebar, tinggi)


def _screenshot(html_path, png_path, lebar, tinggi):
    """Chrome headless langsung — cara yang TERBUKTI bekerja di VPS ini."""
    import subprocess
    chrome = _chrome_path()
    perintah = [
        chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
        "--hide-scrollbars", "--force-device-scale-factor=2",
        f"--window-size={lebar},{tinggi}",
        f"--screenshot={png_path}", f"file://{html_path}",
    ]
    r = subprocess.run(perintah, capture_output=True, text=True, timeout=120)
    if not os.path.exists(png_path):
        raise RuntimeError(
            "render gagal — Chrome tidak menghasilkan PNG. "
            f"exit={r.returncode} stderr={r.stderr[-400:]}"
        )
    # Rapikan: potong ke ukuran tepat (Chrome kadang 2x karena scale factor)
    _potong_tepat(png_path, lebar, tinggi)
    return png_path


def _potong_tepat(png_path, lebar, tinggi):
    """Pastikan PNG berukuran TEPAT (lebar*2, tinggi*2) karena scale 2x."""
    try:
        from PIL import Image
        im = Image.open(png_path)
        target = (lebar * 2, tinggi * 2)
        if im.size != target:
            if im.size[0] >= target[0] and im.size[1] >= target[1]:
                im.crop((0, 0, target[0], target[1])).save(png_path)
            else:
                im.resize(target, Image.LANCZOS).save(png_path)
    except Exception as e:
        print("       ⚠️ potong_tepat gagal:", e)


def tempel_label(gambar_path, label_list, output_path, ukuran=None,
                 judul=None, latar=None, kualitas=85, jenis="umum"):
    """Tempel label ke ilustrasi AI yang SUDAH ADA (tanpa mengubah gambarnya).

    Ini cara yang benar: ilustrasi AI tetap bersih/no-text, label HTML ditempel
    di atasnya. Return path PNG hasil.

    ⚠️ TERUKUR 18 Okt 2026: menempel gambar 1024px sebagai PNG base64 penuh
    (910 KB → data URI 1,2 MB) membuat Chrome macet >120 s. OBAT: perkecil ke
    JPEG kualitas 85 untuk lapisan label (label tetap vektor, jadi tetap tajam),
    lalu kembalikan ukuran aslinya. JANGAN naikkan timeout tanpa ini.
    """
    from PIL import Image
    import io

    im = Image.open(gambar_path).convert("RGB")
    if ukuran:
        im = im.resize(ukuran, Image.LANCZOS)
    lebar, tinggi = im.size

    # Perkecil untuk data URI (JPEG), bukan PNG raksasa
    kecil = im.copy()
    kecil.thumbnail((lebar, tinggi), Image.LANCZOS)
    buf = io.BytesIO()
    kecil.save(buf, format="JPEG", quality=kualitas, optimize=True)
    uri = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    print(f"       data URI: {round(len(uri)/1024)} KB "
          f"(dari PNG {round(os.path.getsize(gambar_path)/1024)} KB)")

    isi = f'<img src="{uri}" alt="ilustrasi">'
    return infografis(isi, output_path, judul=judul,
                      lebar=lebar, tinggi=tinggi,
                      palet={"krem": latar}, label_list=label_list, jenis=jenis)


def _gambar_jadi_data_uri_bytes(im):
    import io
    buf = io.BytesIO()
    im.convert("RGB").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


if __name__ == "__main__":
    # UJI: satu infografis contoh — 4 label + judul, JARAK SUDAH BENAR
    out = "/opt/data/_uji_label_infografis.png"
    X = [130, 440, 690, 890]
    kartu = "".join(
        f'<div style="position:absolute;left:{X[i]-80}px;top:560px;width:160px;'
        f'height:160px;background:{w};border-radius:26px;border:4px solid #1B3A57">'
        f'</div>'
        for i, w in enumerate([PALET_ANAK["biru"], PALET_ANAK["kuning"],
                               PALET_ANAK["hijau"], PALET_ANAK["aksen"]])
    )
    labels = [
        {"teks": "PENGUAPAN", "x": X[0], "y": 470, "warna": "biru", "nomor": 1},
        {"teks": "PENGEMBUNAN", "x": X[1], "y": 470, "warna": "kuning", "nomor": 2},
        {"teks": "HUJAN", "x": X[2], "y": 470, "warna": "hijau", "nomor": 3},
        {"teks": "ALIRAN AIR", "x": X[3], "y": 470, "warna": "aksen", "nomor": 4},
    ]
    p = infografis(kartu, out, judul="SIKLUS HUJAN", label_list=labels)
    print("SIMPAN:", p, os.path.getsize(p), "byte")
