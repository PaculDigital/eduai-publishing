#!/usr/bin/env python3
# ═══════════════════════════════════════════════════════════════════════
#  PERBAIKI TAB AI — sisipkan field "tab" ke config plugin AI
# ═══════════════════════════════════════════════════════════════════════
#
#  KENAPA SKRIP INI ADA
#  ─────────────────────
#  Plugin AI bawaan OnlyOffice (GUID {9DC93CDB-B576-4F0C-B55E-FCC9C48DD007})
#  punya "type": "background" dan TIDAK punya field "tab" di config.json.
#
#  Akibatnya (terverifikasi di source OO):
#    - Plugins.js membuat tab dari item.tab:
#        tab: item.tab ? {action: item.tab.id, caption: ..., separator: ...}
#    - karena item.tab undefined, tab AI TIDAK dibuat sendiri
#    - ia menempel ke tab 'plugins' lewat getTab('plugins')
#    - dan status aktifnya disimpan di localStorage browser
#      (asc_plugins_background) → makanya tab AI "kadang ada, kadang
#      hilang" tergantung browser yang dipakai.
#
#  Skrip ini menyisipkan:
#     "tab": { "id": "eduai-ai", "text": "AI", "separator": true }
#  ke config.json plugin AI. Setelah itu OO membuat tab tersendiri:
#     <li class="ribtab"><a id="eduai-ai" data-tab="eduai-ai">AI</a></li>
#  (template di common/main/lib/component/Mixtbar.js)
#  dan tab itu jadi punya ID tetap yang bisa diwarnai CSS.
#
#  ⚠️  JUGA MENULIS config.json.gz
#  nginx OnlyOffice memakai `gzip_static on` — kalau .gz tidak ikut
#  di-regenerate, yang dikirim ke browser tetap config LAMA.
#  (Jebakan ini sudah terbukti di app.css & logo header.)
#
#  CARA PAKAI
#  ──────────
#    python3 scripts/perbaiki_tab_ai.py           # pasang
#    python3 scripts/perbaiki_tab_ai.py --cek     # periksa saja
#    python3 scripts/perbaiki_tab_ai.py --balik   # kembalikan ke asli
#
#  Dipanggil otomatis oleh scripts/perbaiki_oo.sh sehingga bertahan
#  setiap container dibangun ulang. Aman dijalankan berkali-kali.
# ═══════════════════════════════════════════════════════════════════════
import json
import subprocess
import sys

CT = "oo-converter"
GUID = "{9DC93CDB-B576-4F0C-B55E-FCC9C48DD007}"
PDIR = f"/var/www/onlyoffice/documentserver/sdkjs-plugins/{GUID}"
CFG = f"{PDIR}/config.json"
TAB_ID = "eduai-ai"
TAB_TEXT = "AI"


def sh(cmd):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "pasang"

    rc, _, _ = sh(f"docker ps --format '{{{{.Names}}}}' | grep -qx {CT}")
    if rc != 0:
        print(f"  ✗ container '{CT}' TIDAK JALAN")
        return 1

    rc, out, _ = sh(f"docker exec {CT} test -f {CFG} && echo ada")
    if out != "ada":
        print(f"  ✗ config plugin AI tidak ditemukan: {CFG}")
        return 1

    # ── Mode cek ─────────────────────────────────────────────────────
    if mode == "--cek":
        rc, out, _ = sh(
            f"docker exec {CT} python3 -c \"import json;"
            f"d=json.load(open('{CFG}'));"
            f"print(json.dumps(d.get('tab')))\"")
        print(f"  → field tab plugin AI: {out}")
        ok = '"id": "eduai-ai"' in out or '"id":"eduai-ai"' in out
        print(f"  {'✓ tab AI terpasang' if ok else '✗ tab AI BELUM terpasang'}")
        return 0 if ok else 1

    # ── Mode balik (restore dari backup di container) ────────────────
    if mode == "--balik":
        rc, _, err = sh(
            f"docker exec {CT} sh -c "
            f"\"cp /tmp/backup_ai/config.json.bak {CFG} 2>/dev/null && "
            f"cp /tmp/backup_ai/config.json.gz.bak {CFG}.gz 2>/dev/null\"")
        if rc == 0:
            print("  ✓ dikembalikan dari backup")
            return 0
        print(f"  ✗ gagal balik: {err[:200]}")
        return 1

    # ── Mode pasang ──────────────────────────────────────────────────
    # Backup dulu (idempoten: hanya kalau backup belum ada)
    sh(f"docker exec {CT} sh -c \"mkdir -p /tmp/backup_ai && "
       f"[ -f /tmp/backup_ai/config.json.bak ] || "
       f"cp {CFG} /tmp/backup_ai/config.json.bak\"")
    sh(f"docker exec {CT} sh -c \"[ -f /tmp/backup_ai/config.json.gz.bak ] || "
       f"cp {CFG}.gz /tmp/backup_ai/config.json.gz.bak 2>/dev/null\"")

    script = (
        "import json, gzip, collections\n"
        f"P = {CFG!r}\n"
        "d = json.load(open(P), object_pairs_hook=collections.OrderedDict)\n"
        "sudah = 'tab' in d and isinstance(d.get('tab'), dict) "
        f"and d['tab'].get('id') == {TAB_ID!r}\n"
        "if not sudah:\n"
        "    baru = collections.OrderedDict()\n"
        "    for k, v in d.items():\n"
        "        baru[k] = v\n"
        "        if k == 'guid':\n"
        f"            baru['tab'] = collections.OrderedDict("
        f"[('id', {TAB_ID!r}), ('text', {TAB_TEXT!r}), ('separator', True)])\n"
        "    d = baru\n"
        "    json.dump(d, open(P, 'w'), ensure_ascii=False, indent='\\t')\n"
        "with open(P, 'rb') as f:\n"
        "    data = f.read()\n"
        "with gzip.GzipFile(fileobj=open(P + '.gz', 'wb'), mode='wb',"
        " compresslevel=9, mtime=0) as g:\n"
        "    g.write(data)\n"
        "json.load(open(P))\n"
        "print('tab=' + json.dumps(d.get('tab'), ensure_ascii=False),"
        " 'size=' + str(len(data)), 'sudah=' + str(sudah))\n"
    )
    import base64
    b64s = base64.b64encode(script.encode()).decode()
    rc, out, err = sh(
        f"docker exec {CT} python3 -c \"import base64;exec(base64.b64decode('{b64s}'))\"")
    if rc != 0:
        print(f"  ✗ gagal pasang: {(err or out)[:200]}")
        return 1
    print(f"  ✓ {out}")

    # Verifikasi lewat HTTP (path yang benar-benar dibaca browser)
    rc, out, _ = sh(
        f"docker exec {CT} python3 -c \""
        f"import urllib.request, gzip, json;"
        f"r=urllib.request.urlopen('http://127.0.0.1/sdkjs-plugins/{GUID}/config.json');"
        f"raw=r.read();"
        f"raw=gzip.decompress(raw) if r.headers.get('Content-Encoding')=='gzip' else raw;"
        f"print(json.dumps(json.loads(raw).get('tab'), ensure_ascii=False))\"")
    print(f"  → via HTTP: {out}")
    return 0 if TAB_ID in out else 1


if __name__ == "__main__":
    sys.exit(main())
