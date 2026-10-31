"""Uji tombol buat kerangka: nonaktif sesudah kirim, teks tunggu persis,
cegah kirim ganda lewat submit formulir, tidak terkunci bila validasi gagal.

Jalankan di checkout hermes:
  python3 uji_tombol_kerangka.py
Keluar: LULUS N, GAGAL 0 bila semua lolos, exit 0. Selain itu exit 1.
Tidak menyentuh DB, jaringan, atau container produksi.
"""
import re
import subprocess
import sys
from pathlib import Path

TEMPLATE = Path("/opt/data/services/eduai-publishing/app/templates/buku_siapkan.html")
if not TEMPLATE.exists():
    TEMPLATE = Path(__file__).with_name("buku_siapkan.html")

lulus = []
gagal = []


def cek(nama, syarat):
    (lulus if syarat else gagal).append(nama)
    print(("  LULUS " if syarat else "  GAGAL ") + nama)


teks = TEMPLATE.read_text(encoding="utf-8")

cek("tombol-punya-id", 'id="btn-buat-kerangka"' in teks)
_tag_tombol = re.search(r'<button[^>]*btn-buat-kerangka[^>]*>', teks)
cek("tombol-submit-form-susun",
    bool(_tag_tombol) and 'type="submit"' in _tag_tombol.group(0)
    and 'form="form-susun"' in _tag_tombol.group(0))
cek("tombol-awal-kerangka",
    "Lihat kerangka dulu" in teks)
cek("teks-tunggu-persis", "Wait.. Proses Kerangka" in teks)
cek("handler-submit-bukan-klik",
    "form.addEventListener('submit'" in teks)
cek("nonaktif-sesudah-kirim", "btn.disabled = true" in teks)
cek("cegah-kirim-kedua",
    "sudahDikirim" in teks and "ev.preventDefault()" in teks)
cek("tidak-terkunci-bila-validasi-gagal",
    "form.checkValidity()" in teks)
cek("teks-kerangka-dari-aksi-outline",
    "/buku/outline" in teks and "indexOf('/buku/outline')" in teks)
cek("animasi-putar-css",
    ".tunggu-putar" in teks and "@keyframes tunggu-putar" in teks
    and "animation:tunggu-putar" in teks)
cek("gaya-nonaktif-jelas",
    ".tombol.utama:disabled" in teks and "cursor:not-allowed" in teks)
cek("tombol-judul-alt-tetap-ada",
    "btn-judul-alt" in teks and "/buku/judul-alternatif" in teks)
_css_baru = ""
_m = re.search(r"\.tombol\.utama:disabled.*?@keyframes tunggu-putar\{to\{transform:rotate\(360deg\)\}\}",
               teks, re.S)
if _m:
    _css_baru = _m.group(0)
cek("tanpa-em-dash-di-css-baru", "—" not in _css_baru and bool(_css_baru))

# Ekstrak blok script baru dan periksa sintaks JS dengan node.
blok = None
for m in re.finditer(r"<script>(.*?)</script>", teks, re.S):
    if "btn-buat-kerangka" in m.group(1) and "sudahDikirim" in m.group(1):
        blok = m.group(1)
        break
cek("blok-script-baru-ditemukan", blok is not None)
cek("tanpa-em-dash-di-script-baru", blok is not None and "—" not in blok)
if blok is not None:
    js = Path("/tmp/tombol_kerangka.js")
    js.write_text(blok, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
    cek("js-lolos-node-check", r.returncode == 0)

    # Uji perilaku dengan DOM tiruan di node.
    runner = r"""
const fs = require('fs');
const src = fs.readFileSync('/tmp/tombol_kerangka.js', 'utf8');
function pakai(aksi, valid) {
  let handler = null;
  const btn = { disabled: false, innerHTML: '', anak: [],
    appendChild(x) { this.anak.push(x); } };
  const form = { getAttribute: () => aksi,
    checkValidity: () => valid,
    addEventListener: (nama, fn) => { if (nama === 'submit') handler = fn; } };
  const document = {
    getElementById: (id) => id === 'form-susun' ? form : (id === 'btn-buat-kerangka' ? btn : null),
    createElement: () => ({ className: '', setAttribute: () => {} }),
    createTextNode: (t) => ({ teks: t }) };
  const fn = new Function('document', src);
  fn(document);
  return { btn, handler };
}
function kirim(h, dicegah) {
  const ev = { dicegah: false, preventDefault() { this.dicegah = true; } };
  h(ev);
  return ev.dicegah;
}
let a = pakai('/buku/outline', true);
let cegah1 = kirim(a.handler, false);
console.log('outline-kirim-pertama-tidak-dicegah=' + (!cegah1));
console.log('outline-nonaktif=' + a.btn.disabled);
console.log('outline-teks=' + a.btn.anak.map(x => x.teks || '').join(''));
console.log('outline-spinner=' + a.btn.anak.some(x => x.className === 'tunggu-putar'));
let cegah2 = kirim(a.handler, false);
console.log('outline-kirim-kedua-dicegah=' + cegah2);
let b = pakai('/buku/outline', false);
kirim(b.handler, false);
console.log('validasi-gagal-tidak-terkunci=' + (!b.btn.disabled));
let c = pakai('/buku/susun', true);
kirim(c.handler, false);
console.log('susun-teks=' + c.btn.anak.map(x => x.teks || '').join(''));
"""
    run = Path("/tmp/tombol_kerangka_uji.js")
    run.write_text(runner, encoding="utf-8")
    r = subprocess.run(["node", str(run)], capture_output=True, text=True)
    out = r.stdout
    cek("perilaku-outline-kirim-pertama-lolos",
        "outline-kirim-pertama-tidak-dicegah=true" in out)
    cek("perilaku-outline-nonaktif",
        "outline-nonaktif=true" in out)
    cek("perilaku-outline-teks-persis",
        "outline-teks=Wait.. Proses Kerangka" in out)
    cek("perilaku-outline-spinner",
        "outline-spinner=true" in out)
    cek("perilaku-kirim-kedua-dicegah",
        "outline-kirim-kedua-dicegah=true" in out)
    cek("perilaku-validasi-gagal-tidak-terkunci",
        "validasi-gagal-tidak-terkunci=true" in out)
    cek("perilaku-susun-bukan-teks-kerangka",
        "susun-teks=Wait.. Proses Susun" in out)

print(f"LULUS {len(lulus)}, GAGAL {len(gagal)}")
if gagal:
    print("GAGAL: " + ", ".join(gagal))
    sys.exit(1)
