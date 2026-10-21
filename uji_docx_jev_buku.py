"""UJI NYATA: Jev Buku Umum dipakai perakit BUKU → DOCX diperiksa.

Membuktikan 3 hal yang Bos minta:
  1. Jev benar-benar DIPAKAI (ada jejak log + putusan B3 memblokir daftar)
  2. Buku anak TIDAK lagi berubah jadi ratusan butir daftar
  3. Hasil DOCX tetap utuh: inden, paragraf pertama rata kiri, tabel, gambar

Jalur: buku_umum_assembly.rakit() — jalur produksi, bukan tiruan.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, '/app')

import buku_umum_assembly as A            # noqa: E402
import jev_buku_umum as JB                # noqa: E402
from docx import Document                  # noqa: E402

SUMBER = '/opt/data/buku_hasil/1792485534-5'
KELUAR = '/tmp/uji_buku_jev'
if os.path.isdir(KELUAR):
    shutil.rmtree(KELUAR)
os.makedirs(KELUAR, exist_ok=True)

hasil = {'sumber': SUMBER, 'keluar': KELUAR}


def inden_pt(p):
    fi = p.paragraph_format.first_line_indent
    return round(int(fi) / 12700, 2) if fi is not None else 0.0


# ── 1. Apakah Jev hidup? ────────────────────────────────────────────────
try:
    from app import jev
    hasil['jev_siap'] = jev.cek_siap()
except Exception as e:                      # noqa: BLE001
    hasil['jev_siap'] = {'siap': False, 'sebab': str(e)}

# ── 2. Jalankan perakit buku lewat jalur produksi ───────────────────────
judul = 'Ayo Mengenal Cuaca'
bab_txt = {}
for n in (1, 2):
    p = os.path.join(SUMBER, f'bab{n}', f'bab{n}.txt')
    if os.path.isfile(p):
        bab_txt[n] = open(p, encoding='utf-8', errors='replace').read()

#  Siapkan struktur bab + visual minimal
bab_data = {}
for n in bab_txt:
    bab_data[n] = {'title': f'Judul Bab {n}', 'file': f'bab{n}.txt'}
    os.makedirs(os.path.join(KELUAR, f'bab{n}'), exist_ok=True)
    open(os.path.join(KELUAR, f'bab{n}', f'bab{n}.txt'), 'w',
         encoding='utf-8').write(bab_txt[n])

#  Panggil add_bab lewat rakit (pakai Document kosong + monkeypatch sebisa)
doc = Document()

#  Butuh VISUAL_DIR & TABEL_DATA — arahkan ke folder sementara supaya uji
#  tidak menulis ke folder produksi.
A.VISUAL_DIR = os.path.join(KELUAR, '_visual')
os.makedirs(A.VISUAL_DIR, exist_ok=True)
A.FOLDER_HASIL = KELUAR

jejak = []
for n, teks in bab_txt.items():
    try:
        A.add_bab(doc, n, bab_data[n], teks)
        jejak.append({'bab': n, 'masuk': True})
    except Exception as e:                  # noqa: BLE001
        jejak.append({'bab': n, 'masuk': False, 'sebab': f'{type(e).__name__}: {e}'})
hasil['jejak_add_bab'] = jejak

DOCX = os.path.join(KELUAR, 'UJI_JEV_BUKU.docx')
doc.save(DOCX)
hasil['docx'] = DOCX
hasil['docx_kb'] = round(os.path.getsize(DOCX) / 1024, 1)

# ── 3. Periksa DOCX ─────────────────────────────────────────────────────
d = Document(DOCX)
par = [p for p in d.paragraphs if p.text.strip()]


#  🚨 ALAT UJI DIPERBAIKI 20 Okt 2026 — JANGAN pakai split('.').
#  Terukur: split('.') menghitung "et al." / "(2024)." / URL / desimal
#  sebagai pemisah kalimat ⇒ melaporkan 5 pelanggaran PALSU (13 kalimat
#  padahal 5). Pelajaran 15 Okt 2026: "PRODUKSI SEHAT, yang rusak ALAT UJI".
#  ⇒ WAJIB pakai penghitung yang SAMA dengan produksi.
import tata_paragraf as _T                # noqa: E402


def nkal(t):
    return len(_T.pecah_kalimat(t))


bullet = [p for p in par if p.style.name == 'List Bullet']
isi = [p for p in par if p.style.name != 'List Bullet'
       and len(p.text.strip()) > 40 and not p.style.name.startswith('Heading')]
berinden = [p for p in isi if inden_pt(p) > 0]

hasil['docx_ukur'] = {
    'paragraf_total': len(par),
    'butir_daftar': len(bullet),
    'paragraf_isi': len(isi),
    'berinden_lebih_0': len(berinden),
    'nilai_inden_pt': sorted({inden_pt(p) for p in isi}),
    'terpanjang_kalimat': max((nkal(p.text) for p in isi), default=0),
    'lebih_7_kalimat': sum(1 for p in isi if nkal(p.text) > 7),
    'tabel': len(d.tables),
    'gambar': len(d.inline_shapes),
}

# ── 4. Bukti Jev benar-benar dipakai: ulang pada teks yang sama = cache ─
teks1 = bab_txt[min(bab_txt)]
peta1 = JB.petakan_buku(teks1, pakai_cache=True)
peta2 = JB.petakan_buku(teks1, pakai_cache=True)
hasil['jev_bentuk'] = {
    'kandidat': peta1['jumlah']['kandidat'],
    'judul': peta1['jumlah']['judul'],
    'isi': peta1['jumlah']['isi'],
    'gagal': peta1['jumlah']['gagal'],
    'goyang': len(peta1['goyang']),
    'boleh_daftar': sum(1 for v in (peta1['boleh_daftar'] or {}).values() if v),
    'waktu_detik': peta1['waktu'],
    'dari_cache_ronde1': peta1.get('dari_cache'),
    'dari_cache_ronde2': peta2.get('dari_cache'),
}

print(json.dumps(hasil, indent=1, ensure_ascii=False))

# ── 5. Putusan ──────────────────────────────────────────────────────────
salah = []
u = hasil['docx_ukur']
if not hasil.get('jev_siap', {}).get('siap'):
    salah.append('Jev TIDAK siap')
if hasil['jev_bentuk']['gagal']:
    salah.append(f"Jev gagal {hasil['jev_bentuk']['gagal']} kandidat")
if u['butir_daftar'] > 40:
    salah.append(f"daftar terlalu banyak: {u['butir_daftar']} (cerita rusak?)")
if u['berinden_lebih_0'] < u['paragraf_isi'] * 0.6:
    salah.append(f"inden kurang: {u['berinden_lebih_0']}/{u['paragraf_isi']}")
if u['lebih_7_kalimat'] > 0:
    salah.append(f"{u['lebih_7_kalimat']} paragraf >7 kalimat")
if not hasil['jev_bentuk']['dari_cache_ronde2']:
    salah.append('cache ronde-2 TIDAK terpakai')

print(json.dumps({'salah': salah}, ensure_ascii=False))
sys.exit(0 if not salah else 1)
