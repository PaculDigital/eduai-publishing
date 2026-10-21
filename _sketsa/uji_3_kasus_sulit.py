"""UJI 3 KASUS SULIT — calon penempel presisi (`pipa.py`) SEBELUM dikoding.

Yang diuji (murni algoritme, TANPA AI):
  1. KUTIPAN SALAH KETIK  — AI salah 1-3 huruf / beda spasi / beda tanda baca
  2. KALIMAT KEMBAR       — 2+ paragraf memuat kalimat SAMA → mana yang diganti?
  3. NASKAH BAGIAN-2      — potongan bagian ke-2 harus ditempel di POSISI benar

ATURAN UJI (standar Bos):
  · SEHAT  → harus LULUS
  · DIRUSAK → harus GAGAL (bukti bergigi)
  · Kalau tidak ketemu → WAJIB menolak jujur (JANGAN menebak)
"""
import re
import sys

LULUS = GAGAL = 0


def cek(nama, syarat, bukti=''):
    global LULUS, GAGAL
    if syarat:
        LULUS += 1
        print(f'  ✅ {nama}' + (f' — {bukti}' if bukti else ''))
    else:
        GAGAL += 1
        print(f'  ❌ {nama}' + (f' — {bukti}' if bukti else ''))
    return bool(syarat)


def normal(teks: str) -> str:
    """Bentuk normal untuk pencocokan TOLERAN (bukan tebakan)."""
    t = teks.lower()
    t = re.sub(r'[\u2018\u2019\u201c\u201d]', '"', t)      # kutip pintar → lurus
    t = re.sub(r'[\u2013\u2014]', '-', t)                  # en/em dash → -
    t = re.sub(r'\s+', ' ', t)                             # semua spasi → 1
    t = re.sub(r'[^\w\s\-.,;:()/%"]', '', t)               # buang tanda aneh
    return t.strip()


# ══════════════════════════════════════════════════════════════════════════
#  BAHAN UJI — dipisah supaya tiap kasus diuji pada bahan yang BERSIH.
#  ⚠️ JEBAKAN (ketemu 25Sep26): dulu paragraf 0 & 3 dibuat SAMA untuk
#     KASUS 2, tapi dipakai JUGA untuk KASUS 1 → 6 uji gagal palsu.
#     ATURAN: satu kasus = satu bahan bersih.
# ══════════════════════════════════════════════════════════════════════════
paras_unik = [
    'Perkembangan pesat teknologi dan transformasi digital telah mengubah '
    'lanskap kerja organisasi secara mendasar dalam satu dekade terakhir.',
    'Account Officer dituntut memiliki kesiapan digital agar mampu '
    'beradaptasi dengan perubahan proses layanan yang berlangsung cepat.',
    'Penelitian ini menguji peran kesiapan digital sebagai variabel '
    'mediasi antara kualitas kehidupan kerja dan kinerja adaptif.',
    'Hasil wawancara awal menunjukkan bahwa beban kerja dan dukungan '
    'atasan berpengaruh terhadap kesiapan menghadapi perubahan.',
]
naskah = '\n\n'.join(paras_unik)                    # ← UNIK, untuk KASUS 1

paras_kembar = paras_unik + [paras_unik[0]]         # ← ada 1 pasang kembar
naskah_kembar = '\n\n'.join(paras_kembar)           # ← khusus KASUS 2


def cari_paragraf(naskah: str, kutip: str) -> dict:
    """Cari paragraf yang memuat kutipan. TOLERAN tapi TIDAK menebak.

    Kembalikan {'status': 'cocok'|'toleran'|'kembar'|'tidak_ketemu',
                'indeks': [...], 'skor': float}
    """
    k = normal(kutip)
    if not k:
        return {'status': 'tidak_ketemu', 'indeks': [], 'skor': 0.0}
    par = naskah.split('\n\n')
    kena = []
    for i, p in enumerate(par):
        pn = normal(p)
        if k in pn:                       # cocok PERSIS (setelah normal)
            kena.append((i, 1.0))
            continue
        #  toleran: 90% kata kutipan muncul berurutan
        kata_k = k.split()
        kata_p = pn.split()
        if len(kata_k) >= 4:
            jendela = len(kata_k)
            for j in range(max(1, len(kata_p) - jendela + 1)):
                bagian = ' '.join(kata_p[j:j + jendela])
                rasio = _mirip(bagian, k)
                if rasio >= 0.90:
                    kena.append((i, rasio))
                    break
    if not kena:
        return {'status': 'tidak_ketemu', 'indeks': [], 'skor': 0.0}
    if len(kena) == 1:
        st = 'cocok' if kena[0][1] >= 0.999 else 'toleran'
        return {'status': st, 'indeks': [kena[0][0]], 'skor': kena[0][1]}
    return {'status': 'kembar', 'indeks': [i for i, _ in kena],
            'skor': max(s for _, s in kena)}


def _mirip(a: str, b: str) -> float:
    """Kemiripan sederhana (dice koefisien atas bigram)."""
    if not a or not b:
        return 0.0
    A = {a[i:i + 2] for i in range(len(a) - 1)}
    B = {b[i:i + 2] for i in range(len(b) - 1)}
    if not A or not B:
        return 0.0
    return 2 * len(A & B) / (len(A) + len(B))


# ══════════════════════════════════════════════════════════════════════════
print('═' * 74)
print('KASUS 1 — KUTIPAN SALAH KETIK / BEDA TANDA')
print('═' * 74)

asli = paras_unik[0]
uji_1 = [
    ('persis', asli, 'cocok'),
    ('beda 1 huruf (teknologi→tehnologi)',
     asli.replace('teknologi', 'tehnologi'), 'toleran'),
    ('beda spasi ganda', asli.replace(' dan ', '  dan  '), 'cocok'),
    ('kutip pintar → lurus', asli.replace('"', ''), 'cocok'),
    ('beda tanda hubung', asli.replace('mendasar', 'mendasar-'), 'toleran'),
    ('dipotong separuh',
     ' '.join(asli.split()[:12]), 'cocok'),
    ('kalimat KARANGAN (tidak ada)',
     'Kalimat ini tidak pernah ada di dalam naskah mana pun sama sekali.',
     'tidak_ketemu'),
]
for nama, kutip, harap in uji_1:
    h = cari_paragraf(naskah, kutip)
    cek(f'1. {nama} → {harap}', h['status'] == harap,
        f"dapat={h['status']} skor={h['skor']:.3f} indeks={h['indeks']}")

print()
print('═' * 74)
print('KASUS 2 — KALIMAT KEMBAR (2 paragraf memuat kalimat SAMA)')
print('═' * 74)
h = cari_paragraf(naskah_kembar, paras_kembar[0])
cek('2a. kalimat kembar → status "kembar" (JANGAN menebak)',
    h['status'] == 'kembar', f"dapat={h['status']} indeks={h['indeks']}")
cek('2b. kembar → SEMUA indeks dilaporkan (bukan 1 saja)',
    len(h['indeks']) == 2, f"indeks={h['indeks']} (harus [0, 3])")

#  Kalimat unik harus TETAP dapat 1
h2 = cari_paragraf(naskah_kembar, paras_kembar[1])
cek('2c. kalimat UNIK tetap dapat 1 (tidak salah tuduh kembar)',
    h2['status'] in ('cocok', 'toleran') and len(h2['indeks']) == 1,
    f"dapat={h2['status']} indeks={h2['indeks']}")

print()
print('═' * 74)
print('KASUS 3 — NASKAH BAGIAN-2 (potongan ke-2, bukan ke-1)')
print('═' * 74)
#  Tiru naskah 2 bagian: bagian 1 = paras 0-1, bagian 2 = paras 2-3
bag1 = '\n\n'.join(paras_unik[0:2])
bag2 = '\n\n'.join(paras_unik[2:4])
naskah_penuh = bag1 + '\n\n' + bag2

#  Kutipan dari bagian 2 harus ketemu di NASKAH PENUH (bukan hanya di bagian 2)
kutip_b2 = paras_unik[2]
h3 = cari_paragraf(naskah_penuh, kutip_b2)
cek('3a. kutipan dari bagian-2 ketemu di naskah penuh',
    h3['status'] in ('cocok', 'toleran') and h3['indeks'] == [2],
    f"dapat={h3['status']} indeks={h3['indeks']} (harus [2])")

#  DIBAHAYAKAN: kalau penempel cuma mencari di dalam potongan bagian-2
h3b = cari_paragraf(bag2, kutip_b2)
cek('3b. kalau dicari HANYA di bagian-2 → indeks lokal (jebakan!)',
    h3b['status'] in ('cocok', 'toleran') and h3b['indeks'] == [0],
    f"indeks lokal={h3b['indeks']} ← BUKAN posisi di naskah penuh")

#  Kutipan bagian-1 ditempel setelah bagian-2 = jangan sampai tertukar
kutip_b1 = paras_unik[0]
h3c = cari_paragraf(naskah_penuh, kutip_b1)
cek('3c. kutipan bagian-1 dapat posisi BENAR (indeks 0)',
    h3c['status'] in ('cocok', 'toleran', 'kembar') and 0 in h3c['indeks'],
    f"dapat={h3c['status']} indeks={h3c['indeks']}")

print()
print('═' * 74)
print(f'HASIL: {LULUS} LULUS / {GAGAL} GAGAL')
print('═' * 74)
sys.exit(1 if GAGAL else 0)
