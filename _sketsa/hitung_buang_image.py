"""HITUNG gambar mana yang AMAN dibuang — JANGAN menghapus apa pun.

Aturan Bos: sisakan 1 image backup per proyek.
Aturan KERAS: gambar yang dipakai kontainer HIDUP tidak boleh disentuh.

Cara: kumpulkan semua tag dari kontainer hidup (termasuk via digests), lalu
tandai "SIMPAN" untuk: (a) semua tag yang dipakai kontainer hidup,
(b) 1 tag backup TERBARU per keluarga proyek.
"""
import re
import subprocess


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True,
                          text=True).stdout.strip()


# ── 1. Kontainer hidup → tag + image ID yang WAJIB selamat ────────────────
hidup = []
for line in sh("docker ps --format '{{.Names}}|{{.Image}}'").splitlines():
    nama, img = line.split('|', 1)
    #  Kalau img-nya ID (bukan nama:tag), resolusi ke nama:tag
    if ':' not in img or img.startswith('sha'):
        img = sh(f"docker inspect --format '{{{{.Config.Image}}}}' {nama}")
    iid = sh(f"docker inspect --format '{{{{.Image}}}}' {nama}")
    hidup.append((nama, img, iid))

selamat_tag = {h[1] for h in hidup}
selamat_id = {h[2] for h in hidup}

print('═══ GAMBAR KONTAINER HIDUP (WAJIB SELAMAT) ═══')
for n, i, iid in hidup:
    print(f'  {n:24s} {i:52s} {iid[7:19]}')

# ── 2. Semua gambar ───────────────────────────────────────────────────────
semua = []
for line in sh("docker images --format '{{.Repository}}:{{.Tag}}|{{.ID}}|"
               "{{.Size}}|{{.CreatedAt}}'").splitlines():
    bagian = line.split('|')
    if len(bagian) >= 4:
        semua.append({'tag': bagian[0], 'id': bagian[1],
                      'size': bagian[2], 'dibuat': bagian[3]})

# ── 3. Keluarga proyek (untuk "sisakan 1 backup") ────────────────────────
#  keluarga = nama repo tanpa tag  (mis. 'eduai-app', 'web-bayana')
def keluarga(tag):
    repo = tag.rsplit(':', 1)[0]
    return repo


# ── 4. Tandai SIMPAN: hidup + 1 backup terbaru per keluarga ──────────────
simpan = set()
alasan = {}

for t in selamat_tag:
    simpan.add(t)
    alasan[t] = 'dipakai kontainer hidup'

#  per keluarga: tag mana yang TIDAK hidup, urut waktu terbaru
kel = {}
for g in semua:
    if g['tag'] in selamat_tag:
        continue
    kel.setdefault(keluarga(g['tag']), []).append(g)

for nama_kel, daftar in kel.items():
    if not daftar:
        continue
    #  Ada yang hidup di keluarga ini? kalau ya → simpan 1 backup terbaru
    ada_hidup = any(keluarga(t) == nama_kel for t in selamat_tag)
    daftar.sort(key=lambda x: x['dibuat'], reverse=True)
    #  ⚠️ UTAMAKAN tag 'cadangan-pra-*' (titik mundur terakhir yang di-ACC
    #  untuk deploy) — jangan sampai yang dibuang justru titik mundurnya.
    cadangan = [g for g in daftar if 'cadangan-pra' in g['tag']]
    pilih = cadangan[0] if cadangan else daftar[0]
    simpan.add(pilih['tag'])
    alasan[pilih['tag']] = (
        f'BACKUP/titik mundur keluarga {nama_kel}' if ada_hidup
        else f'satu-satunya sisa keluarga {nama_kel} (backup)')

# ── 5. Hasil ──────────────────────────────────────────────────────────────
buang = [g for g in semua if g['tag'] not in simpan]


def mb(s):
    if 'GB' in s:
        return float(s.replace('GB', '')) * 1024
    if 'kB' in s:
        return float(s.replace('kB', '')) / 1024
    return float(s.replace('MB', ''))


total_buang = sum(mb(g['size']) for g in buang)
print()
print('═══ DISIMPAN ({}) ═══'.format(len(simpan)))
for t in sorted(simpan):
    print(f'  ✅ {t:56s} — {alasan.get(t, "?")}')
print()
print(f'═══ DIBUANG ({len(buang)} gambar, ~{total_buang/1024:.1f} GB) ═══')
for g in sorted(buang, key=lambda x: -mb(x['size'])):
    print(f'  🗑️  {g["size"]:>8}  {g["tag"]}')
