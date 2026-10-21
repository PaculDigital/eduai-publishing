#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════
#  PERBAIKI TAB KOLABORASI + TAB AI — warna & shimmer PERMANEN
# ═══════════════════════════════════════════════════════════════════════
#
#  KENAPA SKRIP INI ADA
#  ─────────────────────
#  Sebelumnya warna tab "Kolaborasi" hanya hidup sebagai PREVIEW CSS di
#  memori browser (add_style_tag) — hilang begitu browser di-refresh.
#  Skrip ini menulis CSS LANGSUNG KE FILE app.css di dalam container OO,
#  jadi efeknya permanen untuk SEMUA browser/user.
#
#  FILE YANG DIUBAH : 5 editor (document, spreadsheet, presentation,
#                     visio, pdf) -> resources/css/app.css
#                     + app.css.gz  (nginx OO pakai `gzip_static on`:
#                       kalau .gz tidak di-regenerate, yang dikirim ke
#                       browser tetap versi LAMA!)
#  MARKER           : EDUAI-TAB-COLLAB      (tab Kolaborasi, #ffa000)
#                     EDUAI-TAB-COLLAB-AI   (tab AI, shimmer emas)
#  WARNA            : #ffa000 (oranye keemasan — pilihan Bos, kandidat C)
#
#  SELEKTOR (hasil baca source OO, JANGAN dikira-kira)
#  ────────────────────────────────────────────────────
#  1) Tab "Kolaborasi" — controller/Toolbar.js membuatnya dengan
#     action: 'review' (caption = textTabCollaboration). Template di
#     common/main/lib/component/Mixtbar.js:
#        <li class="ribtab"><a id="<action>" data-tab="<action>">CAPTION</a></li>
#     → selector benar: a#review / a[data-tab="review"].
#       "collaboration" itu cuma nama LAYOUT PANEL, bukan tab.
#
#  2) Tab "AI" — plugin AI (GUID {9DC93CDB-...}) TIDAK punya field "tab"
#     di config.json, jadi OO tidak membuat tab tersendiri (ia menempel
#     ke tab 'plugins' + statusnya di localStorage browser → makanya
#     "kadang ada, kadang hilang"). perbaiki_tab_ai.py menyisipkan
#     "tab": {"id":"eduai-ai","text":"AI"} sehingga OO membuat
#        <li class="ribtab"><a id="eduai-ai" data-tab="eduai-ai">AI</a></li>
#     → selector benar: a#eduai-ai / a[data-tab="eduai-ai"].
#
#  JEBAKAN YANG SUDAH TERBUKTI (jangan diulang)
#  ────────────────────────────────────────────
#  1. JANGAN `sed -i '/MARKER/d'` — blok CSS multi-baris, sed hanya
#     menghapus baris bermarker → sisa blok menempel & CSS rusak.
#  2. JANGAN set sys.argv SESUDAH exec() — exec() jalan lebih dulu,
#     si penerima membaca argv yang belum diset → mati diam-diam.
#     Nilai HARUS dikirim lewat literal base64 di dalam source.
#  3. AWAS PREFIX MARKER: 'EDUAI-TAB-COLLAB' adalah PREFIX dari
#     'EDUAI-TAB-COLLAB-AI'. Pencarian naif via s.find() akan menemukan
#     blok AI lebih dulu lalu memotong dari titik yang salah →
#     blok menumpuk terus. Karena itu pembersihan di skrip ini memakai
#     DAFTAR MARKER LENGKAP yang dievaluasi terpisah, bukan satu prefix.
#  4. JANGAN lupa regenerate app.css.gz (nginx gzip_static menyajikan
#     versi lama walau app.css sudah benar).
#
#  CARA PAKAI
#  ──────────
#    python3 scripts/perbaiki_tab_kolaborasi.py           # pasang
#    python3 scripts/perbaiki_tab_kolaborasi.py --cek    # periksa saja
#
#  Dipanggil otomatis oleh scripts/perbaiki_oo.sh sehingga bertahan
#  setiap container dibangun ulang.
# ═══════════════════════════════════════════════════════════════════════
import base64
import subprocess
import sys

CT = "oo-converter"
BASE = "/var/www/onlyoffice/documentserver/web-apps/apps"
EDITORS = ["documenteditor", "spreadsheeteditor", "presentationeditor",
           "visioeditor", "pdfeditor"]

# Daftar marker LENGKAP (jangan pakai pencarian prefix — lihat jebakan #3)
MARKER = "EDUAI-TAB-COLLAB"
MARKER_AI = "EDUAI-TAB-COLLAB-AI"
MARKERS = [MARKER, MARKER_AI]     # urut: cek yang lebih spesifik tetap aman
# Jumlah blok CSS yang HARUS ada setelah pasang = 2 (Kolaborasi + AI)
BLOK_HARUS = 2

WARNA = "#ffa000"          # kandidat C — oranye keemasan
WARNA_HOVER = "#ffb63d"
WARNA_AKTIF = "#e08800"    # latar putih saat tab aktif → agak digelapkan

KOMEN = "dibuat oleh perbaiki_tab_kolaborasi.py"

CSS_KOLAB = f"""/* ═══ {MARKER} ═══ {KOMEN} ═══
   Tab "Kolaborasi" (= action 'review' di source OO) dibuat oranye
   keemasan supaya menonjol di bar tab.

   ⚠️ STRUKTUR DOM ASLI (jangan dikira-kira):
      <section class="tabs"><ul role="tablist">
        <li class="ribtab"><a role="tab" id="review" data-tab="review">…</a></li>
      </ul></section>
   Aturan bawaan OO yang membuat tab PUTIH adalah:
      .toolbar .tabs li > a {{ color: var(--text-toolbar-header) }}
   Selektor kita harus MENANG atas aturan itu — karena itu ditulis
   lengkap (.toolbar .tabs li > a) + !important, BUKAN cuma
   'li.ribtab > a' yang kalah spesifisitas. */
.toolbar .tabs li.ribtab > a[data-title="Kolaborasi"],
.toolbar .tabs ul > li > a[data-title="Kolaborasi"],
.toolbar .tabs li.ribtab > a#review,
li.ribtab > a#review {{
    color: {WARNA} !important;
    font-weight: 700 !important;
    text-shadow: 0 0 6px rgba(255, 160, 0, .45) !important;
}}
.toolbar .tabs li.ribtab > a#review:hover,
.toolbar .tabs li.ribtab > a[data-title="Kolaborasi"]:hover,
li.ribtab > a#review:hover,
li.ribtab > a[data-tab="review"]:hover {{
    color: {WARNA_HOVER} !important;
}}
/* tab aktif latarnya putih → digelapkan sedikit biar tetap terbaca */
.toolbar .tabs li.ribtab.active > a#review,
.toolbar .tabs li.active > a[data-title="Kolaborasi"],
.toolbar .tabs ul li.ribtab.active > a[data-tab="review"],
li.ribtab.active > a#review {{
    color: {WARNA_AKTIF} !important;
}}
/* ═══ /{MARKER} ═══ */
"""

CSS_AI = f"""/* ═══ {MARKER_AI} ═══ {KOMEN} ═══
   Tab "AI" = tab plugin background bawaan OnlyOffice.

   ── KENAPA PAKAI [data-title="AI"] ─────────────────────────────────
   Plugin AI TIDAK bisa diberi tab lewat config: di Plugins.js plugin
   bertipe 'background' di-RETURN lebih dulu sebelum blok yang membaca
   `model.get('tab')` → field "tab" di config plugin DIABAIKAN TOTAL.

   Tab AI yang terlihat dibuat jalur internal dengan id = GUID ACAK
   yang BERUBAH setiap editor dibuka (terbukti: 2x buka →
   13df42c9-… lalu 8fc9852e-…). Jadi id TIDAK bisa dipakai.

   Yang STABIL adalah atribut `data-title` (dari template tab OO):
       <a role="tab" id="<guid-acak>" data-tab="<guid-acak>"
          data-title="AI">AI</a>
   `data-title` = caption tab → selalu "AI", tidak berubah tiap load.

   CATATAN: hanya SATU atribut yang boleh dipercaya. JANGAN pakai
   :last-child / urutan tab — DOM OO memuat tab dinamis
   ("Header & Footer", "Chart design") yang tidak terlihat di layar,
   jadi posisi AI TIDAK tetap. */
.toolbar .tabs li.ribtab > a[data-title="AI"],
.toolbar .tabs ul > li > a[data-title="AI"],
.tabs li.ribtab > a[data-title="AI"],
a[data-title="AI"] {{
    /* ⚠️ JANGAN pakai shorthand `background:` + !important — terbukti
       MEMATIKAN animasi background-position (uji terisolasi: shorthand
       → background-position diam di 0% 0%; properti spesifik → bergerak).
       Karena itu ditulis background-image / -size / -repeat terpisah
       TANPA !important, sedangkan color/fill PAKAI !important supaya
       tetap menang atas aturan OO (.toolbar .tabs li>a{{color:#fff}}). */
    background-image: linear-gradient(90deg,
        {WARNA} 0%, #ffd77a 40%, #fff3d0 50%, #ffd77a 60%, {WARNA} 100%);
    background-size: 100% 100%;
    background-repeat: repeat;
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent !important;
    color: {WARNA} !important;   /* fallback kalau background-clip gagal */
    font-weight: 700 !important;
    animation: eduaiAiShimmer 2.8s linear infinite;
}}
@keyframes eduaiAiShimmer {{
    0%   {{ background-position: -100% 0; }}
    100% {{ background-position: 100% 0; }}
}}
/* saat tab AI aktif, latar tab jadi terang → matikan gradien agar
   teks tetap terbaca (teks transparan di latar terang = tak terlihat) */
.toolbar .tabs li.active > a[data-title="AI"],
.tabs li.ribtab.active > a[data-title="AI"] {{
    background: none !important;
    -webkit-text-fill-color: {WARNA_AKTIF} !important;
    color: {WARNA_AKTIF} !important;
    animation: none !important;
}}
/* hormati preferensi aksesibilitas: matikan gerak */
@media (prefers-reduced-motion: reduce) {{
    a[data-title="AI"] {{
        animation: none !important;
        background: none !important;
        -webkit-text-fill-color: {WARNA} !important;
        color: {WARNA} !important;
    }}
}}
/* ═══ /{MARKER_AI} ═══ */
"""

CSS_SEMUA = CSS_KOLAB + CSS_AI


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def b64(x):
    return base64.b64encode(x.encode()).decode()


def main():
    cek_only = "--cek" in sys.argv
    targets = [f"{BASE}/{e}/main/resources/css/app.css" for e in EDITORS]

    rc, _, _ = sh(f"docker ps --format '{{{{.Names}}}}' | grep -qx {CT}")
    if rc != 0:
        print(f"  ✗ container '{CT}' TIDAK JALAN")
        return 1

    if cek_only:
        n = 0
        for t in targets:
            _, out, _ = sh(
                f"docker exec {CT} python3 -c \"import re;"
                f"s=open('{t}').read();"
                f"print(len(re.findall(r'DIBUAT', s)))\" 2>/dev/null || echo 0")
            # hitung dari jumlah komentar penutup tiap blok
            _, out, _ = sh(
                f"docker exec {CT} python3 -c \""
                f"s=open('{t}').read();"
                f"print(s.count('/{MARKER} ═══ */')"
                f" + s.count('/{MARKER_AI} ═══ */'))\" 2>/dev/null || echo 0")
            if out.isdigit() and int(out) >= BLOK_HARUS:
                n += 1
        print(f"  → CSS tab Kolaborasi+AI: {n}/5 editor terpasang")
        return 0 if n >= 5 else 1

    # Pembersih: buang SETIAP blok lengkap untuk tiap marker di daftar,
    # DIEVALUASI TERPISAH supaya prefix 'EDUAI-TAB-COLLAB' tidak salah
    # menangkap blok '-AI' (jebakan #3).
    pembersih = ";".join(
        f"s=re.sub(r'/\\* ═══ {m} ═══.*?/\\* ═══ /{m} ═══ \\*/', '', s, flags=re.S)"
        for m in MARKERS)

    # Sisa blok rusak (marker pembuka tanpa penutup) — dibuang dari
    # komentar pembuka sampai komentar penutup terakhir yang ditemukan.
    pembersih += (
        ";import re as _re\n"
        f"for _m in {MARKERS!r}:\n"
        "    _i = s.find('/* ═══ ' + _m + ' ═══')\n"
        "    while _i >= 0:\n"
        "        _j = s.find('/* ═══ /' + _m + ' ═══ */', _i)\n"
        "        if _j < 0:\n"
        "            _nx = min([x for x in (s.find('/* ═══ ', _i + 5),"
        " len(s)) if x > _i] or [len(s)])\n"
        "            s = s[:_i] + s[_nx:]\n"
        "        else:\n"
        "            s = s[:_i] + s[_j + len('/* ═══ /' + _m + ' ═══ */'):]\n"
        "        _i = s.find('/* ═══ ' + _m + ' ═══')\n"
    )

    b64_clean = b64(pembersih)
    b64_blok = b64(CSS_SEMUA)
    okc = 0

    for t in targets:
        eks = t.split("/")[-4]
        script = (
            "import base64, re\n"
            f"p = {t!r}\n"
            f"s = open(p, encoding='utf-8').read()\n"
            f"blok = base64.b64decode({b64_blok!r}).decode()\n"
            f"pembersih = base64.b64decode({b64_clean!r}).decode()\n"
            "exec(pembersih)\n"
            # buang sisa selektor lama (kalau ada)
            "s = re.sub(r'\\n?#[^\\n{]*-tab-collaboration[^{]*\\{[^}]*\\}', '', s)\n"
            "s = re.sub(r'\\n?\\.ribtab-collaboration[^{]*\\{[^}]*\\}', '', s)\n"
            "s = re.sub(r'\\n{3,}', '\\n\\n', s).rstrip('\\n') + '\\n'\n"
            "s = s + blok\n"
            "open(p, 'w', encoding='utf-8').write(s)\n"
            # regenerate .gz — WAJIB (nginx gzip_static on)
            "with open(p, 'rb') as f:\n"
            "    data = f.read()\n"
            "import gzip\n"
            "with gzip.GzipFile(fileobj=open(p + '.gz', 'wb'), mode='wb',"
            " compresslevel=9, mtime=0) as g:\n"
            "    g.write(data)\n"
            # laporan: jumlah blok per marker (dihitung dari komentar penutup)
            f"print(s.count('/{MARKER} ═══ */'),"
            f" s.count('/{MARKER_AI} ═══ */'), len(s))\n"
        )
        rc, out, err = sh(
            f"docker exec {CT} python3 -c "
            f"\"import base64;exec(base64.b64decode('{b64(script)}'))\"")
        parts = out.split()
        kol_n = int(parts[0]) if parts and parts[0].isdigit() else -1
        ai_n = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1
        size = parts[2] if len(parts) > 2 else '?'
        sehat = (rc == 0 and kol_n == 1 and ai_n == 1)
        okc += 1 if sehat else 0
        print(f"  {'✓' if sehat else '✗'} {eks:16} blok_kolab={kol_n} "
              f"blok_ai={ai_n} size={size}")
        if not sehat and err:
            print(f"      err: {err[:180]}")

    print(f"\n  {'✓' if okc >= 5 else '✗'} CSS tab Kolaborasi+AI bersih & "
          f"terpasang {okc}/5 editor")
    return 0 if okc >= 5 else 1


if __name__ == "__main__":
    sys.exit(main())
